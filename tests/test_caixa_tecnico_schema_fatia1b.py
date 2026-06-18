"""Fatia 1b — schema PG-real do módulo caixa_tecnico (T-CT-027).

Cobre o COMPORTAMENTO em PG real (o que o drill estrutural não garante):
- RLS ENABLE+FORCE + ≥4 policies por tabela (INV-TENANT-001/002).
- Isolamento cross-tenant UNHAPPY: tenant B NÃO vê registros de A (INV-TENANT-003).
- Trigger anti-mutação despesa_validada: UPDATE → RAISE (INV-CT-IMUT-001/D-CT-3).
- Reapresentação rejeitada→pendente NÃO dispara anti-mutação (D-CT-3 / T-CT-057).
- Block-delete despesa SEMPRE: DELETE → RAISE; UPDATE status=cancelada OK (D-CT-5a).
- PrestacaoContas WORM: UPDATE total_adiantado → RAISE (INV-CT-PRESTACAO-WORM-001).
- UNIQUE foto_hash mesmo tenant → IntegrityError; tenant diferente → OK (D-CT-4 / T-CT-058).
- UNIQUE client_offline_id replay → IntegrityError (D-CT-5 / INV-CT-OFFLINE-001).
- Drill ``validar_caixa_tecnico`` verde.

Cada RAISE aborta a transação PG → cada cenário em teste isolado (TST-004).
Todos os testes usam ``transaction=True`` (TransactionTestCase via pytest-django).

IMPORTANTE: usa ``--reuse-db`` (NUNCA ``--create-db``). Memória:
``feedback_test_db_nao_dropar_create_db`` + ``feedback_test_db_owner_app_user``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from django.db import DatabaseError, IntegrityError, connection
from src.infrastructure.caixa_tecnico.models import (
    CaixaTecnico as CaixaTecnicoModel,
)
from src.infrastructure.caixa_tecnico.models import (
    DespesaCaixa as DespesaCaixaModel,
)
from src.infrastructure.caixa_tecnico.models import (
    PrestacaoContasCaixa as PrestacaoContasCaixaModel,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_HASH_V1 = "v1"
_FOTO_HASH_BASE = "a" * 64  # 64 chars HMAC hex


def _hash_tecnico(n: int = 1) -> str:
    return f"tecnico_hash_{n:04d}" + "x" * 60


def _cria_caixa(tenant, tecnico_hash: str | None = None) -> CaixaTecnicoModel:
    """Cria CaixaTecnico dentro do contexto do tenant."""
    if tecnico_hash is None:
        tecnico_hash = _hash_tecnico()
    with run_in_tenant_context(tenant.id):
        return CaixaTecnicoModel.objects.create(
            tenant=tenant,
            tecnico_referencia_hash=tecnico_hash,
            tecnico_key_id=_HASH_V1,
        )


def _cria_despesa(
    tenant,
    caixa: CaixaTecnicoModel,
    *,
    estado: str = "pendente",
    foto_hash: str | None = None,
    client_offline_id: str = "",
) -> DespesaCaixaModel:
    """Cria DespesaCaixa dentro do contexto do tenant."""
    if foto_hash is None:
        foto_hash = _FOTO_HASH_BASE
    with run_in_tenant_context(tenant.id):
        return DespesaCaixaModel.objects.create(
            tenant=tenant,
            caixa=caixa,
            tecnico_referencia_hash=caixa.tecnico_referencia_hash,
            tecnico_key_id=_HASH_V1,
            categoria="combustivel",
            tipo="normal",
            valor=5000,
            estado=estado,
            foto_hash=foto_hash,
            foto_url="http://example.com/foto.jpg",
            data=date.today(),
            client_offline_id=client_offline_id,
        )


def _cria_prestacao(
    tenant,
    caixa: CaixaTecnicoModel,
) -> PrestacaoContasCaixaModel:
    """Cria PrestacaoContasCaixa dentro do contexto do tenant."""
    hoje = date.today()
    with run_in_tenant_context(tenant.id):
        return PrestacaoContasCaixaModel.objects.create(
            tenant=tenant,
            caixa=caixa,
            tecnico_referencia_hash=caixa.tecnico_referencia_hash,
            tecnico_key_id=_HASH_V1,
            periodo_de=hoje - timedelta(days=30),
            periodo_ate=hoje,
            total_adiantado=10000,
            total_despesas_validadas=8000,
            saldo_final=2000,
            direcao="tenant_deve",
            fechada_em=datetime.now(UTC),
        )


# ---------------------------------------------------------------------------
# 1. RLS isolamento cross-tenant
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_rls_isolamento_cross_tenant() -> None:
    """Tenant B NÃO consegue ler registros do tenant A (INV-TENANT-003)."""
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()

    caixa_a = _cria_caixa(tenant_a, tecnico_hash=_hash_tecnico(1))

    # Dentro do contexto do tenant A → vê o caixa
    with run_in_tenant_context(tenant_a.id):
        assert CaixaTecnicoModel.objects.filter(id=caixa_a.id).exists()

    # Dentro do contexto do tenant B → NÃO vê (RLS filtra)
    with run_in_tenant_context(tenant_b.id):
        assert not CaixaTecnicoModel.objects.filter(id=caixa_a.id).exists()


# ---------------------------------------------------------------------------
# 2. Trigger anti-mutação UPDATE despesa_validada
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_trigger_anti_mutacao_update_valida_raise() -> None:
    """UPDATE em despesa com estado='validada' → RAISE (INV-CT-IMUT-001 / D-CT-3)."""
    tenant = TenantFactory()
    caixa = _cria_caixa(tenant)
    despesa = _cria_despesa(tenant, caixa, estado="validada")

    with pytest.raises((DatabaseError, IntegrityError)):
        with run_in_tenant_context(tenant.id):
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE despesa_caixa SET descricao = 'mutação proibida' WHERE id = %s",
                    [str(despesa.id)],
                )


# ---------------------------------------------------------------------------
# 3. Reapresentação rejeitada→pendente NÃO dispara anti-mutação
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_reapresentacao_rejeitada_para_pendente_nao_dispara_trigger() -> None:
    """UPDATE estado rejeitada→pendente NÃO levanta — só validada é WORM (T-CT-057)."""
    tenant = TenantFactory()
    caixa = _cria_caixa(tenant)
    despesa = _cria_despesa(tenant, caixa, estado="rejeitada")

    # Reapresentação legítima: rejeitada → pendente
    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE despesa_caixa SET estado = 'pendente', motivo_rejeicao = '' WHERE id = %s",
                [str(despesa.id)],
            )
        # Deve ter atualizado sem erro
        despesa.refresh_from_db()
        assert despesa.estado == "pendente"


# ---------------------------------------------------------------------------
# 4. Block-delete despesa SEMPRE
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_block_delete_despesa_raise() -> None:
    """DELETE físico em despesa → RAISE em qualquer estado (D-CT-5a/INV-CT-IMUT-001)."""
    tenant = TenantFactory()
    caixa = _cria_caixa(tenant)
    despesa = _cria_despesa(tenant, caixa, estado="pendente")

    with pytest.raises((DatabaseError, IntegrityError)):
        with run_in_tenant_context(tenant.id):
            with connection.cursor() as cur:
                cur.execute(
                    "DELETE FROM despesa_caixa WHERE id = %s",
                    [str(despesa.id)],
                )


@pytest.mark.django_db(transaction=True)
def test_update_status_cancelada_ok() -> None:
    """UPDATE estado para 'cancelada' (soft-delete) → PERMITIDO (Padrão A)."""
    tenant = TenantFactory()
    caixa = _cria_caixa(tenant)
    despesa = _cria_despesa(tenant, caixa, estado="pendente")

    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE despesa_caixa SET estado = 'cancelada' WHERE id = %s",
                [str(despesa.id)],
            )
        despesa.refresh_from_db()
        assert despesa.estado == "cancelada"


# ---------------------------------------------------------------------------
# 5. PrestacaoContas WORM — campos financeiros congelados
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_prestacao_worm_update_total_adiantado_raise() -> None:
    """UPDATE total_adiantado em prestacao fechada → RAISE (INV-CT-PRESTACAO-WORM-001)."""
    tenant = TenantFactory()
    caixa = _cria_caixa(tenant)
    prestacao = _cria_prestacao(tenant, caixa)

    with pytest.raises((DatabaseError, IntegrityError)):
        with run_in_tenant_context(tenant.id):
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE prestacao_contas_caixa SET total_adiantado = 99999 WHERE id = %s",
                    [str(prestacao.id)],
                )


@pytest.mark.django_db(transaction=True)
def test_prestacao_worm_update_pdf_url_ok() -> None:
    """UPDATE pdf_url em prestacao → PERMITIDO (campo não-financeiro — D-CT-8)."""
    tenant = TenantFactory()
    caixa = _cria_caixa(tenant)
    prestacao = _cria_prestacao(tenant, caixa)

    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE prestacao_contas_caixa SET pdf_url = 'http://example.com/pdf.pdf' WHERE id = %s",
                [str(prestacao.id)],
            )
        prestacao.refresh_from_db()
        assert "pdf.pdf" in prestacao.pdf_url


# ---------------------------------------------------------------------------
# 6. UNIQUE foto_hash — mesmo tenant → IntegrityError; tenant diferente → OK
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_unique_foto_hash_mesmo_tenant_raise() -> None:
    """Foto idêntica no mesmo tenant (estado ativo) → IntegrityError (INV-CT-FOTO-DEDUP-001)."""
    tenant = TenantFactory()
    caixa = _cria_caixa(tenant)
    foto_hash = "b" * 64

    _cria_despesa(tenant, caixa, estado="pendente", foto_hash=foto_hash)

    with pytest.raises(IntegrityError):
        _cria_despesa(tenant, caixa, estado="pendente", foto_hash=foto_hash)


@pytest.mark.django_db(transaction=True)
def test_unique_foto_hash_tenant_diferente_ok() -> None:
    """Foto idêntica em tenants DIFERENTES → PERMITIDO (constraint é por tenant — T-CT-058)."""
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    foto_hash = "c" * 64

    caixa_a = _cria_caixa(tenant_a, tecnico_hash=_hash_tecnico(10))
    caixa_b = _cria_caixa(tenant_b, tecnico_hash=_hash_tecnico(20))

    _cria_despesa(tenant_a, caixa_a, estado="pendente", foto_hash=foto_hash)
    # Não deve levantar — tenants diferentes
    _cria_despesa(tenant_b, caixa_b, estado="pendente", foto_hash=foto_hash)


@pytest.mark.django_db(transaction=True)
def test_unique_foto_hash_rejeitada_pode_reapresentar_mesma_foto() -> None:
    """Foto em estado 'rejeitada' sai do índice parcial — pode inserir nova com mesmo hash."""
    tenant = TenantFactory()
    caixa = _cria_caixa(tenant)
    foto_hash = "d" * 64

    # Cria rejeitada (sai da constraint parcial)
    with run_in_tenant_context(tenant.id):
        DespesaCaixaModel.objects.create(
            tenant=tenant,
            caixa=caixa,
            tecnico_referencia_hash=caixa.tecnico_referencia_hash,
            tecnico_key_id=_HASH_V1,
            categoria="combustivel",
            tipo="normal",
            valor=5000,
            estado="rejeitada",
            foto_hash=foto_hash,
            foto_url="http://example.com/foto.jpg",
            data=date.today(),
        )

    # Nova despesa pendente com mesmo foto_hash → deve ser permitida
    _cria_despesa(tenant, caixa, estado="pendente", foto_hash=foto_hash)


# ---------------------------------------------------------------------------
# 7. UNIQUE client_offline_id replay → IntegrityError
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_unique_client_offline_id_replay_raise() -> None:
    """Mesmo client_offline_id no mesmo tenant → IntegrityError (INV-CT-OFFLINE-001 / D-CT-5)."""
    tenant = TenantFactory()
    caixa = _cria_caixa(tenant)
    offline_id = f"mobile-{uuid.uuid4()}"
    foto_hash_1 = "e" * 64
    foto_hash_2 = "f" * 64

    _cria_despesa(tenant, caixa, foto_hash=foto_hash_1, client_offline_id=offline_id)

    with pytest.raises(IntegrityError):
        _cria_despesa(tenant, caixa, foto_hash=foto_hash_2, client_offline_id=offline_id)


@pytest.mark.django_db(transaction=True)
def test_unique_client_offline_id_vazio_nao_conflita() -> None:
    """client_offline_id='' (não-offline) não entra na constraint parcial."""
    tenant = TenantFactory()
    caixa = _cria_caixa(tenant)
    foto_hash_1 = "g" * 64
    foto_hash_2 = "h" * 64

    _cria_despesa(tenant, caixa, foto_hash=foto_hash_1, client_offline_id="")
    # Não deve levantar — client_offline_id='' excluído da constraint
    _cria_despesa(tenant, caixa, foto_hash=foto_hash_2, client_offline_id="")


# ---------------------------------------------------------------------------
# 8. Drill validar_caixa_tecnico
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_drill_validar_caixa_tecnico() -> None:
    """``validar_caixa_tecnico`` deve completar sem erros (T-CT-027)."""
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    # call_command não levanta SystemExit quando PASS
    call_command("validar_caixa_tecnico", stdout=out)
    output = out.getvalue()
    assert "PASS" in output


# ---------------------------------------------------------------------------
# 9. Block-delete prestacao
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_block_delete_prestacao_raise() -> None:
    """DELETE físico em prestação → RAISE (D-CT-8 / registro financeiro imutável)."""
    tenant = TenantFactory()
    caixa = _cria_caixa(tenant)
    prestacao = _cria_prestacao(tenant, caixa)

    with pytest.raises((DatabaseError, IntegrityError)):
        with run_in_tenant_context(tenant.id):
            with connection.cursor() as cur:
                cur.execute(
                    "DELETE FROM prestacao_contas_caixa WHERE id = %s",
                    [str(prestacao.id)],
                )


# ---------------------------------------------------------------------------
# 10. RLS estrutural — ENABLED+FORCED nas 6 tabelas
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_rls_enabled_forced_em_todas_as_tabelas() -> None:
    """ENABLE ROW LEVEL SECURITY + FORCE em todas as 6 tabelas (INV-TENANT-001/002)."""
    tabelas = [
        "caixa_tecnico",
        "adiantamento_caixa",
        "despesa_caixa",
        "prestacao_contas_caixa",
        "politica_caixa",
        "consentimento_gps_colaborador",
    ]
    with connection.cursor() as cur:
        for tabela in tabelas:
            cur.execute(
                """
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class
                WHERE relname = %s AND relnamespace = 'public'::regnamespace;
                """,
                [tabela],
            )
            row = cur.fetchone()
            assert row is not None, f"Tabela não existe: {tabela}"
            rls_enabled, rls_forced = row
            assert rls_enabled, f"RLS não habilitado em {tabela}"
            assert rls_forced, f"RLS não forçado em {tabela}"


@pytest.mark.django_db(transaction=True)
def test_policies_minimas_em_todas_as_tabelas() -> None:
    """≥ 4 policies por tabela (INV-TENANT-002 — SELECT/UPDATE/DELETE/INSERT)."""
    tabelas = [
        "caixa_tecnico",
        "adiantamento_caixa",
        "despesa_caixa",
        "prestacao_contas_caixa",
        "politica_caixa",
        "consentimento_gps_colaborador",
    ]
    with connection.cursor() as cur:
        for tabela in tabelas:
            cur.execute(
                """
                SELECT count(*)
                FROM pg_policies
                WHERE schemaname = 'public' AND tablename = %s;
                """,
                [tabela],
            )
            n = cur.fetchone()[0]
            assert n >= 4, f"Policies insuficientes em {tabela}: {n} (esperado ≥4)"
