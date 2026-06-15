# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `contas-receber` (Nível 5 — fecha a receita ponta a ponta) — RITUAL P0–P3 FECHADO

- **P0–P3 prontos** (2026-06-15): `T-CR-000` re-rastreado pós-orçamentos · `spec.md` v2 · `reviews-consolidado.md`
  (P2: tech-lead Opus + advogado + consultor-rbc, todos APROVAM C/ CORREÇÕES) · `plan.md` + `tasks.md` (T-CR-010..061)
  revisados (PLAN-CR-01..03). Em `docs/faseamento/contas-receber/`.
- **Decisão de gatilho (regra #0):** nenhum gatilho do PRD carrega hoje `cliente_id`+`valor` no outbox. Canônico =
  **`os.concluida` ENRIQUECIDO no OUTBOX** (não no WORM da OS — TL-CR-03); `Certificado.Emitido` reconciliado (não é
  unidade de cobrança); `fiscal.nfse_emitida` secundário. CRITs do P2: `clientes` tem bloqueio **PULL** existente (CR
  faz adapter, não PUSH); OS já consome `os.faturada`/`os.paga` dangling (CR publica). Gateway = **Mock** (Asaas=GATE).
- **Fatias 1a+1b DONE.** 1a: domínio puro `src/domain/contas_receber/` (12 arq + 81 testes). 1b: schema PG
  `src/infrastructure/contas_receber/` — 4 models + 5 migrations (RLS v2 ENABLE+FORCE+4 policies, WORM block-delete/
  worm-check/INSERT-only Pagamento+Override, trigger perfil COALESCE), `ACOES_CONTAS_RECEBER` (8 slugs) +
  `os.faturada`/`os.paga` em ACOES_OS; drill 41/41 + 22 testes PG (cross-tenant + WORM + UNIQUE os_id + CHECK pix);
  ruff+mypy limpos; revisão Opus (testes genuínos; corrigi 1 flake temporal). Achado p/ Fatia 2: desconto-pontualidade
  pré-vencimento sem fórmula na spec. **PRÓXIMO = Fatia 2** (use cases + REST + webhook — núcleo manual+mock+webhook,
  NÃO toca módulo fechado; T-CR-030..037) → 3 (auto-fatura OS + inadimplência + desbloqueio, toca fechados) → P8/P9.

## Última frente FECHADA — `orcamentos` MÓDULO 100% Wave A (2026-06-15)

- Núcleo (Fatia 2 Ondas 2a–2f): criar/itens/enviar/recusar/cancelar/expirar + análise crítica cl. 7.1 perfil-
  aware (fail-closed A) + link público 1-clique (SECURITY DEFINER) + conversão em OS (envelope por item ADR-0082).
  **P8:** ADR-0083 (`PrecoResolvido` reconcilia VO `Preco`; emenda PRD). **P9:** 8 auditores → 1 MÉDIO
  (INV-ORC-PRECO-001 sem teste) consertado + 2ª passada PASS → 8/8 PASS. **T-ORC-039:** `TemplateViewSet` CRUD +
  gate selo RBC perfil A (INV-ORC-SELO-RBC + hook); produto MÉDIO (CHANGELOG) consertado. US Wave B: 003/006/010.
  Commits `b002dae`(2f)·`cf12bc8`(P8)·`24404ca`(P9). GATEs/débitos: `matriz-reconciliacao.md` §8. Detalhe: diário.

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md` · matriz: `docs/faseamento/orcamentos/matriz-reconciliacao.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
