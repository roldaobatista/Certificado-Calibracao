---
owner: tech-lead-saas-regulado
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-CLI-005
plano_revisado: docs/dominios/comercial/modulos/clientes/planos/US-CLI-005.md
veredito: APROVADO COM RESSALVAS
---

# Tech Lead Review — Plano US-CLI-005 (Dedup manual)

## Resumo executivo

Plano arquiteturalmente direcionado certo: soft-delete + evento `Cliente.Mesclado` + use case puro em `application/` + matriz authz expandida. Mas é **insuficiente em 6 pontos** que precisam ser endereçados antes de `/implement`. Dois são bloqueantes (perfil `financeiro` não existe na matriz F-B; contrato do evento perde sinal essencial pra futuras FK migrations) e quatro são correções de pattern que custam zero agora e caro depois (manager soft-delete + atomicidade + audit hash chain + cross-tenant defensivo).

## Veredito

**APROVADO COM RESSALVAS** (6 ressalvas — bloqueiam `/implement` até endereçadas no plano; nenhuma exige reabertura da Story).

---

## Ressalvas (ordem por gravidade)

### 1. CRÍTICA — Perfil `financeiro` não existe na matriz F-B; `clientes.mesclar` deve ir só pra `admin_tenant` no Marco 1

**Problema:** o plano (`T-CLI-014`) afirma "Authz: `clientes.mesclar` (perfil admin_tenant)" mas a pergunta do briefing menciona "também perfil financeiro (qualidade de cadastro fiscal)". **A matriz F-B atual** (`authz/0003_seed_perfis.py:25-47`) seed só 4 perfis: `admin_tenant`, `tecnico`, `rt_signatario`, `cliente_externo_leitura`. **Não existe `financeiro` como perfil global** — esse perfil só aparece quando Wave A criar perfis tenant-specific (preview futuro em INV-AUTHZ-004).

**Correção exigida:**
1. Manter `clientes.mesclar` exclusivamente em `admin_tenant` no `T-CLI-014`. Justificativa documentada: operação destrutiva-em-aparência (perdedor some das queries default) + impacto cross-módulo via evento; alinhado com `clientes.deletar` que já é só admin.
2. Quando Wave A introduzir perfil `gerente_comercial` ou `qualidade_cadastro`, adicionar `clientes.mesclar` à matriz dele via migration nova — não tentar antecipar agora.
3. NÃO expandir `tecnico` nem `rt_signatario` — eles têm só leitura (`clientes.ler` em `clientes/0003_seed_authz_acoes.py:27-29`), mesclar viola separação de responsabilidades.

### 2. CRÍTICA — Contrato do evento `cliente.mesclado` perde dados essenciais pra FK migration futura

**Problema:** payload proposto `{vencedor_id, perdedor_id, campos_sobrescritos, motivo, usuario_id}` é insuficiente. Quando OS/certificados/financeiro existirem (Wave A+), consumers vão precisar migrar FKs apontando pro `perdedor_id` → `vencedor_id`. Sem mais sinal, consumer não sabe:
- **Em qual tenant?** Sem `tenant_id` no payload, consumer cross-tenant assina-tudo precisa fazer 2 queries pra resolver (RLS filtraria, mas é desperdício e ruído).
- **Quando mesclou?** Sem `mesclado_em` timestamp dedicado (separado do `criado_em` do audit), consumer não consegue idempotência (re-replay do bus em Wave A: como saber se já processei?).
- **Qual o estado pré-merge do perdedor?** Sem `perdedor_documento_hash` e `perdedor_nome`, audit fica "qual documento foi mesclado?" sem PII cruzar.
- **Convenção de nomes:** plano usa `Cliente.Mesclado` (PascalCase) — REPETE o mesmo erro corrigido em US-CLI-001 ressalva 3. Outros eventos existentes (`audit/0001_initial.py:21`, US-CLI-001) usam `cliente.criado` (lowercase + dot.notation). Ferramentas de query/dashboard ficam com 2 padrões pra sempre.

