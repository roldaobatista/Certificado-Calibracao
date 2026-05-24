#!/usr/bin/env bash
# =============================================================
# mass-assignment-check.sh
# Onda 2 plano-v2 (2026-05-23) — auditor QUAL apontou itens 121-122
# da checklist (mass assignment / usuario podendo alterar role,
# isAdmin, creditos, verified via PATCH genérico).
#
# Bloqueia:
# 1. ModelSerializer com `fields = "__all__"` em tabela sensivel
# 2. ModelSerializer cuja Meta.model esta na denylist mas que NAO
#    declara `read_only_fields` (heuristica leve)
#
# Aplica a: src/**/*serializer*.py, src/**/serializers.py
#
# Allow via:
#   - Comentario inline na classe Meta: # mass-assignment: skip -- <razao ≥10 chars>
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

# Aplica somente a serializers.py em src/
case "$file_path_norm" in
    src/*serializer*.py|*/src/*serializer*.py) ;;
    *) exit 0 ;;
esac

# Pula tests/ e migrations/
case "$file_path_norm" in
    */tests/*|*/migrations/*) exit 0 ;;
esac

# Skip arquivo inteiro
if printf '%s' "$content" | grep -qE 'mass-assignment:\s*skip\s*--\s*.{10,}'; then
    exit 0
fi

violations=()

# Regra 1: bloqueia `fields = "__all__"` ou `fields = '__all__'` em ModelSerializer
if printf '%s' "$content" | grep -qE 'fields\s*=\s*["\047]__all__["\047]'; then
    # Confere se ha ModelSerializer no arquivo (heuristica leve)
    if printf '%s' "$content" | grep -qE 'ModelSerializer'; then
        violations+=("ModelSerializer com fields = \"__all__\" e proibido (mass assignment). Use lista explicita de campos.")
    fi
fi

# Regra 2: ModelSerializer cuja Meta.model toca tabela sensivel SEM read_only_fields
# Lista de modelos sensiveis (subconjunto da denylist documental)
modelos_sensiveis=("Usuario" "OrdemServico" "AtividadeDaOS" "Equipamento" "Certificado" "ContasReceber" "Pagamento" "Tenant" "RegistroTecnico" "AceiteAtividade" "EquipamentoRecebimento")

for modelo in "${modelos_sensiveis[@]}"; do
    # Busca padrao "model = Usuario" ou similar (com qualifier)
    if printf '%s' "$content" | grep -qE "model\s*=\s*(${modelo}|[a-zA-Z_]+\.${modelo})\b"; then
        # Tem ModelSerializer pra modelo sensivel — exige read_only_fields
        # Heuristica: precisa existir `read_only_fields` no arquivo
        if ! printf '%s' "$content" | grep -qE 'read_only_fields\s*='; then
            violations+=("ModelSerializer para '$modelo' sem read_only_fields declarado. Ver docs/seguranca/campos-protegidos-update.md para lista canonica.")
        fi
    fi
done

# Regra 3: tentativa de aceitar 'tenant_id' explicito em writable field (heuristica)
if printf '%s' "$content" | grep -qE 'tenant_id'; then
    # Se tenant_id aparece e nao esta em read_only_fields, alerta
    if printf '%s' "$content" | grep -qE 'fields\s*=\s*\[' && \
       printf '%s' "$content" | grep -qE 'fields\s*=.*tenant_id'; then
        # tenant_id esta na lista fields — verifica se tambem esta em read_only_fields
        if ! printf '%s' "$content" | grep -qE 'read_only_fields\s*=\s*\[[^]]*tenant_id'; then
            violations+=("Campo 'tenant_id' aparece em 'fields' mas NAO em 'read_only_fields'. INV-TENANT-001: tenant_id nunca pode vir do payload do cliente.")
        fi
    fi
fi

if [ ${#violations[@]} -gt 0 ]; then
    echo "mass-assignment-check: serializer com risco de mass assignment em $file_path" >&2
    echo "" >&2
    for v in "${violations[@]}"; do
        echo "  - $v" >&2
    done
    echo "" >&2
    echo "Denylist canonica: docs/seguranca/campos-protegidos-update.md" >&2
    echo "Allow via: # mass-assignment: skip -- <razao com ≥10 chars>" >&2
    exit 2
fi

exit 0
