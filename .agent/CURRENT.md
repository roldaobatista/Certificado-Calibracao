# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `orcamentos` (P3 DONE → implementação) (2026-06-14)

- Dependência `os-multi-equipamento` FECHADA; envelope por item disponível. **P3 (spec v2+plan+tasks)
  revisado por `tech-lead`+`consultor-rbc` — APROVA COM CORREÇÕES, todas incorporadas.** Detalhe no plan.
- **Fatia 1a+1b DONE (2026-06-14):** domínio puro (45 testes) + schema PG `src/infrastructure/orcamentos/`
  (7 models + RLS v2 + WORM + 6 migrations + repos/mappers + `ACOES_ORCAMENTOS`). **Drill PG-real 20/20**
  (RLS UNHAPPY cross-tenant + WORM UPDATE/DELETE + constraints). Decisões: `item.versao` FK NOT NULL (sem
  `orcamento_id` — espelha entidade); `versao` congelamento one-shot; CHECK do outbox é SINTÁTICO →
  migration de CHECK desnecessária (não criada — REGRA #0). `get_link_por_token`/numeração SerieDocumento
  diferidos p/ Fatia 2.
- **Fatia 2 MAPEADA (2026-06-14):** briefing dos 12 seams + 3 decisões REGRA #0 em `tasks.md`
  (D-FATIA2-A numeração **BURACOS_ACEITOS** — Roldão pode pedir gap-less; D-FATIA2-B série provisionada
  **LAZY** — `serie_documento` vazia; D-FATIA2-C deps `calcular_precos` na view, use case fino).
- **PRÓXIMO = implementar Onda 2a** (`criar_orcamento` + `adicionar_item`/`editar_item` + view) → 2b transições
  → 2c aprovar c/ análise crítica cl.7.1 perfil-aware → 2d consumers → 2e REST público → 2f testes.
  Detalhe: `docs/faseamento/orcamentos/{spec,plan,tasks}.md`.

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
