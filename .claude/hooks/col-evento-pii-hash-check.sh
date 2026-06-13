#!/usr/bin/env bash
# =============================================================
# col-evento-pii-hash-check.sh — colaboradores P7 / INV-COL-PII-LOG (T-COL-052)
#
# Bloqueia payload de evento `colaborador.*` carregando CPF/nome/email/telefone
# em CLARO. A trilha WORM e ineliminavel — PII acidental viola LGPD art. 18
# (direito ao esquecimento impossível) e ADV-COL-06 (pseudonimizacao por evento).
#
# A frente cravou (spec §6 / D-COL-8):
#   - cpf  nunca cru em evento — chave `cpf_hash`
#   - nome nunca cru — chave `nome_hash`
#   - email nunca cru — chave `email_hash`
#   - telefone nunca cru — chave `telefone_hash`
#   - motivo_desligamento nunca cru — chave `motivo_hash`
#   - ator_id_hash (hash de UUID de usuario — D-COL-8)
#   Valores de identidade PII sao os proibidos; UUID colaborador_id em claro
#   e permitido (pseudonimo estavel, nao reidentifica diretamente).
#
# Heuristica (so em arquivos da frente colaboradores):
#   Atua em '*/colaboradores/*.py'. Para cada chamada
#   `_publicar_evento_colaborador(` ... ate `causation_id`, BLOCK se o bloco
#   do payload contiver chave PII CRUA:
#   "cpf":, "nome":, "email":, "telefone":, "motivo_desligamento":
#   (as versoes *_hash sao as permitidas).
#
# Excecoes:
#   - Arquivo de testes (tests/): sem restricao.
#   - Linha com override: '# col-evento-pii-hash: skip -- <razao >=10 chars>'.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/colaboradores/views.py","content":"_publicar_evento_colaborador(\n    acao=\"colaborador.cadastrado\",\n    payload={\"cpf\": colab.cpf},\n    causation_id=c)"}}' | bash .claude/hooks/col-evento-pii-hash-check.sh; echo $?  # 2
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

# Atua so em arquivos da frente colaboradores (exceto testes).
case "$norm_path" in
    */tests/*) exit 0 ;;
    */colaboradores/*.py) ;;
    *) exit 0 ;;
esac

# Se nao publica evento colaborador, nao ha risco.
if ! printf '%s' "$content" | grep -q '_publicar_evento_colaborador'; then
    exit 0
fi

# Override global no arquivo
if printf '%s' "$content" | grep -qE '#[[:space:]]*col-evento-pii-hash:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Para cada bloco _publicar_evento_colaborador(...) ate causation_id, procura
# chave PII crua no payload.
achado=$(printf '%s' "$content" | perl -0777 -ne '
    while (/_publicar_evento_colaborador\((.*?)causation_id/sg) {
        my $blk = $1;
        if ($blk =~ /"(cpf|nome|email|telefone|motivo_desligamento)"\s*:/) {
            print "$1";
            last;
        }
    }
' 2>/dev/null)

if [ -n "$achado" ]; then
    echo "col-evento-pii-hash (ADV-COL-06 / INV-COL-PII-LOG): payload de evento colaborador.* com PII crua: chave \"$achado\" em $file_path" >&2
    echo "" >&2
    echo "Evento WORM e ineliminavel — PII acidental (LGPD x retencao — art. 18 impossivel)." >&2
    echo "Use as chaves hashificadas: cpf_hash / nome_hash / email_hash / telefone_hash / motivo_hash" >&2
    echo "(ADR-0029, derivar_hash_texto_canonicalizado via _hmac_tenant) e ator_id_hash (HMAC-tenant)." >&2
    echo "UUIDs colaborador_id/papel_id em claro sao permitidos (pseudonimo estavel)." >&2
    echo "Override: '# col-evento-pii-hash: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
