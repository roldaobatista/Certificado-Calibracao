# Saneamento SAN-PERFIL-TENANT — T-SAN-PERFIL-009 (Sprint 1)
# AC-SAN-PERFIL-001-9 — funcao SECURITY DEFINER `rebaixar_perfil_tenant_voluntario_cliente()`:
#   - Cooldown >=30 dias entre rebaixamentos voluntarios (A1 plan.md).
#   - Pre-aviso obrigatorio (p_confirmado_pelo_tenant_em >=7 dias atras).
#   - Permitido apenas para BAIXO: B->D, B->C, C->D, A->B (este ultimo so se
#     `acreditacao_suspensa_em` esta ativo — defesa pra perda voluntaria de
#     acreditacao mediante CDC art. 51 IV + Lei 14.181/2021 autonomia contratual).
#   - INSERT outbox `TenantPerfilAlterado` direcao=rebaixamento_voluntario_cliente.
#
# Para subir (PROMOCAO) usar aplicar_evento_cgcre direcao=promocao_regulatoria.
#
# tenant-perfil-imutavel: skip -- migration cria funcao SECURITY DEFINER canonica
# de autonomia contratual; caminho oficial autorizado por ADR-0067 + AC-001-9

from django.db import migrations


SQL_CRIA_FUNCAO_REBAIXAR_VOLUNTARIO = """
CREATE OR REPLACE FUNCTION rebaixar_perfil_tenant_voluntario_cliente(
    p_tenant_id                    UUID,
    p_perfil_novo                  CHAR(1),
    p_motivo                       TEXT,
    p_confirmado_pelo_tenant_em    TIMESTAMPTZ,
    p_registrado_por_id            UUID,
    p_assinatura_a3_id             UUID DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_perfil_anterior     CHAR(1);
    v_historico_id        UUID;
    v_ultimo_rebaixamento TIMESTAMPTZ;
    v_dias_desde_ultimo   INTEGER;
    v_dias_desde_aviso    INTEGER;
    v_outbox_payload      JSONB;
BEGIN
    -- 1. Validacao motivo.
    IF char_length(p_motivo) < 100 THEN
        RAISE EXCEPTION 'rebaixar_voluntario: motivo deve ter >=100 chars (recebido %)', char_length(p_motivo);
    END IF;

    -- 2. Pre-aviso obrigatorio: cliente confirmou >=7 dias antes.
    v_dias_desde_aviso := EXTRACT(EPOCH FROM (NOW() - p_confirmado_pelo_tenant_em)) / 86400;
    IF v_dias_desde_aviso < 7 THEN
        RAISE EXCEPTION 'rebaixar_voluntario: pre-aviso de %d dias < 7 dias minimo (AC-001-9). Confirmacao do tenant em %', v_dias_desde_aviso, p_confirmado_pelo_tenant_em;
    END IF;

    -- 3. Advisory lock por tenant.
    PERFORM pg_advisory_xact_lock(hashtext('tenant_perfil:' || p_tenant_id::text));

    -- 4. Le perfil atual com SELECT FOR UPDATE.
    SELECT perfil_regulatorio
    INTO v_perfil_anterior
    FROM tenants
    WHERE id = p_tenant_id
    FOR UPDATE;

    IF v_perfil_anterior IS NULL THEN
        RAISE EXCEPTION 'rebaixar_voluntario: tenant % nao encontrado', p_tenant_id;
    END IF;

    -- 5. Validacao de transicoes voluntarias (so para BAIXO):
    --    B->D, B->C, C->D (cliente quer pagar menos).
    --    A->B nao permitido por esta funcao (perda de acreditacao A e CGCRE-driven,
    --    nao voluntaria; usar aplicar_evento_cgcre direcao=cancelamento_cgcre).
    IF NOT (
        (v_perfil_anterior = 'B' AND p_perfil_novo IN ('C', 'D'))
        OR (v_perfil_anterior = 'C' AND p_perfil_novo = 'D')
    ) THEN
        RAISE EXCEPTION 'rebaixar_voluntario: transicao % -> % nao permitida (apenas B->C, B->D, C->D; perda de A so via cancelamento_cgcre)', v_perfil_anterior, p_perfil_novo;
    END IF;

    -- 6. Cooldown >=30 dias entre rebaixamentos voluntarios.
    SELECT MAX(registrado_em)
    INTO v_ultimo_rebaixamento
    FROM tenant_perfil_historico
    WHERE tenant_id = p_tenant_id
      AND direcao = 'rebaixamento_voluntario_cliente';

    IF v_ultimo_rebaixamento IS NOT NULL THEN
        v_dias_desde_ultimo := EXTRACT(EPOCH FROM (NOW() - v_ultimo_rebaixamento)) / 86400;
        IF v_dias_desde_ultimo < 30 THEN
            RAISE EXCEPTION 'rebaixar_voluntario: cooldown 30d nao cumprido (%d dias desde ultimo rebaixamento em %)', v_dias_desde_ultimo, v_ultimo_rebaixamento;
        END IF;
    END IF;

    -- 7. UPDATE no tenant.
    UPDATE tenants
    SET perfil_regulatorio          = p_perfil_novo,
        acreditacao_cgcre_numero    = CASE WHEN p_perfil_novo != 'A' THEN NULL ELSE acreditacao_cgcre_numero END,
        acreditacao_suspensa_em     = CASE WHEN p_perfil_novo != 'A' THEN NULL ELSE acreditacao_suspensa_em END,
        acreditacao_suspensa_ate    = CASE WHEN p_perfil_novo != 'A' THEN NULL ELSE acreditacao_suspensa_ate END,
        ilac_mra_aderido            = CASE WHEN p_perfil_novo != 'A' THEN FALSE ELSE ilac_mra_aderido END,
        atualizado_em               = NOW()
    WHERE id = p_tenant_id;

    -- 8. INSERT no historico.
    v_historico_id := gen_random_uuid();
    INSERT INTO tenant_perfil_historico (
        id, tenant_id, perfil_anterior, perfil_novo, direcao, motivo,
        evento_origem_id, auditor_cgcre, certificado_acreditacao_documento_id,
        registrado_em, registrado_por_usuario_id, assinatura_a3_id
    ) VALUES (
        v_historico_id, p_tenant_id, v_perfil_anterior, p_perfil_novo,
        'rebaixamento_voluntario_cliente', p_motivo,
        NULL, NULL, NULL,
        NOW(), p_registrado_por_id, p_assinatura_a3_id
    );

    -- 9. INSERT outbox event TenantPerfilAlterado (consumer notifica AdmAfere
    --    + corretora SUSEP — INV-TENANT-PERFIL-006).
    v_outbox_payload := jsonb_build_object(
        'event_id', gen_random_uuid()::text,
        '_schema_version', 'v1',
        'event_name', 'tenant.perfil_alterado',
        'occurred_at', to_char(NOW() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
        'correlation_id', current_setting('app.correlation_id', true),
        'actor', p_registrado_por_id::text,
        'acao', 'tenant.perfil_alterado',
        'payload', jsonb_build_object(
            'tenant_id_hash', md5(p_tenant_id::text),
            'perfil_anterior', v_perfil_anterior,
            'perfil_novo', p_perfil_novo,
            'direcao', 'rebaixamento_voluntario_cliente',
            'confirmado_pelo_tenant_em', p_confirmado_pelo_tenant_em,
            'registrado_em', NOW(),
            'assinatura_a3_id', p_assinatura_a3_id,
            'notifica_d_e_o', false
        ),
        'causation_id', v_historico_id::text,
        'tenant_id', p_tenant_id::text,
        'usuario_id', p_registrado_por_id,
        'resource_summary', format('tenant=%s rebaixamento_voluntario %s->%s', p_tenant_id, v_perfil_anterior, p_perfil_novo)
    );

    INSERT INTO bus_outbox (
        id, causation_id, acao, envelope_jsonb, tenant_id, criado_em, tentativas
    ) VALUES (
        gen_random_uuid(), v_historico_id, 'tenant.perfil_alterado', v_outbox_payload,
        p_tenant_id, NOW(), 0
    )
    ON CONFLICT (causation_id, acao) DO NOTHING;

    RETURN v_historico_id;
END;
$$;

COMMENT ON FUNCTION rebaixar_perfil_tenant_voluntario_cliente IS
'ADR-0067 + SAN-PERFIL-TENANT T-SAN-PERFIL-009. Autonomia contratual do tenant '
'(CDC art. 51 IV + Lei 14.181/2021). Permite B->C/D e C->D com cooldown 30d e '
'pre-aviso >=7 dias. Perda voluntaria de A nao e permitida por esta funcao '
'(usar aplicar_evento_cgcre direcao=cancelamento_cgcre). UPDATE + INSERT '
'historico + INSERT outbox em transacao unica.';
"""


SQL_REMOVE_FUNCAO = """
DROP FUNCTION IF EXISTS rebaixar_perfil_tenant_voluntario_cliente(
    UUID, CHAR(1), TEXT, TIMESTAMPTZ, UUID, UUID
);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("tenant", "0008_aplicar_evento_cgcre_function"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_CRIA_FUNCAO_REBAIXAR_VOLUNTARIO,
            reverse_sql=SQL_REMOVE_FUNCAO,
        ),
    ]
