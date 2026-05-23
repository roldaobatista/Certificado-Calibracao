# AGENTS.md — canônico de produto/arquitetura

> **Para agentes (Claude Code, Codex CLI, Cursor, Windsurf, Kiro):** este é o documento de referência primária do projeto. O `CLAUDE.md` (irmão) é só adendo de harness do Claude Code e importa este via `@AGENTS.md`.
>
> **Status (2026-05-23 — FOUNDATION F-A+F-B FECHADAS, Marco 1 `clientes` FECHADO, Marco 2 `equipamentos` FECHADO):** Foundation + Marco 1 + Marco 2 entregues via ritual Spec Kit completo (spec FORWARD → plan + reviews → matriz reconciliação → conserto causa-raiz → 10 auditores Família 5). **F-A, F-B, Marco 1 e Marco 2: 10/10 auditores Família 5 = PASS, ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO** (`docs/faseamento/{F-A,F-B,M1-clientes,M2-equipamentos}/auditoria-familia5.md`). **Marco 2 (2ª passada 2026-05-23):** 11 achados pendentes consertados causa-raiz (1 CRÍTICO + 5 ALTO drift-docs em AGENTS/CURRENT/tasks/ADR-0022; 2 MÉDIO LLM `Any`→tipos; 1 MÉDIO supplychain pip-audit + CVE-2025-68616 WeasyPrint mitigado in-app + GATE Wave A; 2 MÉDIO drift OOM/40-linhas). Gate de fechamento de fase = INV-RITUAL-001 (MÉDIO bloqueia igual a CRÍTICO/ALTO; só BAIXO rastreável; hook `ritual-gate-check.sh`).
> - Docs canônicas da Foundation: `docs/faseamento/{F-A,F-B}/{spec,plan,tasks,auditoria-familia5}.md`. `stories-f-a.md`/`stories-f-b.md` → `deprecated` (retrofit retroativo).
> - F-A: 8 GAPs (T-FA-01..08) — 7 causa-raiz + ADR-0020 (REGRAS>orçamento, decisão CODEOWNERS). F-B: 6 GAPs (T-FB-01..06) — predicate binding, vigência fonte-única, MFA django-otp real, ip_hash HMAC, allowlist anti-PII, rollback-órfão.
> - **Suite total (verificado 2026-05-23 pós Marco 2 P4 entrega + 1ª passada P5): 621 passed em 37min (suite completa OK pós ajuste `mem_limit` no docker-compose); 365/365 em `tests/test_equipamentos*.py + tests/regressao/`; hooks `_test-runner.sh` 207/207 verdes em 25 hooks ativos (+qr-hmac-check, equipamento-imutabilidade-check, trigger-stub-sweep, port-binding-validator); makemigrations limpo; ruff zero issues; drills `validar_f_a`/`validar_f_b`/`validar_m1_clientes`/`validar_m2_equipamentos` verdes.**
> - **Gates Wave A rastreados (não bloqueiam Foundation dogfooding; pré-1º tenant externo):** GATE-1..7 (B2/WORM, verificação periódica, NTP, ciclo chave PII, hash AcessoDadosCliente, ADR-0020, higiene `::uuid`) + GATE-FB-1..4 (perfil tenant-specific/INV-AUTHZ-004, retenção authz_decisions+ip_hash, redator escopo PII, texto INV-AUTHZ-002 via ADR) + GATE-CLI-1..8 (retenção stable+B2 WORM, EventoTimeline consumers, p95 visão-360, dashboard regularização, régua D+30/60/89, reativação `ContasReceber.Pago`, consumer agenda, consumer certificados).
> - Marco 1 `clientes` (Wave A): **FECHADO** — ritual Spec Kit completo (spec → plan + 4 reviews → matriz → 18 T-CLI produtor → P5 10 auditores PASS ZERO CRÍTICO/ALTO/MÉDIO). ADR-0021 (anonimização vs retenção). **Marco 2 `equipamentos`: P4 entregue (65 T-EQP em 12 fases + drill PASS), em P5 com 11 achados em conserto causa-raiz** (1 CRÍTICO drift + 5 ALTO drift + 5 MÉDIO LLM/supplychain/drift). ADRs **0018/0019/0020/0021/0022**. Próximo: re-rodar 3 auditores FAIL (drift-docs/LLM/supplychain) → fechamento Marco 2 → US-EQP-003 fase 4 PWA (gate aceite ADR-0018). Estado vivo em `.agent/CURRENT.md`.

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

