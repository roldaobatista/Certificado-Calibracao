"""Regressao — `sanitizar_payload_audit` nao pode redigir UUID surrogate.

Causa-raiz do flake `test_visao_360_filtra_eventos_de_outros_clientes`:
~8.4% dos uuid4 tem corrida de digitos que casa a regex de CPF/telefone por
coincidencia. Sem o guard de UUID o `cliente_id`/`usuario_id`/`causation_id`
da timeline da visao 360 virava `[REDACTED]` e quebrava a correlacao
evento<->cliente. Bug de PRODUCAO (nao artefato de teste): ~8% dos clientes
reais teriam a timeline corrompida. Nao usa banco — funcao pura.
"""

from __future__ import annotations

from uuid import uuid4

from src.infrastructure.audit.services import sanitizar_payload_audit

# UUID v4 valido cujo 1o grupo eh todo digito → casava _RE_TELEFONE_AUDIT.
_UUID_DIGIT_HEAVY = "01234567-89ab-4cde-8f01-234567890123"


def test_uuid_digit_heavy_nao_eh_redigido_como_pii():
    out = sanitizar_payload_audit({"cliente_id": _UUID_DIGIT_HEAVY, "tag": "A"})
    assert out["cliente_id"] == _UUID_DIGIT_HEAVY
    assert out["tag"] == "A"


def test_qualquer_uuid4_real_passa_intacto():
    # Varredura: nenhum uuid4 pode ser confundido com PII (era ~8.4%).
    for _ in range(5000):
        uid = str(uuid4())
        assert sanitizar_payload_audit({"id": uid})["id"] == uid


def test_uuid_aninhado_em_lista_e_dict_preservado():
    payload = {"eventos": [{"cliente_id": _UUID_DIGIT_HEAVY}], "ref": _UUID_DIGIT_HEAVY}
    out = sanitizar_payload_audit(payload)
    assert out["eventos"][0]["cliente_id"] == _UUID_DIGIT_HEAVY
    assert out["ref"] == _UUID_DIGIT_HEAVY


def test_pii_real_continua_redigida_por_valor():
    assert sanitizar_payload_audit({"x": "123.456.789-09"})["x"] == "[REDACTED]"
    assert sanitizar_payload_audit({"x": "12.345.678/0001-95"})["x"] == "[REDACTED]"
    assert sanitizar_payload_audit({"x": "(11) 98888-7777"})["x"] == "[REDACTED]"
    assert sanitizar_payload_audit({"x": "fulano@exemplo.com.br"})["x"] == "[REDACTED]"


def test_chave_na_denylist_continua_redigida_mesmo_com_valor_uuid():
    # Defesa por chave nao pode ser enfraquecida pelo guard de UUID:
    # se a chave eh sabidamente PII, redige independente do valor.
    out = sanitizar_payload_audit({"cpf": _UUID_DIGIT_HEAVY, "nome": "x"})
    assert out["cpf"] == "[REDACTED]"
    assert out["nome"] == "[REDACTED]"


def test_string_nao_pii_nao_uuid_passa_intacta():
    assert sanitizar_payload_audit({"action": "cliente.evento_a"})["action"] == ("cliente.evento_a")
