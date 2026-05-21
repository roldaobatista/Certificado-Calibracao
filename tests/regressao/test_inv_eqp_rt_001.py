"""Anti-regressao INV-EQP-RT-001 (T-EQP-094 — US-EQP-007 / P-EQP-R10).

Garante que o EXCLUDE GIST `rt_competencia_sem_sobreposicao_temporal`
bloqueia sobreposicao temporal por (tenant, grandeza) — happy + unhappy
+ cross-tenant (≥3 testes, padrao TST-004).
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.responsavel_tecnico.services_rt import (
    CompetenciaSobreposta,
    DadosCadastroRT,
    DadosCompetencia,
    cadastrar_rt,
    declarar_competencia,
)

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory


def _cadastra_rt_basico(tenant, admin, usuario_rt):
    return cadastrar_rt(
        tenant_id=tenant.id,
        usuario_rt_id=usuario_rt.id,
        criado_por_id=admin.id,
        dados=DadosCadastroRT(
            nome_completo="RT Reg Padrao",
            cpf="12345678901",
            formacao_academica="Eng - X",
            registro_profissional_tipo="CREA",
            registro_profissional_numero="CREA-MG 1",
            data_inicio_vigencia=date(2026, 1, 1),
        ),
    )


@pytest.mark.django_db(transaction=True)
class TestINVEqpRT001:
    def test_happy_competencia_aceita(self, db):
        sfx = uuid4().hex[:6]
        tenant = TenantFactory(slug=f"rt-h-{sfx}", nome_fantasia="Lab H")
        admin = UsuarioFactory(email=f"adm-h-{sfx}@x.local")
        user_rt = UsuarioFactory(email=f"rt-h-{sfx}@x.local")
        UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
        with run_in_tenant_context(tenant.id, admin.id):
            rt = _cadastra_rt_basico(tenant, admin, user_rt)
            comp = declarar_competencia(
                rt=rt,
                criado_por_id=admin.id,
                dados=DadosCompetencia(
                    grandeza="massa",
                    declarado_em=date(2026, 1, 1),
                    vigente_ate=date(2026, 12, 31),
                ),
            )
            assert comp.id is not None

    def test_unhappy_sobreposicao_levanta(self, db):
        sfx = uuid4().hex[:6]
        tenant = TenantFactory(slug=f"rt-u-{sfx}", nome_fantasia="Lab U")
        admin = UsuarioFactory(email=f"adm-u-{sfx}@x.local")
        user_rt = UsuarioFactory(email=f"rt-u-{sfx}@x.local")
        UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
        with run_in_tenant_context(tenant.id, admin.id):
            rt = _cadastra_rt_basico(tenant, admin, user_rt)
            declarar_competencia(
                rt=rt,
                criado_por_id=admin.id,
                dados=DadosCompetencia(
                    grandeza="massa",
                    declarado_em=date(2026, 1, 1),
                    vigente_ate=date(2026, 12, 31),
                ),
            )
            # Janela sobreposta:
            with pytest.raises(CompetenciaSobreposta):
                declarar_competencia(
                    rt=rt,
                    criado_por_id=admin.id,
                    dados=DadosCompetencia(
                        grandeza="massa",
                        declarado_em=date(2026, 6, 1),
                        vigente_ate=date(2027, 6, 1),
                    ),
                )

    def test_cross_tenant_mesma_grandeza_nao_colide(self, db):
        """Tenants distintos podem ter RTs competentes na mesma grandeza simultaneamente."""
        sfx = uuid4().hex[:6]
        tenant_a = TenantFactory(slug=f"rt-x-a-{sfx}", nome_fantasia="Lab XA")
        tenant_b = TenantFactory(slug=f"rt-x-b-{sfx}", nome_fantasia="Lab XB")
        admin_a = UsuarioFactory(email=f"adm-xa-{sfx}@x.local")
        admin_b = UsuarioFactory(email=f"adm-xb-{sfx}@x.local")
        user_rt_a = UsuarioFactory(email=f"rt-xa-{sfx}@x.local")
        user_rt_b = UsuarioFactory(email=f"rt-xb-{sfx}@x.local")
        UsuarioPerfilTenantFactory(usuario=admin_a, tenant=tenant_a, perfil="admin_tenant")
        UsuarioPerfilTenantFactory(usuario=admin_b, tenant=tenant_b, perfil="admin_tenant")

        with run_in_tenant_context(tenant_a.id, admin_a.id):
            rt_a = _cadastra_rt_basico(tenant_a, admin_a, user_rt_a)
            declarar_competencia(
                rt=rt_a,
                criado_por_id=admin_a.id,
                dados=DadosCompetencia(grandeza="massa", declarado_em=date(2026, 1, 1)),
            )
        # Mesmo periodo + mesma grandeza em tenant B: tem que aceitar
        with run_in_tenant_context(tenant_b.id, admin_b.id):
            rt_b = _cadastra_rt_basico(tenant_b, admin_b, user_rt_b)
            comp_b = declarar_competencia(
                rt=rt_b,
                criado_por_id=admin_b.id,
                dados=DadosCompetencia(grandeza="massa", declarado_em=date(2026, 1, 1)),
            )
            assert comp_b.id is not None
