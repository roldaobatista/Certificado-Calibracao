# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `os-multi-equipamento` (P0..P3 + Fatias 1a/1b DONE) (2026-06-14)

- Retrofit cirúrgico da OS (fechada): 1→N equipamentos (equipamento por ATIVIDADE) + `ItemComercialOS`
  (deslocamento/taxa, decisão Roldão D-OSME-3) + recebimento por instrumento (cl. 7.5). Aditivo/reversível.
  P0..P3 + reviews (tech-lead + consultor-rbc) em `docs/faseamento/os-multi-equipamento/` (spec v2, plan, tasks).
- **Fatia 1a DONE:** enum `TipoItemComercial` + `ItemComercialOSSnapshot` + `ItemOrcamento.equipamento_id`.
- **Fatia 1b DONE:** rename `equipamento_id_desnormalizado`→`equipamento_id` (19 call-sites) + migration **0018**
  (RenameField atômico + triggers V2 COALESCE / reverse V1 + índice `atv_tenant_equip_est_idx` +
  add `AtividadeDaOS.equipamento_recebimento_id`). Trigger forward = COALESCE (fallback OS, compat single-equip).
- **Fatia 1c DONE:** `OS.equipamento` null=True + índice parcial (migration **0019**) + `OSSnapshot.equipamento_id`
  UUID|None (DTOs query) + entidade **`ItemComercialOS`** model+repo+migration **0020** (RLS v2 + INV-OSME-ITEMCOM-001).
  **mypy Success (sem type:ignore) + 4 testes (RLS cross-tenant UNHAPPY) + regressão 20 verdes.**
- **PRÓXIMO:** Fatia 2 (envelope header→item: `ItemOrcamento.equipamento_id` no consumer + `abrir_os_via_orcamento`
  cria atividade c/ equip. do item OU `ItemComercialOS` se None; 3 call-sites `adicionar_atividade`/reabertura/avulsa;
  detecção baixado por atividade em `consumers/equipamento.py`) · Fatia 3 (INVs + carga) · P8 (ADR-0082) · P9.
  GATE-OSME-RECEBIMENTO-7.5 (seam, app equipamentos). Débito pré-existente: DJ001 `perfil_no_evento` (SAN-PERFIL).
- ✅ Descoberta T-OSME-000: `os.aberta` JÁ cruza o bus (INT-01) — TL-ORC-03 estava desatualizado (corrige escopo).

## Frente #5 `orcamentos` — P0/P1/P2 feitos, **PAUSADA** (retomar após os-multi-equipamento)

- Depende do envelope header→item desta frente. Spec sobe a v2. Detalhe: `docs/faseamento/orcamentos/reviews-consolidado.md`.

## Última frente FECHADA — #4 `colaboradores` (2026-06-13)

- Ritual P0→P9, 8/8 auditores PASS após 2 passadas. Detalhe: diário. (#3 precificacao FECHADA — diário.)

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md` (ADR nova OS multi-equip. no P8)
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
