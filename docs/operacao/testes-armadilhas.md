---
owner: roldao
revisado_em: 2026-05-29
proximo_review: 2026-08-29
status: stable
diataxis: how-to
audiencia: agente
relacionados:
  - docs/operacao/setup-local.md
  - tests/conftest.py
  - docker/
---

# Armadilhas do ambiente de teste — leia ANTES de mexer em pytest

> **Por que este arquivo existe:** a auditoria da máquina de dev (2026-05-29) mediu que estas 3 armadilhas já consumiram **5h15 num único dia** (24/05) só pra destravar os testes — zero produto entregue. O conhecimento morava **só na memória privada do agente Claude**, invisível pro Codex CLI e pra qualquer sessão nova. Agora é estado compartilhado do projeto (Constituição §1).
>
> **Princípio mestre:** se um teste falhar, é problema no sistema — corrija a causa raiz. NUNCA mascare (skip, assert vazio, cache-em-memória silencioso, `|| true`).

---

## Comando seguro do dia a dia

```bash
cd "/c/PROJETOS/Certificado de calibracao"

# Suite de API/integração — comando SEGURO (reaproveita o banco, não dropa, não cai em dev)
docker compose exec app poetry run pytest --no-cov --reuse-db

# Um arquivo específico
docker compose exec app poetry run pytest --no-cov --reuse-db tests/test_<modulo>.py

# Suite completa com cobertura (fim de fase — mais lento)
docker compose exec app poetry run pytest
```

**Regra de ouro:** no dia a dia use `--no-cov --reuse-db`. A cobertura completa fica para o portão de fim-de-fase.

---

## Armadilha 1 — NUNCA `--create-db` e NUNCA dropar `test_afere`

**O que acontece:** o banco de teste `test_afere` recebe extensões e permissões (grants) dos scripts de init do Docker — e esses scripts **só rodam quando o volume é criado do zero**. Se você dropar o banco ou usar `--create-db`, o pytest recria a casca **sem** as extensões → erro `function hmac() does not exist` (e parentes).

**Sintoma:** `function hmac(...) does not exist`, `extension "..." does not exist`, ou falha de permissão logo no setup.

**Correção:** use `--reuse-db` (reaproveita o banco com tudo dentro). Se realmente precisar recriar, recrie o **volume Docker** inteiro (`docker compose down -v && docker compose up`), não só o banco.

**Proibido:** `--create-db`, `-o addopts=""` (apaga o `--ds=test` do pyproject → o pytest cai no settings de **dev**, que não tem redis → `ModuleNotFoundError`).

---

## Armadilha 2 — OWNER de `test_afere` tem que ser `app_user` (não `app_migrator`)

**O que acontece:** o pytest-django percorre as conexões em ordem **alfabética**. `default` vem antes de `migrator`. Se o OWNER do banco de teste for `app_migrator`, a conexão `default` (que é `app_user`) tenta DROP+CREATE e quebra — ou pior, escreve no banco errado.

**Incidente real:** uma config de MIRROR fez o pytest **escrever no banco de DEV** → 733 tenants vazaram pro ambiente de teste.

**Correção:** o OWNER de `test_afere` é `app_user`. Confirme nos scripts de init em `docker/`. Nunca aponte a conexão `default` de teste pro `app_migrator`.

---

## Armadilha 3 — `TransactionTestCase` TRUNCA os dados-semente entre testes

**O que acontece:** `TransactionTestCase` (usado em testes que precisam de transação real) faz TRUNCATE de **todas** as tabelas entre cada teste — **incluindo os dados-semente** que vêm de migrations `RunPython` (ex: os 4 perfis de `authz_perfil`).

**Sintoma:** testes quebram em cascata por falta de dado-semente (incidente real: **197 testes** quebraram de uma vez).

**Correção:** o `tests/conftest.py` tem uma fixture `autouse` que detecta `authz_perfil` vazio e **re-aplica as migrations de semente** (via `importlib`) antes do teste. Se criar nova migration de dados-semente, **adicione-a ao catálogo da fixture** — senão o TRUNCATE a apaga e ela não volta.

> **Sentinela (planejado — item do plano de aceleração):** um teste que falha e diz exatamente qual migration de semente ficou de fora do catálogo, pra esta armadilha nunca mais reaparecer silenciosamente.

---

## Tabela-resumo

| Armadilha | Sintoma | Correção |
|---|---|---|
| `--create-db` / dropar test_afere | `hmac() does not exist`, extensão faltando | `--reuse-db`; recriar volume Docker, não o banco |
| `-o addopts=""` | `ModuleNotFoundError` (redis) — caiu em dev | nunca sobrescrever addopts; o `--ds=test` é obrigatório |
| OWNER errado (app_migrator) | DROP/CREATE indevido; vazou pra dev | OWNER de test_afere = app_user |
| TransactionTestCase TRUNCA semente | 197 fails por falta de dado-semente | fixture autouse re-aplica semente; novas migrations entram no catálogo |
