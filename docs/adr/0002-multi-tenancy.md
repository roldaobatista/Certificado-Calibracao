# ADR-0002 — Modelo de multi-tenancy

> **Status:** proposta v2 (17/05/2026 madrugada — revisão pós-auditoria 10 agentes pós-48-módulos). Bloqueante do Portão 2 da ADR-0001 candidata.
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Auditor 2 da 1ª auditoria de 10 agentes (17/05/2026) — 3 vetores críticos + 5 altos de fuga em multi-tenant. Parecer 1 + Parecer 8 da 2ª auditoria confirmaram severidade. **v2:** Auditor 2 + Auditor 8 da auditoria pós-48-módulos apontaram que `1 usuário = 1 tenant` quebra com marketplace, portal cliente matriz+filiais, auditor RBC visitante multi-laboratório. Esta revisão introduz suporte cross-tenant sem violar defesa em profundidade.
> **Depende de:** ADR-0001 v2 (stack Django + PostgreSQL + Celery)
> **Relacionado:** `docs/arquitetura/anti-corrosion-layer.md` (porta `MultiTenantDiscriminator`), ADR-0012 (autorização unificada).

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **Tenant** | Cliente do Aferê (uma assistência técnica, um laboratório) — cada um tem seus próprios dados, separados dos outros. |
| **Multi-tenancy** | Vários tenants compartilhando o mesmo sistema, sem se ver. |
| **RLS (Row-Level Security)** | Trava no banco de dados que impede tenant A enxergar dados de tenant B, mesmo se a aplicação esquecer. Defesa em profundidade. |
| **Schema** | "Pasta de tabelas" dentro do banco. Cada tenant pode ter sua própria pasta OU compartilhar uma única pasta com filtro de tenant_id. |
| **Pool de conexões** | "Estoque de conexões abertas com o banco". App pega uma, usa, devolve. Próximo request reutiliza a mesma conexão. |
| **Thread-local** | Variável que vive só dentro de uma execução de request (não vaza pra próximo). |

---

## Contexto

ADR-0001 v2 recomenda **schema compartilhado + RLS PostgreSQL** pra 100-5000 tenants no VPS Hostinger. Auditor 2 levantou 8 vetores de fuga (3 críticos + 5 altos) que precisam ser cobertos antes de F-A:

**Críticos:**
- **C1.** Prisma/Django ORM em pool de conexões não preserva `SET LOCAL app.tenant_id` entre requests — vazamento determinístico
- **C2.** Celery workers rodam fora do request HTTP — `tenant_id` não é restaurado automaticamente
- **C3.** Role do app não pode ter `BYPASSRLS` nem ser superuser — Docker Compose mal configurado anula RLS inteira

**Altos:**
- **A1.** Raw queries (`$queryRaw`/`connection.cursor()`) furam RLS se policy for permissiva com fallback `true`
- **A2.** Schema-shared + RLS é correto pra 100-5000 tenants — mas exige ADR escrita ANTES de F-A começar
- **A3.** Migrations Prisma/Django rodam como `app_migrator` — precisam de policy de "tenant_id NOT NULL + default trigger"
- **A4.** Backup/restore via `pg_dump` é cross-tenant por design — export-por-tenant exige pipeline específico
- **A5.** Read replica (futuro) herda RLS — mas conexão da replica precisa do mesmo `SET LOCAL`

---

## Decisão

Adotar **schema compartilhado + middleware `tenant_id` thread-local + RLS PostgreSQL + 2 roles distintas + 5 mecanismos defensivos**.

### Componentes da decisão

#### 1. Estratégia de tenancy: schema compartilhado

- **1 schema PostgreSQL** chamado `public` (ou `aferere`) com todas as tabelas
- Coluna `tenant_id UUID NOT NULL` obrigatória em **TODA** tabela com dados de cliente (INV-TENANT-002)
- RLS ativa em todas essas tabelas (INV-TENANT-003)
- **Critério de reversão pra schema-per-tenant ou DB-per-tenant:**
  - TAM > 5.000 tenants ativos
  - 1 cliente farma exige isolamento físico
  - Particionamento por `tenant_id` não resolve performance
- Migração coberta pela porta `MultiTenantDiscriminator` (anti-corrosion layer) — domain code não muda

#### 2. Duas roles distintas no Postgres

