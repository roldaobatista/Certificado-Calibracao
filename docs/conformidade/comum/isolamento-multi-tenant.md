---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0012-autorizacao-unificada.md
  - docs/adr/0015-lifecycle-tenant.md
  - docs/conformidade/comum/lgpd-rat.md
  - docs/conformidade/comum/seguranca-dados.md
  - docs/conformidade/comum/retencao-matriz.md
  - REGRAS-INEGOCIAVEIS.md
  - INV-TENANT-001
  - INV-TENANT-002
  - INV-TENANT-003
  - INV-TENANT-004
  - INV-AUTHZ-001
  - INV-AUTHZ-002
  - INV-AUTHZ-003
  - INV-INT-007
  - INV-013
---

# Isolamento Multi-Tenant — base de conformidade MVP-1

> **Pra quê:** este documento explica, de ponta a ponta, como o Aferê separa os dados de cada cliente (cada laboratório, cada assistência técnica) dentro de um banco de dados único e compartilhado, de forma que **nunca** um cliente veja dados de outro — nem por engano, nem por má-fé, nem por bug. É o documento que auditor RBC/CGCRE, ANPD (LGPD) e cliente corporativo (due diligence) leem antes de aceitar o Aferê como fornecedor. Reúne em um lugar: o modelo de dados, as travas do banco, as decisões de autorização, o apagamento por cliente (LGPD direito ao esquecimento), os backups, a auditoria e os testes que provam que tudo isso funciona.
>
> **Status (2026-05-17):** documento normativo. Implementação técnica depende da Foundation F-A (estofo multi-tenant + RLS + audit) que só começa após Portões 2+3 da ADR-0001 e dos 4 spikes da ADR-0002 (Spike-MT-1..4) — não há código de produto ainda.

---

## Pra dono (resumo em 5 linhas)

- Cada cliente do Aferê tem um "carimbo" único (chamado `tenant_id`) gravado em toda linha de tabela do banco que tem dado dele.
- A "tranca do banco" (RLS — uma trava feita pelo próprio PostgreSQL) garante que mesmo se o nosso código errar, o banco recusa entregar dado de outro cliente.
- A decisão de "esse usuário pode fazer esse clique?" passa por **um lugar só** no sistema (a porta `AuthorizationProvider`), que grava tudo numa trilha imutável — qualquer auditor (RBC, ANPD) sabe exatamente quem viu o quê e quando.
- O "direito ao esquecimento" da LGPD é resolvido por **revogar a chave do cliente** na AWS — os dados ficam no disco como lixo cifrado ilegível, sem precisar mexer linha a linha.
- A retenção legal (Receita 5 anos, ISO 17025 ~25 anos) **vence** sobre o pedido de apagamento — esperamos o fim do prazo legal antes de revogar a chave.

---

## 1. Status de pendência das implementações

| Invariante | Documento existe? | Hook automatizado existe? | Código existe? | Quando entra |
|---|---|---|---|---|
| INV-TENANT-001 (toda query tem `tenant_id`) | sim (REGRAS-INEGOCIAVEIS) | **falta** (`tenant-id-validator.sh`) | não | Foundation F-A |
| INV-TENANT-002 (toda tabela tem coluna `tenant_id`) | sim | **falta** (migration linter) | não | Foundation F-A |
| INV-TENANT-003 (RLS ativa em toda tabela) | sim | **falta** (migration linter) | não | Foundation F-A |
| INV-TENANT-004 (role NOBYPASSRLS + NOSUPERUSER) | sim | **falta** (CI gate) | não | Foundation F-A |
| INV-AUTHZ-001 (decisão única na porta) | sim (ADR-0012) | **falta** (`authz-check.sh`) | não | Foundation F-B |
| INV-AUTHZ-002 (audit trail síncrono imutável) | sim | **falta** (migration linter + release gate) | não | Foundation F-B |
| INV-AUTHZ-003 (RLS aceita lista de tenants) | sim | **falta** (migration linter pattern) | não | Foundation F-B |
| INV-INT-007 (provisioning atômico) | sim (ADR-0015) | **falta** (`provisioning-checkpoint-check`) | não | Onda Wave A |
| INV-013 (log de visualização de PII de cliente) | sim | parcial (decorator `@classified`) | não | Wave A |

