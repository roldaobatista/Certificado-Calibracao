"""Testes do TenantMultiRoleRouter. Puros (sem banco)."""

from __future__ import annotations

from src.infrastructure.multitenant.router import TenantMultiRoleRouter


class TestRouter:
    router = TenantMultiRoleRouter()

    def test_runtime_le_do_default(self) -> None:
        assert self.router.db_for_read(model=None) == "default"

    def test_runtime_escreve_no_default(self) -> None:
        assert self.router.db_for_write(model=None) == "default"

    def test_migrations_so_no_migrator(self) -> None:
        assert self.router.allow_migrate(db="migrator", app_label="audit") is True
        assert self.router.allow_migrate(db="default", app_label="audit") is False

    def test_relations_sempre_permitidas(self) -> None:
        # Mesmo banco fisico, so muda role
        assert self.router.allow_relation(obj1=None, obj2=None) is True
