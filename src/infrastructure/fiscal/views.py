"""NotaFiscalServicoViewSet — REST da frente fiscal/NFS-e (T-FIS-032).

Actions:
  GET  /api/v1/fiscal/nfse/{id}/             retrieve
  POST /api/v1/fiscal/nfse/emitir/           emitir   (US-FIS-001)
  POST /api/v1/fiscal/nfse/{id}/cancelar/    cancelar (US-FIS-003)
  POST /api/v1/fiscal/nfse/{id}/consultar/   consultar (resolve PENDING)

Autorização: RequireAuthz (DEFAULT_PERMISSION_CLASSES) + ACTION_MAP. Idempotency-Key
nos POST de emissão/cancelamento (IDEMP-001). Perfil regulatório server-side
(ADR-0067/INV-FIS-001 — nunca payload); `tipo_acreditacao` do vínculo resolvido
server-side do certificado (INV-FIS-002 — nunca payload). A trava de perfil roda no
USE CASE (ADR-0073/D-FIS-5). Evento `fiscal.nfse_emitida` vai ao outbox (consumer
contas-receber previsto — D-FIS-9). `network_timeout` do provider → 503 sem
persistir (D-FIS-3).

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from django.conf import settings
from django.db import connection, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.fiscal import cancelar_nfse, consultar_status_nfse, emitir_nfse
from src.domain.fiscal.enums import PerfilRegulatorio, TipoServico
from src.domain.fiscal.erros import (
    DocIncompativelComPerfilError,
    DocMetrologicoObrigatorioError,
    MotivoCancelamentoInvalidoError,
    ProviderTimeoutError,
    TransicaoInvalidaError,
)
from src.domain.fiscal.mock_provider import MockFiscalProvider, ModoMock
from src.domain.fiscal.portas import FiscalProvider
from src.infrastructure.authz.perfil_tenant_helper import obter_perfil_tenant_corrente
from src.infrastructure.fiscal.repositories import DjangoNotaFiscalServicoRepository
from src.infrastructure.fiscal.serializers import (
    CancelarNfseSerializer,
    EmitirNfseSerializer,
)
from src.infrastructure.fiscal.vinculo_metrologico import ler_tipo_acreditacao
from src.infrastructure.idempotencia.services_idempotencia import (
    ErroValidacao,
    NovoProcessamento,
    Replay,
    avaliar_chave_idempotencia,
    concluir_chave,
    falhar_chave,
)
from src.infrastructure.multitenant.context import (
    active_tenant_context,
    usuario_id_context,
)

logger = logging.getLogger(__name__)

ENDPOINT_EMITIR = "fiscal.emitir"
ENDPOINT_CANCELAR = "fiscal.cancelar"


def _obter_provider() -> FiscalProvider:
    """Provider injetado. No núcleo = `MockFiscalProvider` (modo via settings —
    adapters reais PlugNotas/Focus são GATE pré-produção). O circuit breaker
    (diferido) seria um wrapper de infra; o use case é agnóstico (D-FIS-8)."""
    modo = getattr(settings, "FISCAL_PROVIDER_MOCK_MODO", ModoMock.ALWAYS_AUTHORIZE.value)
    return MockFiscalProvider(ModoMock(modo))


def _tenant_ou_none() -> UUID | None:
    return active_tenant_context.get()


def _serializar_nota(n: Any) -> dict[str, Any]:
    return {
        "nfse_id": str(n.nfse_id),
        "origem_id": str(n.origem_id),
        "versao": n.versao,
        "status": n.status.value,
        "tipo_servico": n.tipo_servico.value,
        "perfil_no_evento": n.perfil_no_evento.value,
        "valor_centavos": n.valor_centavos,
        "provider_invoice_id": n.provider_invoice_id,
        "certificado_id": str(n.certificado_id) if n.certificado_id else None,
        "declaracao_id": str(n.declaracao_id) if n.declaracao_id else None,
        "tipo_acreditacao_vinculo": (
            n.tipo_acreditacao_vinculo.value if n.tipo_acreditacao_vinculo else None
        ),
        "snapshot_hash": n.snapshot_hash,
        "emitido_em": n.emitido_em.isoformat() if n.emitido_em else None,
        "cancelado_em": n.cancelado_em.isoformat() if n.cancelado_em else None,
    }


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


def _publicar_evento_fiscal(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    usuario_id: UUID,
    resource_summary: str,
) -> None:
    """Evento na cadeia hash + outbox (D-FIS-9 — `fiscal.nfse_emitida` tem consumer
    contas-receber previsto). Import local (molde escopos_cmc)."""
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
        "fiscal evento WORM publicado",
        extra={"tenant_id": str(tenant_id), "acao": acao,
               "correlation_id": str(payload.get("correlation_id", ""))},
    )


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class NotaFiscalServicoViewSet(viewsets.ViewSet):
    """ViewSet REST de NotaFiscalServico (emitir/cancelar/consultar/retrieve)."""

    authz_purpose = "execucao_contrato"
    ACTION_MAP = {
        "retrieve": "fiscal.ver",
        "emitir": "fiscal.emitir",
        "cancelar": "fiscal.cancelar",
        "consultar": "fiscal.consultar",
    }

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    # ---------------------------------------------------------------- GET
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        repo = DjangoNotaFiscalServicoRepository()
        nota = repo.obter_por_id(tenant_id=tenant_id, nfse_id=self._uuid_ou_404(pk))
        if nota is None:
            raise NotFound(f"NFS-e {pk} não encontrada")
        return Response(_serializar_nota(nota))

    # ---------------------------------------------------------------- POST emitir
    @action(detail=False, methods=["post"], url_path="emitir")
    def emitir(self, request: Request) -> Response:
        """POST — US-FIS-001. # idempotency-key: required"""
        s = EmitirNfseSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        perfil_str = obter_perfil_tenant_corrente()
        if not perfil_str:
            return Response(
                {"erro": "perfil regulatório indisponível (fail-closed ADR-0067)"},
                status=status.HTTP_403_FORBIDDEN,
            )
        perfil = PerfilRegulatorio(perfil_str)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        # Vínculo metrológico resolvido SERVER-SIDE do certificado (INV-FIS-002).
        certificado_id = d.get("certificado_id")
        vinculo = (
            ler_tipo_acreditacao(tenant_id=tenant_id, certificado_id=certificado_id)
            if certificado_id
            else None
        )

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_EMITIR,
            payload_fingerprint={
                "origem_id": str(d["origem_id"]),
                "correlation_id": str(d["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoNotaFiscalServicoRepository()
        provider = _obter_provider()
        try:
            inp = emitir_nfse.EmitirNfseInput(
                tenant_id=tenant_id,
                origem_id=d["origem_id"],
                tipo_servico=TipoServico(d["tipo_servico"]),
                perfil=perfil,
                amount_centavos=d["amount_centavos"],
                issuer_taxid=d["issuer_taxid"],
                customer_taxid=d["customer_taxid"],
                customer_name=d["customer_name"],
                cliente_referencia_hash=d["cliente_referencia_hash"],
                service_description=d["service_description"],
                service_code=d["service_code"],
                issue_date=datetime.now(UTC),
                correlation_id=d["correlation_id"],
                certificado_id=certificado_id,
                declaracao_id=d.get("declaracao_id"),
                tipo_acreditacao_vinculo=vinculo,
            )
            with transaction.atomic():
                # Serializa emissões concorrentes da MESMA origem (IDEMP-FIS-03):
                # a 2ª request bloqueia até a 1ª commitar, então `obter_por_origem`
                # acha a nota existente e devolve 409 — sem 2ª chamada ao provider
                # nem IntegrityError do UNIQUE de negócio. Fecha GATE-IDEMP-FIS-EMITIR-RACE.
                self._advisory_lock_origem(tenant_id, d["origem_id"])
                out = emitir_nfse.executar(inp, provider=provider, repo=repo)
                if not out.ja_existia:
                    _publicar_evento_fiscal(
                        acao="fiscal.nfse_emitida",
                        payload={
                            "nfse_id": str(out.nota.nfse_id),
                            "origem_id": str(out.nota.origem_id),
                            "tipo_servico": out.nota.tipo_servico.value,
                            "valor_centavos": out.nota.valor_centavos,
                            "perfil_no_evento": out.nota.perfil_no_evento.value,
                            "cliente_referencia_hash": out.nota.cliente_referencia_hash,
                            "status": out.nota.status.value,
                            "correlation_id": str(d["correlation_id"]),
                        },
                        causation_id=chave_id,
                        tenant_id=tenant_id,
                        usuario_id=usuario_id,
                        resource_summary=f"nfse {out.nota.origem_id} {out.nota.status.value}",
                    )
        except DocIncompativelComPerfilError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_403_FORBIDDEN)
        except DocMetrologicoObrigatorioError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ProviderTimeoutError as exc:
            # Transporte (D-FIS-3): nada persistido — falha a chave + 503.
            return self._falha(chave_id, tenant_id, exc, status.HTTP_503_SERVICE_UNAVAILABLE)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_nota(out.nota)
        # Dupla emissão da mesma origem (D-FIS-3): 409 retornando a nota existente.
        http_status = status.HTTP_409_CONFLICT if out.ja_existia else status.HTTP_201_CREATED
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=http_status,
            response_body_resumo=body,
        )
        return Response(body, status=http_status)

    # ---------------------------------------------------------------- POST cancelar
    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-FIS-003 (cancelamento <24h). # idempotency-key: required"""
        s = CancelarNfseSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        nfse_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CANCELAR,
            payload_fingerprint={"nfse_id": str(nfse_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoNotaFiscalServicoRepository()
        provider = _obter_provider()
        try:
            inp = cancelar_nfse.CancelarNfseInput(
                tenant_id=tenant_id,
                nfse_id=nfse_id,
                motivo=d["motivo"],
                agora=datetime.now(UTC),
            )
            with transaction.atomic():
                self._advisory_lock(nfse_id)
                nota = cancelar_nfse.executar(inp, provider=provider, repo=repo)
                _publicar_evento_fiscal(
                    acao="fiscal.nfse_cancelada",
                    payload={
                        "nfse_id": str(nota.nfse_id),
                        "origem_id": str(nota.origem_id),
                        "motivo_cancelamento": nota.motivo_cancelamento or "",
                        "correlation_id": str(nota.nfse_id),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"cancela nfse {nota.origem_id}",
                )
        except cancelar_nfse.NotaNaoEncontradaError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except cancelar_nfse.PrazoCancelamentoExpiradoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except (TransicaoInvalidaError, MotivoCancelamentoInvalidoError, ValueError) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_nota(nota)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    # ---------------------------------------------------------------- POST consultar
    @action(detail=True, methods=["post"], url_path="consultar")
    def consultar(self, request: Request, pk: str | None = None) -> Response:
        """POST — resolve PENDING via provider (D-FIS-3).

        # idempotency-key: exempt -- leitura-e-transição idempotente sob advisory
        lock (não CAS); no-op em estado terminal; sem efeito colateral duplicável
        (IDEMP-FIS-02).
        """
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        nfse_id = self._uuid_ou_404(pk)
        repo = DjangoNotaFiscalServicoRepository()
        provider = _obter_provider()
        try:
            inp = consultar_status_nfse.ConsultarStatusInput(
                tenant_id=tenant_id, nfse_id=nfse_id, agora=datetime.now(UTC)
            )
            with transaction.atomic():
                self._advisory_lock(nfse_id)
                nota = consultar_status_nfse.executar(inp, provider=provider, repo=repo)
        except cancelar_nfse.NotaNaoEncontradaError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except TransicaoInvalidaError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(_serializar_nota(nota))

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _advisory_lock(nfse_id: UUID) -> None:
        """Serializa transições concorrentes da mesma nota (cancelar/consultar)."""
        with connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [str(nfse_id)])

    @staticmethod
    def _advisory_lock_origem(tenant_id: UUID, origem_id: UUID) -> None:
        """Serializa emissões concorrentes da mesma origem (IDEMP-FIS-03).

        Namespace próprio (`fiscal:emitir:`) pra não colidir com o lock por nfse_id.
        """
        chave = f"fiscal:emitir:{tenant_id}:{origem_id}"
        with connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [chave])

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
        falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=http_status)
        return Response({"erro": str(exc)}, status=http_status)
