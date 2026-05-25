"""Testes integrados M3 Fase 5 — operacoes avancadas + coletar_aceite.

Cobre happy path de:
- coletar_aceite_atividade (T-OS-063 / AC-OS-004-7)
- reabrir_os (T-OS-066 / AC-OS-006-*)
- transferir_tecnico (T-OS-078 / AC-OS-012-1)
- reagendar_atividade (T-OS-077)
- dispensar_aceite_cliente (T-OS-079 / AC-OS-013-* + P-OS-A4)
- marcar_no_show (T-OS-082 / AC-OS-014-*)
- criar_os_avulsa (T-OS-083 / AC-OS-015-*)

Todos contra `DjangoOSRepository` real.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import transaction
from src.application.operacao.os.abrir_os_via_orcamento import (
    AbrirOSInput,
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
    coletar_aceite_atividade,
)
from src.application.operacao.os.concluir_atividade import (
    ConcluirAtividadeInput,
    concluir_atividade,
)
from src.application.operacao.os.iniciar_atividade import (
    IniciarAtividadeInput,
    iniciar_atividade,
)
from src.application.operacao.os.operacoes_avancadas import (
    CriarOSAvulsaInput,
    DispensarAceiteInput,
    ItemOSAvulsa,
    MarcarNoShowInput,
    ReabrirOSInput,
    ReagendarAtividadeInput,
    TransferirTecnicoInput,
    criar_os_avulsa,
    dispensar_aceite_cliente,
    marcar_no_show,
    reabrir_os,
    reagendar_atividade,
    transferir_tecnico,
)
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoOS,
    MotivoCancelamento,
    PrecedenteDispensa,
    TipoAtividade,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.models import (
    OS,
    AceiteAtividade,
    AtividadeDaOS,
    DispensaAceiteAtividade,
    EvidenciaFotoAtividade,
)
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory

MOTIVO_OK = "valor obtido fora da incerteza declarada pelo cliente final"
MOTIVO_OK_B = "tecnico solicitado pela gerencia para outra urgencia regional"


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
            tag=f"M3-OA-{sfx}",
            numero_serie=f"NS-OA-{sfx}",
            fabricante="Toledo",
            modelo="X",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
    return cliente, equipamento


def _abrir_atribuir_iniciar(tenant, cliente, equipamento, executor_id, tipo):
    """Abre OS com 1 atividade do `tipo`, atribui e inicia. Retorna (os_id, ativ_id)."""
    repo = DjangoOSRepository()
    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms-test-key",
        equipamento_id=equipamento.id,
        equipamento_recebimento_id=None,
        analise_critica_id=uuid4(),
        analise_critica_snapshot_hash="b" * 64,
        regra_decisao_acordada="default",
        valor_total=Decimal("100.00"),
        itens=(
            ItemOrcamento(
                tipo=tipo,
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
        res_abrir = abrir_os_via_orcamento(payload=payload, repository=repo)
        atividades = repo.listar_atividades_por_os(res_abrir.os_id)
        ativ_id = atividades[0].id
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res_abrir.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=ativ_id, tecnico_executor_id=executor_id
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
                atividade_id=ativ_id,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                client_event_id=uuid4(),
                iniciada_em=datetime.now(UTC),
            ),
            repository=repo,
        )
    return res_abrir.os_id, ativ_id


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_coletar_aceite_sem_biometria_happy(db):
    """Aceite sem biometria — sem ConsentimentoBiometriaTouch."""
    tenant = TenantFactory(slug=f"m3oa-ace-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()
    os_id, ativ_id = _abrir_atribuir_iniciar(
        tenant, cliente, equipamento, executor_id, TipoAtividade.MANUTENCAO_CORRETIVA
    )
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = coletar_aceite_atividade(
            payload=ColetarAceiteInput(
                atividade_id=ativ_id,
                cliente_referencia_hash="a" * 64,
                cliente_key_id="kms-test-key",
                texto_aceite_bruto="Confirmo a conclusao do servico conforme combinado",
                coletado_em=datetime.now(UTC),
                correlation_id=uuid4(),
            ),
            repository=repo,
        )
    assert res.consentimento_id is None
    with run_in_tenant_context(tenant.id):
        ac = AceiteAtividade.objects.get(id=res.aceite_id)
        assert ac.consentimento_id is None
        assert ac.biometria_payload_encrypted in (b"", None) or len(ac.biometria_payload_encrypted) == 0


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_coletar_aceite_com_biometria_cria_consentimento(db):
    """Bio touch -> ConsentimentoBiometriaTouch criado ANTES (INV-OS-CONSBIO-001)."""
    tenant = TenantFactory(slug=f"m3oa-bio-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()
    _, ativ_id = _abrir_atribuir_iniciar(
        tenant, cliente, equipamento, executor_id, TipoAtividade.MANUTENCAO_CORRETIVA
    )
    repo = DjangoOSRepository()
    agora = datetime.now(UTC)

    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = coletar_aceite_atividade(
            payload=ColetarAceiteInput(
                atividade_id=ativ_id,
                cliente_referencia_hash="a" * 64,
                cliente_key_id="kms-test-key",
                texto_aceite_bruto="Confirmo conclusao",
                coletado_em=agora,
                correlation_id=uuid4(),
                biometria_payload_encrypted=b"\x01\x02\x03\x04\x05",
                biometria_key_id="BIOMETRIA_KEY_test-tenant",
                consentimento_texto_canonico_id=uuid4(),
                consentimento_texto_hash="c" * 64,
                consentimento_versao_politica="1.0.0",
                consentimento_concedido_em=agora,
            ),
            repository=repo,
        )
    assert res.consentimento_id is not None


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_reabrir_os_clona_atividades(db):
    """AC-OS-006-1/2: reabertura cria OS-filha + clona atividades em PENDENTE."""
    tenant = TenantFactory(slug=f"m3oa-reab-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()
    os_id, ativ_id = _abrir_atribuir_iniciar(
        tenant, cliente, equipamento, executor_id, TipoAtividade.VISTORIA
    )
    repo = DjangoOSRepository()
    # Conclui pra ficar terminal.
    with run_in_tenant_context(tenant.id), transaction.atomic():
        concluir_atividade(
            payload=ConcluirAtividadeInput(
                atividade_id=ativ_id,
                usuario_id=executor_id,
                correlation_id=uuid4(),
                concluida_em=datetime.now(UTC),
                aceite_dispensado=True,
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = reabrir_os(
            payload=ReabrirOSInput(
                os_origem_id=os_id,
                motivo=MotivoCancelamento(MOTIVO_OK),
                garantia_procedente=True,
                chamado_origem_id=None,
                sucessao_societaria_id=None,
                correlation_id=uuid4(),
                reaberta_em=datetime.now(UTC),
                reaberta_por_user_id=None,
            ),
            repository=repo,
        )

    assert res.os_id_nova != os_id
    assert len(res.atividades_clonadas) == 1
    with run_in_tenant_context(tenant.id):
        nova = OS.objects.get(id=res.os_id_nova)
        assert nova.os_origem_id == os_id
        assert nova.estado == EstadoOS.RASCUNHO.value
        clones = list(AtividadeDaOS.objects.filter(os_id=res.os_id_nova))
        assert len(clones) == 1
        assert clones[0].estado == EstadoAtividade.PENDENTE.value
        assert clones[0].sequencia == 1


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_transferir_tecnico_atualiza_executor(db):
    tenant = TenantFactory(slug=f"m3oa-tr-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()
    novo_tecnico_id = uuid4()
    repo = DjangoOSRepository()
    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms-test-key",
        equipamento_id=equipamento.id,
        equipamento_recebimento_id=None,
        analise_critica_id=uuid4(),
        analise_critica_snapshot_hash="b" * 64,
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
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res_abrir = abrir_os_via_orcamento(payload=payload, repository=repo)
        atividades = repo.listar_atividades_por_os(res_abrir.os_id)
        ativ_id = atividades[0].id
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res_abrir.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=ativ_id, tecnico_executor_id=executor_id
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )
        transferir_tecnico(
            payload=TransferirTecnicoInput(
                atividade_id=ativ_id,
                novo_tecnico_id=novo_tecnico_id,
                motivo=MotivoCancelamento(MOTIVO_OK_B),
                correlation_id=uuid4(),
                transferida_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_id)
        assert ativ.tecnico_executor_id == novo_tecnico_id


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_reagendar_atividade(db):
    tenant = TenantFactory(slug=f"m3oa-ra-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()
    repo = DjangoOSRepository()
    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms-test-key",
        equipamento_id=equipamento.id,
        equipamento_recebimento_id=None,
        analise_critica_id=uuid4(),
        analise_critica_snapshot_hash="b" * 64,
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
    nova_data = datetime.now(UTC) + timedelta(days=2)
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = abrir_os_via_orcamento(payload=payload, repository=repo)
        ativ_id = repo.listar_atividades_por_os(res.os_id)[0].id
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=ativ_id, tecnico_executor_id=executor_id
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )
        reagendar_atividade(
            payload=ReagendarAtividadeInput(
                atividade_id=ativ_id,
                nova_agendada_para=nova_data,
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        ativ = AtividadeDaOS.objects.get(id=ativ_id)
        assert ativ.agendada_para == nova_data


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_dispensar_aceite_com_a3_happy(db):
    """AC-OS-013-5 (P-OS-A4): dispensa exige A3 + termo + precedente."""
    tenant = TenantFactory(slug=f"m3oa-disp-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()
    gerente_id = uuid4()
    _, ativ_id = _abrir_atribuir_iniciar(
        tenant, cliente, equipamento, executor_id, TipoAtividade.MANUTENCAO_CORRETIVA
    )
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = dispensar_aceite_cliente(
            payload=DispensarAceiteInput(
                atividade_id=ativ_id,
                motivo=MotivoCancelamento(MOTIVO_OK),
                autorizado_por_gerente_id=gerente_id,
                a3_assinatura_hash="d" * 64,
                a3_certificado_emissor_hash="e" * 64,
                a3_assinada_em=datetime.now(UTC),
                termo_pdf_b2_uri="b2://bucket/termo-dispensa.pdf",
                termo_pdf_sha256="f" * 64,
                precedente_tipo=PrecedenteDispensa.IMPOSSIBILIDADE_TECNICA,
                precedente_evento_id=None,
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        disp = DispensaAceiteAtividade.objects.get(id=res.dispensa_id)
        assert disp.atividade_id == ativ_id
        assert disp.autorizado_por_gerente_id == gerente_id


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_marcar_no_show_com_aviso_acknowledged_happy(db):
    """AC-OS-014-1 + AC-OS-014-3 (P-OS-A5)."""
    tenant = TenantFactory(slug=f"m3oa-ns-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    executor_id = uuid4()
    repo = DjangoOSRepository()
    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms-test-key",
        equipamento_id=equipamento.id,
        equipamento_recebimento_id=None,
        analise_critica_id=uuid4(),
        analise_critica_snapshot_hash="b" * 64,
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
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = abrir_os_via_orcamento(payload=payload, repository=repo)
        ativ_id = repo.listar_atividades_por_os(res.os_id)[0].id
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=ativ_id, tecnico_executor_id=executor_id
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )
        # Atividade fica AGENDADA — marca no-show.
        res_ns = marcar_no_show(
            payload=MarcarNoShowInput(
                atividade_id=ativ_id,
                tecnico_user_id=executor_id,
                foto_b2_uri="b2://bucket/no-show.jpg",
                foto_sha256="0" * 64,
                client_event_id=uuid4(),
                client_event_created_at=datetime.now(UTC),
                aviso_terceiros_acknowledged=True,
                correlation_id=uuid4(),
                ocorrido_em=datetime.now(UTC),
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        # Atividade permanece AGENDADA (nao transita).
        ativ = AtividadeDaOS.objects.get(id=ativ_id)
        assert ativ.estado == EstadoAtividade.AGENDADA.value
        foto = EvidenciaFotoAtividade.objects.get(id=res_ns.foto_id)
        assert foto.tipo == "no_show"


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_criar_os_avulsa_happy(db):
    """AC-OS-015-1: cria OS sem orcamento + valor_unitario_snapshot."""
    tenant = TenantFactory(slug=f"m3oa-av-{uuid4().hex[:6]}")
    cliente, equipamento = _setup(tenant)
    repo = DjangoOSRepository()

    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = criar_os_avulsa(
            payload=CriarOSAvulsaInput(
                tenant_id=tenant.id,
                cliente_id=cliente.id,
                cliente_referencia_hash="a" * 64,
                cliente_key_id="kms-test-key",
                equipamento_id=equipamento.id,
                equipamento_recebimento_id=None,
                itens=(
                    ItemOSAvulsa(
                        tipo=TipoAtividade.VISTORIA,
                        sequencia=1,
                        valor_unitario_snapshot=Decimal("90.00"),
                        requer_recebimento=False,
                    ),
                ),
                analise_critica_inline_id=uuid4(),
                analise_critica_snapshot_hash="b" * 64,
                regra_decisao_acordada="default",
                correlation_id=uuid4(),
                criada_em=datetime.now(UTC),
                criada_por_user_id=None,
            ),
            repository=repo,
        )

    with run_in_tenant_context(tenant.id):
        os_obj = OS.objects.get(id=res.os_id)
        assert os_obj.orcamento_origem_id is None
        assert os_obj.numero_os == res.numero_os
        assert os_obj.estado == EstadoOS.RASCUNHO.value
        ativ = AtividadeDaOS.objects.get(id=res.atividades_planejadas[0])
        assert ativ.valor_unitario_snapshot == Decimal("90.00")
