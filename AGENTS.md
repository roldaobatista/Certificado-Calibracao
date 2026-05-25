# AGENTS.md — canônico de produto/arquitetura

> **Para agentes (Claude Code, Codex CLI, Cursor, Windsurf, Kiro):** este é o documento de referência primária do projeto. O `CLAUDE.md` (irmão) é só adendo de harness do Claude Code e importa este via `@AGENTS.md`.
>
> **Status (2026-05-25 — F-A+F-B+M1+M2+F-C1+M3-OS FECHADAS):** entregues via ritual Spec Kit completo. **F-A, F-B, Marco 1, Marco 2, F-C1 e Marco 3 OS: 10/10 auditores Família 5 PASS ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO**. **M3 OS FECHADO 2026-05-25** após 1ª passada (5 PASS / 5 FAIL — 40 achados C/A/M) + 5 batches conserto causa-raiz (drift / idempotência / qualidade / produto / segurança) + 2ª passada (3 PASS + 2 FAIL consertados — ADR-0063 + sweep) + 3ª passada (produto CONCERNS→PASS + drift-docs FAIL→PASS). Gate de fechamento = INV-RITUAL-001 satisfeito.
> - Docs canônicas: `docs/faseamento/{F-A,F-B,M1-clientes,M2-equipamentos,F-C1,M3-os}/{spec,plan,auditoria-familia5}.md`.
> - F-A: 8 GAPs (T-FA-01..08) — 7 causa-raiz + ADR-0020. F-B: 6 GAPs (T-FB-01..06). F-C1: 14 T-FC1. M3 OS: 147 T-OS (Fases 1-10 entregues; 11-12 GAP Wave A).
> - **Suite total (verificado 2026-05-24): pytest 905/0/0 verde em 26min + suite M3 chave 89/89 em 415s; hooks `_test-runner.sh` 312/312 verdes em 42 hooks ativos (+migration-concorrencia-os-check, +sync-merge-foto-appendonly, +authz-check estendido com 6 predicates M3); makemigrations limpo; ruff zero issues; drills `validar_{f_a,f_b,m1_clientes,m2_equipamentos,f_c1}` verdes (`validar_m3_os` em GATE-OS-VALIDAR-DRILL Wave A).**
> - **Gates Wave A rastreados (não bloqueiam Foundation dogfooding; pré-1º tenant externo):** GATE-1..7 (B2/WORM, verificação periódica, NTP, ciclo chave PII, hash AcessoDadosCliente, ADR-0020, higiene `::uuid`) + GATE-FB-1..4 + GATE-CLI-1..8 + **GATE-FC1-ROTACAO-DRILL-REAL** + **GATE-CYBER-BREAKGLASS-U2F-ENFORCE** + **GATE-OS-PERF-1..5** + **GATE-OS-BUS-BRIDGE-1** + **GATE-OBS-LOG-EXTRA-1** + **GATE-OBS-METRIC-OS-1** + **GATE-IDEMP-HOOK-DETECT-ACTION** + **GATE-OS-SYNC-WAVE-A** + **GATE-OS-SUCESSAO-EVIDENCIA** + **GATE-OS-ANON-RETRY-1** + **GATE-OS-VALIDAR-DRILL** + **GATE-OS-CONSBIO-TEXTO-OAB** + **GATE-OS-DPIA-OAB** (Wave A).
> - Marco 1 `clientes` (Wave A): **FECHADO**. Marco 2 `equipamentos`: **FECHADO**. F-C1: **FECHADO**. **Marco 3 `ordens_servico`: FECHADO 2026-05-25** — ver `docs/faseamento/M3-os/auditoria-familia5.md` §"Veredito FINAL". ADRs aceitas no escopo M3 OS: **0023, 0027, 0029, 0030, 0031, 0032, 0033, 0041, 0042, 0056, 0063**. Estado vivo em `.agent/CURRENT.md`.

---

## 1. Identidade do produto

- **Nome:** "Aferê" — **PROVISÓRIO**. Não comprar domínio, não escrever código com slug `afere`, não registrar INPI sem decisão final.
- **Escopo:** ERP completo para empresas de assistência técnica + calibração metrológica (laboratório ISO 17025).
- **Modelo:** SaaS multi-tenant.
- **N módulos:** mínimo 6 confirmados (CRM, Financeiro de alto nível, Orçamentos, Chamados, Ordens de Serviço, Calibração), total real = saída do discovery (pode ser 11, 21 ou 50).
- **Cliente piloto:** Balanças Solution (empresa do Roldão — dogfooding). Não substitui cliente externo pago sob NDA, que ainda é Portão 1 aberto.
- **Diferencial central:** Calibração ISO 17025 — disputa com Calibre.Software (mystery shopping documental concluído).

**Founder is customer:** Roldão é o primeiro cliente. Mitigação obrigatória do risco "customização disfarçada" = Família 0 Discovery rigorosa (15 artefatos), entrevistas com OUTRAS empresas + OPERADORES.

---

## 2. Stack candidata (ADR-0001 — 3 portões)

