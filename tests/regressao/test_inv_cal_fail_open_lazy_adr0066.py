"""Q-CAL-03 conserto P5 (2026-05-27) — regressao fail-open lazy ADR-0066.

Cobre TST-005 do prompt do auditor de qualidade: predicates `cmc_cobre` +
`procedimento_vigente_para` operam fail-open lazy Wave A (ADR-0066). Quando
modulo `metrologia/escopos-cmc` ou `metrologia/procedimentos-calibracao`
PLUGAR (Wave A), estes testes vao QUEBRAR ao chamar predicate sem dado
real — alertando que a regressao silenciosa foi removida e o predicate
agora rejeita ausencia de dado.

ADR-0066 (aceita 2026-05-27 — paralelo ADR-0063 do M3 OS): predicates
`cmc_cobre` + `procedimento_vigente_para` declaram fail-open Wave A com
GATEs explicitos:
  - GATE-CAL-CMC-PREDICATE (acende quando modulo escopos-cmc plugar)
  - GATE-CAL-PROC-VIGENTE-PREDICATE (acende quando modulo
    procedimentos-calibracao plugar)

INVs declaradas neste regression file:
  - INV-CAL-CMC-001 (fail-open lazy Wave A) — ADR-0066
  - INV-CAL-PROC-001 (fail-open lazy Wave A) — ADR-0066

Quando os modulos plugaren, este arquivo precisa virar negativo (predicate
rejeita ausencia de cobertura) — aceite manual + atualizacao dos GATEs.
"""

from __future__ import annotations

from contextlib import contextmanager
from uuid import uuid4

from src.infrastructure.calibracao.predicates_calibracao import (
    cmc_cobre,
    procedimento_vigente_para,
)
from src.infrastructure.multitenant.context import perfil_tenant_context


@contextmanager
def _perfil(perfil: str):
    """T-SAN-PERFIL-018 retrofit: `cmc_cobre` agora le perfil via ContextVar,
    nao mais do payload da request. Helper popula o ContextVar pelo teste."""
    token = perfil_tenant_context.set(perfil)
    try:
        yield
    finally:
        perfil_tenant_context.reset(token)


class TestInvCalCmc001FailOpenLazy:
    """ADR-0066: `cmc_cobre` retorna (True, '') hoje pra perfil 'A' com grandeza
    declarada — modulo `escopos-cmc` ainda nao plugado.

    Quando GATE-CAL-CMC-PREDICATE acender, este teste DEVE QUEBRAR (sinal de
    que a regressao silenciosa foi fechada). Aceite manual + remover este
    arquivo de regressao + adicionar testes positivos contra
    `escopo_cmc_repo`.

    **2026-05-27 — retrofit T-SAN-PERFIL-018:** `cmc_cobre` deixou de ler
    `tipo_acreditacao` do payload (FAIL L6) e passou a consultar perfil
    canonico via ContextVar. Teste populado com perfil 'A' equivale ao
    cenario anterior (`tipo_acreditacao=RBC` no payload de tenant A).
    """

    def test_predicate_retorna_true_em_wave_a(self) -> None:
        with _perfil("A"):
            ok, motivo = cmc_cobre(
                {
                    "tenant_id": uuid4(),
                    "grandeza": "massa",
                    "faixa_min": "0",
                    "faixa_max": "200",
                    "data": "2026-05-27",
                }
            )
        assert ok is True, (
            "ADR-0066 fail-open lazy quebrado — perfil A com grandeza declarada "
            "estava retornando True hoje. Se GATE-CAL-CMC-PREDICATE acendeu, "
            "remova este arquivo + atualize tests positivos."
        )
        assert motivo == ""


class TestInvCalProc001FailOpenLazy:
    """ADR-0066: `procedimento_vigente_para` retorna (True, '') hoje pra
    grandeza declarada — modulo `procedimentos-calibracao` nao plugado.

    Quando GATE-CAL-PROC-VIGENTE-PREDICATE acender, este teste DEVE QUEBRAR.
    """

    def test_predicate_retorna_true_em_wave_a(self) -> None:
        ok, motivo = procedimento_vigente_para(
            {
                "tenant_id": uuid4(),
                "grandeza": "temperatura",
                "data": "2026-05-27",
            }
        )
        assert ok is True, (
            "ADR-0066 fail-open lazy quebrado — procedimento_vigente_para "
            "estava retornando True hoje. Se GATE-CAL-PROC-VIGENTE-PREDICATE "
            "acendeu, remova este arquivo + atualize tests positivos."
        )
        assert motivo == ""
