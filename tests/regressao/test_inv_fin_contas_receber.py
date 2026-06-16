"""Testes de regressão de invariante — módulo `contas-receber` (TST-004 / P9).

Uma função por INV crítica, com o ID literal no nome. Cada teste EXERCE A BARREIRA REAL
e falha se a barreira for removida.

INVs cobertas:
  INV-FIN-GW-001        — webhook idempotente por gateway_event_id
  INV-FIN-GW-002        — pix_recorrente exige convenio_pix_id (CHECK constraint)
  INV-FIN-PERFIL-001    — CALIBRACAO_RBC só perfil A (domínio puro)
  INV-FIN-GRACE-PERFIL-001 — grace por perfil A=45/B=20/C=30/D=7 (domínio puro)
  INV-FIN-SNAPSHOT-PERFIL-001 — perfil_no_evento imutável (trigger 0003)
  INV-FIN-REATIV-001    — desbloqueio ao quitar (consumer contas_receber.pago)
  INV-FIN-INAD-001      — separação cliente×tenant (hook estático)
  INV-CR-OS-TITULO-UNICO  — UNIQUE(tenant,os_id_origem) WHERE estado!=cancelado
  INV-CR-PAGAMENTO-WORM   — Pagamento INSERT-only (trigger 0003)
  INV-CR-OVERRIDE-WORM    — OverrideBloqueio INSERT-only (trigger 0003)
  INV-CR-OVERRIDE-ANTI-PII — justificativa sem PII (validação de domínio)
  INV-CR-WEBHOOK-PAYLOAD-MINIMO — Pagamento não persiste PII do pagador (introspecção)
  INV-FIS-CR-001          — consumer de criação de título registrado em os.concluida
"""

from __future__ import annotations

import subprocess
import uuid
import zlib
from datetime import date, timedelta
from uuid import uuid4

import pytest
from django.db import DatabaseError, IntegrityError

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory

# ---------------------------------------------------------------------------
# Constantes e helpers compartilhados
# ---------------------------------------------------------------------------

_DATA_HOJE = date.today()
_HASH = "b" * 64  # HMAC hex válido (≥32 chars)
_KEY_ID = "v1"
_DBS = ["default", "breaker_writer"]
_VENCIMENTO = _DATA_HOJE + timedelta(days=30)
_VENCIMENTO_ISO = _VENCIMENTO.isoformat()


def _cria_titulo_db(
    tenant,
    *,
    estado: str = "emitido",
    meio: str = "boleto",
    os_id: uuid.UUID | None = None,
    convenio_pix_id: str = "",
):
    """Insere um Titulo diretamente via ORM (dentro de run_in_tenant_context do chamador)."""
    from src.infrastructure.contas_receber.models import Titulo

    return Titulo.objects.create(
        tenant=tenant,
        cliente_atual_id=uuid4(),
        cliente_referencia_hash=_HASH,
        cliente_key_id=_KEY_ID,
        valor_original=10000,
        data_emissao=_DATA_HOJE,
        data_vencimento=_DATA_HOJE,
        estado=estado,
        meio=meio,
        categoria_receita="OUTROS",
        perfil_no_evento="A",
        origem="manual",
        os_id_origem=os_id,
        convenio_pix_id=convenio_pix_id,
    )


def _cria_pagamento_db(tenant, titulo):
    """Insere um Pagamento diretamente via ORM (dentro de run_in_tenant_context do chamador)."""
    from src.infrastructure.contas_receber.models import Pagamento

    return Pagamento.objects.create(
        tenant=tenant,
        titulo=titulo,
        valor=10000,
        data=_DATA_HOJE,
        origem="manual",
        valor_atualizado_snapshot_em_pagamento=10000,
    )


def _cria_override_db(tenant, titulo):
    """Insere um OverrideBloqueio diretamente via ORM (dentro de run_in_tenant_context)."""
    from src.infrastructure.contas_receber.models import OverrideBloqueio

    return OverrideBloqueio.objects.create(
        tenant=tenant,
        titulo=titulo,
        cliente_id=uuid4(),
        novo_prazo_max_dias=30,
        justificativa="J" * 100,
        a3_signature_id="stub-wave-a",
        usuario_id=uuid4(),
        perfil_no_evento="A",
    )