| Camada | Escolha | Notas |
|---|---|---|
| Backend | **Django + DRF** | Admin built-in usado como ferramenta operacional (não interface final) |
| Banco | **PostgreSQL** | Multi-tenancy via schema-shared + RLS + middleware `tenant_id` (ADR-0002) |
| Filas | **procrastinate** | Python sobre PostgreSQL (NÃO `pg-boss` — esse é Node). Celery secundário se necessário |
| Frontend web | **HTMX** sobre Django templates | Reduz dependência de JS pesado |
| Mobile | **Flutter** | Offline-first; assinatura A3 via Flutter FFI + Web PKI Lacuna no PC (ADR-0009) |
| KMS | **AWS KMS Multi-Region Key** | sa-east-1 ↔ us-east-1; **NÃO cópia manual** |
| Storage | **Backblaze B2** (WORM) | Trilha imutável + crypto-shredding por tenant |
| Hospedagem | **Hostinger VPS KVM 4** (SP/BR) | Provedor B (Magalu/Oracle/AWS) pra DR |
| Observabilidade | Grafana Cloud + Axiom | |

**Stack está CANDIDATA, não final** — vira definitiva após Portões 2+3 da ADR-0001 (Portão 1 diferido pra V2). O teste real é construir a Foundation F-A (multi-tenant + RLS + audit) em 4-6 semanas com critérios de validação aplicados — sem spike descartável. Ver memória `nao-construir-codigo-descartavel`.

Veja também: ADR-0002 (multi-tenancy), ADR-0007 (camada domínio + gerador spec→código), ADR-0008 (fiscal pluggable), ADR-0009 (onde A3 assina), `docs/arquitetura/anti-corrosion-layer.md` (**v3 com 18 portas**: as 11 originais Fiscal, Signature, LLM, Storage, Hosting, Auth, Queue, Sync, MultiTenant, OmniChannel, PaymentGateway + AuthorizationProvider, BpmEngineProvider, RuleEngineProvider, AnalyticsBackend, DocumentSearchProvider, MarketplaceExtensionProvider, EmailTemplateProvider — adicionadas na auditoria 10 agentes de 17/05).

---

## 3. Princípios não-negociáveis

Ver `.specify/memory/constitution.md` (6 princípios) + `REGRAS-INEGOCIAVEIS.md` (IDs `INV-NNN`, `INV-TENANT-NNN`, `TST-NNN`, `SEC-NNN`, `INV-AGENT-NNN` — fonte única).

**Resumo operacional:**
1. **Documento é estado compartilhado** — agente que decidir sem doc inventa diferente toda vez.
2. **Spec gera código** (spec-as-source). Não código gera spec.
3. **Conciso vence completo** — AGENTS.md e CLAUDE.md ≤ 300 e ≤ 150 linhas respectivamente.
4. **Non-goals explícitos** — toda spec/ADR declara o que NÃO está no escopo.
5. **IDs rastreáveis** — `US-<MOD>-NNN` → `AC-<MOD>-NNN-N` → `T<MOD>NNN` → commit.
6. **Negócio vence conveniência do agente** — não otimizar pelo que o agente IA erra menos; otimizar pelo Roldão/produto. Critério "agentes dominam X" é tiebreaker, nunca principal.

**Regra mestre:** regra crítica vira **hook**, não só doc. Hoje em `.claude/hooks/` (**42 hooks ativos**, 312/312 casos verdes no `_test-runner` — ampliação Marco 3 OS Fase 9 2026-05-24): block-destructive, secrets-scanner, INV-checker, tenant-id-validator, anti-mascaramento, context-budget, paths-frontmatter-validator, bus-envelope-validator, authz-check (estendido com 6 predicates M3), provisioning-checkpoint-check, mock-in-production, migration-rls-check, audit-immutability-check, audit-pii-salt-check, pyproject-validator, policy-test-coverage, ritual-gate-check, cliente-canonico-imutavel, event-helper-unico, lgpd-policy-unica, csv-safety-import, qr-hmac-check, equipamento-imutabilidade-check, trigger-stub-sweep, port-binding-validator, vigencia-canonica-check, soft-delete-padrao-check, fk-pii-anonimizavel-check, biometria-key-validator, os-conclusao-todas-terminais-check, frontmatter-revisado-em-check, spec-ac-binario-check, prod-settings-check, admin-hardening-check, outbound-webhook-ssrf-check, **migration-concorrencia-os-check** (M3 P9 — INV-OS-CONC-001), **sync-merge-foto-appendonly** (M3 P9 — INV-OS-SYNC-001). `_test-runner.sh` é o orquestrador.

---

## 4. Decisões fundadoras (D1–D5)

| # | Decisão | Detalhe |
|---|---------|---------|
| **D1** | Adotar **Spec Kit** | Framework leve de spec-driven development |
| **D2** | **Spec-as-source** | Spec PT é a verdade; código é gerado/derivado |
| **D3** | **Nomenclatura híbrida PT + 7 arquivos EN de ferramenta** | `CLAUDE.md`, `AGENTS.md`, `README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODEOWNERS` |
| **D4** | **Devcontainer** | Criado após ADR-0001 fechar |
| **D5** | **CODEOWNERS expandido** (10 paths) | 5 anti-bypass + `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/` |

Não reabrir sem ADR.

---

## 5. Modelo de agentes

**4 subagentes especialistas em `.claude/agents/` (humanos-substitutos):**
- `tech-lead-saas-regulado` — arquitetura, decisões técnicas
- `advogado-saas-regulado` — LGPD, contratos, compliance regulatório (parecer estratégico)
- `corretora-seguros-saas` — risco, seguro cyber + RC profissional
- `consultor-rbc-iso17025` — calibração, NIT-DICLA, RBC

