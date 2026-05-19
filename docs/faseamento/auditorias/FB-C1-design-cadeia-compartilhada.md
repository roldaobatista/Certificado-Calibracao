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

---

# FB-C1+C3 CONJUNTO — design reaberto (rodada 2)

> Reabertura pós-BLOQ #1. Estado real RE-verificado 2026-05-18 (Regra #0).
> Substitui as decisões §"Decisão de design" acima onde conflitar; mantém
> não-objetivos e contrato de não-regressão T1-T8.

## Estado real RE-verificado

- **Policy `authz_decisions_select`** (`authz/0002:76-81`): libera
  `tenant_id IS NULL` **só** com `current_setting('app.usuario_id',
  true) = ''`. Decisão pré-tenant autenticada ("listar meus tenants",
  login pós-credencial) roda com `app.usuario_id` SETADO (≠ '') → o
  helper não enxerga o elo anterior → **cadeia pré-tenant bifurca**.
- **`run_as_system`** (`connection.py:124-150`): `usuario_id=None`,
  `tenant_ids=[]`, `modo_sistema=True` → `app.modo_sistema='1'`,
  `app.usuario_id=''`. É o sinal canônico FA-C1.
- **`app.tenant_ids` no select policy authz**: usado SEM o 2º arg
  `, true` (`current_setting('app.tenant_ids')`) — diverge do resto do
  código (connection.py reseta via `RESET`; sem `, true` levanta erro se
  GUC nunca setado na sessão). Latente; corrigido no rewrite.
- **`_hash_linha`** authz: `sha256(hash_anterior + json.dumps(default=
  str))`. Diverge de `calcular_hash` (byte-concat + `canonicalizar`
  `separators=(",",":")`). Trilhas authz e audit têm hashes
  incompatíveis (débito de verificação cruzada).
- **`AuthzDecision`** sem `sequencia`; `Meta.ordering=["-timestamp"]`;
  `select_for_update().order_by("-timestamp").first()` — NÃO trava
  INSERT concorrente; timestamp colide em µs.
- **Testes que ordenam authz por timestamp**:
  `test_authz_audit_imutavel.py:132` (`order_by("timestamp")`). NÃO é
  T1-T8 (esses são `audit`). Será migrado pra `order_by("sequencia")`
  (correção alinhada ao novo invariante — não-mascaramento).

## Decisão de design (conjunto)

### 1. Helper genérico `registrar_em_cadeia` em `audit/services.py`

Partição da cadeia descrita por **2 parâmetros explícitos** (não mais só
`tenant_id`), pois a cadeia pré-tenant authz é POR-USUÁRIO:

```
def registrar_em_cadeia(
    model: type[models.Model],
    *,
    classe_lock: int,            # _ADVISORY_LOCK_CLASSE_AUDIT | _AUTHZ
    chave_cadeia: str,           # str(tenant_id) | f"U:{usuario_id}"
    cadeia_filtro: dict,         # ORM kwargs p/ ler o elo anterior
    payload_hash: dict,          # entra no hash (canonicalizado)
    campos: dict,                # colunas a persistir
) -> models.Model
```

- `transaction.atomic()` + `pg_advisory_xact_lock(classe_lock,
  hashtext(chave_cadeia))`. **`classe_lock` é parâmetro** —
  `_ADVISORY_LOCK_CLASSE_AUTHZ = 0x_A07_2EC` (constante distinta,
  comentário ligando INV-AUTHZ-002). Trilhas `auditoria` e
  `authz_decisions` NÃO compartilham espaço de lock.
- Elo anterior: `model.objects.filter(**cadeia_filtro).order_by(
  "-sequencia").first()`. Genérico — NÃO importa `Auditoria` nem
  `AuthzDecision` no corpo.
- `hash_atual = calcular_hash(hash_anterior, canonicalizar(
  payload_hash))` — **algoritmo único** (mata divergência).
