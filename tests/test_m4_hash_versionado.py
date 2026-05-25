"""Testes helpers crypto HashVersionado (P4 Fase 2 Batch B — T-CAL-031..036).

Cobre:
  - validar_versao (T-CAL-031)
  - parsear_hash_versionado (T-CAL-032)
  - formatar_hash_versionado (T-CAL-033)
  - canonicalizar_payload_para_hmac (T-CAL-034)
  - Roundtrip parse->format == identidade (T-CAL-035)
  - Determinismo: mesma input -> mesma saida (T-CAL-036)

Sem KMS, sem rede. Helpers puros.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

import pytest
from src.domain.metrologia.calibracao.hash_versionado import (
    HMAC_SHA256_BYTES,
    VERSAO_HMAC_ATUAL,
    FormatoHashVersionadoInvalido,
    VersaoForaDoIntervalo,
    canonicalizar_payload_para_hmac,
    formatar_hash_versionado,
    parsear_hash_versionado,
    validar_versao,
)

# =====================================================================
# validar_versao (T-CAL-031)
# =====================================================================


class TestValidarVersao:
    def test_happy_v1(self) -> None:
        assert validar_versao(1) == 1

    def test_happy_v99(self) -> None:
        assert validar_versao(99) == 99

    def test_rejeita_versao_zero(self) -> None:
        with pytest.raises(VersaoForaDoIntervalo):
            validar_versao(0)

    def test_rejeita_versao_100(self) -> None:
        with pytest.raises(VersaoForaDoIntervalo):
            validar_versao(100)

    def test_rejeita_versao_negativa(self) -> None:
        with pytest.raises(VersaoForaDoIntervalo):
            validar_versao(-1)

    def test_rejeita_tipo_nao_int(self) -> None:
        with pytest.raises(TypeError):
            validar_versao("1")  # type: ignore[arg-type]

    def test_versao_atual_eh_valida(self) -> None:
        # Sanity check da constante de producao
        assert validar_versao(VERSAO_HMAC_ATUAL) == VERSAO_HMAC_ATUAL


# =====================================================================
# parsear_hash_versionado (T-CAL-032)
# =====================================================================


class TestParsearHashVersionado:
    def test_happy_v01(self) -> None:
        versao, hmac_bytes = parsear_hash_versionado("v01$aGVsbG8=")
        assert versao == 1
        assert hmac_bytes == b"hello"

    def test_happy_v99(self) -> None:
        versao, hmac_bytes = parsear_hash_versionado("v99$YWJj")
        assert versao == 99
        assert hmac_bytes == b"abc"

    def test_aceita_hmac_sha256_real_32_bytes(self) -> None:
        chave = b"\x00" * 32
        bruto = b"payload-canonico"
        hmac_bytes = hmac.new(chave, bruto, hashlib.sha256).digest()
        raw = formatar_hash_versionado(1, hmac_bytes)
        v, b = parsear_hash_versionado(raw)
        assert v == 1
        assert b == hmac_bytes
        assert len(b) == HMAC_SHA256_BYTES

    def test_rejeita_versao_zero(self) -> None:
        with pytest.raises(VersaoForaDoIntervalo):
            parsear_hash_versionado("v00$aGVsbG8=")

    def test_rejeita_formato_sem_v(self) -> None:
        with pytest.raises(FormatoHashVersionadoInvalido):
            parsear_hash_versionado("01$aGVsbG8=")

    def test_rejeita_versao_1_digito(self) -> None:
        with pytest.raises(FormatoHashVersionadoInvalido):
            parsear_hash_versionado("v1$aGVsbG8=")

    def test_rejeita_separador_errado(self) -> None:
        with pytest.raises(FormatoHashVersionadoInvalido):
            parsear_hash_versionado("v01:aGVsbG8=")

    def test_rejeita_base64_invalido(self) -> None:
        # ! nao eh base64 valido
        with pytest.raises(FormatoHashVersionadoInvalido):
            parsear_hash_versionado("v01$abc!def=")

    def test_rejeita_tipo_nao_str(self) -> None:
        with pytest.raises(FormatoHashVersionadoInvalido):
            parsear_hash_versionado(123)  # type: ignore[arg-type]

    def test_rejeita_string_vazia(self) -> None:
        with pytest.raises(FormatoHashVersionadoInvalido):
            parsear_hash_versionado("")


# =====================================================================
# formatar_hash_versionado (T-CAL-033)
# =====================================================================


class TestFormatarHashVersionado:
    def test_happy_v1(self) -> None:
        raw = formatar_hash_versionado(1, b"hello")
        assert raw == "v01$aGVsbG8="

    def test_happy_v99(self) -> None:
        raw = formatar_hash_versionado(99, b"\x00\x01\x02")
        assert raw.startswith("v99$")

    def test_zero_padding_versao(self) -> None:
        # Versao 5 vira "v05" nao "v5"
        raw = formatar_hash_versionado(5, b"x")
        assert raw.startswith("v05$")

    def test_rejeita_versao_fora_intervalo(self) -> None:
        with pytest.raises(VersaoForaDoIntervalo):
            formatar_hash_versionado(100, b"x")

    def test_rejeita_hmac_bytes_nao_bytes(self) -> None:
        with pytest.raises(TypeError):
            formatar_hash_versionado(1, "string")  # type: ignore[arg-type]

    def test_aceita_bytearray(self) -> None:
        ba = bytearray(b"hello")
        raw = formatar_hash_versionado(1, ba)
        assert raw == "v01$aGVsbG8="

    def test_aceita_hmac_vazio(self) -> None:
        # Caso de borda — hmac_bytes vazio (so formatacao, nao semantica)
        raw = formatar_hash_versionado(1, b"")
        assert raw == "v01$"


# =====================================================================
# Roundtrip parse <-> format (T-CAL-035)
# =====================================================================


class TestRoundtrip:
    @pytest.mark.parametrize("versao", [1, 5, 10, 50, 99])
    def test_roundtrip_versoes_validas(self, versao: int) -> None:
        original = b"\x42" * 32  # 32 bytes "simulando" HMAC-SHA256
        raw = formatar_hash_versionado(versao, original)
        v_decoded, b_decoded = parsear_hash_versionado(raw)
        assert v_decoded == versao
        assert b_decoded == original

    def test_roundtrip_hmac_aleatorio_diversos_tamanhos(self) -> None:
        # base64 com padding variavel (0, 1, 2 chars de =)
        for tam in (32, 33, 34):
            original = bytes(range(tam))
            raw = formatar_hash_versionado(1, original)
            _, b = parsear_hash_versionado(raw)
            assert b == original


# =====================================================================
# canonicalizar_payload_para_hmac (T-CAL-034 + INV-HMAC-005)
# =====================================================================


class TestCanonicalizarPayload:
    def test_happy_dict_simples(self) -> None:
        bytes_canon = canonicalizar_payload_para_hmac({"b": 2, "a": 1})
        # sort_keys=True -> "a" antes de "b"
        assert bytes_canon == b'{"a":1,"b":2}'

    def test_separadores_sem_espacos(self) -> None:
        bytes_canon = canonicalizar_payload_para_hmac({"x": "y", "z": 1})
        # nao deve ter espacos (separators=(',',':'))
        assert b" " not in bytes_canon

    def test_preserva_acentos_utf8_nfc(self) -> None:
        # INV-DOC-CANON-001 — NFC + UTF-8 sem BOM
        bytes_canon = canonicalizar_payload_para_hmac({"motivo": "calibração"})
        # ensure_ascii=False preserva caracteres UTF-8
        assert "ção".encode() in bytes_canon

    def test_determinismo_mesma_input_mesma_saida(self) -> None:
        # Replay deterministico: rodando 100x da mesma saida
        payload = {"cliente_id": "abc", "valor": "10.5", "data": "2026-05-25"}
        primeira = canonicalizar_payload_para_hmac(payload)
        for _ in range(100):
            assert canonicalizar_payload_para_hmac(payload) == primeira

    def test_ordem_keys_diferente_mesma_saida(self) -> None:
        # Mesmo dado em ordem diferente -> mesma representacao canónica
        a = canonicalizar_payload_para_hmac({"a": 1, "b": 2, "c": 3})
        b = canonicalizar_payload_para_hmac({"c": 3, "a": 1, "b": 2})
        assert a == b

    def test_nested_dict_sort_recursivo(self) -> None:
        # sort_keys=True do json funciona recursivamente
        a = canonicalizar_payload_para_hmac({"outer": {"z": 1, "a": 2}})
        assert a == b'{"outer":{"a":2,"z":1}}'

    def test_rejeita_payload_nao_serializavel(self) -> None:
        # set nao eh JSON-nativo
        with pytest.raises(TypeError):
            canonicalizar_payload_para_hmac({"x": {1, 2, 3}})

    def test_rejeita_nan(self) -> None:
        # allow_nan=False — INV-HMAC-005: NaN viola determinismo
        with pytest.raises(TypeError):
            canonicalizar_payload_para_hmac({"valor": float("nan")})

    def test_lista_preservada_em_ordem(self) -> None:
        # Listas NAO sao reordenadas (semantica preservada — ordem importa)
        a = canonicalizar_payload_para_hmac({"pontos": [3, 1, 2]})
        assert a == b'{"pontos":[3,1,2]}'

    def test_string_vazia_e_zero_sao_validos(self) -> None:
        bytes_canon = canonicalizar_payload_para_hmac({"nome": "", "qtd": 0})
        assert bytes_canon == b'{"nome":"","qtd":0}'


# =====================================================================
# Integracao com hmac.new() — caminho real de uso
# =====================================================================


class TestIntegracaoHmacReal:
    def test_uso_completo_canonicalizar_hmac_formatar(self) -> None:
        """Simula caminho real: payload -> canonicaliza -> HMAC -> formata."""
        chave_kms_v1 = b"k" * 32  # placeholder; em prod vem do KMS MRK
        payload = {"calibracao_id": "uuid-abc", "regra_decisao": "BANDA_GUARDA_30"}

        bytes_canon = canonicalizar_payload_para_hmac(payload)
        hmac_bytes = hmac.new(chave_kms_v1, bytes_canon, hashlib.sha256).digest()
        raw = formatar_hash_versionado(1, hmac_bytes)

        # Hash gerado eh roundtrip-valido
        v, b = parsear_hash_versionado(raw)
        assert v == 1
        assert b == hmac_bytes
        assert len(b) == HMAC_SHA256_BYTES

    def test_mesmo_payload_diferentes_chamadas_mesma_assinatura(self) -> None:
        """Replay deterministico: rerunning -> mesma assinatura, sempre."""
        chave = b"k" * 32
        payload = {"id": "x", "n": 5}

        def assinar() -> str:
            bytes_canon = canonicalizar_payload_para_hmac(payload)
            hmac_bytes = hmac.new(chave, bytes_canon, hashlib.sha256).digest()
            return formatar_hash_versionado(1, hmac_bytes)

        primeiro = assinar()
        for _ in range(50):
            assert assinar() == primeiro

    def test_payload_diferente_assinatura_diferente(self) -> None:
        """Sanity: 1 bit de diferenca no payload -> hash totalmente diferente."""
        chave = b"k" * 32

        def assinar(p: dict) -> str:
            bc = canonicalizar_payload_para_hmac(p)
            h = hmac.new(chave, bc, hashlib.sha256).digest()
            return formatar_hash_versionado(1, h)

        a = assinar({"x": 1})
        b = assinar({"x": 2})
        assert a != b
        # Sanity: ambos parsearam ok
        assert parsear_hash_versionado(a)[0] == 1
        assert parsear_hash_versionado(b)[0] == 1


# =====================================================================
# Sanity check de constantes
# =====================================================================


def test_versao_hmac_atual_em_intervalo_valido() -> None:
    """VERSAO_HMAC_ATUAL deve sempre estar dentro do limite suportado."""
    assert 1 <= VERSAO_HMAC_ATUAL <= 99


def test_hmac_sha256_bytes_constante_correta() -> None:
    """HMAC-SHA256 produz 32 bytes (256 bits)."""
    chave = b"x"
    h = hmac.new(chave, b"payload", hashlib.sha256).digest()
    assert len(h) == HMAC_SHA256_BYTES == 32


def test_base64_de_32_bytes_tem_44_chars_com_padding() -> None:
    """Sanity check: 32 bytes -> 44 chars base64 RFC 4648 §3.2."""
    b64 = base64.b64encode(b"\x00" * 32).decode("ascii")
    assert len(b64) == 44  # 32*4/3 com padding
