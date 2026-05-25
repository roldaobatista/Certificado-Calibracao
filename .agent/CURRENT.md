# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + M3 OS FECHADAS. **M4 calibracao P3 ENTREGUE (2026-05-25).**
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-25)

- pytest geral: **905/0/0** em 26min (último run 2026-05-24).
- Hooks `_test-runner.sh`: **312/312** verdes / **42 hooks ativos**.
- ruff/mypy: limpos nos paths novos.

## M4 calibracao — P3 entregue (matriz reconciliação + tasks.md)

P3 do ritual Spec Kit completo em 3 commits hoje:

- `b1c1d6a` — ADR-0065 nova (concorrência calibração — UNIQUE composto + CAS + advisory lock) + retrofit ADR-0024 (6 zonas ILAC G8 + PFA/PRA + AceiteRegraDecisao) + retrofit ADR-0063 (Opção A lazy — predicate em 3 use cases pós-config) + 24 INVs CAL novos em REGRAS-INEGOCIAVEIS.md.
- `e8c4126` — spec.md §16 absorve 10 BLOQUEANTE + 23 MÉDIO dos 4 reviews + PRD §11 com 11 ACs novos + US-CAL-018 nova (reclamação CDC art. 26). Status spec.md + prd.md draft → stable.
- (este commit) — matriz-reconciliacao.md (zero conflito PRD ↔ spec ↔ plan ↔ ADRs ↔ REGRAS) + tasks.md com 160 T-CAL-NNN em 10 fases (Fase 1 migrations 25 / Fase 2 domain 20 / Fase 3 motor §3.3 15 / Fase 4 predicates+authz 15 / Fase 5 use cases 30 / Fase 6 queries 8 / Fase 7 jobs 9 / Fase 8 views REST 14 / Fase 9 hooks novos 8 / Fase 10 regressões+drill 16) + 14 tarefas P3.5 paralelas (minutas OAB + matrizes CGCRE + ADR-0028 rev 3 + DPIA).

## Decisões cravadas (P2 → P3)

- D-M4-1: GUM Decimal + Monte Carlo NumPy ✓
- D-M4-2: ADR-0063 Opção A lazy ✓
- D-M4-3, D-M4-4, D-M4-5: sem previsão de contratação → agente cria minutas/matrizes preliminares com selos REQUER {OAB,CGCRE,SUSEP} HUMANO.

## Próxima fatia

**P4 (`/implement`) — Fase 1 migrations (T-CAL-001..025):** começar pela DDL completa M4 com 19 tabelas + UNIQUE índices + triggers imutabilidade + RLS policies + migration cross-marco M3 plugando `AtividadeDaOS.grandeza` (ADR-0063 Opção A). Sequência sugerida: Fase 1 → Fase 2 (domain) → Fase 3 (motor §3.3) → Fase 4..10. **Estimativa:** 2-3 semanas agente.

**Paralelizável (P3.5 — não bloqueia P4 dogfooding):** 14 tarefas T-CAL-P35-* (minutas canônicas OAB + matrizes técnicas CGCRE + ADR-0028 rev 3 + DPIA-calibracao). Bloqueia 1º tenant externo pago.

## Pendências Wave A rastreadas (33 GATEs novos M4 — somam aos herdados)

GATE-CAL-* (12 RBC + 8 advogado + 3 tech-lead + 1 matrizes-CGCRE) + GATE-SEG-* (9 corretora) = 33 GATEs novos M4 + GATE-OS-* (~20 M3) + GATE-CYBER-BREAKGLASS-U2F-ENFORCE + GATE-HMAC-RETROFIT-MARCO-2-3 + GATE-KMS-IAM-LOCK + GATE-HMAC-DRILL + GATE-SEG-BPT-1 (emergencial dogfooding).
