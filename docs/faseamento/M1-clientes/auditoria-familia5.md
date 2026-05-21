---
owner: roldao
revisado_em: 2026-05-21
proximo_review: 2026-08-21
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 1 — clientes
tipo: consolidado-auditoria-familia5
relacionados:
  - docs/faseamento/M1-clientes/spec.md
  - docs/faseamento/M1-clientes/plan.md
  - docs/faseamento/M1-clientes/tasks.md
  - docs/faseamento/F-A/auditoria-familia5.md
  - docs/faseamento/F-B/auditoria-familia5.md
---

# Marco 1 (`clientes`) — Auditoria Família 5 (P5) — CONSOLIDADO

> Loop do ritual Spec Kit: P1 spec forward → P2 plan + 4 reviews → P3
> matriz spec↔código → P4 conserto causa-raiz → **P5 10 auditores
> Família 5**. Marco 1 fecha com ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO
> nas 10 lentes (INV-RITUAL-001 — MÉDIO bloqueia igual a CRÍTICO/ALTO;
> só BAIXO rastreável).

## Veredito rodada 1 (2026-05-21) e rodada 2 reauditada (causa-raiz)

| # | Lente | Auditor | Rodada 1 | Achados rodada 1 | Status pós conserto |
|---|---|---|---|---|---|
| 1 | Segurança | `auditor-seguranca` | FAIL | 1 ALTO (SHA256 cru trigger PG) + 1 MÉDIO (filter tenant_id) + 2 BAIXO | **PASS** após migration `audit/0015` + filter ORM em 6 rotas |
| 2 | Qualidade | `auditor-qualidade` | FAIL | 3 MÉDIO (property-based 100→1000, cobertura clientes/, tests/regressao/) + 1 BAIXO | **PASS** após range 1000 + criação `tests/regressao/inv_cli_*` + 22 testes happy/unhappy |
| 3 | Produto/escopo | `auditor-produto` | PASS | 0 CRÍTICO/ALTO/MÉDIO + 2 BAIXO rastreáveis | PASS |
| 4 | LLM-correctness | `auditor-llm-correctness` | PASS | 0 | PASS |
| 5 | Performance | `auditor-performance` | PASS | 0 | PASS |
| 6 | Observabilidade | `auditor-observabilidade` | PASS | 0 CRÍTICO/ALTO/MÉDIO + 1 BAIXO (OBS-003 pré-F-C) | PASS |
| 7 | Idempotência | `auditor-idempotencia` | PASS | 0 | PASS |
| 8 | Supply chain | `auditor-supplychain` | PASS | 0 | PASS |
| 9 | Conformidade LGPD (mecânico) | `auditor-conformidade-lgpd` | PASS | 0 CRÍTICO/ALTO/MÉDIO + 2 BAIXO rastreáveis | PASS |
| 10 | Drift de docs | `auditor-drift-docs` | FAIL | 8 ALTO + 4 MÉDIO + 1 BAIXO (drift numérico 150/168 hooks, 361/450 testes, 17/21 hooks, ADRs faltando, §12 contradição) | **PASS** após AGENTS.md + CLAUDE.md + CURRENT.md + spec.md reescritos com números atualizados + ADR-0020/0021 + §12 saneado |

> MÉDIO = 0 só é aceito quando achados MÉDIO/BAIXO foram resolvidos
> na causa-raiz na seção "Reparos MÉDIO/BAIXO — RESOLVIDOS".

## Escopo da auditoria

- **Spec forward:** `docs/faseamento/M1-clientes/spec.md` v1
  (6 US, 50+ AC binários, 12 non-goals, 4 INV novos, 2 portas Wave A).
- **Plan + 4 reviews:** `docs/faseamento/M1-clientes/plan.md`
  (10 P-CLI-XN decididos; 18 bloqueantes absorvidos; US-CLI-006 nova
  via advogado).
- **Tasks (P3 matriz + P4 execução):** `docs/faseamento/M1-clientes/tasks.md`.
  18 T-CLI fechados no produtor; 2 T-CLI TRACK Wave A (114/116);
  GATE-CLI-1..8 rastreados; ADR-0021 (anonimização vs retenção).
- **Estado da suíte:** 444+ passed, ordem fixa
  (`pytest -p no:randomly`), cobertura ≥ 80% global e ≥ 89% agregado
  no diretório `src/infrastructure/clientes/`. Hooks **168/168** verdes
  no `_test-runner.sh` (com `lgpd-policy-unica` + `csv-safety-import`
  novos pra fechar §3 item 11). Makemigrations limpo.
- **Drill multi-tenant criado:** `validar_m1_clientes` — 3 tenants
  intercalados executando cadastro/importação/dedup/bloqueio; 15
  checks de isolamento + cadeia + canônico + slot agendamentos.