- Sem `select_for_update`; caller NÃO abre `atomic` próprio (helper é a
  fronteira transacional — FB-A2/FB-A3 resolvidos pelo advisory lock).
- `registrar_auditoria` vira wrapper fino:
  `cadeia_filtro = {"tenant_id__isnull": True}` se `tenant_id is None`
  senão `{"tenant_id": tenant_id}`; `chave_cadeia="SYSTEM"` / `str(tid)`;
  `classe_lock=_ADVISORY_LOCK_CLASSE_AUDIT`. **Reproduz byte-a-byte o
  comportamento atual → T1-T8 passam sem 1 caractere alterado.**

### 2. `AuthzDecision.sequencia` — `authz/0004` (espelha audit/0009)

`CREATE SEQUENCE authz_decisions_seq` + `ADD COLUMN sequencia BIGINT NOT
NULL DEFAULT nextval(...)` + índice `(tenant_id, sequencia)` +
`state_operations` AddField. `Meta.ordering=["sequencia"]`.
**`dependencies = [("authz","0003_seed_perfis")]` APENAS** (BLOQ #3 —
dep falsa a `audit/0009` removida; cada tabela tem sua sequence).

### 3. FB-C3 — policy `authz_decisions` por-usuário + sinal canônico

A cadeia pré-tenant authz **TEM dono** (o usuário). Reescrita centralizada
em `rls_templates.py` (builder dedicado `policies_authz_decisions()` —
fonte única F-A; NÃO o template genérico fail-loud, que não admite
`tenant_id NULL`):

```sql
-- SELECT
USING (
  current_setting('app.modo_sistema', true) = '1'                 -- run_as_system: trilha completa (drill/CGCRE)
  OR (tenant_id IS NULL
      AND usuario_id = NULLIF(current_setting('app.usuario_id', true), '')::uuid)  -- pré-tenant POR-USUÁRIO
  OR tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids', true), ','))  -- cadeia do tenant
)
-- INSERT WITH CHECK
(
  (tenant_id IS NULL
   AND usuario_id = NULLIF(current_setting('app.usuario_id', true), '')::uuid)
  OR tenant_id = NULLIF(current_setting('app.active_tenant_id', true), '')::uuid
)
```

- `modo_sistema='1'` (FA-C1 canônico) substitui o proxy frágil
  `usuario_id=''` → resolve FB-C3 regressão #2 (worker tenant sem usuário
  NÃO vê mais pré-tenant alheio: sem modo_sistema e sem usuario_id
  casando, nega).
