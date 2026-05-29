#!/usr/bin/env bash
# verificar-catalogo-seed.sh — sentinela do catálogo de migrations de semente.
#
# Motivação: auditoria da máquina de dev (2026-05-29). O `tests/conftest.py`
# tem um catálogo MANUAL `_SEED_MIGRATIONS` que re-aplica os dados-semente
# após o TRUNCATE de cada TransactionTestCase. Se uma migration de semente
# nova entra e NÃO é catalogada, o TRUNCATE a apaga e ela não volta →
# incidente dos 197 testes quebrados (24/05). Este sentinela falha e diz
# exatamente qual migration ficou de fora, ANTES do incidente.
#
# Estático (sem Docker): só inspeciona filesystem + conftest.
#
# Uso:
#   bash scripts/verificar-catalogo-seed.sh   # exit 1 se houver semente fora do catálogo
#
# Convenção (igual ao conftest): migration de semente = arquivo *seed*.py em
# src/infrastructure/**/migrations/ que define função `seed(...)`.
# app_label = nome do diretório que contém migrations/ (cobre path aninhado
# metrologia/padroes → "padroes", ADR-0072).

set -euo pipefail

PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJ_DIR"

CONFTEST="tests/conftest.py"
falhas=0
avisos=0

# Catálogo do conftest: pares ("app", "migration") — só as linhas dentro do bloco _SEED_MIGRATIONS.
catalogo=$(grep -oE '\("[a-z_]+", "[0-9a-zA-Z_]+"\)' "$CONFTEST" | tr -d '() "' )
# normaliza para "app,migration"
catalogo=$(printf '%s\n' "$catalogo" | sed 's/,\([0-9]\)/,\1/' )

esta_no_catalogo() { # app  migration
    printf '%s\n' "$catalogo" | grep -qx "$1,$2"
}

# Restaurável = define seed() OU seed_forward() (ambos suportados pelo conftest).
_restauravel() { grep -qE "^def (seed|seed_forward)\(" "$1"; }

# 1) DIREÇÃO PERIGOSA: toda migration de semente no disco (restaurável) tem que estar no catálogo.
for f in $(find src/infrastructure -path "*/migrations/*seed*.py" | sort); do
    _restauravel "$f" || continue
    mig=$(basename "$f" .py)
    migrations_dir=$(dirname "$f")            # .../<app>/migrations
    app=$(basename "$(dirname "$migrations_dir")")
    if ! esta_no_catalogo "$app" "$mig"; then
        echo "  FALHA: $f define seed() mas ($app, $mig) NÃO está em _SEED_MIGRATIONS do conftest." >&2
        echo "         → TRUNCATE transacional apagaria esse dado-semente sem restaurar (risco do incidente 197 testes)." >&2
        falhas=$((falhas + 1))
    fi
done

# 2) DIREÇÃO DE DRIFT (aviso): entrada do catálogo aponta pra arquivo que não existe, ou existe mas
#    não tem seed() (conftest faz no-op → dado não restaurado).
_subpath() { case "$1" in padroes) echo "metrologia/padroes" ;; *) echo "$1" ;; esac; }
while IFS=, read -r app mig; do
    [ -z "$app" ] && continue
    sub=$(_subpath "$app")
    arq="src/infrastructure/${sub}/migrations/${mig}.py"
    if [ ! -f "$arq" ]; then
        echo "  AVISO: catálogo aponta ($app, $mig) mas $arq não existe (migration renomeada/removida?)." >&2
        avisos=$((avisos + 1))
    elif ! _restauravel "$arq"; then
        echo "  AVISO: ($app, $mig) está no catálogo mas $arq NÃO define seed() nem seed_forward() — o conftest faz no-op e NÃO restaura esse dado." >&2
        avisos=$((avisos + 1))
    fi
done < <(printf '%s\n' "$catalogo")

if [ "$falhas" -gt 0 ]; then
    echo "" >&2
    echo "FALHA: $falhas migration(s) de semente fora do catálogo _SEED_MIGRATIONS. Adicione ao tests/conftest.py." >&2
    exit 1
fi

echo "OK: catálogo de semente sincronizado ($(printf '%s\n' "$catalogo" | grep -c , ) entradas; 0 sementes órfãs). Avisos: $avisos."
exit 0
