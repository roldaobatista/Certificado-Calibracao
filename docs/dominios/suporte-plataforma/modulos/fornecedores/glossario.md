---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fornecedores
dominio: suporte-plataforma
---

# Glossário — Fornecedores

> Específico do módulo. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Fornecedor | Empresa que vende peça/equipamento/serviço pro tenant | "vendor" cru, "supplier" cru | Cadastro de empresa fornecedora | OP14 |
| Categoria de fornecedor | Tipo: peça / equipamento / serviço / calibração externa | "tipo" só | Filtro de busca | OP14 |
| CNPJ do fornecedor | CNPJ raiz da empresa fornecedora | "documento" só | Identificador fiscal | OP14 |
| Contato do fornecedor | Pessoa responsável (vendedor, gerente) | "responsável" só | Linha de contato cadastrada | OP14 |
| Cotação | Solicitação de preço para um conjunto de itens | "pedido de preço" | Documento que vai pra ≥1 fornecedor | OP14 |
| Cotação em paralelo | Mesma cotação enviada simultaneamente a múltiplos fornecedores | "RFQ" cru | Comparativo lado-a-lado | OP14 |
| Resposta de cotação | Preço + prazo + condições retornados pelo fornecedor | "proposta" só | Linha do comparativo | OP14 |
| Comparativo de cotação | Tela com colunas por fornecedor + linhas por item | "matriz" só | Quadro decisório | OP14 |
| Pedido de compra | Documento que formaliza compra do fornecedor escolhido | "PO" cru | Compromisso de compra | OP14 |
| Avaliação de fornecedor | Nota dada após entrega (prazo, qualidade, preço) | "rating" cru | Score histórico | OP14 |
| Histórico de preço | Linha do tempo de preços por (fornecedor, item) | "log de preço" só | Tela de análise comercial | OP14 |
| Status do fornecedor | Ativo / inativo / bloqueado / em homologação | "estado" só | Filtro de listagem | OP14 |
| Homologação | Processo de aprovação inicial antes de virar fornecedor ativo | "qualificação" só | Etapa pré-cadastro completa | OP14 |

---

## Como evolui

- Termo novo → checar conflito.
- Descontinuado → `@deprecated` + janela 3 meses.
