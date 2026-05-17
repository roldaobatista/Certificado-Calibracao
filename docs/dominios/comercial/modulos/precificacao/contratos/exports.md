---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
  - docs/dominios/financeiro/modulos/custeio-real/contratos/exports.md
---

# Contratos de Export — Módulo Precificação

> Formatos de saída específicos.

---

## Exports

### Export 1: Lista de tabelas e preços (CSV/XLSX)

**Propósito:** auditoria externa, análise em Excel, BI.
**Formato:** CSV + XLSX.
**Regulado?:** não.
**Campos obrigatórios:** tabela_id, versao, tipo, criterio_aplicacao, item_id, item_nome, preco_sugerido, preco_minimo, desconto_max_padrao, publicada_em.
**Imutabilidade pós-export:** versões publicadas são imutáveis (INV-026).
**Retenção:** vinculada a `retencao-matriz.md` (versões antigas mantidas pelo prazo fiscal mínimo).

---

### Export 2: Histórico de preço praticado (CSV/XLSX)

**Propósito:** análise de margem realizada, tendência por item/cliente/vendedor.
**Formato:** CSV + XLSX.
**Campos obrigatórios:** data_fechamento, item_id, item_nome, cliente_id (anonimizado se solicitado), vendedor_id, preco_aplicado, desconto_percentual, margem_realizada, regra_versao, tabela_versao.
**Anonimização:** opção de mascarar cliente_id para análises agregadas (LGPD).
**Retenção:** WORM — mantido pelo prazo fiscal (matriz em `docs/conformidade/comum/retencao-matriz.md`).

---

### Export 3: Relatório de aprovações de desconto (CSV/PDF)

**Propósito:** auditoria de governança (quem aprovou o quê).
**Formato:** CSV + PDF.
**Campos obrigatórios:** pedido_id, criado_em, vendedor, aprovador, desconto solicitado, decisão, justificativa, decidido_em.
**Imutabilidade:** sim — pedidos decididos não mudam.
**Retenção:** mínimo 5 anos (audit trail).

---

### Export 4: Snapshot de cálculo individual (JSON)

**Propósito:** consumido por outros módulos (`orcamentos`, `marketplace`) para carimbar o cálculo no documento emitido.
**Formato:** JSON estruturado (snapshot da entidade `CalculoPreco`).
**Imutabilidade:** sim — INV-026.
**Retenção:** vinculada ao documento que o consumiu (orçamento, OS, contrato).

---

### Export 5: Dashboard de margem — relatório executivo (PDF)

**Propósito:** relatório mensal para dono/diretoria.
**Formato:** PDF.
**Campos:** KPIs principais, ranking de itens deficitários, ranking de vendedores, tendência de margem, top descontos.
**Retenção:** gerado sob demanda.

---

## Exports inter-módulos

- `CalculoPreco` (JSON snapshot) → consumido por `orcamentos` (carimba no ItemOrcamento), `marketplace` (preço exibido), `contratos` (preço travado no contrato).
- `HistoricoPrecoPraticado` (alimentado por) `Orcamentos.OrcamentoFechado` → analisado por `analytics`.
- Ver `../../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export

- Mudança em colunas de CSV → ADR (quebra integração externa).
- Mudança em snapshot JSON → ADR + versão no payload (`schema_version`).

## Como esta lista evolui

- Export novo → adicionar.
- Mudança em formato → ADR.
- Export descontinuado → `@deprecated`.
