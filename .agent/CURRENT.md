# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente ATIVA — `orcamentos` Templates (T-ORC-039) — fecha o módulo 100% (2026-06-15)

- Núcleo de orçamentos FECHADO (ver abaixo). Resta **T-ORC-039**: REST `TemplateViewSet` (CRUD + gate
  selo RBC por perfil via hook — D-ORC-13 / AC-ORC-005). Entidade `Template` + tabela já existem; falta a
  camada REST + gate. Em seguida, varrer os GATEs rastreados na `matriz-reconciliacao.md` §8 por prioridade.

## Última frente FECHADA — `orcamentos` núcleo (Fatia 2 Ondas 2a–2f + P8/P9, 2026-06-15)

- Criar/itens/enviar/recusar/cancelar/expirar + análise crítica cl. 7.1 perfil-aware (fail-closed A) + link
  público 1-clique (SECURITY DEFINER) + conversão em OS (envelope por item ADR-0082). **Onda 2f:** família
  INV-ORC-* cravada em REGRAS + 3 hooks pré-commit + 4 testes regressão. **P8:** ADR-0083 (`PrecoResolvido`
  reconcilia VO `Preco`; emenda PRD) + `matriz-reconciliacao.md`. **P9:** 8 auditores roteados → 1 MÉDIO
  (INV-ORC-PRECO-001 sem teste) consertado causa-raiz + 2ª passada PASS → **8/8 PASS zero C/A/M** (INV-RITUAL-001).
  Commits `b002dae`(2f) · `cf12bc8`(P8). GATEs/débitos: ver `matriz-reconciliacao.md` §8. Detalhe: diário.

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md` · matriz: `docs/faseamento/orcamentos/matriz-reconciliacao.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
