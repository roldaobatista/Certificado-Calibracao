"""Testes das ContextVars do multitenant. Puros (sem banco)."""

from __future__ import annotations

from uuid import uuid4

from src.infrastructure.multitenant.context import (
    active_tenant_context,
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

    def test_reset_restaura_default_das_tres_vars(self) -> None:
        # FA-M3: limpar_contexto() removida (armadilha). O padrão correto
        # é token+reset — provado aqui pras 3 vars.
        t1 = tenant_ids_context.set([uuid4()])
        t2 = active_tenant_context.set(uuid4())
        t3 = usuario_id_context.set(uuid4())

        tenant_ids_context.reset(t1)
        active_tenant_context.reset(t2)
        usuario_id_context.reset(t3)

        assert tenant_ids_context.get() == []
        assert active_tenant_context.get() is None
        assert usuario_id_context.get() is None
