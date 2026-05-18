# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Fase/Marco/US.

**Fase:** SANEAMENTO da fundação ANTES do Marco 2. Estratégia Roldão 2026-05-18:
auditar F-A → corrigir → reauditar (loop) → F-B mesmo loop → resolver tudo →
só então fechar Marco 1 (`clientes`) → Marco 2 (`equipamentos`).
**Modo:** AUTÔNOMO.

## Onde paramos (2026-05-18 — sessão encerrada pelo Roldão)

### Fechado e commitado (verde)
- SANEA-06 (suite roda no padrão, 215→), SANEA-03 (anti-injection CSV),
  SANEA-02 (hash PII via HMAC server-side), SANEA-01 (advisory lock atômico).
- **FA-A4** (rede contra migration mentirosa) — commit `1fcbfff`. 217 passed.
- Auditoria F-A rodada 1: consolidado `docs/faseamento/auditorias/F-A-CONSOLIDADO-rodada-1.md`.
  Design FA-C1 fechado pelo tech-lead: `FA-C1-design-hash-chain.md`.

### EM ANDAMENTO — FA-C1 (hash chain por-tenant) — NÃO commitado, NÃO pronto
Estado: **222 passed / 3 failed** na suite. Arquivos alterados (working tree):
`connection.py` (GUC `app.modo_sistema`), `audit/services.py` (cadeia por-tenant
+ lock 2-args + Q-02 fix), `audit/models.py` (campo `sequencia` db_default),
`audit/migrations/0009_auditoria_sequencia.py` (novo), `multitenant/migrations/
0004_audit_hash_chain_por_tenant.py` (novo — policies), `validar_f_a.py`,
`tests/test_audit_chain_e2e.py`, `tests/test_audit_cadeia_por_tenant.py` (novo, T1-T8).

**3 testes a resolver (hipóteses pra retomar rápido):**
1. `test_t3_cadeia_sistema_tenant_null_encadeia` — passa ISOLADO (14/14), falha
   na suite completa → poluição de estado entre testes (outro teste deixa
   linha tenant=NULL ou contexto). Investigar isolamento/ordem.
2+3. `test_isolamento_cross_tenant.py::test_trigger_pg_bloqueia_update/delete_via_raw_sql`
   — FA-C1 trocou policies UPDATE/DELETE da auditoria pra `USING(false)`; agora
   a POLICY bloqueia ANTES do trigger, com erro diferente do que o teste
   asserta. Conserto = ajustar o teste pra aceitar bloqueio por policy OU
   trigger (imutabilidade ficou MAIS forte: policy + trigger). NÃO é bug de
   produção.

### test_afere
Recriado limpo manualmente (drop+create owner app_migrator + migrate
--database=migrator + grants do 01-roles.sh replicados). Migrations todas
aplicadas incl. audit.0009 + multitenant.0004.

## Próximo passo (retomar)
Resolver os 3 testes (hipóteses acima) → suite verde → commitar FA-C1 →
seguir loop F-A: FA-A2 (template RLS único — clientes sem fail-loud, já
investigado: clientes/0002 usa current_setting cru), FA-A1+M2 (PII_HASH_KEY
dedicada), FA-A5+M1 (drill robusto + números), FA-M3 → reauditar F-A rodada 2.

## Fila de tarefas
Ver TaskList (#22 FA-C1 in_progress; #24-27 demais FA-*; #21 F-B; #12-19 SANEA Marco1 parqueados).
