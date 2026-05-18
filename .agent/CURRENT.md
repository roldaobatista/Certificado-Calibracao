# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Fase/Marco/US.

**Fase:** Wave A · Marco 1 (módulo `clientes`) — **FECHADO** em 2026-05-18 (todas as 5 US verdes + 3 auditores Família 5 aprovaram).
**Modo:** AUTÔNOMO; ritual orquestrador OBRIGATÓRIO (memória `feedback_ritual_orquestrador`).

## Estado do módulo clientes (Wave A · Marco 1 — fechado)

| US | Tema | Status | Testes |
|---|---|---|---|
| US-CLI-001 | Cadastro PF/PJ + LGPD + evento Cliente.Criado | ✅ FECHADA | 8 |
| US-CLI-002 | Visão 360° + log acesso INV-013 | ✅ FECHADA | 7 |
| US-CLI-003 | Importação 1-clique CSV (preview + executar + relatório) | ✅ FECHADA | 39 |
| US-CLI-004 | Bloqueio manual + automático ADR-0015 | ✅ FECHADA | 15 |
| US-CLI-005 | Dedup manual wizard + soft-delete | ✅ FECHADA | 9 |

**Suite total: 207 passed + 2 skipped (1 ADR-0015 pendente + 1 antigo). Hooks: 103/103. Cobertura: 86.01%.**

## Auditores Família 5 — Marco 1 clientes (2026-05-18)

- **Qualidade**: PASS com 2 CONCERNS cosméticos (mypy ignores sem inline + cobertura importar 77%→endereçado).
- **Segurança**: CONCERNS com 1 FAIL CRÍTICO (hash de PII em audit sem salt por tenant) → **endereçado em commit 7c793e8**.
- **Produto**: PASS.

Trilha em `docs/governanca/trilha-auditoria-agentes.md`.

## Próximo passo (próxima sessão)

1. Decidir próximo módulo Wave A: candidatos `equipamentos` (stand-alone, base para OS/certificados) ou `orcamentos` (comercial natural).
2. Seguir ritual orquestrador: PRD do módulo → `/specify` (US) → `/plan` → review subagentes → `/tasks` → `/implement` → 3 auditores.

## Estado do sistema

- Containers `afere-db` + `afere-app` rodando.
- Banco `afere` + `test_afere` migrados até última migration (clientes.0013, audit.0007, tenant.0002).
- Para parar: `docker compose down`.

## ADRs pendentes para Wave A continuar

- ADR-0015 fluxo 3 (modo_suspensao no Tenant) — predicate `tenant_nao_suspenso` é stub até implementar.
- Procrastinate worker async — diferido pra Wave A real (importação síncrona valida no Marco 1).
- Parsers nativos Cali/Bling, Excel/XLSX — Wave A.
