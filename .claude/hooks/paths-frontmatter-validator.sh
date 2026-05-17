#!/usr/bin/env bash
# =============================================================
# paths-frontmatter-validator.sh
# Garante que TODO arquivo em .claude/rules/ tem frontmatter com paths: declarado.
# Sem paths:, a regra carrega em todo turno (eager) e queima contexto a toa.
# Evento: PreToolUse(Write|Edit) em .claude/rules/*.md
#
# Como funciona:
#   - Le tool_input.content + file_path
#   - Se file_path bate em .claude/rules/*.md (mas nao .gitkeep)
#   - Verifica que content comeca com frontmatter "---\n...paths:\n---"
#   - Exit 2 se faltar paths:
#
# Como testar:
#   echo '{"tool_input":{"file_path":".claude/rules/foo.md","content":"# Regra\nsem frontmatter"}}' | bash .claude/hooks/paths-frontmatter-validator.sh
#   echo $?    # esperar 2
#
#   echo '{"tool_input":{"file_path":".claude/rules/foo.md","content":"---\npaths: [src/**/*.py]\n---\n# Regra"}}' | bash .claude/hooks/paths-frontmatter-validator.sh
#   echo $?    # esperar 0
# =============================================================

set -u

input=$(cat)

file_path=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    print $j->{tool_input}{file_path} // "";
' 2>/dev/null)

# So se aplica a arquivos em .claude/rules/*.md (exceto .gitkeep)
case "$file_path" in
    *.claude/rules/*.md|*\.claude\\rules\\*.md|*.claude/rules/*/*.md) ;;
    *) exit 0 ;;
esac

# Ignora .gitkeep ou README
case "$file_path" in
    *.gitkeep|*/README.md|*/readme.md) exit 0 ;;
esac

content=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $ti = $j->{tool_input} // {};
    print $ti->{content} // $ti->{new_string} // "";
' 2>/dev/null)

[ -z "$content" ] && exit 0

# Verifica que comeca com frontmatter (---)
if ! printf '%s' "$content" | head -n 1 | grep -qE '^---[[:space:]]*$'; then
    echo "paths-frontmatter-validator: arquivo em .claude/rules/ sem frontmatter YAML em $file_path" >&2
    echo "Adicione no topo:" >&2
    echo "---" >&2
    echo "paths: [\"src/**/*.py\"]   # glob das pastas onde esta regra carrega" >&2
    echo "---" >&2
    exit 2
fi

# Extrai frontmatter (entre os dois ---) e verifica que tem paths:
fm=$(printf '%s' "$content" | awk '/^---[[:space:]]*$/{c++; next} c==1{print}' 2>/dev/null)

if ! printf '%s' "$fm" | grep -qE '^paths:'; then
    echo "paths-frontmatter-validator: frontmatter sem campo 'paths:' em $file_path" >&2
    echo "Regra carregaria em todo turno (eager) e queimaria contexto. Adicione paths: [glob]." >&2
    exit 2
fi

exit 0
