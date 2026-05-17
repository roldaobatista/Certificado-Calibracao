---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-pagar
dominio: financeiro
---

# Contrato UI — Contas a Pagar

> Wave C. Rascunho — validar UX pós-discovery.

## Telas previstas

### TP-01 — Lista de contas a pagar

- Filtros: status, fornecedor, centro de custo, vencimento, valor
- Colunas: fornecedor, descrição, valor, vencimento, status, ações
- Status colorido: vermelho (vencido), laranja (vence hoje), amarelo (aguarda aprovação), verde (pago)
- Ações: "Aprovar", "Pagar", "Editar", "Cancelar"

### TP-02 — Novo lançamento

- Campos: fornecedor (busca + cadastro inline), descrição, valor, vencimento
- Anexar boleto/NF (PDF, imagem)
- Categoria (plano de contas — combobox com busca hierárquica)
- Centro de custo (combobox)
- Rateio (botão "Ratear em vários centros") — soma 100%
- Recorrência (mensal, fixa por N meses) — opcional
- Botão: "Salvar e enviar pra aprovação" / "Salvar rascunho"

### TP-03 — Aprovação

- Lista de pendentes do papel atual
- Ações: aprovar / rejeitar (com observação)
- Visão alçada: dono vê todos > R$ X; gerente vê do seu centro de custo

### TP-04 — Plano de contas

- Árvore expansível
- Edição: adicionar conta filha; renomear; desativar (não deletar — INV-008)
- Template padrão Aferê + botão "Importar do meu contador" (V2)

### TP-05 — Conciliação OFX (V2)

- Upload OFX
- Lista: extrato vs lançamentos a casar
- Sugestões de match por valor + data; confirmar 1 clique

## Mensagens visíveis

| Contexto | Mensagem |
|---|---|
| Aprovação pendente | "Aguardando aprovação de {dono/gerente}." |
| Possível duplicata | "Já existe lançamento parecido neste mês para {fornecedor}. Confirmar?" |
| Vencido | "Vencida há {N} dias." |
| Rateio inválido | "A soma dos percentuais precisa fechar em 100%." |

## Non-goals UI

- Editor visual de fluxo de aprovação complexo (alçadas simples no MVP-2).
- Importação massiva (V2).
- Dashboard "saúde do caixa" — vem do OP12.

## Referências

- `docs/comum/design-system.md` [INFERÊNCIA]
- `prd.md` deste módulo