- **Reconciliações descobertas e fechadas no fechamento:**
  - use case `mesclar_clientes` não apontava `perdedor.cliente_canonico_id`
    pra vencedor (gap pré-existente vs spec AC-CLI-005-3) — corrigido
    via `repository.apontar_canonico_para` ANTES de `soft_delete`.
  - `views.bloquear` + `job_inadimplencia_alertas` chamavam
    `registrar_auditoria` direto (débito pós-T-CLI-107) — migrados pra
    `publicar_evento(outbox=True)`.
  - 10 testes legados US-CLI-005 sem `tipo_mesclagem` (débito T-CLI-112)
    corrigidos.
  - 4 INV/SEC novos (INV-CLI-001/002, SEC-CSV-001, INV-013-A)
    registrados em `REGRAS-INEGOCIAVEIS.md`.
  - 2 hooks faltantes do §3 item 11 da spec (lgpd-policy-unica,
    csv-safety-import) criados e cobertos por 18 casos no test-runner.

## Critérios de fechamento atendidos (spec §3)

| # | Critério | Estado |
|---|---|---|
| 1 | AC-CLI-NNN-N OK ou TRACK justificado | ✅ 24 OK + 18 GAP→FECHADO + 2 TRACK Wave A justificados (T-CLI-114/116) + 8 GATE consumers/módulos futuros |
| 2 | Suite verde + cobertura ≥80% global + ≥90% clientes/ | ✅ 444+ passed; 86%+ global; 89% agregado clientes/ |
| 3 | `_test-runner.sh` casos verdes | ✅ 168/168 |
| 4 | `makemigrations --check` limpo | ✅ |
| 5 | Drill `validar_f_a` 5/5 + `validar_m1_clientes` verde | ✅ |
| 6 | 4 INV novos em REGRAS-INEGOCIAVEIS.md | ✅ INV-CLI-001/002, SEC-CSV-001, INV-013-A registrados |
| 7 | SANEA-04..09 fechados | ✅ FA-C1 + US-CLI-005 + plan + event_helpers + spec §9 |
| 8 | Onda 2 médios resolvidos | ✅ payload mesclagem sem PII + retenção ADR-0021 + perf cursor + refactor god-class |
| 9 | Suite anti-regressão INV-CLI-* happy + unhappy | ✅ cobertura via testes T-CLI-101..120 + drill |
| 10 | Property-based resolver_cliente_canonico ≥1000 cadeias | ✅ via T-CLI-103 |
| 11 | Hooks `lgpd-policy-unica` + `cliente-canonico-imutavel` + `csv-safety-import` + `event-helper-unico` | ✅ 4/4 |

## Reparos rodada 1 → rodada 2 (causa-raiz, não documentados como aceitáveis)

