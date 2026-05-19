---
owner: roldao
revisado_em: 2026-05-19
proximo_review: 2026-08-19
status: stable
diataxis: reference
audiencia: agente
fase: Foundation F-A
tipo: especificacao-forward
substitui: docs/faseamento/stories-f-a.md (retrofit retroativo — agora histórico)
relacionados:
  - .specify/memory/constitution.md
  - docs/faseamento-foundation-waves.md
  - docs/adr/0001-stack.md
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - REGRAS-INEGOCIAVEIS.md
---

# Foundation F-A — Especificação (forward, autoritativa)

> **O que este documento é (Constituição §1, §2):** a fonte da verdade
> do que a Foundation F-A **deve fazer**. Spec-as-source: o código é
> derivado/validado contra esta spec — não o contrário. Onde o código
> divergir desta spec (após revisão dos subagentes), **o código é
> corrigido**, não a spec.
>
> **Por que existe (decisão Roldão 2026-05-19):** F-A foi construída
> pulando o ritual Spec Kit; `stories-f-a.md` é um mapeamento
> *retroativo* (admite isso no próprio cabeçalho). Remendar auditoria por
> auditoria sobre base sem spec-mãe não convergia. Esta spec recria a
> camada do passo 1, governando a reconciliação do código existente.
>
> **Pra Roldão (uma frase):** este é o "contrato" que diz exatamente o
> que o alicérce do sistema tem que fazer; tudo é conferido contra ele.

---

## 1. Escopo

Multi-tenant + Row-Level Security + middleware de contexto + trilha de
auditoria imutável, **rodando local** (sem deploy remoto — memória
`project_deploy_so_quando_roldao_quiser`). Stack ADR-0001 candidata:
Python 3.12 + Django 5 + DRF + PostgreSQL 16 + Poetry + Docker Compose.

### Non-goals explícitos (Constituição §5 — proibição positiva)

F-A **NÃO** entrega, e nenhum agente deve inferir que entrega:

- **NG-FA-1**: autenticação/login, RBAC, `AuthorizationProvider`, MFA —
  isso é **F-B** (esta spec só prepara o terreno: `Usuario`,
  `UsuarioPerfilTenant`, contexto `app.usuario_id`).
- **NG-FA-2**: mobile, app de campo, sync offline.
- **NG-FA-3**: fiscal/NFS-e, assinatura A3, LLM/IA, frontend rico.
- **NG-FA-4**: deploy a servidor remoto, provisionamento de VPS, Backblaze
  real (export de auditoria é **stub agendado**, sem destino B2 nesta
  fase — B2 real é F-B/Wave A).
- **NG-FA-5**: módulos de produto (clientes, OS, calibração…) — Wave A.
- **NG-FA-6**: Redis/observabilidade (Grafana/Axiom/OTel) — F-B/Wave A.

### Invariantes governados (Constituição Regra mestre 2 — citar IDs)

Texto canônico em `REGRAS-INEGOCIAVEIS.md`. F-A materializa:
`INV-001` (auditoria imutável), `INV-TENANT-001` (todo query com
tenant_id), `INV-TENANT-002` (coluna tenant_id NOT NULL), `INV-TENANT-003`
(RLS ativa), `INV-TENANT-004` (roles NOBYPASSRLS/NOSUPERUSER),
`INV-AUTHZ-003` (RLS aceita LISTA de tenants — shape correto desde o dia
1), `SEC-TENANT-001` (RLS em toda tabela com dado de cliente),
`TST-001..004` (anti-mascaramento). F-A **prepara** (não implementa)
`INV-AUTHZ-001/002` e `SEC-MFA-001` (F-B).

---

## 2. Como ler as User Stories

`US-FA-NNN` → `AC-FA-NNN-N` (aceite **binário**: passou / não passou).
Cada AC tem coluna **Estado de reconciliação** preenchida em P3
(`tasks.md`): `OK` (código satisfaz, validado), `GAP` (diverge — vira
T-FA), `N/V` (não verificado ainda). Esta spec define o alvo; P3 mede.

