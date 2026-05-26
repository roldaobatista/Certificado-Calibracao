#!/usr/bin/env bash
# =============================================================
# migration-concorrencia-calibracao-check.sh — Marco 4 P9
# INV-CAL-CONC-001..004 / ADR-0065
#
# Defende a concorrencia da raiz agregado Calibracao + filhos:
#
# 1. (LEITURA_SEM_UNIQUE) — Migration que cria tabela `leitura` DEVE
#    declarar UNIQUE composto (tenant_id, calibracao_id,
#    ponto_calibracao, numero_repeticao) — INV-CAL-CONC-001.
#    Sem isso, 2 metrologistas registrando mesmo ponto+repeticao
#    geram corrida silenciosa.
#
# 2. (CALIBRACAO_REVISION_REMOVE) — Migration que DROPA coluna
#    `revision` da tabela `calibracao` — INV-CAL-CONC-003.
#    Coluna de optimistic lock CAS; remocao quebra 11 transicoes
#    de estado.
#
# Escopo:
#   Apenas arquivos em `src/infrastructure/calibracao/migrations/`.
#   Outras migrations sao ignoradas (deferidas para
#   `migration-rls-check` / `audit-immutability-check`).
#
# Override por migration:
#   # cal-conc: skip -- <razao com >=10 chars>
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/calibracao/migrations/0002_leitura.py","content":"class Migration(migrations.Migration):\n  operations = [migrations.CreateModel(name=\"Leitura\")]"}}' | bash .claude/hooks/migration-concorrencia-calibracao-check.sh
#   echo $?  # 2 (sem UNIQUE composto)
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

# So .py em src/infrastructure/calibracao/migrations/
case "$norm_path" in
    *src/infrastructure/calibracao/migrations/*.py|src/infrastructure/calibracao/migrations/*.py) ;;
    *) exit 0 ;;
esac

# Override
if printf '%s' "$content" | grep -qE '#[[:space:]]*cal-conc:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# =============================================================
# 1. LEITURA_SEM_UNIQUE: migration cria tabela `leitura` mas nao tem
#    UNIQUE composto com as 4 colunas obrigatorias
#    (tenant_id + calibracao_id + ponto_calibracao + numero_repeticao).
#
#    Detecta padroes Django:
#      CreateModel(name='Leitura', ...) OU CreateModel(name="Leitura", ...)
#    E checa se o mesmo content tem as 4 colunas dentro de algum
#    UniqueConstraint(...) ou unique_together= ou UNIQUE INDEX raw SQL.
# =============================================================
if printf '%s' "$content" | grep -qE 'CreateModel\([^)]*name[[:space:]]*=[[:space:]]*["\x27]Leitura["\x27]'; then
    # Verifica se as 4 colunas aparecem dentro de uma constraint unica.
    # Heuristica forte: cada uma das 4 colunas aparece em pelo menos
    # uma linha que tambem contem 'unique' (case-insensitive) ou
    # 'UniqueConstraint' OU as 4 aparecem juntas em uma janela proxima.
    #
    # Simplificacao: verifica se TODAS as 4 substrings aparecem no
    # conteudo E se ha pelo menos uma das palavras-chave de UNIQUE.
    falta=""
    printf '%s' "$content" | grep -q 'tenant_id'         || falta="$falta tenant_id"
    printf '%s' "$content" | grep -q 'calibracao_id'     || falta="$falta calibracao_id"
    printf '%s' "$content" | grep -q 'ponto_calibracao'  || falta="$falta ponto_calibracao"
    printf '%s' "$content" | grep -q 'numero_repeticao'  || falta="$falta numero_repeticao"
    tem_unique=0
    if printf '%s' "$content" | grep -qiE 'UniqueConstraint|unique_together|UNIQUE[[:space:]]+INDEX|UNIQUE[[:space:]]*\('; then
        tem_unique=1
    fi
    if [ -n "$falta" ] || [ "$tem_unique" -eq 0 ]; then
        echo "migration-concorrencia-calibracao-check (LEITURA_SEM_UNIQUE): CreateModel('Leitura') sem UNIQUE composto (tenant_id, calibracao_id, ponto_calibracao, numero_repeticao) em $file_path" >&2
        [ -n "$falta" ] && echo "Faltam referencias as colunas:$falta" >&2
        [ "$tem_unique" -eq 0 ] && echo "Faltam keywords UniqueConstraint / unique_together / UNIQUE INDEX no conteudo." >&2
        echo "INV-CAL-CONC-001 + ADR-0065 — leitura duplicada por race silenciosa quebra cl. 7.5." >&2
        echo "Override: # cal-conc: skip -- <razao com >=10 chars>" >&2
        exit 2
    fi
fi

# =============================================================
# 2. CALIBRACAO_REVISION_REMOVE: migration que REMOVE coluna revision
#    da tabela calibracao. Indicacao:
#      migrations.RemoveField(model_name='calibracao', name='revision')
#    OU SQL "ALTER TABLE calibracao DROP COLUMN revision"
# =============================================================
if printf '%s' "$content" | grep -qE 'RemoveField\([^)]*model_name[[:space:]]*=[[:space:]]*["\x27]calibracao["\x27][^)]*name[[:space:]]*=[[:space:]]*["\x27]revision["\x27]'; then
    echo "migration-concorrencia-calibracao-check (CALIBRACAO_REVISION_REMOVE): RemoveField revision em Calibracao em $file_path" >&2
    echo "INV-CAL-CONC-003 + ADR-0065 — coluna de optimistic lock; remocao quebra 11 transicoes de estado." >&2
    echo "Override: # cal-conc: skip -- <razao com >=10 chars>" >&2
    exit 2
fi

# SQL DROP COLUMN revision em tabela calibracao
if printf '%s' "$content" | grep -qiE 'ALTER[[:space:]]+TABLE[[:space:]]+calibracao[[:space:]]+DROP[[:space:]]+COLUMN[[:space:]]+revision\b'; then
    echo "migration-concorrencia-calibracao-check (CALIBRACAO_REVISION_REMOVE_SQL): ALTER TABLE calibracao DROP COLUMN revision em $file_path" >&2
    echo "INV-CAL-CONC-003 + ADR-0065." >&2
    exit 2
fi

exit 0