**Correção exigida — payload final:**
```json
{
  "tenant_id": "<uuid>",
  "vencedor_id": "<uuid>",
  "perdedor_id": "<uuid>",
  "perdedor_documento_hash": "<sha256>",
  "perdedor_nome": "<string>",
  "campos_sobrescritos": {"nome": "novo", "email": "novo"},
  "motivo": "<string ≥ 10 chars>",
  "mesclado_em": "<ISO8601>",
  "usuario_id": "<uuid>"
}
```
- Action: `cliente.mesclado` (lowercase, dot.notation) — atualizar `T-CLI-013`.
- `motivo` mínimo de 10 chars (mesmo princípio do `audit-immutability: skip` no hook): força justificativa real, evita "ok"/"sim"/"a".
- `mesclado_em` separado do `auditoria.timestamp` (último é só record-of-event-storage; `mesclado_em` é negócio).

### 3. ALTA — Soft-delete via `deletado_em` + custom Manager: 3 pegadinhas operacionais

**Problema:** `T-CLI-010` propõe `Cliente.objects` filtrando `deletado_em IS NULL` por default + `Cliente.all_objects` manager separado. Pattern é correto MAS:

1. **Quebra `get_queryset` da view atual** (`views.py:63-67`): a view filtra `Cliente.objects.filter(tenant_id=active)` — se o manager default já filtrar deletados, ok, mas precisa ser explícito no plano que `get_queryset` continua usando `Cliente.objects` (não `all_objects`).
2. **Dedup em `create` (views.py:82) PRECISA usar `all_objects`** — caso contrário, criar de novo um CPF que foi soft-deleted retornaria 201 (manager default não vê o deletado), criando um cliente "novo" enquanto o `UniqueConstraint(tenant, tipo_pessoa, documento)` continua válido no banco e dispara `IntegrityError`. Decidir agora:
   - **Recomendação:** dedup consulta `Cliente.all_objects.filter(...)` + se `existente.deletado_em IS NOT NULL` retorna 409 com nova mensagem `"detail": "cliente_existia_foi_mesclado"` + link para o vencedor (resolver via `perdedor_id → vencedor_id` lookup em `auditoria`). Sem isso, race de "mesclar A→B + tentar criar A de novo" dá 500.
3. **Admin Django, shell, `queryset.get(pk=...)`** — esses caminhos usam `_default_manager`. Documentar explicitamente que `_default_manager` continua sendo `objects` (com filtro). Auditoria forense usa `all_objects`.

**Correção exigida:**
- Adicionar nota explícita no plano (riscos): "Toda consulta de dedup (`create` em `views.py`) usa `Cliente.all_objects`, não `Cliente.objects`. Manager default filtra deletados em todo o restante do app."
- Adicionar teste: `test_recriar_documento_de_cliente_mesclado_retorna_409_link_vencedor`.
- Definir `_default_manager = objects` explicitamente no Meta — alguns caminhos de migration Django dependem desse atributo.

### 4. ALTA — Use case puro em `application/`: estrutura precisa seguir ADR-0007 §2, não inventar

**Problema:** `T-CLI-012` propõe `src/application/comercial/clientes/mesclar_clientes.py` "use case puro — recebe Repository protocol". ADR-0007 §2 é claríssimo sobre o pattern, mas o plano não cita o protocolo nem onde ele mora. Risco de divergência: use case importa `from src.infrastructure.clientes.models import Cliente` (acopla domain a Django ORM) — anti-padrão que ADR-0007 §6 proíbe.

**Correção exigida:**
- Criar `src/domain/clientes/repository.py` (Protocol) ANTES do use case:
  ```python
  class ClienteRepository(Protocol):
      def get(self, cliente_id: UUID, tenant_id: UUID) -> Cliente | None: ...
      def save(self, cliente: Cliente) -> None: ...
      def soft_delete(self, cliente_id: UUID, motivo: str, usuario_id: UUID) -> None: ...
  ```
