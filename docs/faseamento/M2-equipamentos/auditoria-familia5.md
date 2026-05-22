---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 2 — equipamentos
tipo: consolidado-auditoria-familia5
relacionados:
  - docs/faseamento/M2-equipamentos/spec.md
  - docs/faseamento/M2-equipamentos/plan.md
  - docs/faseamento/M2-equipamentos/tasks.md
  - docs/faseamento/F-A/auditoria-familia5.md
  - docs/faseamento/F-B/auditoria-familia5.md
  - docs/faseamento/M1-clientes/auditoria-familia5.md
---

# Marco 2 (`equipamentos`) — Auditoria Família 5 (P5) — CONSOLIDADO

> Loop do ritual: spec → plan + 4 reviews (tech-lead, advogado, corretora,
> RBC) → tasks (matriz greenfield 65 T-EQP) → reconciliar código (P4) →
> **10 auditores Família 5 sobre o estado reconciliado**. Marco 2 só
> fecha com ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO nas 10 lentes
> (INV-RITUAL-001 — MÉDIO bloqueia fechamento igual a CRÍTICO/ALTO;
> só BAIXO é rastreável).

## Pré-requisitos verificados antes da auditoria

- Suíte `tests/test_equipamentos*.py + tests/regressao/`: **365/365 passed** em 141s.
- Hooks `_test-runner.sh`: **207/207** verdes (24+1 ativos; +qr-hmac-check, equipamento-imutabilidade-check, trigger-stub-sweep, port-binding-validator).
- Drill `validar_m2_equipamentos`: **PASS** (18/18 verificações multi-tenant).
- `ruff check src/ tests/`: limpo.
- `makemigrations --check`: limpo.
- ADRs propostas Marco 2: 0018 (PWA QR), 0019 (responsabilidade IA), 0022 (RT do tenant).
- Docs canônicos aprovados pelo advogado-saas-regulado: 6 (textos-rejeicao-422, transferencia-termo v1.1, template-notificacao-sucatamento, aviso-foto-recebimento, termo-devolucao, aviso-aceite-presencial-atendente).
- Tasks fechadas: 65 T-EQP completos + T-EQP-028 PWA bloqueado por aceite ADR-0018.

## Veredito (2026-05-22)

| Lente | Auditor | Veredito final | CRÍTICO | ALTO | MÉDIO | BAIXO |
|---|---|---|---|---|---|---|
| Segurança | `auditor-seguranca` | **PASS** (2ª passada 2026-05-22 — gate `QR_IP_RATELIMIT_SALT` aplicado) | 0 | 0 | 0 | 2 |
| Qualidade | `auditor-qualidade` | **PASS** | 0 | 0 | 0 | 2 |
| Produto/escopo | `auditor-produto` | **PASS** | 0 | 0 | 0 | 4 |
| Drift docs | `auditor-drift-docs` | **PASS** (2ª passada 2026-05-23 — 11 achados consertados causa-raiz) | 0 | 0 | 0 | 2 |
| LLM correctness | `auditor-llm-correctness` | **PASS** (2ª passada 2026-05-23 — `Any` → tipos corretos) | 0 | 0 | 0 | 3 |
| Performance | `auditor-performance` | **PASS** | 0 | 0 | 0 | 3 |
| Observabilidade | `auditor-observabilidade` | **PASS** | 0 | 0 | 0 | 2 |
| Idempotência | `auditor-idempotencia` | **PASS** | 0 | 0 | 0 | 3 |
| Supply chain | `auditor-supplychain` | **PASS** (2ª passada 2026-05-23 — pip-audit retroativo + CVE-2025-68616 WeasyPrint mitigado in-app + GATE Wave A) | 0 | 0 | 0 | 4 |
| Conformidade LGPD | `auditor-conformidade-lgpd` | **PASS** | 0 | 0 | 0 | 2 |

**Veredito de encerramento: 10/10 lentes PASS ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO. Marco 2 `equipamentos` FECHADO sob INV-RITUAL-001 em 2026-05-23.**

## Achados estruturados (1ª passada — 10/10 vereditos coletados 2026-05-22)

### CRÍTICO

- **D1-CRÍTICO** (drift-docs) — AGENTS.md status Marco 1+Marco 2 desatualizado vs realidade em CURRENT.md. Cascateia decisão de roteamento. PENDENTE próxima sessão.

### ALTO

