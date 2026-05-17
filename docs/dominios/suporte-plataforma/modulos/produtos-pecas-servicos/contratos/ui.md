---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: produtos-pecas-servicos
dominio: suporte-plataforma
---

# Contratos de UI — Catálogo

## Telas

### Tela 1: Lista de itens

**Propósito:** listar / buscar item do catálogo.
**Persona:** comprador, almoxarife, atendente.
**US:** US-CAT-001, US-CAT-005.

**Elementos:**
- Busca (nome, código)
- Filtros: tipo (produto/peça/serviço/kit), status, categoria
- Botão "novo item", "importar planilha"
- Tabela: código, nome, tipo, UM, preço vigente, status

**Estados:**
- Vazio: "catálogo vazio — cadastrar primeiro item ou importar planilha"

---

### Tela 2: Cadastro / Edição de item

**Propósito:** criar ou editar item.
**US:** US-CAT-001, US-CAT-002.

**Elementos:**
- Tipo (radio): produto / peça / serviço
- Campos: nome, código, descrição, UM, categoria, controla-estoque (checkbox)
- Bloco preço: preço atual + "alterar preço" (abre data de vigência futura)
- Botão "salvar"

**Estados:**
- Edição com OS aberta usando este item: aviso "alterações em preço criarão nova versão; OS abertas mantêm preço atual" (INV-026).
- Erro 422 INV-026: "não é possível alterar versão de preço existente; crie nova versão".

---

### Tela 3: Cadastro de kit

**Propósito:** montar kit.
**US:** US-CAT-003.

**Elementos:**
- Campos: nome, código, descrição
- Tabela de composição: adicionar item filho + quantidade + UM
- Preço: soma calculada (read-only) OU manual (toggle)
- Botão "salvar"
- Erro: kit dentro de kit → "não é permitido kit dentro de kit".

---

### Tela 4: Importação de planilha

**Propósito:** importar catálogo inicial.
**US:** US-CAT-004.

**Elementos:**
- Upload XLSX/CSV
- Mapeamento de colunas (auto-detect + ajuste manual)
- Pré-visualização linha-a-linha com erros marcados
- Botões: "aceitar todas válidas", "rejeitar selecionadas", "importar"

**Estados:**
- Erro: "linha 12 — código duplicado", "linha 25 — UM inválida".

---

### Tela 5: Histórico de preços do item

**Propósito:** ver versões de preço.
**Elementos:** tabela com versão, vigente_de, vigente_ate, preço, motivo, autor.

---

## Acessibilidade

WCAG AA. Teclado obrigatório.

## Mobile

Responsivo. Consulta no mobile (ver ADR-0003).

## Como evolui

- Tela nova → linkar US.
