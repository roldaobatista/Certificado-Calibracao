#!/usr/bin/env bash
# =============================================================
# payload-tipo-acreditacao-obsoleto-check.sh — T-SAN-PERFIL-026 / AC-006-4
#
# Bloqueia (exit 2) codigo NOVO que use o campo `tipo_acreditacao` no payload
# da request (request.data, request.POST, request.JSON, etc) — substituido
# por consulta canonica a Tenant.perfil_regulatorio via ContextVar (INV-TENANT-
# PERFIL-001).
#
# Compat-shim: o predicate `cmc_cobre` em `src/infrastructure/calibracao/
# predicates_calibracao.py` AINDA aceita o campo (com WARN log
# `payload_tipo_acreditacao_obsoleto`) ate fim de Wave A modulo `certificados`.
# Mas codigo NOVO nao pode introduzir o uso.
#
# AUTO-ALLOW:
# - Migrations existentes (codigo legado).
# - Codigo dentro de `src/infrastructure/calibracao/predicates_calibracao.py`
#   (proprio compat-shim — caminho oficial conhecido).
# - Testes (mantem cobertura do compat-shim ate ser removido).
# - Documentos `.md` (referencia historica e bem-vinda).
#
# Override: linha contendo '# payload-tipo-acreditacao: skip -- <razao com >=10 chars>'
#
# Origem: SAN-PERFIL-TENANT — ADR-0067 aceito 2026-05-27.
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

# So .py (codigo executavel; .sql nao costuma ter request payload).
case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# Pula testes — mantem cobertura do compat-shim.
case "$norm_path" in
    */tests/*|*/test_*|*_test.py|*conftest.py) exit 0 ;;
esac

# Pula migrations — codigo legado.
case "$norm_path" in
    */migrations/*) exit 0 ;;
esac

# AUTO-ALLOW: caminho oficial conhecido (predicate que tem o compat-shim).
case "$norm_path" in
    *src/infrastructure/calibracao/predicates_calibracao.py) exit 0 ;;
esac

# Override explicito com justificativa
if printf '%s' "$content" | grep -qE '#[[:space:]]*payload-tipo-acreditacao:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Padroes que tentam ler tipo_acreditacao do payload (handlers REST, views, services).
violacao=""

# 1. resource["tipo_acreditacao"] — predicate-style.
if printf '%s' "$content" | grep -qE 'resource(\.get|\[)\s*\(?["'"'"']tipo_acreditacao["'"'"']'; then
    violacao='resource["tipo_acreditacao"] / resource.get("tipo_acreditacao") — predicate antigo style'
# 2. request.data.get("tipo_acreditacao") — DRF serializer.
elif printf '%s' "$content" | grep -qE 'request\.(data|POST|JSON|json|body)(\.get|\[)\s*\(?["'"'"']tipo_acreditacao["'"'"']'; then
    violacao='request.data["tipo_acreditacao"] / request.data.get(...) — view handler lendo do payload'
# 3. serializer.validated_data["tipo_acreditacao"].
elif printf '%s' "$content" | grep -qE 'validated_data(\.get|\[)\s*\(?["'"'"']tipo_acreditacao["'"'"']'; then
    violacao='validated_data["tipo_acreditacao"] — serializer DRF'
# 4. payload["tipo_acreditacao"] em dicionario explicito.
elif printf '%s' "$content" | grep -qE 'payload(\.get|\[)\s*\(?["'"'"']tipo_acreditacao["'"'"']'; then
    violacao='payload["tipo_acreditacao"] — dict de evento/comando'
# 5. dados["tipo_acreditacao"] — outro nome comum de dict de input.
elif printf '%s' "$content" | grep -qE 'dados(\.get|\[)\s*\(?["'"'"']tipo_acreditacao["'"'"']'; then
    violacao='dados["tipo_acreditacao"] — dict de comando/input'
# 6. argumento de funcao chamada `tipo_acreditacao` em criacao de calibracao.
#    Padroes legitimos (entidade.tipo_acreditacao como atributo do Calibracao)
#    nao caem aqui porque nao tem ()/[] de leitura de dict.
fi

if [ -n "$violacao" ]; then
    echo "payload-tipo-acreditacao-obsoleto: codigo novo lendo tipo_acreditacao do payload em $file_path" >&2
    echo "Padrao detectado: $violacao" >&2
    echo "" >&2
    echo "AC-SAN-PERFIL-002-2 + INV-TENANT-PERFIL-001 substituiram self-attestation" >&2
    echo "por payload por consulta canonica a Tenant.perfil_regulatorio via ContextVar." >&2
    echo "" >&2
    echo "Use:" >&2
    echo "  from src.infrastructure.authz.perfil_tenant_helper import obter_perfil_tenant_corrente" >&2
    echo "  perfil = obter_perfil_tenant_corrente()  # fail-closed; retorna 'A'/'B'/'C'/'D' ou ''" >&2
    echo "OU:" >&2
    echo "  from src.infrastructure.authz.perfil_tenant_helper import tenant_perfil_e" >&2
    echo "  allowed, reason = tenant_perfil_e({'A'})" >&2
    echo "" >&2
    echo "Override (raro, exige aprovacao Roldao):" >&2
    echo "  '# payload-tipo-acreditacao: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
