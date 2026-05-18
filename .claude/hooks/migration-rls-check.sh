#!/usr/bin/env bash
# =============================================================
# migration-rls-check.sh
# Enforce INV-TENANT-003 — toda tabela com tenant_id criada por migration TEM
# que receber RLS policy na mesma migration (ou em uma migration explicitamente
# referenciada).
#
# Evento: PreToolUse(Write|Edit) em arquivos */migrations/*.py
#
# Como funciona:
#   - Le tool_input.content / new_string + file_path
#   - Se nao for migration -> pass
#   - Se migration nao cria tabela com tenant_id -> pass
#   - Se migration cria + tem CREATE POLICY ou ENABLE ROW LEVEL SECURITY -> pass
#   - Se migration cria + tem comentario "# rls-policy: external NNNN" -> pass
#   - Caso contrario -> bloqueia (exit 2)
#
# Allowlist hard-coded (tabelas SHARED ACROSS TENANTS, sem tenant_id):
#   tenants, usuarios (mas usuario_perfil_tenant tem tenant_id e exige policy)
#
# Como testar:
#   echo '{"tool_input":{"file_path":"app/migrations/0001.py","content":"CreateModel ... tenant_id ... sem policy"}}' | bash .claude/hooks/migration-rls-check.sh
#   echo $?  # 2
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

# Normaliza separadores Windows
norm_path="${file_path//\\//}"

# So aciona em migrations Python
case "$norm_path" in
    */migrations/*.py) ;;
    *) exit 0 ;;
esac

# Pula __init__.py de migrations
case "$norm_path" in
    */migrations/__init__.py) exit 0 ;;
esac

# Detecta criacao de tabela COM tenant_id
# Patterns: campo explicito tenant_id, FK com to='tenant.Tenant', name="tenant" em ForeignKey
tem_create=0
if printf '%s' "$content" | grep -qiE '(CreateModel|CREATE[[:space:]]+TABLE|op\.create_table)'; then
    tem_create=1
fi

tem_tenant_id=0
if [ "$tem_create" -eq 1 ]; then
    if printf '%s' "$content" | grep -qE '(tenant_id|"tenant"|name="tenant",|to="tenant\.Tenant"|ForeignKey.*tenant\.Tenant)'; then
        tem_tenant_id=1
    fi
fi

# Sem create OU sem tenant_id => nada pra checar
[ "$tem_tenant_id" -eq 0 ] && exit 0

# Tem CREATE POLICY ou ENABLE ROW LEVEL SECURITY na mesma migration?
if printf '%s' "$content" | grep -qiE '(CREATE[[:space:]]+POLICY|ENABLE[[:space:]]+ROW[[:space:]]+LEVEL[[:space:]]+SECURITY)'; then
    exit 0
fi

# Override por comentario: # rls-policy: external NNNN_<nome>
if printf '%s' "$content" | grep -qE '#[[:space:]]*rls-policy:[[:space:]]*external'; then
    exit 0
fi

echo "migration-rls-check (INV-TENANT-003): migration cria tabela com tenant_id sem CREATE POLICY na mesma migration em $file_path" >&2
echo "Adicione 'migrations.RunSQL(CREATE POLICY ... ENABLE ROW LEVEL SECURITY ...)' OU" >&2
echo "use comentario '# rls-policy: external 0002_rls_setup' apontando outra migration." >&2
exit 2
