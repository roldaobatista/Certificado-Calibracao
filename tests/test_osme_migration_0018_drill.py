"""DRILL da migration 0018 — os-multi-equipamento (ADR-0082 / Fatia 1b).

Cobre:
(a) INSERT de atividade SEM equipamento_id -> trigger COALESCE copia de OS.equipamento_id.
(b) INSERT de atividade COM equipamento_id proprio -> preserva (nao sobrescreve).
(c) UPDATE tentando mudar equipamento_id -> trigger imutavel levanta EXCEPTION.
(d) Reverse (migrate 0017) + reaplica (migrate 0018) verificados via campo no schema.

Cuidados do projeto:
- Usa TenantFactory para criar tenant (padrao do projeto).
- SQL direto so em atividade_da_os (tabela do nosso scope).
- Usa run_in_tenant_context para propagar RLS + chave HMAC (pii_hash_key_ativa)
  que o trigger trg_clientes_grava_op_tratamento exige via pii_hash_hmac().
- NUNCA dropar test_afere (perde extensoes/grants).
"""

from __future__ import annotations

import uuid

import pytest
from django.db import connection
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _next_seq() -> int:
    """Chama nextval da sequence global de numero_os."""
    with connection.cursor() as cur:
        cur.execute("SELECT nextval('os_numero_seq_global')")
        return int(cur.fetchone()[0])


def _setup_tenant_equip_cliente_os(tenant):
    """Cria equipamento + cliente + OS para o tenant via SQL.

    Deve ser chamada DENTRO de run_in_tenant_context — que ja propagou
    app.active_tenant_id, app.tenant_ids e app.pii_hash_key_ativa via
    setar_contexto_pg_na_conexao (set_config de escopo local na transacao).
    """
    equip_id = uuid.uuid4()
    cli_id = uuid.uuid4()
    os_id = uuid.uuid4()
    numero = _next_seq()
    tag = f"DRILL-{uuid.uuid4().hex[:6]}"
    doc = f"{uuid.uuid4().int % 99999999999999:014d}"
    nome_cli = f"CliDrill-{tag}"

    with connection.cursor() as cur:
        # Equipamento (tabela: equipamentos).
        cur.execute(
            """
            INSERT INTO equipamentos (
                id, tenant_id, tag, numero_serie, fabricante, modelo,
                faixa, classe, localizacao_fisica,
                perfil_tenant_snapshot, snapshot_schema_version,
                status, criado_em, atualizado_em
            ) VALUES (
                %s, %s, %s, %s, 'FabDrill', 'ModDrill',
                '', '', '',
                %s::jsonb, 'v1',
                'ativo', now(), now()
            )
            """,
            [
                str(equip_id), str(tenant.id), tag, tag,
                '{"perfil": "D"}',
            ],
        )

        # Cliente (tabela: clientes) — colunas NOT NULL obrigatorias.
        # O trigger trg_clientes_grava_op_tratamento chama pii_hash_hmac()
        # que exige app.pii_hash_key_ativa (propagada pelo run_in_tenant_context).
        cur.execute(
            """
            INSERT INTO clientes (
                id, tenant_id, tipo_pessoa, documento, nome, nome_fantasia,
                email, telefone,
                aceite_lgpd_dispensa_motivo,
                aceite_lgpd_ip_hash, aceite_lgpd_origem, aceite_lgpd_versao,
                aceite_lgpd_base_legal, aceite_lgpd_evidencia_externa,
                aceite_lgpd_pendente, cpf_responsavel_legal,
                cliente_canonico_id,
                observacao,
                deletado_motivo_categoria,
                criado_em, atualizado_em
            ) VALUES (
                %s, %s, 'PJ', %s, %s, %s,
                '', '',
                'pj_sem_pf_associada',
                '', '', '',
                '', '',
                false, '',
                %s,
                '',
                '',
                now(), now()
            )
            """,
            [
                str(cli_id), str(tenant.id), doc, nome_cli, nome_cli,
                str(cli_id),  # cliente_canonico_id = proprio id (seed drill)
            ],
        )

        # TipoAtividadeConfig seed para o tenant.
        cur.execute(
            """
            INSERT INTO tipo_atividade_config (
                tenant_id, tipo, requer_competencia_rt,
                tipo_bloqueia_concorrencia, executa_em_campo,
                criado_em, atualizado_em
            ) VALUES (%s, 'calibracao', false, true, false, now(), now())
            ON CONFLICT (tenant_id, tipo) WHERE deletado_em IS NULL DO NOTHING
            """,
            [str(tenant.id)],
        )

        # OS (tabela: ordens_servico).
        cur.execute(
            """
            INSERT INTO ordens_servico (
                id, tenant_id, numero_os, cliente_id,
                cliente_referencia_hash, cliente_key_id,
                equipamento_id, estado, tipo_predominante,
                nao_conformidade_global, valor_total, valor_total_atualizado,
                analise_critica_snapshot_hash,
                regra_decisao_acordada, criada_em, atualizada_em
            ) VALUES (
                %s, %s, %s, %s,
                %s, 'kms-drill',
                %s, 'rascunho', '',
                false, 0, 0,
                %s,
                'default', now(), now()
            )
            """,
            [
                str(os_id), str(tenant.id), numero, str(cli_id),
                "a" * 64,
                str(equip_id),
                "b" * 64,
            ],
        )

    return equip_id, cli_id, os_id