**10 auditores Família 5** (expandido em 2026-05-19, motivado pelo bug `sanitizar_payload_audit` que passou em PASS dos 3 auditores 1.0.0) — operam pré-commit/pré-merge via prompts versionados em `docs/governanca/auditor-*-prompt.md`. Catálogo em `docs/governanca/catalogo-auditores.md`.

| # | Auditor | Versão | Bloqueia |
|---|---|---|---|
| 1 | `auditor-seguranca` | 1.1.0 stable | commit |
| 2 | `auditor-qualidade` | 1.1.0 stable | commit |
| 3 | `auditor-produto` | 1.1.0 stable | merge |
| 4 | `auditor-drift-docs` | 1.0.0 | consultivo |
| 5 | `auditor-llm-correctness` | 1.0.0 stable | commit |
| 6 | `auditor-performance` | 1.0.0 stable | commit |
| 7 | `auditor-observabilidade` | 1.0.0 stable | commit |
| 8 | `auditor-idempotencia` | 1.0.0 stable | commit |
| 9 | `auditor-supplychain` | 1.0.0 stable | commit |
| 10 | `auditor-conformidade-lgpd` | 1.0.0 stable | commit |

Severidade consistente com INV-RITUAL-001 — MÉDIO+ bloqueia fechamento de Fase/Marco/Story.

**Humano licenciado contratado SOB DEMANDA** para casos que exigem assinatura legal (apólice SUSEP, parecer OAB, dossiê CGCRE).

Inventário de subagentes técnicos genéricos (code-reviewer, test-runner, etc.) **NÃO existe por escolha** — o trabalho deles está distribuído entre os 4 substitutos + 10 auditores.

---

## 6. Comandos (Foundation F-A — Marco 1 entregue 2026-05-17)

Stack ativa: Python 3.12 + Django 5.0 + DRF + PostgreSQL 16 + Poetry. Rodam em Docker Compose local (memória `project_deploy_so_quando_roldao_quiser`).

| Operação | Comando |
|---|---|
| Setup local (dono) | ver `docs/operacao/setup-local.md` |
| Subir sistema | `docker compose up` |
| Derrubar sistema | `docker compose down` (mantém dados) / `docker compose down -v` (apaga banco) |
| Rebuild após mudança Python | `docker compose up --build` |
| Rodar testes | `docker compose exec app poetry run pytest` |
| Cobertura HTML | `reports/coverage/index.html` após pytest |
| Lint + format | `poetry run ruff check . && poetry run ruff format .` |
| Type-check | `poetry run mypy src config` |
| Migration nova | `docker compose exec app poetry run python manage.py makemigrations` |
| Aplicar migrations | `docker compose exec app poetry run python manage.py migrate --database=migrator` |
| Verificar objetos de segurança no banco (FA-A4) | `docker compose exec app poetry run python manage.py verificar_objetos_seguranca` |
| Shell Django | `docker compose exec app poetry run python manage.py shell_plus` |
| Testar hooks | `bash .claude/hooks/_test-runner.sh` (312 casos / 42 hooks ativos) |

---

## 7. Política de commits

- **Atômicos:** um propósito por commit. Não misturar fix + feature + refactor.
- **Mensagem:** uma linha curta + descrição se necessário. Padrão livre (não usar Conventional Commits estrito ainda — decisão deferida).
- **Stage seletivo:** `git add <arquivo>` por arquivo. Nunca `git add .` com outras frentes sujas.
- **Co-Authored-By Claude:** incluir nas mensagens.
- **Nunca usar:** `--no-verify`, `--skip-*`, `--ignore-*`, `git reset --hard`, `git push --force`, `git branch -D`, `rm -rf`, `drop table` — sem confirmação explícita do Roldão.
- **Hooks dos commits:** ver `.claude/hooks/block-destructive.sh` e `secrets-scanner.sh`.

---

## 8. Convenções

- **Idioma:** Português (Brasil) em tudo — código, comentários, docs, commits.
- **Linguagem do canal:** sem jargão técnico com o Roldão (ele não programa). Ver `CLAUDE.md` seção "Perfil do usuário" pra tabela de tradução.
- **Pastas chave:**
  - `docs/discovery/` — Família 0 (15 artefatos)
  - `docs/adr/` — Architecture Decision Records (numeração saltou 0003→0007 conscientemente; ver ponto 11)
  - `docs/dominios/<dominio>/modulos/<modulo>/` — estrutura híbrida (D5 do v5)
  - `docs/comum/` — transversal a domínios
  - `docs/governanca/` — Família 5 (auditores, RACI, limites)
  - `docs/conformidade/` — LGPD, fiscal, ISO 17025
  - `docs/operacao/` — runbooks (família 4, ainda vazia)
  - `docs/seguranca/` — MCP policy, supply chain (ainda vazia)
- **Frontmatter obrigatório** em todo doc novo: `owner`, `revisado-em`, `status: draft|stable|deprecated`. Ver `docs/CONVENCOES-DOC.md`.

---

## 9. Segurança / dados

- **Multi-tenancy:** PostgreSQL RLS + middleware Django injeta `tenant_id` em todas as queries. Roles `NOBYPASSRLS`. Hook `tenant-id-validator` ainda a criar.
- **A3 assina sempre client-side** via Web PKI Lacuna (defesa anti-replay: nonce + signing-time server-controlled + one-shot).
- **KMS:** AWS Multi-Region Key — `sa-east-1` primária, `us-east-1` réplica.
- **WORM:** trilha imutável de eventos em Backbloze B2; documentos fiscais corrigíveis em estado mutável.
- **Crypto-shredding por tenant** pra LGPD direito ao esquecimento.
- **Retenção:** matriz Receita 5 anos × ISO 17025 8.4 (~25 anos) × LGPD em `docs/conformidade/comum/retencao-matriz.md` (pendente).

