#!/usr/bin/env bash
# =============================================================
# lic-emergencial-a3-check.sh — M9 Fatia 4 / INV-033 + INV-LIC-BLOQUEIO-001 (T-LIC-062)
#
# Modo emergencial (liberacao excepcional com documento bloqueante vencido) NAO e
# bypass silencioso: exige `assinatura_a3_id` presente + justificativa >=100 chars +
# janela <=7d + evento WORM. As pre-condicoes vivem em `validar_modo_emergencial`
# (D-LIC-6/7); montar o `EventoEmergencial` sem passar por elas reintroduz o bypass.
#
# Heuristica (so .py de src/, fora de teste/migration/doc/transicoes):
#   BLOCK quando o conteudo CRIA a entidade `EventoEmergencial(` SEM chamar
#   `validar_modo_emergencial(` no mesmo conteudo.
#
# Auto-allow (exit 0):
#   - tests/** ; migrations/** ; docs/** ; nao-.py
#   - src/domain/metrologia/licencas_acreditacoes/transicoes.py (lar de validar_modo_emergencial)
#   - src/domain/metrologia/licencas_acreditacoes/entities.py (definicao da dataclass)
#   - conteudo com `validar_modo_emergencial(` (gate presente)
#
# Override: '# lic-emergencial-a3: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/x/uc.py","content":"evento = EventoEmergencial(\n  id=uuid4(),\n)"}}' | bash .claude/hooks/lic-emergencial-a3-check.sh; echo $?  # 2
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

case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py|*conftest.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    docs/*|*/docs/*) exit 0 ;;
    *src/domain/metrologia/licencas_acreditacoes/transicoes.py) exit 0 ;;
    *src/domain/metrologia/licencas_acreditacoes/entities.py) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*lic-emergencial-a3:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Gate presente no mesmo conteudo isenta.
if printf '%s' "$content" | grep -qE 'validar_modo_emergencial[[:space:]]*\('; then
    exit 0
fi

if printf '%s' "$content" | grep -qE 'EventoEmergencial[[:space:]]*\('; then
    echo "lic-emergencial-a3 (INV-033): EventoEmergencial montado sem validar_modo_emergencial em $file_path" >&2
    echo "Modo emergencial nao e bypass silencioso — exige a3_id + justificativa >=100ch + janela <=7d." >&2
    echo "Passe pelas pre-condicoes de dominio antes de criar o evento:" >&2
    echo "  from src.domain.metrologia.licencas_acreditacoes.transicoes import validar_modo_emergencial" >&2
    echo "  validar_modo_emergencial(tipo_documento=..., justificativa=..., assinatura_a3_id=..., janela_dias=...)" >&2
    echo "Override: '# lic-emergencial-a3: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