**Resumo:** 3 hooks complementares precisam ser criados como bloqueantes da Foundation F-A:
1. `tenant-id-validator.sh` — bloqueia query que não passa pelo helper de contexto tenant
2. `migration-linter` (Python) — verifica `tenant_id NOT NULL` + policy RLS v2 + trigger imutabilidade em audit
3. `authz-check.sh` — bloqueia endpoint Django novo sem chamada de `AuthorizationProvider.can()`

(Ver AGENTS.md §12 "O que está pendente" — esta seção é o status atualizado.)

---

## 2. Modelo de dados — o "carimbo" `tenant_id`

### 2.1 Regra geral

**Toda tabela com dado de cliente carrega uma coluna `tenant_id UUID NOT NULL`** (INV-TENANT-002). Sem exceção:

- Tabelas de domínio (ex: `os`, `certificado`, `instrumento`, `cliente_final`, `colaborador`, `fatura`)
- Tabelas de auditoria de tenant (ex: `audit_trail.acessos_dados_cliente`, `audit_trail.authz_decisions`)
- Tabelas de configuração por tenant (ex: `configuracao_sistema`, `feature_flag_tenant`, `template_pdf`)

### 2.2 Tabelas de autenticação — quando carregam e quando não

| Tabela | Carrega `tenant_id`? | Explicação |
|---|---|---|
| `auth_usuario` (cadastro de pessoa) | **não** (ou nullable) | Um usuário pode pertencer a N tenants (parceiro marketplace, auditor RBC visitante multi-laboratório); o vínculo está em `auth_usuario_perfil` |
| `auth_usuario_perfil` (vínculo M:N user × tenant + papel + validade) | **sim** — é a fonte de verdade do middleware (ADR-0012) |
| `auth_perfil` (catálogo de papéis) | nullable | NULL = perfil global Aferê; UUID = perfil customizado de tenant |
| `auth_perfil_acao` (matriz papel × ação) | herda do perfil |
| `auth_sessao` (sessões ativas) | **sim** — escopo da sessão é tenant ativo |

### 2.3 Tabelas de plano-de-controle (NÃO carregam `tenant_id`)

Listagem fechada e revisada com cuidado — qualquer adição passa por revisão humana via CODEOWNERS:

- `tenants` (lista mestra de tenants)
- `planos` (catálogo de planos billing-saas)
- `feature_flags_globais` (definição global de features; o estado por tenant fica em `tenant_features`)
- `migrations_django` (histórico de migrations)
- `aferere_admins` (usuários internos Aferê — Roldão + futuros funcionários Aferê)
- `kms_chaves_tenant` (mapeamento `tenant_id` → `kms_key_arn`; tabela é por-tenant na chave, mas o tenant não consulta — só plano-de-controle)

Toda tabela aqui tem comentário SQL `-- SHARED ACROSS TENANTS` e migração que cria é revisada manualmente.

### 2.4 Comportamento por tipo de tabela

| Tipo de tabela | `tenant_id` | RLS ativa? | Acesso |
|---|---|---|---|
| Domínio (OS, certificado, cliente final…) | obrigatório NOT NULL | sim, policy v2 (lista) | role `app_user` filtra pela lista de tenants do request |
| Audit trail por tenant (acessos, authz_decisions) | obrigatório NOT NULL | sim, append-only via trigger | role `app_user` lê (lista); ninguém escreve fora da porta authz |
| Plano-de-controle (tenants, planos, kms_chaves_tenant) | NÃO | NÃO | role `app_admin_readonly` (Roldão Aferê); `app_user` NÃO acessa |
| Tabelas analíticas (BI — ADR-0011) | sim (espelho) | sim, mesma policy | role `app_bi_readonly` separada; replicação assíncrona |

---

## 3. Policy RLS v2 — lista de tenants

### 3.1 Pattern obrigatório

Toda policy RLS de tabela de domínio segue **exatamente** este pattern (INV-AUTHZ-003):

```sql
-- SELECT: usuário vê linhas cujo tenant_id está na lista permitida
CREATE POLICY tenant_isolation_select ON <tabela>
  FOR SELECT
  USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

-- INSERT: sempre grava no tenant ATIVO (o "onde a ação acontece")
CREATE POLICY tenant_isolation_insert ON <tabela>
  FOR INSERT
  WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

-- UPDATE: pode atualizar linha dentro da lista, mas não pode mudar tenant_id
CREATE POLICY tenant_isolation_update ON <tabela>
  FOR UPDATE
  USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
  WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

-- DELETE: idem
CREATE POLICY tenant_isolation_delete ON <tabela>
  FOR DELETE
  USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));
```