---

## 10. Pontos de extensão

- **MCP servers (`.mcp.json`):** github plugado; filesystem/playwright/postgres sob demanda
- **Hooks (`.claude/hooks/`):** ciclo de vida Claude Code; cuidados Windows + Git Bash em `CLAUDE.md`
- **Subagentes (`.claude/agents/`):** descrição com gatilho concreto; ferramentas restritas
- **Skills (`.claude/skills/`):** criar quando padrão repetir 3x
- **Rules (`.claude/rules/`):** sempre com `paths:` frontmatter (lazy load)

---

## 11. ADRs ativas

| # | Tema | Status | Bloqueia fase | Depende de |
|---|------|--------|---------------|------------|
| ADR-0000 | Uso de IA | ✅ aceito | — | — |
| ADR-0001 | Stack (Django + Flutter + PG) | 🟡 candidata — 3 portões | Foundation F-A | — |
| ADR-0002 | Multi-tenancy (schema-shared + RLS v2) | ✅ aceito v2 (2026-05-17) | Foundation F-A — destravado | ADR-0001 |
| ADR-0003 | Mobile (técnico de campo) | 🟡 proposta | Wave A (app-tecnico) | ADR-0001 |
| ADR-0004 | Sync mobile offline-first | 🟡 proposta | Wave A (app-tecnico) | ADR-0003 |
| ADR-0005 | Engine de automações | 🟡 proposta | Wave B (automacoes-bpm) | ADR-0006 |
| ADR-0006 | Feature flags | ✅ aceito (2026-05-18) | Foundation F-B — destravado | ADR-0002, ADR-0012 |
| ADR-0007 | Camada domínio + gerador spec→código | ✅ aceito (2026-05-17) | Foundation F-A — destravado (codegen completo é Wave A) | ADR-0001 |
| ADR-0008 | Fiscal pluggable (FiscalProvider) | 🟡 proposta | Wave A (fiscal/NFS-e) | — |
| ADR-0009 | Onde A3 assina (cliente-side via Lacuna) | 🟡 proposta | Wave A (certificados) | — |
| ADR-0010 | Estratégia de tela (HTMX núcleo + 4 SPAs isoladas) | 🟡 proposta — pós-auditoria 10 agentes 17/05 | Wave A (UI) | ADR-0001, ADR-0007 |
| ADR-0011 | Banco analítico/BI separado do operacional (3 fases) | 🟡 proposta — pós-auditoria 10 agentes 17/05 | Wave B (bi) | ADR-0002 |
| ADR-0012 | Autorização unificada (porta AuthorizationProvider) | ✅ aceito (2026-05-18) | Foundation F-B — destravado | ADR-0002, ADR-0006 |
| ADR-0013 | Pricing composicional billing-saas (7 tipos de componente) | 🟡 proposta — requisito Roldão 17/05 | Wave B (billing-saas full) | ADR-0005 (soft), ADR-0015 |
| ADR-0014 | Transições regulatórias críticas (6 fluxos ISO 17025) | 🟡 proposta — pós-auditoria integrações 17/05 | Wave A (regulatório) | ADR-0002, ADR-0012 |
| ADR-0015 | Lifecycle tenant (provisioning atômico + sync plano-features + inadimplência) | 🟡 proposta — pós-auditoria integrações 17/05 | Wave A (onboarding+suspensão) | ADR-0002, ADR-0006, ADR-0012 |
| ADR-0016 | Operação consistente (desligamento síncrono + BOM + NC notifica + 10 médios) | 🟡 proposta — pós-auditoria integrações 17/05 | Wave A (operação) | ADR-0002, ADR-0012, ADR-0014 |
| ADR-0017 | CNPJ alfanumérico (IN RFB 2.229/2024 — vigência jul/2026) | ✅ aceito (2026-05-18) | Wave A (todo módulo que persista CNPJ) | ADR-0007, ADR-0002 |
| ADR-0018 | Scanner QR em PWA + BarcodeDetector até Flutter chegar | 🟡 proposta — pós-auditoria PRD `equipamentos` Wave A Marco 2 (2026-05-18) | Wave A Marco 2 (US-EQP-003) | ADR-0001, ADR-0010 |
| ADR-0019 | Responsabilidade civil + segurabilidade de código gerado por agentes IA | 🟡 proposta — pós-auditoria PRD `equipamentos` Wave A Marco 2 (2026-05-18) | Contratação de apólice antes do 1º tenant externo pago | ADR-0000 |
| ADR-0020 | REGRAS-INEGOCIÁVEIS &gt; orçamento; decisão CODEOWNERS expandida (D5) | ✅ aceito (2026-05-19) | Foundation F-A — fechada | — |
| ADR-0021 | Anonimização vs retenção regulatória (3 zonas A/B/C — LGPD art. 16/18 vs Receita/ISO) | ✅ aceito (2026-05-20) — Onda 7B retrofit M3 (NOVO-ALTO-6) | Wave A (matriz `eliminacao_efetiva` vs `anonimizacao_em_lugar` em NF/cert) | ADR-0000, ADR-0007 |
| ADR-0022 | Gestão do RT do tenant (US-EQP-007 / NIT-DICLA-021 — vigência + competências por grandeza + EXCLUDE GIST + imutabilidade pós-INSERT) | ✅ aceito (2026-05-22) — Marco 2 entregue (T-EQP-061..065 + tests/regressao/test_inv_eqp_rt_001.py) | Wave A (GATE-EQP-1 A3 Lacuna + GATE-EQP-RT carta competência + GATE-EQP-RT-NOTIF consumer ANPD/CGCRE) | ADR-0002, ADR-0009, ADR-0012 |
| ADR-0023 | OS com Atividades (1 OS contém N AtividadeDaOS — cada uma com tipo + checklist + estado próprios; suporta caso combinado manutenção + calibração) | ✅ aceito (2026-05-23) — decisão Roldão pré-Marco 3 OS | Wave A Marco 3 (`os`) + Marco 4 (`calibracao`) | ADR-0002, ADR-0007 |
| ADR-0024 | Regra de decisão ISO 17025 cl. 7.8.6 (3 modos + override por cliente + lock pós-emissão) | ✅ aceito (2026-05-23) — Onda 6 saneamento destravar Marco 4 | Wave A Marco 4 (`calibracao`) | ADR-0023 |
| ADR-0025 | Validação de software ISO 17025 cl. 7.11 (URS/IQ/OQ/PQ + replay determinístico + 2º caminho de cálculo) | ✅ aceito (2026-05-23) — Onda 6 saneamento destravar Marco 4 | Wave A Marco 4 + V2 RT vendor | ADR-0007 |
| ADR-0026 | 2ª conferência + independência RT (cl. 6.2.5 — política de exceção objetiva 4 condições + 5%/mês) | ✅ aceito (2026-05-23) — Onda 6 saneamento destravar Marco 4 | Wave A Marco 4 (`calibracao`) | ADR-0022, ADR-0023 |
| ADR-0027 | Sync mobile com merge por atividade (atualiza ADR-0004 pós-ADR-0023 — LWW por atividade_id + IDEMP-001 + backlog visível) | ✅ aceito (2026-05-23 — Onda 6 saneamento, destravar Marco 3 OS) | Wave A Marco 3 + app-tecnico | ADR-0004, ADR-0023 |
| ADR-0028 | Mapa de coberturas seguro Wave A (5 modalidades: E&O ampliado + Cyber A3 + D&O + BPT + extensão veicular UMC) — GATE-SEG-BPT-1 IMEDIATO pra Balanças Solution dogfooding | 🟡 proposta — auditoria 10 lentes TEMA-F.5 + TEMA-G (2026-05-23) | Marco 3 dogfooding BPT + 1º tenant externo pago demais modalidades | ADR-0019, ADR-0023 |
| ADR-0029 | Canonicalização de texto probatório (UTF-8 sem BOM + LF + NFC + sem trailing whitespace + marcadores `<<<CORPO INICIO/FIM>>>`) — INV-DOC-CANON-001 | ✅ aceito (2026-05-23) — auditoria 10 lentes Onda 7E pré-Marco 3 OS | Wave A Marco 3 (`os` — AceiteAtividade) + Marco 4 (`calibracao` — RegistroTecnico) + certificados (snapshot probatório) | ADR-0007 |
| ADR-0030 | Vigência temporal canônica (VO `JanelaVigencia` + campos `vigencia_inicio/vigencia_fim/revogado_em/motivo_revogacao` em toda entidade temporal) — auditoria projeto-inteiro 2026-05-23 lente 10 | ✅ aceito (2026-05-23 — Onda 2 saneamento pré-Marco 3 OS) | Wave A Marco 3 + retrofit RT/RTCompetencia/Certificado | ADR-0007 |
| ADR-0031 | Soft-delete em 3 padrões (estado-máquina explícita / `revogado_em` para imutáveis / `deletado_em` para configurações mutáveis) — tabela entidade→padrão + hook validador | ✅ aceito (2026-05-23 — Onda 2 saneamento pré-Marco 3 OS) | Wave A Marco 3 + retrofit | ADR-0007 |
| ADR-0032 | FK cross-módulo + `ReferenciaPIIAnonimizavel(uuid_atual_id NULL, hash_original NOT NULL)` — propagação Zona A/B/C ADR-0021 via evento `Cliente.Anonimizado` | ✅ aceito (2026-05-23 — Onda 2 saneamento pré-Marco 3 OS) | Wave A Marco 3 + retrofit Equipamento/Certificado/OS | ADR-0021, ADR-0030 |
| ADR-0033 | Bus idempotência consumer (tabela `consumer_idempotencia` + `dead_letter_events` + IDEMP-001/002) — Onda 8 auditoria projeto-inteiro 10 lentes (2026-05-23 noite) | ✅ aceito (2026-05-23) — destravou Marco 3 Fase 4 | Wave A Marco 3 — destravado | ADR-0007 |
| ADR-0034 | Saga compensação cross-módulo (Orquestrada vs Coreografia + 4 sagas críticas mapeadas) | 🟡 proposta | Wave A Marco 3+4 | ADR-0033 |
| ADR-0035 | Tenant suspenso modo read-only (matriz módulos param/continuam — LGPD art. 18 preservado) | 🟡 proposta | Wave A (billing-saas suspensão) | ADR-0015 |
| ADR-0036 | Replay determinismo schema evento (`_schema_version: vN` + janela 90d tolerância) | 🟡 proposta | Wave A bus | ADR-0033 |
| ADR-0037 | Glossário PT-EN canônico (PRD em PT-BR; código `src/` em EN; eventos PascalCase PT) | 🟡 proposta | transversal | ADR-0007 |
| ADR-0038 | Família INV-AUTH (lockout + política senha + sessão idle + retenção 365d) | 🟡 proposta | Wave A (F-B retrofit) | ADR-0012 |
| ADR-0039 | Cliente exterior + MEI (TipoPessoa expandido {PF, PJ, MEI, CLIENTE_EXTERIOR} + tax_id_estrangeiro) | 🟡 proposta | Wave A (retrofit Marco 1) | ADR-0017 |
| ADR-0040 | Padrão metrológico como entidade separada (módulo `metrologia/padroes` distinto de `equipamentos`) | ✅ aceito (2026-05-25) — saneamento pré-Marco 4 decisão Roldão | Wave A Marco 4 + dogfooding lab | ADR-0007, ADR-0002, ADR-0022 |
| ADR-0041 | OS concorrência atividades (matriz tipo×tipo + INV-OS-CONC-001) | 🟡 proposta — pré-Marco 3 spec | Wave A Marco 3 | ADR-0023 |
| ADR-0042 | OS cancelamento parcial × faturamento (escopo final pós-cancelamentos + evento `OS.EscopoAlterado`) | 🟡 proposta — pré-Marco 3 spec | Wave A Marco 3 | ADR-0023 |
| ADR-0043 | Calibração faturamento + bloqueio inadimplência (consumer `Certificado.Emitido → CR` + 409 inadimplência dura + override A3) | 🟡 proposta | Wave A Marco 4 | ADR-0015 |
| ADR-0044 | Exportação regulatória ANVISA/SAÚDE/INMETRO (PDF/A-3 + XML embedded XSD setorial + TSA-ITI + B2 WORM 25a) | 🟡 proposta | Wave A Marco 4 + 1º tenant farma | ADR-0047 |
| ADR-0045 | Certificado recall + suspensão + errata (3 cenários pós-emissão + notificação ANPD/CGCRE) | 🟡 proposta | Wave A Marco 4 | ADR-0023 |
| ADR-0046 | OCSP/CRL revogação online (timeout 3s + fallback CRL 1h + bloqueio assinatura com cert revogado) | 🟡 proposta | Wave A (qualquer A3) | ADR-0009 |
| ADR-0047 | Carimbo TSA-ITI PAdES-LTV (PDF longa duração 25a + ICP-Brasil fallback) | 🟡 proposta | Wave A Marco 4 cert | ADR-0009 |
| ADR-0048 | A3 e-CPF RT cadastro (módulo `seguranca/certificados-digitais` — 3 cadastros: e-CNPJ + e-CPF RT + e-CPF demais) | 🟡 proposta | Wave A | ADR-0046 |
| ADR-0049 | Fiscal CT-e + NFC-e + devolução (CT-e non-goal Wave A; NFC-e non-goal; devolução US-FIS-009) | 🟡 proposta | Wave A fiscal | ADR-0008 |
| ADR-0050 | Gateway pagamento (porta `PaymentGatewayProvider` — cartão recorrente, PIX recorrente, boleto; default Asaas) | 🟡 proposta | Wave A financeiro | ADR-0008 |
| ADR-0051 | Propagação ADR-0023 nos módulos Wave A (orçamento item→atividade; agenda evento→atividade; app filhos da atividade; CR faturamento por atividade) | 🟡 proposta | Wave A (5 módulos operacionais) | ADR-0023 |
| ADR-0052 | PIX recorrente BCB 1.071/2024 (enum `MetodoPagamento.tipo` + INV-BIL-PIX-001) | 🟡 proposta | Wave A billing-saas | ADR-0050 |
| ADR-0053 | Export SPED contábil (SPED ECF + EFD Contribuições + layout Sage/Domínio/Alterdata) | 🟡 proposta — PRÉ-REQUISITO Wave A (contador externo) | Wave A | ADR-0008 |
| ADR-0054 | Webhook out provider (19ª porta ACL `OutboundWebhookProvider` + HMAC + retry + dead letter + SSRF guard) | ✅ aceito (2026-05-24 — implementada em F-C1 P4 Bloco 3) | Wave A (dogfooding) | ADR-0007 |
| ADR-0055 | Marketplace sandbox + revenue share (RestrictedPython + 70/30 + curadoria Aferê) | 🟡 proposta — V2/V3 | V2 marketplace | ADR-0013 |
| ADR-0056 | Numeração de OS — sequence global + unique composto, buracos aceitos | ✅ aceito (2026-05-23) — Marco 3 OS P3 retrofit | Wave A Marco 3 | ADR-0002, ADR-0007, ADR-0023 |
| ADR-0057 | Acessibilidade WCAG 2.1 AA — checklist binária por tela + INV-A11Y-001..008 + hook a11y-checklist-spec + axe-core em E2E na F-C2 (renumerada de 0056) | ✅ aceito (2026-05-23) — Onda 2 plano-v2 | Wave A (toda tela nova) — GATE-A11Y-4 bloqueia M3 Fase 5 gerar 1ª tela sem PRD preenchido | ADR-0010 |
| ADR-0058 | Porta `ProductAnalyticsProvider` (19ª porta ACL) — eventos de produto separados de eventos de domínio + matriz LGPD legítimo-interesse×opt-in + INV-PROD-ANALYTICS-001..003 + hook analytics-anti-pii-payload + catálogo-eventos-analytics | ✅ aceito (2026-05-23) — Onda 2 plano-v2 | Wave A — GATE-PRODANALYTICS-4 bloqueia M3 Fase 5 sem PRD analytics preenchido | ADR-0021 |
| ADR-0059 | Porta `LLMProvider` canônica + INV-LLM-001..010 (redaction pré-envio, vector DB tenant namespace, jailbreak/injection tests, orçamento por usuário, audit log prompt/resposta, retenção ≤30d, sanitize resposta) + hook llm-pii-redaction-check | 🔴 reservada Onda 0 plano-v2 | antes 1ª feature LLM-em-produto | ADR-0021 |
| ADR-0060 | Porta `EmailTemplateProvider` + INV-MAIL-001 (dedup hash event_id+template+destinatário 24h justificado) + tabela backoff explícita (5min→30min→4h→24h) + opt-out + bounce | 🔴 reservada Onda 0 plano-v2 | antes Marco 4/5 | ADR-0033 |
| ADR-0061 | Canal do titular + DPO + INV-DPO-001..003 (rota `/privacidade` + prazo 15 dias resposta + registro RIPD + retenção solicitações 365d) — LGPD art. 41 §1º (movida da Onda 5 → Onda 3 por auditoria LGPD) | 🔴 reservada Onda 0 plano-v2 | antes 1º tenant externo (originalmente Onda 5, antecipada) | ADR-0021 |
| ADR-0062 | Devcontainer canônico (sandbox do host) — INV-DEVCONT-001..004 (devcontainer obrigatório em paths críticos / FS isolado fora do projeto / network egress allowlist em F-C2 / sem secret do host) — formaliza D4 (decisão 2026-05-16) que tinha `.devcontainer/devcontainer.json` mas nunca era ADR | ✅ aceito (2026-05-23) — Onda 2 plano-v2 | janela atual (transição) → F-C1 (devcontainer obrigatório em paths críticos) → F-C2 (network allowlist) | ADR-0000 |
| ADR-0063 | RT competência diferida Marco 4 — predicate `rt_competencia_cobre` INVOCADO nos 3 use cases que carregam executor (atribuir_tecnico/iniciar_atividade/transferir_tecnico) com `grandeza=""` fail-open controlado em Marco 3; bloqueio efetivo automático quando Marco 4 calibracao plugar `AtividadeDaOS.grandeza`. ADR modifica AC-OS-002-3, AC-OS-002b-4, AC-OS-003-6, AC-OS-012-2 do PRD | ✅ aceito (2026-05-25) — P5 M3 OS 2ª passada conserto PROD-M3-02 | Marco 4 calibracao (GATE-OS-GRANDEZA-EM-ATIVIDADE) | ADR-0022, ADR-0023 |
| ADR-0064 | Rotação anual de chave HMAC com histórico em KMS Multi-Region — preserva verificabilidade WORM metrológico 25a (NIST SP 800-57 × ISO 17025 cl. 8.4); formato `v<NN>$<base64(hmac)>` + INV-HMAC-001..005 + hook hmac-versao-formato-check + GATE-HMAC-RETROFIT-MARCO-2-3 | ✅ aceito (2026-05-25) — saneamento pré-Marco 4 decisão Roldão (fecha GATE-CAL-HMAC-RETENCAO) | Wave A Marco 4 P3 (helpers crypto) + retrofit Marco 2/3 Wave A operacional | ADR-0002, ADR-0007, ADR-0021, ADR-0029 |

