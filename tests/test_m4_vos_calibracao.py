"""Testes dos 5 VOs novos M4 calibracao (P4 Fase 2 Batch A — T-CAL-026..030).

Cobre:
  - VersaoMotorCalculo (INV-CAL-VERSAO-001 + ADR-0025 cl. 7.11)
  - EscoreZ + ClassificacaoZ (P-CAL-R8 RBC + NIT-DICLA-026 cl. 5.4)
  - ZonaILACG8 (ADR-0024 revisado + INV-CAL-DEC-005)
  - HashVersionadoV0 (ADR-0064 + INV-HMAC-002)
  - IncertezaCombinada (GUM cl. 5.1.2)

Padroes:
  - TST-005: cada VO tem >=1 happy + >=1 borda explicita
  - TST-006: testes deterministicos (sem uuid.uuid4 em asserts)
  - Decimal puro em qualquer valor metrologico (nao float — INV-CAL-INC-003)
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from src.domain.metrologia.calibracao.value_objects import (
    ClassificacaoZ,
    EscoreZ,
    HashVersionadoV0,
    IncertezaCombinada,
    VersaoMotorCalculo,
    ZonaILACG8,
)
from src.domain.shared.value_objects import JanelaVigencia

# =====================================================================
# VersaoMotorCalculo (T-CAL-026)
# =====================================================================


def _janela_atual() -> JanelaVigencia:
    return JanelaVigencia(inicio=datetime(2026, 1, 1, tzinfo=UTC))


class TestVersaoMotorCalculo:
    def test_happy_gum_classico(self) -> None:
        v = VersaoMotorCalculo(
            semver="1.0.0",
            commit_hash="a" * 40,
            algoritmo_id="GUM_CLASSICO_v1",
            janela_vigencia=_janela_atual(),
        )
        assert v.semver == "1.0.0"
        assert "GUM_CLASSICO_v1" in str(v)

    def test_happy_monte_carlo(self) -> None:
        v = VersaoMotorCalculo(
            semver="2.1.3-rc1",
            commit_hash="b" * 40,
            algoritmo_id="MONTE_CARLO_v1",
            janela_vigencia=_janela_atual(),
        )
        assert v.algoritmo_id == "MONTE_CARLO_v1"

    def test_rejeita_semver_invalido(self) -> None:
        with pytest.raises(ValueError, match="semver invalido"):
            VersaoMotorCalculo(
                semver="1.0",
                commit_hash="a" * 40,
                algoritmo_id="GUM_CLASSICO_v1",
                janela_vigencia=_janela_atual(),
            )

    def test_rejeita_commit_hash_curto(self) -> None:
        with pytest.raises(ValueError, match="commit_hash invalido"):
            VersaoMotorCalculo(
                semver="1.0.0",
                commit_hash="abc",
                algoritmo_id="GUM_CLASSICO_v1",
                janela_vigencia=_janela_atual(),
            )

    def test_rejeita_commit_hash_uppercase(self) -> None:
        # ADR-0025: hash git eh lowercase
        with pytest.raises(ValueError, match="commit_hash invalido"):
            VersaoMotorCalculo(
                semver="1.0.0",
                commit_hash="A" * 40,
                algoritmo_id="GUM_CLASSICO_v1",
                janela_vigencia=_janela_atual(),
            )

    def test_rejeita_algoritmo_fora_da_whitelist(self) -> None:
        with pytest.raises(ValueError, match="algoritmo_id"):
            VersaoMotorCalculo(
                semver="1.0.0",
                commit_hash="a" * 40,
                algoritmo_id="BAYESIAN_v1",
                janela_vigencia=_janela_atual(),
            )


# =====================================================================
# EscoreZ + ClassificacaoZ (T-CAL-027)
# =====================================================================


class TestEscoreZ:
    def test_happy_aceitavel(self) -> None:
        ez = EscoreZ(valor=Decimal("1.5"))
        assert ez.classificacao == ClassificacaoZ.ACEITAVEL
        assert ez.magnitude == Decimal("1.5")

    def test_warning_z_2_5(self) -> None:
        # 2 < |z| <= 3 -> WARNING (P-CAL-R8)
        ez = EscoreZ(valor=Decimal("2.5"))
        assert ez.classificacao == ClassificacaoZ.WARNING

    def test_unacceptable_z_4(self) -> None:
        # |z| > 3 -> UNACCEPTABLE (AnaliseImpactoNCProficiencia)
        ez = EscoreZ(valor=Decimal("4.2"))
        assert ez.classificacao == ClassificacaoZ.UNACCEPTABLE

    def test_borda_z_exato_2(self) -> None:
        # |z| == 2 ainda aceitavel
        assert EscoreZ(valor=Decimal("2")).classificacao == ClassificacaoZ.ACEITAVEL
        assert EscoreZ(valor=Decimal("-2")).classificacao == ClassificacaoZ.ACEITAVEL

    def test_borda_z_exato_3(self) -> None:
        # |z| == 3 ainda WARNING
        assert EscoreZ(valor=Decimal("3")).classificacao == ClassificacaoZ.WARNING

    def test_z_negativo_usa_magnitude(self) -> None:
        ez = EscoreZ(valor=Decimal("-3.5"))
        assert ez.magnitude == Decimal("3.5")
        assert ez.classificacao == ClassificacaoZ.UNACCEPTABLE

    def test_regra_violada_whitelist(self) -> None:
        ez = EscoreZ(
            valor=Decimal("3.1"),
            regra_violada="RULE_1_3SIGMA",
        )
        assert ez.regra_violada == "RULE_1_3SIGMA"

    def test_rejeita_regra_fora_da_whitelist(self) -> None:
        with pytest.raises(ValueError, match="regra_violada"):
            EscoreZ(valor=Decimal("2.5"), regra_violada="RULE_INVENTADA")

    def test_rejeita_valor_float(self) -> None:
        # INV-CAL-INC-003 — Decimal puro
        with pytest.raises(ValueError, match="deve ser Decimal"):
            EscoreZ(valor=2.5)  # type: ignore[arg-type]


# =====================================================================
# ZonaILACG8 (T-CAL-028)
# =====================================================================


class TestZonaILACG8:
    def test_pass_aprova(self) -> None:
        assert ZonaILACG8.PASS.aprova
        assert ZonaILACG8.CONDITIONAL_PASS.aprova
        assert ZonaILACG8.PASS_COM_RESSALVA.aprova

    def test_fail_reprova(self) -> None:
        assert ZonaILACG8.FAIL.reprova
        assert ZonaILACG8.CONDITIONAL_FAIL.reprova
        assert ZonaILACG8.FAIL_COM_RESSALVA.reprova

    def test_pass_nao_reprova(self) -> None:
        assert not ZonaILACG8.PASS.reprova

    def test_na_nem_aprova_nem_reprova(self) -> None:
        # calibracao descritiva — sem limites
        assert not ZonaILACG8.NA.aprova
        assert not ZonaILACG8.NA.reprova

    def test_pfa_exigida_em_zonas_condicionais(self) -> None:
        assert ZonaILACG8.CONDITIONAL_PASS.exige_pfa_calculada
        assert ZonaILACG8.CONDITIONAL_FAIL.exige_pfa_calculada
        assert ZonaILACG8.PASS_COM_RESSALVA.exige_pfa_calculada
        assert ZonaILACG8.FAIL_COM_RESSALVA.exige_pfa_calculada

    def test_pfa_nao_exigida_em_pass_e_fail_puros(self) -> None:
        assert not ZonaILACG8.PASS.exige_pfa_calculada
        assert not ZonaILACG8.FAIL.exige_pfa_calculada
        assert not ZonaILACG8.NA.exige_pfa_calculada


# =====================================================================
# HashVersionadoV0 (T-CAL-029)
# =====================================================================


class TestHashVersionadoV0:
    def test_happy_v01(self) -> None:
        h = HashVersionadoV0(raw="v01$aGVsbG8=")
        assert h.versao == 1
        assert h.base64_hmac == "aGVsbG8="
        assert str(h) == "v01$aGVsbG8="

    def test_happy_v99(self) -> None:
        h = HashVersionadoV0(raw="v99$abc123==")
        assert h.versao == 99

    def test_rejeita_sem_prefixo_v(self) -> None:
        with pytest.raises(ValueError, match="formato invalido"):
            HashVersionadoV0(raw="01$aGVsbG8=")

    def test_rejeita_versao_1_digito(self) -> None:
        # Formato exige 2 digitos (v01 nao v1)
        with pytest.raises(ValueError, match="formato invalido"):
            HashVersionadoV0(raw="v1$aGVsbG8=")

    def test_rejeita_versao_zero(self) -> None:
        # Versao 00 fora de [1, 99]
        with pytest.raises(ValueError):
            HashVersionadoV0(raw="v00$aGVsbG8=")

    def test_rejeita_separador_errado(self) -> None:
        # $ eh unico separador
        with pytest.raises(ValueError, match="formato invalido"):
            HashVersionadoV0(raw="v01:aGVsbG8=")

    def test_rejeita_base64_com_caracter_invalido(self) -> None:
        # ! nao eh base64 valido
        with pytest.raises(ValueError, match="formato invalido"):
            HashVersionadoV0(raw="v01$abc!def=")

    def test_aceita_base64_sem_padding(self) -> None:
        # Base64 sem padding eh valido (RFC 4648 §3.2)
        h = HashVersionadoV0(raw="v01$aGVsbG8")
        assert h.versao == 1


# =====================================================================
# IncertezaCombinada (T-CAL-030)
# =====================================================================


class TestIncertezaCombinada:
    def test_happy_tipo_a_e_b(self) -> None:
        u = IncertezaCombinada(
            valor=Decimal("0.012"),
            grau_liberdade_efetivo=42,
            tem_contribuicao_tipo_a=True,
            qtd_componentes_tipo_b=3,
        )
        assert u.valor == Decimal("0.012")
        assert u.grau_liberdade_efetivo == 42

    def test_happy_so_tipo_b(self) -> None:
        u = IncertezaCombinada(
            valor=Decimal("0.005"),
            grau_liberdade_efetivo=None,  # normal assumida
            tem_contribuicao_tipo_a=False,
            qtd_componentes_tipo_b=2,
        )
        assert u.tem_contribuicao_tipo_a is False
        assert u.qtd_componentes_tipo_b == 2

    def test_rejeita_valor_negativo(self) -> None:
        with pytest.raises(ValueError, match="valor < 0"):
            IncertezaCombinada(
                valor=Decimal("-0.01"),
                grau_liberdade_efetivo=10,
                tem_contribuicao_tipo_a=True,
                qtd_componentes_tipo_b=1,
            )

    def test_rejeita_valor_float(self) -> None:
        with pytest.raises(ValueError, match="deve ser Decimal"):
            IncertezaCombinada(
                valor=0.01,  # type: ignore[arg-type]
                grau_liberdade_efetivo=10,
                tem_contribuicao_tipo_a=True,
                qtd_componentes_tipo_b=1,
            )

    def test_rejeita_grau_liberdade_zero(self) -> None:
        with pytest.raises(ValueError, match="grau_liberdade_efetivo < 1"):
            IncertezaCombinada(
                valor=Decimal("0.01"),
                grau_liberdade_efetivo=0,
                tem_contribuicao_tipo_a=True,
                qtd_componentes_tipo_b=1,
            )

    def test_rejeita_qtd_tipo_b_negativa(self) -> None:
        with pytest.raises(ValueError, match="qtd_componentes_tipo_b < 0"):
            IncertezaCombinada(
                valor=Decimal("0.01"),
                grau_liberdade_efetivo=10,
                tem_contribuicao_tipo_a=True,
                qtd_componentes_tipo_b=-1,
            )

    def test_rejeita_zero_contribuicao(self) -> None:
        # GUM cl. 5.1.2 — u_c precisa de >=1 fonte declarada
        with pytest.raises(ValueError, match="GUM cl. 5.1.2"):
            IncertezaCombinada(
                valor=Decimal("0.01"),
                grau_liberdade_efetivo=None,
                tem_contribuicao_tipo_a=False,
                qtd_componentes_tipo_b=0,
            )
