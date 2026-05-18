---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
frente: FA-A2
revisor: tech-lead-saas-regulado
veredito: APROVA COM CORREÇÕES (absorvidas — ver §Correções absorvidas)
---

# FA-A2 — Design: template RLS único + fail-loud em clientes

> Núcleo multi-tenant/RLS + migration (código sensível, CODEOWNERS). Estado real verificado antes do design (Regra #0).

## Estado real verificado

- `clientes/migrations/0002_rls_policies.py` cria 4 policies com `current_setting('app.tenant_ids')` **CRU** (SELECT/UPDATE/DELETE) e INSERT `WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid)`.
- `multitenant/migrations/0002_fail_loud_e_flag_global.py` já migrou `auditoria` para `require_tenant_ctx()` (RAISE 42501 se `app.tenant_ids` vazio/nulo). Não tocou no INSERT (manteve `active_tenant_id`).
- `connection.py:42-44` faz `RESET app.tenant_ids` no checkout do pool. Em contexto vazio, `current_setting('app.tenant_ids')` cru → `''` → `string_to_array('',',') = {''}` → não casa UUID → **0 linhas silenciosas** (degrada para "vê nada", NÃO RAISE). É o furo de robustez do FA-A2.
- Banco real (`test_afere`): 4 policies de `clientes` confirmadas no estado cru.
- `require_tenant_ctx()` (função PL/pgSQL) já existe em produção via multitenant/0002.

## Decisão de design

1. **Módulo único `src/infrastructure/multitenant/rls_templates.py`** — fonte única do SQL de policies de isolamento por tenant. Funções puras Python que devolvem string SQL:
   - `policies_isolamento_tenant(tabela: str) -> str` — gera as 4 policies (`<tabela>_tenant_isolation_{select,update,delete,insert}`). SELECT/UPDATE/DELETE usam `require_tenant_ctx()` (fail-loud). INSERT mantém `WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid)` — **idêntico ao precedente auditoria/feature_flags do multitenant/0002**; não escopo-creep para `require_active_tenant()` (decisão consolidada FA-A2 fala só em `require_tenant_ctx()`).
   - `reverse_policies_isolamento_tenant(tabela: str) -> str` — DROP das 4 + recria forma CRUA (rollback seguro para o estado pré-FA-A2).
   - `drop_policies_isolamento_tenant(tabela: str) -> str` — só DROP (uso interno do forward: DROP-then-CREATE idempotente).
2. **Migration nova `clientes/0014_rls_fail_loud.py`**:
   - forward: `drop` das 4 policies cruas + `policies_isolamento_tenant("clientes")` (fail-loud).
   - reverse: `reverse_policies_isolamento_tenant("clientes")` (volta ao cru — rollback não regride segurança a ponto de quebrar, só remove o fail-loud).
   - Headers obrigatórios: `# rls-policy:` (tabela já tem RLS habilitado no 0002; só recria policies — declarar `# rls-policy: external 0002`) + `# tests-coverage:` apontando teste happy+unhappy.
   - depende de `("clientes", "0013_*")` (última migration de clientes — confirmar nome exato no implement).
3. **FA-M3 dedup**: o template novo é a fonte única. O `clientes/0002` fica como histórico (não reescrever migration aplicada); migrations futuras de qualquer tabela com `tenant_id` importam de `rls_templates.py`. (Fechamento do dedup é tarefa FA-M3.)

## Testes obrigatórios (happy + UNHAPPY explícito)

- **happy**: em `run_in_tenant_context(tenant=A)`, `Cliente.objects` vê só linhas de A; INSERT de A passa.
- **UNHAPPY (explícito, exigido por feedback "rodar UNHAPPY path")**: sem contexto (`tenant_ids` resetado) → `Cliente.objects.all()` levanta `ProgrammingError` (42501 via `require_tenant_ctx`), **NÃO** retorna lista vazia. Este é o teste que prova o conserto do FA-A2 (antes: 0 linhas silenciosas; depois: RAISE).
- **cross-tenant**: contexto A não vê/insere linha de B (WITH CHECK INSERT).
- **regressão template**: `policies_isolamento_tenant("x")` contém `require_tenant_ctx()` em S/U/D e `active_tenant_id` em INSERT (teste de string do gerador — barato, pega regressão de template).

## Não-objetivos (explícito — princípio 4)

- NÃO converter INSERT para `require_active_tenant()` (escopo do consolidado é `require_tenant_ctx()`; INSERT fail-loud via cast error mantém precedente).
- NÃO reescrever migrations já aplicadas (0002). Só migration nova aditiva.
- NÃO mexer em policies de `auditoria`/`feature_flags` (já fail-loud; FA-C1 fechou auditoria).

## Riscos / pontos para o tech-lead decidir

- (R1) Manter INSERT cru `active_tenant_id::uuid` é aceitável como fail-loud? (cast de `''` → erro de sintaxe UUID = loud, porém mensagem feia, diferente do 42501 limpo). Precedente auditoria/feature_flags faz igual. Recomendação: manter (consistência > limpeza de mensagem; escopo FA-A2 não pediu).
- (R2) reverse_sql voltando ao CRU: rollback remove fail-loud (regride robustez). Alternativa: reverse que mantém require_tenant_ctx (irreversível de fato). Recomendação: reverse volta ao cru para reversibilidade real da migration (rollback é operação de emergência rara; o estado pré-FA-A2 é o cru e já era o "aceito" até ontem).

## Correções absorvidas (review tech-lead 2026-05-18)

Veredito: **APROVA COM CORREÇÕES**. Todas absorvidas neste design antes do implement:

- **(R2 BLOQUEANTE)** reverse_sql NÃO volta ao cru. `reverse_policies_isolamento_tenant` recria as policies **com `require_tenant_ctx()`** (DROP+CREATE igual ao forward). Motivo: reverse cru reintroduz a vuln FA-A2 num caminho que testes/hook (forward-only) não exercitam → rollback de emergência vazaria-para-zero sem alarme. Schema continua reversível (policies existem, RLS ativa); só não regride robustez. Sobrescreve a recomendação original de (R2).
- **(R5 BLOQUEANTE)** migration `clientes/0014` tem dependência **DUPLA explícita**: `("clientes","0013_seed_authz_importar")` E `("multitenant","0002_fail_loud_e_flag_global")` (usa `require_tenant_ctx()` criada lá). Sem isso, `migrate` from-scratch pode aplicar 0014 antes de multitenant/0002 → `function require_tenant_ctx() does not exist`.
- **(R3 obrigatório)** `policies_isolamento_tenant(tabela)` valida `tabela` com `re.fullmatch(r'[a-z_][a-z0-9_]*', tabela)` → `ValueError` se não casar. Mata classe de injeção em DDL mesmo sendo input de migration.
- **(R4 obrigatório)** teste unhappy roda contra PostgreSQL real e asserta **SQLSTATE `42501`** especificamente (via `e.__cause__`/`pgcode`), não `ProgrammingError` genérico — senão erro de digitação no SQL passa o teste.
- **(R1 aceito)** INSERT cru `active_tenant_id::uuid` mantido (fail-loud via 22P02; consistente com precedente multitenant/0002). Débito de higiene `require_active_tenant()` → registrado em FA-M3.
- Teste adicional: `migrate` from-scratch em banco limpo provando ordem de dependência (drill).
