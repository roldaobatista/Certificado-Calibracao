# Saneamento SAN-PERFIL-TENANT — T-SAN-PERFIL-008 + T-SAN-PERFIL-010 (Sprint 1)
# AC-SAN-PERFIL-001-2 + AC-001-6 + AC-001-8 + AC-001-10 + INV-TENANT-PERFIL-002 + INV-006:
#
# Funcao SECURITY DEFINER `aplicar_evento_cgcre(direcao, tenant_id, ...)`:
#   - SELECT FOR UPDATE em tenants (T5 plan.md — concorrencia)
#   - pg_advisory_xact_lock por tenant (T5)
#   - Valida matriz de transicoes (AC-001-8 — D->C, C->B, B->A; suspensao preserva A; etc).
#   - UPDATE tenants (perfil_regulatorio + flags acreditacao).
#   - INSERT tenant_perfil_historico.
#   - INSERT bus_outbox event `TenantPerfilAlterado` (S2 + AC-001-6) quando direcao
#     em {promocao, suspensao, cancelamento}.
#
# Trigger anti-mutation NAO bloqueia esta funcao porque o UPDATE da tenants e
# uma coluna escalar (perfil_regulatorio), nao uma das colunas protegidas pela
# trigger anti-mutation da tabela tenants. Defesa em profundidade ainda vale
# (modelos Python tem .save() bloqueando mutacao direta de perfil_regulatorio
# fora de aplicar_evento_cgcre — sera adicionado em manager customizado depois).
#
# tenant-perfil-imutavel: skip -- migration cria funcao SECURITY DEFINER canonica
# de mutacao; este e o caminho oficial autorizado por ADR-0067

from django.db import migrations


