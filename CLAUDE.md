# Contrato Claude Code — projeto

@AGENTS.md

> **Fase:** Wave A em curso. Frente ativa: `.agent/CURRENT.md`. Contagens: `docs/governanca/STATUS-GERADO.md`.

---

## Idioma

Comunicar em **Português (Brasil)** por padrão.

---

## Estado do ambiente

Stack ativa: Python 3.12 + Django 5.0 + DRF + PostgreSQL 16 + Poetry + Docker Compose local.

**Arquivos canônicos:**
- `AGENTS.md` — produto/arquitetura (importado acima)
- `REGRAS-INEGOCIAVEIS.md` — IDs `INV-*`, `TST-*`, `SEC-*`
- `CONTRIBUTING.md` — fluxo do agente
- `.specify/memory/constitution.md` — princípios
- `docs/adr/INDICE.md` — índice completo de ADRs
- `docs/governanca/STATUS-GERADO.md` — contagens geradas automaticamente

**`.claude/` (versionado):**
- `settings.json` — permissões + hooks
- `hooks/` — lista: `ls .claude/hooks/`; orquestrador: `_test-runner.sh`
- `agents/` — 4 subagentes: `tech-lead-saas-regulado`, `advogado-saas-regulado`, `corretora-seguros-saas`, `consultor-rbc-iso17025`
- `output-styles/pt-br-conciso.md`
- `skills/`, `commands/`, `rules/` — vazios por escolha

Mapa completo em `docs/INDICE.md`.

---

## Notas sobre Windows + Git Bash

- `jq` **não vem por padrão** no Git Bash. Hooks usam `perl -MJSON::PP` para parsear JSON. `sed` puro vaza (quebra na primeira aspa escapada).
- Path com espaços (`C:\PROJETOS\Certificado de calibracao`) — sempre `"${CLAUDE_PROJECT_DIR}"` com aspas.
- `chmod +x` não é confiável no Windows — invocar hooks via `bash script.sh`.
- Sandboxing nativo não suportado (só WSL2).
- Testar hooks: `bash .claude/hooks/_test-runner.sh` (ou `bash .claude/hooks/_test-runner.sh <nome-hook>` para filtrar).
- Verificar denylist de contagens: `bash scripts/status-projeto.sh --check`.
- Hooks de invariante rodam no pré-commit via `.githooks/pre-commit` + manifest `.claude/hooks/pre-commit-manifest.tsv`; write-time é só anti-desastre. Ativar após clonar: `git config core.hooksPath .githooks`.
