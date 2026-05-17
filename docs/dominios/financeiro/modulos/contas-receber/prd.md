---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-receber
dominio: financeiro
---

# PRD — Contas a Receber

## 1. O que é

Geração, emissão, cobrança e baixa de títulos a receber do tenant. Recebe gatilho de Operação (`OSConcluida`) e Comercial (contrato recorrente); produz boleto/PIX/cartão; concilia pagamento; ativa régua de cobrança quando atrasa.

## 2. Por que existe

Dor universal #11 (cobrança/inadimplência) — tenant perde 8-15% do faturamento por falta de régua sistemática. Sem este módulo, OP7 (NFS-e) emite mas ninguém cobra.

## 3. Personas

P-FIN-01 (financeiro do tenant), P-FIN-02 (dono — vê inadimplência), P-COM-02 (vendedor — vê o que recebeu pra liberar comissão).

## 4. Escopo (Wave A)

- Gerar título a partir de OS concluída ou contrato
- Emitir boleto + PIX via gateway (1 gateway no MVP-1)
- Parcelamento simples (até N parcelas iguais)
- Aplicação automática de juros + multa + desconto pontualidade conforme regra do tenant
- Baixa manual + baixa automática via webhook gateway
- Listagem com filtro (status, vencimento, cliente)

## 5. Escopo (Wave B — OP11)

- Régua de cobrança configurável (lembrete D-3, D-0, D+3, D+10, D+30)
- Disparo via WhatsApp + e-mail
- Aging em faixas
- Painel inadimplência > 30 dias
- Conciliação OFX

## 6. Non-goals MVP-1

- Antecipação de recebíveis / factoring
- Conciliação Open Finance bidirecional (Wave B/V2 via Pluggy)
- Múltiplos gateways simultâneos
- Negociação automatizada com desconto progressivo
- DRE / fluxo projetado (vem do OP12 — painel do dono)
- Cobrança judicial / protesto

## 7. User Stories (resumo)

- **US-CR-001:** OS concluída gera título automaticamente conforme valor da OS.
- **US-CR-002:** Tenant emite boleto/PIX em 1 clique; cliente recebe link.
- **US-CR-003:** Pagamento via PIX dispara baixa automática em < 60s (webhook).
- **US-CR-004:** Título vencido aplica juros/multa conforme regra; desconto pontualidade cai automático após vencimento.
- **US-CR-005:** (Wave B) Régua envia lembrete WhatsApp D-3; aviso D+3; alerta financeiro D+10.

AC binários: cada US tem GIVEN-WHEN-THEN com flag observável (status, evento emitido, registro audit).

## 8. NFR

- Emissão boleto/PIX < 3s p95
- Webhook gateway → baixa < 60s
- Idempotência obrigatória (gateway pode reenviar webhook)

## 9. Invariantes citadas

- **INV-026** — preço não-retroativo: alteração de tabela não recalcula títulos já emitidos.
- INV-008 — toda emissão/baixa registrada em audit log.

## 10. Dependências

- Foundation: identidade tenant + cliente único
- OP7 (fiscal) — opcional: emissão de NFS-e junto com boleto
- ADR a definir: qual gateway (Asaas/Iugu/Gerencianet) — bloqueio
