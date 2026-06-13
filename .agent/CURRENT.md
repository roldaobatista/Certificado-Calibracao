# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Última frente FECHADA — #4 `colaboradores` (2026-06-13)

- Ritual P0→P9 completo. P9: 8 auditores → **8/8 PASS zero C/A/M após 2 passadas** (INV-RITUAL-001).
  1ª passada 4 FAIL (documentos[] vazava por papel · teste placebo · raises genéricos · storage_port:object ·
  partial_update sem audit comissão) → conserto causa-raiz → 2ª passada adversarial **8/8 PASS**. BAIXOs → R10.
- Entregue: CRUD + papéis (signatário↔RT por usuario_id · DONO único · motorista pendência) + matriz
  habilidades (catálogo seed global) + comissão default + documentos + desligamento (cascade+outbox) +
  mascaramento PII multi-papel + /elegiveis DTO mínimo. Roldão: R-COL-1 motorista pendência / R-COL-2 ASO fora.
- Detalhe: `docs/faseamento/colaboradores/matriz-reconciliacao.md` §8. (#3 precificacao FECHADA — diário.)

## PRÓXIMA frente — #5 `orcamentos` (1ª ponta de receita)

- Ordem cravada: `docs/faseamento/plano-dependencia-sistema.md` §7 (#5 orcamentos — consome
  catálogo+precificacao; produz `Orcamento.Aprovado` → OS já tem consumer passivo).
- Pré-reqs prontos: configuracoes-sistema ✅ · produtos-pecas-servicos ✅ · precificacao ✅ · colaboradores ✅.
- Seguir ritual P0→P9 sem perguntar (feedback_ordem_dependencia).

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md`
- Histórico M5→PPS: `docs/faseamento/diario/2026-06-12-consolidado-m5-a-pps.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
