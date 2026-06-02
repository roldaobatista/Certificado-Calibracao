#!/usr/bin/env bash
# =============================================================
# tenant-perfil-imutavel-check.sh — T-SAN-PERFIL-013 / AC-001-5 / INV-TENANT-PERFIL-002
#
# Bloqueia (exit 2) escritas que tentem burlar a imutabilidade controlada
# de `tenant.perfil_regulatorio`:
#   - UPDATE tenants SET perfil_regulatorio = ... (deveria usar funcao SECURITY DEFINER)
#   - DROP TRIGGER tph_anti_*_trigger
#   - DROP FUNCTION tph_anti_mutation_block
#   - DROP FUNCTION aplicar_evento_cgcre
#   - DROP FUNCTION rebaixar_perfil_tenant_voluntario_cliente
#   - ALTER TABLE tenants DROP COLUMN perfil_regulatorio
#   - DELETE FROM tenant_perfil_historico (append-only)
#   - UPDATE tenant_perfil_historico (append-only)
#   - UPDATE tenants SET acreditacao_* (cache vigencia/CGCRE so via aplicar_evento_cgcre —
#     INV-LIC-VIG-SYNC-001 / M9 D-LIC-8; SQL direto OU Tenant.objects.update())
#
# Mutacao legitima passa pelas 2 funcoes SECURITY DEFINER que rodam dentro
# da PROPRIA transacao + INSERT em TenantPerfilHistorico + outbox event.
#
# AUTO-ALLOW:
#   - Migration que CRIA a coluna/funcao/trigger (parte de DROP no reverse_sql).
#   - Caminho oficial src/infrastructure/tenant/management/commands/aplicar_evento_cgcre.py
#     (a criar em P5) ou views que chamam SQL via raw com select_for_update.
#
# Override: linha contendo '# tenant-perfil-imutavel: skip -- <razao com >=10 chars>'
# (decisao consciente do Roldao pra migration de manutencao).
#
# Origem: SAN-PERFIL-TENANT (ADR-0067 aceita 2026-05-27).
# =============================================================

set -u

input=$(cat)

content=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $ti = $j->{tool_input} // {};
    my $c = $ti->{content} // $ti->{new_string} // "";
    print $c;
' 2>/dev/null)

file_path=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    print $j->{tool_input}{file_path} // "";
' 2>/dev/null)

[ -z "$content" ] && exit 0

norm_path="${file_path//\\//}"

# So .py e .sql (codigo executavel)
case "$norm_path" in
    *.py|*.sql) ;;
    *) exit 0 ;;
esac

# Pula testes
case "$norm_path" in
    */tests/*|*/test_*|*_test.py) exit 0 ;;
esac

# AUTO-ALLOW: migration que CRIA o trigger/funcao/coluna (DROP esta no reverse_sql).
if printf '%s' "$content" | grep -qiE 'CREATE[[:space:]]+(OR[[:space:]]+REPLACE[[:space:]]+)?FUNCTION[[:space:]]+(tph_anti_mutation_block|aplicar_evento_cgcre|rebaixar_perfil_tenant_voluntario_cliente)'; then
    exit 0
fi
if printf '%s' "$content" | grep -qiE 'CREATE[[:space:]]+TRIGGER[[:space:]]+tph_anti_'; then
    exit 0
fi
if printf '%s' "$content" | grep -qiE 'ADD[[:space:]]+(COLUMN[[:space:]]+)?perfil_regulatorio'; then
    exit 0
fi

# AUTO-ALLOW: migrations 0003 e 0004 fazem UPDATE direto antes da trigger existir.
# Heuristica: arquivo eh migration tenant/0003_* ou 0004_* (ou similar de backfill).
case "$norm_path" in
    *tenant/migrations/0003_perfil_regulatorio_add_nullable.py) exit 0 ;;
    *tenant/migrations/0004_perfil_regulatorio_backfill.py) exit 0 ;;
esac

# Override explicito com justificativa
if printf '%s' "$content" | grep -qE '#[[:space:]]*tenant-perfil-imutavel:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# AUTO-ALLOW: caminho oficial das funcoes SECURITY DEFINER + outbox.
# O comando provisionar_tenant (T-031) tambem chama aplicar_evento_cgcre via raw.
case "$norm_path" in
    *src/application/tenant/aplicar_evento_cgcre.py|*src/application/tenant/rebaixar_voluntario.py|*src/infrastructure/tenant/management/commands/provisionar_tenant.py|*src/infrastructure/tenant/services_perfil.py)
        exit 0
        ;;
