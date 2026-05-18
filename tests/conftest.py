"""Fixtures globais pytest.

Marco 2 vai expandir com TenantFactory, UsuarioFactory, AuditoriaFactory.
Marco 6 vai expandir com fixtures de fuzzing cross-tenant.
"""

import pytest


@pytest.fixture
def fase_atual() -> str:
    """Marca a fase em que estes testes rodam (usado em asserts de smoke)."""
    return "foundation-f-a"
