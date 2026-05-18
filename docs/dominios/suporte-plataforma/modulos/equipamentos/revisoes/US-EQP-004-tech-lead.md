---
owner: tech-lead-saas-regulado
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-004
plano_revisado: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-004.md
veredito: APROVADO COM RESSALVAS
---

# Tech Lead Review — Plano US-EQP-004

## Resumo executivo

Plano cobre a maior parte da superfície sensível da transferência intra-tenant (INV-050, aceite duplo, sanitização anti-PII, audit hash-only, segregação RBC B6, idempotência destrutiva). Modelagem do `TransferenciaEquipamentoAceite` está bem fatiada e reaproveita corretamente a porta `BloqueioClienteQueryService` já viva no Marco 1 (`predicates_authz.cliente_nao_bloqueado` em `src/infrastructure/clientes/predicates_authz.py:21`). Há, contudo, **6 ressalvas** que precisam ser endereçadas antes de `/tasks` — duas críticas (atomicidade + oracle cross-tenant), três altas (idempotency-key, modelagem do consentimento, ordem de checagens), e uma média (rate limit + IP no aceite).

## Veredito

**APROVADO COM RESSALVAS** (6 ressalvas — bloqueiam `/tasks` até endereçadas no plano; nenhuma exige reabertura da Story ou da PRD).

---

## Ressalvas (ordem por gravidade)

### 1. CRÍTICA — Atomicidade real da transferência: `@transaction.atomic` é suficiente, outbox é antecipação

**Problema:** o plano (T-EQP-044) lista 4 mutações que precisam acontecer ou-todas-ou-nenhuma:

1. INSERT em `transferencia_equipamento_aceite`
2. UPDATE em `equipamento.cliente_atual_id`
3. UPDATE em `equipamento.consentimento_compartilhamento_historico_em_transferencia`
4. INSERT em `auditoria` (evento `equipamento.transferido`)

Não há decisão escrita sobre o boundary. Se ficar no nível do `perform_create` do DRF apoiado em `ATOMIC_REQUESTS=True` (confirmado em `config/settings/base.py:127`), o boundary já cobre os 4 INSERTs/UPDATEs **dentro do mesmo request**. Mas: o use case `TransferirEquipamento` (T-EQP-044) está em `application/`, e a regra arquitetural do projeto (revisão US-CLI-005 §1) é que **use case não pode depender de ATOMIC_REQUESTS** porque pode ser invocado em batch/job fora do request lifecycle (importação CSV futura, job de reconciliação, retry de webhook).

**Outbox é antecipação prematura aqui** — o projeto não tem Procrastinate ativo na Wave A Marco 2; introduzir outbox só para esta US duplica complexidade (tabela `outbox_messages` + worker + retry policy) sem ganho. A trilha `auditoria` já é WORM (INV-001 + trigger `auditoria_bloqueia_mutation`) e funciona como "log-as-bus" interim, mesmo padrão aprovado em US-CLI-001.

**Correção exigida:**

1. T-EQP-044 explicita: use case envolve TUDO em `with transaction.atomic():` **dentro do próprio use case**, não confiando em ATOMIC_REQUESTS do DRF. Razões: (a) chamadas fora-de-request, (b) o UPDATE em `equipamento` precisa de `select_for_update()` pra evitar duas transferências concorrentes do mesmo equipamento (lost-update clássico — atendente A transfere pra cliente X, atendente B transfere o mesmo equipamento pra cliente Y, ambos veem cedente original).

2. Sequência exata dentro do `atomic`:
   ```
   equipamento = Equipamento.objects.select_for_update().get(pk=id)
   <validações cross-tenant + bloqueio + aceite + anti-PII>
   TransferenciaEquipamentoAceite.objects.create(...)
   equipamento.cliente_atual_id = novo
   equipamento.consentimento_compartilhamento_historico_em_transferencia = aceite.consentimento_compartilhamento
   equipamento.save(update_fields=[...])
   registrar_auditoria(action="equipamento.transferido", payload=<sanitizado>, ...)
   ```

