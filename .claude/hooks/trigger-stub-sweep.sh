#!/usr/bin/env bash
# =============================================================
# trigger-stub-sweep.sh — Marco 2 P-EQP-T7
#
# Bloqueia commits que mantenham triggers/funcoes PG com sufixo
# `_v0_stub` (placeholders provisorios) chegando em migration. O
# sufixo eh marcador deliberado: codigo agente cria stub durante
# desenvolvimento, mas precisa converter em implementacao final
# (sem `_v0_stub`) antes de cair em release.
#
# Padrao detectado (case-insensitive):
#   - `_v0_stub` em qualquer nome de trigger/function/procedure
#     em arquivo .py de migration ou em arquivo .sql.
#
# Auto-allow (exit 0):
#   - tests/**                    (testam stubs)
#   - **/test_*.py
#   - **/_test-runner.sh          (este proprio executor)
#   - .claude/hooks/**            (o proprio hook eh testado com fixture)
#
# Override em arquivo fora da allowlist:
#   # trigger-stub-sweep: skip -- <razao com >=10 chars>
#
# Como testar:
#   echo '{"tool_input":{"file_path":"migrations/0099.py","content":"CREATE TRIGGER foo_v0_stub..."}}' | bash .claude/hooks/trigger-stub-sweep.sh
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

# Override com justificativa
if printf '%s' "$content" | grep -qE '#[[:space:]]*trigger-stub-sweep:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# AUTO-ALLOW pelo caminho — tests/hooks tocam o pattern.
case "$norm_path" in
    tests/*|*/tests/*|*/test_*.py|*_test.py) exit 0 ;;
    .claude/hooks/*|*/.claude/hooks/*) exit 0 ;;
esac

# So checa arquivos relevantes — migrations Python + SQL.
case "$norm_path" in
    */migrations/*.py|*.sql) ;;
    *) exit 0 ;;
esac

# Detecta `_v0_stub` em qualquer nome de identificador (case
# insensitive — match _v0_stub, _V0_STUB, foo_v0_stub_check, etc).
if printf '%s' "$content" | grep -qiE '[A-Za-z0-9_]*_v0_stub[A-Za-z0-9_]*'; then
    echo "trigger-stub-sweep (P-EQP-T7): identifier com sufixo '_v0_stub' em $file_path" >&2
    echo "Trigger/funcao PG marcada como stub provisorio. Promova para implementacao" >&2
    echo "final (sem sufixo) ou justifique via:" >&2
    echo "   # trigger-stub-sweep: skip -- <razao com >=10 chars>" >&2
    exit 2
fi

exit 0
