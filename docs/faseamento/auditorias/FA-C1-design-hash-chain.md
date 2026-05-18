---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
frente: FA-C1
revisor: tech-lead-saas-regulado
veredito: APROVA COM CORREÇÕES
---

# FA-C1 — Design FECHADO: hash chain por-tenant + cadeia sistema

> Núcleo de auditoria/RLS (código sensível). Design validado pelo tech-lead após verificação do estado real do banco. Substitui o SANEA-04 anterior (que assumia SECURITY DEFINER — rejeitado: FORCE RLS aplica; BYPASSRLS viola INV-TENANT-004).

## Decisões fechadas

1. **GUC explícito `app.modo_sistema='1'`** — NÃO usar `CASE WHEN app.tenant_ids=''`. Esse CASE transformaria perda de contexto (bug/ataque) em estado legível (regressão do fail-loud que a migration 0002 instituiu — `connection.py:42` faz RESET no checkout do pool; request que pegue conexão antes do middleware cairia em `tenant_ids=''` e leria a cadeia sistema inteira). `run_as_system` seta `app.modo_sistema='1'`; policies SELECT/INSERT liberam `tenant_id IS NULL` **só** quando `current_setting('app.modo_sistema',true)='1'`; qualquer outro vazio continua RAISE puro via `require_tenant_ctx()`.
2. **Sequência GLOBAL única** `auditoria_seq` + coluna `sequencia BIGINT`. Encadeamento criptográfico é por-tenant (via `filter(tenant_id=...)`); a sequence só desempata ordem (imune a colisão de timestamp µs sob concorrência). Backfill determinístico `UPDATE ... ORDER BY timestamp, id`. Index `(tenant_id, sequencia)`.
3. **UPDATE/DELETE policy → `USING (false)`** (igual feature_flags 0002:100-103). O trigger `auditoria_anti_update/anti_delete` já é a barreira real; manter `require_tenant_ctx()` só mascara o erro real ("imutável") com "tenant não setado".
4. **registrar_auditoria**: lock por-tenant com **namespace de 2 args** `pg_advisory_xact_lock(CONSTANTE_AUDIT_INT, hashtext('audit-chain:'+chave))` (isola espaço de locks de auditoria — evita deadlock sutil por colisão de hashtext com outro advisory lock). `anterior = Auditoria.objects.filter(tenant_id=tenant_id).order_by('-sequencia').first()`. Remover lock global `_ADVISORY_LOCK_KEY`.
5. **verificar_integridade_cadeia(tenant_id)** → `dict[str|None, tuple[bool,int,list]]`. Enumera `Tenant.objects` (não a auditoria) + cadeia sistema via `run_as_system()`. **Corrige Q-02**: `hash_anterior_esperado = recalc` (encadeia no RECALCULADO, não no salvo) → adulteração no meio quebra esse elo E todos os seguintes (propriedade real de hash chain).

## Correções bloqueantes (sem elas REPROVA)

- (1) GUC `app.modo_sistema` em vez de CASE — não regredir fail-loud.
- (2) advisory lock namespace de 2 args.
- (3) **Auditar TODOS os call sites `registrar_auditoria(tenant_id=None)`** e garantir que estão dentro de `run_as_system()` — hoje signals/provisioning podem não estar; a migração da policy converte "funciona por acaso" em RAISE. Bloqueante.
- (4) Testes T7 e T8 obrigatórios além de T1–T6.

## Ordem de implementação

1. Migration nova `multitenant/000X`: CREATE SEQUENCE; ADD COLUMN sequencia; backfill ORDER BY timestamp,id; SET DEFAULT nextval; SET NOT NULL; CREATE INDEX (tenant_id,sequencia); DROP/CREATE policies SELECT+INSERT com guard `app.modo_sistema='1'`; UPDATE/DELETE → USING(false). Headers `# rls-policy:` + `# tests-coverage:`. reverse_sql completo.
2. `connection.py`: `run_as_system` seta `app.modo_sistema='1'`; `_resetar_app_settings_na_conexao` (linha ~44) faz RESET; `run_in_tenant_context` garante que NÃO vaza '1'.
3. `services.py registrar_auditoria`: lock 2-args por-tenant; filter+order_by sequencia; remove lock global.
4. `services.py verificar_integridade_cadeia`: assinatura nova; por-tenant via Tenant.objects + run_as_system; Q-02 fix.
5. Auditar call sites `registrar_auditoria(tenant_id=None)` → envelopar run_as_system.

## Testes obrigatórios

- T1: 2 tenants intercalados → 2 cadeias independentes íntegras.
- T2: verificação por-tenant retorna dict correto.
- T3: evento tenant-NULL sob run_as_system grava+encadeia na cadeia sistema.
- T4: adulterar payload no MEIO → recalc quebra esse E TODOS os seguintes (`len(quebrados) >= N-i`) — prova Q-02 corrigido.
- T5: request tenant A não vê auditoria de B.
- T6: crypto-shred tenant A não afeta verificação de B.
- **T7 (bloqueante)**: contexto perdido (`tenant_ids=''` sem `modo_sistema`) → SELECT/INSERT em auditoria levanta exceção 42501 (fail-loud preservado).
- **T8**: `modo_sistema` não vaza de run_as_system para run_in_tenant_context na mesma conexão do pool.

## Riscos residuais / escalação

- Race de advisory lock sob 50 tenants concorrentes NÃO fecha em code review — **drill cronometrado com inserts concorrentes reais antes do 1º tenant pago** (escalação ativa ao Roldão, junto com o pentest externo ASVS L2 já registrado).
- Cadeias pré-migration têm ordem reconstruída (timestamp,id), não autoritativa — documentar.