**`app_user`** (acesso normal):
- `NOBYPASSRLS`, `NOSUPERUSER`, `NOCREATEDB`
- Usada pelo Django (web + Celery workers)
- INV-TENANT-004 obrigatória + hook valida

**`app_migrator`** (DDL):
- `NOBYPASSRLS`, `NOSUPERUSER`, mas com `CREATE` nos schemas
- Usada pelas migrations (`python manage.py migrate`)
- Separação previne agente escrever migration que altera dados de produção sem perceber

**SQL de criação (referência):**
```sql
CREATE ROLE app_user WITH
  LOGIN PASSWORD '...'
  NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION;

CREATE ROLE app_migrator WITH
  LOGIN PASSWORD '...'
  NOSUPERUSER NOBYPASSRLS;

GRANT CONNECT ON DATABASE aferere TO app_user, app_migrator;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT ALL ON SCHEMA public TO app_migrator;
```

#### 3. Middleware Django `TenantMiddleware` (v2 — lista de tenants)

> **Mudança v2:** middleware passa a setar **LISTA** de tenants permitidos (`tenant_ids`), não tenant único. Mesmo pra usuário com 1 tenant, a lista tem 1 elemento. Habilita perfis cross-tenant (marketplace, matriz+filiais, auditor RBC multi-lab) sem violar defesa em profundidade. INV-AUTHZ-003 cravado.

Responsabilidades:
1. Extrair `user_id` do JWT (mobile) ou da session (web)
2. **Consultar `auth_usuario_perfil`** pra resolver lista de tenants ativos pra esse usuário no momento (`valido_de ≤ now() ≤ valido_ate`)
3. **Validar tenant "ativo"** que o cliente passou (header `X-Aferê-Active-Tenant` ou query param) — deve estar na lista resolvida
4. Setar `app.tenant_ids` (lista PG via `SET LOCAL`) + `app.active_tenant_id` (tenant onde a ação acontece, dentro da lista)
5. Limpar contexto após response

**Pseudocódigo v2:**
```python
class TenantMiddleware:
    def __call__(self, request):
        user_id = self._extract_user_id(request)  # JWT/session
        if not user_id:
            return HttpResponseForbidden("Missing user context")

        # Resolve LISTA de tenants vigentes pra esse usuário
        tenant_ids = AuthorizationProvider.tenants_for(user_id, at_time=now())
        if not tenant_ids:
            return HttpResponseForbidden("User has no active tenant access")

        # Tenant "ativo" (onde a ação acontece) deve ser subconjunto da lista
        active_tenant = self._extract_active_tenant(request)  # header/param
        if active_tenant and active_tenant not in tenant_ids:
            return HttpResponseForbidden("Active tenant not in user's allowed set")
        if not active_tenant and len(tenant_ids) == 1:
            active_tenant = tenant_ids[0]  # default

        token_list = tenant_ids_context.set(tenant_ids)
        token_active = active_tenant_context.set(active_tenant)
        try:
            return self.get_response(request)
        finally:
            tenant_ids_context.reset(token_list)
            active_tenant_context.reset(token_active)
```

**Princípio:** a lista vem **sempre** da tabela `auth_usuario_perfil` (fonte de verdade), nunca do cliente. Cliente só indica qual tenant está "ativo agora" (escopo do request); middleware valida que está dentro da lista permitida.

#### 4. Connection patcher Django ORM (v2 — `app.tenant_ids` em vez de `app.tenant_id`)

Antes da 1ª query de cada request, abrir transação e executar:
```sql
SET LOCAL app.tenant_ids = '<uuid1>,<uuid2>,<uuid3>';
SET LOCAL app.active_tenant_id = '<uuid_ativo>';  -- pra INSERT/UPDATE saberem qual tenant gravar
```

**Sem isso, a próxima query no mesmo socket do pool herda contexto do request anterior — vazamento determinístico.** (Auditor 2 C1)

**Para usuário com 1 tenant** (caso comum Wave A), a lista tem 1 elemento — mesma defesa, sem caso especial.

**Para INSERT/UPDATE** (operação muta dados), o `tenant_id` gravado é sempre `app.active_tenant_id` — nunca livre. Manager Django força isso automaticamente.

Implementação via signal `django.db.backends.signals.connection_created` + wrap em `transaction.atomic()` no middleware.

#### 5. Wrapper Celery `run_in_tenant_context`

