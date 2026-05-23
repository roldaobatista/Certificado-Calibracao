---
owner: roldao
revisado-em: 2026-05-22
proximo-review: 2026-08-22
status: draft
diataxis: reference
audiencia: agente
fase: Foundation F-A — débitos
tipo: debitos-tecnicos
relacionados:
  - docs/faseamento/F-A/tasks-saneamento.md
  - docs/faseamento/F-A/auditoria-familia5.md
  - docs/comum/eventos/acesso-dados-cliente-registrado.md
  - docs/adr/0013-pricing-composicional-billing-saas.md
  - docs/adr/0015-lifecycle-tenant.md
---

# Foundation F-A — débitos técnicos (BAIXOs rastreados)

> **Para que serve:** lista fechada de débitos técnicos **BAIXOs** identificados na auditoria Onda 2 (Auditor 1). BAIXO não bloqueia fechamento (INV-RITUAL-001), mas precisa ficar visível para não virar dívida invisível. Cada item tem dono, ticket-alvo e marco para resolução.
>
> **Origem:** Auditor 1 — Resolvedor 2/10 do plano "consertar 147 achados", Onda 2 (2026-05-22).
>
> **Como ler:** cada `DT-FA-NN` é um débito rastreável. "Resolvido" exige PR/commit + remoção da linha (não basta marcar `feito`).

---

## Lista canônica

| ID | Origem | Título | Próxima ação | Marco-alvo | Estado |
|----|--------|--------|--------------|-----------|--------|
| DT-FA-01 | F-A-B1 | `JanelaVigencia` ausente em `Tenant` | Retrofit em Wave A (onboarding/lifecycle) — adicionar campos `vigencia_inicio` + `vigencia_fim` + `revogado_em` + `motivo_revogacao` na entidade `Tenant` (migration + VO + teste). ADR-0030 já cobre o padrão. | Wave A — `tenant-lifecycle` (ADR-0015) | rastreado |
| DT-FA-02 | F-A-B2 | Duplicação `acao` + `event_name` no envelope outbox | Manter `acao` por compat M1/M2 durante 1 release; depois Marco 3 OS remover `acao` e deixar só `event_name`. Ticket: criar `T-WA-OUTBOX-REMOVE-ACAO` antes do Marco 3 fechar. | Marco 3 OS pós-fechamento (Wave A) | rastreado |
| DT-FA-03 | F-A-B3 | `OutboxNaoImplementado` exception morta | Classe permanece em `src/infrastructure/audit/event_helpers.py` por compat com testes legados. Avaliar remoção após auditoria de imports em Wave A Marco 3 (`grep -r OutboxNaoImplementado src/ tests/`). Se zero call-sites — remover. | Wave A Marco 3 (revisão dead-code) | rastreado |
| DT-FA-04 | F-A-B4 | `Tenant.plano` enum origem | Definição do enum + transições vem do módulo `billing-saas` (ADR-0013 pricing composicional). F-A não declara enum próprio. Quando billing-saas entrar Wave B, adicionar FK ou referência canônica. | Wave B — billing-saas (ADR-0013) | rastreado |
| DT-FA-05 | F-A-M2 (deriva) | Glossário PT-EN da Foundation no ADR-0037 (Onda 1) | Garantir que ADR-0037 (criação responsabilidade Onda 1) cubra o vocabulário F-A: tenant_id, audit_trail, hash chain, RLS, KMS MRK, crypto-shredding, NOBYPASSRLS, GUC (Grand Unified Configuration), outbox, causation_id, correlation_id, idempotência. **Não criar glossário aqui** — apenas garantir cobertura. | Onda 1 (paralela) entrega ADR-0037 | rastreado |

---

## Política

- BAIXO **não** bloqueia fechamento de fase / marco / story (INV-RITUAL-001). Só CRÍTICO/ALTO/MÉDIO bloqueia.
- BAIXO rastreado sem dono + marco-alvo vira "decorativo" — é proibido por INV-RITUAL-001 (override só do Roldão).
- Resolução de débito exige PR + remoção da linha da tabela acima (não apenas marca "feito"). Hook `ritual-gate-check.sh` valida.

---

## Referências

- `docs/faseamento/F-A/tasks-saneamento.md` — ALTOs+MÉDIOs (irmão deste arquivo)
- `docs/adr/0030-vigencia-temporal-canonica.md` — JanelaVigencia (padrão para DT-FA-01)
- `docs/adr/0013-pricing-composicional-billing-saas.md` — enum Plano (origem para DT-FA-04)
- `REGRAS-INEGOCIAVEIS.md` — INV-RITUAL-001
