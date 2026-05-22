"""Anti-regressao INV-EQP-LOC-001 (T-EQP-099 — AC-EQP-001-4 / LGPD art. 5º I).

`Equipamento.localizacao_fisica` rejeita PII direta (CPF/CNPJ/email/
telefone/nomes proprios consecutivos). Aplicado em `EquipamentoCriarSerializer`
via `validar_localizacao_fisica`.

>=3 testes: happy (string limpa OK) + unhappy (cada padrao PII) +
limite tamanho.
"""

from __future__ import annotations

import pytest
from src.infrastructure.equipamentos.validators import (
    LIMITE_LOCALIZACAO_FISICA,
    conter_pii_direta,
    validar_localizacao_fisica,
)


@pytest.mark.parametrize(
    "texto_limpo",
    [
        "bancada norte - sala 12",
        "predio A, sala 305",
        "box laboratorio acreditacao - posicao 4",
        "sala metrologia eletrica",
    ],
)
def test_happy_textos_limpos_passam(texto_limpo):
    # Nao levanta.
    validar_localizacao_fisica(texto_limpo)
    assert conter_pii_direta(texto_limpo) is False


@pytest.mark.parametrize(
    "texto_pii",
    [
        # CPF mascarado
        "Sala do Dr. responsavel 123.456.789-01",
        # CNPJ mascarado
        "Predio 12.345.678/0001-90 sala 5",
        # E-mail
        "Bancada do tecnico@empresa.com",
        # Telefone BR
        "Sala 4 falar com (11) 99999-9999",
        # >=2 nomes proprios capitalizados
        "Setor do Joao Silva",
    ],
)
def test_unhappy_padrao_pii_falha(texto_pii):
    assert conter_pii_direta(texto_pii) is True
    with pytest.raises(ValueError):
        validar_localizacao_fisica(texto_pii)


def test_limite_tamanho_excedido():
    texto = "x" * (LIMITE_LOCALIZACAO_FISICA + 1)
    with pytest.raises(ValueError):
        validar_localizacao_fisica(texto)
