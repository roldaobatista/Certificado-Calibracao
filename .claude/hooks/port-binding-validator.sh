#!/usr/bin/env bash
# =============================================================
# port-binding-validator.sh — Marco 2 T-EQP-072 / ADR-0007
#
# Defende a fronteira inter-modulo para modulos com PORTA explicita
# (`query_service.py`, `capa_query_service.py`, `predicates.py`).
# Consumidores externos NAO PODEM importar models/admin desses
# modulos diretamente — devem passar pela porta.
#
# Em Marco 2 dois modulos qualificam:
#
# 1. `src/infrastructure/certificados/`
#    Porta: query_service.tem_emitido / equipamentos_com_cert_vigente
#    Bloqueio: imports de `src.infrastructure.certificados.models`
#    fora do proprio modulo + tests + migrations.
#
# 2. `src/infrastructure/qualidade/`
#    Porta: capa_query_service.capa_aberta_para_*
#    Bloqueio: imports de `src.infrastructure.qualidade.models`
#    (stub Marco 2 — modulo nao tem models ainda; preventivo
#    Wave A quando RegistroCAPA nascer).
#
# Auto-allow (exit 0):
#   - tests/**                       (testam tudo)
#   - **/migrations/**               (data migrations cross-modulo)
#   - src/infrastructure/<X>/**      (modulo importa de SI mesmo)
#   - config/**                      (settings/urls compoe)
#   - **/__init__.py                 (re-exports)
#
# Override em arquivo fora da allowlist:
#   # port-binding: skip -- <razao com >=10 chars>
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

# So Python.
case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# Override com justificativa
if printf '%s' "$content" | grep -qE '#[[:space:]]*port-binding:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# AUTO-ALLOW pelo caminho.
case "$norm_path" in
    tests/*|*/tests/*|*/test_*.py|*_test.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    config/*|*/config/*) exit 0 ;;
    */__init__.py) exit 0 ;;
    src/infrastructure/certificados/*|*/src/infrastructure/certificados/*) exit 0 ;;
    src/infrastructure/qualidade/*|*/src/infrastructure/qualidade/*) exit 0 ;;
esac

# Modulos com porta protegida — lista FECHADA. Marco 2: 2 modulos;
# Wave A pode adicionar (manter ordenado).
MODULOS_PROTEGIDOS=("certificados" "qualidade")

# Patterns proibidos por modulo:
#   from src.infrastructure.<X>.models import ...
#   from src.infrastructure.<X>.admin import ...
#   from src.infrastructure.<X>.serializers import ...

for modulo in "${MODULOS_PROTEGIDOS[@]}"; do
    if printf '%s' "$content" \
        | grep -qE "^[[:space:]]*from[[:space:]]+src\.infrastructure\.${modulo}\.(models|admin|serializers|views)[[:space:]]+import"; then
        echo "port-binding-validator (ADR-0007 / T-EQP-072): import direto de modulo PROTEGIDO" >&2
        echo "Arquivo: $file_path" >&2
        echo "Modulo alvo: '$modulo' tem PORTA explicita — use-a." >&2
        echo "  - certificados → src.infrastructure.certificados.query_service" >&2
        echo "  - qualidade    → src.infrastructure.qualidade.capa_query_service" >&2
        echo "" >&2
        echo "Ou justifique via:  # port-binding: skip -- <razao com >=10 chars>" >&2
        exit 2
    fi
done

exit 0
