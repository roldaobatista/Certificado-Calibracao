---
owner: tech-lead-saas-regulado
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-CLI-002
plano_revisado: docs/dominios/comercial/modulos/clientes/planos/US-CLI-002.md
veredito: APROVADO COM RESSALVAS
---

# Tech Lead Review — Plano US-CLI-002 (Visão 360° + audit acesso LGPD INV-013)

## Resumo executivo

Plano direção certa: AC-3 (INV-013) cravado com tabela própria e síncrono; AC-1 alavancando `auditoria` como timeline source enquanto módulos consumidores não existem; AC-2 com índice já adequado. Reuso de `auditoria` como leitura é aceitável **com 2 ressalvas**: o índice atual `ix_audit_tenant_ts` cobre AC-2, mas o filtro proposto `resource_summary=cliente_id` não é seletivo (campo é texto livre "Certificado #123 / Tenant X") — exige convenção formal de `action`/payload, não match em `resource_summary`. AC-3 tem 3 ressalvas técnicas críticas: commit-before-response precisa ser explícito (não basta `transaction.atomic`), `purpose` LGPD deve ser whitelist enum (não free text), e a nova tabela merece RLS+trigger espelhando o pattern `authz_decisions` (já existe — apenas duplicar SQL com nome novo). Nenhuma ressalva reabre a Story; todas fecham editando o plano antes de `/implement`.

## Veredito

**APROVADO COM RESSALVAS** (6 ressalvas — 3 críticas, 2 altas, 1 média).

---

## Ressalvas (ordem por gravidade)

### 1. CRÍTICA — AC-1: filtro `resource_summary=cliente_id` não é seletivo nem indexado

**Problema:** `resource_summary` em `src/infrastructure/audit/models.py:51-54` é texto livre de até 255 chars ("Certificado #123 / Tenant slug"). Não há índice sobre ele, e o conteúdo é humano-legível — não chave estável. Filtrar por `resource_summary=cliente_id` (T-CLI-034) falha por 2 motivos:

1. **Não escala:** sequential scan na tabela inteira filtrada por `tenant_id` (usa `ix_audit_tenant_ts`) + LIKE/igualdade em texto livre. Com 500 eventos do cliente em meio a 500k linhas do tenant, derruba o p95.
2. **Não é robusto:** qualquer mudança no formato de `resource_summary` quebra a query silenciosamente.

**Correção exigida:** estabelecer **convenção formal** no `payload_jsonb` (que é JSONB indexável):
- Toda linha de auditoria que toque um cliente DEVE conter `payload_jsonb->>'cliente_id'` = UUID do cliente.
- Criar índice expressional GIN ou BTREE:
  ```sql
  CREATE INDEX ix_audit_tenant_cliente_ts
    ON auditoria (tenant_id, ((payload_jsonb->>'cliente_id')::uuid), timestamp DESC);
  ```
- Atualizar `docs/governanca/trilha-auditoria-agentes.md` cravando o contrato `payload_jsonb.cliente_id` como obrigatório para qualquer `action` que afete cliente (`cliente.criado`, `cliente.mesclado`, `cliente.bloqueado`, futuras `os.criada`, `certificado.emitido`).
- Migration nova `0004_index_payload_cliente_id.py` no app audit, anotada `# tests-coverage:` (hook `policy-test-coverage`).

**Impacto:** sem isso, AC-2 (p95 < 1.5s) só passa em smoke sintético; cai em produção com volume real.

---

### 2. CRÍTICA — AC-3: `transaction.atomic` NÃO garante commit-before-response

**Problema:** plano (linha 27) diz "gravação síncrona antes da resposta". O endpoint via DRF dentro de `ATOMIC_REQUESTS=True` (pattern atual — `django_provider.py:90-93` confirma) faz `INSERT acessos_dados_cliente` e `SELECT` da timeline na **mesma transação** — o commit só acontece quando o handler retorna. Se um erro 5xx vazar entre o INSERT e o `Response(...)`, o INSERT da auditoria de acesso é descartado junto.

INV-013 exige registro **mesmo que a visualização falhe** — o ponto-chave é "alguém tentou olhar este cliente". `authz_decisions` resolveu isso aceitando trade-off (gravação dentro do atomic do request) porque a decisão `can()` é **pré-condição** — se ela falha, não há resposta a proteger. Em `visao-360` é diferente: a tentativa de acesso é o fato auditável, e ela pode falhar DEPOIS do INSERT.