### 3.2 Por que LISTA (e não um único tenant)

Três cenários reais quebram "1 usuário = 1 tenant":

1. **Marketplace de parceiros (Wave B+):** parceiro que vende plugin para N tenants — precisa ver os dados de pedido dele em cada um.
2. **Portal cliente matriz + filiais:** uma empresa cliente final tem CNPJ matriz + N CNPJs filiais; o usuário responsável pelo grupo precisa ver todos juntos.
3. **Auditor RBC visitante:** auditor da Cgcre visitando 3 laboratórios diferentes na mesma janela de auditoria — acesso temporário aos 3 simultaneamente.

A policy v2 resolve os 3 sem brecha: a lista vem **sempre** da tabela `auth_usuario_perfil` (M:N user × tenant com `valido_de/ate`), e o middleware nunca aceita lista vinda do cliente.

### 3.3 Sem fallback permissivo (failure mode = blocking)

**Banido:**
```sql
-- ERRADO — se app.tenant_ids não setado, retorna NULL → policy libera tudo
current_setting('app.tenant_ids', true)
```

**Correto:**
```sql
-- Sem o segundo argumento, current_setting() levanta erro
-- "unrecognized configuration parameter" se não setado → request falha duro
current_setting('app.tenant_ids')
```

Falhar duro é o comportamento desejado — vazamento silencioso é inaceitável.

### 3.4 Role do app — NOBYPASSRLS + NOSUPERUSER (INV-TENANT-004)

```sql
CREATE ROLE app_user WITH
  LOGIN PASSWORD '...'
  NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION;
```

Hook de CI valida `current_setting('is_superuser') = 'off'` antes de cada deploy. Docker Compose mal configurado rodando o Django como `postgres` superuser anula toda a RLS — esse é o vetor #1 de vazamento determinístico (Auditor 2 da 1ª auditoria 10 agentes 17/05/2026).

---

## 4. Middleware `tenant_id` — implementação

### 4.1 Responsabilidades (em ordem)

1. **Extrair `user_id`** do JWT (mobile Flutter) ou da session (web HTMX).
2. **Consultar `auth_usuario_perfil`** pra resolver a lista de tenants vigentes (`valido_de ≤ now() ≤ valido_ate`) — **fonte única de verdade**.
3. **Validar tenant "ativo"** que o cliente passou (header `X-Aferê-Active-Tenant` ou query param) — deve estar dentro da lista resolvida. Se não passou e a lista tem 1 só → default.
4. **Setar contexto PG** dentro de transação aberta:
   ```sql
   SET LOCAL app.tenant_ids = '<uuid1>,<uuid2>,...';
   SET LOCAL app.active_tenant_id = '<uuid_ativo>';
   ```
5. **Limpar contexto** no `finally` (importantíssimo pra pool de conexões — sem `SET LOCAL` reset, próximo request herda contexto do anterior).

### 4.2 Princípio inviolável

**O middleware NUNCA aceita lista de tenants vinda do cliente.** Cliente só indica qual tenant está "ativo agora" (escopo do request); middleware extrai a lista de `auth_usuario_perfil` e valida que o ativo está dentro dela.

### 4.3 Wrapper Celery (jobs em background)

Toda task Celery que toca tabela com RLS **deve** rodar via wrapper `run_in_tenant_context`:

```python
from infrastructure.queue.provider import run_in_tenant_context

@shared_task
def emit_invoice_task(tenant_id: str, invoice_id: str):
    with run_in_tenant_context(tenant_id):
        invoice = Invoice.objects.get(id=invoice_id)
        # SET LOCAL aplicado, transação aberta
```

Lint custom `semgrep` bloqueia merge de `@shared_task` sem o wrapper. Sem o wrapper, job sem contexto **falha** (não vaza) — comportamento desejado.

### 4.4 Cuidado com testes pytest

Fixture explícita `with_tenant_context(tenant_id)` deve ser declarada em cada teste que toca o banco. Sem ela, o teste falha — replica o comportamento de produção.

```python
@pytest.fixture
def tenant_context(db):
    with run_in_tenant_context(uuid.uuid4()) as ctx:
        yield ctx
```

