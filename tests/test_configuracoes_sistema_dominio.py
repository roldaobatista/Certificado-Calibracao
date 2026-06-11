"""Testes puros do domínio `configuracoes-sistema` (Fatia 1a — T-CFG-016).

Sem banco. Cobre: regime de numeração por tipo (ADR-0080), formato do número,
INV-028 (não diminui), INV-037 (1 matriz), não-sobreposição de vigência, vigência
determinística, VO Aliquota.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.domain.configuracoes_sistema.entities import Filial, Imposto, SerieDocumento
from src.domain.configuracoes_sistema.enums import (
    RegimeNumeracao,
    TipoDocumento,
    TipoImposto,
)
from src.domain.configuracoes_sistema.erros import (
    MatrizInvalidaError,
    NumeroNuncaDiminuiError,
)
from src.domain.configuracoes_sistema.transicoes import (
    ha_sobreposicao_vigencia,
    imposto_vigente_em,
    proximo_formatado,
    regime_numeracao_do_tipo,
    validar_proximo_numero_nao_diminui,
    validar_uma_matriz,
)
from src.domain.configuracoes_sistema.value_objects import Aliquota
from src.domain.shared.value_objects import CNPJ, JanelaVigencia

_CNPJ_OK = "11444777000161"  # válido (DV ok)


def _filial(eh_matriz: bool, cnpj: str = _CNPJ_OK) -> Filial:
    return Filial(
        id=uuid4(), tenant_id=uuid4(), empresa_id=uuid4(),
        cnpj=CNPJ(cnpj), nome="F", eh_matriz=eh_matriz,
    )


def _imposto(
    tipo: TipoImposto, inicio: datetime, fim: datetime | None, filial_id=None, tenant_id=None
) -> Imposto:
    return Imposto(
        id=uuid4(), tenant_id=tenant_id or uuid4(), tipo=tipo, aliquota=Aliquota(Decimal("5")),
        vigencia=JanelaVigencia(inicio=inicio, fim=fim), filial_id=filial_id,
    )


# === regime de numeração por tipo (ADR-0080) ===

@pytest.mark.parametrize(
    "tipo,esperado",
    [
        (TipoDocumento.FATURA, RegimeNumeracao.GAP_LESS),
        (TipoDocumento.CERTIFICADO, RegimeNumeracao.GAP_LESS),
        (TipoDocumento.OS, RegimeNumeracao.BURACOS_ACEITOS),
        (TipoDocumento.ORCAMENTO, RegimeNumeracao.BURACOS_ACEITOS),
        (TipoDocumento.RECIBO, RegimeNumeracao.BURACOS_ACEITOS),
        (TipoDocumento.INTERNO, RegimeNumeracao.BURACOS_ACEITOS),
    ],
)
def test_regime_numeracao_por_tipo(tipo, esperado):
    assert regime_numeracao_do_tipo(tipo) == esperado


def test_formato_numero_com_ano_e_padding():
    serie = SerieDocumento(
        id=uuid4(), tenant_id=uuid4(), tipo=TipoDocumento.OS, prefixo="OS",
        proximo_numero=123, regime_numeracao=RegimeNumeracao.BURACOS_ACEITOS,
        formato="{prefixo}-{ano}-{seq}", padding=6, reset_anual=True,
    )
    assert proximo_formatado(serie, 123, ano=2026) == "OS-2026-000123"


# === INV-028 ===

def test_proximo_numero_nao_diminui():
    validar_proximo_numero_nao_diminui(10, 11)  # ok
    with pytest.raises(NumeroNuncaDiminuiError):
        validar_proximo_numero_nao_diminui(10, 9)


# === INV-037 (1 matriz) ===

def test_uma_matriz_ok():
    validar_uma_matriz([_filial(True), _filial(False, "11222333000181")])


def test_zero_filiais_valido():
    validar_uma_matriz([])


def test_duas_matrizes_falha():
    with pytest.raises(MatrizInvalidaError):
        validar_uma_matriz([_filial(True), _filial(True, "11222333000181")])


def test_nenhuma_matriz_com_filiais_falha():
    with pytest.raises(MatrizInvalidaError):
        validar_uma_matriz([_filial(False), _filial(False, "11222333000181")])


# === não-sobreposição de vigência ===

def test_vigencias_sobrepostas_detectadas():
    fid, tid = uuid4(), uuid4()
    a = _imposto(TipoImposto.ISS, datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 6, 1, tzinfo=UTC), fid, tid)
    b = _imposto(TipoImposto.ISS, datetime(2026, 3, 1, tzinfo=UTC), None, fid, tid)
    assert ha_sobreposicao_vigencia([a], b) is True


def test_vigencias_adjacentes_nao_sobrepoem():
    fid, tid = uuid4(), uuid4()
    a = _imposto(TipoImposto.ISS, datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 6, 1, tzinfo=UTC), fid, tid)
    b = _imposto(TipoImposto.ISS, datetime(2026, 6, 1, tzinfo=UTC), None, fid, tid)
    assert ha_sobreposicao_vigencia([a], b) is False


def test_vigencia_deterministica():
    a = _imposto(TipoImposto.ISS, datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 6, 1, tzinfo=UTC))
    b = _imposto(TipoImposto.ISS, datetime(2026, 6, 1, tzinfo=UTC), None)
    vig = imposto_vigente_em([a, b], TipoImposto.ISS, None, datetime(2026, 8, 1, tzinfo=UTC))
    assert vig is b
    vig2 = imposto_vigente_em([a, b], TipoImposto.ISS, None, datetime(2026, 3, 1, tzinfo=UTC))
    assert vig2 is a


# === VO Aliquota ===

def test_aliquota_fracao():
    assert Aliquota(Decimal("18.5")).fracao() == Decimal("0.185")


def test_aliquota_fora_de_faixa():
    with pytest.raises(ValueError):
        Aliquota(Decimal("150"))


# === use case editar_filial (conserto M6 da auditoria P9) — Fakes, sem banco ===


class _FakeEmpresaRepo:
    """Fake do EmpresaRepository (TST-005) — registra a ORDEM dos salvar_filial
    (a troca atômica DEVE desmarcar a ex-matriz antes de salvar a nova)."""

    def __init__(self, empresa, filiais):
        self._empresa = empresa
        self._filiais = {f.id: f for f in filiais}
        self.salvas_em_ordem = []

    def obter(self, *, tenant_id):
        return self._empresa

    def salvar(self, empresa):
        self._empresa = empresa

    def listar_filiais(self, *, tenant_id, empresa_id):
        return list(self._filiais.values())

    def salvar_filial(self, filial):
        self._filiais[filial.id] = filial
        self.salvas_em_ordem.append(filial)


def _cenario_editar(matriz=True):
    from src.domain.configuracoes_sistema.entities import Empresa
    from src.domain.configuracoes_sistema.enums import RegimeTributario

    tenant_id, empresa_id = uuid4(), uuid4()
    empresa = Empresa(
        id=empresa_id, tenant_id=tenant_id, razao_social="E", cnpj=CNPJ(_CNPJ_OK),
        regime_tributario=RegimeTributario.SIMPLES_NACIONAL,
    )
    f_matriz = Filial(
        id=uuid4(), tenant_id=tenant_id, empresa_id=empresa_id,
        cnpj=CNPJ("11222333000181"), nome="Matriz", eh_matriz=matriz,
    )
    f_comum = Filial(
        id=uuid4(), tenant_id=tenant_id, empresa_id=empresa_id,
        cnpj=CNPJ("34238864000168"), nome="Comum", eh_matriz=False,
    )
    return tenant_id, empresa, f_matriz, f_comum


def test_editar_filial_muda_nome_preserva_matriz():
    from src.application.configuracoes_sistema.empresa import EditarFilialInput, editar_filial

    tenant_id, empresa, f_matriz, f_comum = _cenario_editar()
    repo = _FakeEmpresaRepo(empresa, [f_matriz, f_comum])
    out = editar_filial(
        EditarFilialInput(
            tenant_id=tenant_id, filial_id=f_comum.id, cnpj=f_comum.cnpj.value,
            nome="Comum Renomeada", eh_matriz=False,
        ),
        repo=repo,
    )
    assert out.filial.nome == "Comum Renomeada"
    assert out.ex_matriz is None
    assert out.antes.nome == "Comum"


def test_editar_filial_troca_atomica_de_matriz_desmarca_anterior_primeiro():
    from src.application.configuracoes_sistema.empresa import EditarFilialInput, editar_filial

    tenant_id, empresa, f_matriz, f_comum = _cenario_editar()
    repo = _FakeEmpresaRepo(empresa, [f_matriz, f_comum])
    out = editar_filial(
        EditarFilialInput(
            tenant_id=tenant_id, filial_id=f_comum.id, cnpj=f_comum.cnpj.value,
            nome="Comum", eh_matriz=True,
        ),
        repo=repo,
    )
    assert out.filial.eh_matriz is True
    assert out.ex_matriz is not None and out.ex_matriz.id == f_matriz.id
    assert out.ex_matriz.eh_matriz is False
    # Ordem: desmarca a ex-matriz ANTES (UNIQUE parcial não-deferrable).
    assert [f.id for f in repo.salvas_em_ordem] == [f_matriz.id, f_comum.id]
    matrizes = [f for f in repo.listar_filiais(tenant_id=tenant_id, empresa_id=empresa.id) if f.eh_matriz]
    assert len(matrizes) == 1 and matrizes[0].id == f_comum.id


def test_editar_filial_desmarcar_unica_matriz_falha():
    from src.application.configuracoes_sistema.empresa import EditarFilialInput, editar_filial

    tenant_id, empresa, f_matriz, f_comum = _cenario_editar()
    repo = _FakeEmpresaRepo(empresa, [f_matriz, f_comum])
    with pytest.raises(MatrizInvalidaError):
        editar_filial(
            EditarFilialInput(
                tenant_id=tenant_id, filial_id=f_matriz.id, cnpj=f_matriz.cnpj.value,
                nome="Matriz", eh_matriz=False,
            ),
            repo=repo,
        )
    assert repo.salvas_em_ordem == []  # nada persiste quando INV-037 falha


def test_editar_filial_inexistente_falha():
    from src.application.configuracoes_sistema.empresa import (
        EditarFilialInput,
        FilialAusenteError,
        editar_filial,
    )

    tenant_id, empresa, f_matriz, f_comum = _cenario_editar()
    repo = _FakeEmpresaRepo(empresa, [f_matriz, f_comum])
    with pytest.raises(FilialAusenteError):
        editar_filial(
            EditarFilialInput(
                tenant_id=tenant_id, filial_id=uuid4(), cnpj=_CNPJ_OK,
                nome="X", eh_matriz=False,
            ),
            repo=repo,
        )


def test_editar_filial_matriz_continua_matriz_sem_ex_matriz():
    from src.application.configuracoes_sistema.empresa import EditarFilialInput, editar_filial

    tenant_id, empresa, f_matriz, f_comum = _cenario_editar()
    repo = _FakeEmpresaRepo(empresa, [f_matriz, f_comum])
    out = editar_filial(
        EditarFilialInput(
            tenant_id=tenant_id, filial_id=f_matriz.id, cnpj=f_matriz.cnpj.value,
            nome="Matriz Renomeada", eh_matriz=True,
        ),
        repo=repo,
    )
    assert out.ex_matriz is None  # já era a matriz — não há troca
    assert out.filial.eh_matriz is True
