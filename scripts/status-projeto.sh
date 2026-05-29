#!/usr/bin/env bash
# status-projeto.sh — fonte ÚNICA e AUTOMÁTICA das contagens do projeto.
#
# Motivação: auditoria da máquina de dev (2026-05-29) mediu que as contagens
# (hooks / casos de teste / ADRs / invariantes) eram copiadas À MÃO em 12+
# arquivos e já divergiam entre si — o README anunciava "48 hooks / 379 casos /
# 61 ADRs" quando o real era "55 / 450 / 73". Número colado à mão mente; número
# que sai de comando, não. Estes números são METADADOS (não controle de
# proteção), logo automatizá-los é ganho de velocidade sem risco à rede.
#
# Uso:
#   bash scripts/status-projeto.sh            # imprime as contagens e regenera docs/governanca/STATUS-GERADO.md
#   bash scripts/status-projeto.sh --check    # verifica se os números à mão nos docs canônicos batem; sai 1 se divergir
#   bash scripts/status-projeto.sh --quiet    # só regenera o arquivo, sem imprimir
#
# Janela Windows + Git Bash: sem jq, sem bc — só awk/grep/ls.

set -euo pipefail

# Raiz do projeto = pai de scripts/ (funciona de qualquer diretório).
PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJ_DIR"

GERADO="docs/governanca/STATUS-GERADO.md"

# ---- Contagens da FONTE DIRETA (nunca doc-contra-doc) ----------------------
HOOKS=$(ls .claude/hooks/*.sh 2>/dev/null | grep -v "_test-runner.sh" | wc -l | tr -d ' ')
CASOS=$(grep -c "run_case " .claude/hooks/_test-runner.sh 2>/dev/null | tr -d ' ')
ADRS=$(ls docs/adr/*.md 2>/dev/null | wc -l | tr -d ' ')
INVS=$(grep -ohE "\bINV-[A-Z]*-?[0-9]{3}" REGRAS-INEGOCIAVEIS.md 2>/dev/null | sort -u | wc -l | tr -d ' ')

# ---- Modo --check: os números à mão nos docs batem com o real? -------------
if [[ "${1:-}" == "--check" ]]; then
  divergencias=0
  reportar() { # arquivo  rotulo  esperado  encontrado
    echo "  DIVERGE: $1 diz '$4' para $2, mas o real é '$3'"
    divergencias=$((divergencias + 1))
  }

  for arq in AGENTS.md README.md CLAUDE.md; do
    [[ -f "$arq" ]] || continue
    # "N hooks ativos"
    while IFS= read -r n; do
      [[ -z "$n" ]] && continue
      [[ "$n" != "$HOOKS" ]] && reportar "$arq" "hooks ativos" "$HOOKS" "$n"
    done < <(grep -oE "[0-9]+ hooks? ativos" "$arq" | grep -oE "^[0-9]+")
    # "N/N casos" ou "N casos"
    while IFS= read -r n; do
      [[ -z "$n" ]] && continue
      [[ "$n" != "$CASOS" ]] && reportar "$arq" "casos de teste" "$CASOS" "$n"
    done < <(grep -oE "[0-9]+(/[0-9]+)? (casos|verdes)" "$arq" | grep -oE "^[0-9]+")
  done

  # README também anuncia "N ADRs" no resumo público
  if [[ -f README.md ]]; then
    while IFS= read -r n; do
      [[ -z "$n" ]] && continue
      [[ "$n" != "$ADRS" ]] && reportar "README.md" "ADRs" "$ADRS" "$n"
    done < <(grep -oE "[0-9]+ ADRs" README.md | grep -oE "^[0-9]+")
  fi

  if [[ "$divergencias" -gt 0 ]]; then
    echo ""
    echo "FALHA: $divergencias número(s) à mão divergem do real (hooks=$HOOKS casos=$CASOS ADRs=$ADRS)."
    echo "Corrija o doc OU rode 'bash scripts/status-projeto.sh' e use a fonte gerada."
    exit 1
  fi
  echo "OK: números à mão nos docs canônicos batem com o real (hooks=$HOOKS casos=$CASOS ADRs=$ADRS INVs=$INVS)."
  exit 0
fi

# ---- Regenera o arquivo de fonte única (determinístico, sem timestamp) -----
cat > "$GERADO" <<EOF
---
owner: roldao
revisado_em: gerado-automaticamente
status: generated
diataxis: reference
audiencia: agente+roldao
relacionados:
  - scripts/status-projeto.sh
  - AGENTS.md
  - REGRAS-INEGOCIAVEIS.md
---

# STATUS GERADO — fonte única das contagens do projeto

> **NÃO EDITAR À MÃO.** Este arquivo é regenerado por \`scripts/status-projeto.sh\`.
> Qualquer doc que cite estes números deve apontar para cá, não recontar à mão.
> Verificação anti-drift: \`bash scripts/status-projeto.sh --check\`.

| Métrica | Valor | Fonte direta |
|---|---|---|
| Hooks ativos | **$HOOKS** | \`.claude/hooks/*.sh\` (excl. _test-runner) |
| Casos no _test-runner | **$CASOS** | \`grep -c run_case .claude/hooks/_test-runner.sh\` |
| ADRs | **$ADRS** | \`docs/adr/*.md\` |
| Invariantes (IDs INV-*) | **$INVS** | \`REGRAS-INEGOCIAVEIS.md\` |
EOF

if [[ "${1:-}" != "--quiet" ]]; then
  echo "Contagens reais (fonte direta):"
  echo "  Hooks ativos ........ $HOOKS"
  echo "  Casos de teste ...... $CASOS"
  echo "  ADRs ................ $ADRS"
  echo "  Invariantes INV-* ... $INVS"
  echo ""
  echo "Regenerado: $GERADO"
fi
