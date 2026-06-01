"""M8 Fatia 0 (T-CER-001..004) — reconciliação de cobertura ponto-a-ponto PURA.

Sem Django, sem PG (`--no-cov` roda fora do Docker). Exercita a composição das
peças já validadas (M6 `avaliar_u_cmc`/`u_igual_cmc_suspeita`, VO `FaixaMedicao`,
read-model `OrcamentoPorPontoSnapshot` ADR-0077) + precedência determinística +
partição rbc/não-rbc + fail-closed do lookup 1:1.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.domain.metrologia.calibracao.entities import OrcamentoPorPontoSnapshot
from src.domain.metrologia.calibracao.enums import (
    LeiEscalonamento,
    MetodoTipoAPonto,
)
from src.domain.metrologia.certificados.enums import ClassificacaoPonto
from src.domain.metrologia.certificados.erros import (
    OrcamentoPontoAmbiguoError,
    SemOrcamentoPontoError,
)
from src.domain.metrologia.certificados.portas import CmcParaPort
from src.domain.metrologia.certificados.reconciliacao import (
    PontoMedido,
    reconciliar_pontos,
)
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

_TENANT = uuid4()
_DATA = date(2026, 5, 31)
_FAIXA = FaixaMedicao(Decimal("0"), Decimal("1000"), "g")


def _orc(ponto: str, u: str, *, k: str = "2", nivel: str = "0.9545", nu: str = "60") -> OrcamentoPorPontoSnapshot:
    return OrcamentoPorPontoSnapshot(
        id=uuid4(),
        tenant_id=_TENANT,
        orcamento_incerteza_id=uuid4(),
        ponto_calibracao=Decimal(ponto),
        u_combinada_no_ponto=Decimal(u) / Decimal(k),
        U_expandida_no_ponto=Decimal(u),
        k_no_ponto=Decimal(k),
        nivel_confianca_no_ponto=Decimal(nivel),
        grau_liberdade_efetivo_no_ponto=Decimal(nu),
        replay_determinismo_hash_no_ponto="v01$abc",
        metodo_tipo_a_ponto=MetodoTipoAPonto.SX_PROPRIO,
        n_repeticoes_ponto=10,
        lei_escalonamento_aplicada=LeiEscalonamento.CONSTANTE,
    )


def _pm(ponto: str, valor: str, unidade: str = "g") -> PontoMedido:
    return PontoMedido(
        ponto_calibracao=Decimal(ponto), valor_reportado=Decimal(valor), unidade=unidade
    )


class _FakeCmc:
    """Fake de `CmcParaPort` (T-CER-004): mapa ponto→CMC; None ⇒ ponto fora do
    escopo RBC. Registra chamadas pra provar que pontos FORA_DECLARADA NÃO
    consultam CMC (precedência)."""

    def __init__(self, mapa: dict[Decimal, Decimal]) -> None:
        self.mapa = mapa
        self.chamadas: list[Decimal] = []

    def __call__(
        self, *, tenant_id: UUID, grandeza: Grandeza, ponto: Decimal, data: date
    ) -> Decimal | None:
        self.chamadas.append(ponto)
        return self.mapa.get(ponto)


def _reconciliar(pontos, orcamentos, cmc_para):
    return reconciliar_pontos(
        pontos_medidos=pontos,
        orcamentos_por_ponto=orcamentos,
        faixa_declarada=_FAIXA,
        grandeza=Grandeza.MASSA,
        cmc_para=cmc_para,
        data_emissao=_DATA,
        tenant_id=_TENANT,
    )


# --- T-CER-004: contrato da porta CmcParaPort ---------------------------------


def test_porta_cmc_para_e_runtime_checkable_protocol():
    fake = _FakeCmc({Decimal("100"): Decimal("0.5")})
    assert isinstance(fake, CmcParaPort)


# --- Classificação por precedência (T-CER-001) --------------------------------


def test_rbc_ok_ponto_dentro_u_maior_cmc():
    cmc = _FakeCmc({Decimal("100"): Decimal("0.5")})
    rec = _reconciliar([_pm("100", "100.2")], [_orc("100", "0.8")], cmc)
    (p,) = rec.pontos
    assert p.classificacao is ClassificacaoPonto.RBC_OK
    assert p.cmc_no_ponto == Decimal("0.5")
    assert p.incluido_no_certificado
    assert not p.u_igual_cmc_suspeita
    assert rec.pode_emitir_rbc


def test_u_menor_cmc_bloqueia_rbc():
    cmc = _FakeCmc({Decimal("100"): Decimal("0.9")})
    rec = _reconciliar([_pm("100", "100.2")], [_orc("100", "0.5")], cmc)
    (p,) = rec.pontos
    assert p.classificacao is ClassificacaoPonto.U_MENOR_CMC
    assert not p.incluido_no_certificado
    assert not rec.pode_emitir_rbc
    assert rec.pontos_nao_rbc == (p,)


def test_sem_cmc_perfil_a_ponto_fora_do_escopo_rbc():
    # contexto RBC (cmc_para fornecida) mas ponto sem CMC no mapa → SEM_CMC pendente.
    cmc = _FakeCmc({})
    rec = _reconciliar([_pm("100", "100.2")], [_orc("100", "0.8")], cmc)
    (p,) = rec.pontos
    assert p.classificacao is ClassificacaoPonto.SEM_CMC
    assert p.cmc_no_ponto is None
    assert not p.incluido_no_certificado  # perfil A: pendente decisão RT
    assert not rec.pode_emitir_rbc


def test_fora_declarada_furo_de_processo():
    cmc = _FakeCmc({Decimal("2000"): Decimal("0.5")})
    rec = _reconciliar([_pm("2000", "2000.1")], [_orc("2000", "0.8")], cmc)
    (p,) = rec.pontos
    assert p.classificacao is ClassificacaoPonto.FORA_DECLARADA
    assert not p.incluido_no_certificado


def test_unidade_divergente_fail_closed_fora_declarada():
    cmc = _FakeCmc({Decimal("100"): Decimal("0.5")})
    rec = _reconciliar([_pm("100", "100.2", unidade="kg")], [_orc("100", "0.8")], cmc)
    (p,) = rec.pontos
    assert p.classificacao is ClassificacaoPonto.FORA_DECLARADA


def test_precedencia_fora_declarada_nao_consulta_cmc():
    # Ponto fora da declarada NÃO chega a consultar CMC (precedência fixa).
    cmc = _FakeCmc({Decimal("2000"): Decimal("0.5")})
    rec = _reconciliar([_pm("2000", "2000.1")], [_orc("2000", "0.8")], cmc)
    assert rec.pontos[0].classificacao is ClassificacaoPonto.FORA_DECLARADA
    assert cmc.chamadas == []  # nunca consultou — fora da declarada vence


# --- NC-06: flag u_igual_cmc_suspeita -----------------------------------------


def test_u_igual_cmc_seta_flag_suspeita_mas_nao_bloqueia():
    cmc = _FakeCmc({Decimal("100"): Decimal("0.8")})
    rec = _reconciliar([_pm("100", "100.2")], [_orc("100", "0.8")], cmc)
    (p,) = rec.pontos
    assert p.classificacao is ClassificacaoPonto.RBC_OK  # U==CMC ainda atende (>=)
    assert p.u_igual_cmc_suspeita  # NC-06: sinaliza cópia cega de CMC
    assert rec.pode_emitir_rbc


# --- Contexto não-RBC (B/C/D) -------------------------------------------------


def test_nao_rbc_bcd_ponto_dentro_e_valido_sem_cmc():
    rec = _reconciliar([_pm("100", "100.2"), _pm("500", "500.0")], [_orc("100", "0.8"), _orc("500", "1.0")], None)
    assert all(p.classificacao is ClassificacaoPonto.SEM_CMC for p in rec.pontos)
    assert all(p.incluido_no_certificado for p in rec.pontos)
    assert not rec.pode_emitir_rbc  # B/C/D nunca emite RBC
    assert rec.pontos_rbc == ()
    assert rec.faixa_certificado_min == Decimal("100")
    assert rec.faixa_certificado_max == Decimal("500")


# --- Lookup 1:1 fail-closed (T-CER-002 / INV-CER-RECONCILIA-005) --------------


def test_orcamento_duplicado_no_ponto_fail_closed():
    cmc = _FakeCmc({Decimal("100"): Decimal("0.5")})
    with pytest.raises(OrcamentoPontoAmbiguoError) as exc:
        _reconciliar([_pm("100", "100.2")], [_orc("100", "0.8"), _orc("100", "0.9")], cmc)
    assert exc.value.reason == "ORCAMENTO_PONTO_AMBIGUO"


def test_ponto_sem_orcamento_fail_closed():
    cmc = _FakeCmc({Decimal("100"): Decimal("0.5")})
    with pytest.raises(SemOrcamentoPontoError) as exc:
        _reconciliar([_pm("100", "100.2")], [], cmc)
    assert exc.value.reason == "SEM_ORCAMENTO"


def test_sem_pontos_medidos_fail_closed():
    cmc = _FakeCmc({})
    with pytest.raises(SemOrcamentoPontoError):
        _reconciliar([], [], cmc)


# --- Partição + faixa + ordenação canônica ASC (INV-CER-RECONCILIA-003/004) ---


def test_particao_mix_rbc_e_problematico_e_ordenacao():
    cmc = _FakeCmc({
        Decimal("100"): Decimal("0.5"),  # RBC_OK
        Decimal("500"): Decimal("0.9"),  # U_MENOR_CMC (U=0.5)
        # 800 ausente → SEM_CMC
    })
    pontos = [_pm("500", "500.0"), _pm("100", "100.2"), _pm("800", "800.0")]
    orcs = [_orc("500", "0.5"), _orc("100", "0.8"), _orc("800", "1.0")]
    rec = _reconciliar(pontos, orcs, cmc)

    # ordenados ASC por ponto_calibracao (INV-CER-RECONCILIA-004)
    assert [p.ponto_calibracao for p in rec.pontos] == [Decimal("100"), Decimal("500"), Decimal("800")]
    assert len(rec.pontos_rbc) == 1
    assert rec.pontos_rbc[0].ponto_calibracao == Decimal("100")
    assert len(rec.pontos_nao_rbc) == 2
    assert not rec.pode_emitir_rbc  # há pontos problemáticos pendentes de RT
    # faixa = só o ponto válido (100); problemáticos não entram pré-RT
    assert rec.faixa_certificado_min == Decimal("100")
    assert rec.faixa_certificado_max == Decimal("100")


def test_todos_rbc_ok_faixa_envelope_dos_validos():
    cmc = _FakeCmc({Decimal("100"): Decimal("0.5"), Decimal("900"): Decimal("0.5")})
    rec = _reconciliar(
        [_pm("900", "900.0"), _pm("100", "100.0")],
        [_orc("900", "0.8"), _orc("100", "0.8")],
        cmc,
    )
    assert rec.pode_emitir_rbc
    assert rec.faixa_certificado_min == Decimal("100")
    assert rec.faixa_certificado_max == Decimal("900")
