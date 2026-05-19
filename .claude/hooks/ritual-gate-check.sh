#!/usr/bin/env bash
# =============================================================
# ritual-gate-check.sh
# Enforce INV-RITUAL-001 — nenhuma Fase/Marco/Story e marcada
# FECHADA/PASS/"pode avancar" enquanto houver achado CRITICO, ALTO
# ou MEDIO em aberto (ou FAIL/REPROVADO) no mesmo documento de status.
#
# Evento: PreToolUse(Write|Edit) em docs de status/auditoria:
#   - .agent/CURRENT.md
#   - AGENTS.md
#   - docs/faseamento/**/auditoria-familia5.md
#   - docs/dominios/**/auditorias/CONSOLIDADO.md
#
# Como funciona:
#   - Le tool_input.content / new_string + file_path (perl JSON::PP)
#   - Se nao for doc de status rastreado -> pass (exit 0)
#   - Se conteudo tem override "# ritual-gate: skip" -> pass
#   - Se conteudo tem MARCA DE FECHAMENTO de fase E TAMBEM
#     marca de achado EM ABERTO (CRITICO/ALTO/MEDIO em aberto,
#     pendente, nao resolvido, FAIL, REPROVADO) -> bloqueia (exit 2)
#   - Caso contrario -> pass
#
# Conservador de proposito: so bloqueia quando fechamento E
# achado-em-aberto coexistem. "MEDIO ... RESOLVIDO" nao casa o
# padrao de aberto, entao fase legitimamente fechada passa.
#
# Override (decisao EXCLUSIVA do Roldao, nunca do agente):
#   adicionar no proprio doc/commit a linha:
#   # ritual-gate: skip -- APROVADO POR ROLDAO: <razao >=10 chars>
#
# Como testar:
#   echo '{"tool_input":{"file_path":".agent/CURRENT.md","content":"FASE FECHADA\nMEDIO-3: x em aberto"}}' | bash .claude/hooks/ritual-gate-check.sh ; echo $?  # 2
#   echo '{"tool_input":{"file_path":".agent/CURRENT.md","content":"FASE FECHADA\nReparos MEDIO/BAIXO RESOLVIDOS"}}' | bash .claude/hooks/ritual-gate-check.sh ; echo $?  # 0
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

# So aciona em docs de status/auditoria rastreados
tracked=0
case "$norm_path" in
    *.agent/CURRENT.md) tracked=1 ;;
    */AGENTS.md|AGENTS.md) tracked=1 ;;
    */docs/faseamento/*/auditoria-familia5.md) tracked=1 ;;
    */docs/dominios/*/auditorias/CONSOLIDADO.md) tracked=1 ;;
esac
[ "$tracked" -eq 0 ] && exit 0

# Override explicito do Roldao
if printf '%s' "$content" | grep -qiE '#[[:space:]]*ritual-gate:[[:space:]]*skip[[:space:]]*--[[:space:]]*APROVADO POR ROLDAO'; then
    exit 0
fi

# Marca de FECHAMENTO/avanco de fase
closure_re='FASE FECHADA|FOUNDATION[^.]*FECHAD|F-[A-Z][^.]*FECHAD|MARCO[^.]*FECHAD|STORY[^.]*FECHAD|FECHAD[AO] (VIA|PELO|PELA)|VEREDITO:?[*[:space:]]*PASS|PODE (AVANÇAR|AVANCAR)|PODE PASSAR PARA A (PRÓXIMA|PROXIMA) FASE'
if ! printf '%s' "$content" | grep -qiE "$closure_re"; then
    exit 0
fi

# Marca de ACHADO EM ABERTO no mesmo doc:
#  - CRITICO/ALTO/MEDIO seguido (ate ~40 chars, sem cruzar coluna |)
#    de "em aberto / pendente / nao resolvido / FAIL / REPROVAD"
#  - linha de veto FAIL: / | FAIL | / VEREDITO FAIL
#  - REPROVADO (parecer de subagente)
open_re='(CRÍTICO|CRITICO|ALTO|MÉDIO|MEDIO)[^|]{0,40}(EM ABERTO| ABERTO|ABERTO\)|PENDENTE|NÃO RESOLVID|NAO RESOLVID|FAIL|REPROVAD)'
fail_re='(^|[^A-Z])FAIL[[:space:]]*[:0-9]|\|[[:space:]]*FAIL[[:space:]]*\||VEREDITO:?[*[:space:]]*FAIL|REPROVADO'

if printf '%s' "$content" | grep -qiE "$open_re" || printf '%s' "$content" | grep -qiE "$fail_re"; then
    echo "ritual-gate-check (INV-RITUAL-001): documento marca fase/Marco/Story como FECHADA/PASS/avanca, mas ainda tem achado CRITICO/ALTO/MEDIO em aberto (ou FAIL/REPROVADO) em $file_path" >&2
    echo "Resolva o achado na causa-raiz ANTES de fechar a fase. MEDIO bloqueia igual a CRITICO/ALTO — nao existe 'MEDIO aceitavel/cosmetico/diferido'." >&2
    echo "Override (so o Roldao decide): adicione no doc a linha '# ritual-gate: skip -- APROVADO POR ROLDAO: <razao>'." >&2
    exit 2
fi

exit 0
