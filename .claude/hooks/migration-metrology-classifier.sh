#!/usr/bin/env bash
# =============================================================
# migration-metrology-classifier.sh — Marco 4 P9
# ADR-0025 cl. 7.11.3 + GATE-CAL-MIG-CLASSIF + TEMA-M.4
#
# Migrations que tocam tabelas metrologicas (todas as do agregado
# Calibracao + filhos) precisam DECLARAR explicitamente:
#
#   1. Categoria de validacao ISO 17025 cl. 7.11.3:
#      # metrologia-classificacao: IQ  -> Installation Qualification
#                                          (criar tabela / DDL puro,
#                                           sem mudanca semantica)
#      # metrologia-classificacao: OQ  -> Operational Qualification
#                                          (ALTER, ADD, REMOVE, RENAME
#                                           — exige replay test)
#      # metrologia-classificacao: PQ  -> Performance Qualification
#                                          (mudanca em motor de calculo,
#                                           algoritmo, regra decisao —
#                                           exige replay test EXAUSTIVO
#                                           pre/pos com fixtures historicas)
#
#   2. Vinculo a replay fixture:
#      # replay-fixture: tests/replay_metrologico/<grandeza_ou_geral>.json
#      (ou `none` para migrations IQ puramente estruturais sem dados
#       afetados — exige justificativa em revisao humana mas o hook nao
#       exige fixture pra IQ).
#
# Por que existir:
#   ADR-0025 cl. 7.11.3 — validacao de software ISO 17025 exige rastreio
#   IQ/OQ/PQ por mudanca. Sem categoria explicita, mudanca em motor
#   passa como simples DDL e replay 25a corrompe silenciosamente.
#
# Escopo:
#   Apenas arquivos em `src/infrastructure/calibracao/migrations/*.py`.
#
# Migration neutra (so altera __init__.py ou docstrings) e migration
# inicial 0001 sao auto-allow.
#
# Override por migration:
#   # mig-classif: skip -- <razao com >=10 chars>
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/calibracao/migrations/0099_x.py","content":"operations = [migrations.AddField()]"}}' | bash .claude/hooks/migration-metrology-classifier.sh
#   echo $?  # 2 (sem cabecalho)
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

# Migration 0001_initial.py e __init__.py sao auto-allow
case "$norm_path" in
    *0001_initial.py|*migrations/__init__.py) exit 0 ;;
esac

# Override
if printf '%s' "$content" | grep -qE '#[[:space:]]*mig-classif:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# =============================================================
# Detecta operacoes Django/SQL que justifiquem classificacao:
# CreateModel, AddField, AlterField, RemoveField, RenameField,
# AddConstraint, RemoveConstraint, AlterModelOptions, RunSQL, RunPython.
# Se nao houver operacao, migration eh neutra (so docstring / imports)
# e o hook nao exige cabecalho.
# =============================================================
if ! printf '%s' "$content" | grep -qE 'migrations\.(CreateModel|AddField|AlterField|RemoveField|RenameField|AddConstraint|RemoveConstraint|AlterModelOptions|AlterUniqueTogether|AlterIndexTogether|RunSQL|RunPython|DeleteModel)|^[[:space:]]*operations[[:space:]]*='; then
    exit 0
fi

# =============================================================
# 1. Cabecalho metrologia-classificacao obrigatorio
# =============================================================
classificacao=$(printf '%s' "$content" | grep -E '^#[[:space:]]*metrologia-classificacao:[[:space:]]*(IQ|OQ|PQ)\b' | head -1)
if [ -z "$classificacao" ]; then
    echo "migration-metrology-classifier (SEM_CLASSIFICACAO): migration metrologica sem cabecalho em $file_path" >&2
    echo "Adicione no topo do arquivo (apos a docstring/imports):" >&2
    echo "  # metrologia-classificacao: IQ  (criar tabela / DDL puro)" >&2
    echo "  # metrologia-classificacao: OQ  (ALTER / ADD / RENAME — exige replay)" >&2
    echo "  # metrologia-classificacao: PQ  (mudanca em motor de calculo — replay exaustivo)" >&2
    echo "ADR-0025 cl. 7.11.3 + GATE-CAL-MIG-CLASSIF." >&2
    echo "Override: # mig-classif: skip -- <razao com >=10 chars>" >&2
    exit 2
fi

# =============================================================
# 2. Cabecalho replay-fixture obrigatorio (mesmo que valor seja `none`).
# Pra OQ/PQ, valor `none` SO eh aceito se houver `# replay-fixture-aceite:`
# justificando (e.g. tabela auxiliar sem dado metrologico afetado).
# Pra IQ, `none` aceitavel sem aceite extra.
# =============================================================
replay_line=$(printf '%s' "$content" | grep -E '^#[[:space:]]*replay-fixture:[[:space:]]*' | head -1)
if [ -z "$replay_line" ]; then
    echo "migration-metrology-classifier (SEM_REPLAY_FIXTURE): migration $file_path sem '# replay-fixture: <path>'" >&2
    echo "Adicione no topo:" >&2
    echo "  # replay-fixture: tests/replay_metrologico/<grandeza>.json" >&2
    echo "Ou para migration IQ pura (sem dado afetado):" >&2
    echo "  # replay-fixture: none" >&2
    echo "ADR-0025 cl. 7.11.3." >&2
    exit 2
fi

# Se classificacao OQ ou PQ e replay-fixture=none, exige aceite extra
case "$classificacao" in
    *OQ*|*PQ*)
        if printf '%s' "$replay_line" | grep -qE '^#[[:space:]]*replay-fixture:[[:space:]]*none\b'; then
            if ! printf '%s' "$content" | grep -qE '^#[[:space:]]*replay-fixture-aceite:[[:space:]]*.{10,}'; then
                echo "migration-metrology-classifier (REPLAY_FIXTURE_NONE_SEM_ACEITE): migration $file_path classificada OQ/PQ com replay-fixture=none mas sem '# replay-fixture-aceite: <razao>'" >&2
                echo "OQ/PQ exigem replay deterministico — 'none' so aceito com justificativa formal." >&2
                exit 2
            fi
        fi
        ;;
esac

exit 0
