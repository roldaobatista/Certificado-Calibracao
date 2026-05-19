---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
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

---

## 4. Wave A — MVP-1 com 18 módulos

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
- **operação:** `os`, `chamados`, `agenda`, `app-tecnico`, `base-conhecimento`
- **metrologia:** `calibracao`, `certificados`, `licencas-acreditacoes`
- **rh-frota-qualidade:** `treinamentos`, `seguranca-trabalho`
- **suporte-plataforma:** `estoque`, `equipamentos`, `acesso-seguranca`
- **comercial:** `clientes` ✅ Marco 1 FECHADO 2026-05-18 (5/5 US verdes — cadastro PF/PJ, visão 360, importação CSV, bloqueio, dedup; 3 auditores Família 5 aprovaram), `orcamentos`
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
| **2026-05-18 (saneamento)** | **F-A REABERTA EM SANEAMENTO** — auditoria 10 lentes (`docs/faseamento/auditorias/F-A-CONSOLIDADO-rodada-1.md`) achou débitos CRÍTICO/ALTO; o "F-A FECHADA 5/5" acima foi prematuro (drill fraco: 1 tenant/5 linhas/só feliz, fuzzing 50×100, p99 1 tenant — FA-A5). Loop auditar→corrigir→reauditar: **FA-A4** (rede migration mentirosa), **FA-C1** (hash chain por-tenant + Q-02 + lock por-tenant), **FA-A2** (template RLS único + fail-loud clientes), **FA-A1+FA-M2** (PII_HASH_KEY versionada + hardening prod), **FA-A5+FA-M1** (drill robusto: 3 tenants intercalados + detecção de adulteração + concorrência + fuzzing **50×1000** + benchmark multi-tenant; números/status sincronizados) — todos fechados verdes com review subagente. **Suite real pós-saneamento: 259 passed, cobertura ~85%, hooks 113/113** (drift dos números "295/88/103/86.01" corrigido — FA-M1). Pendente: FA-M3 + **reauditoria F-A rodada 2**. F-B/Marco 2 só retomam após rodada 2 sem CRÍTICO/ALTO. |

---

## 12. Próximos passos imediatos

1. **Roldão revisa** este faseamento e aprova/ajusta — gate manual.
2. **Atualizar ADRs 0010–0016** (item "Itens a fazer" de cada uma) para linkar este doc em vez de referenciar F-A/F-B/Wave A/B soltos.
3. **Criar 3 hooks complementares** (`bus-envelope-validator.sh`, `authz-check.sh`, `provisioning-checkpoint-check.sh`) — bloqueiam Wave A.
4. **Criar 3 hooks F-A** (`tenant-id-validator.sh`, `migration-rls-check.sh`, `audit-immutability-check.sh`) — bloqueiam F-A.
5. **Redigir** `docs/conformidade/comum/isolamento-multi-tenant.md` em paralelo às 2 primeiras semanas de F-A.
6. **Aprovar** ADRs ainda em "proposta" que bloqueiam F-A: 0002 e 0007.
