# AGENTS.md — canônico de produto/arquitetura

> **Para agentes (Claude Code, Codex CLI, Cursor, Windsurf, Kiro):** este é o documento de referência primária do projeto. O `CLAUDE.md` (irmão) é só adendo de harness do Claude Code e importa este via `@AGENTS.md`.
>
> **Status (2026-05-17):** Discovery 15/15 artefatos concluída (síntese em DRAFT v3). Stack cravada como **CANDIDATA** na ADR-0001 (3 portões de validação). Pré-código de produto.

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

**Regra mestre:** regra crítica vira **hook**, não só doc. Hoje em `.claude/hooks/`: `block-destructive.sh`, `secrets-scanner.sh`, `_test-runner.sh`, `INV-checker.sh`, `tenant-id-validator.sh`, `anti-mascaramento.sh`, `context-budget.sh`, `paths-frontmatter-validator.sh`. Faltam: `bus-envelope-validator`, `authz-check.sh`, `provisioning-checkpoint-check` (ver §12).

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

## 6. Comandos (a definir quando Foundation F-A começar)

Pré-código de produto — sem `npm install` ou `manage.py` ainda. Quando F-A começar (Portão 3 da ADR-0001), preencher:

| Operação | Comando |
|---|---|
| Setup dev | _a definir_ |
| Rodar testes | _a definir_ |
| Lint/format | _a definir_ |
| Build | _a definir_ |
| Migration | _a definir_ |
| Servir local | _a definir_ |

Por enquanto, comandos disponíveis:
- `bash .claude/hooks/_test-runner.sh` — testa hooks (23 casos)

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

| # | Tema | Status |
|---|------|--------|
| ADR-0000 | Uso de IA | ✅ aceito |
| ADR-0001 | Stack (Django + Flutter + PG) | 🟡 candidata — 3 portões |
| ADR-0002 | Multi-tenancy (schema-shared + RLS) | 🟡 proposta |
| ADR-0003 | Mobile (técnico de campo) | 🟡 proposta |
| ADR-0004 | Sync mobile offline-first | 🟡 proposta |
| ADR-0005 | Engine de automações | 🟡 proposta |
| ADR-0006 | Feature flags | 🟡 proposta |
| ADR-0007 | Camada domínio + gerador spec→código | 🟡 proposta |
| ADR-0008 | Fiscal pluggable (FiscalProvider) | 🟡 proposta |
| ADR-0009 | Onde A3 assina (cliente-side via Lacuna) | 🟡 proposta |
| ADR-0010 | Estratégia de tela (HTMX núcleo + 4 SPAs isoladas) | 🟡 proposta — pós-auditoria 10 agentes 17/05 |
| ADR-0011 | Banco analítico/BI separado do operacional (3 fases) | 🟡 proposta — pós-auditoria 10 agentes 17/05 |
| ADR-0012 | Autorização unificada (porta AuthorizationProvider) | 🟡 proposta — pós-auditoria 10 agentes 17/05 |
| ADR-0013 | Pricing composicional billing-saas (7 tipos de componente) | 🟡 proposta — requisito Roldão 17/05 |
| ADR-0014 | Transições regulatórias críticas (6 fluxos ISO 17025) | 🟡 proposta — pós-auditoria integrações 17/05 |
| ADR-0015 | Lifecycle tenant (provisioning atômico + sync plano-features + inadimplência) | 🟡 proposta — pós-auditoria integrações 17/05 |
| ADR-0016 | Operação consistente (desligamento síncrono + BOM + NC notifica + 10 médios) | 🟡 proposta — pós-auditoria integrações 17/05 |

---

## 12. O que está pendente (gates)

> **Atualizado em 2026-05-17:** revisado após auditoria de drift que identificou 4 itens declarados pendentes quando já estavam feitos. Lista enxuta abaixo.

### Pendências reais

- **Síntese-final discovery:** sair de DRAFT v3 → STABLE (decisão "sem cliente externo agora" precisa ser cravada explicitamente como input, não pendência aberta)
- **`isolamento-multi-tenant.md`** em `docs/conformidade/comum/` — único doc-base de conformidade MVP-1 que ainda falta (lgpd-rat ✅, seguranca-dados ✅, retencao-matriz ✅, fiscal ✅, dpa-modelo ✅, ripd-modelo ✅, dpia-modulos-novos ✅, incidente-anpd-modelo ✅, pci-dss ✅, open-banking ✅, transferencia-internacional ✅, fiscal-contingencia ✅)
- **Foundation F-A** — código real ainda não começou; Portão 2/3 da ADR-0001 dependem dele
- **3 hooks complementares declarados em INV-INT/INV-AUTHZ ainda a criar:** `bus-envelope-validator` (INV-INT-001/009), `authz-check.sh` (INV-AUTHZ-001), `provisioning-checkpoint-check` (INV-INT-007). Os outros 8 (`block-destructive`, `secrets-scanner`, `_test-runner`, `INV-checker`, `tenant-id-validator`, `anti-mascaramento`, `context-budget`, `paths-frontmatter-validator`) já existem em `.claude/hooks/`.

### Diferido por decisão (não tratar como pendência)

- **Portão 1 da ADR-0001** — cliente externo pago sob NDA. Roldão decidiu em 2026-05-17 (memória `project_sem_cliente_externo_agora`) que não busca cliente externo na janela atual. MVP-1 sai dogfooding-only. R-001 fica mitigado por Discovery 15/15 + mystery shopping documental + estudo Calibre.

### Já feito (removido da lista anterior — estava em drift)

- ~~PRD do produto~~ → `docs/prd.md` (draft, status correto pré-Foundation)
- ~~Faseamento dos módulos~~ → `docs/faseamento-modulos.md` v8 (48 módulos, Foundation + Wave A + Wave B)
- ~~3 prompts auditores Família 5~~ → `docs/governanca/auditor-{seguranca,qualidade,produto}-prompt.md` v1.0.0 (commit 238fa45)

Ver também: `docs/INDICE.md` (sitemap) + `docs/documentos-do-projeto.md` (mapa de docs).
