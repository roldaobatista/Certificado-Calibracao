# AGENTS.md — canônico de produto/arquitetura

> **Para agentes (Claude Code, Codex CLI, Cursor, Windsurf, Kiro):** referência primária do projeto. `CLAUDE.md` é adendo de harness e importa este via `@AGENTS.md`.
>
> **Fase atual:** Wave A em curso. Frente ativa e próximos passos: `.agent/CURRENT.md`. Contagens (hooks/casos/ADRs/INVs): `docs/governanca/STATUS-GERADO.md`. ADRs detalhadas: `docs/adr/INDICE.md`. Histórico: `docs/faseamento/diario/`.

---

## 1. Identidade do produto

- **Nome:** "Aferê" — **PROVISÓRIO**. Não comprar domínio, não escrever código com slug `afere`, não registrar INPI sem decisão final.
- **Escopo:** ERP completo para empresas de assistência técnica + calibração metrológica (laboratório ISO 17025).
- **Modelo:** SaaS multi-tenant.
- **N módulos:** mínimo 6 confirmados (CRM, Financeiro, Orçamentos, Chamados, OS, Calibração), total real = saída do discovery.
- **Cliente piloto:** Balanças Solution (empresa do Roldão — dogfooding). Não substitui cliente externo pago.
- **Diferencial central:** Calibração ISO 17025 — disputa com Calibre.Software.
- **Camada IA "Aferê Prumo":** Wave B/C. Documentação completa em `docs/afere-prumo/LEIA-PRIMEIRO.md`. **NÃO construir agora.**

**Founder is customer:** Roldão é o primeiro cliente. Mitigação obrigatória do risco "customização disfarçada" = Família 0 Discovery rigorosa (15 artefatos).

---

## 2. Stack candidata (ADR-0001 — 3 portões)

| Camada | Escolha | Notas |
|---|---|---|
| Backend | **Django + DRF** | Admin built-in como ferramenta operacional |
| Banco | **PostgreSQL** | Multi-tenancy via schema-shared + RLS + middleware `tenant_id` (ADR-0002) |
| Filas | **procrastinate** | Python sobre PostgreSQL (NÃO `pg-boss`) |
| Frontend web | **HTMX** sobre Django templates | Reduz dependência de JS |
| Mobile | **Flutter** | Offline-first; assinatura A3 via Web PKI Lacuna (ADR-0009) |
| KMS | **AWS KMS Multi-Region Key** | sa-east-1 ↔ us-east-1 |
| Storage | **Backblaze B2** (WORM) | Trilha imutável + crypto-shredding por tenant |
| Hospedagem | **Hostinger VPS KVM 4** (SP/BR) | Provedor B (Magalu/Oracle/AWS) pra DR |
| Observabilidade | Grafana Cloud + Axiom | |

Stack **CANDIDATA** — definitiva após Portões 2+3 da ADR-0001. Ver `docs/arquitetura/anti-corrosion-layer.md` (18 portas).

---

## 3. Princípios não-negociáveis

Ver `.specify/memory/constitution.md` (6 princípios) + `REGRAS-INEGOCIAVEIS.md` (IDs `INV-*`, `TST-*`, `SEC-*`).

**Resumo operacional:**
1. **Documento é estado compartilhado** — agente que decidir sem doc inventa diferente toda vez.
2. **Spec gera código** (spec-as-source). Não código gera spec.
3. **Conciso vence completo** — AGENTS.md ≤ 200 linhas; CLAUDE.md ≤ 60 linhas.
4. **Non-goals explícitos** — toda spec/ADR declara o que NÃO está no escopo.
5. **IDs rastreáveis** — `US-<MOD>-NNN` → `AC-<MOD>-NNN-N` → `T<MOD>NNN` → commit.
6. **Negócio vence conveniência do agente** — otimizar pelo Roldão/produto, não pelo que o agente IA erra menos.

**Regra mestre:** regra crítica vira **hook**, não só doc. Hooks em `.claude/hooks/` — lista completa via `ls .claude/hooks/`; contagens em `docs/governanca/STATUS-GERADO.md`. Orquestrador: `.claude/hooks/_test-runner.sh`.

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

**Auditores Família 5** — operam pré-commit/pré-merge via prompts em `docs/governanca/auditor-*-prompt.md`. Catálogo em `docs/governanca/catalogo-auditores.md`.

