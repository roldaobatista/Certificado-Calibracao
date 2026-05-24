#!/usr/bin/env bash
# =============================================================
# prod-settings-check.sh
# Foundation F-C1 P4 T-FC1-01 — INV-PROD-SET-001
#
# Valida config/settings/prod.py contra ~14 settings exigidos pelo
# hardening de producao. Hook bloqueia commit se qualquer setting
# critico estiver ausente/incorreto.
#
# Aplica a: config/settings/prod.py
#
# Allow PONTUAL (por valor, nao por arquivo) via:
#   # prod-settings: skip-<NOME_SETTING> -- <razao ≥10 chars>
#
# Exemplo:
#   # prod-settings: skip-CSP -- inventario assets Wave A; entra F-C2
#
# Skip de arquivo inteiro via:
#   # prod-settings: skip-all -- <razao ≥10 chars>
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

# Aplica somente a config/settings/prod.py
case "$file_path_norm" in
    */config/settings/prod.py|config/settings/prod.py) ;;
    *) exit 0 ;;
esac

# Skip arquivo inteiro
if printf '%s' "$content" | grep -qE 'prod-settings:\s*skip-all\s*--\s*.{10,}'; then
    exit 0
fi

# Helper para verificar se um skip especifico foi declarado
has_skip() {
    local nome="$1"
    printf '%s' "$content" | grep -qE "prod-settings:\s*skip-${nome}\s*--\s*.{10,}"
}

violations=()

# 1. DEBUG = False (rejeita DEBUG=True ou ausencia explicita)
if has_skip "DEBUG"; then :
elif printf '%s' "$content" | grep -qE '^\s*DEBUG\s*=\s*True'; then
    violations+=("DEBUG=True em prod (deve ser DEBUG=False)")
elif ! printf '%s' "$content" | grep -qE '^\s*DEBUG\s*=\s*False'; then
    violations+=("DEBUG=False ausente (declaracao explicita exigida)")
fi

# 2. ALLOWED_HOSTS validado — exige menção + nao pode ser ["*"]
if has_skip "ALLOWED_HOSTS"; then :
elif printf '%s' "$content" | grep -qE 'ALLOWED_HOSTS\s*=\s*\[\s*["\047]\*["\047]\s*\]'; then
    violations+=("ALLOWED_HOSTS=['*'] em prod (proibido — exige lista fechada)")
elif ! printf '%s' "$content" | grep -qE '(ALLOWED_HOSTS|DJANGO_ALLOWED_HOSTS)'; then
    violations+=("ALLOWED_HOSTS/DJANGO_ALLOWED_HOSTS nao declarado")
fi

# 3. SESSION_COOKIE_SECURE = True
if has_skip "SESSION_COOKIE_SECURE"; then :
elif ! printf '%s' "$content" | grep -qE '^\s*SESSION_COOKIE_SECURE\s*=\s*True'; then
    violations+=("SESSION_COOKIE_SECURE=True ausente")
fi

# 4. CSRF_COOKIE_SECURE = True
if has_skip "CSRF_COOKIE_SECURE"; then :
elif ! printf '%s' "$content" | grep -qE '^\s*CSRF_COOKIE_SECURE\s*=\s*True'; then
    violations+=("CSRF_COOKIE_SECURE=True ausente")
fi

# 5. SECURE_HSTS_SECONDS >= 31_536_000 (1 ano)
if has_skip "SECURE_HSTS_SECONDS"; then :
elif ! printf '%s' "$content" | grep -qE '^\s*SECURE_HSTS_SECONDS\s*=\s*[0-9_]+'; then
    violations+=("SECURE_HSTS_SECONDS ausente")
else
    valor=$(printf '%s' "$content" | grep -oE '^\s*SECURE_HSTS_SECONDS\s*=\s*[0-9_]+' | head -1 | grep -oE '[0-9_]+$' | tr -d '_')
    if [ "${valor:-0}" -lt 31536000 ]; then
        violations+=("SECURE_HSTS_SECONDS=$valor < 31536000 (1 ano minimo)")
    fi
fi

# 6. SECURE_HSTS_INCLUDE_SUBDOMAINS = True
if has_skip "SECURE_HSTS_INCLUDE_SUBDOMAINS"; then :
elif ! printf '%s' "$content" | grep -qE '^\s*SECURE_HSTS_INCLUDE_SUBDOMAINS\s*=\s*True'; then
    violations+=("SECURE_HSTS_INCLUDE_SUBDOMAINS=True ausente (R-1/TL-01/SEG-06)")
fi

# 7. SECURE_HSTS_PRELOAD = True
if has_skip "SECURE_HSTS_PRELOAD"; then :
elif ! printf '%s' "$content" | grep -qE '^\s*SECURE_HSTS_PRELOAD\s*=\s*True'; then
    violations+=("SECURE_HSTS_PRELOAD=True ausente (R-1/SEG-06)")
fi

# 8. SECURE_SSL_REDIRECT = True
if has_skip "SECURE_SSL_REDIRECT"; then :
elif ! printf '%s' "$content" | grep -qE '^\s*SECURE_SSL_REDIRECT\s*=\s*True'; then
    violations+=("SECURE_SSL_REDIRECT=True ausente")
fi

