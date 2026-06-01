"""CertificadoViewSet — REST do M8 certificados (T-CER-045/046/047).

Actions:
  GET  /api/v1/certificados/{id}/             retrieve (read-path WORM — só snapshot)
  POST /api/v1/certificados/decidir-ponto/    decidir_ponto (NC-03 — pré-condição RT)
  POST /api/v1/certificados/emitir/           emitir (US-CER-001 — emissão metrológica)
  POST /api/v1/certificados/{id}/reemitir/    reemitir (US-CER-004 — v(N+1))

Perfil/tipo_acreditacao/vigência SEMPRE server-side do Tenant (ADR-0067 — nunca body;
defesa L6). `cmc_para` injetado SÓ em perfil A (o use case rebaixa por vencimento/
suspensão — INV-CER-CGCRE-VIG-001). Idempotency-Key obrigatória nos POST (IDEMP-001).
Emissão/reemissão serializadas por advisory lock por calibração (TL-A1) e número
visível confirmado DENTRO da mesma transação. retrieve lê SÓ do snapshot persistido —
NUNCA reconsulta `cmc_para`/`tenant_perfil_e` (INV-CER-SNAPSHOT-CMC-001).

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from django.db import connection, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.metrologia.certificados.decidir_ponto_reconciliacao import (
    DecidirPontoInput,
    decidir_ponto_reconciliacao,
)
from src.application.metrologia.certificados.emitir_certificado import (
    EmitirCertificadoInput,
    emitir_certificado,
)
from src.application.metrologia.certificados.reemitir_certificado import (
    ReemitirCertificadoInput,
    reemitir_certificado,
)
from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.certificados.enums import (
    CategoriaMotivoExclusao,
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
)
from src.domain.metrologia.certificados.erros import (
    CertificadoError,
    CertificadoJaEmitidoError,
    ReconciliacaoCertificadoError,
    ReemissaoConflitanteError,
)
from src.domain.metrologia.certificados.numeracao import ReservaNumero
from src.domain.metrologia.certificados.transicoes import perfil_e_acreditado
from src.infrastructure.calibracao.repositories import DjangoCalibracaoRepository
from src.infrastructure.idempotencia.services_idempotencia import (
    ErroValidacao,
    NovoProcessamento,
    Replay,
    avaliar_chave_idempotencia,
    concluir_chave,
    falhar_chave,
)
from src.infrastructure.metrologia.certificados import query_service
from src.infrastructure.metrologia.certificados.repositories import (
    DjangoAnaliseReconciliacaoRepository,
    DjangoCertificadoRepository,
    DjangoNumeracaoCertificadoRepository,
)
from src.infrastructure.metrologia.certificados.serializers import (
    DecidirPontoSerializer,
    EmitirCertificadoSerializer,
    ReemitirCertificadoSerializer,
    serializar_certificado_leitura,
)
from src.infrastructure.multitenant.context import (
    active_tenant_context,
    usuario_id_context,
)
from src.infrastructure.tenant.models import Tenant

logger = logging.getLogger(__name__)

ENDPOINT_EMITIR = "certificados.emitir"
ENDPOINT_REEMITIR = "certificados.reemitir"
ENDPOINT_DECIDIR = "certificados.decidir_ponto"

# Erros de domínio fail-closed / regra de negócio → 422 (capturados DEPOIS dos 409).
_ERROS_422 = (ReconciliacaoCertificadoError, CertificadoError)


@dataclass(frozen=True, slots=True)
class _CtxEmissao:
    """Contexto montado server-side para uma emissão/reemissão (sem estado mutável na
    view). `num_repo`/`reserva` permitem ao caller confirmar o número DENTRO do atomic."""

    inp: EmitirCertificadoInput
    num_repo: DjangoNumeracaoCertificadoRepository
    reserva: ReservaNumero


def _resposta_erro_idempotencia(erro: ErroValidacao) -> Response:
    body = {"codigo": erro.codigo, "detalhe": erro.detalhe}
    if erro.headers:
        return Response(body, status=erro.http_status, headers=erro.headers)
    return Response(body, status=erro.http_status)


def _aplicar_idempotencia(
    request: Request,
    *,
    tenant_id: UUID,
    usuario_id: UUID,
    endpoint: str,
    payload_fingerprint: dict[str, Any],
) -> tuple[NovoProcessamento | None, Response | None]:
    avaliacao = avaliar_chave_idempotencia(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        endpoint=endpoint,
        chave_header=request.META.get("HTTP_IDEMPOTENCY_KEY"),
        payload=payload_fingerprint,
    )
    if isinstance(avaliacao, ErroValidacao):
        return None, _resposta_erro_idempotencia(avaliacao)
    if isinstance(avaliacao, Replay):
        return None, Response(
            avaliacao.response_body_resumo or {}, status=avaliacao.response_status
        )
    assert isinstance(avaliacao, NovoProcessamento)
    return avaliacao, None


def _tenant_ou_none() -> UUID | None:
    return active_tenant_context.get()


def _advisory_lock_cert(*, tenant_id: UUID, calibracao_id: UUID) -> None:
    """Serializa emissão/reemissão concorrente da MESMA calibração (TL-A1 — molde
    ADR-0065). Liberado no commit/rollback (xact). Fecha o TOCTOU do `revision`
    quando chamado ANTES de `obter_revision_para_cas`."""
    chave = f"{tenant_id}:certificado:{calibracao_id}"
    with connection.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [chave])


def _publicar_evento_cert(
    *,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    usuario_id: UUID,
    resource_summary: str,
) -> None:
    """Emite `Certificados.CertificadoReconciliado` na cadeia hash central WORM
    (T-CER-047). `cadeia=True, outbox=False`: evento PascalCase NÃO vai ao bus_outbox
    (CHECK lowercase) e não há consumer cross-módulo (status=emitido interno, não
    distribuível até A3). perfil_no_evento é derivado server-side (ContextVar)."""
    from src.infrastructure.audit.event_helpers import publicar_evento

    publicar_evento(
        acao="Certificados.CertificadoReconciliado",
        payload=payload,
        causation_id=causation_id,
        tenant_id=tenant_id,
        usuario_id=usuario_id if usuario_id != UUID(int=0) else None,
        resource_summary=resource_summary,
        outbox=False,
    )
    logger.info(
        "certificados evento WORM publicado acao=Certificados.CertificadoReconciliado",
        extra={"tenant_id": str(tenant_id), "resource": resource_summary},
    )


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class CertificadoViewSet(viewsets.ViewSet):
    """ViewSet REST de Certificado (emissão metrológica + reemissão + decisão RT)."""

    authz_purpose = "execucao_contrato"
    ACTION_MAP = {
        "retrieve": "certificados.ver",
        "decidir_ponto": "certificados.decidir_ponto",
        "emitir": "certificados.emitir",
        "reemitir": "certificados.reemitir",
    }

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    # ---------------------------------------------------------------- GET retrieve
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        """Read-path WORM: cert + N pontos do SNAPSHOT persistido. NUNCA reconsulta
        cmc_para/tenant_perfil_e (INV-CER-SNAPSHOT-CMC-001)."""
        cert_id = self._uuid_ou_404(pk)
        repo = DjangoCertificadoRepository()
        cert = repo.obter_por_id(cert_id)
        if cert is None:
            raise NotFound(f"Certificado {pk} não encontrado")
        pontos = repo.listar_pontos(certificado_id=cert_id)
        return Response(serializar_certificado_leitura(cert, pontos))

    # ---------------------------------------------------------------- POST decidir
    @action(detail=False, methods=["post"], url_path="decidir-ponto")
    def decidir_ponto(self, request: Request) -> Response:
        """POST — NC-03 decisão WORM do RT por ponto. # idempotency-key: required"""
        s = DecidirPontoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id, erro = self._contexto()
        if erro is not None:
            return erro

        novo, resp = _aplicar_idempotencia(
            request, tenant_id=tenant_id, usuario_id=usuario_id, endpoint=ENDPOINT_DECIDIR,
            payload_fingerprint={
                "calibracao_id": str(d["calibracao_id"]),
                "ponto": str(d["ponto_calibracao"]),
                "correlation_id": str(d["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = DecidirPontoInput(
                tenant_id=tenant_id,
                calibracao_id=d["calibracao_id"],
                ponto_calibracao=d["ponto_calibracao"],
                classificacao=ClassificacaoPonto(d["classificacao"]),
                decisao_rt=DecisaoReconciliacaoRT(d["decisao_rt"]),
                categoria_motivo=CategoriaMotivoExclusao(d["categoria_motivo"]),
                justificativa=d["justificativa"],
                correlation_id=d["correlation_id"],
                criado_em=datetime.now(UTC),
                ressalva_nao_rbc=d["ressalva_nao_rbc"],
            )
            with transaction.atomic():
                decisao = decidir_ponto_reconciliacao(
                    inp, analise_repo=DjangoAnaliseReconciliacaoRepository()
                )
        except (CertificadoError, ValueError) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {
            "calibracao_id": str(decisao.calibracao_id),
            "ponto_calibracao": str(decisao.ponto_calibracao),
            "decisao_rt": decisao.decisao_rt.value,
            "justificativa_hash": decisao.justificativa_hash,
        }
        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED, response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST emitir
    @action(detail=False, methods=["post"], url_path="emitir")
    def emitir(self, request: Request) -> Response:
        """POST — US-CER-001 emissão metrológica atômica. # idempotency-key: required"""
        s = EmitirCertificadoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, perfil, usuario_id, erro = self._contexto_com_perfil()
        if erro is not None:
            return erro
        calibracao_id = d["calibracao_id"]

        novo, resp = _aplicar_idempotencia(
            request, tenant_id=tenant_id, usuario_id=usuario_id, endpoint=ENDPOINT_EMITIR,
            payload_fingerprint={
                "calibracao_id": str(calibracao_id),
                "correlation_id": str(d["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        tenant = Tenant.objects.filter(id=tenant_id).first()
        if tenant is None:
            return self._falha(chave_id, tenant_id, NotFound("tenant"), status.HTTP_403_FORBIDDEN)
        cert_repo = DjangoCertificadoRepository()
        try:
            cal = DjangoCalibracaoRepository().obter_por_id(calibracao_id)
            if cal is None:
                return self._falha(
                    chave_id, tenant_id, NotFound(f"calibração {calibracao_id}"),
                    status.HTTP_404_NOT_FOUND,
                )
            data_emissao = d["data_emissao"] or datetime.now(UTC).date()
            ctx = self._montar_contexto_emissao(
                tenant=tenant, perfil=perfil, calibracao=cal, calibracao_id=calibracao_id,
                data_emissao=data_emissao, correlation_id=d["correlation_id"],
                snapshot_padroes=list(d["snapshot_padroes_usados_json"]), cert_repo=cert_repo,
            )
            with transaction.atomic():
                _advisory_lock_cert(tenant_id=tenant_id, calibracao_id=calibracao_id)
                if not ctx.num_repo.confirmar_numero(
                    reserva_id=ctx.reserva.id, tenant_id=tenant_id
                ):
                    raise CertificadoJaEmitidoError("reserva de número expirou — reenvie")
                cert = emitir_certificado(
                    ctx.inp, cert_repo=cert_repo,
                    analise_repo=DjangoAnaliseReconciliacaoRepository(),
                )
                pontos_snap = cert_repo.listar_pontos(certificado_id=cert.id)
                body = serializar_certificado_leitura(cert, pontos_snap)
                _publicar_evento_cert(
                    payload=body, causation_id=chave_id, tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"certificado {cert.numero_certificado} v{cert.versao}",
                )
        except CertificadoJaEmitidoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except _ERROS_422 as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED, response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST reemitir
    @action(detail=True, methods=["post"], url_path="reemitir")
    def reemitir(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-CER-004 reemissão versionada. # idempotency-key: required"""
        s = ReemitirCertificadoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, perfil, usuario_id, erro = self._contexto_com_perfil()
        if erro is not None:
            return erro
        cert_anterior_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request, tenant_id=tenant_id, usuario_id=usuario_id, endpoint=ENDPOINT_REEMITIR,
            payload_fingerprint={
                "certificado_anterior_id": str(cert_anterior_id),
                "correlation_id": str(d["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        tenant = Tenant.objects.filter(id=tenant_id).first()
        if tenant is None:
            return self._falha(chave_id, tenant_id, NotFound("tenant"), status.HTTP_403_FORBIDDEN)
        cert_repo = DjangoCertificadoRepository()
        v_n = cert_repo.obter_por_id(cert_anterior_id)
        if v_n is None or v_n.tenant_id != tenant_id:
            return self._falha(
                chave_id, tenant_id, NotFound(f"certificado {cert_anterior_id}"),
                status.HTTP_404_NOT_FOUND,
            )
        override_padroes = d["snapshot_padroes_usados_json"]
        try:
            cal = DjangoCalibracaoRepository().obter_por_id(v_n.calibracao_id)
            if cal is None:
                return self._falha(
                    chave_id, tenant_id, NotFound(f"calibração {v_n.calibracao_id}"),
                    status.HTTP_404_NOT_FOUND,
                )
            data_emissao = d["data_emissao"] or datetime.now(UTC).date()
            ctx = self._montar_contexto_emissao(
                tenant=tenant, perfil=perfil, calibracao=cal,
                calibracao_id=v_n.calibracao_id, data_emissao=data_emissao,
                correlation_id=d["correlation_id"], snapshot_padroes=[], cert_repo=cert_repo,
            )
            with transaction.atomic():
                # TL-A1: advisory lock ANTES de ler o revision (fecha TOCTOU).
                _advisory_lock_cert(tenant_id=tenant_id, calibracao_id=v_n.calibracao_id)
                revision = cert_repo.obter_revision_para_cas(
                    tenant_id=tenant_id, certificado_id=cert_anterior_id
                )
                if revision is None:
                    raise ReemissaoConflitanteError(
                        f"certificado {cert_anterior_id} não está EMITIDO "
                        f"(já substituído/revogado)"
                    )
                if not ctx.num_repo.confirmar_numero(
                    reserva_id=ctx.reserva.id, tenant_id=tenant_id
                ):
                    raise CertificadoJaEmitidoError("reserva de número expirou — reenvie")
                inp = ReemitirCertificadoInput(
                    tenant_id=tenant_id, certificado_anterior=v_n, revision_anterior=revision,
                    motivo=d["motivo"], calibracao=cal,
                    pontos_medidos=ctx.inp.pontos_medidos,
                    orcamentos_por_ponto=ctx.inp.orcamentos_por_ponto, perfil=perfil,
                    numero_interno=ctx.inp.numero_interno,
                    numero_certificado=ctx.inp.numero_certificado,
                    data_emissao=data_emissao, emitido_em=ctx.inp.emitido_em,
                    correlation_id=d["correlation_id"], cmc_para=ctx.inp.cmc_para,
                    acreditacao_vigencia_fim=ctx.inp.acreditacao_vigencia_fim,
                    acreditacao_suspensa_em=ctx.inp.acreditacao_suspensa_em,
                    acreditacao_suspensa_ate=ctx.inp.acreditacao_suspensa_ate,
                    snapshot_padroes_usados_json=(override_padroes or None),
                )
                nova = reemitir_certificado(
                    inp, cert_repo=cert_repo,
                    analise_repo=DjangoAnaliseReconciliacaoRepository(),
                )
                pontos_snap = cert_repo.listar_pontos(certificado_id=nova.id)
                body = serializar_certificado_leitura(nova, pontos_snap)
                _publicar_evento_cert(
                    payload=body, causation_id=chave_id, tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"reemissao {nova.numero_certificado} v{nova.versao}",
                )
        except (CertificadoJaEmitidoError, ReemissaoConflitanteError) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except _ERROS_422 as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED, response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- helpers
    def _montar_contexto_emissao(
        self, *, tenant: Tenant, perfil: str, calibracao: CalibracaoSnapshot,
        calibracao_id: UUID, data_emissao: date, correlation_id: UUID,
        snapshot_padroes: list[dict[str, Any]], cert_repo: DjangoCertificadoRepository,
    ) -> _CtxEmissao:
        """Monta o Input da emissão a partir do estado persistido + server-side. Lê
        pontos/orçamentos (adapters B), injeta `cmc_para` SÓ em perfil A (o use case
        rebaixa por vencimento/suspensão), reserva o número visível. Vigência/suspensão
        vêm do Tenant (nunca body — defesa L6)."""
        tenant_id = tenant.id
        pontos = query_service.listar_pontos_medidos(
            tenant_id=tenant_id, calibracao_id=calibracao_id
        )
        orcs = query_service.listar_orcamentos_por_ponto(
            tenant_id=tenant_id, calibracao_id=calibracao_id
        )
        cmc = query_service.cmc_para_adapter if perfil_e_acreditado(perfil) else None
        numero_interno = cert_repo.proximo_numero_interno(tenant_id=tenant_id)
        num_repo = DjangoNumeracaoCertificadoRepository()
        reserva = num_repo.reservar_numero(
            tenant_id=tenant_id, tenant_slug=tenant.slug, ano=data_emissao.year,
            correlation_id=correlation_id,
        )
        inp = EmitirCertificadoInput(
            tenant_id=tenant_id, calibracao=calibracao, pontos_medidos=pontos,
            orcamentos_por_ponto=orcs, perfil=perfil, numero_interno=numero_interno,
            numero_certificado=reserva.numero_certificado,
            snapshot_padroes_usados_json=snapshot_padroes, data_emissao=data_emissao,
            emitido_em=datetime.now(UTC), correlation_id=correlation_id, cmc_para=cmc,
            acreditacao_vigencia_fim=tenant.acreditacao_vigencia_fim,
            acreditacao_suspensa_em=tenant.acreditacao_suspensa_em,
            acreditacao_suspensa_ate=tenant.acreditacao_suspensa_ate,
        )
        return _CtxEmissao(inp=inp, num_repo=num_repo, reserva=reserva)

    def _contexto(self) -> tuple[Any, Any, Response | None]:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return None, None, Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        return tenant_id, usuario_id, None

    def _contexto_com_perfil(self) -> tuple[Any, Any, Any, Response | None]:
        from src.infrastructure.authz.perfil_tenant_helper import (
            obter_perfil_tenant_corrente,
        )

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return None, None, None, Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        perfil = obter_perfil_tenant_corrente()
        if not perfil:
            return None, None, None, Response(
                {"erro": "perfil regulatório indisponível (fail-closed ADR-0067)"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)
        return tenant_id, perfil, usuario_id, None

    @staticmethod
    def _uuid_ou_404(raw: str | None) -> UUID:
        try:
            return UUID(str(raw))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"id inválido: {exc}") from exc

    @staticmethod
    def _falha(chave_id: UUID, tenant_id: UUID, exc: Exception, http_status: int) -> Response:
        falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=http_status)
        return Response({"erro": str(exc)}, status=http_status)
