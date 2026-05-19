---
owner: roldao
revisado_em: 2026-05-19
proximo_review: 2026-08-19
status: stable
diataxis: explanation
audiencia: agente
fase: Foundation F-A
tipo: plano-arquitetural
revisores: [tech-lead-saas-regulado, advogado-saas-regulado, consultor-rbc-iso17025]
relacionados:
  - docs/faseamento/F-A/spec.md
  - docs/adr/0002-multi-tenancy.md
  - docs/faseamento/auditorias/FA-C1-design-hash-chain.md
---

# Foundation F-A — Plano arquitetural (como realizar a spec)

> **Pra quê:** ponte entre `spec.md` (o quê) e `tasks.md` (reconciliação
> spec↔código). Descreve a arquitetura que satisfaz cada US-FA, ancorada
> no design **já implementado e saneado** (F-A rodada 2 = zero
> crítico/alto) — esta fase NÃO reescreve; **valida o caminho** e expõe
> riscos pros revisores antes da matriz P3.
>
> `status: draft` até os 3 revisores aprovarem. Bloqueantes absorvidos
> numa seção §"Correções" antes de P3.

---

## Princípio do plano

O código F-A existe e passou por saneamento rodada 2. O plano **não é**
"como construir do zero"; é **"a arquitetura que a spec exige, onde ela
vive no código, e onde pode haver risco/gap"** — para os revisores
validarem a abordagem antes de P3 medir AC-a-AC.

---

## US-FA-001 — Ambiente

Docker Compose: `afere-db` (postgres:16-alpine) + `afere-app`
(Poetry/Django). `config/settings/{base,dev,test,prod}.py`; test isola
cache LocMem (sem Redis). Healthcheck público via válvula `@public`
(materializada em F-B; em F-A `/healthz` é allowlist do middleware).
Risco baixo. **Onde:** `docker-compose.yml`, `config/settings/`,
`docker/postgres/init/01-roles.sh`.

## US-FA-002 — Entidades

`Tenant`, `Usuario`(AbstractBaseUser)+`UsuarioPerfilTenant`,
`Auditoria`(INSERT-only, `sequencia` via SEQUENCE/`db_default
nextval`), `FeatureFlag`. Decisão: `sequencia` é DDL `ADD COLUMN DEFAULT
nextval` (preenche linhas existentes sem UPDATE — não bate na RLS;
backfill por UPDATE seria bloqueado). **Onde:** `src/infrastructure/{
tenant,usuario,audit,feature_flag}/models.py` + migrations. **Risco:**
ordem de migrations entre apps na criação from-scratch (R2-S1 backlog) —
ver §Pontos P-A4.

## US-FA-003 — Isolamento 2 camadas

(a) `TenantMiddleware`: resolve lista de tenants de `UsuarioPerfilTenant`
(nunca do cliente), `SET LOCAL` GUCs sob transação. (b) RLS PG via
**fonte única** `rls_templates.py`: `require_tenant_ctx()` RAISE 42501
(fail-loud — não "vê-zero") + pattern `ANY(string_to_array(...))`
(`INV-AUTHZ-003`). Roles `app_user`/`app_migrator` NOBYPASSRLS+NOSUPERUSER
(`INV-TENANT-004`). Reverse das policies recria fail-loud (não regride a
robustez). **Risco:** `ALTER DEFAULT PRIVILEGES` é por-banco — test_afere
precisa dos grants próprios (foot-gun R2-S1; documentado, vira tarefa de
infra de teste em P4). **Onde:** `multitenant/{middleware,connection,
rls_templates,context}.py`.

## US-FA-004 — Contexto fail-loud

`run_in_tenant_context` / `run_as_system` (modo_sistema='1' canônico) /
`run_in_user_context` (pré-tenant por-usuário — extraído na frente
FB-C1+C3, mora em F-A pois é infra de contexto). `connection_created`
reseta GUCs no checkout (não herda pool). **Decisão:** `modo_sistema='1'`
é o **único** sinal de "sistema" (proxy `usuario_id=''` foi regressão,
eliminada). **Onde:** `multitenant/connection.py`.

