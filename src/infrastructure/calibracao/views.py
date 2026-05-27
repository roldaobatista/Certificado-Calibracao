"""ViewSets DRF M4 P4 Fase 8 (T-CAL-123..134 + T-CAL-095).

CalibracaoViewSet — 3 actions production-ready + 1 GET:
  POST /api/v1/calibracoes/recepcionar  (US-CAL-001)
  POST /api/v1/calibracoes/{id}/configurar  (US-CAL-002)
  POST /api/v1/calibracoes/{id}/cancelar  (US-CAL-007 — entregue P5 conserto 2026-05-27)
  GET  /api/v1/calibracoes/{id}/

Todas 3 actions POST emitem `EventoDeCalibracao` WORM no mesmo
`transaction.atomic` (OBS-CAL-01 conserto P5) + exigem `Idempotency-Key`
header (IDEMP-CAL-01 conserto P5) + derivam hashes PII server-side
(SEG-CAL-01/07/08 conserto P5).

Outros endpoints (LeituraViewSet, OrcamentoIncertezaViewSet, RevisaoViewSet,
ConferenciaViewSet, NaoConformidadeViewSet, SubcontratacaoViewSet,
ReclamacaoViewSet) seguem mesmo padrao e serao plugados em Wave A — use cases
puros ja existem em src/application/.../calibracao/.

Autorizacao: RequireAuthz via DEFAULT_PERMISSION_CLASSES + ACTION_MAP
seguindo M3 OS.

Multi-tenant: tenant_id via active_tenant_context. NUNCA passa em
body ou querystring — RLS bloqueia se contexto ausente.

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP — mesmo
# pattern de ordens_servico/views.py.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.metrologia.calibracao.append_evento_calibracao import (
    AppendEventoCalibracaoInput,
)
from src.application.metrologia.calibracao.append_evento_calibracao import (
    executar as append_evento_executar,
)
from src.application.metrologia.calibracao.configurar_calibracao import (
    CalibracaoNaoEncontrada,
    ConfigurarCalibracaoInput,
    ConflitoVersaoCalibracao,
    EstadoInvalidoParaConfigurar,
)
from src.application.metrologia.calibracao.configurar_calibracao import (
    executar as configurar_executar,
)
from src.application.metrologia.calibracao.corrigir_leitura import (
    CalibracaoEstadoNaoPermiteCorrigir,
    CorrigirLeituraInput,
    LeituraNaoEncontrada,
)
from src.application.metrologia.calibracao.corrigir_leitura import (
    executar as corrigir_leitura_executar,
)
from src.application.metrologia.calibracao.criar_calibracao import (
    CriarCalibracaoInput,
)
from src.application.metrologia.calibracao.criar_calibracao import (
    executar as criar_executar,
)
from src.application.metrologia.calibracao.registrar_leitura import (
    ConflitoLeituraExistente,
    EstadoInvalidoParaRegistrarLeitura,
    IdempotencyPayloadMismatch,
    RegistrarLeituraInput,
)
from src.application.metrologia.calibracao.registrar_leitura import (
    executar as registrar_leitura_executar,
)
from src.domain.metrologia.calibracao.entities import OrigemLeitura
from src.domain.metrologia.calibracao.enums import (
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)
from src.infrastructure.calibracao.lgpd import (
    derivar_cliente_key_id,
    derivar_cliente_referencia_hash,
    derivar_hash_texto_canonicalizado,
    derivar_user_id_hash,
)
from src.infrastructure.calibracao.repositories import (
    DjangoCalibracaoRepository,
    DjangoEventoDeCalibracaoRepository,
    DjangoLeituraCorrecaoRepository,
    DjangoLeituraRepository,
)
from src.infrastructure.calibracao.serializers import (
    CancelarCalibracaoSerializer,
    ConfigurarCalibracaoSerializer,
    CorrigirLeituraSerializer,
    RecepcionarCalibracaoSerializer,
    RegistrarLeituraSerializer,
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

logger = logging.getLogger(__name__)

# Endpoints registrados pro service de idempotencia (IDEMP-001 +
# INV-CAL-IDEMP-001 + IDEMP-CAL-01 conserto 2026-05-27).
# String estavel — UNIQUE (tenant_id, endpoint, chave). NUNCA renomear
# sem migration retrofit.
ENDPOINT_CAL_RECEPCIONAR = "calibracao.recepcionar"
ENDPOINT_CAL_CONFIGURAR = "calibracao.configurar"
ENDPOINT_CAL_CANCELAR = "calibracao.cancelar"
ENDPOINT_CAL_REGISTRAR_LEITURA = "calibracao.registrar_leitura"
ENDPOINT_CAL_CORRIGIR_LEITURA = "calibracao.corrigir_leitura"


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
    """Converte CalibracaoSnapshot em dict serializavel (Wave A).

    OBS-CAL-03 conserto P5: inclui `correlation_id` no payload pra rastreio
    cross-request (paralelo M3 OS). Logs estruturados nas actions tambem
    propagam o mesmo correlation_id via `extra=` (OBS-002).
    """
    return {
        "id": str(snapshot.id),
        "numero_interno": snapshot.numero_interno,
        "numero_exibido": snapshot.numero_exibido,
        "status": snapshot.status.value,
        "revision": snapshot.revision,
        "tipo_acreditacao": snapshot.tipo_acreditacao.value,
        "criada_em": snapshot.criada_em.isoformat(),
        "correlation_id": str(snapshot.correlation_id),
    }


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class CalibracaoViewSet(viewsets.ViewSet):
    """ViewSet REST de Calibracao (CRUD + transicoes de estado).

    Endpoints production-ready (3 actions POST + 1 GET):
      - retrieve: GET /api/v1/calibracoes/{id}/
      - recepcionar: POST /api/v1/calibracoes/recepcionar/  (US-CAL-001)
      - configurar: POST /api/v1/calibracoes/{id}/configurar/  (US-CAL-002)
      - cancelar: POST /api/v1/calibracoes/{id}/cancelar/  (US-CAL-007)
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

        evento_repo = DjangoEventoDeCalibracaoRepository()
        with transaction.atomic():
            out = criar_executar(inp, repo)
            # OBS-CAL-01 conserto P5: emite elo WORM da recepcao no mesmo
            # atomic — rollback unificado. Payload sanitizado pelo use case.
            append_evento_executar(
                AppendEventoCalibracaoInput(
                    tenant_id=tenant_id,
                    calibracao_id=out.snapshot.id,
                    tipo="CalibracaoRecepcionada",
                    payload_raw={
                        "numero_interno": out.snapshot.numero_interno,
                        "numero_exibido": out.snapshot.numero_exibido,
                        "origem_recepcao": out.snapshot.origem_recepcao.value,
                        "atividade_os_id": str(
                            out.snapshot.atividade_os_id
                        ) if out.snapshot.atividade_os_id else "",
                        "instrumento_id": str(out.snapshot.instrumento_id),
                        "cliente_referencia_hash": out.snapshot.cliente_referencia_hash,
                        "tipo_acreditacao": out.snapshot.tipo_acreditacao.value,
                        "status": out.snapshot.status.value,
                    },
                    finalidade="recepcao_calibracao",
                    actor_user_id=usuario_id,
                    occurred_at=out.snapshot.criada_em,
                    correlation_id=out.snapshot.correlation_id,
                    causation_id=novo.chave_id,  # type: ignore[arg-type]
                ),
                evento_repo,
            )

        body = _serializar_snapshot(out.snapshot)
        # OBS-CAL-03 conserto P5: log estruturado em endpoint sensivel.
        logger.info(
            "calibracao.recepcionar OK calibracao_id=%s numero=%s",
            out.snapshot.id,
            out.snapshot.numero_exibido,
            extra={
                "tenant_id": str(tenant_id),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_CAL_RECEPCIONAR,
                "calibracao_id": str(out.snapshot.id),
                "usuario_id": str(usuario_id),
            },
        )
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

        evento_repo = DjangoEventoDeCalibracaoRepository()
        try:
            with transaction.atomic():
                out = configurar_executar(inp, repo)
                # OBS-CAL-01: elo WORM da configuracao (cl. 7.2 + ADR-0024).
                append_evento_executar(
                    AppendEventoCalibracaoInput(
                        tenant_id=tenant_id_ctx,
                        calibracao_id=out.snapshot.id,
                        tipo="ConfiguracaoSalva",
                        payload_raw={
                            "calibracao_id": str(out.snapshot.id),
                            "revision": out.snapshot.revision,
                            "procedimento_id": str(
                                out.snapshot.procedimento_id or ""
                            ),
                            "procedimento_versao_snapshot": (
                                out.snapshot.procedimento_versao_snapshot
                            ),
                            "regra_decisao": out.snapshot.regra_decisao.value,
                            "regra_decisao_acordada_em": (
                                out.snapshot.regra_decisao_acordada_em.isoformat()
                                if out.snapshot.regra_decisao_acordada_em
                                else ""
                            ),
                            "escopo_id": str(out.snapshot.escopo_id or ""),
                            "analise_critica_pedido_id": str(
                                out.snapshot.analise_critica_pedido_id or ""
                            ),
                            "analise_critica_pedido_inline_hash": (
                                out.snapshot.analise_critica_pedido_inline_hash
                            ),
                            "status": out.snapshot.status.value,
                        },
                        finalidade="configuracao_calibracao",
                        actor_user_id=usuario_id,
                        occurred_at=datetime.now(UTC),
                        correlation_id=out.snapshot.correlation_id,
                        causation_id=novo.chave_id,  # type: ignore[arg-type]
                    ),
                    evento_repo,
                )
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
        # OBS-CAL-03: log estruturado pos-configurar (cl. 7.2 + ADR-0024).
        logger.info(
            "calibracao.configurar OK calibracao_id=%s revision=%d procedimento_id=%s",
            out.snapshot.id,
            out.snapshot.revision,
            out.snapshot.procedimento_id,
            extra={
                "tenant_id": str(tenant_id_ctx),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_CAL_CONFIGURAR,
                "calibracao_id": str(out.snapshot.id),
                "usuario_id": str(usuario_id),
                "revision": out.snapshot.revision,
            },
        )
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id_ctx,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body)

    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
    # idempotency-key: skip -- _aplicar_idempotencia consome HTTP_IDEMPOTENCY_KEY no corpo
    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request: Request, pk: str | None = None) -> Response:
        """POST /api/v1/calibracoes/{id}/cancelar/.

        US-CAL-007 (T-CAL-095) — production-ready (P5 conserto 2026-05-27).
        Transita qualquer estado nao-terminal -> CANCELADA via CAS (ADR-0065
        INV-CAL-CONC-003). Motivo canonicalizado >= 30 chars; hash derivado
        server-side (SEG-CAL-07). Emite `EventoDeCalibracao(tipo=Cancelada)`
        no mesmo `transaction.atomic` (OBS-CAL-01 conserto P5). Idempotency-Key
        obrigatoria via `_aplicar_idempotencia` (IDEMP-001 + INV-CAL-IDEMP-001).
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

        # PROD-CAL-03 conserto P5: use case `cancelar_calibracao` plugado;
        # emite EventoDeCalibracao(tipo=Cancelada) no mesmo atomic
        # (OBS-CAL-01 conserto P5).
        from src.application.metrologia.calibracao.cancelar_calibracao import (
            CalibracaoNaoEncontrada as CancelarCalNaoEncontrada,
        )
        from src.application.metrologia.calibracao.cancelar_calibracao import (
            CancelarCalibracaoInput,
            ConflitoVersaoCalibracaoCancelar,
            EstadoInvalidoParaCancelar,
        )
        from src.application.metrologia.calibracao.cancelar_calibracao import (
            executar as cancelar_executar,
        )

        repo = DjangoCalibracaoRepository()
        evento_repo = DjangoEventoDeCalibracaoRepository()
        try:
            inp_cancelar = CancelarCalibracaoInput(
                calibracao_id=cal_id,
                revision_esperada=dados["revision_esperada"],
                motivo_cancelamento_hash=motivo_hash,
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
                out_cancelar = cancelar_executar(inp_cancelar, repo)
                append_evento_executar(
                    AppendEventoCalibracaoInput(
                        tenant_id=tenant_id_ctx,
                        calibracao_id=out_cancelar.snapshot.id,
                        tipo="Cancelada",
                        payload_raw={
                            "calibracao_id": str(out_cancelar.snapshot.id),
                            "revision": out_cancelar.snapshot.revision,
                            "motivo_hash": motivo_hash,
                            "status": out_cancelar.snapshot.status.value,
                        },
                        finalidade="cancelamento_calibracao",
                        actor_user_id=usuario_id,
                        occurred_at=datetime.now(UTC),
                        correlation_id=out_cancelar.snapshot.correlation_id,
                        causation_id=novo.chave_id,  # type: ignore[arg-type]
                    ),
                    evento_repo,
                )
        except CancelarCalNaoEncontrada as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_404_NOT_FOUND,
            )
            raise NotFound(str(exc)) from exc
        except EstadoInvalidoParaCancelar as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {"erro": str(exc), "codigo": "EstadoInvalido"},
                status=status.HTTP_409_CONFLICT,
            )
        except ConflitoVersaoCalibracaoCancelar as exc:
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

        body = _serializar_snapshot(out_cancelar.snapshot)
        logger.info(
            "calibracao.cancelar OK calibracao_id=%s revision=%d",
            out_cancelar.snapshot.id,
            out_cancelar.snapshot.revision,
            extra={
                "tenant_id": str(tenant_id_ctx),
                "correlation_id": str(out_cancelar.snapshot.correlation_id),
                "endpoint": ENDPOINT_CAL_CANCELAR,
                "calibracao_id": str(out_cancelar.snapshot.id),
                "usuario_id": str(usuario_id),
                "revision": out_cancelar.snapshot.revision,
            },
        )
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id_ctx,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body)


def _serializar_leitura(snapshot: Any, idempotente: bool = False) -> dict[str, Any]:
    return {
        "id": str(snapshot.id),
        "calibracao_id": str(snapshot.calibracao_id),
        "ponto_calibracao": str(snapshot.ponto_calibracao),
        "numero_repeticao": snapshot.numero_repeticao,
        "valor_lido": str(snapshot.valor_lido),
        "unidade": snapshot.unidade,
        "origem": snapshot.origem.value,
        "timestamp": snapshot.timestamp.isoformat(),
        "correlation_id": str(snapshot.correlation_id),
        "idempotente": idempotente,
    }


def _serializar_leitura_correcao(snapshot: Any) -> dict[str, Any]:
    return {
        "id": str(snapshot.id),
        "leitura_id": str(snapshot.leitura_id),
        "valor_original": str(snapshot.valor_original),
        "valor_corrigido": str(snapshot.valor_corrigido),
        "corrigido_em": snapshot.corrigido_em.isoformat(),
        "correlation_id": str(snapshot.correlation_id),
    }


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class LeituraViewSet(viewsets.ViewSet):
    """ViewSet REST de Leitura (T-CAL-124 — registrar + corrigir).

      POST /api/v1/calibracoes/{calibracao_pk}/registrar-leitura
      POST /api/v1/leituras/{leitura_pk}/corrigir
    """

    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
    # idempotency-key: skip -- _aplicar_idempotencia consome HTTP_IDEMPOTENCY_KEY no corpo
    @action(
        detail=False,
        methods=["post"],
        url_path="calibracoes/(?P<calibracao_pk>[^/.]+)/registrar-leitura",
    )
    def registrar(
        self, request: Request, calibracao_pk: str | None = None
    ) -> Response:
        """POST /api/v1/calibracoes/{calibracao_pk}/registrar-leitura/.

        US-CAL-003. Calibracao precisa estar em EM_EXECUCAO.
        Idempotency-Key obrigatoria + UNIQUE composto (tenant, calibracao,
        ponto, repeticao) garante atomicidade. `client_event_id` opcional
        habilita sync mobile (ADR-0027).
        """
        serializer = RegistrarLeituraSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        try:
            cal_id = UUID(str(calibracao_pk))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"calibracao_id invalido: {exc}") from exc

        tenant_id_ctx = active_tenant_context.get()
        if tenant_id_ctx is None:
            return Response(
                {"erro": "tenant_id ausente no contexto"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)

        # SEG-CAL-09: executor_id_hash server-side a partir do usuario logado.
        executor_id_hash = derivar_user_id_hash(
            usuario_id=usuario_id, tenant_id=tenant_id_ctx
        )

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id_ctx,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CAL_REGISTRAR_LEITURA,
            payload_fingerprint={
                "calibracao_id": str(cal_id),
                "ponto_calibracao": str(dados["ponto_calibracao"]),
                "numero_repeticao": dados["numero_repeticao"],
                "valor_lido": str(dados["valor_lido"]),
                "unidade": dados["unidade"],
                "origem": dados["origem"],
                "client_event_id": str(dados.get("client_event_id") or ""),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None

        cal_repo = DjangoCalibracaoRepository()
        leitura_repo = DjangoLeituraRepository()
        evento_repo = DjangoEventoDeCalibracaoRepository()
        try:
            inp = RegistrarLeituraInput(
                calibracao_id=cal_id,
                ponto_calibracao=dados["ponto_calibracao"],
                numero_repeticao=dados["numero_repeticao"],
                valor_lido=dados["valor_lido"],
                unidade=dados["unidade"],
                origem=OrigemLeitura(dados["origem"]),
                timestamp=dados["timestamp"],
                executor_id_hash=executor_id_hash,
                correlation_id=dados["correlation_id"],
                client_event_id=dados.get("client_event_id"),
            )
        except (TypeError, ValueError) as exc:
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
                out = registrar_leitura_executar(inp, cal_repo, leitura_repo)
                if not out.idempotente:
                    append_evento_executar(
                        AppendEventoCalibracaoInput(
                            tenant_id=tenant_id_ctx,
                            calibracao_id=cal_id,
                            tipo="LeituraRegistrada",
                            payload_raw={
                                "leitura_id": str(out.snapshot.id),
                                "calibracao_id": str(cal_id),
                                "ponto_calibracao": str(
                                    out.snapshot.ponto_calibracao
                                ),
                                "numero_repeticao": out.snapshot.numero_repeticao,
                                "unidade": out.snapshot.unidade,
                                "origem": out.snapshot.origem.value,
                            },
                            finalidade="leitura_registrada",
                            actor_user_id=usuario_id,
                            occurred_at=datetime.now(UTC),
                            correlation_id=out.snapshot.correlation_id,
                            causation_id=novo.chave_id,  # type: ignore[arg-type]
                        ),
                        evento_repo,
                    )
        except CalibracaoNaoEncontrada as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_404_NOT_FOUND,
            )
            raise NotFound(str(exc)) from exc
        except EstadoInvalidoParaRegistrarLeitura as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {"erro": str(exc), "codigo": "EstadoInvalido"},
                status=status.HTTP_409_CONFLICT,
            )
        except ConflitoLeituraExistente as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {
                    "erro": str(exc),
                    "codigo": "LeituraDuplicada",
                    "leitura_id_existente": str(exc.leitura_existente.id),
                },
                status=status.HTTP_409_CONFLICT,
            )
        except IdempotencyPayloadMismatch as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
            return Response(
                {
                    "erro": str(exc),
                    "codigo": "IdempotencyPayloadMismatch",
                    "campos_divergentes": list(exc.campos_divergentes),
                    "leitura_id_existente": str(exc.leitura_existente.id),
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        body = _serializar_leitura(out.snapshot, idempotente=out.idempotente)
        http_status = (
            status.HTTP_200_OK if out.idempotente else status.HTTP_201_CREATED
        )
        logger.info(
            "calibracao.registrar_leitura OK leitura_id=%s calibracao_id=%s idempotente=%s",
            out.snapshot.id,
            cal_id,
            out.idempotente,
            extra={
                "tenant_id": str(tenant_id_ctx),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_CAL_REGISTRAR_LEITURA,
                "calibracao_id": str(cal_id),
                "usuario_id": str(usuario_id),
            },
        )
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id_ctx,
            response_status=http_status,
            response_body_resumo=body,
        )
        return Response(body, status=http_status)

    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
    # idempotency-key: skip -- _aplicar_idempotencia consome HTTP_IDEMPOTENCY_KEY no corpo
    @action(
        detail=False,
        methods=["post"],
        url_path="leituras/(?P<leitura_pk>[^/.]+)/corrigir",
    )
    def corrigir(
        self, request: Request, leitura_pk: str | None = None
    ) -> Response:
        """POST /api/v1/leituras/{leitura_pk}/corrigir/.

        US-CAL-004 / AC-CAL-004-7 — rasura digital cl. 7.5 ISO 17025.
        SEG-CAL-09 + SEG-CAL-08: `razao_correcao_hash` + `corretor_id_hash`
        derivados server-side. Calibracao precisa estar em CONFIGURADA
        ou EM_EXECUCAO.
        """
        serializer = CorrigirLeituraSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        try:
            leitura_id = UUID(str(leitura_pk))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"leitura_id invalido: {exc}") from exc

        tenant_id_ctx = active_tenant_context.get()
        if tenant_id_ctx is None:
            return Response(
                {"erro": "tenant_id ausente no contexto"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)

        razao_hash = derivar_hash_texto_canonicalizado(
            texto=dados["razao_correcao_canonicalizada"],
            tenant_id=tenant_id_ctx,
        )
        corretor_id_hash = derivar_user_id_hash(
            usuario_id=usuario_id, tenant_id=tenant_id_ctx
        )

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id_ctx,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CAL_CORRIGIR_LEITURA,
            payload_fingerprint={
                "leitura_id": str(leitura_id),
                "valor_corrigido": str(dados["valor_corrigido"]),
                "razao_hash_fingerprint": hashlib.sha256(
                    razao_hash.encode()
                ).hexdigest(),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None

        cal_repo = DjangoCalibracaoRepository()
        leitura_repo = DjangoLeituraRepository()
        correcao_repo = DjangoLeituraCorrecaoRepository()
        evento_repo = DjangoEventoDeCalibracaoRepository()

        leitura_atual = leitura_repo.obter_por_id(leitura_id)
        if leitura_atual is None:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_404_NOT_FOUND,
            )
            raise NotFound(f"leitura_id={leitura_id} nao encontrada")
        calibracao_id_leitura = leitura_atual.calibracao_id

        try:
            inp = CorrigirLeituraInput(
                leitura_id=leitura_id,
                valor_corrigido=dados["valor_corrigido"],
                razao_correcao_canonicalizada=dados[
                    "razao_correcao_canonicalizada"
                ],
                razao_correcao_hash=razao_hash,
                corretor_id_hash=corretor_id_hash,
                corrigido_em=dados["corrigido_em"],
                correlation_id=dados["correlation_id"],
            )
        except (TypeError, ValueError) as exc:
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
                out = corrigir_leitura_executar(
                    inp, cal_repo, leitura_repo, correcao_repo
                )
                append_evento_executar(
                    AppendEventoCalibracaoInput(
                        tenant_id=tenant_id_ctx,
                        calibracao_id=calibracao_id_leitura,
                        tipo="LeituraCorrigida",
                        payload_raw={
                            "correcao_id": str(out.snapshot.id),
                            "leitura_id": str(out.snapshot.leitura_id),
                            "valor_original": str(out.snapshot.valor_original),
                            "valor_corrigido": str(
                                out.snapshot.valor_corrigido
                            ),
                            "razao_correcao_hash": (
                                out.snapshot.razao_correcao_hash
                            ),
                        },
                        finalidade="leitura_corrigida",
                        actor_user_id=usuario_id,
                        occurred_at=datetime.now(UTC),
                        correlation_id=out.snapshot.correlation_id,
                        causation_id=novo.chave_id,  # type: ignore[arg-type]
                    ),
                    evento_repo,
                )
        except LeituraNaoEncontrada as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_404_NOT_FOUND,
            )
            raise NotFound(str(exc)) from exc
        except CalibracaoEstadoNaoPermiteCorrigir as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {"erro": str(exc), "codigo": "EstadoInvalido"},
                status=status.HTTP_409_CONFLICT,
            )
        except ValueError as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_400_BAD_REQUEST,
            )
            return Response(
                {"erro": str(exc), "codigo": "RasuraInocua"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        body = _serializar_leitura_correcao(out.snapshot)
        logger.info(
            "calibracao.corrigir_leitura OK correcao_id=%s leitura_id=%s",
            out.snapshot.id,
            out.snapshot.leitura_id,
            extra={
                "tenant_id": str(tenant_id_ctx),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_CAL_CORRIGIR_LEITURA,
                "leitura_id": str(out.snapshot.leitura_id),
                "usuario_id": str(usuario_id),
            },
        )
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id_ctx,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)