**Correção exigida:** dois caminhos aceitáveis — recomendo o (A):

**A — Two-phase: commit do audit antes de tocar timeline** (preferido, simples)
```python
# T-CLI-034 — pseudocódigo
def visao_360(request, cliente_id):
    # 1. authz check (já grava authz_decisions na atomic do middleware)
    provider.can(usuario_id, "clientes.visao360", resource={"cliente_id": cliente_id}, purpose="execucao_contrato")

    # 2. Audit do acesso LGPD — transação PRÓPRIA, commit antes da timeline
    with transaction.atomic():
        registrar_acesso_dados_cliente(
            tenant_id=request.tenant_id,
            usuario_id=request.user.id,
            cliente_id=cliente_id,
            finalidade=AcessoFinalidade.VISAO_360_OPERACIONAL,
            ip_hash=sha256(request.META["REMOTE_ADDR"]),
        )
    # ↑ commit aqui (atomic fechou)

    # 3. Timeline em transação separada (ATOMIC_REQUESTS abre nova)
    eventos = ler_timeline(tenant_id, cliente_id, limit=200)
    return Response(eventos)
```

Isso exige **desligar `ATOMIC_REQUESTS` neste endpoint** OU usar `transaction.non_atomic_requests` decorator. Documentar a exceção no docstring.

**B — Defer log via savepoint + commit hook**
Mais complexo, sem ganho real aqui. Rejeito.

**Adicionar AC no plano:** AC-CLI-002-3.1 — "se a leitura da timeline falhar com erro, a linha de `acessos_dados_cliente` deve existir no banco". Teste correspondente: forçar exception após `registrar_acesso_dados_cliente` e verificar `count == 1`.

---

### 3. CRÍTICA — Reuso do app `audit` correto, mas falta RLS + trigger anti-mutation

**Problema:** T-CLI-031 fala "RLS pattern v2. Trigger anti-mutation (INV-013 estendida)" mas não detalha que essa é uma nova tabela = nova migration = hooks `migration-rls-check` E `audit-immutability-check` vão exigir SQL explícito.

**Decisão arquitetural confirmada:** **manter no app `audit` existente, NÃO criar app `lgpd-audit`.** Justificativa:
- A natureza é a mesma — trilha imutável append-only com tenant_id + RLS + trigger.
- Cardinalidade esperada (≤ 500 acessos/cliente/ano) é uma ordem de grandeza menor que `auditoria` geral; manter junto não cria pressão de partição.
- Separar em app dedicado triplicaria boilerplate (apps.py, migrations init, RLS bootstrap) sem ganho de modularidade — a fronteira certa é a **tabela**, não o app.
- `authz_decisions` segue o mesmo pattern (app `authz`, tabela própria, RLS+trigger) — consistência.

**Correção exigida no plano:**
- Renomear T-CLI-031 pra explicitar 3 entregáveis no SQL:
  1. `CREATE TABLE acessos_dados_cliente` (`tenant_id NOT NULL`, `cliente_id NOT NULL`, `usuario_id NOT NULL`, `finalidade text NOT NULL`, `ip_hash text NOT NULL`, `timestamp timestamptz DEFAULT now() NOT NULL`).
  2. `ENABLE/FORCE ROW LEVEL SECURITY` + 2 policies: `acessos_dados_cliente_select` (`tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ','))`) e `acessos_dados_cliente_insert` (`tenant_id = NULLIF(current_setting('app.active_tenant_id', true), '')::uuid`). UPDATE/DELETE sem policy = bloqueado por padrão.
  3. Trigger `acessos_dados_cliente_anti_update` + `acessos_dados_cliente_anti_delete` espelhando `authz_decisions_bloqueia_mutation` (migration 0002 authz).
- Anotar `# tests-coverage: tests/test_acesso_cliente_isolamento.py tests/test_acesso_cliente_imutavel.py` na migration (hook `policy-test-coverage` exige).
- INV-013 deve ser citada no docstring do trigger (já feito em `auditoria_anti_*` — replicar).

---

### 4. ALTA — `finalidade` precisa ser whitelist enum, não CharField livre

**Problema:** plano (linha 19, 31) menciona `finalidade` mas não tipa. INV-013 + LGPD art. 9 exigem **finalidade específica documentada** — string livre permite que código grave `"ver"` ou `""` e quebra auditoria.

