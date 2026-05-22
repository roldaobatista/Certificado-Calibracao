"""Anti-regressao INV-EQP-ANOM-002 (T-EQP-103 — AC-EQP-006-2).

`EquipamentoRecebimento.justificativa_decisao` >=30 chars + anti-PII.
Validator `validar_justificativa_decisao`.

>=3 testes: happy + unhappy curto + unhappy PII.
"""

from __future__ import annotations

import pytest
from src.infrastructure.equipamentos.validators import (
    JUSTIFICATIVA_DECISAO_MIN_CHARS,
    validar_justificativa_decisao,
)


def test_happy_justificativa_limpa_e_longa():
    validar_justificativa_decisao(
        "Calibracao tecnicamente viavel; amassado nao afeta celula "
        "de carga. Cliente avisado verbalmente sobre situacao."
    )


def test_unhappy_curta():
    with pytest.raises(ValueError, match=rf">={JUSTIFICATIVA_DECISAO_MIN_CHARS}"):
        validar_justificativa_decisao("Curta.")


@pytest.mark.parametrize(
    "texto_pii",
    [
        # Tem >=30 chars E PII direta — deve falhar por PII.
        (
            "Cliente Joao Silva concordou em aceitar com ressalva ja que "
            "a peca esta sem afetacao."
        ),
        "Contato tecnico foi feito via email cliente@empresa.com.br hoje.",
        "Cliente verificado por telefone (11) 99999-9999 confirmou.",
        "Cliente CPF 123.456.789-01 deu consentimento verbal.",
    ],
)
def test_unhappy_com_pii(texto_pii):
    with pytest.raises(ValueError, match=r"PII"):
        validar_justificativa_decisao(texto_pii)
