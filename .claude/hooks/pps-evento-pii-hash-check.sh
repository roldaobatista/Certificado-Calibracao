#!/usr/bin/env bash
# =============================================================
# pps-evento-pii-hash-check.sh — produtos-pecas-servicos P7 / INV-PPS-IMPORTACAO-STAGING + ADV-PPS-01/02 (T-PPS-051)
#
# Bloqueia payload de evento `Catalogo.*` carregando TEXTO LIVRE CRU. A trilha
# WORM e ineliminavel — texto livre (descricao/motivo) e PII acidental que nao
# se consegue apagar depois (conflito LGPD x retencao). A frente cravou:
#   - `descricao`/`motivo` entram HASHIFICADOS (ADR-0029 — chaves *_hash)
#   - `criado_por` vira `criado_por_id_hash` (HMAC-tenant, molde M5)
#   - nome de ITEM em claro usa a chave `nome_item` (nao-PII; a chave `nome`
#     da denylist do sanitizador e pra nome de GENTE)
#
# Heuristica (so em arquivos da frente que publicam evento):
#   Atua em '*/produtos_pecas_servicos/*.py'. Para cada chamada
#   `_publicar_evento_catalogo(` ... ate `causation_id`, BLOCK se o bloco do
#   payload contiver chave proibida CRUA: "descricao":, "motivo":, "nome":,
#   "criado_por": ou "nome_tabela": (P9 LGPD-M1 — nome de tabela e texto livre;
#   as versoes *_hash/nome_item sao as permitidas).
#
# Override: '# pps-evento-pii-hash: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/produtos_pecas_servicos/views.py","content":"_publicar_evento_catalogo(\n    acao=\"Catalogo.ItemCadastrado\",\n    payload={\"motivo\": d[\"motivo\"]},\n    causation_id=c)"}}' | bash .claude/hooks/pps-evento-pii-hash-check.sh; echo $?  # 2
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
    */produtos_pecas_servicos/*.py) ;;
    *) exit 0 ;;
esac

if ! printf '%s' "$content" | grep -q '_publicar_evento_catalogo'; then
    exit 0
fi

if printf '%s' "$content" | grep -qE '#[[:space:]]*pps-evento-pii-hash:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Para cada bloco _publicar_evento_catalogo(...) ate causation_id, procura
# chave proibida crua no payload (descricao/motivo/nome/criado_por sem _hash).
achado=$(printf '%s' "$content" | perl -0777 -ne '
    while (/_publicar_evento_catalogo\((.*?)causation_id/sg) {
        my $blk = $1;
        if ($blk =~ /"(descricao|motivo|nome|criado_por|nome_tabela)"\s*:/) {
            print "$1";
            last;
        }
    }
' 2>/dev/null)

if [ -n "$achado" ]; then
    echo "pps-evento-pii-hash (ADV-PPS-01/02): payload de evento Catalogo.* com texto livre/PII cru: chave \"$achado\" em $file_path" >&2
    echo "" >&2
    echo "Evento WORM e ineliminavel — texto livre e PII acidental (LGPD x retencao)." >&2
    echo "Use as chaves hashificadas: descricao_hash / motivo_hash (ADR-0029," >&2
    echo "derivar_hash_texto_canonicalizado) e criado_por_id_hash (HMAC-tenant)." >&2
    echo "Nome de ITEM em claro = chave nome_item (nao colide com a denylist)." >&2
    echo "Override: '# pps-evento-pii-hash: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
