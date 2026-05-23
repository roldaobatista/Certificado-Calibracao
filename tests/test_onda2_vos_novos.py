"""Testes dos VOs novos da Onda 2 saneamento (2026-05-23).

Cobre:
  - JanelaVigencia (ADR-0030 — INV-VIG-001..004)
  - ReferenciaPIIAnonimizavel (ADR-0032 — INV-ANON-001/003)
  - Telefone (E.164 + DDD-BR)
  - UF, PaisISO3166
  - Dinheiro
  - FaixaMedicao, IncertezaExpandida, Grandeza, NumeroCertificado

Padrão TST-005: cada função pública de VO tem ≥1 happy + ≥1 borda explícita.
Padrão TST-006: testes determinísticos (sem uuid.uuid4 em assertions).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
    NumeroCertificado,
)
from src.domain.shared.value_objects import (
    UF,
    Dinheiro,
    JanelaVigencia,
    PaisISO3166,
    ReferenciaPIIAnonimizavel,
    Telefone,
    TenantLifecycleEstado,
    TransicaoInvalida,
    transicoes_validas_de,
    validar_transicao_tenant,
)

# =========================================================================
# JanelaVigencia (ADR-0030 — INV-VIG-001..004)
# =========================================================================


class TestJanelaVigencia:
    def test_inv_vig_001_happy_inicio_antes_fim(self) -> None:
        ini = datetime(2026, 1, 1, tzinfo=UTC)
        fim = datetime(2027, 1, 1, tzinfo=UTC)
        v = JanelaVigencia(inicio=ini, fim=fim)
        assert v.inicio == ini
        assert v.fim == fim

    def test_inv_vig_001_unhappy_inicio_apos_fim(self) -> None:
        ini = datetime(2026, 1, 1, tzinfo=UTC)
        fim = datetime(2025, 1, 1, tzinfo=UTC)
        with pytest.raises(ValueError, match="INV-VIG-001"):
            JanelaVigencia(inicio=ini, fim=fim)

    def test_inv_vig_002_happy_revogado_com_motivo(self) -> None:
        v = JanelaVigencia(
            inicio=datetime(2026, 1, 1, tzinfo=UTC),
            fim=datetime(2027, 1, 1, tzinfo=UTC),
            revogado_em=datetime(2026, 6, 1, tzinfo=UTC),
            motivo_revogacao="ausencia prolongada do RT por afastamento medico",
        )
        assert v.revogado_em is not None

    def test_inv_vig_002_unhappy_revogado_sem_motivo(self) -> None:
        with pytest.raises(ValueError, match="INV-VIG-002"):
            JanelaVigencia(
                inicio=datetime(2026, 1, 1, tzinfo=UTC),
                revogado_em=datetime(2026, 6, 1, tzinfo=UTC),
                motivo_revogacao="curto",  # < 10 chars
            )

    def test_inv_vig_003_unhappy_revogado_apos_fim(self) -> None:
        with pytest.raises(ValueError, match="INV-VIG-003"):
            JanelaVigencia(
                inicio=datetime(2026, 1, 1, tzinfo=UTC),
                fim=datetime(2026, 6, 1, tzinfo=UTC),
                revogado_em=datetime(2027, 1, 1, tzinfo=UTC),  # > fim
                motivo_revogacao="motivo qualquer com mais de 10 chars",
            )

    def test_inv_vig_004_unhappy_datetime_naive(self) -> None:
        with pytest.raises(ValueError, match="INV-VIG-004"):
            JanelaVigencia(inicio=datetime(2026, 1, 1))  # sem tz

    def test_vigente_em_dentro_da_janela(self) -> None:
        v = JanelaVigencia(
            inicio=datetime(2026, 1, 1, tzinfo=UTC),
            fim=datetime(2027, 1, 1, tzinfo=UTC),
        )
        assert v.vigente_em(datetime(2026, 6, 1, tzinfo=UTC)) is True

    def test_vigente_em_antes_do_inicio(self) -> None:
        v = JanelaVigencia(inicio=datetime(2026, 6, 1, tzinfo=UTC))
        assert v.vigente_em(datetime(2026, 1, 1, tzinfo=UTC)) is False

    def test_vigente_em_apos_revogacao(self) -> None:
        v = JanelaVigencia(
            inicio=datetime(2026, 1, 1, tzinfo=UTC),
            revogado_em=datetime(2026, 6, 1, tzinfo=UTC),
            motivo_revogacao="afastamento permanente do RT",
        )
        assert v.vigente_em(datetime(2026, 7, 1, tzinfo=UTC)) is False
        assert v.vigente_em(datetime(2026, 3, 1, tzinfo=UTC)) is True


# =========================================================================
# ReferenciaPIIAnonimizavel (ADR-0032 — INV-ANON-001/003)
# =========================================================================


class TestReferenciaPIIAnonimizavel:
    def test_happy_referencia_viva(self) -> None:
        ref = ReferenciaPIIAnonimizavel(
            uuid_atual_id=UUID("12345678-1234-1234-1234-123456789012"),
            hash_original="a" * 64,
            key_id="v1",
        )
        assert not ref.eliminada()

    def test_zona_a_referencia_eliminada(self) -> None:
        ref = ReferenciaPIIAnonimizavel(
            uuid_atual_id=None,  # Zona A — eliminacao efetiva
            hash_original="a" * 64,
            key_id="v1",
        )
        assert ref.eliminada()

    def test_inv_anon_001_unhappy_hash_vazio(self) -> None:
        with pytest.raises(ValueError, match="INV-ANON-001"):
            ReferenciaPIIAnonimizavel(
                uuid_atual_id=None,
                hash_original="",
                key_id="v1",
            )

    def test_inv_anon_001_unhappy_hash_curto(self) -> None:
        with pytest.raises(ValueError, match="hash_original tamanho"):
            ReferenciaPIIAnonimizavel(
                uuid_atual_id=None,
                hash_original="curto",
                key_id="v1",
            )

    def test_inv_anon_003_unhappy_key_id_formato(self) -> None:
        with pytest.raises(ValueError, match="key_id formato"):
            ReferenciaPIIAnonimizavel(
                uuid_atual_id=None,
                hash_original="a" * 64,
                key_id="invalido",  # nao bate ^v\d+$
            )


# =========================================================================
# Telefone E.164 + DDD-BR
# =========================================================================


class TestTelefone:
    def test_happy_celular_br_e164(self) -> None:
        t = Telefone("+5511987654321")
        assert t.value == "+5511987654321"
        assert t.is_brasileiro
        assert t.is_celular_br

    def test_happy_fixo_br_e164(self) -> None:
        t = Telefone("+551134567890")
        assert t.is_brasileiro
        assert not t.is_celular_br

    def test_happy_internacional(self) -> None:
        t = Telefone("+14155551234")
        assert not t.is_brasileiro
        assert not t.is_celular_br

    def test_auto_correcao_sem_codigo_pais(self) -> None:
        t = Telefone("11987654321")
        assert t.value == "+5511987654321"

    def test_aceita_formatacao_com_pontuacao(self) -> None:
        t = Telefone("(11) 98765-4321")
        assert t.value == "+5511987654321"

    def test_unhappy_ddd_invalido(self) -> None:
        with pytest.raises(ValueError, match="DDD"):
            Telefone("+5500987654321")  # DDD 00 invalido

    def test_unhappy_curto_demais(self) -> None:
        with pytest.raises(ValueError):
            Telefone("+551")


# =========================================================================
# UF + PaisISO3166
# =========================================================================


class TestUF:
    def test_happy_sp(self) -> None:
        assert UF("SP").value == "SP"

    def test_normaliza_lowercase(self) -> None:
        assert UF("sp").value == "SP"

    def test_unhappy_uf_inexistente(self) -> None:
        with pytest.raises(ValueError, match="UF invalida"):
            UF("XX")


class TestPaisISO3166:
    def test_happy_br(self) -> None:
        assert PaisISO3166("BR").value == "BR"

    def test_normaliza_lowercase(self) -> None:
        assert PaisISO3166("br").value == "BR"

    def test_unhappy_formato(self) -> None:
        with pytest.raises(ValueError, match="formato"):
            PaisISO3166("BRA")


# =========================================================================
# Dinheiro (centavos + ISO 4217)
# =========================================================================


class TestDinheiro:
    def test_happy_brl(self) -> None:
        d = Dinheiro(centavos=12345)
        assert d.moeda == "BRL"
        assert d.centavos == 12345

    def test_soma_mesma_moeda(self) -> None:
        d1 = Dinheiro(100, "BRL")
        d2 = Dinheiro(50, "BRL")
        assert (d1 + d2).centavos == 150

    def test_unhappy_soma_moedas_diferentes(self) -> None:
        d1 = Dinheiro(100, "BRL")
        d2 = Dinheiro(50, "USD")
        with pytest.raises(ValueError, match="nao soma"):
            d1 + d2

    def test_unhappy_float_em_centavos(self) -> None:
        with pytest.raises(ValueError, match="deve ser int"):
            Dinheiro(centavos=1.5)  # type: ignore[arg-type]

    def test_multiplicacao_por_int(self) -> None:
        d = Dinheiro(100, "BRL")
        assert (d * 3).centavos == 300

    def test_representacao_str(self) -> None:
        assert str(Dinheiro(12345, "BRL")) == "BRL 123,45"
        assert str(Dinheiro(-100, "BRL")) == "BRL -1,00"


# =========================================================================
# Grandeza, FaixaMedicao, IncertezaExpandida, NumeroCertificado
# =========================================================================


class TestGrandeza:
    def test_happy_massa(self) -> None:
        assert Grandeza.from_string("massa") == Grandeza.MASSA

    def test_normaliza_uppercase(self) -> None:
        assert Grandeza.from_string("MASSA") == Grandeza.MASSA

    def test_unhappy_grandeza_desconhecida(self) -> None:
        with pytest.raises(ValueError, match="Grandeza desconhecida"):
            Grandeza.from_string("inventada")


class TestFaixaMedicao:
    def test_happy(self) -> None:
        f = FaixaMedicao(Decimal("0"), Decimal("200"), "kg")
        assert f.amplitude() == Decimal("200")
        assert f.contem(Decimal("100"))

    def test_unhappy_inferior_maior(self) -> None:
        with pytest.raises(ValueError, match="inferior"):
            FaixaMedicao(Decimal("200"), Decimal("0"), "kg")

    def test_unhappy_float_em_vez_de_decimal(self) -> None:
        with pytest.raises(ValueError, match="Decimal"):
            FaixaMedicao(0.0, 200.0, "kg")  # type: ignore[arg-type]

    def test_unhappy_unidade_fora_whitelist(self) -> None:
        with pytest.raises(ValueError, match="whitelist"):
            FaixaMedicao(Decimal("0"), Decimal("200"), "quilo")


class TestIncertezaExpandida:
    def test_happy_k2_normal(self) -> None:
        u = IncertezaExpandida(
            valor=Decimal("0.05"),
            fator_k=Decimal("2"),
            nivel_confianca=Decimal("0.9545"),
            unidade="kg",
        )
        assert u.incerteza_padrao_combinada() == Decimal("0.025")

    def test_unhappy_nivel_fora_intervalo(self) -> None:
        with pytest.raises(ValueError, match="nivel_confianca"):
            IncertezaExpandida(
                valor=Decimal("0.05"),
                fator_k=Decimal("2"),
                nivel_confianca=Decimal("95.45"),  # deveria ser 0.9545
                unidade="kg",
            )

    def test_unhappy_valor_negativo(self) -> None:
        with pytest.raises(ValueError, match="valor"):
            IncertezaExpandida(
                valor=Decimal("-0.01"),
                fator_k=Decimal("2"),
                nivel_confianca=Decimal("0.95"),
                unidade="kg",
            )

    def test_unhappy_k_zero(self) -> None:
        with pytest.raises(ValueError, match="fator_k"):
            IncertezaExpandida(
                valor=Decimal("0.05"),
                fator_k=Decimal("0"),
                nivel_confianca=Decimal("0.95"),
                unidade="kg",
            )


class TestNumeroCertificado:
    def test_happy(self) -> None:
        n = NumeroCertificado("BALANCAS-2026-000042")
        assert n.tenant_slug == "BALANCAS"
        assert n.ano == 2026
        assert n.sequencial == 42

    def test_normaliza_lowercase(self) -> None:
        assert NumeroCertificado("balancas-2026-000042").value == "BALANCAS-2026-000042"

    def test_unhappy_formato(self) -> None:
        with pytest.raises(ValueError, match="formato"):
            NumeroCertificado("BALANCAS_2026_42")


# =========================================================================
# F-A-M3 — TenantLifecycleEstado (Onda 2 saneamento — 2026-05-22)
# =========================================================================


class TestTenantLifecycleEstado:
    def test_enum_tem_7_estados(self) -> None:
        assert len(list(TenantLifecycleEstado)) == 7
        nomes = {e.name for e in TenantLifecycleEstado}
        assert nomes == {
            "PROVISIONANDO",
            "ATIVO",
            "SUSPENSO_INADIMPLENCIA",
            "READONLY",
            "BLOQUEADO",
            "CANCELANDO",
            "EXTINTO",
        }

    def test_transicao_valida_provisionando_para_ativo(self) -> None:
        # nao levanta
        validar_transicao_tenant(
            TenantLifecycleEstado.PROVISIONANDO,
            TenantLifecycleEstado.ATIVO,
        )

    def test_transicao_invalida_provisionando_para_bloqueado(self) -> None:
        with pytest.raises(TransicaoInvalida, match="transicao invalida"):
            validar_transicao_tenant(
                TenantLifecycleEstado.PROVISIONANDO,
                TenantLifecycleEstado.BLOQUEADO,
            )

    def test_extinto_eh_terminal(self) -> None:
        assert transicoes_validas_de(TenantLifecycleEstado.EXTINTO) == frozenset()
        # qualquer destino a partir de EXTINTO deve levantar
        for destino in TenantLifecycleEstado:
            if destino == TenantLifecycleEstado.EXTINTO:
                continue
            with pytest.raises(TransicaoInvalida):
                validar_transicao_tenant(TenantLifecycleEstado.EXTINTO, destino)

    def test_ativo_pode_ir_para_4_estados(self) -> None:
        permitidos = transicoes_validas_de(TenantLifecycleEstado.ATIVO)
        assert permitidos == frozenset({
            TenantLifecycleEstado.SUSPENSO_INADIMPLENCIA,
            TenantLifecycleEstado.READONLY,
            TenantLifecycleEstado.BLOQUEADO,
            TenantLifecycleEstado.CANCELANDO,
        })

    def test_suspenso_volta_para_ativo_ou_escala_para_bloqueado(self) -> None:
        permitidos = transicoes_validas_de(
            TenantLifecycleEstado.SUSPENSO_INADIMPLENCIA
        )
        assert TenantLifecycleEstado.ATIVO in permitidos
        assert TenantLifecycleEstado.BLOQUEADO in permitidos

    def test_cancelando_so_vai_para_extinto(self) -> None:
        assert transicoes_validas_de(TenantLifecycleEstado.CANCELANDO) == frozenset({
            TenantLifecycleEstado.EXTINTO,
        })

    def test_str_da_estado_retorna_valor(self) -> None:
        assert str(TenantLifecycleEstado.ATIVO) == "ativo"
        assert (
            str(TenantLifecycleEstado.SUSPENSO_INADIMPLENCIA)
            == "suspenso_inadimplencia"
        )
