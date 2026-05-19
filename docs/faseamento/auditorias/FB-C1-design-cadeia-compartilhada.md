---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
frente: FB-C1 + FB-A2 + FB-A3 (acoplado a FB-C3 — ver §Correções)
revisor: tech-lead-saas-regulado
veredito: APROVA COM CORREÇÕES (3 bloqueantes — absorvidas)
---

# FB-C1 — Design: cadeia hash authz por-tenant via helper compartilhado

> Núcleo F-A saneado (`audit/services.py`) + núcleo F-B (`authz/
> django_provider.py`). Toca código F-A já fechado → review tech-lead
> obrigatório antes do implement. Estado real verificado (Regra #0).

## Estado real verificado

- `authz/django_provider.py:62-64` `_hash_linha`: `sha256((hash_anterior +
  json.dumps(sort_keys=True, ensure_ascii=False, default=str)).encode())`.
- `audit/hash_chain.py:20-24` `calcular_hash`: `sha256(hash_anterior_bytes
  || canonicalizar_bytes)` — **byte-concat**, e `canonicalizar` usa
  `separators=(",",":")` (compacto) + serializer tipado (datetime naive =
  fail-loud). **Os dois algoritmos divergem** → trilhas authz e audit têm
  hashes incompatíveis (débito de auditoria: impossível verificação
  cruzada/uniforme).
- `authz/django_provider.py:219-224`: `select_for_update().order_by(
  "-timestamp").first()` — lock de linha existente NÃO barra INSERT
  concorrente; `timestamp` colide em µs (o bug que FA-C1 matou). Sem
  coluna `sequencia` em `AuthzDecision` (model:116-194, `Meta.ordering=
  ["-timestamp"]`).
- `audit/services.py` pós-FA-C1/FA-M3: `registrar_auditoria` faz
  `transaction.atomic()` → `pg_advisory_xact_lock(CLASSE, hashtext(chave))`
  → `_obter_hash_anterior(tenant_id)` (filtra tenant, ordena `-sequencia`)
  → `calcular_hash(anterior, canonicalizar(payload))` → `create`. Padrão
  provado e reauditado verde (F-A rodada 2).
- `audit/migrations/0009`: template de coluna `sequencia` via
  `CREATE SEQUENCE` + `ADD COLUMN DEFAULT nextval` (DDL, não UPDATE — não
  bate na RLS) + `state_operations`.

## Decisão de design

### 1. Helper de cadeia compartilhado em `audit/services.py`

Extrair o padrão de `registrar_auditoria` para função genérica reusável
por qualquer tabela INSERT-only com cadeia hash por-tenant:

```
def registrar_em_cadeia(
    model: type[models.Model],
    *,
    chave_cadeia: str,          # str(tenant_id) ou "SYSTEM"
    tenant_id: UUID | None,
    payload_hash: dict,         # o que entra no hash (canonicalizado)
    campos: dict,               # colunas a persistir (inclui tenant_id etc)
) -> models.Model
```

- Abre `transaction.atomic()` + `pg_advisory_xact_lock(
  _ADVISORY_LOCK_CLASSE_<X>, hashtext(chave_cadeia))`. **Namespace de
  classe SEPARADO por tabela** (`_ADVISORY_LOCK_CLASSE_AUDIT` para
  `auditoria`, novo `_ADVISORY_LOCK_CLASSE_AUTHZ` para `authz_decisions`)
  — não serializar trilhas distintas entre si nem colidir hashtext.
- `_obter_hash_anterior` generalizado → `_ultimo_hash_da_cadeia(model,
  tenant_id)`: `model.objects.order_by("-sequencia")` + filtro
  `tenant_id__isnull=True` se None senão `tenant_id=tenant_id`
  (idêntico ao FA-C1, agora paramétrico no model).
- `hash_atual = calcular_hash(hash_anterior, canonicalizar(payload_hash))`
  — **algoritmo único** (mata a divergência). `registrar_auditoria` passa
  a CHAMAR `registrar_em_cadeia(Auditoria, ...)` (refator sem mudar
  comportamento — testes T1-T8 FA-C1 continuam verdes = prova de não-
  regressão).
- Sem `select_for_update` (o advisory lock por-chave-de-cadeia é a trava
  real — FA-A3/FB-A3 resolvido). Caller NÃO abre atomic próprio (FB-A2:
  o helper é a fronteira transacional, igual `registrar_auditoria` hoje).

### 2. `AuthzDecision.sequencia` (migration espelhando audit/0009)

`authz/migrations/0004_authzdecision_sequencia.py`: `CREATE SEQUENCE
authz_decisions_seq` + `ADD COLUMN sequencia BIGINT NOT NULL DEFAULT
nextval(...)` + índice `(tenant_id, sequencia)` + `state_operations`
AddField. `Meta.ordering` → `["sequencia"]`. Dependência:
`("authz","0003_seed_perfis")` + `("audit","0009_auditoria_sequencia")`
(garante ordem; o helper compartilhado vive em `audit`).

### 3. `django_provider._gravar_audit` delega

Monta `payload_hash` (campos semânticos da decisão) + `campos` (colunas) e
chama `registrar_em_cadeia(AuthzDecision, chave_cadeia=str(tenant_id) if
tenant_id else "SYSTEM", tenant_id=tenant_id, ...)`. Remove `_hash_linha`,
`_canonicalizar_payload`, `select_for_update`, e o `with
transaction.atomic()` aninhado do `can()` (FB-A2). Apaga código morto.

## Não-objetivos

- NÃO mudar o algoritmo do `audit` (mantém `calcular_hash`/`canonicalizar`
  — é o padrão correto; quem converge é o authz). Testes FA-C1 provam.
- NÃO reescrever migrations aplicadas. Migration nova aditiva.
- FB-C2/C3/C4/C5 são frentes separadas (não entram aqui).
- NÃO mexer no trigger PG anti-mutation authz (já existe; FB-C3 trata a
  policy `modo_sistema`).

## Pontos para o tech-lead

- (P1) `registrar_em_cadeia` genérico em `audit/services.py` — abstração
  honesta ou acopla `audit`↔`authz`? Alternativa: helper em
  `audit/hash_chain.py` (camada mais baixa, sem model). Recomendo
  `audit/services.py` (já tem lock+tx+canon juntos; authz importar de
  infra→infra é ok).
- (P2) Namespace de advisory lock por tabela (classe distinta) — concordas
  que `auditoria` e `authz_decisions` NÃO devem compartilhar o mesmo
  espaço de lock (senão um insert de audit serializa um can())?
- (P3) `registrar_auditoria` virar wrapper fino de `registrar_em_cadeia`
  sem regressão — os testes T1-T8 FA-C1 + drill cobrem? Algum risco no
  `payload` vs `payload_jsonb` (Auditoria tem coluna `payload_jsonb`;
  o que entra no hash é o canonicalizado do `payload` original).
- (P4) Migration `authz/0004` depende de `audit/0009`? Necessário só se o
  helper exigir a sequence de audit — não exige (cada tabela tem sua
  sequence). A dep é só pra ordem determinística de leitura do helper?
  Avaliar se a dep dupla é mesmo necessária ou ruído.

## Correções absorvidas (review tech-lead 2026-05-18) — APROVA COM CORREÇÕES

3 bloqueantes antes do `/implement`:

- **(BLOQ #1 — DESCOBERTA CRÍTICA: FB-C1 ⇄ FB-C3 acoplados)** A policy
  real `authz_decisions_select` libera linha `tenant_id IS NULL` (cadeia
  "sistema"/pré-tenant) **só quando `current_setting('app.usuario_id',
  true)=''`**. Mas decisão pré-tenant autenticada (ex.: "listar meus
  tenants") roda com o usuário JÁ identificado (`app.usuario_id` setado,
  ≠ ''). Logo `_ultimo_hash_da_cadeia(AuthzDecision, tenant_id=None)`
  NÃO enxerga o elo anterior → toda decisão pré-tenant vira "primeira
  linha" → cadeia sistema authz **bifurca/reinicia silenciosamente**.
  O `run_as_system()` (modo_sistema='1') do padrão FA-C1 NÃO está ativo
  nesse fluxo. **Conclusão:** FB-C1 não pode copiar cego o padrão FA-C1;
  **FB-C1 e FB-C3 têm que ser desenhados/implementados JUNTOS** — a
  policy precisa permitir ler/gravar a cadeia pré-tenant authz no
  contexto real onde ela acontece. Opções a decidir no design conjunto:
  (a) policy pré-tenant baseada em `usuario_id = current_setting(
  'app.usuario_id')` (cadeia pré-tenant POR-USUÁRIO, não global — cada
  usuário só vê/encadeia as próprias decisões pré-tenant; elimina o
  problema de visibilidade E o de cadeia global cross-user); (b) `can()`
  pré-tenant envelopar a gravação em `run_as_system()` (custo: toda
  decisão de login passa por modo_sistema — risco de escopo). **Recom.
  preliminar: (a)** — cadeia pré-tenant por-usuário é semanticamente
  correta (a "cadeia sistema" do audit existe pra eventos sem dono;
  decisão authz pré-tenant TEM dono: o usuário). Reabrir FB-C1 design
  como **FB-C1+C3 conjunto** antes de implementar. Provar com teste:
  2 `can()` pré-tenant consecutivos do mesmo usuário fora de contexto de
  tenant → encadeiam; usuário B não vê cadeia pré-tenant de A.
- **(BLOQ #2 — canon fail-loud na borda)** `resource` vem da view (pode
  ter `set`, objeto Django, datetime naive); `canonicalizar._serializar`
  faz `raise TypeError` fora de {datetime,date,Decimal,UUID}. Como
  `can()` está em transação, vira erro opaco que derruba a autorização
  inteira (pior que o bug atual com `default=str`). Conserto: normalizar
  `resource`/payload authz pra JSON-safe ANTES do hash, na borda de
  `can()`, com validação explícita + teste unhappy (tipo inválido →
  erro claro e cedo, não TypeError dentro da transação). NÃO diferir.
- **(BLOQ #3 — P4 era ruído)** `authz/0004` depende **apenas** de
  `("authz","0003_seed_perfis")`. REMOVIDA a dep falsa a `audit/0009`
  (cada tabela tem sua sequence; helper é runtime, não schema).
- Não-bloqueantes: `_ADVISORY_LOCK_CLASSE_AUTHZ` constante distinta e
  visível (ex.: `0x_A07_2EC`) + comentário ligando INV-AUTHZ-002; o
  helper genérico NÃO importa `Auditoria` no corpo (só recebe `model`);
  `test_audit_cadeia_por_tenant.py` deve passar SEM 1 caractere alterado
  (contrato de não-regressão); +5 testes obrigatórios (login pré-tenant
  encadeia sem 42501; isolamento de lock entre tabelas; round-trip canon
  authz com tipos ricos; unhappy resource inválido; T1-T8 intactos).

## Próximo passo (retomar)

FB-C1 vira **FB-C1+C3 conjunto**. Reabrir o design contemplando a cadeia
pré-tenant authz POR-USUÁRIO (recomendação preliminar (a) do BLOQ #1),
revisar de novo com tech-lead, então implementar com os 5 testes +
não-regressão T1-T8. As tarefas #11 e #15 passam a ser uma só frente.