3. Bus / outbox **NÃO** entra agora. Quando Procrastinate nascer (Wave B), o evento `equipamento.transferido` em `auditoria` vira fonte do CDC pro bus — mesma decisão de US-CLI-001 ressalva 3. Registrar em "Riscos" do plano: "linhas de auditoria não migradas pro bus; bus será publicação adicional".

4. Trigger PG `bloquear_update_aceite_apos_concretizado` (T-EQP-038) é defesa em profundidade e está correta — mantém. Mas atenção: ela bloqueia UPDATE em `TransferenciaEquipamentoAceite` depois de criada. O lost-update que `select_for_update` protege é em `Equipamento`, não no aceite. Manter as duas defesas.

### 2. CRÍTICA — Oracle cross-tenant: ordem de validações precisa ser SQL-only, não dois SELECTs

**Problema:** AC-EQP-004-2 exige 422 genérico "cliente não encontrado neste tenant" sem oracle. T-EQP-044 lista 2 validações:

- "Validar `novo_cliente_id` existe + `novo_cliente.tenant_id == equipamento.tenant_id`"

A implementação ingênua é dois SELECTs:
```python
cliente = Cliente.objects.get(id=novo_cliente_id)  # bypass RLS = vaza
if cliente.tenant_id != equipamento.tenant_id:
    return 422
```

Isso vaza por dois caminhos: (a) `Cliente.objects` sem `active_tenant` retorna apenas o tenant ativo via RLS — `get()` retorna `DoesNotExist` quando o cliente existe em outro tenant; isso é o resultado correto, **mas** o atacante mede o tempo entre `DoesNotExist` (cliente não existe no meu tenant) e qualquer outro caminho (cliente existe mas bloqueado, cliente existe mas tem fatura) e ainda assim oracle de existência intra-tenant; (b) se algum agente futuro "consertar" usando `Cliente.objects.all().get()` ou shell sem middleware, vira oracle cross-tenant determinístico.

**Correção exigida:**

1. Use case faz **um único** SELECT tenant-scoped, sem nunca tocar `objects.all()`:
   ```python
   # active_tenant injetado por middleware; objects.filter aplica RLS
   cliente = Cliente.objects.filter(id=novo_cliente_id).first()
   if cliente is None:
       raise ValidationError({"novo_cliente_id": "cliente não encontrado neste tenant"})  # 422
   ```
   `tenant_id` **não entra no Python-side** — entra no SQL via RLS. O `cliente is None` cobre 3 estados indistinguíveis: (i) UUID inexistente, (ii) UUID de outro tenant, (iii) cliente soft-deleted. Isso é a defesa correta — `Cliente.tenant_id` nunca aparece no controle de fluxo.

2. Adicionar teste **`test_transferir_cross_tenant_timing_indistinguivel_de_uuid_inexistente`** — Apenas mensagem; medir timing é flaky em CI, mas garantir que a **resposta JSON** é byte-idêntica nos dois casos (UUID que não existe em nenhum tenant × UUID que existe em outro tenant) é estável e suficiente. O teste atual `test_transferir_cross_tenant_retorna_422_sem_oracle` (T-EQP-048) precisa explicitar isso na asserção.

3. Adicionar teste de fuzzing curto: 100 UUIDs aleatórios + 1 UUID real de outro tenant → 101 respostas idênticas (status + body). Análogo ao fuzzing F-B de 500 cross-tenant.

4. Documentar no plano (riscos): "use case NUNCA pode usar `Cliente.objects.all()` ou bypassar middleware tenant — RLS é a defesa primária; defense-in-depth via teste cross-tenant".

### 3. ALTA — Idempotency-Key 24h: tabela `idempotency_key`, não Redis

**Problema:** T-EQP-048 lista o teste `test_idempotency_key_24h_recusa_reuso_destrutivo`, mas nenhuma task implementa o mecanismo. `docs/arquitetura/cross-cutting/idempotencia.md:65` define o padrão (`idempotency_cache` com índice composto, request body hash, response cache). Não há decisão Redis vs tabela.

**Recomendação (Redis NÃO):**