## US-FA-005 — Hash chain por-cadeia

Helper **único** `registrar_em_cadeia(model, classe_lock, cadeia_filtro,
payload_hash, campos)` em `audit/services.py`: `transaction.atomic` +
`pg_advisory_xact_lock(classe_por_tabela, hashtext(chave_derivada_do_
filtro))` → lê elo anterior por `order_by(-sequencia)` → `calcular_hash(
anterior, canonicalizar(payload))` → create. **Decisões-chave (já
revisadas em FA-C1 + FB-C1):** (1) chave do lock **derivada** do filtro
(não pode divergir → não bifurca); (2) `pg_advisory_xact_lock` (vive até
COMMIT do request sob ATOMIC_REQUESTS — liberar antes seria incorreto:
MVCC esconde linha não-commitada → bifurcaria); (3) classe de lock
distinta por tabela (auditoria ≠ authz). `verificar_integridade_cadeia`
recomputa e encadeia no **recalculado** (Q-02). **Onde:**
`audit/{services,hash_chain,canonicalizar}.py`, migration `0009`,
trigger em `0003`.

## US-FA-006 — PII pseudonimizada

HMAC-SHA256 versionado, salt = `tenant_id` na mensagem, retorno
`{key_id}:{digest}`; `verificar_pii_hash` resolve por prefixo; versão
ausente → exceção **inconclusiva** (não "não casou" — dever de exatidão
LGPD art. 6 V). Gate de produção por entropia da chave. **Onde:**
`audit/services.py` (`hashear_pii_com_salt_tenant`, `verificar_pii_hash`,
`sanitizar_payload_audit`), registry de chaves em settings.

## US-FA-007 — Hooks

15 hooks em `.claude/hooks/`; `_test-runner.sh` cobre cada um happy +
unhappy; número canônico = output do runner (não fixo em doc — evita
drift). `tenant-id-validator`, `migration-rls-check`,
`audit-immutability-check`, anti-mascaramento (`TST-001..004`).
**Decisão:** Regra crítica → hook, doc só explica (Constituição Regra
mestre 1).

## US-FA-008 — Suite + drill robusto

`validar_f_a` (FA-A5): N tenants intercalados + injeção de elo
adulterado **exigindo detecção** + concorrência + guarda
anti-falso-verde + hooks por **exit code**. Fuzzing ≥50×1000
cross-tenant. p99<200ms multi-tenant. **Onde:** `tests/`,
`multitenant/management/commands/validar_f_a.py`.

## US-FA-009 — Convenções + conformidade

`docs/arquitetura/django-convencoes.md`,
`docs/conformidade/comum/isolamento-multi-tenant.md`. Tetos de tamanho:
`REGRAS-INEGOCIAVEIS.md` acima do teto (Constituição §3) → **GAP
conhecido**, não esconder; P4 decide (compactar vs ADR que ajusta teto).

---

## Pontos para os revisores (bloqueante até resposta)

