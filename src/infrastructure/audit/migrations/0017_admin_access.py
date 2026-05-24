"""AdminAccess — trilha append-only de acessos a /admin/* (F-C1 P4 T-FC1-05).

Materializa INV-ADMIN-002 + AC-FC1-002-3..7 do spec F-C1.

- append-only com trigger anti-mutation (UPDATE/DELETE proibidos exceto
  campos especificos: usuario_id->NULL+usuario_id_hash pos pseudonimizacao;
  user_agent_hash zerado + tombstoned_em apos retencao 24m)
- RLS: SELECT cross-tenant (auditoria de plataforma); INSERT modo_sistema OR
  qualquer autenticado (middleware grava direto); DELETE NUNCA
- 3 indexes
- ip_hash e user_agent_hash em HMAC com salt versionado (LGPD)

# tests-coverage: tests/test_admin_access_inv_admin_002.py (Wave A)
# rls-policy: external 0017 -- policy nasce nesta mesma migration
"""

import uuid

from django.db import migrations, models

FORWARD_RLS_TRIGGER = r"""
ALTER TABLE admin_access ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_access FORCE ROW LEVEL SECURITY;

-- SELECT: cross-tenant (auditoria de plataforma — usado por dashboards admin)
CREATE POLICY admin_access_select ON admin_access
    FOR SELECT
    USING (TRUE);

-- INSERT: middleware grava sem contexto de tenant — qualquer um pode INSERT
-- (RLS nao bloqueia INSERT direto da app, controle de quem chama o
-- middleware fica nas views Django)
CREATE POLICY admin_access_insert ON admin_access
    FOR INSERT
    WITH CHECK (TRUE);

-- UPDATE: SO modo_sistema (jobs de pseudonimizacao 90d + tombstone 24m)
CREATE POLICY admin_access_update ON admin_access
    FOR UPDATE
    USING (current_setting('app.modo_sistema', true) = '1');

-- DELETE: NUNCA (audit imutavel — soft-delete via tombstoned_em)
CREATE POLICY admin_access_no_delete ON admin_access
    FOR DELETE
    USING (FALSE);

-- Trigger anti-mutation: bloqueia UPDATE de campos imutaveis
-- (path, metodo, status_code, motivo_negacao, eh_break_glass, timestamp,
--  ip_hash). Campos mutaveis por design: usuario_id (pseudonimizacao
-- 90d -> NULL), usuario_id_hash (preenchido na pseudonimizacao),
-- user_agent_hash (zerado no tombstone 24m), tombstoned_em.

CREATE OR REPLACE FUNCTION admin_access_anti_mutation()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.path IS DISTINCT FROM OLD.path THEN
        RAISE EXCEPTION 'admin_access.path eh imutavel';
    END IF;
    IF NEW.metodo IS DISTINCT FROM OLD.metodo THEN
        RAISE EXCEPTION 'admin_access.metodo eh imutavel';
    END IF;
    IF NEW.status_code IS DISTINCT FROM OLD.status_code THEN
        RAISE EXCEPTION 'admin_access.status_code eh imutavel';
    END IF;
    IF NEW.motivo_negacao IS DISTINCT FROM OLD.motivo_negacao THEN
        RAISE EXCEPTION 'admin_access.motivo_negacao eh imutavel';
    END IF;
    IF NEW.eh_break_glass IS DISTINCT FROM OLD.eh_break_glass THEN
        RAISE EXCEPTION 'admin_access.eh_break_glass eh imutavel';
    END IF;
    IF NEW.timestamp IS DISTINCT FROM OLD.timestamp THEN
        RAISE EXCEPTION 'admin_access.timestamp eh imutavel';
    END IF;
    IF NEW.ip_hash IS DISTINCT FROM OLD.ip_hash THEN
        RAISE EXCEPTION 'admin_access.ip_hash eh imutavel';
    END IF;
    -- Apos tombstone, usuario_id_hash tambem vira imutavel
    IF OLD.tombstoned_em IS NOT NULL THEN
        IF NEW.usuario_id_hash IS DISTINCT FROM OLD.usuario_id_hash THEN
            RAISE EXCEPTION 'admin_access pos-tombstone: usuario_id_hash imutavel';
        END IF;
    END IF;
    -- usuario_id so pode mudar de NOT NULL -> NULL (pseudonimizacao 90d)
    IF OLD.usuario_id IS NOT NULL AND NEW.usuario_id IS NOT NULL THEN
        IF NEW.usuario_id IS DISTINCT FROM OLD.usuario_id THEN
            RAISE EXCEPTION 'admin_access.usuario_id so pode mudar para NULL (pseudonimizacao)';
        END IF;
    END IF;
    IF OLD.usuario_id IS NULL AND NEW.usuario_id IS NOT NULL THEN
        RAISE EXCEPTION 'admin_access.usuario_id nao pode reaparecer apos NULL';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER admin_access_anti_mutation_trg
    BEFORE UPDATE ON admin_access
    FOR EACH ROW
    EXECUTE FUNCTION admin_access_anti_mutation();
"""

REVERSE_RLS_TRIGGER = r"""
DROP TRIGGER IF EXISTS admin_access_anti_mutation_trg ON admin_access;
DROP FUNCTION IF EXISTS admin_access_anti_mutation();
DROP POLICY IF EXISTS admin_access_select ON admin_access;
DROP POLICY IF EXISTS admin_access_insert ON admin_access;
DROP POLICY IF EXISTS admin_access_update ON admin_access;
DROP POLICY IF EXISTS admin_access_no_delete ON admin_access;
ALTER TABLE admin_access DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0016_consumer_idempotencia_dead_letter"),
        ("multitenant", "0004_audit_hash_chain_por_tenant"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminAccess",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("usuario_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("usuario_id_hash", models.CharField(blank=True, default="", max_length=64)),
                ("ip_hash", models.CharField(max_length=64)),
                ("user_agent_hash", models.CharField(max_length=64)),
                ("path", models.CharField(max_length=500)),
                ("metodo", models.CharField(max_length=10)),
                ("status_code", models.IntegerField()),
                ("motivo_negacao", models.CharField(blank=True, default="", max_length=64)),
                ("eh_break_glass", models.BooleanField(db_index=True, default=False)),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "tombstoned_em",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
            ],
            options={
                "verbose_name": "Acesso admin (trilha)",
                "verbose_name_plural": "Acessos admin (trilha)",
                "db_table": "admin_access",
            },
        ),
        migrations.AddIndex(
            model_name="adminaccess",
            index=models.Index(fields=["timestamp"], name="idx_admin_acc_ts"),
        ),
        migrations.AddIndex(
            model_name="adminaccess",
            index=models.Index(
                fields=["usuario_id", "timestamp"], name="idx_admin_acc_user_ts"
            ),
        ),
        migrations.AddIndex(
            model_name="adminaccess",
            index=models.Index(
                fields=["motivo_negacao", "timestamp"], name="idx_admin_acc_neg_ts"
            ),
        ),
        migrations.RunSQL(sql=FORWARD_RLS_TRIGGER, reverse_sql=REVERSE_RLS_TRIGGER),
    ]
