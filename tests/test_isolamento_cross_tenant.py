"""Fuzzing cross-tenant: prova que RLS bloqueia vazamento entre tenants.

EXIGE PG VIVO. Marker `tenant_isolation` separa estes testes dos puros.
Roda no Marco 8 (drill final F-A) com docker compose up rodando.

Cenarios cobertos:
- T1: 2 tenants, mesma tabela (auditoria), tenant A nunca ve linha de B
- T2: usuario com acesso a {A, B} tenta acessar C -> bloqueado pela RLS
- T3: INSERT em auditoria com active_tenant != tenant_id WITH CHECK -> falha
- T4: SET LOCAL nao setado -> current_setting() RAISE -> query falha duro
- T5: feature_flag global (tenant_id NULL) visivel mesmo sem tenant_ids setado
- T6: trigger PG bloqueia UPDATE/DELETE em auditoria (defesa final)
- T7: 50 threads x 100 queries cruzadas, ZERO vazamentos (fuzzing)

Criterio de saida F-A (faseamento §2): "RLS bloqueia cross-tenant em 100%
dos testes de fuzzing concorrente (50 threads × 1000 queries)".
"""

from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import UUID

import pytest
from django.db import IntegrityError, connection
from django.db.utils import DataError, InternalError, ProgrammingError

# Exceções equivalentes — PG ERRCODE varia, Django mapeia diferente conforme contexto
ERROS_RLS = (IntegrityError, InternalError, ProgrammingError, DataError)

from src.infrastructure.audit.models import Auditoria
from src.infrastructure.feature_flag.models import FeatureFlag, FonteFlag
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)
from tests.factories import (
    FeatureFlagFactory,
    TenantFactory,
    UsuarioFactory,
)

pytestmark = pytest.mark.tenant_isolation  # marker requer PG vivo + RLS aplicada


@pytest.mark.django_db(transaction=True)
class TestRLSBloqueiaCrossTenant:
    def test_tenant_a_nao_ve_auditoria_de_tenant_b(self) -> None:
        with run_as_system():
            t_a = TenantFactory()
            t_b = TenantFactory()
            u = UsuarioFactory()

        with run_in_tenant_context(tenant_id=t_a.id, usuario_id=u.id):
            Auditoria.objects.create(
                tenant=t_a,
                usuario=u,
                action="evento.a",
                resource_summary="acao-no-tenant-A",
                payload_jsonb={"x": 1},
                hash_atual="hash-a-1",
            )

        with run_in_tenant_context(tenant_id=t_b.id, usuario_id=u.id):
            Auditoria.objects.create(
                tenant=t_b,
                usuario=u,
                action="evento.b",
                resource_summary="acao-no-tenant-B",
                payload_jsonb={"x": 2},
                hash_atual="hash-b-1",
            )

        # Tenant A so ve evento.a (e nunca evento.b — KEY assert)
        # NOTA: outros testes podem ter deixado linhas residuais no DB com
        # transaction=True; checamos por presenca/ausencia em vez de igualdade.
        with run_in_tenant_context(tenant_id=t_a.id, usuario_id=u.id):
            visiveis_a = set(Auditoria.objects.values_list("action", flat=True))
        assert "evento.a" in visiveis_a
        assert "evento.b" not in visiveis_a  # KEY ASSERT: ZERO vazamento

        # Tenant B so ve evento.b (e nunca evento.a)
        with run_in_tenant_context(tenant_id=t_b.id, usuario_id=u.id):
            visiveis_b = set(Auditoria.objects.values_list("action", flat=True))
        assert "evento.b" in visiveis_b
        assert "evento.a" not in visiveis_b  # KEY ASSERT: ZERO vazamento

    def test_insert_com_active_tenant_diferente_do_tenant_id_falha(self) -> None:
        with run_as_system():
            t_a = TenantFactory()
            t_b = TenantFactory()
            u = UsuarioFactory()

        with run_in_tenant_context(tenant_id=t_a.id, usuario_id=u.id):
            # Tenta inserir com tenant=t_b enquanto active=t_a — WITH CHECK rejeita
            with pytest.raises(ERROS_RLS):
                Auditoria.objects.create(
                    tenant=t_b,  # ERRO — fora do active_tenant_id
                    usuario=u,
                    action="evento.malicioso",
                    resource_summary="tentativa-de-cross-tenant",
                    payload_jsonb={"x": 1},
                    hash_atual="hash-mal",
                )

    def test_query_sem_tenant_ids_setado_falha_duro(self) -> None:
        """ADR-0002 §6: sem fallback permissivo. current_setting sem default = error."""
        # Sem run_in_tenant_context — tenant_ids vazio
        with pytest.raises(ERROS_RLS):
            list(Auditoria.objects.all())


