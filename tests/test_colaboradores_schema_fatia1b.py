"""Testes PG-real do schema colaboradores — Fatia 1b (T-COL-030).

Verifica o comportamento real do banco (RLS, índices parciais, CHECKs, trigger)
usando TenantFactory + run_in_tenant_context (padrão do projeto) e SQL direto
para verificações de infraestrutura PG. Espelha o molde dos testes de
precificacao (tests/test_precificacao_schema_fatia1b.py).

Convenções:
  - @pytest.mark.django_db(transaction=True): testes que criam dados cross-tenant
    (TransactionTestCase — isolamento de transação real). Seeds são restaurados
    pelo conftest autouse _restaura_seeds_apos_truncate antes de cada um.
  - @pytest.mark.django_db(transaction=True) também para testes de seed: garante
    que o conftest re-aplica seeds (dados não sobrevivem rollback em não-transacional
    quando banco de teste foi recriado sem seeds persistentes).
  - TenantFactory + run_in_tenant_context: para INSERT com RLS (padrão M8/precificacao).
  - SQL direto via cursor: para verificações de metadados PG (pg_class, pg_policies, etc.)
    e para cenários de UNHAPPY path que precisam de controle fino de session settings.

Testes obrigatórios:
  1. RLS UNHAPPY — acesso cross-tenant bloqueado x4 tabelas-tenant
  2. UNIQUE CPF parcial — re-cadastro após soft-delete é PERMITIDO
  3. UNIQUE DONO parcial — 2º DONO ativo → erro de índice único
  4. CHECK comissão fora 0..100 → erro
  5. Trigger BEFORE DELETE bloqueia delete físico com filho
  6. catalogo_habilidade global — legível por 2 tenants distintos
  7. Seeds authz colaboradores.* presentes
  8. Seeds catálogo habilidade presentes
"""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import Iterator

import pytest
from django.db import connection, transaction
from django.db import utils as db_utils
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

# =============================================================
# Helpers
# =============================================================


@contextlib.contextmanager
def _espera_erro_pg() -> Iterator[None]:
    """Savepoint atômico para isolar violação de constraint PG em teste transacional.

    Após qualquer erro de constraint/trigger no PostgreSQL, a transação fica em
    estado abortado (InFailedSqlTransaction). Sem SAVEPOINT, todos os comandos
    seguintes falham. Este helper usa `transaction.atomic()` (que cria SAVEPOINT
    real em contexto transacional) para recuperar o estado após a exceção esperada.

    Uso:
        with pytest.raises(db_utils.IntegrityError):
            with _espera_erro_pg():
                cur.execute("INSERT ... com violação de CHECK")
        # transação está limpa para o próximo comando
    """
    try:
        with transaction.atomic():
            yield
    except Exception:
        raise


def _insert_colaborador_sql(
    cur,
    tenant_id: uuid.UUID,
    cpf: str = "12345678901",
    comissao: str = "10.00",
) -> uuid.UUID:
    """Insere colaborador com SQL direto (dentro de contexto de tenant ativo)."""
    cid = uuid.uuid4()
    cur.execute(
        "INSERT INTO colaborador "
        "(id, tenant_id, nome, cpf, email, telefone, vinculo, data_admissao, "
        "comissao_default_pct, observacao, criado_em, atualizado_em) "
        "VALUES (%s, %s, 'Fulano', %s, 'f@f.com', '11999', 'clt', '2024-01-01', "
        "%s, '', NOW(), NOW()) RETURNING id;",
        [str(cid), str(tenant_id), cpf, comissao],
    )
    row = cur.fetchone()
    assert row is not None
    return row[0]


def _insert_colaborador_soft_delete(
    cur,
    tenant_id: uuid.UUID,
    cpf: str,
) -> uuid.UUID:
    """Insere colaborador já soft-deletado (sai do índice parcial CPF)."""
    cid = uuid.uuid4()
    cur.execute(
        "INSERT INTO colaborador "
        "(id, tenant_id, nome, cpf, email, telefone, vinculo, data_admissao, "
        "comissao_default_pct, observacao, deletado_em, criado_em, atualizado_em) "
        "VALUES (%s, %s, 'Fulano', %s, 'f@f.com', '11999', 'clt', '2024-01-01', "
        "10.00, '', NOW(), NOW(), NOW()) RETURNING id;",
        [str(cid), str(tenant_id), cpf],
    )
    row = cur.fetchone()
    assert row is not None
    return row[0]