Todo Celery task que toca tabela com RLS **DEVE** ser executada via wrapper:
```python
from infrastructure.queue.provider import run_in_tenant_context

@shared_task
def emit_invoice_task(tenant_id: str, invoice_id: str):
    with run_in_tenant_context(tenant_id):
        # SET LOCAL aplicado, transação aberta
        invoice = Invoice.objects.get(id=invoice_id)
        # ... resto do código
```

**Sem o wrapper, o job:**
- ❌ Vaza (se a role do worker tiver BYPASSRLS — não nosso caso, mas se Docker mal config)
- ✅ Falha (se policy RLS for `USING (tenant_id = current_setting('app.tenant_id')::uuid)` sem fallback `true`) — comportamento desejado

Lint custom semgrep bloqueia `@shared_task` sem `run_in_tenant_context`.

#### 6. Policy RLS v2 — lista de tenants, sem fallback permissivo

> **Mudança v2:** policy aceita lista de tenants permitidos via `string_to_array`. Mantém defesa em profundidade (sem fallback permissivo); habilita cross-tenant pra perfis Wave B+ (marketplace, portal cliente matriz+filiais). INV-AUTHZ-003.

**ERRADO #1 (vaza se setting não setado):**
```sql
CREATE POLICY tenant_isolation ON certificados
  USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids', true), ',')));
-- O `true` retorna NULL se não setado → policy permite tudo
```

**ERRADO #2 (tenant único — quebra cross-tenant):**
```sql
CREATE POLICY tenant_isolation ON certificados
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
-- Padrão v1; quebra pra usuário com acesso a N tenants
```

**CORRETO v2 (falha duro + suporta lista):**
```sql
-- SELECT/UPDATE/DELETE: usuário vê qualquer linha cujo tenant_id está na lista permitida
CREATE POLICY tenant_isolation_select ON certificados
  FOR SELECT
  USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

-- INSERT: sempre grava no active_tenant_id (não livre)
CREATE POLICY tenant_isolation_insert ON certificados
  FOR INSERT
  WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

-- UPDATE: pode atualizar linha cujo tenant_id está na lista, mas não pode mudar tenant_id
CREATE POLICY tenant_isolation_update ON certificados
  FOR UPDATE
  USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
  WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));
```

**Sem `true` em nenhum `current_setting`:** ERRO `unrecognized configuration parameter` se não setado — failure mode é blocking, não permitindo.

**Migration de v1 → v2:** ~50 policies existentes regeradas via script SQL. Padrão automatizável (sed/script Python lendo schema + emitindo novas policies). Bloqueio: requer janela de manutenção curta (5-10 min) pra DROP POLICY + CREATE POLICY em todas as tabelas. Drill obrigatório em staging antes.

#### 7. Lint custom proíbe raw queries fora do wrapper

`semgrep` rule bloqueia merge se:
```python
# ❌ PROIBIDO
cursor = connection.cursor()
cursor.execute("SELECT * FROM certificados WHERE ...")

# ✅ PERMITIDO (via porta + wrapper)
with run_in_tenant_context(tenant_id):
    qs = Certificado.objects.filter(...)
```

Exceção: `infrastructure/multitenant/` pode ter raw queries explícitas (cuidadosamente revisadas pelo Auditor 2).

#### 8. Migration linter

Hook pre-commit + CI custom rule:
- Toda nova tabela com PK deve ter `tenant_id UUID NOT NULL` + FK pra `tenants`
- Toda tabela nova com `tenant_id` DEVE ter policy RLS criada na mesma migration
- Excepcionalmente: tabelas globais (`tenants`, `plans`, `feature_flags`) marcadas explicitamente com comentário `-- SHARED ACROSS TENANTS`

#### 9. Export por tenant (LGPD art. 18 portabilidade)

Pipeline `export_tenant(tenant_id: UUID) -> ZipFile`:
- Itera cada tabela com `tenant_id`
- `COPY (SELECT * FROM tabela WHERE tenant_id = $1) TO STDOUT WITH CSV HEADER`
- Inclui PDFs do Backblaze B2 com prefix `tenant_id/`
- Gera ZIP encriptado com chave do tenant + envia link assinado
- Teste E2E rodando trimestralmente

---

## Defesa em profundidade — 4 camadas

