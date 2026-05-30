"""Cobertura RBC — matemática pura da decisão de bloqueio (M6 T-ECMC-004).

Implementa as 3 condições cumulativas da ADR-0074 (cobertura RBC tridimensional):
  1. Contenção total da faixa (`faixa_solicitada ⊆ faixa_escopo`) — NÃO interseção
     (TL-C-08; interseção parcial deixaria emitir RBC fora do CMC = fraude).
  2. `U_reportada ≥ CMC` (ILAC-P14:09/2020 §5.5 — INV-ECMC-009): o lab não pode
     reportar incerteza melhor que a capacidade declarada.
  3. Menor CMC por faixa (RBC-NC-03 / NIT-DICLA-012): N métodos cobrindo o mesmo
     ponto → a CMC efetiva é a MENOR.

Puro, sem Django, sem float (Decimal — erro de arredondamento metrológico). As
funções retornam reasons estáveis (consumers comparam string), espelhando o
contrato dos predicates (`predicates_calibracao.py`).
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from src.domain.metrologia.faixa_cobertura import faixa_contida
from src.domain.metrologia.value_objects import FaixaMedicao

from .entities import EscopoCMCSnapshot

# Geometria de contenção compartilhada (M7 T-PROC-000): `faixa_contida` agora
# vive em src/domain/metrologia/faixa_cobertura.py e é reexportada aqui para
# preservar o contrato `cobertura.faixa_contida` (query_service M6 + testes).
__all__ = [
    "faixa_contida",
    "avaliar_contencao",
    "cmc_no_ponto",
    "menor_cmc_por_faixa",
    "u_atende_cmc",
    "avaliar_u_cmc",
    "u_igual_cmc_suspeita",
    "REASON_OK",
    "REASON_FORA_DO_ESCOPO",
    "REASON_UNIDADE_INCOMPATIVEL",
    "REASON_INCERTEZA_ABAIXO_CMC",
]

# Reasons estáveis ESPECÍFICOS do escopo CGCRE (mapeados a 412 pela aplicação) —
# distintos dos reasons neutros da geometria compartilhada (erro de domínio
# `EscopoNaoCobreFaixa`, fraude de acreditação cl. 8.1.3 — RBC).
REASON_OK = ""
REASON_FORA_DO_ESCOPO = "cmc_fora_do_escopo"
REASON_UNIDADE_INCOMPATIVEL = "cmc_unidade_incompativel"
REASON_INCERTEZA_ABAIXO_CMC = "incerteza_abaixo_do_cmc"


def avaliar_contencao(
    *, solicitada: FaixaMedicao, escopo: FaixaMedicao
) -> tuple[bool, str]:
    """Versão com reason ESPECÍFICO do escopo (`cmc_*`) da contenção de faixa.

    Embrulha a geometria compartilhada `faixa_contida` com os reasons do domínio
    escopos-cmc. Returns (True, "") se contido; (False, reason) caso contrário.
    """
    if solicitada.unidade != escopo.unidade:
        return False, REASON_UNIDADE_INCOMPATIVEL
    if faixa_contida(solicitada=solicitada, escopo=escopo):
        return True, REASON_OK
    return False, REASON_FORA_DO_ESCOPO


def cmc_no_ponto(*, escopo: EscopoCMCSnapshot, ponto: Decimal) -> Decimal:
    """CMC do escopo no ponto de medição (delega à forma — ADR-0074)."""
    return escopo.cmc_em(ponto)


def menor_cmc_por_faixa(
    escopos: Sequence[EscopoCMCSnapshot], *, ponto: Decimal
) -> Decimal | None:
    """CMC efetiva no ponto quando N métodos cobrem a mesma faixa: a MENOR
    (RBC-NC-03 / NIT-DICLA-012 — o escopo publica a CMC do método de menor
    incerteza). Recebe escopos JÁ filtrados (mesma grandeza, ponto contido,
    vigentes/CONFIRMADOS). Retorna a menor CMC no ponto, ou None se vazio.
    """
    cmcs = [esc.cmc_em(ponto) for esc in escopos]
    return min(cmcs) if cmcs else None


def u_atende_cmc(*, u_reportada: Decimal, cmc_no_ponto: Decimal) -> bool:
    """`U ≥ CMC` (ILAC-P14 §5.5 / INV-ECMC-009). A CMC é o PISO da incerteza
    reportável. `U < CMC` → False (bloqueia emissão RBC)."""
    if not isinstance(u_reportada, Decimal) or not isinstance(cmc_no_ponto, Decimal):
        raise ValueError("u_atende_cmc() exige Decimal (sem float)")
    return u_reportada >= cmc_no_ponto


def avaliar_u_cmc(*, u_reportada: Decimal, cmc_no_ponto: Decimal) -> tuple[bool, str]:
    """Versão com reason estável de `U ≥ CMC`.

    Returns (True, "") se atende; (False, 'incerteza_abaixo_do_cmc') se U < CMC.
    """
    if u_atende_cmc(u_reportada=u_reportada, cmc_no_ponto=cmc_no_ponto):
        return True, REASON_OK
    return False, REASON_INCERTEZA_ABAIXO_CMC


def u_igual_cmc_suspeita(*, u_reportada: Decimal, cmc_no_ponto: Decimal) -> bool:
    """`U == CMC` exato é SUSPEITO de cópia cega (RBC-NC-07): a incerteza do
    serviço deveria somar as contribuições do instrumento do cliente, então na
    prática `U > CMC`. Sinaliza para revisão; NÃO bloqueia por si só (o bloqueio
    duro é `U < CMC`). A garantia de que U vem do orçamento de incerteza (e não é
    `U=CMC` por default) é responsabilidade do use case de emissão.
    """
    return u_reportada == cmc_no_ponto