**Como ler a tabela:** "Bloqueia fase" = essa ADR precisa estar aprovada+implementada antes que a fase comece. "Depende de" = essa ADR usa decisões de outras (`soft` = referência conceitual, não bloqueante). Detalhe das fases em `docs/faseamento-foundation-waves.md`.

---

## 12. O que está pendente (gates)

> **Atualizado em 2026-05-25 (pós Marco 3 OS FECHADO):** Foundation F-A+F-B FECHADAS (2026-05-19); Marco 1 `clientes` FECHADO; Marco 2 `equipamentos` FECHADO; F-C1 FECHADO; **Marco 3 `ordens_servico` FECHADO 2026-05-25**. P5 ritual concluído: 1ª passada (5 PASS / 5 FAIL — 40 achados C/A/M) → 5 batches conserto causa-raiz → 2ª passada (3 PASS + 2 FAIL consertados via ADR-0063 + sweep) → 3ª passada (produto+drift = PASS). **10/10 auditores Família 5 PASS ZERO CRÍTICO/ALTO/MÉDIO**.

### Pendências reais

- **Marco 1 `clientes` FECHADO** — 18 T-CLI produtor + drill `validar_m1_clientes` PASS + 4 testes regressão. 10 auditores Família 5 PASS ZERO CRÍTICO/ALTO/MÉDIO. GATE-CLI-1..8 rastreados Wave A. Consolidado em `docs/faseamento/M1-clientes/auditoria-familia5.md`.
- **Marco 2 `equipamentos` FECHADO** — 65 T-EQP em 12 fases + drill `validar_m2_equipamentos` 18/18 PASS. 10/10 PASS ZERO C/A/M. CVE-2025-68616 WeasyPrint mitigado in-app; GATE-EQP-DEP-WEASYPRINT-UPGRADE Wave A. Detalhes em `docs/faseamento/M2-equipamentos/auditoria-familia5.md`.
- **F-C1 FECHADO** — 14 T-FC1 + 9 INVs novas em REGRAS (INV-ADMIN-001..003 + INV-PROD-SET-001 + INV-WEBHOOK-OUT-001..005), ADR-0054 aceito, break-glass U2F enforce, drills reais arquivados. 10/10 PASS ZERO C/A/M.
- **Marco 3 `ordens_servico` — P4 ENTREGUE / P5 EM CONSERTO** — 147 T-OS planejados; Fases 1-10 entregues (18 use cases + 4 query services + 11 endpoints REST + 4 jobs procrastinate + 13 regressões INV-OS = 48 testes; suite M3 chave 89/89 PASS; hooks 312/312). Fases 11-12 (integração US + sagas/carga/drill) = GAP Wave A. P5 1ª passada 2026-05-24 = **5/10 PASS / 5/10 FAIL** (40 achados C/A/M em conserto causa-raiz: drift-docs / idempotência / qualidade / produto / segurança). ADRs aceitas no escopo: 0023, 0027, 0029, 0030, 0031, 0032, 0033, 0041, 0042, 0056. Detalhes em `docs/faseamento/M3-os/auditoria-familia5.md`.
- **Wave A** — pendente autorização Roldão pra arrancar. Pré-requisitos: PRDs em `stable`, ADRs em proposta precisam ser aceitas (0003, 0004, 0008, 0009, 0010, 0014, 0015, 0016, 0018, 0019, 0034, 0035). Marcos 1, 2 e 3 abrem caminho. **Saneamento pré-Marco 4 concluído 2026-05-25** — ADR-0040 (padrão metrológico entidade separada) + ADR-0064 (rotação HMAC + KMS 25a) aceitas; US-CAL-017 (subcontratação cl. 6.6) adicionada ao PRD calibração. Dossiê em `docs/faseamento/auditorias/PRE-M4-CALIBRACAO-saneamento.md`.
- **Wave A do VO `CNPJ`** — ADR-0017 aceita pelo Roldão em 2026-05-18. Implementação do VO + suite Serpro acontece em Wave A sob revisão do `tech-lead-saas-regulado`.

