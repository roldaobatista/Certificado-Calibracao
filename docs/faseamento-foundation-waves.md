---
owner: roldao
revisado_em: 2026-05-27
proximo_review: 2026-08-27
status: stable
diataxis: reference
audiencia: agente
relacionados:
  - docs/faseamento-modulos.md
  - docs/adr/0001-stack.md
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - docs/adr/0008-fiscal-pluggable.md
  - docs/adr/0009-onde-a3-assina.md
  - docs/adr/0010-estrategia-tela.md
  - docs/adr/0011-banco-analitico-bi.md
  - docs/adr/0012-autorizacao-unificada.md
  - docs/adr/0013-pricing-composicional.md
  - docs/adr/0014-transicoes-regulatorias.md
  - docs/adr/0015-lifecycle-tenant.md
  - docs/adr/0016-operacao-consistente.md
  - REGRAS-INEGOCIAVEIS.md
---

# Faseamento Foundation + Waves — definição canônica das fases

> **Pra quê:** 7 ADRs (0010–0016) usam "Foundation F-A", "Foundation F-B", "Wave A", "Wave B" como se todo mundo soubesse o que é. Não tinha doc único definindo. Auditor A apontou como gap crítico em 2026-05-17. Este arquivo é a fonte única — quem viola, é violação de ADR.
>
> **Não duplica** `docs/faseamento-modulos.md` (esse lista QUAIS módulos entram em cada wave). Aqui está o **contrato técnico** de cada fase: objetivo, critérios de entrada, entregáveis, critérios de saída (mortalidade), dependências entre ADRs.
>
> **Pra Roldão (em uma frase):** primeiro a gente constrói a base que sustenta o sistema todo (Foundation F-A), depois liga o controle de quem-pode-o-quê (Foundation F-B), aí entram os 18 módulos que a Balanças Solution precisa pra rodar de verdade (Wave A), depois os outros 27 módulos pra virar produto completo (Wave B), e por último as melhorias avançadas (Wave C / V2).

---

## 1. Mapa das fases (overview)

| Fase | Duração estimada | Pré-código de produto? | Objetivo central |
|------|------------------|------------------------|------------------|
| **Foundation F-A** | 4–6 semanas | sim (primeira construção real) | Multi-tenant + RLS + middleware + audit trail funcionando local |
| **Foundation F-B** | 2–3 semanas (overlap final F-A) | sim | Autenticação + RBAC + AuthorizationProvider + MFA |
| **Wave A — MVP-1** | 8–12 semanas | não — código de produto | 18 módulos rodando em dogfooding na Balanças Solution |
| **Wave B — expansão** | 16–24 semanas | não | +27 módulos restantes (comercial avançado, financeiro completo, suporte, BI, qualidade) |
| **Wave C / V2** | 16+ semanas | não | Pós-MVP: BI semântico, Temporal, MFA hardware, federation, marketplace |

**Total estimado até MVP-1 dogfooding profundo:** Foundation (6–9 semanas) + Wave A (8–12 semanas) = **14–21 semanas (≈ 3,5–5 meses)**, dentro da janela 5–7 meses da 3ª auditoria.

> **Atenção:** estimativas operacionais, não comerciais. Não há promessa de release pública. Datas reais só se preenchem após a fase fechar (ver §12).

---

## 2. Foundation F-A — base técnica multi-tenant

### Pra dono (Roldão)
F-A é o "alicerce do prédio". Aqui a gente cria o banco de dados com a trava que impede um cliente ver dado de outro cliente, monta o esqueleto do Django com a regra de "todo acesso passa por filtro de tenant", e liga o registro automático de cada coisa que acontece no sistema (audit trail). Sem mobile. Sem nota fiscal. Sem IA. Só o alicerce. Se o alicerce não passar nos testes de carga e de invasão, a gente NÃO joga código fora — a gente troca a estratégia (ex: usar Cockroach em vez de Postgres) mas mantém o modelo já escrito.

### Objetivo de negócio
Ter PostgreSQL + Row-Level Security (RLS) + middleware Django injetando `tenant_id` automático + trilha de auditoria imutável funcionando **localmente** (sem deploy a servidor remoto — ver memória `project_deploy_so_quando_roldao_quiser`).

**Sem nesta fase:** mobile, fiscal, LLM, frontend rico, integrações externas, deploy.

### Critérios de entrada
- [x] ADR-0001 (stack) aprovada como **candidata** — Portões 2 fechado, Portão 1 diferido pra V2
- [x] ADR-0002 (multi-tenancy) em proposta com decisão schema-shared + RLS
- [x] ADR-0007 (camada de domínio + gerador spec→código) em proposta
- [ ] **Roldão aprova arrancar F-A** explicitamente (gate manual — ainda não dado)
- [ ] Devcontainer (D4) criado e validado em outro PC

### Entregáveis técnicos
1. **Esqueleto Django 5.0 LTS + DRF + PostgreSQL 16** rodando local via Docker Compose (mesma topologia da ADR-0001, sem traefik/grafana/litellm/otel ainda — esses entram em F-B/Wave A)
2. **4 entidades núcleo** modeladas, migradas e testadas:
   - `Tenant` (id, slug, nome_fantasia, plano, status_lifecycle, criado_em)
   - `Usuario` (id, email, senha_hash, mfa_secret, criado_em) + tabela M:N `auth_usuario_perfil` com `valido_de/ate` (preparação INV-AUTHZ-003)
   - `Auditoria` (id, tenant_id, user_id, action, resource_summary, payload_jsonb, hash_anterior, hash_atual, timestamp) — INSERT-only com trigger PG bloqueando UPDATE/DELETE + hash chain
   - `FeatureFlag` (tenant_id, modulo, feature_key, ativo, fonte enum) — preparação ADR-0006 + ADR-0015 INV-INT-008
3. **Multi-tenancy operacional** conforme ADR-0002:
   - Middleware Django thread-local que extrai `tenant_id` do JWT e injeta na conexão PG via `SET LOCAL app.tenant_ids = '<uuid>'`
   - Role `app_user` com `NOBYPASSRLS NOSUPERUSER` (INV-TENANT-004)
   - Role `app_migrator` separada (também NOBYPASSRLS)
   - Policy RLS em todas tabelas com `tenant_id` usando pattern `ANY(string_to_array(current_setting('app.tenant_ids'), ','))` (INV-AUTHZ-003 já no shape correto desde dia 1)
   - Wrapper obrigatório `run_in_tenant(tenant_id, fn)` para tasks Celery (mesmo que Celery ainda mal usado)
