# 03 — Matriz de agentes (13 papéis)

> Cada agente tem `.claude/agents/<nome>.md` com escopo explícito. Violação de escopo = bloqueio por hook.
>
> **10 executores + 3 auditores externos** (estes últimos substituem humanos contratados — ver `16-agentes-auditores-externos.md`).

## Visão geral — Executores (internos)

| # | Agente | Mandato | Owner de |
|---|--------|---------|----------|
| 1 | **backend-api** | Auth, RBAC, workflows OS, emissão oficial, assinatura/QR, reemissão, sync server-side | `apps/api/**` |
| 2 | **regulator** | Interpreta DOQ-CGCRE, NIT-DICLA, Portaria 157/2022, ILAC P10/G8, RTM. Valida §9 e §16. | `packages/normative-rules/**`, `compliance/normative-packages/**` |
| 3 | **metrology-calc** | Engine de incerteza k=2, balanço, regra de decisão ILAC G8 | `packages/engine-uncertainty/**` |
| 4 | **web-ui** | Next.js SSR/SSG, wizard de revisão, portal, e-mails transacionais | `apps/web/**`, `apps/portal/**` |
| 5 | **android** | Kotlin, offline-first, SQLCipher, sync idempotente cliente | `apps/android/**` |
| 6 | **db-schema** | Postgres, multitenancy, audit log imutável, hash-chain, WORM | `packages/db/**`, `packages/audit-log/**` |
| 7 | **qa-acceptance** | Testes E2E por AC, fixtures, property tests, archiva evidência no dossiê | `evals/**`, `compliance/validation-dossier/**` |
| 8 | **lgpd-security** | Base jurídica, assinatura eletrônica, retenção, hardening audit, DSAR | co-owner `packages/audit-log/**`, `compliance/legal-opinions/**` |
| 9 | **copy-compliance** | Lint de claims regulatórios em site, portal, e-mails, docs comerciais | `packages/copy-lint/**`, `compliance/approved-claims.md` |
| 10 | **product-governance** | Gate de merge regulatório. Sem escrita em código. CODEOWNERS nas áreas sensíveis. | `compliance/release-norm/**` (só leitura em código) |

## Visão geral — Auditores externos (substituem humanos contratados)

Ver detalhamento completo em [`16-agentes-auditores-externos.md`](./16-agentes-auditores-externos.md).

| # | Agente | Mandato | Owner de |
|---|--------|---------|----------|
| 11 | **metrology-auditor** | Pré-auditoria ISO 17025/CGCRE. Simula auditor real. Bloqueia release se encontra não-conformidade. | `compliance/audits/metrology/**` |
| 12 | **legal-counsel** | Parecer jurídico-regulatório (LGPD, claims, contratos). Bloqueia release se detecta risco alto. | `compliance/audits/legal/**` |
| 13 | **senior-reviewer** | Code review sênior independente em áreas blocker. Bloqueia merge se detecta risco arquitetural/segurança. | `compliance/audits/code/**` |

**Regra dura para auditores**: auditor **nunca** edita o artefato que audita. Emite parecer; executor corrige e resubmete.

## Estrutura obrigatória de cada `.claude/agents/<nome>.md`

```yaml
---
name: <agente>
description: <uma linha>
model: sonnet | opus | haiku
tools: [Read, Edit, Write, Grep, Glob, Bash, ...]
---

## Mandato
<o que faz e o que NÃO faz>

## Specs de referência
- PRD §<n>
- /compliance/<arquivo>.md

## Paths permitidos (escrita)
- <glob>

## Paths bloqueados (leitura ok, escrita não)
- <glob>

## Hand-offs
- Quando precisar de X → delegar para agente Y
- Quando descobrir Z → escalar para product-governance
```

## Regras de colaboração

1. **Isolamento por ownership**: agente A não escreve em path de agente B. Violação detectada por hook `PreToolUse`.
2. **Cross-cutting** (ex.: mudança que afeta api + web + android): usar Agent Teams com file locking; nunca edição paralela descoordenada.
3. **`product-governance` é o único que pode revisar PR de qualquer outro agente**. Os demais revisam só no próprio escopo.
4. **Tool allowlist do orquestrador**: `Agent(backend-api, regulator, metrology-calc, web-ui, android, db-schema, qa-acceptance, lgpd-security, copy-compliance, product-governance, metrology-auditor, legal-counsel, senior-reviewer)`. Nenhum outro nome pode ser invocado.
5. **Separação de funções executor × auditor**: `regulator` não é auditado por si; `metrology-auditor` audita. `lgpd-security` não é auditado por si; `legal-counsel` audita. Dono do código não é auditado por si; `senior-reviewer` audita.

## Modelo recomendado por agente

- **Opus** (raciocínio complexo, normativo, auditoria): `regulator`, `metrology-calc`, `product-governance`, `metrology-auditor`, `legal-counsel`, `senior-reviewer`.
- **Sonnet** (engenharia geral): `backend-api`, `web-ui`, `android`, `db-schema`, `qa-acceptance`, `lgpd-security`.
- **Haiku** (varreduras baratas): `copy-compliance` em batch mode.