### Foundation F-A + F-B FECHADAS via ritual (2026-05-19)

- **F-A** + **F-B** — ritual Spec Kit completo (spec forward → plan + reviews → matriz reconciliação → conserto causa-raiz → 3 auditores Família 5 = PASS ZERO CRÍTICO/ALTO/MÉDIO). Foundation FECHADA. Detalhes: `docs/faseamento/F-A/auditoria-familia5.md` + `docs/faseamento/F-B/auditoria-familia5.md`.

### Hooks (42 ativos — 312/312 casos verdes; +11 prod-settings-check + admin-hardening-check + outbound-webhook-ssrf-check + 8 FR1..FR8 do frontmatter-revisado-em-check F-C1 P4; +9 qr-hmac-check + 13 equipamento-imutabilidade-check + 9 port-binding-validator + 6 trigger-stub-sweep Marco 2; +7 migration-concorrencia-os-check + 10 sync-merge-foto-appendonly + 4 authz-check predicates M3 do Marco 3 OS Fase 9)

Veja §3 pra lista completa. Marco 5 da F-A (2026-05-17) acrescentou:
- `migration-rls-check.sh` — INV-TENANT-003: bloqueia migration que cria tabela com `tenant_id` sem `CREATE POLICY`/`ENABLE ROW LEVEL SECURITY` na mesma migration (allow via `# rls-policy: external NNNN`).
- `audit-immutability-check.sh` — bloqueia DROP TRIGGER `auditoria_anti_*`, DROP FUNCTION `auditoria_bloqueia_mutation`, ALTER TABLE auditoria DISABLE RLS, TRUNCATE/DELETE/UPDATE em `auditoria`. Allow via `# audit-immutability: skip -- <razão ≥10 chars>`.

