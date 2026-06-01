"""M8 Fatia 2b — read-adapters do query_service (T-CER-044) PG-real.

Cobre os adapters que alimentam a emissão a partir do estado persistido:
`listar_pontos_medidos` (média Decimal das repetições), `listar_orcamentos_por_ponto`
(conversão Model→Snapshot + ordenação + enums reconstruídos) e `cmc_para_adapter`
(fail-closed None sem escopo RBC vigente; conversão Grandeza→.value + date→datetime).
RLS: dados de outro tenant não vazam.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from src.domain.metrologia.calibracao.enums import LeiEscalonamento, MetodoTipoAPonto
from src.domain.metrologia.value_objects import Grandeza
from src.infrastructure.metrologia.certificados.query_service import (
    cmc_para_adapter,
    listar_orcamentos_por_ponto,
    listar_pontos_medidos,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.m8_pg_fixtures import (
    cenario_tenant_equipamento,
    criar_calibracao_aprovada,
    criar_leituras,
    criar_orcamento_incerteza,
    criar_ponto_orcamento,
)

_DATA = date(2026, 5, 31)


@pytest.mark.django_db(transaction=True)
def test_listar_pontos_medidos_media_decimal():
    tenant, equip = cenario_tenant_equipamento("qspm")
    cal = criar_calibracao_aprovada(tenant, equip)
    # ponto 100: média de (100.0, 101.0, 99.0) = 100.0 ; ponto 500: (500, 502, 501)=501
    criar_leituras(tenant, cal, ponto="100", valores=["100.0", "101.0", "99.0"])
    criar_leituras(tenant, cal, ponto="500", valores=["500.0", "502.0", "501.0"])
    with run_in_tenant_context(tenant.id):
        pontos = listar_pontos_medidos(tenant_id=tenant.id, calibracao_id=cal.id)
    assert [p.ponto_calibracao for p in pontos] == [Decimal("100"), Decimal("500")]  # ASC
    assert pontos[0].valor_reportado == Decimal("100.0")  # média exata Decimal
    assert pontos[1].valor_reportado == Decimal("501.0")
    assert pontos[0].unidade == "g"


@pytest.mark.django_db(transaction=True)
def test_listar_pontos_medidos_media_nao_inteira_preserva_decimal():
    tenant, equip = cenario_tenant_equipamento("qspd")
    cal = criar_calibracao_aprovada(tenant, equip)
    # média de (10, 11) = 10.5 — checa divisão Decimal (não float/Avg)
    criar_leituras(tenant, cal, ponto="10", valores=["10.0", "11.0"])
    with run_in_tenant_context(tenant.id):
        pontos = listar_pontos_medidos(tenant_id=tenant.id, calibracao_id=cal.id)
    assert pontos[0].valor_reportado == Decimal("10.5")


@pytest.mark.django_db(transaction=True)
def test_listar_orcamentos_por_ponto_converte_e_ordena():
    tenant, equip = cenario_tenant_equipamento("qsorc")
    cal = criar_calibracao_aprovada(tenant, equip)
    orc = criar_orcamento_incerteza(tenant, cal)
    # cria fora de ordem para provar o ORDER BY ASC do adapter
    criar_ponto_orcamento(tenant, orc, ponto="500", U="0.9")
    criar_ponto_orcamento(tenant, orc, ponto="100", U="0.8")
    with run_in_tenant_context(tenant.id):
        snaps = listar_orcamentos_por_ponto(tenant_id=tenant.id, calibracao_id=cal.id)
    assert [s.ponto_calibracao for s in snaps] == [Decimal("100"), Decimal("500")]  # ASC
    assert snaps[0].U_expandida_no_ponto == Decimal("0.8")
    assert snaps[1].U_expandida_no_ponto == Decimal("0.9")
    # enums reconstruídos a partir das strings persistidas
    assert snaps[0].metodo_tipo_a_ponto is MetodoTipoAPonto.SX_PROPRIO
    assert snaps[0].lei_escalonamento_aplicada is LeiEscalonamento.CONSTANTE
    assert snaps[0].u_combinada_no_ponto == Decimal("0.8") / Decimal("2")


@pytest.mark.django_db(transaction=True)
def test_orcamentos_por_ponto_isolamento_tenant():
    # RLS + filtro tenant explícito: orçamento de outro tenant não aparece.
    t1, e1 = cenario_tenant_equipamento("qsiso1")
    cal1 = criar_calibracao_aprovada(t1, e1)
    orc1 = criar_orcamento_incerteza(t1, cal1)
    criar_ponto_orcamento(t1, orc1, ponto="100", U="0.8")
    t2, e2 = cenario_tenant_equipamento("qsiso2")
    cal2 = criar_calibracao_aprovada(t2, e2)
    orc2 = criar_orcamento_incerteza(t2, cal2)
    criar_ponto_orcamento(t2, orc2, ponto="200", U="0.5")
    with run_in_tenant_context(t1.id):
        snaps = listar_orcamentos_por_ponto(tenant_id=t1.id, calibracao_id=cal1.id)
    assert [s.ponto_calibracao for s in snaps] == [Decimal("100")]  # só do t1


@pytest.mark.django_db(transaction=True)
def test_cmc_para_adapter_sem_escopo_retorna_none_fail_closed():
    # Sem escopo CMC confirmado vigente → None (bloqueia RBC). Exercita a conversão
    # Grandeza→.value + date→datetime sem estourar (fail-safe do QS de escopos).
    tenant, _ = cenario_tenant_equipamento("qscmc")
    with run_in_tenant_context(tenant.id):
        cmc = cmc_para_adapter(
            tenant_id=tenant.id, grandeza=Grandeza.MASSA, ponto=Decimal("100"), data=_DATA
        )
    assert cmc is None
