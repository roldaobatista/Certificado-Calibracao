"""CaixaTecnicoViewSets — REST da frente caixa-tecnico (T-CT-032 / Fatia 2).

ViewSets autenticados:
  DespesaCaixaViewSet:
    GET  /api/v1/caixa-tecnico/despesas/                list
    GET  /api/v1/caixa-tecnico/despesas/{id}/           retrieve
    POST /api/v1/caixa-tecnico/despesas/lancar/         lancar despesa (US-CT-002)
    POST /api/v1/caixa-tecnico/despesas/{id}/validar/   validar (US-CT-003)
    POST /api/v1/caixa-tecnico/despesas/{id}/rejeitar/  rejeitar (US-CT-004)
    POST /api/v1/caixa-tecnico/despesas/{id}/reapresentar/ reapresentar (US-CT-007)

  AdiantamentoCaixaViewSet:
    GET  /api/v1/caixa-tecnico/adiantamentos/           list
    GET  /api/v1/caixa-tecnico/adiantamentos/{id}/      retrieve
    POST /api/v1/caixa-tecnico/adiantamentos/solicitar/ solicitar (US-CT-001)
    POST /api/v1/caixa-tecnico/adiantamentos/{id}/aprovar/  aprovar (US-CT-005)
    POST /api/v1/caixa-tecnico/adiantamentos/{id}/recusar/  recusar (US-CT-006)
    POST /api/v1/caixa-tecnico/adiantamentos/{id}/entregar/ entregar (US-CT-008)

  PrestacaoContasViewSet:
    GET  /api/v1/caixa-tecnico/prestacoes/              list
    GET  /api/v1/caixa-tecnico/prestacoes/{id}/         retrieve
    POST /api/v1/caixa-tecnico/prestacoes/fechar/       fechar (US-CT-009)

  sync-lote (action extra em DespesaCaixaViewSet):
    POST /api/v1/caixa-tecnico/despesas/sync-lote/      sync lote (US-CT-010)

Idempotência REST (Idempotency-Key obrigatória em POST de escrita — IDEMP-001).
Perfil sempre server-side (INV-FIN-SNAPSHOT-PERFIL-001).
Advisory lock ``pg_advisory_xact_lock`` em fechar_prestacao (R6 / concorrência).
``publicar_evento(outbox=True)`` dentro do mesmo ``transaction.atomic``.

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import base64
import logging
from typing import Any
from uuid import UUID

from django.db import connection, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.caixa_tecnico.aprovar_adiantamento import (
    AprovarAdiantamentoInput,
    AprovarAdiantamentoUseCase,
)
from src.application.caixa_tecnico.entregar_adiantamento import (
    EntregarAdiantamentoInput,
    EntregarAdiantamentoUseCase,
)
from src.application.caixa_tecnico.fechar_prestacao import (
    FecharPrestacaoInput,
    FecharPrestacaoUseCase,
)
from src.application.caixa_tecnico.lancar_despesa import (
    LancarDespesaInput,
    LancarDespesaUseCase,
)
from src.application.caixa_tecnico.reapresentar_despesa import (
    ReapresentarDespesaInput,
    ReapresentarDespesaUseCase,
)
from src.application.caixa_tecnico.recusar_adiantamento import (
    RecusarAdiantamentoInput,
    RecusarAdiantamentoUseCase,
)
from src.application.caixa_tecnico.rejeitar_despesa import (
    RejeitarDespesaInput,
    RejeitarDespesaUseCase,
)
from src.application.caixa_tecnico.solicitar_adiantamento import (
    SolicitarAdiantamentoInput,
    SolicitarAdiantamentoUseCase,
)
from src.application.caixa_tecnico.sync_despesas_lote import (
    ItemLote,
)
from src.application.caixa_tecnico.validar_despesa import (
    ValidarDespesaInput,
    ValidarDespesaUseCase,
)
from src.domain.caixa_tecnico.enums import CategoriaDespesa, MeioEntrega, TipoDespesa
from src.domain.caixa_tecnico.erros import (
    AdiantamentoNaoCancelavel,
    CaixaTecnicoDesligado,
    CaixaTecnicoDomainError,
    FotoComprovanteObrigatoria,
    LoteExcedido,
    PeriodoPrestacaoFechado,
    TransicaoInvalida,
)
from src.infrastructure.authz.perfil_tenant_helper import obter_perfil_tenant_corrente
from src.infrastructure.caixa_tecnico.ports_stub import (
    ConsentimentoGpsFake,
    FotoComprovanteStorageFake,
)
from src.infrastructure.caixa_tecnico.repositories import (
    AdiantamentoRepository,
    CaixaTecnicoRepository,
    DespesaRepository,
    PoliticaRepository,
    PrestacaoRepository,
)
from src.infrastructure.caixa_tecnico.serializers import (
    AprovarAdiantamentoSerializer,
    EntregarAdiantamentoSerializer,
    FecharPrestacaoSerializer,
    LancarDespesaSerializer,
    ReapresentarDespesaSerializer,
    RecusarAdiantamentoSerializer,
    RejeitarDespesaSerializer,
    SolicitarAdiantamentoSerializer,
    SyncDespesasLoteSerializer,
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

# ---------------------------------------------------------------------------
# Constantes de endpoint (para idempotência)
# ---------------------------------------------------------------------------

ENDPOINT_LANCAR = "caixa_tecnico.despesa.lancar"
ENDPOINT_REAPRESENTAR = "caixa_tecnico.despesa.reapresentar"
ENDPOINT_VALIDAR = "caixa_tecnico.despesa.validar"
ENDPOINT_REJEITAR = "caixa_tecnico.despesa.rejeitar"
ENDPOINT_SOLICITAR_ADIAN = "caixa_tecnico.adiantamento.solicitar"
ENDPOINT_APROVAR_ADIAN = "caixa_tecnico.adiantamento.aprovar"
ENDPOINT_RECUSAR_ADIAN = "caixa_tecnico.adiantamento.recusar"
ENDPOINT_ENTREGAR_ADIAN = "caixa_tecnico.adiantamento.entregar"
ENDPOINT_FECHAR_PRESTACAO = "caixa_tecnico.prestacao.fechar"
ENDPOINT_SYNC_LOTE = "caixa_tecnico.despesa.sync_lote"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tenant_ou_none() -> UUID | None:
    return active_tenant_context.get()


def _obter_perfil() -> str | None:
    return obter_perfil_tenant_corrente() or None


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


def _publicar_evento_ct(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    usuario_id: UUID,
    resource_summary: str,
) -> None:
    """Evento na cadeia hash + outbox (D-CT-11). Import local (molde agenda/CR)."""
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
        "caixa_tecnico evento WORM publicado",
        extra={"tenant_id": str(tenant_id), "acao": acao},
    )


def _serializar_despesa(d: Any) -> dict[str, Any]:
    return {
        "despesa_id": str(d.despesa_id),
        "tenant_id": str(d.tenant_id),
        "caixa_id": str(d.caixa_id),
        "categoria": d.categoria.value,
        "tipo": d.tipo.value,
        "valor_centavos": d.valor.centavos,
        "estado": d.estado.value,
        "foto_hash": d.foto_hash,
        "foto_url": str(d.foto_url),
        "data": d.data.isoformat(),
        "descricao": d.descricao,
        "km_percorridos": d.km_percorridos,
        "acima_limite": d.acima_limite,
        "client_offline_id": d.client_offline_id,
        "os_id": str(d.os_id) if d.os_id else None,
        "criado_em": d.criado_em.isoformat(),
        "revision": d.revision,
    }


def _serializar_adiantamento(a: Any) -> dict[str, Any]:
    return {
        "adiantamento_id": str(a.adiantamento_id),
        "tenant_id": str(a.tenant_id),
        "caixa_id": str(a.caixa_id),
        "valor_centavos": a.valor.centavos,
        "estado": a.estado.value,
        "meio": a.meio.value,
        "solicitado_em": a.solicitado_em.isoformat(),
        "aprovado_em": a.aprovado_em.isoformat() if a.aprovado_em else None,
        "entregue_em": a.entregue_em.isoformat() if a.entregue_em else None,
        "recusado_em": a.recusado_em.isoformat() if a.recusado_em else None,
        "cancelado_em": a.cancelado_em.isoformat() if a.cancelado_em else None,
        "motivo_recusa": a.motivo_recusa,
        "criado_em": a.criado_em.isoformat(),
        "revision": a.revision,
    }


def _serializar_prestacao(p: Any) -> dict[str, Any]:
    return {
        "prestacao_id": str(p.prestacao_id),
        "tenant_id": str(p.tenant_id),
        "caixa_id": str(p.caixa_id),
        "periodo_de": p.periodo.de.isoformat(),
        "periodo_ate": p.periodo.ate.isoformat(),
        "total_adiantado": p.total_adiantado.centavos,
        "total_despesas_validadas": p.total_despesas_validadas.centavos,
        "saldo_final": p.saldo_final.centavos,
        "direcao": p.direcao.value,
        "fechada_em": p.fechada_em.isoformat(),
        "criado_em": p.criado_em.isoformat(),
        "observacoes": p.observacoes,
    }


# ---------------------------------------------------------------------------
# Fábricas de use cases (portas FAKE em Wave A — Fatia 3a substitui)
# ---------------------------------------------------------------------------


def _make_foto_storage() -> FotoComprovanteStorageFake:
    """Porta FAKE de storage de foto (Fatia 3a substitui por real)."""
    return FotoComprovanteStorageFake()


def _make_consentimento_port() -> ConsentimentoGpsFake:
    """Porta FAKE de consentimento GPS (Fatia 3a substitui por real)."""
    return ConsentimentoGpsFake(opt_in_ativo=False)  # fail-safe: sem opt-in por padrão


def _make_lancar_uc() -> LancarDespesaUseCase:
    return LancarDespesaUseCase(
        caixa_repo=CaixaTecnicoRepository(),
        despesa_repo=DespesaRepository(),
        politica_repo=PoliticaRepository(),
        prestacao_repo=PrestacaoRepository(),
        foto_storage=_make_foto_storage(),
        consentimento_port=_make_consentimento_port(),
    )


def _make_fechar_uc() -> FecharPrestacaoUseCase:
    return FecharPrestacaoUseCase(
        caixa_repo=CaixaTecnicoRepository(),
        adiantamento_repo=AdiantamentoRepository(),
        despesa_repo=DespesaRepository(),
        prestacao_repo=PrestacaoRepository(),
    )


# ---------------------------------------------------------------------------
# Helpers internos dos ViewSets
# ---------------------------------------------------------------------------


def _advisory_lock_ct(chave: str) -> None:
    """Advisory lock transacional para serializar operações concorrentes (R6)."""
    with connection.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [chave])


def _uuid_ou_404(raw: str | None) -> UUID:
    try:
        return UUID(str(raw))
    except (ValueError, TypeError) as exc:
        raise NotFound(f"id inválido: {exc}") from exc


def _falha(chave_id: UUID, tenant_id: UUID, exc: Exception, http_status_code: int) -> Response:
    falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=http_status_code)
    return Response({"erro": str(exc)}, status=http_status_code)


# ---------------------------------------------------------------------------
# ViewSet de Despesas
# ---------------------------------------------------------------------------


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class DespesaCaixaViewSet(viewsets.ViewSet):
    """ViewSet REST de Despesas do Caixa Técnico (Fatia 2)."""

    authz_purpose = "caixa_tecnico"
    ACTION_MAP = {
        "list": "caixa_tecnico.ver",
        "retrieve": "caixa_tecnico.ver",
        "lancar": "caixa_tecnico.lancar_despesa",
        "validar_despesa": "caixa_tecnico.validar_despesa",
        "rejeitar_despesa": "caixa_tecnico.rejeitar_despesa",
        "reapresentar": "caixa_tecnico.reapresentar_despesa",
        "sync_lote": "caixa_tecnico.sync_lote",
    }

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    # ---------------------------------------------------------------- GET list
    def list(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        caixa_id_str = request.query_params.get("caixa_id")
        if not caixa_id_str:
            return Response({"erro": "caixa_id obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            caixa_id = UUID(caixa_id_str)
        except ValueError:
            return Response({"erro": "caixa_id inválido"}, status=status.HTTP_400_BAD_REQUEST)
        repo = DespesaRepository()
        despesas = repo.listar_por_caixa(tenant_id=tenant_id, caixa_id=caixa_id)
        return Response([_serializar_despesa(d) for d in despesas])

    # ---------------------------------------------------------------- GET retrieve
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        repo = DespesaRepository()
        d = repo.obter_por_id(tenant_id=tenant_id, despesa_id=_uuid_ou_404(pk))
        if d is None:
            raise NotFound(f"Despesa {pk} não encontrada.")
        return Response(_serializar_despesa(d))

    # ---------------------------------------------------------------- POST lancar
    @action(detail=False, methods=["post"], url_path="lancar")
    def lancar(self, request: Request) -> Response:
        """POST — US-CT-002 lançamento de despesa. # idempotency-key: required"""
        s = LancarDespesaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_LANCAR,
            payload_fingerprint={
                "caixa_id": str(d.get("caixa_id", "")),
                "client_offline_id": d.get("client_offline_id") or "",
                "foto_mime": d["foto_mime"],
                "categoria": d["categoria"],
                "data": str(d["data"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        # caixa_id vem do query param ou do payload — aqui vem do payload via serializer
        caixa_id_raw = request.query_params.get("caixa_id") or request.data.get("caixa_id")
        if not caixa_id_raw:
            falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=400)
            return Response({"erro": "caixa_id obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            caixa_id = UUID(str(caixa_id_raw))
        except ValueError:
            falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=400)
            return Response({"erro": "caixa_id inválido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            foto_bytes = base64.b64decode(d["foto_base64"])
        except Exception:
            falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=400)
            return Response({"erro": "foto_base64 inválido"}, status=status.HTTP_400_BAD_REQUEST)

        uc = _make_lancar_uc()
        inp = LancarDespesaInput(
            tenant_id=tenant_id,
            caixa_id=caixa_id,
            foto_bytes=foto_bytes,
            foto_mime=d["foto_mime"],
            categoria=CategoriaDespesa(d["categoria"]),
            valor_centavos=d["valor_centavos"],
            data=d["data"],
            colaborador_id=d["colaborador_id"],
            descricao=d.get("descricao"),
            km_percorridos=d.get("km_percorridos"),
            client_offline_id=d.get("client_offline_id"),
            os_id=d.get("os_id"),
            tipo=TipoDespesa(d.get("tipo", TipoDespesa.NORMAL.value)),
            despesa_origem_id=d.get("despesa_origem_id"),
        )
        try:
            with transaction.atomic():
                out = uc.executar(inp)
                _publicar_evento_ct(
                    acao="caixa_tecnico.despesa.lancada",
                    payload={
                        "despesa_id": str(out.despesa.despesa_id),
                        "caixa_id": str(caixa_id),
                        "categoria": out.despesa.categoria.value,
                        "valor_centavos": out.despesa.valor.centavos,
                        "gps_aviso": out.gps_aviso,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"despesa_caixa {out.despesa.despesa_id} lançada",
                )
        except FotoComprovanteObrigatoria as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_412_PRECONDITION_FAILED)
        except CaixaTecnicoDesligado as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except PeriodoPrestacaoFechado as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except CaixaTecnicoDomainError as exc:
            return _falha(chave_id, tenant_id, exc, exc.http_status)
        except ValueError as exc:
            # client_offline_id duplicado → trata como replay idempotente (200)
            if "client_offline_id já existe" in str(exc):
                concluir_chave(
                    chave_id=chave_id,
                    tenant_id=tenant_id,
                    response_status=200,
                    response_body_resumo={"replay": True},
                )
                return Response({"replay": True}, status=status.HTTP_200_OK)
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        body = _serializar_despesa(out.despesa)
        if out.gps_aviso:
            body["gps_aviso"] = True
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST validar
    @action(detail=True, methods=["post"], url_path="validar")
    def validar_despesa(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-CT-003 validar despesa. # idempotency-key: required"""
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        despesa_id = _uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_VALIDAR,
            payload_fingerprint={"despesa_id": str(despesa_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        uc = ValidarDespesaUseCase(despesa_repo=DespesaRepository())
        try:
            with transaction.atomic():
                despesa = uc.executar(
                    ValidarDespesaInput(
                        tenant_id=tenant_id,
                        despesa_id=despesa_id,
                        usuario_id=usuario_id,
                    )
                )
                _publicar_evento_ct(
                    acao="caixa_tecnico.despesa.validada",
                    payload={"despesa_id": str(despesa_id)},
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"despesa_caixa {despesa_id} validada",
                )
        except TransicaoInvalida as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except CaixaTecnicoDomainError as exc:
            return _falha(chave_id, tenant_id, exc, exc.http_status)
        except ValueError as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        body = _serializar_despesa(despesa)
        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id, response_status=200, response_body_resumo=body
        )
        return Response(body)

    # ---------------------------------------------------------------- POST rejeitar
    @action(detail=True, methods=["post"], url_path="rejeitar")
    def rejeitar_despesa(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-CT-004 rejeitar despesa. # idempotency-key: required"""
        s = RejeitarDespesaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        despesa_id = _uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_REJEITAR,
            payload_fingerprint={
                "despesa_id": str(despesa_id),
                "motivo_hash": str(hash(d["motivo"])),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        uc = RejeitarDespesaUseCase(despesa_repo=DespesaRepository())
        try:
            with transaction.atomic():
                despesa = uc.executar(
                    RejeitarDespesaInput(
                        tenant_id=tenant_id,
                        despesa_id=despesa_id,
                        motivo=d["motivo"],
                        usuario_id=usuario_id,
                    )
                )
                _publicar_evento_ct(
                    acao="caixa_tecnico.despesa.rejeitada",
                    payload={"despesa_id": str(despesa_id)},
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"despesa_caixa {despesa_id} rejeitada",
                )
        except TransicaoInvalida as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except CaixaTecnicoDomainError as exc:
            return _falha(chave_id, tenant_id, exc, exc.http_status)
        except ValueError as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        body = _serializar_despesa(despesa)
        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id, response_status=200, response_body_resumo=body
        )
        return Response(body)

    # ---------------------------------------------------------------- POST reapresentar
    @action(detail=True, methods=["post"], url_path="reapresentar")
    def reapresentar(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-CT-007 reapresentar despesa rejeitada. # idempotency-key: required"""
        s = ReapresentarDespesaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        despesa_id = _uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_REAPRESENTAR,
            payload_fingerprint={"despesa_id": str(despesa_id), "foto_mime": d["foto_mime"]},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            foto_bytes = base64.b64decode(d["foto_base64"])
        except Exception:
            falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=400)
            return Response({"erro": "foto_base64 inválido"}, status=status.HTTP_400_BAD_REQUEST)

        uc = ReapresentarDespesaUseCase(
            despesa_repo=DespesaRepository(),
            foto_storage=_make_foto_storage(),
        )
        try:
            with transaction.atomic():
                despesa = uc.executar(
                    ReapresentarDespesaInput(
                        tenant_id=tenant_id,
                        despesa_id=despesa_id,
                        foto_bytes=foto_bytes,
                        foto_mime=d["foto_mime"],
                        colaborador_id=d["colaborador_id"],
                    )
                )
        except FotoComprovanteObrigatoria as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_412_PRECONDITION_FAILED)
        except TransicaoInvalida as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except CaixaTecnicoDomainError as exc:
            return _falha(chave_id, tenant_id, exc, exc.http_status)
        except ValueError as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        body = _serializar_despesa(despesa)
        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id, response_status=200, response_body_resumo=body
        )
        return Response(body)

    # ---------------------------------------------------------------- POST sync-lote
    @action(detail=False, methods=["post"], url_path="sync-lote")
    def sync_lote(self, request: Request) -> Response:
        """POST — US-CT-010 sync lote offline (207). # idempotency-key: required"""
        s = SyncDespesasLoteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        usuario_id = usuario_id_context.get() or UUID(int=0)
        caixa_id = d["caixa_id"]

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_SYNC_LOTE,
            payload_fingerprint={
                "caixa_id": str(caixa_id),
                "total_itens": len(d["itens"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        itens = [
            ItemLote(
                foto_base64=item["foto_base64"],
                foto_mime=item["foto_mime"],
                categoria=CategoriaDespesa(item["categoria"]),
                valor_centavos=item["valor_centavos"],
                data=item["data"],
                descricao=item.get("descricao"),
                km_percorridos=item.get("km_percorridos"),
                client_offline_id=item.get("client_offline_id"),
                os_id=item.get("os_id"),
            )
            for item in d["itens"]
        ]

        lancar_uc = _make_lancar_uc()
        try:
            with transaction.atomic():
                # Atomicidade per-item: savepoint por item
                resultados = []
                caixa_repo = CaixaTecnicoRepository()
                despesa_repo = DespesaRepository()

                # Validações globais antes de per-item
                if len(itens) > 20:
                    raise LoteExcedido("lote excede 20 itens")
                caixa = caixa_repo.obter_por_id(tenant_id, caixa_id)
                if caixa is None:
                    falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=422)
                    return Response({"erro": "caixa não encontrado"}, status=422)
                if caixa.esta_desligado:
                    falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=409)
                    return Response({"erro": "caixa desligado"}, status=status.HTTP_409_CONFLICT)

                for i, item in enumerate(itens):
                    # Dedup por client_offline_id
                    if item.client_offline_id:
                        if despesa_repo.existe_gateway_offline(tenant_id, item.client_offline_id):
                            resultados.append(
                                {
                                    "indice": i,
                                    "sucesso": True,
                                    "despesa_id": None,
                                    "erro": "replay idempotente",
                                    "codigo_http": 200,
                                }
                            )
                            continue

                    try:
                        foto_bytes = base64.b64decode(item.foto_base64)
                    except Exception:
                        resultados.append(
                            {
                                "indice": i,
                                "sucesso": False,
                                "despesa_id": None,
                                "erro": "foto_base64 inválido",
                                "codigo_http": 400,
                            }
                        )
                        continue

                    from django.db import transaction as dj_transaction

                    sp = dj_transaction.savepoint()
                    try:
                        lancar_inp = LancarDespesaInput(
                            tenant_id=tenant_id,
                            caixa_id=caixa_id,
                            foto_bytes=foto_bytes,
                            foto_mime=item.foto_mime,
                            categoria=item.categoria,
                            valor_centavos=item.valor_centavos,
                            data=item.data,
                            colaborador_id=d["colaborador_id"],
                            descricao=item.descricao,
                            km_percorridos=item.km_percorridos,
                            client_offline_id=item.client_offline_id,
                            os_id=item.os_id,
                        )
                        out = lancar_uc.executar(lancar_inp)
                        dj_transaction.savepoint_commit(sp)
                        resultados.append(
                            {
                                "indice": i,
                                "sucesso": True,
                                "despesa_id": str(out.despesa.despesa_id),
                                "erro": None,
                                "codigo_http": 201,
                            }
                        )
                    except CaixaTecnicoDomainError as exc:
                        dj_transaction.savepoint_rollback(sp)
                        resultados.append(
                            {
                                "indice": i,
                                "sucesso": False,
                                "despesa_id": None,
                                "erro": str(exc),
                                "codigo_http": exc.http_status,
                            }
                        )
                    except Exception as exc:
                        dj_transaction.savepoint_rollback(sp)
                        resultados.append(
                            {
                                "indice": i,
                                "sucesso": False,
                                "despesa_id": None,
                                "erro": str(exc),
                                "codigo_http": 422,
                            }
                        )

                body = {"resultados": resultados}
                concluir_chave(
                    chave_id=chave_id,
                    tenant_id=tenant_id,
                    response_status=207,
                    response_body_resumo=body,
                )
                return Response(body, status=status.HTTP_207_MULTI_STATUS)

        except LoteExcedido as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        except CaixaTecnicoDomainError as exc:
            return _falha(chave_id, tenant_id, exc, exc.http_status)
        except ValueError as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)


# ---------------------------------------------------------------------------
# ViewSet de Adiantamentos
# ---------------------------------------------------------------------------


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class AdiantamentoCaixaViewSet(viewsets.ViewSet):
    """ViewSet REST de Adiantamentos do Caixa Técnico (Fatia 2)."""

    authz_purpose = "caixa_tecnico"
    ACTION_MAP = {
        "list": "caixa_tecnico.ver",
        "retrieve": "caixa_tecnico.ver",
        "solicitar": "caixa_tecnico.solicitar_adiantamento",
        "aprovar": "caixa_tecnico.aprovar_adiantamento",
        "recusar": "caixa_tecnico.recusar_adiantamento",
        "entregar": "caixa_tecnico.entregar_adiantamento",
    }

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    # ---------------------------------------------------------------- GET list
    def list(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        caixa_id_str = request.query_params.get("caixa_id")
        if not caixa_id_str:
            return Response({"erro": "caixa_id obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            caixa_id = UUID(caixa_id_str)
        except ValueError:
            return Response({"erro": "caixa_id inválido"}, status=status.HTTP_400_BAD_REQUEST)
        repo = AdiantamentoRepository()
        adiantamentos = repo.listar_por_caixa(tenant_id=tenant_id, caixa_id=caixa_id)
        return Response([_serializar_adiantamento(a) for a in adiantamentos])

    # ---------------------------------------------------------------- GET retrieve
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        repo = AdiantamentoRepository()
        a = repo.obter_por_id(tenant_id=tenant_id, adiantamento_id=_uuid_ou_404(pk))
        if a is None:
            raise NotFound(f"Adiantamento {pk} não encontrado.")
        return Response(_serializar_adiantamento(a))

    # ---------------------------------------------------------------- POST solicitar
    @action(detail=False, methods=["post"], url_path="solicitar")
    def solicitar(self, request: Request) -> Response:
        """POST — US-CT-001 solicitar adiantamento. # idempotency-key: required"""
        s = SolicitarAdiantamentoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_SOLICITAR_ADIAN,
            payload_fingerprint={
                "caixa_id": str(d["caixa_id"]),
                "valor_centavos": d["valor_centavos"],
                "meio": d["meio"],
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        uc = SolicitarAdiantamentoUseCase(
            caixa_repo=CaixaTecnicoRepository(),
            adiantamento_repo=AdiantamentoRepository(),
        )
        try:
            with transaction.atomic():
                adiantamento = uc.executar(
                    SolicitarAdiantamentoInput(
                        tenant_id=tenant_id,
                        caixa_id=d["caixa_id"],
                        valor_centavos=d["valor_centavos"],
                        meio=MeioEntrega(d["meio"]),
                        justificativa=d.get("justificativa"),
                    )
                )
                _publicar_evento_ct(
                    acao="caixa_tecnico.adiantamento.solicitado",
                    payload={
                        "adiantamento_id": str(adiantamento.adiantamento_id),
                        "valor_centavos": adiantamento.valor.centavos,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"adiantamento_caixa {adiantamento.adiantamento_id} solicitado",
                )
        except CaixaTecnicoDesligado as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except CaixaTecnicoDomainError as exc:
            return _falha(chave_id, tenant_id, exc, exc.http_status)
        except ValueError as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        body = _serializar_adiantamento(adiantamento)
        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id, response_status=201, response_body_resumo=body
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST aprovar
    @action(detail=True, methods=["post"], url_path="aprovar")
    def aprovar(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-CT-005 aprovar adiantamento. # idempotency-key: required"""
        s = AprovarAdiantamentoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        adiantamento_id = _uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        perfil_str = _obter_perfil()

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_APROVAR_ADIAN,
            payload_fingerprint={"adiantamento_id": str(adiantamento_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        uc = AprovarAdiantamentoUseCase(
            adiantamento_repo=AdiantamentoRepository(),
            politica_repo=PoliticaRepository(),
        )
        try:
            with transaction.atomic():
                adiantamento = uc.executar(
                    AprovarAdiantamentoInput(
                        tenant_id=tenant_id,
                        adiantamento_id=adiantamento_id,
                        aprovado_por_id=d["aprovado_por_id"],
                        perfil=perfil_str,
                    )
                )
                _publicar_evento_ct(
                    acao="caixa_tecnico.adiantamento.aprovado",
                    payload={"adiantamento_id": str(adiantamento_id)},
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"adiantamento_caixa {adiantamento_id} aprovado",
                )
        except TransicaoInvalida as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except CaixaTecnicoDomainError as exc:
            return _falha(chave_id, tenant_id, exc, exc.http_status)
        except ValueError as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        body = _serializar_adiantamento(adiantamento)
        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id, response_status=200, response_body_resumo=body
        )
        return Response(body)

    # ---------------------------------------------------------------- POST recusar
    @action(detail=True, methods=["post"], url_path="recusar")
    def recusar(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-CT-006 recusar adiantamento. # idempotency-key: required"""
        s = RecusarAdiantamentoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        adiantamento_id = _uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_RECUSAR_ADIAN,
            payload_fingerprint={
                "adiantamento_id": str(adiantamento_id),
                "motivo_hash": str(hash(d["motivo"])),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        uc = RecusarAdiantamentoUseCase(adiantamento_repo=AdiantamentoRepository())
        try:
            with transaction.atomic():
                adiantamento = uc.executar(
                    RecusarAdiantamentoInput(
                        tenant_id=tenant_id,
                        adiantamento_id=adiantamento_id,
                        motivo=d["motivo"],
                        recusado_por_id=usuario_id,
                    )
                )
                _publicar_evento_ct(
                    acao="caixa_tecnico.adiantamento.recusado",
                    payload={"adiantamento_id": str(adiantamento_id)},
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"adiantamento_caixa {adiantamento_id} recusado",
                )
        except TransicaoInvalida as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except CaixaTecnicoDomainError as exc:
            return _falha(chave_id, tenant_id, exc, exc.http_status)
        except ValueError as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        body = _serializar_adiantamento(adiantamento)
        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id, response_status=200, response_body_resumo=body
        )
        return Response(body)

    # ---------------------------------------------------------------- POST entregar
    @action(detail=True, methods=["post"], url_path="entregar")
    def entregar(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-CT-008 entregar adiantamento. # idempotency-key: required"""
        s = EntregarAdiantamentoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        adiantamento_id = _uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_ENTREGAR_ADIAN,
            payload_fingerprint={"adiantamento_id": str(adiantamento_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        uc = EntregarAdiantamentoUseCase(adiantamento_repo=AdiantamentoRepository())
        try:
            with transaction.atomic():
                adiantamento = uc.executar(
                    EntregarAdiantamentoInput(
                        tenant_id=tenant_id,
                        adiantamento_id=adiantamento_id,
                        entregue_por_id=d["entregue_por_id"],
                    )
                )
                _publicar_evento_ct(
                    acao="caixa_tecnico.adiantamento.entregue",
                    payload={"adiantamento_id": str(adiantamento_id)},
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"adiantamento_caixa {adiantamento_id} entregue",
                )
        except AdiantamentoNaoCancelavel as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except TransicaoInvalida as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except CaixaTecnicoDomainError as exc:
            return _falha(chave_id, tenant_id, exc, exc.http_status)
        except ValueError as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        body = _serializar_adiantamento(adiantamento)
        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id, response_status=200, response_body_resumo=body
        )
        return Response(body)


# ---------------------------------------------------------------------------
# ViewSet de Prestações de Contas
# ---------------------------------------------------------------------------


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class PrestacaoContasViewSet(viewsets.ViewSet):
    """ViewSet REST de Prestações de Contas do Caixa Técnico (Fatia 2)."""

    authz_purpose = "caixa_tecnico"
    ACTION_MAP = {
        "list": "caixa_tecnico.ver",
        "retrieve": "caixa_tecnico.ver",
        "fechar": "caixa_tecnico.fechar_prestacao",
    }

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    # ---------------------------------------------------------------- GET list
    def list(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        caixa_id_str = request.query_params.get("caixa_id")
        if not caixa_id_str:
            return Response({"erro": "caixa_id obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            caixa_id = UUID(caixa_id_str)
        except ValueError:
            return Response({"erro": "caixa_id inválido"}, status=status.HTTP_400_BAD_REQUEST)
        repo = PrestacaoRepository()
        prestacoes = repo.listar_por_caixa(tenant_id=tenant_id, caixa_id=caixa_id)
        return Response([_serializar_prestacao(p) for p in prestacoes])

    # ---------------------------------------------------------------- GET retrieve
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        repo = PrestacaoRepository()
        p = repo.obter_por_id(tenant_id=tenant_id, prestacao_id=_uuid_ou_404(pk))
        if p is None:
            raise NotFound(f"Prestação {pk} não encontrada.")
        return Response(_serializar_prestacao(p))

    # ---------------------------------------------------------------- POST fechar
    @action(detail=False, methods=["post"], url_path="fechar")
    def fechar(self, request: Request) -> Response:
        """POST — US-CT-009 fechar prestação de contas (advisory lock R6). # idempotency-key: required"""
        s = FecharPrestacaoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        usuario_id = usuario_id_context.get() or UUID(int=0)
        caixa_id = d["caixa_id"]

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_FECHAR_PRESTACAO,
            payload_fingerprint={
                "caixa_id": str(caixa_id),
                "periodo_de": str(d["periodo_de"]),
                "periodo_ate": str(d["periodo_ate"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        uc = _make_fechar_uc()
        try:
            with transaction.atomic():
                # R6: advisory lock por (tenant, tecnico) — evita 2 fechamentos concorrentes
                _advisory_lock_ct(f"ct:fechar:{tenant_id}:{caixa_id}")
                prestacao = uc.executar(
                    FecharPrestacaoInput(
                        tenant_id=tenant_id,
                        caixa_id=caixa_id,
                        periodo_de=d["periodo_de"],
                        periodo_ate=d["periodo_ate"],
                        observacoes=d.get("observacoes"),
                    )
                )
                _publicar_evento_ct(
                    acao="caixa_tecnico.prestacao.fechada",
                    payload={
                        "prestacao_id": str(prestacao.prestacao_id),
                        "caixa_id": str(caixa_id),
                        "saldo_final": prestacao.saldo_final.centavos,
                        "direcao": prestacao.direcao.value,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"prestacao_contas {prestacao.prestacao_id} fechada",
                )
        except PeriodoPrestacaoFechado as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except CaixaTecnicoDomainError as exc:
            return _falha(chave_id, tenant_id, exc, exc.http_status)
        except ValueError as exc:
            return _falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)

        body = _serializar_prestacao(prestacao)
        concluir_chave(
            chave_id=chave_id, tenant_id=tenant_id, response_status=201, response_body_resumo=body
        )
        return Response(body, status=status.HTTP_201_CREATED)
