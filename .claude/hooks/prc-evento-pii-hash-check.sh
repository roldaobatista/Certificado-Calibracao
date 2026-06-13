#!/usr/bin/env bash
# =============================================================
# prc-evento-pii-hash-check.sh — precificacao P7 / INV-PRC-JUSTIFICATIVA-HASH + ADV-PRC-03 (T-PRC-052)
#
# Bloqueia payload de evento `Precificacao.*` carregando TEXTO LIVRE CRU.
# A trilha WORM e ineliminavel — texto livre (justificativa/motivo/aviso_texto)
# e PII acidental que nao se consegue apagar depois (conflito LGPD x retencao).
# A frente cravou (spec §6 / ADV-PRC-03):
#   - `justificativa` nunca cru em evento — chave `justificativa_hash`
#   - `motivo` nunca cru — chave `motivo_hash`
#   - `aviso_texto` nunca cru — chave `aviso_texto_hash`
#   - `criado_por`/`solicitante_id`/`decisor_id` viram `*_id_hash`
#   - valores numericos de Parametros/Faixas NAO entram (segredo comercial)
#     so diff de NOMES de campos
#
# Heuristica (so em arquivos da frente que publicam evento):
#   Atua em '*/precificacao/*.py'. Para cada chamada
#   `_publicar_evento_precificacao(` ... ate `causation_id`, BLOCK se o bloco
#   do payload contiver chave proibida CRUA:
#   "justificativa":, "motivo":, "aviso_texto":, "criado_por":,
#   "solicitante_id":, "decisor_id":
#   (as versoes *_hash sao as permitidas).
#
# Override: '# prc-evento-pii-hash: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/precificacao/views.py","content":"_publicar_evento_precificacao(\n    acao=\"Precificacao.AprovacaoDecidida\",\n    payload={\"justificativa\": d[\"justificativa\"]},\n    causation_id=c)"}}' | bash .claude/hooks/prc-evento-pii-hash-check.sh; echo $?  # 2
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
    */precificacao/*.py) ;;
    *) exit 0 ;;
esac

if ! printf '%s' "$content" | grep -q '_publicar_evento_precificacao'; then
    exit 0
fi

if printf '%s' "$content" | grep -qE '#[[:space:]]*prc-evento-pii-hash:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Para cada bloco _publicar_evento_precificacao(...) ate causation_id, procura
# chave proibida crua no payload.
achado=$(printf '%s' "$content" | perl -0777 -ne '
    while (/_publicar_evento_precificacao\((.*?)causation_id/sg) {
        my $blk = $1;
        if ($blk =~ /"(justificativa|motivo|aviso_texto|criado_por|solicitante_id|decisor_id)"\s*:/) {
            print "$1";
            last;
        }
    }
' 2>/dev/null)

if [ -n "$achado" ]; then
    echo "prc-evento-pii-hash (ADV-PRC-03 / INV-PRC-JUSTIFICATIVA-HASH): payload de evento Precificacao.* com texto livre/PII cru: chave \"$achado\" em $file_path" >&2
    echo "" >&2
    echo "Evento WORM e ineliminavel — texto livre e PII acidental (LGPD x retencao)." >&2
    echo "Use as chaves hashificadas: justificativa_hash / motivo_hash / aviso_texto_hash" >&2
    echo "(ADR-0029, derivar_hash_texto_canonicalizado) e *_id_hash (HMAC-tenant)." >&2
    echo "Valores numericos de Parametros/Faixas NAO entram — so diff de NOMES." >&2
    echo "Override: '# prc-evento-pii-hash: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
