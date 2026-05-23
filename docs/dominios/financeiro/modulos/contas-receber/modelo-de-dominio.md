---
owner: Roldão
revisado-em: 2026-05-23
status: draft
modulo: contas-receber
dominio: financeiro
---

# Modelo de Domínio — Contas a Receber

## Agregados

### `Fatura` (raiz de agregado)

Documento que agrupa itens cobráveis (OSs, contratos) em um único cliente.

Atributos:
- `id`, `tenant_id`, `cliente_id`, `numero_sequencial_tenant`
- `data_emissao`, `valor_bruto`, `valor_liquido` (após descontos)
- `origem`: `os` | `contrato-recorrente` | `manual`
- `status`: `rascunho` | `emitida` | `parcialmente-paga` | `paga` | `cancelada`
- `itens[]`: referência a OS, **`AtividadeDaOS`** (ADR-0051 — permite faturamento parcial por atividade concluída) ou linha de contrato
- `categoria_receita` (enum: `CALIBRACAO_RBC | CALIBRACAO_NAO_RBC | MANUTENCAO_CORRETIVA | MANUTENCAO_PREVENTIVA | PECA_REVENDA | DESLOCAMENTO | OUTROS` — A-FIN-002; preenchido na geração com base no tipo da `AtividadeDaOS` de origem)

### `Titulo` (raiz separada)

Cobrança individual emitida a partir da fatura.

Atributos:
- `id`, `fatura_id`, `tenant_id`, `cliente_id`
- `valor_original`, `valor_atualizado` (com juros/multa)
- `data_emissao`, `data_vencimento`, `data_baixa`
- `meio`: `boleto` | `pix` | `pix_recorrente` | `cartao` | `cartao_recorrente` (ADR-0050)
- `gateway_externo_id` (nullable até gateway responder)
- `convenio_pix_id` (NOT NULL quando `meio=pix_recorrente` — INV-FIN-GW-002)
- `linha_digitavel` / `qr_code` / `tx_id`
- `status`: `aberto` | `pago` | `parcialmente-pago` | `vencido` | `cancelado` | `em-disputa`
- `regra_juros_id`, `regra_multa_id`, `regra_desconto_id`

### `Parcela` (subentidade do Título)

Quando título é parcelado. Cada parcela tem `valor`, `vencimento`, `status` próprios.

### `Pagamento` (entidade de evento)

Registro imutável de baixa. Atributos: `titulo_id`, `valor`, `data`, `origem` (`webhook-gateway`, `ofx`, `manual`, `pix-direto`), `comprovante_url`, `audit`, `valor_atualizado_snapshot_em_pagamento` (Decimal — M-FIN-002 — snapshot do `Titulo.valor_atualizado` no momento da baixa, fotografa juros+multa aplicados naquele instante).

## Regras de negócio

- **Juros/multa/desconto** aplicados na leitura (`valor_atualizado` calculado on-the-fly conforme data atual) — nunca persistir valor inflado, persiste regra.
- **Idempotência**: webhook gateway com mesmo `tx_id` aplicado 2× = 1 pagamento.
- **Cancelamento** só permitido se `status = aberto` E sem pagamento parcial.
- **Baixa parcial**: divide saldo restante em novo título sucessor (configurável).
- **INV-026**: alterar tabela de preço não recalcula títulos já emitidos.

## Eventos emitidos

> **Nomenclatura canônica** (ver `docs/comum/integracoes-inter-modulos.md` §Padrão): prefixo `ContasReceber.*`.

- `ContasReceber.TituloEmitido(titulo_id, valor, cliente_id, vencimento)`
- `ContasReceber.BoletoGerado(titulo_id, linha_digitavel)`
- `ContasReceber.Pago(titulo_id, valor, data, origem)` → consumido por Comercial (timeline 360°), Comissões (gatilho OP4), Fiscal (gatilho opcional NFS-e)
- `ContasReceber.TituloVencido(titulo_id, dias_atraso)` → consumido por régua de cobrança (Wave B), Portal Cliente
- `ContasReceber.TituloCancelado(titulo_id, razao)`
- `ContasReceber.DescontoAplicado(titulo_id, valor, motivo: penalidade_sla|nota_credito_bonificacao|manual)` → consumido por auditoria, BI

**Compatibilidade transitória:** aliases legados `TituloEmitido`/`Pago`/`BoletoGerado` aceitos durante Wave A (consumers antigos ainda escutam); auditor schema-version bloqueia novos handlers em aliases.

## Consumers (deste módulo) — GATE-CLI-6 / INV-FIN-REATIV-001

- **`ContasReceber.Pago`** (auto-consumido neste módulo) → quando título é a **última fatura vencida** do cliente bloqueado por inadimplência (INV-INT-010), o consumer publica `Cliente.Desbloqueado(motivo=pagamento_quitou)` em ≤5min. Em caso de pagamento parcial onde ainda existe fatura vencida em aberto, o bloqueio é mantido.
- **Diferenciação tenant vs cliente do tenant — INV-FIN-INAD-001:** inadimplência do CLIENTE do tenant usa `Cliente.bloqueado` (INV-INT-010); inadimplência do TENANT (billing-saas) usa `BillingSaas.TenantSuspenso` (INV-INT-009). Os dois nunca cruzam.

## Eventos consumidos

- `OS.Concluida` (Operação) → gera fatura + título
- `AtividadeDaOS.Concluida` (ADR-0051) → gera fatura parcial quando flag de faturamento por atividade ativa
- `Contrato.Renovado` (Comercial) → gera título recorrente
- `Marketplace.PagamentoConfirmado` (Comercial/marketplace) → cria título já liquidado (registra recebimento) + publica `ContasReceber.TituloEmitido` + `ContasReceber.Pago` na mesma transação
- `SLA.PenalidadeCalculada` (Comercial/sla-contratual) → cria desconto/multa em título aberto do cliente (ou nota de crédito se não houver título)
- `SLA.BonificacaoCalculada` (Comercial/sla-contratual) → cria nota de crédito a favor do cliente (abate próximo título ou vira saldo)
- `BillingSaas.FaturaPaga` (Financeiro/billing-saas) — consumido por `relatorios-financeiros/` (não por este módulo; mantido aqui só pra cross-reference)
- Webhook gateway → emite `ContasReceber.Pago`

## Non-goals do modelo

- Não modela antecipação/factoring (Wave B/V2).
- Não modela conta corrente do cliente (saldo agregado) — Wave B/V2.
- Não modela protesto/cartório.

## Invariantes

- INV-026 (preço não-retroativo), INV-008 (audit log), **INV-FIN-REATIV-001**, **INV-FIN-INAD-001**, **INV-FIN-GW-001**, **INV-FIN-GW-002**.

## Referências

- `docs/comum/integracoes-inter-modulos.md` (eventos)
- OP-FIN, OP11