- **D4-ALTO** (drift-docs) — AGENTS.md L8/L225 hooks "168/168 casos (21 ativos)" desatualizado vs realidade `_test-runner.sh` 207/207 (25 hooks). PENDENTE.
- **D2-ALTO** (drift-docs) — CURRENT.md L44 ("192/192") contradiz L67 ("207/207") no mesmo escopo. PENDENTE.
- **D1-ALTO×4** (drift-docs) — tasks.md mantém GAP fantasma: T-EQP-070 (hook qr-hmac), T-EQP-080 (textos-rejeicao), T-EQP-092/094/097/105 (regressão + drill) — entregues mas sem ✅. PENDENTE.
- **D6-ALTO** (drift-docs) — ADR-0022 frontmatter `status: proposta` mas implementada como código em Marco 2. PENDENTE.

### MÉDIO (INV-RITUAL-001)

- **MEDIO-1 SEC** — gate `QR_IP_RATELIMIT_SALT >=32 chars` em `config/settings/prod.py` (mesmo padrão de `PII_HASH_KEY` e `QR_HMAC_KEY`); fallback hardcoded removido de `views_qr_publico.py`. Conserto causa-raiz aplicado 2026-05-22; validado 18/18 testes QR público + rate-limit. Item zerado.
- **MEDIO-1 supplychain** (procedural) — marker `pip-audit:` ausente em commits de 4 deps Marco 2 (weasyprint, pydyf, qrcode, workalendar). Conserto: rodar `pip-audit` retroativo + anexar ao docs. PENDENTE próxima sessão.
- **MEDIO-1 LLM** — `services_ficha360.py:118` `usuario_id: Any = None` deve virar `UUID | None`. PENDENTE próxima sessão.
- **MEDIO-2 LLM** — `services_versao.py:102` `assinatura_a3_assinada_em: Any` deve virar `datetime | None`. PENDENTE próxima sessão.
- **D8-MÉDIO** (drift-docs) — CURRENT.md L69-71 self-reference contradiz suite verde (OOM já resolvido em L45). PENDENTE.
- **D3-MÉDIO** (drift-docs) — CURRENT.md viola "≤40 linhas" (519 linhas). Mover lista T-EQP para `docs/faseamento/diario/`. PENDENTE.
- **D2-MÉDIO** (drift-docs) — spec.md/tasks.md frontmatter `revisado_em: 2026-05-21` desatualizado (conteúdo evoluiu até 2026-05-23). PENDENTE.

### BAIXO (rastreável; não bloqueia)

- 3 BAIXO performance (PERF-001 jobs management commands — não endpoints visíveis): GATE-EQP-PERF-1/2/3 Wave A.
- 4 BAIXO produto (drift cosmético em tabela de GATEs): consertar tasks.md.
- 2 BAIXO observabilidade (OBS-001/003 etiqueta + métricas): GATE-OBS-EQP-1/2 Wave A pós F-C.
- 3 BAIXO idempotência: GATE-IDEMP-EQP-1/2/3 Wave A.
- 2 BAIXO conformidade LGPD: GATE-LGPD-M2-1/2 Wave A (sentinelas `base_legal:` + matriz retenção +3 linhas).
- 4 BAIXO supply chain: GATE-DEP-001/002/003 Wave A (SHA pin Docker/actions).
- 2 BAIXO segurança: GATE-EQP-S-RL-1 (IP vazio fail-loud Wave A) + GATE-EQP-S-TIM-1 (timing 429 vs 404).
- 2 BAIXO qualidade: TST-007 varredura ≥1000 PII regex + TST-005 unit `validar_motivo_detalhe`.
- 3 BAIXO LLM-correctness: docstring ambígua services_versao + `# type: ignore` em massa views.py.
- 2 BAIXO drift-docs: sessão "continuação" sem âncora + spec "8 fases" vs "9 fases".

## Resolução de achados em sessão

