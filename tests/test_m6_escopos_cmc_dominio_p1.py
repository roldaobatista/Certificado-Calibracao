"""Testes do domínio escopos-cmc — M6 Fatia 1a (T-ECMC-001/002/006).

Enums + entidade (cmc_em/vigente_em/consultavel) + máquina de estados + regras
puras (anti-fraude rbc_efetivo). Sem DB.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.domain.metrologia.escopos_cmc import transicoes
from src.domain.metrologia.escopos_cmc.entities import EscopoCMCSnapshot
from src.domain.metrologia.escopos_cmc.enums import (
    EstadoEscopo,
    FormaCMC,
    OrigemEscopo,
)
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

_DT0 = datetime(2026, 1, 1, tzinfo=UTC)
_DT1 = datetime(2026, 6, 1, tzinfo=UTC)
_DT2 = datetime(2026, 12, 1, tzinfo=UTC)


def _escopo(
    *,
    estado: EstadoEscopo = EstadoEscopo.CONFIRMADO,
    vigencia_inicio: datetime = _DT0,
    vigencia_fim: datetime | None = None,
    revogado_em: datetime | None = None,
    forma: FormaCMC = FormaCMC.ABSOLUTA,
    coef: str | None = None,
) -> EscopoCMCSnapshot:
    return EscopoCMCSnapshot(
        id=uuid4(),
        tenant_id=uuid4(),
        grandeza=Grandeza.MASSA,
        faixa=FaixaMedicao(Decimal("0"), Decimal("100"), "kg"),
        cmc_forma=forma,
        cmc_valor=Decimal("0.01"),
        cmc_unidade="kg",
        rbc_acreditado=True,
        versao=1,
        vigente_a_partir=vigencia_inicio,
        estado=estado,
        revision=0,
        vigencia_inicio=vigencia_inicio,
        correlation_id=uuid4(),
        cmc_coef_relativo=None if coef is None else Decimal(coef),
        vigencia_fim=vigencia_fim,
        revogado_em=revogado_em,
    )


class TestEstadoEscopo:
    def test_confirmado_consultavel(self) -> None:
        assert EstadoEscopo.CONFIRMADO.consultavel_para_cobertura

    def test_rascunho_nao_consultavel_mas_editavel(self) -> None:
        assert not EstadoEscopo.RASCUNHO_EXTRAIDO.consultavel_para_cobertura
        assert EstadoEscopo.RASCUNHO_EXTRAIDO.editavel

    def test_revogado_terminal_nao_consultavel(self) -> None:
        assert EstadoEscopo.REVOGADO.terminal
        assert not EstadoEscopo.REVOGADO.consultavel_para_cobertura

    def test_confirmado_nao_editavel(self) -> None:
        assert not EstadoEscopo.CONFIRMADO.editavel


class TestCMCEm:
    def test_absoluta(self) -> None:
        esc = _escopo()
        assert esc.cmc_em(Decimal("50")) == Decimal("0.01")

    def test_relativa(self) -> None:
        esc = _escopo(forma=FormaCMC.RELATIVA_LINEAR, coef="0.001")
        # 0.01 + 0.001·40 = 0.05
        assert esc.cmc_em(Decimal("40")) == Decimal("0.05")

    def test_relativa_sem_coef_levanta(self) -> None:
        esc = _escopo(forma=FormaCMC.RELATIVA_LINEAR, coef=None)
        with pytest.raises(ValueError, match="cmc_coef_relativo"):
            esc.cmc_em(Decimal("10"))

    def test_float_levanta(self) -> None:
        with pytest.raises(ValueError, match="Decimal"):
            _escopo().cmc_em(50.0)  # type: ignore[arg-type]


class TestVigenteEm:
    def test_dentro_da_janela_aberta(self) -> None:
        assert _escopo(vigencia_inicio=_DT0).vigente_em(_DT1)

    def test_antes_do_inicio_nao_vigente(self) -> None:
        assert not _escopo(vigencia_inicio=_DT1).vigente_em(_DT0)

    def test_apos_fim_nao_vigente(self) -> None:
        assert not _escopo(vigencia_inicio=_DT0, vigencia_fim=_DT1).vigente_em(_DT2)

    def test_revogado_nao_vigente_a_partir_da_revogacao(self) -> None:
        esc = _escopo(vigencia_inicio=_DT0, revogado_em=_DT1)
        assert esc.vigente_em(_DT0)  # antes da revogação
        assert not esc.vigente_em(_DT1)  # no instante da revogação
        assert not esc.vigente_em(_DT2)


class TestConsultavel:
    def test_confirmado_vigente_consultavel(self) -> None:
        assert _escopo(estado=EstadoEscopo.CONFIRMADO).consultavel(_DT1)

    def test_rascunho_vigente_nao_consultavel(self) -> None:
        # INV-ECMC-007: rascunho extraído nunca cobre
        assert not _escopo(estado=EstadoEscopo.RASCUNHO_EXTRAIDO).consultavel(_DT1)

    def test_confirmado_revogado_nao_consultavel(self) -> None:
        esc = _escopo(estado=EstadoEscopo.CONFIRMADO, revogado_em=_DT0)
        assert not esc.consultavel(_DT1)

    def test_origem_default_manual(self) -> None:
        assert _escopo().origem is OrigemEscopo.MANUAL


class TestTransicoes:
    def test_rascunho_para_confirmado_ok(self) -> None:
        assert transicoes.pode_transicionar(
            EstadoEscopo.RASCUNHO_EXTRAIDO, EstadoEscopo.CONFIRMADO
        )

    def test_rascunho_para_revogado_ok(self) -> None:
        assert transicoes.pode_transicionar(
            EstadoEscopo.RASCUNHO_EXTRAIDO, EstadoEscopo.REVOGADO
        )

    def test_confirmado_para_revogado_ok(self) -> None:
        assert transicoes.pode_transicionar(
            EstadoEscopo.CONFIRMADO, EstadoEscopo.REVOGADO
        )

    def test_confirmado_para_rascunho_proibido(self) -> None:
        # CONFIRMADO é WORM: não volta a rascunho (revisão = nova versão)
        assert not transicoes.pode_transicionar(
            EstadoEscopo.CONFIRMADO, EstadoEscopo.RASCUNHO_EXTRAIDO
        )

    def test_revogado_terminal(self) -> None:
        for destino in EstadoEscopo:
            assert not transicoes.pode_transicionar(EstadoEscopo.REVOGADO, destino)


class TestRegrasPerfil:
    def test_perfil_a_permite_rbc(self) -> None:
        assert transicoes.perfil_permite_rbc("A")
        assert transicoes.perfil_permite_rbc("a")  # normaliza

    def test_perfil_nao_a_nega_rbc(self) -> None:
        assert not transicoes.perfil_permite_rbc("B")
        assert not transicoes.perfil_permite_rbc("D")

    def test_rbc_efetivo_a_mantem(self) -> None:
        assert transicoes.rbc_efetivo(rbc_solicitado=True, perfil="A")

    def test_rbc_efetivo_nao_a_forca_false(self) -> None:
        # anti-fraude INV-ECMC-002 / FAIL L6: B/C/D nunca RBC, nem via payload
        assert not transicoes.rbc_efetivo(rbc_solicitado=True, perfil="B")
        assert not transicoes.rbc_efetivo(rbc_solicitado=True, perfil="D")

    def test_rbc_efetivo_false_continua_false(self) -> None:
        assert not transicoes.rbc_efetivo(rbc_solicitado=False, perfil="A")


class TestMotivoRevogacao:
    def test_curto_levanta(self) -> None:
        with pytest.raises(ValueError, match=">= 10"):
            transicoes.validar_motivo_revogacao("curto")

    def test_suficiente_ok(self) -> None:
        transicoes.validar_motivo_revogacao("revogado por supervisão CGCRE 2026")
