---
owner: roldao
revisado-em: 2026-05-23
status: stable
diataxis: how-to
audiencia: agente
relacionados:
  - docs/operacao/setup-local.md
  - REGRAS-INEGOCIAVEIS.md
  - AGENTS.md
---

# Runbook — operação dia-a-dia (estado atual)

> **Pra quê:** procedimento certo na hora certa. Estado atual: dogfooding local-only (sem deploy a servidor remoto — memória `project_deploy_so_quando_roldao_quiser`). Runbook de produção entra quando F-C2 fechar.

---

## 1. Subir o sistema (todos os dias)

Pré-requisitos: Docker Desktop rodando, repositório clonado, terminal Git Bash aberto na raiz do projeto.

```bash
docker compose up
```

**Esperado:** containers `app`, `db`, `worker` sobem. Django responde em `http://localhost:8000`. Postgres em `localhost:5432`.

**Saída esperada:** `app | Watching for file changes` indica que o reload está armado. Se o terminal travar em "Waiting for database", aguardar 30s — Postgres demora a primeira vez.

Para rodar em background (libera terminal):

```bash
docker compose up -d
docker compose logs -f app
```

---

## 2. Derrubar o sistema

Cenário A — pausar trabalho mantendo dados:

```bash
docker compose down
```

Cenário B — reset completo (apaga banco, perde dados):

```bash
docker compose down -v
```

> ⚠️ `-v` apaga o volume do Postgres. Só usar quando: (a) acabou um experimento de fixture e quer começar limpo, ou (b) suite de teste corrompeu estado. Confirmar com Roldão antes se há trabalho não-commitado.

---

## 3. Diagnóstico rápido — "alguma coisa não funciona"

Lista em ordem de "mais provável" → "menos provável":

### 3.1 Sistema não responde em `localhost:8000`

```bash
docker compose ps
```

Esperado: `app` com status `Up` e mapeamento `0.0.0.0:8000->8000/tcp`. Se diz `Exited`, ver logs:

```bash
docker compose logs --tail=100 app
```

Causas comuns:
- Migration nova sem aplicar → ver §6
- Erro de syntax em código novo → procurar `Traceback` no log
- Porta 8000 ocupada por outro processo → `docker compose down` + `netstat -ano | findstr :8000` no PowerShell pra ver quem está usando

### 3.2 Testes falhando localmente

```bash
docker compose exec app poetry run pytest -x --ff
```

Flags: `-x` para no primeiro erro; `--ff` (failed first) roda os que falharam antes primeiro.

Se um teste falha pela 1ª vez:
1. Ler a mensagem de erro inteira (não só a primeira linha).
2. Conferir se é regressão de algo recém-editado: `git diff` + `git log --oneline -5`.
3. Rodar SÓ o teste isolado: `pytest tests/path/to/test_xxx.py::test_caso -vv`.
4. NÃO mascarar (`skip`, `assertTrue(True)`, `@pytest.mark.xfail`) — REGRA #0 do CLAUDE.md.

### 3.3 Suite de hooks falhando

```bash
bash .claude/hooks/_test-runner.sh 2>&1 | tail -10
```

Esperado: `resumo: NNN ok, 0 falhas`. Se há falha, o output mostra qual caso e qual hook.

Se um hook está bloqueando edit legítimo, NÃO desativar — usar allowlist explícita (`# hook-name: skip -- <razão>`) e justificar.

**Modo rápido por filtro (iteração — desde Onda 2 plano-v2):**

```bash
bash .claude/hooks/_test-runner.sh WS          # só casos com ID começando em "WS"
bash .claude/hooks/_test-runner.sh prod-set    # só casos do hook prod-settings-check
```

Suite completa demora ~30-60s no Windows (cada caso forka bash+perl). Em iteração de UM hook, rodar só os casos dele economiza ~95% do tempo. **Antes de commit final** (com vários hooks tocados) rodar SEM filtro pra pegar regressões cross-hook.

### 3.4 Container `app` está vivo mas API retorna 500

```bash
docker compose exec app poetry run python manage.py check
docker compose exec app poetry run python manage.py showmigrations
```

Causa comum: migration aplicada mas Django settings divergente (DEBUG=False sem ALLOWED_HOSTS, banco do `migrator` divergente do `app_user`).

---

## 4. Aplicar mudança no código

### 4.1 Código Python puro (`src/**/*.py`)

Django roda com `--reload` no devcontainer e docker compose dev. Mudança em `.py` é refletida em segundos. Conferir log:

```bash
docker compose logs --tail=20 app
```

