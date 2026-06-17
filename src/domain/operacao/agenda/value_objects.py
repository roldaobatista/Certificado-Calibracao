"""Value Objects imutáveis do domínio agenda (Fatia 1a — T-AGE-012).

Todos ``frozen + slots`` (imutáveis). NÃO importa Django.

``Janela``                 — intervalo temporal half-open ``[inicia_at, termina_at)``.
``RegraRecorrencia``       — regra RRULE RFC 5545 (string serializada).
``ResultadoJornada``       — resultado da validação ``validar_jornada_umc``.
``RegimeJornadaResolvido`` — regime + fonte, com invariante fail-safe.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .enums import FonteRegime, RegimeJornada


@dataclass(frozen=True, slots=True)
class Janela:
    """Intervalo temporal half-open ``[inicia_at, termina_at)`` (D-AGE-13 / R12).

    Semântica half-open: dois slots adjacentes (09:00-10:00 e 10:00-11:00)
    NÃO colidem. Isso espelha o ``tstzrange '[)'`` do EXCLUDE GIST no banco
    (INV-AG-OVERLAP-001).

    Invariante: ``inicia_at < termina_at`` — levanta ``ValueError`` se violado.
    """

    inicia_at: datetime
    termina_at: datetime

    def __post_init__(self) -> None:
        if self.inicia_at >= self.termina_at:
            raise ValueError(
                f"Janela inválida: inicia_at ({self.inicia_at!r}) "
                f"deve ser estritamente anterior a termina_at ({self.termina_at!r})"
            )

    @property
    def duracao_minutos(self) -> float:
        """Duração da janela em minutos."""
        return (self.termina_at - self.inicia_at).total_seconds() / 60

    def sobrepoe(self, outra: Janela) -> bool:
        """Verifica sobreposição half-open: ``[a,b)`` ∩ ``[c,d)`` ≠ ∅.

        Condição: ``a < d AND c < b``.
        Slots adjacentes (b == c) NÃO se sobrepõem (semântica half-open).
        """
        return self.inicia_at < outra.termina_at and outra.inicia_at < self.termina_at


@dataclass(frozen=True, slots=True)
class RegraRecorrencia:
    """Regra de recorrência no formato RRULE RFC 5545 (D-AGE-8 / US-AG-009).

    ``rrule_str`` — string RRULE serializada, ex.:
        ``FREQ=WEEKLY;BYDAY=MO,WE,FR``
        ``FREQ=MONTHLY;BYMONTHDAY=1``

    A validação sintática da string é responsabilidade do use case / serializer.
    O domínio armazena a string opaca e delega a interpretação para
    ``materializar_janela`` (``recorrencia.py``).
    """

    rrule_str: str
    descricao_publica: str = ""


@dataclass(frozen=True, slots=True)
class ResultadoJornada:
    """Resultado da validação ``validar_jornada_umc`` (D-AGE-4 / INV-AG-JORNADA-UMC-001).

    ``ok``           — ``True`` se a janela não viola nenhuma regra.
    ``violacao``     — código da regra violada (ex.: ``"R1_INTER_JORNADA"``); ``None`` se ok.
    ``faltante_min`` — minutos faltando para satisfazer a regra; ``None`` se ok.
    ``proximo_slot`` — próxima janela de início válida sugerida; ``None`` se ok ou indeterminado.
    """

    ok: bool
    violacao: str | None = None
    faltante_min: float | None = None
    proximo_slot: datetime | None = None


@dataclass(frozen=True, slots=True)
class RegimeJornadaResolvido:
    """Regime de jornada resolvido para um colaborador em uma data (D-AGE-15).

    Invariante (INV-AG-REGIME-001 / fail-safe):
        ``fonte == indeterminado`` ⇒ ``regime`` DEVE ser ``nao_aplica``.
        Qualquer outra combinação levanta ``ValueError``.

    Isso evita que o sistema assuma motorista_profissional para um papel ambíguo,
    prevenindo falso-bloqueio (R2 indevida) e falso-negativo encoberto.
    """

    regime: RegimeJornada
    fonte: FonteRegime

    def __post_init__(self) -> None:
        if self.fonte == FonteRegime.INDETERMINADO and self.regime != RegimeJornada.NAO_APLICA:
            raise ValueError(
                f"RegimeJornadaResolvido inválido: fonte={self.fonte!r} exige "
                f"regime=nao_aplica, mas recebeu regime={self.regime!r}. "
                "Papéis de campo conflitantes sem override humano devem usar "
                "nao_aplica (fail-safe — INV-AG-REGIME-001 / D-AGE-15)."
            )


@dataclass(frozen=True, slots=True)
class TecnicoJornada:
    """Dados do técnico necessários para a validação de jornada (D-AGE-4).

    Passado como parâmetro para ``validar_jornada_umc``. Carrega apenas
    o que o predicate de jornada precisa — sem PII além do identificador.

    ``is_tecnico_campo``  — derivado do papel (``TECNICO`` ou ``MOTORISTA_UMC``).
    ``aloca_em_umc``      — indica se o evento está alocando o técnico em UMC
                            (frota/campo). Só quando ambos são ``True`` a jornada
                            UMC é validada (D-AGE-4).
    ``tenant_id``         — escopo de tenant (RLS).
    ``colaborador_id``    — identificador do colaborador.
    """

    tenant_id: UUID
    colaborador_id: UUID
    is_tecnico_campo: bool
    aloca_em_umc: bool