def _autenticar(client, usuario, tenant) -> None:
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
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


def _cenario_perfil_a():
    from src.infrastructure.authz.django_provider import invalidate_user_cache

    sfx = uuid4().hex[:8]
    tenant = TenantFactory(perfil_a=True, slug=f"inv-cr-{sfx}")
    admin = UsuarioFactory(email=f"adm-inv-{sfx}@cr.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)
    return {"tenant": tenant, "admin": admin}


def _gateway_id_mock(titulo_id, meio: str = "boleto") -> str:
    """Reproduz _gateway_id_deterministico do MockPaymentGatewayProvider."""
    base = f"{titulo_id}|{meio}|{_VENCIMENTO.isoformat()}"
    crc = zlib.crc32(base.encode("utf-8")) & 0xFFFFFFFF
    return f"MOCK-{crc:08x}"


def _criar_titulo_e_emitir(tenant, admin):
    """Cria título via REST e emite boleto (para ter gateway_externo_id setado)."""
    from rest_framework.test import APIClient

    client = APIClient()
    _autenticar(client, admin, tenant)

    resp = client.post(
        "/api/v1/contas-receber/criar/",
        {
            "cliente_referencia_hash": uuid4().hex,
            "cliente_key_id": "v1",
            "valor_centavos": 8000,
            "data_vencimento": _VENCIMENTO_ISO,
            "meio": "boleto",
            "categoria_receita": "CALIBRACAO_RBC",
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert resp.status_code == 201, f"criar falhou: {resp.data}"
    titulo_id = resp.data["titulo_id"]

    resp2 = client.post(
        f"/api/v1/contas-receber/{titulo_id}/emitir-boleto/",
        {},
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert resp2.status_code == 201, f"emitir-boleto falhou: {resp2.data}"
    gateway_externo_id = resp2.data.get("gateway_externo_id")
    assert gateway_externo_id, "emitir-boleto não retornou gateway_externo_id"
    return titulo_id, gateway_externo_id


def _payload_webhook(gateway_event_id: str, titulo_gw_id: str, centavos: int = 8000) -> bytes:
    return f"{gateway_event_id}|{titulo_gw_id}|{centavos}|{date.today().isoformat()}".encode()


def _post_webhook(payload: bytes, signature: str = "mock-sig-valida"):
    from rest_framework.test import APIClient

    client = APIClient()
    return client.post(
        "/api/v1/public/contas-receber/webhook/",
        data=payload,
        content_type="application/octet-stream",
        HTTP_X_GATEWAY_SIGNATURE=signature,
    )


# ===========================================================================
# INV-FIN-GW-001 — webhook idempotente por gateway_event_id
# ===========================================================================


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_inv_fin_gw_001_webhook_replay_nao_cria_pagamento_duplicado():
    """INV-FIN-GW-001: replay do mesmo gateway_event_id não cria 2º Pagamento.

    Barreira: UNIQUE(gateway_event_id) via `@consumer_idempotente` + SELECT EXISTS
    no use case `processar_webhook_pagamento`. O replay retorna 200 mas NÃO insere
    novo registro em `pagamento_titulo`.
    """
    from src.infrastructure.contas_receber.models import Pagamento as PagamentoModel
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    ctx = _cenario_perfil_a()
    titulo_id, gateway_externo_id = _criar_titulo_e_emitir(ctx["tenant"], ctx["admin"])

    event_id = f"evt-inv-gw001-{uuid4().hex[:10]}"
    payload = _payload_webhook(event_id, gateway_externo_id)

    resp1 = _post_webhook(payload, signature="sig-valida")
    resp2 = _post_webhook(payload, signature="sig-valida")  # replay

    assert resp1.status_code == 200, f"1ª chamada falhou: {resp1.status_code} {resp1.data}"
    assert resp2.status_code == 200, f"2ª chamada (replay) falhou: {resp2.status_code} {resp2.data}"

    with run_in_tenant_context(ctx["tenant"].id):
        contagem = PagamentoModel.objects.filter(titulo_id=titulo_id).count()

    assert contagem == 1, (
        f"INV-FIN-GW-001 violado: {contagem} Pagamentos criados para o mesmo "
        f"gateway_event_id={event_id!r} (esperava 1)"
    )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_inv_fin_gw_001_pagamento_gateway_event_unico_resistente_a_corrida():
    """INV-FIN-GW-001 (P9 MÉDIO-1): UniqueConstraint parcial `uq_cr_pagamento_gateway_event`
    é a defesa de BANCO contra o TOCTOU do check-then-act sob concorrência — 2 Pagamentos
    com o MESMO gateway_event_id (não-vazio) são barrados. A constraint é PARCIAL: pagamentos
    manuais (gateway_event_id="") NÃO colidem entre si.
    """
    from django.db import transaction as _tx
    from src.infrastructure.contas_receber.models import Pagamento
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory(perfil_a=True)
    with run_in_tenant_context(tenant.id):
        titulo = _cria_titulo_db(tenant)
        ev = f"evt-corrida-{uuid4().hex[:10]}"
        Pagamento.objects.create(
            tenant=tenant,
            titulo=titulo,
            valor=8000,
            data=_DATA_HOJE,
            origem="webhook_gateway",
            valor_atualizado_snapshot_em_pagamento=8000,
            gateway_event_id=ev,
        )
        # 2º Pagamento com o MESMO gateway_event_id → barrado pela constraint
        with pytest.raises(IntegrityError), _tx.atomic():
            Pagamento.objects.create(
                tenant=tenant,
                titulo=titulo,
                valor=8000,
                data=_DATA_HOJE,
                origem="webhook_gateway",
                valor_atualizado_snapshot_em_pagamento=8000,
                gateway_event_id=ev,
            )
        # Parcial: 2 pagamentos manuais (gateway_event_id="" default) NÃO colidem
        _cria_pagamento_db(tenant, titulo)
        _cria_pagamento_db(tenant, titulo)
        manuais = Pagamento.objects.filter(titulo=titulo, gateway_event_id="").count()
    assert manuais == 2, f"constraint parcial barrou pagamentos manuais (got {manuais}, esperava 2)"


# ===========================================================================
# INV-FIN-GW-002 — pix_recorrente exige convenio_pix_id
# ===========================================================================


@pytest.mark.django_db(transaction=True)
def test_inv_fin_gw_002_pix_recorrente_exige_convenio():
    """INV-FIN-GW-002: CHECK constraint `chk_cr_titulo_pix_recorrente_convenio`.

    INSERT de Titulo com meio=pix_recorrente e convenio_pix_id vazio →
    IntegrityError (violação de CHECK no PG). Barreira: migration 0001_initial.
    """
    from src.infrastructure.contas_receber.models import Titulo
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        Titulo.objects.create(
            tenant=tenant,
            cliente_atual_id=uuid4(),
            cliente_referencia_hash=_HASH,
            cliente_key_id=_KEY_ID,
            valor_original=10000,
            data_emissao=_DATA_HOJE,
            data_vencimento=_DATA_HOJE,
            estado="emitido",
            meio="pix_recorrente",
            categoria_receita="OUTROS",
            perfil_no_evento="A",
            origem="manual",
            convenio_pix_id="",  # violação: pix_recorrente sem convênio
        )


# ===========================================================================
# INV-FIN-PERFIL-001 — CALIBRACAO_RBC só perfil A (domínio puro)
# ===========================================================================


def test_inv_fin_perfil_001_calibracao_rbc_exige_perfil_a():
    """INV-FIN-PERFIL-001: `categoria_permitida(CALIBRACAO_RBC, 'B')` levanta.

    Barreira pura de domínio em `src/domain/contas_receber/categoria.py`.
    Sem banco — teste puro de função.
    """
    from src.domain.contas_receber.categoria import categoria_permitida
    from src.domain.contas_receber.enums import CategoriaReceita
    from src.domain.contas_receber.erros import CategoriaReceitaExigePerfilA

    for perfil_nao_a in ("B", "C", "D"):
        with pytest.raises(CategoriaReceitaExigePerfilA):
            categoria_permitida(CategoriaReceita.CALIBRACAO_RBC, perfil_nao_a)


def test_inv_fin_perfil_001_calibracao_rbc_permitida_perfil_a():
    """INV-FIN-PERFIL-001 (happy): `categoria_permitida(CALIBRACAO_RBC, 'A')` → True."""
    from src.domain.contas_receber.categoria import categoria_permitida
    from src.domain.contas_receber.enums import CategoriaReceita

    assert categoria_permitida(CategoriaReceita.CALIBRACAO_RBC, "A") is True


# ===========================================================================
# INV-FIN-GRACE-PERFIL-001 — grace por perfil A=45/B=20/C=30/D=7
# ===========================================================================


def test_inv_fin_grace_perfil_001_valores_por_perfil():
    """INV-FIN-GRACE-PERFIL-001: `grace_period_por_perfil` retorna dias corretos.

    Barreira pura de domínio em `src/domain/contas_receber/grace.py`. Sem banco.
    Valores da spec §3 D-CR-9: A=45, B=20, C=30, D=7.
    """
    from src.domain.contas_receber.grace import grace_period_por_perfil

    esperados = {"A": 45, "B": 20, "C": 30, "D": 7}
    for perfil, dias in esperados.items():
        resultado = grace_period_por_perfil(perfil)
        assert resultado == dias, (
            f"INV-FIN-GRACE-PERFIL-001 violado: perfil={perfil!r} "
            f"esperava {dias}, got {resultado}"
        )


def test_inv_fin_grace_perfil_001_perfil_desconhecido_fail_closed():
    """INV-FIN-GRACE-PERFIL-001 (fail-closed): perfil desconhecido levanta PerfilIndeterminado."""
    from src.domain.contas_receber.erros import PerfilIndeterminado
    from src.domain.contas_receber.grace import grace_period_por_perfil

    with pytest.raises(PerfilIndeterminado):
        grace_period_por_perfil("X")


# ===========================================================================
# INV-FIN-SNAPSHOT-PERFIL-001 — perfil_no_evento imutável (trigger 0003)
# ===========================================================================


@pytest.mark.django_db(transaction=True)
def test_inv_fin_snapshot_perfil_001_perfil_no_evento_imutavel():
    """INV-FIN-SNAPSHOT-PERFIL-001: UPDATE de perfil_no_evento num Titulo → DatabaseError.

    Barreira: trigger WORM `titulo_receber_worm_check` (migration 0003).
    Campo `perfil_no_evento` listado nos campos imutáveis do trigger.
    """
    from src.infrastructure.contas_receber.models import Titulo
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        titulo = _cria_titulo_db(tenant)

    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Titulo.objects.filter(id=titulo.id).update(perfil_no_evento="B")


# ===========================================================================
# INV-FIN-REATIV-001 — desbloqueio ao quitar (consumer contas_receber.pago)
# ===========================================================================


@pytest.mark.django_db(transaction=True)
def test_inv_fin_reativ_001_desbloqueio_ao_quitar_inadimplencia():
    """INV-FIN-REATIV-001: quitação de única dívida vencida encerra bloqueio automático.

    Barreira: consumer `handle_contas_receber_pago` em
    `src/infrastructure/clientes/consumers/contas_receber_eventos.py`. Quando não há
    outra vencida em aberto, o `ClienteBloqueio` de motivo `automatico_inadimplencia_90d`
    é encerrado e evento `cliente.desbloqueado` é publicado.
    """
    import json as _json
    from datetime import UTC, datetime

    from django.db import connection as dj_conn
    from src.domain.contas_receber.entities import Titulo as TituloDomain
    from src.domain.contas_receber.enums import (
        CategoriaReceita,
        EstadoTitulo,
        MeioCobranca,
        OrigemTitulo,
    )
    from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel
    from src.infrastructure.clientes.bloqueio import (
        CAUSATION_TITULO_VENCIDO,
        MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
    )
    from src.infrastructure.clientes.consumers.contas_receber_eventos import (
        handle_contas_receber_pago,
    )
    from src.infrastructure.clientes.models import Cliente, ClienteBloqueio, TipoPessoa
    from src.infrastructure.contas_receber.repositories import DjangoTituloRepository
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory(perfil_a=True)

    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Teste INV-FIN-REATIV-001",
            email="reativ001@test.local",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        bloqueio = ClienteBloqueio.objects.create(
            cliente=cliente,
            tenant=tenant,
            motivo_categoria=MOTIVO_AUTOMATICO_INADIMPLENCIA_90D,
            motivo_observacao="",
            justificativa_bruta="bloqueio de teste para invariante INV-FIN-REATIV-001 (>=30 chars)",
            causation_type=CAUSATION_TITULO_VENCIDO,
            confirmacao_comunicacao_previa=True,
            bloqueado_por_usuario_id=None,
        )
        # Única dívida do cliente — já quitada.
        titulo_domain = TituloDomain(
            titulo_id=uuid4(),
            tenant_id=tenant.id,
            cliente_referencia=ReferenciaPIIAnonimizavel(
                uuid_atual_id=cliente.id,
                hash_original=uuid4().hex + uuid4().hex,
                key_id="v1",
            ),
            valor_original=Dinheiro(centavos=100000, moeda="BRL"),
            data_emissao=_DATA_HOJE - timedelta(days=90),
            data_vencimento=_DATA_HOJE - timedelta(days=60),
            estado=EstadoTitulo.PAGO,
            meio=MeioCobranca.BOLETO,
            categoria_receita=CategoriaReceita.CALIBRACAO_NAO_RBC,
            perfil_no_evento="A",
            origem=OrigemTitulo.MANUAL,
            revision=0,
            criado_em=datetime.now(UTC),
        )
        DjangoTituloRepository().salvar_novo_titulo(titulo_domain)

    # Roda o consumer que encerra o bloqueio.
    envelope = {
        "event_id": str(uuid4()),
        "tenant_id": str(tenant.id),
        "acao": "contas_receber.pago",
        "payload": {"titulo_id": str(titulo_domain.titulo_id), "novo_estado": "pago"},
    }
    with run_in_tenant_context(tenant.id):
        handle_contas_receber_pago(envelope)

    with run_in_tenant_context(tenant.id):
        recarregado = ClienteBloqueio.objects.get(id=bloqueio.id)
        with dj_conn.cursor() as cur:
            cur.execute(
                "SELECT envelope_jsonb FROM bus_outbox WHERE acao = %s",
                ["cliente.desbloqueado"],
            )
            rows = cur.fetchall()

    assert recarregado.desbloqueado_em is not None, (
        "INV-FIN-REATIV-001 violado: bloqueio não foi encerrado após quitação da única dívida"
    )
    assert recarregado.desbloqueado_motivo == "pagamento_quitou_inadimplencia", (
        f"motivo inesperado: {recarregado.desbloqueado_motivo!r}"
    )
    assert len(rows) == 1, (
        f"INV-FIN-REATIV-001: esperava 1 evento cliente.desbloqueado, got {len(rows)}"
    )
    payload_evt = rows[0][0] if isinstance(rows[0][0], dict) else _json.loads(rows[0][0])
    assert payload_evt["payload"]["cliente_id"] == str(cliente.id)


# ===========================================================================
# INV-FIN-INAD-001 — separação cliente×tenant (hook estático)
# ===========================================================================


def test_inv_fin_inad_001_hook_bloqueia_billing_saas_em_contas_receber():
    """INV-FIN-INAD-001: hook `policy-tenant-vs-cliente.sh` rejeita referência a `BillingSaas`.

    Barreira: script `.claude/hooks/policy-tenant-vs-cliente.sh`. Recebe JSON com
    `tool_input.content` contendo `BillingSaas` em arquivo de path `contas_receber` →
    exit code 2 (bloqueio). Arquivo de teste (`tests/`) → exit code 0 (auto-allow).
    """
    import json
    import os

    hook_path = os.path.join(
        os.path.dirname(__file__),  # tests/regressao/
        "..", "..",
        ".claude", "hooks", "policy-tenant-vs-cliente.sh",
    )
    hook_path = os.path.abspath(hook_path)

    # Cenário 1: código proibido em path contas_receber → exit 2.
    payload_block = json.dumps({
        "tool_input": {
            "file_path": "src/infrastructure/contas_receber/somemodule.py",
            "content": "from src.infrastructure.billing_saas.models import BillingSaas\n",
        }
    })
    result_block = subprocess.run(  # -- hook_path e abspath fixo; input e JSON constante do teste, sem entrada do usuario
        ["bash", hook_path],
        input=payload_block,
        capture_output=True,
        text=True,
    )
    assert result_block.returncode == 2, (
        f"INV-FIN-INAD-001: hook deveria bloquear (exit 2) referência a BillingSaas "
        f"em contas_receber, got exit={result_block.returncode}\n"
        f"stderr: {result_block.stderr}"
    )

    # Cenário 2: mesmo conteúdo em path de tests → auto-allow (exit 0).
    payload_allow = json.dumps({
        "tool_input": {
            "file_path": "tests/test_contas_receber_foo.py",
            "content": "from src.infrastructure.billing_saas.models import BillingSaas\n",
        }
    })
    result_allow = subprocess.run(  # -- hook_path e abspath fixo; input e JSON constante do teste, sem entrada do usuario
        ["bash", hook_path],
        input=payload_allow,
        capture_output=True,
        text=True,
    )
    assert result_allow.returncode == 0, (
        f"INV-FIN-INAD-001: hook NÃO deveria bloquear arquivo de tests, "
        f"got exit={result_allow.returncode}"
    )

    # Cenário 3: StatusLifecycle (legítimo, plano-de-controle do tenant) → exit 0.
    payload_ok = json.dumps({
        "tool_input": {
            "file_path": "src/infrastructure/contas_receber/consumers/os_eventos.py",
            "content": "from src.infrastructure.tenant.models import StatusLifecycle, Tenant\n",
        }
    })
    result_ok = subprocess.run(  # -- hook_path e abspath fixo; input e JSON constante do teste, sem entrada do usuario
        ["bash", hook_path],
        input=payload_ok,
        capture_output=True,
        text=True,
    )
    assert result_ok.returncode == 0, (
        f"INV-FIN-INAD-001: StatusLifecycle é legítimo, não deve bloquear. "
        f"exit={result_ok.returncode}"
    )


# ===========================================================================
# INV-CR-OS-TITULO-UNICO — UNIQUE(tenant,os_id_origem) WHERE estado!=cancelado
# ===========================================================================


@pytest.mark.django_db(transaction=True)
def test_inv_cr_os_titulo_unico_dois_ativos_mesma_os_raise():
    """INV-CR-OS-TITULO-UNICO: 2 títulos ativos para a mesma OS → IntegrityError.

    Barreira: UNIQUE parcial `uq_cr_titulo_os_ativo` (migration 0001) —
    `UNIQUE(tenant_id, os_id_origem) WHERE estado != 'cancelado'`.
    """
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    os_id = uuid4()

    with run_in_tenant_context(tenant.id):
        _cria_titulo_db(tenant, os_id=os_id)  # 1º título ativo

    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        _cria_titulo_db(tenant, os_id=os_id)  # 2º título ativo — deve falhar


@pytest.mark.django_db(transaction=True)
def test_inv_cr_os_titulo_unico_permite_novo_apos_cancelar():
    """INV-CR-OS-TITULO-UNICO (happy): título cancelado não conta para o UNIQUE parcial."""
    from src.infrastructure.contas_receber.models import Titulo
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    os_id = uuid4()

    with run_in_tenant_context(tenant.id):
        t1 = _cria_titulo_db(tenant, os_id=os_id)
        Titulo.objects.filter(id=t1.id).update(estado="cancelado")

    with run_in_tenant_context(tenant.id):
        t2 = _cria_titulo_db(tenant, os_id=os_id)  # agora deve funcionar

    assert t2.id != t1.id


# ===========================================================================
# INV-CR-PAGAMENTO-WORM — Pagamento INSERT-only (trigger 0003)
# ===========================================================================


@pytest.mark.django_db(transaction=True)
def test_inv_cr_pagamento_worm_insert_only_update_raise():
    """INV-CR-PAGAMENTO-WORM: UPDATE em pagamento_titulo → DatabaseError.

    Barreira: trigger `pagamento_titulo_block_update` (migration 0003 — Padrão B
    INSERT-only). Qualquer UPDATE no modelo Pagamento levanta exceção do PG.
    """
    from src.infrastructure.contas_receber.models import Pagamento
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        titulo = _cria_titulo_db(tenant)
        pagamento = _cria_pagamento_db(tenant, titulo)

    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Pagamento.objects.filter(id=pagamento.id).update(valor=1)


@pytest.mark.django_db(transaction=True)
def test_inv_cr_pagamento_worm_insert_only_delete_raise():
    """INV-CR-PAGAMENTO-WORM: DELETE em pagamento_titulo → DatabaseError.

    Barreira: trigger `pagamento_titulo_block_delete` (migration 0003).
    """
    from src.infrastructure.contas_receber.models import Pagamento
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        titulo = _cria_titulo_db(tenant)
        pagamento = _cria_pagamento_db(tenant, titulo)

    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Pagamento.objects.filter(id=pagamento.id).delete()


# ===========================================================================
# INV-CR-OVERRIDE-WORM — OverrideBloqueio INSERT-only (trigger 0003)
# ===========================================================================


@pytest.mark.django_db(transaction=True)
def test_inv_cr_override_worm_insert_only_update_raise():
    """INV-CR-OVERRIDE-WORM: UPDATE em override_bloqueio → DatabaseError.

    Barreira: trigger `override_bloqueio_block_update` (migration 0003 — Padrão B
    INSERT-only). Qualquer UPDATE no modelo OverrideBloqueio levanta exceção do PG.
    """
    from src.infrastructure.contas_receber.models import OverrideBloqueio
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        titulo = _cria_titulo_db(tenant)
        override = _cria_override_db(tenant, titulo)

    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        OverrideBloqueio.objects.filter(id=override.id).update(novo_prazo_max_dias=45)


@pytest.mark.django_db(transaction=True)
def test_inv_cr_override_worm_insert_only_delete_raise():
    """INV-CR-OVERRIDE-WORM: DELETE em override_bloqueio → DatabaseError.

    Barreira: trigger `override_bloqueio_block_delete` (migration 0003).
    """
    from src.infrastructure.contas_receber.models import OverrideBloqueio
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        titulo = _cria_titulo_db(tenant)
        override = _cria_override_db(tenant, titulo)

    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        OverrideBloqueio.objects.filter(id=override.id).delete()


# ===========================================================================
# INV-CR-OVERRIDE-ANTI-PII — justificativa sem PII (validação de domínio)
# ===========================================================================


def test_inv_cr_override_anti_pii_justificativa_com_cpf_raise():
    """INV-CR-OVERRIDE-ANTI-PII: justificativa com CPF → JustificativaInsuficiente.

    Barreira: função pura `_validar_justificativa_anti_pii` em
    `src/application/contas_receber/override_bloqueio.py`. Rejeita CPF, CNPJ, e-mail
    e telefone em texto WORM (D-CR-20). Teste puro — sem banco.
    """
    from src.application.contas_receber.override_bloqueio import (
        _validar_justificativa_anti_pii,
    )
    from src.domain.contas_receber.erros import JustificativaInsuficiente

    # CPF formatado
    with pytest.raises(JustificativaInsuficiente):
        _validar_justificativa_anti_pii("Autorizo override para 123.456.789-09 cliente VIP")

    # CPF sem formatação
    with pytest.raises(JustificativaInsuficiente):
        _validar_justificativa_anti_pii("Autorizo override para 12345678909 cliente VIP")


def test_inv_cr_override_anti_pii_justificativa_com_email_raise():
    """INV-CR-OVERRIDE-ANTI-PII: justificativa com e-mail → JustificativaInsuficiente."""
    from src.application.contas_receber.override_bloqueio import (
        _validar_justificativa_anti_pii,
    )
    from src.domain.contas_receber.erros import JustificativaInsuficiente

    with pytest.raises(JustificativaInsuficiente):
        _validar_justificativa_anti_pii("Override solicitado para cliente@empresa.com.br VIP")


def test_inv_cr_override_anti_pii_justificativa_limpa_ok():
    """INV-CR-OVERRIDE-ANTI-PII (happy): justificativa sem PII → não levanta."""
    from src.application.contas_receber.override_bloqueio import (
        _validar_justificativa_anti_pii,
    )

    # Deve completar sem levantar
    _validar_justificativa_anti_pii(
        "Cliente solicitou prazo adicional por motivo de força maior documentado "
        "internamente no protocolo de atendimento. Aprovado por gerente financeiro."
    )


# ===========================================================================
# INV-CR-WEBHOOK-PAYLOAD-MINIMO — Pagamento não persiste PII do pagador
# ===========================================================================


def test_inv_cr_webhook_payload_minimo_pagamento_sem_pii_pagador():
    """INV-CR-WEBHOOK-PAYLOAD-MINIMO: model Pagamento NÃO tem campos de PII do pagador.

    Barreira: o model `Pagamento` (models.py) foi projetado sem campos como
    `nome_pagador`, `cpf_pagador`, `email_pagador` (D-CR-19 minimização). Este teste
    inspeciona os campos reais do model e afirma que esses campos não existem.
    """
    from src.infrastructure.contas_receber.models import Pagamento

    campos_do_model = {f.name for f in Pagamento._meta.get_fields()}

    campos_pii_proibidos = {
        "nome_pagador",
        "cpf_pagador",
        "email_pagador",
        "documento_pagador",
        "cpf",
        "cnpj",
        "nome_cliente",
        "email_cliente",
        "telefone_pagador",
        "telefone_cliente",
        "pagador_nome",
        "pagador_cpf",
        "pagador_email",
    }

    campos_pii_presentes = campos_pii_proibidos & campos_do_model
    assert not campos_pii_presentes, (
        f"INV-CR-WEBHOOK-PAYLOAD-MINIMO violado: model Pagamento tem campos de PII do "
        f"pagador: {campos_pii_presentes!r} (D-CR-19). "
        "Pagamento só deve guardar: valor, data, origem, gateway_event_id, comprovante_url."
    )


# ===========================================================================
# INV-FIS-CR-001 — consumer de criação de título registrado em os.concluida
# ===========================================================================


def test_inv_fis_cr_001_consumer_autofatura_registrado_em_os_concluida():
    """INV-FIS-CR-001: o consumer que cria título está registrado para `os.concluida`.

    Barreira: `ContasReceberConfig.ready()` em `apps.py` registra `handle_os_concluida`
    para a ação `os.concluida` (não `certificado.emitido` nem `os.concluida.fiscal`).
    Este teste importa o registry do outbox_worker e afirma que `handle_os_concluida`
    está na lista de consumers de `os.concluida`.
    """
    # Força o carregamento dos AppConfigs (ready() registra os consumers)
    from django.apps import apps

    apps.get_app_config("contas_receber")  # força acesso (já carregado em test runner)

    from src.infrastructure.audit.outbox_worker import _REGISTRY
    from src.infrastructure.contas_receber.consumers.os_eventos import handle_os_concluida

    consumers_os_concluida = _REGISTRY.get("os.concluida", [])

    assert handle_os_concluida in consumers_os_concluida, (
        f"INV-FIS-CR-001 violado: `handle_os_concluida` NÃO está registrado para "
        f"ação `os.concluida` no registry do outbox_worker. "
        f"Consumers registrados: {[getattr(fn, '__name__', fn) for fn in consumers_os_concluida]}"
    )

    # Confirma que NÃO está em `certificado.emitido` (gatilho errado seria bug de spec)
    consumers_cert = _REGISTRY.get("certificado.emitido", [])
    assert handle_os_concluida not in consumers_cert, (
        "INV-FIS-CR-001: `handle_os_concluida` está erroneamente em `certificado.emitido` "
        "(gatilho canônico do faturamento é `os.concluida` — D-CR-12)"
    )
