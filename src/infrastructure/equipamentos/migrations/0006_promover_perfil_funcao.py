"""T-EQP-009 (AC-EQP-001-7b / P-EQP-T4) — funcao SECURITY DEFINER
`promover_perfil_equipamento_snapshot`.

Unica via legitima de mutar `perfil_tenant_snapshot` apos cadastro.
Trigger `equipamento_perfil_tenant_imutavel_trg` (migration 0002)
respeita GUC `app.perfil_promocao_permitida='1'`; esta funcao seta
o GUC com SET LOCAL antes do UPDATE.

Regras cravadas (P-EQP-T4):
1. `p_perfil_novo` ∈ {C, B, A}. D nao e destino valido (downgrade
   alvo proibido).
2. Direcao monotonica crescente: D<C<B<A (ordem 1..4); novo_ord
   estritamente maior que atual_ord — proibido downgrade E mesmo
   perfil (re-promocao sem mudanca nao tem sentido).
3. `p_evidencia_documental_id` NOT NULL.
4. `p_justificativa` LENGTH >= 100 chars.
5. `p_rt_id` NOT NULL (referencia ao RT do tenant — US-EQP-007).
6. Re-aplica isolamento: equipamento.tenant_id ==
   current_setting('app.active_tenant_id') — SECURITY DEFINER nao
   pode virar bypass de tenant.

Anti-PII na justificativa: validacao em Python no service wrapper
(regex CPF/email/telefone/nomes) — defesa em profundidade fora de
PL/pgSQL (regex unicode complexa).

NAO cria `EquipamentoVersao` AQUI — depende de T-EQP-012 (US-EQP-002
`motivo_mudanca=mudanca_classe_metrologica`). Quando T-EQP-012
existir, a funcao ganha INSERT em `equipamentos_versao` apos o
UPDATE, dentro da mesma transacao. Evento `equipamento.perfil_promovido`
ja e publicado pelo service (cadeia 25a WORM).

NG-EQP-14: promocao em lote = Wave B (esta funcao opera 1 equipamento
por chamada).

# tests-coverage: tests/test_equipamentos_promover_perfil_t_eqp_009.py
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- T-EQP-009 - promover_perfil_equipamento_snapshot (SECURITY DEFINER)
-- =============================================================
CREATE OR REPLACE FUNCTION promover_perfil_equipamento_snapshot(
    p_equipamento_id uuid,
    p_perfil_novo text,
    p_evidencia_documental_id uuid,
    p_justificativa text,
    p_rt_id uuid,
    p_decisor_id uuid
) RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $body$
DECLARE
    v_perfil_atual text;
    v_atual_ord int;
    v_novo_ord int;
    v_tenant_id uuid;
    v_active_tenant text;
    v_snapshot_atualizado jsonb;
BEGIN
    -- Re-aplica isolamento (SECURITY DEFINER nao pode virar bypass).
    v_active_tenant := current_setting('app.active_tenant_id', true);
    IF v_active_tenant IS NULL OR v_active_tenant = '' THEN
        RAISE EXCEPTION
            'P-EQP-T4: promover_perfil exige app.active_tenant_id no contexto.';
    END IF;

    -- Defesa: argumentos obrigatorios.
    IF p_equipamento_id IS NULL THEN
        RAISE EXCEPTION 'P-EQP-T4: p_equipamento_id obrigatorio.';
    END IF;
    IF p_evidencia_documental_id IS NULL THEN
        RAISE EXCEPTION
            'P-EQP-T4: p_evidencia_documental_id obrigatorio (rastreabilidade RBC).';
    END IF;
    IF p_rt_id IS NULL THEN
        RAISE EXCEPTION
            'P-EQP-T4: p_rt_id obrigatorio (assinatura RT - US-EQP-007).';
    END IF;
    IF p_decisor_id IS NULL THEN
        RAISE EXCEPTION 'P-EQP-T4: p_decisor_id obrigatorio.';
    END IF;
    IF p_justificativa IS NULL OR length(p_justificativa) < 100 THEN
        RAISE EXCEPTION
            'P-EQP-T4: justificativa exige >=100 chars (atual=%).',
            COALESCE(length(p_justificativa), 0);
    END IF;

    -- Mapeamento direcao D<C<B<A. D nao e destino valido.
    v_novo_ord := CASE p_perfil_novo
        WHEN 'C' THEN 2
        WHEN 'B' THEN 3
        WHEN 'A' THEN 4
        ELSE NULL
    END;
    IF v_novo_ord IS NULL THEN
        RAISE EXCEPTION
            'P-EQP-T4: p_perfil_novo invalido (%). Destinos validos: C, B, A '
            '(D nao e destino de promocao).', p_perfil_novo;
    END IF;

    -- Lock pessimista pra evitar dupla promocao concorrente.
    SELECT tenant_id, perfil_tenant_snapshot->>'perfil'
        INTO v_tenant_id, v_perfil_atual
    FROM equipamentos
    WHERE id = p_equipamento_id
      AND deletado_em IS NULL
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'P-EQP-T4: equipamento % nao encontrado (ou soft-deleted).',
            p_equipamento_id;
    END IF;

    -- Re-aplica isolamento de tenant.
    IF v_tenant_id::text <> v_active_tenant THEN
        RAISE EXCEPTION
            'P-EQP-T4: equipamento de outro tenant (% vs %).',
            v_tenant_id, v_active_tenant;
    END IF;

    -- Direcao monotonica crescente. Snapshot sem perfil = ordem 1 (D).
    v_atual_ord := CASE COALESCE(v_perfil_atual, 'D')
        WHEN 'D' THEN 1
        WHEN 'C' THEN 2
        WHEN 'B' THEN 3
        WHEN 'A' THEN 4
        ELSE 0
    END;
    IF v_atual_ord = 0 THEN
        RAISE EXCEPTION
            'P-EQP-T4: perfil atual invalido (%); reparar snapshot via '
            'migration de dados antes de promover.', v_perfil_atual;
    END IF;
    IF v_novo_ord <= v_atual_ord THEN
        RAISE EXCEPTION
            'P-EQP-T4: direcao invalida (% -> %). Downgrade e mesmo perfil '
            'sao proibidos; promocao exige nova_ord > atual_ord.',
            COALESCE(v_perfil_atual, 'D'), p_perfil_novo;
    END IF;

    -- Libera trigger imutabilidade APENAS nesta transacao.
    PERFORM set_config('app.perfil_promocao_permitida', '1', true);

    UPDATE equipamentos
       SET perfil_tenant_snapshot = jsonb_set(
               COALESCE(perfil_tenant_snapshot, '{}'::jsonb),
               '{perfil}',
               to_jsonb(p_perfil_novo)
           )
     WHERE id = p_equipamento_id
    RETURNING perfil_tenant_snapshot INTO v_snapshot_atualizado;

    -- Imediatamente recolhe a permissao (defesa: se chamador fizer
    -- outro UPDATE na mesma transacao, NAO deve passar).
    PERFORM set_config('app.perfil_promocao_permitida', '0', true);

    RETURN v_snapshot_atualizado;
END;
$body$;

-- Funcao SECURITY DEFINER roda como owner (app_migrator). app_user
-- precisa de EXECUTE pra invocar; o corpo executa com privilegios
-- do owner — RLS e triggers respeitam mesmo assim porque a funcao
-- re-aplica isolamento (current_setting('app.active_tenant_id')) e
-- a permissao GUC `app.perfil_promocao_permitida` so e setada na
-- transacao corrente.
REVOKE EXECUTE ON FUNCTION
    promover_perfil_equipamento_snapshot(uuid, text, uuid, text, uuid, uuid)
    FROM PUBLIC;
GRANT EXECUTE ON FUNCTION
    promover_perfil_equipamento_snapshot(uuid, text, uuid, text, uuid, uuid)
    TO app_user;

COMMENT ON FUNCTION
    promover_perfil_equipamento_snapshot(uuid, text, uuid, text, uuid, uuid)
IS 'T-EQP-009 (P-EQP-T4) - unica via legitima de mutar perfil_tenant_snapshot. '
   'Direcao D<C<B<A (downgrade proibido). Anti-PII na justificativa = service Python.';
"""

REVERSE = """
DROP FUNCTION IF EXISTS promover_perfil_equipamento_snapshot(uuid, text, uuid, text, uuid, uuid);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("equipamentos", "0005_seed_authz_criar"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
