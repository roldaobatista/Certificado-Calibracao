# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## Frente PRÓXIMA — `contas-receber` (Nível 5 — fecha a receita ponta a ponta)

- A cadeia de preço (config→pps→precificacao→colaboradores→orcamentos) está **COMPLETA**. Próxima peça do
  `plano-dependencia-sistema.md`: **`contas-receber`** — consome `OS.Concluida`/`Certificado.Emitido`/
  `Fiscal.NFSeEmitida` → `TituloEmitido` (fatura pelo valor JÁ carimbado no evento, não reconsulta preço);
  baixa via `PaymentGatewayProvider` (Asaas ADR-0050) — núcleo com **stub** (cost-plus/gateway real diferidos).
  Iniciar pelo ritual P0 (discovery/spec → revisões tech-lead/advogado → plan → tasks).

## Última frente FECHADA — `orcamentos` MÓDULO 100% Wave A (2026-06-15)

- Núcleo (Fatia 2 Ondas 2a–2f): criar/itens/enviar/recusar/cancelar/expirar + análise crítica cl. 7.1 perfil-
  aware (fail-closed A) + link público 1-clique (SECURITY DEFINER) + conversão em OS (envelope por item ADR-0082).
  **P8:** ADR-0083 (`PrecoResolvido` reconcilia VO `Preco`; emenda PRD). **P9:** 8 auditores → 1 MÉDIO
  (INV-ORC-PRECO-001 sem teste) consertado + 2ª passada PASS → 8/8 PASS. **T-ORC-039:** `TemplateViewSet` CRUD +
  gate selo RBC perfil A (INV-ORC-SELO-RBC + hook); produto MÉDIO (CHANGELOG) consertado. US Wave B: 003/006/010.
  Commits `b002dae`(2f)·`cf12bc8`(P8)·`24404ca`(P9). GATEs/débitos: `matriz-reconciliacao.md` §8. Detalhe: diário.

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md` · matriz: `docs/faseamento/orcamentos/matriz-reconciliacao.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