| # | Auditor | Bloqueia | Nota de roteamento |
|---|---|---|---|
| 1 | `auditor-seguranca` | commit | sempre |
| 2 | `auditor-qualidade` | commit | sempre |
| 3 | `auditor-produto` | merge | sempre |
| 4 | `auditor-drift-docs` | — | varredura mensal (aposentado como LLM — 0 bugs em 32 achados) |
| 5 | `auditor-llm-correctness` | commit | sempre |
| 6 | `auditor-performance` | commit | sempre |
| 7 | `auditor-observabilidade` | commit | sempre |
| 8 | `auditor-idempotencia` | commit | sempre |
| 9 | `auditor-supplychain` | commit | só quando diff toca pyproject/lock/Dockerfile |
| 10 | `auditor-conformidade-lgpd` | commit | só quando diff toca campo PII |

Severidade: MÉDIO+ bloqueia fechamento (INV-RITUAL-001 — decisão Roldão). 2ª passada: só auditores que tiveram MÉDIO+, restritos ao diff do conserto (R5). Verificação adversarial de TODO achado MÉDIO+ antes do mutirão (R6).

**Humano licenciado SOB DEMANDA** para casos que exigem assinatura (apólice SUSEP, parecer OAB, dossiê CGCRE). Zero contratações até produção real (decisão Roldão 2026-05-27).

---

## 6. Comandos

Stack ativa: Python 3.12 + Django 5.0 + DRF + PostgreSQL 16 + Poetry. Docker Compose local.

| Operação | Comando |
|---|---|
| Setup local | `docs/operacao/setup-local.md` |
| Subir sistema | `docker compose up` |
| Derrubar | `docker compose down` / `docker compose down -v` (apaga banco) |
| Rebuild Python | `docker compose up --build` |
| Rodar testes | `docker compose exec app poetry run pytest` |
| Cobertura HTML | `reports/coverage/index.html` |
| Lint + format | `poetry run ruff check . && poetry run ruff format .` |
| Type-check | `poetry run mypy src config` |
| Migration nova | `docker compose exec app poetry run python manage.py makemigrations` |
| Aplicar migrations | `docker compose exec app poetry run python manage.py migrate --database=migrator` |
| Objetos de segurança | `docker compose exec app poetry run python manage.py verificar_objetos_seguranca` |
| Shell Django | `docker compose exec app poetry run python manage.py shell_plus` |
| Testar hooks | `bash .claude/hooks/_test-runner.sh` |
| Contagens do projeto | `bash scripts/status-projeto.sh` |
| Verificar denylist | `bash scripts/status-projeto.sh --check` |

---

## 7. Política de commits

- **Atômicos:** um propósito por commit. Não misturar fix + feature + refactor.
- **Mensagem:** uma linha curta + descrição se necessário. Padrão livre.
- **Stage seletivo:** `git add <arquivo>` por arquivo. Nunca `git add .` com outras frentes sujas.
- **Co-Authored-By Claude:** incluir nas mensagens.
- **Proibido commit isolado de `.agent/CURRENT.md`** — o handoff entra no commit da própria fatia (R16).
- **Nunca usar:** `--no-verify`, `--skip-*`, `--ignore-*`, `git reset --hard`, `git push --force`, `git branch -D`, `rm -rf`, `drop table` — sem confirmação explícita do Roldão.

---

## 8. Convenções

- **Idioma:** Português (Brasil) em tudo — código, comentários, docs, commits.
- **Linguagem do canal:** sem jargão técnico com o Roldão. Ver `CLAUDE.md` global para tabela de tradução.
- **Pastas chave:**
  - `docs/discovery/` — Família 0 (15 artefatos)
  - `docs/adr/` — ADRs (ver `docs/adr/INDICE.md` pra navegação)
  - `docs/dominios/<dominio>/modulos/<modulo>/` — estrutura híbrida
  - `docs/governanca/` — Família 5 (auditores, RACI, limites)
  - `docs/conformidade/` — LGPD, fiscal, ISO 17025
  - `docs/faseamento/diario/` — histórico de módulos fechados
- **Frontmatter obrigatório** em todo doc novo: `owner`, `revisado-em`, `status: draft|stable|deprecated`. Ver `docs/CONVENCOES-DOC.md`.

---

## 9. Segurança / dados

- **Multi-tenancy:** PostgreSQL RLS + middleware Django + roles `NOBYPASSRLS`.
- **A3 assina sempre client-side** via Web PKI Lacuna (nonce + signing-time server-controlled + one-shot).
- **KMS:** AWS Multi-Region Key — `sa-east-1` primária, `us-east-1` réplica.
- **WORM:** trilha imutável de eventos em Backblaze B2.
- **Crypto-shredding por tenant** pra LGPD direito ao esquecimento.
- **Retenção:** matriz em `docs/conformidade/comum/retencao-matriz.md`.

