#!/usr/bin/env bash
# =============================================================
# agenda-jornada-perfil-agnostica-check.sh — agenda Fatia 3d / INV-AG-JORNADA-UMC-001 (T-AGE-047)
#
# Garante que `validar_jornada_umc` e a lógica de jornada NÃO são gateadas
# por perfil regulatório A/B/C/D (INV-AG-JORNADA-UMC-001 — perfil-AGNÓSTICA).
#
# Jornada de técnico de campo é ORDEM PÚBLICA trabalhista (Lei 13.103/2015
# + CLT 235-C + ADI 5322). Não depende de acreditação ISO 17025. Gateá-la
# por perfil A/B/C/D é mascaramento de passivo trabalhista (ADV-AGE-04).
#
# Heurística (só em arquivos da frente agenda, fora de teste/migration):
#   BLOCK quando QUALQUER linha de código (não comentário) chama ou
#   referencia `validar_jornada_umc` OU `validar_jornada` condicionada
#   por `perfil` (A/B/C/D ou obter_perfil / perfil_no_evento).
#   TAMBÉM bloqueia se `validar_jornada` está dentro de bloco `if.*perfil`.
#
# Auto-allow (exit 0):
#   - tests/** ; migrations/** ; docs/** ; não-.py
#   - path não *agenda*
#   - src/domain/operacao/agenda/jornada.py (domínio puro — implementa sem perfil)
#   - override: '# agenda-jornada-perfil-agnostica: skip -- <razão >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/application/operacao/agenda/criar_evento.py","content":"if perfil == \"A\":\n    validar_jornada_umc(tecnico, regime, janela, eventos, cap)"}}' | bash .claude/hooks/agenda-jornada-perfil-agnostica-check.sh; echo $?  # 2
#   echo '{"tool_input":{"file_path":"src/application/operacao/agenda/criar_evento.py","content":"resultado = validar_jornada_umc(tecnico, regime, janela, eventos, cap)"}}' | bash .claude/hooks/agenda-jornada-perfil-agnostica-check.sh; echo $?  # 0
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

# So arquivos da frente agenda
case "$norm_path" in
    *agenda*) ;;
    *) exit 0 ;;
esac

# Ignora
case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py|*conftest.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    docs/*|*/docs/*) exit 0 ;;
    # Domínio puro: implementa a função sem perfil (permitido)
    */domain/operacao/agenda/jornada.py) exit 0 ;;
esac

# Override global
if printf '%s' "$content" | grep -qE '#[[:space:]]*agenda-jornada-perfil-agnostica:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Verifica se validar_jornada_umc aparece condicionada por perfil.
# Padrão: if (perfil|obter_perfil|perfil_no_evento) ... validar_jornada
# OU: validar_jornada chamada dentro de bloco gateado por perfil.
# Heurística conservadora: se o mesmo arquivo tem validar_jornada_umc
# E tem condicional de perfil (if.*perfil.*[ABCD]) na mesma vizinhança.

has_jornada=$(printf '%s' "$content" | grep -cvE '^[[:space:]]*#' | grep -c 'validar_jornada_umc\|validar_jornada' 2>/dev/null || true)
# Recheck sem pipe problemático
if ! printf '%s' "$content" | grep -vE '^[[:space:]]*#' | grep -qE 'validar_jornada_umc|validar_jornada'; then
    exit 0
fi

# Arquivo tem validar_jornada — verifica se há gate por perfil nas linhas de código
if printf '%s' "$content" | grep -vE '^[[:space:]]*#' \
    | grep -qE '(if|elif|and|or)[^#]*(perfil|obter_perfil_tenant|perfil_no_evento)[^#]*(==|in|!=)[^#]*(\"A\"|\"B\"|\"C\"|\"D\"|[ABCD])'; then
    # Pode ser gate inocente em outro contexto — verificar se a jornada está no mesmo bloco
    # Heurística: linhas de perfil próximas a validar_jornada (arquivo inteiro com ambas)
    echo "agenda-jornada-perfil-agnostica (INV-AG-JORNADA-UMC-001): $file_path parece gatear validar_jornada_umc por perfil A/B/C/D." >&2
    echo "" >&2
    echo "Jornada de técnico de campo é ordem pública trabalhista (Lei 13.103/2015 + CLT 235-C)." >&2
    echo "NÃO depende do perfil metrológico A/B/C/D — é perfil-AGNÓSTICA (ADV-AGE-04 / INV-AG-JORNADA-UMC-001)." >&2
    echo "validar_jornada_umc() deve rodar para qualquer perfil quando is_tecnico_campo=True e aloca_em_umc=True." >&2
    echo "Override: '# agenda-jornada-perfil-agnostica: skip -- <razão com >=10 chars>'" >&2
    exit 2
fi

exit 0