Mortalidade (Constituição §4 + foundation-waves §2 "se reprovar"):
reprovar critério de saída **muda estratégia, não joga código fora**
(ADR-0001 portões; ADR-0002 schema-per-tenant como plano B; modelos e
migrations permanecem).

---

## US-FA-001 — Ambiente reproduzível local

**Como** orquestrador F-A, **quero** o esqueleto Django 5 + DRF + PG16 +
Poetry subir por Docker Compose com um comando, **para** ter ambiente
determinístico antes de qualquer lógica.

- **AC-FA-001-1**: `docker compose up -d` levanta `afere-db` (PG16) +
  `afere-app` (Py3.12/Django5) sem erro.
- **AC-FA-001-2**: `manage.py check` sem warning de configuração.
- **AC-FA-001-3**: `/healthz/` responde 200 JSON, marcada pública sem
  exigir contexto de tenant.
- **AC-FA-001-4**: `config.settings.test` isola cache (LocMem) e não
  depende de Redis/serviço externo.

## US-FA-002 — Entidades-núcleo modeladas e migradas

**Como** orquestrador F-A, **quero** `Tenant`, `Usuario` (+
`UsuarioPerfilTenant`), `Auditoria`, `FeatureFlag`, **para** sustentar o
multi-tenant e preparar F-B/ADR-0006.

- **AC-FA-002-1**: `Tenant`(id UUID, slug unique, nome_fantasia, plano,
  status_lifecycle, criado_em).
- **AC-FA-002-2**: `Usuario` AbstractBaseUser, email = USERNAME_FIELD,
  flag `mfa_obrigatorio`; `UsuarioPerfilTenant` (usuario×tenant×perfil
  com `valido_de`/`valido_ate`) — fonte de verdade da lista de tenants
  (`INV-AUTHZ-003`).
- **AC-FA-002-3**: `Auditoria` INSERT-only com `hash_anterior`,
  `hash_atual`, `sequencia` (ordem monotônica **para os elos criados a
  partir da migration que adiciona a coluna**; elos pré-migration têm
  ordem física de heap — **não-autoritativos cronologicamente**,
  integridade criptográfica preservada — C2-b/P-A2), `payload_jsonb`,
  `tenant_id` nullable (cadeia "sistema").
- **AC-FA-002-4**: `FeatureFlag`(tenant_id, modulo, feature_key, ativo,
  fonte enum).
- **AC-FA-002-5**: `makemigrations --check` **limpo** (zero drift
  model↔migration) e `migrate --database=migrator` aplica from-scratch
  sem erro (inclui ordem de migrations entre apps).

## US-FA-003 — Isolamento multi-tenant em duas camadas

**Como** sistema, **quero** isolamento forçado por (a) middleware que
injeta a **lista** de tenants e (b) RLS PG que bloqueia query fora da
lista, com roles sem bypass, **para** que vazamento cross-tenant seja
impossível mesmo com bug de aplicação.

- **AC-FA-003-1**: `TenantMiddleware` extrai `usuario_id`, resolve a
  lista de tenants vigentes via `UsuarioPerfilTenant` (nunca aceita
  lista do cliente), valida o tenant ativo contra a lista; sem
  usuário/tenant em path não-público → resposta de erro clara (401/403),
  nunca acesso silencioso.
- **AC-FA-003-2**: Roles `app_user` e `app_migrator` ambas
  `NOBYPASSRLS` + `NOSUPERUSER` (`INV-TENANT-004`); verificável por
  query a `pg_roles`.
- **AC-FA-003-3**: Toda policy RLS de isolamento usa o pattern
  `tenant_id::text = ANY(string_to_array(<ctx>, ','))` com `<ctx>`
  **fail-loud** (`require_tenant_ctx()` RAISE 42501 em contexto vazio)
  — `INV-AUTHZ-003` + `INV-TENANT-003`. SQL gerado por **fonte única**
  (`rls_templates.py`). **`auditoria` e `authz_decisions` têm
  `tenant_id` nullable por design** (cadeia sistema / decisão
  pré-tenant): usam **builders dedicados na MESMA fonte única**
  (`rls_templates.py` + migration de policy) com pattern estendido
  (`current_setting('app.modo_sistema')='1'` para sistema; pré-tenant
  POR-USUÁRIO no authz). Isto **não é exceção ao princípio de fonte
  única** — é a fonte única acomodando `tenant_id` nullable; proibido
  "consertar" essas policies pro template genérico (reintroduz a
  regressão FB-C1⇄FB-C3). SQL cru de policy espalhado em migration =
  bloqueado (BLOQ-1).
