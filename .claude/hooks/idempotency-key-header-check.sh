#!/usr/bin/env bash
# =============================================================
# idempotency-key-header-check.sh
# Onda 2 plano-v2 (2026-05-23) — IDEMP-001a (sub-regra de IDEMP-001).
# Servidor REJEITA com 400 quando header Idempotency-Key esta ausente
# em POST critico (financeiro, fiscal, certificado, OS, pagamento).
#
# Aplica a: src/**/views.py em paths criticos (financeiro/, fiscal/,
#           certificados/, ordens_servico/, contas_receber/, pagamentos/)
#
# Logica de deteccao:
# 1. Detecta classe ViewSet/APIView com metodo create/post/perform_create
# 2. Verifica se ha leitura de request.headers.get("Idempotency-Key")
#    OU chamada a algum helper que faca isso (decorator @idempotente,
#    mixin IdempotencyMixin, etc.)
# 3. Se nao ha leitura nem helper, bloqueia
#
# Allow via:
#   - Comentario inline na view: # idempotency-key: skip -- <razao ≥10 chars>
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

# Aplica somente a views.py em paths criticos
case "$file_path_norm" in
    */src/infrastructure/financeiro/*/views.py|src/infrastructure/financeiro/*/views.py) ;;
    */src/infrastructure/fiscal/*/views.py|src/infrastructure/fiscal/*/views.py) ;;
    */src/infrastructure/certificados/*/views.py|src/infrastructure/certificados/*/views.py) ;;
    */src/infrastructure/ordens_servico/*/views.py|src/infrastructure/ordens_servico/*/views.py) ;;
    */src/infrastructure/ordens_servico/views.py|src/infrastructure/ordens_servico/views.py) ;;
    */src/infrastructure/contas_receber/*/views.py|src/infrastructure/contas_receber/*/views.py) ;;
    */src/infrastructure/pagamentos/*/views.py|src/infrastructure/pagamentos/*/views.py) ;;
    */src/infrastructure/calibracao/*/views.py|src/infrastructure/calibracao/*/views.py) ;;
    */src/infrastructure/calibracao/views.py|src/infrastructure/calibracao/views.py) ;;
    *) exit 0 ;;
esac

# Pula tests/ e migrations/
case "$file_path_norm" in
    */tests/*|*/migrations/*) exit 0 ;;
esac

# Skip arquivo inteiro
if printf '%s' "$content" | grep -qE 'idempotency-key:\s*skip\s*--\s*.{10,}'; then
    exit 0
fi

# Detecta se ha view POST/create:
#   - def create / def post / def perform_create
#   - @api_view([POST])
#   - @action(... methods=["post"] ...) — padrao DRF ViewSet usado em M3 OS
#     (GATE-IDEMP-HOOK-DETECT-ACTION fechado em P5 conserto 2026-05-24)
tem_post=0
if printf '%s' "$content" | grep -qE '(def\s+(create|post|perform_create)\s*\(|@api_view\([^)]*["\047]POST["\047])'; then
    tem_post=1
fi
if printf '%s' "$content" | grep -qE '@action\([^)]*methods\s*=\s*\[[^]]*["\047]post["\047]' ; then
    tem_post=1
fi

if [ "$tem_post" = "0" ]; then
    exit 0
fi

# Detecta se ha leitura de Idempotency-Key OU uso de helper canonico
tem_protecao=0

# Leitura direta do header
if printf '%s' "$content" | grep -qE '(request\.headers\.get\(\s*["\047]Idempotency-Key["\047]|request\.META\.get\(\s*["\047]HTTP_IDEMPOTENCY_KEY["\047])'; then
    tem_protecao=1
fi

# Helper/decorator canonico
if printf '%s' "$content" | grep -qE '(@idempotente|@requires_idempotency_key|IdempotencyMixin|with_idempotency_key|services_idempotencia)'; then
    tem_protecao=1
fi

if [ "$tem_protecao" = "0" ]; then
    echo "idempotency-key-header-check: view POST em path critico SEM leitura de Idempotency-Key em $file_path" >&2
    echo "" >&2
    echo "IDEMP-001a (sub-regra Onda 2 plano-v2): servidor REJEITA com 400 quando header ausente em POST critico." >&2
    echo "Esperado um dos seguintes:" >&2
    echo "  - request.headers.get(\"Idempotency-Key\")" >&2
    echo "  - request.META.get(\"HTTP_IDEMPOTENCY_KEY\")" >&2
    echo "  - Decorator @idempotente ou @requires_idempotency_key" >&2
    echo "  - Mixin IdempotencyMixin" >&2
    echo "  - Uso de src.infrastructure.idempotencia.services_idempotencia" >&2
    echo "" >&2
    echo "Allow via: # idempotency-key: skip -- <razao com ≥10 chars>" >&2
    exit 2
fi

exit 0