Esperado: `Watching for file changes with StatReloader` + `Performing system checks...` + `System check identified no issues`.

### 4.2 Mudança em dependência (`pyproject.toml`)

```bash
docker compose down
docker compose up --build
```

Rebuild da imagem do `app` é necessário porque `poetry install` roda na build.

### 4.3 Migration nova

```bash
docker compose exec app poetry run python manage.py makemigrations
docker compose exec app poetry run python manage.py migrate --database=migrator
```

> ⚠️ SEMPRE `--database=migrator`. O usuário `app_user` é `NOBYPASSRLS` e não consegue criar tabela (ADR-0002). O `migrator` é a única role com DDL.

Hook `migration-rls-check.sh` valida que migration que cria tabela com `tenant_id` declara `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY` na mesma migration (INV-TENANT-003).

### 4.4 Mudança em hook (`.claude/hooks/*.sh`)

1. Editar o hook.
2. `chmod +x .claude/hooks/seu-hook.sh` (Windows: o bit + x é simulado pelo Git Bash; isto é necessário).
3. Adicionar casos de teste em `.claude/hooks/_test-runner.sh`.
4. `bash .claude/hooks/_test-runner.sh` deve dar `0 falhas`.
5. Registrar em `.claude/settings.json` (PreToolUse — `Write|Edit`).

---

## 5. Suite de qualidade antes de commit

```bash
docker compose exec app poetry run ruff check .
docker compose exec app poetry run ruff format --check .
docker compose exec app poetry run mypy src config
docker compose exec app poetry run pytest
bash .claude/hooks/_test-runner.sh
```

Tudo deve passar. Se algo falha:
- Ruff: aplicar `ruff format .` (sem `--check`) e commitar.
- Mypy: corrigir tipos. NÃO usar `# type: ignore` sem comentário ≥10 chars (hook `anti-mascaramento` valida).
- Pytest: corrigir código. NÃO usar `@pytest.mark.skip` sem motivo (hook `anti-mascaramento` valida).
- _test-runner: ver §3.3.

---

## 6. Quando hook bloqueia um edit

O hook bloqueia com `exit 2` e mensagem em stderr. Ler a mensagem inteira — em geral indica:

1. **A regra violada** (`SEC-001`, `INV-TENANT-001`, etc).
2. **A allowlist disponível** (comentário inline ou skip de arquivo).
3. **Onde está documentada** (REGRAS-INEGOCIAVEIS.md, docs/seguranca/, etc).

**Sempre** tentar atender a regra primeiro. Allowlist com `skip` é último recurso e exige razão ≥10 chars descrevendo POR QUE. Razão ruim ("debugging", "fix later", "TODO") = drift.

Se o hook está com bug (false positive crônico), corrigir o hook — não desativar.

---

## 7. Sessão de agente IA travada

Sintomas: terminal não responde, comando rodando há > 5min sem output, Claude Code parece em loop.

Procedimento:
1. `Ctrl+C` no terminal (não dispara `block-destructive`).
2. Se subprocess travou, ver `docker compose ps` para confirmar containers OK.
3. Reset da sessão Claude Code: fechar e reabrir (perde contexto da sessão; histórico via memórias persistentes em `~/.claude/projects/...`).
4. Investigar causa: ler `.agent/CURRENT.md` para retomar do último estado conhecido.

---

## 8. Backup / Restore (dogfooding)

### Backup do volume Postgres dogfooding

```bash
docker compose exec db pg_dump -U postgres -d afere_dev > backup-$(date +%Y%m%d).sql
```

Arquivar em local seguro (NUNCA committar). Backup operacional real (B2 WORM por tenant com KMS) entra em F-C2 + Wave A.

### Restore para estado pré-experimento

```bash
docker compose down -v
docker compose up -d db
sleep 10
docker compose exec -T db psql -U postgres -d afere_dev < backup-YYYYMMDD.sql
docker compose up -d app worker
```

---

## 9. Rotação de credencial dogfooding

> **F-C1 P4 T-FC1-12** entregou o procedimento canônico expandido em
> `docs/operacao/rotacao-credenciais-dogfooding.md` (com mapeamento 1:1 →
> AWS KMS produtivo de F-C3 + checklist eliminação efetiva LGPD art. 16).

Resumo (ver doc canônico pro passo-a-passo completo):