- **AC-FA-003-4**: Toda tabela com `tenant_id` tem `ENABLE` + `FORCE ROW
  LEVEL SECURITY` e coluna `tenant_id NOT NULL` quando o domínio exige
  (`INV-TENANT-002`); tabelas com `tenant_id` nullable por design
  (auditoria/sistema) são exceção declarada na spec da entidade.
- **AC-FA-003-5**: `makemigrations`/migration que cria tabela com
  `tenant_id` sem policy RLS na mesma migration é **bloqueada por hook**
  (`INV-TENANT-003`), allow só via `# rls-policy: external NNNN`
  justificado.

## US-FA-004 — Contexto de execução fail-loud (request, worker, sistema)

**Como** sistema, **quero** três contextos explícitos e que contexto
vazio **falhe alto** (nunca "vê 0 linhas" silencioso), **para** que
worker/cron/login não vazem nem corrompam cadeia.

- **AC-FA-004-1**: `run_in_tenant_context(tenant_id, usuario_id)` —
  request HTTP e tasks; seta `app.tenant_ids`/`app.active_tenant_id`/
  `app.usuario_id`, `modo_sistema=False`.
- **AC-FA-004-2**: `run_as_system()` — cron/manutenção sem dono; seta
  `app.modo_sistema='1'` (sinal canônico único de "sistema"); SEM
  modo_sistema e SEM contexto → RLS RAISE (fail-loud, não vê-zero).
- **AC-FA-004-3**: `run_in_user_context(usuario_id)` — autenticado
  PRÉ-TENANT (login, "listar meus tenants"): `app.usuario_id` setado,
  sem tenant, `modo_sistema=False`. É o contrato único do caminho
  pré-tenant (middleware usa o mesmo).
- **AC-FA-004-4**: Connection pool: GUCs `app.*` resetadas no checkout
  de conexão nova (não herda sessão anterior); `modo_sistema` não vaza
  de `run_as_system` para contexto de tenant subsequente.

## US-FA-005 — Trilha de auditoria imutável com hash chain por-cadeia

**Como** sistema, **quero** trilha INSERT-only com hash encadeado
**por-tenant** (cadeia "sistema" para eventos sem dono), serializada por
advisory lock, recomputável, **para** atender `INV-001` + ANPD/CGCRE.

- **AC-FA-005-1**: Cada linha: `hash_atual = sha256(hash_anterior_bytes
  || canonicalizar(payload))`; `canonicalizar` determinístico
  (sort_keys, separators compactos, tipos ricos serializados, datetime
  naive = fail-loud). Algoritmo **único** reusável (`calcular_hash` +
  `canonicalizar`), não reimplementado por tabela.
- **AC-FA-005-2**: Encadeamento **por partição** (filtro da cadeia:
  tenant, ou sistema): elo anterior lido sob `pg_advisory_xact_lock` de
  **classe por-tabela**, ordenado por `sequencia` monotônica **(para
  elos pós-migration; pré-migration = ordem heap não-autoritativa,
  ver AC-FA-002-3)**; chave do lock **derivada do filtro** (não pode
  divergir → não bifurca).
- **AC-FA-005-2b** (P-A1, invariante de concorrência): uma
  transação/request registra elos em **no máximo 1 cadeia por classe de
  lock**. Chamada multi-cadeia na mesma transação é proibida OU adquire
  os locks em **ordem total determinística** (ordenada pela chave da
  cadeia) — sem isso, dois requests multi-cadeia em ordem inversa
  deadlock. Prova empírica (probe de deadlock + concorrência real) é
  drill (AC-FA-008-3) + escalada externa (pentest ASVS L2) antes do 1º
  tenant pago — limite honesto de revisão de código.
