"""Migration 0018 — os-multi-equipamento Fatia 1b (ADR-0082).

Operacoes (ordem importa):
1. RenameField: equipamento_id_desnormalizado -> equipamento_id
2. AddField: equipamento_recebimento_id na AtividadeDaOS
3. AddIndex: atv_tenant_equip_est_idx (tenant, equipamento_id, estado)
4. RunSQL: triggers V2 (FORWARD) / V1 (REVERSE)
5. AlterField: atualiza help_text de equipamento_id para o novo texto ADR-0082

TRIGGER V2 (forward):
- BEFORE INSERT: IF equipamento_id IS NULL: copia de OS.equipamento_id
  (COALESCE — compat OS single-equip legada). Se nao NULL, preserva.
- UPDATE imutavel: bloqueia equipamento_id + tipo_bloqueia_concorrencia.

TRIGGER V1 (reverse):
- Restaura corpo pre-retrofit (SELECT incondicional para equipamento_id_desnormalizado).
"""

from __future__ import annotations

from django.db import migrations, models

# ---------------------------------------------------------------------------
# FORWARD: Triggers V2 (ADR-0082 os-multi-equipamento)
# ---------------------------------------------------------------------------
TRIGGER_FORWARD_V2 = r"""
CREATE OR REPLACE FUNCTION atividade_da_os_concorrencia_denormalize_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
DECLARE
    v_equip uuid;
    v_bloq boolean;
BEGIN
    -- ADR-0082 os-multi-equipamento: equipamento_id e proprio da atividade.
    -- Fallback p/ OS.equipamento_id apenas se o INSERT nao trouxe equipamento
    -- (compat OS single-equip legada). COALESCE preserva o valor do INSERT.
    IF NEW.equipamento_id IS NULL THEN
        SELECT equipamento_id INTO v_equip FROM ordens_servico WHERE id = NEW.os_id;
        NEW.equipamento_id := v_equip;
    END IF;
    SELECT tipo_bloqueia_concorrencia INTO v_bloq
    FROM tipo_atividade_config
    WHERE tenant_id = NEW.tenant_id AND tipo = NEW.tipo AND deletado_em IS NULL
    LIMIT 1;
    NEW.tipo_bloqueia_concorrencia := COALESCE(v_bloq, TRUE);
    RETURN NEW;
END;
$body$;

CREATE OR REPLACE FUNCTION atividade_da_os_concorrencia_imutavel_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF OLD.equipamento_id IS DISTINCT FROM NEW.equipamento_id THEN
        RAISE EXCEPTION 'INV-OS-CONC-001: equipamento_id imutavel pos-INSERT';
    END IF;
    IF OLD.tipo_bloqueia_concorrencia IS DISTINCT FROM NEW.tipo_bloqueia_concorrencia THEN
        RAISE EXCEPTION 'INV-OS-CONC-001: tipo_bloqueia_concorrencia imutavel pos-INSERT';
    END IF;
    RETURN NEW;
END;
$body$;
"""

# ---------------------------------------------------------------------------
# REVERSE: Restaura corpo V1 (pre-retrofit, com SELECT incondicional
# e referencia ao nome antigo equipamento_id_desnormalizado).
# ---------------------------------------------------------------------------
TRIGGER_FORWARD_V1 = r"""
CREATE OR REPLACE FUNCTION atividade_da_os_concorrencia_denormalize_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
DECLARE
    v_equip uuid;
    v_bloq boolean;
BEGIN
    SELECT equipamento_id INTO v_equip FROM ordens_servico WHERE id = NEW.os_id;
    NEW.equipamento_id_desnormalizado := v_equip;
    SELECT tipo_bloqueia_concorrencia INTO v_bloq
    FROM tipo_atividade_config
    WHERE tenant_id = NEW.tenant_id AND tipo = NEW.tipo AND deletado_em IS NULL
    LIMIT 1;
    NEW.tipo_bloqueia_concorrencia := COALESCE(v_bloq, TRUE);
    RETURN NEW;
END;
$body$;

CREATE OR REPLACE FUNCTION atividade_da_os_concorrencia_imutavel_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF OLD.equipamento_id_desnormalizado IS DISTINCT FROM NEW.equipamento_id_desnormalizado THEN
        RAISE EXCEPTION 'INV-OS-CONC-001: equipamento_id_desnormalizado imutavel pos-INSERT';
    END IF;
    IF OLD.tipo_bloqueia_concorrencia IS DISTINCT FROM NEW.tipo_bloqueia_concorrencia THEN
        RAISE EXCEPTION 'INV-OS-CONC-001: tipo_bloqueia_concorrencia imutavel pos-INSERT';
    END IF;
    RETURN NEW;
END;
$body$;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("ordens_servico", "0017_alter_eventodeos_perfil_no_evento"),
    ]

    operations = [
        # 1. Rename atomico — preserva dados, sem DROP+ADD.
        migrations.RenameField(
            model_name="atividadedaos",
            old_name="equipamento_id_desnormalizado",
            new_name="equipamento_id",
        ),
        # 2. Novo campo equipamento_recebimento_id na atividade (ADR-0082 / cl. 7.4.3).
        migrations.AddField(
            model_name="atividadedaos",
            name="equipamento_recebimento_id",
            field=models.UUIDField(
                blank=True,
                null=True,
                help_text=(
                    "FK EquipamentoRecebimento POR INSTRUMENTO (ADR-0082 / cl. 7.4.3 + 7.8.2.1 ISO 17025). "
                    "Move de OS.equipamento_recebimento_id (1-por-OS, depreciado) para a atividade. "
                    "INV-OSME-RCB-001: requer_recebimento => NOT NULL e equip. recebido == calibrado. "
                    "Preenchimento completo do vinculo = GATE-OSME-RECEBIMENTO-7.5 (app equipamentos)."
                ),
            ),
        ),
        # 3. Indice cobrindo deteccao de equipamento baixado por atividade (TL-OSME-02).
        migrations.AddIndex(
            model_name="atividadedaos",
            index=models.Index(
                fields=["tenant", "equipamento_id", "estado"],
                name="atv_tenant_equip_est_idx",
            ),
        ),
        # 4. Triggers V2 (forward) / V1 (reverse).
        #    RenameField DEVE vir antes de RunSQL: a funcao V2 referencia
        #    a coluna pelo novo nome `equipamento_id`.
        migrations.RunSQL(
            sql=TRIGGER_FORWARD_V2,
            reverse_sql=TRIGGER_FORWARD_V1,
        ),
        # 5. Atualiza help_text do campo apos rename (model tem texto novo ADR-0082;
        #    RenameField preserva o help_text antigo da 0005 — AlterField corrige).
        migrations.AlterField(
            model_name="atividadedaos",
            name="equipamento_id",
            field=models.UUIDField(
                blank=True,
                null=True,
                help_text=(
                    "Equipamento PROPRIO da atividade (ADR-0082 / retrofit os-multi-equipamento). "
                    "Fonte de verdade da concorrencia metrologica INV-OS-CONC-001. Fallback p/ "
                    "OS.equipamento_id via trigger quando NULL (compat OS single-equip legada)."
                ),
            ),
        ),
    ]