4. **Audit trail síncrono** com hash chain ligando linhas; trigger PG bloqueia UPDATE/DELETE; export hourly stub (job Celery agendado, sem destino B2 ainda)
5. **pytest base** com factories (factory-boy) para Tenant/Usuario; testes de fuzzing cross-tenant; pytest-cov ≥ 80%
6. **Devcontainer** (D4) reproduzindo o setup com 1 comando
7. **Convenções django** (`docs/arquitetura/django-convencoes.md`) escritas e aplicadas — naming, layered, signals proibidos por default, select_related/prefetch_related obrigatórios
8. **Pacote de hooks complementares** criado em `.claude/hooks/`:
   - `tenant-id-validator.sh` — bloqueia query SQL/ORM sem `tenant_id` no WHERE (INV-TENANT-001)
   - `migration-rls-check.sh` — bloqueia migration que cria tabela com `tenant_id` sem policy RLS (INV-TENANT-003)
   - `audit-immutability-check.sh` — valida que tabela `auditoria` mantém trigger anti-UPDATE/DELETE
9. **Base de conformidade MVP-1 (parcial)**: `docs/conformidade/comum/isolamento-multi-tenant.md` redigido com evidência da implementação

### Critérios de saída (mortalidade falsificável)
Se reprovar em **qualquer** dos critérios abaixo, **muda estratégia, não joga código fora** (ver §10):

- [ ] RLS bloqueia cross-tenant em **100%** dos testes de fuzzing concorrente (50 threads × 1000 queries)
- [ ] p99 de query operacional típica < **200ms** com **10k linhas × 50 tenants sintéticos** (índices compostos `(tenant_id, ...)` validados)
- [ ] Drill cronometrado de **restore PG** com pgBackRest em provedor de teste local: **< 30min** para 1 tenant (RPO 15min validado em sintético)
- [ ] Hook `tenant-id-validator` passa em **100%** dos casos do `_test-runner.sh` (incluindo queries dinâmicas, subqueries, JOINs)
- [ ] Hash chain do audit trail validada: cada linha tem `hash_atual = sha256(hash_anterior || payload)` e trigger anti-UPDATE/DELETE comprovado em teste de fuzzing
- [ ] **Critério Roldão (ADR-0001 Portão 3):** ≤ 2 intervenções de código/semana do Roldão; ≤ 3 bugs SEV-1 no período; gasto de tokens LLM ≤ R$ 1.500 nas 4–6 semanas (limite ADR-0001)
- [ ] Auditor de Segurança não bloqueou nenhum merge nos últimos 14 dias da fase

### Bloqueado por (gates externos)
- ADR-0001 aprovada como candidata (✅ feito)
- ADR-0002 em ao menos proposta com revisão técnica
- ADR-0007 em proposta
- Decisão Roldão de "arrancar F-A" (manual)
- `docs/conformidade/comum/isolamento-multi-tenant.md` redigido em paralelo às 2 primeiras semanas
- 3 hooks complementares criados (`bus-envelope`, `authz-check`, `provisioning-checkpoint` — esses 3 não bloqueiam F-A mas precisam estar prontos antes de F-B/Wave A)

### Se reprovar
- Token cap ≥ R$ 1.500 OU > 3 bugs SEV-1 → **dispara plano B** (tech-lead consultivo R$ 8–15k/mês). Código F-A **permanece** e continua evoluindo sob nova orquestração.
- p99 > 200ms sem caminho de otimização viável → revisita ADR-0001 (avaliar Cockroach/Citus/escala vertical). Modelo Django **permanece**.
- RLS falha em fuzzing → revisita ADR-0002 (avaliar schema-per-tenant). Migrations e domain models **permanecem**.

---

## 3. Foundation F-B — autenticação + RBAC + AuthorizationProvider

### Pra dono (Roldão)
F-B liga o controle de acesso. Agora o sistema sabe quem é cada usuário (login), em quais empresas (tenants) ele tem acesso, e o que cada perfil pode fazer (técnico vê OS dele, gerente vê de todos, RT assina certificado, cliente final só lê o próprio). Esse controle passa por **um único ponto** — o `AuthorizationProvider` — pra ser auditável de verdade quando a LGPD perguntar "quem viu o CPF do cliente X em tal data?".

### Objetivo de negócio
Login funciona + 4 perfis básicos funcionam + MFA TOTP obrigatório pros perfis sensíveis + audit trail de autorização síncrono + INV-AUTHZ-001..003 implementadas e validadas por hook.

### Critérios de entrada
- [ ] F-A com **todos** os critérios de saída verdes
- [ ] ADR-0012 (autorização unificada) aprovada — não mais "proposta"
- [ ] ADR-0006 (feature flags) em ao menos proposta consistente com ADR-0015 INV-INT-008
- [ ] Hook `authz-check.sh` criado e testado em `.claude/hooks/`
- [ ] Decisão Roldão de prosseguir

### Entregáveis técnicos
1. **AuthorizationProvider** implementado como porta + adapter local (sem provedor externo ainda):
   - Assinatura: `can(user_id, action, resource, tenant_id, purpose) → AuthDecision{allowed, reason, perfis_aplicados, escopo_avaliado}`
   - Cache Redis com TTL ≤ 5min + invalidação imediata em mudança de perfil/feature (preparação INV-INT-008)
   - 4 perfis seed: `admin_tenant`, `tecnico`, `rt_signatario`, `cliente_externo_leitura`
2. **django-allauth + django-otp** integrados — login, reset de senha, MFA TOTP, sessões
3. **Decorator `@public` explícito** + deny-by-default global em todas as views (INV-AUTHZ-001 forçada por hook)
4. **Migration RLS v2**: regerar **~50 policies** existentes (mesmo que F-A tenha criado só 4–6 tabelas, gerar o script reusável que vai rodar quando Wave A adicionar dezenas de tabelas)
5. **Audit trail authz síncrono** (INV-AUTHZ-002): tabela `audit_trail.authz_decisions` INSERT-only com trigger PG bloqueando UPDATE/DELETE + hash chain + job de export hourly pra Backblaze B2 (agora com destino real, não stub)
6. **Hook `authz-check.sh`** bloqueia merge de endpoint Django novo sem chamada `AuthorizationProvider.can()` — validado nos 23+ casos do `_test-runner.sh`
7. **16 cenários E2E** (4 perfis × 4 ações típicas × positivo+negativo) em pytest + Playwright