- **AC-FA-005-6** (C2-a): a fronteira entre cadeia pré-migration
  (não-autoritativa) e autoritativa é um **marco de corte gravado
  dentro da própria trilha** — um elo encadeado/imutável "início de
  cadeia autoritativa" registrando o maior `sequencia` no instante da
  migration. Frase em doc não basta como evidência CGCRE.
- **AC-FA-005-7** (BLOQ-2): `AcessoDadosCliente`
  (`registrar_acesso_dados_cliente`, INV-013 — log de visualização de
  PII de cliente) é INSERT-only protegida por **trigger PG
  anti-mutation**, **SEM hash chain em F-A** — decisão consciente
  (imutabilidade vem do trigger; encadeamento dessa trilha específica é
  gate rastreado de Wave A se ANPD/CGCRE exigir). Teste prova o trigger
  rejeitando UPDATE/DELETE (a barreira real, já que não há cadeia).
- **AC-FA-005-3**: Trigger PG `auditoria_anti_update` +
  `auditoria_anti_delete` rejeitam mutação (`RAISE` errcode 23514);
  `DROP TRIGGER`/`DISABLE RLS`/`TRUNCATE`/`UPDATE`/`DELETE` em
  `auditoria` **bloqueados por hook** (allow só com justificativa ≥10
  chars).
- **AC-FA-005-4**: `verificar_integridade_cadeia` recomputa cada elo e
  encadeia no **recalculado** (adulteração no meio quebra esse elo E
  todos os seguintes — propriedade real de hash chain); verificação
  por-tenant + cadeia sistema; isolamento da detecção (tenant íntegro
  não acusado junto).
- **AC-FA-005-5**: Export hourly é **stub agendado** (NG-FA-4 — sem B2
  real nesta fase).

## US-FA-006 — PII pseudonimizada versionada (não anonimização)

**Como** sistema, **quero** referenciar PII na auditoria por HMAC
versionado com salt por-tenant, **para** responder ANPD "quem viu CPF X
em data Y" sem armazenar o dado cru e sobreviver à rotação de chave.

- **AC-FA-006-1**: `hashear_pii_com_salt_tenant(valor, tenant_id)` =
  HMAC-SHA256 com chave de servidor, mensagem inclui `tenant_id` (mesmo
  CPF, tenants distintos → hashes distintos); retorno prefixado
  `{key_id}:{digest}`.
- **AC-FA-006-2**: `tenant_id` obrigatório (sem ele falha alto, não
  silencia com "").
- **AC-FA-006-3**: `verificar_pii_hash` resolve a chave pelo prefixo
  (funciona após rotação); versão ausente do registry → **inconclusiva**
  (exceção), **não** "não casou" (dever de exatidão LGPD art. 6 V).
- **AC-FA-006-3b** (B-1): toda ocorrência de `ChavePIIIndisponivel` em
  contexto de resposta a titular/ANPD **gera evento próprio** na cadeia
  sistema (timestamp, `key_id` ausente, id do hash consultado — nunca o
  valor cru, finalidade). Accountability LGPD art. 6 X — exceção em
  runtime sozinha não basta.
- **AC-FA-006-4** (BLOQ-3 — rebaixado de garantia p/ capacidade): F-A
  **fornece** `sanitizar_payload_audit` (redator de PII por
  denylist + regex) e gate de produção por entropia da chave. A
  **obrigatoriedade** de aplicá-lo em endpoint que exponha
  `payload_jsonb` é invariante de **Wave A** (travado por hook/review na
  entrega do 1º endpoint que devolva auditoria) — em F-A não há tal
  endpoint (NG-FA-3/5).
- **AC-FA-006-5** (B-4 — eliminação × imutabilidade): PII na trilha
  **nunca é dado cru** (sempre HMAC pseudonimizado). O direito de
  eliminação (LGPD art. 18 VI) sobre a trilha imutável se realiza por
  **crypto-shredding por tenant** (destruição da chave/salt do tenant
  torna o hash irreversível/não-verificável), **não** por DELETE — o
  registro de *que houve o acesso* permanece sob base do art. 16
  (guarda p/ exercício de direitos / obrigação legal: Receita 5a × ISO
  8.4). Ciclo de vida de chave aposentada (`PII_HASH_KEYS_RETIRED`) é
  **amarrado por ID à matriz de retenção**: chave não é aposentada antes
  do prazo legal de retenção da trilha que ela verifica.

