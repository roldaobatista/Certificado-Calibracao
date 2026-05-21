#!/usr/bin/env bash
# =============================================================
# csv-safety-import.sh — SEC-CSV-001 / SANEA-03
#
# Bloqueia (exit 2) geração de CSV fora da allowlist sem passar por
# `sanitizar_celula_csv` (clientes/csv_safety.py) — defesa anti
# CSV/formula injection (OWASP CSV Injection).
#
# Padrões disparadores (writers/exports):
#   - `csv.writer(...).writerow(...)`
#   - `csv.DictWriter(...).writerow(...)`
#   - `pandas.DataFrame.to_csv(...)`  /  `df.to_csv(...)`
#   - `writerows(...)`
#
# Bloqueia se conteúdo NÃO mencionar `sanitizar_celula_csv` (defesa
# em profundidade — não exige chamada na mesma linha, só presença no
# arquivo). Em arquivo fora da allowlist sem o helper, exporta-se cru.
#
# Allowlist (auto-allow):
#   - src/infrastructure/clientes/csv_safety.py (helper canônico)
#   - tests/**                                  (testes do helper)
#   - **/migrations/**                          (data migration one-off)
#   - docs/**                                   (não é código)
#
# Override em arquivo fora da allowlist:
#   # csv-safety: skip -- <razão com >=10 chars>
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/relatorios/exporter.py","content":"import csv\nw = csv.writer(f)\nw.writerow([\"=cmd|x\"])"}}' | bash .claude/hooks/csv-safety-import.sh
#   echo $?  # 2
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

case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# AUTO-ALLOW
case "$norm_path" in
    *src/infrastructure/clientes/csv_safety.py) exit 0 ;;
    */tests/*|*/test_*|*_test.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    *docs/*) exit 0 ;;
esac

# Override com justificativa
if printf '%s' "$content" | grep -qE '#[[:space:]]*csv-safety:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Detecta gatilhos de escrita CSV/Excel
detectou_export=0
if printf '%s' "$content" | grep -qE 'csv\.(writer|DictWriter)[[:space:]]*\('; then
    detectou_export=1
elif printf '%s' "$content" | grep -qE '\.writerow[s]?[[:space:]]*\('; then
    detectou_export=1
elif printf '%s' "$content" | grep -qE '\.to_csv[[:space:]]*\('; then
    detectou_export=1
fi

[ "$detectou_export" -eq 0 ] && exit 0

# Se exportou e NÃO referencia o helper, bloqueia.
if ! printf '%s' "$content" | grep -qE 'sanitizar_celula_csv'; then
    echo "csv-safety-import (SEC-CSV-001): geração de CSV em $file_path sem passar por sanitizar_celula_csv" >&2
    echo "Importe: from src.infrastructure.clientes.csv_safety import sanitizar_celula_csv" >&2
    echo "Aplique em cada célula antes de writerow/to_csv (anti CSV/formula injection — OWASP)." >&2
    echo "Override (raro): adicione '# csv-safety: skip -- <razão com >=10 chars>'" >&2
    exit 2
fi

exit 0