### Critérios de saída (mortalidade)
- [ ] **16 cenários E2E** (perfil × ação × tenant × positivo/negativo) passam — sem flake
- [ ] Hook `authz-check.sh` rejeita 100% dos endpoints sem `can()` no `_test-runner.sh`
- [ ] Migration RLS v2 (lista de tenants — INV-AUTHZ-003) regerou **todas** as policies existentes; teste de fuzzing concorrente: usuário multi-tenant {A,B} tenta acessar tenant C → bloqueado
- [ ] Audit trail authz: `can()` retorna **apenas após commit** do audit log (validado por teste que mata o processo entre `can()` e response — linha existe no banco)
- [ ] MFA TOTP obrigatório validado pros 4 perfis sensíveis seed (SEC-MFA-001)
- [ ] Auditor de Segurança aprova a fase

### Bloqueado por
- F-A verde
- ADR-0012 aprovada
- Hook `authz-check.sh` criado
- INV-AUTHZ-001..003 redigidas em `REGRAS-INEGOCIAVEIS.md` (✅ feito)

### Se reprovar
- Falha em cenários E2E → debug pontual, sem mudar estratégia (escopo pequeno).
- Performance do `can()` < 5ms p99 não atingida → ajusta cache; se inviável, ADR-0012 reabre para avaliar OPA/Cerbos como adapter externo.

> **Reconciliação 2026-05-19 (ritual Spec Kit — fonte executável =
> `docs/faseamento/F-B/spec.md`):** 3 itens deste §3 foram corrigidos
> por autoridade superior e ficam aqui registrados p/ não driftar:
> (a) "cache Redis" → **LocMemCache** e (b) "destino B2 real" →
> **B2 diferido (gate)** — ambos por ajuste de aceitação da **ADR-0012**
> (autoridade > este contrato; texto §3 era pré-ajuste);
> (c) critério "`can()` retorna apenas após commit do audit log" →
> **atomicidade decisão↔audit / rollback-órfão** (BLOQ-4 review
> tech-lead): "commit antes do retorno" é tecnicamente falso sob
> `ATOMIC_REQUESTS` (savepoint) — a garantia ficou mais forte (sem
> decisão órfã), não reduzida. Detalhe em `F-B/spec.md` §3/§4 +
> `F-B/plan.md` §Correções.

---

## 4. Foundation F-C — Hardening + Observabilidade (3 sub-foundations sequenciais)

> **Criada em 2026-05-23** pela Onda 0 do plano-v2 de saneamento (após auditoria 10 lentes detectar que LICENSE indefinida, logging placeholder, paginação ausente, throttle ausente, circuit breaker ausente, hardening prod ausente e pin SHA ausente bloqueavam o 1º deploy externo).
>
> **Por que 3 sub-foundations e não uma só:** auditoria do plano-v1 com 10 lentes (2026-05-23) detectou que F-C com 9 GAPs violava o princípio "Conciso vence completo" (F-A teve 8 GAPs, F-B teve 6 — projeção pra F-C com 9 GAPs era de ~25 achados pendentes no fechamento, igual Marco 2 estourou). Convergência LLM + OBS + SEC: quebrar em 3 sub-foundations sequenciais.
>
> **Bloqueia Wave A inteira.** Sem F-C1/F-C2/F-C3 verdes, 1º deploy externo é inviável.

### Pra dono (Roldão)

F-C é o "endurecimento" do alicerce antes de subir paredes. F-A montou o alicerce multi-tenant, F-B ligou o controle de quem pode o quê. Agora F-C garante que (1) o sistema não vaze coisa em produção por descuido de configuração, (2) a gente consegue ver o que está acontecendo quando algo der errado, e (3) o sistema aguenta quando uma dependência externa cair. Sem F-C, qualquer cliente externo pago vai ver bug que a gente não consegue diagnosticar.

### 4.1 F-C1 — Hardening crítico

**Objetivo:** trancar a configuração de produção, blindar o `/admin/` e fechar a porta de saída pra requisições não confiáveis (SSRF).

**Entregáveis técnicos:**
1. Hook `prod-settings-check.sh` valida `config/settings/prod.py` exige: `DEBUG=False`, `ALLOWED_HOSTS` lista fechada, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `SECURE_HSTS_SECONDS >= 31536000`, `SECURE_SSL_REDIRECT=True`, `SECURE_REFERRER_POLICY=same-origin`, `X_FRAME_OPTIONS=DENY`, `SECURE_CONTENT_TYPE_NOSNIFF=True` + cabeçalhos CSP via `django-csp` ou middleware próprio.
2. INV-ADMIN-001 redigida em REGRAS-INEGOCIÁVEIS + hook `admin-hardening-check.sh`: rota `/admin/` exige MFA obrigatório + rate-limit + IP allowlist + log auditável de cada acesso.
3. ADR-0054 aceita E IMPLEMENTADA na mesma sub-foundation (não split — aceitação cega é débito): porta `OutboundWebhookProvider` com HMAC + SSRF guard (bloqueio de IPs privados RFC1918/loopback/link-local + DNS rebinding lock) + allowlist de portas + timeout.
4. Rotação de credenciais dogfooding (lição da auditoria SEC: gitleaks sem rotação é teatro — mesmo sem segredo encontrado no histórico, faz sentido rotacionar `DJANGO_SECRET_KEY` e `KMS_KEY_ID` dogfooding como exercício antes do 1º deploy).

**Critérios de saída:** 10 auditores Família 5 PASS ZERO CRÍTICO/ALTO/MÉDIO + drill SSRF (tentar resolver `169.254.169.254`, `localhost`, `192.168.x.x` no provider — bloqueio) + drill MFA admin (sem MFA = 403 + log) + suite verde.

### 4.2 F-C2 — Observabilidade infra

**Objetivo:** ter log estruturado com `tenant_id`+`correlation_id`+`request_id` automático em toda chamada, ter endpoints de health/readiness corretos, decidir destino do log.

