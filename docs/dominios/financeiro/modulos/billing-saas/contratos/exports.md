---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
---

# Contratos de Export — Módulo Billing SaaS

> Formatos de saída do módulo: PDF de fatura, CSV de cobranças, dados pra Fiscal emitir NFS-e a si próprio.

---

## Exports

### Export 1: Fatura SaaS (PDF)

**Propósito:** documento de cobrança do Aferê pro tenant. Para registro contábil e pagamento.
**Formato:** PDF/A (longa duração).
**Regulado?:** não (mas referencia NFS-e correspondente quando emitida).
**Validador externo:** N/A (formato interno).
**Template:** `templates/billing-saas/fatura.html` (a criar pós ADR-0001).
**Campos obrigatórios:** número fatura, data emissão, data vencimento, tenant (razão social + CNPJ), plano contratado, ciclo, valor bruto, descontos (cupons), valor líquido, instruções de pagamento, número NFS-e (se emitida).
**Campos opcionais:** logo, observações, código de barras boleto, QR PIX.
**Assinatura digital:** não obrigatória; pode ter para certas integrações.
**Imutabilidade pós-emissão:** sim — fatura paga não pode ser editada (`INV-NNN`); correção via estorno + nova.
**Retenção:** ver `../../../conformidade/comum/retencao-matriz.md` (mínimo Receita 5 anos).

---

### Export 2: Recibo de pagamento (PDF)

**Propósito:** comprovante pra tenant pós-confirmação de pagamento.
**Formato:** PDF.
**Regulado?:** não.
**Campos obrigatórios:** referência à fatura, valor pago, data/hora pagamento, método (cartão 4 últimos dígitos / boleto / PIX), gateway_transacao_id.

---

### Export 3: Histórico de faturas (CSV/XLSX)

**Propósito:** tenant exporta histórico pra conciliação contábil interna.
**Formato:** CSV (UTF-8 com BOM) e XLSX.
**Campos:** número, data emissão, data vencimento, valor bruto, desconto, valor líquido, status, pago_em, método_pagamento, gateway_transacao_id.
**Filtros:** período, status.

---

### Export 4: Payload para Fiscal (NFS-e da assinatura)

**Propósito:** quando fatura é paga, Aferê emite NFS-e a si próprio (município de origem). Este export é o payload entregue ao módulo `fiscal`.
**Formato:** JSON (interno, não regulado diretamente — quem regula é o XML da NFS-e gerado pelo `fiscal`).
**Disparo:** evento `BillingSaas.FaturaPaga` → módulo `fiscal` consome.
**Campos:** tomador (tenant), prestador (Aferê), serviço (código LC 116/03 — software/SaaS), valor, ISS retido/não retido conforme município.
**Imutabilidade:** sim, espelhada da fatura.
**Ver também:** ADR-0008 (Fiscal pluggable).

---

### Export 5: Relatório de MRR/Churn (admin — operador comercial)

**Propósito:** acompanhamento gerencial do SaaS.
**Formato:** CSV/XLSX.
**Campos:** mês, MRR, novos clientes, churn, upgrade, downgrade, MRR líquido.
**Periodicidade:** mensal.
**Audiência:** apenas papel `operador_comercial_afere` + Roldão.

---

### Export 6: Log de auditoria de assinaturas (admin)

**Propósito:** trilha de mudanças críticas (reativação manual, override de plano, isenção de cobrança) para conformidade interna.
**Formato:** CSV.
**Campos:** quando, quem, tenant_id, evento, de→para, motivo.
**Origem:** entidade `HistoricoAssinatura` (append-only WORM).
**Retenção:** alinhada com matriz LGPD/Receita.

---

## Exports inter-módulos

- `BillingSaas.FaturaPaga` → `fiscal` (emite NFS-e), `contabilidade` (lança receita).
- `BillingSaas.TenantSuspenso` → `auth` (corta acesso), todos módulos (entram read-only).
- Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export regulado

- Não há export DIRETAMENTE regulado neste módulo (regulação está no `fiscal` que consome).
- Template de fatura interna: mudança = bump CHANGELOG e migração suave (faturas emitidas mantêm versão antiga).

## Como esta lista evolui

- Export novo → adicionar + ligar a US se aplicável.
- Export descontinuado → marcar `@deprecated` + janela 6 meses (clientes podem ter integração).
