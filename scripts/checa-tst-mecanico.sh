#!/usr/bin/env bash
# scripts/checa-tst-mecanico.sh
# Verificação mecânica de TST-004 (INV-* sem teste) e TST-006 (UUID literal hardcoded em testes).
# Criado 2026-06-12 — auditoria de cerimônia R9 (aprovação Roldão).
#
# Uso:
#   bash scripts/checa-tst-mecanico.sh --report   # informativo, exit 0 sempre
#   bash scripts/checa-tst-mecanico.sh --strict    # exit 1 se encontrar problema real
#
# Compatível com Git Bash (Windows) + bash Linux. SEM jq — usa grep e perl.
#
# Cobertura:
#   TST-004: toda família INV-<X>-NNN em REGRAS-INEGOCIAVEIS.md que tenha código
#            construído deve ter classe/função TestINV_<X> em tests/.
#   TST-006: UUIDs literais hardcoded em testes (padrão 8-4-4-4-12 hex).

set -euo pipefail

# ── Configuração ──────────────────────────────────────────────────────────────
STRICT=false
if [[ "${1:-}" == "--strict" ]]; then
    STRICT=true
elif [[ "${1:-}" == "--report" ]]; then
    STRICT=false
else
    echo "Uso: bash scripts/checa-tst-mecanico.sh --report | --strict"
    exit 1
fi

PROJETO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGRAS="$PROJETO_ROOT/REGRAS-INEGOCIAVEIS.md"
TESTS_DIR="$PROJETO_ROOT/tests"

PROBLEMAS=0
AVISOS=0

# ── Utilidades ────────────────────────────────────────────────────────────────
log_ok()   { echo "[OK]      $*"; }
log_warn() { echo "[AVISO]   $*"; AVISOS=$((AVISOS + 1)); }
log_fail() { echo "[FALHA]   $*"; PROBLEMAS=$((PROBLEMAS + 1)); }
log_info() { echo "[INFO]    $*"; }

separador() { echo "────────────────────────────────────────────────────"; }

# ── Verifica pré-condições ────────────────────────────────────────────────────
if [[ ! -f "$REGRAS" ]]; then
    echo "[ERRO] REGRAS-INEGOCIAVEIS.md não encontrado em $PROJETO_ROOT"
    exit 1
fi

if [[ ! -d "$TESTS_DIR" ]]; then
    echo "[ERRO] Diretório tests/ não encontrado em $PROJETO_ROOT"
    exit 1
fi

echo ""
echo "=================================================="
echo "  checa-tst-mecanico.sh — verificação TST-004/006"
echo "  Projeto: $PROJETO_ROOT"
echo "  Data: $(date '+%Y-%m-%d %H:%M')"
echo "=================================================="
echo ""

# ── TST-004: Famílias INV-* com código devem ter TestINV_ em tests/ ───────────
separador
echo "TST-004 — Famílias INV-* com teste correspondente"
separador
echo ""

# Extrai todas as famílias únicas: INV-CLI, INV-TENANT, INV-PAD, etc.
# Padrão: INV-<FAMILIA>-NNN (aceita tanto INV-X-001 quanto INV-X-001a)
FAMILIAS=$(grep -o 'INV-[A-Z_][A-Z0-9_]*-[0-9]\+' "$REGRAS" 2>/dev/null \
    | perl -ne 'if (/INV-([A-Z0-9_]+)-\d+/) { print "$1\n" }' \
    | sort -u)

if [[ -z "$FAMILIAS" ]]; then
    log_warn "Nenhuma família INV-* encontrada em REGRAS-INEGOCIAVEIS.md"
