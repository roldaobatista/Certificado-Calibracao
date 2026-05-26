#!/usr/bin/env bash
# =============================================================
# incerteza-versao-motor-check.sh — Marco 4 P9 INV-CAL-VERSAO-001 / ADR-0025
#
# Defende o conteudo do campo `versao_motor_calculo` persistido em
# Calibracao + OrcamentoIncerteza. Sem versionamento explicito (semver +
# commit-hash + algoritmo_id), replay deterministico em 25 anos quebra
# e CGCRE em 2050 nao consegue reproduzir resultados.
#
# Forma canonica (VersaoMotorCalculo.__str__):
#   "<ALGORITMO_v<N>> <SEMVER>@<COMMIT7>"
#   Ex: "GUM_CLASSICO_v1 1.0.0@a1b2c3d"
#
# Bloqueios:
#
# 1. (LITERAL_VAZIO_FORA_RECEPCIONADA) `versao_motor_calculo` atribuido
#    a string literal NAO-VAZIA que nao bate o formato canonico.
#    Aceita "" (default em RECEPCIONADA — pre-calculo).
#    Aceita f-string / variavel (runtime — fora do escopo do hook).
#    Bloqueia: "1.0.0", "motor-v1", "GUM_CLASSICO" — falta um dos
#    componentes (algoritmo_id, semver com 3 partes, ou @<commit>).
#
# 2. (PERSISTIDO_VAZIO_POS_CALCULO) `versao_motor_calculo=""` literal
#    em construcao de OrcamentoIncertezaSnapshot ou em UPDATE SQL na
#    tabela `orcamento_incerteza`. ORCAMENTO sem versao do motor =
#    auditoria 25a quebrada.
#
# Auto-allow (exit 0):
#   - tests/**                                (testam o helper)
#   - **/migrations/**                        (data migrations one-off)
#   - docs/**                                 (exemplos em docs/ADRs)
#   - src/domain/metrologia/calibracao/value_objects.py
#     (regex canonico vive aqui)
#   - src/application/metrologia/calibracao/criar_calibracao.py
#     (cravacao do default vazio "" na criacao em RECEPCIONADA)
#
# Override em arquivo fora da allowlist:
#   # incerteza-versao: skip -- <razao com >=10 chars>
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/foo.py","content":"versao_motor_calculo = \"1.0.0\""}}' | bash .claude/hooks/incerteza-versao-motor-check.sh
#   echo $?  # 2
#
#   echo '{"tool_input":{"file_path":"src/foo.py","content":"versao_motor_calculo = \"GUM_CLASSICO_v1 1.0.0@abc1234\""}}' | bash .claude/hooks/incerteza-versao-motor-check.sh
#   echo $?  # 0
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

# Tipos cobertos: Python (.py) e SQL (.sql)
case "$norm_path" in
    *.py|*.sql) ;;
    *) exit 0 ;;
esac