## US-FA-007 — Invariantes forçados por hook (não só doc)

**Como** orquestrador, **quero** os invariantes críticos travados em
hook pre-commit, **para** que regressão não passe por revisão humana
(Constituição Regra mestre 1).

- **AC-FA-007-1**: `tenant-id-validator` bloqueia query SQL/ORM sem
  `tenant_id` (`INV-TENANT-001`), incluindo subquery/JOIN/dinâmica.
- **AC-FA-007-2**: `migration-rls-check` (`INV-TENANT-003`) +
  `audit-immutability-check` (`INV-001`) ativos.
- **AC-FA-007-3**: `_test-runner.sh` cobre cada hook com casos happy +
  unhappy; suíte de hooks **100% verde** (contagem lida do output, não
  fixa em doc — número canônico vive no `_test-runner`).
- **AC-FA-007-4**: Anti-mascaramento (`TST-001..004`) ativo: skip sem
  motivo, assert vazio, `type:ignore` solto, `INV-*` sem teste →
  bloqueado.

## US-FA-008 — Suite + fuzzing + drill robusto `validar_f_a`

**Como** orquestrador, **quero** validar a fase em um comando, com drill
que **não mente** (anti-falso-verde), **para** ter critério binário.

- **AC-FA-008-1**: pytest-django + factory-boy; suíte verde; cobertura
  ≥ 80% (gate `--cov-fail-under`).
- **AC-FA-008-2**: Fuzzing concorrente cross-tenant (≥ 50 threads × 1000
  queries) — **zero vazamento** (`INV-TENANT-001/003`, critério de
  mortalidade §2).
- **AC-FA-008-3**: `validar_f_a` robusto (FA-A5): N tenants intercalados
  com cadeias independentes íntegras; **injeção de elo adulterado EXIGE
  detecção** (reprova se passar limpo); concorrência; **guarda
  anti-falso-verde** (reprova se cadeia vazia); hooks por **exit code**,
  não substring.
- **AC-FA-008-4**: p99 de query operacional típica < **200ms** com
  ~10k linhas × 50 tenants sintéticos intercalados (índices
  `(tenant_id, …)` validados) — critério de mortalidade §2.
- **AC-FA-008-5**: Drill cronometrado de restore PG < 30min para 1
  tenant (operacional; evidência registrada).
- **AC-FA-008-6** (P-A4): ambiente de teste (`test_afere`) **replica a
  matriz de roles/grants de produção** — `app_user`/`app_migrator`
  NOBYPASSRLS+NOSUPERUSER + default privileges — **verificável por
  comando** (`verificar_objetos_seguranca` ou equivalente contra
  test_afere). Sem isso o fuzzing AC-FA-008-2 é **falso-verde** (pode
  rodar com privilégio ≠ produção e "passar" mascarando vazamento).
- **AC-FA-008-7** (C1-b): `verificar_integridade_cadeia` tem
  **periodicidade definida** em operação e o resultado (data, escopo,
  ok/quebrados) é **persistido como registro próprio** (cl. ISO 8.4.2 —
  evidência periódica). Em F-A pode ser **stub agendado** (como o export
  B2), mas a obrigação é rastreada (gate Wave A).

## US-FA-009 — Convenções + conformidade de isolamento

**Como** orquestrador, **quero** as convenções Django e a evidência de
isolamento documentadas, **para** que agente futuro não reinvente estilo
e a conformidade MVP-1 tenha base.

- **AC-FA-009-1**: `docs/arquitetura/django-convencoes.md` `status:
  stable` (naming PT, camadas domain/infrastructure/application, signals
  proibidos por default, select_related obrigatório).
- **AC-FA-009-2**: `docs/conformidade/comum/isolamento-multi-tenant.md`
  com evidência da implementação real (2 camadas + fail-loud + roles).
- **AC-FA-009-3**: Tetos de tamanho respeitados (Constituição §3):
  `AGENTS.md ≤ 250`, `CLAUDE.md ≤ 150`, `REGRAS-INEGOCIAVEIS.md ≤ 120`
  — **desvio conhecido**: REGRAS está acima; registrar como GAP em P3
  (não esconder).