- Wave A Marco 2 **não tem Redis no compose** (confirmar — mas a Foundation rodou sem ele). Introduzir Redis só pra idempotency-key é antecipar infra e quebrar o princípio "nada construído pra ser jogado fora" se o padrão da Wave B for diferente.
- Tabela `idempotency_key` PostgreSQL é suficiente: TTL pode ser `expires_at` + job de cleanup diário; cache de response em coluna `response_body_jsonb`. Custo de IO mínimo dado o volume (10 req/min/usuário cap por rate-limit T-EQP-047).
- Tabela com RLS — INV-TENANT-001: idempotency-key tenant-scoped, senão atacante reusa chave de outro tenant.

**Correção exigida:**

1. Nova task **T-EQP-049**: migration 0015 cria tabela `idempotency_key` com colunas `tenant_id` (NOT NULL + RLS policy + INV-TENANT-002), `endpoint` (string), `idempotency_key` (UUID), `request_body_hash` (sha256), `response_status` (smallint), `response_body_jsonb` (jsonb), `criado_em`, `expires_at`. Constraint composta `UNIQUE(tenant_id, endpoint, idempotency_key)`. Hook `migration-rls-check` exigirá `CREATE POLICY` na mesma migration.

2. Nova task **T-EQP-050**: decorator `@idempotent(ttl_hours=24)` em `src/infrastructure/idempotencia/` (módulo novo — usado depois pelos outros módulos destrutivos Wave A: mesclar cliente, sucatar equipamento, emitir certificado). Casos:
   - Chave nova → processa + grava `response_body_jsonb` no commit.
   - Chave usada + mesmo `request_body_hash` → replay 200/201 do cache.
   - Chave usada + body diferente → 400 "chave idempotente já usada com payload diferente".
   - Chave usada mas em processo → 409 (lock pessimista via `SELECT ... FOR UPDATE NOWAIT` na linha do cache).

3. Aplicar decorator em `POST /v1/equipamentos/{id}/transferir`. Header `Idempotency-Key: <uuid>` obrigatório no endpoint (responder 400 se faltar — "Idempotency-Key header obrigatório em mutação destrutiva"). 

4. Teste explícito de reuso cross-tenant: tenant A grava chave K; tenant B usa mesma chave K → tenant B processa normalmente (não vê linha de A — RLS isola).

### 4. ALTA — `consentimento_compartilhamento_historico_em_transferencia` é flag do EQUIPAMENTO, não do aceite — mas captura é no aceite

**Problema:** o plano mistura os dois. Modelo de domínio (`modelo-de-dominio.md:41`) declara a flag em `Equipamento` (default false). T-EQP-044 diz "setar `Equipamento.consentimento_...` conforme aceite do cedente". Onde fica gravado o **input** do cedente?

Cenário ambíguo: cedente aceita transferir + consente compartilhar histórico → transferência feita; 6 meses depois, cessionário transfere de novo pra terceiro D. O que acontece com o consentimento? Sobrescreve `Equipamento.consentimento_...` com a decisão do **segundo** aceite (cessionário-virou-cedente)? Aí o consentimento original do cedente A → B vira invisível, e o histórico anterior à 1ª transferência também fica sob a nova decisão. Isso viola RBC B6 (cl. 4.2 — confidencialidade entre titulares sucessivos).

**Correção exigida:**

1. Modelagem dupla:
   - **`TransferenciaEquipamentoAceite.consentimento_compartilhamento_historico: boolean`** (NOT NULL) — captura imutável da decisão DAQUELA transferência. Imutável pelo trigger `bloquear_update_aceite_apos_concretizado` (já previsto T-EQP-038).
   - **`Equipamento.consentimento_compartilhamento_historico_em_transferencia: boolean`** — flag derivada do **último** aceite. Existe pra performance (serializer ficha 360° lê 1 boolean em vez de SELECT na transferencia mais recente).

2. Atualização do plano-modelagem: adicionar `consentimento_compartilhamento_historico` em T-EQP-038 (campo do aceite). Atualizar `modelo-de-dominio.md` no mesmo PR (acréscimo, não mudança — boolean novo no aceite + nota explicando dupla escrita).

