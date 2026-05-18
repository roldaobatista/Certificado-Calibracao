---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
tipo: design-aprovado
frente: SANEA-04
revisor: tech-lead-saas-regulado
veredito: APROVA COM CORREÇÕES
---

# SANEA-04 — Design aprovado: hash chain por tenant

> Conserto do núcleo da auditoria imutável (ISO 17025 cl. 8.4 / LGPD). Design validado pelo subagente tech-lead antes de implementar (código sensível — ritual). Achados SEG-D1 + R-CLI-02.

## Decisão: Opção A / variante a2 — cadeia POR tenant + cadeia "sistema" (tenant NULL)

Cada `tenant_id` tem sua cadeia hash independente; eventos globais (tenant NULL) formam a cadeia "sistema". Justificativa: auditoria CGCRE é por laboratório/tenant; crypto-shredding LGPD de 1 tenant não pode quebrar a cadeia de outro; elimina concentração de risco R-CLI-02; é o padrão correto a cristalizar (replica em todos os módulos).

## Mecanismo (leitura autoritativa do "anterior" sob FORCE RLS)

Função SQL `ultimo_hash_da_cadeia(p_tenant uuid) RETURNS text`, `LANGUAGE sql STABLE SECURITY DEFINER`, `SET search_path = pg_catalog, public` (anti search_path hijack), `REVOKE ALL FROM PUBLIC` + `GRANT EXECUTE` só ao role app. Filtro `WHERE tenant_id IS NOT DISTINCT FROM p_tenant` (resolve NULL = cadeia sistema sem branch). Retorna só 1 hash opaco (nunca payload) — superfície mínima. Desempate `ORDER BY timestamp DESC, id DESC` (timestamp microssegundo pode colidir sob o lock).

## Itens obrigatórios pra merge (condições do tech-lead)

1. `SET search_path` fixo na função SECURITY DEFINER + REVOKE PUBLIC.
2. Corrigir a policy INSERT da `auditoria` pro caso tenant NULL — **bloqueador pré-existente confirmado**: `RLS_POLICY_TEMPLATE` (0001_rls_setup.py:42-44) usa `WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid)`; com tenant NULL → `''::uuid` → erro → evento global nunca inseriu sob FORCE RLS. Nova policy INSERT espelhando o padrão validado de `feature_flags` (0002:91-97).
3. Desempate por `id` na ordenação (services.py:143 + verificador).
4. T1–T6 verdes.

## Migration nova (em `multitenant/migrations/` — NÃO editar 0001/0002)

- `CREATE FUNCTION ultimo_hash_da_cadeia(uuid)` + REVOKE/GRANT + search_path.
- Policy INSERT da auditoria aceitando `(tenant_id IS NULL AND contexto sistema)`.
- Índice `(tenant_id, timestamp DESC, id DESC)` (cobre leitura do último elo + verificação por-tenant; B-tree indexa NULL → cadeia sistema também O(log n)).
- Headers `# rls-policy:` + `# tests-coverage:` (hooks migration-rls-check + policy-test-coverage).

## services.py

- `registrar_auditoria`: trocar `Auditoria.objects.order_by("-timestamp").first()` (linha 143-144) por chamada de `ultimo_hash_da_cadeia(tenant_id)`. Advisory lock passa a ser **por tenant** (`hashtext(tenant_id::text)`; key constante reservada pra cadeia NULL) — reduz concentração R-CLI-02. Lock + leitura + insert na mesma `atomic()`.
- `verificar_integridade_cadeia(tenant_id=SENTINEL, limit=None) -> dict[str|None, tuple[bool,int,list[str]]]`: sem arg verifica cada cadeia por tenant isolada (inclui NULL); com `tenant_id=X` verifica só X (caso CGCRE). Recálculo ordena `(timestamp, id)` dentro do escopo do tenant.

## Testes de regressão obrigatórios (sem eles REJEITA)

- T1: 2 tenants intercalados — `hash_anterior` de A2 == `hash_atual` de A1 (não de B1).
- T2: verificação por-tenant isolada (A e B íntegros independente).
- T3: cadeia sistema (tenant NULL) — 3 eventos globais encadeiam (2º tem hash_anterior = hash do 1º).
- T4: adulteração em A detectada; B continua íntegra.
- T5: não-furo cross-tenant — função SECURITY DEFINER não vaza payload de B.
- T6: crypto-shred da cadeia de A não quebra verificação de B.
- T7 (drill, fora da suite): N tenants concorrentes em paralelo — escala como item de processo.

## Escalações ativas ao Roldão (além do que IA garante em review)

- **T7 — drill cronometrado de concorrência** em ambiente controlado antes de prod (race de pool sob carga só aparece em drill real).
- **Pentest externo ASVS L2 antes do 1º tenant externo pago** — a função SECURITY DEFINER + RLS é a superfície de maior risco; fuzzing externo é obrigatório. É gasto com terceiro (decisão Roldão); não bloqueia o conserto agora (sem cliente externo na janela atual — memória `project_sem_cliente_externo_agora`), fica como pré-condição de go-live pago.

## CORREÇÃO AO DESIGN (achado na implementação 2026-05-18)

O design assumiu que `SECURITY DEFINER` contorna a RLS. **Não contorna** quando a
tabela tem `FORCE ROW LEVEL SECURITY` (caso da `auditoria`): a policy aplica
até para o owner/definer; só roles com `BYPASSRLS` (ou superuser) escapam.
`app_migrator`/`app_user` não têm BYPASSRLS, então `tenants_com_cadeia()` e
`linhas_da_cadeia()` batem em `require_tenant_ctx()` → RAISE "app.tenant_ids
nao setado". `ultimo_hash_da_cadeia()` (registrar_auditoria) **funciona** porque
roda dentro do contexto do request (tenant no `app.tenant_ids`). T1 (encadeamento
por-tenant) passou; T2–T6 (verificador) falham por isto.

**Bug de fundação adicional detectado**: `python manage.py migrate` reporta
"Applying 0004 ... OK" mas o SQL do `RunSQL` NÃO persiste (funções não existem
depois). O mesmo SQL aplicado via `connection.cursor().execute(FORWARD)` no
shell Django funciona. Causa raiz ainda não isolada — é F-A (mecanismo de
migration) e deve entrar na auditoria estruturada de F-A.

**Reabordagem necessária (a decidir na auditoria F-A):** (a) role dedicado
`BYPASSRLS` dono das funções de leitura de cadeia; ou (b) verificador roda por
tenant dentro de `run_in_tenant_context(tenant)` + enumeração de tenants via
tabela `Tenant` (não `auditoria`) + cadeia sistema via mecanismo próprio; ou
(c) policy SELECT da `auditoria` com cláusula que permita leitura escopada de
1 tenant a um role de verificação. SANEA-04 volta pro fluxo estruturado de F-A.

## Débito consciente registrado (não bloqueia)

Campo `seq BIGINT` por-tenant via sequence dedicada (robustez se relógio do servidor voltar) — futuro; desempate por `id` cobre o caso agora.
