"""T-EQP-012 + T-EQP-016 (AC-EQP-002-1 / AC-EQP-002-5) — testes do modelo
`EquipamentoVersao`.

Cobre:
1. Cadastro happy em multi-tenant (RLS aplicado).
2. Enum `motivo_mudanca` cobre os 9 valores (P-EQP-R2).
3. INV-EQP-VERSAO-001 — `motivo_detalhe` anti-PII (CPF/CNPJ/email/nome).
4. `motivo_detalhe` >=100 chars quando motivo obriga aprovacao.
5. RLS cross-tenant — versao de outro tenant invisivel.
6. INSERT-only — UPDATE bloqueado em Python (T-EQP-013 cravara em PG).
7. CHECK A3 all-or-nothing (P-EQP-T5).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    MOTIVOS_QUE_OBRIGAM_APROVACAO,
    Equipamento,
    EquipamentoVersao,
    MotivoMudancaEquipamentoVersao,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory

JUSTIFICATIVA_OK_100 = (
    "Substituicao do componente principal apos auditoria interna do "
    "ciclo 2026; rastreabilidade preservada conforme procedimento."
)


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"eqp-ver-{sfx}")
    usuario = UsuarioFactory(email=f"ver-{sfx}@c.local")
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Versao",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag="VER-001",
            numero_serie="NS-VER-1",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D", "schema": "1.0.0"},
        )
    return {
        "tenant": tenant,
        "cliente": cliente,
        "equipamento": equipamento,
        "usuario": usuario,
    }


# ----------------------------------------------------------------------
# Happy path
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_cadastro_basico_versao_motivo_simples(cenario):
    """T-EQP-012 — versao criada com motivo `correcao_cadastral` (sem
    aprovacao obrigatoria); motivo_detalhe pode ficar vazio."""
    with run_in_tenant_context(cenario["tenant"].id):
        versao = EquipamentoVersao.objects.create(
            tenant=cenario["tenant"],
            equipamento=cenario["equipamento"],
            campo="modelo",
            valor_anterior_hash="hash_old_xxxxx",
            valor_novo_hash="hash_new_yyyyy",
            motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL,
            motivo_detalhe="",
            snapshot_jsonb={"modelo": "Prix 4 Plus"},
            criado_por=cenario["usuario"],
        )
    assert versao.id is not None
    assert versao.motivo_mudanca == "correcao_cadastral"


@pytest.mark.django_db(transaction=True)
def test_enum_motivo_mudanca_cobre_9_valores():
    """P-EQP-R2 — enum fechado com 9 valores."""
    assert len(MotivoMudancaEquipamentoVersao.choices) == 9
    valores = {v for v, _ in MotivoMudancaEquipamentoVersao.choices}
    assert valores == {
        "correcao_cadastral",
        "mudanca_local",
        "troca_acessorio",
        "recalibracao_diferente_faixa",
        "mudanca_classe_metrologica",
        "ajuste_pos_calibracao",
        "substituicao_componente_critico",
        "atualizacao_firmware",
        "outros",
    }


@pytest.mark.django_db(transaction=True)
def test_3_motivos_obrigam_aprovacao():
    """T-EQP-015 ancora — 3 motivos disparam fluxo gestor_qualidade."""
    assert MOTIVOS_QUE_OBRIGAM_APROVACAO == {
        "outros",
        "substituicao_componente_critico",
        "atualizacao_firmware",
    }


# ----------------------------------------------------------------------
# INV-EQP-VERSAO-001 — motivo_detalhe anti-PII
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_inv_eqp_versao_001_motivo_detalhe_rejeita_cpf(cenario):
    """INV-EQP-VERSAO-001 — CPF na justificativa bloqueia."""
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(ValidationError, match="PII direta"):
            EquipamentoVersao.objects.create(
                tenant=cenario["tenant"],
                equipamento=cenario["equipamento"],
                campo="modelo",
                valor_anterior_hash="a",
                valor_novo_hash="b",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.OUTROS,
                motivo_detalhe=(
                    "Mudanca solicitada pelo CPF 123.456.789-01 do cliente "
                    "apos avaliacao tecnica do equipamento; documentacao "
                    "anexa neste protocolo."
                ),
                criado_por=cenario["usuario"],
            )


@pytest.mark.django_db(transaction=True)
def test_inv_eqp_versao_001_motivo_detalhe_rejeita_email(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(ValidationError, match="PII direta"):
            EquipamentoVersao.objects.create(
                tenant=cenario["tenant"],
                equipamento=cenario["equipamento"],
                campo="modelo",
                valor_anterior_hash="a",
                valor_novo_hash="b",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.OUTROS,
                motivo_detalhe=(
                    "Solicitado via email cliente@empresa.com.br apos "
                    "validacao tecnica concluida; substituicao registrada "
                    "neste mesmo protocolo de servico."
                ),
                criado_por=cenario["usuario"],
            )


@pytest.mark.django_db(transaction=True)
def test_inv_eqp_versao_001_motivo_detalhe_rejeita_nome_proprio(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(ValidationError, match="PII direta"):
            EquipamentoVersao.objects.create(
                tenant=cenario["tenant"],
                equipamento=cenario["equipamento"],
                campo="modelo",
                valor_anterior_hash="a",
                valor_novo_hash="b",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.OUTROS,
                motivo_detalhe=(
                    "Solicitacao apresentada por Joao Silva Santos "
                    "(metrologista) apos vistoria; rastreabilidade do "
                    "componente preservada conforme procedimento interno."
                ),
                criado_por=cenario["usuario"],
            )


@pytest.mark.django_db(transaction=True)
def test_motivo_detalhe_obrigatorio_quando_outros(cenario):
    """AC-EQP-002-4 — motivo `outros` exige motivo_detalhe >=100 chars."""
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(ValidationError, match=">=100"):
            EquipamentoVersao.objects.create(
                tenant=cenario["tenant"],
                equipamento=cenario["equipamento"],
                campo="modelo",
                valor_anterior_hash="a",
                valor_novo_hash="b",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.OUTROS,
                motivo_detalhe="curto",
                criado_por=cenario["usuario"],
            )


@pytest.mark.django_db(transaction=True)
def test_motivo_detalhe_opcional_quando_nao_obriga(cenario):
    """Motivos como `correcao_cadastral` aceitam motivo_detalhe vazio."""
    with run_in_tenant_context(cenario["tenant"].id):
        v = EquipamentoVersao.objects.create(
            tenant=cenario["tenant"],
            equipamento=cenario["equipamento"],
            campo="modelo",
            valor_anterior_hash="a",
            valor_novo_hash="b",
            motivo_mudanca=MotivoMudancaEquipamentoVersao.MUDANCA_LOCAL,
            motivo_detalhe="",
            criado_por=cenario["usuario"],
        )
    assert v.motivo_detalhe == ""


# ----------------------------------------------------------------------
# RLS cross-tenant
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_rls_cross_tenant_versao_invisivel(cenario):
    """INV-TENANT-001 — versao de tenant_a invisivel ao tenant_b."""
    with run_in_tenant_context(cenario["tenant"].id):
        EquipamentoVersao.objects.create(
            tenant=cenario["tenant"],
            equipamento=cenario["equipamento"],
            campo="modelo",
            valor_anterior_hash="a",
            valor_novo_hash="b",
            motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL,
            criado_por=cenario["usuario"],
        )
    tenant_b = TenantFactory(slug=f"ver-b-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant_b.id):
        visiveis = EquipamentoVersao.objects.count()
    assert visiveis == 0


# ----------------------------------------------------------------------
# INSERT-only
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_insert_only_save_apos_persistido_levanta(cenario):
    """T-EQP-012 (T-EQP-013 grava em PG) — save() em instancia ja
    persistida deve levantar RuntimeError em Python."""
    with run_in_tenant_context(cenario["tenant"].id):
        v = EquipamentoVersao.objects.create(
            tenant=cenario["tenant"],
            equipamento=cenario["equipamento"],
            campo="modelo",
            valor_anterior_hash="a",
            valor_novo_hash="b",
            motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL,
            criado_por=cenario["usuario"],
        )
        v.campo = "faixa"
        with pytest.raises(RuntimeError, match="INSERT-only"):
            v.save()


@pytest.mark.django_db(transaction=True)
def test_insert_only_delete_levanta(cenario):
    """T-EQP-012 — delete() levanta RuntimeError em Python."""
    with run_in_tenant_context(cenario["tenant"].id):
        v = EquipamentoVersao.objects.create(
            tenant=cenario["tenant"],
            equipamento=cenario["equipamento"],
            campo="modelo",
            valor_anterior_hash="a",
            valor_novo_hash="b",
            motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL,
            criado_por=cenario["usuario"],
        )
        with pytest.raises(RuntimeError, match="INSERT-only"):
            v.delete()


# ----------------------------------------------------------------------
# CHECK A3 all-or-nothing (P-EQP-T5)
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_check_a3_so_referencia_sem_resto_falha(cenario):
    """P-EQP-T5 — preencher apenas `assinatura_a3_referencia` sem
    `assinada_em` + `certificado_emissor_hash` viola CHECK."""
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(IntegrityError, match="ck_eqp_versao_a3_all_or_nothing"):
            EquipamentoVersao.objects.create(
                tenant=cenario["tenant"],
                equipamento=cenario["equipamento"],
                campo="classe",
                valor_anterior_hash="a",
                valor_novo_hash="b",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.MUDANCA_CLASSE_METROLOGICA,
                criado_por=cenario["usuario"],
                assinatura_a3_referencia=uuid4(),
                # falta assinatura_a3_assinada_em + certificado_emissor_hash
            )


@pytest.mark.django_db(transaction=True)
def test_check_a3_referencia_null_sem_resto_ok(cenario):
    """P-EQP-T5 — A3 NULL inteiro e valido (motivos sem A3)."""
    with run_in_tenant_context(cenario["tenant"].id):
        v = EquipamentoVersao.objects.create(
            tenant=cenario["tenant"],
            equipamento=cenario["equipamento"],
            campo="modelo",
            valor_anterior_hash="a",
            valor_novo_hash="b",
            motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL,
            criado_por=cenario["usuario"],
        )
    assert v.assinatura_a3_referencia is None
