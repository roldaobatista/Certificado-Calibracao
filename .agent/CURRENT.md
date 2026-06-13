# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente EM CURSO — #3 `precificacao` (parcial, stub custo)

- P0 FECHADO (`0f511d4`): greenfield; seams prontos (PPS, Imposto, moldes de porta, WORM Padrão B).
- P1 FECHADO (`e9f5799`): spec v1 recorte Wave A sobre PRD US-PRC-001..008.
- P2 FECHADO (`88cd519`): revisões tech-lead+advogado AMBAS APROVA COM CORREÇÕES; spec v2 stable.
- Emendas cross-doc P2→P3 APLICADAS (`dcb8621`): retencao-matriz, lgpd-rat, ADR-0081 emenda.
- Decisões Roldão batch (2026-06-12): dois modos de preço; alçadas 3 níveis; semáforo de margem.
- P3 FECHADO (2026-06-12): plan+tasks ready-for-implement (23 T-PRC; lock 880_404; 6 migrations;
  emenda modelo-de-dominio no P8). Fatia 1a FECHADA (47 testes puros; fingerprint via canonicalizador
  de DOMÍNIO — conserto orquestrador: domínio não importa infrastructure). **EM CURSO: Fatia 1b schema PG.**
- Docs em `docs/faseamento/precificacao/`.

## Frente AUDITORIA DE CERIMÔNIA — CONCLUÍDA E APLICADA (2026-06-12)

- R1..R22 aplicados em 5 commits: hooks→pré-commit (write-time só anti-desastre) + ritual reformado +
  fonte única denylist + conformidade→GATEs + REGRAS fatiada. Validado: test-runner completo verde.
- Relatório: `docs/faseamento/auditorias/AUDITORIA-CERIMONIA-rodada-1.md` (§8 decisão+aplicação).

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
