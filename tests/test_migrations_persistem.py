"""FA-A4 — rede de proteção: migration que reporta OK TEM que ter aplicado.

Auditoria F-A rodada 1: `manage.py migrate` no alias errado marca a
migration como aplicada em `django_migrations` mas NÃO executa o `RunSQL`
(router.allow_migrate só roda no alias `migrator`). Sem esta rede, RLS /
trigger / policy / função de segurança pode estar "aplicada" e não existir
no banco — e ninguém percebe até vazar dado entre tenants.

Este teste confere o catálogo REAL do Postgres contra o inventário mínimo
esperado. Se uma migration de segurança mentir, ESTE teste falha na suite.
"""

from __future__ import annotations

import pytest
from src.infrastructure.multitenant.verificacao_objetos import (
    FUNCOES_SEGURANCA,
    TABELAS_RLS,
    TRIGGERS_ANTI_MUTATION,
    verificar_objetos_seguranca,
)

pytestmark = pytest.mark.tenant_isolation  # exige PG real (catálogo)


@pytest.mark.django_db
def test_objetos_de_seguranca_existem_fisicamente_no_banco() -> None:
    """RLS+policies+triggers+funções das migrations existem de verdade."""
    problemas = verificar_objetos_seguranca()
    assert problemas == [], (
        "Migration reportou OK mas objeto de seguranca NAO existe no banco " f"(FA-A4): {problemas}"
    )


@pytest.mark.django_db
def test_inventario_minimo_nao_regrediu() -> None:
    """Guarda contra alguém esvaziar o inventário pra mascarar o teste 1."""
    assert len(TABELAS_RLS) >= 9
    assert len(TRIGGERS_ANTI_MUTATION) >= 6
    assert len(FUNCOES_SEGURANCA) >= 4
    assert "auditoria" in TABELAS_RLS
    assert "clientes" in TABELAS_RLS
    assert "require_tenant_ctx" in FUNCOES_SEGURANCA
