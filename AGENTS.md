# AGENTS.md — Aferê

> Arquivo canônico, lido por **Claude Code, OpenAI Codex CLI, Cursor, GitHub Copilot, Amp, Windsurf, Gemini CLI** (padrão aberto AGENTS.md — Linux Foundation).
>
> **Fonte de verdade.** Configurações específicas (`.claude/`, `.codex/`) espelham o que está aqui.

## 1. Produto

**Aferê** — plataforma metrológica de certificação de calibração (ISO/IEC 17025, Inmetro/Cgcre). Web (Next.js) + Android (Kotlin, offline-first) + backend único (Postgres). Multitenant. Emissão regulada com trilha imutável. Ver [`PRD.md`](./PRD.md) v1.8.

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
afere/
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

### Primeira vez após clone

```bash
pnpm install
bash tools/install-hooks.sh            # git hooks canônicos (copy-lint + ownership-lint)
bash tools/install-mcp.sh both         # MCP servers em Claude e Codex
```

Detalhe de MCP servers em [`tools/setup-mcp.md`](./tools/setup-mcp.md).

### Em Claude Code

```bash
claude
```

Claude Code lê `CLAUDE.md` → este `AGENTS.md` → `.claude/agents/*.md` → `.claude/settings.json`.

### Em Codex CLI

```bash
codex
```

Codex lê `AGENTS.md` diretamente → `.codex/config.toml` → `.codex/agents/*`.

Ambas sessões operam sobre o mesmo repo, mesmos guardrails, mesmos gates — `.githooks/pre-commit` é acionado pelo git **independente** da CLI (fail-closed em copy-lint, ownership-lint e demais gates).

### Sanidade entre sessões

```bash
pnpm check:drift       # valida .claude/agents ↔ .codex/agents em sincronia
pnpm check:all         # typecheck + check:drift
```

## 10. Como finalizar, commitar e publicar

O usuário principal não programa. Quando ele disser "pode fazer tudo", "continua", "finaliza", "faz o commit", "manda para main" ou equivalente, o agente deve levar a tarefa até Git/GitHub, desde que os gates estejam verdes.

### Antes do commit

```bash
git status --short
pnpm check:all
pnpm test:tenancy              # obrigatório quando tocar db, tenancy, audit, compliance ou área crítica
bash .githooks/pre-commit
```

Regras:

- Nunca usar `--no-verify`.
- Nunca usar `git push --force` ou `git push --force-with-lease` em `main`.
- Se teste ou hook falhar, corrigir antes de commitar. Não empurrar falha para o usuário.
- Se o hook falhar no Windows/WSL por `node` ausente, corrigir o hook/ambiente; não pular gate. Os hooks usam `.claude/hooks/lib.sh` para cair para `pnpm.cmd` quando necessário.
- Mensagem de commit deve ser curta e convencional, por exemplo `feat: implement compliance guardrail tooling`, `fix: enforce tenant sql lint`, `docs: document agent workflow`.

### Commit padrão

```bash
git add -A
git commit -m "<tipo>: <resumo>"
```

Após commitar, confirmar:

```bash
git status --short
git log --oneline -1
```

### Publicação padrão deste repositório

A branch padrão do GitHub é `main`. Se o usuário pedir para "mandar para main", "subir", "publicar" ou "fazer push", usar push direto sem force:

```bash
git checkout main
git pull --ff-only origin main
git push origin main
```

Se o trabalho foi feito em outra branch e o usuário pediu explicitamente push para `main`, publicar o `HEAD` atual em `main` sem force:

```bash
git push origin HEAD:main
git checkout -B main origin/main
```

Se houver divergência remota, não resolver com force. Fazer `git fetch origin`, inspecionar o histórico e preferir merge/rebase normal com nova verificação completa.

### Pull Request

Usar PR quando o usuário pedir revisão, quando houver exigência explícita de PR/ADR, ou quando a mudança alterar `compliance/**` de forma regulatória sensível sem autorização direta para push em `main`.

```bash
git push -u origin <branch>
gh pr create --title "<titulo>" --body "<resumo e testes>"
```

### Depois do push

Confirmar remoto e branch padrão:

```bash
git ls-remote --heads origin main
git ls-remote --symref origin HEAD
git status -sb
```

Responder ao usuário com commit, branch, verificações executadas e qualquer limitação honesta.

## 11. Handoff para `/resume`

Ao encerrar uma sessão relevante, o agente deve deixar um registro em:

```text
compliance/sessions-log/<YYYY-MM-DD>/<tool>-<session-id>.jsonl
```

Esse handoff é obrigatório quando houver commit, push, mudança em `compliance/**`, mudança de harness ou decisão arquitetural.

O registro deve conter:

- branch local/remota e último commit;
- comandos de verificação executados;
- resumo do que foi feito;
- limitações honestas;
- próximos passos em ordem;
- instrução explícita para o próximo agente ler `AGENTS.md`, `harness/STATUS.md` e o handoff antes de alterar código.

Se não houver ID real de sessão, usar `codex-handoff` ou `claude-handoff`. O objetivo é que `/resume` tenha contexto suficiente sem depender da memória efêmera do agente.

## 12. Referências

- [`PRD.md`](./PRD.md) — requisitos do produto
- [`harness/README.md`](./harness/README.md) — índice do design do harness (16 arquivos)
- [`harness/STATUS.md`](./harness/STATUS.md) — status de aprovação de cada decisão
