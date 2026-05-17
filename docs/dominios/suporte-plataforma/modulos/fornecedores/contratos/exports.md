---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fornecedores
dominio: suporte-plataforma
---

# Contratos de Export — Fornecedores

## Exports

### Export 1: Lista de fornecedores (XLSX/CSV)

**Propósito:** export gerencial.
**Formato:** XLSX preferencial / CSV.
**Regulado:** não.
**Campos:** CNPJ, razão, nome fantasia, categorias, status, score médio 12m, gasto total 12m, data homologação.

---

### Export 2: Comparativo de cotação (PDF)

**Propósito:** documentar decisão para auditoria interna.
**Formato:** PDF.
**Regulado:** não (auditoria interna apenas).
**Campos:** cabeçalho cotação, matriz fornecedores × itens, melhor preço destacado, fornecedor escolhido, justificativa, assinatura do comprador (Wave futura).

---

### Export 3: Pedido de compra (PDF)

**Propósito:** documento formal enviado ao fornecedor.
**Formato:** PDF.
**Regulado:** não (mas tem implicação contratual).
**Campos:** dados tenant, dados fornecedor, itens (item/qtd/preço unitário/total), condição de pagamento, prazo, valor total, observações, assinatura.
**Imutabilidade pós-envio:** sim — alterações após envio criam nova versão (similar a cotação).
**Retenção:** ver `docs/conformidade/comum/retencao-matriz.md`.

---

### Export 4: Histórico de preço por item (CSV / XLSX)

**Propósito:** análise comercial.
**Campos:** item, fornecedor, data_cotacao, preço, prazo, condição.

---

### Export 5: Relatório de avaliação de fornecedor (PDF)

**Propósito:** dossiê do fornecedor para reunião / decisão de renovação.
**Campos:** dados fornecedor, lista de pedidos 12m, avaliações por pedido, médias por dimensão (prazo/qualidade/preço), gráficos.

---

### Export 6: Relatório de gasto por fornecedor (XLSX)

**Propósito:** análise financeira / curva ABC.
**Campos:** fornecedor, n° pedidos, valor total, ticket médio, categoria, score.

---

## Exports inter-módulos

- Pedido de compra dispara evento consumido por **Financeiro** (contas a pagar futuro).
- Recebimento físico (do **Estoque**) dispara gatilho de avaliação aqui.
- Histórico de preço pode alimentar **Catálogo** (sugestão de atualização de preço-padrão — Wave futura).

## Versionamento

- Mudança de layout de PDF de pedido de compra → bump CHANGELOG; pedidos antigos mantêm layout original (snapshot).
- Mudança de colunas em CSV/XLSX → janela 6 meses.

## Como evolui

- Export novo → adicionar.
- Mudança em pedido de compra (layout/conteúdo) → ADR (impacta contratos com fornecedor).
