# Aferê (nome provisório)

> ERP completo para empresas de assistência técnica + calibração metrológica. Diferencial: emissão de certificado ISO/IEC 17025 (RBC/INMETRO).

---

## Status atual (Wave A em curso)

- **Foundations F-A, F-B, F-C1 FECHADAS** — multi-tenant + RLS + auth + RBAC + hardening
- **Marcos 1-4 FECHADOS** — clientes, equipamentos, ordens de serviço, calibração ISO 17025
- **Bloco metrologia Wave A COMPLETO** — padrões, escopos-cmc, procedimentos, certificados, licenças-acreditações
- **Módulos operacionais entregues** — fiscal/NFS-e, configuracoes-sistema, produtos-pecas-servicos
- **Frente ativa** — `precificacao` (parcial, stub custo) — ver `.agent/CURRENT.md`
- **Stack:** Python 3.12 + Django 5.0 + DRF + PostgreSQL 16 + Poetry + Docker Compose
- **LICENSE:** BUSL-1.1 (parecer subagente `advogado-saas-regulado`; confirmação OAB humano pendente)
- **ADRs vivas e frias:** `docs/adr/INDICE.md`

> **Contagens reais** (hooks / casos de teste / ADRs / INVs) são geradas automaticamente por `scripts/status-projeto.sh` — ver `docs/governanca/STATUS-GERADO.md`. Verificar denylist: `bash scripts/status-projeto.sh --check`.

> **Detalhamento vivo:** `.agent/CURRENT.md` (frente em curso + próximos passos).

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