| Achado | Origem | Status |
|---|---|---|
| MEDIO-1 SEC: gate `QR_IP_RATELIMIT_SALT` | auditor-seguranca | ✅ resolvido causa-raiz 2026-05-22 (config/settings/prod.py + base.py + views_qr_publico.py; 18/18 testes verdes) |
| MEDIO-1 LLM: `usuario_id: Any` em ficha360 | auditor-llm-correctness | ✅ resolvido 2026-05-23: `usuario_id: UUID \| None = None` em `services_ficha360.py:118`. mypy + ruff limpos. |
| MEDIO-2 LLM: `assinatura_a3_assinada_em: Any` | auditor-llm-correctness | ✅ resolvido 2026-05-23: `assinatura_a3_assinada_em: datetime \| None = None` em `services_versao.py:102` + `from datetime import datetime`. mypy + ruff limpos. |
| MEDIO-1 supplychain: pip-audit retroativo | auditor-supplychain | ✅ resolvido 2026-05-23: rodado `pip-audit --strict`; doc `docs/seguranca/pip-audit-marco-2.md`. Achado relevante: WeasyPrint 62.3 com **CVE-2025-68616 SSRF via redirect (CVSS 7.5)** — **mitigação dura aplicada** em `services_etiqueta.py:gerar_etiqueta_pdf` (custom `url_fetcher` recusa qualquer URL não-`data:`) + **GATE-EQP-DEP-WEASYPRINT-UPGRADE** Wave A (upgrade 62→68 rompe pin pydyf<0.11). 343/343 testes Marco 2 passam pós-mitigação. |
| D1-CRÍTICO + 5 ALTO + 2 MÉDIO drift-docs | auditor-drift-docs | ✅ resolvido 2026-05-23: AGENTS.md status Marco 1/Marco 2 + hooks 207/207 (25 ativos) + ADR-0022 ✅ aceito + tabela ADRs atualizada; CURRENT.md re-enxugado para 39 linhas (histórico arquivado em `docs/faseamento/diario/2026-05-23-marco2-p4-entrega-completa.md`); tasks.md 6 T-EQP marcados ✅ (070/080/092/094/097/105); spec.md/plan.md/tasks.md frontmatter revisado_em 2026-05-23. |

## GATEs Wave A rastreados (não bloqueiam Marco 2 dogfooding)

Mantidos em `tasks.md` §GATEs Wave A:

- GATE-EQP-1: A3 cliente-side Lacuna
- GATE-EQP-2: B2 Backblaze produção
- GATE-EQP-3: portal-cliente OTP (Wave B Q2-2027)
- GATE-EQP-4: matriz competências real
- GATE-EQP-5: timestamp RFC 3161 ICP-Brasil
- GATE-EQP-KMS: AWS KMS MRK
- GATE-EQP-PENTEST: timing oracle externo
- GATE-EQP-S1: evidência operacional 90d QR HMAC
- GATE-EQP-S5: cap de responsabilidade no contrato
- GATE-EQP-S6: RIPD por módulo
- GATE-EQP-S7: DR drill anual
- GATE-EQP-S8: cert RC do tenant
- GATE-EQP-RT: carta competência RT humano
- GATE-EQP-RT-AUTHZ: gestor_qualidade em ações tenant.rt.*
- GATE-EQP-RT-NOTIF: consumer ANPD/CGCRE 30d
- GATE-EQP-CLI-* (8 GATEs Marco 1 herdados)
- GATE-EQP-ACESSO-MASSIVO: alerta P2 fichas/h
- GATE-EQP-TRANSF-PAYLOAD-COMPLETO: 5 campos extras P-EQP-A4
- GATE-EQP-INV025-TRIGGER: ✅ FECHADO em T-EQP-013

## Status (parcial — 2ª sessão encerrada 2026-05-23)

Sessão 2026-05-23: **11 achados pendentes da 1ª passada consertados causa-raiz** (1 CRÍTICO + 5 ALTO + 5 MÉDIO). Detalhe item-a-item na tabela "Resolução de achados em sessão" acima. Validação:

- `tests/test_equipamentos*.py + tests/regressao/`: 343/343 PASS pós-mitigação WeasyPrint.
- Hooks `_test-runner.sh`: 207/207 PASS.
- `mypy src/infrastructure/equipamentos/*.py`: zero erro.
- `ruff check src/infrastructure/equipamentos/`: zero issue.

Próxima etapa: re-rodar 3 auditores que deram FAIL na 1ª passada (drift-docs, llm-correctness, supplychain) pra confirmar PASS ZERO CRÍTICO/ALTO/MÉDIO na 2ª passada; com 10/10 lentes em PASS, registrar veredito de encerramento do Marco 2.

Status alvo: encerramento via ritual Spec Kit quando 10/10 lentes chegarem em PASS ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO.

---

## Apêndice — invocação dos auditores

Cada auditor rodou em paralelo via subagent dedicado em `.claude/agents/`
com prompt em `docs/governanca/auditor-{lente}-prompt.md`. Severidade
INV-RITUAL-001 aplicada uniformemente.
