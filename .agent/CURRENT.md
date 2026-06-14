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
  UUID|None + entidade **`ItemComercialOS`** model+repo+migration **0020** (RLS v2 + INV-OSME-ITEMCOM-001).
- **Fatia 2 DONE:** envelope header→item (`equipamento_id` por item no consumer); `abrir_os_via_orcamento` bifurca
  (item c/ equip→atividade própria; sem→`ItemComercialOS`); OS multi-equip → `OS.equipamento`=NULL (1 equip mantém);
  pré-check baixado itera todos equip. em 1 query; 3 call-sites (adicionar/reabrir/avulsa); detecção baixado por
  `AtividadeDaOS.equipamento_id` (Risco #1). **mypy 0 + 5 testes (multi-equip + UNHAPPY baixado) + regressão 21 verdes.**
- **PRÓXIMO:** Fatia 3 (emenda INV-OS-ATIV-002/EQP-001 + INV-OSME-RCB-001/ITEMCOM-001 em REGRAS + atualizar testes
  regressão p/ multi-equip + teste de CARGA concorrência cross-equipamento) · P8 (ADR-0082 + emenda ADR-0023 +
  matriz-feature-perfil + STATUS-GERADO) · P9 auditores. GATE-OSME-RECEBIMENTO-7.5. Débito pré-existente: DJ001 `perfil_no_evento`.
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
