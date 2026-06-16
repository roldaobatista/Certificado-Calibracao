#!/usr/bin/env bash
# =============================================================
# policy-tenant-vs-cliente.sh — contas-receber Fatia 3d / INV-FIN-INAD-001 (T-CR-047)
#
# Inadimplencia do CLIENTE do tenant != inadimplencia do TENANT no SaaS Afere.
#   - Bloqueio de CLIENTE por atraso vive em `clientes` (`ClienteBloqueio`, motivo
#     `automatico_inadimplencia_90d`), alimentado por contas-receber (titulo vencido).
#   - Suspensao do TENANT no SaaS vive em `billing-saas` (ADR-0015) via `BillingSaas`/
#     `TenantSuspenso`. (NB: `StatusLifecycle.SUSPENSO` do modulo `tenant` e o gate de
#     "tenant ativo" do auto-faturamento — ADR-0035 — e e LEGITIMO; nao casa aqui.)
# **Nada cruza:** cliente bloqueado nao mexe no plano do tenant; tenant suspenso no SaaS
# nao bloqueia clientes do tenant. Cruzar gera bloqueio injusto -> churn (D-CR / INV-INT-009/010).
#
# Heuristica (so .py em path *clientes* ou *contas_receber*, fora de teste/migration/doc):
#   BLOCK quando o conteudo importa ou referencia o billing do SaaS
#   (`billing_saas`/`billing-saas`/`BillingSaas`/`TenantSuspenso`) — acoplamento proibido
#   entre o operacional (cliente) e o plano-de-controle (tenant no SaaS).
#
# Auto-allow (exit 0):
#   - tests/** ; migrations/** ; docs/** ; nao-.py
#   - path nao-*clientes* e nao-*contas_receber*
#
# Override: '# policy-tenant-vs-cliente: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/clientes/bloqueio.py","content":"from src.infrastructure.billing_saas.models import TenantSuspenso"}}' | bash .claude/hooks/policy-tenant-vs-cliente.sh; echo $?  # 2
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

# So a fronteira operacional cliente/contas-receber.
case "$norm_path" in
    *clientes*|*contas_receber*) ;;
    *) exit 0 ;;
esac

case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py|*conftest.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    docs/*|*/docs/*) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*policy-tenant-vs-cliente:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Referencia ao billing do SaaS (plano-de-controle) no codigo operacional do cliente.
# Linhas de comentario (^#) sao ignoradas; o restante (codigo + docstring) e barrado.
if printf '%s' "$content" | grep -vE '^[[:space:]]*#' \
    | grep -qE '(billing[_-]saas|BillingSaas|TenantSuspenso)'; then
    echo "policy-tenant-vs-cliente (INV-FIN-INAD-001): operacional de cliente acoplado ao billing do SaaS em $file_path" >&2
    echo "Inadimplencia do CLIENTE do tenant != suspensao do TENANT no SaaS Afere — nada cruza." >&2
    echo "Bloqueio de cliente vive em clientes/ (ClienteBloqueio); suspensao do tenant em billing-saas (ADR-0015)." >&2
    echo "Para gate de 'tenant ativo' do auto-faturamento use StatusLifecycle (modulo tenant), nao billing-saas." >&2
    echo "Override: '# policy-tenant-vs-cliente: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
