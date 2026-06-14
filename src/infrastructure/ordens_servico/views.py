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

import hashlib
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
    CancelarAtividadeInput,
    CancelarOSInput,
    ErroCancelar,
    cancelar_atividade,
    cancelar_os,
)
from src.application.operacao.os.coletar_aceite import (
    ColetarAceiteInput,
    ErroColetarAceite,
    coletar_aceite_atividade,
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
from src.application.operacao.os.marcar_nao_conformidade import (
    ErroMarcarNC,
    ErroResolverNC,
    MarcarNCInput,
    ResolverNCInput,
    marcar_nao_conformidade,
    resolver_nc,
)
from src.application.operacao.os.operacoes_avancadas import (
    CriarOSAvulsaInput,
    DispensarAceiteInput,
    ErroDispensar,
    ErroNoShow,
    ErroOSAvulsa,
    ErroReabrir,
    ErroTransferir,
    ItemOSAvulsa,
    MarcarNoShowInput,
    ReabrirOSInput,
    ReagendarAtividadeInput,
    TransferirTecnicoInput,
    criar_os_avulsa,
    dispensar_aceite_cliente,
    marcar_no_show,
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
    PrecedenteDispensa,
    TipoAtividade,
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

# Endpoints registrados pro service de idempotencia (IDEMP-001 / P-EQP-T6
# horizontal F-A). String estavel — usada como parte da UNIQUE
# (tenant_id, endpoint, chave). NUNCA renomear sem migration de retrofit.
ENDPOINT_OS_CANCELAR = "os.cancelar"
ENDPOINT_OS_REABRIR = "os.reabrir"
ENDPOINT_OS_ATIVIDADE_CRIAR = "os.atividade.criar"
ENDPOINT_OS_ATIVIDADE_INICIAR = "os.atividade.iniciar"
ENDPOINT_OS_ATIVIDADE_CONCLUIR = "os.atividade.concluir"
ENDPOINT_OS_ATIVIDADE_REAGENDAR = "os.atividade.reagendar"
ENDPOINT_OS_ATIVIDADE_TRANSFERIR = "os.atividade.transferir"
# Endpoints novos M3 P5 (PROD-M3-01 — 6 use cases sem REST + OS avulsa).
ENDPOINT_OS_ATIVIDADE_CANCELAR = "os.atividade.cancelar"
ENDPOINT_OS_ATIVIDADE_NC = "os.atividade.marcar_nc"
ENDPOINT_OS_ATIVIDADE_NC_RESOLVER = "os.atividade.resolver_nc"
ENDPOINT_OS_ATIVIDADE_ACEITE = "os.atividade.aceite"
ENDPOINT_OS_ATIVIDADE_DISPENSA = "os.atividade.dispensa"
ENDPOINT_OS_ATIVIDADE_NO_SHOW = "os.atividade.no_show"
ENDPOINT_OS_AVULSA = "os.avulsa"


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


def _resposta_erro_idempotencia(erro: ErroValidacao) -> Response:
    """Mapeia ErroValidacao do service de idempotencia -> Response HTTP."""
    body = {"codigo": erro.codigo, "detalhe": erro.detalhe}
    if erro.headers:
        return Response(body, status=erro.http_status, headers=erro.headers)
    return Response(body, status=erro.http_status)


def _aplicar_idempotencia(
    request,
    tenant_id: UUID,
    usuario_id: UUID,
    endpoint: str,
    payload_fingerprint: dict,
) -> tuple[NovoProcessamento | None, Response | None]:
    """Avalia Idempotency-Key. Retorna (chave_p_concluir, resposta_imediata).

    Caller usa o padrao:
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
        "avulsa": "os.criar",
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
        tid = _active_tenant_ou_403()
        repo = DjangoOSRepository()
        try:
            visao = visao_360_da_os(UUID(pk), repo)
        except (ValueError, TypeError):
            return Response({"codigo": "OSIdInvalido"}, status=400)
        if visao is None:
            return Response({"codigo": "OSNaoEncontrada"}, status=404)
        # SEG-M3-OS-04 (P5 conserto): defesa em profundidade contra IDOR.
        # RLS isola, mas se contexto vazar (test mal isolado, role bypass)
        # retorna 404 em vez de revelar existencia de OS de outro tenant.
        if visao.tenant_id != tid:
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
        tid = _active_tenant_ou_403()
        repo = DjangoOSRepository()
        try:
            limit = int(request.query_params.get("limit", "100"))
            os_obj = repo.get_os_by_id(UUID(pk))
            if os_obj is None:
                return Response({"codigo": "OSNaoEncontrada"}, status=404)
            # SEG-M3-OS-04 (P5 conserto): defesa em profundidade contra IDOR.
            if os_obj.tenant_id != tid:
                return Response({"codigo": "OSNaoEncontrada"}, status=404)
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
        # idempotency-key: required -- IDEMP-001 retry/duplo-clique
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get() or uuid4()
        ser = CancelarOSRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            motivo = MotivoCancelamento(ser.validated_data["motivo"])
        except (ValueError, TypeError) as exc:
            return Response({"codigo": "MotivoInvalido", "detalhe": str(exc)}, status=400)
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_CANCELAR,
            payload_fingerprint={
                "os_id": str(pk),
                "motivo_hash": hashlib.sha256(motivo.texto.encode()).hexdigest(),  # audit-pii-salt: skip -- VO MotivoCancelamento anti-PII; fingerprint de idempotencia
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = cancelar_os(
                    payload=CancelarOSInput(
                        os_id=UUID(pk),
                        usuario_id=user_id,
                        motivo=motivo,
                        correlation_id=uuid4(),
                        cancelada_em=datetime.now(UTC),
                    ),
                    repository=repo,
                )
        except ErroCancelar as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {
            "os_id": str(res.os_id),
            "atividades_canceladas": [str(a) for a in res.atividades_canceladas],
        }
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    # POST /v1/os/{id}/reabrir/
    @action(detail=True, methods=["post"])
    def reabrir(self, request, pk=None):
        # idempotency-key: required -- IDEMP-001 retry duplica OS-filha
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get() or uuid4()
        ser = ReabrirOSRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            motivo = MotivoCancelamento(ser.validated_data["motivo"])
        except (ValueError, TypeError) as exc:
            return Response({"codigo": "MotivoInvalido", "detalhe": str(exc)}, status=400)
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_REABRIR,
            payload_fingerprint={
                "os_origem_id": str(pk),
                "motivo_hash": hashlib.sha256(motivo.texto.encode()).hexdigest(),  # audit-pii-salt: skip -- VO MotivoCancelamento anti-PII; fingerprint de idempotencia
                "garantia_procedente": ser.validated_data["garantia_procedente"],
                "sucessao_societaria_id": str(
                    ser.validated_data.get("sucessao_societaria_id") or ""
                ),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
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
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {
            "os_id_nova": str(res.os_id_nova),
            "numero_os_nova": res.numero_os_nova,
            "atividades_clonadas": [str(a) for a in res.atividades_clonadas],
        }
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # POST /v1/os/avulsa/ — US-OS-015 (M3 P5 batch 4)
    @action(detail=False, methods=["post"])
    def avulsa(self, request):
        # idempotency-key: required -- IDEMP-001
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        d = request.data
        # Validacao inline minima — schema completo entra em GATE-OS-AVULSA-SCHEMA Wave A.
        itens_raw = d.get("itens", [])
        if not itens_raw:
            return Response({"codigo": "OSSemItens"}, status=400)
        itens = tuple(
            ItemOSAvulsa(
                tipo=TipoAtividade(item["tipo"]),
                sequencia=int(item["sequencia"]),
                valor_unitario_snapshot=Decimal(str(item["valor_unitario_snapshot"])),
                requer_recebimento=bool(item.get("requer_recebimento", False)),
                # D-OSME-4 / AC-OSME-003-3: equipamento_id por item.
                equipamento_id=(
                    UUID(str(item["equipamento_id"]))
                    if item.get("equipamento_id")
                    else None
                ),
            )
            for item in itens_raw
        )
        # TL-OSME-03 / AC-OSME-003-3: payload_fingerprint inclui equipamentos dos itens.
        # Evita colisao entre OS avulsas com header igual mas equipamentos diferentes.
        equip_fingerprint = sorted(
            str(item.equipamento_id) for item in itens if item.equipamento_id is not None
        )
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id or uuid4(),
            endpoint=ENDPOINT_OS_AVULSA,
            payload_fingerprint={
                "cliente_id": str(d.get("cliente_id", "")),
                "equipamento_id": str(d.get("equipamento_id", "")),
                "itens_qtd": len(itens),
                "analise_critica_inline_id": str(d.get("analise_critica_inline_id", "")),
                # D-OSME-4: equipamentos dos itens no fingerprint (TL-OSME-03).
                "equip_ids": equip_fingerprint,
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = criar_os_avulsa(
                    payload=CriarOSAvulsaInput(
                        tenant_id=tid,
                        cliente_id=UUID(d["cliente_id"]),
                        cliente_referencia_hash=str(d.get("cliente_referencia_hash", "")),
                        cliente_key_id=str(d.get("cliente_key_id", "")),
                        equipamento_id=(
                            UUID(d["equipamento_id"])
                            if d.get("equipamento_id")
                            else None
                        ),
                        equipamento_recebimento_id=(
                            UUID(d["equipamento_recebimento_id"])
                            if d.get("equipamento_recebimento_id")
                            else None
                        ),
                        itens=itens,
                        analise_critica_inline_id=UUID(d["analise_critica_inline_id"]),
                        analise_critica_snapshot_hash=str(
                            d.get("analise_critica_snapshot_hash", "")
                        ),
                        regra_decisao_acordada=str(d.get("regra_decisao_acordada", "default")),
                        correlation_id=uuid4(),
                        criada_em=datetime.now(UTC),
                        criada_por_user_id=user_id,
                    ),
                    repository=repo,
                )
        except ErroOSAvulsa as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {
            "os_id": str(res.os_id),
            "numero_os": res.numero_os,
            "atividades_planejadas": [str(a) for a in res.atividades_planejadas],
        }
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)


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
        "cancelar": "os.atualizar",
        "marcar_nc": "atividade.executar",
        "resolver_nc": "atividade.executar",
        "aceite": "atividade.executar",
        "dispensa": "os.atualizar",
        "no_show": "atividade.executar",
    }

    def get_authz_action(self, request) -> str | None:
        action = getattr(self, "action", None)
        return self.ACTION_MAP.get(action) if action else None

    def get_authz_resource(self, request):
        return {}

    # POST /v1/os/{os_id}/atividades/
    @action(detail=False, methods=["post"], url_path=r"os/(?P<os_id>[^/.]+)/atividades")
    def criar(self, request, os_id=None):
        # idempotency-key: required -- IDEMP-001 retry duplica atividade
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get() or uuid4()
        ser = AdicionarAtividadeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ATIVIDADE_CRIAR,
            payload_fingerprint={
                "os_id": str(os_id),
                "tipo": str(ser.validated_data["tipo"]),
                "sequencia": ser.validated_data["sequencia"],
                "valor_unitario": str(ser.validated_data["valor_unitario"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
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
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {
            "atividade_id": str(res.atividade_id),
            "os_id": str(res.os_id),
            "sequencia": res.sequencia,
        }
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # POST /v1/atividades/{id}/iniciar/
    @action(detail=True, methods=["post"])
    def iniciar(self, request, pk=None):
        # idempotency-key: required -- IDEMP-001 retry retorna 412 sem replay
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        if user_id is None:
            return Response({"codigo": "UsuarioAusente"}, status=403)
        ser = IniciarAtividadeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ATIVIDADE_INICIAR,
            payload_fingerprint={
                "atividade_id": str(pk),
                "client_event_id": str(ser.validated_data["client_event_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
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
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {
            "atividade_id": str(res.atividade_id),
            "os_id": str(res.os_id),
            "os_transitou_para_em_execucao": res.os_transitou_para_em_execucao,
        }
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body)

    # POST /v1/atividades/{id}/concluir/
    @action(detail=True, methods=["post"])
    def concluir(self, request, pk=None):
        # idempotency-key: required -- IDEMP-001 retry retorna 412 sem replay
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        if user_id is None:
            return Response({"codigo": "UsuarioAusente"}, status=403)
        ser = ConcluirAtividadeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ATIVIDADE_CONCLUIR,
            payload_fingerprint={
                "atividade_id": str(pk),
                "aceite_dispensado": ser.validated_data["aceite_dispensado"],
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
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
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {
            "atividade_id": str(res.atividade_id),
            "os_id": str(res.os_id),
            "os_transitou_para_concluida": res.os_transitou_para_concluida,
            "tipo_predominante": res.tipo_predominante,
        }
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body)

    # POST /v1/atividades/{id}/reagendar/
    @action(detail=True, methods=["post"])
    def reagendar(self, request, pk=None):
        # idempotency-key: required -- IDEMP-001 retry duplica reagendamentos
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get() or uuid4()
        ser = ReagendarAtividadeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ATIVIDADE_REAGENDAR,
            payload_fingerprint={
                "atividade_id": str(pk),
                "nova_agendada_para": ser.validated_data["nova_agendada_para"].isoformat(),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
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
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {"atividade_id": str(res.atividade_id)}
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body)

    # POST /v1/atividades/{id}/transferir/
    @action(detail=True, methods=["post"])
    def transferir(self, request, pk=None):
        # idempotency-key: required -- IDEMP-001 retry notifica tecnico 2x
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get() or uuid4()
        ser = TransferirTecnicoRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            motivo = MotivoCancelamento(ser.validated_data["motivo"])
        except (ValueError, TypeError) as exc:
            return Response({"codigo": "MotivoInvalido", "detalhe": str(exc)}, status=400)
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ATIVIDADE_TRANSFERIR,
            payload_fingerprint={
                "atividade_id": str(pk),
                "novo_tecnico_id": str(ser.validated_data["novo_tecnico_id"]),
                "motivo_hash": hashlib.sha256(motivo.texto.encode()).hexdigest(),  # audit-pii-salt: skip -- VO MotivoCancelamento anti-PII; fingerprint de idempotencia
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
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
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {"atividade_id": str(res.atividade_id)}
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body)

    # =============================================================
    # M3 P5 batch 4 (PROD-M3-01): 6 use cases sem REST -> expostos.
    # Pra ficar enxuto e nao explodir o arquivo, payloads usam validacao
    # inline em vez de serializer DRF formal — gate-rest-serializer-polish
    # Wave A polira validacao de schema.
    # =============================================================

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        # idempotency-key: required -- IDEMP-001
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get() or uuid4()
        try:
            motivo = MotivoCancelamento(request.data.get("motivo", ""))
        except (ValueError, TypeError) as exc:
            return Response({"codigo": "MotivoInvalido", "detalhe": str(exc)}, status=400)
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ATIVIDADE_CANCELAR,
            payload_fingerprint={
                "atividade_id": str(pk),
                "motivo_hash": hashlib.sha256(motivo.texto.encode()).hexdigest(),  # audit-pii-salt: skip -- VO MotivoCancelamento anti-PII; fingerprint de idempotencia
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = cancelar_atividade(
                    payload=CancelarAtividadeInput(
                        atividade_id=UUID(pk),
                        usuario_id=user_id,
                        motivo=motivo,
                        correlation_id=uuid4(),
                        cancelada_em=datetime.now(UTC),
                    ),
                    repository=repo,
                )
        except ErroCancelar as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {"atividade_id": str(res.atividade_id), "os_id": str(res.os_id)}
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body)

    @action(detail=True, methods=["post"], url_path="nc")
    def marcar_nc(self, request, pk=None):
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        if user_id is None:
            return Response({"codigo": "UsuarioAusente"}, status=403)
        try:
            razao = MotivoCancelamento(request.data.get("razao", ""))
        except (ValueError, TypeError) as exc:
            return Response({"codigo": "RazaoInvalida", "detalhe": str(exc)}, status=400)
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ATIVIDADE_NC,
            payload_fingerprint={
                "atividade_id": str(pk),
                "razao_hash": hashlib.sha256(razao.texto.encode()).hexdigest(),  # audit-pii-salt: skip -- VO MotivoCancelamento anti-PII; fingerprint de idempotencia
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = marcar_nao_conformidade(
                    payload=MarcarNCInput(
                        atividade_id=UUID(pk),
                        usuario_id=user_id,
                        razao=razao,
                        correlation_id=uuid4(),
                        marcada_em=datetime.now(UTC),
                    ),
                    repository=repo,
                )
        except ErroMarcarNC as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {"nc_id": str(res.nc_id), "atividade_id": str(res.atividade_id)}
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="resolver-nc")
    def resolver_nc(self, request, pk=None):
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        if user_id is None:
            return Response({"codigo": "UsuarioAusente"}, status=403)
        try:
            causa = MotivoCancelamento(request.data.get("causa_raiz", ""))
            acao = MotivoCancelamento(request.data.get("acao_corretiva", ""))
        except (ValueError, TypeError) as exc:
            return Response({"codigo": "TextoInvalido", "detalhe": str(exc)}, status=400)
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ATIVIDADE_NC_RESOLVER,
            payload_fingerprint={
                "atividade_id": str(pk),
                "causa_hash": hashlib.sha256(causa.texto.encode()).hexdigest(),  # audit-pii-salt: skip -- VO MotivoCancelamento anti-PII; fingerprint de idempotencia
                "acao_hash": hashlib.sha256(acao.texto.encode()).hexdigest(),  # audit-pii-salt: skip -- VO MotivoCancelamento anti-PII; fingerprint de idempotencia
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = resolver_nc(
                    payload=ResolverNCInput(
                        atividade_id=UUID(pk),
                        usuario_id=user_id,
                        causa_raiz=causa,
                        acao_corretiva=acao,
                        correlation_id=uuid4(),
                        eficacia_verificada_em=datetime.now(UTC),
                    ),
                    repository=repo,
                )
        except ErroResolverNC as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {"nc_id": str(res.nc_id), "atividade_id": str(res.atividade_id)}
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body)

    @action(detail=True, methods=["post"])
    def aceite(self, request, pk=None):
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get() or uuid4()
        d = request.data
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ATIVIDADE_ACEITE,
            payload_fingerprint={
                "atividade_id": str(pk),
                "cliente_referencia_hash": str(d.get("cliente_referencia_hash", "")),
                "texto_hash": hashlib.sha256(
                    str(d.get("texto_aceite_bruto", "")).encode()
                ).hexdigest(),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = coletar_aceite_atividade(
                    payload=ColetarAceiteInput(
                        atividade_id=UUID(pk),
                        cliente_referencia_hash=str(d.get("cliente_referencia_hash", "")),
                        cliente_key_id=str(d.get("cliente_key_id", "")),
                        texto_aceite_bruto=str(d.get("texto_aceite_bruto", "")),
                        coletado_em=datetime.now(UTC),
                        correlation_id=uuid4(),
                    ),
                    repository=repo,
                )
        except ErroColetarAceite as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {
            "aceite_id": str(res.aceite_id),
            "atividade_id": str(res.atividade_id),
            "consentimento_id": (
                str(res.consentimento_id) if res.consentimento_id else None
            ),
        }
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def dispensa(self, request, pk=None):
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get() or uuid4()
        d = request.data
        try:
            motivo = MotivoCancelamento(d.get("motivo", ""))
            precedente_tipo = PrecedenteDispensa(d.get("precedente_tipo", ""))
        except (ValueError, TypeError) as exc:
            return Response(
                {"codigo": "PayloadInvalido", "detalhe": str(exc)}, status=400
            )
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ATIVIDADE_DISPENSA,
            payload_fingerprint={
                "atividade_id": str(pk),
                "motivo_hash": hashlib.sha256(motivo.texto.encode()).hexdigest(),  # audit-pii-salt: skip -- VO MotivoCancelamento anti-PII; fingerprint de idempotencia
                "precedente_tipo": precedente_tipo.value,
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = dispensar_aceite_cliente(
                    payload=DispensarAceiteInput(
                        atividade_id=UUID(pk),
                        motivo=motivo,
                        autorizado_por_gerente_id=UUID(d["autorizado_por_gerente_id"]),
                        a3_assinatura_hash=str(d.get("a3_assinatura_hash", "")),
                        a3_certificado_emissor_hash=str(
                            d.get("a3_certificado_emissor_hash", "")
                        ),
                        a3_assinada_em=datetime.fromisoformat(d["a3_assinada_em"]),
                        termo_pdf_b2_uri=str(d.get("termo_pdf_b2_uri", "")),
                        termo_pdf_sha256=str(d.get("termo_pdf_sha256", "")),
                        precedente_tipo=precedente_tipo,
                        precedente_evento_id=(
                            UUID(d["precedente_evento_id"])
                            if d.get("precedente_evento_id")
                            else None
                        ),
                        correlation_id=uuid4(),
                        solicitada_em=datetime.now(UTC),
                    ),
                    repository=repo,
                )
        except ErroDispensar as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {
            "dispensa_id": str(res.dispensa_id),
            "atividade_id": str(res.atividade_id),
        }
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="no-show")
    def no_show(self, request, pk=None):
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get()
        if user_id is None:
            return Response({"codigo": "UsuarioAusente"}, status=403)
        d = request.data
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ATIVIDADE_NO_SHOW,
            payload_fingerprint={
                "atividade_id": str(pk),
                "client_event_id": str(d.get("client_event_id", "")),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None
        repo = DjangoOSRepository()
        try:
            with transaction.atomic():
                res = marcar_no_show(
                    payload=MarcarNoShowInput(
                        atividade_id=UUID(pk),
                        tecnico_user_id=user_id,
                        foto_b2_uri=str(d.get("foto_b2_uri", "")),
                        foto_sha256=str(d.get("foto_sha256", "")),
                        client_event_id=UUID(d["client_event_id"]),
                        client_event_created_at=datetime.fromisoformat(
                            d["client_event_created_at"]
                        ),
                        aviso_terceiros_acknowledged=bool(
                            d.get("aviso_terceiros_acknowledged", False)
                        ),
                        correlation_id=uuid4(),
                        ocorrido_em=datetime.now(UTC),
                        geo_lat=d.get("geo_lat"),
                        geo_long=d.get("geo_long"),
                        geo_municipio_hash=str(d.get("geo_municipio_hash", "")),
                    ),
                    repository=repo,
                )
        except ErroNoShow as exc:
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=exc.http_status,
            )
            return _erro_response(exc)
        body = {"foto_id": str(res.foto_id), "atividade_id": str(res.atividade_id)}
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)
