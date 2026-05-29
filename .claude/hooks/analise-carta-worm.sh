#!/usr/bin/env bash
# =============================================================
# analise-carta-worm.sh  (INV-PAD-010 / ADR-0070)
# Protege a tabela `analise_carta_controle` como WORM (append-only).
#
# AnaliseCartaControle e o registro probatorio CONGELADO da decisao do RT
# sobre a carta de controle Shewhart (LC/UCL/LCL/sigma + versao_motor +
# decisao_rt + justificativa hash). Uma vez gravado, NUNCA muda nem some
# (ISO 17025 cl. 8.4 retencao + cl. 7.11 validacao software + INV-PAD-010).
#
# Bloqueia (exit 2) qualquer escrita .py/.sql que contenha:
#   - UPDATE analise_carta_controle SET ...
#   - DELETE FROM analise_carta_controle
#   - TRUNCATE [TABLE] analise_carta_controle
#   - DROP TRIGGER analise_carta_controle_append_only*
#   - DROP FUNCTION analise_carta_controle_append_only
#   - ALTER TABLE analise_carta_controle ... DISABLE ROW LEVEL SECURITY
#   - ALTER TABLE analise_carta_controle DROP CONSTRAINT
#
# Auto-allow (PASS):
#   - .md (doc nao aciona)
#   - tests / fixtures
#   - a propria migration de criacao do trigger WORM (tem CREATE + reverse_sql
#     com DROP na mesma RunSQL). Heuristica: se o conteudo TAMBEM cria o
#     trigger/funcao append_only, e migration valida.
#   - override explicito com justificativa (>= 10 chars apos --)
#
# Override (raro, exige aprovacao Roldao):
#   # analise-carta-worm: skip -- <razao com >=10 chars>
#
# Razao: agente IA pode tentar "corrigir" uma analise de carta congelada
# (ex: recalcular UCL/LCL e regravar a linha) como atalho. NAO existe atalho —
# decisao errada exige NOVA AnaliseCartaControle (append), nunca mutar a antiga.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"x.sql","content":"UPDATE analise_carta_controle SET decisao_rt='\''X'\'';"}}' | bash .claude/hooks/analise-carta-worm.sh
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

# Pula testes / fixtures
case "$norm_path" in
    */tests/*|*/test_*|*_test.py|*/fixtures/*) exit 0 ;;
esac

# AUTO-ALLOW: a propria migration de criacao do trigger WORM tem REVERSE_SQL
# com DROP. Se o MESMO conteudo tambem CRIA o trigger/funcao append_only, e
# parte de uma migration valida (FORWARD com CREATE + REVERSE com DROP).
if printf '%s' "$content" | grep -qiE 'CREATE[[:space:]]+TRIGGER[[:space:]]+analise_carta_controle_append_only'; then
    exit 0
fi
if printf '%s' "$content" | grep -qiE 'CREATE[[:space:]]+(OR[[:space:]]+REPLACE[[:space:]]+)?FUNCTION[[:space:]]+analise_carta_controle_append_only'; then
    exit 0
fi

# Override com justificativa explicita (>= 10 chars uteis apos --)
if printf '%s' "$content" | grep -qE '#[[:space:]]*analise-carta-worm:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Padroes que rasgam a defesa WORM da carta de controle
violacao=""

if printf '%s' "$content" | grep -qiE 'DROP[[:space:]]+TRIGGER[[:space:]]+(IF[[:space:]]+EXISTS[[:space:]]+)?analise_carta_controle_append_only'; then
    violacao="DROP TRIGGER analise_carta_controle_append_only*"
elif printf '%s' "$content" | grep -qiE 'DROP[[:space:]]+FUNCTION[[:space:]]+(IF[[:space:]]+EXISTS[[:space:]]+)?analise_carta_controle_append_only'; then
    violacao="DROP FUNCTION analise_carta_controle_append_only"
elif printf '%s' "$content" | grep -qiE 'ALTER[[:space:]]+TABLE[[:space:]]+analise_carta_controle.*DISABLE[[:space:]]+ROW[[:space:]]+LEVEL[[:space:]]+SECURITY'; then
    violacao="ALTER TABLE analise_carta_controle DISABLE ROW LEVEL SECURITY"
elif printf '%s' "$content" | grep -qiE 'TRUNCATE[[:space:]]+(TABLE[[:space:]]+)?analise_carta_controle'; then
    violacao="TRUNCATE analise_carta_controle"
elif printf '%s' "$content" | grep -qiE 'DELETE[[:space:]]+FROM[[:space:]]+analise_carta_controle'; then
    violacao="DELETE FROM analise_carta_controle"
elif printf '%s' "$content" | grep -qiE 'UPDATE[[:space:]]+analise_carta_controle[[:space:]]+SET'; then
    violacao="UPDATE analise_carta_controle SET ..."
elif printf '%s' "$content" | grep -qiE 'ALTER[[:space:]]+TABLE[[:space:]]+analise_carta_controle[[:space:]]+DROP[[:space:]]+CONSTRAINT'; then
    violacao="ALTER TABLE analise_carta_controle DROP CONSTRAINT"
fi

if [ -n "$violacao" ]; then
    echo "analise-carta-worm: tentativa de mutar/remover defesa WORM da carta de controle em $file_path" >&2
    echo "Padrao detectado: $violacao" >&2
    echo "AnaliseCartaControle e registro probatorio CONGELADO (ADR-0070 + INV-PAD-010 + ISO 17025 cl. 8.4)." >&2
    echo "Decisao errada exige NOVA analise (append), nunca mutar/apagar a antiga." >&2
    echo "Override (raro, exige aprovacao Roldao): adicione '# analise-carta-worm: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
