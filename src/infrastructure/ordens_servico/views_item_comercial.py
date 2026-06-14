"""ViewSet REST de ItemComercialOS — T-OSME-035 / ADR-0082 §7.

Extraído de `views.py` (P9 2026-06-14) para manter o módulo de views da OS
abaixo do limite de tamanho (hook `arquivo-tamanho-aviso`) — o ViewSet de itens
comerciais é uma unidade coesa (CRUD mínimo + recálculo de `valor_total`).

INV-OSME-ITEMCOM-001: item comercial NUNCA tem equipamento_id nem entra no
índice de concorrência; soma em OS.valor_total_atualizado.

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (os.gerir_item_comercial)
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from src.domain.operacao.os.entities import (
    EventoDeOSSnapshot,
    ItemComercialOSSnapshot,
    OSSnapshot,
)
from src.domain.operacao.os.value_objects import (
    TipoEventoDeOS,
    TipoItemComercial,
)
from src.infrastructure.idempotencia.services_idempotencia import (
    concluir_chave,
    falhar_chave,
)
from src.infrastructure.multitenant.context import usuario_id_context
from src.infrastructure.ordens_servico.event_helpers import sanitizar_payload_evento_os
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository
from src.infrastructure.ordens_servico.views import (
    _active_tenant_ou_403,
    _aplicar_idempotencia,
)

# T-OSME-035 / ADR-0082: CRUD item comercial da OS (acao authz os.gerir_item_comercial).
ENDPOINT_OS_ITEM_COMERCIAL_CRIAR = "os.item_comercial.criar"
ENDPOINT_OS_ITEM_COMERCIAL_REMOVER = "os.item_comercial.remover"

# =============================================================
# ItemComercialOS ViewSet — CRUD mínimo (T-OSME-035 / ADR-0082 §7)
# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (os.gerir_item_comercial)
# =============================================================


class ItemComercialOSViewSet(viewsets.ViewSet):
    """CRUD mínimo de ItemComercialOS: adicionar/remover numa OS não-terminal.

    INV-OSME-ITEMCOM-001: item comercial NUNCA tem equipamento_id nem entra
    no índice de concorrência. Soma em OS.valor_total_atualizado (valor corrente
    pós-mutações; OS.valor_total é o original imutável do orçamento).

    Endpoints:
    - POST /v1/os/{os_id}/itens-comerciais/          -> adicionar
    - DELETE /v1/os/{os_id}/itens-comerciais/{id}/   -> remover (soft-delete)
    - GET /v1/os/{os_id}/itens-comerciais/           -> listar
    """

    authz_purpose = "execucao_contrato"
    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP
    ACTION_MAP = {
        "adicionar": "os.gerir_item_comercial",
        "remover": "os.gerir_item_comercial",
        "listar": "os.ler",
    }

    def get_authz_action(self, request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request):
        return {}

    # POST /v1/os/{os_id}/itens-comerciais/
    @action(
        detail=False,
        methods=["post"],
        url_path=r"os/(?P<os_id>[^/.]+)/itens-comerciais",
    )
    def adicionar(self, request, os_id: str | None = None) -> Response:
        """Adiciona item comercial a uma OS nao-terminal.

        INV-OSME-ITEMCOM-001: valor soma em OS.valor_total_atualizado.
        IDEMP-001: Idempotency-Key obrigatória — retry seguro em falha de rede.

        Body: {tipo, descricao_publica, valor, quantidade?, origem_item_id?}
        """
        # idempotency-key: required -- IDEMP-001 retry duplica item
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get() or uuid4()
        d = request.data

        # Validacao inline minima (gate-rest-serializer-polish Wave A polira).
        tipo_raw = d.get("tipo", "")
        try:
            tipo = TipoItemComercial(tipo_raw)
        except (ValueError, TypeError):
            return Response(
                {"codigo": "TipoItemComercialInvalido", "detalhe": f"tipo={tipo_raw!r} invalido"},
                status=400,
            )
        descricao = str(d.get("descricao_publica", "")).strip()
        if not descricao:
            return Response({"codigo": "DescricaoObrigatoria"}, status=400)
        try:
            valor = Decimal(str(d["valor"]))
        except (KeyError, InvalidOperation, ValueError, TypeError):
            return Response({"codigo": "ValorObrigatorio"}, status=400)
        if valor <= Decimal("0"):
            return Response({"codigo": "ValorDeveSerPositivo"}, status=400)
        quantidade = int(d.get("quantidade", 1))
        if quantidade < 1:
            return Response({"codigo": "QuantidadeDeveSerPositiva"}, status=400)
        origem_item_id_raw = d.get("origem_item_id")
        origem_item_id: UUID | None = None
        if origem_item_id_raw:
            try:
                origem_item_id = UUID(str(origem_item_id_raw))
            except (ValueError, AttributeError):
                return Response({"codigo": "OrigemItemIdInvalido"}, status=400)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ITEM_COMERCIAL_CRIAR,
            payload_fingerprint={
                "os_id": str(os_id),
                "tipo": tipo.value,
                "descricao_hash": hashlib.sha256(
                    descricao.encode()
                ).hexdigest(),  # audit-pii-salt: skip -- descricao_publica e texto comercial (deslocamento/taxa), nao PII; hash e fingerprint de idempotencia, nao discriminante de PII
                "valor": str(valor),
                "quantidade": quantidade,
            },
        )
        if resp is not None:
            return resp
        assert novo is not None

        repo = DjangoOSRepository()
        try:
            os_id_uuid = UUID(str(os_id))
        except (ValueError, AttributeError):
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=400,
            )
            return Response({"codigo": "OSIdInvalido"}, status=400)

        with transaction.atomic():
            os_snap = repo.get_os_by_id(os_id_uuid)
            if os_snap is None or os_snap.tenant_id != tid:
                falhar_chave(
                    chave_id=novo.chave_id,  # type: ignore[arg-type]
                    tenant_id=tid,
                    response_status=404,
                )
                return Response({"codigo": "OSNaoEncontrada"}, status=404)

            # INV-OSME-ITEMCOM-001: só permite em OS não-terminal.
            if os_snap.estado.terminal:
                falhar_chave(
                    chave_id=novo.chave_id,  # type: ignore[arg-type]
                    tenant_id=tid,
                    response_status=422,
                )
                return Response(
                    {
                        "codigo": "OSTerminalNaoPermiteItemComercial",
                        "detalhe": f"OS em estado {os_snap.estado.value} nao aceita novos itens.",
                    },
                    status=422,
                )

            item_id = uuid4()
            item_snap = ItemComercialOSSnapshot(
                id=item_id,
                tenant_id=tid,
                os_id=os_id_uuid,
                tipo=tipo,
                descricao_publica=descricao,
                valor=valor,
                quantidade=quantidade,
                origem_item_id=origem_item_id,
            )
            item_salvo = repo.salvar_item_comercial(item_snap)

            # INV-OSME-ITEMCOM-001: soma valor em OS.valor_total_atualizado.
            valor_novo_item = item_salvo.valor * item_salvo.quantidade
            os_atualizada = _recalcular_valor_total_os(os_snap, repo, delta=valor_novo_item)
            repo.salvar_os(os_atualizada)

            # Trilha de auditoria (OBS-001 — mutacao de OS emite evento).
            payload_data, payload_hash = sanitizar_payload_evento_os(
                {
                    "item_id": str(item_salvo.id),
                    "os_id": str(os_id_uuid),
                    "tipo": tipo.value,
                    "valor": str(valor),
                    "quantidade": quantidade,
                    "acao": "item_comercial_adicionado",
                }
            )
            repo.publicar_evento(
                EventoDeOSSnapshot(
                    id=uuid4(),
                    tenant_id=tid,
                    os_id=os_id_uuid,
                    atividade_id=None,
                    tipo=TipoEventoDeOS.OS_ESCOPO_ALTERADO,
                    payload_hash=payload_hash,
                    payload_data=payload_data,
                    correlation_id=uuid4(),
                    actor_user_id=user_id,
                    occurred_at=datetime.now(UTC),
                    criado_em=datetime.now(UTC),
                )
            )

        body = {
            "item_id": str(item_salvo.id),
            "os_id": str(os_id_uuid),
            "tipo": item_salvo.tipo.value,
            "descricao_publica": item_salvo.descricao_publica,
            "valor": str(item_salvo.valor),
            "quantidade": item_salvo.quantidade,
        }
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # DELETE /v1/os/{os_id}/itens-comerciais/{item_id}/
    @action(
        detail=False,
        methods=["delete"],
        url_path=r"os/(?P<os_id>[^/.]+)/itens-comerciais/(?P<item_id>[^/.]+)",
    )
    def remover(self, request, os_id: str | None = None, item_id: str | None = None) -> Response:
        """Remove (soft-delete Padrao A) item comercial de OS nao-terminal.

        INV-OSME-ITEMCOM-001: valor subtraído de OS.valor_total_atualizado.
        IDEMP-001: Idempotency-Key recomendada.
        """
        # idempotency-key: required -- IDEMP-001 retry remove 2x sem efeito (idempotente por natureza do soft-delete)
        tid = _active_tenant_ou_403()
        user_id = usuario_id_context.get() or uuid4()

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tid,
            usuario_id=user_id,
            endpoint=ENDPOINT_OS_ITEM_COMERCIAL_REMOVER,
            payload_fingerprint={"os_id": str(os_id), "item_id": str(item_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None

        repo = DjangoOSRepository()
        try:
            os_id_uuid = UUID(str(os_id))
            item_id_uuid = UUID(str(item_id))
        except (ValueError, AttributeError):
            falhar_chave(
                chave_id=novo.chave_id,  # type: ignore[arg-type]
                tenant_id=tid,
                response_status=400,
            )
            return Response({"codigo": "IdInvalido"}, status=400)

        with transaction.atomic():
            os_snap = repo.get_os_by_id(os_id_uuid)
            if os_snap is None or os_snap.tenant_id != tid:
                falhar_chave(
                    chave_id=novo.chave_id,  # type: ignore[arg-type]
                    tenant_id=tid,
                    response_status=404,
                )
                return Response({"codigo": "OSNaoEncontrada"}, status=404)

            if os_snap.estado.terminal:
                falhar_chave(
                    chave_id=novo.chave_id,  # type: ignore[arg-type]
                    tenant_id=tid,
                    response_status=422,
                )
                return Response(
                    {
                        "codigo": "OSTerminalNaoPermiteRemoverItem",
                        "detalhe": f"OS em estado {os_snap.estado.value} nao aceita remocao de itens.",
                    },
                    status=422,
                )

            # Verifica que o item existe e pertence à OS/tenant (RLS ja protege,
            # mas defesa em profundidade evita mensagens de erro informativas).
            itens = repo.listar_itens_comerciais_por_os(os_id_uuid)
            item_existente = next((i for i in itens if i.id == item_id_uuid), None)
            if item_existente is None:
                falhar_chave(
                    chave_id=novo.chave_id,  # type: ignore[arg-type]
                    tenant_id=tid,
                    response_status=404,
                )
                return Response({"codigo": "ItemComercialNaoEncontrado"}, status=404)

            item_removido = repo.remover_item_comercial(
                item_id_uuid,
                removido_por_usuario_id=user_id,
                motivo="Removido via API",
            )

            # INV-OSME-ITEMCOM-001: subtrai valor de OS.valor_total_atualizado.
            valor_subtraido = item_removido.valor * item_removido.quantidade
            os_atualizada = _recalcular_valor_total_os(os_snap, repo, delta=-valor_subtraido)
            repo.salvar_os(os_atualizada)

            # Trilha de auditoria (OBS-001).
            payload_data, payload_hash = sanitizar_payload_evento_os(
                {
                    "item_id": str(item_id_uuid),
                    "os_id": str(os_id_uuid),
                    "tipo": item_removido.tipo.value,
                    "acao": "item_comercial_removido",
                }
            )
            repo.publicar_evento(
                EventoDeOSSnapshot(
                    id=uuid4(),
                    tenant_id=tid,
                    os_id=os_id_uuid,
                    atividade_id=None,
                    tipo=TipoEventoDeOS.OS_ESCOPO_ALTERADO,
                    payload_hash=payload_hash,
                    payload_data=payload_data,
                    correlation_id=uuid4(),
                    actor_user_id=user_id,
                    occurred_at=datetime.now(UTC),
                    criado_em=datetime.now(UTC),
                )
            )

        body = {"item_id": str(item_id_uuid), "os_id": str(os_id_uuid)}
        concluir_chave(
            chave_id=novo.chave_id,  # type: ignore[arg-type]
            tenant_id=tid,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    # GET /v1/os/{os_id}/itens-comerciais/
    @action(
        detail=False,
        methods=["get"],
        url_path=r"os/(?P<os_id>[^/.]+)/itens-comerciais/lista",
    )
    def listar(self, request, os_id: str | None = None) -> Response:
        """Lista itens comerciais ativos de uma OS (AC-OSME-006-1)."""
        tid = _active_tenant_ou_403()
        repo = DjangoOSRepository()
        try:
            os_id_uuid = UUID(str(os_id))
        except (ValueError, AttributeError):
            return Response({"codigo": "OSIdInvalido"}, status=400)

        os_snap = repo.get_os_by_id(os_id_uuid)
        if os_snap is None or os_snap.tenant_id != tid:
            return Response({"codigo": "OSNaoEncontrada"}, status=404)

        itens = repo.listar_itens_comerciais_por_os(os_id_uuid)
        return Response(
            {
                "os_id": str(os_id_uuid),
                "itens_comerciais": [
                    {
                        "item_id": str(i.id),
                        "tipo": i.tipo.value,
                        "descricao_publica": i.descricao_publica,
                        "valor": str(i.valor),
                        "quantidade": i.quantidade,
                        "origem_item_id": str(i.origem_item_id) if i.origem_item_id else None,
                    }
                    for i in itens
                ],
            }
        )


def _recalcular_valor_total_os(
    os_snap: OSSnapshot,
    repo: DjangoOSRepository,
    delta: Decimal,
) -> OSSnapshot:
    """Aplica delta em valor_total_atualizado (INV-OSME-ITEMCOM-001).

    Retorna novo OSSnapshot com valor atualizado. Use case envolve em
    transaction.atomic — sem risco de dirty read.
    """
    return OSSnapshot(
        id=os_snap.id,
        tenant_id=os_snap.tenant_id,
        numero_os=os_snap.numero_os,
        cliente_id=os_snap.cliente_id,
        cliente_referencia_hash=os_snap.cliente_referencia_hash,
        cliente_key_id=os_snap.cliente_key_id,
        equipamento_id=os_snap.equipamento_id,
        equipamento_recebimento_id=os_snap.equipamento_recebimento_id,
        orcamento_origem_id=os_snap.orcamento_origem_id,
        os_origem_id=os_snap.os_origem_id,
        sucessao_societaria_id=os_snap.sucessao_societaria_id,
        estado=os_snap.estado,
        tipo_predominante=os_snap.tipo_predominante,
        nao_conformidade_global=os_snap.nao_conformidade_global,
        valor_total=os_snap.valor_total,
        valor_total_atualizado=os_snap.valor_total_atualizado + delta,
        analise_critica_id=os_snap.analise_critica_id,
        analise_critica_snapshot_hash=os_snap.analise_critica_snapshot_hash,
        regra_decisao_acordada=os_snap.regra_decisao_acordada,
        criada_em=os_snap.criada_em,
        atualizada_em=os_snap.atualizada_em,
        criada_por_user_id=os_snap.criada_por_user_id,
    )