### 4.5 Guarda automático contra queries cruas

Hook `tenant-id-validator.sh` (pré-commit + CI) bloqueia merge se encontrar:

```python
# ❌ PROIBIDO fora de infrastructure/multitenant/
cursor = connection.cursor()
cursor.execute("SELECT * FROM ...")

# ✅ PERMITIDO
with run_in_tenant_context(tenant_id):
    qs = Model.objects.filter(...)
```

Exceção única: pasta `infrastructure/multitenant/` pode ter raw queries (revisadas por CODEOWNERS).

---

## 5. Crypto-shredding por tenant — LGPD direito ao esquecimento

### 5.1 Mecanismo

Cada tenant tem **uma chave dedicada na AWS KMS Multi-Region Key** (sa-east-1 primária ↔ us-east-1 réplica — sem cópia manual):

- `kms_chaves_tenant.kms_key_arn` aponta para a chave do tenant
- Dados sensíveis (PII, fiscais, dados de medição com identificadores de cliente) são cifrados em coluna usando **Fernet/AES-256** com chave do tenant
- A trilha imutável em Backblaze B2 (WORM) é gravada cifrada com a mesma chave

### 5.2 Apagamento por revogação

Quando o tenant exerce o direito ao esquecimento (LGPD art. 18 VI) ou termina o contrato + janela de retenção:

1. **Revoga-se a chave KMS** do tenant (`aws kms schedule-key-deletion`)
2. Os dados continuam fisicamente no disco e na trilha WORM, mas viram **lixo cifrado ilegível**
3. **Não precisamos varrer milhões de linhas** para apagar — é uma operação atômica
4. Backups antigos também viram ilegíveis (mesma chave revogada)

### 5.3 Retenção legal vence sobre apagamento

| Categoria | Prazo legal | Pode revogar antes? |
|---|---|---|
| Documento fiscal (NF-e/NFS-e) | Receita 5 anos (art. 173 CTN) | **não** |
| Certificado de calibração ISO 17025 | ~25 anos (cl. 8.4) | **não** |
| Audit trail acessos | 5 anos mínimo | **não** |
| Cadastro de cliente final | 5 anos após fim de contrato | **não** |
| Mensagens WhatsApp/e-mail operacionais | 1-2 anos | sim, sob demanda |
| Telemetria + analytics | 13 meses | sim, anonimização automática |

Detalhamento completo em `docs/conformidade/comum/retencao-matriz.md`. Direito ao esquecimento espera o **fim do prazo legal** antes de revogar a chave.

### 5.4 O que NÃO é crypto-shredding

- **Não é "delete físico"** — dados ficam no disco, apenas ilegíveis
- **Não é reversível** — chave revogada na AWS KMS não volta (período de espera 7-30 dias antes da deleção definitiva)
- **Não substitui RLS** — defesa em profundidade: durante o ciclo de vida, RLS protege; ao fim, shredding finaliza

---

## 6. Matriz de comportamentos por evento de tenant

| Evento | Disparo | Comportamento por módulo | Invariante |
|---|---|---|---|
| `BillingSaas.AssinaturaCriada` | Cliente novo paga | Provisioning state machine 7 etapas (`NAO_INICIADO → … → PRONTO`); tenant não loga até `PRONTO` | INV-INT-007 (ADR-0015) |
| `BillingSaas.TenantSuspenso` (modo `read_only`) | Inadimplência leve | Sessões mantidas; mutações bloqueadas; emails enviados | INV-INT-009 |
| `BillingSaas.TenantSuspenso` (modo `bloqueado_total`) | Inadimplência grave | Sessões encerradas; login bloqueado; features desligadas em cascata | INV-INT-009 |
| `BillingSaas.TenantReativado` | Pagamento confirmado | Restauração inversa em ≤5min | INV-INT-009 |
| `BillingSaas.AssinaturaCancelada` | Fim de contrato | Janela de retenção (Receita 5a × ISO 25a × LGPD); depois revoga KMS | retencao-matriz |
| `BillingSaas.PlanoMudouModulos` | Upgrade/downgrade/addon | Sincroniza `tenant_features`; invalida cache Redis; força re-auth se feature crítica saiu | INV-INT-008 |
| Vínculo cross-tenant criado/expirado (`auth_usuario_perfil`) | Marketplace, auditor RBC, matriz+filial | Invalida cache de autorização; próximo request recalcula lista de tenants | INV-AUTHZ-003 |
| Acesso a PII de cliente | Qualquer query que envolve dado classe "regulado" | Grava `audit_trail.acessos_dados_cliente` síncrono | INV-013 |
| Decisão de autorização | Toda chamada `AuthorizationProvider.can()` | Grava `audit_trail.authz_decisions` síncrono + hash chain | INV-AUTHZ-002 |

