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

## SANEAMENTO F-B — em andamento (rodada 1 feita)

Rodada 1 (3 lentes) consolidada em `auditorias/F-B-CONSOLIDADO-rodada-1.md`
+ commit `d02e9aa`: 5 CRÍTICO + 7 ALTO. Tema: F-B escrita contra
contrato PRÉ-FA-C1; saneamento F-A divergiu/quebrou ela.

**Descoberta crítica no review FB-C1 (tech-lead):** FB-C1 e FB-C3 estão
ACOPLADOS. A policy `authz_decisions_select` libera a cadeia pré-tenant
só com `app.usuario_id=''`, mas decisão pré-tenant autenticada tem
usuario_id setado → o helper de cadeia não leria o elo anterior → cadeia
authz pré-tenant bifurca. Viraram UMA frente (#11). Recomendação
preliminar: cadeia pré-tenant authz POR-USUÁRIO (não global). Análise +
3 bloqueantes em `auditorias/FB-C1-design-cadeia-compartilhada.md`
§Correções.

## Próximo passo (retomar)
1. **FB-C1+C3 conjunto** (#11): reabrir design contemplando cadeia
   pré-tenant authz por-usuário → review tech-lead → implementar helper
   compartilhado `registrar_em_cadeia` (algoritmo único) + sequencia +
   normalização resource JSON-safe + 5 testes + não-regressão T1-T8.
2. FB-C2 (#13 authz_public), FB-C4+C5 (#12 drill+cripto), ALTOs (#10).
3. Reauditar F-B rodada 2 (#14). Loop até zero CRÍTICO/ALTO.
4. Backlog Wave-A (#8), lint sweep (#7) — NÃO reabrem F-A/F-B.
5. F-B saneada → Marco 1 `clientes` definitivo → Marco 2.

## Fila de tarefas
TaskList: #11 FB-C1+C3 conjunto (PRÓXIMO — design reaberto), #12/#13
demais CRÍTICOs F-B, #10 ALTOs F-B, #14 reauditoria F-B r2, #8/#7
Wave-A. Consolidados em `docs/faseamento/auditorias/`.
