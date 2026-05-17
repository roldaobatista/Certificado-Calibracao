---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: produtos-pecas-servicos
dominio: suporte-plataforma
---

# PRD — Módulo Catálogo (Produtos / Peças / Serviços / Kits)

## 1. O que este módulo é

Catálogo central do tenant. Cadastra itens vendidos/usados na operação: **produtos** (venda direta), **peças** (consumidas em OS), **serviços** (cobrados sem baixar estoque) e **kits** (agrupamentos). Define preço vigente com versionamento (INV-026 — preço não-retroativo) e unidade de medida. **Status:** gap MVP-1 → MVP-2.

## 2. Por que existe

- BIG-12 (estoque rastreável precisa de SKU canônico)
- Gap discovery: sem catálogo central, OS lança item "à mão" → inconsistência de preço, perda de histórico.
- Preparação para faturamento (Financeiro precisa de linha de catálogo).

## 3. Personas

Ver `personas.md` + `../../personas.md` (P-SUP-01 almoxarife, P-SUP-03 comprador, P-COM-* atendente, P-OP-01 técnico).

## 4. Escopo (o que ESTÁ)

- CRUD de item (produto, peça, serviço, kit)
- Atributos: nome, código interno, código fabricante, descrição, UM, controla-estoque (flag), categoria
- Preço vigente com versionamento (INV-026)
- Composição de kit (lista de itens + quantidade)
- Status ativo/inativo (sem exclusão dura — preserva histórico)
- Importação inicial via planilha (CSV/XLSX) com aceite por linha

## 5. Non-goals

- NÃO controla saldo de estoque (vai pra módulo Estoque)
- NÃO emite NF (Financeiro)
- NÃO faz cotação com fornecedor (Fornecedores)
- NÃO calcula custo médio ponderado (Estoque)
- NÃO trata tabela de preço multi-canal V1 (MVP-2 wave inicial é tabela única)

## 6. User Stories

### US-CAT-001: Cadastrar peça

**Como** almoxarife, **quero** cadastrar uma peça nova com preço, **para** usar em OS.

- **AC-CAT-001-1**: GIVEN tipo=peça, WHEN preencho nome + código + UM + preço + controla-estoque=true, THEN item é salvo com preço vigente a partir de hoje.
- **AC-CAT-001-2**: GIVEN tento salvar com código duplicado no tenant, THEN erro 409 PT "código já existe".

**Invariantes:** `INV-026`.

### US-CAT-002: Atualizar preço sem afetar histórico

**Como** comprador, **quero** atualizar preço de peça, **para** refletir alta do fornecedor.

- **AC-CAT-002-1**: GIVEN item com preço R$ 50 vigente desde 2026-01-01, WHEN cadastro novo preço R$ 55 a partir de 2026-06-01, THEN nova versão é criada; OS abertas antes de 2026-06-01 continuam com R$ 50.
- **AC-CAT-002-2**: GIVEN OS aberta hoje, WHEN consulto preço, THEN sistema retorna preço com `data_referencia=hoje` (INV-026).

**Invariantes:** `INV-026`.

### US-CAT-003: Criar kit

**Como** atendente, **quero** criar um kit (ex: "manutenção preventiva"), **para** simplificar lançamento em OS.

- **AC-CAT-003-1**: GIVEN seleciono 3 peças + 1 serviço com quantidades, WHEN salvo kit, THEN kit é criado com preço = soma das partes OU preço manual.

### US-CAT-004: Importar catálogo via planilha

**Como** Roldão (onboarding), **quero** importar 500 itens via planilha, **para** começar a operar.

- **AC-CAT-004-1**: GIVEN planilha XLSX com colunas mapeadas, WHEN importo, THEN sistema valida linha-a-linha + permite aceite/rejeição por linha.

### US-CAT-005: Inativar item

**Como** comprador, **quero** inativar peça obsoleta, **para** parar de aparecer em OS nova.

- **AC-CAT-005-1**: GIVEN item ativo, WHEN inativo, THEN OS abertas continuam funcionando; OS nova não consegue selecionar.

## 7. Métricas

Ver `metricas.md`.

## 8. NFR

- Performance: lista p95 ≤ 1s
- Importação 500 linhas ≤ 30s
- Segurança: edição requer permissão `catalogo:edit`

## 9. Glossário

Ver `glossario.md`.