**Entregáveis técnicos:**
1. Substituir placeholder em `config/settings/base.py:441-462` por configuração real de `structlog` + processor automático que injeta `tenant_id` (vindo do middleware multi-tenant), `correlation_id` (gerado/lido em middleware HTTP via header `X-Correlation-Id`) e `request_id` em todo `logger.info/warning/error`. Decisão: `extra={...}` manual fica PROIBIDO (causa drift); processor é fonte única. Retrofit dos 29 call sites com `extra=` manual (13 arquivos) num único commit "logging-processor-canonico".
2. INV-LOG-001..003 redigidas em REGRAS: (001) todo log estruturado tem `tenant_id`+`correlation_id`; (002) `extra=` manual proíbido fora do processor; (003) destino do log é stdout + driver Docker → Axiom (decisão a fechar nesta sub-foundation; alternativa: Promtail → Grafana Cloud Loki).
3. Endpoints separados (correção da confusão liveness vs readiness apontada pelo auditor OBS):
   - `/health` (liveness) → só processo vivo + connection pool ok
   - `/ready` (readiness k8s) → só DB respondendo (B2 e KMS FORA — se B2 piscar, k8s não pode tirar pod)
   - `/health/deep` (probe operacional, não k8s) → DB + B2 + KMS + bus outbox sem backlog grande
4. SIGTERM handler em procrastinate worker (versão a pinar — auditor PERF confirmou suporte nativo desde 2.x, mas plano-v1 não tinha versão fixada): worker termina job em voo, drena fila, não pega novo.
5. Contextvar `correlation_id` propagado nos 4 pontos críticos: middleware HTTP grava; DRF view lê; `EventEnvelope.publicar()` lê do contextvar e inclui no envelope; consumer entra no contextvar antes de processar evento. Sem isso, tracing quebra na borda outbox.

**Critérios de saída:** 10 auditores PASS + drill "matar worker durante job" (SIGTERM → drena → sem job perdido) + verificar 100% dos logs novos têm `tenant_id`+`correlation_id` automáticos + drill `/ready` vs `/health/deep` (B2 cai → `/ready` continua 200, `/health/deep` retorna 503).

### 4.3 F-C3 — Instrumentação + resiliência

**Objetivo:** medir o que importa (técnico + negócio), proteger contra abuso e proteger contra dependência externa derrubando o sistema.

**Entregáveis técnicos:**
1. Adicionar serviço **Redis** ao `docker-compose.yml` (auditor PERF: throttle DRF sem Redis cai em LocMemCache por worker, vira ficção em multi-worker gunicorn).
2. PERF-1 paginação DRF: `DEFAULT_PAGINATION_CLASS=PageNumberPagination` + `PAGE_SIZE=50` em `config/settings/base.py` + hook `paginacao-obrigatoria-check.sh` que rejeita `ListAPIView`/`ModelViewSet` sem `pagination_class` declarada. **Retrofit dos 621 testes** que esperam array cru pra esperar `{count,results}` — orçado como T próprio (`T-FC3-PAGINACAO-RETROFIT-TESTES`).
3. PERF-3 throttle DRF: `DEFAULT_THROTTLE_CLASSES` ativo + escopos por endpoint caro autenticado (POST `/clientes/`, importação CSV, revogação consentimento, futuras chamadas LLM) + INV-RATE-001..003.
4. PERF-2 circuit breaker + DLQ ativa: implementar `circuitbreaker` em chamadas externas (Lacuna, KMS, futuro Asaas) com **fake adapter determinístico** (injeta timeout/erro/lentidão — não mock vazio); `outbox_worker.py` move pra `dead_letter_events` após `max_tentativas=5` com backoff exponencial + jitter; **drill de envenenamento orçado** como T próprio (T-FC3-DLQ-DRILL — forçar 5 falhas e asserir linha em `dead_letter_events`).
5. OBS-2 instrumentação: `prometheus-client` + `opentelemetry-sdk` + decoradores em consumers/views/sagas + dashboard Grafana Cloud com 5 métricas técnicas (p95/p99 por endpoint, taxa de erro, depth fila outbox, taxa DLQ) **e 5 métricas de NEGÓCIO acordadas com Roldão** (OS aberta/dia, certificado emitido/dia, OS sem aceite > 48h, inadimplência R$/dia, NPS dogfooding).
6. SUPPLY-1 pin SHA: `Dockerfile` base + 3 actions (`checkout@v4`, `setup-python@v5`, `github-script@v7`) + base PostgreSQL + Redis → todos pinados por `@sha256:` (Docker) ou `@<commit>` (Actions). `.github/dependabot.yml` ativo com **política escrita** em `docs/governanca/dependabot-policy.md`: auto-merge patch+security em actions/docker; humano (eu — Claude Code) avalia minor/major.

**Critérios de saída:** 10 auditores PASS + drill DLQ envenenamento (5 falhas → mensagem em `dead_letter_events` + alerta) + drill throttle multi-worker (Redis ativo, 100 req/s em endpoint throttle=10/s → 90 bloqueadas) + 5 métricas de negócio populadas em Grafana com dados sintéticos + Dependabot rodando 1 ciclo sem ruído.

### Bloqueado por

- F-A + F-B verdes (já fechadas em 2026-05-19)
- LICENSE definida (Onda 0 ✅)
- Devcontainer materializado (D4 ✅ — `.devcontainer/devcontainer.json` já existe; ADR-0062 reservada formaliza)
- ADR-0054 (Webhook out) — aceita E implementada juntas em F-C1
- Roldão aprovar arrancar F-C1

### Não-objetivos de F-C (Onda 5 do plano-v2)

Os seguintes itens ficam **explicitamente fora** de F-C e entram em ondas posteriores do plano-v2:

- Acessibilidade WCAG (ADR-0057) → Onda 2 do plano-v2, paralela ao Marco 3 OS (antes M3 implementar tela)
- Analytics produto (ADR-0058) → Onda 2 do plano-v2
- LLMProvider + INV-LLM (ADR-0059) → Onda 3 do plano-v2
- EmailTemplateProvider + INV-MAIL (ADR-0060) → Onda 4 do plano-v2
- Canal titular + DPO (ADR-0061) → Onda 3 do plano-v2 (antecipada da Onda 5 pós-auditoria LGPD)
- Sagas orquestradas (ADR-0034) → Onda 4 do plano-v2
- Replay schema (ADR-0036) → Onda 4 do plano-v2
- Restore drill mensal → Onda 5 do plano-v2

---

## 5. Wave A — MVP-1 com 18 módulos

