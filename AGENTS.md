# AGENTS.md — canônico de produto/arquitetura

> **Para agentes (Claude Code, Codex CLI, Cursor, Windsurf, Kiro):** este é o documento de referência primária do projeto. O `CLAUDE.md` (irmão) é só adendo de harness do Claude Code e importa este via `@AGENTS.md`.
>
> **Status (2026-05-17):** **Foundation F-A INICIADA** — autorização do Roldão recebida; ADR-0002 e ADR-0007 promovidas a "aceito" como parte do gate. Discovery 15/15 concluída (síntese STABLE v1.0). Stack candidata cravada na ADR-0001 (3 portões; Portão 1 diferido pra V2). Saindo de "pré-código" — esqueleto Django + PostgreSQL local em construção. Janela esperada da F-A: 4–6 semanas. Acompanhamento em `.agent/CURRENT.md`.

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
3. **Conciso vence completo** — AGENTS.md e CLAUDE.md ≤ 250 e ≤ 150 linhas respectivamente.
4. **Non-goals explícitos** — toda spec/ADR declara o que NÃO está no escopo.
5. **IDs rastreáveis** — `US-<MOD>-NNN` → `AC-<MOD>-NNN-N` → `T<MOD>NNN` → commit.
6. **Negócio vence conveniência do agente** — não otimizar pelo que o agente IA erra menos; otimizar pelo Roldão/produto. Critério "agentes dominam X" é tiebreaker, nunca principal.

**Regra mestre:** regra crítica vira **hook**, não só doc. Hoje em `.claude/hooks/` (15 hooks ativos, 103/103 testes verdes): `block-destructive`, `secrets-scanner`, `_test-runner`, `INV-checker`, `tenant-id-validator`, `anti-mascaramento`, `context-budget`, `paths-frontmatter-validator`, `bus-envelope-validator`, `authz-check`, `provisioning-checkpoint-check`, `mock-in-production`, `migration-rls-check`, `audit-immutability-check`, `pyproject-validator` (drill F-A 2026-05-18 — valida PEP 440 + sintaxe extras Poetry), `policy-test-coverage` (drill F-A 2026-05-18 — exige `# tests-coverage:` apontando teste happy+unhappy quando migration cria policy RLS).

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
- `advogado-saas-regulado` — LGPD, contratos, compliance regulatório
- `corretora-seguros-saas` — risco, seguro cyber + RC profissional
- `consultor-rbc-iso17025` — calibração, NIT-DICLA, RBC

**3 auditores Família 5 (Segurança, Qualidade, Produto)** — operam pré-commit/pré-merge via prompts versionados (`docs/governanca/auditor-*-prompt.md` — pendente). Catálogo em `docs/governanca/catalogo-auditores.md`.

**Humano licenciado contratado SOB DEMANDA** para casos que exigem assinatura legal (apólice SUSEP, parecer OAB, dossiê CGCRE).

Inventário de subagentes técnicos genéricos (code-reviewer, test-runner, etc.) **NÃO existe por escolha** — o trabalho deles está distribuído entre os 4 substitutos + 3 auditores.

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
| Aplicar migrations | `docker compose exec app poetry run python manage.py migrate` |
| Shell Django | `docker compose exec app poetry run python manage.py shell_plus` |
| Testar hooks | `bash .claude/hooks/_test-runner.sh` (71 casos) |

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
| ADR-0006 | Feature flags | 🟡 proposta | Foundation F-B | ADR-0002, ADR-0012 |
| ADR-0007 | Camada domínio + gerador spec→código | ✅ aceito (2026-05-17) | Foundation F-A — destravado (codegen completo é Wave A) | ADR-0001 |
| ADR-0008 | Fiscal pluggable (FiscalProvider) | 🟡 proposta | Wave A (fiscal/NFS-e) | — |
| ADR-0009 | Onde A3 assina (cliente-side via Lacuna) | 🟡 proposta | Wave A (certificados) | — |
| ADR-0010 | Estratégia de tela (HTMX núcleo + 4 SPAs isoladas) | 🟡 proposta — pós-auditoria 10 agentes 17/05 | Wave A (UI) | ADR-0001, ADR-0007 |
| ADR-0011 | Banco analítico/BI separado do operacional (3 fases) | 🟡 proposta — pós-auditoria 10 agentes 17/05 | Wave B (bi) | ADR-0002 |
| ADR-0012 | Autorização unificada (porta AuthorizationProvider) | 🟡 proposta — pós-auditoria 10 agentes 17/05 | Foundation F-B | ADR-0002, ADR-0006 |
| ADR-0013 | Pricing composicional billing-saas (7 tipos de componente) | 🟡 proposta — requisito Roldão 17/05 | Wave B (billing-saas full) | ADR-0005 (soft), ADR-0015 |
| ADR-0014 | Transições regulatórias críticas (6 fluxos ISO 17025) | 🟡 proposta — pós-auditoria integrações 17/05 | Wave A (regulatório) | ADR-0002, ADR-0012 |
| ADR-0015 | Lifecycle tenant (provisioning atômico + sync plano-features + inadimplência) | 🟡 proposta — pós-auditoria integrações 17/05 | Wave A (onboarding+suspensão) | ADR-0002, ADR-0006, ADR-0012 |
| ADR-0016 | Operação consistente (desligamento síncrono + BOM + NC notifica + 10 médios) | 🟡 proposta — pós-auditoria integrações 17/05 | Wave A (operação) | ADR-0002, ADR-0012, ADR-0014 |
| ADR-0017 | CNPJ alfanumérico (IN RFB 2.229/2024 — vigência jul/2026) | ✅ aceito (2026-05-18) | Wave A (todo módulo que persista CNPJ) | ADR-0007, ADR-0002 |

**Como ler a tabela:** "Bloqueia fase" = essa ADR precisa estar aprovada+implementada antes que a fase comece. "Depende de" = essa ADR usa decisões de outras (`soft` = referência conceitual, não bloqueante). Detalhe das fases em `docs/faseamento-foundation-waves.md`.

---

## 12. O que está pendente (gates)

> **Atualizado em 2026-05-17:** revisado após auditoria de drift que identificou 4 itens declarados pendentes quando já estavam feitos. Lista enxuta abaixo.

### Pendências reais

- **Drill Foundation F-A** — **5/5 critérios automáveis VERDE em 2026-05-18** (execução autônoma no Docker). 8 marcos entregues + 2 migrations de refinamento descobertas pelo próprio drill (fail-loud RLS via `require_tenant_ctx()`; policies de `feature_flags` e `usuario_perfil_tenant` cirurgicamente liberadas pra INSERT system + tenant). Suite final: 58 passed, 1 skipped (justificado Wave A). Falta apenas critérios 6+7 (drill restore PG manual + métricas operacionais 4-6 semanas). Detalhes em `docs/faseamento/drill-f-a-saida.md`.
- **Wave A do VO `CNPJ`** — ADR-0017 aceita pelo Roldão em 2026-05-18 (gap detectado e corrigido no mesmo dia: 9 docs canônicas alinhadas + IN RFB 2.229/2024 acrescentada às normas). Implementação do VO + suite de testes oficial Serpro acontece em Wave A, sob revisão do subagente `tech-lead-saas-regulado`.

### Hooks (13 ativos — 88/88 testes verdes)

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
