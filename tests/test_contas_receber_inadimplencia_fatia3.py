"""Fatia 3b — inadimplência perfil-aware (T-CR-043). Verificação 3b (parte 1: adapter).

Cobre o adapter real `TituloVencidoInadimplenciaSource` que substitui o
`SourceListaInterim` do módulo `clientes`:
  - grace por perfil na fronteira exata (D+44 perfil A NÃO entra / D+46 entra);
  - grace menor (perfil D = 7 dias);
  - `InadimplenciaItem` estendido (perfil/grace_perfil) — PLAN-CR-01;
  - cliente anonimizado (cliente_atual_id NULL) fora da régua;
  - `iter_inadimplentes_90d` materializa lista (sem contexto aninhado);
  - `SourceListaInterim` legado aceita os campos novos sem quebrar (PLAN-CR-01);
  - `get_source()` parametrizado por settings.

A notificação D+30/D+45 (T-CR-044) é testada em separado (parte 2).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from django.db import DatabaseError, connection
from django.test import override_settings
from src.domain.comercial.clientes.inadimplencia_source import InadimplenciaItem
from src.domain.contas_receber.entities import Titulo
from src.domain.contas_receber.enums import (
    CategoriaReceita,
    EstadoTitulo,
    MeioCobranca,
    OrigemTitulo,
)
from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel
from src.infrastructure.contas_receber.inadimplencia_adapter import (
    TituloVencidoInadimplenciaSource,
    grace_period_inadimplencia_por_perfil,
)
from src.infrastructure.contas_receber.repositories import DjangoTituloRepository
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _hash_cliente() -> str:
    return uuid4().hex + uuid4().hex


def _criar_titulo_vencido(tenant, *, dias_vencido: int, cliente_id, perfil: str) -> Titulo:
    titulo = Titulo(
        titulo_id=uuid4(),
        tenant_id=tenant.id,
        cliente_referencia=ReferenciaPIIAnonimizavel(
            uuid_atual_id=cliente_id, hash_original=_hash_cliente(), key_id="v1"
        ),
        valor_original=Dinheiro(centavos=100000, moeda="BRL"),
        data_emissao=date.today() - timedelta(days=dias_vencido + 30),
        data_vencimento=date.today() - timedelta(days=dias_vencido),
        estado=EstadoTitulo.VENCIDO,
        meio=MeioCobranca.BOLETO,
        categoria_receita=CategoriaReceita.CALIBRACAO_NAO_RBC,
        perfil_no_evento=perfil,
        origem=OrigemTitulo.MANUAL,
        revision=0,
        criado_em=datetime.now(UTC),
    )
    DjangoTituloRepository().salvar_novo_titulo(titulo)
    return titulo


def _criar_prova(tenant, *, titulo_id, marco: str = "D30", dias_vencido: int = 50) -> None:
    """Prova de aviso (fail-closed perfil A — T-CR-044b). Dentro de run_in_tenant_context."""
    from src.infrastructure.contas_receber.models import NotificacaoInadimplencia

    NotificacaoInadimplencia.objects.create(
        tenant_id=tenant.id,
        titulo_id=titulo_id,
        cliente_referencia_hash=_hash_cliente(),
        marco=marco,
        dias_vencido=dias_vencido,
        perfil_no_evento="A",
    )


@pytest.mark.django_db(transaction=True)
def test_grace_perfil_a_fronteira_d44_fora_d46_dentro():
    """Perfil A: grace 45 dias. D+44 NÃO entra na régua; D+46 entra (INV-FIN-GRACE-PERFIL-001).
    Com prova de aviso (fail-closed) presente em ambos, isola a fronteira do GRACE."""
    tenant = TenantFactory(perfil_a=True)
    cli_44 = uuid4()
    cli_46 = uuid4()
    with run_in_tenant_context(tenant.id):
        t44 = _criar_titulo_vencido(tenant, dias_vencido=44, cliente_id=cli_44, perfil="A")
        t46 = _criar_titulo_vencido(tenant, dias_vencido=46, cliente_id=cli_46, perfil="A")
        _criar_prova(tenant, titulo_id=t44.titulo_id)  # fail-closed: precisa de prova
        _criar_prova(tenant, titulo_id=t46.titulo_id)
        items = TituloVencidoInadimplenciaSource._coletar_do_tenant(tenant)
    clientes = {i.cliente_id for i in items}
    assert cli_46 in clientes  # 46 > grace 45 → entra
    assert cli_44 not in clientes  # 44 < grace 45 → não entra


@pytest.mark.django_db(transaction=True)
def test_grace_perfil_d_curto_d10_entra():
    """Perfil D: grace 7 dias. D+10 entra (grace menor que perfil A)."""
    tenant = TenantFactory(perfil_d=True)
    cli = uuid4()
    with run_in_tenant_context(tenant.id):
        _criar_titulo_vencido(tenant, dias_vencido=10, cliente_id=cli, perfil="D")
        items = TituloVencidoInadimplenciaSource._coletar_do_tenant(tenant)
    assert cli in {i.cliente_id for i in items}


@pytest.mark.django_db(transaction=True)
def test_item_carrega_perfil_e_grace():
    """InadimplenciaItem estendido (PLAN-CR-01): perfil + grace_perfil preenchidos."""
    tenant = TenantFactory(perfil_a=True)
    cli = uuid4()
    with run_in_tenant_context(tenant.id):
        t = _criar_titulo_vencido(tenant, dias_vencido=50, cliente_id=cli, perfil="A")
        _criar_prova(tenant, titulo_id=t.titulo_id)  # fail-closed perfil A
        items = TituloVencidoInadimplenciaSource._coletar_do_tenant(tenant)
    item = next(i for i in items if i.cliente_id == cli)
    assert item.perfil == "A"
    assert item.grace_perfil == 45
    assert item.dias_vencido == 50


@pytest.mark.django_db(transaction=True)
def test_fail_closed_perfil_a_sem_aviso_nao_bloqueia():
    """FAIL-CLOSED CDC (T-CR-044b): perfil A vencido além do grace mas SEM prova de aviso
    → NÃO entra na régua de bloqueio. Com prova → entra."""
    tenant = TenantFactory(perfil_a=True)
    cli_sem = uuid4()
    cli_com = uuid4()
    with run_in_tenant_context(tenant.id):
        _criar_titulo_vencido(tenant, dias_vencido=60, cliente_id=cli_sem, perfil="A")
        t_com = _criar_titulo_vencido(tenant, dias_vencido=60, cliente_id=cli_com, perfil="A")
        _criar_prova(tenant, titulo_id=t_com.titulo_id)
        items = TituloVencidoInadimplenciaSource._coletar_do_tenant(tenant)
    clientes = {i.cliente_id for i in items}
    assert cli_sem not in clientes  # sem aviso → fail-closed barra o bloqueio
    assert cli_com in clientes  # com aviso → entra


@pytest.mark.django_db(transaction=True)
def test_fail_closed_nao_aplica_perfil_d():
    """Fail-closed é só perfil A; perfil D entra na régua sem prova (D-CR-22)."""
    tenant = TenantFactory(perfil_d=True)
    cli = uuid4()
    with run_in_tenant_context(tenant.id):
        _criar_titulo_vencido(tenant, dias_vencido=10, cliente_id=cli, perfil="D")
        items = TituloVencidoInadimplenciaSource._coletar_do_tenant(tenant)
    assert cli in {i.cliente_id for i in items}


@pytest.mark.django_db(transaction=True)
def test_cliente_anonimizado_fora_da_regua():
    """cliente_atual_id NULL (anonimizado LGPD) não entra na régua de bloqueio."""
    tenant = TenantFactory(perfil_d=True)
    with run_in_tenant_context(tenant.id):
        # título vencido bem além do grace, mas sem cliente_atual_id
        titulo = Titulo(
            titulo_id=uuid4(),
            tenant_id=tenant.id,
            cliente_referencia=ReferenciaPIIAnonimizavel(
                uuid_atual_id=None, hash_original=_hash_cliente(), key_id="v1"
            ),
            valor_original=Dinheiro(centavos=100000, moeda="BRL"),
            data_emissao=date.today() - timedelta(days=120),
            data_vencimento=date.today() - timedelta(days=90),
            estado=EstadoTitulo.VENCIDO,
            meio=MeioCobranca.BOLETO,
            categoria_receita=CategoriaReceita.CALIBRACAO_BASICA,
            perfil_no_evento="D",
            origem=OrigemTitulo.MANUAL,
            revision=0,
            criado_em=datetime.now(UTC),
        )
        DjangoTituloRepository().salvar_novo_titulo(titulo)
        items = TituloVencidoInadimplenciaSource._coletar_do_tenant(tenant)
    assert items == []


@pytest.mark.django_db(transaction=True)
def test_grace_period_inadimplencia_por_perfil_le_tenant():
    tenant_a = TenantFactory(perfil_a=True)
    tenant_d = TenantFactory(perfil_d=True)
    assert grace_period_inadimplencia_por_perfil(tenant_a.id) == 45
    assert grace_period_inadimplencia_por_perfil(tenant_d.id) == 7


@pytest.mark.django_db(transaction=True)
def test_iter_inadimplentes_materializa_lista():
    """iter_inadimplentes_90d retorna iterator sobre lista (sem contexto aninhado)."""
    tenant = TenantFactory(perfil_b=True)
    cli = uuid4()
    with run_in_tenant_context(tenant.id):
        _criar_titulo_vencido(tenant, dias_vencido=30, cliente_id=cli, perfil="B")
    # Chamado FORA de contexto (como o job faz) — itera tenants internamente.
    items = list(TituloVencidoInadimplenciaSource().iter_inadimplentes_90d())
    assert any(i.cliente_id == cli for i in items)


def test_source_lista_interim_aceita_campos_novos():
    """PLAN-CR-01: SourceListaInterim entrega perfil/grace_perfil sem quebrar."""
    from src.infrastructure.clientes.inadimplencia import SourceListaInterim

    fonte = [
        {
            "tenant_id": str(uuid4()),
            "cliente_id": str(uuid4()),
            "dias_vencido": 95,
            "causation_titulo_id": str(uuid4()),
            "perfil": "A",
            "grace_perfil": 45,
        }
    ]
    with override_settings(INADIMPLENCIA_FONTE_INTERIM=fonte):
        items = list(SourceListaInterim().iter_inadimplentes_90d())
    assert len(items) == 1
    assert items[0].perfil == "A"
    assert items[0].grace_perfil == 45


def test_source_lista_interim_sem_campos_novos_default_none():
    """Deploy parcial: dict sem perfil/grace_perfil → defaults None (não quebra)."""
    from src.infrastructure.clientes.inadimplencia import SourceListaInterim

    fonte = [
        {
            "tenant_id": str(uuid4()),
            "cliente_id": str(uuid4()),
            "dias_vencido": 95,
            "causation_titulo_id": str(uuid4()),
        }
    ]
    with override_settings(INADIMPLENCIA_FONTE_INTERIM=fonte):
        items = list(SourceListaInterim().iter_inadimplentes_90d())
    assert items[0].perfil is None
    assert items[0].grace_perfil is None


@pytest.mark.django_db(transaction=True)
def test_get_source_parametrizado_por_settings():
    from src.infrastructure.clientes.inadimplencia import SourceListaInterim, get_source

    with override_settings(INADIMPLENCIA_SOURCE_IMPL="contas_receber"):
        assert isinstance(get_source(), TituloVencidoInadimplenciaSource)
    with override_settings(INADIMPLENCIA_SOURCE_IMPL="interim"):
        assert isinstance(get_source(), SourceListaInterim)


# ============================================================
# T-CR-044 — notificação D+30/D+45 perfil A (Caminho C)
# ============================================================


def _criar_cliente(tenant, *, email: str):
    from src.infrastructure.clientes.models import Cliente, TipoPessoa

    return Cliente.objects.create(
        tenant=tenant,
        tipo_pessoa=TipoPessoa.PJ,
        documento="11222333000181",
        nome="Cliente Teste Inadimplencia",
        email=email,
        aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
    )


def _rodar_job(tenant) -> int:
    from src.infrastructure.contas_receber.management.commands.job_notificar_inadimplencia import (
        Command,
    )

    with run_in_tenant_context(tenant.id):
        return Command()._por_tenant(tenant, dry=False)


def test_montar_aviso_puro():
    """Unit: montar_aviso produz assunto/corpo provisório com os campos (sem DB)."""
    from datetime import date as _date

    from src.application.contas_receber.notificar_inadimplencia import (
        TituloVencidoInfo,
        marco_de_dias_vencido,
        montar_aviso,
    )

    assert marco_de_dias_vencido(29) is None
    assert marco_de_dias_vencido(30) == "D30"
    assert marco_de_dias_vencido(44) == "D30"  # janela D30 (re-disparo robusto)
    assert marco_de_dias_vencido(45) == "D45"
    assert marco_de_dias_vencido(60) == "D45"

    aviso = montar_aviso(
        tenant_nome="Lab Exemplo",
        titulos=[
            TituloVencidoInfo(
                titulo_id=uuid4(),
                valor_centavos=150000,
                data_vencimento=_date(2026, 5, 1),
                dias_vencido=30,
            )
        ],
        marco="D30",
        grace_perfil=45,
        canal_regularizacao_url="https://exemplo/regularizar",
    )
    assert "Lab Exemplo" in aviso.assunto
    assert "MINUTA PROVISÓRIA" in aviso.corpo
    assert "https://exemplo/regularizar" in aviso.corpo
    assert "R$ 1500,00" in aviso.corpo
    assert aviso.data_bloqueio_prevista == _date(2026, 6, 15)  # 1 maio + 45 dias


@pytest.mark.django_db(transaction=True)
def test_notificacao_d30_perfil_a_email_ao_cliente():
    from django.core import mail

    mail.outbox.clear()
    tenant = TenantFactory(perfil_a=True, nome_fantasia="Laboratorio Alfa")
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant, email="devedor@cliente.local")
        _criar_titulo_vencido(tenant, dias_vencido=30, cliente_id=cliente.id, perfil="A")
    enviados = _rodar_job(tenant)
    assert enviados == 1
    assert len(mail.outbox) >= 1
    msg = mail.outbox[0]
    assert "devedor@cliente.local" in msg.to
    assert "Laboratorio Alfa" in msg.from_email  # remetente = tenant (Caminho C)
    assert "Laboratorio Alfa" in msg.subject


@pytest.mark.django_db(transaction=True)
def test_notificacao_evento_sem_email_minimizacao():
    """Minimização (D-CR-19): o evento carrega cliente_referencia_hash, NUNCA o e-mail."""
    from django.core import mail

    mail.outbox.clear()
    tenant = TenantFactory(perfil_a=True, nome_fantasia="Lab Beta")
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant, email="segredo@cliente.local")
        _criar_titulo_vencido(tenant, dias_vencido=45, cliente_id=cliente.id, perfil="A")
    _rodar_job(tenant)
    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT envelope_jsonb::text FROM bus_outbox WHERE acao = %s",
                ["contas_receber.inadimplencia_dura_atingida"],
            )
            rows = [r[0] for r in cur.fetchall()]
    assert rows, "evento de inadimplência não publicado"
    blob = " ".join(rows)
    assert "segredo@cliente.local" not in blob  # e-mail NUNCA no evento
    assert "cliente_referencia_hash" in blob


@pytest.mark.django_db(transaction=True)
def test_notificacao_perfil_b_nao_envia():
    from django.core import mail

    mail.outbox.clear()
    tenant = TenantFactory(perfil_b=True)
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant, email="b@cliente.local")
        _criar_titulo_vencido(tenant, dias_vencido=30, cliente_id=cliente.id, perfil="B")
    enviados = _rodar_job(tenant)
    assert enviados == 0
    assert mail.outbox == []


@pytest.mark.django_db(transaction=True)
def test_notificacao_dia_fora_marco_nao_envia():
    from django.core import mail

    mail.outbox.clear()
    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant, email="x@cliente.local")
        # 20 dias < janela D30 → nada a notificar
        _criar_titulo_vencido(tenant, dias_vencido=20, cliente_id=cliente.id, perfil="A")
    enviados = _rodar_job(tenant)
    assert enviados == 0


@pytest.mark.django_db(transaction=True)
def test_notificacao_evento_payload_rico_para_tenant():
    """Aviso ao admin/tenant = evento inadimplencia_dura_atingida com payload rico
    (titulos_vencidos + data_bloqueio_prevista + canal_regularizacao_url — D-CR-9).
    `usuario_perfil_tenant` é self-select (RLS): job de sistema não lista admins por
    query → o evento é o canal canônico (consumido pelo painel/CRM do tenant)."""
    import json as _json

    tenant = TenantFactory(perfil_a=True, nome_fantasia="Lab Gama")
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant, email="cli@cliente.local")
        _criar_titulo_vencido(tenant, dias_vencido=30, cliente_id=cliente.id, perfil="A")
    _rodar_job(tenant)
    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT envelope_jsonb FROM bus_outbox WHERE acao = %s",
                ["contas_receber.inadimplencia_dura_atingida"],
            )
            row = cur.fetchone()
    assert row is not None
    env = row[0] if isinstance(row[0], dict) else _json.loads(row[0])
    payload = env["payload"]
    assert payload["marco"] == "D30"
    assert payload["titulos_vencidos"]  # lista não-vazia
    assert "data_bloqueio_prevista" in payload
    assert "canal_regularizacao_url" in payload


@pytest.mark.django_db(transaction=True)
def test_notificacao_resiliente_a_falha_smtp():
    """SMTP indisponível → job loga e NÃO derruba; e (fail-closed) NÃO grava prova."""
    from unittest.mock import patch

    from django.core import mail
    from django.core.mail import EmailMessage
    from src.infrastructure.contas_receber.models import NotificacaoInadimplencia

    mail.outbox.clear()
    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant, email="falha@cliente.local")
        _criar_titulo_vencido(tenant, dias_vencido=30, cliente_id=cliente.id, perfil="A")
    with patch.object(EmailMessage, "send", side_effect=Exception("smtp down")):
        enviados = _rodar_job(tenant)  # não levanta
    assert enviados == 0  # SMTP falhou → nada confirmado
    with run_in_tenant_context(tenant.id):
        # prova = aviso REAL: sem envio, sem prova (não pode bloquear sem avisar)
        assert not NotificacaoInadimplencia.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_notificacao_registra_prova_de_envio():
    from django.core import mail
    from src.infrastructure.contas_receber.models import NotificacaoInadimplencia

    mail.outbox.clear()
    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant, email="prova@cliente.local")
        t = _criar_titulo_vencido(tenant, dias_vencido=30, cliente_id=cliente.id, perfil="A")
    _rodar_job(tenant)
    with run_in_tenant_context(tenant.id):
        prova = NotificacaoInadimplencia.objects.filter(
            titulo_id=t.titulo_id, marco="D30"
        ).first()
    assert prova is not None
    assert "prova@cliente.local" not in prova.cliente_referencia_hash  # sem e-mail na prova


@pytest.mark.django_db(transaction=True)
def test_notificacao_idempotente_nao_reenvia_marco():
    from django.core import mail
    from src.infrastructure.contas_receber.models import NotificacaoInadimplencia

    mail.outbox.clear()
    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        cliente = _criar_cliente(tenant, email="idem@cliente.local")
        t = _criar_titulo_vencido(tenant, dias_vencido=30, cliente_id=cliente.id, perfil="A")
    n1 = _rodar_job(tenant)
    n2 = _rodar_job(tenant)  # prova já existe → não reenvia o marco D30
    assert n1 == 1
    assert n2 == 0
    with run_in_tenant_context(tenant.id):
        assert (
            NotificacaoInadimplencia.objects.filter(titulo_id=t.titulo_id, marco="D30").count()
            == 1
        )


@pytest.mark.django_db(transaction=True)
def test_notificacao_inadimplencia_insert_only():
    """INV-CR-NOTIF-WORM: NotificacaoInadimplencia é INSERT-only (block-update/delete)."""
    from django.db import transaction as _tx
    from src.infrastructure.contas_receber.models import NotificacaoInadimplencia

    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        t = _criar_titulo_vencido(tenant, dias_vencido=50, cliente_id=uuid4(), perfil="A")
        _criar_prova(tenant, titulo_id=t.titulo_id, marco="D45")
        prova = NotificacaoInadimplencia.objects.filter(titulo_id=t.titulo_id).first()
        assert prova is not None
        with pytest.raises(DatabaseError), _tx.atomic():
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE notificacao_inadimplencia SET marco='D30' WHERE id=%s",
                    [str(prova.id)],
                )
        with pytest.raises(DatabaseError), _tx.atomic():
            with connection.cursor() as cur:
                cur.execute(
                    "DELETE FROM notificacao_inadimplencia WHERE id=%s", [str(prova.id)]
                )


def test_inadimplencia_item_default_none_isinstance():
    """InadimplenciaItem mantém compat: 4 campos obrigatórios + 2 opcionais."""
    item = InadimplenciaItem(
        tenant_id=UUID(int=1),
        cliente_id=UUID(int=2),
        dias_vencido=95,
        causation_titulo_id=UUID(int=3),
    )
    assert item.perfil is None
    assert item.grace_perfil is None
