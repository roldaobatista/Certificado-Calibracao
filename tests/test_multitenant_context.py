"""Testes das ContextVars do multitenant. Puros (sem banco)."""

from __future__ import annotations

from uuid import uuid4

from src.infrastructure.multitenant.context import (
    active_tenant_context,
    limpar_contexto,
    tenant_ids_context,
    usuario_id_context,
)


class TestContextVarsDefault:
    def test_tenant_ids_default_vazio(self) -> None:
        assert tenant_ids_context.get() == []

    def test_active_tenant_default_none(self) -> None:
        assert active_tenant_context.get() is None

    def test_usuario_id_default_none(self) -> None:
        assert usuario_id_context.get() is None


class TestContextVarsIsolamento:
    def test_set_reset_nao_vaza(self) -> None:
        tid1, tid2 = uuid4(), uuid4()
        token = tenant_ids_context.set([tid1, tid2])
        try:
            assert tenant_ids_context.get() == [tid1, tid2]
        finally:
            tenant_ids_context.reset(token)
        assert tenant_ids_context.get() == []

    def test_limpar_contexto_zera_tudo(self) -> None:
        tenant_ids_context.set([uuid4()])
        active_tenant_context.set(uuid4())
        usuario_id_context.set(uuid4())

        limpar_contexto()

        assert tenant_ids_context.get() == []
        assert active_tenant_context.get() is None
        assert usuario_id_context.get() is None