3. Lógica de visibilidade de histórico no serializer (T-EQP-045): cessionário só vê certs anteriores à **última transferência** se `Equipamento.consentimento_compartilhamento_historico_em_transferencia=true`. Certs entre cedente A e cedente B continuam invisíveis se aceite A→B foi false, **mesmo que aceite B→C seja true** — o aceite vale só pra histórico DAQUELE titular. Isso muda a regra: serializer precisa ler a cadeia de aceites, não só a flag do equipamento.

4. **Trade-off honesto:** se a regra fica complexa demais pra Marco 2 (a cadeia de aceites exige join recursivo ou tabela `EquipamentoHistoricoTitularidade` separada), Roldão decide: (a) Marco 2 implementa só o "último aceite governa tudo" (simples, mas RBC B6 fica parcialmente cumprida — registrar débito em riscos do plano) ou (b) Marco 2 fica com regra completa (mais 1 task + +3 testes). **Minha recomendação: opção (a)** — implementa simples agora, débito documentado, RBC B6 fechado em Wave B com cadeia completa quando portal-cliente nascer. O risco real (cessionário ver certs proibidos) é mitigado: na opção (a), o último cessionário ou vê tudo, ou nada — nunca um subset confuso.

### 5. ALTA — Ordem de validações + 412 vs 422 + reason genérico

**Problema:** T-EQP-044 lista validações em ordem que vaza estado:

1. Cliente existe + tenant correto → 422
2. Cedente não bloqueado + sem fatura → 412
3. Aceite presentes → 400
4. `motivo_detalhe` anti-PII → 400

Cenário oracle: atacante manda transferência cross-tenant **com aceite válido + sem PII**. Resposta = 422. Atacante manda mesma transferência **sem aceite**. Resposta = 400. Diferença revela que o cliente existe (validação 3 só roda se passou da 1). Isso é oracle de existência intra-tenant via ordem de checagens.

**Correção exigida:**

1. Ordem **dura** (não-negociável):
   1. **Idempotency-Key header presente** → 400 se falta (antes de qualquer SQL).
   2. **Payload sintático válido** (aceites presentes + `motivo_categoria` no enum + `motivo_detalhe` sem PII) → 400. Isso é serializer-level, roda antes de qualquer SELECT.
   3. **Authz** (`equipamento.transferir` no perfil) → 403.
   4. **Existência + tenant do equipamento + novo cliente** (1 SELECT tenant-scoped cada) → 422 genérico.
   5. **Bloqueio cedente + financeiro** → 412.
   6. **Lock + UPDATE**.

2. Reasons no 422 são todos **idênticos**: `"recurso não encontrado neste tenant"`. Nunca diferenciar "equipamento não existe" de "cliente novo não existe" — Auditor Segurança da F-A já cravou esse padrão em INV-AUTHZ-001.

3. Adicionar teste **`test_ordem_validacoes_nao_vaza_existencia`**: payload sem aceite + cliente cross-tenant → mesma resposta que payload sem aceite + cliente inexistente. Body byte-idêntico.

### 6. MÉDIA — `aceite_origem_ip_hash` precisa salt por tenant + IPv6

**Problema:** T-EQP-038 lista `aceite_origem_ip_hash` e `aceite_destino_ip_hash`. Sem detalhe de algoritmo. SHA-256 sem salt em IPv4 é dicionário de 4 bilhões — quebrável offline em segundos. Mesmo padrão do `documento_hash` do US-CLI-001 (salt por tenant) deve ser aplicado aqui.

**Correção exigida:**

1. Algoritmo: `sha256(salt_tenant || ip_normalizado)`. `ip_normalizado` = forma canônica IPv6 (`ipaddress.ip_address(raw).compressed`) — IPv4 → `::ffff:1.2.3.4`. Senão dois requests do mesmo IP em formatos diferentes (`192.168.1.1` vs `0xC0A80101`) geram hashes distintos e o aceite "não bate".

2. T-EQP-038 deve referenciar `src/infrastructure/clientes/services/hash_pii.py` (criado no fix retroativo Marco 1) para reusar `hash_pii_com_salt_tenant()`. Não recriar a função.

3. Teste **`test_aceite_ip_hash_usa_salt_tenant_e_ipv6_canonico`**.