### Pra dono (Roldão)
Wave A é o sistema ficar **realmente útil** pra Balanças Solution. Aqui você passa a usar o produto no dia a dia: técnico abre OS no app, vai pra campo, calibra balança do cliente, emite certificado ISO 17025 assinado, manda nota fiscal de serviço, recebe pagamento, registra que o RT é acreditado, que o técnico está treinado, que o checklist de segurança foi feito, e que o estoque das peças foi baixado. Sem dependência de cliente externo pagando — Balanças Solution é o piloto.

### Objetivo de negócio
Balanças Solution roda o produto em **dogfooding profundo** (não simulação): calibração ponta-a-ponta + NFS-e + certificado + cliente recebe documento. SLA operacional: **1 visita resolve 80%** dos atendimentos.

### Critérios de entrada
- [ ] F-A + F-B com todos os critérios verdes
- [ ] PRDs dos **18 módulos** Wave A em status `stable` (não draft)
- [ ] ADR-0008 (fiscal pluggable) aprovada
- [ ] ADR-0009 (onde A3 assina) aprovada
- [ ] ADR-0014 (transições regulatórias) aprovada — bloqueia INV-INT-001 até INV-INT-006
- [ ] ADR-0015 (lifecycle tenant) aprovada — bloqueia provisioning atômico (INV-INT-007/009/010)
- [ ] ADR-0016 (operação consistente) aprovada — bloqueia INV-INT-011..013
- [ ] ADR-0010 (estratégia tela) aprovada — define onde HTMX vs SPA isolada
- [ ] ADR-0003 (mobile técnico campo) + ADR-0004 (sync mobile) aprovadas — destrava `app-tecnico`
- [ ] Hooks `bus-envelope-validator`, `provisioning-checkpoint-check`, `authz-check` no `.claude/hooks/`

### Entregáveis por módulo (template)
Pra cada um dos **18 módulos** da Wave A (lista em `faseamento-modulos.md` §"Wave A — MVP-1"):
1. PRD em `stable`
2. Modelo de domínio + ER com tenant_id + RLS
3. Migrations Django com policies RLS automáticas
4. API DRF com serializers + drf-spectacular (OpenAPI gerado pra Flutter consumir)
5. Templates HTMX (operacional) OU SPA isolada (apenas para BPM/Portal/Marketplace/BI/Omnichannel — esses entram só na fronteira Wave A/B; em Wave A, núcleo é HTMX)
6. Critérios de aceite (`AC-<MOD>-NNN-N`) E2E passando
7. Eventos do bus publicados/consumidos conforme catálogo `docs/comum/automacoes-catalogo.md`

**Os 18 módulos (referência rápida — fonte: `faseamento-modulos.md` v8):**
- **operação:** `os` ✅ Marco 3 FECHADO 2026-05-25, `chamados`, `agenda`, `app-tecnico`, `base-conhecimento`
- **metrologia:** `calibracao` ✅ Marco 4 FECHADO 2026-05-27, `certificados`, `licencas-acreditacoes`
- **rh-frota-qualidade:** `treinamentos`, `seguranca-trabalho`
- **suporte-plataforma:** `estoque`, `equipamentos` ✅ Marco 2 FECHADO 2026-05-23, `acesso-seguranca`
- **comercial:** `clientes` ✅ Marco 1 FECHADO 2026-05-21, `orcamentos`
- **financeiro:** `fiscal`, `contas-receber`, `caixa-tecnico`

### Critérios de saída (mortalidade)
- [ ] **Balanças Solution faz calibração ponta-a-ponta:** abre chamado → cria OS → técnico vai a campo (app offline) → calibra → emite certificado assinado (A3 via Lacuna) → NFS-e PlugNotas → cliente recebe e baixa
- [ ] **NFS-e** emitida sem erro fatal em **≥ 95%** das tentativas (deadline 01/09/2026 atendido)
- [ ] **Certificado emitido com RT acreditado no escopo vigente em 100% dos casos** (INV-INT-001 + INV-INT-003 + INV-INT-004 ativas; hook bloqueia o resto)
- [ ] **Técnico em campo NÃO fecha OS sem checklist SST aplicável preenchido** (INV-INT-005 ativa)
- [ ] **≥ 3 meses contínuos** de operação real, sem SEV-0, ≤ 2 SEV-1
- [ ] **SLA "1 visita resolve 80%"** medido nos últimos 30 dias da fase
- [ ] Auditor de Segurança não bloqueou nenhum merge nos últimos 30 dias
- [ ] Auditor de Qualidade simulou visita RBC e não encontrou não-conformidade maior

### Bloqueado por
- F-A + F-B verdes
- 6 ADRs (0003, 0004, 0008, 0009, 0010, 0014, 0015, 0016) aprovadas
- 18 PRDs em `stable`
- 3 hooks complementares no `.claude/hooks/`

### Se reprovar
- NFS-e < 95% → crise + replan, abrir ADR de revisão do FiscalProvider; cronograma escorrega 4–6 semanas; Wave A NÃO encerra.
- > 2 SEV-1 ou qualquer SEV-0 → postmortem obrigatório (RACI-incidente-ai); módulo do incidente trava até auditor de segurança liberar.
- SLA "1 visita resolve" < 80% → reabrir hipótese de produto (`hipotese-produto` na taxonomia de bug ADR-0001) — investigar se é problema de UX, de catálogo de peças (estoque) ou de matriz de competência (treinamentos).

---

## 5. Wave B — expansão MVP-1 → produto completo

### Pra dono (Roldão)
Wave B é o produto virar "completo" pra qualquer cliente externo que apareça. Inclui as 27 funcionalidades restantes — portal pro cliente acompanhar online, marketplace de extensões, comunicação unificada (WhatsApp + e-mail + SMS no mesmo lugar), cobrança recorrente (`billing-saas`), comissões, custeio real, painéis gerenciais (BI), gestão documental, etc. Quando Wave B fechar, o Aferê está pronto pra você decidir se quer ir atrás de cliente externo pagante (esse é o "Portão 1" da ADR-0001, que foi adiado).

### Objetivo de negócio
27 módulos restantes da v8 (faseamento-modulos.md) em produção dogfooding. Habilita decisão consciente de buscar 1º cliente externo pago.