SQL_CRIA_FUNCAO_APLICAR_EVENTO_CGCRE = """
CREATE OR REPLACE FUNCTION aplicar_evento_cgcre(
    p_direcao              TEXT,
    p_tenant_id            UUID,
    p_perfil_novo          CHAR(1),
    p_motivo               TEXT,
    p_evento_origem_id     UUID DEFAULT NULL,
    p_auditor_cgcre        TEXT DEFAULT NULL,
    p_documento_cgcre_id   UUID DEFAULT NULL,
    p_registrado_por_id    UUID DEFAULT NULL,
    p_assinatura_a3_id     UUID DEFAULT NULL,
    p_suspensa_em          DATE DEFAULT NULL,
    p_suspensa_ate         DATE DEFAULT NULL,
    p_numero_rbc           TEXT DEFAULT NULL,
    p_ilac_mra_aderido     BOOLEAN DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_perfil_anterior     CHAR(1);
    v_historico_id        UUID;
    v_outbox_payload      JSONB;
    v_outbox_causation_id UUID;
    v_acao_outbox         TEXT;
    v_emite_outbox        BOOLEAN;
BEGIN
    -- 1. Validacao de direcao (sanity check ao banco).
    IF p_direcao NOT IN (
        'provisionamento_inicial',
        'promocao_regulatoria',
        'suspensao_temporaria_cgcre',
        'cancelamento_cgcre',
        'reducao_escopo_cgcre',
        'correcao_administrativa'
    ) THEN
        RAISE EXCEPTION 'aplicar_evento_cgcre: direcao % invalida ou pertence a outra funcao (rebaixar_voluntario)', p_direcao;
    END IF;

    -- 2. Validacao motivo >=100 chars (CHECK do banco tambem cobre).
    IF char_length(p_motivo) < 100 THEN
        RAISE EXCEPTION 'aplicar_evento_cgcre: motivo deve ter >=100 chars (recebido %)', char_length(p_motivo);
    END IF;

    -- 3. Advisory lock por tenant (T5 plan.md — bloqueia 2 promocoes concorrentes).
    PERFORM pg_advisory_xact_lock(hashtext('tenant_perfil:' || p_tenant_id::text));

    -- 4. Le perfil atual com SELECT FOR UPDATE.
    SELECT perfil_regulatorio
    INTO v_perfil_anterior
    FROM tenants
    WHERE id = p_tenant_id
    FOR UPDATE;

    IF v_perfil_anterior IS NULL THEN
        RAISE EXCEPTION 'aplicar_evento_cgcre: tenant % nao encontrado', p_tenant_id;
    END IF;

    -- 5. Validacao de transicoes (AC-001-8).
    --    PROVISIONAMENTO_INICIAL so se perfil anterior estava NULL (impossivel
    --    pos-migration 0005). Mesmo assim, esta funcao nao deve ser chamada
    --    para provisionamento — provisioning roda na migration 0004 direto.
    IF p_direcao = 'provisionamento_inicial' THEN
        RAISE EXCEPTION 'aplicar_evento_cgcre: provisionamento_inicial e cravado em migration 0004, nao via esta funcao';
    END IF;

    --    PROMOCAO: monotonic UP (D->C, C->B, B->A). Jumps proibidos.
    IF p_direcao = 'promocao_regulatoria' THEN
        IF NOT (
            (v_perfil_anterior = 'D' AND p_perfil_novo = 'C')
            OR (v_perfil_anterior = 'C' AND p_perfil_novo = 'B')
            OR (v_perfil_anterior = 'B' AND p_perfil_novo = 'A')
        ) THEN
            RAISE EXCEPTION 'aplicar_evento_cgcre: promocao % -> % nao permitida (so monotonic D->C, C->B, B->A; jumps exigem multiplas promocoes)', v_perfil_anterior, p_perfil_novo;
        END IF;
        IF p_assinatura_a3_id IS NULL THEN
            RAISE EXCEPTION 'aplicar_evento_cgcre: promocao_regulatoria exige assinatura A3 (INV-TENANT-PERFIL-007)';
        END IF;
        IF p_documento_cgcre_id IS NULL THEN
            RAISE EXCEPTION 'aplicar_evento_cgcre: promocao_regulatoria exige certificado_acreditacao_documento_id (INV-TENANT-PERFIL-007)';
        END IF;
        IF p_perfil_novo = 'A' AND p_auditor_cgcre IS NULL THEN
            RAISE EXCEPTION 'aplicar_evento_cgcre: promocao para A exige auditor_cgcre nomeado';
        END IF;
    END IF;

    --    SUSPENSAO_TEMPORARIA_CGCRE: preserva A. p_perfil_novo deve ser igual a anterior.
    IF p_direcao = 'suspensao_temporaria_cgcre' THEN
        IF v_perfil_anterior != 'A' OR p_perfil_novo != 'A' THEN
            RAISE EXCEPTION 'aplicar_evento_cgcre: suspensao_temporaria_cgcre so se aplica a perfil A (era %, novo %)', v_perfil_anterior, p_perfil_novo;
        END IF;
        IF p_suspensa_em IS NULL OR p_suspensa_ate IS NULL THEN
            RAISE EXCEPTION 'aplicar_evento_cgcre: suspensao exige p_suspensa_em e p_suspensa_ate';
        END IF;
    END IF;

    --    CANCELAMENTO_CGCRE: A -> B (lab perde acreditacao).
    IF p_direcao = 'cancelamento_cgcre' THEN
        IF v_perfil_anterior != 'A' OR p_perfil_novo != 'B' THEN
            RAISE EXCEPTION 'aplicar_evento_cgcre: cancelamento_cgcre exige transicao A -> B (era % -> %)', v_perfil_anterior, p_perfil_novo;
        END IF;
    END IF;

    --    REDUCAO_ESCOPO_CGCRE: NAO muda perfil — historico apenas (atualiza licencas Wave A).
    IF p_direcao = 'reducao_escopo_cgcre' THEN
        IF p_perfil_novo != v_perfil_anterior THEN
            RAISE EXCEPTION 'aplicar_evento_cgcre: reducao_escopo_cgcre nao muda perfil (era %, novo % invalido)', v_perfil_anterior, p_perfil_novo;
        END IF;
    END IF;

    --    CORRECAO_ADMINISTRATIVA: aceita qualquer transicao mas exige aprovacao manual via app.
    --    Sem validacao adicional no banco (responsabilidade do caller).

    -- 6. UPDATE no tenant.
    UPDATE tenants
    SET perfil_regulatorio          = p_perfil_novo,
        acreditacao_cgcre_numero    = CASE WHEN p_numero_rbc IS NOT NULL THEN p_numero_rbc
                                           WHEN p_perfil_novo != 'A' THEN NULL
                                           ELSE acreditacao_cgcre_numero END,
        acreditacao_suspensa_em     = CASE WHEN p_direcao = 'suspensao_temporaria_cgcre' THEN p_suspensa_em
                                           WHEN p_direcao IN ('cancelamento_cgcre') THEN NULL
                                           ELSE acreditacao_suspensa_em END,
        acreditacao_suspensa_ate    = CASE WHEN p_direcao = 'suspensao_temporaria_cgcre' THEN p_suspensa_ate
                                           WHEN p_direcao IN ('cancelamento_cgcre') THEN NULL
                                           ELSE acreditacao_suspensa_ate END,
        ilac_mra_aderido            = CASE WHEN p_ilac_mra_aderido IS NOT NULL THEN p_ilac_mra_aderido
                                           WHEN p_perfil_novo != 'A' THEN FALSE
                                           ELSE ilac_mra_aderido END,
        atualizado_em               = NOW()
    WHERE id = p_tenant_id;

    -- 7. INSERT no historico (append-only — trigger valida).
    v_historico_id := gen_random_uuid();
    INSERT INTO tenant_perfil_historico (
        id, tenant_id, perfil_anterior, perfil_novo, direcao, motivo,
        evento_origem_id, auditor_cgcre, certificado_acreditacao_documento_id,
        registrado_em, registrado_por_usuario_id, assinatura_a3_id
    ) VALUES (
        v_historico_id, p_tenant_id, v_perfil_anterior, p_perfil_novo, p_direcao, p_motivo,
        p_evento_origem_id, p_auditor_cgcre, p_documento_cgcre_id,
        NOW(), p_registrado_por_id, p_assinatura_a3_id
    );

    -- 8. INSERT outbox event TenantPerfilAlterado (INV-006).
    --    Emite em {promocao, suspensao, cancelamento}. Reducao e correcao
    --    consolidam apenas no relatorio trimestral (US-008).
    v_emite_outbox := p_direcao IN (
        'promocao_regulatoria',
        'suspensao_temporaria_cgcre',
        'cancelamento_cgcre'
    );

    IF v_emite_outbox THEN
        v_outbox_causation_id := v_historico_id;
        v_acao_outbox := 'tenant.perfil_alterado';
        v_outbox_payload := jsonb_build_object(
            'event_id', gen_random_uuid()::text,
            '_schema_version', 'v1',
            'event_name', v_acao_outbox,
            'occurred_at', to_char(NOW() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
            'correlation_id', current_setting('app.correlation_id', true),
            'actor', COALESCE(p_registrado_por_id::text, 'sistema'),
            'acao', v_acao_outbox,
            'payload', jsonb_build_object(
                'tenant_id_hash', md5(p_tenant_id::text),
                'perfil_anterior', v_perfil_anterior,
                'perfil_novo', p_perfil_novo,
                'direcao', p_direcao,
                'registrado_em', NOW(),
                'assinatura_a3_id', p_assinatura_a3_id,
                'documento_cgcre_id', p_documento_cgcre_id,
                'notifica_d_e_o', p_direcao = 'cancelamento_cgcre'
            ),
            'causation_id', v_outbox_causation_id::text,
            'tenant_id', p_tenant_id::text,
            'usuario_id', p_registrado_por_id,
            'resource_summary', format('tenant=%s perfil=%s->%s', p_tenant_id, v_perfil_anterior, p_perfil_novo)
        );

        INSERT INTO bus_outbox (
            id, causation_id, acao, envelope_jsonb, tenant_id, criado_em, tentativas
        ) VALUES (
            gen_random_uuid(), v_outbox_causation_id, v_acao_outbox, v_outbox_payload,
            p_tenant_id, NOW(), 0
        )
        ON CONFLICT (causation_id, acao) DO NOTHING;
    END IF;

    RETURN v_historico_id;
END;
$$;

-- Documentacao da funcao para introspection.
COMMENT ON FUNCTION aplicar_evento_cgcre IS
'ADR-0067 + SAN-PERFIL-TENANT T-SAN-PERFIL-008. Funcao canonica de mutacao de '
'tenant.perfil_regulatorio para fluxos CGCRE (promocao/suspensao/cancelamento/'
'reducao/correcao). UPDATE + INSERT historico + INSERT outbox em transacao unica. '
'SECURITY DEFINER bypassa RLS de bus_outbox (cravando tenant_id explicito). '
'Concorrencia via advisory lock por tenant. Caminho oficial autorizado por '
'INV-TENANT-PERFIL-002 (hook tenant-perfil-imutavel-check valida).';
"""


SQL_REMOVE_FUNCAO = """
DROP FUNCTION IF EXISTS aplicar_evento_cgcre(
    TEXT, UUID, CHAR(1), TEXT, UUID, TEXT, UUID, UUID, UUID, DATE, DATE, TEXT, BOOLEAN
);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("tenant", "0007_tenant_perfil_historico_table"),
        ("audit", "0011_bus_outbox"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_CRIA_FUNCAO_APLICAR_EVENTO_CGCRE,
            reverse_sql=SQL_REMOVE_FUNCAO,
        ),
    ]
