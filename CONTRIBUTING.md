# CONTRIBUTING.md — fluxo do agente

> Este documento descreve o **fluxo de trabalho do AGENTE de IA** (não de humano contribuidor externo). Roldão é o dono não-técnico; contribuidores são agentes (Claude Code, Codex CLI) + 3 auditores-agentes.

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

## Regras de commit (Conventional Commits)

- `feat:` nova feature
- `fix:` correção
- `refactor:` reorganização sem mudança de comportamento
- `docs:` doc
- `test:` teste
- `chore:` infra/ferramenta
- `compliance:` mudança regulatória (LGPD, ISO, fiscal)
- Cada commit cita ≥1 ID (`US-`, `T-`, `INV-`, `ADR-`, `SEC-`).
- Commits atômicos: 1 propósito por commit. Nunca misturar `feat + fix + refactor`.

---

## PROIBIÇÕES (enforced por hook)

- `--no-verify`, `--skip-*`, `--ignore-*` em commits.
- `@ts-ignore`, `@eslint-disable` sem justificativa documentada.
- `skip()`, `assertTrue(true)`, baselines pra esconder erro de teste.
- Edição direta de `.claude/hooks/`, `.claude/settings.json`, `.specify/memory/constitution.md`, `REGRAS-INEGOCIAVEIS.md`, `docs/conformidade/`, `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/` — exigem aprovação humana via CODEOWNERS.
- Push direto em pastas críticas listadas em `.github/CODEOWNERS`.
- Query SQL/ORM sem `tenant_id` no WHERE (INV-TENANT-001).

---

## Como atualizar este arquivo

Mudança no fluxo → ADR formal + atualizar este arquivo + atualizar `docs/roteamento-dual.md`.