---

## 7. Backup / restore — isolamento mantido

### 7.1 Backup

- **Default:** `pg_dump` full do banco, cifrado com chave KMS do plano-de-controle (não da tenant individual), agendado via pgBackRest
- **Por tenant (sob demanda — LGPD art. 18 portabilidade):** pipeline `export_tenant(tenant_id: UUID) -> ZipFile`:
  - Itera cada tabela com `tenant_id` filtrando
  - `COPY (SELECT * FROM <tabela> WHERE tenant_id = $1) TO STDOUT WITH CSV HEADER`
  - Inclui PDFs do B2 com prefix `tenant_id/`
  - ZIP cifrado com chave do tenant + link assinado válido por 72h

### 7.2 Restore em staging

- Restauração em ambiente de staging usa role `app_user` (NOBYPASSRLS) — outros tenants ficam "mascarados" automaticamente para o testador
- Para investigar incidente de tenant específico, abre-se sessão temporária com `SET LOCAL app.tenant_ids = '<uuid_alvo>'` + audit
- **Proibido** usar role `postgres` superuser para investigação rotineira

### 7.3 Drill mensal (cronograma ADR-0002)

- **1 drill obrigatório antes do 1º tenant pago:** RLS bypass — agente tenta esquecer `WHERE tenant_id`; mede que RLS bloqueia em <100ms
- Drill de export-por-tenant disparado quando 5 tenants pagos ativos
- Drill de restore-por-tenant: restaurar 1 tenant random + validar que RLS continua ativa + outros tenants invisíveis

---

## 8. Auditoria — quem viu / mudou o quê

### 8.1 Tabela `audit_trail.acessos_dados_cliente` (INV-013)

Append-only via trigger PG. Toda query que toca dado classe "regulado" (PII de cliente final, dados fiscais) grava linha:

| Campo | Conteúdo |
|---|---|
| `timestamp` | ISO 8601 UTC |
| `user_id` | UUID |
| `tenant_id` | UUID (escopo da consulta) |
| `recurso` | tabela + chave consultada (sem PII bruta) |
| `finalidade` | base LGPD ("execucao_contrato", "obrigacao_legal", "legitimo_interesse", …) |
| `ip_hash` | SHA-256 do IP **salgado por tenant** (HMAC com `tenant_id` da query) |

Retenção: 5 anos quente + cópia hourly Backblaze WORM.

**Exceção — Escopo C de QR público (INV-051):** scan anônimo sem sessão usa **salt institucional global do Aferê** (`settings.AFERE_AUDIT_GLOBAL_SALT`), NÃO `tenant_id` do equipamento. Razão: salgar com `tenant_id` do equipamento em audit de scan anônimo permitiria correlação cross-tenant em dump consolidado de scans públicos. Decisão pós-auditoria advogado US-EQP-003 R2 (2026-05-18). Audit de scan público fica em `audit_trail.eventos` action=`equipamento.qr_scanned` com `escopo=anonimo`. Detalhes técnicos: `docs/conformidade/equipamentos/qr-publico-allowlist.md` §3.

### 8.2 Tabela `audit_trail.authz_decisions` (INV-AUTHZ-002)

Toda decisão da porta `AuthorizationProvider.can()` grava:

| Campo | Conteúdo |
|---|---|
| `timestamp` | quando |
| `user_id` | quem pediu |
| `tenant_id` | em qual tenant |
| `action` | string `modulo.acao` |
| `resource_summary` | JSON resumido (sem PII cru) |
| `purpose` | finalidade LGPD |
| `decision` | `allowed` / `denied` |
| `reason` | string explicando |
| `perfis_aplicados` | array de UUIDs de perfis |
| `escopo_avaliado` | JSON com atributos ABAC consultados |
| `ip_hash` | SHA-256 |
| `hash_anterior` | SHA-256 da linha anterior (hash chain) |

