# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente EM CURSO — #3 `precificacao` (parcial, stub custo)

- P0 FECHADO (`0f511d4`): greenfield; seams prontos (PPS, Imposto, moldes de porta, WORM Padrão B).
- P1 FECHADO (`e9f5799`): spec v1 recorte Wave A sobre PRD US-PRC-001..008.
- P2 FECHADO (`88cd519`): revisões tech-lead+advogado AMBAS APROVA COM CORREÇÕES; spec v2 stable.
- Emendas cross-doc P2→P3 APLICADAS (`dcb8621`): retencao-matriz, lgpd-rat, ADR-0081 emenda.
- Decisões Roldão batch (2026-06-12): dois modos de preço; alçadas 3 níveis; semáforo de margem.
- P3 FECHADO (2026-06-12): plan+tasks ready-for-implement (23 T-PRC; lock 880_404; emenda modelo-dominio no P8).
- Fatia 1a FECHADA (47 testes puros; fingerprint via canonicalizador de DOMÍNIO — conserto: domínio não importa infra).
- Fatia 1b FECHADA (7 tabelas RLS v2/WORM/exclusion/advisory 880_404; drill 31/31; 14 testes PG; migrate 7/7).
- **Fatia 2 FECHADA:** 11 E2E PG-real 11/11 verdes + 67 puros + ruff/mypy/hooks/makemigrations PASS.
  Correções: `serializar_regra`+`serializar_pedido` alias `regra_id`/`pedido_id`; `_pode_ver_margem`
  e `_derivar_papel_decisor` migrados para `DjangoAuthorizationProvider` (has_perm Django não usa
  authz_perfil_acao); migration 0009 expandida com `alcada_dono`/`alcada_gerente`; RLS context em
  query ORM do teste; `MARGEM_ALVO` exige `custo_referencia_em` (TL-PRC-07).
- **EM CURSO: Fatia 3 (P7 — INV-PRC em REGRAS + TestINV_PRC + 3 hooks no manifest pré-commit, T-PRC-050..052) → P8 → P9.**
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
