#!/usr/bin/env bash
# =============================================================
# provisioning-checkpoint-check.sh
# Enforce INV-INT-007 — tenant so consegue logar/operar apos
# `onboarding.estado = PRONTO` (state machine 7 etapas atomica).
#
# Evento: PreToolUse(Write|Edit) em codigo Python (views Django/DRF
# que aceitam request autenticado).
#
# Como funciona:
#   - Le tool_input.content / new_string + file_path
#   - Detecta endpoint novo que recebe `request` autenticado
#   - Bloqueia (exit 2) se nao consultar onboarding.estado nem
#     consumir BillingSaas.AssinaturaPronta antes de servir
#
# Allowlist (nao bloqueia):
#   - Endpoints publicos (sem auth)
#   - Endpoints de auth/login/signup (rodam ANTES do tenant existir)
#   - Endpoints do proprio modulo onboarding (precisam funcionar pre-PRONTO)
#   - Webhooks de gateway (callback async)
#   - Testes, migrations, management commands
#
# Limitacao atual (pre-codigo):
#   - Modulo onboarding ainda nao existe (Wave A).
#   - Hook fica em modo WARNING ate F-A entregar onboarding —
#     se file_path em codigo de aplicacao mas hook nao consegue
#     verificar checkpoint, retorna 0 (sem bloqueio) + mensagem stderr.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"app/os/views.py","content":"@api_view([\"POST\"])\ndef criar_os(request):\n    user = request.user\n    return Response()"}}' | bash .claude/hooks/provisioning-checkpoint-check.sh
#   echo $?    # esperar 2 (sem checkpoint)
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

case "$file_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# Pula testes, migrations, management, admin, fixtures
case "$file_path" in
    */tests/*|*/test_*|*_test.py|*/migrations/*|*/management/*|*/admin.py|*/fixtures/*) exit 0 ;;
esac

# Pula modulos onde checkpoint nao se aplica
case "$file_path" in
    */onboarding/*|*/auth/*|*/signup/*|*/login/*|*/webhooks/*|*/health*|*/metrics*) exit 0 ;;
esac

# So checa se o codigo tem endpoint autenticado
if ! printf '%s' "$content" | grep -qE '@api_view|class[[:space:]]+\w+(View|ViewSet|APIView)|def[[:space:]]+(get|post|put|patch|delete|create|update)[[:space:]]*\('; then
    exit 0
fi

# Allowlist explicita
if printf '%s' "$content" | grep -qE 'permission_classes[[:space:]]*=[[:space:]]*\[[[:space:]]*AllowAny'; then
    exit 0
fi
if printf '%s' "$content" | grep -qE '#[[:space:]]*provisioning-checkpoint:[[:space:]]*skip'; then
    exit 0  # bypass intencional, justificado em comentario adjacente
fi

# Regra: codigo deve consultar onboarding.estado OU consumir AssinaturaPronta
if printf '%s' "$content" | grep -qE '(onboarding\.estado|AssinaturaPronta|ProvisioningCompletado|tenant_pronto|require_tenant_pronto)'; then
    exit 0  # tem checkpoint
fi

# Modo WARNING (pre-codigo): nao bloqueia ate modulo onboarding existir,
# mas avisa que essa rota vai precisar do checkpoint na F-A.
echo "provisioning-checkpoint-check (INV-INT-007): endpoint autenticado em $file_path nao consulta onboarding.estado nem BillingSaas.AssinaturaPronta." >&2
echo "Quando modulo onboarding for entregue (Wave A), este hook vai BLOQUEAR. Por enquanto, apenas warning." >&2

# Exit 0 mesmo: warning sem bloqueio enquanto pre-codigo.
# Quando Wave A entregar onboarding, mudar este exit para 2.
exit 0
