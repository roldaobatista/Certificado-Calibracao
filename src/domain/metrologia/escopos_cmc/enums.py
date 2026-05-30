"""Enums fechados do domínio escopos-cmc (M6 Wave A — T-ECMC-001).

Estados + tipos canônicos do EscopoCMC. Frozen + str-mixin para serializar em
JSON sem conversão manual (mesmo padrão de
src/domain/metrologia/padroes/enums.py). Bate 1:1 com choices em
src/infrastructure/metrologia/escopos_cmc/models.py (Fatia 1b). Domain NÃO
importa Django (ADR-0007).
"""

from __future__ import annotations

from enum import Enum


class EstadoEscopo(str, Enum):
    """Ciclo de vida do EscopoCMC (spec §4 / plan v2 §15).

    `RASCUNHO_EXTRAIDO` (decisão N — extração PDF): linha candidata extraída do
    PDF da CGCRE, editável, AINDA NÃO vigente. Só vira escopo válido após
    conferência humana (INV-ECMC-007). `CONFIRMADO`: vigente, WORM Padrão B
    (ADR-0031). `REVOGADO`: terminal (revogação one-shot + motivo).
    """

    RASCUNHO_EXTRAIDO = "RASCUNHO_EXTRAIDO"
    CONFIRMADO = "CONFIRMADO"
    REVOGADO = "REVOGADO"

    @property
    def consultavel_para_cobertura(self) -> bool:
        """Só CONFIRMADO entra em `cobre()`/`cmc_para()` (fail-closed ADR-0073).

        Rascunho extraído nunca cobre (INV-ECMC-007); revogado sai da cobertura.
        A vigência temporal (ADR-0030) é verificada em separado.
        """
        return self is EstadoEscopo.CONFIRMADO

    @property
    def editavel(self) -> bool:
        """Apenas o rascunho extraído é editável; CONFIRMADO é WORM."""
        return self is EstadoEscopo.RASCUNHO_EXTRAIDO

    @property
    def terminal(self) -> bool:
        return self is EstadoEscopo.REVOGADO


class OrigemEscopo(str, Enum):
    """Como o escopo entrou no sistema (auditoria de proveniência)."""

    MANUAL = "MANUAL"  # digitado linha-a-linha
    EXTRACAO_PDF = "EXTRACAO_PDF"  # extraído do PDF CGCRE + conferência humana


class FormaCMC(str, Enum):
    """Forma como a CMC é declarada no escopo CGCRE (ADR-0074 / RBC-NC-01).

    A CMC raramente é um número fixo: a CGCRE publica frequentemente como
    `a + b·X` (termo fixo + termo proporcional ao mensurando). Comparar `U ≥ CMC`
    exige calcular a CMC NO PONTO de medição — ver `EscopoCMCSnapshot.cmc_em`.
    """

    ABSOLUTA = "ABSOLUTA"  # CMC = cmc_valor (constante)
    RELATIVA_LINEAR = "RELATIVA_LINEAR"  # CMC = cmc_valor (a) + cmc_coef_relativo (b) · |X|
