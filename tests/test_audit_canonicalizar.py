"""Testes da canonicalizacao JSON — puros, sem banco.

Cobertura critica: 2 maquinas calculando o mesmo payload TEM que chegar no mesmo
JSON canonico. Sem isso, hash chain quebra com falso-positivo.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from src.infrastructure.audit.canonicalizar import canonicalizar


class TestOrdemDeterministica:
    def test_chaves_em_ordem_alfabetica_independente_de_insercao(self) -> None:
        p1 = {"b": 1, "a": 2, "c": 3}
        p2 = {"c": 3, "a": 2, "b": 1}
        assert canonicalizar(p1) == canonicalizar(p2)
        assert canonicalizar(p1) == '{"a":2,"b":1,"c":3}'

    def test_chaves_nested_tambem_ordenadas(self) -> None:
        p = {"z": {"b": 1, "a": 2}, "a": [{"y": 1, "x": 2}]}
        out = canonicalizar(p)
        # ambos os nested ordenados
        assert out == '{"a":[{"x":2,"y":1}],"z":{"a":2,"b":1}}'

    def test_sem_espaco_apos_virgula_ou_dois_pontos(self) -> None:
        out = canonicalizar({"a": 1, "b": 2})
        assert ", " not in out
        assert ": " not in out


class TestTiposCustom:
    def test_datetime_utc_isoformat(self) -> None:
        dt = datetime(2026, 5, 17, 14, 30, 0, tzinfo=timezone.utc)
        out = canonicalizar({"ts": dt})
        assert '"ts":"2026-05-17T14:30:00+00:00"' in out

    def test_datetime_naive_e_proibido(self) -> None:
        dt = datetime(2026, 5, 17, 14, 30, 0)  # sem tz
        with pytest.raises(ValueError, match="naive proibido"):
            canonicalizar({"ts": dt})

    def test_date_isoformat(self) -> None:
        d = date(2026, 5, 17)
        assert canonicalizar({"d": d}) == '{"d":"2026-05-17"}'

    def test_decimal_preserva_precisao(self) -> None:
        # Float perderia precisao; Decimal stringifica sem virar float
        valor = Decimal("12.345678901234567890")
        out = canonicalizar({"v": valor})
        assert '"v":"12.345678901234567890"' in out

    def test_uuid_stringifica(self) -> None:
        u = UUID("11111111-2222-3333-4444-555555555555")
        out = canonicalizar({"id": u})
        assert '"id":"11111111-2222-3333-4444-555555555555"' in out

    def test_acentos_preservados_utf8(self) -> None:
        out = canonicalizar({"msg": "calibração concluída"})
        assert "calibração" in out  # nao escapou pra \u...

    def test_tipo_desconhecido_levanta(self) -> None:
        class Estranho:
            pass

        with pytest.raises(TypeError, match="nao-serializavel"):
            canonicalizar({"x": Estranho()})  # type: ignore[dict-item]


class TestHashChainHelper:
    """Confirma que helpers canonicalizar + calcular_hash produzem resultado estavel."""

    def test_hash_estavel_para_mesmo_payload(self) -> None:
        from src.infrastructure.audit.hash_chain import calcular_hash

        payload = {"action": "criar", "id": 42}
        canon = canonicalizar(payload)
        h1 = calcular_hash(None, canon)
        h2 = calcular_hash(None, canon)
        assert h1 == h2
        assert len(h1) == 64  # sha256 hex

    def test_hash_muda_se_hash_anterior_muda(self) -> None:
        from src.infrastructure.audit.hash_chain import calcular_hash

        canon = canonicalizar({"a": 1})
        h1 = calcular_hash(None, canon)
        h2 = calcular_hash("abc123", canon)
        assert h1 != h2

    def test_hash_muda_se_payload_muda(self) -> None:
        from src.infrastructure.audit.hash_chain import calcular_hash

        h1 = calcular_hash(None, canonicalizar({"a": 1}))
        h2 = calcular_hash(None, canonicalizar({"a": 2}))
        assert h1 != h2
