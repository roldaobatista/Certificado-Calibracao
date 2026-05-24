#!/usr/bin/env bash
# =============================================================
# migration-concorrencia-os-check.sh — Marco 3 T-OS-105
#
# Defende INV-OS-CONC-001 (ADR-0041) — `idx_atividade_em_execucao_por_equip`
# eh o constraint declarativo que evita 2 atividades calibracao
# EM_EXECUCAO no mesmo equipamento. Bloqueia migration que:
#
# 1. CREATE TABLE atividade_da_os ... sem incluir o unique partial index
#    `idx_atividade_em_execucao_por_equip` na mesma migration OU em
#    migration-irma (referenciada).
# 2. DROP INDEX idx_atividade_em_execucao_por_equip sem outra migration
#    da MESMA familia recriando.
# 3. ALTER TABLE atividade_da_os DISABLE ROW LEVEL SECURITY (defesa em
#    profundidade — outro hook tambem cobre).
#
# Allow (exit 0):
# - migration ja existente preservada (sem CREATE/DROP do indice).
# - Path fora de `**/migrations/**`.
# - Override: `# concorrencia-os: skip -- <razao>=10 chars>`.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"a/migrations/0099.py","content":"CREATE TABLE atividade_da_os ( id uuid );"}}' \
#     | bash .claude/hooks/migration-concorrencia-os-check.sh
#   echo $?  # esperar 2
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

# So aplica em migrations.
if ! printf '%s' "$file_path" | grep -qE 'migrations/'; then
    exit 0
fi

# Override explicito.
if printf '%s' "$content" | grep -qE '#[[:space:]]*concorrencia-os:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# 1) CREATE TABLE atividade_da_os sem indice de concorrencia.
if printf '%s' "$content" | grep -qiE 'CREATE TABLE[[:space:]]+atividade_da_os\b|CreateModel.*name.*AtividadeDaOS'; then
    if ! printf '%s' "$content" | grep -qE 'idx_atividade_em_execucao_por_equip'; then
        cat >&2 <<EOF
migration-concorrencia-os-check: migracao cria/recria 'atividade_da_os'
sem o indice unique parcial 'idx_atividade_em_execucao_por_equip'
(INV-OS-CONC-001 / ADR-0041).

Arquivo: $file_path

Inclua o indice na MESMA migration OU referencie migration-irma:

  CREATE UNIQUE INDEX idx_atividade_em_execucao_por_equip
    ON atividade_da_os (tenant_id, equipamento_id_desnormalizado)
    WHERE estado='em_execucao' AND tipo_bloqueia_concorrencia=true;

Override (com razao >=10 chars):
  # concorrencia-os: skip -- <razao>
EOF
        exit 2
    fi
fi

# 2) DROP do indice sem recreacao na mesma migration.
if printf '%s' "$content" | grep -qiE 'DROP INDEX[[:space:]]+(IF EXISTS[[:space:]]+)?idx_atividade_em_execucao_por_equip|RemoveIndex.*idx_atividade_em_execucao_por_equip'; then
    if ! printf '%s' "$content" | grep -qE 'CREATE UNIQUE INDEX[[:space:]]+idx_atividade_em_execucao_por_equip|AddIndex.*idx_atividade_em_execucao_por_equip'; then
        cat >&2 <<EOF
migration-concorrencia-os-check: migration faz DROP de
'idx_atividade_em_execucao_por_equip' sem recriar na mesma migration.
INV-OS-CONC-001 ficaria sem defesa declarativa.

Arquivo: $file_path

Override (com razao >=10 chars):
  # concorrencia-os: skip -- <razao>
EOF
        exit 2
    fi
fi

# 3) DISABLE ROW LEVEL SECURITY em atividade_da_os.
if printf '%s' "$content" | grep -qiE 'ALTER TABLE[[:space:]]+atividade_da_os[[:space:]]+DISABLE ROW LEVEL SECURITY'; then
    cat >&2 <<EOF
migration-concorrencia-os-check: ALTER TABLE atividade_da_os DISABLE ROW
LEVEL SECURITY proibido (defesa em profundidade INV-TENANT-001).

Arquivo: $file_path

Override (com razao >=10 chars):
  # concorrencia-os: skip -- <razao>
EOF
    exit 2
fi

exit 0