else
    for FAMILIA in $FAMILIAS; do
        # Verifica se existe algum código Python construído para esta família
        # Proxy: se há qualquer arquivo .py em src/ mencionando a família
        TEM_CODIGO=$(grep -r "INV_${FAMILIA}\|INV-${FAMILIA}" \
            "$PROJETO_ROOT/src" 2>/dev/null \
            | grep -v "# INV\|#INV\|'INV\|\"INV" \
            | head -1 || true)

        if [[ -z "$TEM_CODIGO" ]]; then
            # Família sem código construído — informativo apenas
            log_info "INV-${FAMILIA}: sem código src/ (módulo ainda não construído?)"
            continue
        fi

        # Tem código — verifica se existe TestINV_ nos testes
        TEM_TESTE=$(grep -r "test_INV_${FAMILIA}\|TestINV_${FAMILIA}\|TEST_INV_${FAMILIA}" \
            "$TESTS_DIR" 2>/dev/null | head -1 || true)

        if [[ -n "$TEM_TESTE" ]]; then
            log_ok "INV-${FAMILIA}: teste encontrado"
        else
            log_fail "INV-${FAMILIA}: código em src/ existe, mas NENHUM teste test_INV_${FAMILIA}_* em tests/"
        fi
    done
fi

echo ""

# ── TST-006: UUIDs literais hardcoded em testes ───────────────────────────────
separador
echo "TST-006 — UUIDs literais hardcoded em testes (potencial fraqueza)"
separador
echo ""
log_info "Padrão procurado: UUID v4 completo 8-4-4-4-12 hex em arquivos test_*.py"
echo ""

# UUID completo: xxxxxxxx-xxxx-4xxx-[89ab]xxx-xxxxxxxxxxxx
# Regex simples que captura qualquer UUID de 32 hex + 4 hífens (não só v4)
UUID_HITS=$(grep -rn \
    '[0-9a-fA-F]\{8\}-[0-9a-fA-F]\{4\}-[0-9a-fA-F]\{4\}-[0-9a-fA-F]\{4\}-[0-9a-fA-F]\{12\}' \
    "$TESTS_DIR" \
    --include="test_*.py" \
    --include="*_test.py" \
    2>/dev/null || true)

if [[ -z "$UUID_HITS" ]]; then
    log_ok "Nenhum UUID literal hardcoded encontrado em tests/"
else
    # Filtra: ignora UUIDs em comentários de justificativa (# uuid literal intencional)
    UUID_SUSPEITOS=$(echo "$UUID_HITS" | grep -v "# uuid.*intencional\|# tst-006.*ok\|# literal.*intencional" || true)

    if [[ -z "$UUID_SUSPEITOS" ]]; then
        log_ok "UUIDs encontrados mas todos marcados com justificativa (ok)"
    else
        CONTAGEM=$(echo "$UUID_SUSPEITOS" | wc -l | tr -d ' ')
        log_warn "TST-006: $CONTAGEM ocorrência(s) de UUID literal em testes sem justificativa"
        echo ""
        echo "  (TST-006 = BAIXO por tabela R8; verificar se há teste-irmão com input literal"
        echo "   de borda cobrindo caso determinístico — não é veto automático)"
        echo ""
        echo "$UUID_SUSPEITOS" | head -20 | while IFS= read -r linha; do
            echo "  $linha"
        done
        if [[ $(echo "$UUID_SUSPEITOS" | wc -l) -gt 20 ]]; then
            echo "  ... (mostrando primeiras 20 de $CONTAGEM)"
        fi
    fi
fi

echo ""

# ── Resumo ────────────────────────────────────────────────────────────────────
separador
echo "Resumo"
separador
echo ""
echo "  Falhas (TST-004 INV sem teste): $PROBLEMAS"
echo "  Avisos (TST-006 UUID / outros): $AVISOS"
echo ""

if [[ "$STRICT" == "true" && "$PROBLEMAS" -gt 0 ]]; then
    echo "[STRICT] $PROBLEMAS problema(s) encontrado(s) — exit 1"
    echo ""
    exit 1
fi

echo "[OK] Verificação concluída — exit 0"
echo ""
exit 0
