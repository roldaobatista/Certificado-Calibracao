"""Database router — separa app_user (runtime) de app_migrator (DDL).

Razao: ADR-0002 §2 — 2 roles distintas no Postgres, ambas NOBYPASSRLS.
- app_user (alias `default`): SELECT/INSERT/UPDATE/DELETE em runtime.
- app_migrator (alias `migrator`): apenas CREATE/ALTER em migrations.

Sem este router, migrations rodariam como app_user — que NAO tem CREATE
no schema. Falha por design (pratica que previne agente IA escrever
migration em endpoint operacional).
"""

from __future__ import annotations

import os
import sys
from typing import Any


def _esta_em_pytest() -> bool:
    """Detecta execucao sob pytest.

    Usa 3 sinais robustos:
    1. PYTEST_CURRENT_TEST em os.environ — setado pelo pytest durante test.
    2. 'pytest' importado em sys.modules — setado quando pytest-django carrega.
    3. sys.argv[0] contendo 'pytest' — chamada CLI direta.

    NAO usa comparacao de DATABASES.TEST.NAME — em PROD, ambos os aliases
    `default` e `migrator` apontam pro mesmo banco fisico runtime (`afere`),
    e settings.DATABASES['default']['TEST']['NAME'] sai como 'test_afere'
    (default Django) mesmo fora de pytest. Comparacao seria True em runtime
    real → liberava DDL no alias `default` em PROD, derrubando defesa em
    profundidade do ADR-0002 §2 (achado segurança-MED-1 do P5 F-C1).
    """
    if "PYTEST_CURRENT_TEST" in os.environ:
        return True
    if "pytest" in sys.modules:
        return True
    argv0 = sys.argv[0] if sys.argv else ""
    return "pytest" in argv0


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
        # Em runtime: migrations SO rodam no alias `migrator` (CREATE/ALTER).
        # Em test (pytest-django): cria test_afere via alias `default` e roda
        # migrate la — sem este fallback, test_afere fica vazio (router
        # bloqueia migrate em `default`) e toda a suite reporta "relation X
        # does not exist". Detecta pytest via env+sys.modules (NAO via
        # settings — comparacao por NAME daria True em PROD).
        if _esta_em_pytest():
            return True
        return db == "migrator"