- Use case recebe `ClienteRepository` + `EventBus` (Protocol, não impl) via DI.
- Implementação concreta em `src/infrastructure/repositories/cliente_django.py` (cria pasta — ainda não existe; criar agora estabelece o pattern pra próximos módulos).
- Use case NÃO importa nada de `django.*`, `src.infrastructure.*`. Importa só `src.domain.*` + tipos puros.
- Adicionar teste do use case com fake repo (sem subir Django): `test_mesclar_clientes_use_case_com_fake_repo`. ADR-0007 §1 promete "Domain code testável sem subir Django — 10x mais rápido" — entrega isso agora pro pattern provar.

### 5. MÉDIA — Bloqueio cross-tenant: redundante mas mantém (defesa em profundidade)

**Problema:** `T-CLI-012` propõe "Bloqueia se vencedor ou perdedor estão em tenants diferentes (impossível pela RLS mas defensivo)". A análise está correta — RLS (`clientes/0002_rls_policies.py:18-29`) já bloqueia: SELECT do perdedor de outro tenant retorna 0 linhas, então o use case já recebe `None` no `get(perdedor_id)`. Defesa adicional NÃO é redundante por 2 razões:

1. **Wave A vai introduzir queries cross-tenant** (parceiro marketplace, INV-AUTHZ-003 lista de tenants). Quando isso acontecer, RLS deixa de garantir 1 tenant — passa a garantir "tenant ∈ lista permitida". Mesclar vencedor tenant A com perdedor tenant B pode passar pela RLS se usuário tiver acesso aos 2. **Defesa explícita no use case é o único guardião correto**.
2. **Bug em middleware** (`active_tenant_context` não setado, ou pulou cleanup) — defesa explícita captura antes do `save()` corromper estado.

**Correção exigida:**
- Manter o bloqueio defensivo no use case (`if vencedor.tenant_id != perdedor.tenant_id: raise CrossTenantMergeError(inv_id="INV-TENANT-001")`).
- Trocar o comentário do plano de "impossível pela RLS mas defensivo" pra "defesa em profundidade: RLS protege em F-B (1 tenant); Wave A com lista de tenants pode permitir SELECT cross-tenant — use case continua único guardião". Honestidade arquitetural.
- Teste `test_mesclar_cross_tenant_bloqueado` já está proposto — adicionar variação `test_mesclar_cross_tenant_com_usuario_multi_tenant_bloqueado` que simula contexto Wave A.

### 6. MÉDIA — Atomicidade + hash chain do audit + ordem de operações

**Problema:** plano não fala sobre transação atômica nem sobre ordem das 3 operações (sobrescrever vencedor + soft-delete perdedor + gravar audit). 3 problemas latentes:

1. **Sem `transaction.atomic()`:** se sobrescrever salva, soft-delete falha, audit não roda → estado inconsistente (vencedor com nome novo, perdedor ativo). `registrar_auditoria` já usa `transaction.atomic()` interno (`audit/services.py:45`), mas o use case precisa envolver TUDO num atomic externo. ATOMIC_REQUESTS do DRF não cobre — use case roda fora do request lifecycle quando chamado em batch (T-CLI futuro).
2. **Audit DEPOIS de save:** ordem correta é (a) save vencedor (b) soft-delete perdedor (c) `registrar_auditoria` — porque audit grava `cliente_id` do vencedor; se save falhar, audit teria UUID órfão.
3. **Hash chain advisory lock contention:** `registrar_auditoria` usa `pg_advisory_xact_lock` (`services.py:48`) — serializa TODOS os inserts de audit. Em batch Wave B (mesclar 100 pares importados de CSV), cada use case espera o anterior. Não bloquear merge, mas DOCUMENTAR: "batch merge é V2 (non-goal do plano); quando entrar, considerar bulk audit ou hash chain por particionamento".

**Correção exigida:**
- Adicionar no use case: `with transaction.atomic():` envolvendo as 3 operações.
- Documentar ordem: "1. sobrescrever vencedor → 2. soft-delete perdedor → 3. audit `cliente.mesclado`. Falha em qualquer passo rola back tudo."
- Adicionar teste: `test_mesclar_falha_no_audit_nao_persiste_sobrescrita` (mock `registrar_auditoria` raise → vencedor volta ao estado original; perdedor não-deletado).
- Total recomendado: **9 testes** (6 propostos + 3 acima das ressalvas 3, 5 e 6).