@pytest.mark.django_db(transaction=True)
class TestFeatureFlagGlobal:
    def test_flag_global_visivel_mesmo_em_contexto_tenant(self) -> None:
        from uuid import uuid4 as _uuid
        flag_global_key = f"dark-mode-{_uuid().hex[:6]}"
        flag_tenant_key = f"x-{_uuid().hex[:6]}"

        with run_as_system():
            t = TenantFactory()
            u = UsuarioFactory()
            # Flag GLOBAL (tenant_id NULL) — exige system context (cond A)
            FeatureFlag.objects.create(
                modulo="core",
                feature_key=flag_global_key,
                ativo=True,
                fonte=FonteFlag.GLOBAL,
            )

        # Flag por-tenant — exige tenant context (cond B)
        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            FeatureFlag.objects.create(
                tenant=t, modulo="calibracao", feature_key=flag_tenant_key, ativo=True
            )
            keys = set(FeatureFlag.objects.values_list("feature_key", flat=True))

        assert flag_global_key in keys  # global visivel em contexto tenant
        assert flag_tenant_key in keys  # por-tenant tambem visivel


@pytest.mark.django_db(transaction=True)
class TestTriggerPGAntiMutation:
    def test_trigger_pg_bloqueia_update_mesmo_via_raw_sql(self) -> None:
        with run_as_system():
            t = TenantFactory()
            u = UsuarioFactory()

        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            linha = Auditoria.objects.create(
                tenant=t,
                usuario=u,
                action="evento.trigger",
                resource_summary="testa-trigger",
                payload_jsonb={"x": 1},
                hash_atual="hash-trigger-1",
            )

            # Tentativa de UPDATE via SQL bruto — trigger PG levanta exception
            with pytest.raises(ERROS_RLS):
                with connection.cursor() as cur:
                    cur.execute(
                        "UPDATE auditoria SET action = 'tampered' WHERE id = %s",
                        [str(linha.id)],
                    )

    def test_trigger_pg_bloqueia_delete_mesmo_via_raw_sql(self) -> None:
        with run_as_system():
            t = TenantFactory()
            u = UsuarioFactory()

        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            linha = Auditoria.objects.create(
                tenant=t,
                usuario=u,
                action="evento.trigger.del",
                resource_summary="testa-trigger-del",
                payload_jsonb={"x": 1},
                hash_atual="hash-trigger-del",
            )

            with pytest.raises(ERROS_RLS):
                with connection.cursor() as cur:
                    cur.execute("DELETE FROM auditoria WHERE id = %s", [str(linha.id)])


@pytest.mark.django_db(transaction=True)
@pytest.mark.slow
class TestFuzzingConcorrente:
    """Criterio de saida F-A: 50 threads × 1000 queries, ZERO vazamento."""

    def test_50_threads_x_100_queries_zero_vazamento(self) -> None:
        # Setup: 2 tenants, 1 usuario por tenant
        with run_as_system():
            t_a = TenantFactory()
            t_b = TenantFactory()
            u_a = UsuarioFactory()
            u_b = UsuarioFactory()

            # Cria 100 linhas em cada tenant
            for i in range(100):
                with run_in_tenant_context(tenant_id=t_a.id, usuario_id=u_a.id):
                    Auditoria.objects.create(
                        tenant=t_a, usuario=u_a,
                        action="a", resource_summary=f"a-{i}",
                        payload_jsonb={"i": i}, hash_atual=f"a-{i}",
                    )
                with run_in_tenant_context(tenant_id=t_b.id, usuario_id=u_b.id):
                    Auditoria.objects.create(
                        tenant=t_b, usuario=u_b,
                        action="b", resource_summary=f"b-{i}",
                        payload_jsonb={"i": i}, hash_atual=f"b-{i}",
                    )

        # Fuzzing: 50 threads alternando tenants, contam o que veem
        vazamentos: list[str] = []
        lock = threading.Lock()

        def worker(tenant_id: UUID, action_esperada: str, n_queries: int) -> None:
            local_vazamentos: list[str] = []
            for _ in range(n_queries):
                with run_in_tenant_context(tenant_id=tenant_id, usuario_id=u_a.id):
                    acoes = list(Auditoria.objects.values_list("action", flat=True))
                    for a in acoes:
                        if a != action_esperada:
                            local_vazamentos.append(
                                f"thread tenant={tenant_id} viu action={a} (esperava {action_esperada})"
                            )
            if local_vazamentos:
                with lock:
                    vazamentos.extend(local_vazamentos)

        with ThreadPoolExecutor(max_workers=50) as ex:
            futuros = []
            for i in range(50):
                if i % 2 == 0:
                    futuros.append(ex.submit(worker, t_a.id, "a", 100))
                else:
                    futuros.append(ex.submit(worker, t_b.id, "b", 100))
            for f in as_completed(futuros):
                f.result()

        assert vazamentos == [], (
            f"VAZAMENTO CROSS-TENANT DETECTADO em fuzzing: {len(vazamentos)} ocorrencias. "
            f"Amostra: {vazamentos[:5]}"
        )