Também fix no `authz-check.sh`: allowlist expandida para `*/models.py` e `*/apps.py`; normalização de separadores Windows (backslash→forward).

### Diferido por decisão (não tratar como pendência)

- **Portão 1 da ADR-0001** — cliente externo pago sob NDA. Roldão decidiu em 2026-05-17 (memória `project_sem_cliente_externo_agora`) que não busca cliente externo na janela atual. MVP-1 sai dogfooding-only. R-001 fica mitigado por Discovery 15/15 + mystery shopping documental + estudo Calibre.

### Já feito (removido da lista anterior — estava em drift)

- ~~PRD do produto~~ → `docs/prd.md` (draft, status correto pré-Foundation)
- ~~Faseamento dos módulos~~ → `docs/faseamento-modulos.md` v8 (48 módulos, Foundation + Wave A + Wave B)
- ~~3 prompts auditores Família 5~~ → `docs/governanca/auditor-{seguranca,qualidade,produto}-prompt.md` v1.0.0 (commit 238fa45)
- ~~`isolamento-multi-tenant.md`~~ → criado em 2026-05-17 noite (481 linhas)
- ~~3 hooks complementares~~ → `bus-envelope-validator.sh`, `authz-check.sh`, `provisioning-checkpoint-check.sh` criados em 2026-05-17 noite e registrados em `.claude/settings.json`
- ~~Doc canônico Foundation/Waves~~ → `docs/faseamento-foundation-waves.md` criado em 2026-05-17 noite (372 linhas)
- ~~Síntese-final discovery DRAFT v3 → STABLE~~ → `docs/discovery/sintese-final.md` fechada em STABLE v1.0 em 2026-05-17 madrugada do dia seguinte (Caminho A diferido pra V2 por decisão Roldão)

Ver também: `docs/INDICE.md` (sitemap) + `docs/documentos-do-projeto.md` (mapa de docs).
