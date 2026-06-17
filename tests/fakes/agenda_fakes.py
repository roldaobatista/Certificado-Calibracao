"""Fakes CONFIGURÁVEIS das 6 portas de domínio da agenda (Fatia 2 — T-AGE-030).

Fakes permitem que os testes controlem o comportamento das portas sem acesso
a módulos fechados (OS/colaboradores/CR/RT). Cada fake é configurável via
atributos mutáveis antes de ser injetado no use case.

Uso típico nos testes:
    repo = FakeEventoAgendaRepository()
    colaborador = FakeColaboradorAgendaPort(regime=RegimeJornada.MOTORISTA_PROFISSIONAL)
    rt = FakeRTSubstitutoPort(tem_rt=True)
    ...
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from src.domain.operacao.agenda.entities import (
    EventoAgenda,
    EventoAuditoriaAgenda,
    Feriado,
    RegimeJornadaColaborador,
    RegistroNoShow,
)
from src.domain.operacao.agenda.enums import FonteRegime, RegimeJornada
from src.domain.operacao.agenda.value_objects import RegimeJornadaResolvido

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# FakeEventoAgendaRepository
# ---------------------------------------------------------------------------


class FakeEventoAgendaRepository:
    """Fake in-memory do EventoAgendaRepository."""

    def __init__(self) -> None:
        self._eventos: dict[UUID, EventoAgenda] = {}
        self._auditorias: list[EventoAuditoriaAgenda] = []
        self._no_shows: list[RegistroNoShow] = []
        self._feriados: list[Feriado] = []
        self._regimes: list[RegimeJornadaColaborador] = []

    # --- EventoAgenda ---

    def obter_por_id(self, *, tenant_id: UUID, evento_id: UUID) -> EventoAgenda | None:
        ev = self._eventos.get(evento_id)
        if ev is None or ev.tenant_id != tenant_id:
            return None  # anti-oráculo cross-tenant → None
        return ev

    def salvar_novo(self, evento: EventoAgenda) -> None:
        """Simula EXCLUDE GIST: levanta IntegrityError se overlap com evento ativo."""
        from django.db import IntegrityError

        for ev in self._eventos.values():
            if ev.tenant_id != evento.tenant_id:
                continue
            if ev.tecnico_id != evento.tecnico_id:
                continue
            if ev.estado.value == "cancelado":
                continue
            if ev.id == evento.id:
                continue
            # Half-open overlap: [a,b) ∩ [c,d) ≠ ∅ ↔ a<d AND c<b
            if ev.inicia_at < evento.termina_at and evento.inicia_at < ev.termina_at:
                raise IntegrityError(
                    "EXCLUDE GIST: overlap detected (fake) — "
                    f"evento existente {ev.id} [{ev.inicia_at}-{ev.termina_at})"
                )
        # UNIQUE (recorrencia_id, ocorrencia_dt)
        if evento.recorrencia_id is not None and evento.ocorrencia_dt is not None:
            for ev in self._eventos.values():
                if (
                    ev.tenant_id == evento.tenant_id
                    and ev.recorrencia_id == evento.recorrencia_id
                    and ev.ocorrencia_dt == evento.ocorrencia_dt
                    and ev.id != evento.id
                ):
                    raise IntegrityError(
                        "UNIQUE (recorrencia_id, ocorrencia_dt) violation (fake)"
                    )
        self._eventos[evento.id] = evento

    def atualizar(self, *, tenant_id: UUID, evento: EventoAgenda) -> None:
        import dataclasses
        from datetime import UTC, datetime

        if evento.id not in self._eventos or self._eventos[evento.id].tenant_id != tenant_id:
            raise RuntimeError(f"atualizar: evento {evento.id} não encontrado.")
        # Verifica overlap (exceto o próprio evento)
        from django.db import IntegrityError

        for ev in self._eventos.values():
            if ev.id == evento.id:
                continue
            if ev.tenant_id != tenant_id or ev.tecnico_id != evento.tecnico_id:
                continue
            if ev.estado.value == "cancelado":
                continue
            if ev.inicia_at < evento.termina_at and evento.inicia_at < ev.termina_at:
                raise IntegrityError(
                    f"EXCLUDE GIST: overlap em atualização (fake) — evento {ev.id}"
                )
        updated = dataclasses.replace(evento, atualizado_em=datetime.now(UTC))
        self._eventos[evento.id] = updated

    def listar_por_tecnico_no_dia(
        self,
        *,
        tenant_id: UUID,
        tecnico_id: UUID,
        data: date,
    ) -> list[EventoAgenda]:
        return [
            ev
            for ev in self._eventos.values()
            if ev.tenant_id == tenant_id
            and ev.tecnico_id == tecnico_id
            and ev.inicia_at.date() == data
            and ev.estado.value != "cancelado"
        ]

    def listar_por_tenant(
        self,
        *,
        tenant_id: UUID,
        tecnico_id: UUID | None = None,
        inicia_apos: datetime | None = None,
        inicia_antes: datetime | None = None,
    ) -> list[EventoAgenda]:
        resultado = [ev for ev in self._eventos.values() if ev.tenant_id == tenant_id]
        if tecnico_id is not None:
            resultado = [ev for ev in resultado if ev.tecnico_id == tecnico_id]
        if inicia_apos is not None:
            resultado = [ev for ev in resultado if ev.inicia_at >= inicia_apos]
        if inicia_antes is not None:
            resultado = [ev for ev in resultado if ev.inicia_at < inicia_antes]
        return resultado

    def salvar_auditoria(self, registro: EventoAuditoriaAgenda) -> None:
        self._auditorias.append(registro)

    def salvar_no_show(self, registro: RegistroNoShow) -> None:
        self._no_shows.append(registro)

    def tem_agenda_futura(self, *, tenant_id: UUID, colaborador_id: UUID) -> bool:
        agora = datetime.now(UTC)
        return any(
            ev.tenant_id == tenant_id
            and ev.tecnico_id == colaborador_id
            and ev.inicia_at > agora
            and ev.estado.value != "cancelado"
            for ev in self._eventos.values()
        )

    def listar_feriados(
        self,
        *,
        tenant_id: UUID,
        data_inicio: date,
        data_fim: date,
    ) -> list[Feriado]:
        return [
            f
            for f in self._feriados
            if f.ativo and data_inicio <= f.data <= data_fim
            and (f.tenant_id is None or f.tenant_id == tenant_id)
        ]

    def salvar_feriado(self, feriado: Feriado) -> None:
        self._feriados.append(feriado)

    def salvar_regime_override(self, override: RegimeJornadaColaborador) -> None:
        self._regimes.append(override)

    # Helpers para testes
    def adicionar_feriado(self, data: date, descricao: str = "Feriado", nacional: bool = True, tenant_id: UUID | None = None) -> None:
        """Adiciona feriado no fake sem passar pelo use case."""
        self._feriados.append(
            Feriado(
                id=uuid4(),
                data=data,
                descricao=descricao,
                nacional=nacional,
                tenant_id=tenant_id,
                criado_em=datetime.now(UTC),
                ativo=True,
            )
        )

    def contar_eventos(self) -> int:
        return len(self._eventos)

    def contar_auditorias(self) -> int:
        return len(self._auditorias)


# ---------------------------------------------------------------------------
# FakeColaboradorAgendaPort
# ---------------------------------------------------------------------------


class FakeColaboradorAgendaPort:
    """Fake configurável de ColaboradorAgendaPort.

    Atributos:
        regime: RegimeJornada a retornar (default nao_aplica — sem restrição de jornada).
        fonte: FonteRegime da resolução (default derivado_papel).
        tem_cnh_pendente: True se o técnico tem pendência de CNH.
        is_campo: True se é técnico de campo.
    """

    def __init__(
        self,
        regime: RegimeJornada = RegimeJornada.NAO_APLICA,
        fonte: FonteRegime = FonteRegime.DERIVADO_PAPEL,
        tem_cnh_pendente: bool = False,
        is_campo: bool = True,
    ) -> None:
        self.regime = regime
        self.fonte = fonte
        self.tem_cnh_pendente = tem_cnh_pendente
        self.is_campo = is_campo

    def is_tecnico_campo(self, *, tenant_id: UUID, colaborador_id: UUID) -> bool:
        return self.is_campo

    def pendencia_cnh(self, *, tenant_id: UUID, colaborador_id: UUID) -> bool:
        return self.tem_cnh_pendente

    def regime_jornada(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
        na_data: date,
    ) -> RegimeJornadaResolvido:
        return RegimeJornadaResolvido(regime=self.regime, fonte=self.fonte)


# ---------------------------------------------------------------------------
# FakeOSSchedulingPort
# ---------------------------------------------------------------------------


class FakeOSSchedulingPort:
    """Fake configurável de OSSchedulingPort. No-op seguro."""

    def __init__(self) -> None:
        self.chamadas_atribuir: list[dict[str, Any]] = []
        self.atividades: dict[UUID, dict[str, Any]] = {}

    def atribuir_tecnico(
        self,
        *,
        tenant_id: UUID,
        atividade_id: UUID,
        tecnico_id: UUID,
        agendada_para: datetime,
        actor_usuario_id: UUID,
    ) -> None:
        self.chamadas_atribuir.append(
            {
                "tenant_id": tenant_id,
                "atividade_id": atividade_id,
                "tecnico_id": tecnico_id,
                "agendada_para": agendada_para,
            }
        )

    def obter_atividade(
        self,
        *,
        tenant_id: UUID,
        atividade_id: UUID,
    ) -> dict[str, Any] | None:
        return self.atividades.get(atividade_id)


# ---------------------------------------------------------------------------
# FakeRTSubstitutoPort
# ---------------------------------------------------------------------------


class FakeRTSubstitutoPort:
    """Fake configurável de RTSubstitutoPort.

    Atributos:
        tem_rt: True se há RT competente no slot (default True — sem restrição).
        ausencia_deterministica: True se a ausência é determinística (412).
    """

    def __init__(
        self,
        tem_rt: bool = True,
        ausencia_deterministica: bool = False,
    ) -> None:
        self.tem_rt = tem_rt
        self.ausencia_deterministica = ausencia_deterministica

    def tem_rt_competente_no_slot(
        self,
        *,
        tenant_id: UUID,
        grandeza: str,
        data_slot: date,
    ) -> bool:
        return self.tem_rt

    def eh_deterministica_ausencia(
        self,
        *,
        tenant_id: UUID,
        grandeza: str,
        data_slot: date,
    ) -> bool:
        return self.ausencia_deterministica


# ---------------------------------------------------------------------------
# FakeMapsProvider
# ---------------------------------------------------------------------------


class FakeMapsProvider:
    """Fake de MapsProvider — sempre retorna None (stub Wave A)."""

    def estimar_deslocamento_min(
        self,
        *,
        origem_lat: float,
        origem_lng: float,
        destino_lat: float,
        destino_lng: float,
    ) -> float | None:
        return None  # stub Wave A — GATE-AGE-MAPS


# ---------------------------------------------------------------------------
# FakeNotificacaoClientePort
# ---------------------------------------------------------------------------


class FakeNotificacaoClientePort:
    """Fake de NotificacaoClientePort — registra chamadas em log."""

    def __init__(self) -> None:
        self.avisos_enfileirados: list[dict[str, Any]] = []

    def enfileirar_aviso_reagendamento(
        self,
        *,
        tenant_id: UUID,
        evento_id: UUID,
        cliente_id: UUID,
        nova_janela_inicia: datetime,
        nova_janela_termina: datetime,
    ) -> None:
        self.avisos_enfileirados.append(
            {
                "tenant_id": tenant_id,
                "evento_id": evento_id,
                "cliente_id": cliente_id,
                "nova_janela_inicia": nova_janela_inicia,
                "nova_janela_termina": nova_janela_termina,
            }
        )
        logger.info(
            "fake_notificacao: aviso enfileirado para evento %s (stub — GATE-AGE-OMNICHANNEL)",
            evento_id,
        )


# ---------------------------------------------------------------------------
# FakeAReceberPort
# ---------------------------------------------------------------------------


class FakeAReceberPort:
    """Fake de AReceberPort — simula criação de título em contas-receber.

    Atributos:
        deve_falhar: Se True, levanta RuntimeError ao criar título.
        titulo_ids_criados: Lista de UUIDs gerados.
    """

    def __init__(self, deve_falhar: bool = False) -> None:
        self.deve_falhar = deve_falhar
        self.titulo_ids_criados: list[UUID] = []
        self.chamadas: list[dict[str, Any]] = []

    def criar_titulo_manual(
        self,
        *,
        tenant_id: UUID,
        cliente_id: UUID,
        valor: Any,
        descricao: str,
        perfil_no_evento: str,
        referencia_evento_id: UUID,
    ) -> UUID:
        if self.deve_falhar:
            raise RuntimeError("FakeAReceberPort: falha simulada.")
        titulo_id = uuid4()
        self.titulo_ids_criados.append(titulo_id)
        self.chamadas.append(
            {
                "tenant_id": tenant_id,
                "cliente_id": cliente_id,
                "valor": valor,
                "descricao": descricao,
                "perfil_no_evento": perfil_no_evento,
                "referencia_evento_id": referencia_evento_id,
                "titulo_id_gerado": titulo_id,
            }
        )
        return titulo_id
