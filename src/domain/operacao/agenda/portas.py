"""Portas (Protocols @runtime_checkable) do domínio agenda (Fatia 1a — T-AGE-016).

INV-FIS-003 / D-AGE-5..9: domínio/use case NUNCA importam ORM Django; toda
persistência e integração passa por estes Protocols. O use case sempre recebe
uma implementação injetada — agnóstico da concretização (fake no domínio,
adapter Django na infra).

Portas:
- ``EventoAgendaRepository`` — CRUD do agregado EventoAgenda.
- ``OSSchedulingPort``        — escreve na OS via ``atribuir_tecnico`` (seam D-AGE-5).
- ``ColaboradorAgendaPort``   — papel + CNH + regime de jornada (D-AGE-7/12/15).
- ``RTSubstitutoPort``        — competência RT projetada ao instante do slot (D-AGE-6).
- ``MapsProvider``            — rota/deslocamento (stub Wave A — GATE-AGE-MAPS).
- ``NotificacaoClientePort``  — aviso de reagendamento (stub Wave A — GATE-AGE-OMNICHANNEL).
- ``AReceberPort``            — no-show cobrável → ``criar_titulo_manual`` (D-AGE-9).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol, runtime_checkable
from uuid import UUID

from .entities import (
    EventoAgenda,
    EventoAuditoriaAgenda,
    Feriado,
    RegimeJornadaColaborador,
    RegistroNoShow,
)
from .value_objects import RegimeJornadaResolvido


@runtime_checkable
class EventoAgendaRepository(Protocol):
    """Repositório de ``EventoAgenda`` — porta de persistência.

    Implementação concreta (``DjangoEventoAgendaRepository``) vive em
    ``src/infrastructure/agenda/``. Os use cases recebem sempre uma instância
    injetada.
    """

    def obter_por_id(self, *, tenant_id: UUID, evento_id: UUID) -> EventoAgenda | None:
        """Retorna o evento ou ``None`` (cross-tenant → None via RLS → 404 anti-oráculo)."""
        ...

    def salvar_novo(self, evento: EventoAgenda) -> None:
        """Persiste um evento novo (INSERT)."""
        ...

    def atualizar(self, *, tenant_id: UUID, evento: EventoAgenda) -> None:
        """Atualiza estado + timestamps (bump de ``revision``; trigger WORM enforça)."""
        ...

    def listar_por_tecnico_no_dia(
        self,
        *,
        tenant_id: UUID,
        tecnico_id: UUID,
        data: date,
    ) -> list[EventoAgenda]:
        """Lista eventos do técnico em um dia específico (para validação de jornada)."""
        ...

    def listar_por_tenant(
        self,
        *,
        tenant_id: UUID,
        tecnico_id: UUID | None = None,
        inicia_apos: datetime | None = None,
        inicia_antes: datetime | None = None,
    ) -> list[EventoAgenda]:
        """Lista eventos com filtros opcionais (grade multi-técnico)."""
        ...

    def salvar_auditoria(self, registro: EventoAuditoriaAgenda) -> None:
        """Persiste registro de auditoria WORM (INSERT-only — INV-AG-AUDIT-WORM-001)."""
        ...

    def salvar_no_show(self, registro: RegistroNoShow) -> None:
        """Persiste registro de no-show WORM (INSERT-only)."""
        ...

    def tem_agenda_futura(self, *, tenant_id: UUID, colaborador_id: UUID) -> bool:
        """``True`` se o técnico tem eventos futuros (para ``esta_referenciado``)."""
        ...

    def listar_feriados(
        self,
        *,
        tenant_id: UUID,
        data_inicio: date,
        data_fim: date,
    ) -> list[Feriado]:
        """Lista feriados (nacionais + custom do tenant) no intervalo."""
        ...

    def salvar_feriado(self, feriado: Feriado) -> None:
        """Persiste feriado custom do tenant (INSERT)."""
        ...

    def salvar_regime_override(self, override: RegimeJornadaColaborador) -> None:
        """Persiste override de regime de jornada (INSERT-com-vigência — WORM)."""
        ...


@runtime_checkable
class OSSchedulingPort(Protocol):
    """Porta de escrita na OS via ``atribuir_tecnico`` (D-AGE-5 / TL-AGE-04).

    A agenda é o CALLER que chama ``application/operacao/os/atribuir_tecnico``
    para escrever ``tecnico_executor_id`` + ``agendada_para`` e transitar a
    atividade ``PENDENTE → AGENDADA``. NÃO duplica a máquina de estados da OS.
    """

    def atribuir_tecnico(
        self,
        *,
        tenant_id: UUID,
        atividade_id: UUID,
        tecnico_id: UUID,
        agendada_para: datetime,
        actor_usuario_id: UUID,
    ) -> None:
        """Atribui o técnico à atividade e transita o estado (PENDENTE→AGENDADA)."""
        ...

    def obter_atividade(
        self,
        *,
        tenant_id: UUID,
        atividade_id: UUID,
    ) -> dict[str, object] | None:
        """Lê dados da atividade via repositório (não SQL cru — TL-AGE-05)."""
        ...


@runtime_checkable
class ColaboradorAgendaPort(Protocol):
    """Porta de leitura de dados do colaborador (D-AGE-7/12/15 / TL-AGE-03).

    ``is_tecnico_campo`` é derivado do papel (``TECNICO`` ou ``MOTORISTA_UMC``).
    ``pendencia_cnh`` é legível via ``PapelColaboradorOutputSerializer`` sem
    estender o modelo ``Colaborador`` (zero extensão de ``colaboradores``).

    ``regime_jornada`` é resolvido pela ordem: override humano vigente →
    deriva do papel → indeterminado = ``nao_aplica`` (D-AGE-15).
    """

    def is_tecnico_campo(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
    ) -> bool:
        """``True`` se o colaborador tem papel ``TECNICO`` ou ``MOTORISTA_UMC``."""
        ...

    def pendencia_cnh(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
    ) -> bool:
        """``True`` se há pendência de CNH (vencida ou irregular — INV-AG-CNH-001)."""
        ...

    def regime_jornada(
        self,
        *,
        tenant_id: UUID,
        colaborador_id: UUID,
        na_data: date,
    ) -> RegimeJornadaResolvido:
        """Retorna o regime de jornada resolvido para o colaborador na data dada.

        Resolução fail-safe (D-AGE-15 / INV-AG-REGIME-001):
        1. Override humano vigente (``RegimeJornadaColaborador``) → vence.
        2. Deriva do papel:
           - ``MOTORISTA_UMC`` → ``motorista_profissional``.
           - ``TECNICO``       → ``clt_geral``.
           - outros / sem papel de campo → ``nao_aplica``.
        3. Papéis de campo conflitantes simultâneos sem override →
           ``nao_aplica`` + fonte ``indeterminado`` + audit ``regime_indeterminado``.

        IA NUNCA chama ``enquadrar_regime`` automaticamente (INV-AG-REGIME-001).
        """
        ...


@runtime_checkable
class RTSubstitutoPort(Protocol):
    """Porta de competência do RT projetada ao instante do slot (D-AGE-6).

    Reusa o predicate ``rt_competencia_cobre`` + ``RTCompetencia`` (ADR-0022)
    consultados projetados para ``data=slot.inicia_at.date()`` (granularidade
    DATA — PLAN-AGE-01), atravessando ``RTSubstituicao`` vigente na data
    (ADR-0068 §2.2 — RBC-AGE-04).

    Limitação conhecida (PLAN-AGE-02 / R15): não projeta o vínculo do titular
    (``encerrado_em`` futuro) — aceitável pois a agenda é consultiva.
    """

    def tem_rt_competente_no_slot(
        self,
        *,
        tenant_id: UUID,
        grandeza: str,
        data_slot: date,
    ) -> bool:
        """``True`` se há RT titular OU substituto competente na grandeza na data do slot.

        Perfil A determinístico: ausência → ``SemRTNoSlot`` (412).
        Perfil A incerto:        aviso ``RTPendenteConfirmacaoNoSlot``.
        B/C: warning + confirmação; D: desabilitado.
        """
        ...

    def eh_deterministica_ausencia(
        self,
        *,
        tenant_id: UUID,
        grandeza: str,
        data_slot: date,
    ) -> bool:
        """``True`` se a ausência de RT é determinística (bloqueio formal declarado).

        Determina se deve levantar 412 (determinístico) ou apenas warning (incerto).
        """
        ...


@runtime_checkable
class MapsProvider(Protocol):
    """Porta de rota/deslocamento (stub Wave A — GATE-AGE-MAPS).

    Wave A: o gerente preenche o tempo de deslocamento manualmente.
    Wave B: implementação real com API de mapas.
    """

    def estimar_deslocamento_min(
        self,
        *,
        origem_lat: float,
        origem_lng: float,
        destino_lat: float,
        destino_lng: float,
    ) -> float | None:
        """Estima tempo de deslocamento em minutos. Retorna ``None`` se indisponível."""
        ...


@runtime_checkable
class NotificacaoClientePort(Protocol):
    """Porta de notificação de reagendamento (stub Wave A — GATE-AGE-OMNICHANNEL).

    Wave A: enfileira o aviso (sem envio real).
    Wave B: integração com ``comunicacao-omnichannel``.
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
        """Enfileira aviso de reagendamento para o cliente."""
        ...


@runtime_checkable
class AReceberPort(Protocol):
    """Porta de lançamento de cobrança de no-show (D-AGE-9 / INV-AG-NOSHOW-AR-001).

    Quando no-show é cobrável, o use case chama ``criar_titulo_manual``
    (use case público de CR) via esta porta. NÃO cria consumer dentro de CR
    (fechado) — simetria com D-AGE-5 (TL-AGE-02).

    O adapter concreto vive em ``src/infrastructure/agenda/`` e monta
    ``CriarTituloManualInput`` com ``perfil_no_evento`` server-side.
    """

    def criar_titulo_manual(
        self,
        *,
        tenant_id: UUID,
        cliente_id: UUID,
        valor: object,  # Dinheiro — evita importação cross-domain neste nível
        descricao: str,
        perfil_no_evento: str,
        referencia_evento_id: UUID,
    ) -> UUID:
        """Cria título manual em contas-receber e retorna o ``titulo_id``."""
        ...
