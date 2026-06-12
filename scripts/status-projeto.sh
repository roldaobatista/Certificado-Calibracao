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
#   bash scripts/status-projeto.sh --check    # denylist: falha (exit 1) se AGENTS/CLAUDE/README contiverem contagem viva (\d+ hooks/casos/ADRs/INVs)
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
ADRS=$(ls docs/adr/[0-9]*.md 2>/dev/null | wc -l | tr -d ' ')
INVS=$(grep -ohE "\bINV-[A-Z]*-?[0-9]{3}" REGRAS-INEGOCIAVEIS.md 2>/dev/null | sort -u | wc -l | tr -d ' ')

# ---- Modo --check: denylist — falha se encontrar contagem viva nos contratos -
# Rationale (R11 auditoria-cerimonia-2026-06-12): policiar cópia-de-número é
# estruturalmente furado (auditoria mediu "72 ativos" quando o real era 74).
# Fonte única = STATUS-GERADO.md. AGENTS/CLAUDE/README devem usar ponteiro, não
# número. O gate agora FALHA se encontrar padrão de contagem viva nesses arquivos.
if [[ "${1:-}" == "--check" ]]; then
  ocorrencias=0

  # Padrões de contagem viva (regex ERE):
  #   \d+ hooks ativos | \d+ casos | \d+/\d+ casos | \d+ ADRs | \d+ INVs(ariantes)
  DENYLIST_RE='[0-9]+ hooks? ativos|[0-9]+(/[0-9]+)? casos? (verdes?|no _test-runner)|[0-9]+ ADRs|[0-9]+ INVs?'

  for arq in AGENTS.md CLAUDE.md README.md; do
    [[ -f "$arq" ]] || continue
    matches=$(grep -Ec "$DENYLIST_RE" "$arq" 2>/dev/null || true)
    if [[ "$matches" -gt 0 ]]; then
      echo "  DENYLIST: $arq contém $matches linha(s) com contagem viva."
      grep -En "$DENYLIST_RE" "$arq" | head -5 | sed "s/^/    /"
      ocorrencias=$((ocorrencias + matches))
    fi
  done

  if [[ "$ocorrencias" -gt 0 ]]; then
    echo ""
    echo "FALHA: $ocorrencias linha(s) com contagem viva encontradas em AGENTS/CLAUDE/README."
    echo "Substitua o número por ponteiro para docs/governanca/STATUS-GERADO.md."
    echo "Contagens reais: hooks=$HOOKS casos=$CASOS ADRs=$ADRS INVs=$INVS"
    exit 1
  fi
  echo "OK: AGENTS.md, CLAUDE.md e README.md não contêm contagens vivas (hooks=$HOOKS casos=$CASOS ADRs=$ADRS INVs=$INVS)."
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