Append-only via trigger PG (`BEFORE UPDATE/DELETE` rejeita); cópia hourly B2 WORM. Garantia anti-adulteração: quebra de hash chain dispara alerta P1.

### 8.3 Resposta a fiscalização

Pergunta típica ANPD: "Quem viu o CPF do cliente João Silva (CPF 123.456.789-00) em 2027-03-15?"

Resposta vem de uma query única:
```sql
SELECT user_id, timestamp, finalidade, ip_hash
FROM audit_trail.acessos_dados_cliente
WHERE tenant_id = '<tenant_do_joao>'
  AND recurso @> '{"cliente_final_id": "<uuid_joao>"}'
  AND timestamp::date = '2027-03-15';
```

Sem ponto único e audit síncrono, essa resposta é impossível.

---

## 9. Não-objetivos explícitos

Lista fechada do que **NÃO** vamos fazer (e por quê):

1. **NÃO usar schema-per-tenant.** TAM 100-5000 tenants — gerenciar 5000 schemas + cada migration rodando 5000× é insustentável. Reversão prevista em ADR-0002 só se TAM > 5000 ou cliente farma TOP exigir isolamento físico.
2. **NÃO usar database-per-tenant.** Mesma razão + custo Hostinger explode.
3. **NÃO confiar em filtro só na aplicação.** Defesa em profundidade exige aplicação + ORM + RLS + hooks/lint. Cada camada protege se a anterior falhar.
4. **NÃO confiar em `request.user.tenant_id` direto em views.** Middleware é único ponto de entrada — view consulta via helper que lê o contexto, nunca o request raw.
5. **NÃO permitir lista de tenants vinda do cliente.** Lista vem sempre de `auth_usuario_perfil`; cliente só indica tenant ativo.
6. **NÃO permitir role do app com BYPASSRLS / SUPERUSER.** Quebra RLS inteira. CI gate valida.
7. **NÃO permitir audit fire-and-forget.** Audit é síncrono na mesma transação da decisão — perda de evento = perda de prova jurídica.
8. **NÃO permitir `--no-verify` ou `eslint-disable` em arquivos sob `infrastructure/multitenant/`, `infrastructure/authz/`, `audit_trail/`.** CODEOWNERS bloqueia (D5).
9. **NÃO aceitar export cross-tenant via UI.** Relatório consolidado Roldão usa role separada `app_admin_readonly` com audit obrigatório, fora do fluxo normal.

---

## 10. Riscos conhecidos e mitigações

| Risco | Mitigação |
|---|---|
| Migration regerando ~50 policies RLS (v1 → v2 lista de tenants) | Script SQL automatizado (lê schema + emite policies); drill obrigatório em staging; janela de manutenção 5-10 min |
| Performance RLS (5-15% overhead em queries OLTP) | Índice composto `(tenant_id, ...)` em toda tabela quente; benchmark contínuo em Grafana |
| Lock contention em tabelas hot (`os`, `equipamento`) sob carga | Particionamento nativo PostgreSQL 11+ por `tenant_id` hash (gatilho TAM > 1000 tenants) |
| Cross-tenant query intencional (relatório consolidado Aferê) | Role `app_admin_readonly` separada + UI de admin Aferê + audit obrigatório + sem acesso UI tenant |
| Cache Redis vazando entre tenants | Chave de cache sempre prefixada com `tenant:{tenant_id}:`; lint custom valida |
| Read replica futura herdando RLS | Conexão da replica também aplica `SET LOCAL`; spike-MT-5 valida |
| Vínculo `auth_usuario_perfil` expirado mas sessão ativa | Middleware revalida a cada request (não confia em cache > 5min); evento de expiração invalida cache |
| Backup `pg_dump` cross-tenant por design | Export-por-tenant via pipeline dedicado para portabilidade LGPD; backup full é interno (chave KMS Aferê) |
| Tenant fantasma após falha no provisioning | State machine INV-INT-007 marca estado; tenants em estado != PRONTO não logam; alerta P1 em falha |

---

## 11. Como validar — testes obrigatórios

### 11.1 Spikes de validação (ADR-0002 — bloqueantes da Foundation F-A)

