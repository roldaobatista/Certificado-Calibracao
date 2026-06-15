"""Frente contas-receber — Fatia 1b (T-CR-027): schema PG-real.

Cobre o COMPORTAMENTO em PG real (o que o drill estrutural não garante):
- RLS ENABLE+FORCE + 4 policies por tabela (INV-TENANT-001/002).
- Isolamento cross-tenant UNHAPPY: tenant B não vê título de A (INV-TENANT-003).
- block-delete RAISE em Titulo/Pagamento/OverrideBloqueio (INV-CR-* WORM).
- Campo probatório imutável RAISE (ex: valor_original → erro).
- Estado transiciona OK (UPDATE estado permitido).
- `data_baixa` one-shot (NULL→valor ok; valor→outro RAISE).
- `cancelado_em` one-shot (NULL→valor ok; valor→outro RAISE).
- `Pagamento` INSERT-only (UPDATE RAISE — INV-CR-PAGAMENTO-WORM).
- `OverrideBloqueio` INSERT-only (UPDATE RAISE — INV-CR-OVERRIDE-WORM).
- UNIQUE os_id ativo (2º título ativo mesma OS → IntegrityError; após cancelar
  o 1º, permite).
- CHECK convenio_pix (pix_recorrente sem convenio → IntegrityError — INV-FIN-GW-002).

Cada RAISE aborta a transação PG → cada cenário em teste isolado (TST-004).
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from django.db import DatabaseError, IntegrityError, connection
from django.utils import timezone as dj_tz
from src.infrastructure.contas_receber.models import (
    OverrideBloqueio,
    Pagamento,
    Titulo,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_DATA_HOJE = date.today()
_HASH = "a" * 64  # HMAC hex válido (≥32 chars)
_KEY_ID = "v1"


def _cria_titulo(
    tenant,
    *,
    estado: str = "emitido",
    meio: str = "boleto",
    os_id: uuid.UUID | None = None,
    convenio_pix_id: str = "",
) -> Titulo:
    with run_in_tenant_context(tenant.id):
        return Titulo.objects.create(
            tenant=tenant,
            cliente_atual_id=uuid.uuid4(),
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


def _cria_pagamento(tenant, titulo: Titulo) -> Pagamento:
    with run_in_tenant_context(tenant.id):
        return Pagamento.objects.create(
            tenant=tenant,
            titulo=titulo,
            valor=10000,
            data=_DATA_HOJE,
            origem="manual",
            valor_atualizado_snapshot_em_pagamento=10000,
        )


def _cria_override(tenant, titulo: Titulo) -> OverrideBloqueio:
    with run_in_tenant_context(tenant.id):
        return OverrideBloqueio.objects.create(
            tenant=tenant,
            titulo=titulo,
            cliente_id=uuid.uuid4(),
            novo_prazo_max_dias=30,
            justificativa="J" * 100,
            a3_signature_id="stub-wave-a",
            usuario_id=uuid.uuid4(),
            perfil_no_evento="A",
        )


# ---------------------------------------------------------------------------
# 1. Estrutura RLS
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_rls_force_e_4_policies_titulo() -> None:
    tabela = "titulo_receber"
    with connection.cursor() as cur:
        cur.execute(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON c.relnamespace=n.oid "
            "WHERE n.nspname='public' AND c.relname=%s",
            [tabela],
        )
        enabled, forced = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM pg_policies WHERE tablename=%s", [tabela])
        n_pol = cur.fetchone()[0]
    assert enabled, "INV-TENANT-001: titulo_receber sem RLS"
    assert forced, "INV-TENANT-002: titulo_receber sem FORCE"
    assert n_pol >= 4, f"titulo_receber com <4 policies ({n_pol})"


@pytest.mark.django_db
def test_rls_force_e_4_policies_pagamento() -> None:
    tabela = "pagamento_titulo"
    with connection.cursor() as cur:
        cur.execute(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON c.relnamespace=n.oid "
            "WHERE n.nspname='public' AND c.relname=%s",
            [tabela],
        )
        enabled, forced = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM pg_policies WHERE tablename=%s", [tabela])
        n_pol = cur.fetchone()[0]
    assert enabled, "pagamento_titulo sem RLS"
    assert forced, "pagamento_titulo sem FORCE"
    assert n_pol >= 4, f"pagamento_titulo com <4 policies ({n_pol})"


@pytest.mark.django_db
def test_rls_force_e_4_policies_override() -> None:
    tabela = "override_bloqueio"
    with connection.cursor() as cur:
        cur.execute(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON c.relnamespace=n.oid "
            "WHERE n.nspname='public' AND c.relname=%s",
            [tabela],
        )
        enabled, forced = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM pg_policies WHERE tablename=%s", [tabela])
        n_pol = cur.fetchone()[0]
    assert enabled, "override_bloqueio sem RLS"
    assert forced, "override_bloqueio sem FORCE"
    assert n_pol >= 4, f"override_bloqueio com <4 policies ({n_pol})"


# ---------------------------------------------------------------------------
# 2. Isolamento cross-tenant (UNHAPPY)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_rls_isola_titulo_entre_tenants() -> None:
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    titulo_a = _cria_titulo(tenant_a)
    # Tenant B NÃO enxerga título do tenant A.
    with run_in_tenant_context(tenant_b.id):
        assert not Titulo.objects.filter(id=titulo_a.id).exists()
    # Tenant A enxerga o próprio.
    with run_in_tenant_context(tenant_a.id):
        assert Titulo.objects.filter(id=titulo_a.id).exists()


# ---------------------------------------------------------------------------
# 3. block-delete RAISE (WORM — INV-CR-*)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_delete_fisico_titulo_raise() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Titulo.objects.filter(id=titulo.id).delete()


@pytest.mark.django_db(transaction=True)
def test_delete_fisico_pagamento_raise() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant)
    pagamento = _cria_pagamento(tenant, titulo)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Pagamento.objects.filter(id=pagamento.id).delete()


@pytest.mark.django_db(transaction=True)
def test_delete_fisico_override_raise() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant)
    override = _cria_override(tenant, titulo)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        OverrideBloqueio.objects.filter(id=override.id).delete()


# ---------------------------------------------------------------------------
# 4. Campo probatório imutável RAISE (WORM Padrão B — D-CR-17)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_valor_original_imutavel_raise() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Titulo.objects.filter(id=titulo.id).update(valor_original=99999)


@pytest.mark.django_db(transaction=True)
def test_cliente_hash_imutavel_raise() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Titulo.objects.filter(id=titulo.id).update(cliente_referencia_hash="b" * 64)


@pytest.mark.django_db(transaction=True)
def test_perfil_no_evento_imutavel_raise() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Titulo.objects.filter(id=titulo.id).update(perfil_no_evento="B")


@pytest.mark.django_db(transaction=True)
def test_categoria_receita_imutavel_raise() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Titulo.objects.filter(id=titulo.id).update(categoria_receita="MANUTENCAO_CORRETIVA")


# ---------------------------------------------------------------------------
# 5. Estado transiciona OK (campo mutável)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_estado_transiciona_ok() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant, estado="emitido")
    with run_in_tenant_context(tenant.id):
        n = Titulo.objects.filter(id=titulo.id).update(estado="vencido")
    assert n == 1


# ---------------------------------------------------------------------------
# 6. data_baixa one-shot
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_data_baixa_first_set_ok() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant)
    with run_in_tenant_context(tenant.id):
        n = Titulo.objects.filter(id=titulo.id).update(data_baixa=_DATA_HOJE)
    assert n == 1


@pytest.mark.django_db(transaction=True)
def test_data_baixa_one_shot_raise() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant)
    with run_in_tenant_context(tenant.id):
        Titulo.objects.filter(id=titulo.id).update(data_baixa=_DATA_HOJE)
    # Tentar mudar → RAISE. Data fixa garantidamente != hoje (evita flake no dia 1).
    outro_dia = date(2000, 1, 1)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Titulo.objects.filter(id=titulo.id).update(data_baixa=outro_dia)


# ---------------------------------------------------------------------------
# 7. cancelado_em one-shot
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_cancelado_em_first_set_ok() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant)
    now = dj_tz.now()
    with run_in_tenant_context(tenant.id):
        n = Titulo.objects.filter(id=titulo.id).update(estado="cancelado", cancelado_em=now)
    assert n == 1


@pytest.mark.django_db(transaction=True)
def test_cancelado_em_one_shot_raise() -> None:
    tenant = TenantFactory()
    now = dj_tz.now()
    titulo = _cria_titulo(tenant)
    with run_in_tenant_context(tenant.id):
        Titulo.objects.filter(id=titulo.id).update(estado="cancelado", cancelado_em=now)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Titulo.objects.filter(id=titulo.id).update(cancelado_em=dj_tz.now())


# ---------------------------------------------------------------------------
# 8. Pagamento INSERT-only (UPDATE RAISE)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_pagamento_update_raise() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant)
    pagamento = _cria_pagamento(tenant, titulo)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Pagamento.objects.filter(id=pagamento.id).update(valor=1)


# ---------------------------------------------------------------------------
# 9. OverrideBloqueio INSERT-only (UPDATE RAISE)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_override_update_raise() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant)
    override = _cria_override(tenant, titulo)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        OverrideBloqueio.objects.filter(id=override.id).update(novo_prazo_max_dias=45)


# ---------------------------------------------------------------------------
# 10. UNIQUE os_id ativo (INV-CR-OS-TITULO-UNICO / R6)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_unique_os_id_ativo_raise() -> None:
    tenant = TenantFactory()
    os_id = uuid.uuid4()
    _cria_titulo(tenant, os_id=os_id)
    # 2º título ativo para a mesma OS → IntegrityError
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        _cria_titulo(tenant, os_id=os_id)


@pytest.mark.django_db(transaction=True)
def test_unique_os_id_permite_apos_cancelar() -> None:
    tenant = TenantFactory()
    os_id = uuid.uuid4()
    titulo = _cria_titulo(tenant, os_id=os_id)
    # Cancelar o 1º
    with run_in_tenant_context(tenant.id):
        Titulo.objects.filter(id=titulo.id).update(estado="cancelado")
    # Agora deve permitir 2º título ativo para a mesma OS
    novo = _cria_titulo(tenant, os_id=os_id)
    assert novo.id != titulo.id


# ---------------------------------------------------------------------------
# 11. CHECK convenio_pix (INV-FIN-GW-002)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_pix_recorrente_sem_convenio_raise() -> None:
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        Titulo.objects.create(
            tenant=tenant,
            cliente_atual_id=uuid.uuid4(),
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
            convenio_pix_id="",  # violação: meio=pix_recorrente sem convênio
        )


@pytest.mark.django_db(transaction=True)
def test_pix_recorrente_com_convenio_ok() -> None:
    tenant = TenantFactory()
    titulo = _cria_titulo(tenant, meio="pix_recorrente", convenio_pix_id="conv-abc-123")
    assert titulo.id is not None
