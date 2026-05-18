---
owner: tech-lead-saas-regulado
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-CLI-001
plano_revisado: docs/dominios/comercial/modulos/clientes/planos/US-CLI-001.md
veredito: APROVADO COM RESSALVAS
---

# Tech Lead Review — Plano US-CLI-001

## Resumo executivo

Plano sólido no recorte. Modelagem do AddField `aceite_lgpd_em`, dedup 409 estruturada e interim event-as-audit-trail são decisões corretas dado o estado real da Foundation (sem Procrastinate ativo, sem eventbus formal). Há, contudo, **5 ressalvas** que precisam ser endereçadas antes de `/implement` — uma delas crítica (vazamento via 409) e duas que afetam migração futura pro bus.

## Veredito

**APROVADO COM RESSALVAS** (5 ressalvas — bloqueiam `/implement` até endereçadas no plano; nenhuma exige reabertura da Story).

---

## Ressalvas (ordem por gravidade)

### 1. CRÍTICA — Response 409 estruturada vaza existência cross-tenant (INV-AUTHZ-001 + INV-TENANT-001)

**Problema:** o plano (`T-CLI-003`) propõe devolver `{"detail": "cliente_ja_existe", "cliente_id": "<uuid>", "link": "/api/v1/clientes/<uuid>"}` quando dedup dispara. Hoje a dedup é por `UniqueConstraint(tenant, tipo_pessoa, documento)` — o que significa que **a 409 SÓ pode disparar para um cliente do MESMO tenant** (RLS + `active_tenant` no `perform_create` garantem isso). Então **devolver `cliente_id` é seguro do ponto de vista cross-tenant** — mas isso depende da defesa em profundidade estar íntegra. Se em algum momento a checagem de unicidade subir pro nível do banco sem filtro de tenant (DB constraint UNIQUE(documento) global ou cache fora do tenant), a 409 vira oráculo de existência cross-tenant.

**Correção exigida (não-negociável):**
1. A 409 só pode ser construída **após** consulta ao queryset já filtrado por `active_tenant` (`Cliente.objects.filter(tenant_id=active, documento=X).first()`). NUNCA derivar o `cliente_id` capturando o `IntegrityError` cru do banco — `IntegrityError` em RLS pode pegar uma linha de outro tenant em condição de borda + dispararia também em UNIQUE global futuro.
2. Adicionar **teste explícito de não-vazamento cross-tenant**: tenant A cria cliente CPF=X; tenant B tenta criar cliente CPF=X; resposta esperada = **201 Created** (não 409), porque RLS isola e `UniqueConstraint(tenant, tipo_pessoa, documento)` permite. Esse teste protege contra regressão se alguém trocar `UniqueConstraint` por `unique=True` no campo.
3. Documentar no plano (riscos): "409 nunca pode ser construída a partir de `IntegrityError.__cause__` sem re-consultar via queryset tenant-scoped".

### 2. ALTA — `aceite_lgpd_em` deve ser NOT NULL com default explícito de migration

**Problema:** plano não decide nullable vs NOT NULL. AC-CLI-001-2 exige aceite LGPD **obrigatório no cadastro**. Nullable contradiz o AC; serializer pode até validar `required=True`, mas o modelo aceitaria NULL em outros caminhos (admin Django, shell, fixture, importação CSV futura US-CLI-003).

**Correção exigida:**
- Campo `aceite_lgpd_em = DateTimeField(null=False, blank=False)` no modelo.
- Migration: tabela está vazia em dev (0 linhas), então pode aplicar NOT NULL direto **sem default**. Em prod (que não existe ainda) seria backfill com `criado_em` antes do `ALTER COLUMN SET NOT NULL` — registrar isso no item 1 dos riscos do plano (já está parcialmente; tornar explícito).
- Como o catálogo de finalidades é separado (T-CLI-002), recomendo já adicionar campo `aceite_lgpd_finalidade` (CharField/FK pro catálogo) **agora**, mesmo que enum pequeno — porque migrations seguintes para adicionar coluna NOT NULL em tabela populada são caras (Wave A vai popular `clientes` rapidamente). Default no boundary: `"execucao_contrato"` (RAT-03).

### 3. ALTA — Interim event-as-audit-trail tem 2 dívidas técnicas que precisam ficar visíveis

**Problema:** gravar `Cliente.Criado` em `auditoria` como `action="Cliente.Criado"` com payload em `payload_jsonb` é arquiteturalmente aceitável — `auditoria` já tem hash chain WORM (INV-001), trigger anti-mutation, índice por `action` (`ix_audit_action_ts`). **Mas há dois problemas que precisam ficar visíveis:**

1. **Migração Wave A:** quando Procrastinate entrar, **NÃO migrar essas linhas pro bus**. Elas continuam em `auditoria` (são trilha histórica imutável — INV-001 proíbe mutação). O bus passa a ser **publicação adicional**, não substituição. Isso precisa estar escrito no plano agora (riscos §3) pra evitar que algum agente futuro "limpe" as linhas em nome de unificação.
2. **Convenção de nomes:** o índice `ix_audit_action_ts` filtra por `action`. Outros eventos do sistema já gravados em `auditoria` usam `usuario.criado`, `certificado.emitido` (lowercase, dot.notation — ver migration `audit/0001_initial.py:21`). O plano usa `Cliente.Criado` (PascalCase). **Inconsistência.** Padronizar **agora** pra `cliente.criado` (lowercase) — caso contrário ferramentas de query/dashboard ficam com dois padrões pra sempre. Custo zero agora, custo alto depois.

