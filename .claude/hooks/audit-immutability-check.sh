#!/usr/bin/env bash
# =============================================================
# audit-immutability-check.sh
# Protege a trilha de auditoria contra remocao das defesas (Marco 4 F-A).
#
# Bloqueia (exit 2) qualquer escrita que contenha:
#   - DROP TRIGGER auditoria_anti_*
#   - DROP FUNCTION auditoria_bloqueia_mutation
#   - ALTER TABLE auditoria ... DISABLE ROW LEVEL SECURITY
#   - TRUNCATE [TABLE] auditoria
#   - DELETE FROM auditoria
#   - UPDATE auditoria SET ...
#   - ALTER TABLE auditoria DROP CONSTRAINT
#
# Override: linha contendo '# audit-immutability: skip --' com justificativa
# (>= 10 chars apos --) OU se conteudo eh teste / migration de criacao do
# proprio trigger (auto-allow para reverse_sql).
#
# Razao: agente IA pode tentar "limpar audit antigo" como atalho. NAO existe
# atalho — se realmente precisa, exige aprovacao manual + override com motivo.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"x.sql","content":"DROP TRIGGER auditoria_anti_update ON auditoria;"}}' | bash .claude/hooks/audit-immutability-check.sh
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

# So .py e .sql (codigo executavel — markdown nao aciona)
case "$norm_path" in
    *.py|*.sql) ;;
    *) exit 0 ;;
esac

# Pula testes
case "$norm_path" in
    */tests/*|*/test_*|*_test.py) exit 0 ;;
esac

# AUTO-ALLOW: a propria migration de criacao do trigger tem REVERSE_SQL com DROP.
# Heuristica robusta: se o MESMO conteudo tambem cria os triggers/funcao, e
# parte de uma migration valida (criacao + reverso na mesma RunSQL).
if printf '%s' "$content" | grep -qiE 'CREATE[[:space:]]+TRIGGER[[:space:]]+auditoria_anti'; then
    exit 0
fi
if printf '%s' "$content" | grep -qiE 'CREATE[[:space:]]+(OR[[:space:]]+REPLACE[[:space:]]+)?FUNCTION[[:space:]]+auditoria_bloqueia_mutation'; then
    exit 0
fi

# Permite override com justificativa explicita (>= 10 chars uteis apos --)
if printf '%s' "$content" | grep -qE '#[[:space:]]*audit-immutability:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Padroes que rasgam a defesa
violacao=""

if printf '%s' "$content" | grep -qiE 'DROP[[:space:]]+TRIGGER[[:space:]]+auditoria_anti'; then
    violacao="DROP TRIGGER auditoria_anti_*"
elif printf '%s' "$content" | grep -qiE 'DROP[[:space:]]+FUNCTION[[:space:]]+auditoria_bloqueia_mutation'; then
    violacao="DROP FUNCTION auditoria_bloqueia_mutation"
elif printf '%s' "$content" | grep -qiE 'ALTER[[:space:]]+TABLE[[:space:]]+auditoria.*DISABLE[[:space:]]+ROW[[:space:]]+LEVEL[[:space:]]+SECURITY'; then
    violacao="ALTER TABLE auditoria DISABLE ROW LEVEL SECURITY"
elif printf '%s' "$content" | grep -qiE 'TRUNCATE[[:space:]]+(TABLE[[:space:]]+)?auditoria'; then
    violacao="TRUNCATE auditoria"
elif printf '%s' "$content" | grep -qiE 'DELETE[[:space:]]+FROM[[:space:]]+auditoria'; then
    violacao="DELETE FROM auditoria"
elif printf '%s' "$content" | grep -qiE 'UPDATE[[:space:]]+auditoria[[:space:]]+SET'; then
    violacao="UPDATE auditoria SET ..."
elif printf '%s' "$content" | grep -qiE 'ALTER[[:space:]]+TABLE[[:space:]]+auditoria[[:space:]]+DROP[[:space:]]+CONSTRAINT'; then
    violacao="ALTER TABLE auditoria DROP CONSTRAINT"
fi

if [ -n "$violacao" ]; then
    echo "audit-immutability-check: tentativa de remover defesa da trilha de auditoria em $file_path" >&2
    echo "Padrao detectado: $violacao" >&2
    echo "Audit trail e INSERT-only por design (ISO 17025 8.4 + LGPD art. 37 + Marco 4 F-A)." >&2
    echo "Override (raro, exige aprovacao Roldao): adicione '# audit-immutability: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
