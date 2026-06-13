---
owner: roldao
revisado-em: 2026-06-13
status: stable
diataxis: reference
audiencia: agente+roldao
relacionados:
  - scripts/status-projeto.sh
  - AGENTS.md
  - REGRAS-INEGOCIAVEIS.md
---

# STATUS GERADO — fonte única das contagens do projeto

> **NÃO EDITAR À MÃO.** Este arquivo é regenerado por `scripts/status-projeto.sh`.
> Qualquer doc que cite estes números deve apontar para cá, não recontar à mão.
> Verificação anti-drift: `bash scripts/status-projeto.sh --check`.

| Métrica | Valor | Fonte direta |
|---|---|---|
| Hooks ativos | **80** | `.claude/hooks/*.sh` (excl. _test-runner) |
| Casos no _test-runner | **619** | `grep -c run_case .claude/hooks/_test-runner.sh` |
| ADRs | **82** | `docs/adr/*.md` |
| Invariantes (IDs INV-*) | **143** | `REGRAS-INEGOCIAVEIS.md` |
