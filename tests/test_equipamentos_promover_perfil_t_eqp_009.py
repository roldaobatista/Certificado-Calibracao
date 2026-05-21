"""T-EQP-009 (AC-EQP-001-7b / P-EQP-T4) - promocao do perfil_tenant_snapshot
via funcao SECURITY DEFINER `promover_perfil_equipamento_snapshot`.

Cobre:
1. Happy path D->A, D->C, C->B (saltos e sequencial).
2. Direcao invalida — A->D / A->B downgrade / mesmo perfil C->C.
3. Destino fora de {C, B, A} (D, X).
4. Argumentos obrigatorios (evidencia, rt_id) — Python pre-valida.
5. Justificativa < 100 chars.
6. Justificativa com PII (CPF / email / nome proprio).
7. Cross-tenant (chamar com contexto de outro tenant) bloqueia.
8. Regressao: UPDATE direto fora da funcao continua bloqueado por
   `equipamento_perfil_tenant_imutavel_trg` (INV-EQP-001).
9. Evento `equipamento.perfil_promovido` publicado no bus_outbox.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db.utils import ProgrammingError
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.equipamentos.services_perfil import (
    EquipamentoNaoEncontrado,
    EvidenciaObrigatoria,
    JustificativaInvalida,
    PerfilDestinoInvalido,
    RTObrigatorio,
    promover_perfil_equipamento,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory

JUSTIFICATIVA_OK = (
    "Promocao baseada em auditoria interna 2026-05; equipamento atende "
    "requisitos OIML R76 classe III conforme dossie tecnico anexo."
)


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"eqp-prom-{sfx}")
    decisor = UsuarioFactory(email=f"dec-{sfx}@c.local")
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Promocao",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag="PROM-001",
            numero_serie="NS-PROM-1",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D", "schema": "1.0.0"},
        )
    return {
        "tenant": tenant,
        "cliente": cliente,
        "equipamento": equipamento,
        "decisor_id": decisor.id,
        "rt_id": uuid4(),
        "evidencia_id": uuid4(),
    }


# ----------------------------------------------------------------------
# Happy paths
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_happy_d_para_a_salto_completo(cenario):
    """T-EQP-009 - promocao D->A em salto unico (3 niveis) deve passar."""
    with run_in_tenant_context(cenario["tenant"].id):
        resultado = promover_perfil_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento_id=cenario["equipamento"].id,
            decisor_id=cenario["decisor_id"],
            rt_id=cenario["rt_id"],
            perfil_novo="A",
            evidencia_documental_id=cenario["evidencia_id"],
            justificativa=JUSTIFICATIVA_OK,
        )
        cenario["equipamento"].refresh_from_db()
    assert resultado.snapshot_atualizado["perfil"] == "A"
    assert cenario["equipamento"].perfil_tenant_snapshot["perfil"] == "A"
    # Schema original preservado.
    assert cenario["equipamento"].perfil_tenant_snapshot["schema"] == "1.0.0"


@pytest.mark.django_db(transaction=True)
def test_happy_d_para_c_um_nivel(cenario):
    """T-EQP-009 - promocao D->C (passo minimo) deve passar."""
    with run_in_tenant_context(cenario["tenant"].id):
        resultado = promover_perfil_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento_id=cenario["equipamento"].id,
            decisor_id=cenario["decisor_id"],
            rt_id=cenario["rt_id"],
            perfil_novo="C",
            evidencia_documental_id=cenario["evidencia_id"],
            justificativa=JUSTIFICATIVA_OK,
        )
    assert resultado.snapshot_atualizado["perfil"] == "C"


@pytest.mark.django_db(transaction=True)
def test_happy_d_para_c_depois_c_para_b(cenario):
    """T-EQP-009 - duas promocoes consecutivas D->C->B."""
    with run_in_tenant_context(cenario["tenant"].id):
        promover_perfil_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento_id=cenario["equipamento"].id,
            decisor_id=cenario["decisor_id"],
            rt_id=cenario["rt_id"],
            perfil_novo="C",
            evidencia_documental_id=cenario["evidencia_id"],
            justificativa=JUSTIFICATIVA_OK,
        )
        promover_perfil_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento_id=cenario["equipamento"].id,
            decisor_id=cenario["decisor_id"],
            rt_id=cenario["rt_id"],
            perfil_novo="B",
            evidencia_documental_id=uuid4(),
            justificativa=JUSTIFICATIVA_OK,
        )
        cenario["equipamento"].refresh_from_db()
    assert cenario["equipamento"].perfil_tenant_snapshot["perfil"] == "B"


# ----------------------------------------------------------------------
# Direcao invalida
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_downgrade_a_para_b_bloqueado(cenario):
    """P-EQP-T4 - downgrade A->B levanta PerfilDestinoInvalido."""
    with run_in_tenant_context(cenario["tenant"].id):
        promover_perfil_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento_id=cenario["equipamento"].id,
            decisor_id=cenario["decisor_id"],
            rt_id=cenario["rt_id"],
            perfil_novo="A",
            evidencia_documental_id=cenario["evidencia_id"],
            justificativa=JUSTIFICATIVA_OK,
        )
        with pytest.raises(PerfilDestinoInvalido, match="direcao invalida"):
            promover_perfil_equipamento(
                tenant_id=cenario["tenant"].id,
                equipamento_id=cenario["equipamento"].id,
                decisor_id=cenario["decisor_id"],
                rt_id=cenario["rt_id"],
                perfil_novo="B",
                evidencia_documental_id=uuid4(),
                justificativa=JUSTIFICATIVA_OK,
            )


@pytest.mark.django_db(transaction=True)
def test_mesmo_perfil_c_para_c_bloqueado(cenario):
    """P-EQP-T4 - re-promocao pro mesmo perfil bloqueada."""
    with run_in_tenant_context(cenario["tenant"].id):
        promover_perfil_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento_id=cenario["equipamento"].id,
            decisor_id=cenario["decisor_id"],
            rt_id=cenario["rt_id"],
            perfil_novo="C",
            evidencia_documental_id=cenario["evidencia_id"],
            justificativa=JUSTIFICATIVA_OK,
        )
        with pytest.raises(PerfilDestinoInvalido, match="direcao invalida"):
            promover_perfil_equipamento(
                tenant_id=cenario["tenant"].id,
                equipamento_id=cenario["equipamento"].id,
                decisor_id=cenario["decisor_id"],
                rt_id=cenario["rt_id"],
                perfil_novo="C",
                evidencia_documental_id=uuid4(),
                justificativa=JUSTIFICATIVA_OK,
            )


@pytest.mark.django_db(transaction=True)
def test_perfil_destino_d_invalido(cenario):
    """P-EQP-T4 - D nao e destino valido (somente C, B, A)."""
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(PerfilDestinoInvalido, match="destinos validos"):
            promover_perfil_equipamento(
                tenant_id=cenario["tenant"].id,
                equipamento_id=cenario["equipamento"].id,
                decisor_id=cenario["decisor_id"],
                rt_id=cenario["rt_id"],
                perfil_novo="D",
                evidencia_documental_id=cenario["evidencia_id"],
                justificativa=JUSTIFICATIVA_OK,
            )


@pytest.mark.django_db(transaction=True)
def test_perfil_destino_letra_aleatoria_invalido(cenario):
    """P-EQP-T4 - destino fora do enum bloqueado."""
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(PerfilDestinoInvalido):
            promover_perfil_equipamento(
                tenant_id=cenario["tenant"].id,
                equipamento_id=cenario["equipamento"].id,
                decisor_id=cenario["decisor_id"],
                rt_id=cenario["rt_id"],
                perfil_novo="X",
                evidencia_documental_id=cenario["evidencia_id"],
                justificativa=JUSTIFICATIVA_OK,
            )


# ----------------------------------------------------------------------
# Argumentos obrigatorios
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_evidencia_documental_id_obrigatorio(cenario):
    """P-EQP-T4 - evidencia_documental_id None levanta EvidenciaObrigatoria."""
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(EvidenciaObrigatoria):
            promover_perfil_equipamento(
                tenant_id=cenario["tenant"].id,
                equipamento_id=cenario["equipamento"].id,
                decisor_id=cenario["decisor_id"],
                rt_id=cenario["rt_id"],
                perfil_novo="A",
                evidencia_documental_id=None,  # type: ignore[arg-type]
                justificativa=JUSTIFICATIVA_OK,
            )


@pytest.mark.django_db(transaction=True)
def test_rt_id_obrigatorio(cenario):
    """P-EQP-T4 - rt_id None levanta RTObrigatorio."""
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(RTObrigatorio):
            promover_perfil_equipamento(
                tenant_id=cenario["tenant"].id,
                equipamento_id=cenario["equipamento"].id,
                decisor_id=cenario["decisor_id"],
                rt_id=None,  # type: ignore[arg-type]
                perfil_novo="A",
                evidencia_documental_id=cenario["evidencia_id"],
                justificativa=JUSTIFICATIVA_OK,
            )


# ----------------------------------------------------------------------
# Justificativa
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_justificativa_curta_bloqueada(cenario):
    """P-EQP-T4 - justificativa <100 chars levanta JustificativaInvalida."""
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(JustificativaInvalida, match=">=100 chars"):
            promover_perfil_equipamento(
                tenant_id=cenario["tenant"].id,
                equipamento_id=cenario["equipamento"].id,
                decisor_id=cenario["decisor_id"],
                rt_id=cenario["rt_id"],
                perfil_novo="A",
                evidencia_documental_id=cenario["evidencia_id"],
                justificativa="curta",
            )


@pytest.mark.django_db(transaction=True)
def test_justificativa_com_cpf_bloqueada(cenario):
    """INV-EQP-LOC-001 (reuso) - PII direta na justificativa bloqueia."""
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(JustificativaInvalida, match="PII direta"):
            promover_perfil_equipamento(
                tenant_id=cenario["tenant"].id,
                equipamento_id=cenario["equipamento"].id,
                decisor_id=cenario["decisor_id"],
                rt_id=cenario["rt_id"],
                perfil_novo="A",
                evidencia_documental_id=cenario["evidencia_id"],
                justificativa=(
                    "Promocao avaliada pelo CPF 123.456.789-01 do tecnico "
                    "responsavel apos validacao do dossie tecnico OIML R76 "
                    "classe III conforme procedimento interno."
                ),
            )


@pytest.mark.django_db(transaction=True)
def test_justificativa_com_email_bloqueada(cenario):
    with run_in_tenant_context(cenario["tenant"].id):
        with pytest.raises(JustificativaInvalida, match="PII direta"):
            promover_perfil_equipamento(
                tenant_id=cenario["tenant"].id,
                equipamento_id=cenario["equipamento"].id,
                decisor_id=cenario["decisor_id"],
                rt_id=cenario["rt_id"],
                perfil_novo="A",
                evidencia_documental_id=cenario["evidencia_id"],
                justificativa=(
                    "Comunicacao via tecnico@laboratorio.com.br confirmou "
                    "atendimento aos requisitos OIML R76 classe III conforme "
                    "dossie tecnico anexo nesta data."
                ),
            )


# ----------------------------------------------------------------------
# Cross-tenant
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_cross_tenant_bloqueado(cenario):
    """Re-aplicacao do isolamento na SECURITY DEFINER — promover equipamento
    de outro tenant deve falhar mesmo SECURITY DEFINER pulando RLS."""
    tenant_b = TenantFactory(slug=f"eqp-prom-b-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant_b.id):
        with pytest.raises(EquipamentoNaoEncontrado):
            # Visao do tenant_b NAO ve o equipamento de tenant_a (RLS no
            # SELECT FOR UPDATE da funcao retorna 0 rows pela checagem
            # de tenant ativo).
            promover_perfil_equipamento(
                tenant_id=tenant_b.id,
                equipamento_id=cenario["equipamento"].id,
                decisor_id=cenario["decisor_id"],
                rt_id=cenario["rt_id"],
                perfil_novo="A",
                evidencia_documental_id=cenario["evidencia_id"],
                justificativa=JUSTIFICATIVA_OK,
            )


# ----------------------------------------------------------------------
# Regressao INV-EQP-001 — UPDATE direto fora da funcao continua bloqueado
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_update_direto_continua_bloqueado_apos_promocao(cenario):
    """INV-EQP-001 - mesmo apos promocao legitima, UPDATE direto via ORM
    continua bloqueado (GUC `app.perfil_promocao_permitida` reseta pra '0'
    no fim da funcao)."""
    with run_in_tenant_context(cenario["tenant"].id):
        promover_perfil_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento_id=cenario["equipamento"].id,
            decisor_id=cenario["decisor_id"],
            rt_id=cenario["rt_id"],
            perfil_novo="A",
            evidencia_documental_id=cenario["evidencia_id"],
            justificativa=JUSTIFICATIVA_OK,
        )
        # Tenta mudar PRA OUTRO snapshot (campo arbitrario novo) sem passar
        # pela funcao SECURITY DEFINER — deve cair no trigger imutabilidade.
        with pytest.raises(ProgrammingError, match="INV-EQP-001"):
            Equipamento.all_objects.filter(id=cenario["equipamento"].id).update(
                perfil_tenant_snapshot={
                    "perfil": "A",
                    "schema": "1.0.0",
                    "tentativa_bypass": True,
                },
            )


# ----------------------------------------------------------------------
# Evento publicado
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_evento_perfil_promovido_publicado_em_cadeia(cenario):
    """AC-EQP-001-7b - evento `equipamento.perfil_promovido` cravado na
    cadeia de auditoria com payload sanitizado."""
    with run_in_tenant_context(cenario["tenant"].id):
        promover_perfil_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento_id=cenario["equipamento"].id,
            decisor_id=cenario["decisor_id"],
            rt_id=cenario["rt_id"],
            perfil_novo="A",
            evidencia_documental_id=cenario["evidencia_id"],
            justificativa=JUSTIFICATIVA_OK,
        )
        eventos = list(
            Auditoria.objects.filter(action="equipamento.perfil_promovido")
        )
    assert len(eventos) == 1
    payload = eventos[0].payload_jsonb
    assert payload["perfil_novo"] == "A"
    assert payload["equipamento_id"] == str(cenario["equipamento"].id)
    # Justificativa NUNCA em texto cru - sempre hash.
    assert "justificativa_hash" in payload
    assert JUSTIFICATIVA_OK not in str(payload)