1. Gerar nova chave (Django: `get_random_secret_key()`; HMAC: `openssl rand -hex 32`).
2. Backup do `.env` antigo (temporário — eliminado no passo 7).
3. Substituir no `.env` + bumpar `KEY_ID` quando aplicável (HMAC).
4. `docker compose restart app worker`.
5. Validar (`manage.py check`, sessões antigas inválidas, hash novo ≠ antigo).
6. **`shred -u`** no backup + checklist manual (history, OneDrive, backup local).
7. Arquivar drill em `docs/operacao/drills/rotacao-dogfooding-YYYY-MM-DD.md` com declaração datada de eliminação efetiva.

**Chaves cobertas** (5): `DJANGO_SECRET_KEY`, `PII_HASH_KEY` (+ID), `QR_HMAC_KEY` (+ID), `QR_IP_RATELIMIT_SALT`, `ADMIN_ACCESS_HASH_SALT` (F-C1).

Procedimento produtivo (KMS MRK, AWS): F-C3 (`GATE-CYBER-KMSROT`).

---

## 10. Próximos runbooks (a criar quando entrar a fase correspondente)

| Doc | Quando criar | Bloqueia |
|---|---|---|
| `deploy.md` | F-C3 (instrumentação + resiliência) | 1º deploy externo |
| `backup-restore.md` (produtivo B2 WORM) | F-C2 | 1º tenant externo |
| `dr-plan.md` (provedor caiu, RPO/RTO) | F-C2 + LGPD-3 (Onda 5 plano-v2) | 1º tenant externo |
| `observabilidade.md` | F-C2 | 1º deploy externo |
| `go-live-checklist.md` | Wave A | 1º cliente externo pago |
| `incidente-postmortem.md` | F-C3 | 1º SEV-0/SEV-1 |
| `multi-tenant-ops.md` | Wave A | 1º tenant externo |
| `rotacao-credenciais.md` (produtivo) | F-C1 | 1º deploy externo |
| `provisionamento.md` | F-C3 + Wave A | 1º deploy externo |
| `maintenance-windows.md` | Wave A | 1º cliente externo pago |
| `capacity-planning.md` | Wave B | quando passar de 3 tenants |
| `acionamento-agente.md` | Wave A | 1º watchdog produtivo |

---

## 11. Quem opera o quê (estado atual)

- **Roldão:** decisor final em incidente; aprovar mudança em REGRAS-INEGOCIAVEIS, constitution, AGENTS.md (paths protegidos por CODEOWNERS); rotacionar credencial; instalar ferramenta nova no host.
- **Subagente `tech-lead-saas-regulado`:** revisão arquitetural não-trivial; code review semanal de paths sensíveis.
- **Subagente `auditor-seguranca`:** bloqueia commit/merge se SEC-*/INV-TENANT-*/SEC-TENANT-* violado.
- **Subagente `auditor-conformidade-lgpd`:** revisa mudanças em PII; aprova allowlist em `seed-anti-pii-real` e `mass-assignment-check` por modelo sensível.
- **Outros 8 auditores Família 5:** bloqueiam pré-commit/pré-merge conforme catálogo em `docs/governanca/catalogo-auditores.md`.

---

## 12. Princípios de operação (vigentes hoje)

1. **Zero deploy a servidor remoto** até Roldão autorizar (memória `project_deploy_so_quando_roldao_quiser`).
2. **Toda mudança em REGRAS / constitution / AGENTS.md / `.claude/hooks/` / `.github/workflows/`** passa por CODEOWNERS antes de merge.
3. **Não declarar pronto sem rodar** — `_test-runner.sh` + `pytest` + `ruff` + `mypy` antes de commitar (memória `feedback_nao_declarar_pronto_sem_rodar`).
4. **Causa raiz, nunca sintoma** — teste falhou = problema no sistema (memória `feedback_resolver_nao_documentar`).
5. **Commits atômicos** — um propósito por commit (AGENTS §7).
6. **Stage seletivo** — `git add <arquivo>` por arquivo. Nunca `git add .` cego (AGENTS §7).
7. **Rollback é primeiro recurso** quando algo pega fogo — fix em produção é exceção (relevante em F-C3+).

---

## 13. Severidades (vigente para incidente de dogfooding hoje; produtivas em F-C3+)

| Severidade | Definição | Reação |
|---|---|---|
| SEV-0 | Vazamento cross-tenant; dado fiscal corrompido; KMS perdido | Parar trabalho; chamar Roldão; conter; postmortem ≤ 30 dias |
| SEV-1 | Módulo MVP-1 fora; certificado emitido errado | Conter em 30 min; postmortem ≤ 30 dias |
| SEV-2 | Funcionalidade degradada não-crítica | Próxima sessão de trabalho |
| SEV-3 | Cosmético; UX degrade | Próxima janela de manutenção |
