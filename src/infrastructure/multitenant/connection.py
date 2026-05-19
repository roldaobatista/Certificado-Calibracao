"""Connection patcher + helpers de execucao com contexto de tenant.

Por que precisa: Django ORM em pool de conexoes NAO preserva `SET LOCAL`
entre requests. Quando uma conexao volta pro pool, o proximo request que
peega ela herda o estado. Sem o patcher, vazamento deterministico
(ADR-0002 v2 Auditor 2 C1).

Estrategia (3 camadas):
1. `connection_created` signal — sempre que abre conexao nova, reseta vars.
2. `setar_contexto_pg_na_conexao()` — chamado pelo TenantMiddleware no inicio
   de cada request, ja dentro de transacao (`SET LOCAL` vive ate o COMMIT).
3. `run_in_tenant_context()` context manager — pra jobs Procrastinate/Celery
   (rodam fora de request HTTP).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator
from uuid import UUID

from django.db import connection, connections, transaction
from django.db.backends.signals import connection_created
from django.dispatch import receiver

from .context import (
    active_tenant_context,
    tenant_ids_context,
    usuario_id_context,
)


@receiver(connection_created)
def _resetar_app_settings_na_conexao(sender: object, connection: Any, **kwargs: Any) -> None:
    """No checkout de conexao nova do pool, garante que `app.*` vem zerado.

    NAO podemos confiar que a sessao PG anterior limpou. Defesa em profundidade.
    """
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cur:
        cur.execute("RESET app.tenant_ids;")
        cur.execute("RESET app.active_tenant_id;")
        cur.execute("RESET app.usuario_id;")
        # FA-C1: modo_sistema libera leitura/escrita da cadeia de auditoria
        # "sistema" (tenant_id IS NULL) APENAS sob run_as_system. Resetar no
        # checkout impede vazar '1' pra um request normal que pegue a conexao.
        cur.execute("RESET app.modo_sistema;")


def setar_contexto_pg_na_conexao(
    tenant_ids: list[UUID],
    active_tenant: UUID | None,
    usuario_id: UUID | None,
    using: str = "default",
    modo_sistema: bool = False,
) -> None:
    """SET LOCAL nas 4 GUCs PG. Exige transacao aberta — chamador garante.

    Lista vira string CSV (PG `string_to_array(current_setting('app.tenant_ids'), ',')`
    nas policies — ADR-0002 v2 §6).

    `modo_sistema` (FA-C1): '1' libera a cadeia de auditoria sistema
    (tenant_id IS NULL); só `run_as_system` passa True. Qualquer contexto
    vazio SEM modo_sistema continua RAISE (fail-loud — ADR-0002 §6).
    """
    conn = connections[using]
    if conn.vendor != "postgresql":
        return

    tenant_ids_csv = ",".join(str(tid) for tid in tenant_ids) if tenant_ids else ""
    active_str = str(active_tenant) if active_tenant else ""
    usuario_str = str(usuario_id) if usuario_id else ""
    modo_sistema_str = "1" if modo_sistema else ""

    with conn.cursor() as cur:
        # set_config(name, value, is_local=true) = SET LOCAL — vive ate COMMIT
        cur.execute(
            "SELECT set_config('app.tenant_ids', %s, true), "
            "set_config('app.active_tenant_id', %s, true), "
            "set_config('app.usuario_id', %s, true), "
            "set_config('app.modo_sistema', %s, true);",
            [tenant_ids_csv, active_str, usuario_str, modo_sistema_str],
        )


@contextmanager
def run_in_tenant_context(
    tenant_id: UUID,
    usuario_id: UUID | None = None,
    using: str = "default",
) -> Iterator[None]:
    """Wrapper obrigatorio pra Procrastinate/Celery tasks que tocam tabela com RLS.

    Workers rodam fora de request HTTP — middleware NAO chega ate eles. Sem
    este wrapper, a task vaza (se policy mal escrita) ou falha (defesa correta).

    Uso:
        @procrastinate_app.task
        def emitir_certificado(tenant_id, cert_id, usuario_id):
            with run_in_tenant_context(UUID(tenant_id), UUID(usuario_id)):
                Certificado.objects.get(id=cert_id)  # RLS aplica
                ...
    """
    token_list = tenant_ids_context.set([tenant_id])
    token_active = active_tenant_context.set(tenant_id)
    token_user = usuario_id_context.set(usuario_id)
    try:
        with transaction.atomic(using=using):
            setar_contexto_pg_na_conexao(
                tenant_ids=[tenant_id],
                active_tenant=tenant_id,
                usuario_id=usuario_id,
                using=using,
                modo_sistema=False,  # contexto de tenant NUNCA é modo_sistema
            )
            yield
    finally:
        tenant_ids_context.reset(token_list)
        active_tenant_context.reset(token_active)
        usuario_id_context.reset(token_user)


@contextmanager
def run_in_user_context(
    usuario_id: UUID,
    using: str = "default",
) -> Iterator[None]:
    """Contexto AUTENTICADO PRÉ-TENANT: usuário identificado, sem tenant ativo.

    FB-C1+C3 (BLOQ #2). Fluxos legítimos: login pós-credencial, "listar meus
    tenants", qualquer `can()` pré-tenant. NÃO é `run_as_system` (tem dono: o
    usuário) nem `run_in_tenant_context` (não há tenant selecionado ainda).

    `app.usuario_id` setado + `tenant_ids=[]` + `modo_sistema=False`. A policy
    `authz_decisions` (authz/0005) lê/grava a cadeia pré-tenant POR-USUÁRIO
    com base nesse `app.usuario_id` — sem este contexto a cadeia pré-tenant
    bifurcaria silenciosamente (era o bug FB-C1⇄FB-C3).
    """
    token_list = tenant_ids_context.set([])
    token_active = active_tenant_context.set(None)
    token_user = usuario_id_context.set(usuario_id)
    try:
        with transaction.atomic(using=using):
            setar_contexto_pg_na_conexao(
                tenant_ids=[],
                active_tenant=None,
                usuario_id=usuario_id,
                using=using,
                modo_sistema=False,  # tem dono (usuário) — NÃO é modo_sistema
            )
            yield
    finally:
        tenant_ids_context.reset(token_list)
        active_tenant_context.reset(token_active)
        usuario_id_context.reset(token_user)


@contextmanager
def run_as_system(using: str = "default") -> Iterator[None]:
    """Contexto para operacoes do sistema (cron, manutencao) sem tenant.

    Limita o que pode ser tocado — tabelas com RLS bloqueiam (sem tenant_ids
    setado, current_setting('app.tenant_ids') retorna '' que NAO casa nenhuma
    linha; ADR-0002 v2 §6 sem fallback permissivo).

    Uso: provisionar tenant novo, limpar audit antigo (com aprovacao), etc.
    """
    token_list = tenant_ids_context.set([])
    token_active = active_tenant_context.set(None)
    token_user = usuario_id_context.set(None)
    try:
        with transaction.atomic(using=using):
            setar_contexto_pg_na_conexao(
                tenant_ids=[],
                active_tenant=None,
                usuario_id=None,
                using=using,
                modo_sistema=True,  # FA-C1: libera cadeia auditoria sistema
            )
            yield
    finally:
        tenant_ids_context.reset(token_list)
        active_tenant_context.reset(token_active)
        usuario_id_context.reset(token_user)
