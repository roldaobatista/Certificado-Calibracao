# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Última frente FECHADA — #3 `precificacao` (2026-06-13)

- Ritual P0→P9 completo. 5 fatias (domínio/schema/use cases+REST/P7/P8) + auditoria.
- P9: 8 auditores roteados → **8/8 PASS zero C/A/M após 3 passadas** (INV-RITUAL-001 satisfeito).
  1ª passada 4 MÉDIO (qual/prod/perf/obs) → conserto → 2ª passada adversarial **pegou 2 consertos
  falsos** (obter_padrao docstring mentindo + correlation_id de fonte vazia) → conserto focado → 3ª PASS.
- Entregue: motor de preço por cesta + 2 modos + alçadas 3 níveis + semáforo + vínculo cliente→tabela REST.
- Decisões Roldão: 2 modos de preço / alçadas 10/20/dono / semáforo de margem (não reabrir).
- Detalhe: `docs/faseamento/precificacao/matriz-reconciliacao.md` §8.

## Frente AUDITORIA DE CERIMÔNIA — CONCLUÍDA E APLICADA (2026-06-12)

- R1..R22 aplicados (Roldão aprovou tudo): hooks→pré-commit, ritual reformado, denylist de contagens,
  conformidade→GATEs, REGRAS fatiada. Relatório: `docs/faseamento/auditorias/AUDITORIA-CERIMONIA-rodada-1.md`.

## Frente EM CURSO — #4 `colaboradores` (base, seed habilidade estático)

- P0→P6 fechados: domínio + schema PG + use cases/REST (Fatia 1a/1b/2). 94 testes verdes
  (55 domínio + 12 schema + 27 API E2E). Decisões Roldão R-COL-1 (motorista pendência) + R-COL-2 (ASO fora).
- PRÓXIMO: P7 — INV-COL-* + hooks + evento Colaborador.Anonimizado · P8 emendas · P9 auditores.
- Ritual P0→P9 sem perguntar (feedback_ordem_dependencia).

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md`
- Histórico M5→PPS: `docs/faseamento/diario/2026-06-12-consolidado-m5-a-pps.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
