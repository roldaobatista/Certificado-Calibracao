# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Última frente FECHADA — #4 `colaboradores` (2026-06-13)

- Ritual P0→P9. P9: 8 auditores → **8/8 PASS zero C/A/M após 2 passadas** (1ª pegou documentos[] vazando por
  papel + teste placebo + storage_port:object + audit comissão; conserto causa-raiz). BAIXOs → R10. Detalhe: matriz §8.
- Entregue: CRUD + papéis (signatário↔RT por usuario_id · DONO único · motorista pendência) + matriz habilidades
  (catálogo seed global) + comissão + documentos + desligamento (cascade+outbox) + mascaramento PII + /elegiveis DTO.
  Roldão: R-COL-1 motorista pendência / R-COL-2 ASO fora. (#3 precificacao FECHADA — diário.)

## Frente #5 `orcamentos` — P0/P1/P2 feitos, **PAUSADA por dependência** (2026-06-13)

- P0 (T-ORC-000) + spec v1 + P2 (tech-lead+advogado APROVA C/ CORREÇÕES) prontos. Decisões Roldão:
  R-ORC-1 equipamento no orçamento · R-ORC-2 aprovação lógica-agora/PDF-depois · **R-ORC-3 N equipamentos
  por orçamento E OS + itens compartilhados**. Detalhe: `docs/faseamento/orcamentos/reviews-consolidado.md`.
- ⛔ R-ORC-3 exige retrofit OS (1→N equip.). Envelope `Orcamento.Aprovado` muda (equip. por item).

## PRÓXIMA frente — `os-multi-equipamento` (PRÉ-REQUISITO de orcamentos)

- Retrofit CIRÚRGICO da OS (módulo fechado): `OS.equipamento` → nullable; equipamento por ATIVIDADE
  (coluna `equipamento_id_desnormalizado` JÁ existe; índice INV-OS-CONC-001 já chaveia por ela — não move).
  Migration RELAXANTE (não destrutiva) + ADR nova + emenda ADR-0023/INV-OS-ATIV-002/INV-OS-EQP-001 +
  envelope header→item + OS publica `OS.Aberta` de volta. Esforço M, aditivo/reversível.
- Acionar `consultor-rbc-iso17025`: recebimento por instrumento (cl. 7.5) — `equipamento_recebimento_id` por OS hoje.
- Depois: orcamentos v2 (envelope por item + correções TL/ADV) → P3 → impl → P9.

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md`
- Histórico M5→PPS: `docs/faseamento/diario/2026-06-12-consolidado-m5-a-pps.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
