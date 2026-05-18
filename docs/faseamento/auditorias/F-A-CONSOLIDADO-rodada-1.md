---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
tipo: consolidado-auditoria-F-A
rodada: 1
---

# F-A — Consolidado da auditoria 10 lentes (rodada 1)

> Estratégia Roldão 2026-05-18: auditar a fundação de baixo pra cima (F-A → F-B → Marco 1), loop auditar→corrigir→reauditar até passar. Esta é a rodada 1 de F-A. 10 lentes especializadas + **verificação de realidade (Regra #0)** que resolveu contradições entre pareceres.

## Verificação de realidade — contradições resolvidas (Regra #0)

Vários pareceres divergiram ou erraram por leitura parcial. Verificado no banco/suite real:

| Alegação de parecer | Realidade verificada | Veredito |
|---|---|---|
| "auditoria não tem RLS" (Lente 5) | `pg_class`: auditoria relrowsecurity=t, relforcerowsecurity=t + 4 policies (ins/sel/upd/del) | **REFUTADO** — tem RLS |
| "domain/application não existem, ADR-0007 não cumprida" (Lente 1) | `src/domain/` (authz, comercial, shared) e `src/application/` (comercial) existem e populados | **REFUTADO** — existe (magro, ok pra F-A) |
| "app_user sem CREATE → produção pode estar sem RLS" (Lentes 1/9/10) | `has_schema_privilege('app_user','public','CREATE')` = TRUE; banco `afere` real tem 32 policies + 6 triggers íntegros (Lente 8 provou) | **REFUTADO** — causa-raiz errada; prod íntegra |
| "suite 214 passed + 1 FAILED (teste de isolamento de cliente)" (Lente 8) | `pytest` real: **215 passed, 0 failed, 0 skipped** | **REFUTADO** — suite verde |
| "bug de migration = catástrofe, prod pode estar sem proteção" (6 lentes) | Causa real: `router.py:38 allow_migrate` só executa no alias `migrator`; rodar `migrate` no alias errado marca aplicada sem executar. Caminho oficial (docker-compose `--database=migrator`) funciona; banco íntegro | **REBAIXADO** — foot-gun real, não catástrofe de prod |

Lição: auditoria multi-agente converge mas também amplifica relato impreciso do sintoma. Verificar o estado real antes de consertar é inegociável.

## Débitos REAIS confirmados (pós-verificação)

| ID | Débito | Gravidade | Origem (lentes) | Conserto |
|---|---|---|---|---|
| **FA-C1** | Hash chain é cadeia GLOBAL, não por-tenant. `verificar_integridade_cadeia` assume cadeia única e roda sob RLS → quebra/falso-positivo com >1 tenant. Ordenação por `timestamp` não-monotônico (colisão µs sob lock) → reordena elos. Q-02: verificador usa `hash_anterior_esperado = linha.hash_atual` SALVO → adulteração no meio só acusa 1 elo; propriedade "quebra todas as seguintes" é FALSA. Detecção de adulteração NUNCA testada (só caminho feliz, 1 tenant). | **CRÍTICO** | 1,2,3,5,6,7,9 (convergência massiva) | SANEA-04 reentra com escopo F-A. Design tech-lead fechado: cadeia por-tenant + cadeia sistema (NULL) + **sequência monotônica** (BIGSERIAL/seq por-tenant, não timestamp) + verificação por-tenant escopada + corrigir Q-02 (recalcular encadeado) + REJEITAR SECURITY DEFINER e REJEITAR BYPASSRLS (viola INV-TENANT-004). Lock por-tenant junto. Testes T1–T6 + adulteração no meio + elo faltante obrigatórios. |
| **FA-A1** | `PII_HASH_KEY` deriva de `SECRET_KEY` por sha256 se env vazia. Rotacionar SECRET_KEY (prática de segurança) invalida TODOS os hashes de PII retroativos → impossível responder ANPD "quem viu CPF X em data Y". | **ALTO** | 1,2,5 | Chave dedicada `PII_HASH_KEY` obrigatória sem default em prod (ImproperlyConfigured se ausente); versionar (`v1:`) + guardar key_id ao lado do hash p/ rotação sem perder histórico. |
| **FA-A2** | `clientes/migrations/0002_rls_policies.py` usa template RLS hardcoded com `current_setting('app.tenant_ids')` CRU, SEM `require_tenant_ctx()` fail-loud (divergente do multitenant/0002 que migrou pra fail-loud). clientes sem fail-loud = degrada pra "vê nada" em contexto vazio em vez de RAISE — furo de robustez de isolamento. | **ALTO** | 10 (D3) | Extrair template único `src/infrastructure/multitenant/rls_templates.py` com `require_tenant_ctx()`; clientes importa; migration nova regenera policies de `cliente` com fail-loud. |
| **FA-A3** | Advisory lock GLOBAL único serializa toda auditoria de TODOS os tenants num ponto. Gargalo + ponto único de falha sistêmica. | **ALTO** | 1,2,7,9 | Lock por-tenant `pg_advisory_xact_lock(hashtext(tenant_id::text))`; key reservada p/ cadeia NULL. Resolver junto com FA-C1. |
| **FA-A4** | Foot-gun de migration: rodar `migrate` no alias errado (sem `--database=migrator`) marca aplicada SEM executar o SQL (allow_migrate=False pula operação mas grava registro). `AGENTS.md:111` documenta o comando ERRADO (sem `--database`). | **ALTO** | 9,10 (causa-raiz corrigida pós-verificação) | (a) corrigir AGENTS.md:111 → `migrate --database=migrator`; (b) wrapper/command que ABORTA se `current_user != app_migrator` OU se allow_migrate vai pular tudo; (c) hook/teste `test_migrations_persistem.py`: pós-migrate, assertar via `pg_policies`/`pg_proc`/`pg_trigger` que objetos das RunSQL F-A existem fisicamente. |
| **FA-A5** | Critérios de saída F-A declarados verdes com drill fraco: hash chain validada com 1 tenant/5 linhas (§2 exige fuzzing); fuzzing cross-tenant rodou 50×100 não 50×1000 (§2); p99 mediu 1 tenant sequencial, não 10k linhas × 50 tenants. F-A "FECHADA" prematura. | **ALTO** | 3,4,6 | Drill robusto: ≥3 tenants intercalados + verificação por-tenant + injeção de elo faltante (exigir detecção) + concorrência; fuzzing 50×1000; benchmark multi-tenant em escala. Status F-A → "FECHADA COM RESSALVAS / em saneamento". |
| **FA-M1** | Drift de números: AGENTS.md "295 passed + 3 skipped / 88 / 103 / 86.01%" vs real **215 passed, 0 skipped / 16 hooks / 113 casos runner / 85.96%**. Label hardcoded "88/88" em `validar_f_a.py:7,61`. Status "F-A FECHADA 5/5" contradiz SANEA-04 (mesmo dia, stable). | **MÉDIO** | 4,8 | Sincronizar AGENTS.md + CLAUDE.md + validar_f_a.py + drill-f-a-saida.md com números verificados. (Estende SANEA-10.) |
| **FA-M2** | `prod.py` placeholder sem hardening obrigatório (PII_HASH_KEY/SECRET_KEY dedicadas, cookies seguros, HSTS). Gate de deploy ausente. | **MÉDIO** | 5 | `prod.py` falha duro se faltar segredo dedicado; ativar hardening; gate antes de dado real. Liga com FA-A1. |
| **FA-M3** | Higiene: `context.py limpar_contexto()` sem token (armadilha plantada); duplicação template RLS (FA-A2); `registrar_auditoria` god-function (lock+leitura+cálculo+persistência). | **MÉDIO** | 1,10 | Remover/consertar limpar_contexto; template único (FA-A2); separar `_obter_hash_anterior()` ao mexer em FA-C1. |

## Refutados (NÃO tratar — alarme falso, registrar pra não retrabalhar)

- auditoria sem RLS (tem). domain/application inexistentes (existem). produção sem RLS (íntegra, 32 policies). suite com teste falhando (215 verde). "migrate mente em prod catastroficamente" (foot-gun de alias, caminho oficial ok).

## Plano do loop (rodada 1 → conserto → rodada 2)

Ordem de conserto (causa-raiz, sem mascarar):
1. **FA-A4** primeiro (salvaguarda de migration + doc) — sem isso não confio nos consertos seguintes que usam migration.
2. **FA-C1 + FA-A3** juntos (hash chain por-tenant + sequência monotônica + lock por-tenant + Q-02 + cadeia sistema) — é o SANEA-04 com escopo correto; maior peça.
3. **FA-A2** (template RLS único + fail-loud em clientes).
4. **FA-A1 + FA-M2** (PII_HASH_KEY dedicada + prod hardening).
5. **FA-A5 + FA-M1** (drill robusto + sincronizar números/status).
6. **FA-M3** (higiene).
Depois: reauditar F-A (rodada 2) com as mesmas 10 lentes. Loop até zero CRÍTICO/ALTO. Só então F-B.
