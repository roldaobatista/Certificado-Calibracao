"""DocumentoRegulatorioViewSet — REST do M9 licencas-acreditacoes (T-LIC-044).

Actions:
  GET  /api/v1/licencas/{id}/                  retrieve (documento + revisões)
  POST /api/v1/licencas/cadastrar/             cadastrar (US-LIC-001, não-promoção)
  POST /api/v1/licencas/promover-perfil-a/     promover (US-LIC-001 AC-4 — D-LIC-4)
  POST /api/v1/licencas/{id}/renovar/          renovar (US-LIC-002/004)
  POST /api/v1/licencas/{id}/acionar-emergencial/  modo emergencial (US-LIC-003)

Perfil regulatório SEMPRE server-side (ADR-0067 — nunca body; defesa L6). `bloqueante`
DERIVADO da fronteira por tipo (D-LIC-5). Idempotency-Key obrigatória nos POST
(IDEMP-001). A promoção é ATÔMICA (cadastro Licenca + `aplicar_evento_cgcre` na mesma
transação — D-LIC-4); a vigência da acreditação é gravada no cache `Tenant.acreditacao_
vigencia_fim` (que o M8 lê — fecha GATE-CER-CGCRE-VIG-DATA-POPULAR).

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from django.db import DatabaseError, transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.metrologia.licencas_acreditacoes.acionar_modo_emergencial import (
    AcionarModoEmergencialInput,
    BloqueioAtivoAusenteError,
)
from src.application.metrologia.licencas_acreditacoes.acionar_modo_emergencial import (
    executar as acionar_executar,
)
from src.application.metrologia.licencas_acreditacoes.cadastrar_documento_regulatorio import (
    CadastrarDocumentoInput,
    DocumentoDuplicadoError,
)
from src.application.metrologia.licencas_acreditacoes.cadastrar_documento_regulatorio import (
    executar as cadastrar_executar,
)
from src.application.metrologia.licencas_acreditacoes.promover_perfil_a import (
    PromoverPerfilAInput,
)
from src.application.metrologia.licencas_acreditacoes.promover_perfil_a import (
    executar as promover_executar,
)
from src.application.metrologia.licencas_acreditacoes.renovar_documento import (
    DocumentoNaoEncontradoError,
    RenovarDocumentoInput,
)
from src.application.metrologia.licencas_acreditacoes.renovar_documento import (
    executar as renovar_executar,
)
from src.domain.metrologia.licencas_acreditacoes.enums import (
    MotivoRevisao,
    TipoDocumentoRegulatorio,
)
from src.domain.metrologia.licencas_acreditacoes.erros import (
    AnexoObrigatorioError,
    LicencaError,
    ModoEmergencialInvalidoError,
    PerfilNaoAutorizaCGCREError,
    VigenciaInvalidaError,
)
from src.infrastructure.idempotencia.services_idempotencia import (
    ErroValidacao,
    NovoProcessamento,
    Replay,
    avaliar_chave_idempotencia,
    concluir_chave,
    falhar_chave,
)
from src.infrastructure.metrologia.licencas_acreditacoes.eventos_cgcre import (
    DjangoAplicarEventoCgcre,
)
from src.infrastructure.metrologia.licencas_acreditacoes.repositories import (
    DjangoAlertaRepository,
    DjangoBloqueioRepository,
    DjangoDocumentoRegulatorioRepository,
    DjangoEventoEmergencialRepository,
    DjangoRevisaoRepository,
)
from src.infrastructure.metrologia.licencas_acreditacoes.serializers import (
    AcionarEmergencialSerializer,
    CadastrarDocumentoSerializer,
    PromoverPerfilASerializer,
    RenovarDocumentoSerializer,
    serializar_documento_leitura,
)
from src.infrastructure.multitenant.context import (
    active_tenant_context,
    usuario_id_context,
)

logger = logging.getLogger(__name__)

ENDPOINT_CADASTRAR = "licencas.cadastrar"
ENDPOINT_PROMOVER = "licencas.promover"
ENDPOINT_RENOVAR = "licencas.renovar"
ENDPOINT_EMERGENCIAL = "licencas.acionar_emergencial"

# Erros de domínio → HTTP.
_ERROS_403 = (PerfilNaoAutorizaCGCREError,)
_ERROS_409 = (DocumentoDuplicadoError, BloqueioAtivoAusenteError)
_ERROS_422 = (
    AnexoObrigatorioError,
    ModoEmergencialInvalidoError,
    VigenciaInvalidaError,
    LicencaError,
)


def _publicar_evento_licenca(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    usuario_id: UUID,
    resource_summary: str,
) -> None:
    """Emite evento na cadeia hash central `auditoria` (molde escopos_cmc/procedimentos)."""
    from src.infrastructure.audit.event_helpers import publicar_evento

    publicar_evento(
        acao=acao,
        payload=payload,
        causation_id=causation_id,
        tenant_id=tenant_id,
        usuario_id=usuario_id if usuario_id != UUID(int=0) else None,
        resource_summary=resource_summary,
    )
    logger.info(
        "licencas evento WORM publicado acao=%s",
        acao,
        extra={
            "tenant_id": str(tenant_id),
            "acao": acao,
            "correlation_id": str(causation_id),
        },
    )


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class DocumentoRegulatorioViewSet(viewsets.ViewSet):
    """ViewSet REST de DocumentoRegulatorio (cadastro + promoção + renovação +
    modo emergencial + leitura)."""

    authz_purpose = "execucao_contrato"
    ACTION_MAP = {
        "retrieve": "licencas.ver",
        "cadastrar": "licencas.cadastrar",
        "promover": "licencas.cadastrar",
        "renovar": "licencas.renovar",
        "acionar_emergencial": "licencas.acionar_emergencial",
    }

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    # ---------------------------------------------------------------- GET retrieve
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        doc_id = self._uuid_ou_404(pk)
        tenant_id, _usuario_id, erro = self._contexto()
        if erro is not None:
            return erro
        doc_repo = DjangoDocumentoRegulatorioRepository()
        doc = doc_repo.obter_por_id(tenant_id=tenant_id, documento_id=doc_id)
        if doc is None:
            raise NotFound(f"Documento regulatório {pk} não encontrado")
        revisoes = DjangoRevisaoRepository().listar_por_documento(
            tenant_id=tenant_id, documento_id=doc_id
        )
        return Response(
            serializar_documento_leitura(
                doc, hoje=timezone.now().date(), revisoes=revisoes
            )
        )

    # ---------------------------------------------------------------- POST cadastrar
    @action(detail=False, methods=["post"], url_path="cadastrar")
    def cadastrar(self, request: Request) -> Response:
        """POST — US-LIC-001 cadastro (não-promoção). # idempotency-key: required"""
        s = CadastrarDocumentoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, perfil, usuario_id, erro = self._contexto_com_perfil()
        if erro is not None:
            return erro

        novo, resp = self._idempotencia(
            request, tenant_id=tenant_id, usuario_id=usuario_id,
            endpoint=ENDPOINT_CADASTRAR,
            payload_fingerprint={
                "tipo": d["tipo"], "numero": d["numero"],
                "orgao_emissor": d["orgao_emissor"],
                "correlation_id": str(d["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = CadastrarDocumentoInput(
                tenant_id=tenant_id,
                tipo=TipoDocumentoRegulatorio(d["tipo"]),
                numero=d["numero"],
                orgao_emissor=d["orgao_emissor"],
                vigencia_inicio=d["vigencia_inicio"],
                vigencia_fim=d["vigencia_fim"],
                perfil=perfil,
                anexo_id=d["anexo_id"],
                anexo_sha256=d["anexo_sha256"],
                criado_por=usuario_id,
                criado_em=datetime.now(UTC),
                correlation_id=d["correlation_id"],
                escopo=d["escopo"],
                numero_cgcre=d["numero_cgcre"],
                ilac_mra_aderido=d["ilac_mra_aderido"],
                titular_referencia_hash=d["titular_referencia_hash"],
                titular_referencia_key_id=d["titular_referencia_key_id"],
                responsavel_id=d["responsavel_id"],
                observacao=d["observacao"],
            )
            with transaction.atomic():
                out = cadastrar_executar(inp, DjangoDocumentoRegulatorioRepository())
                body = serializar_documento_leitura(
                    out.documento, hoje=timezone.now().date()
                )
                _publicar_evento_licenca(
                    acao="licencas.documento_cadastrado", payload=body,
                    causation_id=chave_id, tenant_id=tenant_id, usuario_id=usuario_id,
                    resource_summary=f"documento {out.documento.tipo.value} {out.documento.numero}",
                )
        except _ERROS_403 as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_403_FORBIDDEN)
        except _ERROS_409 as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except _ERROS_422 as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED, response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST promover
    @action(detail=False, methods=["post"], url_path="promover-perfil-a")
    def promover(self, request: Request) -> Response:
        """POST — US-LIC-001 AC-4: cadastra acreditação CGCRE + promove perfil
        atomicamente (D-LIC-4). # idempotency-key: required"""
        s = PromoverPerfilASerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, perfil, usuario_id, erro = self._contexto_com_perfil()
        if erro is not None:
            return erro

        novo, resp = self._idempotencia(
            request, tenant_id=tenant_id, usuario_id=usuario_id,
            endpoint=ENDPOINT_PROMOVER,
            payload_fingerprint={
                "numero": d["numero"], "orgao_emissor": d["orgao_emissor"],
                "perfil_novo": d["perfil_novo"],
                "correlation_id": str(d["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = PromoverPerfilAInput(
                tenant_id=tenant_id,
                perfil_atual=perfil,
                perfil_novo=d["perfil_novo"],
                numero=d["numero"],
                orgao_emissor=d["orgao_emissor"],
                vigencia_inicio=d["vigencia_inicio"],
                vigencia_fim=d["vigencia_fim"],
                escopo=d["escopo"],
                numero_cgcre=d["numero_cgcre"],
                assinatura_a3_id=d["assinatura_a3_id"],
                motivo=d["motivo"],
                criado_por=usuario_id,
                criado_em=datetime.now(UTC),
                correlation_id=d["correlation_id"],
                auditor_cgcre=d["auditor_cgcre"],
                ilac_mra_aderido=d["ilac_mra_aderido"],
                anexo_id=d["anexo_id"],
                anexo_sha256=d["anexo_sha256"],
            )
            with transaction.atomic():
                out = promover_executar(
                    inp,
                    doc_repo=DjangoDocumentoRegulatorioRepository(),
                    aplicar_evento_cgcre=DjangoAplicarEventoCgcre(),
                )
                body = serializar_documento_leitura(
                    out.documento, hoje=timezone.now().date()
                )
                body["promovido"] = out.promovido
                if out.promovido:
                    _publicar_evento_licenca(
                        acao="licencas.documento_cadastrado", payload=body,
                        causation_id=chave_id, tenant_id=tenant_id, usuario_id=usuario_id,
                        resource_summary=(
                            f"acreditacao CGCRE {out.documento.numero} "
                            f"-> perfil {d['perfil_novo']}"
                        ),
                    )
        except _ERROS_403 as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_403_FORBIDDEN)
        except _ERROS_409 as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except _ERROS_422 as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except DatabaseError as exc:
            # `aplicar_evento_cgcre` rejeita transição inválida (não-monotônica, sem A3,
            # sem auditor p/ A) via RAISE EXCEPTION → regra de negócio → 422.
            return self._falha(
                chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED, response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST renovar
    @action(detail=True, methods=["post"], url_path="renovar")
    def renovar(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-LIC-002/004 nova revisão. # idempotency-key: required"""
        s = RenovarDocumentoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        doc_id = self._uuid_ou_404(pk)
        tenant_id, perfil, usuario_id, erro = self._contexto_com_perfil()
        if erro is not None:
            return erro

        novo, resp = self._idempotencia(
            request, tenant_id=tenant_id, usuario_id=usuario_id,
            endpoint=ENDPOINT_RENOVAR,
            payload_fingerprint={
                "documento_id": str(doc_id),
                "nova_vigencia_fim": d["nova_vigencia_fim"].isoformat(),
                "correlation_id": str(d["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = RenovarDocumentoInput(
                tenant_id=tenant_id,
                documento_id=doc_id,
                nova_vigencia_inicio=d["nova_vigencia_inicio"],
                nova_vigencia_fim=d["nova_vigencia_fim"],
                anexo_id=d["anexo_id"],
                anexo_sha256=d["anexo_sha256"],
                motivo=MotivoRevisao(d["motivo"]),
                criado_por=usuario_id,
                criado_em=datetime.now(UTC),
                correlation_id=d["correlation_id"],
                perfil=perfil,
            )
            with transaction.atomic():
                out = renovar_executar(
                    inp,
                    doc_repo=DjangoDocumentoRegulatorioRepository(),
                    revisao_repo=DjangoRevisaoRepository(),
                    bloqueio_repo=DjangoBloqueioRepository(),
                    alerta_repo=DjangoAlertaRepository(),
                    cgcre_sync=DjangoAplicarEventoCgcre(),
                )
                body = {
                    "documento_id": str(doc_id),
                    "numero_revisao": out.revisao.numero_revisao,
                    "nova_vigencia_fim": out.revisao.data_validade.isoformat(),
                    "bloqueios_resolvidos": out.bloqueios_resolvidos,
                    "alertas_cancelados": out.alertas_cancelados,
                }
                _publicar_evento_licenca(
                    acao="licencas.documento_renovado", payload=body,
                    causation_id=chave_id, tenant_id=tenant_id, usuario_id=usuario_id,
                    resource_summary=f"renovacao documento {doc_id} v{out.revisao.numero_revisao}",
                )
        except DocumentoNaoEncontradoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except _ERROS_422 as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except DatabaseError as exc:
            # `aplicar_evento_cgcre(renovacao_vigencia_cgcre)` rejeita estado inválido
            # (tenant não-A, vigência ausente) via RAISE EXCEPTION → regra de negócio → 422.
            return self._falha(
                chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED, response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------- POST acionar-emergencial
    @action(detail=True, methods=["post"], url_path="acionar-emergencial")
    def acionar_emergencial(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-LIC-003 / INV-033 liberação emergencial. # idempotency-key: required"""
        s = AcionarEmergencialSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        doc_id = self._uuid_ou_404(pk)
        tenant_id, _perfil, usuario_id, erro = self._contexto_com_perfil()
        if erro is not None:
            return erro

        novo, resp = self._idempotencia(
            request, tenant_id=tenant_id, usuario_id=usuario_id,
            endpoint=ENDPOINT_EMERGENCIAL,
            payload_fingerprint={
                "documento_id": str(doc_id),
                "operacao": d["operacao_executada"],
                "correlation_id": str(d["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = AcionarModoEmergencialInput(
                tenant_id=tenant_id,
                documento_id=doc_id,
                operacao_executada=d["operacao_executada"],
                justificativa=d["justificativa"],
                admin_id=usuario_id,
                assinatura_a3_id=d["assinatura_a3_id"],
                janela_dias=d["janela_dias"],
                criado_em=datetime.now(UTC),
                correlation_id=d["correlation_id"],
            )
            with transaction.atomic():
                out = acionar_executar(
                    inp,
                    bloqueio_repo=DjangoBloqueioRepository(),
                    evento_repo=DjangoEventoEmergencialRepository(),
                )
                body = {
                    "evento_id": str(out.evento.id),
                    "bloqueio_id": str(out.evento.bloqueio_id),
                    "libera_apenas_nao_rbc": out.evento.libera_apenas_nao_rbc,
                    "expira_em": out.evento.expira_em.isoformat(),
                    "justificativa_hash": out.evento.justificativa_hash,
                }
                _publicar_evento_licenca(
                    acao="licencas.modo_emergencial_acionado", payload=body,
                    causation_id=chave_id, tenant_id=tenant_id, usuario_id=usuario_id,
                    resource_summary=f"emergencial documento {doc_id}",
                )
        except BloqueioAtivoAusenteError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except _ERROS_422 as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED, response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- helpers
    def _idempotencia(
        self, request: Request, *, tenant_id: UUID, usuario_id: UUID,
        endpoint: str, payload_fingerprint: dict[str, Any],
    ) -> tuple[NovoProcessamento | None, Response | None]:
        avaliacao = avaliar_chave_idempotencia(
            tenant_id=tenant_id, usuario_id=usuario_id, endpoint=endpoint,
            chave_header=request.META.get("HTTP_IDEMPOTENCY_KEY"),
            payload=payload_fingerprint,
        )
        if isinstance(avaliacao, ErroValidacao):
            body = {"codigo": avaliacao.codigo, "detalhe": avaliacao.detalhe}
            if avaliacao.headers:
                return None, Response(body, status=avaliacao.http_status, headers=avaliacao.headers)
            return None, Response(body, status=avaliacao.http_status)
        if isinstance(avaliacao, Replay):
            return None, Response(
                avaliacao.response_body_resumo or {}, status=avaliacao.response_status
            )
        assert isinstance(avaliacao, NovoProcessamento)
        return avaliacao, None

    def _contexto(self) -> tuple[Any, Any, Response | None]:
        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return None, None, Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        return tenant_id, usuario_id, None

    def _contexto_com_perfil(self) -> tuple[Any, Any, Any, Response | None]:
        from src.infrastructure.authz.perfil_tenant_helper import (
            obter_perfil_tenant_corrente,
        )

        tenant_id = active_tenant_context.get()
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
    def _falha(
        chave_id: UUID, tenant_id: UUID, exc: Exception, http_status: int
    ) -> Response:
        # OBS-002: bloqueio fail-closed em path crítico carrega trilha estruturada;
        # `chave_id` = Idempotency-Key (correlador único server-side da requisição).
        logger.warning(
            "licencas bloqueio fail-closed codigo=%s status=%s",
            exc.__class__.__name__, http_status,
            extra={
                "tenant_id": str(tenant_id),
                "correlation_id": str(chave_id),
                "codigo": exc.__class__.__name__,
                "http_status": http_status,
            },
        )
        falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=http_status)
        return Response({"erro": str(exc)}, status=http_status)