**Regra mestre:** regra crítica vira **hook**, não só doc. Hoje em `.claude/hooks/` (**32 hooks ativos**, 207/207 casos verdes no `_test-runner` — ampliação Onda 4 saneamento 2026-05-23 a validar): block-destructive, secrets-scanner, INV-checker, tenant-id-validator, anti-mascaramento, context-budget, paths-frontmatter-validator, bus-envelope-validator (estendido Onda 3 — Cliente.Anonimizado + envelope v10), authz-check, provisioning-checkpoint-check, mock-in-production, migration-rls-check, audit-immutability-check, audit-pii-salt-check, pyproject-validator, policy-test-coverage, ritual-gate-check, cliente-canonico-imutavel, event-helper-unico, lgpd-policy-unica, csv-safety-import, qr-hmac-check, equipamento-imutabilidade-check, trigger-stub-sweep, port-binding-validator, **vigencia-canonica-check** (Onda 4 — ADR-0030 INV-VIG-001..004), **soft-delete-padrao-check** (Onda 4 — ADR-0031 INV-SOFT-001..003), **fk-pii-anonimizavel-check** (Onda 4 — ADR-0032 INV-ANON-001..004), **biometria-key-validator** (Onda 4 — INV-OS-ACEITE-BIO-001), **os-conclusao-todas-terminais-check** (Onda 4 — INV-OS-ATIV-001), **frontmatter-revisado-em-check** (Onda 4), **spec-ac-binario-check** (Onda 4). `_test-runner.sh` é o orquestrador.

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
| Testar hooks | `bash .claude/hooks/_test-runner.sh` (207 casos / 25 hooks) |

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
| ADR-0021 | Anonimização vs retenção regulatória (3 zonas A/B/C — LGPD art. 16/18 vs Receita/ISO) | 🟡 proposta — pós review advogado-saas-regulado 2026-05-20 Marco 1 US-CLI-006 | Wave A (matriz `eliminacao_efetiva` vs `anonimizacao_em_lugar` em NF/cert) | ADR-0000, ADR-0007 |
| ADR-0022 | Gestão do RT do tenant (US-EQP-007 / NIT-DICLA-021 — vigência + competências por grandeza + EXCLUDE GIST + imutabilidade pós-INSERT) | ✅ aceito (2026-05-22) — Marco 2 entregue (T-EQP-061..065 + tests/regressao/test_inv_eqp_rt_001.py) | Wave A (GATE-EQP-1 A3 Lacuna + GATE-EQP-RT carta competência + GATE-EQP-RT-NOTIF consumer ANPD/CGCRE) | ADR-0002, ADR-0009, ADR-0012 |
| ADR-0023 | OS com Atividades (1 OS contém N AtividadeDaOS — cada uma com tipo + checklist + estado próprios; suporta caso combinado manutenção + calibração) | ✅ aceito (2026-05-23) — decisão Roldão pré-Marco 3 OS | Wave A Marco 3 (`os`) + Marco 4 (`calibracao`) | ADR-0002, ADR-0007 |
| ADR-0024 | Regra de decisão ISO 17025 cl. 7.8.6 (3 modos + override por cliente + lock pós-emissão) | 🟡 proposta — auditoria 10 lentes TEMA-F.1 (2026-05-23) | Wave A Marco 4 (`calibracao`) | ADR-0023 |
| ADR-0025 | Validação de software ISO 17025 cl. 7.11 (URS/IQ/OQ/PQ + replay determinístico + 2º caminho de cálculo) | 🟡 proposta — auditoria 10 lentes TEMA-F.2 (2026-05-23) | Wave A Marco 4 + V2 RT vendor | ADR-0007 |
| ADR-0026 | 2ª conferência + independência RT (cl. 6.2.5 — política de exceção objetiva 4 condições + 5%/mês) | 🟡 proposta — auditoria 10 lentes TEMA-F.3 (2026-05-23) | Wave A Marco 4 (`calibracao`) | ADR-0022, ADR-0023 |
| ADR-0027 | Sync mobile com merge por atividade (atualiza ADR-0004 pós-ADR-0023 — LWW por atividade_id + IDEMP-001 + backlog visível) | 🟡 proposta — auditoria 10 lentes TEMA-F.4 (2026-05-23) | Wave A Marco 3 + app-tecnico | ADR-0004, ADR-0023 |
| ADR-0028 | Mapa de coberturas seguro Wave A (5 modalidades: E&O ampliado + Cyber A3 + D&O + BPT + extensão veicular UMC) — GATE-SEG-BPT-1 IMEDIATO pra Balanças Solution dogfooding | 🟡 proposta — auditoria 10 lentes TEMA-F.5 + TEMA-G (2026-05-23) | Marco 3 dogfooding BPT + 1º tenant externo pago demais modalidades | ADR-0019, ADR-0023 |
| ADR-0029 | Canonicalização de texto probatório (UTF-8 sem BOM + LF + NFC + sem trailing whitespace + marcadores `<<<CORPO INICIO/FIM>>>`) — INV-DOC-CANON-001 | ✅ aceito (2026-05-23) — auditoria 10 lentes Onda 7E pré-Marco 3 OS | Wave A Marco 3 (`os` — AceiteAtividade) + Marco 4 (`calibracao` — RegistroTecnico) + certificados (snapshot probatório) | ADR-0007 |
| ADR-0030 | Vigência temporal canônica (VO `JanelaVigencia` + campos `vigencia_inicio/vigencia_fim/revogado_em/motivo_revogacao` em toda entidade temporal) — auditoria projeto-inteiro 2026-05-23 lente 10 | 🟡 proposta — pré-Marco 3 (bloqueia drift em OS/Cal/Cert/Procedimento/Padrão/Tarifa) | Wave A Marco 3 + retrofit RT/RTCompetencia/Certificado | ADR-0007 |
| ADR-0031 | Soft-delete em 3 padrões (estado-máquina explícita / `revogado_em` para imutáveis / `deletado_em` para configurações mutáveis) — tabela entidade→padrão + hook validador | 🟡 proposta — pré-Marco 3 (bloqueia 5ª variante em OS) | Wave A Marco 3 + retrofit | ADR-0007 |
| ADR-0032 | FK cross-módulo + `ReferenciaPIIAnonimizavel(uuid_atual_id NULL, hash_original NOT NULL)` — propagação Zona A/B/C ADR-0021 via evento `Cliente.Anonimizado` | 🟡 proposta — pré-Marco 3 (bloqueia PROTECT em cert emitido) | Wave A Marco 3 + retrofit Equipamento/Certificado/OS | ADR-0021, ADR-0030 |
| ADR-0033 | Bus idempotência consumer (tabela `consumer_idempotencia` + `dead_letter_events` + IDEMP-001/002) — Onda 8 auditoria projeto-inteiro 10 lentes (2026-05-23 noite) | 🟡 proposta | Wave A Marco 3 (qualquer consumer) | ADR-0007 |
| ADR-0034 | Saga compensação cross-módulo (Orquestrada vs Coreografia + 4 sagas críticas mapeadas) | 🟡 proposta | Wave A Marco 3+4 | ADR-0033 |
| ADR-0035 | Tenant suspenso modo read-only (matriz módulos param/continuam — LGPD art. 18 preservado) | 🟡 proposta | Wave A (billing-saas suspensão) | ADR-0015 |
| ADR-0036 | Replay determinismo schema evento (`_schema_version: vN` + janela 90d tolerância) | 🟡 proposta | Wave A bus | ADR-0033 |
| ADR-0037 | Glossário PT-EN canônico (PRD em PT-BR; código `src/` em EN; eventos PascalCase PT) | 🟡 proposta | transversal | ADR-0007 |
| ADR-0038 | Família INV-AUTH (lockout + política senha + sessão idle + retenção 365d) | 🟡 proposta | Wave A (F-B retrofit) | ADR-0012 |
| ADR-0039 | Cliente exterior + MEI (TipoPessoa expandido {PF, PJ, MEI, CLIENTE_EXTERIOR} + tax_id_estrangeiro) | 🟡 proposta | Wave A (retrofit Marco 1) | ADR-0017 |
| ADR-0040 | Padrão metrológico como entidade separada (módulo `metrologia/padroes` distinto de `equipamentos`) | 🟡 proposta | Wave A Marco 4 + dogfooding lab | ADR-0007 |
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
| ADR-0054 | Webhook out provider (19ª porta ACL `OutboundWebhookProvider` + HMAC + retry + dead letter + SSRF guard) | 🟡 proposta — PRÉ-REQUISITO Wave A (Roldão pediu) | Wave A | ADR-0007 |
| ADR-0055 | Marketplace sandbox + revenue share (RestrictedPython + 70/30 + curadoria Aferê) | 🟡 proposta — V2/V3 | V2 marketplace | ADR-0013 |

