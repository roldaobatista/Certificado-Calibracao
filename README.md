# Aferê (nome provisório)

> ERP completo para empresas de assistência técnica + calibração metrológica. Diferencial: emissão de certificado ISO/IEC 17025 (RBC/INMETRO).

---

## Status atual (2026-05-23)

- **Foundation F-A FECHADA** (multi-tenant + RLS + audit imutável + 4 entidades núcleo) — 10/10 auditores Família 5 PASS ZERO CRÍTICO/ALTO/MÉDIO
- **Foundation F-B FECHADA** (auth + RBAC + AuthorizationProvider + MFA TOTP) — 10/10 PASS ZERO C/A/M
- **Marco 1 `clientes` FECHADO** (Wave A) — cadastro PF/PJ, visão 360, importação CSV, bloqueio, dedup
- **Marco 2 `equipamentos` FECHADO** (Wave A) — equipamentos, RT, vigência, competências por grandeza
- **Marco 3 `os` em curso** — spec FORWARD em P1; consumers + sagas OS Fase 4 entregues (T-OS-029..039)
- **Foundation F-C reservada** (3 sub-foundations sequenciais: F-C1 hardening, F-C2 observabilidade, F-C3 instrumentação+resiliência) — bloqueia Wave A; pré-requisito do 1º deploy externo
- **Stack ativa:** Python 3.12 + Django 5.0 + DRF + PostgreSQL 16 + Poetry + Docker Compose
- **LICENSE:** BUSL-1.1 aplicada na Onda 0 do plano-v2 (parecer subagente `advogado-saas-regulado`; confirmação OAB humano pendente)
- **57 ADRs aceitas/propostas + 6 reservadas** (ADR-0057..0062 — a11y, ProductAnalytics, LLMProvider, EmailTemplate, DPO, Devcontainer; ADR-0056 = numeração OS Marco 3 P3, já aceita)
- **Suite:** 621 testes verdes em 37 min; 32 hooks ativos; 207/207 casos no `_test-runner.sh`

> Detalhamento vivo: `docs/faseamento-foundation-waves.md` + `.agent/CURRENT.md`.

---

## ⚠️ Nome provisório

"Aferê" é nome de trabalho. Decisão final adiada até antes de: comprar domínio, escrever código com slug `afere`, primeiro cliente externo, INPI.

---

## Mapa rápido

| Você é... | Comece por |
|---|---|
| **Dono / não-técnico** | `docs/painel-do-dono.md` → `docs/MAPA-DO-DONO.md` → `docs/tutoriais/dono/` |
| **Agente de IA (Claude / Codex)** | `CLAUDE.md` → `AGENTS.md` → `REGRAS-INEGOCIAVEIS.md` → `docs/INDICE.md` |
| **Auditor humano** | `docs/INDICE.md` → `docs/governanca/` → `docs/conformidade/` |
| **Curioso técnico** | `docs/documentos-do-projeto.md` (mapa completo) → `docs/arquitetura/` |

---

## Como subir localmente

Pré-requisitos: Docker Desktop + Git + (opcional) VS Code com Dev Containers.

Passo-a-passo objetivo: `docs/operacao/setup-local.md`.

Comandos básicos (resumo — ver AGENTS.md §6 para a tabela completa):

| Operação | Comando |
|---|---|
| Subir | `docker compose up` |
| Derrubar (mantém dados) | `docker compose down` |
| Rodar testes | `docker compose exec app poetry run pytest` |
| Lint + format | `poetry run ruff check . && poetry run ruff format .` |
| Type-check | `poetry run mypy src config` |
| Testar hooks | `bash .claude/hooks/_test-runner.sh` |

---

## Estrutura do projeto

Ver `docs/documentos-do-projeto.md` (mapa de docs) e `docs/INDICE.md` (sitemap navegável).

---

## Como contribuir

Este projeto é 100% desenvolvido por agentes de IA. Roldão é o dono não-técnico + primeiro cliente (dogfooding na Balanças Solution). Ver `CONTRIBUTING.md` (fluxo do agente) e `docs/governanca/limites-autonomia.md` (quando agente escala pra humano).

---

## Licença

Business Source License 1.1 (BUSL-1.1) — ver `LICENSE`. Texto oficial em https://mariadb.com/bsl11/.

- Change Date: 2030-05-23
- Change License: Apache 2.0
- Aplicada por decisão da Onda 0 do plano-v2 de saneamento (parecer subagente `advogado-saas-regulado` em 2026-05-23; confirmação por advogado humano licenciado pendente antes do 1º cliente externo pago).