# =============================================================
# 1. RLS UNHAPPY — cross-tenant bloqueado x4 tabelas
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_rls_colaborador_cross_tenant() -> None:
    """Colaborador do tenant A não é visível para tenant B."""
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()

    # Cria colaborador como tenant A
    with run_in_tenant_context(tenant_a.id):
        with connection.cursor() as cur:
            cid = _insert_colaborador_sql(cur, tenant_a.id, cpf="11111111111")

    # Consulta como tenant B — deve ser invisível (RLS)
    with run_in_tenant_context(tenant_b.id):
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM colaborador WHERE id = %s;", [str(cid)])
            row = cur.fetchone()
            assert row is not None
            assert row[0] == 0, "RLS falhou: colaborador de A visível para B"


@pytest.mark.django_db(transaction=True)
def test_rls_colaborador_papel_cross_tenant() -> None:
    """Papel do colaborador do tenant A não é visível para tenant B."""
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()

    with run_in_tenant_context(tenant_a.id):
        with connection.cursor() as cur:
            cid = _insert_colaborador_sql(cur, tenant_a.id, cpf="22222222201")
            pid = uuid.uuid4()
            cur.execute(
                "INSERT INTO colaborador_papel "
                "(id, colaborador_id, tenant_id, papel, data_inicio, pendencia_cnh, criado_em) "
                "VALUES (%s, %s, %s, 'tecnico', '2024-01-01', FALSE, NOW());",
                [str(pid), str(cid), str(tenant_a.id)],
            )

    with run_in_tenant_context(tenant_b.id):
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM colaborador_papel WHERE id = %s;", [str(pid)])
            row = cur.fetchone()
            assert row is not None
            assert row[0] == 0, "RLS falhou: papel de A visível para B"


@pytest.mark.django_db(transaction=True)
def test_rls_colaborador_habilidade_cross_tenant() -> None:
    """Habilidade do tenant A não é visível para tenant B."""
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()

    with run_in_tenant_context(tenant_a.id):
        with connection.cursor() as cur:
            cid = _insert_colaborador_sql(cur, tenant_a.id, cpf="33333333301")
            hid = uuid.uuid4()
            cur.execute(
                "INSERT INTO colaborador_habilidade "
                "(id, colaborador_id, tenant_id, descricao_livre, nivel, data_avaliacao, criado_em) "
                "VALUES (%s, %s, %s, 'Técnico PLC', 'capacitado', '2024-01-01', NOW());",
                [str(hid), str(cid), str(tenant_a.id)],
            )

    with run_in_tenant_context(tenant_b.id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM colaborador_habilidade WHERE id = %s;", [str(hid)]
            )
            row = cur.fetchone()
            assert row is not None
            assert row[0] == 0, "RLS falhou: habilidade de A visível para B"


@pytest.mark.django_db(transaction=True)
def test_rls_colaborador_documento_cross_tenant() -> None:
    """Documento do tenant A não é visível para tenant B."""
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()

    with run_in_tenant_context(tenant_a.id):
        with connection.cursor() as cur:
            cid = _insert_colaborador_sql(cur, tenant_a.id, cpf="44444444401")
            did = uuid.uuid4()
            cur.execute(
                "INSERT INTO colaborador_documento "
                "(id, colaborador_id, tenant_id, tipo, storage_key, sha256, data_upload, criado_em) "
                "VALUES (%s, %s, %s, 'cnh', 'storage/doc.pdf', %s, NOW(), NOW());",
                [str(did), str(cid), str(tenant_a.id), "a" * 64],
            )

    with run_in_tenant_context(tenant_b.id):
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM colaborador_documento WHERE id = %s;", [str(did)])
            row = cur.fetchone()
            assert row is not None
            assert row[0] == 0, "RLS falhou: documento de A visível para B"


