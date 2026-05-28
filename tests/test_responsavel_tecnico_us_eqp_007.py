"""US-EQP-007 — Gestão do Responsável Técnico do tenant (P-EQP-R10 BLOQUEANTE).

Cobre:
- AC-EQP-007-1: cadastro de RT happy + payload completo.
- AC-EQP-007-2 (INV-EQP-RT-001): EXCLUDE GIST rejeita sobreposicao
  temporal por (tenant, grandeza) -> 409.
- AC-EQP-007-3: declarar competencia + predicate
  `decisor_tem_competencia_para_atividade`.
- AC-EQP-007-4: trocar RT dispara `tenant.rt.trocado` no bus_outbox.
- AC-EQP-007-5: trigger PG bloqueia UPDATE em campos imutaveis pos-INSERT.
- Cross-tenant: tenant A nao enxerga RT de tenant B.
- Authz: perfil sem `responsavel_tecnico.gerenciar` toma 403 em POST.
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from django.db import DatabaseError, connection
from rest_framework.test import APIClient
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.responsavel_tecnico.models import (
    ResponsavelTecnicoTenant,
)
from src.infrastructure.responsavel_tecnico.predicates import (
    decisor_tem_competencia_para_atividade,
)
from src.infrastructure.responsavel_tecnico.services_rt import (
    CompetenciaSobreposta,
    DadosCadastroRT,
    DadosCompetencia,
    cadastrar_rt,
    declarar_competencia,
    trocar_rt,
)

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory


def _autenticar(client: APIClient, usuario, tenant, com_mfa: bool = True) -> None:
    if com_mfa:
        from django_otp import DEVICE_ID_SESSION_KEY
        from django_otp.plugins.otp_totp.models import TOTPDevice

        device, _ = TOTPDevice.objects.get_or_create(
            user=usuario, name="default", defaults={"confirmed": True}
        )
        if not device.confirmed:
            device.confirmed = True
            device.save()
        client.force_login(usuario)
        session = client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
    else:
        client.force_login(usuario)
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


@pytest.fixture
def cenario(db):
    suffix = uuid4().hex[:6]
    tenant_a = TenantFactory(slug=f"rt-a-{suffix}", nome_fantasia="Lab Calib RT A")
    tenant_b = TenantFactory(slug=f"rt-b-{suffix}", nome_fantasia="Lab Calib RT B")
    admin_a = UsuarioFactory(email=f"adm-a-{suffix}@rt.local")
    admin_b = UsuarioFactory(email=f"adm-b-{suffix}@rt.local")
    rt_user_a = UsuarioFactory(email=f"rt-a-{suffix}@rt.local")
    rt_user_b = UsuarioFactory(email=f"rt-b-{suffix}@rt.local")
    tecnico_a = UsuarioFactory(email=f"tec-a-{suffix}@rt.local")
    UsuarioPerfilTenantFactory(usuario=admin_a, tenant=tenant_a, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=admin_b, tenant=tenant_b, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=tecnico_a, tenant=tenant_a, perfil="tecnico")
    for u, t in [
        (admin_a, tenant_a),
        (admin_b, tenant_b),
        (tecnico_a, tenant_a),
    ]:
        invalidate_user_cache(u.id, t.id)
    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "admin_a": admin_a,
        "admin_b": admin_b,
        "tecnico_a": tecnico_a,
        "rt_user_a": rt_user_a,
        "rt_user_b": rt_user_b,
    }


def _dados_cadastro_basico(usuario_rt_id, inicio=None):
    return DadosCadastroRT(
        nome_completo="João da Silva Engenheiro",
        cpf="12345678901",
        formacao_academica="Engenharia Mecanica - UFMG - 2010",
        registro_profissional_tipo="CREA",
        registro_profissional_numero="CREA-MG 123.456/D",
        data_inicio_vigencia=inicio or date(2026, 1, 1),
    )


@pytest.mark.django_db(transaction=True)
class TestCadastroHappy:
    def test_admin_cadastra_rt_201(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["admin_a"], cenario["tenant_a"])
        payload = {
            "usuario_rt_id": str(cenario["rt_user_a"].id),
            "nome_completo": "João da Silva",
            "cpf": "12345678901",
            "formacao_academica": "Engenharia Mecanica - UFMG - 2010",
            "registro_profissional_tipo": "CREA",
            "registro_profissional_numero": "CREA-MG 123.456/D",
            "data_inicio_vigencia": "2026-01-01",
        }
        resp = client.post("/api/v1/responsaveis-tecnicos/", payload, format="json")
        assert resp.status_code == 201, resp.content
        body = resp.json()
        assert body["registro_profissional_tipo"] == "CREA"
        assert body["vigente"] is True
        assert "cpf_hash" not in body  # cpf hash NUNCA exposto
        # Persistencia: RT criado + evento na cadeia
        with run_in_tenant_context(cenario["tenant_a"].id):
            assert ResponsavelTecnicoTenant.objects.filter(id=body["id"]).exists()
            assert Auditoria.objects.filter(action="tenant.rt.cadastrado").exists()


@pytest.mark.django_db(transaction=True)
class TestCompetenciaSemSobreposicao:
    def test_competencia_sobreposta_409(self, cenario):
        with run_in_tenant_context(cenario["tenant_a"].id, cenario["admin_a"].id):
            rt = cadastrar_rt(
                tenant_id=cenario["tenant_a"].id,
                usuario_rt_id=cenario["rt_user_a"].id,
                criado_por_id=cenario["admin_a"].id,
                dados=_dados_cadastro_basico(cenario["rt_user_a"].id),
            )
            declarar_competencia(
                rt=rt,
                criado_por_id=cenario["admin_a"].id,
                dados=DadosCompetencia(
                    grandeza="massa",
                    declarado_em=date(2026, 1, 1),
                    vigente_ate=date(2026, 12, 31),
                ),
            )
            # Segunda declaracao sobrepoe a janela 2026-01-01..2026-12-31
            with pytest.raises(CompetenciaSobreposta):
                declarar_competencia(
                    rt=rt,
                    criado_por_id=cenario["admin_a"].id,
                    dados=DadosCompetencia(
                        grandeza="massa",
                        declarado_em=date(2026, 6, 1),
                        vigente_ate=date(2026, 10, 1),
                    ),
                )

    def test_competencia_consecutiva_aceita(self, cenario):
        """Janela `[)` permite encostar: ate=2026-12-31 e proximo de=2026-12-31 colidem;
        de=2027-01-01 NAO colide."""
        with run_in_tenant_context(cenario["tenant_a"].id, cenario["admin_a"].id):
            rt = cadastrar_rt(
                tenant_id=cenario["tenant_a"].id,
                usuario_rt_id=cenario["rt_user_a"].id,
                criado_por_id=cenario["admin_a"].id,
                dados=_dados_cadastro_basico(cenario["rt_user_a"].id),
            )
            declarar_competencia(
                rt=rt,
                criado_por_id=cenario["admin_a"].id,
                dados=DadosCompetencia(
                    grandeza="temperatura",
                    declarado_em=date(2026, 1, 1),
                    vigente_ate=date(2026, 12, 31),
                ),
            )
            # Janela seguinte separada por 1 dia — sem sobreposicao.
            c2 = declarar_competencia(
                rt=rt,
                criado_por_id=cenario["admin_a"].id,
                dados=DadosCompetencia(
                    grandeza="temperatura",
                    declarado_em=date(2027, 1, 1),
                    vigente_ate=date(2027, 12, 31),
                ),
            )
            assert c2.id is not None


@pytest.mark.django_db(transaction=True)
class TestPredicateCompetencia:
    def test_rt_vigente_com_competencia_passa(self, cenario):
        with run_in_tenant_context(cenario["tenant_a"].id, cenario["admin_a"].id):
            rt = cadastrar_rt(
                tenant_id=cenario["tenant_a"].id,
                usuario_rt_id=cenario["rt_user_a"].id,
                criado_por_id=cenario["admin_a"].id,
                dados=_dados_cadastro_basico(cenario["rt_user_a"].id),
            )
            declarar_competencia(
                rt=rt,
                criado_por_id=cenario["admin_a"].id,
                dados=DadosCompetencia(
                    grandeza="massa",
                    declarado_em=date(2026, 1, 1),
                ),
            )
            ok = decisor_tem_competencia_para_atividade(
                decisor_id=cenario["rt_user_a"].id,
                atividade="aprovar_versionamento",
                grandeza="massa",
                tenant_id=cenario["tenant_a"].id,
                hoje=date(2026, 5, 21),
            )
            assert ok is True

    def test_usuario_sem_rt_nao_passa(self, cenario):
        with run_in_tenant_context(cenario["tenant_a"].id, cenario["admin_a"].id):
            ok = decisor_tem_competencia_para_atividade(
                decisor_id=cenario["tecnico_a"].id,  # nao e RT
                atividade="x",
                grandeza="massa",
                tenant_id=cenario["tenant_a"].id,
            )
            assert ok is False

    def test_grandeza_diferente_nao_passa(self, cenario):
        with run_in_tenant_context(cenario["tenant_a"].id, cenario["admin_a"].id):
            rt = cadastrar_rt(
                tenant_id=cenario["tenant_a"].id,
                usuario_rt_id=cenario["rt_user_a"].id,
                criado_por_id=cenario["admin_a"].id,
                dados=_dados_cadastro_basico(cenario["rt_user_a"].id),
            )
            declarar_competencia(
                rt=rt,
                criado_por_id=cenario["admin_a"].id,
                dados=DadosCompetencia(grandeza="massa", declarado_em=date(2026, 1, 1)),
            )
            ok = decisor_tem_competencia_para_atividade(
                decisor_id=cenario["rt_user_a"].id,
                atividade="x",
                grandeza="temperatura",
                tenant_id=cenario["tenant_a"].id,
            )
            assert ok is False


@pytest.mark.django_db(transaction=True)
class TestTrocaRTPublicaEvento:
    def test_trocar_rt_dispara_evento_agregador(self, cenario):
        with run_in_tenant_context(cenario["tenant_a"].id, cenario["admin_a"].id):
            atual = cadastrar_rt(
                tenant_id=cenario["tenant_a"].id,
                usuario_rt_id=cenario["rt_user_a"].id,
                criado_por_id=cenario["admin_a"].id,
                dados=_dados_cadastro_basico(cenario["rt_user_a"].id),
            )
            _, novo = trocar_rt(
                rt_atual=atual,
                usuario_novo_rt_id=cenario["rt_user_b"].id,
                operador_id=cenario["admin_a"].id,
                dados_novo_rt=DadosCadastroRT(
                    nome_completo="Maria Substituta",
                    cpf="98765432100",
                    formacao_academica="Quimica - UFMG - 2015",
                    registro_profissional_tipo="CRQ",
                    registro_profissional_numero="CRQ-MG 999/V",
                    data_inicio_vigencia=date(2027, 1, 1),
                ),
            )
            atual.refresh_from_db()
            assert atual.encerrado_em is not None
            assert atual.motivo_encerramento == "substituicao"
            assert novo.vigente is True
            # 3 eventos: encerrado, cadastrado, trocado
            acoes = set(
                Auditoria.objects.filter(
                    action__startswith="tenant.rt."
                ).values_list("action", flat=True)
            )
            assert {
                "tenant.rt.encerrado",
                "tenant.rt.cadastrado",
                "tenant.rt.trocado",
            }.issubset(acoes)


@pytest.mark.django_db(transaction=True)
class TestTriggerImutabilidade:
    def test_update_em_campo_imutavel_levanta(self, cenario):
        with run_in_tenant_context(cenario["tenant_a"].id, cenario["admin_a"].id):
            rt = cadastrar_rt(
                tenant_id=cenario["tenant_a"].id,
                usuario_rt_id=cenario["rt_user_a"].id,
                criado_por_id=cenario["admin_a"].id,
                dados=_dados_cadastro_basico(cenario["rt_user_a"].id),
            )
        # Tenta forcar UPDATE em nome_completo_snapshot via raw SQL.
        # Trigger PG levanta `ProgrammingError` (RAISE EXCEPTION em plpgsql),
        # nao `IntegrityError`. `DatabaseError` cobre ambos no Django.
        with run_in_tenant_context(cenario["tenant_a"].id):
            with pytest.raises(DatabaseError) as exc:
                with connection.cursor() as cur:
                    cur.execute(
                        "UPDATE responsavel_tecnico_tenant "
                        "SET nome_completo_snapshot = 'X' WHERE id = %s",
                        [str(rt.id)],
                    )
            assert "imutavel" in str(exc.value).lower()


@pytest.mark.django_db(transaction=True)
class TestCrossTenant:
    def test_tenant_b_nao_ve_rt_de_a(self, cenario):
        with run_in_tenant_context(cenario["tenant_a"].id, cenario["admin_a"].id):
            cadastrar_rt(
                tenant_id=cenario["tenant_a"].id,
                usuario_rt_id=cenario["rt_user_a"].id,
                criado_por_id=cenario["admin_a"].id,
                dados=_dados_cadastro_basico(cenario["rt_user_a"].id),
            )
        client = APIClient()
        _autenticar(client, cenario["admin_b"], cenario["tenant_b"])
        resp = client.get("/api/v1/responsaveis-tecnicos/")
        assert resp.status_code == 200
        # F-C3: paginação global ativa — resposta vem no envelope DRF
        # {count, next, previous, results}. Lista de tenant B nao mostra RT de A.
        corpo = resp.json()
        assert corpo["count"] == 0
        assert corpo["results"] == []


@pytest.mark.django_db(transaction=True)
class TestAuthz:
    def test_tecnico_sem_gerenciar_toma_403_em_cadastro(self, cenario):
        client = APIClient()
        _autenticar(client, cenario["tecnico_a"], cenario["tenant_a"])
        payload = {
            "usuario_rt_id": str(cenario["rt_user_a"].id),
            "nome_completo": "X Y",
            "cpf": "11111111111",
            "formacao_academica": "X",
            "registro_profissional_tipo": "CREA",
            "registro_profissional_numero": "CREA-MG 1",
            "data_inicio_vigencia": "2026-01-01",
        }
        resp = client.post("/api/v1/responsaveis-tecnicos/", payload, format="json")
        assert resp.status_code == 403, resp.content
