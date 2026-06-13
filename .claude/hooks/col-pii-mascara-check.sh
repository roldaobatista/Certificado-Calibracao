#!/usr/bin/env bash
# =============================================================
# col-pii-mascara-check.sh — colaboradores P7 / INV-COL-PII-MASCARA (T-COL-052)
#
# Bloqueia serializers da frente `colaboradores` que exponham campos PII
# (cpf, email, telefone, ctps_info, cnh_info, foto_storage_key) sem passar
# pelo choke-point `filtrar_visao_pii`.
#
# INV-COL-PII-MASCARA exige que TODO serializer de SAIDA da frente que
# declare campos PII DEVE invocar `filtrar_visao_pii(` antes de retornar
# (D-COL-7 / TL-COL-05 / ADV-COL-04).
#
# Heuristica (so em serializers da frente colaboradores):
#   Atua em '*/colaboradores/*serializer*.py' e '*/colaboradores/serializers.py'.
#   BLOCK se o arquivo define funcao/classe de saida que lista campo PII
#   ("cpf", "email", "telefone", "ctps_info", "cnh_info", "foto_storage_key")
#   MAS nao contem a definicao de `filtrar_visao_pii` NEM sua invocacao.
#
# Excecoes legitimas (nao bloqueia):
#   - O proprio arquivo que DEFINE `filtrar_visao_pii` (e.g., o serializers.py
#     canônico que tem a funcao) — reconhecido por conter `def filtrar_visao_pii`.
#   - ElegivelDTOSerializer nao declara campos PII — nao ha risco.
#   - Serializers de ENTRADA (create/update): nome_exibicao, cpf de entrada sem saida.
#   - Override por linha: '# col-pii-mascara: skip -- <razao >=10 chars>'.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/colaboradores/outros_serializers.py","content":"class ColabSerializer:\n    cpf = serializers.CharField()\n    email = serializers.EmailField()\n\ndef serializar_saida(c):\n    return {\"cpf\": c.cpf, \"email\": c.email}"}}' | bash .claude/hooks/col-pii-mascara-check.sh; echo $?  # 2
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

# Atua so em serializers da frente colaboradores.
case "$norm_path" in
    */colaboradores/serializers.py) ;;
    */colaboradores/*serializer*.py) ;;
    *) exit 0 ;;
esac

# Se o arquivo DEFINE filtrar_visao_pii (arquivo canonical), e permitido —
# e ele proprio usa internamente. Nao bloquear.
if printf '%s' "$content" | grep -q 'def filtrar_visao_pii'; then
    exit 0
fi

# Se nao declara campo PII em saida, nao ha risco.
if ! printf '%s' "$content" | grep -qE '"cpf"|"email"|"telefone"|"ctps_info"|"cnh_info"|"foto_storage_key"'; then
    exit 0
fi

# Override global no arquivo
if printf '%s' "$content" | grep -qE '#[[:space:]]*col-pii-mascara:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Arquivo expoe campo PII mas NAO chama filtrar_visao_pii. BLOCK.
if ! printf '%s' "$content" | grep -qE 'filtrar_visao_pii[[:space:]]*\('; then
    echo "col-pii-mascara (INV-COL-PII-MASCARA): serializer em $file_path expoe" >&2
    echo "  campo PII (cpf/email/telefone/ctps_info/cnh_info/foto_storage_key)" >&2
    echo "  sem invocar filtrar_visao_pii()." >&2
    echo "" >&2
    echo "filtrar_visao_pii() e o choke-point UNICO de mascaramento PII da frente" >&2
    echo "colaboradores (D-COL-7 / INV-COL-PII-MASCARA / ADV-COL-04)." >&2
    echo "TODO serializer de saida que inclua campos PII DEVE passar por ele." >&2
    echo "Override (com justificativa >=10 chars):" >&2
    echo "  # col-pii-mascara: skip -- <razao com >=10 chars>" >&2
    exit 2
fi

exit 0
