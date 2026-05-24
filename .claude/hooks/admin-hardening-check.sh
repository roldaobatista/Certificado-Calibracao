#!/usr/bin/env bash
# =============================================================
# admin-hardening-check.sh
# Foundation F-C1 P4 T-FC1-06 — INV-ADMIN-001
#
# Valida duas coisas:
#   1. config/urls.py raiz monta /admin/ SOMENTE quando AdminHardening-
#      Middleware esta registrado em MIDDLEWARE (settings/base.py).
#   2. config/settings/base.py (ou prod.py) NAO remove o middleware
#      AdminHardeningMiddleware se /admin/ esta exposto.
#
# Logica:
#   - Se o arquivo editado eh config/urls.py:
#       * detecta path("admin/", admin.site.urls) ou equivalente
#       * se monta /admin/, exige menção a AdminHardeningMiddleware em
#         outro arquivo (verifica config/settings/base.py)
#   - Se o arquivo eh config/settings/base.py ou prod.py:
#       * detecta MIDDLEWARE = [...]
#       * se contem AdminHardeningMiddleware -> OK
#       * se NAO contem MAS urls.py monta /admin/ -> BLOQUEIA
#
# Allow via:
#   - Comentario inline: # admin-hardening: skip -- <razao ≥10 chars>
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

# Aplica somente a config/urls.py e config/settings/{base,prod}.py
case "$file_path_norm" in
    */config/urls.py|config/urls.py) tipo="urls" ;;
    */config/settings/base.py|config/settings/base.py) tipo="settings" ;;
    */config/settings/prod.py|config/settings/prod.py) tipo="settings" ;;
    *) exit 0 ;;
esac

# Skip arquivo inteiro
if printf '%s' "$content" | grep -qE 'admin-hardening:\s*skip\s*--\s*.{10,}'; then
    exit 0
fi

# Detecta se /admin/ esta sendo MONTADO no urls.py
admin_montado_no_arquivo=0
if printf '%s' "$content" | grep -qE 'path\(\s*["\047]admin/?["\047]\s*,\s*admin\.site\.urls\s*\)'; then
    admin_montado_no_arquivo=1
fi

# Detecta se AdminHardeningMiddleware aparece no MIDDLEWARE
tem_middleware=0
if printf '%s' "$content" | grep -qE 'AdminHardeningMiddleware'; then
    tem_middleware=1
fi

violations=()

if [ "$tipo" = "urls" ] && [ "$admin_montado_no_arquivo" = "1" ]; then
    # urls.py monta /admin/ — exige que settings tenha o middleware
    # (verifica config/settings/base.py em disco)
    settings_path="config/settings/base.py"
    if [ ! -f "$settings_path" ]; then
        # tenta caminhos absolutos comuns
        if [ -f "${CLAUDE_PROJECT_DIR:-.}/config/settings/base.py" ]; then
            settings_path="${CLAUDE_PROJECT_DIR}/config/settings/base.py"
        fi
    fi
    if [ -f "$settings_path" ]; then
        if ! grep -qE 'AdminHardeningMiddleware' "$settings_path"; then
            violations+=("$file_path monta /admin/ MAS $settings_path nao registra AdminHardeningMiddleware (INV-ADMIN-001)")
        fi
    else
        violations+=("nao encontrei config/settings/base.py para verificar AdminHardeningMiddleware")
    fi
fi

if [ "$tipo" = "settings" ] && [ "$tem_middleware" = "0" ]; then
    # settings sem o middleware — verifica se urls monta /admin/
    urls_path="config/urls.py"
    if [ ! -f "$urls_path" ] && [ -f "${CLAUDE_PROJECT_DIR:-.}/config/urls.py" ]; then
        urls_path="${CLAUDE_PROJECT_DIR}/config/urls.py"
    fi
    if [ -f "$urls_path" ]; then
        if grep -qE 'path\(\s*["\047]admin/?["\047]\s*,\s*admin\.site\.urls\s*\)' "$urls_path"; then
            # Tem /admin/ mas settings nao tem middleware
            # Allow se settings tem TODOS os MIDDLEWARE comentados (placeholder)
            if printf '%s' "$content" | grep -qE '^\s*MIDDLEWARE\s*=\s*\['; then
                violations+=("MIDDLEWARE em $file_path NAO contem AdminHardeningMiddleware mas $urls_path monta /admin/")
            fi
        fi
    fi
fi

if [ ${#violations[@]} -gt 0 ]; then
    echo "admin-hardening-check: /admin/ exposto sem AdminHardeningMiddleware em $file_path" >&2
    echo "" >&2
    for v in "${violations[@]}"; do
        echo "  - $v" >&2
    done
    echo "" >&2
    echo "INV-ADMIN-001 (F-C1 spec): /admin/* exige MFA + IP allowlist + rate-limit + session-rebind." >&2
    echo "Adicionar 'src.infrastructure.authz.middleware_admin.AdminHardeningMiddleware'" >&2
    echo "em MIDDLEWARE depois de MfaRequiredMiddleware." >&2
    echo "" >&2
    echo "Allow via: # admin-hardening: skip -- <razao ≥10 chars>" >&2
    exit 2
fi

exit 0