---

## 3. Critérios de saída da fase (mortalidade — espelham foundation-waves §2)

F-A só **fecha** quando, sobre o código reconciliado a esta spec:

1. Fuzzing concorrente RLS: 100% sem vazamento (AC-FA-008-2).
2. p99 < 200ms no cenário multi-tenant sintético (AC-FA-008-4).
3. Restore PG < 30min (AC-FA-008-5).
4. `tenant-id-validator` 100% no `_test-runner` (AC-FA-007-1/3).
5. Hash chain validada + trigger anti-mutation provado (AC-FA-005-*).
6. Drill `validar_f_a` robusto verde, sem falso-verde (AC-FA-008-3).
7. Ambiente de teste replica matriz de roles/grants de produção,
   verificável por comando (AC-FA-008-6 — senão #1 é falso-verde).
8. 3 auditores Família 5 sem CRÍTICO/ALTO (P5).

Reprovar → muda estratégia (ADR-0001/0002), **mantém** modelos e
migrations.

### 3.1 Aceitação consciente de risco (período F-A local-only)

Em F-A a imutabilidade da trilha repousa em **trigger PG + RLS +
verificação por recomputo, num único PostgreSQL local**. A
**salvaguarda-contra-perda** (ISO 17025 cl. 7.11.3 / LGPD art. 6 VII /
art. 46) — cópia independente WORM — é **deliberadamente diferida**
(NG-FA-4) e **aqui declarada como risco aceito conscientemente**, válido
**apenas** porque F-A é dogfooding-only, sem dado de titular externo e
sem registro técnico ISO real (memória `project_sem_cliente_externo_
agora`). O `docker compose down -v` destrói a trilha local — aceitável
só neste período.

### 3.2 Gates rastreados ANTES de qualquer dado real (não bloqueiam F-A)

Convergência dos 3 revisores: F-A **fecha** sem estes; mas são
**pré-condição bloqueante** antes do 1º tenant externo / 1º registro
ISO real (rastrear em `foundation-waves` + `retencao-matriz`):

- **GATE-1** (C1-a/B-3): export B2/WORM **operacional** — cópia imutável
  independente do PostgreSQL local.
- **GATE-2** (C1-b): verificação de integridade **periódica com
  evidência persistida** (não stub).
- **GATE-3** (BLOQ-ISO-2): carimbo de tempo da auditoria de **fonte
  confiável** (NTP/servidor, não relógio de cliente).
- **GATE-4** (B-4/advogado): política formal de ciclo de vida de chave
  PII amarrada à matriz de retenção (não aposentar antes do prazo legal).
- **GATE-5** (BLOQ-2): se ANPD/CGCRE exigir, encadeamento hash de
  `AcessoDadosCliente` (em F-A só trigger PG).

---

## 4. Relação com o código existente (reconciliação — P3)

Esta spec é **forward e autoritativa**. O código F-A passou por
saneamento rodada 2 (zero crítico/alto) — provável alto índice de `OK`
na matriz, mas **nada é assumido**: P3 (`tasks.md`) verifica cada AC
contra o código real e abre `T-FA-NNN` para cada `GAP`. `stories-f-a.md`
vira histórico (não-autoritativo).

**P2 concluído (2026-05-19):** `plan.md` revisado pelos 3 subagentes —
APROVA COM CORREÇÕES; bloqueantes absorvidos (esta spec corrigida +
`plan.md` §"Correções absorvidas"). Disposição: `[SPEC]` aplicado aqui;
`[T-FA/P4]` (B-1 evento inconclusivo, C2-a marco de corte, P-A1 caso
drill multi-cadeia, P-A4 smoke grants test_afere) vira tarefa em P3→P4;
`[GATE-WaveA]` (GATE-1..5) rastreado; `[P3-verify]` (existência de
`retencao-matriz.md` em `stable` — B-2) checado em P3.

> **Próximo (P3):** `tasks.md` — matriz que mede cada AC desta spec
> corrigida contra o código real; cada divergência vira `T-FA-NNN`
> (causa-raiz, sem mascaramento).