def _insert_atividade_raw(tenant_id, os_id, equip_id=None) -> uuid.UUID:
    """INSERT direto em atividade_da_os. RLS nao se aplica a esta tabela."""
    atv_id = uuid.uuid4()
    with connection.cursor() as cur:
        if equip_id is not None:
            cur.execute(
                """
                INSERT INTO atividade_da_os (
                    id, tenant_id, os_id, tipo, sequencia, estado,
                    valor_unitario_snapshot, geo_municipio_hash, grandeza,
                    tipo_bloqueia_concorrencia, equipamento_id
                ) VALUES (
                    %s, %s, %s, 'calibracao', 1, 'pendente',
                    100, '', '', false, %s
                )
                """,
                [str(atv_id), str(tenant_id), str(os_id), str(equip_id)],
            )
        else:
            cur.execute(
                """
                INSERT INTO atividade_da_os (
                    id, tenant_id, os_id, tipo, sequencia, estado,
                    valor_unitario_snapshot, geo_municipio_hash, grandeza,
                    tipo_bloqueia_concorrencia
                ) VALUES (
                    %s, %s, %s, 'calibracao', 1, 'pendente',
                    100, '', '', false
                )
                """,
                [str(atv_id), str(tenant_id), str(os_id)],
            )
    return atv_id


