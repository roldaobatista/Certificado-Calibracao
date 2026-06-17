"""Entidades (snapshots DTO imutáveis) do domínio agenda (Fatia 1a — T-AGE-011).

Todos ``@dataclass(frozen=True, slots=True)`` — atravessam fronteiras de camada.
O adapter Django converte Model ↔ Snapshot. O domínio NUNCA importa django.*.

Entidades:
- ``EventoAgenda``           — raiz de agregado; ``atividade_id`` NOT NULL quando ``tipo=os``.
- ``Recorrencia``            — regra RRULE + âncora de materialização.
- ``RegistroNoShow``         — no-show com custo e flag de cobrança (INSERT-only WORM).
- ``CapacidadeTecnico``      — capacidade diária configurada por técnico (D-AGE-11).
- ``Feriado``                — feriado nacional (seed) ou custom por tenant (D-AGE-10).
- ``EventoAuditoriaAgenda``  — trilha de auditoria WORM (INSERT-only — INV-AG-AUDIT-WORM-001).
- ``RegimeJornadaColaborador``— override humano de regime de jornada (D-AGE-15).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from .enums import (
    AcaoAuditoria,
    EstadoEvento,
    FonteRegime,
    MotivoBloqueio,
    RegimeJornada,
    TipoEvento,
)
from .erros import AtividadeObrigatoria


@dataclass(frozen=True, slots=True)
class EventoAgenda:
    """Raiz de agregado da agenda (D-AGE-3 / D-AGE-2 / INV-AG-ATIVIDADE-001).

    Invariante: quando ``tipo == os``, ``atividade_id`` DEVE ser não-nulo
    (ADR-0023/0051 — agendar ATIVIDADE, não OS inteira).

    ``os_id``           — desnormalizado derivado; NÃO é fonte de verdade.
    ``aloca_em_umc``    — indica que o técnico está sendo alocado em campo/UMC;
                          ativa a validação de jornada UMC (D-AGE-4).
    ``revision``        — versão otimista (bump a cada transição de estado).
    """

    id: UUID
    tenant_id: UUID
    tecnico_id: UUID
    tipo: TipoEvento
    estado: EstadoEvento
    inicia_at: datetime
    termina_at: datetime
    aloca_em_umc: bool
    criado_por_usuario_id: UUID
    criado_em: datetime
    atualizado_em: datetime
    revision: int = 0
    # Obrigatório quando tipo == os (INV-AG-ATIVIDADE-001):
    atividade_id: UUID | None = None
    # Desnormalizado derivado (não é fonte de verdade):
    os_id: UUID | None = None
    # Opcional (só para tipo == bloqueio):
    motivo_bloqueio: MotivoBloqueio | None = None
    descricao_publica: str = ""
    # Recorrência originadora (None = evento avulso):
    recorrencia_id: UUID | None = None
    # Data âncora da ocorrência na série de recorrência (UNIQUE com recorrencia_id):
    ocorrencia_dt: datetime | None = None
    # Feriado — flag para confirmação explícita (D-AGE-10):
    confirmar_feriado: bool = False

    def __post_init__(self) -> None:
        if self.tipo == TipoEvento.OS and self.atividade_id is None:
            raise AtividadeObrigatoria(
                f"EventoAgenda tipo=os exige atividade_id (INV-AG-ATIVIDADE-001). "
                f"evento_id={self.id!r}"
            )


@dataclass(frozen=True, slots=True)
class Recorrencia:
    """Regra de recorrência de um evento (D-AGE-8 / US-AG-009 / INV-AG-RECORRENCIA-001).

    A materialização de ocorrências é feita por ``materializar_janela``
    (``recorrencia.py``) — puro, determinístico, idempotente por
    ``(recorrencia_id, ocorrencia_dt)`` UNIQUE.

    ``duracao_minutos`` — duração de cada ocorrência materializada.
    ``ativo``           — se ``False``, o job de materialização para de expandir.
    """

    id: UUID
    tenant_id: UUID
    tecnico_id: UUID
    rrule_str: str
    inicia_em: datetime  # âncora de início da série
    duracao_minutos: int
    ativo: bool
    tipo: TipoEvento
    criado_por_usuario_id: UUID
    criado_em: datetime
    atualizado_em: datetime
    atividade_id: UUID | None = None
    os_id: UUID | None = None
    aloca_em_umc: bool = False


@dataclass(frozen=True, slots=True)
class RegistroNoShow:
    """Registro de no-show (INSERT-only WORM — INV-AG-AUDIT-WORM-001 / D-AGE-9).

    Quando ``cobrar_cliente=True``, o use case chama ``AReceberPort.criar_titulo_manual``
    (D-AGE-9) e publica ``agenda.no_show.registrado`` (INV-AG-NOSHOW-AR-001).

    ``custo_estimado`` — custo estimado da visita frustrada (decimal, 2 casas).
    """

    id: UUID
    tenant_id: UUID
    evento_id: UUID
    tecnico_id: UUID
    ocorrido_em: datetime
    custo_estimado: Decimal
    cobrar_cliente: bool
    registrado_por_usuario_id: UUID
    criado_em: datetime
    observacao: str = ""


@dataclass(frozen=True, slots=True)
class CapacidadeTecnico:
    """Capacidade de trabalho diária configurada por técnico (D-AGE-11).

    Default 8h úteis seg-sex (08:00-17:00, 1h almoço) se não cadastrada.
    Base para o indicador de US-AG-010 (75%/90% de horas alocadas).

    ``horas_uteis_dia``    — horas úteis por dia de trabalho (default 8).
    ``dias_trabalho``      — dias da semana trabalhados (0=seg .. 6=dom).
    ``hora_inicio``        — hora de início do expediente (HH no formato 0-23).
    ``hora_fim``           — hora de fim do expediente.
    """

    id: UUID
    tenant_id: UUID
    colaborador_id: UUID
    horas_uteis_dia: int
    dias_trabalho: frozenset[int]  # 0=seg .. 6=dom
    hora_inicio: int  # 0-23
    hora_fim: int  # 0-23
    vigencia_inicio: date
    criado_por_usuario_id: UUID
    criado_em: datetime
    atualizado_em: datetime
    vigencia_fim: date | None = None  # None = vigente indefinidamente


@dataclass(frozen=True, slots=True)
class Feriado:
    """Feriado (seed nacional ou custom por tenant — D-AGE-10 / US-AG-005).

    Agendar em feriado exige ``confirmar_feriado=True`` no evento (D-AGE-10).
    ``tenant_id=None`` indica feriado do catálogo nacional (seed imutável).
    """

    id: UUID
    data: date
    descricao: str
    nacional: bool
    tenant_id: UUID | None  # None = nacional (seed); UUID = custom por tenant
    criado_em: datetime
    ativo: bool = True


@dataclass(frozen=True, slots=True)
class EventoAuditoriaAgenda:
    """Trilha de auditoria WORM (INSERT-only — INV-AG-AUDIT-WORM-001).

    Toda transição de estado ou reagendamento gera um registro aqui.
    O trigger PG bloqueia UPDATE e DELETE (Fatia 1b).

    ``payload_resumo`` — resumo não-PII da mudança (diff de campos relevantes).
    """

    id: UUID
    tenant_id: UUID
    evento_id: UUID
    acao: AcaoAuditoria
    actor_usuario_id: UUID | None
    occurred_at: datetime
    criado_em: datetime
    payload_resumo: str = ""


@dataclass(frozen=True, slots=True)
class RegimeJornadaColaborador:
    """Override humano de regime de jornada (D-AGE-15 / INV-AG-REGIME-001).

    Mora na agenda (não em colaboradores — colaboradores permanece FECHADO).
    INSERT-com-vigência: cada alteração insere nova linha; a vigente é a
    com maior ``vigencia_inicio`` ≤ ``na_data``.

    IA NUNCA grava nesta tabela — só humano (RH/advogado) via
    ``enquadrar_regime`` (T-AGE-036).

    ``definido_por_usuario_id`` — usuário humano que fez o override.
    ``fonte``                   — sempre ``override_humano`` nesta entidade.
    """

    id: UUID
    tenant_id: UUID
    colaborador_id: UUID
    regime: RegimeJornada
    vigencia_inicio: date
    definido_por_usuario_id: UUID
    fonte: FonteRegime
    criado_em: datetime
    vigencia_fim: date | None = None  # None = vigente indefinidamente
    justificativa: str = ""

    def __post_init__(self) -> None:
        if self.fonte != FonteRegime.OVERRIDE_HUMANO:
            raise ValueError(
                f"RegimeJornadaColaborador.fonte deve ser override_humano; "
                f"recebido: {self.fonte!r}. "
                "IA não pode gravar override de regime (INV-AG-REGIME-001)."
            )
