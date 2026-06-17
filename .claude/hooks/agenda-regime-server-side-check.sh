#!/usr/bin/env bash
# =============================================================
# agenda-regime-server-side-check.sh — agenda Fatia 3d / INV-AG-REGIME-001 (T-AGE-047)
#
# Garante que:
#   1. `regime` e `perfil` NUNCA vêm do payload da request em código da agenda
#      (serializers/views — server-side obrigatório).
#   2. IA NUNCA grava override de `RegimeJornadaColaborador` automaticamente
#      (só humano RH/gerente via enquadrar_regime — R6 / D-AGE-15).
#
# Se o regime viesse do payload, um cliente forjaria seu enquadramento trabalhista
# (ex: motorista_profissional → nao_aplica para burlar jornada). Se a IA
# gravasse override automaticamente, enquadraria o colaborador sem autorização
# humana (passivo trabalhista + LGPD).
#
# Heurística (só .py em path *agenda*, fora de teste/migration/domínio):
#   BLOCK quando QUALQUER linha de código (não comentário):
#     (a) atribui `regime` de fonte do cliente (request.data/POST/JSON/
#         body/validated_data/payload/initial_data) — INV-AG-REGIME-001 §1
#     (b) chama `salvar_regime_override` ou cria `RegimeJornadaColaborador`
#         fora do use case `enquadrar_regime.py` — INV-AG-REGIME-001 §2
#
# Auto-allow (exit 0):
#   - tests/** ; migrations/** ; docs/**; não-.py
#   - path não *agenda*
#   - src/domain/operacao/agenda/** (domínio recebe regime por parâmetro)
#   - src/application/operacao/agenda/enquadrar_regime.py (use case legítimo)
#   - override: '# agenda-regime-server-side: skip -- <razão >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/agenda/serializers.py","content":"regime = request.data[\"regime\"]"}}' | bash .claude/hooks/agenda-regime-server-side-check.sh; echo $?  # 2
#   echo '{"tool_input":{"file_path":"src/infrastructure/agenda/views.py","content":"regime = resolver_regime_server_side(colab_id)"}}' | bash .claude/hooks/agenda-regime-server-side-check.sh; echo $?  # 0
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
    # Domínio puro: recebe regime como parâmetro (permitido)
    */domain/operacao/agenda/*) exit 0 ;;
    # Use case legítimo de enquadramento humano (único autorizado a gravar override)
    */application/operacao/agenda/enquadrar_regime.py) exit 0 ;;
esac

# Override global
if printf '%s' "$content" | grep -qE '#[[:space:]]*agenda-regime-server-side:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

BLOCKED=0

# (a) regime atribuído de fonte do cliente
if printf '%s' "$content" | grep -vE '^[[:space:]]*#' \
    | grep -qE 'regime["'"'"']?[[:space:]]*[:=][^=].*((request\.(data|POST|JSON|json|body))|validated_data|payload|initial_data)'; then
    echo "agenda-regime-server-side (INV-AG-REGIME-001 §1): $file_path — 'regime' vem do payload da request." >&2
    echo "O regime de jornada NUNCA pode vir do cliente (R6 / D-AGE-15 / ADR-0067)." >&2
    echo "Derive server-side via ColaboradorAgendaAdapter.regime_jornada(na_data=slot.date())." >&2
    BLOCKED=1
fi

# (b) IA grava override fora do use case enquadrar_regime
# Detecta criação direta de RegimeJornadaColaborador fora do contexto autorizado
if printf '%s' "$content" | grep -vE '^[[:space:]]*#' \
    | grep -qE 'RegimeJornadaColaborador\.objects\.(create|get_or_create|update_or_create)'; then
    echo "agenda-regime-server-side (INV-AG-REGIME-001 §2): $file_path — RegimeJornadaColaborador.objects.create fora de enquadrar_regime.py." >&2
    echo "IA NUNCA grava override de regime automaticamente (R6 / D-AGE-15)." >&2
    echo "Só humano (RH/gerente) pode chamar enquadrar_regime via endpoint dedicado." >&2
    BLOCKED=1
fi

[ "$BLOCKED" -eq 1 ] && echo "Override: '# agenda-regime-server-side: skip -- <razão com >=10 chars>'" >&2 && exit 2

exit 0