---

## Pontos fortes do plano

- Reconhecimento explícito do limite (AC-1 parcial em MVP-1 — módulos consumidores não existem; evento publicado pra futuro) é honesto e correto.
- Soft-delete via campo nullable (não tabela separada de "deleções") é o pattern certo pra ISO 17025 8.4 (perdedor continua visível em auditoria/forense) + LGPD art. 16 (crypto-shredding por tenant via campo).
- Não tenta antecipar wizard UI — non-goals corretos pra esta fase backend-only.
- Aproveita corretamente os hooks ativos (`tenant-id-validator`, `authz-check`, `audit-immutability-check`).
- T-CLI-014 (migration de matriz authz) segue exatamente o pattern de `clientes/0003_seed_authz_acoes.py` — consistência mantida.

---

## ADR-0011 (BI espelho) — impacto

**Nenhum bloqueante**, mas relevante: quando ADR-0011 entrar (Wave B), o evento `cliente.mesclado` em `auditoria` é exatamente o sinal que o CDC/ETL vai consumir pra atualizar dimensão `dim_cliente` no warehouse (SCD Type 2: vencedor mantém histórico, perdedor vira "merged_into=vencedor_id"). Payload da ressalva 2 (`tenant_id`, `mesclado_em`, `perdedor_documento_hash`) é exatamente o que o ETL precisa.

---

## ADR-0014/0015/0016 (integrações inter-modulares) — impacto

**Atenção:** INV-INT-010 (cliente inadimplente bloqueado) e INV-INT-011 (colaborador desligado) usam pattern de **consumer obrigatório reagindo a evento**. `cliente.mesclado` vai virar uma INV-INT-NNN nova quando Wave A criar OS/certificados/financeiro — preparar contrato agora (payload da ressalva 2) economiza dor depois. Sugerir reservar `INV-INT-014` na próxima atualização de REGRAS-INEGOCIAVEIS.md (não bloqueia este plano; anotar no roadmap).

---

## Recomendação operacional

1. Aplicar as 6 ressalvas no plano (`docs/dominios/comercial/modulos/clientes/planos/US-CLI-005.md`) — bloqueante pra abrir `/tasks`.
2. Consultar `advogado-saas-regulado` em paralelo — soft-delete + retenção (LGPD art. 16 vs Receita 5 anos vs ISO 17025 25 anos) é território dele, não meu.
3. Re-revisar (este parecer) **NÃO** é necessário se as 6 forem aplicadas literalmente. Se houver divergência, re-invocar.
4. Após `/implement`, rodar 3 auditores Família 5: Segurança (foco no cross-tenant defensivo + payload sem PII cruzar), Qualidade (cobertura dos 9 testes + nome citando INVs), Produto (UX da resposta 409 ao tentar recriar documento mesclado).

---

## Limites de honestidade

- **Confiante:** ressalvas 1, 2, 3, 4 — estado real confirmado lendo `views.py`, `clientes/0003_seed_authz_acoes.py`, `authz/0003_seed_perfis.py`, `audit/services.py`, ADR-0007.
- **Suspeita não-provada:** ressalva 6.3 (advisory lock contention em batch) — não medi throughput real; pode ser desprezível com 100 pares. Recomendo cron drill cronometrado em Wave B antes de habilitar batch merge.
- **Fora do meu alcance:**
  - Soft-delete vs hard-delete em retenção LGPD/ISO 17025/Receita 5 anos — escalar `advogado-saas-regulado` (já listado no plano).
  - Texto do `motivo` mínimo (10 chars suficiente? 30? 50?) — escalar UX/Produto.
  - Bug sutil de runtime onde `pg_advisory_xact_lock` interage com `SET LOCAL row_security = off` em alguma migration futura — recomendo pentest externo (R$ 25-50k) antes do 1º tenant pago, conforme limite já citado em revisão de US-CLI-001.
