---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: produtos-pecas-servicos
dominio: suporte-plataforma
---

# Contratos de Export — Catálogo

## Exports

### Export 1: Catálogo completo (XLSX/CSV)

**Propósito:** export gerencial para auditoria, backup, migração.
**Formato:** XLSX (preferencial) / CSV.
**Regulado:** não.
**Campos obrigatórios:** código, nome, tipo, UM, categoria, controla-estoque, preço vigente, status, criado_em.
**Campos opcionais:** descrição, código fabricante, snapshot completo de versões.
**Filtros:** mesmos da Tela 1.

**Exemplo (CSV):**
```
codigo,nome,tipo,um,preco_vigente,status
PEC-001,"Bateria 9V",peca,un,12.50,ativo
```

---

### Export 2: Histórico de preços do item (CSV)

**Propósito:** auditoria de variação de preço (regulatório fiscal interno).
**Formato:** CSV.
**Regulado:** não (mas alimenta export fiscal — ver `docs/conformidade/comum/fiscal.md`).
**Campos:** item_código, versao_n, preco, vigente_de, vigente_ate, autor, motivo.

---

### Export 3: Template de importação (XLSX)

**Propósito:** modelo para o tenant preencher e importar via Tela 4.
**Formato:** XLSX com colunas mapeadas e exemplos.
**Campos:** os mesmos do cadastro + coluna "OBSERVAÇÕES" para erros.

---

### Export 4: Kit detalhado (PDF)

**Propósito:** imprimir/enviar composição de kit pra cliente em proposta.
**Formato:** PDF.
**Regulado:** não.
**Campos:** kit_nome, composição (item + quantidade + UM + preço unitário), preço total.

---

## Exports inter-módulos

- Lista de itens consumida por **Estoque** (saldo por item) — via API.
- Lista de itens consumida por **OS** (Operação) — via API com `data_referencia`.
- Histórico de preço alimenta auditoria fiscal — via API ou export CSV.

## Versionamento

- Mudança de colunas no export → bump CHANGELOG + janela 6 meses.
- Template de importação versionado (`v1`, `v2`) com header marcando versão.

## Como evolui

- Export novo → adicionar.
- Mudança de schema → coordenar com integradores (Estoque, OS).
