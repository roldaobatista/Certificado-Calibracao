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
from src.application.metrologia.calibracao.aprovar_2a_conferencia import (
    Aprovar2aConferenciaInput,
    EstadoInvalidoParaAprovar2aConferencia,
    Excecao2aConferenciaSemRegistro,
    FraudeConferenteEhRevisorOuExecutor,
)
from src.application.metrologia.calibracao.aprovar_2a_conferencia import (
    executar as aprovar_2a_executar,
)
from src.application.metrologia.calibracao.aprovar_revisao import (
    AprovarRevisaoInput,
    EstadoInvalidoParaAprovarRevisao,
    ExcecaoAdr0026Invalida,
    FraudeRevisorEhExecutor,
)
from src.application.metrologia.calibracao.aprovar_revisao import (
    executar as aprovar_revisao_executar,
)
from src.application.metrologia.calibracao.configurar_calibracao import (
    CalibracaoNaoEncontrada,
    ConfigurarCalibracaoInput,
    ConflitoVersaoCalibracao,
    EscopoNaoCobreFaixa,
    EstadoInvalidoParaConfigurar,
    ProcedimentoVigenteAusente,
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
from src.application.metrologia.calibracao.nao_conformidade import (
    AbrirNCInput,
    ConflitoEstadoNaoConformidade,
    EstadoInvalidoParaTransicao,
    FecharNCInput,
    NaoConformidadeNaoEncontrada,
)
from src.application.metrologia.calibracao.nao_conformidade import (
    abrir as abrir_nc_executar,
)
from src.application.metrologia.calibracao.nao_conformidade import (
    fechar as fechar_nc_executar,
)
from src.application.metrologia.calibracao.reclamacao import (
    AbrirReclamacaoInput,
    AtribuirRTInput,
    ConflitoEstadoReclamacao,
    EstadoInvalidoParaTransicaoReclamacao,
    JanelaCDCExpirada,
    ReclamacaoNaoEncontrada,
    ResponderReclamacaoInput,
    RTNaoIndependenteDaCalibracaoOriginal,
)
from src.application.metrologia.calibracao.reclamacao import (
    abrir as abrir_reclamacao_executar,
)
from src.application.metrologia.calibracao.reclamacao import (
    atribuir_rt as atribuir_rt_executar,
)
from src.application.metrologia.calibracao.reclamacao import (
    responder as responder_reclamacao_executar,
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
from src.application.metrologia.calibracao.rejeitar_revisao import (
    EstadoInvalidoParaRejeitarRevisao,
    RejeitarRevisaoInput,
)
from src.application.metrologia.calibracao.rejeitar_revisao import (
    executar as rejeitar_revisao_executar,
)
from src.domain.metrologia.calibracao.entities import OrigemLeitura
from src.domain.metrologia.calibracao.enums import (
    DecisaoReclamacao,
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
    DjangoNaoConformidadeRepository,
    DjangoReclamacaoCalibracaoRepository,
)
from src.infrastructure.calibracao.serializers import (
    AbrirNCSerializer,
    AbrirReclamacaoSerializer,
    Aprovar2aConferenciaSerializer,
    AprovarRevisaoSerializer,
    AtribuirRTReclamacaoSerializer,
    CancelarCalibracaoSerializer,
    ConfigurarCalibracaoSerializer,
    CorrigirLeituraSerializer,
    FecharNCSerializer,
    RecepcionarCalibracaoSerializer,
    RegistrarLeituraSerializer,
    RejeitarRevisaoSerializer,
    ResponderReclamacaoSerializer,
)
from src.infrastructure.idempotencia.services_idempotencia import (
    ErroValidacao,
    NovoProcessamento,
    Replay,
    avaliar_chave_idempotencia,
    concluir_chave,
    falhar_chave,
)
from src.infrastructure.metrologia.escopos_cmc import (
    query_service as escopos_cmc_qs,
)
from src.infrastructure.metrologia.procedimentos_calibracao import (
    query_service as procedimentos_qs,
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
ENDPOINT_CAL_APROVAR_REVISAO = "calibracao.aprovar_revisao"
ENDPOINT_CAL_REJEITAR_REVISAO = "calibracao.rejeitar_revisao"
ENDPOINT_CAL_APROVAR_2A_CONF = "calibracao.aprovar_2a_conferencia"
ENDPOINT_NC_ABRIR = "calibracao.nc_abrir"
ENDPOINT_NC_FECHAR = "calibracao.nc_fechar"
ENDPOINT_RECL_ABRIR = "calibracao.reclamacao_abrir"
ENDPOINT_RECL_ATRIBUIR_RT = "calibracao.reclamacao_atribuir_rt"
ENDPOINT_RECL_RESPONDER = "calibracao.reclamacao_responder"


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
                # ADR-0076: faixa declarada entra no fingerprint (declaracoes
                # distintas nao sao idempotentes entre si).
                "grandeza_calibrada": dados.get("grandeza_calibrada", "") or "",
                "faixa_calibrada_min": str(dados.get("faixa_calibrada_min") or ""),
                "faixa_calibrada_max": str(dados.get("faixa_calibrada_max") or ""),
                "unidade_calibrada": dados.get("unidade_calibrada", "") or "",
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
                # ADR-0076: faixa calibrada declarada pelo RT (validada no use case).
                grandeza_calibrada=dados.get("grandeza_calibrada", "") or "",
                faixa_calibrada_min=dados.get("faixa_calibrada_min"),
                faixa_calibrada_max=dados.get("faixa_calibrada_max"),
                unidade_calibrada=dados.get("unidade_calibrada", "") or "",
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
                # ADR-0073: portas reais injetadas — escopo CMC (M6) +
                # procedimento vigente (M7). Ordem escopo->procedimento.
                out = configurar_executar(
                    inp,
                    repo,
                    cobertura=escopos_cmc_qs.cobre,
                    procedimento=procedimentos_qs.cobre_procedimento,
                )
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
        except EscopoNaoCobreFaixa as exc:
            # ADR-0073/0074 cond. 1: RBC sem escopo CMC vigente cobrindo a faixa.
            # OBS-002: trilha do bloqueio metrologico (motivo reconstituivel).
            logger.warning(
                "calibracao.configurar BLOQUEADO EscopoNaoCobreFaixa "
                "calibracao_id=%s grandeza=%s motivo=%s",
                cal_id,
                exc.grandeza,
                exc.motivo,
                extra={
                    "tenant_id": str(tenant_id_ctx),
                    "calibracao_id": str(cal_id),
                    "grandeza": exc.grandeza,
                    "faixa_min": exc.faixa_min,
                    "faixa_max": exc.faixa_max,
                    "unidade": exc.unidade,
                    "motivo": exc.motivo,
                    "bloqueio": "EscopoNaoCobreFaixa",
                },
            )
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_412_PRECONDITION_FAILED,
            )
            return Response(
                {
                    "erro": str(exc),
                    "codigo": "EscopoNaoCobreFaixa",
                    "grandeza": exc.grandeza,
                    "faixa_min": exc.faixa_min,
                    "faixa_max": exc.faixa_max,
                    "unidade": exc.unidade,
                    "motivo": exc.motivo,
                },
                status=status.HTTP_412_PRECONDITION_FAILED,
            )
        except ProcedimentoVigenteAusente as exc:
            # M7 cl. 7.2.1: RBC sem procedimento PUBLICADO vigente cobrindo a faixa.
            # OBS-002: trilha do bloqueio metrologico (motivo reconstituivel).
            logger.warning(
                "calibracao.configurar BLOQUEADO ProcedimentoVigenteAusente "
                "calibracao_id=%s grandeza=%s motivo=%s",
                cal_id,
                exc.grandeza,
                exc.motivo,
                extra={
                    "tenant_id": str(tenant_id_ctx),
                    "calibracao_id": str(cal_id),
                    "grandeza": exc.grandeza,
                    "faixa_min": exc.faixa_min,
                    "faixa_max": exc.faixa_max,
                    "unidade": exc.unidade,
                    "motivo": exc.motivo,
                    "bloqueio": "ProcedimentoVigenteAusente",
                },
            )
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_412_PRECONDITION_FAILED,
            )
            return Response(
                {
                    "erro": str(exc),
                    "codigo": "ProcedimentoVigenteAusente",
                    "grandeza": exc.grandeza,
                    "faixa_min": exc.faixa_min,
                    "faixa_max": exc.faixa_max,
                    "unidade": exc.unidade,
                    "motivo": exc.motivo,
                },
                status=status.HTTP_412_PRECONDITION_FAILED,
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


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class RevisaoViewSet(viewsets.ViewSet):
    """ViewSet REST de Revisao (T-CAL-126 — aprovar + rejeitar).

      POST /api/v1/calibracoes/{id}/aprovar-revisao   (US-CAL-007)
      POST /api/v1/calibracoes/{id}/rejeitar-revisao  (US-CAL-007 caminho B)
    """

    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
    # idempotency-key: skip -- _aplicar_idempotencia consome HTTP_IDEMPOTENCY_KEY no corpo
    @action(
        detail=False,
        methods=["post"],
        url_path="calibracoes/(?P<calibracao_pk>[^/.]+)/aprovar-revisao",
    )
    def aprovar(
        self, request: Request, calibracao_pk: str | None = None
    ) -> Response:
        """EM_REVISAO_1 -> AGUARDANDO_2A_CONFERENCIA.

        SEG-CAL-09: revisor_id derivado do usuario logado.
        SEG-CAL-10 (GATE Wave A): snapshot_competencia_revisor_json
        ainda aceito no body; deve passar a ser derivado server-side
        de RTCompetencia quando GATE-CAL-10 fechar.
        """
        serializer = AprovarRevisaoSerializer(data=request.data)
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
        revisor_id = usuario_id  # SEG-CAL-09 server-side

        snap_competencia = dict(dados["snapshot_competencia_revisor_json"])
        # Fingerprint estavel (chaves ordenadas) — INV-DOC-CANON-001 lite.
        snap_fp = hashlib.sha256(
            "|".join(
                f"{k}={snap_competencia[k]}" for k in sorted(snap_competencia)
            ).encode()
        ).hexdigest()

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id_ctx,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CAL_APROVAR_REVISAO,
            payload_fingerprint={
                "calibracao_id": str(cal_id),
                "revision_esperada": dados["revision_esperada"],
                "revisor_id": str(revisor_id),
                "snap_competencia_fp": snap_fp,
                "excecao_motivo": dados.get("excecao_motivo") or "",
            },
        )
        if resp is not None:
            return resp
        assert novo is not None

        repo = DjangoCalibracaoRepository()
        evento_repo = DjangoEventoDeCalibracaoRepository()
        try:
            inp = AprovarRevisaoInput(
                calibracao_id=cal_id,
                revision_esperada=dados["revision_esperada"],
                revisor_id=revisor_id,
                snapshot_competencia_revisor_json=snap_competencia,
                excecao_motivo=dados.get("excecao_motivo"),
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
                out = aprovar_revisao_executar(inp, repo)
                append_evento_executar(
                    AppendEventoCalibracaoInput(
                        tenant_id=tenant_id_ctx,
                        calibracao_id=cal_id,
                        tipo="revisao_aprovada",
                        payload_raw={
                            "calibracao_id": str(cal_id),
                            "revision": out.snapshot.revision,
                            "status": out.snapshot.status.value,
                            "snap_competencia_fp": snap_fp,
                            "excecao_motivo": dados.get("excecao_motivo")
                            or "",
                        },
                        finalidade="revisao_aprovada",
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
        except EstadoInvalidoParaAprovarRevisao as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {"erro": str(exc), "codigo": "EstadoInvalido"},
                status=status.HTTP_409_CONFLICT,
            )
        except FraudeRevisorEhExecutor as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
            return Response(
                {"erro": str(exc), "codigo": "RTSemSegregacao"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except ExcecaoAdr0026Invalida as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
            return Response(
                {"erro": str(exc), "codigo": "ExcecaoAdr0026Invalida"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
        logger.info(
            "calibracao.aprovar_revisao OK calibracao_id=%s revision=%d",
            cal_id,
            out.snapshot.revision,
            extra={
                "tenant_id": str(tenant_id_ctx),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_CAL_APROVAR_REVISAO,
                "calibracao_id": str(cal_id),
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
    @action(
        detail=False,
        methods=["post"],
        url_path="calibracoes/(?P<calibracao_pk>[^/.]+)/rejeitar-revisao",
    )
    def rejeitar(
        self, request: Request, calibracao_pk: str | None = None
    ) -> Response:
        """EM_REVISAO_1 -> EM_EXECUCAO (devolve pro metrologista corrigir)."""
        serializer = RejeitarRevisaoSerializer(data=request.data)
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

        # SEG-CAL-07 style: hash do motivo derivado server-side pra fingerprint.
        motivo_hash = derivar_hash_texto_canonicalizado(
            texto=dados["motivo_rejeicao_canonicalizado"],
            tenant_id=tenant_id_ctx,
        )

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id_ctx,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CAL_REJEITAR_REVISAO,
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

        repo = DjangoCalibracaoRepository()
        evento_repo = DjangoEventoDeCalibracaoRepository()
        try:
            inp = RejeitarRevisaoInput(
                calibracao_id=cal_id,
                revision_esperada=dados["revision_esperada"],
                motivo_rejeicao_canonicalizado=dados[
                    "motivo_rejeicao_canonicalizado"
                ],
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
                out = rejeitar_revisao_executar(inp, repo)
                append_evento_executar(
                    AppendEventoCalibracaoInput(
                        tenant_id=tenant_id_ctx,
                        calibracao_id=cal_id,
                        tipo="revisao_rejeitada",
                        payload_raw={
                            "calibracao_id": str(cal_id),
                            "revision": out.snapshot.revision,
                            "status": out.snapshot.status.value,
                            "motivo_hash": motivo_hash,
                        },
                        finalidade="revisao_rejeitada",
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
        except EstadoInvalidoParaRejeitarRevisao as exc:
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
        logger.info(
            "calibracao.rejeitar_revisao OK calibracao_id=%s revision=%d",
            cal_id,
            out.snapshot.revision,
            extra={
                "tenant_id": str(tenant_id_ctx),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_CAL_REJEITAR_REVISAO,
                "calibracao_id": str(cal_id),
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
class ConferenciaViewSet(viewsets.ViewSet):
    """ViewSet REST de 2a Conferencia (T-CAL-127 — aprovar).

      POST /api/v1/calibracoes/{id}/aprovar-2a-conferencia  (US-CAL-008)
    """

    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
    # idempotency-key: skip -- _aplicar_idempotencia consome HTTP_IDEMPOTENCY_KEY no corpo
    @action(
        detail=False,
        methods=["post"],
        url_path="calibracoes/(?P<calibracao_pk>[^/.]+)/aprovar-2a-conferencia",
    )
    def aprovar_2a(
        self, request: Request, calibracao_pk: str | None = None
    ) -> Response:
        """AGUARDANDO_2A_CONFERENCIA -> APROVADA. US-CAL-008 + ADR-0026."""
        serializer = Aprovar2aConferenciaSerializer(data=request.data)
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
        conferente_id = usuario_id  # SEG-CAL-09 server-side

        snap_competencia = dict(dados["snapshot_competencia_conferente_json"])
        snap_fp = hashlib.sha256(
            "|".join(
                f"{k}={snap_competencia[k]}" for k in sorted(snap_competencia)
            ).encode()
        ).hexdigest()

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id_ctx,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CAL_APROVAR_2A_CONF,
            payload_fingerprint={
                "calibracao_id": str(cal_id),
                "revision_esperada": dados["revision_esperada"],
                "conferente_id": str(conferente_id),
                "snap_competencia_fp": snap_fp,
                "excecao_motivo": dados.get("excecao_motivo") or "",
                "excecao_2a_conf_id": str(
                    dados.get("excecao_2a_conf_id") or ""
                ),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None

        repo = DjangoCalibracaoRepository()
        evento_repo = DjangoEventoDeCalibracaoRepository()
        try:
            inp = Aprovar2aConferenciaInput(
                calibracao_id=cal_id,
                revision_esperada=dados["revision_esperada"],
                conferente_id=conferente_id,
                snapshot_competencia_conferente_json=snap_competencia,
                excecao_motivo=dados.get("excecao_motivo"),
                excecao_2a_conf_id=dados.get("excecao_2a_conf_id"),
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
                out = aprovar_2a_executar(inp, repo)
                append_evento_executar(
                    AppendEventoCalibracaoInput(
                        tenant_id=tenant_id_ctx,
                        calibracao_id=cal_id,
                        tipo="segunda_conferencia_aprovada",
                        payload_raw={
                            "calibracao_id": str(cal_id),
                            "revision": out.snapshot.revision,
                            "status": out.snapshot.status.value,
                            "snap_competencia_fp": snap_fp,
                            "excecao_motivo": dados.get("excecao_motivo")
                            or "",
                            "excecao_2a_conf_id": str(
                                dados.get("excecao_2a_conf_id") or ""
                            ),
                        },
                        finalidade="segunda_conferencia_aprovada",
                        actor_user_id=usuario_id,
                        occurred_at=datetime.now(UTC),
                        correlation_id=out.snapshot.correlation_id,
                        causation_id=novo.chave_id,  # type: ignore[arg-type]
                    ),
                    evento_repo,
                )
                # Saga happy path: 2a conferencia aprovada eleva
                # status pra APROVADA. Emite tambem `calibracao_aprovada`
                # pro bus (Marco 5 certificados consome — INT-02).
                append_evento_executar(
                    AppendEventoCalibracaoInput(
                        tenant_id=tenant_id_ctx,
                        calibracao_id=cal_id,
                        tipo="calibracao_aprovada",
                        payload_raw={
                            "calibracao_id": str(cal_id),
                            "revision": out.snapshot.revision,
                            "status": out.snapshot.status.value,
                        },
                        finalidade="calibracao_aprovada",
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
        except EstadoInvalidoParaAprovar2aConferencia as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {"erro": str(exc), "codigo": "EstadoInvalido"},
                status=status.HTTP_409_CONFLICT,
            )
        except FraudeConferenteEhRevisorOuExecutor as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
            return Response(
                {"erro": str(exc), "codigo": "RTSemSegregacao"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except Excecao2aConferenciaSemRegistro as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
            return Response(
                {"erro": str(exc), "codigo": "Excecao2aSemRegistro"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except ExcecaoAdr0026Invalida as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
            return Response(
                {"erro": str(exc), "codigo": "ExcecaoAdr0026Invalida"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
        logger.info(
            "calibracao.aprovar_2a_conferencia OK calibracao_id=%s revision=%d status=%s",
            cal_id,
            out.snapshot.revision,
            out.snapshot.status.value,
            extra={
                "tenant_id": str(tenant_id_ctx),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_CAL_APROVAR_2A_CONF,
                "calibracao_id": str(cal_id),
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


def _serializar_nc(snapshot: Any) -> dict[str, Any]:
    return {
        "id": str(snapshot.id),
        "calibracao_id": (
            str(snapshot.calibracao_id) if snapshot.calibracao_id else None
        ),
        "origem_proficiencia_id": (
            str(snapshot.origem_proficiencia_id)
            if snapshot.origem_proficiencia_id
            else None
        ),
        "estado": snapshot.estado.value,
        "decisao_continuar_ou_parar": (
            snapshot.decisao_continuar_ou_parar.value
        ),
        "correlation_id": str(snapshot.correlation_id),
    }


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class NaoConformidadeViewSet(viewsets.ViewSet):
    """ViewSet REST de Nao-Conformidade (T-CAL-128 — abrir + fechar).

      POST /api/v1/nao-conformidades/abrir         (US-CAL-013 marcar-nc)
      POST /api/v1/nao-conformidades/{id}/fechar   (US-CAL-014 resolver-nc)

    GAP intermediario (Wave A — GATE-NC-INTERMEDIATE-TRANSITIONS):
    `definir-acao-corretiva` + `executar-acao` + `verificar-eficacia`
    nao expostos via API por enquanto. NC criada via abrir fica em CONTIDA;
    fechar so funciona quando NC ja esta em EFICACIA_VERIFICADA (admin
    pode avancar via shell ate as 3 transicoes intermediarias entrarem).
    """

    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
    # idempotency-key: skip -- _aplicar_idempotencia consome HTTP_IDEMPOTENCY_KEY no corpo
    @action(
        detail=False,
        methods=["post"],
        url_path="nao-conformidades/abrir",
    )
    def abrir(self, request: Request) -> Response:
        """POST /api/v1/nao-conformidades/abrir/.

        US-CAL-013 marcar-nc. Cria NC em estado CONTIDA. Origem XOR:
        exatamente UMA de {calibracao_id, origem_proficiencia_id}.
        """
        serializer = AbrirNCSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        tenant_id_ctx = active_tenant_context.get()
        if tenant_id_ctx is None:
            return Response(
                {"erro": "tenant_id ausente no contexto"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)

        descricao_hash = derivar_hash_texto_canonicalizado(
            texto=dados["descricao_canonicalizada"],
            tenant_id=tenant_id_ctx,
        )
        responsavel_hash = derivar_user_id_hash(
            usuario_id=usuario_id, tenant_id=tenant_id_ctx
        )

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id_ctx,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_NC_ABRIR,
            payload_fingerprint={
                "calibracao_id": str(dados.get("calibracao_id") or ""),
                "origem_proficiencia_id": str(
                    dados.get("origem_proficiencia_id") or ""
                ),
                "descricao_hash_fingerprint": hashlib.sha256(
                    descricao_hash.encode()
                ).hexdigest(),
                "correlation_id": str(dados["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None

        nc_repo = DjangoNaoConformidadeRepository()
        evento_repo = DjangoEventoDeCalibracaoRepository()
        try:
            inp = AbrirNCInput(
                tenant_id=tenant_id_ctx,
                calibracao_id=dados.get("calibracao_id"),
                origem_proficiencia_id=dados.get("origem_proficiencia_id"),
                descricao_canonicalizada=dados["descricao_canonicalizada"],
                descricao_hash=descricao_hash,
                responsavel_acao_user_id=usuario_id,
                responsavel_acao_user_id_hash=responsavel_hash,
                correlation_id=dados["correlation_id"],
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

        with transaction.atomic():
            out = abrir_nc_executar(inp, nc_repo)
            if out.snapshot.calibracao_id is not None:
                append_evento_executar(
                    AppendEventoCalibracaoInput(
                        tenant_id=tenant_id_ctx,
                        calibracao_id=out.snapshot.calibracao_id,
                        tipo="nc_aberta",
                        payload_raw={
                            "nc_id": str(out.snapshot.id),
                            "estado": out.snapshot.estado.value,
                            "descricao_hash": descricao_hash,
                        },
                        finalidade="nc_aberta",
                        actor_user_id=usuario_id,
                        occurred_at=datetime.now(UTC),
                        correlation_id=out.snapshot.correlation_id,
                        causation_id=novo.chave_id,  # type: ignore[arg-type]
                    ),
                    evento_repo,
                )

        body = _serializar_nc(out.snapshot)
        logger.info(
            "calibracao.nc_abrir OK nc_id=%s estado=%s",
            out.snapshot.id,
            out.snapshot.estado.value,
            extra={
                "tenant_id": str(tenant_id_ctx),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_NC_ABRIR,
                "nc_id": str(out.snapshot.id),
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

    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
    # idempotency-key: skip -- _aplicar_idempotencia consome HTTP_IDEMPOTENCY_KEY no corpo
    @action(
        detail=False,
        methods=["post"],
        url_path="nao-conformidades/(?P<nc_pk>[^/.]+)/fechar",
    )
    def fechar(self, request: Request, nc_pk: str | None = None) -> Response:
        """POST /api/v1/nao-conformidades/{id}/fechar/.

        US-CAL-014 resolver-nc. EFICACIA_VERIFICADA -> FECHADA.
        """
        serializer = FecharNCSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)

        try:
            nc_id = UUID(str(nc_pk))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"nc_id invalido: {exc}") from exc

        tenant_id_ctx = active_tenant_context.get()
        if tenant_id_ctx is None:
            return Response(
                {"erro": "tenant_id ausente no contexto"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id_ctx,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_NC_FECHAR,
            payload_fingerprint={"nc_id": str(nc_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None

        nc_repo = DjangoNaoConformidadeRepository()
        evento_repo = DjangoEventoDeCalibracaoRepository()

        try:
            with transaction.atomic():
                out = fechar_nc_executar(FecharNCInput(nc_id=nc_id), nc_repo)
                if out.snapshot.calibracao_id is not None:
                    append_evento_executar(
                        AppendEventoCalibracaoInput(
                            tenant_id=tenant_id_ctx,
                            calibracao_id=out.snapshot.calibracao_id,
                            tipo="nc_resolvida",
                            payload_raw={
                                "nc_id": str(out.snapshot.id),
                                "estado": out.snapshot.estado.value,
                            },
                            finalidade="nc_resolvida",
                            actor_user_id=usuario_id,
                            occurred_at=datetime.now(UTC),
                            correlation_id=out.snapshot.correlation_id,
                            causation_id=novo.chave_id,  # type: ignore[arg-type]
                        ),
                        evento_repo,
                    )
        except NaoConformidadeNaoEncontrada as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_404_NOT_FOUND,
            )
            raise NotFound(str(exc)) from exc
        except EstadoInvalidoParaTransicao as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {"erro": str(exc), "codigo": "EstadoInvalido"},
                status=status.HTTP_409_CONFLICT,
            )
        except ConflitoEstadoNaoConformidade as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {
                    "erro": str(exc),
                    "codigo": "ConflitoEstado",
                    "estado_atual": exc.snapshot_atual.estado.value,
                },
                status=status.HTTP_409_CONFLICT,
            )

        body = _serializar_nc(out.snapshot)
        logger.info(
            "calibracao.nc_fechar OK nc_id=%s estado=%s",
            out.snapshot.id,
            out.snapshot.estado.value,
            extra={
                "tenant_id": str(tenant_id_ctx),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_NC_FECHAR,
                "nc_id": str(out.snapshot.id),
                "usuario_id": str(usuario_id),
            },
        )
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id_ctx,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body)


def _serializar_reclamacao(snapshot: Any) -> dict[str, Any]:
    return {
        "id": str(snapshot.id),
        "calibracao_id": str(snapshot.calibracao_id),
        "certificado_id": str(snapshot.certificado_id),
        "estado": snapshot.estado.value,
        "decisao": snapshot.decisao.value if snapshot.decisao else None,
        "aberta_em": snapshot.aberta_em.isoformat(),
        "respondida_em": (
            snapshot.respondida_em.isoformat()
            if snapshot.respondida_em
            else None
        ),
        "correlation_id": str(snapshot.correlation_id),
    }


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class ReclamacaoViewSet(viewsets.ViewSet):
    """ViewSet REST de ReclamacaoCalibracao (T-CAL-132 — 3 actions).

      POST /api/v1/reclamacoes/abrir                (US-CAL-018-1)
      POST /api/v1/reclamacoes/{id}/atribuir-rt     (US-CAL-018-2)
      POST /api/v1/reclamacoes/{id}/responder       (US-CAL-018-4)

    cl. 7.9 ISO 17025 + CDC art. 26 (janela 90d).
    """

    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
    # idempotency-key: skip -- _aplicar_idempotencia consome HTTP_IDEMPOTENCY_KEY no corpo
    @action(
        detail=False,
        methods=["post"],
        url_path="reclamacoes/abrir",
    )
    def abrir(self, request: Request) -> Response:
        """POST /api/v1/reclamacoes/abrir/."""
        serializer = AbrirReclamacaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        tenant_id_ctx = active_tenant_context.get()
        if tenant_id_ctx is None:
            return Response(
                {"erro": "tenant_id ausente no contexto"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)

        # SEG-CAL-01/08: hashes server-side.
        cliente_referencia_hash = derivar_cliente_referencia_hash(
            cliente_id=dados["cliente_id"], tenant_id=tenant_id_ctx
        )
        relato_hash = derivar_hash_texto_canonicalizado(
            texto=dados["relato_canonicalizado"], tenant_id=tenant_id_ctx
        )

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id_ctx,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_RECL_ABRIR,
            payload_fingerprint={
                "calibracao_id": str(dados["calibracao_id"]),
                "certificado_id": str(dados["certificado_id"]),
                "cliente_referencia_hash": cliente_referencia_hash,
                "relato_hash_fingerprint": hashlib.sha256(
                    relato_hash.encode()
                ).hexdigest(),
                "correlation_id": str(dados["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None

        recl_repo = DjangoReclamacaoCalibracaoRepository()
        evento_repo = DjangoEventoDeCalibracaoRepository()
        try:
            inp = AbrirReclamacaoInput(
                tenant_id=tenant_id_ctx,
                calibracao_id=dados["calibracao_id"],
                certificado_id=dados["certificado_id"],
                cliente_referencia_hash=cliente_referencia_hash,
                relato_canonicalizado=dados["relato_canonicalizado"],
                relato_hash=relato_hash,
                aberta_em=datetime.now(UTC),
                certificado_emitido_em=dados["certificado_emitido_em"],
                prazo_resposta_dia_util=dados["prazo_resposta_dia_util"],
                correlation_id=dados["correlation_id"],
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
                out = abrir_reclamacao_executar(inp, recl_repo)
                append_evento_executar(
                    AppendEventoCalibracaoInput(
                        tenant_id=tenant_id_ctx,
                        calibracao_id=dados["calibracao_id"],
                        tipo="reclamacao_aberta",
                        payload_raw={
                            "reclamacao_id": str(out.snapshot.id),
                            "certificado_id": str(out.snapshot.certificado_id),
                            "cliente_referencia_hash": (
                                cliente_referencia_hash
                            ),
                            "relato_hash": relato_hash,
                            "estado": out.snapshot.estado.value,
                        },
                        finalidade="reclamacao_aberta",
                        actor_user_id=usuario_id,
                        occurred_at=datetime.now(UTC),
                        correlation_id=out.snapshot.correlation_id,
                        causation_id=novo.chave_id,  # type: ignore[arg-type]
                    ),
                    evento_repo,
                )
        except JanelaCDCExpirada as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_410_GONE,
            )
            return Response(
                {"erro": str(exc), "codigo": "JanelaCDCExpirada"},
                status=status.HTTP_410_GONE,
            )

        body = _serializar_reclamacao(out.snapshot)
        logger.info(
            "calibracao.reclamacao_abrir OK reclamacao_id=%s",
            out.snapshot.id,
            extra={
                "tenant_id": str(tenant_id_ctx),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_RECL_ABRIR,
                "reclamacao_id": str(out.snapshot.id),
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

    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
    # idempotency-key: skip -- _aplicar_idempotencia consome HTTP_IDEMPOTENCY_KEY no corpo
    @action(
        detail=False,
        methods=["post"],
        url_path="reclamacoes/(?P<reclamacao_pk>[^/.]+)/atribuir-rt",
    )
    def atribuir_rt(
        self, request: Request, reclamacao_pk: str | None = None
    ) -> Response:
        """RECEBIDA -> EM_ANALISE. AC-CAL-018-2 — RT independente."""
        serializer = AtribuirRTReclamacaoSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        try:
            reclamacao_id = UUID(str(reclamacao_pk))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"reclamacao_id invalido: {exc}") from exc

        tenant_id_ctx = active_tenant_context.get()
        if tenant_id_ctx is None:
            return Response(
                {"erro": "tenant_id ausente no contexto"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)

        recl_repo = DjangoReclamacaoCalibracaoRepository()
        cal_repo = DjangoCalibracaoRepository()

        atual = recl_repo.obter_por_id(reclamacao_id)
        if atual is None:
            raise NotFound(f"reclamacao_id={reclamacao_id} nao encontrada")
        calibracao = cal_repo.obter_por_id(atual.calibracao_id)
        if calibracao is None:
            raise NotFound(
                f"calibracao_id={atual.calibracao_id} nao encontrada"
            )

        # SEG-CAL-09: derivar 3 hashes server-side.
        rt_atribuido_hash = derivar_user_id_hash(
            usuario_id=usuario_id, tenant_id=tenant_id_ctx
        )
        # AC-CAL-018-2: revisor_id/conferente_id sao UUIDs em Calibracao;
        # derivar para hash compativel.
        revisor_original_hash = (
            derivar_user_id_hash(
                usuario_id=calibracao.revisor_id, tenant_id=tenant_id_ctx
            )
            if calibracao.revisor_id is not None
            else ""
        )
        conferente_original_hash = (
            derivar_user_id_hash(
                usuario_id=calibracao.conferente_id, tenant_id=tenant_id_ctx
            )
            if calibracao.conferente_id is not None
            else ""
        )

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id_ctx,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_RECL_ATRIBUIR_RT,
            payload_fingerprint={
                "reclamacao_id": str(reclamacao_id),
                "rt_atribuido_hash": rt_atribuido_hash,
                "permitir_excecao": bool(dados["permitir_mesmo_rt_excecao"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None

        try:
            inp = AtribuirRTInput(
                reclamacao_id=reclamacao_id,
                rt_atribuido_user_id_hash=rt_atribuido_hash,
                revisor_original_id_hash=revisor_original_hash or rt_atribuido_hash,
                conferente_original_id_hash=(
                    conferente_original_hash or rt_atribuido_hash
                ),
                permitir_mesmo_rt_excecao=dados["permitir_mesmo_rt_excecao"],
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
                out = atribuir_rt_executar(inp, recl_repo)
        except ReclamacaoNaoEncontrada as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_404_NOT_FOUND,
            )
            raise NotFound(str(exc)) from exc
        except EstadoInvalidoParaTransicaoReclamacao as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {"erro": str(exc), "codigo": "EstadoInvalido"},
                status=status.HTTP_409_CONFLICT,
            )
        except RTNaoIndependenteDaCalibracaoOriginal as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_412_PRECONDITION_FAILED,
            )
            return Response(
                {"erro": str(exc), "codigo": "RTNaoIndependente"},
                status=status.HTTP_412_PRECONDITION_FAILED,
            )
        except ConflitoEstadoReclamacao as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {
                    "erro": str(exc),
                    "codigo": "ConflitoEstado",
                    "estado_atual": exc.snapshot_atual.estado.value,
                },
                status=status.HTTP_409_CONFLICT,
            )

        body = _serializar_reclamacao(out.snapshot)
        logger.info(
            "calibracao.reclamacao_atribuir_rt OK reclamacao_id=%s",
            out.snapshot.id,
            extra={
                "tenant_id": str(tenant_id_ctx),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_RECL_ATRIBUIR_RT,
                "reclamacao_id": str(out.snapshot.id),
                "usuario_id": str(usuario_id),
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
    @action(
        detail=False,
        methods=["post"],
        url_path="reclamacoes/(?P<reclamacao_pk>[^/.]+)/responder",
    )
    def responder(
        self, request: Request, reclamacao_pk: str | None = None
    ) -> Response:
        """EM_ANALISE -> RESPONDIDA. AC-CAL-018-4: PROCEDENTE_RECALL
        aciona saga M5 via evento `reclamacao_respondida`."""
        serializer = ResponderReclamacaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        try:
            reclamacao_id = UUID(str(reclamacao_pk))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"reclamacao_id invalido: {exc}") from exc

        tenant_id_ctx = active_tenant_context.get()
        if tenant_id_ctx is None:
            return Response(
                {"erro": "tenant_id ausente no contexto"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)

        resposta_hash = derivar_hash_texto_canonicalizado(
            texto=dados["resposta_canonicalizada"], tenant_id=tenant_id_ctx
        )

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id_ctx,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_RECL_RESPONDER,
            payload_fingerprint={
                "reclamacao_id": str(reclamacao_id),
                "decisao": dados["decisao"],
                "resposta_hash_fingerprint": hashlib.sha256(
                    resposta_hash.encode()
                ).hexdigest(),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None

        recl_repo = DjangoReclamacaoCalibracaoRepository()
        evento_repo = DjangoEventoDeCalibracaoRepository()
        try:
            inp = ResponderReclamacaoInput(
                reclamacao_id=reclamacao_id,
                resposta_canonicalizada=dados["resposta_canonicalizada"],
                resposta_hash=resposta_hash,
                decisao=DecisaoReclamacao(dados["decisao"]),
                respondida_em=dados["respondida_em"],
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
                out = responder_reclamacao_executar(inp, recl_repo)
                append_evento_executar(
                    AppendEventoCalibracaoInput(
                        tenant_id=tenant_id_ctx,
                        calibracao_id=out.snapshot.calibracao_id,
                        tipo="reclamacao_respondida",
                        payload_raw={
                            "reclamacao_id": str(out.snapshot.id),
                            "decisao": dados["decisao"],
                            "resposta_hash": resposta_hash,
                            "dispara_recall_m5": out.dispara_recall_m5,
                        },
                        finalidade="reclamacao_respondida",
                        actor_user_id=usuario_id,
                        occurred_at=datetime.now(UTC),
                        correlation_id=out.snapshot.correlation_id,
                        causation_id=novo.chave_id,  # type: ignore[arg-type]
                    ),
                    evento_repo,
                )
        except ReclamacaoNaoEncontrada as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_404_NOT_FOUND,
            )
            raise NotFound(str(exc)) from exc
        except EstadoInvalidoParaTransicaoReclamacao as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {"erro": str(exc), "codigo": "EstadoInvalido"},
                status=status.HTTP_409_CONFLICT,
            )
        except ConflitoEstadoReclamacao as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id_ctx,
                response_status=status.HTTP_409_CONFLICT,
            )
            return Response(
                {
                    "erro": str(exc),
                    "codigo": "ConflitoEstado",
                    "estado_atual": exc.snapshot_atual.estado.value,
                },
                status=status.HTTP_409_CONFLICT,
            )

        body = _serializar_reclamacao(out.snapshot)
        body["dispara_recall_m5"] = out.dispara_recall_m5
        logger.info(
            "calibracao.reclamacao_responder OK reclamacao_id=%s decisao=%s",
            out.snapshot.id,
            dados["decisao"],
            extra={
                "tenant_id": str(tenant_id_ctx),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_RECL_RESPONDER,
                "reclamacao_id": str(out.snapshot.id),
                "usuario_id": str(usuario_id),
                "dispara_recall_m5": out.dispara_recall_m5,
            },
        )
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id_ctx,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body)
