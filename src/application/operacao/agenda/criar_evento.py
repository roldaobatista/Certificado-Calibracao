"""Use case `criar_evento` — criação de EventoAgenda tipo OS (T-AGE-031 / US-AG-001/002/013).

Fluxo:
  1. Resolve regime via porta (server-side — INV-AG-REGIME-001).
  2. Valida CNH se motorista_profissional + aloca_em_umc (INV-AG-CNH-001).
  3. Valida feriado (D-AGE-10).
  4. Valida jornada UMC perfil-agnóstico (INV-AG-JORNADA-UMC-001).
  5. Tenta gravar EventoAgenda — IntegrityError do EXCLUDE GIST → ConflitoAgenda 409.
  6. Grava EventoAuditoriaAgenda(criado) WORM.
  7. Se regime indeterminado: audit adicional.

Sem advisory lock — o EXCLUDE GIST é o mecanismo de unicidade (PLAN-AGE-06).
Perfil e regime SEMPRE server-side (INV-AG-PERFIL-001 / INV-AG-REGIME-001).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from django.db import IntegrityError

from src.domain.operacao.agenda.entities import EventoAgenda, EventoAuditoriaAgenda
from src.domain.operacao.agenda.enums import (
    AcaoAuditoria,
    EstadoEvento,
    FonteRegime,
    RegimeJornada,
    TipoEvento,
)
from src.domain.operacao.agenda.erros import (
    ConflitoAgenda,
    FeriadoNaoConfirmado,
    JornadaUMCViolada,
    MotoristaSemCNH,
)
from src.domain.operacao.agenda.jornada import EventoSimples, validar_jornada_umc
from src.domain.operacao.agenda.portas import (
    ColaboradorAgendaPort,
    EventoAgendaRepository,
    OSSchedulingPort,
    RTSubstitutoPort,
)
from src.domain.operacao.agenda.value_objects import Janela, TecnicoJornada


def _para_evento_simples(evento: EventoAgenda) -> EventoSimples:
    """Converte EventoAgenda → EventoSimples para validação de jornada."""
    return EventoSimples(
        tipo=evento.tipo,
        janela=Janela(inicia_at=evento.inicia_at, termina_at=evento.termina_at),
    )

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CriarEventoInput:
    """Payload de criação de evento de OS.

    ``perfil_tenant`` NUNCA vem do payload (server-side — INV-AG-PERFIL-001).
    ``atividade_id`` obrigatório quando ``tipo=os`` (INV-AG-ATIVIDADE-001).
    """

    tenant_id: UUID
    tecnico_id: UUID
    janela: Janela
    aloca_em_umc: bool
    perfil_tenant: str  # A/B/C/D — server-side
    criado_por_usuario_id: UUID
    tipo: TipoEvento = TipoEvento.OS
    atividade_id: UUID | None = None
    os_id: UUID | None = None
    recorrencia_id: UUID | None = None
    ocorrencia_dt: datetime | None = None
    confirmar_feriado: bool = False
    descricao_publica: str = ""
    acordo_coletivo_12h: bool = False


@dataclass(frozen=True, slots=True)
class CriarEventoOutput:
    evento: EventoAgenda
    regime_era_indeterminado: bool = False


def executar(
    inp: CriarEventoInput,
    *,
    repo: EventoAgendaRepository,
    colaborador_port: ColaboradorAgendaPort,
    os_port: OSSchedulingPort,
    rt_port: RTSubstitutoPort,
) -> CriarEventoOutput:
    """Cria EventoAgenda. Raise em qualquer violação antes de gravar."""
    agora = datetime.now(UTC)
    data_slot: date = inp.janela.inicia_at.date()

    # 1. Resolve regime (server-side, perfil-agnóstico)
    regime_resolvido = colaborador_port.regime_jornada(
        tenant_id=inp.tenant_id,
        colaborador_id=inp.tecnico_id,
        na_data=data_slot,
    )
    regime_era_indeterminado = regime_resolvido.fonte == FonteRegime.INDETERMINADO

    # 2. CNH — antes de qualquer gravação
    if inp.aloca_em_umc and regime_resolvido.regime == RegimeJornada.MOTORISTA_PROFISSIONAL:
        pendencia = colaborador_port.pendencia_cnh(
            tenant_id=inp.tenant_id,
            colaborador_id=inp.tecnico_id,
        )
        if pendencia:
            raise MotoristaSemCNH(
                f"Técnico {inp.tecnico_id} tem pendência de CNH (INV-AG-CNH-001)."
            )

    # 3. Feriado
    if not inp.confirmar_feriado:
        feriados = repo.listar_feriados(
            tenant_id=inp.tenant_id,
            data_inicio=data_slot,
            data_fim=data_slot,
        )
        if feriados:
            descricoes = ", ".join(f.descricao for f in feriados)
            raise FeriadoNaoConfirmado(
                f"Data {data_slot} é feriado ({descricoes}). "
                "Envie `confirmar_feriado=true` para agendar mesmo assim."
            )

    # 4. Jornada UMC (validar antes de gravar — R9)
    if inp.aloca_em_umc:
        eventos_dia = repo.listar_por_tecnico_no_dia(
            tenant_id=inp.tenant_id,
            tecnico_id=inp.tecnico_id,
            data=data_slot,
        )
        tecnico_jornada = TecnicoJornada(
            tenant_id=inp.tenant_id,
            colaborador_id=inp.tecnico_id,
            is_tecnico_campo=True,
            aloca_em_umc=True,
        )
        resultado = validar_jornada_umc(
            tecnico=tecnico_jornada,
            regime=regime_resolvido.regime,
            janela=inp.janela,
            eventos_existentes=[_para_evento_simples(ev) for ev in eventos_dia],
            acordo_coletivo_12h=inp.acordo_coletivo_12h,
        )
        if not resultado.ok and resultado.violacao is not None:
            raise JornadaUMCViolada(
                f"Jornada UMC violada: {resultado.violacao}. "
                f"Faltam {resultado.faltante_min} min."
                + (
                    f" Próximo slot: {resultado.proximo_slot.isoformat()}."
                    if resultado.proximo_slot
                    else ""
                )
            )

    # 5. Monta entidade (inicia_at / termina_at, não janela)
    evento = EventoAgenda(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        tecnico_id=inp.tecnico_id,
        tipo=inp.tipo,
        estado=EstadoEvento.AGENDADO,
        inicia_at=inp.janela.inicia_at,
        termina_at=inp.janela.termina_at,
        aloca_em_umc=inp.aloca_em_umc,
        criado_por_usuario_id=inp.criado_por_usuario_id,
        criado_em=agora,
        atualizado_em=agora,
        revision=0,
        atividade_id=inp.atividade_id,
        os_id=inp.os_id,
        recorrencia_id=inp.recorrencia_id,
        ocorrencia_dt=inp.ocorrencia_dt,
        confirmar_feriado=inp.confirmar_feriado,
        descricao_publica=inp.descricao_publica,
    )

    # 6. Persiste — IntegrityError do EXCLUDE GIST → 409
    try:
        repo.salvar_novo(evento)
    except IntegrityError as exc:
        raise ConflitoAgenda(
            f"Conflito de agenda para técnico {inp.tecnico_id} "
            f"no slot {inp.janela.inicia_at}-{inp.janela.termina_at}."
        ) from exc

    # 7. Auditoria WORM (payload_resumo como JSON string)
    payload_resumo = json.dumps(
        {
            "tipo": inp.tipo.value,
            "inicia_at": inp.janela.inicia_at.isoformat(),
            "termina_at": inp.janela.termina_at.isoformat(),
            "aloca_em_umc": inp.aloca_em_umc,
            "perfil_tenant": inp.perfil_tenant,
            "regime": regime_resolvido.regime.value,
            "fonte_regime": regime_resolvido.fonte.value,
        },
        ensure_ascii=False,
    )
    auditoria = EventoAuditoriaAgenda(
        id=uuid4(),
        evento_id=evento.id,
        tenant_id=inp.tenant_id,
        acao=AcaoAuditoria.CRIADO,
        actor_usuario_id=inp.criado_por_usuario_id,
        occurred_at=agora,
        criado_em=agora,
        payload_resumo=payload_resumo,
    )
    repo.salvar_auditoria(auditoria)

    # 8. Regime indeterminado: auditoria adicional + warning
    if regime_era_indeterminado:
        logger.warning(
            "agenda_criar_evento: regime indeterminado para tecnico %s — "
            "pendência de enquadramento humano (INV-AG-REGIME-001)",
            inp.tecnico_id,
            extra={"tenant_id": str(inp.tenant_id)},
        )
        payload_indeterminado = json.dumps(
            {
                "tecnico_id": str(inp.tecnico_id),
                "regime_resolvido": regime_resolvido.regime.value,
                "fonte": regime_resolvido.fonte.value,
            },
            ensure_ascii=False,
        )
        auditoria_regime = EventoAuditoriaAgenda(
            id=uuid4(),
            evento_id=evento.id,
            tenant_id=inp.tenant_id,
            acao=AcaoAuditoria.REGIME_INDETERMINADO,
            actor_usuario_id=inp.criado_por_usuario_id,
            occurred_at=agora,
            criado_em=agora,
            payload_resumo=payload_indeterminado,
        )
        repo.salvar_auditoria(auditoria_regime)

    return CriarEventoOutput(evento=evento, regime_era_indeterminado=regime_era_indeterminado)
