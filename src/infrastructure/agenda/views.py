"""AgendaViewSet — REST da frente agenda (T-AGE-031..038 / Fatia 2).

Actions autenticadas (AgendaViewSet):
  GET  /api/v1/agenda/                        list (grade multi-técnico — PLAN-AGE-04)
  GET  /api/v1/agenda/{id}/                   retrieve
  POST /api/v1/agenda/validar/                validar (dry-run — US-AG-002)
  POST /api/v1/agenda/                        criar evento OS (US-AG-001/013)
  POST /api/v1/agenda/bloquear/               criar bloqueio (US-AG-004)
  POST /api/v1/agenda/{id}/mover/             mover evento (D-AGE-3)
  POST /api/v1/agenda/{id}/reagendar/         reagendar (US-AG-008)
  POST /api/v1/agenda/{id}/no-show/           registrar no-show (US-AG-012)
  POST /api/v1/agenda/resolver-conflito/      resolver conflito (US-AG-011)
  POST /api/v1/agenda/enquadrar-regime/       override regime humano (D-AGE-15)

Idempotência REST (Idempotency-Key obrigatória em POST de escrita — IDEMP-001).
Perfil e regime SEMPRE server-side (INV-AG-PERFIL-001 / INV-AG-REGIME-001).
Grade multi-técnico em 1 query agregada (O(1) em técnicos — PLAN-AGE-04).
Unicidade de overlap garantida pelo EXCLUDE GIST (sem advisory lock — PLAN-AGE-06).
``publicar_evento(outbox=True)`` dentro do mesmo ``transaction.atomic``.

Portas injetadas (Fatia 3a — T-AGE-040..043):
  - ColaboradorAgenda: ColaboradorAgendaAdapter (papel + CNH + regime fail-safe).
  - OSScheduling: OSSchedulingAdapter (atribuir_tecnico real — OS→AGENDADA).
  - RTSubstituto: RTSubstitutoAdapter (competência projetada à data do slot).
  - AReceber: AReceberAdapter (criar_titulo_manual real em contas_receber).
  - Notificacao: stub (GATE-AGE-OMNICHANNEL — Wave B).
  - Maps: None (GATE-AGE-MAPS — Wave B).

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.operacao.agenda import (
    criar_bloqueio,
    criar_evento,
    enquadrar_regime,
    mover_evento,
    reagendar_evento,
    registrar_no_show,
    resolver_conflito,
    validar_evento,
)
from src.domain.operacao.agenda.enums import MotivoBloqueio, RegimeJornada, TipoEvento
from src.domain.operacao.agenda.erros import (
    ConflitoAgenda,
    EventoNaoEncontrado,
    FeriadoNaoConfirmado,
    JornadaUMCViolada,
    JustificativaConflitoCurta,
    MotoristaSemCNH,
    TransicaoEventoProibida,
)
from src.domain.operacao.agenda.value_objects import Janela
from src.infrastructure.agenda.adapters import (
    AReceberAdapter,
    ColaboradorAgendaAdapter,
    OSSchedulingAdapter,
    RTSubstitutoAdapter,
)
from src.infrastructure.agenda.repositories import DjangoEventoAgendaRepository
from src.infrastructure.agenda.serializers import (
    CriarBloqueioSerializer,
    CriarEventoSerializer,
    EnquadrarRegimeSerializer,
    MoverEventoSerializer,
    ReagendarEventoSerializer,
    RegistrarNoShowSerializer,
    ResolverConflitoSerializer,
    ValidarEventoSerializer,
)
from src.infrastructure.authz.perfil_tenant_helper import obter_perfil_tenant_corrente
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

ENDPOINT_CRIAR = "agenda.criar"
ENDPOINT_BLOQUEAR = "agenda.bloquear"
ENDPOINT_MOVER = "agenda.mover"
ENDPOINT_REAGENDAR = "agenda.reagendar"
ENDPOINT_NO_SHOW = "agenda.no_show"
ENDPOINT_RESOLVER = "agenda.resolver_conflito"
ENDPOINT_REGIME = "agenda.enquadrar_regime"
ENDPOINT_VALIDAR = "agenda.validar"


# ---------------------------------------------------------------------------
# Stubs de portas que permanecem em Wave A (Wave B os substitui)
# ---------------------------------------------------------------------------


class _NotificacaoStub:
    """Stub de NotificacaoClientePort — enfileira em log (GATE-AGE-OMNICHANNEL).

    # TODO Fatia 3: substituir por adapter omnichannel real.
    """

    def enfileirar_aviso_reagendamento(
        self,
        *,
        tenant_id: UUID,
        evento_id: UUID,
        cliente_id: UUID,
        nova_janela_inicia: datetime,
        nova_janela_termina: datetime,
    ) -> None:
        logger.info(
            "NotificacaoStub: aviso enfileirado para evento %s cliente %s (stub GATE-AGE-OMNICHANNEL)",
            evento_id,
            cliente_id,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tenant_ou_none() -> UUID | None:
    return active_tenant_context.get()


def _obter_perfil() -> str | None:
    return obter_perfil_tenant_corrente() or None


def _serializar_evento(ev: Any) -> dict[str, Any]:
    return {
        "id": str(ev.id),
        "tenant_id": str(ev.tenant_id),
        "tecnico_id": str(ev.tecnico_id),
        "tipo": ev.tipo.value,
        "estado": ev.estado.value,
        "inicia_at": ev.inicia_at.isoformat(),
        "termina_at": ev.termina_at.isoformat(),
        "aloca_em_umc": ev.aloca_em_umc,
        "atividade_id": str(ev.atividade_id) if ev.atividade_id else None,
        "os_id": str(ev.os_id) if ev.os_id else None,
        "motivo_bloqueio": ev.motivo_bloqueio.value if ev.motivo_bloqueio else None,
        "descricao_publica": ev.descricao_publica,
        "recorrencia_id": str(ev.recorrencia_id) if ev.recorrencia_id else None,
        "ocorrencia_dt": ev.ocorrencia_dt.isoformat() if ev.ocorrencia_dt else None,
        "confirmar_feriado": ev.confirmar_feriado,
        "revision": ev.revision,
        "criado_em": ev.criado_em.isoformat(),
        "atualizado_em": ev.atualizado_em.isoformat(),
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


def _publicar_evento_agenda(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    usuario_id: UUID,
    resource_summary: str,
) -> None:
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
        "agenda evento WORM publicado",
        extra={"tenant_id": str(tenant_id), "acao": acao},
    )


# ---------------------------------------------------------------------------
# ViewSet
# ---------------------------------------------------------------------------


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class AgendaViewSet(viewsets.ViewSet):
    """ViewSet REST de Agenda (Fatia 2 — calendário multi-técnico + jornada UMC)."""

    authz_purpose = "operacao_agenda"
    ACTION_MAP = {
        "list": "agenda.ver",
        "retrieve": "agenda.ver",
        "validar": "agenda.ver",
        "criar": "agenda.criar",
        "bloquear": "agenda.bloquear",
        "mover": "agenda.mover",
        "reagendar": "agenda.mover",
        "no_show": "agenda.no_show",
        "resolver_conflito": "agenda.resolver_conflito",
        "enquadrar_regime": "agenda.enquadrar_regime",
    }

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    # --- Leitura ---

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        """GET /agenda/{id}/ — retorna evento por ID (RLS enforça cross-tenant → 404)."""
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        repo = DjangoEventoAgendaRepository()
        ev = repo.obter_por_id(tenant_id=tenant_id, evento_id=self._uuid_ou_404(pk))
        if ev is None:
            raise NotFound(f"Evento {pk} não encontrado.")
        return Response(_serializar_evento(ev))

    def list(self, request: Request) -> Response:
        """GET /agenda/ — grade multi-técnico em 1 query (O(1) em técnicos — PLAN-AGE-04).

        Filtros opcionais: ``tecnico_id``, ``inicia_apos``, ``inicia_antes``.
        """
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        tecnico_id_str = request.query_params.get("tecnico_id")
        inicia_apos_str = request.query_params.get("inicia_apos")
        inicia_antes_str = request.query_params.get("inicia_antes")

        tecnico_id: UUID | None = None
        if tecnico_id_str:
            try:
                tecnico_id = UUID(tecnico_id_str)
            except ValueError:
                return Response({"erro": "tecnico_id inválido"}, status=status.HTTP_400_BAD_REQUEST)

        inicia_apos: datetime | None = None
        inicia_antes: datetime | None = None
        try:
            if inicia_apos_str:
                inicia_apos = datetime.fromisoformat(inicia_apos_str)
            if inicia_antes_str:
                inicia_antes = datetime.fromisoformat(inicia_antes_str)
        except ValueError:
            return Response(
                {"erro": "formato de data inválido"}, status=status.HTTP_400_BAD_REQUEST
            )

        repo = DjangoEventoAgendaRepository()
        # 1 query agregada — O(1) em técnicos (PLAN-AGE-04)
        eventos = repo.listar_por_tenant(
            tenant_id=tenant_id,
            tecnico_id=tecnico_id,
            inicia_apos=inicia_apos,
            inicia_antes=inicia_antes,
        )
        return Response([_serializar_evento(ev) for ev in eventos])

    # --- Dry-run ---

    @action(detail=False, methods=["post"], url_path="validar")
    def validar(self, request: Request) -> Response:
        """POST /agenda/validar/ — dry-run pré-save (US-AG-002 / R9). # idempotency-key: required"""
        s = ValidarEventoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        perfil_str = _obter_perfil()
        if not perfil_str:
            return Response(
                {"erro": "perfil regulatório indisponível (fail-closed ADR-0067)"},
                status=status.HTTP_403_FORBIDDEN,
            )

        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_VALIDAR,
            payload_fingerprint={
                "tecnico_id": str(d["tecnico_id"]),
                "inicia_at": d["inicia_at"].isoformat(),
                "termina_at": d["termina_at"].isoformat(),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoEventoAgendaRepository()
        janela = Janela(inicia_at=d["inicia_at"], termina_at=d["termina_at"])
        inp = validar_evento.ValidarEventoInput(
            tenant_id=tenant_id,
            tecnico_id=d["tecnico_id"],
            janela=janela,
            aloca_em_umc=d["aloca_em_umc"],
            perfil_tenant=perfil_str,
            acordo_coletivo_12h=d["acordo_coletivo_12h"],
        )
        # Dry-run NÃO usa transaction.atomic — garante que nada é gravado
        out = validar_evento.executar(
            inp,
            repo=repo,
            colaborador_port=ColaboradorAgendaAdapter(),
            rt_port=RTSubstitutoAdapter(),
        )
        body = {"ok": out.ok, "violacoes": out.violacoes}
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    # --- Escrita ---

    @action(detail=False, methods=["post"], url_path="criar")
    def criar(self, request: Request) -> Response:
        """POST /agenda/criar/ — criar evento OS. # idempotency-key: required"""
        s = CriarEventoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        perfil_str = _obter_perfil()
        if not perfil_str:
            return Response(
                {"erro": "perfil regulatório indisponível (fail-closed ADR-0067)"},
                status=status.HTTP_403_FORBIDDEN,
            )

        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CRIAR,
            payload_fingerprint={
                "tecnico_id": str(d["tecnico_id"]),
                "inicia_at": d["inicia_at"].isoformat(),
                "termina_at": d["termina_at"].isoformat(),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoEventoAgendaRepository()
        janela = Janela(inicia_at=d["inicia_at"], termina_at=d["termina_at"])
        inp = criar_evento.CriarEventoInput(
            tenant_id=tenant_id,
            tecnico_id=d["tecnico_id"],
            janela=janela,
            aloca_em_umc=d["aloca_em_umc"],
            perfil_tenant=perfil_str,
            criado_por_usuario_id=usuario_id,
            tipo=TipoEvento(d["tipo"]),
            atividade_id=d.get("atividade_id"),
            os_id=d.get("os_id"),
            recorrencia_id=d.get("recorrencia_id"),
            ocorrencia_dt=d.get("ocorrencia_dt"),
            confirmar_feriado=d["confirmar_feriado"],
            descricao_publica=d["descricao_publica"],
            acordo_coletivo_12h=d["acordo_coletivo_12h"],
        )
        try:
            with transaction.atomic():
                out = criar_evento.executar(
                    inp,
                    repo=repo,
                    colaborador_port=ColaboradorAgendaAdapter(),
                    os_port=OSSchedulingAdapter(),
                    rt_port=RTSubstitutoAdapter(),
                )
                _publicar_evento_agenda(
                    acao="agenda.evento.alocado",
                    payload={
                        "evento_id": str(out.evento.id),
                        "tecnico_id": str(d["tecnico_id"]),
                        "tipo": d["tipo"],
                        "inicia_at": d["inicia_at"].isoformat(),
                        "termina_at": d["termina_at"].isoformat(),
                        "aloca_em_umc": d["aloca_em_umc"],
                        "perfil_tenant": perfil_str,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"agenda evento {out.evento.id} alocado",
                )
                if out.regime_era_indeterminado:
                    _publicar_evento_agenda(
                        acao="agenda.jornada_umc.violada",
                        payload={
                            "evento_id": str(out.evento.id),
                            "tecnico_id": str(d["tecnico_id"]),
                            "motivo": "regime_indeterminado",
                            "perfil_tenant": perfil_str,
                        },
                        causation_id=chave_id,
                        tenant_id=tenant_id,
                        usuario_id=usuario_id,
                        resource_summary=f"agenda regime indeterminado {out.evento.id}",
                    )
        except ConflitoAgenda as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except JornadaUMCViolada as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except FeriadoNaoConfirmado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except MotoristaSemCNH as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_evento(out.evento)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="bloquear")
    def bloquear(self, request: Request) -> Response:
        """POST /agenda/bloquear/ — criar bloqueio (US-AG-004). # idempotency-key: required"""
        s = CriarBloqueioSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        perfil_str = _obter_perfil()
        if not perfil_str:
            return Response(
                {"erro": "perfil regulatório indisponível"},
                status=status.HTTP_403_FORBIDDEN,
            )

        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_BLOQUEAR,
            payload_fingerprint={
                "tecnico_id": str(d["tecnico_id"]),
                "inicia_at": d["inicia_at"].isoformat(),
                "termina_at": d["termina_at"].isoformat(),
                "motivo": d["motivo"],
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoEventoAgendaRepository()
        janela = Janela(inicia_at=d["inicia_at"], termina_at=d["termina_at"])
        inp = criar_bloqueio.CriarBloqueioInput(
            tenant_id=tenant_id,
            tecnico_id=d["tecnico_id"],
            janela=janela,
            motivo=MotivoBloqueio(d["motivo"]),
            criado_por_usuario_id=usuario_id,
            perfil_tenant=perfil_str,
            descricao_publica=d["descricao_publica"],
        )
        try:
            with transaction.atomic():
                out = criar_bloqueio.executar(inp, repo=repo)
                _publicar_evento_agenda(
                    acao="agenda.bloqueio.criado",
                    payload={
                        "evento_id": str(out.evento.id),
                        "tecnico_id": str(d["tecnico_id"]),
                        "motivo": d["motivo"],
                        "inicia_at": d["inicia_at"].isoformat(),
                        "termina_at": d["termina_at"].isoformat(),
                        "perfil_tenant": perfil_str,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"agenda bloqueio {out.evento.id}",
                )
        except ConflitoAgenda as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_evento(out.evento)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="mover")
    def mover(self, request: Request, pk: str | None = None) -> Response:
        """POST /agenda/{id}/mover/ — move janela (D-AGE-3). # idempotency-key: required"""
        s = MoverEventoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        perfil_str = _obter_perfil()
        if not perfil_str:
            return Response({"erro": "perfil indisponível"}, status=status.HTTP_403_FORBIDDEN)

        evento_id = self._uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_MOVER,
            payload_fingerprint={
                "evento_id": str(evento_id),
                "inicia_at": d["inicia_at"].isoformat(),
                "termina_at": d["termina_at"].isoformat(),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoEventoAgendaRepository()
        nova_janela = Janela(inicia_at=d["inicia_at"], termina_at=d["termina_at"])
        inp = mover_evento.MoverEventoInput(
            tenant_id=tenant_id,
            evento_id=evento_id,
            nova_janela=nova_janela,
            movido_por_usuario_id=usuario_id,
            perfil_tenant=perfil_str,
            confirmar_feriado=d["confirmar_feriado"],
            acordo_coletivo_12h=d["acordo_coletivo_12h"],
        )
        try:
            with transaction.atomic():
                out = mover_evento.executar(
                    inp,
                    repo=repo,
                    colaborador_port=ColaboradorAgendaAdapter(),
                )
                _publicar_evento_agenda(
                    acao="agenda.evento.reagendado",
                    payload={
                        "evento_id": str(evento_id),
                        "inicia_at": d["inicia_at"].isoformat(),
                        "termina_at": d["termina_at"].isoformat(),
                        "perfil_tenant": perfil_str,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"agenda evento {evento_id} movido",
                )
        except EventoNaoEncontrado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except TransicaoEventoProibida as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ConflitoAgenda as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except JornadaUMCViolada as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except FeriadoNaoConfirmado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except MotoristaSemCNH as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_evento(out.evento)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reagendar")
    def reagendar(self, request: Request, pk: str | None = None) -> Response:
        """POST /agenda/{id}/reagendar/ — reagenda + aviso (US-AG-008). # idempotency-key: required"""
        s = ReagendarEventoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        perfil_str = _obter_perfil()
        if not perfil_str:
            return Response({"erro": "perfil indisponível"}, status=status.HTTP_403_FORBIDDEN)

        evento_id = self._uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_REAGENDAR,
            payload_fingerprint={
                "evento_id": str(evento_id),
                "inicia_at": d["inicia_at"].isoformat(),
                "termina_at": d["termina_at"].isoformat(),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoEventoAgendaRepository()
        nova_janela = Janela(inicia_at=d["inicia_at"], termina_at=d["termina_at"])
        inp = reagendar_evento.ReagendarEventoInput(
            tenant_id=tenant_id,
            evento_id=evento_id,
            nova_janela=nova_janela,
            reagendado_por_usuario_id=usuario_id,
            perfil_tenant=perfil_str,
            confirmar_feriado=d["confirmar_feriado"],
            acordo_coletivo_12h=d["acordo_coletivo_12h"],
            motivo_reagendamento=d["motivo_reagendamento"],
            cliente_id=d.get("cliente_id"),
        )
        try:
            with transaction.atomic():
                out = reagendar_evento.executar(
                    inp,
                    repo=repo,
                    colaborador_port=ColaboradorAgendaAdapter(),
                    notificacao_port=_NotificacaoStub(),  # GATE-AGE-OMNICHANNEL Wave B
                )
                _publicar_evento_agenda(
                    acao="agenda.evento.reagendado",
                    payload={
                        "evento_id": str(evento_id),
                        "inicia_at": d["inicia_at"].isoformat(),
                        "termina_at": d["termina_at"].isoformat(),
                        "aviso_enfileirado": out.aviso_enfileirado,
                        "perfil_tenant": perfil_str,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"agenda evento {evento_id} reagendado",
                )
        except EventoNaoEncontrado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except TransicaoEventoProibida as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ConflitoAgenda as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except JornadaUMCViolada as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except FeriadoNaoConfirmado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except MotoristaSemCNH as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_evento(out.evento)
        body["aviso_enfileirado"] = out.aviso_enfileirado
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="no-show")
    def no_show(self, request: Request, pk: str | None = None) -> Response:
        """POST /agenda/{id}/no-show/ — registrar no-show (US-AG-012). # idempotency-key: required"""
        s = RegistrarNoShowSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        perfil_str = _obter_perfil()
        if not perfil_str:
            return Response({"erro": "perfil indisponível"}, status=status.HTTP_403_FORBIDDEN)

        evento_id = self._uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_NO_SHOW,
            payload_fingerprint={"evento_id": str(evento_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoEventoAgendaRepository()
        inp = registrar_no_show.RegistrarNoShowInput(
            tenant_id=tenant_id,
            evento_id=evento_id,
            registrado_por_usuario_id=usuario_id,
            perfil_tenant=perfil_str,
            cobrar_cliente=d["cobrar_cliente"],
            custo_estimado_centavos=d["custo_estimado_centavos"],
            observacao=d["observacao"],
            cliente_id=d.get("cliente_id"),
        )
        try:
            with transaction.atomic():
                out = registrar_no_show.executar(
                    inp,
                    repo=repo,
                    areceber_port=AReceberAdapter(),
                )
                _publicar_evento_agenda(
                    acao="agenda.no_show.registrado",
                    payload={
                        "evento_id": str(evento_id),
                        "cobrar_cliente": d["cobrar_cliente"],
                        "custo_estimado_centavos": d["custo_estimado_centavos"],
                        "titulo_criado": out.titulo_criado,
                        "perfil_tenant": perfil_str,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"agenda no-show {evento_id}",
                )
        except EventoNaoEncontrado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except TransicaoEventoProibida as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {
            "no_show_id": str(out.no_show.id),
            "evento_id": str(evento_id),
            "cobrar_cliente": out.no_show.cobrar_cliente,
            "custo_estimado": str(out.no_show.custo_estimado),
            "titulo_criado": out.titulo_criado,
        }
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="resolver-conflito")
    def resolver_conflito(self, request: Request) -> Response:
        """POST /agenda/resolver-conflito/ — resolução manual (US-AG-011). # idempotency-key: required"""
        s = ResolverConflitoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        perfil_str = _obter_perfil()
        if not perfil_str:
            return Response({"erro": "perfil indisponível"}, status=status.HTTP_403_FORBIDDEN)

        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_RESOLVER,
            payload_fingerprint={
                "evento_novo_id": str(d["evento_novo_id"]),
                "evento_antigo_id": str(d["evento_antigo_id"]),
                "opcao": d["opcao"],
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoEventoAgendaRepository()
        inp = resolver_conflito.ResolverConflitoInput(
            tenant_id=tenant_id,
            evento_novo_id=d["evento_novo_id"],
            evento_antigo_id=d["evento_antigo_id"],
            opcao=resolver_conflito.OpcaoConflito(d["opcao"]),
            razao=d["razao"],
            resolvido_por_usuario_id=usuario_id,
            perfil_tenant=perfil_str,
        )
        try:
            with transaction.atomic():
                out = resolver_conflito.executar(inp, repo=repo)
                _publicar_evento_agenda(
                    acao="agenda.conflito.resolvido",
                    payload={
                        "evento_mantido_id": str(out.evento_mantido.id),
                        "evento_cancelado_id": str(out.evento_cancelado.id)
                        if out.evento_cancelado
                        else None,
                        "opcao": d["opcao"],
                        "perfil_tenant": perfil_str,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"agenda conflito resolvido {out.evento_mantido.id}",
                )
        except JustificativaConflitoCurta as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except EventoNaoEncontrado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {
            "evento_mantido_id": str(out.evento_mantido.id),
            "evento_cancelado_id": str(out.evento_cancelado.id) if out.evento_cancelado else None,
            "opcao": d["opcao"],
        }
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="enquadrar-regime")
    def enquadrar_regime(self, request: Request) -> Response:
        """POST /agenda/enquadrar-regime/ — override humano de regime (D-AGE-15). # idempotency-key: required"""
        s = EnquadrarRegimeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        perfil_str = _obter_perfil()
        if not perfil_str:
            return Response({"erro": "perfil indisponível"}, status=status.HTTP_403_FORBIDDEN)

        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_REGIME,
            payload_fingerprint={
                "colaborador_id": str(d["colaborador_id"]),
                "regime": d["regime"],
                "vigencia_inicio": str(d["vigencia_inicio"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoEventoAgendaRepository()
        inp = enquadrar_regime.EnquadrarRegimeInput(
            tenant_id=tenant_id,
            colaborador_id=d["colaborador_id"],
            regime=RegimeJornada(d["regime"]),
            vigencia_inicio=d["vigencia_inicio"],
            vigencia_fim=d.get("vigencia_fim"),
            definido_por_usuario_id=usuario_id,
            justificativa=d["justificativa"],
        )
        try:
            with transaction.atomic():
                out = enquadrar_regime.executar(inp, repo=repo)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {
            "override_id": str(out.override.id),
            "colaborador_id": str(out.override.colaborador_id),
            "regime": out.override.regime.value,
            "vigencia_inicio": out.override.vigencia_inicio.isoformat(),
            "vigencia_fim": out.override.vigencia_fim.isoformat()
            if out.override.vigencia_fim
            else None,
            "fonte": out.override.fonte.value,
        }
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # --- Helpers ---

    @staticmethod
    def _uuid_ou_404(raw: str | None) -> UUID:
        try:
            return UUID(str(raw))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"id inválido: {exc}") from exc

    @staticmethod
    def _falha(chave_id: UUID, tenant_id: UUID, exc: Exception, http_status_code: int) -> Response:
        falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=http_status_code)
        return Response({"erro": str(exc)}, status=http_status_code)
