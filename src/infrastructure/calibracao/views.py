"""ViewSets DRF M4 P4 Fase 8 (T-CAL-123..134).

Esqueleto Wave A — cobre apenas CalibracaoViewSet com 3 actions:
  POST /api/v1/calibracoes/recepcionar
  POST /api/v1/calibracoes/{id}/configurar
  POST /api/v1/calibracoes/{id}/cancelar
  GET  /api/v1/calibracoes/{id}/

Outros endpoints (LeituraViewSet, OrcamentoIncertezaViewSet, RevisaoViewSet,
ConferenciaViewSet, NaoConformidadeViewSet, SubcontratacaoViewSet,
ReclamacaoViewSet) seguem mesmo padrao e serao plugados quando
necessario.

Autorizacao: RequireAuthz via DEFAULT_PERMISSION_CLASSES + ACTION_MAP
seguindo M3 OS.

Multi-tenant: tenant_id via active_tenant_context. NUNCA passa em
body ou querystring — RLS bloqueia se contexto ausente.

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP — mesmo
# pattern de ordens_servico/views.py.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.metrologia.calibracao.configurar_calibracao import (
    CalibracaoNaoEncontrada,
    ConfigurarCalibracaoInput,
    ConflitoVersaoCalibracao,
    EstadoInvalidoParaConfigurar,
)
from src.application.metrologia.calibracao.configurar_calibracao import (
    executar as configurar_executar,
)
from src.application.metrologia.calibracao.criar_calibracao import (
    CriarCalibracaoInput,
)
from src.application.metrologia.calibracao.criar_calibracao import (
    executar as criar_executar,
)
from src.domain.metrologia.calibracao.enums import (
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)
from src.infrastructure.calibracao.lgpd import (
    derivar_cliente_key_id,
    derivar_cliente_referencia_hash,
    derivar_hash_texto_canonicalizado,
)
from src.infrastructure.calibracao.repositories import DjangoCalibracaoRepository
from src.infrastructure.calibracao.serializers import (
    CancelarCalibracaoSerializer,
    ConfigurarCalibracaoSerializer,
    RecepcionarCalibracaoSerializer,
)
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

# Endpoints registrados pro service de idempotencia (IDEMP-001 +
# INV-CAL-IDEMP-001 + IDEMP-CAL-01 conserto 2026-05-27).
# String estavel — UNIQUE (tenant_id, endpoint, chave). NUNCA renomear
# sem migration retrofit.
ENDPOINT_CAL_RECEPCIONAR = "calibracao.recepcionar"
ENDPOINT_CAL_CONFIGURAR = "calibracao.configurar"
ENDPOINT_CAL_CANCELAR = "calibracao.cancelar"


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
    """Avalia Idempotency-Key. Retorna (chave_p_concluir, resposta_imediata).

    Padrao identico a `infrastructure/ordens_servico/views.py` (M3 OS).
    Caller usa:
        novo, resp = _aplicar_idempotencia(...)
        if resp is not None: return resp
        # caso novo: executa business + concluir_chave(novo.chave_id, ...)
    """
    chave_header = request.META.get("HTTP_IDEMPOTENCY_KEY")
    avaliacao = avaliar_chave_idempotencia(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        endpoint=endpoint,
        chave_header=chave_header,
        payload=payload_fingerprint,
    )
    if isinstance(avaliacao, ErroValidacao):
        return None, _resposta_erro_idempotencia(avaliacao)
    if isinstance(avaliacao, Replay):
        return None, Response(
            avaliacao.response_body_resumo or {},
            status=avaliacao.response_status,
        )
    assert isinstance(avaliacao, NovoProcessamento)
    return avaliacao, None


def _serializar_snapshot(snapshot: Any) -> dict[str, Any]:
    """Converte CalibracaoSnapshot em dict serializavel (Wave A)."""
    return {
        "id": str(snapshot.id),
        "numero_interno": snapshot.numero_interno,
        "numero_exibido": snapshot.numero_exibido,
        "status": snapshot.status.value,
        "revision": snapshot.revision,
        "tipo_acreditacao": snapshot.tipo_acreditacao.value,
        "criada_em": snapshot.criada_em.isoformat(),
    }


class CalibracaoViewSet(viewsets.ViewSet):
    """ViewSet REST de Calibracao (CRUD + transicoes de estado).

    Endpoints expostos (Wave A esqueleto):
      - retrieve: GET /api/v1/calibracoes/{id}/
      - recepcionar: POST /api/v1/calibracoes/recepcionar/
      - configurar: POST /api/v1/calibracoes/{id}/configurar/
      - cancelar: POST /api/v1/calibracoes/{id}/cancelar/
    """

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        """GET /api/v1/calibracoes/{id}/."""
        repo = DjangoCalibracaoRepository()
        try:
            cal_id = UUID(str(pk))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"id invalido: {exc}") from exc
        snapshot = repo.obter_por_id(cal_id)
        if snapshot is None:
            raise NotFound(f"Calibracao {cal_id} nao encontrada")
        return Response(_serializar_snapshot(snapshot))

    @action(detail=False, methods=["post"], url_path="recepcionar")
    def recepcionar(self, request: Request) -> Response:
        """POST /api/v1/calibracoes/recepcionar/.

        # idempotency-key: required -- IDEMP-001 + INV-CAL-IDEMP-001
        Cria Calibracao em estado RECEPCIONADA (US-CAL-001).
        """
        serializer = RecepcionarCalibracaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return Response(
                {"erro": "tenant_id ausente no contexto"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)

        # SEG-CAL-01: derivar PII server-side (ADR-0032 + ADR-0064).
        cliente_id = dados.get("cliente_id")
        cliente_referencia_hash = derivar_cliente_referencia_hash(
            cliente_id=cliente_id, tenant_id=tenant_id
        )
        cliente_key_id = derivar_cliente_key_id(tenant_id=tenant_id)

        # IDEMP-CAL-01: Idempotency-Key obrigatoria + payload fingerprint.
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CAL_RECEPCIONAR,
            payload_fingerprint={
                "origem_recepcao": dados["origem_recepcao"],
                "atividade_os_id": str(dados.get("atividade_os_id") or ""),
                "instrumento_id": str(dados["instrumento_id"]),
                "cliente_id": str(cliente_id or ""),
                "cliente_referencia_hash": cliente_referencia_hash,
                "tipo_acreditacao": dados["tipo_acreditacao"],
                "correlation_id": str(dados["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None

        repo = DjangoCalibracaoRepository()
        try:
            inp = CriarCalibracaoInput(
                tenant_id=tenant_id,
                origem_recepcao=OrigemRecepcao(dados["origem_recepcao"]),
                atividade_os_id=dados.get("atividade_os_id"),
                instrumento_id=dados["instrumento_id"],
                snapshot_equipamento_json=dados["snapshot_equipamento_json"],
                cliente_id=cliente_id,
                cliente_referencia_hash=cliente_referencia_hash,
                cliente_key_id=cliente_key_id,
                tipo_acreditacao=TipoAcreditacao(dados["tipo_acreditacao"]),
                recepcionada_em=datetime.now(UTC),
                correlation_id=dados["correlation_id"],
            )
        except ValueError as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id,
                response_status=status.HTTP_400_BAD_REQUEST,
            )
            return Response(
                {"erro": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            out = criar_executar(inp, repo)

        body = _serializar_snapshot(out.snapshot)
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="configurar")
    def configurar(self, request: Request, pk: str | None = None) -> Response:
        """POST /api/v1/calibracoes/{id}/configurar/.

        # idempotency-key: required -- IDEMP-001 + INV-CAL-IDEMP-001
        RECEPCIONADA -> CONFIGURADA (US-CAL-002).
        """
        serializer = ConfigurarCalibracaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        try:
            cal_id = UUID(str(pk))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"id invalido: {exc}") from exc

        # SEG-CAL-08: derivar hash server-side a partir do texto inline.
        tenant_id_ctx = active_tenant_context.get()
        if tenant_id_ctx is None:
            return Response(
                {"erro": "tenant_id ausente no contexto"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)
        texto_inline = dados.get("analise_critica_pedido_inline_texto", "") or ""
        analise_inline_hash = (
            derivar_hash_texto_canonicalizado(
                texto=texto_inline, tenant_id=tenant_id_ctx
            )
            if texto_inline
            else ""
        )

        # IDEMP-CAL-01: Idempotency-Key obrigatoria.
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id_ctx,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CAL_CONFIGURAR,
            payload_fingerprint={
                "calibracao_id": str(cal_id),
                "revision_esperada": dados["revision_esperada"],
                "procedimento_id": str(dados["procedimento_id"]),
                "regra_decisao": dados["regra_decisao"],
                "regra_decisao_acordada_documento_id": str(
                    dados["regra_decisao_acordada_documento_id"]
                ),
                "escopo_id": str(dados.get("escopo_id") or ""),
                "analise_critica_pedido_id": str(
                    dados.get("analise_critica_pedido_id") or ""
                ),
                "analise_critica_pedido_inline_hash": analise_inline_hash,
                "capacidade_tecnica_confirmada_por_user_id": str(
                    dados.get("capacidade_tecnica_confirmada_por_user_id") or ""
                ),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None

        repo = DjangoCalibracaoRepository()
        try:
            inp = ConfigurarCalibracaoInput(
                calibracao_id=cal_id,
                revision_esperada=dados["revision_esperada"],
                procedimento_id=dados["procedimento_id"],
                procedimento_versao_snapshot=dados[
                    "procedimento_versao_snapshot"
                ],
                regra_decisao=RegraDecisao(dados["regra_decisao"]),
                regra_decisao_acordada_em=dados["regra_decisao_acordada_em"],
                regra_decisao_acordada_documento_id=dados[
                    "regra_decisao_acordada_documento_id"
                ],
                escopo_id=dados.get("escopo_id"),
                analise_critica_pedido_id=dados.get(
                    "analise_critica_pedido_id"
                ),
                analise_critica_pedido_inline_hash=analise_inline_hash,
                capacidade_tecnica_confirmada_por_user_id=dados.get(
                    "capacidade_tecnica_confirmada_por_user_id"
                ),
            )
        except ValueError as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_400_BAD_REQUEST,
            )
            return Response(
                {"erro": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                out = configurar_executar(inp, repo)
        except CalibracaoNaoEncontrada as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_404_NOT_FOUND,
            )
            raise NotFound(str(exc)) from exc
        except EstadoInvalidoParaConfigurar as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {"erro": str(exc), "codigo": "EstadoInvalido"},
                status=status.HTTP_409_CONFLICT,
            )
        except ConflitoVersaoCalibracao as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {
                    "erro": str(exc),
                    "codigo": "ConflitoVersao",
                    "revision_atual": exc.snapshot_atual.revision,
                },
                status=status.HTTP_409_CONFLICT,
            )

        body = _serializar_snapshot(out.snapshot)
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id_ctx,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body)

    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request: Request, pk: str | None = None) -> Response:
        """POST /api/v1/calibracoes/{id}/cancelar/.

        # idempotency-key: required -- IDEMP-001 + INV-CAL-IDEMP-001
        Wave A esqueleto: use case `cancelar_calibracao` (T-CAL-095) ainda
        nao implementado. Retorna 501 documentando pendencia, MAS ja
        valida Idempotency-Key + payload fingerprint (defesa em
        profundidade quando T-CAL-095 plugar).
        """
        serializer = CancelarCalibracaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        tenant_id_ctx = active_tenant_context.get()
        if tenant_id_ctx is None:
            return Response(
                {"erro": "tenant_id ausente no contexto"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)
        try:
            cal_id = UUID(str(pk))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"id invalido: {exc}") from exc

        # SEG-CAL-07: derivar hash do motivo server-side.
        motivo_hash = derivar_hash_texto_canonicalizado(
            texto=dados["motivo_cancelamento_canonicalizado"],
            tenant_id=tenant_id_ctx,
        )
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id_ctx,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CAL_CANCELAR,
            payload_fingerprint={
                "calibracao_id": str(cal_id),
                "revision_esperada": dados["revision_esperada"],
                "motivo_hash_fingerprint": hashlib.sha256(
                    motivo_hash.encode()
                ).hexdigest(),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None

        # GATE-CAL-CANCELAR-USE-CASE Wave A — T-CAL-095 pendente.
        body = {
            "codigo": "NaoImplementado",
            "detalhe": (
                "Cancelamento de calibracao ainda nao disponivel nesta "
                "versao. Use case sera entregue em Wave A "
                "(GATE-CAL-CANCELAR-USE-CASE)."
            ),
        }
        falhar_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id_ctx,
            response_status=status.HTTP_501_NOT_IMPLEMENTED,
        )
        return Response(body, status=status.HTTP_501_NOT_IMPLEMENTED)