**Como ler a tabela:** "Bloqueia fase" = essa ADR precisa estar aprovada+implementada antes que a fase comece. "Depende de" = essa ADR usa decisões de outras (`soft` = referência conceitual, não bloqueante). Detalhe das fases em `docs/faseamento-foundation-waves.md`.

---

## 12. O que está pendente (gates)

> **Atualizado em 2026-05-23 (pós Onda 7 — auditoria rodada 2 OS+Cal+Cert):** Foundation F-A+F-B FECHADAS (2026-05-19); Marco 1 `clientes` FECHADO (PASS ZERO C/A/M); Marco 2 `equipamentos` FECHADO (2ª passada 2026-05-23 — 10/10 PASS ZERO C/A/M). **Marco 3 OS pre-spec FORWARD:** 2 rodadas de auditoria 10 lentes aplicadas (R1: 179 achados; R2: 80 achados pós-retrofit). 6 ondas R1 + Onda 7 R2 → 28+6 CRÍTICOS = 100% fechados; ~210 outros achados resolvidos ou rastreados como GATE Wave A. Pronto pra arrancar P1 (spec FORWARD do `os`).

### Pendências reais

- **Marco 1 `clientes` FECHADO** — 18 T-CLI produtor + drill `validar_m1_clientes` PASS + 4 testes regressão. 10 auditores Família 5 PASS ZERO CRÍTICO/ALTO/MÉDIO. GATE-CLI-1..8 rastreados Wave A. Consolidado em `docs/faseamento/M1-clientes/auditoria-familia5.md`.
- **Marco 2 `equipamentos` FECHADO** — 65 T-EQP em 12 fases + drill `validar_m2_equipamentos` 18/18 PASS. P5 ritual Spec Kit: 1ª passada 2026-05-22 (7 PASS / 3 FAIL) → conserto causa-raiz dos 11 achados 2026-05-23 → 2ª passada 2026-05-23 = **10/10 PASS ZERO CRÍTICO/ALTO/MÉDIO**. CVE-2025-68616 WeasyPrint mitigado in-app (custom `url_fetcher`); GATE-EQP-DEP-WEASYPRINT-UPGRADE Wave A. Detalhes em `docs/faseamento/M2-equipamentos/auditoria-familia5.md`.
- **Wave A** — pendente autorização Roldão pra arrancar. Pré-requisitos: PRDs em `stable`, ADRs em proposta precisam ser aceitas (0003, 0004, 0008, 0009, 0010, 0014, 0015, 0016, 0018, 0019, 0021). Marco 1 e Marco 2 abrem caminho.
- **Wave A do VO `CNPJ`** — ADR-0017 aceita pelo Roldão em 2026-05-18. Implementação do VO + suite Serpro acontece em Wave A sob revisão do `tech-lead-saas-regulado`.

### Foundation F-A + F-B FECHADAS via ritual (2026-05-19)

- **F-A** + **F-B** — ritual Spec Kit completo (spec forward → plan + reviews → matriz reconciliação → conserto causa-raiz → 3 auditores Família 5 = PASS ZERO CRÍTICO/ALTO/MÉDIO). Foundation FECHADA. Detalhes: `docs/faseamento/F-A/auditoria-familia5.md` + `docs/faseamento/F-B/auditoria-familia5.md`.

### Hooks (25 ativos — 207/207 casos verdes; +9 qr-hmac-check + 13 equipamento-imutabilidade-check + 9 port-binding-validator + 6 trigger-stub-sweep Marco 2)

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
