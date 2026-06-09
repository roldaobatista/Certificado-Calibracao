#!/usr/bin/env bash
# =============================================================
# fiscal-perfil-server-side-check.sh — fiscal/NFS-e Fatia 3 / INV-FIS-001 (T-FIS-041)
#
# Defesa anti-fraude L6: na emissao de NFS-e o perfil regulatorio NUNCA pode vir do
# payload da request (ADR-0067) — senao um tenant D forja uma NFS-e de calibracao RBC
# (fraude documental viavel, cl. 8.1.3). O perfil efetivo so sai server-side
# (`obter_perfil_tenant_corrente`/`tenant_perfil_e`) e a trava roda no use case
# (`documento_metrologico_obrigatorio_por_perfil` — ADR-0073).
#
# Heuristica (so .py em path *fiscal*, fora de teste/migration/doc/dominio):
#   BLOCK quando o conteudo atribui `perfil` a partir de fonte do cliente
#   (request.data/POST/JSON/body, validated_data, payload, initial_data) SEM o gate
#   server-side no mesmo conteudo.
#
# Auto-allow (exit 0):
#   - tests/** ; migrations/** ; docs/** ; nao-.py ; path nao-*fiscal*
#   - src/domain/fiscal/perfil_documento.py (lar da trava pura)
#   - conteudo com `obter_perfil_tenant_corrente`/`tenant_perfil_e(`/`documento_metrologico_obrigatorio_por_perfil`
#
# Override: '# fiscal-perfil-server-side: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/fiscal/views.py","content":"perfil = request.data[\"perfil\"]"}}' | bash .claude/hooks/fiscal-perfil-server-side-check.sh; echo $?  # 2
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
    *.py) ;;
    *) exit 0 ;;
esac

# So arquivos da frente fiscal.
case "$norm_path" in
    *fiscal*) ;;
    *) exit 0 ;;
esac

case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py|*conftest.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    docs/*|*/docs/*) exit 0 ;;
    *src/domain/fiscal/perfil_documento.py) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*fiscal-perfil-server-side:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Line-oriented (FIS-SEG-02): bloqueia se QUALQUER linha de CODIGO (nao comentario)
# atribui `perfil` a partir do payload — mesmo que um token server-side legitimo
# apareca noutra linha (a linha maliciosa nao pode ser encoberta). Comentarios/
# docstrings de linha (iniciados por #) sao ignorados.
if printf '%s' "$content" | grep -vE '^[[:space:]]*#' \
    | grep -qE 'perfil["'"'"']?[[:space:]]*[:=][^=].*((request\.(data|POST|JSON|json|body))|validated_data|payload|initial_data)'; then
    echo "fiscal-perfil-server-side (INV-FIS-001): perfil de emissao NFS-e vindo do payload em $file_path" >&2
    echo "O perfil regulatorio NUNCA vem da request (ADR-0067) — tenant D forjaria NFS-e RBC." >&2
    echo "Derive server-side e valide no use case:" >&2
    echo "  perfil = obter_perfil_tenant_corrente()  # ContextVar do middleware" >&2
    echo "  documento_metrologico_obrigatorio_por_perfil(perfil=perfil, ...)  # ADR-0073" >&2
    echo "Override: '# fiscal-perfil-server-side: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
