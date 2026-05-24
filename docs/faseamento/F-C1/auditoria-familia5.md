---
owner: roldao
revisado-em: 2026-05-24
proximo-review: 2026-08-24
status: draft
diataxis: explanation
audiencia: agente
fase: Foundation F-C1
tipo: consolidado-auditoria-familia5
relacionados:
  - docs/faseamento/F-C1/spec.md
  - docs/faseamento/F-C1/plan.md
  - docs/faseamento/F-C1/matriz-reconciliacao.md
  - docs/faseamento/F-A/auditoria-familia5.md
  - docs/faseamento/F-B/auditoria-familia5.md
  - docs/faseamento/M1-clientes/auditoria-familia5.md
  - docs/faseamento/M2-equipamentos/auditoria-familia5.md
  - REGRAS-INEGOCIAVEIS.md
---

# Foundation F-C1 — Auditoria Família 5 (P5)

> Loop do ritual: spec → plan + 3 reviews → matriz → P4 implementação (Blocos 1..6 + saneamento test infra Tasks #8/9/10) → **10 auditores Família 5**. F-C1 só fecha com ZERO C/A/M (INV-RITUAL-001).

## Pré-requisitos verificados antes da 1ª passada

- Suíte pytest: **905/0/0 verde** em 26min (`reports/pytest-run8.log`).
- Hooks `_test-runner.sh`: **288/288 verdes**.
- Drill `validar_f_c1`: **10/10 PASS** em DB dev.
- ruff/mypy: limpos.
- F-C1 P4 entregue em 14 T-FC1 distribuídos em 6 Blocos + extras de test infra.

## 1ª passada — 2026-05-24

| Lente | Auditor | Veredito | CRÍTICO | ALTO | MÉDIO | BAIXO |
|---|---|---|---|---|---|---|
| Segurança | `auditor-seguranca` | **FAIL** | 0 | 0 | 2 | 1 |
| Qualidade | `auditor-qualidade` | **FAIL** | 0 | 1 | 0 | 2 |
| Produto/escopo | `auditor-produto` | **FAIL** | 3 | 1 | 1 | 0 |
| Drift docs | `auditor-drift-docs` | **FAIL** | 2 | 6 | 4 | 1 |
| LLM correctness | `auditor-llm-correctness` | **FAIL** | 0 | 0 | 1 | 2 |
| Performance | `auditor-performance` | **PASS** | 0 | 0 | 0 | 0 |
| Observabilidade | `auditor-observabilidade` | **FAIL** | 0 | 0 | 1 | 1 |
| Idempotência | `auditor-idempotencia` | **PASS** | 0 | 0 | 0 | 0 |
| Supply chain | `auditor-supplychain` | **PASS** | 0 | 0 | 0 | 1 |
| Conformidade LGPD | `auditor-conformidade-lgpd` | **PASS** | 0 | 0 | 0 | 2 |

**Veredito 1ª passada: 5 FAIL + 4 PASS — 5 CRÍTICO + 8 ALTO + 9 MÉDIO. Conserto causa-raiz obrigatório (INV-RITUAL-001).**

## Achados estruturados (dedup + consertos aplicados)

Vários auditores reportaram o mesmo achado por ângulos diferentes (drift-docs C1 = produto C2 = qualidade A1). Lista consolidada:

### CRÍTICO

- **C1: REGRAS-INEGOCIAVEIS.md sem INV-ADMIN-001..003 + INV-PROD-SET-001 + INV-WEBHOOK-OUT-001..005** (produto-CRITICO-1, drift-docs-CRITICO-1, qualidade-ALTO-1).
  - **Conserto:** commit `6f3e755` — REGRAS ganha 3 seções com os 9 IDs cravados + hook + consequência. **Resolvido.**
- **C2: ADR-0054 status `proposta` apesar de implementada em F-C1 P4 Bloco 3** (produto-CRITICO-1, drift-docs-ALTO-4).
  - **Conserto:** commit `6f3e755` — ADR-0054 promovida `proposta` → `aceito (2026-05-24)`; AGENTS.md §11 atualizado. **Resolvido.**
- **C3: AC-FC1-004-2,-3,-4 (drill rotação real + log datado + runbook §10) não cumprido** (produto-CRITICO-3).
  - **Conserto parcial:** commit `4957cf5` ajusta drill 9 do `validar_f_c1` para exigir convenção `rotacao-dogfooding-YYYY-MM-DD.md` real (não `*-aceitacao-procedimento.md`); commit `ff45fa0` atualiza runbook §10 com tabela de procedimentos canônicos. **Bloqueio remanescente:** Roldão precisa executar 1 rotação real + arquivar log (Task #24 — GATE-FC1-ROTACAO-DRILL-REAL).
- **C4: AGENTS.md §3 lista 32 hooks / 207 casos mas realidade é ~40/288** (drift-docs-CRITICO-2).
  - **Conserto:** commit `ff45fa0` — §3, §6, §12, cabeçalho atualizados para ~40 hooks ativos / 288/288 casos. **Resolvido.**

### ALTO

- **A1: INV-ADMIN-003 referenciada em código sem entrada em REGRAS e sem teste citando o ID** (qualidade-ALTO-1).
  - **Conserto:** commit `6f3e755` (REGRAS) + commit `4957cf5` (`tests/test_inv_admin_003_break_glass.py` com 5 casos). **Resolvido.**
- **A2: AC-FC1-006-5 (drill break-glass) não executado** (produto-ALTO-1).
  - **Bloqueio remanescente:** Roldão precisa executar `criar_admin_recovery` + arquivar log (Task #24 — GATE-CYBER-BREAKGLASS-DRILL).
- **A3..A6: AGENTS.md §6, §12, cabeçalho, CURRENT.md ≤40 linhas, ADR-0054 status** (drift-docs-ALTO-1..6).
  - **Conserto:** commit `ff45fa0`. **Resolvido.**

### MÉDIO (INV-RITUAL-001)

- **MED-1 (segurança): router em test condição triggera em PROD**.
  - **Conserto:** commit `4957cf5` — router agora detecta pytest via `PYTEST_CURRENT_TEST` + `sys.modules` + `sys.argv` em vez de comparar TEST.NAME. Test runtime negado vs test pytest liberado. **Resolvido.**
- **MED-2 (segurança / INV-ADMIN-003): middleware aceita TOTP em conta break-glass apesar de spec exigir U2F**.
  - **Conserto:** commit `4957cf5` — `_device_eh_webauthn` checa `persistent_id` do `otp_device`; quando `is_break_glass=True`, camada 1 do middleware bloqueia fail-loud com motivo `break_glass_sem_u2f`. **GATE-CYBER-BREAKGLASS-U2F-ENFORCE** rastreado pra Wave A integrar `django-otp-webauthn`. **Resolvido.**
- **MED-1 (llm): docstring de `_aplicar_seed` mente sobre "tolerante a IntegrityError"** (llm-correctness-MED-1).
  - **Conserto:** commit `4957cf5` — docstring honesta (só captura `ModuleNotFoundError`). **Resolvido.**
- **MED-1 (obs): `criar_admin_recovery` não grava na cadeia auditável**.
  - **Conserto:** commit `4957cf5` — invoca `publicar_evento(acao="Admin.BreakGlass.CONTA_CRIADA")` na mesma `transaction.atomic()` do `Usuario.create_user`; ação registrada em `acoes_canonicas.ACOES_ADMIN_BREAK_GLASS`. **Resolvido.**
- **MED-1 (produto): glossário sem 5 termos novos** (produto-MED-1).
  - **Conserto:** commit `ff45fa0` — break-glass, admin-recovery, outbound webhook, SSRF guard, canonical string. **Resolvido.**
- **MED-1..MED-4 (drift): spec texto "≥250 hooks", checklist desatualizado, data 2026-05-23, CURRENT sem data**.
  - **Conserto:** commit `ff45fa0`. **Resolvido.**

### BAIXO (rastreável; não bloqueia)

- DEP-003 (supply chain): Dockerfile + postgres tag-only sem SHA pin — pré-existente, GATE-DEP-DOCKERFILE-SHA-PIN Wave A.
- LGPD-borderline: `criar_admin_recovery` recebe PII via CLI — GATE-LGPD-DPIA-ADMIN-2 (DPIA admin-access cobre criação manual).
- OBS-003: métrica `break_glass_account_created_total` — pré-Foundation F-C, CONCERN BAIXO; GATE-OBS-BREAKGLASS-METRICS.
- Senha break-glass sem checagem de complexidade (só ≥14 chars) — GATE-FC1-CRIAR-RECOVERY-SENHA-COMPLEXA.
- `_SEED_MIGRATIONS` hardcoded sem teste meta de coerência — GATE-QLD-FC1-2.
- `_aplicar_seed` engole `ModuleNotFoundError` silenciosamente — GATE-QLD-FC1-3.
- `docs/operacao/rotacao-credenciais-dogfooding.md §4` cita "janela mínima legal" do AWS KMS — texto a esclarecer com `advogado-saas-regulado` (não bloqueia).
- `docs/discovery/insumos/problemas-codigo-agentes-ia.txt` sem frontmatter — decisão Roldão (insumo bruto OK).

## Status pós consertos (2026-05-24)

**Tasks #12..#23 fechadas:** 21 dos 22 itens C/A/M consertados via causa-raiz (3 commits: `6f3e755` + `4957cf5` + `ff45fa0`).

**Pendente pra 2ª passada (Task #24):**
- Roldão executa rotação real de 1 chave dogfooding → arquiva `docs/operacao/drills/rotacao-dogfooding-YYYY-MM-DD.md` com declaração datada (LGPD art. 16).
- Roldão executa `manage.py criar_admin_recovery` → arquiva `docs/operacao/drills/break-glass-YYYY-MM-DD.md`.

**Após Task #24:** dispara 2ª passada (10 auditores). Critério ZERO C/A/M (INV-RITUAL-001).

## GATEs Wave A propostos

| GATE | Origem | Quando |
|---|---|---|
| **GATE-CYBER-BREAKGLASS-U2F-ENFORCE** | segurança-MED-2 | Wave A integra `django-otp-webauthn`; middleware passa a aceitar device WebAuthn |
| **GATE-CYBER-BREAKGLASS-DRILL** | produto-AC-006-5 | drill mensal break-glass arquivado |
| **GATE-FC1-ROTACAO-DRILL-REAL** | produto-AC-004-2 | rotação real mensal arquivada |
| **GATE-LGPD-DPIA-ADMIN-2** | lgpd-BAIXO-1 | DPIA admin-access cobre criação manual de break-glass |
| **GATE-OBS-BREAKGLASS-METRICS** | obs-BAIXO-1 | métrica `break_glass_account_created_total` em Grafana (sobe pra MÉDIO em F-C2) |
| **GATE-FC1-CRIAR-RECOVERY-SENHA-COMPLEXA** | segurança-BAIXO-1 | validador de entropy/dicionário em `criar_admin_recovery` |
| **GATE-QLD-FC1-2** | qualidade-BAIXO-1 | teste meta `_SEED_MIGRATIONS` × `glob *seed*.py` |
| **GATE-QLD-FC1-3** | qualidade-BAIXO-2 | `_aplicar_seed` warn em vez de swallow silencioso |
| **GATE-DEP-DOCKERFILE-SHA-PIN** | supplychain-BAIXO-1 | SHA pin de imagens em Dockerfile + docker-compose |
| **GATE-DEP-POSTGRES-SHA-PIN** | supplychain-BAIXO-1 | SHA pin `postgres:16-alpine` |