| Camada | Mecanismo | Falha quando |
|---|---|---|
| **1. Aplicação (frontline)** | `TenantMiddleware` extrai tenant_id; Manager Django filtra automaticamente | Agente esquece `objects.filter(tenant_id=...)` em código novo |
| **2. ORM (segunda barreira)** | Django ORM via custom `TenantQuerySet` força filtro tenant_id | Agente usa `objects_raw` ou `.using('admin')` |
| **3. Banco (defesa final)** | RLS policy bloqueia query sem `app.tenant_id` setado | Policy mal escrita com fallback `true` ou role com BYPASSRLS |
| **4. Hooks/Lint (preventivo)** | semgrep + migration linter bloqueam merge antes de chegar em produção | Hook desabilitado, ou regra incompleta |

**Filosofia:** assumir que cada camada vai falhar eventualmente. A camada seguinte protege.

---

## Spike de validação (obrigatório antes de F-A)

### Spike-MT-1 — Prova de RLS com pool concorrente
**Objetivo:** confirmar que `SET LOCAL app.tenant_id` sobrevive no pool de conexões Django.
**Setup:** 100 requests simultâneas, 2 tenants, mesma view, mesma conexão.
**Métrica:** ZERO vazamento (request do tenant A nunca retorna dado do tenant B).
**Custo:** 2 dias.

### Spike-MT-2 — Prepared statements + RLS
**Objetivo:** Auditor 2 M1 — confirmar que `current_setting` é replanned a cada execução em prepared statement.
**Setup:** 2 tenants alternando 1000 queries na mesma conexão usando `prepare`.
**Métrica:** cada tenant vê SÓ seus dados; nenhum hit cruzado.
**Custo:** 1 dia.

### Spike-MT-3 — Celery + RLS
**Objetivo:** confirmar que `run_in_tenant_context` em Celery worker preserva isolamento.
**Setup:** 50 jobs paralelos de 5 tenants diferentes, cada job lê tabela com RLS.
**Métrica:** ZERO vazamento; jobs sem `run_in_tenant_context` FALHAM em vez de vazar.
**Custo:** 2 dias.

### Spike-MT-4 — Cross-tenant canary
**Objetivo:** detectar vazamento em produção antes do cliente.
**Setup:** tenant sintético "canary" com dados marcadores; query daily que verifica que tenant_canary não aparece em nenhuma response cross-tenant.
**Métrica:** alerta automático se canary vazar.
**Custo:** 1 dia.

**Total spike de validação:** 6 dias úteis.

---

## Drill cronograma obrigatório (revisado pós-auditoria 17/05/2026)

**Antes do 1º tenant pago** (apenas 1 obrigatório):

1. **Drill RLS bypass** — agente tenta deliberadamente esquecer `WHERE tenant_id` em query; mede se RLS bloqueia. Cronômetro: deve ser bloqueado em <100ms.

**Quando 5 tenants pagos ativos** (mais 3 disparam):

2. **Drill Celery sem wrapper** — agente roda task sem `run_in_tenant_context`; mede se FALHA (não vaza). Cronômetro: deve falhar em <500ms.
3. **Drill export-por-tenant** — exporta tenant_canary; mede tamanho do ZIP + tempo. Cronômetro: <60s pra tenant com 10k registros.
4. **Drill cross-tenant fuzzing** — 1000 queries randômicas com tenant_id trocado; mede vazamentos. Cronômetro: 0 vazamentos.

**Razão da redução:** Auditor 4 (sobre-engenharia) + 9 (vs concorrentes BR) da 3ª auditoria de 10 agentes (17/05/2026) alertaram que 4 drills mensais pré-cliente-pago = teatro consumindo 2-3 dias/mês do Roldão sem cliente real reclamando. 1 drill obrigatório mantém defesa essencial (RLS) sem inflar trabalho operacional.

---

## Itens a fazer

### Bloqueantes pra F-A começar
- [ ] **Spike-MT-1, MT-2, MT-3, MT-4** rodados e verde (6 dias úteis)
- [ ] **INV-TENANT-004 documentada** em `REGRAS-INEGOCIAVEIS.md` ✅ (feito 17/05/2026)
- [ ] **INV-AUTHZ-003 documentada** em `REGRAS-INEGOCIAVEIS.md` ✅ (feito 17/05/2026 madrugada)
- [ ] **Hook validador** de role NOBYPASSRLS criado e rodando em CI
- [ ] **Lint custom semgrep** pra `@shared_task` sem wrapper
- [ ] **Lint custom semgrep** pra raw queries fora de `infrastructure/multitenant/`
- [ ] **Migration linter** pra nova tabela exigir tenant_id + RLS policy v2 (lista de tenants)
- [ ] **Tabela `auth_usuario_perfil`** (M:N user × tenant com `valido_de/ate`) — fonte de verdade do middleware (ADR-0012)