# AUTO-ALLOW pelo caminho
auto_allow=0
case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py) auto_allow=1 ;;
    */migrations/*) auto_allow=1 ;;
    docs/*|*/docs/*) auto_allow=1 ;;
    src/domain/metrologia/calibracao/value_objects.py|*src/domain/metrologia/calibracao/value_objects.py) auto_allow=1 ;;
    src/application/metrologia/calibracao/criar_calibracao.py|*src/application/metrologia/calibracao/criar_calibracao.py) auto_allow=1 ;;
esac

# Override
if printf '%s' "$content" | grep -qE '#[[:space:]]*incerteza-versao:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

[ "$auto_allow" -eq 1 ] && exit 0

# =============================================================
# 1. LITERAL_VAZIO_FORA_RECEPCIONADA: literal nao-vazio que falha
#    formato canonico VersaoMotorCalculo.__str__ ("<ALG_vN> <SEMVER>@<COMMIT7>").
# =============================================================

# Padrao alvo: versao_motor_calculo = "..."
# (Aceita variacoes "versao_motor_calculo=" e "versao_motor_calculo = ")
viol_lines=$(printf '%s\n' "$content" | grep -nE 'versao_motor_calculo[[:space:]]*=[[:space:]]*["\x27][^"\x27]+["\x27]' || true)

if [ -n "$viol_lines" ]; then
    bad=$(printf '%s\n' "$viol_lines" | while IFS= read -r line; do
        # Extrai valor literal entre aspas
        val=$(printf '%s' "$line" | perl -ne '
            if (/versao_motor_calculo\s*=\s*(["\x27])([^"\x27]*)\1/) {
                print "$2\n";
            }
        ')
        [ -z "$val" ] && continue
        # Formato canonico: contem algoritmo_id (_v<digit>) E semver \d+\.\d+\.\d+ E @<7+ hex>
        # Regex amalgamado:
        #   ^.*_v\d+.* \d+\.\d+\.\d+(-[0-9A-Za-z\.\-]+)?@[0-9a-f]{7,40}$
        if printf '%s' "$val" | grep -qE '^[A-Z][A-Z0-9_]*_v[0-9]+ [0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z\.\-]+)?@[0-9a-f]{7,40}$'; then
            continue
        fi
        printf '%s\n' "$line"
    done)
    if [ -n "$bad" ]; then
        echo "incerteza-versao-motor-check (LITERAL_FORMATO_INVALIDO): versao_motor_calculo literal em $file_path nao bate formato canonico" >&2
        printf '%s\n' "$bad" | head -5 >&2
        echo "Formato esperado: '<ALGORITMO>_v<N> <SEMVER>@<COMMIT7+>' (ex: 'GUM_CLASSICO_v1 1.0.0@a1b2c3d')" >&2
        echo "INV-CAL-VERSAO-001 + ADR-0025 cl. 7.11 — replay deterministico exige snapshot da versao." >&2
        echo "Use str(VersaoMotorCalculo(...)) do helper unico value_objects.py." >&2
        echo "Override: # incerteza-versao: skip -- <razao com >=10 chars>" >&2
        exit 2
    fi
fi

# =============================================================
# 2. PERSISTIDO_VAZIO_POS_CALCULO: OrcamentoIncertezaSnapshot(...) com
#    versao_motor_calculo="" literal. Snapshot do orcamento eh
#    POS-calculo — string vazia rompe INV-CAL-VERSAO-001.
#
# Detecta padroes:
#   OrcamentoIncertezaSnapshot(... versao_motor_calculo="" ...)
#   ou em SQL: INSERT INTO orcamento_incerteza ... versao_motor_calculo='' ...
# =============================================================
case "$norm_path" in
    *.py)
        # Heuristica: linha que contem OrcamentoIncerteza (Snapshot|orcamento_repo)
        # e ao mesmo tempo versao_motor_calculo="" (em janela proxima de 5 linhas)
        if printf '%s' "$content" | grep -qE 'OrcamentoIncertezaSnapshot[[:space:]]*\(' \
           && printf '%s\n' "$content" | grep -nE 'versao_motor_calculo[[:space:]]*=[[:space:]]*["\x27]["\x27]' >/dev/null 2>&1; then
            echo "incerteza-versao-motor-check (PERSISTIDO_VAZIO_POS_CALCULO): OrcamentoIncertezaSnapshot construido com versao_motor_calculo=\"\" em $file_path" >&2
            echo "Orcamento eh POS-calculo — campo vazio quebra INV-CAL-VERSAO-001 (replay 25a impossivel)." >&2
            echo "Use str(VersaoMotorCalculo(semver, commit_hash, algoritmo_id, vigencia))." >&2
            exit 2
        fi
        ;;
    *.sql)
        # UPDATE/INSERT em orcamento_incerteza com versao_motor_calculo=''
        if printf '%s' "$content" | grep -qiE 'INSERT[[:space:]]+INTO[[:space:]]+orcamento_incerteza|UPDATE[[:space:]]+orcamento_incerteza'; then
            if printf '%s' "$content" | grep -qE "versao_motor_calculo[[:space:]]*=[[:space:]]*''"; then
                echo "incerteza-versao-motor-check (SQL_PERSISTIDO_VAZIO): UPDATE/INSERT em orcamento_incerteza com versao_motor_calculo='' em $file_path" >&2
                echo "Campo obrigatorio pos-calculo (INV-CAL-VERSAO-001)." >&2
                exit 2
            fi
        fi
        ;;
esac

exit 0
