#!/usr/bin/env bash
# =============================================================
# feature-perfil-matriz-validator.sh — T-SAN-PERFIL-038 / AC-005-3
#
# Bloqueia (exit 2) commit de PRD novo (docs/dominios/**/prd.md) ou ADR novo
# (docs/adr/*.md) que adicione US-* / AC-*-N em feature listada na matriz
# `docs/conformidade/comum/matriz-feature-perfil.md` sem que a feature
# correspondente exista naquela matriz.
#
# Heuristica (T12 reescrito do plan.md):
#   - Path: docs/dominios/*/modulos/*/prd.md OU docs/adr/*.md OU
#           docs/faseamento/*/spec.md
#   - Match grep: linhas com `US-` ou `AC-` indicam declaracao de feature.
#   - Para cada US/AC novo no diff, valida que o "tema" da US ja consta
#     na matriz (busca por palavras-chave: regra de decisao, 2a conferencia,
#     validacao software, TSA-ITI, ILAC-MRA, A3, GUM, Monte Carlo, etc).
#   - Se for adicao GENERICA (nao toca temas da matriz), passa.
#
# Override: linha contendo '# feature-perfil-matriz: skip -- <razao com >=10 chars>'
#
# Origem: SAN-PERFIL-TENANT — ADR-0067 §4 Decisao.
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

# So PRDs, ADRs e specs de faseamento.
case "$norm_path" in
    *docs/dominios/*/modulos/*/prd.md) ;;
    *docs/adr/*.md) ;;
    *docs/faseamento/*/spec.md) ;;
    *) exit 0 ;;
esac

# AUTO-ALLOW: a propria matriz nao se valida.
case "$norm_path" in
    *docs/conformidade/comum/matriz-feature-perfil.md) exit 0 ;;
esac

# Override explicito.
if printf '%s' "$content" | grep -qE '#[[:space:]]*feature-perfil-matriz:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Procura US-*/AC-*-N que tocam temas da matriz (case-insensitive).
# Lista de temas-chave que aparecem na matriz. Se um deles aparecer
# proximo de um US/AC novo (mesma linha ou ate 3 linhas antes/depois),
# a matriz precisa cobrir.
TEMAS_MATRIZ="regra de decisao|2a conferencia|2ª conferencia|segunda conferencia|validacao software|validação de software|TSA-ITI|ILAC-MRA|A3 ICP-Brasil|GUM|Monte Carlo|snapshot RT|template certificado|selo CGCRE|selo RBC|subcontratacao|reclamacao CDC|retencao 25a|verificacao periodica vigencia"

# Verifica se o conteudo declara feature crítica.
# `-w` (word-match): termos so casam como palavra inteira — evita
# falso-positivo "GUM" dentro de "alGUMa"/"alGUM" (palavra comum em PT-BR)
# e siglas curtas (A3) coladas a outras letras.
if ! printf '%s' "$content" | grep -qiwE "$TEMAS_MATRIZ"; then
    # Diff nao toca tema da matriz — passa.
    exit 0
fi

# Tem tema da matriz. Verifica se ha referencia a `matriz-feature-perfil.md`
# OU se o tema esta mencionado em conjunto com perfis A/B/C/D
# (sinaliza que o autor pensou em perfil).
if printf '%s' "$content" | grep -qiE 'matriz-feature-perfil|perfil[[:space:]]*[ABCD]|perfil_regulatorio|perfil_a|perfil_b|perfil_c|perfil_d'; then
    exit 0
fi

# Sinal de problema: PRD/ADR adicionando feature de tema sensivel sem
# pensar em perfil. Bloquear.
echo "feature-perfil-matriz-validator: $file_path declara feature de tema sensivel sem referenciar perfil regulatorio." >&2
echo "" >&2
echo "Tema(s) detectado(s) na declaracao:" >&2
printf '%s' "$content" | grep -inwE "$TEMAS_MATRIZ" | head -3 >&2
echo "" >&2
echo "Toda feature critica tem comportamento condicional por perfil (ADR-0067 §4)." >&2
echo "Acoes possiveis:" >&2
echo "  1. Referencie matriz: docs/conformidade/comum/matriz-feature-perfil.md" >&2
echo "  2. Mencione perfil regulatorio (A/B/C/D) explicitamente no AC/INV" >&2
echo "  3. Adicione linha na matriz cobrindo o comportamento do tema novo" >&2
echo "" >&2
echo "Override (raro): '# feature-perfil-matriz: skip -- <razao com >=10 chars>'" >&2
exit 2