esac

# Padroes que rasgam a defesa
violacao=""

if printf '%s' "$content" | grep -qiE 'UPDATE[[:space:]]+tenants[[:space:]]+SET[[:space:]]+perfil_regulatorio'; then
    violacao="UPDATE tenants SET perfil_regulatorio (use aplicar_evento_cgcre ou rebaixar_perfil_tenant_voluntario_cliente)"
elif printf '%s' "$content" | grep -qiE 'DROP[[:space:]]+TRIGGER[[:space:]]+tph_anti_'; then
    violacao="DROP TRIGGER tph_anti_* (trigger anti-mutacao da tabela append-only)"
elif printf '%s' "$content" | grep -qiE 'DROP[[:space:]]+FUNCTION[[:space:]]+tph_anti_mutation_block'; then
    violacao="DROP FUNCTION tph_anti_mutation_block"
elif printf '%s' "$content" | grep -qiE 'DROP[[:space:]]+FUNCTION[[:space:]]+(aplicar_evento_cgcre|rebaixar_perfil_tenant_voluntario_cliente)'; then
    violacao="DROP FUNCTION das funcoes SECURITY DEFINER de mutacao de perfil"
elif printf '%s' "$content" | grep -qiE 'ALTER[[:space:]]+TABLE[[:space:]]+tenants[[:space:]]+DROP[[:space:]]+COLUMN[[:space:]]+perfil_regulatorio'; then
    violacao="ALTER TABLE tenants DROP COLUMN perfil_regulatorio"
elif printf '%s' "$content" | grep -qiE 'ALTER[[:space:]]+TABLE[[:space:]]+tenants[[:space:]]+ALTER[[:space:]]+COLUMN[[:space:]]+perfil_regulatorio'; then
    violacao="ALTER TABLE tenants ALTER COLUMN perfil_regulatorio"
elif printf '%s' "$content" | grep -qiE 'UPDATE[[:space:]]+tenants[[:space:]]+SET[[:space:]].*acreditacao_(vigencia_fim|vigencia_inicio|cgcre_numero|suspensa_em|suspensa_ate)'; then
    violacao="UPDATE tenants SET acreditacao_* (cache de acreditacao so via aplicar_evento_cgcre — INV-LIC-VIG-SYNC-001 / M9 D-LIC-8)"
elif printf '%s' "$content" | grep -qiE 'Tenant\.objects.*\.update\([^)]*acreditacao_(vigencia_fim|vigencia_inicio|cgcre_numero|suspensa_em|suspensa_ate)'; then
    violacao="Tenant.objects.update(acreditacao_*) (cache de acreditacao so via aplicar_evento_cgcre — INV-LIC-VIG-SYNC-001 / M9 D-LIC-8)"
elif printf '%s' "$content" | grep -qiE 'DELETE[[:space:]]+FROM[[:space:]]+tenant_perfil_historico'; then
    violacao="DELETE FROM tenant_perfil_historico (tabela append-only)"
elif printf '%s' "$content" | grep -qiE 'UPDATE[[:space:]]+tenant_perfil_historico[[:space:]]+SET'; then
    violacao="UPDATE tenant_perfil_historico (tabela append-only)"
elif printf '%s' "$content" | grep -qiE 'ALTER[[:space:]]+TABLE[[:space:]]+tenant_perfil_historico[[:space:]]+DISABLE'; then
    violacao="ALTER TABLE tenant_perfil_historico DISABLE TRIGGER (defesa anti-mutacao)"
fi

if [ -n "$violacao" ]; then
    echo "tenant-perfil-imutavel-check: tentativa de burlar INV-TENANT-PERFIL-002 em $file_path" >&2
    echo "Padrao detectado: $violacao" >&2
    echo "Mutacao de tenant.perfil_regulatorio so via funcoes SECURITY DEFINER:" >&2
    echo "  - aplicar_evento_cgcre(direcao, ...) — fluxos CGCRE + provisioning + correcao" >&2
    echo "  - rebaixar_perfil_tenant_voluntario_cliente() — autonomia tenant (cooldown 30d)" >&2
    echo "TenantPerfilHistorico e append-only (INV-TENANT-PERFIL-002)." >&2
    echo "Override (raro, exige aprovacao Roldao):" >&2
    echo "  '# tenant-perfil-imutavel: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
