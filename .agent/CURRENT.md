# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `orcamentos` (P3 DONE → implementação) (2026-06-14)

- Dependência `os-multi-equipamento` FECHADA; envelope por item disponível. **Spec v2 + plan + tasks prontos (P3).**
- Revisão do plan: `tech-lead` + `consultor-rbc` **APROVA COM CORREÇÕES** — todas incorporadas (CRIT-1
  `ACOES_ORCAMENTOS` lowercase no bus; ALTO-1/2 casamento `handle_os_aberta`+reuso resolver anti-N+1;
  análise crítica cl.7.1: `itens_avaliados` ricos C1 + confirmação de ressalva cl.7.1.1-d C2/C3).
- **Fatia 1a DONE (2026-06-14):** domínio puro `src/domain/comercial/orcamentos/` (8 arquivos: enums,
  value_objects c/ Desconto+CondicoesPagamento, entities, erros, repository Protocols, transicoes c/ máquina
  de estados + tradução enum D-ORC-16 + `montar_envelope` casando com consumer OS). Dinheiro VO em todos os
  valores (corrigi desvio do subagente: era int/Decimal misto). 45 testes verdes; ruff/mypy limpos.
- **PRÓXIMO = Fatia 1b** (schema PG: 7 models + RLS + WORM + ACOES_ORCAMENTOS/migration CHECK) →
  2 use cases/REST → 3 INVs → P8/P9. Detalhe: `docs/faseamento/orcamentos/{spec,plan,tasks}.md`.

## Última frente FECHADA — `os-multi-equipamento` (2026-06-14)

- Retrofit cirúrgico OS 1→N equipamentos (equipamento por ATIVIDADE) + `ItemComercialOS` (deslocamento/taxa) +
  recebimento por instrumento (estrutura). Aditivo/reversível. ADR-0082.
- Ritual P0→P9. Fatias 1a/1b/1c/2/2-leitura(T-OSME-035)/3 DONE. **P9:** 7 auditores → 4 c/ MÉDIO+ →
  consertos causa-raiz → 2ª passada 4/4 PASS (INV-RITUAL-001 ok, zero C/A/M).
- **GATE VERMELHO** da regressão (use case `abrir_os_via_orcamento` documentava fallback header→item mas não
  implementava — só o consumer) RESOLVIDO (fallback movido p/ use case). Regressão módulo OS: **96 verdes**.
- Débitos rastreados: **GATE-OSME-RECEBIMENTO-7.5** (enforcement recebimento por atividade — app `equipamentos`);
  **GATE-OS-AUTHZ-ACTION-MAP** (`os.atualizar` nunca seedado em reagendar/transferir/cancelar/dispensa/reabrir —
  bug pré-existente fora do escopo; `criar` já corrigido p/ `os.adicionar_atividade`). BAIXOs lote (R10):
  try/finally migration 0021, `correlation_id` ad-hoc em eventos OS. Detalhe: `matriz-reconciliacao.md` (ata P9).

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
