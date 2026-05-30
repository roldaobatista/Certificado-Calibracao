# AGENTS.md — canônico de produto/arquitetura

> **Para agentes (Claude Code, Codex CLI, Cursor, Windsurf, Kiro):** este é o documento de referência primária do projeto. O `CLAUDE.md` (irmão) é só adendo de harness do Claude Code e importa este via `@AGENTS.md`.
>
> **Status (2026-05-27 noite — F-A+F-B+M1+M2+F-C1+M3-OS+M4 + SAN-PERFIL-TENANT 1-4 TODAS FECHADAS + auditoria 10 lentes pré-Wave A em execução):** 7 Foundations/Marcos com 10/10 auditores Família 5 PASS ZERO CRÍTICO/ALTO/MÉDIO. **Marco 4 `metrologia/calibracao` FECHADO 2026-05-27** após 1ª passada (41 C/A/M) → 6 batches S1..S6.1 conserto causa-raiz → 2ª passada (8 PASS + 2 CONCERNS BAIXO carryover) → 4ª passada drift-docs PASS limpo. **SAN-PERFIL-TENANT Sprints 1-4 FECHADOS 2026-05-27 noite** (schema perfil A/B/C/D + predicate `tenant_perfil_e` + provisionar_tenant + snapshot `perfil_no_evento` WORM). **Auditoria 10 lentes pré-Wave A 2026-05-27 madrugada**: ~150 achados (37 CRÍTICOS, ~50 ALTOS, ~60 MÉDIOS) — plano de 5 ondas em `docs/faseamento/auditorias/PRE-WAVE-A-CONSOLIDADO-rodada-1.md`. ADRs aceitas M4: **0040, 0064, 0065, 0066**. ADR aceita SAN: **0067**.
> - Docs canônicas: `docs/faseamento/{F-A,F-B,M1-clientes,M2-equipamentos,F-C1,M3-os,M4-calibracao,SAN-PERFIL-TENANT}/{spec,plan,auditoria-familia5|tasks}.md`.
> - F-A: 8 GAPs (T-FA-01..08) — 7 causa-raiz + ADR-0020. F-B: 6 GAPs (T-FB-01..06). F-C1: 14 T-FC1. M3 OS: 147 T-OS (Fases 1-10 entregues; 11-12 GAP Wave A). M4: 160 T-CAL (~156 entregues; 4 TRACK Wave A — MC numpy, perf, backup B2+KMS, 10 ViewSets restantes). SAN-PERFIL-TENANT: 4 sprints fechados (Sprints 5-6 = Wave A).
> - **Suite total (verificado 2026-05-27): pytest M4 chave 629/629 verde em ~27s + pytest geral 905/0/0 em 26min (último full run 2026-05-24); hooks `_test-runner.sh` 450/450 verdes em 55 hooks ativos (+6 M4 P9 + +3 SAN-PERFIL Sprints 1-3 + +4 M5 P7 padroes: padrao-incertezas-so-via-recal, padrao-auxiliar-em-controle, shewhart-perfil-A, analise-carta-worm); makemigrations limpo; ruff zero issues; drills `validar_{f_a,f_b,m1_clientes,m2_equipamentos,f_c1,m4_calibracao,m5_padroes(43/43),san_perfil_tenant_migrations(17/17),san_perfil_tenant_snapshots(6/6)}` estruturalmente verdes (`validar_m3_os` em GATE-OS-VALIDAR-DRILL Wave A; drill M4 estrutural 53+ checks, conexão PG real em GATE-CAL-DRILL-LOCAL Wave A).**
> - **Gates Wave A rastreados (não bloqueiam Foundation dogfooding; pré-1º tenant externo):** GATE-1..7 (B2/WORM, verificação periódica, NTP, ciclo chave PII, hash AcessoDadosCliente, ADR-0020, higiene `::uuid`) + GATE-FB-1..4 + GATE-CLI-1..8 + **GATE-FC1-ROTACAO-DRILL-REAL** + **GATE-CYBER-BREAKGLASS-U2F-ENFORCE** + **GATE-OS-PERF-1..5** + **GATE-OS-BUS-BRIDGE-1** + **GATE-OBS-LOG-EXTRA-1** + **GATE-OBS-METRIC-OS-1** + **GATE-IDEMP-HOOK-DETECT-ACTION** + **GATE-OS-SYNC-WAVE-A** + **GATE-OS-SUCESSAO-EVIDENCIA** + **GATE-OS-ANON-RETRY-1** + **GATE-OS-VALIDAR-DRILL** + **GATE-OS-CONSBIO-TEXTO-OAB** + **GATE-OS-DPIA-OAB** + **GATE-TENANT-PERFIL-{SCHEMA,PROVISIONING,TEMPLATES-CERT,MATRIZ-RETENCAO,AUTHZ-PREDICATE,TESTES-MATRIZ,OBSERVABILIDADE}** (Wave A).
> - **Marcos FECHADOS:** M1 (2026-05-21) + M2 (2026-05-23) + F-C1 (2026-05-24) + M3 OS (2026-05-25) + M4 calibração (2026-05-27) + **M5 `metrologia/padroes` (2026-05-29 — 1º módulo Wave A; ritual P1→P10, re-passada+confirmação 8 auditores PASS ZERO C/A/M, INV-RITUAL-001 satisfeito; p5+p10 23/23 estável em 3 rodadas; ADRs 0070/0071/0072)**. ADRs M3: 0023/0027/0029/0030/0031/0032/0033/0041/0042/0056/0063. ADRs M4: 0040/0064/0065/0066. SAN-PERFIL: 0067. Auditoria 10 lentes pré-Wave A 2026-05-27: 24 ADRs promovidas/emendadas + 2 ADRs novas (0068 sucessão RT, 0069 bypass cl. 6.2) + 3 reservadas (0059/0060/0061). **Wave A: M5 `metrologia/padroes` acrescentou ADR-0070/0071/0072 (revisão RBC+tech-lead do plan).** Estado vivo em `.agent/CURRENT.md`. Detalhes em `docs/faseamento/M{3-os,4-calibracao}/auditoria-familia5.md` e `docs/faseamento/auditorias/PRE-WAVE-A-CONSOLIDADO-rodada-1.md`.

