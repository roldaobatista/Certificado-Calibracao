# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `orcamentos` (Fatia 2 em curso) (2026-06-15)

- Fatias 1a (domínio) + 1b (schema PG) DONE. Dep `os-multi-equipamento` FECHADA (envelope por item).
  Decisões Fatia 2 em `tasks.md`: D-FATIA2-A numeração BURACOS_ACEITOS · B série LAZY · C deps na view.
- **Ondas 2a+2b+2c-1 DONE:** criar+itens+`OrcamentoViewSet` · enviar/recusar/cancelar/expirar (eventos
  outbox, LinkPublico token 256b) · item de calibração DECLARA mensurando (migration 0008 + CHECK + fail-fast).
- **Onda 2c-2 DONE (2026-06-15):** motor análise crítica cl. 7.1 + `aprovar_orcamento`. Função PURA
  `decidir_analise_critica` (matriz A/B/C/D + indeterminado fail-closed) + `aprovacao.py` (use case) +
  `analise_critica_ports.py` (portas CMC/proc + perfil/suspensão server-side) + action REST `aprovar`
  (200 aprova → `aprovado_pendente_os` / 422 reprova+WORM). snapshot_hash ADR-0029; eventos
  reprovada/com_ressalva/aprovado. Camada A: 7 auditores PASS + `consultor-rbc` CONFIRMA-COM-AJUSTES
  (ACH-3 MÉDIO redação suspensão CORRIGIDO; ACH-1+fingerprint BAIXO corrigidos; ACH-2/4 + GATE-ORC-PERF-APROVAR
  + GATE-OBS-ORC-METRICA-APROVACAO em `tasks.md`). **121 testes verdes** no módulo.
- **PRÓXIMO = Onda 2d** (consumers `handle_os_aberta` T-ORC-035 + `handle_cliente_anonimizado` T-ORC-036)
  → 2e REST público (`OrcamentoPublicoView` T-ORC-038: GET ressalvas + POST aprovar 1-clique, Aprovacao WORM,
  `ressalvas_confirmadas` quando `com_ressalva`) → 2f testes contrato/INV (T-ORC-050..054) → P8/P9.

## Última frente FECHADA — `os-multi-equipamento` (2026-06-14)

- Retrofit OS 1→N equipamentos (equip. por atividade) + `ItemComercialOS`. Aditivo/reversível. ADR-0082.
  Ritual P0→P9 (P9: 7 auditores → 2ª passada 4/4 PASS). Regressão OS **96 verdes**.
- Débitos: **GATE-OSME-RECEBIMENTO-7.5** (enforcement recebimento por atividade) · **GATE-OS-AUTHZ-ACTION-MAP**
  (`os.atualizar` não seedado em reagendar/transferir/cancelar/dispensa/reabrir — bug pré-existente).
  Detalhe: `matriz-reconciliacao.md` (ata P9) + `docs/faseamento/diario/`.

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
