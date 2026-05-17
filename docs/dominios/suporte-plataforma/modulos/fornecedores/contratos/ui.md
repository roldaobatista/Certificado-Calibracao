---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fornecedores
dominio: suporte-plataforma
---

# Contratos de UI — Fornecedores

## Telas

### Tela 1: Lista de fornecedores

**Propósito:** localizar e ver status.
**US:** US-FOR-001.
**Elementos:** busca (CNPJ/razão), filtros (categoria, status), tabela (razão, CNPJ, categorias, score, status), ação "novo fornecedor".

**Estados:** vazio "nenhum fornecedor cadastrado ainda".

---

### Tela 2: Cadastro / Edição de fornecedor

**US:** US-FOR-001.
**Elementos:**
- Aba "Dados": CNPJ (com lookup automático via Receita — [INFERÊNCIA] V2), razão, nome fantasia, categorias (multi-select), condição de pagamento, dados bancários
- Aba "Contatos": lista CRUD
- Aba "Documentos": upload checklist (contrato social, certidões, comprovante bancário)
- Aba "Histórico": gasto total, score, avaliações
- Botão "homologar" disponível quando docs completos

**Erros:** "CNPJ inválido", "CNPJ já cadastrado".

---

### Tela 3: Nova cotação

**US:** US-FOR-002.
**Elementos:**
- Seleção de itens (com qtd e observação)
- Seleção de fornecedores (lista filtrada por categoria)
- Prazo de resposta (default 7 dias)
- Canal de envio: e-mail / WhatsApp / ambos
- Botão "enviar cotação"

---

### Tela 4: Comparativo de cotação

**US:** US-FOR-003.
**Elementos:**
- Cabeçalho: cotação + itens + prazo
- Tabela: linhas = itens; colunas = fornecedores; cada célula mostra preço + prazo + condição
- Melhor preço por linha em destaque verde
- Botão "escolher fornecedor X" por coluna
- Modal de justificativa quando escolhe NÃO menor preço (categoria + texto)

**Estados:** "fornecedor Y não respondeu" → célula vazia + ícone aviso.

---

### Tela 5: Resposta de cotação (público — fornecedor)

**Acessível por:** token único no link.
**Elementos:**
- Cabeçalho com nome do tenant + itens pedidos
- Por item: preço unitário, prazo (dias), condição pagamento, observação
- Total calculado
- Botão "enviar resposta"
- Sem login Aferê (token-only).

**Estados:**
- Token expirado: "esta cotação expirou em DD/MM/AAAA" (410 Gone)
- Já respondida: bloqueia nova submissão; permite ver o que enviou.

---

### Tela 6: Pedido de compra

**US:** US-FOR-004.
**Elementos:** dados do pedido (puxa da cotação escolhida), botão "enviar ao fornecedor" (gera PDF + e-mail), status atual.

---

### Tela 7: Avaliação pós-entrega

**US:** US-FOR-005.
**Acessível por:** alerta após recebimento total no Estoque.
**Elementos:** 3 sliders (prazo, qualidade, preço — 0-10) + campo comentário.

---

### Tela 8: Histórico de preço

**US:** US-FOR-006.
**Elementos:** seleciona item; gráfico de linha por fornecedor ao longo do tempo; tabela de cotações/pedidos.

---

## Acessibilidade

WCAG AA. Tela 5 (resposta pública) deve funcionar em mobile.

## Mobile

Responsivo. Avaliação tem versão mobile.

## Como evolui

- Tela nova → linkar US.
