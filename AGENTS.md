# AGENTS.md — Kalibrium

> Arquivo canônico, lido por **Claude Code, OpenAI Codex CLI, Cursor, GitHub Copilot, Amp, Windsurf, Gemini CLI** (padrão aberto AGENTS.md — Linux Foundation).
>
> **Fonte de verdade.** Configurações específicas (`.claude/`, `.codex/`) espelham o que está aqui.

## 1. Produto

**Kalibrium** — plataforma metrológica de certificação de calibração (ISO/IEC 17025, Inmetro/Cgcre). Web (Next.js) + Android (Kotlin, offline-first) + backend único (Postgres). Multitenant. Emissão regulada com trilha imutável. Ver [`PRD.md`](./PRD.md) v1.8.

## 2. Princípios não-negociáveis

1. **Conformidade por arquitetura**: regras normativas automatizáveis são bloqueios duros, não recomendações.
2. **Spec-as-source**: toda feature começa em `specs/NNNN-slug.md`. Código que diverge da spec é bug.
3. **Estado fora do processo**: sessões de agente são efêmeras. Verdade vive em Git + Postgres + artefatos em `compliance/`.
4. **Budgets como feature**: caps de custo/tokens em `harness/11-budgets.md` são aplicados por hook.
5. **Done = AC verde + evidência arquivada**: não é opinião de revisor. Evidência em `compliance/validation-dossier/`.
6. **Fail-closed**: em dúvida, **parar** a emissão. Nunca assumir risco silencioso.

Detalhamento em [`harness/01-principios.md`](./harness/01-principios.md).

## 3. Estrutura do repositório

```
kalibrium/
├─ AGENTS.md                     ← este arquivo
├─ PRD.md                        ← requisitos (v1.8)
├─ harness/                      ← decisão arquitetural (16 arquivos)
├─ specs/                        ← spec-driven development por feature
├─ adr/                          ← decisões arquiteturais
├─ apps/
│  ├─ api/                       ← backend técnico (owner: backend-api)
│  ├─ web/                       ← Next.js back-office (owner: web-ui)
│  ├─ portal/                    ← Next.js portal do cliente (owner: web-ui)
│  └─ android/                   ← Kotlin offline-first (owner: android)
├─ packages/
│  ├─ engine-uncertainty/        ← owner: metrology-calc
│  ├─ normative-rules/           ← owner: regulator (consumida só por apps/api)
│  ├─ db/                        ← owner: db-schema
│  ├─ audit-log/                 ← owner: db-schema + lgpd-security
│  ├─ copy-lint/                 ← owner: copy-compliance
│  └─ contracts/                 ← tRPC/zod schemas compartilhados
├─ evals/                        ← testes (AC, regulatory, tenancy, sync, snapshots)
├─ compliance/                   ← governança, dossiê, runbooks, auditorias
├─ infra/                        ← IaC
├─ .claude/                      ← config específica do Claude Code
└─ .codex/                       ← config específica do Codex CLI
```

## 4. Agentes (13 papéis)

10 executores + 3 auditores externos. Detalhamento em [`harness/03-agentes.md`](./harness/03-agentes.md) e [`harness/16-agentes-auditores-externos.md`](./harness/16-agentes-auditores-externos.md).

| Executor | Owner de | | Auditor | Audita |
|----------|----------|---|---------|--------|
| backend-api | `apps/api/**` | | metrology-auditor | ISO 17025/CGCRE |
| regulator | `packages/normative-rules/**` | | legal-counsel | LGPD, claims, contratos |
| metrology-calc | `packages/engine-uncertainty/**` | | senior-reviewer | Código crítico |
| web-ui | `apps/web/**`, `apps/portal/**` | | | |
| android | `apps/android/**` | | | |
| db-schema | `packages/db/**`, `packages/audit-log/**` | | | |
| qa-acceptance | `evals/**`, `compliance/validation-dossier/**` | | | |
| lgpd-security | co-owner `packages/audit-log/**` | | | |
| copy-compliance | `packages/copy-lint/**` | | | |
| product-governance | `compliance/release-norm/**` | | | |

**Regra dura**: auditor nunca edita o que audita; executor nunca aprova o próprio PR em área crítica.

## 5. Regras duras de repositório

- Nunca `git push --force` em `main` ou em branches protegidas.
- Nunca `--no-verify` em commits.
- `compliance/**` só muda com PR + ADR.
- `PRD.md` só muda com aprovação de `product-governance`.
- Qualquer código em área crítica (`apps/api/src/domain/emission/**`, `audit/**`, `engine-uncertainty/**`, `normative-rules/**`, `audit-log/**`) aciona full regression (ver [`harness/14-verification-cascade.md`](./harness/14-verification-cascade.md) L4).

## 6. Pipeline de compliance (resumo)

- **Normative package versionado e assinado**: cada certificado grava o pacote normativo vigente. Ver [`harness/04-compliance-pipeline.md`](./harness/04-compliance-pipeline.md).
- **Dossiê de validação**: `compliance/validation-dossier/` com `requirements.yaml`, `traceability-matrix.yaml`, evidência por execução.
- **Guardrails**: 7 gates de multitenancy, audit log, WORM, ownership. Ver [`harness/05-guardrails.md`](./harness/05-guardrails.md).
- **Release-norm**: cada release produz `compliance/release-norm/<versao>.md` assinado por `product-governance` com pareceres PASS dos 3 auditores.

## 7. Operação com múltiplas ferramentas (Claude Code + Codex CLI)

Este projeto é **tool-agnóstico**. Ver [`harness/17-multi-tooling.md`](./harness/17-multi-tooling.md) para a estratégia completa.

**Regra simples de roteamento:**

| Tipo de tarefa | Ferramenta preferida |
|----------------|----------------------|
| Raciocínio regulatório profundo, épico novo, release de fatia, arquitetura, Agent Teams | **Claude Code** |
| Refactor mecânico, teste em lote, DevOps, backlog autônomo, cloud exec | **Codex CLI** |
| Code review crítico de área blocker | Ambos (dupla checagem) |

Qualquer uma das ferramentas segue o harness. Configs em `.claude/` e `.codex/` são **espelhos** deste AGENTS.md.

## 8. Limitações honestas

- Este harness **sustenta** a conformidade ISO/IEC 17025; não a substitui. Pessoas competentes, procedimentos válidos e padrões rastreáveis continuam sendo da organização emissora.
- Os 3 auditores agentes fazem **pré-auditoria**. Em 5 casos-limite (auditoria CGCRE real, processo, incidente LGPD, acidente metrológico, reclamação em órgão regulador) o sistema escala ao usuário com briefing pronto para contratar humano.
- Claims proibidos em [`harness/06-copy-lint.md`](./harness/06-copy-lint.md) — "100% conforme", "passa em qualquer auditoria", garantia de acreditação — são bloqueados por CI.

## 9. Como começar uma sessão

### Em Claude Code
```
cd kalibrium
claude
```
Claude Code lê `CLAUDE.md` → este `AGENTS.md` → `.claude/agents/*.md` → `.claude/settings.json`.

### Em Codex CLI
```
cd kalibrium
codex
```
Codex lê `AGENTS.md` diretamente → `.codex/config.toml` → `.codex/agents/*`.

Ambas sessões operam sobre o mesmo repo, mesmos guardrails, mesmos gates.

## 10. Referências

- [`PRD.md`](./PRD.md) — requisitos do produto
- [`harness/README.md`](./harness/README.md) — índice do design do harness (16 arquivos)
- [`harness/STATUS.md`](./harness/STATUS.md) — status de aprovação de cada decisão
