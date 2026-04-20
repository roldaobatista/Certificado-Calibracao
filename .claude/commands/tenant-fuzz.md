---
description: Dispara fuzz cross-tenant para detectar vazamento entre tenants (Gate 5)
---

Roda a suíte de fuzz em `evals/tenancy/` para garantir que não há leak cross-tenant.

Passos:

1. Cria 2 tenants sintéticos com dados distintos.
2. Gera N=500 payloads aleatórios combinando: queries, IDs, tokens, headers.
3. Para cada payload, tenta ler/escrever no tenant errado via todas as rotas públicas.
4. Sucesso = 100% das tentativas bloqueadas por RLS + RBAC.
5. Falha = issue blocker aberta + release suspenso; escala para `db-schema` + `backend-api`.

Se `$ARGUMENTS` for fornecido, limitar a uma área (`emission`, `audit`, `sync`). Sem argumento, rodar full.

Ver `harness/05-guardrails.md` Gate 5.
