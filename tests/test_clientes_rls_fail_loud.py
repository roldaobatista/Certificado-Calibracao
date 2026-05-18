"""FA-A2 — prova fail-loud das policies RLS de `clientes`.

Antes do FA-A2 `clientes/0002` usava `current_setting('app.tenant_ids')`
CRU: em contexto vazio devolvia `''` → policy "via 0 linhas" SILENCIOSA
(degradava para "vê nada" em vez de RAISE). `clientes/0014` regenera as
policies com `require_tenant_ctx()` (RAISE SQLSTATE 42501).

Cobre o `# tests-coverage:` de `clientes/0014_rls_fail_loud.py`:
- HAPPY: contexto de tenant → vê as próprias linhas.
- UNHAPPY (a prova do FA-A2): contexto vazio → RAISE com SQLSTATE **42501**
  (assert do código específico, não ProgrammingError genérico — R4).
- cross-tenant: contexto A não vê nem insere linha de B.
- regressão do template (`rls_templates.py`): forma do SQL + anti-injeção.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db.utils import ProgrammingError
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.multitenant.rls_templates import (
    policies_isolamento_tenant,
    reverse_policies_isolamento_tenant,
)

from tests.factories import TenantFactory


def _sqlstate(exc: BaseException) -> str | None:
    """SQLSTATE da exceção PG, atravessando o wrapper do Django (psycopg3)."""
    causa = exc.__cause__
    return getattr(causa, "sqlstate", None) if causa is not None else None


@pytest.mark.django_db(transaction=True)
@pytest.mark.tenant_isolation
class TestClientesRLSFailLoud:
    def test_happy_contexto_tenant_ve_as_proprias_linhas(self) -> None:
        tenant_a = TenantFactory(slug=f"a-{uuid4().hex[:8]}")
        with run_in_tenant_context(tenant_a.id):
            c = Cliente.objects.create(
                tenant=tenant_a,
                tipo_pessoa=TipoPessoa.PJ,
                documento="11222333000181",
                nome="Cliente A",
            )
            assert Cliente.objects.filter(id=c.id).count() == 1

    def test_unhappy_contexto_vazio_levanta_42501_nao_lista_vazia(self) -> None:
        """A PROVA do FA-A2: contexto vazio RAISE 42501, NÃO 0 linhas mudo.

        Antes do conserto isto retornava `[]` silenciosamente (furo).
        """
        tenant_a = TenantFactory(slug=f"a-{uuid4().hex[:8]}")
        with run_in_tenant_context(tenant_a.id):
            Cliente.objects.create(
                tenant=tenant_a,
                tipo_pessoa=TipoPessoa.PJ,
                documento="11222333000181",
                nome="Cliente A",
            )

        # Fora de qualquer run_in_tenant_context: app.tenant_ids resetado.
        with pytest.raises(ProgrammingError) as exc:
            list(Cliente.objects.all())

        assert _sqlstate(exc.value) == "42501", (
            f"Esperado SQLSTATE 42501 (require_tenant_ctx), "
            f"veio {_sqlstate(exc.value)!r}: {exc.value}"
        )

    def test_cross_tenant_b_nao_ve_nem_insere_em_a(self) -> None:
        tenant_a = TenantFactory(slug=f"a-{uuid4().hex[:8]}")
        tenant_b = TenantFactory(slug=f"b-{uuid4().hex[:8]}")
        with run_in_tenant_context(tenant_a.id):
            c_a = Cliente.objects.create(
                tenant=tenant_a,
                tipo_pessoa=TipoPessoa.PJ,
                documento="11222333000181",
                nome="A",
            )
        with run_in_tenant_context(tenant_b.id):
            assert Cliente.objects.filter(id=c_a.id).count() == 0
            # INSERT com tenant de A enquanto active = B → WITH CHECK rejeita.
            with pytest.raises(ProgrammingError):
                Cliente.objects.create(
                    tenant=tenant_a,
                    tipo_pessoa=TipoPessoa.PJ,
                    documento="33000167000101",
                    nome="cross",
                )


class TestTemplateRLS:
    """Regressão barata do gerador — pega template torto sem subir banco."""

    def test_select_update_delete_usam_require_tenant_ctx(self) -> None:
        sql = policies_isolamento_tenant("clientes")
        assert sql.count("require_tenant_ctx()") == 4  # select + update(x2) + delete
        assert "current_setting('app.tenant_ids')" not in sql  # nada de cru

    def test_insert_usa_active_tenant_id(self) -> None:
        sql = policies_isolamento_tenant("clientes")
        assert (
            "FOR INSERT\n    WITH CHECK (tenant_id = "
            "current_setting('app.active_tenant_id')::uuid)" in sql
        )

    def test_forward_dropa_antes_de_criar(self) -> None:
        sql = policies_isolamento_tenant("clientes")
        assert sql.index("DROP POLICY IF EXISTS") < sql.index("CREATE POLICY")

    def test_reverse_nao_volta_ao_cru(self) -> None:
        # R2: reverse continua fail-loud (idêntico ao forward).
        assert reverse_policies_isolamento_tenant("clientes") == (
            policies_isolamento_tenant("clientes")
        )

    @pytest.mark.parametrize(
        "ruim", ["clientes; DROP TABLE x", "Clientes", "1tab", "a b", "tab--", ""]
    )
    def test_nome_tabela_invalido_levanta_valueerror(self, ruim: str) -> None:
        with pytest.raises(ValueError):
            policies_isolamento_tenant(ruim)
