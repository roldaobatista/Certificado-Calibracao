"""Reconciliação F-A P4 — provas dos T-FA-01..04 (causa-raiz).

Cada teste prova um GAP fechado da matriz docs/faseamento/F-A/tasks.md:
- T-FA-01: invariante "1 cadeia/classe-lock por transação" fail-loud.
- T-FA-02: marco de corte é elo imutável encadeado + idempotente.
- T-FA-03: trigger PG rejeita UPDATE/DELETE em acessos_dados_cliente
  (a barreira real — AcessoDadosCliente NÃO tem hash chain por decisão).
- T-FA-04: ChavePIIIndisponivel em resposta-titular gera evento próprio.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.core.management import call_command
from django.db import IntegrityError, InternalError, ProgrammingError, transaction
from src.infrastructure.audit.models import AcessoDadosCliente, Auditoria
from src.infrastructure.audit.services import (
    ChavePIIIndisponivel,
    hashear_pii_com_salt_tenant,
    registrar_acesso_dados_cliente,
    registrar_auditoria,
    verificar_pii_hash_resposta_titular,
)
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)

from tests.factories import TenantFactory, UsuarioFactory

pytestmark = pytest.mark.tenant_isolation


@pytest.mark.django_db(transaction=True)
class TestReconciliacaoP4:
    def test_t_fa_01_multi_cadeia_mesma_transacao_falha_alto(self) -> None:
        """T-FA-01: 2 cadeias de tenants distintos na MESMA transação →
        RuntimeError claro (não deadlock silencioso). Chamadores reais
        não violam (1 tenant/tx); aqui forçamos a violação."""
        with run_as_system():
            ta, tb = TenantFactory(), TenantFactory()
            ua = UsuarioFactory()

        with pytest.raises(RuntimeError, match="T-FA-01: multi-cadeia"):
            with run_in_tenant_context(tenant_id=ta.id, usuario_id=ua.id):
                # 1ª cadeia (tenant A) — ok
                registrar_auditoria(
                    tenant_id=ta.id,
                    usuario_id=ua.id,
                    action="t.a",
                    resource_summary="r",
                    payload={"i": 1},
                )
                # 2ª cadeia distinta (tenant B) na MESMA transação → barra
                registrar_auditoria(
                    tenant_id=tb.id,
                    usuario_id=ua.id,
                    action="t.b",
                    resource_summary="r",
                    payload={"i": 2},
                )

    def test_t_fa_01_cadeia_unica_por_tx_passa(self) -> None:
        """Não-regressão: 2 elos da MESMA cadeia na mesma tx → ok."""
        with run_as_system():
            ta = TenantFactory()
            ua = UsuarioFactory()
        with run_in_tenant_context(tenant_id=ta.id, usuario_id=ua.id):
            registrar_auditoria(
                tenant_id=ta.id, usuario_id=ua.id, action="a1",
                resource_summary="r", payload={"i": 1},
            )
            e2 = registrar_auditoria(
                tenant_id=ta.id, usuario_id=ua.id, action="a2",
                resource_summary="r", payload={"i": 2},
            )
        assert e2.hash_anterior is not None  # encadeou normal

    def test_t_fa_02_marco_corte_imutavel_encadeado_idempotente(self) -> None:
        """T-FA-02: marcar_cadeia_autoritativa grava elo na cadeia
        sistema, encadeado, e é idempotente (não duplica)."""
        call_command("marcar_cadeia_autoritativa")
        with run_as_system():
            marcos = list(
                Auditoria.objects.filter(
                    tenant_id__isnull=True,
                    action="auditoria.marco_inicio_cadeia_autoritativa",
                )
            )
        assert len(marcos) == 1
        assert marcos[0].hash_atual  # é elo real encadeado
        assert "sequencia_corte" in marcos[0].payload_jsonb
        # idempotente
        call_command("marcar_cadeia_autoritativa")
        with run_as_system():
            n = Auditoria.objects.filter(
                tenant_id__isnull=True,
                action="auditoria.marco_inicio_cadeia_autoritativa",
            ).count()
        assert n == 1

    def test_t_fa_03_acessos_dados_cliente_trigger_bloqueia_mutacao(self) -> None:
        """T-FA-03: AcessoDadosCliente NÃO tem hash chain (decisão
        consciente AC-FA-005-7); a barreira real é o trigger PG —
        provado aqui rejeitando UPDATE e DELETE."""
        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
        with run_in_tenant_context(tenant_id=tenant.id, usuario_id=usuario.id):
            acesso = registrar_acesso_dados_cliente(
                tenant_id=tenant.id,
                usuario_id=usuario.id,
                cliente_id=uuid4(),
                finalidade="auditoria_interna",
            )
            with pytest.raises((IntegrityError, InternalError, ProgrammingError)):
                with transaction.atomic():
                    acesso.finalidade = "adulterado"
                    acesso.save(update_fields=["finalidade"])
            with pytest.raises((IntegrityError, InternalError, ProgrammingError)):
                with transaction.atomic():
                    AcessoDadosCliente.objects.filter(id=acesso.id).delete()

    def test_t_fa_04_inconclusivo_gera_evento_proprio(self) -> None:
        """T-FA-04: verificar_pii_hash_resposta_titular, ao receber hash
        com versão de chave ausente, grava evento na cadeia do tenant
        (accountability art. 6 X) e re-levanta ChavePIIIndisponivel —
        sem o valor cru no payload."""
        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
        with run_in_tenant_context(tenant_id=tenant.id, usuario_id=usuario.id):
            hash_chave_inexistente = "v999:" + "a" * 64
            antes = Auditoria.objects.filter(
                tenant_id=tenant.id, action="pii.verificacao_inconclusiva"
            ).count()
            with pytest.raises(ChavePIIIndisponivel):
                verificar_pii_hash_resposta_titular(
                    "12345678900",
                    tenant.id,
                    hash_chave_inexistente,
                    usuario_id=usuario.id,
                )
            eventos = list(
                Auditoria.objects.filter(
                    tenant_id=tenant.id, action="pii.verificacao_inconclusiva"
                )
            )
        assert len(eventos) == antes + 1
        ev = eventos[-1]
        assert ev.payload_jsonb["key_id_ausente"] == "v999"
        # valor cru NUNCA no payload
        assert "12345678900" not in str(ev.payload_jsonb)

    def test_t_fa_06_test_db_replica_matriz_roles_producao(self) -> None:
        """T-FA-06 (tech-lead P-A4): guarda anti-falso-verde. Se a suíte
        rodasse com role superuser/BYPASSRLS, o fuzzing cross-tenant
        (AC-FA-008-2) passaria MENTINDO (RLS ignorada). Aqui provamos que
        o ambiente de teste (test_afere) usa a MESMA matriz de produção:
        a role efetiva da conexão é NOBYPASSRLS + NOSUPERUSER, e
        app_user/app_migrator existem com esses atributos."""
        from django.db import connection

        with connection.cursor() as cur:
            cur.execute(
                "SELECT current_user, "
                "(SELECT rolsuper FROM pg_roles WHERE rolname=current_user), "
                "(SELECT rolbypassrls FROM pg_roles WHERE rolname=current_user);"
            )
            user_atual, is_super, is_bypass = cur.fetchone()
            cur.execute(
                "SELECT rolname, rolsuper, rolbypassrls FROM pg_roles "
                "WHERE rolname IN ('app_user','app_migrator') ORDER BY rolname;"
            )
            roles = cur.fetchall()

        assert is_super is False, f"conexão de teste é SUPERUSER ({user_atual}) — fuzzing falso-verde"
        assert is_bypass is False, f"conexão de teste é BYPASSRLS ({user_atual}) — fuzzing falso-verde"
        assert len(roles) == 2, f"app_user/app_migrator ausentes em test_afere: {roles}"
        for nome, rsuper, rbypass in roles:
            assert rsuper is False, f"{nome} é SUPERUSER em test_afere"
            assert rbypass is False, f"{nome} é BYPASSRLS em test_afere"

    def test_t_fa_04_caminho_feliz_nao_gera_evento(self) -> None:
        """Não-regressão: hash válido → True, sem evento de inconclusivo."""
        with run_as_system():
            tenant = TenantFactory()
            usuario = UsuarioFactory()
        with run_in_tenant_context(tenant_id=tenant.id, usuario_id=usuario.id):
            h = hashear_pii_com_salt_tenant("12345678900", tenant.id)
            ok = verificar_pii_hash_resposta_titular(
                "12345678900", tenant.id, h, usuario_id=usuario.id
            )
            n = Auditoria.objects.filter(
                tenant_id=tenant.id, action="pii.verificacao_inconclusiva"
            ).count()
        assert ok is True
        assert n == 0
