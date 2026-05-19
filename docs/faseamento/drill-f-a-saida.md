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

> **STATUS 2026-05-18 — F-A FECHADA COM RESSALVAS, EM SANEAMENTO (rodada 1→2).** A auditoria de 10 lentes (`auditorias/F-A-CONSOLIDADO-rodada-1.md`) achou débitos CRÍTICO/ALTO. Loop de saneamento em curso: FA-A4/FA-C1/FA-A2/FA-A1+FA-M2/FA-A5+FA-M1 fechados; FA-M3 + reauditoria rodada 2 pendentes. F-A **não** está fechada definitivamente — só fecha quando a rodada 2 vier sem CRÍTICO/ALTO. Este drill foi **endurecido** pelo FA-A5 (era fraco: 1 tenant/5 linhas/só feliz, 50×100, p99 1 tenant).
>
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
  [OK ] Hooks _test-runner verdes: resumo: 113 ok, 0 falhas
  [OK ] Roles app_user/app_migrator NOBYPASSRLS: ambas NOBYPASSRLS + NOSUPERUSER
  [OK ] Trigger auditoria_anti_* existe: triggers: ['auditoria_anti_delete', 'auditoria_anti_update']
  [OK ] Hash chain do audit trail integro: 3 tenants intercalados OK; adulteracao detectada (1 elos); 80 inserts concorrentes -> 84 elos integros
  [OK ] p99 query operacional < 200ms: 3 tenants x 500 = 1500 linhas: p50=3.0ms p99=7.2ms (lim 200ms)

F-A drill: 5/5 criterios automaveis OK. Falta validar 2 criterios operacionais (memoria + auditor).
```

Se algum falhar, o comando sai com erro e diz qual.

### Versão rápida (sem benchmark, ~10s)

```bash
docker compose exec app poetry run python manage.py validar_f_a --quick
```

---

## Rodar fuzzing cross-tenant (50 threads × 1000 queries)

Critério §2 L94: **ZERO vazamento** em fuzzing concorrente (50×1000 —
FA-A5 corrigiu o drill fraco anterior que era 50×100).

```bash
docker compose exec app poetry run pytest \
  tests/test_isolamento_cross_tenant.py \
  -m "tenant_isolation and slow" -v
```

Saída esperada:
```
test_50_threads_x_1000_queries_zero_vazamento PASSED  [100%]
=== 1 passed in ~145s ===
```

Se falhar com `VAZAMENTO CROSS-TENANT DETECTADO`, é **SEV-0** — para tudo + abrir postmortem.

---

## Critério 6: Drill manual de restore PG (cronometrado, < 30min)

**✅ EXECUTADO 2026-05-18 — 2,52 segundos total (limite 30 min, folga 700x)**

Como rodado autonomamente pelo agente no Docker do PC:

1. Populou DB com 3 tenants × 3000 linhas auditoria = 9000 linhas (volume não-trivial).
2. **Dump:** `pg_dump -F c -d afere` → 0,84s, 1 MiB.
3. **Drop + Create + Restore + Reaplicar grants:** 1,68s.
4. Validou pós-restore com `validar_f_a --quick` → 5/5 OK (trigger anti-mutation sobreviveu, RLS íntegro, hash chain válido).

**Notas:**
- Usado `pg_dump`/`pg_restore` (vem com PG). `pgBackRest` formal com WAL archiving + retenção fica pra quando autorizar deploy.
- 12.020 linhas restauradas (inclui populadas + stale de testes anteriores).
- Comando reproduzível em `src/infrastructure/multitenant/management/commands/popular_drill.py`.

Anotado em `docs/governanca/trilha-auditoria-agentes.md` (a confirmar quando o doc for criado).

---

## Critério 7: Métricas operacionais do período

Avaliados **na operação**, não em código. Coletados automaticamente pelo management
command `relatorio_operacao_fa`:

```bash
docker compose exec app poetry run python manage.py relatorio_operacao_fa
```

| Métrica | Limite | Como medir |
|---|---|---|
| Intervenções de código do Roldão | ≤ 2 / semana em média ao longo das 4–6 semanas | git log: commits sem `Co-Authored-By: Claude` no body |
| Bugs SEV-1 no período | ≤ 3 totais | git log com `--grep=SEV-1` |
| Gasto LLM | ≤ R$ 1.500 nas 4–6 semanas | Console Anthropic — verificação manual (TBD) |
| Auditor de Segurança vetou? | Nenhum veto nos últimos 14 dias da fase | git log com `--grep="veto auditor"` |

**Estado em 2026-05-18 (1 dia de F-A, 0,1 / 4 semanas observadas):**

- ✅ Intervenções Roldão: **0** (limite ≤ 2/sem)
- ✅ Bugs SEV-1: **0** (limite ≤ 3)
- 🟡 Gasto LLM: **TBD** — Roldão verifica no console Anthropic
- ✅ Vetos auditor segurança: **0** nos últimos 14 dias

**Decisão pendente do Roldão:** aceitar evidência empírica do período atual (tudo dentro
do limite, mas só 1 dia observado) ou aguardar 4 semanas literais de operação.

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
