"""Anti-regressao INV-EQP-VERSAO-001 (T-EQP-100 — AC-EQP-002-5).

`EquipamentoVersao.motivo_detalhe` rejeita PII direta (mesma regex
INV-EQP-LOC-001). Quando motivo esta em MOTIVOS_QUE_OBRIGAM_APROVACAO,
exige >=100 chars adicionalmente.

>=3 testes: happy + unhappy PII + unhappy curto-quando-obriga.
"""

from __future__ import annotations

import pytest
from src.infrastructure.equipamentos.validators import validar_motivo_detalhe


def test_happy_motivo_detalhe_limpo_passa():
    validar_motivo_detalhe(
        "Substituicao do componente metrologico apos falha de fabrica.",
        motivo_obriga_detalhe=False,
    )
    validar_motivo_detalhe(
        "Substituicao por troca de PCB principal pos-falha. "
        "RT validou. Cliente solicitou. Mantem caracteristicas "
        "metrologicas do modelo original. Documentado em ata.",
        motivo_obriga_detalhe=True,
    )


@pytest.mark.parametrize(
    "texto_pii",
    [
        "Cliente Joao Silva pediu troca de placa.",  # nomes
        "Contato: tecnico@cliente.com.br",  # email
        "Verificar com 11 99999-9999",  # telefone
        "Cliente CPF 123.456.789-01 solicitou.",  # cpf
        "Empresa CNPJ 12.345.678/0001-90 reportou problema.",  # cnpj
    ],
)
def test_unhappy_motivo_detalhe_com_pii(texto_pii):
    # Quando motivo nao obriga detalhe minimo, mas detalhe ESTA
    # preenchido com PII, ainda deve bloquear.
    if len(texto_pii) >= 100:
        with pytest.raises(ValueError):
            validar_motivo_detalhe(texto_pii, motivo_obriga_detalhe=True)
    else:
        # Texto curto: quando obriga detalhe falha por tamanho.
        # Quando nao obriga, falha por PII direto.
        with pytest.raises(ValueError):
            validar_motivo_detalhe(texto_pii, motivo_obriga_detalhe=False)


def test_unhappy_curto_quando_motivo_obriga():
    with pytest.raises(ValueError, match=r">=100"):
        validar_motivo_detalhe("Curto.", motivo_obriga_detalhe=True)
