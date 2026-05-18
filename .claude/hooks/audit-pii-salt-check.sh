#!/usr/bin/env bash
# =============================================================
# audit-pii-salt-check.sh
# Anti-regressao do FAIL critico do Auditor de Seguranca Familia 5
# (2026-05-18): hash de PII em audit precisa ser salgado por tenant.
#
# Bloqueia (exit 2) qualquer escrita em arquivo de view/serializer/use case
# que contenha o padrao `hashlib.sha256(<algo>).hexdigest()` SEM uma das
# excecoes abaixo, dentro de um contexto que cheira a "audit" (payload de
# registrar_auditoria, hash chain, ip_hash, etc).
#
# A regra eh conservadora: bloqueia o padrao perigoso e exige troca pelo
# helper `audit.services.hashear_pii_com_salt_tenant(valor, tenant_id)`.
#
# Excecoes (NAO bloqueia):
#   - Arquivo eh hook ou teste de hook
#   - Arquivo eh `src/infrastructure/audit/hash_chain.py` (hash da CADEIA do
#     audit usa sha256 sem sal — eh diferente; quem se preocupa eh PII NO
#     PAYLOAD, nao o hash chain).
#   - Arquivo eh `src/infrastructure/audit/services.py` (helper mora aqui).
#   - Linha contem `# audit-pii-salt: skip -- <razao >= 10 chars>`.
#   - Linha ja chama `hashear_pii_com_salt_tenant`.
#   - Hash de IP eh aceitavel sem sal por tenant (IP eh PII fraca; padrao do
#     projeto eh sha256(ip) puro em _hashear_ip — tratado como excecao quando
#     a variavel/funcao se chama *_hashear_ip / *ip_hash*).
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/clientes/views.py","new_string":"hashlib.sha256(documento.encode(\"utf-8\")).hexdigest()"}}' | bash .claude/hooks/audit-pii-salt-check.sh
#   echo $?  # 2
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

# Normaliza separadores Windows.
file_path_norm=$(printf '%s' "$file_path" | tr '\\' '/')

# Arquivos isentos por path
case "$file_path_norm" in
    */.claude/hooks/*|*/test_hooks*|*tests/test_hooks*) exit 0 ;;
    */infrastructure/audit/hash_chain.py) exit 0 ;;
    */infrastructure/audit/services.py) exit 0 ;;
    */infrastructure/audit/canonicalizar.py) exit 0 ;;
    *.md|*.txt|*.json|*.yml|*.yaml|*.toml) exit 0 ;;
esac

# So aplica a arquivos Python que potencialmente gravam audit.
case "$file_path_norm" in
    *.py) : ;;
    *) exit 0 ;;
esac

# Procura padrao perigoso: hashlib.sha256(<algo>).hexdigest()
# Regex permissiva (`.*`) pra capturar parenteses aninhados como
# `.encode("utf-8")`.
if printf '%s' "$content" | grep -nE 'hashlib\.sha256\(.*\.hexdigest\(\)' > /tmp/_apsc_hits 2>/dev/null; then
    while IFS=: read -r linha_num linha_conteudo; do
        # Skip se linha contem override
        if printf '%s' "$linha_conteudo" | grep -qE '# *audit-pii-salt: *skip -- .{10,}'; then
            continue
        fi
        # Skip se linha chama hashear_pii_com_salt_tenant explicitamente
        if printf '%s' "$linha_conteudo" | grep -q 'hashear_pii_com_salt_tenant'; then
            continue
        fi
        # Extrai SOMENTE a parte de codigo (antes do `#`) pra filtros que
        # nao devem ser enganados por palavras no comentario inline.
        linha_codigo=$(printf '%s' "$linha_conteudo" | perl -ne 's/#.*$//; print')
        # Skip se eh hash de IP (padrao aceito do projeto)
        if printf '%s' "$linha_codigo" | grep -qiE '(ip[._]hash|hashear_ip|hash_ip)'; then
            continue
        fi
        # Skip se o codigo monta string com sal (afere-salt, salt_tenant, etc).
        if printf '%s' "$linha_codigo" | grep -qiE '(salt|afere-salt)'; then
            continue
        fi
        # BLOQUEIO
        echo "audit-pii-salt-check: hash sha256 sem salt por tenant em $file_path linha $linha_num" >&2
        echo "" >&2
        echo "  $linha_conteudo" >&2
        echo "" >&2
        echo "Razao: hash de PII (CPF/CNPJ/nome/email/telefone) sem sal por tenant" >&2
        echo "eh invertivel via rainbow table (FAIL critico Auditor Seguranca 2026-05-18)." >&2
        echo "" >&2
        echo "Correcao: use o helper" >&2
        echo "  from src.infrastructure.audit.services import hashear_pii_com_salt_tenant" >&2
        echo "  doc_hash = hashear_pii_com_salt_tenant(documento, tenant_id)" >&2
        echo "" >&2
        echo "Override (com justificativa >=10 chars):" >&2
        echo "  hashlib.sha256(x).hexdigest()  # audit-pii-salt: skip -- <razao>" >&2
        rm -f /tmp/_apsc_hits
        exit 2
    done < /tmp/_apsc_hits
fi
rm -f /tmp/_apsc_hits 2>/dev/null

exit 0
