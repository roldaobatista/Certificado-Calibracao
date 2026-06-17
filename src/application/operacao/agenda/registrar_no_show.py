"""Use case `registrar_no_show` — RegistroNoShow INSERT-only WORM (T-AGE-033 / US-AG-012).

Se ``cobrar_cliente=True``, chama ``AReceberPort.criar_titulo_manual`` (FAKE em testes,
adapter real na Fatia 3 — GATE-AGE-AR). Publica ``agenda.no_show.registrado`` (via view).
INV-AG-NOSHOW-AR-001: cobrável → sempre chama AReceber.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.operacao.agenda.entities import EventoAuditoriaAgenda, RegistroNoShow
from src.domain.operacao.agenda.enums import AcaoAuditoria, EstadoEvento
from src.domain.operacao.agenda.erros import EventoNaoEncontrado, TransicaoEventoProibida
from src.domain.operacao.agenda.portas import AReceberPort, EventoAgendaRepository

logger = logging.getLogger(__name__)


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
    repo.salvar_no_show(no_show)

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

    # Cobrança via AReceberPort (FAKE Fatia 2; adapter real Fatia 3 — GATE-AGE-AR)
    titulo_criado = False
    if inp.cobrar_cliente and inp.custo_estimado_centavos > 0:
        try:
            from src.domain.shared.value_objects import Dinheiro

            areceber_port.criar_titulo_manual(
                tenant_id=inp.tenant_id,
                cliente_id=inp.cliente_id or UUID(int=0),
                valor=Dinheiro(centavos=inp.custo_estimado_centavos, moeda="BRL"),
                descricao=f"No-show evento {inp.evento_id}",
                perfil_no_evento=inp.perfil_tenant,
                referencia_evento_id=inp.evento_id,
            )
            titulo_criado = True
        except Exception:
            logger.error(
                "registrar_no_show: falha ao criar título em AReceber para evento %s",
                inp.evento_id,
                exc_info=True,
                extra={"tenant_id": str(inp.tenant_id)},
            )

    return RegistrarNoShowOutput(no_show=no_show, titulo_criado=titulo_criado)