---

## 10. Pontos de extensão

- **MCP servers (`.mcp.json`):** github plugado; filesystem/playwright/postgres sob demanda
- **Hooks (`.claude/hooks/`):** ciclo de vida Claude Code; lista via `ls .claude/hooks/`; cuidados Windows + Git Bash em `CLAUDE.md`
- **Subagentes (`.claude/agents/`):** descrição com gatilho concreto; ferramentas restritas
- **Skills (`.claude/skills/`):** criar quando padrão repetir 3x
- **Rules (`.claude/rules/`):** sempre com `paths:` frontmatter (lazy load)

---

## 11. ADRs vivas (slim)

> Índice completo (vivas + frias + reservadas): `docs/adr/INDICE.md`.

| Nº | Título curto | Módulo / área |
|---|---|---|
| 0002 | Multi-tenancy RLS v2 | infra / todo módulo |
| 0006 | Feature flags por tenant | infra / F-B |
| 0007 | Camada domínio + spec-as-source | arquitetura |
| 0008 | Fiscal pluggable FiscalProvider | fiscal / NFS-e |
| 0012 | Autorização unificada AuthorizationProvider | authz |
| 0014 | Transições regulatórias ISO 17025 | regulatório |
| 0015 | Lifecycle tenant provisioning + perfil | tenant / onboarding |
| 0017 | CNPJ alfanumérico IN RFB 2.229/2024 | todo módulo com CNPJ |
| 0021 | Anonimização vs retenção (zonas A/B/C) | LGPD / PII |
| 0022 | Gestão RT v2 competência método+faixa | RT / calibração |
| 0023 | OS com Atividades (1 OS → N Atividades) | ordens_servico |
| 0024 | Regra de decisão ISO 17025 cl. 7.8.6 | calibração |
| 0025 | Validação software cl. 7.11 v2 | metrologia |
| 0026 | 2ª conferência independência RT cl. 6.2.5 | calibração |
| 0029 | Canonicalização texto probatório | toda entidade WORM |
| 0030 | Vigência temporal canônica JanelaVigencia | toda entidade temporal |
| 0031 | Soft-delete 3 padrões | toda entidade |
| 0032 | FK cross-módulo + ReferenciaPIIAnonimizavel | LGPD / cross-módulo |
| 0033 | Bus idempotência consumer | filas / procrastinate |
| 0036 | Replay determinismo schema evento | bus |
| 0040 | Padrão metrológico entidade separada | metrologia/padroes |
| 0043 | Calibração faturamento + inadimplência | billing / certificados |
| 0044 | Exportação regulatória ANVISA + perfil A | certificados |
| 0045 | Certificado recall + errata perfil-aware | certificados |
| 0054 | Webhook out HMAC + SSRF guard | webhooks / F-C1 |
| 0056 | Numeração OS sequence + buracos aceitos | ordens_servico |
| 0064 | Rotação HMAC anual KMS 25a | criptografia / WORM |
| 0065 | Concorrência calibração UNIQUE+CAS+advisory | calibração |
| 0067 | Perfil regulatório tenant 4 perfis A/B/C/D | tenant / todo módulo |
| 0070 | Carta Shewhart híbrida WORM congelado | metrologia/padroes |
| 0071 | 2ª implementação cl. 7.11 mesmo mensurando | metrologia/padroes |
| 0072 | Path infra metrologia aninhado | infra metrologia |
| 0073 | Validação metrológica no use case (não DRF) | metrologia / use cases |
| 0074 | Cobertura RBC tridimensional | escopos-cmc |
| 0075 | Capacidade interna B/C/D ≠ CMC acreditada A | escopos-cmc |
| 0076 | Faixa DECLARADA config vs pontos emissão | escopos-cmc / certificados |
| 0077 | Orçamento incerteza POR PONTO retrofit M4 | calibração / certificados |
| 0078 | Tabela certificados achatada + lógica aninhada | certificados |
| 0079 | Licenca fonte rica + cache Tenant unidirecional | licencas / tenant |
| 0080 | Numeração SerieDocumento 2 regimes | configuracoes-sistema |
| 0081 | Duas fontes de preço lista×venda fail-closed | produtos-pecas-servicos |
| 0082 | OS multi-equipamento (equipamento por atividade) | ordens_servico |

---

## 12. Gates e pendências

Ver `.agent/CURRENT.md` (frente ativa + próximos passos) e `docs/governanca/STATUS-GERADO.md` (contagens). Gates rastreados ficam nos docs de cada frente (`docs/faseamento/<modulo>/`). Histórico de módulos fechados em `docs/faseamento/diario/`.
