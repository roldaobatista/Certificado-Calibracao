# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Fase/Marco/US.

**Fase:** SANEAMENTO F-A **CONCLUÍDO** (rodada 2 verde). Próxima fase:
saneamento F-B (mesmo loop) → Marco 1 `clientes` definitivo → Marco 2
`equipamentos`. **Modo:** AUTÔNOMO.

## F-A SANEADA E FECHADA (2026-05-18)

Loop auditar→corrigir→reauditar completo. Rodada 1 (1 CRÍTICO + 6 ALTO +
3 MÉDIO) → todos fechados via ritual (design → review subagente →
implement → verde → commit/push):

- `1fcbfff` FA-A4 — rede contra migration mentirosa
- `3b08bbb` FA-C1+FA-A3 — hash chain por-tenant + cadeia sistema + Q-02 +
  lock por-tenant + sequência monotônica
- `2eb986a` FA-A2 — template RLS único + fail-loud em clientes
- `7243684` FA-A1+FA-M2 — PII_HASH_KEY versionada + registry redatado +
  gate de prod por entropia + colunas ip_hash→TextField
- `d7e7e0b` FA-A5+FA-M1 — drill robusto + números/status sincronizados
- `9bf092e` FA-M3 — higiene (limpar_contexto removido, god-function
  quebrada, base.py E402)
- `a8cb79e` drift migration clientes (makemigrations --check verde)

**Reauditoria rodada 2 — 3 lentes, código real: ZERO CRÍTICO / ZERO
ALTO.** Segurança (`auditor-seguranca`) PASS, arquitetura
(`tech-lead`) APROVA, qualidade (`auditor-qualidade`) PASS.
Consolidado: `docs/faseamento/auditorias/F-A-CONSOLIDADO-rodada-2.md`.
Suite 259 passed (0 skip), cobertura 84.84%, hooks 113/113.

## Próximo passo (retomar)
1. **Saneamento F-B** (TaskList #9): auditar F-B 10 lentes → corrigir
   CRÍTICO/ALTO via ritual → reauditar rodada 2 → zero CRÍTICO/ALTO.
2. Backlog Wave-A rodada 2 (TaskList #8): R2-M1/M2 + BAIXOs — NÃO
   reabrem F-A; endereçar em Wave A.
3. #7 lint sweep Wave-A (clientes/models.py RUF012/DJ012, test files).
4. Após F-B saneada → Marco 1 `clientes` definitivo → Marco 2.

## Fila de tarefas
TaskList: #9 F-B saneamento (próximo), #8 backlog Wave-A r2, #7 lint
sweep. Consolidados em `docs/faseamento/auditorias/`.
