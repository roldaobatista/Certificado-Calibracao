"""Enums fechados do domínio procedimentos-calibracao (M7 — T-PROC-010).

Estados + tipos canônicos do ProcedimentoCalibracao. Frozen + str-mixin para
serializar em JSON sem conversão manual (molde `escopos_cmc/enums.py`). Bate 1:1
com choices em models.py (Fatia 1b). Domain NÃO importa Django (ADR-0007).
"""

from __future__ import annotations

from enum import Enum


class EstadoProcedimento(str, Enum):
    """Ciclo de vida do ProcedimentoCalibracao (D2 — distinto do M6).

    `RASCUNHO`: em elaboração, editável, AINDA NÃO vigente. `PUBLICADO`: vigente,
    documento controlado, WORM Padrão B (ADR-0031) — só este entra na resolução
    `vigente_em()` (cl. 7.2.1). `REVOGADO`: terminal (one-shot + motivo).
    """

    RASCUNHO = "RASCUNHO"
    PUBLICADO = "PUBLICADO"
    REVOGADO = "REVOGADO"

    @property
    def consultavel_para_resolucao(self) -> bool:
        """Só PUBLICADO entra em `vigente_em()` (fail-closed). RASCUNHO nunca
        resolve; REVOGADO sai. A vigência temporal (ADR-0030) é à parte."""
        return self is EstadoProcedimento.PUBLICADO

    @property
    def editavel(self) -> bool:
        """Apenas o rascunho é editável; PUBLICADO é WORM."""
        return self is EstadoProcedimento.RASCUNHO

    @property
    def publicavel(self) -> bool:
        """Só RASCUNHO pode ser publicado."""
        return self is EstadoProcedimento.RASCUNHO

    @property
    def terminal(self) -> bool:
        return self is EstadoProcedimento.REVOGADO


class TipoMetodo(str, Enum):
    """Classificação do método (ISO 17025 cl. 7.2.1.5 / cl. 7.2.2 — RBC NC-PROC-01).

    `NORMALIZADO`: método de norma publicada (OIML/ABNT/ISO) — só verificação.
    `NAO_NORMALIZADO`: desenvolvido internamente — exige VALIDAÇÃO documentada.
    `MODIFICADO`: norma adaptada/estendida — exige validação da modificação.
    """

    NORMALIZADO = "NORMALIZADO"
    NAO_NORMALIZADO = "NAO_NORMALIZADO"
    MODIFICADO = "MODIFICADO"

    @property
    def exige_validacao(self) -> bool:
        """Método não-normalizado/modificado exige evidência de validação
        (cl. 7.2.2.1) — bloqueio duro é fail-open lazy no MVP (INV-PROC-010)."""
        return self in (TipoMetodo.NAO_NORMALIZADO, TipoMetodo.MODIFICADO)
