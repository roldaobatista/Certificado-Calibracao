"""Tests helpers LGPD M4 — derivacao server-side de hashes PII +
sanitizar_payload_evento_calibracao.

Conserto Batch S2 — SEG-CAL-01/03/07/08 + LGPD-CAL-01 da 1a passada
Familia 5 (2026-05-27).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from src.infrastructure.calibracao.lgpd import (
    derivar_cliente_key_id,
    derivar_cliente_referencia_hash,
    derivar_hash_texto_canonicalizado,
    sanitizar_payload_evento_calibracao,
)

# =====================================================================
# derivar_cliente_referencia_hash — SEG-CAL-01
# =====================================================================


class TestDerivarClienteReferenciaHash:
    def test_formato_canonico(self) -> None:
        tenant = uuid4()
        cli = uuid4()
        h = derivar_cliente_referencia_hash(cliente_id=cli, tenant_id=tenant)
        assert h.startswith("v01$"), h
        assert len(h) <= 80

    def test_determinismo(self) -> None:
        """Mesmo input -> mesmo hash."""
        tenant = uuid4()
        cli = uuid4()
        h1 = derivar_cliente_referencia_hash(cliente_id=cli, tenant_id=tenant)
        h2 = derivar_cliente_referencia_hash(cliente_id=cli, tenant_id=tenant)
        assert h1 == h2

    def test_isolamento_cross_tenant(self) -> None:
        """Mesmo cliente_id em tenants diferentes -> hashes diferentes."""
        cli = uuid4()
        h_a = derivar_cliente_referencia_hash(cliente_id=cli, tenant_id=uuid4())
        h_b = derivar_cliente_referencia_hash(cliente_id=cli, tenant_id=uuid4())
        assert h_a != h_b

    def test_isolamento_cross_cliente(self) -> None:
        """Mesmo tenant + clientes distintos -> hashes diferentes."""
        tenant = uuid4()
        h_a = derivar_cliente_referencia_hash(cliente_id=uuid4(), tenant_id=tenant)
        h_b = derivar_cliente_referencia_hash(cliente_id=uuid4(), tenant_id=tenant)
        assert h_a != h_b

    def test_avulsa_sem_cliente(self) -> None:
        """cliente_id=None gera hash canonico do tenant + sentinel."""
        tenant = uuid4()
        h = derivar_cliente_referencia_hash(cliente_id=None, tenant_id=tenant)
        assert h.startswith("v01$")
        # Determinismo da avulsa
        h2 = derivar_cliente_referencia_hash(cliente_id=None, tenant_id=tenant)
        assert h == h2

    def test_avulsa_difere_de_cliente_real(self) -> None:
        tenant = uuid4()
        h_avulsa = derivar_cliente_referencia_hash(cliente_id=None, tenant_id=tenant)
        h_cliente = derivar_cliente_referencia_hash(
            cliente_id=uuid4(), tenant_id=tenant
        )
        assert h_avulsa != h_cliente


# =====================================================================
# derivar_cliente_key_id
# =====================================================================


class TestDerivarClienteKeyId:
    def test_formato(self) -> None:
        tenant = uuid4()
        key = derivar_cliente_key_id(tenant_id=tenant)
        assert key.startswith("tenant-")
        assert key.endswith("-key-v01")

    def test_determinismo(self) -> None:
        tenant = uuid4()
        assert derivar_cliente_key_id(tenant_id=tenant) == derivar_cliente_key_id(
            tenant_id=tenant
        )

    def test_isolamento_cross_tenant(self) -> None:
        assert derivar_cliente_key_id(tenant_id=uuid4()) != derivar_cliente_key_id(
            tenant_id=uuid4()
        )


# =====================================================================
# derivar_hash_texto_canonicalizado — SEG-CAL-07/08
# =====================================================================


class TestDerivarHashTexto:
    def test_formato_canonico(self) -> None:
        h = derivar_hash_texto_canonicalizado(
            texto="cliente desistiu apos analise critica", tenant_id=uuid4()
        )
        assert h.startswith("v01$")

    def test_determinismo(self) -> None:
        tenant = uuid4()
        texto = "x" * 50
        assert derivar_hash_texto_canonicalizado(
            texto=texto, tenant_id=tenant
        ) == derivar_hash_texto_canonicalizado(texto=texto, tenant_id=tenant)

    def test_texto_diferente_gera_hash_diferente(self) -> None:
        tenant = uuid4()
        h_a = derivar_hash_texto_canonicalizado(texto="motivo A", tenant_id=tenant)
        h_b = derivar_hash_texto_canonicalizado(texto="motivo B", tenant_id=tenant)
        assert h_a != h_b

    def test_isolamento_cross_tenant_mesmo_texto(self) -> None:
        texto = "mesmo texto"
        h_a = derivar_hash_texto_canonicalizado(texto=texto, tenant_id=uuid4())
        h_b = derivar_hash_texto_canonicalizado(texto=texto, tenant_id=uuid4())
        assert h_a != h_b


# =====================================================================
# sanitizar_payload_evento_calibracao — SEG-CAL-03 + LGPD-CAL-01
# =====================================================================


class TestSanitizarPayloadEvento:
    def test_finalidade_obrigatoria(self) -> None:
        with pytest.raises(ValueError, match="finalidade"):
            sanitizar_payload_evento_calibracao({}, finalidade="")

    def test_finalidade_muito_curta_recusa(self) -> None:
        with pytest.raises(ValueError, match="finalidade"):
            sanitizar_payload_evento_calibracao({}, finalidade="abc")

    def test_pii_denylist_redigida(self) -> None:
        out = sanitizar_payload_evento_calibracao(
            {"cpf": "12345678900", "nome": "Joao da Silva"},
            finalidade="calibracao_recepcionada",
        )
        assert out["cpf"] == "[REDACTED-PII]"
        assert out["nome"] == "[REDACTED-PII]"

    def test_uuid_estrutural_preservado(self) -> None:
        cid = str(uuid4())
        out = sanitizar_payload_evento_calibracao(
            {"calibracao_id": cid, "correlation_id": cid, "executor_id": cid},
            finalidade="calibracao_recepcionada",
        )
        assert out["calibracao_id"] == cid
        assert out["correlation_id"] == cid
        assert out["executor_id"] == cid

    def test_hash_versionado_preservado(self) -> None:
        out = sanitizar_payload_evento_calibracao(
            {"cliente_referencia_hash": "v01$ABC123="},
            finalidade="calibracao_recepcionada",
        )
        assert out["cliente_referencia_hash"] == "v01$ABC123="

    def test_dict_aninhado(self) -> None:
        out = sanitizar_payload_evento_calibracao(
            {"endereco_cliente": {"cep": "01310-100", "logradouro": "Av Paulista"}},
            finalidade="calibracao_aprovada",
        )
        # `endereco_cliente` nao bate denylist exata (mas o helper nao
        # entra recursivo nele pq nao casa). Conteudo do dict aninhado
        # tem chaves `cep` + `logradouro` (na denylist) -> redigidos.
        assert out["endereco_cliente"]["cep"] == "[REDACTED-PII]"
        assert out["endereco_cliente"]["logradouro"] == "[REDACTED-PII]"

    def test_lista_recursivo(self) -> None:
        out = sanitizar_payload_evento_calibracao(
            {"contatos": [{"email": "x@y.com"}, {"telefone": "11999998888"}]},
            finalidade="reclamacao_recebida",
        )
        assert out["contatos"][0]["email"] == "[REDACTED-PII]"
        assert out["contatos"][1]["telefone"] == "[REDACTED-PII]"

    def test_nao_muta_input(self) -> None:
        original = {"cpf": "12345"}
        sanitizar_payload_evento_calibracao(
            original, finalidade="calibracao_recepcionada"
        )
        assert original["cpf"] == "12345"

    def test_uuid_digit_heavy_em_valor_preservado(self) -> None:
        """Paralelo bug `sanitizar_payload_audit` 2026-05-19: UUID
        digit-heavy nao deve ser confundido com PII numerica."""
        uuid_digit_heavy = "33333333-3333-4333-8333-333333333333"
        out = sanitizar_payload_evento_calibracao(
            {"executor_id": uuid_digit_heavy},
            finalidade="leitura_registrada",
        )
        assert out["executor_id"] == uuid_digit_heavy
