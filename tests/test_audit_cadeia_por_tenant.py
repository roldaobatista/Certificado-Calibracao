"""FA-C1 - hash chain POR tenant + cadeia sistema (auditoria F-A rodada 1).

Testes T1-T8 obrigatórios do design aprovado pelo tech-lead
(docs/faseamento/auditorias/FA-C1-design-hash-chain.md). Provam:
cadeia independente por tenant, cadeia sistema (tenant NULL), Q-02
corrigido (adulteração no meio quebra todos os seguintes), fail-loud
preservado, modo_sistema não vaza no pool.
"""

from __future__ import annotations

import pytest
from django.db import connection, transaction
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.audit.services import (
    registrar_auditoria,
    verificar_integridade_cadeia,
)
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)

from tests.factories import TenantFactory, UsuarioFactory

pytestmark = pytest.mark.tenant_isolation  # exige PG real (RLS/policies)


@pytest.mark.django_db(transaction=True)
class TestCadeiaPorTenant:
    def test_t1_dois_tenants_intercalados_cadeias_independentes(self) -> None:
        with run_as_system():
            ta, tb = TenantFactory(), TenantFactory()
            ua, ub = UsuarioFactory(), UsuarioFactory()

        with run_in_tenant_context(tenant_id=ta.id, usuario_id=ua.id):
            a1 = registrar_auditoria(
                tenant_id=ta.id,
                usuario_id=ua.id,
                action="a1",
                resource_summary="r",
                payload={"i": 1},
            )
        with run_in_tenant_context(tenant_id=tb.id, usuario_id=ub.id):
            registrar_auditoria(
                tenant_id=tb.id,
                usuario_id=ub.id,
                action="b1",
                resource_summary="r",
                payload={"i": 9},
            )
        with run_in_tenant_context(tenant_id=ta.id, usuario_id=ua.id):
            a2 = registrar_auditoria(
                tenant_id=ta.id,
                usuario_id=ua.id,
                action="a2",
                resource_summary="r",
                payload={"i": 2},
            )

        # A2 encadeia no A1 — NAO no B1 que entrou no meio.
        assert a1.hash_anterior is None
        assert a2.hash_anterior == a1.hash_atual

    def test_t2_verificacao_por_tenant_retorna_dict(self) -> None:
        with run_as_system():
            ta, tb = TenantFactory(), TenantFactory()
            ua, ub = UsuarioFactory(), UsuarioFactory()
        with run_in_tenant_context(tenant_id=ta.id, usuario_id=ua.id):
            for i in range(4):
                registrar_auditoria(
                    tenant_id=ta.id,
                    usuario_id=ua.id,
                    action=f"a{i}",
                    resource_summary="r",
                    payload={"i": i},
                )
        with run_in_tenant_context(tenant_id=tb.id, usuario_id=ub.id):
            for i in range(3):
                registrar_auditoria(
                    tenant_id=tb.id,
                    usuario_id=ub.id,
                    action=f"b{i}",
                    resource_summary="r",
                    payload={"i": i},
                )
        res = verificar_integridade_cadeia()
        assert res[str(ta.id)] == (True, 4, [])
        assert res[str(tb.id)] == (True, 3, [])

    def test_t3_cadeia_sistema_tenant_null_encadeia(self) -> None:
        # A cadeia "sistema" (tenant NULL) é GLOBAL e perpétua. A tabela
        # `auditoria` é append-only imutável (trigger + policy bloqueiam
        # DELETE/TRUNCATE), então o flush do pytest-django NÃO consegue
        # limpá-la entre testes — logo "a primeira linha sistema" não existe
        # no escopo de um teste: s1 encadeia no último elo sistema deixado
        # por testes/boot anteriores. O que T3 prova (design FA-C1) é
        # "evento tenant-NULL sob run_as_system GRAVA + ENCADEIA na cadeia
        # sistema", verificado por encadeamento relativo + integridade total.
        ok_antes, total_antes, _ = verificar_integridade_cadeia(tenant_id=None)[None]

        with run_as_system():
            s1 = registrar_auditoria(
                tenant_id=None,
                usuario_id=None,
                action="sistema.boot",
                resource_summary="g",
                payload={"n": 1},
            )
            s2 = registrar_auditoria(
                tenant_id=None,
                usuario_id=None,
                action="sistema.boot",
                resource_summary="g",
                payload={"n": 2},
            )
        assert s1.tenant_id is None
        assert s2.hash_anterior == s1.hash_atual  # s2 encadeia em s1
        ok, total, quebrados = verificar_integridade_cadeia(tenant_id=None)[None]
        assert ok is True
        assert total == total_antes + 2  # gravou exatamente os 2 elos novos
        assert quebrados == []

    def test_t4_adulteracao_no_meio_quebra_todos_os_seguintes(self) -> None:
        """Prova Q-02 corrigido: encadeia no RECALCULADO, não no salvo."""
        with run_as_system():
            ta = TenantFactory()
            ua = UsuarioFactory()
        with run_in_tenant_context(tenant_id=ta.id, usuario_id=ua.id):
            registrar_auditoria(
                tenant_id=ta.id,
                usuario_id=ua.id,
                action="e0",
                resource_summary="r",
                payload={"i": 0},
            )
            a1 = registrar_auditoria(
                tenant_id=ta.id,
                usuario_id=ua.id,
                action="e1",
                resource_summary="r",
                payload={"i": 1},
            )
            # Elo 2 ENVENENADO: hash_atual não corresponde ao payload.
            # INSERT direto (policy permite; trigger só nega UPDATE/DELETE).
            Auditoria.objects.create(
                tenant_id=ta.id,
                usuario_id=ua.id,
                action="e2",
                resource_summary="r",
                payload_jsonb={"i": 2},
                hash_anterior=a1.hash_atual,
                hash_atual="0" * 64,
            )
            registrar_auditoria(
                tenant_id=ta.id,
                usuario_id=ua.id,
                action="e3",
                resource_summary="r",
                payload={"i": 3},
            )
            registrar_auditoria(
                tenant_id=ta.id,
                usuario_id=ua.id,
                action="e4",
                resource_summary="r",
                payload={"i": 4},
            )
        ok, total, quebrados = verificar_integridade_cadeia(tenant_id=ta.id)[str(ta.id)]
        assert ok is False
        assert total == 5
        # Elo 2 adulterado + 3 + 4 (encadeiam no recalculado): >= 3 quebrados.
        # Sem o fix Q-02 (encadeava no salvo) só o elo 2 apareceria.
        assert len(quebrados) >= 3

    def test_t5_request_tenant_a_nao_ve_auditoria_de_b(self) -> None:
        with run_as_system():
            ta, tb = TenantFactory(), TenantFactory()
            ua, ub = UsuarioFactory(), UsuarioFactory()
        with run_in_tenant_context(tenant_id=ta.id, usuario_id=ua.id):
            registrar_auditoria(
                tenant_id=ta.id,
                usuario_id=ua.id,
                action="segredo_de_A",
                resource_summary="r",
                payload={"x": 1},
            )
        with run_in_tenant_context(tenant_id=tb.id, usuario_id=ub.id):
            visiveis = list(Auditoria.objects.values_list("action", flat=True))
        assert "segredo_de_A" not in visiveis

    def test_t6_cadeia_de_B_intacta_independe_de_A(self) -> None:
        with run_as_system():
            ta, tb = TenantFactory(), TenantFactory()
            ua, ub = UsuarioFactory(), UsuarioFactory()
        with run_in_tenant_context(tenant_id=ta.id, usuario_id=ua.id):
            a0 = registrar_auditoria(
                tenant_id=ta.id,
                usuario_id=ua.id,
                action="a0",
                resource_summary="r",
                payload={"i": 0},
            )
            Auditoria.objects.create(  # A envenenado
                tenant_id=ta.id,
                usuario_id=ua.id,
                action="a1",
                resource_summary="r",
                payload_jsonb={"i": 1},
                hash_anterior=a0.hash_atual,
                hash_atual="f" * 64,
            )
        with run_in_tenant_context(tenant_id=tb.id, usuario_id=ub.id):
            for i in range(3):
                registrar_auditoria(
                    tenant_id=tb.id,
                    usuario_id=ub.id,
                    action=f"b{i}",
                    resource_summary="r",
                    payload={"i": i},
                )
        res = verificar_integridade_cadeia()
        assert res[str(tb.id)] == (True, 3, [])  # B íntegro
        assert res[str(ta.id)][0] is False  # A acusado, não contamina B

    def test_t7_contexto_perdido_sem_modo_sistema_levanta_42501(self) -> None:
        """Fail-loud preservado: contexto vazio sem modo_sistema → RAISE."""
        from django.db.utils import ProgrammingError

        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT set_config('app.tenant_ids','',true), "
                    "set_config('app.modo_sistema','',true);"
                )
            with pytest.raises(ProgrammingError) as exc:
                list(Auditoria.objects.all())
        msg = str(exc.value)
        assert "app.tenant_ids" in msg or "42501" in msg

    def test_t8_modo_sistema_nao_vaza_para_contexto_tenant(self) -> None:
        with run_as_system():
            ta = TenantFactory()
            ua = UsuarioFactory()
        # run_as_system fechou (SET LOCAL morreu no commit). Agora contexto
        # de tenant NÃO pode ter modo_sistema='1'.
        with run_in_tenant_context(tenant_id=ta.id, usuario_id=ua.id):
            with connection.cursor() as cur:
                cur.execute("SELECT current_setting('app.modo_sistema', true);")
                val = cur.fetchone()[0]
        assert val != "1"
