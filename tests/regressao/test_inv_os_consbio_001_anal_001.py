"""Anti-regressao INV-OS-CONSBIO-001 (P-OS-A1) + INV-OS-ANAL-001 (P-OS-R2).

INV-OS-CONSBIO-001: AceiteAtividade com biometria touch EXIGE
ConsentimentoBiometriaTouch FK 1:1 NOT NULL. Domain valida cedo via
`valida_consentimento_biometria` + use case bloqueia + trigger PG defende.

INV-OS-ANAL-001 (cl. 7.1 ISO 17025): abertura via orcamento exige
`analise_critica_id` NOT NULL no payload — sem -> 412
`OrcamentoSemAnaliseCritica`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import transaction
from src.application.operacao.os.abrir_os_via_orcamento import (
    AbrirOSInput,
    ErroAbrirOS,
    ItemOrcamento,
    abrir_os_via_orcamento,
)
from src.application.operacao.os.atribuir_tecnico import (
    AtribuicaoAtividade,
    AtribuirTecnicoInput,
    atribuir_tecnico,
)
from src.application.operacao.os.coletar_aceite import (
    ColetarAceiteInput,
    ErroColetarAceite,
    coletar_aceite_atividade,
)
from src.application.operacao.os.iniciar_atividade import (
    IniciarAtividadeInput,
    iniciar_atividade,
)
from src.domain.operacao.os.value_objects import TipoAtividade
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import (
    OS,
    AceiteAtividade,
    ConsentimentoBiometriaTouch,
)
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory


def _setup(tenant):
    sfx = uuid4().hex[:6]
    with run_in_tenant_context(tenant.id):
        cliente, _ = Cliente.objects.get_or_create(
            tenant=tenant,
            documento="11222333000181",
            defaults={
                "tipo_pessoa": TipoPessoa.PJ,
                "nome": f"Cli {sfx}",
                "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
            },
        )
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag=f"INV-AC-{sfx}",
            numero_serie=f"NS-AC-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_e_iniciar(tenant, cliente, equipamento, executor_id):
    repo = DjangoOSRepository()
    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms",
        equipamento_id=equipamento.id,
        equipamento_recebimento_id=None,
        analise_critica_id=uuid4(),
        analise_critica_snapshot_hash="b" * 64,
        regra_decisao_acordada="default",
        valor_total=Decimal("100.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.MANUTENCAO_CORRETIVA,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=False,
            ),
        ),
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = abrir_os_via_orcamento(payload=payload, repository=repo)
        atividades = repo.listar_atividades_por_os(res.os_id)
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=atividades[0].id,
                        tecnico_executor_id=executor_id,
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )
        iniciar_atividade(
            payload=IniciarAtividadeInput(
                atividade_id=atividades[0].id,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
    return atividades[0].id


# =============================================================
# INV-OS-CONSBIO-001 — biometria sem consent bloqueia
# =============================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_consbio_001_happy_aceite_sem_bio_dispensa_consent(db):
    """Happy: aceite SEM biometria nao precisa de ConsentimentoBiometriaTouch."""
    tenant = TenantFactory(slug=f"inv-bio-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor = uuid4()
    ativ_id = _abrir_e_iniciar(tenant, cliente, equipamento, executor)

    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = coletar_aceite_atividade(
            payload=ColetarAceiteInput(
                atividade_id=ativ_id,
                cliente_referencia_hash="a" * 64,
                cliente_key_id="kms",
                texto_aceite_bruto="Aceito o servico conforme combinado",
                coletado_em=datetime.now(UTC),
                correlation_id=uuid4(),
            ),
            repository=repo,
        )
    assert res.consentimento_id is None
    with run_in_tenant_context(tenant.id):
        ace = AceiteAtividade.objects.get(id=res.aceite_id)
        assert ace.consentimento_id is None


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_consbio_001_unhappy_bio_sem_consent_412(db):
    """Unhappy: biometria_payload presente SEM consentimento_concedido_em -> 412."""
    tenant = TenantFactory(slug=f"inv-bio-u-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor = uuid4()
    ativ_id = _abrir_e_iniciar(tenant, cliente, equipamento, executor)

    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), pytest.raises(ErroColetarAceite) as exc:
        coletar_aceite_atividade(
            payload=ColetarAceiteInput(
                atividade_id=ativ_id,
                cliente_referencia_hash="a" * 64,
                cliente_key_id="kms",
                texto_aceite_bruto="Aceito",
                coletado_em=datetime.now(UTC),
                correlation_id=uuid4(),
                biometria_payload_encrypted=b"\x01\x02\x03",
                biometria_key_id="bio-key",
                # consentimento_concedido_em propositalmente None.
            ),
            repository=repo,
        )
    assert exc.value.codigo == "ConsentimentoBiometriaAusente"
    assert exc.value.http_status == 412


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_consbio_001_cross_tenant_consent_pertence_ao_mesmo_tenant(db):
    """Cross-tenant: ConsentimentoBiometriaTouch criado herda tenant da atividade."""
    tenant = TenantFactory(slug=f"inv-bio-ct-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor = uuid4()
    ativ_id = _abrir_e_iniciar(tenant, cliente, equipamento, executor)

    repo = DjangoOSRepository()
    agora = datetime.now(UTC)
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = coletar_aceite_atividade(
            payload=ColetarAceiteInput(
                atividade_id=ativ_id,
                cliente_referencia_hash="a" * 64,
                cliente_key_id="kms",
                texto_aceite_bruto="Aceito",
                coletado_em=agora,
                correlation_id=uuid4(),
                biometria_payload_encrypted=b"\x01\x02\x03",
                biometria_key_id="bio-key",
                consentimento_texto_canonico_id=uuid4(),
                consentimento_texto_hash="c" * 64,
                consentimento_versao_politica="1.0.0",
                consentimento_concedido_em=agora,
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        consent = ConsentimentoBiometriaTouch.objects.get(id=res.consentimento_id)
        assert consent.tenant_id == tenant.id
        assert consent.atividade_id == ativ_id


# =============================================================
# INV-OS-ANAL-001 — analise critica obrigatoria
# =============================================================


def _payload_basico(tenant, cliente, equipamento, *, analise_critica_id):
    return AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms",
        equipamento_id=equipamento.id,
        equipamento_recebimento_id=None,
        analise_critica_id=analise_critica_id,
        analise_critica_snapshot_hash="b" * 64 if analise_critica_id else "",
        regra_decisao_acordada="default",
        valor_total=Decimal("100.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.VISTORIA,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=False,
            ),
        ),
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_anal_001_happy_com_analise_critica_abre(db):
    """Happy: analise_critica_id presente -> OS criada normalmente."""
    tenant = TenantFactory(slug=f"inv-anal-h-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    analise_id = uuid4()
    payload = _payload_basico(
        tenant, cliente, equipamento, analise_critica_id=analise_id
    )
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = abrir_os_via_orcamento(payload=payload, repository=repo)
    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=res.os_id)
        assert os_obj.analise_critica_id == analise_id
        assert os_obj.analise_critica_snapshot_hash == "b" * 64


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_anal_001_unhappy_sem_analise_critica_412(db):
    """Unhappy: analise_critica_id=None -> 412 OrcamentoSemAnaliseCritica."""
    tenant = TenantFactory(slug=f"inv-anal-u-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    payload = _payload_basico(
        tenant, cliente, equipamento, analise_critica_id=None
    )
    repo = DjangoOSRepository()
    with run_in_tenant_context(tenant.id), pytest.raises(ErroAbrirOS) as exc:
        abrir_os_via_orcamento(payload=payload, repository=repo)
    assert exc.value.codigo == "OrcamentoSemAnaliseCritica"
    assert exc.value.http_status == 412


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_inv_os_anal_001_cross_tenant_analise_critica_persistida_por_tenant(db):
    """Cross-tenant: cada tenant tem seu analise_critica_id isolado na OS."""
    tenant_a = TenantFactory(slug=f"inv-anal-cta-{uuid4().hex[:6]}")
    tenant_b = TenantFactory(slug=f"inv-anal-ctb-{uuid4().hex[:6]}")
    cli_a, eq_a = _setup(tenant_a)
    cli_b, eq_b = _setup(tenant_b)
    analise_a = uuid4()
    analise_b = uuid4()
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant_a.id), transaction.atomic():
        res_a = abrir_os_via_orcamento(
            payload=_payload_basico(tenant_a, cli_a, eq_a, analise_critica_id=analise_a),
            repository=repo,
        )
    with run_in_tenant_context(tenant_b.id), transaction.atomic():
        res_b = abrir_os_via_orcamento(
            payload=_payload_basico(tenant_b, cli_b, eq_b, analise_critica_id=analise_b),
            repository=repo,
        )

    with run_in_tenant_context(tenant_a.id):
        os_a = OS.objects.get(id=res_a.os_id)
        assert os_a.analise_critica_id == analise_a
    with run_in_tenant_context(tenant_b.id):
        os_b = OS.objects.get(id=res_b.os_id)
        assert os_b.analise_critica_id == analise_b
    assert analise_a != analise_b
