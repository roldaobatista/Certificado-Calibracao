"""Anti-regressao INV-EQP-ANOM-001 (T-EQP-102 — AC-EQP-006-2).

`EquipamentoRecebimento.anomalias_observadas` <=500 chars + anti-PII
(mesma regex INV-EQP-LOC-001). Validator `validar_anomalias_observadas`.

>=3 testes: happy + unhappy PII + unhappy >500.
"""

from __future__ import annotations

import pytest
from src.infrastructure.equipamentos.validators import (
    ANOMALIAS_OBSERVADAS_MAX_CHARS,
    validar_anomalias_observadas,
)


def test_happy_texto_anomalia_limpo():
    validar_anomalias_observadas(
        "Painel frontal apresenta amassado leve no canto direito. "
        "Sem afetacao da celula de carga."
    )
    # Vazio tambem aceito.
    validar_anomalias_observadas("")
    validar_anomalias_observadas(None)


@pytest.mark.parametrize(
    "texto_pii",
    [
        "Cliente Joao Silva relatou queda do equipamento.",
        "Tecnico@email.com viu o problema.",
        "(11) 99999-9999 reportou.",
        "Empresa CNPJ 12.345.678/0001-90 entregou ja amassado.",
    ],
)
def test_unhappy_anomalia_com_pii(texto_pii):
    with pytest.raises(ValueError):
        validar_anomalias_observadas(texto_pii)


def test_unhappy_excede_limite():
    texto = "x" * (ANOMALIAS_OBSERVADAS_MAX_CHARS + 1)
    with pytest.raises(ValueError, match=str(ANOMALIAS_OBSERVADAS_MAX_CHARS)):
        validar_anomalias_observadas(texto)
