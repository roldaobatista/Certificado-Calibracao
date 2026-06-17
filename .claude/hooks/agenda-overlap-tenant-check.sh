#!/usr/bin/env bash
# =============================================================
# agenda-overlap-tenant-check.sh — agenda Fatia 3d / INV-AG-OVERLAP-001 (T-AGE-047)
#
# Garante que o EXCLUDE GIST de overlap da agenda inclui `tenant_id` como
# primeira coluna da constraint (isolamento multi-tenant ADR-0002 + R1).
# Sem `tenant_id` na EXCLUDE, um técnico de tenant B poderia colidir com
# o slot de técnico de tenant A — furo de isolamento silencioso (RLS não
# escopa constraints de exclusão).
#
# Heurística (só em migrations de agenda):
#   Atua em '*/agenda/migrations/*.py' que contém 'ExclusionConstraint'
#   ou 'EXCLUDE USING'.
#   BLOCK quando:
#     - contem ExclusionConstraint ou EXCLUDE USING
#     - SEM mencionar 'tenant_id' na mesma migration
#
# Auto-allow (exit 0):
#   - tests/** ; docs/** ; não-.py
#   - migrations que NÃO mencionam ExclusionConstraint nem EXCLUDE USING
#   - override: '# agenda-overlap-tenant: skip -- <razão >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/agenda/migrations/0003.py","content":"ExclusionConstraint(fields=[\"tecnico_id\"])"}}' | bash .claude/hooks/agenda-overlap-tenant-check.sh; echo $?  # 2
#   echo '{"tool_input":{"file_path":"src/infrastructure/agenda/migrations/0003.py","content":"ExclusionConstraint(fields=[\"tenant_id\",\"tecnico_id\"])"}}' | bash .claude/hooks/agenda-overlap-tenant-check.sh; echo $?  # 0
# =============================================================

set -u

input=$(cat)

content=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $ti = $j->{tool_input} // {};
    print $ti->{content} // $ti->{new_string} // "";
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

# So arquivos .py
case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# So migrations da frente agenda
case "$norm_path" in
    */agenda/migrations/*) ;;
    *) exit 0 ;;
esac

# tests/ e docs/ ignorados
case "$norm_path" in
    tests/*|*/tests/*|docs/*|*/docs/*) exit 0 ;;
esac

# Se nao menciona ExclusionConstraint nem EXCLUDE USING, nao ha risco.
if ! printf '%s' "$content" | grep -qiE 'ExclusionConstraint|EXCLUDE[[:space:]]+USING'; then
    exit 0
fi

# Override global
if printf '%s' "$content" | grep -qE '#[[:space:]]*agenda-overlap-tenant:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Verifica se tenant_id esta presente na mesma migration.
if printf '%s' "$content" | grep -qE 'tenant_id'; then
    exit 0
fi

# ExclusionConstraint sem tenant_id — BLOCK.
echo "agenda-overlap-tenant (INV-AG-OVERLAP-001): $file_path contem ExclusionConstraint/EXCLUDE USING sem 'tenant_id'." >&2
echo "" >&2
echo "O EXCLUDE GIST de overlap DEVE incluir tenant_id como 1ª coluna (ADR-0002 / R1):" >&2
echo "  ExclusionConstraint(" >&2
echo "    fields=[('tenant_id','='),('tecnico_id','='),('slot','&&')]," >&2
echo "    condition=Q(estado__ne='cancelado')," >&2
echo "  )" >&2
echo "Sem tenant_id, técnico de tenant B pode colidir com slot de tenant A silenciosamente." >&2
echo "Override: '# agenda-overlap-tenant: skip -- <razão com >=10 chars>'" >&2
exit 2
