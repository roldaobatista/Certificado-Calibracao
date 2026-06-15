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
- **Fatias 1a+1b+2a DONE.** 1a domínio puro (12 arq, 81 testes). 1b schema PG (4 models + 5 migrations RLS v2/WORM/
  INSERT-only/trigger perfil COALESCE; `ACOES_CONTAS_RECEBER` + `os.faturada`/`os.paga`; drill 41/41 + 22 testes PG).
  **2a (núcleo manual):** use cases criar/baixar/cancelar + `ContasReceberViewSet` (criar/baixar-manual/cancelar/
  retrieve/list) + serializers + urls; idempotência REST, advisory lock, perfil server-side, eventos titulo_emitido/
  pago/titulo_cancelado; 13 testes. **2b (gateway/webhook/override):** emitir-boleto/pix-recorrente (Mock) +
  webhook público (SECURITY DEFINER `resolver_cr_titulo_por_gateway` migration 0006 + HMAC + idempotência dupla
  + anti-oráculo 401) + override (anti-PII 4 regex, 5/mês, WORM); 15 testes. Revisão Opus: reconciliou
  Protocol↔adapter + tirou DRF dos use cases; corrigiu slug não-canônico do incidente HMAC. **Módulo CR: núcleo
  REST completo (manual + gateway Mock + webhook).** **PRÓXIMO = Fatia 3** (auto-fatura OS + inadimplência +
  desbloqueio — toca OS/clientes FECHADOS; T-CR-040..048) → P8/P9. Débitos p/ P9: snapshot webhook=valor_original
  (sem juros); desconto-pontualidade pré-vencimento sem fórmula; INV-FIN-* voltam ao mestre na fatia 3d.

## Última frente FECHADA — `orcamentos` MÓDULO 100% Wave A (2026-06-15)

- Detalhe no diário + `[[estado-do-projeto-wave-a-em-curso]]`. ADR-0083 (`PrecoResolvido`). Commits
  `b002dae`/`cf12bc8`/`24404ca`/`4f8b326`. US Wave B: 003/006/010. Matriz: `orcamentos/matriz-reconciliacao.md` §8.

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md` · matriz: `docs/faseamento/orcamentos/matriz-reconciliacao.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
