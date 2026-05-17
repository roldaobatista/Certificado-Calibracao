---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-pagar
dominio: financeiro
---

# Modelo de Domínio — Contas a Pagar

> Wave C. Modelo provisório; refinar pós-discovery.

## Agregados previstos

### `Lancamento` (raiz)

Atributos:
- `id`, `tenant_id`, `fornecedor_id`, `descricao`
- `valor`, `data_emissao`, `data_vencimento`, `data_pagamento`
- `conta_analitica_id` (plano de contas), `centro_custo_id`
- `status`: `rascunho` | `aguardando-aprovacao` | `aprovado` | `pago` | `cancelado`
- `anexos[]` (boleto, NF, comprovante)
- `rateio[]` (subentidade — centros de custo + percentuais)
- `aprovacoes[]` (cadeia de aprovação)

### `PlanoDeContas` (entidade por tenant)

Árvore. Cada nó: `codigo` (1.2.3), `nome`, `tipo` (sintética/analítica), `pai_id`.

Template padrão Aferê (pra calibração): receita serviço calibração / receita venda peça / custo peça / despesa aluguel / despesa pessoal / despesa frota / despesa marketing / impostos / [INFERÊNCIA — refinar com contador].

### `CentroDeCusto` (entidade por tenant)

Lista plana (não-hierárquico no MVP-2). Ex: matriz, filial-X, equipe-comercial, projeto-cliente-Y.

### `ContaBancaria`

`id`, `tenant_id`, `banco`, `agencia`, `conta`, `tipo` (corrente/poupança/PIX).

### `Pagamento` (entidade evento)

Igual a Contas a Receber: imutável; data, valor, origem (manual/OFX/Pluggy), comprovante.

## Regras de negócio

- Lançamento > alçada não pode ser pago sem aprovação completa.
- Rateio: soma dos percentuais = 100%.
- Plano de contas: lançamento sempre em conta analítica.
- Mesma chave (fornecedor + valor + mês) detectada → alerta duplicata (não bloqueia).
- INV-008: audit log de toda mudança.

## Eventos emitidos

- `LancamentoCriado`
- `LancamentoAprovado`
- `Pagamento(lancamento_id, valor, data)`
- `LancamentoCancelado`

## Eventos consumidos

- Webhook Open Finance (V2): pagamento efetuado dispara baixa
- OFX importado: concilia
- (Não consome eventos de OS — contas a pagar é desacoplado da operação)

## Non-goals

- Folha de pagamento (RH)
- Apuração contábil completa (contador externo)
- Cálculo de imposto a pagar
- DDA bancário

## Invariantes

INV-008 (audit). Demais a definir pós-discovery.

## Dependências

- Fornecedores (`suporte-plataforma/modulos/fornecedores/`)
- Pluggy/Belvo (V2)

## Referências

- `docs/comum/integracoes-externas/pluggy-belvo.md`
- `docs/dominios/financeiro/README.md`
