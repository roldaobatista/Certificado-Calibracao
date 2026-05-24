"""ViewSets DRF M3 OS Fase 8 (T-OS-094..104).

Endpoints REST expondo use cases da Fase 5 + queries da Fase 6.

Autorizacao via RequireAuthz (DEFAULT_PERMISSION_CLASSES) + ACTION_MAP:
- `os.ler` para list / retrieve / timeline / minhas
- `os.criar` para criar (consumer Orcamento.Aprovado eh a via primaria;
  POST /v1/os/ aqui eh OS avulsa balcao US-OS-015)
- `os.atualizar` para cancelar / reabrir / atividade.*
- `atividade.executar` para iniciar / concluir / marcar_nc / resolver_nc

Multi-tenant: tenant_id via active_tenant_context. NUNCA passa em
querystring/body — RLS bloqueia se contexto ausente.

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP — mesmo
# pattern de clientes/views.py.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from src.application.operacao.os.adicionar_atividade import (
    AdicionarAtividadeInput,
    ErroAdicionarAtividade,
    adicionar_atividade,
)
from src.application.operacao.os.cancelar import (
    CancelarOSInput,
    ErroCancelar,
    cancelar_os,
)
from src.application.operacao.os.concluir_atividade import (
    ConcluirAtividadeInput,
    ErroConcluirAtividade,
    concluir_atividade,
)
from src.application.operacao.os.iniciar_atividade import (
    ErroIniciarAtividade,
    IniciarAtividadeInput,
    iniciar_atividade,
)
from src.application.operacao.os.operacoes_avancadas import (
    ErroReabrir,
    ErroTransferir,
    ReabrirOSInput,
    ReagendarAtividadeInput,
    TransferirTecnicoInput,
    reabrir_os,
    reagendar_atividade,
    transferir_tecnico,
)
from src.application.operacao.os.queries.listagem import (
    listar_os,
    os_do_tecnico,
)
from src.application.operacao.os.queries.timeline import timeline_da_os
from src.application.operacao.os.queries.visao_360 import visao_360_da_os
from src.domain.operacao.os.value_objects import (
    MotivoCancelamento,
    TipoAtividade,
)
from src.infrastructure.multitenant.context import (
    active_tenant_context,
    usuario_id_context,
)
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository
from src.infrastructure.ordens_servico.serializers import (
    AdicionarAtividadeRequestSerializer,
    CancelarOSRequestSerializer,
    ConcluirAtividadeRequestSerializer,
    IniciarAtividadeRequestSerializer,
    ReabrirOSRequestSerializer,
    ReagendarAtividadeRequestSerializer,
    TransferirTecnicoRequestSerializer,
)


def _active_tenant_ou_403() -> UUID:
    tid = active_tenant_context.get()
    if tid is None:
        raise NotFound("Tenant context ausente")
    return tid


def _erro_response(exc) -> Response:
    """Mapeia ErroAbrirOS / ErroAdicionarAtividade / etc -> Response."""
    return Response(
        {"codigo": exc.codigo, "detalhe": exc.detalhe},
        status=exc.http_status,
    )


# =============================================================
# OS ViewSet (GET list / GET retrieve / timeline / cancelar / reabrir / minhas)
# =============================================================


class OSViewSet(viewsets.ViewSet):
    """OS — listagem, visao 360, timeline, cancel/reabrir."""

    authz_purpose = "execucao_contrato"
    ACTION_MAP = {
        "list": "os.ler",
        "retrieve": "os.ler",
        "timeline": "os.ler",
        "minhas": "os.ler",
        "cancelar": "os.atualizar",
        "reabrir": "os.atualizar",
    }

    def get_authz_action(self, request) -> str | None:
        action = getattr(self, "action", None)
        return self.ACTION_MAP.get(action) if action else None

    def get_authz_resource(self, request):
        return {}

    # GET /v1/os/
    def list(self, request):
        tid = _active_tenant_ou_403()
        repo = DjangoOSRepository()
        estado = request.query_params.get("estado")
        cliente_id = request.query_params.get("cliente_id")
        equipamento_id = request.query_params.get("equipamento_id")
        limit = int(request.query_params.get("limit", "50"))
        offset = int(request.query_params.get("offset", "0"))
        try:
            items = listar_os(
                tenant_id=tid,
                repository=repo,
                estado=estado,
                cliente_id=UUID(cliente_id) if cliente_id else None,
                equipamento_id=UUID(equipamento_id) if equipamento_id else None,
                limit=limit,
                offset=offset,
            )
        except ValueError as exc:
            return Response({"codigo": "ParametroInvalido", "detalhe": str(exc)}, status=400)
        return Response(
            {
                "items": [
                    {
                        "os_id": str(i.os_id),
                        "numero_os": i.numero_os,
                        "estado": i.estado,
                        "tipo_predominante": i.tipo_predominante,
                        "valor_total_atualizado": str(i.valor_total_atualizado),
                        "nao_conformidade_global": i.nao_conformidade_global,
                        "criada_em": i.criada_em.isoformat(),
                    }
                    for i in items
                ],
                "limit": limit,
                "offset": offset,
            }
        )

    # GET /v1/os/{id}/
    def retrieve(self, request, pk=None):
        _active_tenant_ou_403()
        repo = DjangoOSRepository()
        try:
            visao = visao_360_da_os(UUID(pk), repo)
        except (ValueError, TypeError):
            return Response({"codigo": "OSIdInvalido"}, status=400)
        if visao is None:
            return Response({"codigo": "OSNaoEncontrada"}, status=404)
        return Response(
            {
                "os_id": str(visao.os_id),
                "numero_os": visao.numero_os,
                "estado": visao.estado,
                "tipo_predominante": visao.tipo_predominante,
                "nao_conformidade_global": visao.nao_conformidade_global,
                "valor_total": str(visao.valor_total),
                "valor_total_atualizado": str(visao.valor_total_atualizado),
                "criada_em": visao.criada_em.isoformat(),
                "atualizada_em": visao.atualizada_em.isoformat(),
                "atividades": [
                    {
                        "atividade_id": str(a.atividade_id),
                        "tipo": a.tipo,
                        "sequencia": a.sequencia,
                        "estado": a.estado,
                        "tecnico_executor_id": str(a.tecnico_executor_id)
                        if a.tecnico_executor_id
                        else None,
                        "valor_unitario_snapshot": str(a.valor_unitario_snapshot),
                        "tem_aceite": a.tem_aceite,
                        "tem_dispensa": a.tem_dispensa,
                        "tem_nc_ativa": a.tem_nc_ativa,
                        "qtd_fotos": a.qtd_fotos,
                    }
                    for a in visao.atividades
                ],
            }
        )

    # GET /v1/os/{id}/timeline/
    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        _active_tenant_ou_403()
        repo = DjangoOSRepository()
        try:
            limit = int(request.query_params.get("limit", "100"))
            eventos = timeline_da_os(UUID(pk), repo, limit=limit)
        except (ValueError, TypeError) as exc:
            return Response({"codigo": "ParametroInvalido", "detalhe": str(exc)}, status=400)
        return Response(
            {
                "items": [
                    {
                        "evento_id": str(e.evento_id),
                        "tipo": e.tipo,
                        "atividade_id": str(e.atividade_id) if e.atividade_id else None,
                        "payload_data": e.payload_data,
                        "correlation_id": str(e.correlation_id),
                        "occurred_at": e.occurred_at.isoformat(),
                    }
                    for e in eventos
                ]
            }
        )

    # GET /v1/os/minhas/
    @action(detail=False, methods=["get"])
    def minhas(self, request):
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        if user_id is None:
            return Response({"codigo": "UsuarioAusente"}, status=403)
        repo = DjangoOSRepository()
        items = os_do_tecnico(
            tenant_id=tid,
            tecnico_user_id=user_id,
            repository=repo,
            limit=int(request.query_params.get("limit", "50")),
        )
        return Response(
            {
                "items": [
                    {
                        "os_id": str(i.os_id),
                        "numero_os": i.numero_os,
                        "estado": i.estado,
                    }
                    for i in items
                ]
            }
        )

    # POST /v1/os/{id}/cancelar/
    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        ser = CancelarOSRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            motivo = MotivoCancelamento(ser.validated_data["motivo"])
        except (ValueError, TypeError) as exc:
            return Response({"codigo": "MotivoInvalido", "detalhe": str(exc)}, status=400)
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = cancelar_os(
                    payload=CancelarOSInput(
                        os_id=UUID(pk),
                        usuario_id=user_id or uuid4(),
                        motivo=motivo,
                        correlation_id=uuid4(),
                        cancelada_em=datetime.now(UTC),
                    ),
                    repository=repo,
                )
        except ErroCancelar as exc:
            return _erro_response(exc)
        return Response(
            {
                "os_id": str(res.os_id),
                "atividades_canceladas": [str(a) for a in res.atividades_canceladas],
            },
            status=status.HTTP_200_OK,
        )

    # POST /v1/os/{id}/reabrir/
    @action(detail=True, methods=["post"])
    def reabrir(self, request, pk=None):
        _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        ser = ReabrirOSRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            motivo = MotivoCancelamento(ser.validated_data["motivo"])
        except (ValueError, TypeError) as exc:
            return Response({"codigo": "MotivoInvalido", "detalhe": str(exc)}, status=400)
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = reabrir_os(
                    payload=ReabrirOSInput(
                        os_origem_id=UUID(pk),
                        motivo=motivo,
                        garantia_procedente=ser.validated_data["garantia_procedente"],
                        chamado_origem_id=ser.validated_data.get("chamado_origem_id"),
                        sucessao_societaria_id=ser.validated_data.get(
                            "sucessao_societaria_id"
                        ),
                        correlation_id=uuid4(),
                        reaberta_em=datetime.now(UTC),
                        reaberta_por_user_id=user_id,
                    ),
                    repository=repo,
                )
        except ErroReabrir as exc:
            return _erro_response(exc)
        return Response(
            {
                "os_id_nova": str(res.os_id_nova),
                "numero_os_nova": res.numero_os_nova,
                "atividades_clonadas": [str(a) for a in res.atividades_clonadas],
            },
            status=status.HTTP_201_CREATED,
        )


# =============================================================
# Atividade ViewSet (POST adicionar / iniciar / concluir / reagendar / transferir)
# =============================================================


class AtividadeViewSet(viewsets.ViewSet):
    """Atividade da OS — adicionar + lifecycle."""

    authz_purpose = "execucao_contrato"
    ACTION_MAP = {
        "criar": "os.atualizar",
        "iniciar": "atividade.executar",
        "concluir": "atividade.executar",
        "reagendar": "os.atualizar",
        "transferir": "os.atualizar",
    }

    def get_authz_action(self, request) -> str | None:
        action = getattr(self, "action", None)
        return self.ACTION_MAP.get(action) if action else None

    def get_authz_resource(self, request):
        return {}

    # POST /v1/os/{os_id}/atividades/
    @action(detail=False, methods=["post"], url_path=r"os/(?P<os_id>[^/.]+)/atividades")
    def criar(self, request, os_id=None):
        _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        ser = AdicionarAtividadeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = adicionar_atividade(
                    payload=AdicionarAtividadeInput(
                        os_id=UUID(os_id),
                        tipo=TipoAtividade(ser.validated_data["tipo"]),
                        sequencia=ser.validated_data["sequencia"],
                        valor_unitario=Decimal(
                            str(ser.validated_data["valor_unitario"])
                        ),
                        correlation_id=uuid4(),
                        solicitada_em=datetime.now(UTC),
                        solicitada_por_user_id=user_id,
                    ),
                    repository=repo,
                )
        except ErroAdicionarAtividade as exc:
            return _erro_response(exc)
        return Response(
            {
                "atividade_id": str(res.atividade_id),
                "os_id": str(res.os_id),
                "sequencia": res.sequencia,
            },
            status=status.HTTP_201_CREATED,
        )

    # POST /v1/atividades/{id}/iniciar/
    @action(detail=True, methods=["post"])
    def iniciar(self, request, pk=None):
        _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        if user_id is None:
            return Response({"codigo": "UsuarioAusente"}, status=403)
        ser = IniciarAtividadeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = iniciar_atividade(
                    payload=IniciarAtividadeInput(
                        atividade_id=UUID(pk),
                        usuario_id=user_id,
                        correlation_id=uuid4(),
                        client_event_id=ser.validated_data["client_event_id"],
                        iniciada_em=datetime.now(UTC),
                        geo_lat=ser.validated_data.get("geo_lat"),
                        geo_long=ser.validated_data.get("geo_long"),
                        geo_municipio_hash=ser.validated_data.get(
                            "geo_municipio_hash", ""
                        ),
                    ),
                    repository=repo,
                )
        except ErroIniciarAtividade as exc:
            return _erro_response(exc)
        return Response(
            {
                "atividade_id": str(res.atividade_id),
                "os_id": str(res.os_id),
                "os_transitou_para_em_execucao": res.os_transitou_para_em_execucao,
            }
        )

    # POST /v1/atividades/{id}/concluir/
    @action(detail=True, methods=["post"])
    def concluir(self, request, pk=None):
        _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        if user_id is None:
            return Response({"codigo": "UsuarioAusente"}, status=403)
        ser = ConcluirAtividadeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = concluir_atividade(
                    payload=ConcluirAtividadeInput(
                        atividade_id=UUID(pk),
                        usuario_id=user_id,
                        correlation_id=uuid4(),
                        concluida_em=datetime.now(UTC),
                        aceite_dispensado=ser.validated_data["aceite_dispensado"],
                    ),
                    repository=repo,
                )
        except ErroConcluirAtividade as exc:
            return _erro_response(exc)
        return Response(
            {
                "atividade_id": str(res.atividade_id),
                "os_id": str(res.os_id),
                "os_transitou_para_concluida": res.os_transitou_para_concluida,
                "tipo_predominante": res.tipo_predominante,
            }
        )

    # POST /v1/atividades/{id}/reagendar/
    @action(detail=True, methods=["post"])
    def reagendar(self, request, pk=None):
        _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        ser = ReagendarAtividadeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = reagendar_atividade(
                    payload=ReagendarAtividadeInput(
                        atividade_id=UUID(pk),
                        nova_agendada_para=ser.validated_data["nova_agendada_para"],
                        correlation_id=uuid4(),
                        solicitada_em=datetime.now(UTC),
                        solicitada_por_user_id=user_id,
                    ),
                    repository=repo,
                )
        except ErroTransferir as exc:
            return _erro_response(exc)
        return Response({"atividade_id": str(res.atividade_id)})

    # POST /v1/atividades/{id}/transferir/
    @action(detail=True, methods=["post"])
    def transferir(self, request, pk=None):
        _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        ser = TransferirTecnicoRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            motivo = MotivoCancelamento(ser.validated_data["motivo"])
        except (ValueError, TypeError) as exc:
            return Response({"codigo": "MotivoInvalido", "detalhe": str(exc)}, status=400)
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = transferir_tecnico(
                    payload=TransferirTecnicoInput(
                        atividade_id=UUID(pk),
                        novo_tecnico_id=ser.validated_data["novo_tecnico_id"],
                        motivo=motivo,
                        correlation_id=uuid4(),
                        transferida_em=datetime.now(UTC),
                        solicitada_por_user_id=user_id,
                    ),
                    repository=repo,
                )
        except ErroTransferir as exc:
            return _erro_response(exc)
        return Response({"atividade_id": str(res.atividade_id)})
