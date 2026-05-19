#!/usr/bin/env bash
# =============================================================
# authz-check.sh
# Enforce INV-AUTHZ-001 — toda decisao "usuario pode fazer X?"
# passa pela porta AuthorizationProvider.can(). Proibido decidir
# autorizacao em decorator espalhado, em view ad-hoc, em queryset
# ou em signal.
#
# Evento: PreToolUse(Write|Edit) em codigo Python (views Django/DRF).
#
# Como funciona:
#   - Le tool_input.content / new_string + file_path
#   - Detecta endpoint novo: @api_view, def get/post/put/patch/delete
#     em ViewSet, def has_permission
#   - Bloqueia (exit 2) se nao houver chamada de AuthorizationProvider.can()
#     no corpo do metodo
#
# Allowlist (nao bloqueia):
#   - Views publicas declaradas: @permission_classes([AllowAny])
#   - Health check / metrics / status (lista hardcoded)
#   - Testes, management commands, migrations
#
# Limitacao atual (pre-codigo):
#   - AuthorizationProvider ainda nao existe (ADR-0012 propos, F-B implementa).
#   - Hook ja vigilante para quando 1a view surgir.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"app/views.py","content":"@api_view([\"POST\"])\ndef criar_os(request):\n    return Response({\"ok\": True})"}}' | bash .claude/hooks/authz-check.sh
#   echo $?    # esperar 2 (sem can())
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

# Normaliza separadores Windows (backslash → forward) para case patterns funcionarem
norm_path="${file_path//\\//}"

case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# Pula testes, migrations, management commands, admin, models, apps Django
# (esses arquivos podem ter metodos com nomes semelhantes a HTTP verbs —
# Auditoria.delete() bloqueia DELETE em codigo; nao e endpoint REST)
case "$norm_path" in
    */tests/*|*/test_*|*_test.py|*/migrations/*|*/management/*|*/admin.py|*/models.py|*/apps.py|*/fixtures/*) exit 0 ;;
esac

# Allowlist de paths publicos / sistema
case "$norm_path" in
    */health*|*/metrics*|*/status*|*/webhooks/*) exit 0 ;;
esac

# Detecta endpoint novo
endpoint_detectado=0
if printf '%s' "$content" | grep -qE '@api_view|@action[[:space:]]*\(|class[[:space:]]+\w+(View|ViewSet|APIView)|def[[:space:]]+(get|post|put|patch|delete|create|update|destroy|list|retrieve)[[:space:]]*\('; then
    endpoint_detectado=1
fi
if printf '%s' "$content" | grep -qE 'def[[:space:]]+has_permission[[:space:]]*\('; then
    endpoint_detectado=1
fi

[ "$endpoint_detectado" -eq 0 ] && exit 0

# Allowlist por declaracao explicita
if printf '%s' "$content" | grep -qE 'permission_classes[[:space:]]*=[[:space:]]*\[[[:space:]]*AllowAny'; then
    exit 0
fi
# FB-C2: valvula publica canonica do projeto. @public (funcao),
# PublicEndpoint (mixin CBV/DRF) ou _authz_public = True sao marcacao
# legitima de "view sem can()" — equivalente a AllowAny. is_public
# (fonte unica) resolve em runtime; aqui o hook so reconhece o texto.
if printf '%s' "$content" | grep -qE '(^|[^a-zA-Z_])@public([^a-zA-Z_]|$)|PublicEndpoint|_authz_public[[:space:]]*=[[:space:]]*True'; then
    exit 0
fi
if printf '%s' "$content" | grep -qE '#[[:space:]]*authz-check:[[:space:]]*skip'; then
    exit 0  # bypass intencional, justificado em comentario adjacente
fi

# Regra: tem que chamar AuthorizationProvider.can()
if ! printf '%s' "$content" | grep -qE '(AuthorizationProvider\.can|authz\.can|\.can\(["'\''])'; then
    echo "authz-check (INV-AUTHZ-001): endpoint novo sem chamada de AuthorizationProvider.can() em $file_path" >&2
    echo "Toda decisao 'esse usuario pode fazer essa acao?' passa pela porta. Proibido decidir em decorator espalhado, queryset ou signal." >&2
    echo "Se endpoint e publico: adicione permission_classes=[AllowAny] OU comentario '# authz-check: skip' com justificativa." >&2
    exit 2
fi

exit 0