---

## 1. Identidade do produto

- **Nome:** "Aferê" — **PROVISÓRIO**. Não comprar domínio, não escrever código com slug `afere`, não registrar INPI sem decisão final.
- **Escopo:** ERP completo para empresas de assistência técnica + calibração metrológica (laboratório ISO 17025).
- **Modelo:** SaaS multi-tenant.
- **N módulos:** mínimo 6 confirmados (CRM, Financeiro de alto nível, Orçamentos, Chamados, Ordens de Serviço, Calibração), total real = saída do discovery (pode ser 11, 21 ou 50).
- **Cliente piloto:** Balanças Solution (empresa do Roldão — dogfooding). Não substitui cliente externo pago sob NDA, que ainda é Portão 1 aberto.
- **Diferencial central:** Calibração ISO 17025 — disputa com Calibre.Software (mystery shopping documental concluído).
- **Camada de IA (add-on) — codinome "Aferê Prumo":** produto de IA (cérebro + agentes por setor; atende WhatsApp por áudio, orça, abre OS, confere certificado, avisa prazos — com aprovação humana) **já descoberto e arquitetado por completo** (3 ADRs aceitos + auditoria cega de 10 arquitetos Opus + mapa de encaixe) no projeto irmão `C:/projetos/balancas-solution-ia/`. É um **domínio DENTRO do Aferê** (`src/domain/copiloto` + portas novas `llm`/`omnichannel`/`docsearch`/`bpm`/`stt`), reusando as portas existentes — **não reconstrói nada**. Entra em **Wave B/C** (decisão Roldão 2026-05-30: ritmo normal, **não antecipar**; precisa do MVP-1 rodando com dados reais). **NÃO construir agora.** Ao chegar em Wave B/C, ler **`docs/afere-prumo/LEIA-PRIMEIRO.md`** (documentação COMPLETA — descoberta + ADRs + encaixe, **versionada neste próprio repo** desde 2026-05-30) + `docs/evolucao/afere-prumo-trilha-ia.md` (resumo no roadmap). Matéria-prima pesada (cérebro 1.099 fontes, 24 GB) fica fora do repo — ver `docs/afere-prumo/LEIA-PRIMEIRO.md`.

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

**Regra mestre:** regra crítica vira **hook**, não só doc. Hoje em `.claude/hooks/` (**55 hooks ativos**, 450/450 casos verdes no `_test-runner` — ampliação Marco 4 calibração Fase 9 2026-05-26 + SAN-PERFIL-TENANT Sprints 1-3 2026-05-27 + M5 padroes P7 2026-05-29): block-destructive, secrets-scanner, INV-checker, tenant-id-validator, anti-mascaramento, context-budget, paths-frontmatter-validator, bus-envelope-validator, authz-check (estendido com 6 predicates M3), provisioning-checkpoint-check, mock-in-production, migration-rls-check, audit-immutability-check, audit-pii-salt-check, pyproject-validator, policy-test-coverage, ritual-gate-check, cliente-canonico-imutavel, event-helper-unico, lgpd-policy-unica, csv-safety-import, qr-hmac-check, equipamento-imutabilidade-check, trigger-stub-sweep, port-binding-validator, vigencia-canonica-check, soft-delete-padrao-check, fk-pii-anonimizavel-check, biometria-key-validator, os-conclusao-todas-terminais-check, frontmatter-revisado-em-check, spec-ac-binario-check, prod-settings-check, admin-hardening-check, outbound-webhook-ssrf-check, idempotency-key-header-check, mass-assignment-check, seed-anti-pii-real, prd-ux-states-check, arquivo-tamanho-aviso, **migration-concorrencia-os-check** (M3 P9 — INV-OS-CONC-001), **sync-merge-foto-appendonly** (M3 P9 — INV-OS-SYNC-001), **hmac-versao-formato-check** (M4 P9 — INV-HMAC-001 + ADR-0064), **incerteza-versao-motor-check** (M4 P9 — INV-CAL-VERSAO-001), **cmc-binding-check** (M4 P9 — INV-CAL-CMC-001), **migration-concorrencia-calibracao-check** (M4 P9 — INV-CAL-CONC-001..004), **migration-metrology-classifier** (M4 P9 — ADR-0025 cl. 7.11.3), **metrology-replay-fixtures-versionadas** (M4 P9 — §3.3 spec), **tenant-perfil-imutavel-check** (SAN-PERFIL Sprint 1 — INV-TENANT-PERFIL-001/002), **payload-tipo-acreditacao-obsoleto-check** (SAN-PERFIL Sprint 2 — INV-TENANT-PERFIL-005), **feature-perfil-matriz-validator** (SAN-PERFIL Sprint 3 — INV-TENANT-PERFIL-006), **padrao-incertezas-so-via-recal** (M5 P7 — INV-PAD-006 + C-10 GUC), **padrao-auxiliar-em-controle** (M5 P7 — INV-PAD-007 cl. 6.4.5), **shewhart-perfil-A** (M5 P7 — INV-PAD-008 + ADR-0067/0070), **analise-carta-worm** (M5 P7 — INV-PAD-010 + ADR-0070). `_test-runner.sh` é o orquestrador.

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

