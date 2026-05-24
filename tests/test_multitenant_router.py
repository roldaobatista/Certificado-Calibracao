"""Testes do TenantMultiRoleRouter. Puros (sem banco).

Atualizado 2026-05-24 (P5 F-C1 conserto segurança-MED-1): router agora
detecta pytest via env+sys.modules em vez de comparar TEST.NAME — comparacao
dava True em PROD e derrubava defesa em profundidade ADR-0002 §2.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

from src.infrastructure.multitenant.router import TenantMultiRoleRouter, _esta_em_pytest


class TestRouter:
    router = TenantMultiRoleRouter()

    def test_runtime_le_do_default(self) -> None:
        assert self.router.db_for_read(model=None) == "default"

    def test_runtime_escreve_no_default(self) -> None:
        assert self.router.db_for_write(model=None) == "default"

    def test_migrations_em_pytest_default_liberado(self) -> None:
        """Pytest rodando -> PYTEST_CURRENT_TEST presente -> default liberado."""
        # Em pytest real, PYTEST_CURRENT_TEST esta setado pelo runner.
        assert _esta_em_pytest() is True
        assert self.router.allow_migrate(db="default", app_label="audit") is True
        assert self.router.allow_migrate(db="migrator", app_label="audit") is True

    def test_migrations_em_runtime_default_negado(self) -> None:
        """Runtime real (sem pytest): default negado, migrator aceito.

        Simula PROD removendo PYTEST_CURRENT_TEST + pytest de sys.modules +
        sys.argv. Garante que router NAO libera DDL em alias `default` em
        producao — defesa em profundidade ADR-0002 §2 (achado P5 F-C1
        segurança-MED-1).
        """
        env_sem_pytest = {
            k: v for k, v in os.environ.items() if k != "PYTEST_CURRENT_TEST"
        }
        modules_sem_pytest = {
            k: v for k, v in sys.modules.items() if not k.startswith("pytest")
        }
        with (
            patch.dict(os.environ, env_sem_pytest, clear=True),
            patch.dict(sys.modules, modules_sem_pytest, clear=True),
            patch.object(sys, "argv", ["manage.py", "runserver"]),
        ):
            assert _esta_em_pytest() is False
            assert self.router.allow_migrate(db="migrator", app_label="audit") is True
            assert self.router.allow_migrate(db="default", app_label="audit") is False

    def test_relations_sempre_permitidas(self) -> None:
        # Mesmo banco fisico, so muda role
        assert self.router.allow_relation(obj1=None, obj2=None) is True
