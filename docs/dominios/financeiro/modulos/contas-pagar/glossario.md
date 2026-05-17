---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-pagar
dominio: financeiro
---

# Glossário — Contas a Pagar

| Termo | Definição |
|---|---|
| **Conta a pagar** | Obrigação financeira do tenant com fornecedor/credor (boleto recebido, fatura, salário, imposto). |
| **Fornecedor** | Pessoa/empresa que vendeu produto/serviço ao tenant; vem de `suporte-plataforma/fornecedores`. |
| **Plano de contas** | Hierarquia de categorias contábeis (1.x receita, 2.x custo, 3.x despesa, 4.x...). |
| **Centro de custo** | Agrupamento gerencial (filial, equipe, projeto) usado pra distribuir despesas. |
| **Conta sintética** | Pai na hierarquia; soma das analíticas. |
| **Conta analítica** | Folha onde lançamento ocorre. |
| **Lançamento** | Operação financeira a pagar com data, valor, categoria, centro de custo. |
| **Fluxo de aprovação** | Sequência de papéis que precisam aprovar antes de pagar (gerente → financeiro → dono). |
| **Anexo** | Boleto/NF/contrato anexado ao lançamento. |
| **Rateio** | Distribuição de um lançamento em múltiplos centros de custo. |
| **Pagamento programado** | Lançamento agendado pra débito automático ou pix programado. |
| **Conta bancária** | Conta do tenant da qual o pagamento sai. |
| **Conciliação ativa** | Casamento de pagamento efetuado com extrato bancário (espelho de contas a receber). |
| **DDA** | Débito Direto Autorizado — boleto chega via banco do tenant. Non-goal MVP. |

## Status do módulo

**Wave C / Pós-MVP-1** — gap consciente. README do domínio: "contas a pagar + DRE + fluxo projetado são gaps de MVP-1". Doc inicial pra registrar decisão e ancorar discovery posterior.

## Referências

- `docs/dominios/financeiro/README.md`
- `docs/dominios/suporte-plataforma/modulos/fornecedores/`
- BIG-08 (caixa do técnico — paralelo, não substituto)
