# Aferê (nome provisório)

> ERP completo para empresas de assistência técnica + calibração metrológica. Diferencial: emissão de certificado ISO/IEC 17025 (RBC/INMETRO).

---

## Status atual (2026-05-27)

- **Foundation F-A FECHADA** (multi-tenant + RLS + audit imutável + 4 entidades núcleo) — 10/10 auditores Família 5 PASS ZERO CRÍTICO/ALTO/MÉDIO
- **Foundation F-B FECHADA** (auth + RBAC + AuthorizationProvider + MFA TOTP) — 10/10 PASS ZERO C/A/M
- **Marco 1 `clientes` FECHADO** (Wave A) — cadastro PF/PJ, visão 360, importação CSV, bloqueio, dedup
- **Marco 2 `equipamentos` FECHADO** (Wave A) — equipamentos, RT, vigência, competências por grandeza
- **Foundation F-C1 FECHADA** — hardening (admin, prod-settings, webhook-out, break-glass U2F)
- **Marco 3 `ordens_servico` FECHADO 2026-05-25** — OS com Atividades (ADR-0023), saga compensação, sync mobile (ADR-0027), append-only WORM
- **Marco 4 `metrologia/calibracao` FECHADO 2026-05-27** — ISO 17025 (recepção, configuração, leituras, NC, subcontratação, hash-chain WORM ADR-0064/0065, fail-open lazy ADR-0066)
- **Foundation F-C2/F-C3 reservadas** (observabilidade + instrumentação+resiliência) — pré-requisito do 1º deploy externo
- **Stack ativa:** Python 3.12 + Django 5.0 + DRF + PostgreSQL 16 + Poetry + Docker Compose
- **LICENSE:** BUSL-1.1 aplicada na Onda 0 do plano-v2 (parecer subagente `advogado-saas-regulado`; confirmação OAB humano pendente)
- **61 ADRs aceitas/propostas** (0000..0058 + 0062..0066) — ADR-0064/0065/0066 do Marco 4; ADR-0063 do Marco 3
- **Suite:** pytest M4 chave 629/629 verde em ~27s; pytest geral 905/0/0 (último full run 2026-05-24); 48 hooks ativos; 379/379 casos no `_test-runner.sh`

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