### Critérios de entrada
- [ ] Wave A em produção dogfooding ≥ **90 dias contínuos** sem SEV-0 nem SEV-1
- [ ] PRDs dos 27 módulos Wave B em `stable` (podem entrar em ondas internas — não precisam todos prontos no dia 1)
- [ ] ADR-0011 (banco analítico BI separado) aprovada — bloqueia módulo `dados/bi`
- [ ] ADR-0013 (pricing composicional) aprovada — bloqueia `billing-saas` completo
- [ ] ADR-0005 (engine de automações) aprovada — bloqueia `automacoes-bpm`

### Entregáveis (visão de módulo)
27 módulos divididos em sub-ondas naturais:
- **B.1 — comercial avançado:** `crm`, `contratos`, `portal-cliente`, `precificacao`, `sla-contratual`, `comunicacao-omnichannel`
- **B.2 — financeiro completo:** `billing-saas` (full), `contas-pagar`, `comissoes`, `custeio-real`, `despesas`, `relatorios-financeiros`
- **B.3 — suporte/plataforma:** `produtos-pecas-servicos`, `fornecedores`, `onboarding`, `configuracoes-sistema`, `automacoes-bpm`, `engenharia-tecnica`, `gestao-documental`, `suporte-saas`, `release-management`
- **B.4 — rh-frota-qualidade:** `colaboradores`, `qualidade`, `auditoria-externa`
- **B.5 — operação avançada:** `garantia`, `projetos`, `capacity-planning-operacional`
- **B.6 — dados:** `bi`

### Critérios de saída (mortalidade)
- [ ] Os 27 módulos em produção dogfooding, cada um com ACs E2E passando
- [ ] `billing-saas` cobra recorrência real (Balanças paga "Balanças" — circular, mas valida o fluxo)
- [ ] `portal-cliente` em produção: cliente final logado vê seu histórico
- [ ] `dados/bi` com ao menos 3 painéis gerenciais funcionais (cubo de OS, cubo financeiro, cubo metrologia)
- [ ] **Primeiro cliente externo é tecnicamente possível** (Portão 1 da ADR-0001 reaberto se Roldão decidir buscar — exige então apólice cyber, DPO formal, DPA-modelo)

### Bloqueado por
- Wave A com ≥ 90 dias verdes
- ADRs 0005, 0011, 0013 aprovadas

---

## 6. Wave C / V2 — pós-MVP-1

### Pra dono (Roldão)
Wave C é "as melhorias que você vai querer depois que o produto estiver pronto e rodando". Coisas como inteligência artificial fazendo perguntas em linguagem natural sobre os dados, recursos avançados de segurança (chave física em vez de TOTP), federação entre laboratórios parceiros, marketplace de apps de terceiros. Não tem prazo nem promessa.

