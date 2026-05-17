# ARQUITETURA.md

> Este arquivo é **apenas um ponteiro**. A arquitetura detalhada está em `docs/arquitetura/`.

**Status:** ADR-0001 v2 (stack — Django + Flutter + PostgreSQL) aprovada como **CANDIDATA** (não final) em 17/05/2026 — sujeita a 3 portões de validação. Ver `docs/adr/0001-stack.md`.

**Histórico:** v1 (TS fullstack) reprovada pela 1ª auditoria de 10 agentes; v2 (Django + Flutter) pivotou aplicando critério "negócio vence"; 2ª auditoria validou direção MAS exigiu portões antes de cravar definitiva.

**3 portões:**
1. Discovery fechada (ICP + MVP-1 + 3 cartas de intenção)
2. 4 ADRs filhas escritas: ADR-0002 multi-tenancy ✏️ rascunho, ADR-0007 domain layer ✏️ rascunho, ADR-0008 fiscal pluggable ✏️ rascunho, ADR-0009 onde A3 assina ✏️ rascunho
3. Spike F-1 + 4 drills cronometrados + 5 ativos contratuais

## Localização da arquitetura detalhada

- `docs/arquitetura/overview.md` — code map, entry points, boundaries
- `docs/arquitetura/cross-cutting/` — 8 docs: erro, log, retry, timeout, idempotência, transação, auth-rbac, validação
- `docs/adr/0001-stack.md` ⭐ — stack escolhida
- `docs/adr/0002-multi-tenancy.md` — modelo de isolamento
- `docs/adr/0003-mobile-tecnico-campo.md` — modelo mobile
- `docs/comum/governanca-modelo-comum.md` — fronteira entre comum e específico de módulo
- `docs/comum/integracoes-inter-modulos.md` — contratos entre domínios/módulos
- `docs/comum/integracoes-externas/` — 1 doc por parceiro (SEFAZ, Pluggy/Belvo, Bling/Tiny, gateway, e-mail, WhatsApp)
- `docs/comum/isolamento-multi-tenant.md` — INV-TENANT-001 + SEC-TENANT-001
- `docs/seguranca/` — mcp-policy, agente-input-nao-confiavel, supply-chain, classificacao-dados

---

## Princípios arquiteturais (validos antes de stack)

1. **Modular** — cliente pode ativar/desativar módulos (assinatura por módulo).
2. **Multi-tenant** — vários clientes (assistências/laboratórios) como tenants SaaS.
3. **Founder is customer** — Roldão é o primeiro tenant; não inviabiliza modelo SaaS.
4. **Spec-as-source** (D2) — spec PT é a verdade; código segue a spec.
5. **Domínio antes de módulo** — agrupamento por domínio (Comercial, Operação, Financeiro, Metrologia, Suporte) precede módulo individual.

Stack-specific principles serão adicionados no ADR-0001.
