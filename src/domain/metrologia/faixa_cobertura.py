"""Geometria pura de cobertura de faixa — COMPARTILHADA (M7 T-PROC-000).

Extraída de `escopos_cmc/cobertura.py` (D-PROC-6 / revisão tech-lead+RBC
2026-05-30): a contenção `faixa_solicitada ⊆ faixa_escopo` é IDÊNTICA entre
`escopos-cmc` (M6 — portão de escopo RBC) e `procedimentos-calibracao` (M7 —
portão de procedimento vigente). Os dois portões rodam na MESMA transição de
configuração (escopo→procedimento); geometria divergente entre eles (ex. "kg" vs
"kilograma", ou esquecer o fail-closed de unidade) é bug que vaza só em produção,
numa barreira de fraude regulatória. Centralizar a geometria mata essa classe.

**Só a GEOMETRIA é compartilhada** — os ERROS de domínio são distintos: M6 fala
`EscopoNaoCobreFaixa` / `cmc_fora_do_escopo` (fraude de acreditação cl. 8.1.3);
M7 fala `ProcedimentoVigenteAusente` / `procedimento_inexistente` (lacuna de
método cl. 7.2.1). Cada módulo embrulha esta geometria com seus próprios reasons.
Reasons aqui são NEUTROS (sem prefixo de domínio).

Puro: Decimal (nunca float — erro de arredondamento metrológico), sem Django.
"""

from __future__ import annotations

from src.domain.metrologia.value_objects import FaixaMedicao

# Reasons NEUTROS (cada módulo de domínio mapeia para o seu erro específico).
REASON_OK = ""
REASON_FORA_DA_FAIXA = "fora_da_faixa"
REASON_UNIDADE_INCOMPATIVEL = "unidade_incompativel"


def faixa_contida(*, solicitada: FaixaMedicao, escopo: FaixaMedicao) -> bool:
    """Contenção TOTAL: `solicitada ⊆ escopo` (ADR-0074 cond. 1 / INV-ECMC-005 /
    INV-PROC-001).

    Exige mesma unidade (fail-closed em unidade divergente — conversão de
    unidade é refinamento futuro; bloquear é mais seguro que cobrir indevido).
    """
    if solicitada.unidade != escopo.unidade:
        return False
    return (
        solicitada.inferior >= escopo.inferior
        and solicitada.superior <= escopo.superior
    )


def avaliar_contencao(
    *, solicitada: FaixaMedicao, escopo: FaixaMedicao
) -> tuple[bool, str]:
    """Versão com reason NEUTRO da contenção de faixa.

    Returns (True, "") se contido; (False, reason neutro) caso contrário. Cada
    módulo de domínio traduz o reason para o seu erro específico.
    """
    if solicitada.unidade != escopo.unidade:
        return False, REASON_UNIDADE_INCOMPATIVEL
    if faixa_contida(solicitada=solicitada, escopo=escopo):
        return True, REASON_OK
    return False, REASON_FORA_DA_FAIXA
