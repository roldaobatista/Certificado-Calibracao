"""Use case `registrar_no_show` — RegistroNoShow INSERT-only WORM (T-AGE-033 / US-AG-012).

INV-AG-NOSHOW-AR-001 (atomicidade): se ``cobrar_cliente=True``, o no-show exige
``cliente_id`` + ``custo_estimado_centavos > 0`` e chama
``AReceberPort.criar_titulo_manual`` DENTRO da transação do caller. Se a criação do
título falhar, a exceção PROPAGA — o no-show inteiro é revertido (nunca commitar
no-show cobrável sem título). Publica ``agenda.no_show.registrado`` (via view).
Unicidade por evento garantida por ``UniqueConstraint(tenant, evento_id)`` (migration
0009) → 2º no-show concorrente do mesmo evento vira ``TransicaoEventoProibida``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from django.db import IntegrityError

from src.domain.operacao.agenda.entities import EventoAuditoriaAgenda, RegistroNoShow
from src.domain.operacao.agenda.enums import AcaoAuditoria, EstadoEvento
from src.domain.operacao.agenda.erros import EventoNaoEncontrado, TransicaoEventoProibida
from src.domain.operacao.agenda.portas import AReceberPort, EventoAgendaRepository


@dataclass(frozen=True, slots=True)
class RegistrarNoShowInput:
    tenant_id: UUID
    evento_id: UUID
    registrado_por_usuario_id: UUID
    perfil_tenant: str  # server-side
    cobrar_cliente: bool = False
    custo_estimado_centavos: int = 0
    observacao: str = ""
    # Opcional: ID do cliente para criar título (necessário quando cobrar_cliente=True)
    cliente_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class RegistrarNoShowOutput:
    no_show: RegistroNoShow
    titulo_criado: bool  # True se AReceberPort foi chamada com sucesso


def executar(
    inp: RegistrarNoShowInput,
    *,
    repo: EventoAgendaRepository,
    areceber_port: AReceberPort,
) -> RegistrarNoShowOutput:
    """Registra no-show. INSERT-only WORM."""
    agora = datetime.now(UTC)

    evento = repo.obter_por_id(tenant_id=inp.tenant_id, evento_id=inp.evento_id)
    if evento is None:
        raise EventoNaoEncontrado(f"Evento {inp.evento_id} não encontrado.")

    estados_validos = {EstadoEvento.AGENDADO, EstadoEvento.EM_EXECUCAO}
    if evento.estado not in estados_validos:
        raise TransicaoEventoProibida(
            f"Evento {inp.evento_id} em estado {evento.estado.value!r} — "
            "não pode registrar no-show."
        )

    # Cobrança fail-loud: valida ANTES de gravar (A3 / INV-AG-NOSHOW-AR-001).
    # cobrar_cliente exige cliente_id + custo > 0 — sem ramo silencioso.
    cliente_cobranca: UUID | None = None
    if inp.cobrar_cliente:
        if inp.cliente_id is None:
            raise ValueError(
                "No-show cobrável (cobrar_cliente=True) exige cliente_id "
                "(INV-AG-NOSHOW-AR-001)."
            )
        if inp.custo_estimado_centavos <= 0:
            raise ValueError(
                "No-show cobrável exige custo_estimado_centavos > 0 "
                "(INV-AG-NOSHOW-AR-001)."
            )
        cliente_cobranca = inp.cliente_id

    no_show = RegistroNoShow(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        evento_id=inp.evento_id,
        tecnico_id=evento.tecnico_id,
        ocorrido_em=agora,
        custo_estimado=Decimal(inp.custo_estimado_centavos) / 100,
        cobrar_cliente=inp.cobrar_cliente,
        registrado_por_usuario_id=inp.registrado_por_usuario_id,
        criado_em=agora,
        observacao=inp.observacao,
    )
    # UniqueConstraint(tenant, evento_id) (migration 0009) → 2º no-show concorrente
    # do mesmo evento falha no banco; vira 409 (fecha o TOCTOU — INV-AG-NOSHOW-AR-001).
    try:
        repo.salvar_no_show(no_show)
    except IntegrityError as exc:
        raise TransicaoEventoProibida(
            f"No-show já registrado para evento {inp.evento_id} "
            "(unicidade INV-AG-NOSHOW-AR-001)."
        ) from exc

    # Auditoria WORM
    payload_resumo = json.dumps(
        {
            "cobrar_cliente": inp.cobrar_cliente,
            "custo_estimado_centavos": inp.custo_estimado_centavos,
            "perfil_tenant": inp.perfil_tenant,
        },
        ensure_ascii=False,
    )
    auditoria = EventoAuditoriaAgenda(
        id=uuid4(),
        evento_id=inp.evento_id,
        tenant_id=inp.tenant_id,
        acao=AcaoAuditoria.NO_SHOW,
        actor_usuario_id=inp.registrado_por_usuario_id,
        occurred_at=agora,
        criado_em=agora,
        payload_resumo=payload_resumo,
    )
    repo.salvar_auditoria(auditoria)

    # Cobrança via AReceberPort DENTRO da transação do caller — a falha PROPAGA
    # (A1 / atomicidade INV-AG-NOSHOW-AR-001): nunca commitar no-show cobrável sem
    # título. Adapter real na Fatia 3 (GATE-AGE-AR / GATE-AGE-NO-SHOW-AGENDA).
    titulo_criado = False
    if cliente_cobranca is not None:
        from src.domain.shared.value_objects import Dinheiro

        areceber_port.criar_titulo_manual(
            tenant_id=inp.tenant_id,
            cliente_id=cliente_cobranca,
            valor=Dinheiro(centavos=inp.custo_estimado_centavos, moeda="BRL"),
            descricao=f"No-show evento {inp.evento_id}",
            perfil_no_evento=inp.perfil_tenant,
            referencia_evento_id=inp.evento_id,
        )
        titulo_criado = True

    return RegistrarNoShowOutput(no_show=no_show, titulo_criado=titulo_criado)
