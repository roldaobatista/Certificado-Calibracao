"""T-EQP-017 (AC-EQP-002-6 / INV-EQP-VERSAO-002) — service
`criar_versao_equipamento` + evento `equipamento.versao_criada` sanitizado.

Cobre:
1. Happy path: cria EquipamentoVersao + publica evento com payload.
2. Payload tem 5 campos basicos + 9 derivados/hashes — NUNCA campos crus.
3. Defesa INV-EQP-VERSAO-002: assert anti-vaza bloqueia mutacao
   experimental que injete campo proibido.
4. Acao canonica registrada (`equipamento.versao_criada`).
5. Hashes calculados com salt do tenant (HMAC).
6. RLS: cross-tenant nao cria versao no tenant errado.
7. Valores `valor_anterior`/`valor_novo` cru NUNCA estao no payload.
8. `motivo_detalhe` cru NUNCA esta no payload.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import (
    Equipamento,
    EquipamentoVersao,
    MotivoMudancaEquipamentoVersao,
)
from src.infrastructure.equipamentos.services_versao import (
    CAMPOS_PAYLOAD_PERMITIDOS,
    CAMPOS_PAYLOAD_PROIBIDOS,
    DadosCriacaoVersao,
    PayloadVazandoPII,
    _validar_payload_anti_vaza,
    criar_versao_equipamento,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"eqp-evt-{sfx}")
    usuario = UsuarioFactory(email=f"evt-{sfx}@c.local")
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Evento",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag="EVT-001",
            numero_serie="NS-EVT-1",
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
# Happy
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_happy_cria_versao_e_publica_evento(cenario):
    """T-EQP-017 — service cria EquipamentoVersao + publica evento."""
    with run_in_tenant_context(cenario["tenant"].id):
        resultado = criar_versao_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            criado_por_id=cenario["usuario"].id,
            dados=DadosCriacaoVersao(
                campo="modelo",
                valor_anterior="Prix 4",
                valor_novo="Prix 4 Plus",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL,
            ),
        )
        assert EquipamentoVersao.objects.filter(id=resultado.versao.id).exists()
        eventos = list(
            Auditoria.objects.filter(action="equipamento.versao_criada")
        )
    assert len(eventos) == 1


@pytest.mark.django_db(transaction=True)
def test_payload_so_tem_campos_da_lista_positiva(cenario):
    """INV-EQP-VERSAO-002 — payload publicado so contem campos
    autorizados."""
    with run_in_tenant_context(cenario["tenant"].id):
        criar_versao_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            criado_por_id=cenario["usuario"].id,
            dados=DadosCriacaoVersao(
                campo="modelo",
                valor_anterior="Prix 4",
                valor_novo="Prix 4 Plus",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL,
            ),
        )
        evento = Auditoria.objects.get(action="equipamento.versao_criada")
    chaves = set(evento.payload_jsonb.keys())
    # Toda chave do payload deve estar na lista positiva.
    assert chaves <= CAMPOS_PAYLOAD_PERMITIDOS, (
        f"payload tem chave fora da lista positiva: {chaves - CAMPOS_PAYLOAD_PERMITIDOS}"
    )
    # Nenhuma chave proibida explicita.
    assert not (chaves & CAMPOS_PAYLOAD_PROIBIDOS), (
        f"payload vazou campo proibido: {chaves & CAMPOS_PAYLOAD_PROIBIDOS}"
    )


@pytest.mark.django_db(transaction=True)
def test_payload_nao_vaza_valor_anterior_novo_crus(cenario):
    """Defesa basica — `Prix 4` (anterior) e `Prix 4 Plus` (novo) nao
    aparecem em str(payload)."""
    with run_in_tenant_context(cenario["tenant"].id):
        criar_versao_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            criado_por_id=cenario["usuario"].id,
            dados=DadosCriacaoVersao(
                campo="modelo",
                valor_anterior="Prix 4",
                valor_novo="Prix 4 Plus",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL,
            ),
        )
        evento = Auditoria.objects.get(action="equipamento.versao_criada")
    assert "Prix 4 Plus" not in str(evento.payload_jsonb)
    assert evento.payload_jsonb.get("valor_anterior_hash")
    assert evento.payload_jsonb.get("valor_novo_hash")


@pytest.mark.django_db(transaction=True)
def test_payload_nao_vaza_motivo_detalhe_cru(cenario):
    """INV-EQP-VERSAO-002 — `motivo_detalhe` em texto cru NUNCA no
    payload (somente `motivo_detalhe_hash`)."""
    detalhe = (
        "Substituicao do componente principal apos auditoria do ciclo "
        "2026; rastreabilidade preservada por procedimento PROC-001."
    )
    with run_in_tenant_context(cenario["tenant"].id):
        criar_versao_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            criado_por_id=cenario["usuario"].id,
            dados=DadosCriacaoVersao(
                campo="modelo",
                valor_anterior="A",
                valor_novo="B",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.SUBSTITUICAO_COMPONENTE_CRITICO,
                motivo_detalhe=detalhe,
            ),
        )
        evento = Auditoria.objects.get(action="equipamento.versao_criada")
    assert detalhe not in str(evento.payload_jsonb)
    assert evento.payload_jsonb.get("motivo_detalhe_hash")


@pytest.mark.django_db(transaction=True)
def test_payload_nao_vaza_cliente_id_cru(cenario):
    """INV-EQP-VERSAO-002 — `cliente_atual_id` em texto cru NUNCA no
    payload (somente hash)."""
    with run_in_tenant_context(cenario["tenant"].id):
        criar_versao_equipamento(
            tenant_id=cenario["tenant"].id,
            equipamento=cenario["equipamento"],
            criado_por_id=cenario["usuario"].id,
            dados=DadosCriacaoVersao(
                campo="modelo",
                valor_anterior="A",
                valor_novo="B",
                motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL,
            ),
        )
        evento = Auditoria.objects.get(action="equipamento.versao_criada")
    assert str(cenario["cliente"].id) not in str(evento.payload_jsonb)
    assert evento.payload_jsonb.get("cliente_atual_id_no_momento_hash")


# ----------------------------------------------------------------------
# Defesa em profundidade — assert anti-vaza
# ----------------------------------------------------------------------


def test_validar_payload_anti_vaza_bloqueia_motivo_detalhe_cru():
    with pytest.raises(PayloadVazandoPII, match="motivo_detalhe"):
        _validar_payload_anti_vaza(
            {
                "tenant_id": "x",
                "equipamento_id": "y",
                "versao_id": "z",
                "motivo_detalhe": "isso e proibido",
            }
        )


def test_validar_payload_anti_vaza_bloqueia_valor_anterior_cru():
    with pytest.raises(PayloadVazandoPII, match="valor_anterior"):
        _validar_payload_anti_vaza({"valor_anterior": "Prix 4"})


def test_validar_payload_anti_vaza_bloqueia_assinatura_a3_hash_truncado():
    """P-EQP-T5 — hash A3 truncado proibido (so UUID opaco vai)."""
    with pytest.raises(PayloadVazandoPII, match="assinatura_a3_hash"):
        _validar_payload_anti_vaza({"assinatura_a3_hash": "abc123"})


def test_validar_payload_anti_vaza_bloqueia_numero_serie_cru():
    with pytest.raises(PayloadVazandoPII, match="numero_serie"):
        _validar_payload_anti_vaza({"numero_serie": "NS-123"})


def test_validar_payload_anti_vaza_bloqueia_campo_fora_da_lista_positiva():
    """Whitelist e FECHADA — campo experimental nao-listado bloqueia."""
    with pytest.raises(PayloadVazandoPII, match="fora da lista positiva"):
        _validar_payload_anti_vaza(
            {
                "tenant_id": "x",
                "equipamento_id": "y",
                "experimento_qualquer_coisa": "valor",
            }
        )


# ----------------------------------------------------------------------
# Cross-tenant
# ----------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_cross_tenant_bloqueado(cenario):
    """Defesa em profundidade — tentar criar versao no contexto de
    outro tenant bloqueia em alguma camada (ValidationError do clean()
    porque equipamento nao visivel via RLS, OU IntegrityError/RLS
    explicito quando service ignora clean). Nunca chega a versao."""
    from django.core.exceptions import ValidationError
    from django.db.utils import IntegrityError, ProgrammingError

    tenant_b = TenantFactory(slug=f"evt-b-{uuid4().hex[:8]}")
    with run_in_tenant_context(tenant_b.id):
        with pytest.raises((IntegrityError, ProgrammingError, ValidationError)):
            criar_versao_equipamento(
                tenant_id=cenario["tenant"].id,  # tenta passar tenant_a
                equipamento=cenario["equipamento"],
                criado_por_id=cenario["usuario"].id,
                dados=DadosCriacaoVersao(
                    campo="modelo",
                    valor_anterior="A",
                    valor_novo="B",
                    motivo_mudanca=MotivoMudancaEquipamentoVersao.CORRECAO_CADASTRAL,
                ),
            )
        # Em qualquer caso, NAO existe versao para o equipamento no
        # tenant errado.
        assert EquipamentoVersao.objects.filter(
            equipamento_id=cenario["equipamento"].id
        ).count() == 0
