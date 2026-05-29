"""Integracao PG-real do job P6 (T-PAD-050) — prova as queries ORM do loader.

Diferente do teste puro (`test_m5_padroes_jobs_p6.py`), este exercita
`_carregar_e_alertar`: insere um padrao via adapter Django dentro do contexto
de tenant (RLS ativa), grava um recal preso, e confirma que o loader
materializa os snapshots corretos (annotate Max VI + filtros de estado).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from src.application.metrologia.padroes.jobs.alertar_padroes_pendencias import (
    TipoAlertaPadrao,
)
from src.domain.metrologia.padroes.entities import (
    PadraoMetrologicoSnapshot,
    RecalExternoPadraoSnapshot,
)
from src.domain.metrologia.padroes.enums import (
    ClassePadrao,
    EstadoPadrao,
    StatusRecal,
    SubtipoPadrao,
    VinculacaoCadeia,
)
from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
)
from src.infrastructure.metrologia.padroes.management.commands.processar_jobs_padroes import (
    _carregar_e_alertar,
)
from src.infrastructure.metrologia.padroes.repositories import (
    DjangoPadraoRepository,
    DjangoRecalExternoRepository,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _snap_padrao(tenant_id, *, proximo_recal: date) -> PadraoMetrologicoSnapshot:
    return PadraoMetrologicoSnapshot(
        id=uuid4(),
        tenant_id=tenant_id,
        numero_serie=f"PAD-{uuid4().hex[:8]}",
        fabricante="Mettler",
        modelo="XPR",
        subtipo=SubtipoPadrao.PRINCIPAL,
        grandezas=(Grandeza.MASSA,),
        faixas=(FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),),
        incertezas_certificado=(
            IncertezaExpandida(
                Decimal("0.001"), Decimal("2"), Decimal("0.9545"), "g"
            ),
        ),
        vinculacao=VinculacaoCadeia.INMETRO,
        classe=ClassePadrao.E2,
        cert_externo_storage_key="key-x",
        validade_certificado_rastreabilidade=date(2099, 1, 1),
        proximo_recal=proximo_recal,
        intervalo_recal_meses=12,
        intervalo_vi_meses=3,
        criterio_intervalo="cl. 6.4.7 estabilidade",
        estado=EstadoPadrao.EM_USO,
        revision=1,
        rastreabilidade_origem_revogada=False,
        vigencia_inicio=datetime.now(UTC),
        correlation_id=uuid4(),
    )


@pytest.mark.django_db(transaction=True)
def test_loader_detecta_recal_vencendo_pg_real() -> None:
    tenant = TenantFactory(slug=f"pad-job-{uuid4().hex[:8]}")
    agora = datetime.now(UTC)
    proximo = (agora + timedelta(days=10)).date()  # dentro da janela 30d

    with run_in_tenant_context(tenant.id):
        DjangoPadraoRepository().salvar_novo(_snap_padrao(tenant.id, proximo_recal=proximo))
        alertas = _carregar_e_alertar(tenant.id, agora)

    tipos = [a.tipo for a in alertas]
    assert TipoAlertaPadrao.RECAL_VENCENDO in tipos
    recal_vencendo = next(
        a for a in alertas if a.tipo == TipoAlertaPadrao.RECAL_VENCENDO
    )
    assert recal_vencendo.severidade == "P2_ALERTA"
    assert recal_vencendo.tenant_id == tenant.id


@pytest.mark.django_db(transaction=True)
def test_loader_detecta_recal_preso_pg_real() -> None:
    tenant = TenantFactory(slug=f"pad-job-{uuid4().hex[:8]}")
    agora = datetime.now(UTC)

    with run_in_tenant_context(tenant.id):
        padrao = _snap_padrao(
            tenant.id, proximo_recal=(agora + timedelta(days=365)).date()
        )
        DjangoPadraoRepository().salvar_novo(padrao)
        recal = RecalExternoPadraoSnapshot(
            id=uuid4(),
            tenant_id=tenant.id,
            padrao_id=padrao.id,
            enviado_em=agora - timedelta(days=120),  # > 90d
            lab_externo="Lab RBC",
            responsavel_envio_id_hash="v1$h",
            status=StatusRecal.ENVIADO,
        )
        DjangoRecalExternoRepository().salvar_novo(recal)
        alertas = _carregar_e_alertar(tenant.id, agora)

    presos = [a for a in alertas if a.tipo == TipoAlertaPadrao.RECAL_RETORNO_ATRASADO]
    assert len(presos) == 1
    assert presos[0].severidade == "P1_RECAL_PRESO"
    assert presos[0].referencia_id == recal.id


@pytest.mark.django_db(transaction=True)
def test_loader_sem_pendencia_nao_alerta_pg_real() -> None:
    tenant = TenantFactory(slug=f"pad-job-{uuid4().hex[:8]}")
    agora = datetime.now(UTC)
    with run_in_tenant_context(tenant.id):
        DjangoPadraoRepository().salvar_novo(
            _snap_padrao(tenant.id, proximo_recal=(agora + timedelta(days=300)).date())
        )
        alertas = _carregar_e_alertar(tenant.id, agora)
    # padrao recem-criado: proxima VI = agora + 3 meses (> 30d) -> nada
    assert alertas == []