# =============================================================
# 2. UNIQUE CPF parcial — re-cadastro após soft-delete PERMITIDO
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_unique_cpf_parcial_permite_recadastro_apos_soft_delete() -> None:
    """Soft-delete remove o colaborador do índice parcial; re-cadastro com mesmo CPF é válido."""
    tenant = TenantFactory()

    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            # Cadastra colaborador e soft-deleta
            cid1 = _insert_colaborador_soft_delete(cur, tenant.id, cpf="55555555501")

            # Re-cadastra com mesmo CPF — deve funcionar
            cid2 = _insert_colaborador_sql(cur, tenant.id, cpf="55555555501")
            assert cid1 != cid2, "Segundo cadastro com mesmo CPF após soft-delete falhou"

            # Terceiro ativo com mesmo CPF — deve violar índice
            with pytest.raises(db_utils.IntegrityError):
                _insert_colaborador_sql(cur, tenant.id, cpf="55555555501")


# =============================================================
# 3. UNIQUE DONO parcial — 2º DONO ativo → violação de índice
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_partial_unique_dono() -> None:
    """Apenas um papel DONO ativo por tenant (INV-COL-DONO-UNICO)."""
    tenant = TenantFactory()

    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cid1 = _insert_colaborador_sql(cur, tenant.id, cpf="66666666601")
            cid2 = _insert_colaborador_sql(cur, tenant.id, cpf="66666666602")

            # Primeiro DONO ativo — ok
            pid1 = uuid.uuid4()
            cur.execute(
                "INSERT INTO colaborador_papel "
                "(id, colaborador_id, tenant_id, papel, data_inicio, pendencia_cnh, criado_em) "
                "VALUES (%s, %s, %s, 'dono', '2024-01-01', FALSE, NOW());",
                [str(pid1), str(cid1), str(tenant.id)],
            )

            # Segundo DONO ativo — deve violar uq_col_papel_dono_unico
            pid2 = uuid.uuid4()
            with pytest.raises(db_utils.IntegrityError):
                cur.execute(
                    "INSERT INTO colaborador_papel "
                    "(id, colaborador_id, tenant_id, papel, data_inicio, pendencia_cnh, criado_em) "
                    "VALUES (%s, %s, %s, 'dono', '2024-06-01', FALSE, NOW());",
                    [str(pid2), str(cid2), str(tenant.id)],
                )


# =============================================================
# 4. CHECK comissão fora 0..100 → erro
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_check_comissao_range() -> None:
    """Comissão fora do intervalo 0..100 viola ck_col_comissao_range."""
    tenant = TenantFactory()

    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            # 101% → deve violar CHECK
            # _espera_erro_pg cria savepoint para isolar a violação: após erro PG
            # a transação fica em estado abortado sem SAVEPOINT/ROLLBACK TO.
            with pytest.raises(db_utils.IntegrityError):
                with _espera_erro_pg():
                    _insert_colaborador_sql(cur, tenant.id, cpf="77777777701", comissao="101.00")

            # -1% → deve violar CHECK
            with pytest.raises(db_utils.IntegrityError):
                with _espera_erro_pg():
                    _insert_colaborador_sql(cur, tenant.id, cpf="77777777702", comissao="-1.00")

            # 0% e 100% → válidos (limites inclusivos do CHECK)
            _insert_colaborador_sql(cur, tenant.id, cpf="77777777703", comissao="0.00")
            _insert_colaborador_sql(cur, tenant.id, cpf="77777777704", comissao="100.00")