**Correção exigida:** criar `class AcessoFinalidade(models.TextChoices)` em `src/infrastructure/audit/models.py` com valores cravados:
```python
class AcessoFinalidade(models.TextChoices):
    VISAO_360_OPERACIONAL = "visao_360_operacional", "Visão 360 operacional"
    SUPORTE_TICKET = "suporte_ticket", "Suporte a chamado/ticket"
    INVESTIGACAO_FRAUDE = "investigacao_fraude", "Investigação de fraude"
    AUDITORIA_INTERNA = "auditoria_interna", "Auditoria interna"
    OBRIGACAO_LEGAL = "obrigacao_legal", "Obrigação legal"
```
Campo `finalidade = CharField(choices=AcessoFinalidade.choices, max_length=50)`. Adicionar `CHECK constraint` no PG espelhando o enum (defesa em profundidade — alguém com raw SQL não escapa).

**Teste novo a adicionar em T-CLI-036:** `test_finalidade_fora_do_enum_levanta_erro` (tenta `finalidade="ver"` → 400/IntegrityError).

---

### 5. ALTA — Índice composto faltando + paginação cap

**Problema:**
- A tabela `acessos_dados_cliente` precisa de `Index(["tenant_id", "cliente_id", "-timestamp"])` pra suportar a query "últimos N acessos a este cliente" (relatório LGPD pro titular). Sem isso, em 12 meses o relatório vai degradar.
- T-CLI-034 "lista os primeiros 200 eventos" — bom, mas precisa ser **`LIMIT 200` server-side** com `ORDER BY timestamp DESC`, não slicing em Python pós-fetch (já visto bug similar em outros projetos). Cravar no plano.

**Correção exigida:** adicionar índice no `Meta.indexes` da nova model + cravar `LIMIT 200` no `services.py` do app audit (não na view).

---

### 6. MÉDIA — Não-objetivo declarado mas faltando 1 explícito

**Problema:** plano declara non-goals (UI, eventos de módulos futuros, cache, paginação rica). Falta um non-goal explícito que evita gold-plate em Marco 1:

**Adicionar:** "Relatório LGPD pro titular (lista de quem acessou meus dados) — Wave A. Esta US só GRAVA; consumir vem depois."

Isso evita que alguém puxe pra cá o endpoint de leitura `GET /api/v1/lgpd/acessos-meus-dados/` que pertence a outro módulo (`portal-cliente` ou `lgpd`).

---

## Pontos fortes

- Reuso correto da `auditoria` como leitura — evita duplicar timeline e mantém consistência (single source of truth pra eventos).
- Decisão certa de NÃO criar app `lgpd-audit` (overhead sem ganho — fronteira é tabela, não app).
- Trigger anti-mutation + RLS já é pattern conhecido (`authz_decisions`, `auditoria`) — reuso direto reduz risco.
- AC-3 isolado em tabela própria (não polui `auditoria` com semântica LGPD) — boa separação.
- Lista de 7 testes em T-CLI-036 cobre os cenários certos (cross-tenant via RLS, cross-cliente, perfil sem permissão, imutabilidade).

## Sugestão de teste adicional

Além dos 7 já listados, acrescentar:
1. **`test_visao_360_grava_audit_acesso_mesmo_quando_timeline_falha`** — força exception após `registrar_acesso_dados_cliente`; verifica que linha persistiu (cobre ressalva #2).
2. **`test_acesso_dados_cliente_index_payload_cliente_id_usado`** — `EXPLAIN` confirma uso do índice expressional (cobre ressalva #1).
3. **`test_finalidade_fora_do_enum_levanta_erro`** — DB-level CHECK + Django choices (cobre ressalva #4).

## Limites desta revisão

Não validei comportamento em concorrência (2 acessos simultâneos ao mesmo cliente). Pattern de `pg_advisory_xact_lock` usado em `audit/services.py:48` é para hash chain — aqui não há cadeia, então **não precisa lock**. Mas se LGPD pedir ordenação determinística entre acessos simultâneos, considerar. Recomendo deixar como está e revisitar se métrica de drill mostrar gap.

Não cobri aspecto regulatório de "finalidade" (LGPD art. 9 + art. 18) — escalado pro `advogado-saas-regulado` em paralelo (já agendado no plano §"Subagentes a consultar").