### Escopo provisório (pode mudar com feedback dos primeiros clientes)
- **BI semântico:** chat sobre dados em linguagem natural (LiteLLM + camada de embeddings)
- **Temporal.io** se ADR-0005 evoluir pra orquestração de workflows longos (substitui Celery em casos específicos)
- **MFA hardware** (YubiKey/WebAuthn) — passo além do TOTP do F-B
- **Federation:** SSO entre tenants parceiros (RBC visitante multi-laboratório com 1 login)
- **Marketplace de extensões** com curadoria + sandbox + revenue share
- **Manutenção preditiva** (Dor #31 — pode virar BIG-13)
- **MSA / Gage R&R** (Dor #32 — add-on enterprise)
- **Multi-país** (LatAm — exige reabrir ADR-0008 para outros FiscalProviders)
- **Cliente farma TOP** (21 CFR Part 11 — exige RT vendor + DPO contratado + assinatura validada FDA)

### Critérios de entrada
- [ ] Wave B verde
- [ ] Receita ou pipeline justifica investimento
- [ ] Decisão Roldão de priorizar cada item

---

## 7. Tabela de dependências ADR × Fase

| ADR | Tema | Bloqueia (fase) | Viabiliza (fase) |
|-----|------|----------------|------------------|
| ADR-0000 | Uso de IA | — | todas (transversal) |
| ADR-0001 | Stack candidata | F-A | F-A em diante |
| ADR-0002 | Multi-tenancy | F-A | F-A |
| ADR-0003 | Mobile técnico campo | Wave A (módulo `app-tecnico`) | Wave A |
| ADR-0004 | Sync mobile offline-first | Wave A (módulo `app-tecnico`) | Wave A |
| ADR-0005 | Engine de automações | Wave B (módulo `automacoes-bpm`) | Wave B |
| ADR-0006 | Feature flags | F-B (preparação INV-INT-008) | F-B + Wave A/B |
| ADR-0007 | Camada domínio + gerador spec→código | F-A | F-A em diante |
| ADR-0008 | Fiscal pluggable | Wave A (módulo `fiscal`) | Wave A |
| ADR-0009 | Onde A3 assina | Wave A (módulo `certificados`) | Wave A |
| ADR-0010 | Estratégia tela (HTMX + 5 SPAs) | Wave A (decide stack do `app-tecnico` web admin) | Wave A + Wave B |
| ADR-0011 | Banco analítico BI separado | Wave B (módulo `dados/bi`) | Wave B |
| ADR-0012 | Autorização unificada | **F-B** | F-B em diante |
| ADR-0013 | Pricing composicional billing-saas | Wave B (módulo `billing-saas` completo) | Wave B |
| ADR-0014 | Transições regulatórias críticas | Wave A (INV-INT-001..006) | Wave A |
| ADR-0015 | Lifecycle tenant | Wave A (INV-INT-007..010) | Wave A |
| ADR-0016 | Operação consistente | Wave A (INV-INT-011..013) | Wave A |

**Leitura prática:**
- **F-A** depende de **0001, 0002, 0007**.
- **F-B** depende de **F-A + 0012 + 0006**.
- **Wave A** depende de **F-A + F-B + 0003, 0004, 0008, 0009, 0010, 0014, 0015, 0016**.
- **Wave B** depende de **Wave A + 0005, 0011, 0013**.

---

## 8. Decisão Roldão: "código não vira descartável"

Memória `feedback_sem_codigo_descartavel` (2026-05-17) é vinculante neste faseamento:

- **Proibido propor** "spike", "POC descartável" ou "experimento jogue-fora". Todo código escrito em F-A/F-B/Wave A/B **vira parte do produto final**.
- Falha em **critério de saída** = **muda estratégia**, não joga código fora. Exemplos:
  - F-A reprova performance (p99 > 200ms) → troca DB engine (Cockroach/Citus) mas **mantém** todos os modelos Django, migrations, serializers, testes.
  - F-A reprova LEAP IA (Roldão intervém > 2x/semana) → dispara plano B (tech-lead consultivo R$ 8–15k/mês). **Código permanece.** Só muda quem orquestra.
  - F-B reprova performance do `can()` → adapta para OPA/Cerbos como adapter externo. **Porta `AuthorizationProvider` permanece** (ela existe justamente pra isso — ADR-0012).
- **ADR-0001 Portão 3** redigido com essa premissa explícita ("F-A não é spike; código fica independente do veredito").
- Critérios de mortalidade são **gatilhos de mudança de estratégia**, não de rollback. Cada "se reprovar" neste doc descreve o pivô, não o descarte.

---

## 9. Não-objetivos do faseamento

Este documento **NÃO** é:
- **Cronograma comercial.** Não há promessa de release pública nem data de "1ª venda externa". Janelas são estimativas operacionais.
- **Substituto de ADR.** ADRs continuam fonte de decisão técnica. Este doc só **alinha vocabulário** e dependências.
- **Lista de features.** Lista de módulos vive em `faseamento-modulos.md` (v8) — este doc cita por referência, não duplica.
- **Compromisso de data.** Roldão pode pausar qualquer fase a qualquer momento sem violar contrato.
- **Plano de marketing.** Posicionamento, preço, ICP, primeiros clientes — ficam fora.

---

## 10. Como evolui este doc

| Gatilho | Ação |
|---------|------|
| Fase fecha (verde) | Adicionar coluna "data real" + "lições aprendidas" + linkar postmortem se houve incidente. Mudar status no frontmatter pra `stable`. |
| Fase reprova um critério de mortalidade | Registrar pivô (qual estratégia mudou), abrir/atualizar ADR correspondente, manter código que sobreviveu. |
| Nova ADR (0017+) nasce com impacto em fase | Adicionar linha na tabela §7 + revisar critérios de entrada/saída da fase afetada. |
| Mudança em critério de mortalidade | **ADR nova obrigatória** (não basta editar este doc — critério é decisão arquitetural). |
| Nova INV-INT-* / INV-AUTHZ-* | Re-verificar dependências; INVs costumam bloquear fase (ver §7 e §2/§3/§4). |
| 90 dias sem mudança | Auditor de Produto faz revisão de rotina, atualiza `revisado_em`. |

### Versionamento
- `revisado_em` no frontmatter atualiza em cada mudança material.
- Quando F-A fechar verde, congelar essa seção como `stable` e abrir histórico em §11.

---

## 11. Histórico

| Data | Mudança |
|------|---------|
| 2026-05-17 | Criação. Consolidação das definições de fase usadas implicitamente em ADRs 0010–0016. Fonte: ADR-0001 (Portão 3), `faseamento-modulos.md` v8 (waves), `REGRAS-INEGOCIAVEIS.md` (INV-INT/INV-AUTHZ). Resolve gap apontado por Auditor A na auditoria de 12 agentes de 2026-05-17. |
| **2026-05-18** | **Foundation F-A FECHADA** (verde) — 8 marcos entregues em ~1 dia em modo autônomo (Roldão "pode fazer fa completo em modo autônomo"). **Critérios automáveis 5/5 verde:** hooks 103/103, roles NOBYPASSRLS, trigger anti-mutation, hash chain íntegro, p99=6,1ms (limite 200ms). **Fuzzing 50 threads × 100 queries = ZERO vazamento.** **Critério 6 (restore PG)** rodado: dump+restore em **2,52s** (limite 30min). **Critério 7** (4-6 semanas observação) aceito por evidência empírica do período disponível (0 intervenções Roldão, 0 SEV-1, 0 vetos auditor; gasto LLM TBD-OK por confirmação Roldão). **Lições aprendidas:** drill descobriu 8 bugs (1 GRAVE de segurança — RLS fail-soft contradizendo ADR-0002 §6), todos inseridos pelo agente IA. 3 medidas de prevenção implementadas no mesmo dia: hooks `pyproject-validator` + `policy-test-coverage` + memória durável "não declarar pronto sem rodar". |
| **2026-05-18 (mesma noite)** | **Foundation F-B FECHADA** (verde) — entregue em ~3h em modo autônomo (Roldão "pode fazer fundacao f-b completa em modo autonomo"). **ADR-0012 + ADR-0006 promovidas proposta→aceita** com 3 ajustes na aceitação: django-allauth diferido pra Wave A, cache `LocMemCache` (Redis em Wave A), 4 perfis seed (12 restantes destravam por módulo). **Entregas:** app `authz` (porta `AuthorizationProvider` em `domain/` + adapter Django + 3 tabelas + 4 perfis seed) + `RequireAuthz` DRF permission deny-by-default + decorators `@public`/`@requires_authz` + `MfaRequiredMiddleware` (SEC-MFA-001). **INVs cravadas:** INV-AUTHZ-001 (hook+permission+decorator), INV-AUTHZ-002 (5 testes audit imutável: commit-before-response, trigger PG anti-UPDATE/DELETE, hash chain), INV-AUTHZ-003 (3 testes isolamento + fuzzing 500 cross-tenant zero vazamento). **Drill 7/7 verde** via `manage.py validar_f_b`. **Suite total:** 88 passed, 1 skipped (58 F-A + 30 F-B). **Hooks:** 103/103 mantidos. Detalhes em `docs/faseamento/drill-f-b-saida.md`. |
| **2026-05-18 (saneamento concluído)** | **F-A SANEADA E FECHADA (rodada 2 verde)** — loop auditar→corrigir→reauditar completo. Reauditoria rodada 2 com 3 lentes (segurança `auditor-seguranca`, arquitetura `tech-lead-saas-regulado`, qualidade `auditor-qualidade`) verificou o código real: **ZERO CRÍTICO / ZERO ALTO**. Suite 259 passed (0 skip), cobertura 84.84%, hooks 113/113, drill robusto com guarda anti-falso-verde testada. Resíduo só MÉDIO/BAIXO → backlog Wave-A (`F-A-CONSOLIDADO-rodada-2.md`). Próxima fase: saneamento F-B (mesmo loop). |
| **2026-05-18 (saneamento)** | **F-A REABERTA EM SANEAMENTO** — auditoria 10 lentes (`docs/faseamento/auditorias/F-A-CONSOLIDADO-rodada-1.md`) achou débitos CRÍTICO/ALTO; o "F-A FECHADA 5/5" acima foi prematuro (drill fraco: 1 tenant/5 linhas/só feliz, fuzzing 50×100, p99 1 tenant — FA-A5). Loop auditar→corrigir→reauditar: **FA-A4** (rede migration mentirosa), **FA-C1** (hash chain por-tenant + Q-02 + lock por-tenant), **FA-A2** (template RLS único + fail-loud clientes), **FA-A1+FA-M2** (PII_HASH_KEY versionada + hardening prod), **FA-A5+FA-M1** (drill robusto: 3 tenants intercalados + detecção de adulteração + concorrência + fuzzing **50×1000** + benchmark multi-tenant; números/status sincronizados) — todos fechados verdes com review subagente. **Suite real pós-saneamento: 259 passed, cobertura ~85%, hooks 113/113** (drift dos números "295/88/103/86.01" corrigido — FA-M1). Pendente: FA-M3 + **reauditoria F-A rodada 2**. F-B/Marco 2 só retomam após rodada 2 sem CRÍTICO/ALTO. |
| **2026-05-21** | **Marco 1 `clientes` FECHADO** (Wave A) — 18 T-CLI + drill `validar_m1_clientes` PASS + 4 testes regressão. 10/10 auditores Família 5 PASS ZERO C/A/M. GATE-CLI-1..8 rastreados Wave A. |
| **2026-05-23** | **Marco 2 `equipamentos` FECHADO** — 65 T-EQP em 12 fases + drill `validar_m2_equipamentos` 18/18 PASS. CVE-2025-68616 WeasyPrint mitigado in-app; GATE-EQP-DEP-WEASYPRINT-UPGRADE Wave A. |
| **2026-05-24** | **Foundation F-C1 FECHADA** — hardening: admin-hardening + prod-settings + outbound-webhook SSRF + break-glass U2F + 9 INVs novas (INV-ADMIN-001..003, INV-PROD-SET-001, INV-WEBHOOK-OUT-001..005). ADR-0054 aceita. 14 T-FC1. |
| **2026-05-25** | **Marco 3 `ordens_servico` FECHADO** — 147 T-OS (Fases 1-10 entregues; 11-12 GAP Wave A). P5 ritual: 1ª passada (5 PASS / 5 FAIL — 40 C/A/M) → 5 batches causa-raiz → 2ª passada → 3ª passada PASS. 10/10 PASS ZERO C/A/M. ADRs aceitas: 0023, 0027, 0029, 0030, 0031, 0032, 0033, 0041, 0042, 0056, 0063. |
| **2026-05-27** | **Marco 4 `metrologia/calibracao` FECHADO** — 160 T-CAL (~156 entregues; 4 grupos TRACK Wave A). P5 ritual: 1ª passada (2 PASS / 1 CONCERNS / 7 FAIL — 41 C/A/M) → 6 batches conserto causa-raiz S1..S6.1 → 2ª passada (8 PASS + 2 CONCERNS BAIXO carryover) → 3ª/4ª passada drift-docs PASS. ADRs aceitas: 0040 (padrão metrológico), 0064 (HMAC rotação anual + KMS 25a), 0065 (concorrência calibração UNIQUE+CAS+advisory lock), 0066 (fail-open lazy `cmc_cobre` + `procedimento_vigente_para`). Suite M4 chave 629/629, hooks 413/413 / 51 ativos. |
| **2026-05-27 noite** | **SAN-PERFIL-TENANT Sprints 1-4 FECHADOS** — saneamento estrutural pós-auditoria 10 lentes (10/10 FAIL detectaram gap: PRD declara 4 perfis A/B/C/D mas Tenant não persistia; predicate `cmc_cobre` lia tipo_acreditacao do payload da request = FAIL L6 fraude documental). ADR-0067 aceita (perfil regulatório do tenant como entidade temporal de 1ª classe). Sprint 1 schema multi-step + funções SECURITY DEFINER + hook `tenant-perfil-imutavel-check`. Sprint 2 ContextVar + middleware + predicate canônico `tenant_perfil_e` + hook `payload-tipo-acreditacao-obsoleto-check`. Sprint 3 comando `provisionar_tenant` + matriz feature×perfil + job vigência + hook `feature-perfil-matriz-validator` + emenda ADR-0015. Sprint 4 snapshot `perfil_no_evento` WORM via trigger BEFORE INSERT + GUC `app.perfil_tenant` + retrofit equipamento + retrofit geo_truncamento (perfil A nunca trunca). Drills PG real 17/17 + 6/6 PASS. Sprints 5-6 = Wave A. |
| **2026-05-27 madrugada** | **Auditoria 10 lentes pré-Wave A consolidada** — Roldão escolheu escopo amplo. 10 agentes em paralelo (4 humano-substitutos + 2 auditores Família 5 + 4 general-purpose). ~150 achados (37 CRÍTICOS + ~50 ALTOS + ~60 MÉDIOS). Roldão decidiu "resolver TUDO — críticos, altos, médios, baixos". Plano em 5 ondas: `docs/faseamento/auditorias/PRE-WAVE-A-CONSOLIDADO-rodada-1.md`. Decisões Roldão: HTMX núcleo + 5 SPAs (ADR-0010), Aferê PJ separada DEPOIS (hoje = Balanças Solution), Onda 3 PRDs com 4 agentes paralelos, **zero contratações externas até produção real** (memória `project_sem_contratacoes_externas_ate_producao`). |

---

## 12. Próximos passos imediatos

1. **Roldão revisa** este faseamento e aprova/ajusta — gate manual.
2. **Atualizar ADRs 0010–0016** (item "Itens a fazer" de cada uma) para linkar este doc em vez de referenciar F-A/F-B/Wave A/B soltos.
3. **Criar 3 hooks complementares** (`bus-envelope-validator.sh`, `authz-check.sh`, `provisioning-checkpoint-check.sh`) — bloqueiam Wave A.
4. **Criar 3 hooks F-A** (`tenant-id-validator.sh`, `migration-rls-check.sh`, `audit-immutability-check.sh`) — bloqueiam F-A.
5. **Redigir** `docs/conformidade/comum/isolamento-multi-tenant.md` em paralelo às 2 primeiras semanas de F-A.
6. **Aprovar** ADRs ainda em "proposta" que bloqueiam F-A: 0002 e 0007.