# =============================================================
# 5. Trigger BEFORE DELETE bloqueia delete físico com filho
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_trigger_block_delete_com_filho() -> None:
    """Trigger col_colaborador_block_delete impede DELETE físico quando há filho."""
    tenant = TenantFactory()

    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cid = _insert_colaborador_sql(cur, tenant.id, cpf="88888888801")

            # Insere papel filho
            pid = uuid.uuid4()
            cur.execute(
                "INSERT INTO colaborador_papel "
                "(id, colaborador_id, tenant_id, papel, data_inicio, pendencia_cnh, criado_em) "
                "VALUES (%s, %s, %s, 'tecnico', '2024-01-01', FALSE, NOW());",
                [str(pid), str(cid), str(tenant.id)],
            )

            # Tenta DELETE físico — trigger deve bloquear com INV-COL-INATIVO.
            # _espera_erro_pg cria savepoint: exceção do trigger aborta a transação PG;
            # sem SAVEPOINT/ROLLBACK TO comandos seguintes falham com InFailedSqlTransaction.
            with pytest.raises(Exception, match="INV-COL-INATIVO"):
                with _espera_erro_pg():
                    cur.execute("DELETE FROM colaborador WHERE id = %s;", [str(cid)])

            # Colaborador sem filhos — DELETE físico deve funcionar sem exceção
            cid2 = _insert_colaborador_sql(cur, tenant.id, cpf="88888888802")
            cur.execute("DELETE FROM colaborador WHERE id = %s;", [str(cid2)])

            # Verifica que o colaborador sem filho foi removido
            cur.execute(
                "SELECT COUNT(*) FROM colaborador WHERE id = %s;", [str(cid2)]
            )
            row = cur.fetchone()
            assert row is not None
            assert row[0] == 0, "DELETE de colaborador sem filho não removeu o registro"


# =============================================================
# 6. catalogo_habilidade global — leitura por 2 tenants distintos
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_catalogo_habilidade_global() -> None:
    """catalogo_habilidade é acessível por qualquer tenant (sem RLS)."""
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()

    # Como tenant A
    with run_in_tenant_context(tenant_a.id):
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM catalogo_habilidade;")
            row = cur.fetchone()
            assert row is not None
            count_a = row[0]

    # Como tenant B — mesmo catálogo deve ser visível
    with run_in_tenant_context(tenant_b.id):
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM catalogo_habilidade;")
            row = cur.fetchone()
            assert row is not None
            count_b = row[0]

    assert count_a == count_b, (
        f"catalogo_habilidade retornou contagens diferentes: A={count_a}, B={count_b}"
    )
    assert count_a >= 10, f"Catálogo global tem menos de 10 habilidades ({count_a})"


# =============================================================
# 7. Seeds authz presentes
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_seed_authz_presente() -> None:
    """10 ações colaboradores.* devem estar presentes na tabela authz_perfil_acao."""
    acoes = [
        "colaboradores.cadastrar",
        "colaboradores.editar",
        "colaboradores.desligar",
        "colaboradores.ver",
        "colaboradores.ver_pii",
        "colaboradores.gerir_papel",
        "colaboradores.gerir_habilidade",
        "colaboradores.ver_comissao",
        "colaboradores.ver_auditoria",
        "colaboradores.consultar_elegiveis",
    ]
    with connection.cursor() as cur:
        cur.execute(
            "SELECT COUNT(DISTINCT acao) FROM authz_perfil_acao WHERE acao = ANY(%s);",
            [acoes],
        )
        row = cur.fetchone()
        assert row is not None
        count = row[0]
    assert count == 10, (
        f"Esperado 10 ações colaboradores.* no authz_perfil_acao, encontrado {count}"
    )


# =============================================================
# 8. Seeds catálogo presentes
# =============================================================


@pytest.mark.django_db(transaction=True)
def test_seed_catalogo_presente() -> None:
    """16 habilidades do catálogo global devem estar presentes."""
    codigos_esperados = [
        "massa", "volume", "temperatura", "dimensional", "pressao",
        "eletricidade", "tempo_frequencia", "vazao", "torque", "dureza",
        "acustica", "otica", "umidade", "ph_condutividade",
        "laboratorio_geral", "inspecao_metrologia_legal",
    ]
    with connection.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM catalogo_habilidade WHERE codigo = ANY(%s);",
            [codigos_esperados],
        )
        row = cur.fetchone()
        assert row is not None
        count = row[0]
    assert count == 16, f"Esperado 16 habilidades no catálogo, encontrado {count}"


@pytest.mark.django_db(transaction=True)
def test_seed_catalogo_grandezas() -> None:
    """Habilidades com grandeza não-nula devem existir (ao menos 14 das 16)."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM catalogo_habilidade WHERE grandeza IS NOT NULL;"
        )
        row = cur.fetchone()
        assert row is not None
        count = row[0]
    assert count >= 14, f"Esperado >=14 habilidades com grandeza, encontrado {count}"