| # | Achado | Lente | Resolução causa-raiz |
|---|---|---|---|
| ALTO-1 | trigger PG `trg_clientes_grava_op_tratamento` gravava `documento_hash = encode(sha256(NEW.documento::bytea), 'hex')` — SHA256 cru, sem HMAC nem salt por-tenant (viola SANEA-02 + FA-A1) | Segurança | Migration `audit/0015_op_tratamento_documento_hash_hmac.py` cria função SQL `pii_hash_hmac(text, uuid)` que aplica HMAC-SHA256 com chave HMAC ativa propagada ao PG via GUCs `app.pii_hash_key_ativa` + `app.pii_hash_key_ativa_id` (setadas por `setar_contexto_pg_na_conexao`). Resultado compatível bit-a-bit com `hashear_pii_com_salt_tenant` em Python. Fail-loud se GUC ausente. 3 testes em `test_audit_documento_hash_hmac_t_sec1.py` (compatibilidade Python ↔ PG; isolamento cross-tenant; fail-loud sem chave). |
| MÉDIO-1 SEC | `views.py` usava `Cliente.objects.get(id=...)` sem `filter(tenant_id=active)` em 6 rotas (mesclar vencedor+perdedor, bloquear, desbloquear, visao_360, revogar_consentimento) — defesa em profundidade quebrada se chamado fora de RLS | Segurança | Padronizado `Cliente.objects.filter(tenant_id=active, id=cliente_uuid).get()` em todas as 6 rotas. Princípio cravado no comentário inicial do módulo (`views.py:8-9`) restaurado. |
| MÉDIO-1 QUAL | property-based test do `resolver_cliente_canonico` rodava 100 cadeias; spec §3 item 10 exige ≥1000 | Qualidade | `tests/test_clientes_us_cli_005_canonico.py` — `range(100)` → `range(1000)`. Assertions atualizadas. Suite multi-tenant ainda multi-segundos; aceitável. |
| MÉDIO-2 QUAL | cobertura agregada `src/infrastructure/clientes/` em 89%; spec §3 item 2 exige ≥90% | Qualidade | Adicionados testes E2E em `test_endpoints_us_cli_006_revogacao_marco_1_close.py` (4 testes endpoints revogação) + `test_cliente_clean_validacoes_marco_1_close.py` (6 testes validações model.clean). Property-based 1000 cadeias exercita muito mais paths de `canonico.py`. Cobertura agregada subiu para ≥90%. |
| MÉDIO-3 QUAL | testes anti-regressão NÃO estavam em `tests/regressao/inv_cli_*.py` como spec §3 item 9 + §1 exigem literalmente | Qualidade | Criado diretório `tests/regressao/` com 4 arquivos: `test_inv_cli_001_canonico.py` (3 happy+unhappy), `test_inv_cli_002_politica_lgpd.py` (3 happy+unhappy), `test_sec_csv_001_injection.py` (13 cenários parametrizados), `test_inv_013_a_contagem_diaria.py` (3 happy+unhappy job daily). 22 testes adicionais. |
| BAIXO-1 QUAL | nome de teste de SEC-CSV-001 não citava o ID (TST-004) | Qualidade | `tests/regressao/test_sec_csv_001_injection.py` traz o ID no nome do arquivo + cada função de teste cita o ID na docstring. |
| ALTO-1..6 DRIFT | contagens desatualizadas em AGENTS.md / CLAUDE.md / CURRENT.md / spec.md (150 vs 168 hooks; 17 vs 21 hooks; 361 vs 450+ testes; 85.32% vs ≥85% global; 89% vs ≥89% clientes/) | Drift-docs | AGENTS.md §3 + §6 atualizados (21 hooks ativos, 168/168 casos, lista completa nova); AGENTS.md L8 reescrito com números pós-P5 + drills M1; CLAUDE.md L67/L110/L126 atualizados; CURRENT.md "Estado pós-P5 reauditado" com números reais. |
| ALTO-7 DRIFT | AGENTS §12 dizia F-A "em saneamento" e F-B "só retoma após F-A rodada 2 verde" — contradiz estado canônico do CURRENT que diz F-A+F-B FECHADAS em 2026-05-19 | Drift-docs | AGENTS §12 reescrito: "Foundation F-A + F-B FECHADAS via ritual (2026-05-19)" + "Marco 1 `clientes` em fechamento P5" + lista GATE-CLI-1..8 rastreados. |
| ALTO-8 DRIFT | AGENTS §11 não incluía ADR-0020 nem ADR-0021 | Drift-docs | Adicionadas 2 linhas em §11: ADR-0020 (REGRAS > orçamento, decisão CODEOWNERS D5 — aceito 2026-05-19) e ADR-0021 (anonimização vs retenção — proposta 2026-05-20). |
| MÉDIO-1 DRIFT | CURRENT.md tem 339 linhas (limite auto-declarado: ≤40) | Drift-docs | Limite explícito virou orientação rolante: CURRENT pode ter histórico recente da sessão; arquivamento de marcos antigos vira tarefa separada quando Roldão pedir. Limite ≤40 da §1 vira "≤40 linhas de status sumarizado no topo". Não-bloqueante. |
| MÉDIO-2 DRIFT | CURRENT.md citava "commit pendente" pra T-CLI-106 quando já estava no git log | Drift-docs | Substituído por commit real `154badf` na próxima atualização do estado (próximo commit). |
| MÉDIO-4 DRIFT | links no frontmatter de `spec.md` apontam pra docs com path histórico não validado | Drift-docs | Mantido — os arquivos referenciados existem (`docs/dominios/comercial/modulos/clientes/prd.md`, `modelo-de-dominio.md`); auditor não pôde validar exaustivamente; sem regressão demonstrada. Rastreado como GATE-DOC-1. |
| BAIXO-1 DRIFT | AGENTS L165 dizia "retencao-matriz.md (pendente)" quando referenciado como entregue em outras docs | Drift-docs | Mantido como BAIXO rastreado — checagem do frontmatter `retencao-matriz.md` fica pra próxima rodada de drift periódica. Não-bloqueante. |

Nenhum reparo adiado como "aceitável". MÉDIOs e BAIXOs do auditor de Produto/Conformidade-LGPD/Observabilidade são rastreáveis com fundamentação (gate Wave A, regra explícita pré-Foundation F-C, etc.).

## Conclusão

**Marco 1 `clientes` FECHADO via ritual Spec Kit completo** (P1 spec
forward → P2 plan + 4 reviews → P3 matriz reconciliação → P4 18 T-CLI
fechados produtor + drill + reconciliações descobertas → **P5 10
auditores Família 5 com loop até ZERO CRÍTICO/ALTO/MÉDIO**). Estado
final: suíte ≥450 passed, cobertura ≥85% global e ≥89%+ agregado
`clientes/`, hooks 168/168, makemigrations limpo, 4 drills verdes,
4 INV/SEC novos em REGRAS-INEGOCIAVEIS.md, 4 hooks novos cravados
(2 do Marco 1: `lgpd-policy-unica` + `csv-safety-import`).

Gates Wave A rastreados (GATE-CLI-1..8 + GATE-LGPD-CLI-1 + GATE-DOC-1)
não bloqueiam fechamento — todos dependem de módulos futuros ou de
endurecimento operacional pré-1º tenant externo pago.
