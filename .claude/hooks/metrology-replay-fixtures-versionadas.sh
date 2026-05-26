#!/usr/bin/env bash
# =============================================================
# metrology-replay-fixtures-versionadas.sh — Marco 4 P9
# T-CAL-142 / T-CAL-058 / INV-CAL-VERSAO-001 / §16.5 motor / ADR-0025
#
# Defende as fixtures de replay metrologico em
# `tests/replay_metrologico/`. Estas fixtures sao o GROUND TRUTH que
# garante replay determinístico bit-a-bit em 25 anos (ISO 17025 cl. 7.11
# + cl. 8.4). Mudanca silenciosa em `outputs_esperados_*` quebra
# validacao do motor sem deixar trilha.
#
# Por que existir:
#   Fixture replay = contrato cripto entre versao do motor e resultado
#   esperado. Atualizar fixture sem aceite formal = manipular evidencia
#   regulatoria; auditor CGCRE em 2050 nao consegue saber se output
#   antigo foi "corrigido" pra esconder bug ou se motor foi atualizado
#   legitimamente.
#
# Bloqueia:
#   Toda mudanca em `tests/replay_metrologico/**` (qualquer .json, .py,
#   .yaml) que NAO contenha aceite formal no proprio arquivo:
#     - JSON: chave de topo "_aceite_motivo" com valor string >=20 chars.
#     - .py: comentario `# replay-fixture-aceite: <razao com >=20 chars>`.
#     - .yaml: linha de topo `# replay-fixture-aceite: <razao>=20 chars>`.
#
# Auto-allow:
#   - Criacao de pasta nova (commit que cria tests/replay_metrologico/
#     pela primeira vez, sinalizado por `# replay-fixture-init` no
#     conteudo).
#   - Arquivos `README.md` / `__init__.py` / `.gitignore` da pasta.
#
# Override por arquivo (caso emergencial):
#   # replay-fixture: skip -- <razao com >=20 chars>
#
# Como testar:
#   echo '{"tool_input":{"file_path":"tests/replay_metrologico/massa.json","content":"{\"resultado\": 1.23}"}}' | bash .claude/hooks/metrology-replay-fixtures-versionadas.sh
#   echo $?  # 2 (sem aceite)
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

# So `tests/replay_metrologico/...`
case "$norm_path" in
    tests/replay_metrologico/*|*/tests/replay_metrologico/*) ;;
    *) exit 0 ;;
esac

# Arquivos administrativos auto-allow
case "$norm_path" in
    */README.md|*README.md|*/__init__.py|*__init__.py|*/.gitignore|*.gitignore) exit 0 ;;
esac

# Init da pasta (1a vez) — auto-allow
if printf '%s' "$content" | grep -qE '#[[:space:]]*replay-fixture-init\b'; then
    exit 0
fi

# Override por arquivo
if printf '%s' "$content" | grep -qE '#[[:space:]]*replay-fixture:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{20,}'; then
    exit 0
fi

# =============================================================
# Aceite formal — depende da extensao
# =============================================================
ext="${norm_path##*.}"

case "$ext" in
    json)
        # Procura `"_aceite_motivo": "<>=20 chars>"`. JSON aspas duplas obrigatorio.
        if printf '%s' "$content" | grep -qE '"_aceite_motivo"[[:space:]]*:[[:space:]]*"[^"]{20,}"'; then
            exit 0
        fi
        echo "metrology-replay-fixtures-versionadas (SEM_ACEITE_JSON): $file_path sem chave '_aceite_motivo' com >=20 chars" >&2
        echo "Adicione no topo do JSON:" >&2
        echo '  "_aceite_motivo": "<razao tecnica + ticket/ADR de referencia>"' >&2
        echo "T-CAL-142 + INV-CAL-VERSAO-001 + ADR-0025 cl. 7.11." >&2
        echo "Override unico: # replay-fixture: skip -- <razao com >=20 chars>" >&2
        exit 2
        ;;
    py)
        if printf '%s' "$content" | grep -qE '^#[[:space:]]*replay-fixture-aceite:[[:space:]]*.{20,}'; then
            exit 0
        fi
        echo "metrology-replay-fixtures-versionadas (SEM_ACEITE_PY): $file_path sem comentario '# replay-fixture-aceite: <razao>=20 chars>'" >&2
        echo "Adicione no topo do arquivo:" >&2
        echo "  # replay-fixture-aceite: <razao tecnica + ticket/ADR>" >&2
        exit 2
        ;;
    yaml|yml)
        if printf '%s' "$content" | grep -qE '^#[[:space:]]*replay-fixture-aceite:[[:space:]]*.{20,}'; then
            exit 0
        fi
        echo "metrology-replay-fixtures-versionadas (SEM_ACEITE_YAML): $file_path sem '# replay-fixture-aceite: <razao>=20>'" >&2
        exit 2
        ;;
    *)
        # Extensao desconhecida em tests/replay_metrologico/ — exigir aceite
        # via comentario `# replay-fixture: skip --` ja tratado acima.
        echo "metrology-replay-fixtures-versionadas (EXTENSAO_DESCONHECIDA): $file_path extensao .$ext nao reconhecida" >&2
        echo "Aceitas: .json (chave _aceite_motivo) | .py/.yaml (comentario # replay-fixture-aceite)" >&2
        exit 2
        ;;
esac
