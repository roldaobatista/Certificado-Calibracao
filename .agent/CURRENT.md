# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `orcamentos` (Fatia 2 em curso) (2026-06-15)

- Fatias 1a (domínio) + 1b (schema PG) DONE. Dep `os-multi-equipamento` FECHADA (envelope por item).
  Decisões Fatia 2 em `tasks.md`: D-FATIA2-A numeração BURACOS_ACEITOS · B série LAZY · C deps na view.
- **Ondas 2a/2b/2c-1 DONE:** criar+itens+`OrcamentoViewSet` · enviar/recusar/cancelar/expirar (outbox,
  LinkPublico 256b) · item de calibração DECLARA mensurando (migration 0008 + CHECK + fail-fast).
- **Onda 2c-2 DONE (`243ce69`):** motor análise crítica cl. 7.1 + `aprovar_orcamento` — função PURA
  `decidir_analise_critica` (matriz A/B/C/D + indeterminado fail-closed) + portas CMC/proc + perfil
  server-side + action REST (200→`aprovado_pendente_os` / 422 reprova+WORM) + snapshot_hash ADR-0029.
  Camada A 7 PASS + `consultor-rbc` CONFIRMA-COM-AJUSTES (ACH-3 MÉDIO corrigido).
- **Onda 2d DONE (2026-06-15):** consumers `handle_os_aberta` (T-ORC-035: fecha saga →convertido + publica
  `orcamento.convertido`; OS avulsa=no-op) + `handle_cliente_anonimizado` (T-ORC-036/LGPD: rascunho cancela,
  **enviado EXPIRA** [decisão Roldão], aprovado+ preserva; revoga link; `cliente.dados_anonimizados` dormente
  =GATE-ANON-EVENTO-RECONCILIAR). Camada A 7 PASS zero MÉDIO+. **128 testes verdes**.
- **PRÓXIMO = Onda 2e** REST público (`OrcamentoPublicoView` T-ORC-038: GET `{token}` ressalvas + POST aprovar
  1-clique, token resolve tenant D-ORC-19, Aprovacao WORM aceite rico, `ressalvas_confirmadas` se `com_ressalva`)
  → 2f testes contrato/INV (T-ORC-050..054) → P8/P9. GATEs Onda 2d: PERF-APROVAR · OBS-METRICA · ANON-BULK.

## Última frente FECHADA — `os-multi-equipamento` (2026-06-14, ADR-0082)

- Retrofit OS 1→N equipamentos + `ItemComercialOS`. P0→P9 (7 auditores, 2ª passada 4/4 PASS). 96 verdes.
  Débitos: **GATE-OSME-RECEBIMENTO-7.5** · **GATE-OS-AUTHZ-ACTION-MAP** (pré-existente). Detalhe: diário.

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
