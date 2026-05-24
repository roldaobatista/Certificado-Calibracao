#!/usr/bin/env bash
# =============================================================
# prd-ux-states-check.sh
# Onda 2 plano-v2 (2026-05-23) — auditor PROD apontou que PRDs
# cobrem caminho feliz mas omitem estados nao-felizes.
# Hook valida que PRD novo tem secao "UX dos estados nao-felizes".
#
# Aplica a: docs/dominios/**/prd.md
#
# Allow via:
#   - Arquivo inteiro: # prd-ux-states: skip -- <razao ≥10 chars>
# =============================================================

set -u
input=$(cat)

content=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/; my $raw = <STDIN>; my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $ti = $j->{tool_input} // {};
    print $ti->{content} // $ti->{new_string} // "";
' 2>/dev/null)

file_path=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/; my $raw = <STDIN>; my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    print $j->{tool_input}{file_path} // "";
' 2>/dev/null)

[ -z "$content" ] && exit 0
file_path_norm=$(printf '%s' "$file_path" | tr '\\' '/')

# Aplica somente a PRD de modulo de dominio
case "$file_path_norm" in
    */docs/dominios/*/modulos/*/prd.md|docs/dominios/*/modulos/*/prd.md) ;;
    *) exit 0 ;;
esac

# Pula templates
case "$file_path_norm" in
    *_TEMPLATE*|*template*) exit 0 ;;
esac

# Skip arquivo inteiro
if printf '%s' "$content" | grep -qE 'prd-ux-states:\s*skip\s*--\s*.{10,}'; then
    exit 0
fi

# Verifica se PRD tem secao de UX dos estados nao-felizes
# Aceita variacoes: "UX dos estados", "UX estados", "Estados nao-felizes", "Estados não-felizes"
if printf '%s' "$content" | grep -qiE '^##.*(UX.*estados|estados.*n[aã]o[ -]felizes|estados.*nao.felizes)' ; then
    # Tem secao — extrai conteudo da secao usando flag awk explicita
    # (range "pattern1,pattern2" falha quando proxima secao tem digito que bate [^.])
    secao=$(printf '%s' "$content" | awk '
        /^##/ {
            if (in_secao && !primeiro_h2) { exit }
            primeiro_h2 = 0
            if ($0 ~ /[Uu][Xx].*[Ee]stados/ || $0 ~ /[Ee]stados.*n[aã]o.felizes/ || $0 ~ /[Ee]stados.*nao.felizes/) {
                in_secao = 1
                primeiro_h2 = 1
                print
                next
            }
        }
        in_secao { print }
    ')

    estados_obrigatorios=("[Ee]mpty" "[Ll]oading" "5xx|servidor|server" "403|permiss[aã]o.negada|negada" "401|sess[aã]o.expirada|expirada" "duplo.submit|dupla.submiss|debounce|idempotency" "422|valida[cç][aã]o|validation" "404|n[aã]o.existe|nao.existe|not.found")

    faltando=()
    for estado in "${estados_obrigatorios[@]}"; do
        if ! printf '%s' "$secao" | grep -qiE "$estado"; then
            faltando+=("$estado")
        fi
    done

    if [ ${#faltando[@]} -gt 0 ]; then
        echo "prd-ux-states-check: secao 'UX dos estados nao-felizes' presente mas incompleta em $file_path" >&2
        echo "Estados nao cobertos:" >&2
        for f in "${faltando[@]}"; do
            echo "  - $f" >&2
        done
        echo "" >&2
        echo "Ver docs/CONVENCOES-DOC.md §5.bis para lista completa." >&2
        echo "Allow via: # prd-ux-states: skip -- <razao ≥10 chars>" >&2
        exit 2
    fi

    exit 0
fi

# Nao tem secao
echo "prd-ux-states-check: PRD sem secao 'UX dos estados nao-felizes' em $file_path" >&2
echo "" >&2
echo "Decisao Onda 2 plano-v2 (2026-05-23): PRD deve declarar AC binario para empty/loading/erro/permissao/sessao/duplo-submit/validacao/404 por tela." >&2
echo "Ver docs/CONVENCOES-DOC.md §5.bis" >&2
echo "Allow via: # prd-ux-states: skip -- <razao ≥10 chars>" >&2
exit 2
