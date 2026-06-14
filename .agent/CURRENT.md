# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `os-multi-equipamento` (P0..P3 + Fatia 1a — PRÓXIMO = Fatia 1b schema/migration) (2026-06-13)

- **Impl Fatia 1a DONE** (T-OSME-010/011/013-parte): enum `TipoItemComercial` + `ItemComercialOSSnapshot` +
  `ItemOrcamento.equipamento_id` (aditivo, 12 testes/mypy/ruff verdes). PRÓXIMO = Fatia 1b: rename
  `equipamento_id_desnormalizado`→`equipamento_id` (ATÔMICO cross-layer) + migration 0018 (CREATE OR REPLACE
  2 triggers + reverse) + OS/recebimento nullable + ItemComercialOS model+RLS + **drill banco COM dados** (TL-01).

- Retrofit cirúrgico da OS (fechada): 1→N equipamentos (equipamento por ATIVIDADE) + entidade
  `ItemComercialOS` (deslocamento/taxa) + recebimento por instrumento (cl. 7.5). Aditivo/reversível, esforço L.
- P0 (T-OSME-000) + spec **v2** + P2 (tech-lead + consultor-rbc, ambos APROVA C/ CORREÇÕES) + **P3 plan/tasks**
  (T-OSME-010..061, 4 fatias) prontos. Detalhe: `docs/faseamento/os-multi-equipamento/reviews-consolidado.md`.
- Decisões: **Roldão D-OSME-3** = item comercial como LINHA na OS (não diferir). D-OSME-1 renomear
  `equipamento_id_desnormalizado`→`equipamento_id`. D-OSME-5/RBC = recebimento migra OS→atividade.
- 3 CRÍTICOS p/ P3: TL-01 RenameField quebra triggers PL/pgSQL (CREATE OR REPLACE ambas + reverse) ·
  TL-02 índice novo `atv_tenant_equip_estado_idx` (detecção baixado) · TL-03 3 call-sites a mais
  (adicionar_atividade/reabertura/OS avulsa). GATE-OSME-RECEBIMENTO-7.5 (seam preenchimento, app equipamentos).
- ✅ Descoberta T-OSME-000: `os.aberta` JÁ cruza o bus (INT-01) — TL-ORC-03 estava desatualizado.

## Frente #5 `orcamentos` — P0/P1/P2 feitos, **PAUSADA** (retomar após os-multi-equipamento)

- Depende de `os-multi-equipamento` (envelope header→item). Spec sobe a v2 consumindo o envelope por item +
  correções TL/ADV. Detalhe: `docs/faseamento/orcamentos/reviews-consolidado.md`.

## Última frente FECHADA — #4 `colaboradores` (2026-06-13)

- Ritual P0→P9, 8/8 auditores PASS após 2 passadas. Detalhe: diário. (#3 precificacao FECHADA — diário.)

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md` (ADR nova OS multi-equip. no P3/impl)
- Histórico M5→PPS: `docs/faseamento/diario/2026-06-12-consolidado-m5-a-pps.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