- Pré-tenant POR-USUÁRIO → usuário só lê/encadeia as próprias decisões
  pré-tenant; helper enxerga o elo anterior no contexto real → cadeia
  não bifurca (resolve BLOQ #1).
- INSERT sem branch `modo_sistema` (authz nunca grava sob run_as_system;
  não adicionar permissivo morto — higiene de segurança).
- `, true` em todos os `current_setting` (corrige latente).
- Migration nova `authz/0005_policy_authz_decisions_por_usuario`
  (DROP-then-CREATE idempotente, reverse recria a MESMA — não regride a
  robustez, padrão FA-A2). Trigger anti-mutation **intacto** (não tocar).

### 4. `django_provider` delega

`_gravar_audit` monta `payload_hash` (campos semânticos, hoje em
`payload`) + `campos` (colunas) e chama `registrar_em_cadeia(
AuthzDecision, classe_lock=_ADVISORY_LOCK_CLASSE_AUTHZ,
chave_cadeia=str(tenant_id) if tenant_id else f"U:{usuario_id}",
cadeia_filtro={"tenant_id": tenant_id} if tenant_id else
{"tenant_id__isnull": True, "usuario_id": usuario_id}, ...)`. Remove
`_hash_linha`, `_canonicalizar_payload`, `select_for_update`, e o `with
transaction.atomic()` aninhado de `can()` (FB-A2). Apaga código morto.

### 5. BLOQ #2 — normalização JSON-safe na borda de `can()`

`resource` vem da view (pode ter `set`, instância Django, datetime
naive). `canonicalizar._serializar` faz `raise TypeError`/`ValueError`
fora de {datetime tz-aware, date, Decimal, UUID}. **Antes** de qualquer
transação, `can()` chama `_normalizar_para_hash(resource)`:

- `dict` → recursão (chave não-str → `ValueError` claro);
- `list/tuple/set` → lista (set ordenado p/ determinismo);
- `str/int/float/bool/None` → intactos;
- `datetime/date/Decimal/UUID` → intactos (canonicalizar serializa;
  datetime naive segue fail-loud — desejado);
- qualquer outro → `ValueError("resource authz contém tipo não
  serializável: <tipo> em <caminho>")` **cedo, fora da transação** (não
  TypeError opaco dentro dela derrubando a autorização).

## Testes obrigatórios (5 + não-regressão)

1. `test_audit_cadeia_por_tenant.py` (T1-T8) passa **sem 1 caractere
   alterado** — contrato de não-regressão do refator do helper.
2. `test_authz_cadeia_pre_tenant_por_usuario`: 2 `can()` pré-tenant
   (`tenant_id=None`) consecutivos do MESMO usuário fora de contexto de
   tenant → `hash_anterior` do 2º == `hash_atual` do 1º (encadeia, sem
   42501).
3. `test_authz_pre_tenant_isolado_entre_usuarios`: usuário B não vê/encadeia
   na cadeia pré-tenant de A (RLS por-usuário).
4. `test_authz_cadeia_tenant_independente`: decisões intercaladas de 2
   tenants encadeiam cada uma na própria cadeia (espelho T1).
5. `test_authz_lock_isolado_de_audit`: classes de advisory lock distintas
   — insert de `auditoria` não serializa um `can()` (prova `classe_lock`
   distinto).
6. `test_authz_resource_tipo_invalido_erro_claro`: `resource` com tipo
   não serializável → `ValueError` claro ANTES da transação (não
   TypeError/erro opaco; decisão não é gravada pela metade).
7. `test_authz_hash_chain_*` existentes migram `order_by` → `sequencia`
   e continuam verdes (algoritmo convergiu — relacional, não absoluto).

## Não-objetivos (mantidos)

- NÃO mudar `calcular_hash`/`canonicalizar` (authz converge pro padrão).
- NÃO reescrever migrations aplicadas; `0004`/`0005` aditivas.
- NÃO tocar trigger PG anti-mutation authz.
- FB-C2/C4/C5/ALTOs são frentes separadas.

## Pontos para o tech-lead (re-review obrigatório)

- (Q1) Helper com `cadeia_filtro: dict` (ORM kwargs) + `classe_lock`
  parametrizado — abstração honesta p/ "tabela INSERT-only com cadeia
  hash particionável"? Ou a partição deveria ser um objeto/strategy?
- (Q2) Cadeia pré-tenant authz POR-USUÁRIO (`U:{usuario_id}`) — semântica
  correta vs. "cadeia sistema" do audit (sem dono)? Risco de um usuário
  com muitas decisões pré-tenant alongar 1 cadeia (perf do
  `order_by(-sequencia).first()` é O(1) com índice `(usuario_id,
  sequencia)` — incluir esse índice na 0004?).
- (Q3) Policy authz em builder dedicado no `rls_templates.py` (não o
  genérico) — concorda que authz_decisions NÃO cabe no template
  fail-loud (admite `tenant_id NULL`) e merece função própria na MESMA
  fonte única?
- (Q4) INSERT sem branch `modo_sistema` — algum fluxo legítimo grava
  `authz_decisions` sob run_as_system (seed/migração futura)? Se não,
  manter mínimo.
- (Q5) Migrar `test_authz_audit_imutavel` p/ `order_by("sequencia")` —
  correção alinhada ao invariante, não mascaramento? Confirmar.

## Correções absorvidas — review tech-lead #2 (2026-05-18) — APROVA COM CORREÇÕES

Veredito: Q1 APROVA c/ correção, Q2 APROVA c/ correção, Q3 APROVA,
Q4 APROVA c/ correção, Q5 APROVA. 4 bloqueantes antes do `/implement`:

- **(BLOQ #1 — chave de lock derivada do filtro, nunca passada à mão)**
  `chave_cadeia` e `cadeia_filtro` divergir = cadeia bifurca silenciosa.
  Helper recebe **só** `cadeia_filtro`; deriva
  `chave_cadeia = json.dumps(cadeia_filtro, sort_keys=True, default=str)`
  por construção. Chamador NUNCA passa string de lock. `classe_lock`
  continua parâmetro (constante por tabela). Helper assevera que `model`
  tem campo `sequencia` (erro claro se faltar — não FieldError opaco
  dentro do lock). Não-regressão: muda só o INT do advisory lock (não
  observável); hash/persistência inalterados → T1-T8 byte-a-byte.
- **(BLOQ #2 — contrato de contexto do `can()` pré-tenant)** Extrair
  `run_in_user_context(usuario_id)` em `connection.py` (usuario_id
  setado, tenant_ids=[], active_tenant=None, modo_sistema=False) —
  refator honesto do bloco inline já existente em
  `TenantMiddleware._resolver_tenants_permitidos`. Middleware passa a
  usá-lo. `_gravar_audit` pré-tenant (tenant_id None) com usuario_id
  None → **RAISE claro** (não reinício silencioso de cadeia). Teste #2
  roda DENTRO de `run_in_user_context` (não monta GUC à mão).
- **(BLOQ #3 — fronteira transacional real sob ATOMIC_REQUESTS)**
  Documentar no docstring do helper: sob `ATOMIC_REQUESTS=True` o
  `pg_advisory_xact_lock` vive até o COMMIT do request (savepoint, não
  nova tx) — **igual ao `registrar_auditoria` hoje, não é regressão**.
  Liberar o lock antes do commit seria INCORRETO (próximo escritor não
  veria a linha não-commitada via MVCC → bifurcaria) — por isso
  xact-lock é o certo. Argumento de ausência de deadlock: 1 request =
  1 cadeia authz (request de tenant não faz `can()` pré-tenant e
  vice-versa); audit e authz usam classes de lock distintas. Prova
  empírica (deadlock probe + contenção 50 req concorrentes
  tenant+pré-tenant) entra no **drill F-B (#12)** — não fecha por code
  review (limite honesto do tech-lead).
- **(BLOQ #4 — resource normalizado é fonte ÚNICA p/ hash E persistência)**
  `can()` computa `resource_norm = _normalizar_para_hash(resource)`
  UMA vez; `resource_norm` alimenta tanto `payload_hash` quanto o
  `campos["resource_summary"]` persistido. Adicionar
  `verificar_integridade_cadeia_authz` (espelho do de audit) +
  teste round-trip: `can()` com `resource` de tipo rico válido (set,
  Decimal, UUID) → verificação recomputa hash do persistido → íntegro.
- Testes adicionais (além dos 7): INSERT authz sob `run_as_system` →
  negado; `can()` pré-tenant sem `app.usuario_id` → falha alto, não
  reinicia cadeia; round-trip integridade authz com tipo rico;
  (concorrência real pré-tenant mesmo usuário → drill #12).
- Nota no docstring de `rls_templates.py`: `authz_decisions` é exceção
  consciente (tenant_id nullable por design) → builder dedicado, NÃO o
  template fail-loud genérico. Comentário na policy INSERT explicando
  ausência proposital do branch `modo_sistema`.

**Próximo:** implementar exatamente isto (causa-raiz, sem mascaramento)
→ suite verde + T1-T8 intactos + hooks 113/113 → commit/push → frente
#14 (reauditoria rodada 2: seg+tech-lead+qualidade sobre código real).
