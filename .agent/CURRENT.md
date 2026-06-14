# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `orcamentos` (P3 DONE → implementação) (2026-06-14)

- Dependência `os-multi-equipamento` FECHADA; envelope por item disponível. **Spec v2 + plan + tasks prontos (P3).**
- Revisão do plan: `tech-lead` + `consultor-rbc` **APROVA COM CORREÇÕES** — todas incorporadas (CRIT-1
  `ACOES_ORCAMENTOS` lowercase no bus; ALTO-1/2 casamento `handle_os_aberta`+reuso resolver anti-N+1;
  análise crítica cl.7.1: `itens_avaliados` ricos C1 + confirmação de ressalva cl.7.1.1-d C2/C3).
- **Fatia 1a+1b DONE (2026-06-14):** domínio puro (45 testes) + schema PG `src/infrastructure/orcamentos/`
  (7 models + RLS v2 + WORM + 6 migrations + repos/mappers + `ACOES_ORCAMENTOS`). **Drill PG-real 20/20**
  (RLS UNHAPPY cross-tenant + WORM UPDATE/DELETE + constraints). Decisões: `item.versao` FK NOT NULL (sem
  `orcamento_id` — espelha entidade); `versao` congelamento one-shot; CHECK do outbox é SINTÁTICO →
  migration de CHECK desnecessária (não criada — REGRA #0). `get_link_por_token`/numeração SerieDocumento
  diferidos p/ Fatia 2.
- **PRÓXIMO = Fatia 2** (use cases + consumers + REST: criar/adicionar-item/enviar/aprovar c/ análise crítica
  cl.7.1 perfil-aware/recusar/cancelar + `handle_os_aberta` + REST público token). Detalhe:
  `docs/faseamento/orcamentos/{spec,plan,tasks}.md`.

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
