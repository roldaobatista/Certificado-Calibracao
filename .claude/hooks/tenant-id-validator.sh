#!/usr/bin/env bash
# =============================================================
# tenant-id-validator.sh
# Enforce INV-TENANT-001 + INV-TENANT-002.
# Evento: PreToolUse(Write|Edit) em codigo Python (Django/DRF) e migrations
#
# Como funciona:
#   - Le tool_input.content (Write) ou new_string (Edit) + file_path
#   - Se for migration: bloqueia CreateModel/CREATE TABLE sem coluna tenant_id
#   - Se for codigo Python com .objects.all() ou query SQL sem WHERE tenant_id em tabela de dominio cliente: bloqueia
#   - Exit 2 = bloqueia
#
# Limitacao atual (pre-codigo):
#   - Lista de "tabelas de dominio cliente" sera mantida em
#     .claude/hooks/tenant-tables.allowlist (a criar quando codigo existir).
#     Por enquanto, qualquer create_model/CREATE TABLE sem tenant_id em
#     migrations/ vira FAIL — generoso pra evitar miss.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"app/migrations/0001_initial.py","content":"class Migration:\n    operations = [CreateModel(name=\"Pedido\", fields=[(\"id\", AutoField())])]"}}' | bash .claude/hooks/tenant-id-validator.sh
#   echo $?    # esperar 2 (sem tenant_id)
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

# Allowlist de tabelas que NAO precisam tenant_id (cross-tenant/sistema)
# Ajustar quando codigo aparecer.
crosstenant_tables="tenant tenants user_global feature_flag billing_plan migration django_migrations django_content_type auth_permission auth_group"

# Caso 1: migrations Django/Alembic
case "$file_path" in
    */migrations/*.py|*alembic*/versions/*.py)
        # Detecta CreateModel ou CREATE TABLE
        if printf '%s' "$content" | grep -qiE '(CreateModel|CREATE[[:space:]]+TABLE|op\.create_table)'; then
            # Tem que mencionar tenant_id
            if ! printf '%s' "$content" | grep -qE '(tenant_id|"tenant"|tenant[[:space:]]*=)'; then
                # Verifica se e tabela cross-tenant
                table_name=$(printf '%s' "$content" | grep -oE 'name="[a-zA-Z_]+"' | head -1 | sed -E 's/name="([^"]+)"/\1/')
                if [ -n "$table_name" ]; then
                    for ct in $crosstenant_tables; do
                        if [ "$ct" = "$table_name" ]; then
                            exit 0  # permitido
                        fi
                    done
                fi
                echo "tenant-id-validator (INV-TENANT-002): migration cria tabela sem tenant_id em $file_path" >&2
                echo "Tabelas cross-tenant em allowlist: $crosstenant_tables" >&2
                echo "Se nova tabela e cross-tenant, adicione a allowlist no proprio hook." >&2
                exit 2
            fi
        fi
        ;;
esac

# Caso 2: codigo Python com .objects.all() sem filtro
# Permite TenantQuerySet.objects.all() (manager customizado injeta tenant_id)
# Bloqueia Model.objects.all() em codigo de aplicacao
case "$file_path" in
    *.py)
        # Pula testes e management commands cross-tenant
        case "$file_path" in
            */tests/*|*/test_*|*_test.py|*/management/*|*/migrations/*) exit 0 ;;
        esac
        if printf '%s' "$content" | grep -qE '\.objects\.all\(\)'; then
            # So bloqueia se nao for em conjunto com filtro tenant
            if ! printf '%s' "$content" | grep -qE '(filter\([^)]*tenant|in_tenant_context|TenantManager|with_tenant)'; then
                echo "tenant-id-validator (INV-TENANT-001): .objects.all() sem filtro tenant em $file_path" >&2
                echo "Use TenantManager ou .filter(tenant_id=...)" >&2
                exit 2
            fi
        fi
        ;;
esac

exit 0