### Para `tech-lead-saas-regulado` (arquitetura/concorrência)
- **P-A1**: A fronteira transacional do hash chain sob `ATOMIC_REQUESTS`
  (advisory lock vive até COMMIT do request) — aceitar e documentar como
  invariante de F-A, ou exigir `can()`/`registrar_*` fora de transação
  longa? Há risco de contenção/deadlock entre cadeias num mesmo request?
  (Já sinalizado em FB-C1 BLOQ#3 — quero o veredito formal pra F-A.)
- **P-A2**: `sequencia` via `ADD COLUMN DEFAULT nextval` atribui ordem
  física (heap) às linhas pré-migration (não (timestamp,id)). Aceitável
  como "cadeias pré-migration não-autoritativas" dado que não há trilha
  de produção? Confirmar pra F-A.
- **P-A4**: from-scratch migration order (R2-S1) + `ALTER DEFAULT
  PRIVILEGES` por-banco no test_afere — tratar como tarefa de infra de
  teste em P4 (não reabre F-A) ou é critério de saída?

### Para `advogado-saas-regulado` (LGPD/retenção/trilha)
- **P-B1**: `verificar_pii_hash` retornar "inconclusivo" (exceção) quando
  a versão da chave sumiu do registry — suficiente pro dever de exatidão
  (art. 6 V) e pra resposta ANPD, ou exige também log do próprio
  "inconclusivo"?
- **P-B2**: Export de auditoria ser **stub** em F-A (B2 real só F-B) —
  algum risco de retenção/imutabilidade no período F-A local-only? A
  matriz de retenção (Receita 5a × ISO 8.4 × LGPD) é citada por ID, não
  duplicada — OK?

### Para `consultor-rbc-iso17025` (trilha ISO/CGCRE)
- **P-C1**: Hash chain por-tenant + cadeia "sistema" + recomputo no
  recalculado atende a expectativa de trilha íntegra/inviolável da ISO
  17025 cl. 7.5/7.11 para fins de auditoria CGCRE — mesmo com export B2
  diferido pra F-B (em F-A a imutabilidade é trigger PG + verificação)?
- **P-C2**: `sequencia` heap-order pré-migration: do ponto de vista de
  rastreabilidade metrológica, registrar explicitamente "cadeias
  pré-Foundation não-autoritativas" basta, dado dogfooding-only sem
  cliente externo?

> Revisar **apenas** a abordagem (não reimplementar). Veredito por
> ponto: APROVA / APROVA COM CORREÇÃO / REJEITA + bloqueantes numerados.

---

## Correções absorvidas — review 3 subagentes (2026-05-19)

Veredito dos 3: **APROVA COM CORREÇÕES** (nenhum REJEITA; nenhum reabre
F-A nem joga código fora — Constituição §4). Disposição de cada
bloqueante: `[SPEC]` corrige texto da spec agora; `[T-FA/P4]` vira tarefa
de reconciliação/conserto em P3→P4; `[GATE-WaveA]` obrigação rastreada
ANTES do 1º tenant externo/registro real (NÃO bloqueia fechar F-A
dogfooding); `[P3-verify]` confere em P3.

### Tech-lead (arquitetura)
- **P-A1 `[SPEC]`+`[T-FA/P4]`**: declarar invariante **"uma transação/
  request registra elos em no máx. 1 cadeia por classe de lock; chamada
  multi-cadeia na mesma transação é proibida OU adquire locks em ordem
  total determinística (ordenada pela chave da cadeia)"**. Drill ganha
  caso intra-request multi-cadeia. Escalada honrada: probe de deadlock +
  pentest ASVS L2 externos antes do 1º tenant pago (limite de code
  review — não fecha aqui).
- **P-A2 `[SPEC]`**: herdar na US-FA-005 o texto "cadeias pré-migration
  têm ordem heap, não cronológica — não-autoritativas p/ rastreabilidade
  temporal; integridade criptográfica preservada".
- **P-A4 `[SPEC §3]`+`[T-FA/P4]`**: "ambiente de teste replica a matriz
  de roles/grants de produção (NOBYPASSRLS/NOSUPERUSER + default
  privileges), verificável por comando" vira **critério de saída de
  F-A** (sem isso o fuzzing AC-FA-008-2 é falso-verde).
- **BLOQ-1 `[SPEC]`**: AC-FA-003-3 declara que `auditoria` e
  `authz_decisions` usam **builders dedicados na mesma fonte única**
  (pattern `modo_sistema`/pré-tenant) — não é exceção ao princípio, é a
  fonte única acomodando `tenant_id` nullable.
- **BLOQ-2 `[SPEC]`**: US-FA-005 declara status de
  `AcessoDadosCliente`/`registrar_acesso_dados_cliente` (INV-013):
  INSERT-only + trigger PG anti-mutation, **sem hash chain em F-A**
  (decisão consciente). Encadeamento dessa trilha específica =
  `[GATE-WaveA]` se ANPD/CGCRE exigir (ver advogado B-4 / RBC).
- **BLOQ-3 `[SPEC]`**: rebaixar AC-FA-006-4 de garantia para
  "F-A fornece `sanitizar_payload_audit`; obrigatoriedade de uso em
  endpoint que exponha `payload_jsonb` é invariante de Wave A".

### Advogado (LGPD)
- **B-1 `[T-FA/P4]`**: `ChavePIIIndisponivel` em contexto de resposta
  titular/ANPD gera **evento próprio** na cadeia sistema (timestamp,
  key_id ausente, id do hash consultado — não o valor cru, finalidade).
  Accountability art. 6 X.
- **B-2 `[P3-verify]`**: confirmar que o ID `retencao-matriz.md` resolve
  para doc real em `status: stable`; se não existir → GAP bloqueante de
  conformidade (não cosmético).
- **B-3 `[SPEC §3]`**: cláusula expressa de aceitação consciente de
  risco de retenção/durabilidade no período F-A local-only +
  **`[GATE-WaveA]`** "B2/WORM operacional é pré-condição de qualquer
  dado de titular externo".
- **B-4 `[SPEC]`** (não estava em P-B1/P-B2 — achado novo, o mais
  relevante): US-FA-006 concilia art. 18 VI (eliminação) × imutabilidade
  — PII na trilha **nunca é dado cru**; eliminação do titular se realiza
  por **crypto-shredding** (destruição da chave/salt do tenant),
  preservando-se o registro do *acesso* sob base do art. 16
  (guarda p/ exercício de direitos / obrigação legal).
- Ciclo de vida de chave aposentada amarrado por ID à matriz de
  retenção (não aposentar chave antes do prazo legal da trilha que ela
  verifica) → `[SPEC]` US-FA-006 + `[GATE-WaveA]` política formal.

### RBC / ISO 17025
- **C1-a `[GATE-WaveA]`**: B2 WORM = gate bloqueante ANTES do 1º
  registro técnico real (cl. 7.11.3/8.4.2) — rastreado em
  `retencao-matriz` + foundation-waves; F-A fecha sem ele
  (dogfooding-only, sem registro real).
- **C1-b `[SPEC]`+`[GATE-WaveA]`**: definir periodicidade da
  `verificar_integridade_cadeia` em operação + persistir o resultado
  como **registro próprio** (cl. 8.4.2 evidência periódica). F-A pode
  ser "stub agendado" como o export, **obrigação rastreada**.
- **C2-a `[T-FA/P4]`**: fronteira "não-autoritativa" precisa ser um
  **marco de corte gravado dentro da própria trilha** (registro
  encadeado/imutável "início de cadeia autoritativa" = maior
  `sequencia` no instante da migration), não frase em doc.
- **C2-b `[SPEC]`**: emendar AC-FA-002-3/AC-FA-005-2 — "monotônica"
  qualificada (segmento pré-migration não-autoritativo).
- **BLOQ-ISO-1 `[SPEC §3]`**: nomear que a salvaguarda-contra-perda
  (cl. 7.11.3) é deliberadamente diferida e rastreada (não só implícita
  em NG-FA-4).
- **BLOQ-ISO-2 `[GATE-WaveA]`**: carimbo de tempo da auditoria de fonte
  confiável (NTP/servidor, não relógio de cliente) — requisito Wave A
  rastreado.

**Convergência dos 3 (forte):** o diferimento do B2/WORM é aceitável
para F-A dogfooding, MAS vira **gate bloqueante explícito e rastreado
antes de qualquer dado de titular externo/registro ISO real**. F-A
**fecha** sem B2; F-B/Wave A **não começam a receber dado real** sem ele.

Pós-correções → `plan.md` `status: stable`. Próximo: P3 mede a spec
corrigida contra o código (matriz `tasks.md`); `[T-FA/P4]` viram
tarefas; `[GATE-WaveA]` viram itens rastreados em foundation-waves +
retenção-matriz.