## 6. Comandos (Foundations F-A/F-B/F-C1 + Marcos 1-4 + SAN-PERFIL fechados 2026-05-27)

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
| Testar hooks | `bash .claude/hooks/_test-runner.sh` (450 casos / 55 hooks ativos — +4 M5 P7: padrao-incertezas-so-via-recal, padrao-auxiliar-em-controle, shewhart-perfil-A, analise-carta-worm) |

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

- **Multi-tenancy:** PostgreSQL RLS + middleware Django injeta `tenant_id` em todas as queries. Roles `NOBYPASSRLS`. Hook `tenant-id-validator` ATIVO em `.claude/hooks/tenant-id-validator.sh` (criado em F-A).
- **A3 assina sempre client-side** via Web PKI Lacuna (defesa anti-replay: nonce + signing-time server-controlled + one-shot).
- **KMS:** AWS Multi-Region Key — `sa-east-1` primária, `us-east-1` réplica.
- **WORM:** trilha imutável de eventos em Backbloze B2; documentos fiscais corrigíveis em estado mutável.
- **Crypto-shredding por tenant** pra LGPD direito ao esquecimento.
- **Retenção:** matriz Receita 5 anos × ISO 17025 8.4 (~25 anos) × LGPD em `docs/conformidade/comum/retencao-matriz.md` (existe, `status: draft` desde M3 Onda 2; linha de padrões/executor adicionada em M5 P8 T-PAD-071).

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
| ADR-0003 | Mobile Flutter offline-first (técnico de campo) — decisões cravadas (Flutter + sync ADR-0027 + A3 Lacuna FFI + EXIF segregado) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A (app-tecnico) | ADR-0001, ADR-0027, ADR-0067 |
| ADR-0004 | Sync mobile offline-first — refinada por ADR-0027 (LWW por atividade_id + IDEMP-001) | ✅ aceito (2026-05-27 — Onda PRE-A.2; refined-by 0027) | Wave A (app-tecnico) | ADR-0003, ADR-0027 |
| ADR-0005 | Engine de automações | 🟡 proposta | Wave B (automacoes-bpm) | ADR-0006 |
| ADR-0006 | Feature flags | ✅ aceito (2026-05-18) | Foundation F-B — destravado | ADR-0002, ADR-0012 |
| ADR-0007 | Camada domínio + gerador spec→código | ✅ aceito (2026-05-17) | Foundation F-A — destravado (codegen completo é Wave A) | ADR-0001 |
| ADR-0008 | Fiscal pluggable (FiscalProvider) + emenda matriz perfil×NFS-e | ✅ aceito (2026-05-27 — Onda PRE-A.2; deadline 01/09/2026) | Wave A (fiscal/NFS-e) | ADR-0001, ADR-0067 |
| ADR-0009 | Onde A3 assina (cliente-side via Lacuna) + emenda perfil A obrigatório | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A (certificados) | ADR-0067 |
| ADR-0010 | Estratégia de tela (HTMX núcleo + 5 SPAs isoladas) | ✅ aceito (2026-05-27 — decisão Roldão via AskUserQuestion) | Wave A (UI) | ADR-0001, ADR-0007 |
| ADR-0011 | Banco analítico/BI separado do operacional (3 fases) | 🟡 proposta — pós-auditoria 10 agentes 17/05 | Wave B (bi) | ADR-0002 |
| ADR-0012 | Autorização unificada (porta AuthorizationProvider) | ✅ aceito (2026-05-18) | Foundation F-B — destravado | ADR-0002, ADR-0006 |
| ADR-0013 | Pricing composicional billing-saas + emenda componente `perfil_regulatorio` obrigatório (2026-05-27 Onda PRE-A.2) | 🟡 proposta + emenda — promoção formal DIFERIDA Wave B (billing-saas full); modelo de dados já cravado | Wave B (billing-saas full) | ADR-0005 (soft), ADR-0015, ADR-0067 |
| ADR-0014 | Transições regulatórias críticas (6 fluxos ISO 17025) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A (regulatório) | ADR-0002, ADR-0012 |
| ADR-0015 | Lifecycle tenant (provisioning atômico + etapa 0 perfil + sync plano-features + inadimplência) | ✅ aceito (2026-05-27 — Onda PRE-A.2; já emendada Sprint 3 SAN-PERFIL com etapa 0 COLETA_PERFIL_REGULATORIO) | Wave A (onboarding+suspensão) | ADR-0002, ADR-0006, ADR-0012, ADR-0067 |
| ADR-0016 | Operação consistente (desligamento síncrono + BOM + NC notifica + 10 médios) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A (operação) | ADR-0002, ADR-0012, ADR-0014 |
| ADR-0017 | CNPJ alfanumérico (IN RFB 2.229/2024 — vigência jul/2026) | ✅ aceito (2026-05-18) | Wave A (todo módulo que persista CNPJ) | ADR-0007, ADR-0002 |
| ADR-0018 | Scanner QR em PWA + BarcodeDetector até Flutter chegar | 🟡 proposta — pós-auditoria PRD `equipamentos` Wave A Marco 2 (2026-05-18) | Wave A Marco 2 (US-EQP-003) | ADR-0001, ADR-0010 |
| ADR-0019 | Responsabilidade civil + segurabilidade de código gerado por agentes IA | ✅ aceito 2026-05-27 + `superseded-by: 0028` | Cláusula afirmativa IA no DPA-cap-responsabilidade (preparação defensiva — contratação apólice DIFERIDA pra produção real) | ADR-0000, ADR-0028 |
| ADR-0020 | REGRAS-INEGOCIÁVEIS &gt; orçamento; decisão CODEOWNERS expandida (D5) | ✅ aceito (2026-05-19) | Foundation F-A — fechada | — |
| ADR-0021 | Anonimização vs retenção regulatória (3 zonas A/B/C — LGPD art. 16/18 vs Receita/ISO) | ✅ aceito (2026-05-20) — Onda 7B retrofit M3 (NOVO-ALTO-6) | Wave A (matriz `eliminacao_efetiva` vs `anonimizacao_em_lugar` em NF/cert) | ADR-0000, ADR-0007 |
| ADR-0022 | Gestão do RT do tenant (NIT-DICLA-021) — **v2 (2026-05-27): competência por método específico + faixa**, não só grandeza | ✅ aceito v1 (2026-05-22 Marco 2) + ✅ v2 emenda (2026-05-27 — Onda PRE-A.2, fecha L3#4) | Wave A (GATE-EQP-RT + retrofit RTCompetencia + T-RT-V2-001..006) | ADR-0002, ADR-0009, ADR-0012, ADR-0068 |
| ADR-0023 | OS com Atividades (1 OS contém N AtividadeDaOS — cada uma com tipo + checklist + estado próprios; suporta caso combinado manutenção + calibração) | ✅ aceito (2026-05-23) — decisão Roldão pré-Marco 3 OS | Wave A Marco 3 (`os`) + Marco 4 (`calibracao`) | ADR-0002, ADR-0007 |
| ADR-0024 | Regra de decisão ISO 17025 cl. 7.8.6 (3 modos + override por cliente + lock pós-emissão) | ✅ aceito (2026-05-23) — Onda 6 saneamento destravar Marco 4 | Wave A Marco 4 (`calibracao`) | ADR-0023 |
| ADR-0025 | Validação de software ISO 17025 cl. 7.11 — **v2 (2026-05-27): estendida aos 4 módulos metrologia Wave A** (certificados, procedimentos, padroes, licencas-acreditacoes) | ✅ aceito v1 (2026-05-23 Marco 4) + ✅ v2 (2026-05-27 — Onda PRE-A.2, fecha L3#3) | Wave A 4 módulos metrologia + V2 RT vendor (T-VAL-SW-001..016) | ADR-0007, ADR-0067 |
| ADR-0026 | 2ª conferência + independência RT (cl. 6.2.5 — política de exceção objetiva 4 condições + 5%/mês) | ✅ aceito (2026-05-23) — Onda 6 saneamento destravar Marco 4 | Wave A Marco 4 (`calibracao`) | ADR-0022, ADR-0023 |
| ADR-0027 | Sync mobile com merge por atividade (atualiza ADR-0004 pós-ADR-0023 — LWW por atividade_id + IDEMP-001 + backlog visível) | ✅ aceito (2026-05-23 — Onda 6 saneamento, destravar Marco 3 OS) | Wave A Marco 3 + app-tecnico | ADR-0004, ADR-0023 |
| ADR-0028 | Mapa de coberturas seguro Wave A (5 modalidades: E&O ampliado + Cyber A3 + D&O + BPT + extensão veicular UMC) — GATE-SEG-BPT-1 IMEDIATO pra Balanças Solution dogfooding | 🟡 proposta — auditoria 10 lentes TEMA-F.5 + TEMA-G (2026-05-23) | Marco 3 dogfooding BPT + 1º tenant externo pago demais modalidades | ADR-0019, ADR-0023 |
| ADR-0029 | Canonicalização de texto probatório (UTF-8 sem BOM + LF + NFC + sem trailing whitespace + marcadores `<<<CORPO INICIO/FIM>>>`) — INV-DOC-CANON-001 | ✅ aceito (2026-05-23) — auditoria 10 lentes Onda 7E pré-Marco 3 OS | Wave A Marco 3 (`os` — AceiteAtividade) + Marco 4 (`calibracao` — RegistroTecnico) + certificados (snapshot probatório) | ADR-0007 |
| ADR-0030 | Vigência temporal canônica (VO `JanelaVigencia` + campos `vigencia_inicio/vigencia_fim/revogado_em/motivo_revogacao` em toda entidade temporal) — auditoria projeto-inteiro 2026-05-23 lente 10 | ✅ aceito (2026-05-23 — Onda 2 saneamento pré-Marco 3 OS) | Wave A Marco 3 + retrofit RT/RTCompetencia/Certificado | ADR-0007 |
| ADR-0031 | Soft-delete em 3 padrões (estado-máquina explícita / `revogado_em` para imutáveis / `deletado_em` para configurações mutáveis) — tabela entidade→padrão + hook validador | ✅ aceito (2026-05-23 — Onda 2 saneamento pré-Marco 3 OS) | Wave A Marco 3 + retrofit | ADR-0007 |
| ADR-0032 | FK cross-módulo + `ReferenciaPIIAnonimizavel(uuid_atual_id NULL, hash_original NOT NULL)` — propagação Zona A/B/C ADR-0021 via evento `Cliente.Anonimizado` | ✅ aceito (2026-05-23 — Onda 2 saneamento pré-Marco 3 OS) | Wave A Marco 3 + retrofit Equipamento/Certificado/OS | ADR-0021, ADR-0030 |
| ADR-0033 | Bus idempotência consumer (tabela `consumer_idempotencia` + `dead_letter_events` + IDEMP-001/002) — Onda 8 auditoria projeto-inteiro 10 lentes (2026-05-23 noite) | ✅ aceito (2026-05-23) — destravou Marco 3 Fase 4 | Wave A Marco 3 — destravado | ADR-0007 |
| ADR-0034 | Saga compensação cross-módulo (Orquestrada vs Coreografia + 4 sagas críticas mapeadas) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A Marco 3+4 | ADR-0033 |
| ADR-0035 | Tenant suspenso modo read-only + matriz perfil-aware ADR-0067 (A 30d max; D 180d) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A (billing-saas suspensão) | ADR-0015, ADR-0067 |
| ADR-0036 | Replay determinismo schema evento (`_schema_version: vN` + janela 90d tolerância) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A bus | ADR-0033 |
| ADR-0037 | Glossário PT-EN canônico | ✅ aceito (2026-05-27 — Onda PRE-A.2) | transversal | ADR-0007 |
| ADR-0038 | Família INV-AUTH (lockout + política senha + sessão idle + retenção 365d) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A (F-B retrofit) | ADR-0012 |
| ADR-0039 | Cliente exterior + MEI (TipoPessoa expandido) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A (retrofit Marco 1) | ADR-0017 |
| ADR-0040 | Padrão metrológico como entidade separada (módulo `metrologia/padroes` distinto de `equipamentos`) | ✅ aceito (2026-05-25) — saneamento pré-Marco 4 decisão Roldão | Wave A Marco 4 + dogfooding lab | ADR-0007, ADR-0002, ADR-0022 |
| ADR-0041 | OS concorrência atividades (matriz tipo×tipo + INV-OS-CONC-001) | 🟡 proposta — pré-Marco 3 spec | Wave A Marco 3 | ADR-0023 |
| ADR-0042 | OS cancelamento parcial × faturamento (escopo final pós-cancelamentos + evento `OS.EscopoAlterado`) | 🟡 proposta — pré-Marco 3 spec | Wave A Marco 3 | ADR-0023 |
| ADR-0043 | Calibração faturamento + bloqueio inadimplência + emenda grace perfil-aware (A D+45 / D D+7) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A `certificados` + financeiro | ADR-0015, ADR-0067 |
| ADR-0044 | Exportação regulatória ANVISA/SAÚDE/INMETRO + emenda predicate `tenant_perfil_e({A})` obrigatório | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A `certificados` + 1º tenant farma | ADR-0047, ADR-0067 |
| ADR-0045 | Certificado recall + suspensão + errata + emenda perfil-aware (A recall + CGCRE; D errata simples) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A `certificados` | ADR-0023, ADR-0067 |
| ADR-0046 | OCSP/CRL revogação online (timeout 3s + fallback CRL 1h) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A (qualquer A3) | ADR-0009 |
| ADR-0047 | Carimbo TSA-ITI PAdES-LTV 25a + ICP-Brasil fallback | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A `certificados` | ADR-0009 |
| ADR-0048 | A3 e-CPF RT cadastro (3 cadastros: e-CNPJ + e-CPF RT + e-CPF demais) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A | ADR-0046 |
| ADR-0049 | Fiscal CT-e + NFC-e + devolução (CT-e/NFC-e non-goal Wave A; devolução US-FIS-009) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A fiscal | ADR-0008 |
| ADR-0050 | Gateway pagamento (porta `PaymentGatewayProvider` — cartão + PIX recorrente + boleto; default Asaas) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A financeiro | ADR-0008 |
| ADR-0051 | Propagação ADR-0023 nos módulos Wave A (orçamento/agenda/app/CR por atividade) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A (5 módulos operacionais) | ADR-0023 |
| ADR-0052 | PIX recorrente BCB 1.071/2024 | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A billing-saas | ADR-0050 |
| ADR-0053 | Export SPED contábil (ECF + EFD Contribuições + layout Sage/Domínio/Alterdata) | ✅ aceito (2026-05-27 — Onda PRE-A.2) | Wave A | ADR-0008 |
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
| ADR-0065 | Concorrência calibração — UNIQUE composto `(tenant_id, calibracao_id, ponto_calibracao, numero_repeticao)` em `leitura` + CAS optimistic lock em `Calibracao.revision` + advisory lock `pg_advisory_xact_lock` em hash-chain `evento_de_calibracao` por `(tenant_id, calibracao_id)` + INV-CAL-CONC-001..004 | ✅ aceito (2026-05-25) — P3 M4 decisão Roldão pré-Fase 1 migrations | Wave A Marco 4 P4 Fase 1 (migrations) + retrofit caller mobile sync (ADR-0027 LWW por atividade_id) | ADR-0007, ADR-0027 |
| ADR-0066 | Predicates `cmc_cobre` + `procedimento_vigente_para` declarados em P4 Fase 2 com fail-open lazy controlado (paralelo a ADR-0063 do M3 OS) — 6 ACs do PRD calibração modificados; bloqueio real entra em vigor em Wave A com criação dos módulos `metrologia/escopos-cmc` + `metrologia/procedimentos-calibracao` (`GATE-CAL-CMC-PREDICATE` + `GATE-CAL-PROC-VIGENTE-PREDICATE`) | ✅ aceito (2026-05-27) — Batch S5 conserto 1ª passada P5 M4 (PROD-CAL-01/02) | Wave A (dois módulos novos) | ADR-0063 (paralelo), ADR-0030 |
| ADR-0067 | Perfil regulatório do tenant como entidade temporal de 1ª classe (4 perfis A/B/C/D) — schema `Tenant.perfil_regulatorio` + `TenantPerfilHistorico` + predicate `tenant_perfil_e` fail-closed + snapshot `perfil_no_evento` em WORM + matriz feature×perfil + retrofit Foundation/M1-M4 + 7 GATEs Wave A (`GATE-TENANT-PERFIL-*`) — fecha 10/10 achados da auditoria 2026-05-27 (FAIL fraude documental L6, FAIL LGPD over-retention L8, CONCERN CGCRE L3, FAIL trilha D→A nunca codada L4) | ✅ aceito (2026-05-27) — auditoria 10 lentes pedido Roldão "ver se o sistema grava tipo de empresa"; Roldão decidiu manter 4 perfis + consertar antes de Wave A | Wave A (1º tenant externo pago) — bloqueante | ADR-0002, ADR-0007, ADR-0030, ADR-0031 |
| ADR-0068 | Sucessão/substituição temporária do RT (NIT-DICLA-016) — modelo `RTSubstituicao` + 4 condições + competência herdada subset + dupla A3 + notificação CGCRE perfil A > 30d + matriz perfil-aware | ✅ aceito (2026-05-27) — auditoria 10 lentes pré-Wave A Onda PRE-A.2, fecha L1#7 + L3#15 | Wave A (`agenda`, `app-tecnico`, `certificados` — T-RT-SUB-001..010) | ADR-0022, ADR-0030, ADR-0067 |
| ADR-0069 | Bypass competência ISO 17025 cl. 6.2 — 4 condições objetivas obrigatórias + cota mensal por perfil (A 5% / B 10% / C 5% / D 20%) + A3 gestor + lock pós-aceite + notificação CGCRE bypass perfil A > 2 meses (análogo ADR-0026) | ✅ aceito (2026-05-27) — auditoria 10 lentes pré-Wave A Onda PRE-A.2, fecha L1#5 + L3-cl.6.2 | Wave A `rh-frota-qualidade/treinamentos` US-TRE-007 (T-COMP-BYPASS-001..008) | ADR-0026, ADR-0067 |
| ADR-0070 | Carta controle Shewhart híbrida — read-model p/ gráfico + registro WORM congelado `AnaliseCartaControle` da decisão (LC/UCL/LCL/σ + versao_motor + decisao_rt + justificativa hash); INV-PAD-010 | ✅ aceito (2026-05-28) — revisão RBC plan M5 padroes (NC-1 ALTO) | Wave A M5 `metrologia/padroes` US-PAD-008 | ADR-0025, ADR-0029, ADR-0064, ADR-0067 |
| ADR-0071 | "2º caminho de cálculo" (cl. 7.11) = 2 implementações independentes do MESMO mensurando (anti-bug software), NÃO 2 estimadores; deriva→tendência Shewhart; k via Welch-Satterthwaite quando ν_eff<30; INV-PAD-009 redefinida | ✅ aceito (2026-05-28) — revisão RBC plan M5 (NC-2/NC-3 ALTO/MÉDIO); refines ADR-0025 v2 | Wave A M5 `metrologia/padroes` US-PAD-009 | ADR-0025, ADR-0070 |
| ADR-0072 | Path infra metrologia aninhado `src/infrastructure/metrologia/<modulo>/` (espelha domínio); M4 calibracao achatado fica dívida conhecida (não renomear) | ✅ aceito (2026-05-28) — revisão tech-lead plan M5 (P3) | Wave A M5+ (`padroes`, `escopos-cmc`, `procedimentos`) | ADR-0040 |
| ADR-0073 | Validação de cobertura metrológica (`cmc_cobre`/`procedimento_vigente_para`) no use case, não no permission layer DRF (regra de negócio metrológico exige estado persistido pós-permissão) | ✅ aceito (2026-05-29) — revisão tech-lead plan M6 escopos-cmc (TL-C-01) | Wave A M6 `escopos-cmc` + `procedimentos` | ADR-0007, ADR-0012, ADR-0066 |
| ADR-0074 | Cobertura RBC tridimensional: faixa ⊆ escopo (config) + `U ≥ CMC` (emissão, 2ª porta `cmc_para`, ILAC-P14 §5.5) + menor-CMC-por-faixa (NIT-DICLA-012); INV-ECMC-009 | ✅ aceito (2026-05-29) — revisão RBC plan M6 (NC-01/NC-03) | Wave A M6 `escopos-cmc` US-CAL-015 + emissão | ADR-0073, ADR-0066, ADR-0025 |
| ADR-0075 | Capacidade interna declarada (B/C/D) ≠ CMC acreditada (A) — separação terminológica obrigatória (cl. 8.1.3 uso indevido de acreditação); dado compartilhado, rótulo+badge distintos | ✅ aceito (2026-05-29) — revisão RBC plan M6 (NC-02) + decisão Roldão O | Wave A M6 `escopos-cmc` | ADR-0067, ADR-0040, ADR-0017 |

**ADRs reservadas (esqueletos 2026-05-27 — ativação diferida):** ADR-0059 LLMProvider (antes 1ª feature LLM Wave B); ADR-0060 EmailTemplate (antes `comunicacao-omnichannel` Wave A); ADR-0061 Canal titular + DPO (antes 1º dogfooding real — interim manual aceito hoje).

**Como ler a tabela:** "Bloqueia fase" = essa ADR precisa estar aprovada+implementada antes que a fase comece. "Depende de" = essa ADR usa decisões de outras (`soft` = referência conceitual, não bloqueante). Detalhe das fases em `docs/faseamento-foundation-waves.md`.

---

## 12. O que está pendente (gates)

> **Atualizado em 2026-05-27 (Marco 4 FECHADO):** Foundation F-A+F-B FECHADAS (2026-05-19); Marco 1 `clientes` FECHADO; Marco 2 `equipamentos` FECHADO; F-C1 FECHADO; **Marco 3 `ordens_servico` FECHADO 2026-05-25**; **Marco 4 `metrologia/calibracao` FECHADO 2026-05-27**. 1ª passada (2 CRÍTICO + 13 ALTO + 26 MÉDIO) → 6 batches conserto causa-raiz (S1 drift-docs / S2 segurança+LGPD / S3 idempotência / S4 observabilidade / S5 produto+qualidade / S6 drift S4-S5 / S6.1 drift residual interno) zeraram **2/2 CRÍTICO + 13/13 ALTO + 21/26 MÉDIO**; 5 MÉDIO remanescentes são TRACK Wave A (PG real). 2ª passada Família 5: **8 PASS** + 2 CONCERNS BAIXO carryover (seguranca GATE-KMS; drift-docs CONCERNS→PASS pós-S6.1). LLM-correctness subiu CONCERNS→PASS. INV-RITUAL-001 satisfeito. Detalhes em `docs/faseamento/M4-calibracao/auditoria-familia5.md` §6.

### Pendências reais

- **Marco 1 `clientes` FECHADO** — 18 T-CLI produtor + drill `validar_m1_clientes` PASS + 4 testes regressão. 10 auditores Família 5 PASS ZERO CRÍTICO/ALTO/MÉDIO. GATE-CLI-1..8 rastreados Wave A. Consolidado em `docs/faseamento/M1-clientes/auditoria-familia5.md`.
- **Marco 2 `equipamentos` FECHADO** — 65 T-EQP em 12 fases + drill `validar_m2_equipamentos` 18/18 PASS. 10/10 PASS ZERO C/A/M. CVE-2025-68616 WeasyPrint mitigado in-app; GATE-EQP-DEP-WEASYPRINT-UPGRADE Wave A. Detalhes em `docs/faseamento/M2-equipamentos/auditoria-familia5.md`.
- **F-C1 FECHADO** — 14 T-FC1 + 9 INVs novas em REGRAS (INV-ADMIN-001..003 + INV-PROD-SET-001 + INV-WEBHOOK-OUT-001..005), ADR-0054 aceito, break-glass U2F enforce, drills reais arquivados. 10/10 PASS ZERO C/A/M.
- **Marco 3 `ordens_servico` FECHADO 2026-05-25** — 147 T-OS; Fases 1-10 entregues (18 use cases + 4 query services + 11 endpoints REST + 4 jobs procrastinate + 13 regressões INV-OS). Fases 11-12 (integração US + sagas/carga/drill) = GAP Wave A. P5 ritual: 1ª passada (5 PASS / 5 FAIL — 40 C/A/M) → 5 batches causa-raiz → 2ª passada (consertos + ADR-0063) → 3ª passada (PASS). 10/10 PASS ZERO C/A/M. ADRs aceitas: 0023, 0027, 0029, 0030, 0031, 0032, 0033, 0041, 0042, 0056, 0063. Detalhes em `docs/faseamento/M3-os/auditoria-familia5.md` §"Veredito FINAL".
- **Marco 4 `metrologia/calibracao` FECHADO 2026-05-27** — 160 T-CAL planejados; ~156 entregues nas partes factíveis sem PG real; 4 grupos TRACK Wave A (T-CAL-055..058 Monte Carlo numpy DEP-001 / T-CAL-113 perf assertNumQueries / T-CAL-114 backup B2+KMS / T-CAL-124..133 10 ViewSets restantes / T-CAL-143..144 hooks foto-exif+override / T-CAL-148..160 regressões PG-real). Suite M4 chave 629/629 PASS; hooks 413/413 / 51 ativos. P5 1ª passada 2026-05-27 = **2 PASS / 1 CONCERNS / 7 FAIL** (2 CRÍTICO + 13 ALTO + 26 MÉDIO) → 6 batches conserto causa-raiz (S1 drift-docs / S2 segurança+LGPD / S3 idempotência / S4 observabilidade / S5 produto+qualidade / S6 drift S4-S5) zeraram 2/2 CRÍTICO + 13/13 ALTO + 21/26 MÉDIO; 5 MÉDIO restantes são TRACK Wave A (PG real). 2ª passada 2026-05-27 retornou 8 PASS + 1 CONCERNS (seguranca BAIXO carryover GATE-KMS) + 1 CONCERNS pré-S6 (drift-docs). ADRs aceitas: **0040, 0064, 0065, 0066** (todas em §11). Detalhes em `docs/faseamento/M4-calibracao/auditoria-familia5.md`.
- **Wave A** — pendente autorização Roldão pra arrancar. Pré-requisitos: PRDs em `stable`, ADRs em proposta precisam ser aceitas (0003, 0004, 0008, 0009, 0010, 0014, 0015, 0016, 0018, 0019, 0034, 0035). Marcos 1, 2 e 3 abrem caminho. **Saneamento pré-Marco 4 concluído 2026-05-25** — ADR-0040 (padrão metrológico entidade separada) + ADR-0064 (rotação HMAC + KMS 25a) aceitas; US-CAL-017 (subcontratação cl. 6.6) adicionada ao PRD calibração. Dossiê em `docs/faseamento/auditorias/PRE-M4-CALIBRACAO-saneamento.md`.
- **🟡 SAN-PERFIL-TENANT — Saneamento pré-Wave A — perfil regulatório do tenant (ADR-0067 ✅ aceita 2026-05-27 — Sprints 1+2+3+4 FECHADOS)** — Auditoria 10 lentes 2026-05-27 detectou gap estrutural (10/10 FAIL): PRD declara 4 perfis A/B/C/D mas `Tenant` não persistia perfil; predicate `cmc_cobre` lia tipo_acreditacao do payload da request (FAIL L6 fraude documental viável). Roldão decidiu manter 4 perfis + consertar antes de Wave A. **Sprint 1 entregue:** schema multi-step (migrations 0003-0010) + funções SECURITY DEFINER `aplicar_evento_cgcre()` e `rebaixar_perfil_tenant_voluntario_cliente()` + tabela `tenant_perfil_historico` append-only + 2 triggers anti-mutação + drill 17/17 PASS + hook `tenant-perfil-imutavel-check`. **Sprint 2 entregue:** ContextVar `perfil_tenant_context` + middleware popula + helper canônico `tenant_perfil_e(perfis_aceitos)` fail-closed timeout 50ms + retrofit `cmc_cobre` lê tenant (fecha FAIL L6) + hook `payload-tipo-acreditacao-obsoleto-check` + 23 testes regressão + TenantFactory traits + fixtures + marker `@pytest.mark.perfil`. **Sprint 3 entregue:** comando `provisionar_tenant` + job mensal `verificar_vigencia_acreditacao_perfil_a` + matriz canônica `docs/conformidade/comum/matriz-feature-perfil.md` + hook `feature-perfil-matriz-validator` + emenda ADR-0015 etapa 0 + runbook DPO + retrofit `popular_drill`. **Sprint 4 entregue (2026-05-27 noite):** GUC `app.perfil_tenant` em `setar_contexto_pg_na_conexao` + middleware passa perfil_atual + 3 migrations adicionando `perfil_no_evento CHAR(1) NULL` em audit/evento_de_calibracao/evento_de_os + 3 triggers BEFORE INSERT lendo `current_setting('app.perfil_tenant')` quando NULL + coluna `escopos_acreditados_vigentes_no_momento JSONB` em evento_de_calibracao (R7 plan.md) + retrofit `registrar_auditoria()` passa perfil via ContextVar + retrofit `criar_equipamento` deriva perfil do Tenant pra snapshot + retrofit `geo_truncamento_calibracao_5a` perfil A nunca trunca (R10 plan.md / AC-005-6) + drill `validar_san_perfil_tenant_snapshots` 6/6 PASS + comando `validar_san_perfil_tenant_eventos_historicos` gera CSV evidência defensiva A4. **Validação PG real:** migrate aplicado 6 migrations OK + drill snapshots 6/6 + relatório evidência 1 evento exportado + suite ampla regression+audit+M3+M4 voltou exit 0. **Pendente:** Sprints 5-6 Wave A (templates certificado + onboarding UX + direitos-titular + export trimestral seguradora + sinistro export). Tasks rastreadas em `docs/faseamento/SAN-PERFIL-TENANT/tasks.md`.
- **Wave A do VO `CNPJ`** — ADR-0017 aceita pelo Roldão em 2026-05-18. Implementação do VO + suite Serpro acontece em Wave A sob revisão do `tech-lead-saas-regulado`.

### Foundation F-A + F-B FECHADAS via ritual (2026-05-19)

- **F-A** + **F-B** — ritual Spec Kit completo (spec forward → plan + reviews → matriz reconciliação → conserto causa-raiz → 3 auditores Família 5 = PASS ZERO CRÍTICO/ALTO/MÉDIO). Foundation FECHADA. Detalhes: `docs/faseamento/F-A/auditoria-familia5.md` + `docs/faseamento/F-B/auditoria-familia5.md`.

### Hooks (55 ativos — 450/450 casos verdes; +4 M5 P7 padroes (INV-PAD-006/007/008/010): padrao-incertezas-so-via-recal + padrao-auxiliar-em-controle + shewhart-perfil-A + analise-carta-worm; +11 prod-settings-check + admin-hardening-check + outbound-webhook-ssrf-check + 8 FR1..FR8 do frontmatter-revisado-em-check F-C1 P4; +9 qr-hmac-check + 13 equipamento-imutabilidade-check + 9 port-binding-validator + 6 trigger-stub-sweep Marco 2; +7 migration-concorrencia-os-check + 10 sync-merge-foto-appendonly + 4 authz-check predicates M3 do Marco 3 OS Fase 9; +6 do Marco 4 P9: hmac-versao-formato-check, incerteza-versao-motor-check, cmc-binding-check, migration-concorrencia-calibracao-check, migration-metrology-classifier, metrology-replay-fixtures-versionadas; +3 do SAN-PERFIL-TENANT Sprints 1-3 2026-05-27: tenant-perfil-imutavel-check, payload-tipo-acreditacao-obsoleto-check, feature-perfil-matriz-validator)

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
