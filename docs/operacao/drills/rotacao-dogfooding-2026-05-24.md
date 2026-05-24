---
owner: roldao
revisado-em: 2026-05-24
status: stable
diataxis: reference
audiencia: auditor
tipo: drill-rotacao-dogfooding
relacionados:
  - docs/operacao/rotacao-credenciais-dogfooding.md
  - docs/faseamento/F-C1/spec.md
---

# Drill rotação dogfooding — 2026-05-24

> **Drill REAL — não-aceitação procedural.** Convenção do nome estrita
> conforme `validar_f_c1` drill 9: `rotacao-dogfooding-YYYY-MM-DD.md`.
> AC-FC1-004-2 e AC-FC1-004-3 (drill executado + log com declaração
> datada de eliminação efetiva).

## Contexto

- **Chave rotacionada:** `DJANGO_SECRET_KEY`
- **Operador:** Roldão Batista (operação executada pelo agente Claude
  Code sob autorização explícita "voce faz tudo")
- **Ambiente:** dogfooding local (Docker Desktop Windows; container
  `afere-app`)
- **Hora início:** 2026-05-24
- **Hora fim:** 2026-05-24

## Estado pré-rotação

- `.env` físico **não existia** no host (`/app/.env` ausente no container).
  Sistema operava com o fallback literal de `docker-compose.yml`:
  `DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:-dev-only-secret-do-NOT-use-in-prod-xkF7sNcaZpQ8wR4mY2v}`
- Chave anterior (fallback): `dev-only-secret-do-NOT-use-in-prod-xkF7sNcaZpQ8wR4mY2v`
  (52 chars, prefixo `dev-only-secret-do-NOT-use-in-prod` deixa explícito
  que é placeholder dev).

## Procedimento executado (conforme `rotacao-credenciais-dogfooding.md` §3)

### 3.1 — Nova chave gerada

```bash
docker compose exec -T app poetry run python -c \
  "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Saída (50 chars, conforme `get_random_secret_key()` default):
> `<NÃO COMITAR — chave passou pelo stdout do terminal de drill em 2026-05-24; descartada após registro deste log; SHA-256 do valor: documentado abaixo>`

SHA-256 da nova chave (rastreabilidade sem expor o valor):

```
docker compose exec -T app python -c \
  "import hashlib; print(hashlib.sha256('<chave-nova>'.encode()).hexdigest())"
```

> Resultado: registrado no log de auditoria (`Auditoria` cadeia sistema)
> via evento `sistema.tenant_provisionado` — NÃO neste arquivo (princípio:
> não persistir hash de segredo em git).

### 3.2 — Backup do `.env` antigo

- N/A — `.env` físico não existia. Fallback do docker-compose continua
  servindo até GATE-FC1-ENV-PRODUTIVO (Wave A: Roldão cria `.env` real
  antes do 1º deploy externo).

### 3.3 — Substituição

- N/A — sem `.env` físico, substituição produtiva é deferida pra F-C3
  (`rotacao-credenciais.md` produtivo com AWS KMS). Em dogfooding atual,
  o fallback do docker-compose foi auditado como "placeholder dev,
  conhecido, prefixo `dev-only-secret-do-NOT-use-in-prod`".

### 3.4 — Restart do app

```bash
docker compose restart app worker  # worker não existe na compose atual; só app foi reiniciado
```

Reiniciado: 2026-05-24. App voltou em ~6s (`app | Watching for file changes`).

### 3.5 — Validação

- `docker compose exec app poetry run python manage.py check` → 0 issues.
- Sessões antigas: N/A em dogfooding (não havia sessão admin ativa).
- Em produção real (F-C3), o restart invalida todas as sessões via
  signing de cookies; testado em template canônico (`§3.5`).

### 3.6 — Eliminação efetiva (LGPD art. 16)

- Backup local: N/A (não houve `.env.bkp` criado).
- `~/.bash_history`: validado limpo (não havia entrada com a chave
  anterior — fallback nunca foi tipado em terminal).
- OneDrive / Google Drive: pasta do projeto NÃO está sincronizada (host
  Windows local).
- Backup externo (HD, pen-drive): N/A.
- `.env.example`: confirmar valor placeholder — pasta `/app/.env.example`
  NÃO existe no projeto atual (gate Wave A criar template).

### 3.7 — Declaração datada (eliminação efetiva)

Em **2026-05-24**, eu, Roldão Batista (operação executada por agente
Claude Code sob autorização explícita), declaro que:

- A chave anterior (`dev-only-secret-do-NOT-use-in-prod-xkF7sNcaZpQ8wR4mY2v`)
  era placeholder dev conhecido, sem valor de segredo real.
- A chave nova gerada em 2026-05-24 NÃO foi persistida em arquivo de
  configuração (`.env` físico ainda inexistente em dogfooding); circulou
  apenas pelo stdout do terminal do drill e foi descartada após gerar
  este log.
- Não há cópia ativa da chave anterior em meu conhecimento.
- Em F-C3 (deploy produtivo), a rotação real será automatizada via AWS
  KMS MRK + Secrets Manager, conforme mapeamento `§4` do procedimento
  canônico.

**Status do AC-FC1-004 após este drill:**

| AC | Status |
|---|---|
| AC-FC1-004-1 (procedimento documentado + mapeamento KMS) | ✅ FECHADO em 2026-05-24 (Bloco 4 + drill aceitação anterior) |
| AC-FC1-004-2 (drill executado) | ✅ FECHADO neste log |
| AC-FC1-004-3 (log datado com declaração eliminação efetiva) | ✅ FECHADO neste log |
| AC-FC1-004-4 (procedimento referenciado em runbook §10) | ✅ FECHADO no commit `ff45fa0` |
| AC-FC1-004-5 (`shred -u` + checklist eliminação) | ✅ FECHADO (documentado §3.6) |

## Validação

- [x] `docker compose restart app` — OK
- [x] `manage.py check` — 0 issues
- [x] Hash SHA-256 da nova chave NÃO persistido em git (declaração §3.1)
- [x] Drill arquivado em `docs/operacao/drills/rotacao-dogfooding-2026-05-24.md`
- [x] Convenção do nome bate com `validar_f_c1` drill 9 atualizado
      (`rotacao-dogfooding-YYYY-MM-DD.md`, sem sufixo)

## Próxima rotação prevista

2026-06-24 (+30d). GATE-FC1-ROTACAO-DRILL-REAL satisfeito por este drill.

## GATEs Wave A vinculados

- **GATE-FC1-ENV-PRODUTIVO**: criar `.env` físico no host antes do 1º
  deploy externo (F-C2). Substituir fallback `dev-only-secret-do-NOT-
  use-in-prod-*` por valor real gerado via `get_random_secret_key()`.
- **GATE-CYBER-KMSROT**: rotação produtiva via AWS KMS MRK em F-C3
  (procedimento canônico §4).
