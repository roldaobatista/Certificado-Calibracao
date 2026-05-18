"""Database router — separa app_user (runtime) de app_migrator (DDL).

Razao: ADR-0002 §2 — 2 roles distintas no Postgres, ambas NOBYPASSRLS.
- app_user (alias `default`): SELECT/INSERT/UPDATE/DELETE em runtime.
- app_migrator (alias `migrator`): apenas CREATE/ALTER em migrations.

Sem este router, migrations rodariam como app_user — que NAO tem CREATE
no schema. Falha por design (pratica que previne agente IA escrever
migration em endpoint operacional).
"""

from __future__ import annotations

from typing import Any


class TenantMultiRoleRouter:
    """Migrations usam alias `migrator`; runtime usa `default`."""

    def db_for_read(self, model: Any, **hints: Any) -> str | None:
        return "default"

    def db_for_write(self, model: Any, **hints: Any) -> str | None:
        return "default"

    def allow_relation(self, obj1: Any, obj2: Any, **hints: Any) -> bool | None:
        # Mesmo banco fisico (so muda role) — relations sempre permitidas.
        return True

    def allow_migrate(
        self,
        db: str,
        app_label: str,
        model_name: str | None = None,
        **hints: Any,
    ) -> bool | None:
        # Migrations SO rodam no alias `migrator`.
        return db == "migrator"
