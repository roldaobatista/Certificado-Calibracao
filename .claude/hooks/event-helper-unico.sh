#!/usr/bin/env bash
# =============================================================
# event-helper-unico.sh — T-CLI-105 / SANEA-08
#
# Bloqueia (exit 2) chamada direta a `registrar_em_cadeia` OU
# `registrar_auditoria` OU INSERT em `bus_outbox` fora da allowlist.
# Padrão único Wave A: `audit.event_helpers.publicar_evento`.
#
# Allowlist (auto-allow — exit 0):
#   - src/infrastructure/audit/**     (a primitiva mora aqui)
#   - src/infrastructure/multitenant/** (circular import com audit)
#   - tests/**                         (testam a primitiva)
#   - **/migrations/**                 (data migration one-off)
#
# Override em arquivo fora da allowlist:
#   # event-helper: skip -- <razão com >=10 chars>
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/clientes/services.py","content":"registrar_em_cadeia(...)"}}' | bash .claude/hooks/event-helper-unico.sh
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

norm_path="${file_path//\\//}"

# Só .py (código Python — SQL puro é coberto por outros hooks)
case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# AUTO-ALLOW pelo caminho
case "$norm_path" in
    *src/infrastructure/audit/*) exit 0 ;;
    *src/infrastructure/multitenant/*) exit 0 ;;
    */tests/*|*/test_*|*_test.py) exit 0 ;;
    */migrations/*) exit 0 ;;
esac

# Override com justificativa
if printf '%s' "$content" | grep -qE '#[[:space:]]*event-helper:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Padrões proibidos fora da allowlist
violacao=""

if printf '%s' "$content" | grep -qE '\bregistrar_em_cadeia[[:space:]]*\('; then
    violacao="chamada direta a registrar_em_cadeia()"
elif printf '%s' "$content" | grep -qE '\bregistrar_auditoria[[:space:]]*\('; then
    violacao="chamada direta a registrar_auditoria()"
elif printf '%s' "$content" | grep -qiE 'INSERT[[:space:]]+INTO[[:space:]]+bus_outbox'; then
    violacao="INSERT SQL cru em bus_outbox"
fi

if [ -n "$violacao" ]; then
    echo "event-helper-unico: $violacao em $file_path" >&2
    echo "Use o helper único: from src.infrastructure.audit.event_helpers import publicar_evento" >&2
    echo "Garantias 1-4 (sanitize em escrita, validação de tenant, atomicidade do caller, idempotência)" >&2
    echo "ficam centralizadas — não duplicar envelope (SANEA-08)." >&2
    echo "Override (raro): adicione '# event-helper: skip -- <razão com >=10 chars>'" >&2
    exit 2
fi

exit 0