### Bloqueantes pra Foundation F-B (auth) começar
- [ ] **Middleware `TenantMiddleware` v2** com lista de tenants
- [ ] **Connection patcher** com `app.tenant_ids` + `app.active_tenant_id`
- [ ] **Spike-MT-5 (NOVO)** — fuzzing cross-tenant: usuário com acesso a {A, B} tenta acessar C → bloqueado pela RLS

### Bloqueantes pra Wave B (marketplace + portal cliente cross-tenant) começar
- [ ] **Migration v1→v2 das ~50 policies RLS** — script SQL automatizado + drill staging
- [ ] **UI "trocar tenant ativo"** (header `X-Aferê-Active-Tenant`)
- [ ] **Drill cross-tenant em produção** — auditoria simula vazamento

### Configuração inicial
- [ ] SQL de criação das 2 roles em `infrastructure/db/init/01-roles.sql`
- [ ] Implementação `TenantMiddleware` em `infrastructure/multitenant/middleware.py`
- [ ] Implementação `run_in_tenant_context` em `infrastructure/queue/celery.py`
- [ ] Custom Manager Django (`TenantManager`) com filtro automático
- [ ] Pipeline `export_tenant(tenant_id)` em `infrastructure/multitenant/export.py`

### Pós-MVP-1
- [ ] Drill mensal cronometrado configurado (cron + alerta)
- [ ] Read replica RLS validação (quando entrar replica)

---

## Consequências

### Positivas
- **Defesa em profundidade real** — 4 camadas. Mesmo se 3 falharem, a 4ª protege.
- **R-001 (vazamento cross-tenant) score 25 → ~5** após implementação completa.
- **Migração futura pra schema-per-tenant ou DB-per-tenant** sem mudar domain code (porta `MultiTenantDiscriminator`).
- **Conformidade LGPD art. 18** (portabilidade) via `export_tenant`.

### Negativas
- **6 dias de spike obrigatórios** antes de F-A começar — atrasa cronograma.
- **Overhead de performance** — RLS adiciona ~5-15% por query OLTP (Crunchy Data benchmarks). Mitigado por índices `(tenant_id, ...)`.
- **Complexidade pros agentes IA** — toda task Celery exige wrapper; cada nova tabela exige policy RLS. Mitigado por convenções rígidas + lint + scaffold.

### Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| Schema-shared vs schema-per-tenant | Schema-shared | TAM 100-5000 tenants; per-tenant explode migrations (5000 schemas × cada migration) |
| RLS Postgres vs filtro só na aplicação | RLS Postgres + filtro aplicação | Defesa em profundidade — R-001 score 25 exige |
| Celery wrapper obrigatório vs assumir cuidado do agente | Wrapper obrigatório | Agente esquece. Wrapper força falha (não vazamento) |
| Policy com fallback `true` (suave) vs sem fallback (duro) | Sem fallback | Falha duro é desejável; soft fail vaza tudo |
| 1 role do app vs 2 roles separadas | 2 roles (app + migrator) | Separação migration/DML reduz blast radius |

---

## Critérios de reversão

| Sinal | Resposta |
|---|---|
| TAM > 5.000 tenants ativos em 2028 | Migrar pra schema-per-tenant via `MultiTenantDiscriminator.migrate_tenant()` |
| Cliente farma grande exige isolamento físico | Migrar esse tenant específico pra DB-per-tenant |
| Performance RLS > 30% overhead | Avaliar particionamento por `tenant_id` hash |
| Postgres lock contention em tabelas hot (`os`, `equipamento`) | Particionamento nativo Postgres 11+ |
| Vazamento cross-tenant em produção (R-001 materializar) | Postmortem + auditoria de segurança externa + revisão completa de policies |

---

## Aprovação

- [ ] **Roldão (decisor):** aceita schema-shared + RLS + 2 roles? — pendente
- [ ] **Auditor 2 (multi-tenant — 1ª auditoria):** confirma que 3 críticos + 5 altos estão cobertos? — pendente
- [ ] **Auditor 6 (segurança):** confirma defesa em profundidade adequada? — pendente
- [ ] **Spike-MT-1..4 verde:** pendente (6 dias úteis)
