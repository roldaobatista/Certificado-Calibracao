# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente EM CURSO — #3 `precificacao` (parcial, stub custo)

- P0 FECHADO (`0f511d4`): greenfield; seams prontos (PPS, Imposto, moldes de porta, WORM Padrão B).
- P1 FECHADO (`e9f5799`): spec v1 recorte Wave A sobre PRD US-PRC-001..008.
- P2 FECHADO (`88cd519`): revisões tech-lead+advogado AMBAS APROVA COM CORREÇÕES; spec v2 stable.
- Emendas cross-doc P2→P3 APLICADAS (`dcb8621`): retencao-matriz, lgpd-rat, ADR-0081 emenda.
- Decisões Roldão batch (2026-06-12): dois modos de preço; alçadas 3 níveis; semáforo de margem.
- **PRÓXIMO: P3 — `plan.md` + `tasks.md` (T-PRC-010..) → implement → P7 → P8 → P9.**
- Docs em `docs/faseamento/precificacao/`.

## Frente AUDITORIA DE CERIMÔNIA — aplicação em curso

- APROVADA INTEGRAL pelo Roldão 2026-06-12 (4 pacotes: A hooks / B auditores / C docs / D conformidade).
- Pacotes B/C/D sendo aplicados nesta sessão; pacote A (dispatcher hooks pré-commit) = frente técnica própria.
- Relatório: `docs/faseamento/auditorias/AUDITORIA-CERIMONIA-rodada-1.md`.

## Ordem das próximas frentes (#4 em diante)

(plano: `docs/faseamento/plano-dependencia-sistema.md`)

4. `colaboradores` (base, seed habilidade estático)
5. `orcamentos`

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens (hooks/casos/ADRs/INVs): `docs/governanca/STATUS-GERADO.md`
- ADRs vivas/frias: `docs/adr/INDICE.md`
- Histórico M5→PPS: `docs/faseamento/diario/2026-06-12-consolidado-m5-a-pps.md`
- Gates consolidados: `docs/governanca/STATUS-GERADO.md` + docs de cada frente
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