# 9. SECURE_PROXY_SSL_HEADER declarado (Hostinger atras de proxy)
if has_skip "SECURE_PROXY_SSL_HEADER"; then :
elif ! printf '%s' "$content" | grep -qE '^\s*SECURE_PROXY_SSL_HEADER\s*=\s*\('; then
    violations+=("SECURE_PROXY_SSL_HEADER ausente (R-1/TL-01 — sem isso HSTS+SSL_REDIRECT entram em loop atras de proxy)")
fi

# 10. CSRF_TRUSTED_ORIGINS declarado e nao contem "*"
if has_skip "CSRF_TRUSTED_ORIGINS"; then :
elif printf '%s' "$content" | grep -qE 'CSRF_TRUSTED_ORIGINS\s*=\s*\[\s*["\047]\*["\047]\s*\]'; then
    violations+=("CSRF_TRUSTED_ORIGINS=['*'] proibido (R-1/TL-01)")
elif ! printf '%s' "$content" | grep -qE 'CSRF_TRUSTED_ORIGINS'; then
    violations+=("CSRF_TRUSTED_ORIGINS nao declarado (R-1/TL-01)")
fi

# 11. DATA_UPLOAD_MAX_MEMORY_SIZE <= 10MB (anti-DoS form bomb)
if has_skip "DATA_UPLOAD_MAX_MEMORY_SIZE"; then :
elif ! printf '%s' "$content" | grep -qE '^\s*DATA_UPLOAD_MAX_MEMORY_SIZE\s*='; then
    violations+=("DATA_UPLOAD_MAX_MEMORY_SIZE ausente (R-1/TL-01 — anti-DoS form bomb)")
else
    valor=$(printf '%s' "$content" | grep -oE '^\s*DATA_UPLOAD_MAX_MEMORY_SIZE\s*=\s*[0-9_]+' | head -1 | grep -oE '[0-9_]+$' | tr -d '_')
    if [ "${valor:-0}" -gt 10485760 ]; then
        violations+=("DATA_UPLOAD_MAX_MEMORY_SIZE=$valor > 10485760 (10MB max) — risco DoS form bomb")
    fi
fi

# 12. DATA_UPLOAD_MAX_NUMBER_FIELDS <= 1000
if has_skip "DATA_UPLOAD_MAX_NUMBER_FIELDS"; then :
elif ! printf '%s' "$content" | grep -qE '^\s*DATA_UPLOAD_MAX_NUMBER_FIELDS\s*='; then
    violations+=("DATA_UPLOAD_MAX_NUMBER_FIELDS ausente (R-1/TL-01 — anti-DoS form bomb)")
else
    valor=$(printf '%s' "$content" | grep -oE '^\s*DATA_UPLOAD_MAX_NUMBER_FIELDS\s*=\s*[0-9_]+' | head -1 | grep -oE '[0-9_]+$' | tr -d '_')
    if [ "${valor:-0}" -gt 1000 ]; then
        violations+=("DATA_UPLOAD_MAX_NUMBER_FIELDS=$valor > 1000 — risco DoS form bomb")
    fi
fi

# 13. X_FRAME_OPTIONS = "DENY"
if has_skip "X_FRAME_OPTIONS"; then :
elif ! printf '%s' "$content" | grep -qE '^\s*X_FRAME_OPTIONS\s*=\s*["\047]DENY["\047]'; then
    violations+=("X_FRAME_OPTIONS='DENY' ausente")
fi

# 14. SECURE_CONTENT_TYPE_NOSNIFF = True
if has_skip "SECURE_CONTENT_TYPE_NOSNIFF"; then :
elif ! printf '%s' "$content" | grep -qE '^\s*SECURE_CONTENT_TYPE_NOSNIFF\s*=\s*True'; then
    violations+=("SECURE_CONTENT_TYPE_NOSNIFF=True ausente")
fi

# 15. SECURE_REFERRER_POLICY in ("same-origin", "strict-origin-when-cross-origin")
if has_skip "SECURE_REFERRER_POLICY"; then :
elif ! printf '%s' "$content" | grep -qE 'SECURE_REFERRER_POLICY\s*=\s*["\047](same-origin|strict-origin-when-cross-origin)["\047]'; then
    violations+=("SECURE_REFERRER_POLICY ausente ou valor invalido (esperado 'same-origin' ou 'strict-origin-when-cross-origin')")
fi

# 16. CSP declarado via django-csp ou middleware proprio
# (heuristica: procura CONTENT_SECURITY_POLICY ou csp.middleware.CSPMiddleware)
if has_skip "CSP"; then :
elif ! printf '%s' "$content" | grep -qE '(CONTENT_SECURITY_POLICY|CSPMiddleware|csp_middleware)'; then
    violations+=("CSP nao declarado (django-csp ou middleware proprio)")
fi

if [ ${#violations[@]} -gt 0 ]; then
    echo "prod-settings-check: hardening de producao incompleto em $file_path" >&2
    echo "" >&2
    for v in "${violations[@]}"; do
        echo "  - $v" >&2
    done
    echo "" >&2
    echo "Spec: docs/faseamento/F-C1/spec.md AC-FC1-001-1 (INV-PROD-SET-001)" >&2
    echo "Allow PONTUAL: # prod-settings: skip-<NOME> -- <razao ≥10 chars>" >&2
    echo "Allow ARQUIVO: # prod-settings: skip-all -- <razao ≥10 chars>" >&2
    exit 2
fi

exit 0
