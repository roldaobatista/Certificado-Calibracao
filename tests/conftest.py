"""Fixtures globais pytest.

Marco 2 vai expandir com TenantFactory, UsuarioFactory, AuditoriaFactory.
Marco 6 vai expandir com fixtures de fuzzing cross-tenant.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

import pytest
from django.apps import apps as django_apps
from django.db import connection

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


@pytest.fixture
def fase_atual() -> str:
    """Marca a fase em que estes testes rodam (usado em asserts de smoke)."""
    return "foundation-f-a"


# =============================================================
# T-SAN-PERFIL-023 (Sprint 2 ADR-0067) — fixtures parametrizadas por perfil.
#
# 4 fixtures explicitas pra cenarios regulados — eliminam o "perfil D default
# silencioso" que mascarava bug que so aparece em perfil A (FAIL L9 da auditoria
# 10 lentes 2026-05-27).
#
# Uso:
#     def test_emissao_certificado_acreditado(tenant_a):
#         # tenant_a ja tem perfil='A' + numero RBC fake + ilac_mra_aderido=True
#         ...
#
#     def test_balancas_solution_caminho(tenant_b):
#         # tenant_b = caminho Roldao/dogfooding
#         ...
#
# Marcador pytest correspondente (T-SAN-PERFIL-027):
#     @pytest.mark.perfil("A")        # documentacao + parametrize matrix futura
# =============================================================


@pytest.fixture
def tenant_a(db):
    """Tenant acreditado RBC/CGCRE — perfil A + numero RBC fake + ILAC-MRA."""
    from tests.factories import TenantFactory

    return TenantFactory(perfil_a=True)


@pytest.fixture
def tenant_b(db):
    """Tenant rastreavel nao-acreditado — caminho Balancas Solution dogfooding (Roldao)."""
    from tests.factories import TenantFactory

    return TenantFactory(perfil_b=True)


@pytest.fixture
def tenant_c(db):
    """Tenant em preparacao para acreditar — trilha D->A (BIG-03 do discovery)."""
    from tests.factories import TenantFactory

    return TenantFactory(perfil_c=True)


@pytest.fixture
def tenant_d(db):
    """Tenant comercial puro — sem rituais ISO 17025 (PII retencao 5a)."""
    from tests.factories import TenantFactory

    return TenantFactory(perfil_d=True)


# =============================================================
# TASK #9 (2026-05-24) — restaura seeds apos limpeza transacional.
#
# Problema: pytest-django com `@pytest.mark.django_db(transaction=True)`
# usa TransactionTestCase, que limpa todas as tabelas entre tests
# (defesa pra evitar leak cross-test). A consequencia: tabelas
# populadas via migration RunPython (`*seed*.py`) ficam vazias do
# segundo test em diante, e endpoints recebem `rbac_denied` porque
# a matriz perfil x acao desapareceu.
#
# Solucao: fixture autouse function-scope que detecta `authz_perfil`
# vazio e re-aplica TODAS as migrations seed (convencao uniforme:
# arquivo `*seed*.py` em `src/infrastructure/*/migrations/` com
# funcao `seed(apps, schema_editor)`).
#
# Alternativa rejeitada: `serialized_rollback=True` em cada
# `django_db` marker — exige modificar dezenas de arquivos de teste
# por uma mesma razao (drift garantido). Outra rejeitada: hardcoded
# INSERTs no conftest — frágil, sai de sincronia com migrations.
# =============================================================

# Catalogo das migrations seed conhecidas (descobertas via:
# `find src/infrastructure -name "*seed*.py" -path "*/migrations/*"`).
# Cada tupla: (app_label, migration_module_name).
_SEED_MIGRATIONS: list[tuple[str, str]] = [
    ("authz", "0003_seed_perfis"),
    ("authz", "0007_seed_perfis_marco_3_4"),
    ("clientes", "0003_seed_authz_acoes"),
    ("clientes", "0007_seed_authz_mesclar"),
    ("clientes", "0010_seed_authz_bloquear"),
    ("clientes", "0011_seed_authz_visao360"),
    ("clientes", "0013_seed_authz_importar"),
    ("equipamentos", "0004_seed_authz_acoes"),
    ("equipamentos", "0005_seed_authz_criar"),
    ("equipamentos", "0009_seed_authz_ficha360"),
    ("equipamentos", "0013_seed_authz_transferir"),
    ("equipamentos", "0015_seed_authz_revogar_consentimento"),
    ("equipamentos", "0018_seed_authz_sucatear"),
    ("equipamentos", "0020_seed_authz_receber"),
    ("equipamentos", "0023_seed_authz_devolver"),
    ("equipamentos", "0025_seed_authz_provisorio"),
    ("equipamentos", "0027_seed_authz_versionar"),
    ("ordens_servico", "0004_seed_tipo_atividade_config"),
    ("ordens_servico", "0013_seed_authz_os"),
    ("responsavel_tecnico", "0002_seed_authz_acoes"),
    ("calibracao", "0013_seed_authz_calibracao"),
    ("calibracao", "0021_seed_authz_registrar_recebimento"),
    ("calibracao", "0022_seed_authz_m4_rest_completo"),
    ("padroes", "0005_seed_authz_padroes"),
    ("padroes", "0007_seed_authz_vinculo_dossie_carta"),
    ("escopos_cmc", "0005_seed_authz_escopos_cmc"),
    ("procedimentos_calibracao", "0005_seed_authz_procedimentos"),
    ("certificados", "0006_seed_authz_certificados"),
    ("licencas_acreditacoes", "0005_seed_authz_licencas"),
    ("fiscal", "0005_seed_authz_fiscal"),
    ("configuracoes_sistema", "0006_seed_authz_configuracoes"),
    ("produtos_pecas_servicos", "0006_seed_authz_catalogo"),
    ("precificacao", "0006_seed_authz_precificacao"),
    ("precificacao", "0009_seed_authz_precificacao_acoes_faltantes"),
    ("colaboradores", "0005_seed_authz_colaboradores"),
    ("colaboradores", "0006_seed_catalogo_habilidade"),
]


def _seeds_estao_vazios() -> bool:
    """True se a matriz authz nao tem perfis-modelo (tenant_id NULL).

    Usamos `authz_perfil WHERE tenant_id IS NULL` como sentinela porque
    a migration 0003_seed_perfis insere os 4 perfis base com tenant=NULL.
    """
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM authz_perfil WHERE tenant_id IS NULL;")
        return cur.fetchone()[0] == 0


def _aplicar_seed(app_label: str, migration_name: str) -> None:
    """Importa a migration e chama `seed(apps, schema_editor)`.

    Captura APENAS `ModuleNotFoundError` (caso entry de `_SEED_MIGRATIONS`
    desincronize com filesystem — migration renomeada/removida). Toda
    outra excecao propaga: como `_seeds_estao_vazios()` gate-ia execucao
    e o teste transacional acabou de fazer TRUNCATE, a tabela esta limpa
    quando o seed roda — IntegrityError aqui seria bug de migration que
    precisa ser visto, NAO engolido.
    """
    # ADR-0072: modulos metrologia/* ficam aninhados; o app_label ("padroes")
    # nao casa 1:1 com o caminho do modulo. Mapa para os apps aninhados.
    _APP_MODULE_SUBPATH = {
        "padroes": "metrologia.padroes",
        "escopos_cmc": "metrologia.escopos_cmc",
        "procedimentos_calibracao": "metrologia.procedimentos_calibracao",
        "licencas_acreditacoes": "metrologia.licencas_acreditacoes",
    }
    sub = _APP_MODULE_SUBPATH.get(app_label, app_label)
    module_path = f"src.infrastructure.{sub}.migrations.{migration_name}"
    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError:
        return
    # Convenção primária: função `seed(apps, schema_editor)`. Algumas migrations
    # (ex: ordens_servico 0004) nomeiam o restore `seed_forward` (par com
    # `seed_reverse`); sem este fallback, o conftest fazia no-op e o dado-semente
    # NÃO era restaurado após TRUNCATE transacional (achado da auditoria 2026-05-29).
    seed_func = getattr(mod, "seed", None) or getattr(mod, "seed_forward", None)
    if seed_func is None:
        return
    with connection.schema_editor(atomic=False) as schema_editor:
        seed_func(django_apps, schema_editor)


def _restaurar_seeds() -> None:
    """Roda todas as migrations seed na ordem do catalogo."""
    for app_label, migration_name in _SEED_MIGRATIONS:
        _aplicar_seed(app_label, migration_name)


@pytest.fixture(autouse=True)
def _restaura_seeds_apos_truncate(request: FixtureRequest, db) -> None:  # type: ignore[no-untyped-def]
    """Antes de cada teste transacional, garante que seeds estao populados.

    Detecta marker `transaction=True` (TransactionTestCase via pytest-django).
    Sem `transaction`, TestCase usa rollback e seeds persistem do setup
    de migration — nada a fazer.
    """
    marker = request.node.get_closest_marker("django_db")
    is_transactional = bool(
        marker and marker.kwargs.get("transaction", False)
    )
    if not is_transactional:
        return
    if _seeds_estao_vazios():
        _restaurar_seeds()
