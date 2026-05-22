"""T-EQP-055 (US-EQP-006 AC-EQP-006-7b / P-EQP-R3) — condicoes ambientais
do EquipamentoRecebimento + porta stub CAPAQueryService.

Cobre:
- Service: criar_recebimento aceita temp_ambiente_c, ur_percentual,
  pressao_kpa, justificativa_condicoes_ambientais_ausentes.
- Validacao de faixa (-50..80 / 0..100 / 50..120).
- Justificativa quando preenchida: >=20 chars + anti-PII.
- Alerta P3 stub `equipamento.recebimento_sem_ambiente` quando todos os
  3 NULL + sem justificativa (soft, nao bloqueia).
- Trigger PG imutabilidade pos-INSERT em ALL 4 campos.
- Payload do evento `equipamento.recebido` inclui bloco `ambiente`.
- Porta `qualidade.capa_query_service` stub.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import DatabaseError
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    Equipamento,
    EquipamentoRecebimento,
)
from src.infrastructure.equipamentos.services_recebimento import (
    CondicoesAmbientaisInvalidas,
    DadosRecebimento,
    criar_recebimento,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.qualidade import capa_query_service

from tests.factories import TenantFactory, UsuarioFactory


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:6]
    tenant = TenantFactory(slug=f"amb-{sfx}", nome_fantasia="Lab Amb")
    operador = UsuarioFactory(email=f"op-amb-{sfx}@e.local")
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Amb",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq = Equipamento.objects.create(
            tenant=tenant,
            tag=f"AMB-{sfx}",
            numero_serie=f"NSAMB-{sfx}",
            fabricante="Toledo",
            modelo="X1",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return {"tenant": tenant, "operador": operador, "eq": eq}


# ====================================================================
# Happy paths
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_recebimento_com_ambiente_completo(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_recebimento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            recebido_por_id=cenario["operador"].id,
            dados=DadosRecebimento(
                condicao_visual_chegada="integro",
                temp_ambiente_c="23.5",
                ur_percentual="55",
                pressao_kpa="101.3",
            ),
        )
        rec = EquipamentoRecebimento.objects.get(id=resultado.recebimento.id)
    assert rec.temp_ambiente_c == Decimal("23.50")
    assert rec.ur_percentual == Decimal("55.00")
    assert rec.pressao_kpa == Decimal("101.30")
    assert rec.justificativa_condicoes_ambientais_ausentes == ""


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_recebimento_com_ambiente_parcial(cenario):
    """So temperatura preenchida — ur/pressao NULL OK porque grandeza nao exige."""
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_recebimento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            recebido_por_id=cenario["operador"].id,
            dados=DadosRecebimento(
                condicao_visual_chegada="integro",
                temp_ambiente_c="21",
            ),
        )
        rec = EquipamentoRecebimento.objects.get(id=resultado.recebimento.id)
    assert rec.temp_ambiente_c == Decimal("21.00")
    assert rec.ur_percentual is None
    assert rec.pressao_kpa is None


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_recebimento_todos_null_com_justificativa(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_recebimento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            recebido_por_id=cenario["operador"].id,
            dados=DadosRecebimento(
                condicao_visual_chegada="integro",
                justificativa_ambiental_ausentes=(
                    "Grandeza massa bruta nao exige medicao ambiental "
                    "(RBC cl. 6.3)."
                ),
            ),
        )
        rec = EquipamentoRecebimento.objects.get(id=resultado.recebimento.id)
    assert rec.temp_ambiente_c is None
    assert rec.ur_percentual is None
    assert rec.pressao_kpa is None
    assert "Grandeza massa bruta" in rec.justificativa_condicoes_ambientais_ausentes


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_recebimento_todos_null_sem_justificativa_dispara_alerta(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_recebimento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            recebido_por_id=cenario["operador"].id,
            dados=DadosRecebimento(condicao_visual_chegada="integro"),
        )
        # Alerta P3 stub disparado
        eventos_alerta = Auditoria.objects.filter(
            action="equipamento.recebimento_sem_ambiente",
        ).filter(
            payload_jsonb__recebimento_id=str(resultado.recebimento.id)
        )
        assert eventos_alerta.exists()
        evento = eventos_alerta.first()
        # Payload sanitizado: sem PII, sem tag, sem cliente
        assert evento is not None
        payload = evento.payload_jsonb
        assert payload["equipamento_id"] == str(cenario["eq"].id)
        assert "tag" not in payload
        assert "cliente" not in payload


# ====================================================================
# Validacao de faixa
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_temp_fora_faixa_falha(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        with pytest.raises(CondicoesAmbientaisInvalidas, match=r"temp_ambiente_c"):
            criar_recebimento(
                tenant_id=cenario["tenant"].id,
                equipamento=cenario["eq"],
                recebido_por_id=cenario["operador"].id,
                dados=DadosRecebimento(
                    condicao_visual_chegada="integro",
                    temp_ambiente_c="150",  # absurdo
                ),
            )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ur_fora_faixa_falha(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        with pytest.raises(CondicoesAmbientaisInvalidas, match=r"ur_percentual"):
            criar_recebimento(
                tenant_id=cenario["tenant"].id,
                equipamento=cenario["eq"],
                recebido_por_id=cenario["operador"].id,
                dados=DadosRecebimento(
                    condicao_visual_chegada="integro",
                    ur_percentual="-5",  # negativo invalido
                ),
            )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_pressao_fora_faixa_falha(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        with pytest.raises(CondicoesAmbientaisInvalidas, match=r"pressao_kpa"):
            criar_recebimento(
                tenant_id=cenario["tenant"].id,
                equipamento=cenario["eq"],
                recebido_por_id=cenario["operador"].id,
                dados=DadosRecebimento(
                    condicao_visual_chegada="integro",
                    pressao_kpa="200",
                ),
            )


# ====================================================================
# Validacao da justificativa
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_justificativa_curta_falha(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        with pytest.raises(CondicoesAmbientaisInvalidas, match=r"justificativa"):
            criar_recebimento(
                tenant_id=cenario["tenant"].id,
                equipamento=cenario["eq"],
                recebido_por_id=cenario["operador"].id,
                dados=DadosRecebimento(
                    condicao_visual_chegada="integro",
                    justificativa_ambiental_ausentes="curta",
                ),
            )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_justificativa_com_pii_falha(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        with pytest.raises(CondicoesAmbientaisInvalidas, match=r"PII"):
            criar_recebimento(
                tenant_id=cenario["tenant"].id,
                equipamento=cenario["eq"],
                recebido_por_id=cenario["operador"].id,
                dados=DadosRecebimento(
                    condicao_visual_chegada="integro",
                    justificativa_ambiental_ausentes=(
                        "Operador Joao Silva nao verificou condicoes."
                    ),
                ),
            )


# ====================================================================
# Imutabilidade pos-INSERT (trigger PG)
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_temp_imutavel_pos_insert(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_recebimento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            recebido_por_id=cenario["operador"].id,
            dados=DadosRecebimento(
                condicao_visual_chegada="integro",
                temp_ambiente_c="22",
            ),
        )
        with pytest.raises(DatabaseError, match=r"temp_ambiente_c imutavel"):
            EquipamentoRecebimento.objects.filter(
                id=resultado.recebimento.id
            ).update(temp_ambiente_c=Decimal("99.00"))


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ur_imutavel_pos_insert(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_recebimento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            recebido_por_id=cenario["operador"].id,
            dados=DadosRecebimento(
                condicao_visual_chegada="integro",
                ur_percentual="50",
            ),
        )
        with pytest.raises(DatabaseError, match=r"ur_percentual imutavel"):
            EquipamentoRecebimento.objects.filter(
                id=resultado.recebimento.id
            ).update(ur_percentual=Decimal("80.00"))


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_pressao_imutavel_pos_insert(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_recebimento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            recebido_por_id=cenario["operador"].id,
            dados=DadosRecebimento(
                condicao_visual_chegada="integro",
                pressao_kpa="101",
            ),
        )
        with pytest.raises(DatabaseError, match=r"pressao_kpa imutavel"):
            EquipamentoRecebimento.objects.filter(
                id=resultado.recebimento.id
            ).update(pressao_kpa=Decimal("110.00"))


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_justificativa_imutavel_pos_insert(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_recebimento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            recebido_por_id=cenario["operador"].id,
            dados=DadosRecebimento(
                condicao_visual_chegada="integro",
                justificativa_ambiental_ausentes=(
                    "Grandeza nao exige medicao ambiental (RBC cl. 6.3)."
                ),
            ),
        )
        with pytest.raises(DatabaseError, match=r"justificativa_condicoes_ambientais_ausentes imutavel"):
            EquipamentoRecebimento.objects.filter(
                id=resultado.recebimento.id
            ).update(
                justificativa_condicoes_ambientais_ausentes="alterado"
            )


# ====================================================================
# Payload do evento
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_payload_evento_inclui_bloco_ambiente(cenario):
    with run_in_tenant_context(cenario["tenant"].id, cenario["operador"].id):
        resultado = criar_recebimento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["eq"],
            recebido_por_id=cenario["operador"].id,
            dados=DadosRecebimento(
                condicao_visual_chegada="integro",
                temp_ambiente_c="23",
                ur_percentual="55",
                pressao_kpa="101",
            ),
        )
        evento = Auditoria.objects.filter(
            action="equipamento.recebido",
        ).filter(payload_jsonb__recebimento_id=str(resultado.recebimento.id)).first()
    assert evento is not None
    payload = evento.payload_jsonb
    assert "ambiente" in payload
    ambiente = payload["ambiente"]
    assert ambiente["temp_ambiente_c"] == 23.0
    assert ambiente["ur_percentual"] == 55.0
    assert ambiente["pressao_kpa"] == 101.0
    assert ambiente["tem_justificativa_ausentes"] is False


# ====================================================================
# Porta CAPAQueryService stub
# ====================================================================


def test_capa_stub_retorna_false(cenario):
    """Marco 2 stub — modulo qualidade nao existe ainda."""
    assert capa_query_service.capa_aberta_para_recebimento(uuid4()) is False
    assert capa_query_service.capa_aberta_para_equipamento(cenario["eq"].id) is False