- **Spike-MT-1:** 100 requests simultâneas em 2 tenants, mesma view, mesma conexão de pool — zero vazamento
- **Spike-MT-2:** prepared statements + RLS — `current_setting` replanned a cada execução
- **Spike-MT-3:** 50 jobs Celery paralelos de 5 tenants — `run_in_tenant_context` isola; jobs sem wrapper falham
- **Spike-MT-4:** canary tenant sintético — alerta automático se aparecer em response cross-tenant

### 11.2 Testes de fuzzing concorrente (bloqueante Wave A)

| Cenário | Resultado esperado |
|---|---|
| Usuário com acesso a tenants {A, B} tenta GET `/api/os/<id_de_C>` | 403 Forbidden + log de tentativa em `authz_decisions` |
| Job Celery despachado sem `run_in_tenant_context` | Falha com erro claro `app.tenant_ids not set`; **não vaza** |
| View Django nova sem chamar `AuthorizationProvider.can()` | `authz-check.sh` bloqueia merge no pre-commit |
| Migration que cria tabela sem `tenant_id` | `migration-linter` bloqueia merge |
| Migration que cria tabela sem policy RLS | `migration-linter` bloqueia merge |
| Role do app com BYPASSRLS / SUPERUSER | CI gate bloqueia deploy |
| Bypass via role admin (cross-tenant intencional) | Audit obrigatório + alerta P2 se fora de janela autorizada |
| Cache Redis com chave sem prefix tenant | Lint custom bloqueia merge |

### 11.3 Drill mensal cronometrado (pós-MVP-1)

- RLS bypass: <100ms para bloquear
- Celery sem wrapper: <500ms para falhar
- Export por tenant: <60s para tenant com 10k registros
- Cross-tenant fuzzing: 0 vazamentos em 1000 queries randômicas

---

## 12. Referências

### ADRs
- `docs/adr/0002-multi-tenancy.md` — decisão arquitetural e policy RLS v2
- `docs/adr/0012-autorizacao-unificada.md` — porta AuthorizationProvider + 4 camadas
- `docs/adr/0015-lifecycle-tenant.md` — provisioning atômico + sync features + inadimplência

### Invariantes (`REGRAS-INEGOCIAVEIS.md`)
- INV-TENANT-001 — toda query SQL/ORM contém `tenant_id`
- INV-TENANT-002 — toda tabela com dado de cliente tem `tenant_id NOT NULL`
- INV-TENANT-003 — RLS ativa em toda tabela com `tenant_id`
- INV-TENANT-004 — role `app_user` NOBYPASSRLS + NOSUPERUSER
- INV-AUTHZ-001 — toda decisão passa pela porta `AuthorizationProvider.can()`
- INV-AUTHZ-002 — audit trail síncrono e imutável
- INV-AUTHZ-003 — RLS aceita lista de tenants (não 1 fixo)
- INV-INT-007 — provisioning atômico state machine 7 etapas
- INV-013 — log de visualização de dados de cliente (cl. 4.2 ISO 17025)

### Conformidade
- LGPD Lei 13.709/2018 — art. 6º (princípios), art. 18 (direitos do titular), art. 46-49 (segurança)
- Resolução CD/ANPD 15/2024 — incidentes
- ISO 17025 cl. 4.2 — imparcialidade e confidencialidade
- ISO 17025 cl. 8.3 — controle de documentos
- ISO 17025 cl. 8.4 — retenção (~25 anos)
- Receita Federal art. 173 CTN — retenção fiscal 5 anos

### Hooks (`.claude/hooks/`)
- `tenant-id-validator.sh` — **a criar** (bloqueante F-A)
- `authz-check.sh` — **a criar** (bloqueante F-B)
- `migration-linter` (Python) — **a criar** (bloqueante F-A)
- `bus-envelope-validator` — **a criar** (bloqueante Wave A — INV-INT-001..013)
- `secrets-scanner.sh` — existe
- `block-destructive.sh` — existe

### Documentos irmãos de conformidade
- `docs/conformidade/comum/lgpd-rat.md` — base LGPD
- `docs/conformidade/comum/seguranca-dados.md` — classificação + criptografia + controles
- `docs/conformidade/comum/retencao-matriz.md` — Receita 5a × ISO 17025 8.4 × LGPD
- `docs/conformidade/comum/dpia-modulos-novos.md` — avaliação de impacto por módulo
- `docs/conformidade/comum/incidente-anpd-modelo.md` — fluxo de incidente 72h