**Correção exigida:**
- Trocar `action="Cliente.Criado"` por `action="cliente.criado"` em todo o plano.
- Adicionar nota explícita no riscos: "linhas de auditoria NÃO são migradas pro bus Procrastinate; bus é publicação adicional".
- Definir schema do `payload_jsonb` agora (mesmo que mínimo): `{"cliente_id": "<uuid>", "tipo_pessoa": "PF|PJ", "documento_hash": "<sha256>"}`. **Não logar CPF/CNPJ em claro no audit trail** — LGPD: trilha imutável de cadastros viraria depósito permanente de PII. Hash + tabela `clientes` para resolver quando precisar.

### 4. MÉDIA — `migration-rls-check` no AddField: confirmar que passa, mas com lookup

**Plano afirma:** "AlterField em tabela já com RLS — não cria policy nova, deve passar". Vou validar a leitura do hook em pre-commit, **não é responsabilidade do plano garantir**. Recomendação ao implementador:

- Antes do `/implement`, rodar `bash .claude/hooks/_test-runner.sh` para confirmar suite 88/88 verde.
- O hook bloqueia `CREATE TABLE com tenant_id sem CREATE POLICY na mesma migration`. `AddField aceite_lgpd_em` não cria tabela nem policy — deve passar. Se bloquear (false positive), allow via `# rls-policy: external 0002` apontando policy existente.

### 5. MÉDIA — Cobertura de testes: faltam 3 unhappy paths

**3 testes propostos cobrem:**
- AC-1: 409 com link (1 happy)
- AC-2: aceite LGPD obrigatório (1 unhappy do AC-2)
- AC-2: evento gravado (1 happy)

**Faltam (recomendado adicionar):**
1. **Cross-tenant non-leak** (já exigido na ressalva 1): tenant A cria CPF=X; tenant B cria CPF=X → 201, não 409.
2. **Aceite LGPD com timestamp futuro** ou inválido (string não-ISO8601): retorna 400 com mensagem clara.
3. **Evento NÃO gravado se POST falha** (transação atômica): POST com payload válido mas `serializer.save()` falha por race condition → `auditoria` não tem linha órfã `cliente.criado`. Requer envolver `perform_create` em `transaction.atomic()` ou gravar audit DEPOIS do save bem-sucedido. Plano não fala sobre transação atômica — adicionar.

**Total recomendado: 6 testes (3 propostos + 3 acima).**

---

## Pontos fortes do plano

- Sequência de tasks (`T-CLI-001..005`) bem fatiada, cada uma ≤1 commit.
- Reconhecimento explícito da dívida técnica do interim event-as-audit-trail nos riscos §3 (honesto sobre o estado real da Foundation).
- Não tenta antecipar Procrastinate nem importação CSV — non-goals corretos.
- Aproveita corretamente os 3 hooks ativos (`tenant-id-validator`, `authz-check`, `migration-rls-check`).
- Catálogo de finalidades LGPD em `docs/conformidade/comum/finalidades-lgpd.md` é a forma certa de evitar enum hardcoded espalhado pelo código.

---

## ADR-0011 (BI espelho) — impacto

**Nenhum bloqueante.** ADR-0011 ainda é proposta; banco analítico não existe. Quando entrar (Wave B), o evento `cliente.criado` em `auditoria` é exatamente o sinal que o CDC/ETL vai consumir pra hidratar o espelho — modelagem atual já compatível.

---

## Recomendação operacional

1. Aplicar as 5 ressalvas no plano (`docs/dominios/comercial/modulos/clientes/planos/US-CLI-001.md`) — bloqueante pra abrir `/tasks`.
2. Re-revisar (este parecer) **NÃO** é necessário se as 5 forem aplicadas literalmente. Se houver divergência, re-invocar.
3. Após `/implement`, rodar auditor de Qualidade (cobertura dos 6 testes) + Segurança (foco no não-vazamento da 409 + log sem PII).

---

## Limites de honestidade

- **Confiante:** ressalvas 1, 2, 3 (estado real do código já confirmado lendo `clientes/models.py`, `views.py`, `audit/0001_initial.py`).
- **Suspeita não-provada:** ressalva 5.3 (transação atômica) — `perform_create` do DRF já roda em `ATOMIC_REQUESTS` se settings habilitar; não confirmei o setting do projeto. Pedir ao implementador checar `config/settings/base.py::DATABASES['default']['ATOMIC_REQUESTS']`. Se True, gravação do audit dentro de `perform_create` já é atômica gratuitamente.
- **Fora do meu alcance:** validação do texto legal do aceite LGPD + finalidade RAT-03 (escalar `advogado-saas-regulado`, já listado nos subagentes a consultar pelo plano).
