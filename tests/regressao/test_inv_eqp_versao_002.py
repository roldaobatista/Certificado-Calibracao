"""Anti-regressao INV-EQP-VERSAO-002 (T-EQP-101 — AC-EQP-002-6).

Payload do evento `equipamento.versao_criada` segue lista FECHADA
(positiva) + bloqueia 7 campos proibidos (negativa). Defesa em
profundidade via `_validar_payload_anti_vaza`.

>=3 testes: happy (payload limpo passa) + unhappy (cada proibido) +
campo fora da whitelist.
"""

from __future__ import annotations

import pytest
from src.infrastructure.equipamentos.services_versao import (
    CAMPOS_PAYLOAD_PERMITIDOS,
    CAMPOS_PAYLOAD_PROIBIDOS,
    PayloadVazandoPII,
    _validar_payload_anti_vaza,
)


def test_happy_payload_so_com_chaves_permitidas():
    payload = {
        "tenant_id": "uuid-1",
        "equipamento_id": "uuid-2",
        "versao_id": "uuid-3",
        "campo": "modelo",
        "motivo_mudanca": "correcao_cadastral",
    }
    # Nao levanta.
    _validar_payload_anti_vaza(payload)


def test_proibidas_sao_sete():
    """Lista negativa explicita — defesa em profundidade alem da
    positiva. Garantia: o conjunto NAO encolhe sem PR."""
    assert len(CAMPOS_PAYLOAD_PROIBIDOS) == 7


@pytest.mark.parametrize(
    "chave_proibida",
    [
        "motivo_detalhe",
        "valor_anterior",
        "valor_novo",
        "cliente_atual_id",
        "cliente_atual_id_no_momento",
        "assinatura_a3_hash",
        "numero_serie",
    ],
)
def test_unhappy_chave_proibida_levanta(chave_proibida):
    payload = {
        "tenant_id": "uuid",
        "equipamento_id": "uuid",
        "versao_id": "uuid",
        "campo": "x",
        "motivo_mudanca": "outros",
        chave_proibida: "valor_qualquer",
    }
    with pytest.raises(PayloadVazandoPII, match=r"INV-EQP-VERSAO-002"):
        _validar_payload_anti_vaza(payload)


def test_unhappy_chave_fora_da_whitelist():
    """Defesa em profundidade — chave nao listada (nao proibida nem
    permitida) tambem levanta. Forca PR pra adicionar a whitelist."""
    payload = {
        "tenant_id": "uuid",
        "campo_inventado_nao_listado": "x",
    }
    assert "campo_inventado_nao_listado" not in CAMPOS_PAYLOAD_PERMITIDOS
    with pytest.raises(PayloadVazandoPII, match=r"fora da lista positiva"):
        _validar_payload_anti_vaza(payload)