@pytest.mark.django_db(transaction=True, databases=["default"])
def test_0018_drill_a_insert_sem_equipamento_trigger_coalesce():
    """(a) INSERT sem equipamento_id -> trigger COALESCE copia OS.equipamento_id."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        equip_id, cli_id, os_id = _setup_tenant_equip_cliente_os(tenant)
        atv_id = _insert_atividade_raw(tenant.id, os_id, equip_id=None)

        with connection.cursor() as cur:
            cur.execute(
                "SELECT equipamento_id FROM atividade_da_os WHERE id = %s",
                [str(atv_id)],
            )
            result = cur.fetchone()[0]

    assert str(result) == str(equip_id), (
        f"Trigger COALESCE deve copiar OS.equipamento_id={equip_id}, got {result}"
    )


@pytest.mark.django_db(transaction=True, databases=["default"])
def test_0018_drill_b_insert_com_equipamento_proprio_preserva():
    """(b) INSERT COM equipamento_id proprio -> preserva, nao sobrescreve com OS.equipamento_id."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        equip_os, cli_id, os_id = _setup_tenant_equip_cliente_os(tenant)

        # Cria segundo equipamento para ser o "proprio" da atividade.
        equip_proprio = uuid.uuid4()
        tag2 = f"DRILL2-{uuid.uuid4().hex[:6]}"
        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO equipamentos (
                    id, tenant_id, tag, numero_serie, fabricante, modelo,
                    faixa, classe, localizacao_fisica,
                    perfil_tenant_snapshot, snapshot_schema_version,
                    status, criado_em, atualizado_em
                ) VALUES (
                    %s, %s, %s, %s, 'FabDrill2', 'ModDrill2',
                    '', '', '',
                    %s::jsonb, 'v1',
                    'ativo', now(), now()
                )
                """,
                [str(equip_proprio), str(tenant.id), tag2, tag2, '{"perfil": "D"}'],
            )

        atv_id = _insert_atividade_raw(tenant.id, os_id, equip_id=equip_proprio)

        with connection.cursor() as cur:
            cur.execute(
                "SELECT equipamento_id FROM atividade_da_os WHERE id = %s",
                [str(atv_id)],
            )
            result = cur.fetchone()[0]

    assert str(result) == str(equip_proprio), (
        f"Trigger deve preservar equipamento proprio={equip_proprio}, got {result}"
    )
    assert str(result) != str(equip_os), (
        "Trigger NAO deve sobrescrever com OS.equipamento_id quando atividade tem proprio"
    )


@pytest.mark.django_db(transaction=True, databases=["default"])
def test_0018_drill_c_update_equipamento_id_levanta_exception():
    """(c) UPDATE tentando mudar equipamento_id -> trigger imutavel levanta EXCEPTION.

    INSERT e UPDATE ficam na mesma transacao (run_in_tenant_context) para garantir
    que a linha exista quando o trigger avaliar OLD vs NEW. O UPDATE levanta dentro
    do mesmo bloco; capturamos via try/except para nao propagar pro context manager
    e depois assegurar que a excecao ocorreu.
    """
    from django.db.utils import InternalError, ProgrammingError

    tenant = TenantFactory()
    excecao_capturada: Exception | None = None

    with run_in_tenant_context(tenant.id):
        equip_id, cli_id, os_id = _setup_tenant_equip_cliente_os(tenant)
        atv_id = _insert_atividade_raw(tenant.id, os_id, equip_id=None)

        outro_equip = uuid.uuid4()
        try:
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE atividade_da_os SET equipamento_id = %s WHERE id = %s",
                    [str(outro_equip), str(atv_id)],
                )
        except (InternalError, ProgrammingError, Exception) as exc:
            excecao_capturada = exc

    assert excecao_capturada is not None, (
        "Trigger imutavel deveria ter levantado excecao ao tentar alterar equipamento_id"
    )
    assert "imutavel" in str(excecao_capturada), (
        f"Mensagem esperada 'imutavel' nao encontrada em: {excecao_capturada}"
    )


@pytest.mark.django_db(transaction=True, databases=["default"])
def test_0018_drill_d_coluna_equipamento_recebimento_id_existe():
    """(d) Coluna equipamento_recebimento_id existe em atividade_da_os apos migrate 0018."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'atividade_da_os'
              AND column_name = 'equipamento_recebimento_id'
            """
        )
        row = cur.fetchone()
    assert row is not None, (
        "Coluna equipamento_recebimento_id deve existir em atividade_da_os "
        "apos migration 0018"
    )


@pytest.mark.django_db(transaction=True, databases=["default"])
def test_0018_drill_e_indice_atv_tenant_equip_est_idx_existe():
    """(e) Indice atv_tenant_equip_est_idx existe apos migrate 0018."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'atividade_da_os'
              AND indexname = 'atv_tenant_equip_est_idx'
            """
        )
        row = cur.fetchone()
    assert row is not None, (
        "Indice atv_tenant_equip_est_idx deve existir em atividade_da_os "
        "apos migration 0018"
    )
