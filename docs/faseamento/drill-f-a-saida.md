---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: stable
diataxis: how-to
audiencia: dono
relacionados:
  - docs/faseamento-foundation-waves.md
  - docs/adr/0001-stack.md
  - docs/adr/0002-multi-tenancy.md
  - src/infrastructure/multitenant/management/commands/validar_f_a.py
---

# Drill de saída — Foundation F-A

> **Pra que serve:** F-A só fecha (e Foundation F-B só começa) quando os 7 critérios abaixo estiverem todos verdes. Este doc lista cada critério + como rodar.
>
> **Quando rodar:** ao final das 4–6 semanas da F-A, antes de Roldão autorizar passar pra F-B.

---

## 5 critérios automáveis (1 comando)

Com o `docker compose up` rodando em outro terminal, executar:

```bash
cd "/c/PROJETOS/Certificado de calibracao"
docker compose exec app poetry run python manage.py validar_f_a
```

Vai aparecer algo tipo:

```
[1/5] Hooks _test-runner...
[2/5] Roles NOBYPASSRLS...
[3/5] Trigger anti-mutation...
[4/5] Hash chain...
[5/5] Benchmark p99 (pode demorar)...

===== RESUMO DRILL F-A =====
  [OK ] Hooks 88/88 verdes: resumo: 88 ok, 0 falhas
  [OK ] Roles app_user/app_migrator NOBYPASSRLS: ambas NOBYPASSRLS + NOSUPERUSER
  [OK ] Trigger auditoria_anti_* existe: triggers: ['auditoria_anti_delete', 'auditoria_anti_update']
  [OK ] Hash chain do audit trail integro: 5 linhas verificadas, 0 quebras
  [OK ] p99 query operacional < 200ms: p50=4.2ms p99=18.7ms (limite 200ms)

F-A drill: 5/5 criterios automaveis OK. Falta validar 2 criterios operacionais (memoria + auditor).
```

Se algum falhar, o comando sai com erro e diz qual.

### Versão rápida (sem benchmark, ~10s)

```bash
docker compose exec app poetry run python manage.py validar_f_a --quick
```

---

## Rodar fuzzing cross-tenant (50 threads × 100 queries)

Critério: **ZERO vazamento** em fuzzing concorrente.

```bash
docker compose exec app poetry run pytest \
  tests/test_isolamento_cross_tenant.py \
  -m "tenant_isolation and slow" -v
```

Saída esperada:
```
test_50_threads_x_100_queries_zero_vazamento PASSED  [100%]
=== 1 passed in 18.4s ===
```

Se falhar com `VAZAMENTO CROSS-TENANT DETECTADO`, é **SEV-0** — para tudo + abrir postmortem.

---

## Critério 6: Drill manual de restore PG (cronometrado, < 30min)

Este precisa ser feito **uma vez** durante a F-A. Não é automável.

1. Em outro container/máquina, instalar `pgBackRest`.
2. Configurar `/etc/pgbackrest.conf` apontando pro `db` do docker-compose.
3. Executar backup full: `pgbackrest --stanza=afere backup`.
4. Dropar o banco no container atual: `docker compose exec db psql -U postgres -c "DROP DATABASE afere;"`.
5. Iniciar cronômetro.
6. Restaurar: `pgbackrest --stanza=afere restore`.
7. Parar cronômetro quando `docker compose exec app poetry run python manage.py validar_f_a --quick` voltar 5/5.

Cronômetro **< 30min** = passou. Anotar tempo em `docs/governanca/trilha-auditoria-agentes.md`.

---

## Critério 7: Métricas operacionais do período

Avaliados **na operação**, não em código. Cada um vira linha no `painel-do-dono.md`:

| Métrica | Limite | Como medir |
|---|---|---|
| Intervenções de código do Roldão | ≤ 2 / semana em média ao longo das 4–6 semanas | Contar commits cuja mensagem cita "ajuste manual Roldão" ou trocas de direção que ele teve que pedir |
| Bugs SEV-1 no período | ≤ 3 totais | Contar entries em `docs/governanca/trilha-auditoria-agentes.md` marcadas SEV-1 |
| Gasto LLM | ≤ R$ 1.500 nas 4–6 semanas | Console Anthropic + console OpenAI somados |
| Auditor de Segurança vetou? | Nenhum veto nos últimos 14 dias da fase | Logs do hook autz-check + revisões do auditor |

---

## Se algum critério reprovar

**NÃO joga código fora** (memória `feedback_sem_codigo_descartavel`). A regra é **mudar estratégia mantendo o código**:

| Critério reprovado | Estratégia |
|---|---|
| Hooks falham | Investigar + corrigir hook (não desabilitar) |
| NOBYPASSRLS quebrado | Re-aplicar SQL `01-roles.sh`, drill outra vez |
| Trigger ausente | Re-rodar migration `0002_trigger_anti_mutation` |
| Hash chain quebra | Investigar adulteração; rodar `verificar_integridade_cadeia()` com `limit=None` pra achar o elo |
| p99 > 200ms | Avaliar índices, CockroachDB ou Citus (mantém o modelo, troca o motor) |
| Fuzzing vaza | SEV-0 → postmortem → revisar policies RLS |
| Restore > 30min | Avaliar pgBackRest com S3 paralelo, ou esperar Wave A |
| Roldão > 2 interv/sem | Disparar plano B (tech-lead consultivo R$ 8–15k/mês) — código F-A permanece |

---

## Após drill verde

1. Atualizar `docs/faseamento-foundation-waves.md` §10 (histórico) com linha "F-A fechada em DD/MM/2026, lições aprendidas".
2. Mudar status do frontmatter pra `stable`.
3. Atualizar `AGENTS.md` §11 — ADR-0001 vira ✅ aceita (não mais candidata; Portão 2+3 fechados).
4. Atualizar `.agent/CURRENT.md` — fase passa pra Foundation F-B.
5. Commit `feat(F-A): drill verde 5/7 critérios — F-A FECHADA`.
6. Esperar autorização do Roldão pra arrancar F-B.
