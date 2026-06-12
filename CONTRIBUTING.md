# CONTRIBUTING.md — fluxo do agente

> Este documento descreve o **fluxo de trabalho do AGENTE de IA** (não de humano contribuidor externo). Roldão é o dono não-técnico; contribuidores são agentes (Claude Code, Codex CLI) + **10 auditores Família 5** (catálogo em `docs/governanca/catalogo-auditores.md`) + 1 transversal Tier 4 `bus-integrity` + 4 humanos-substitutos (`.claude/agents/`).

---

## Fluxo obrigatório (em ordem)

1. **Ler constituição** — `.specify/memory/constitution.md` (6 princípios + 5 decisões fundadoras).
2. **Ler regras críticas** — `REGRAS-INEGOCIAVEIS.md` (IDs `INV-`, `INV-TENANT-`, `TST-`, `SEC-`).
3. **Ler estado atual** — `.agent/SESSION.md` + `.agent/CURRENT.md`.
4. **Ler spec da feature** — `docs/dominios/<dom>/modulos/<mod>/specs/<NNN-feature>/spec.md`.
5. **Ler plan** — `.../plan.md`.
6. **Implementar tarefa atômica (5–15 min)** — uma `T<MOD>NNN` por vez do `tasks.md`.
7. **Auditor roda** (catalogo-auditores.md define qual + trigger).
8. **Commit** com mensagem citando IDs: `feat(US-CRM-001): T-CRM-003 — implementa filtro de funil`.
9. **Atualizar `CHANGELOG.md`** na seção `[Unreleased]`.

---

## Regras de commit

> **Conflito reconciliado (2026-05-27):** AGENTS.md §7 diz "padrão livre — decisão deferida". Na prática, os commits dos 7 marcos fechados usam **Conventional Commits relaxado** — prefixo (`feat:`, `fix:`, `docs:`, `chore:`) com escopo livre (ex.: `fix(M4 P5 batch S4+S5-restante): ...`). Adotar esse padrão de fato; decisão formal via ADR fica como Wave A.

- `feat:` nova feature
- `fix:` correção
- `refactor:` reorganização sem mudança de comportamento
- `docs:` doc
- `test:` teste
- `chore:` infra/ferramenta
- `compliance:` mudança regulatória (LGPD, ISO, fiscal)
- Cada commit cita ≥1 ID (`US-`, `T-`, `INV-`, `ADR-`, `SEC-`).
- Commits atômicos: 1 propósito por commit. Nunca misturar `feat + fix + refactor`.
- `Co-Authored-By: Claude <noreply@anthropic.com>` quando agente gera o commit.

---

## PROIBIÇÕES (enforced por hook)

- `--no-verify`, `--skip-*`, `--ignore-*` em commits.
- `@ts-ignore`, `@eslint-disable` sem justificativa documentada.
- `skip()`, `assertTrue(true)`, baselines pra esconder erro de teste.
- Edição direta de `.claude/hooks/`, `.claude/settings.json`, `.specify/memory/constitution.md`, `REGRAS-INEGOCIAVEIS.md`, `docs/conformidade/`, `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/` — exigem aprovação humana via CODEOWNERS.
- Push direto em pastas críticas listadas em `.github/CODEOWNERS`.
- Query SQL/ORM sem `tenant_id` no WHERE (INV-TENANT-001).

---

## Disciplina pós-auditoria de cerimônia (2026-06-12)

Aprovação integral do Roldão — pacotes B e D. Duas regras operacionais aplicadas a partir desta data:

### R4 — Crescimento de hooks: dispatcher consolidado

Verificação nova de invariante de módulo **nasce como check de pré-commit no dispatcher consolidado** (`scripts/dispatcher-precommit.sh` — criado na frente técnica do Pacote A). Hook write-time (executado a cada edição de arquivo) é reservado para anti-desastre:
- `block-destructive` — operações destrutivas irreversíveis
- `secrets-scanner` — segredos/credenciais no código
- `anti-mascaramento` — bypass silencioso de teste
- `mock-in-production` — mock em path de produção real
- `seed-anti-pii-real` — PII real em seeds
- `csv-safety-import` — CSV com dados reais sem validação

Todos os demais checks de invariante de domínio pertencem ao pré-commit, não ao write-time. Não criar hook write-time novo sem aprovação explícita do Roldão.

### R16 — Fim dos commits isolados de estado

**Proibido commit isolado contendo somente `.agent/CURRENT.md`.** A atualização de estado do agente entra no commit da própria fatia de trabalho (junto com os arquivos de código/doc que a fatia modificou). Commits de handoff puro eram 12,4% do histórico (113 de 913 commits) sem valor de código — não se repetem.

---

## Como atualizar este arquivo

Mudança no fluxo → ADR formal + atualizar este arquivo + atualizar `docs/roteamento-dual.md`.