4. **Atenção LGPD:** advogado-saas-regulado decide se IP hash do aceite tem retenção infinita (audit imutável) ou 5 anos (matriz). Hash com salt é pseudonimização (LGPD art. 13 § 4º), mas o salt por tenant existir em `clientes` e poder ser correlacionado merece nota no parecer dele.

---

## Pontos fortes do plano

- Fatiamento `T-EQP-038..048` claro, cada task ≤1 commit.
- Reaproveitamento correto da porta `BloqueioClienteQueryService` (Marco 1, `predicates_authz.cliente_nao_bloqueado:21`) — sem reinventar.
- Stub `EmptyFinanceiroQueryService` + override de hook `port-binding-validator` em settings dev/test é o padrão certo pra interim — análogo ao `tenant_nao_suspenso` STUB do US-CLI-003.
- Trigger PG `bloquear_update_aceite_apos_concretizado` como defesa em profundidade além do código Python.
- Texto do termo versionado em `constants/texto_versao_transferencia.py` — segue padrão US-CLI-001 R2 (aceites antigos preservam versão).
- 15 testes propostos cobrem 80% da matriz de risco; faltam só os 4 testes adicionados nas ressalvas 2/3/5/6.

---

## ADRs impactadas

- **ADR-0002 (multi-tenancy):** nada a mudar — INV-050 já está coberta na cl. de RLS + lookup tenant-scoped.
- **ADR-0015 (lifecycle tenant):** se `tenant_nao_suspenso` ficar gate da action `equipamento.transferir`, plano precisa explicitar (T-EQP-046 só fala de perfis, não de gate de tenant suspenso). **Minha recomendação: adicionar `tenant_nao_suspenso` como predicate da action no seed authz.** Tenant suspenso não deve poder mexer em vínculo cliente-equipamento (risco de lavagem de equipamento durante suspensão).
- **ADR-0018/0019:** sem impacto.
- **Pricing/billing-saas:** sem impacto Marco 2.

---

## Recomendação operacional

1. Aplicar as 6 ressalvas no plano (`docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-004.md`) — bloqueante pra abrir `/tasks`.
2. Atualizar `modelo-de-dominio.md` no mesmo PR pra refletir `TransferenciaEquipamentoAceite.consentimento_compartilhamento_historico` (ressalva 4).
3. Re-revisar **NÃO** é necessário se as 6 forem aplicadas literalmente. Se houver divergência (especialmente na opção a/b da ressalva 4), re-invocar.
4. Após `/implement`, rodar auditor de Qualidade (cobertura ≥85% + 4 testes novos das ressalvas) + Segurança (fuzzing cross-tenant + idempotency-key cross-tenant + ordem de validações).

---

## Limites de honestidade

- **Confiante:** ressalvas 1, 2, 5, 6 (padrão já validado em US-CLI-001/004/005; estado real do código confirmado em `predicates_authz.py`, `config/settings/base.py:127`, `REGRAS-INEGOCIAVEIS.md:80`).
- **Confiante mas com trade-off:** ressalva 3 (idempotency em tabela PG). Redis seria marginalmente mais barato em IO sob carga real (100+ req/s) — não temos volume pra justificar; revisitar se Wave B mostrar contention.
- **Suspeita com proposta condicional:** ressalva 4 (cadeia de aceites RBC B6). A regra completa exige decisão produto/RBC — minha recomendação (opção a — último aceite governa) é técnica + pragmática, mas `consultor-rbc-iso17025` precisa endossar antes do `/implement`.
- **Fora do meu alcance:** retenção do `ip_hash` no aceite (LGPD vs audit imutável — escalar `advogado-saas-regulado`); valor jurídico do aceite via UI HTMX (sem A3, sem portal-cliente) — escalar `advogado-saas-regulado` confirmando que segue padrão CC art. 421/422 de US-CLI-001.
- **Recomendação não-código:** quando 1º tenant pago entrar (post-Portão 1), considerar pentest externo focado em transferência (cenário clássico de business-logic flaw — atacante encontra caminho pra transferir equipamento de outro tenant via combinação de race + IDOR). ASVS L2 não cobre 100% desse vetor; pentest humano sim.
