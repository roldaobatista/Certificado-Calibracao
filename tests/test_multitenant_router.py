"""Testes do TenantMultiRoleRouter. Puros (sem banco)."""

from __future__ import annotations

from unittest.mock import patch

from src.infrastructure.multitenant.router import TenantMultiRoleRouter


class TestRouter:
    router = TenantMultiRoleRouter()

    def test_runtime_le_do_default(self) -> None:
        assert self.router.db_for_read(model=None) == "default"

    def test_runtime_escreve_no_default(self) -> None:
        assert self.router.db_for_write(model=None) == "default"

    def test_migrations_so_no_migrator_em_runtime(self) -> None:
        """Runtime (sem TEST.NAME comum): default eh negado, migrator e
        aceito — defesa em profundidade ADR-0002 §2."""
        databases_runtime = {
            "default": {"TEST": {"NAME": "test_afere"}},
            "migrator": {"TEST": {"NAME": "test_outro"}},
        }
        with patch("django.conf.settings.DATABASES", databases_runtime):
            assert self.router.allow_migrate(db="migrator", app_label="audit") is True
            assert self.router.allow_migrate(db="default", app_label="audit") is False

    def test_migrations_liberadas_em_test_quando_default_e_migrator_compartilham_db(
        self,
    ) -> None:
        """Em test: pytest-django cria test DB via alias `default`; default e
        migrator apontam pro MESMO test_afere fisico (config/settings/base.py
        DATABASES). Router libera default tambem — senao test DB fica sem
        tabelas (regressao detectada 2026-05-24)."""
        databases_test = {
            "default": {"TEST": {"NAME": "test_afere"}},
            "migrator": {"TEST": {"NAME": "test_afere"}},
        }
        with patch("django.conf.settings.DATABASES", databases_test):
            assert self.router.allow_migrate(db="default", app_label="audit") is True
            assert self.router.allow_migrate(db="migrator", app_label="audit") is True

    def test_relations_sempre_permitidas(self) -> None:
        # Mesmo banco fisico, so muda role
        assert self.router.allow_relation(obj1=None, obj2=None) is True
