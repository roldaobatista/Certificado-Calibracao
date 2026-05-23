---
owner: Roldão
revisado-em: 2026-05-23
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

- Gerar título a partir de OS concluída, **`AtividadeDaOS` concluída** (ADR-0051) ou contrato
- Emitir boleto + PIX + **PIX recorrente** (BCB 1.071/2024) + cartão recorrente via porta `PaymentGatewayProvider` (ADR-0050)
- Parcelamento simples (até N parcelas iguais)
- Aplicação automática de juros + multa + desconto pontualidade conforme regra do tenant
- Baixa manual + baixa automática via webhook gateway (HMAC + idempotência — INV-FIN-GW-001)
- Listagem com filtro (status, vencimento, cliente, **`categoria_receita`** — A-FIN-002)
- **Reativação de cliente bloqueado** quando última fatura vencida é quitada (INV-FIN-REATIV-001 / GATE-CLI-6)

### Diferenciação tenant vs cliente do tenant (INV-FIN-INAD-001 / C-FIN-002)

- **Inadimplência do cliente do tenant:** política livre por tenant. Default sugerido: 90d em aberto bloqueia novo orçamento + OS. Configurável por tenant via `tenant_inadimplencia_config`.
- **Inadimplência do tenant Aferê:** módulo `billing-saas` (ADR-0015). NÃO confundir com a anterior.
- Nenhuma policy/código cruza os dois. Hook `policy-tenant-vs-cliente.sh` (Onda 10) valida.

## 5. Escopo (Wave B — OP11)

- Régua de cobrança configurável (lembrete D-3, D-0, D+3, D+10, D+30)
- Disparo via WhatsApp + e-mail (via `OmniChannelProvider`)
- Aging em faixas
- Painel inadimplência > 30 dias
- **Conciliação OFX (A-FIN-003) — explicitamente Wave B**
- **Marketplace produtor (M-FIN-003)** — receita de marketplace é Wave B

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
- **US-CR-006 (C-FIN-001 / GATE-CLI-6):** Quando última fatura vencida de cliente bloqueado por inadimplência é paga, sistema publica `Cliente.Desbloqueado(motivo=pagamento_quitou)` em ≤5min, liberando novos orçamentos+OS.
- **US-CR-007 (A-FIN-001):** Emitir cobrança via porta `PaymentGatewayProvider` (cartão recorrente, PIX recorrente BCB 1.071/2024, boleto). Provedor configurável por tenant.
- **US-CR-008 (A-FIN-002):** Classificar receita por `categoria_receita` (`CALIBRACAO_RBC`, `CALIBRACAO_NAO_RBC`, `MANUTENCAO_CORRETIVA`, `MANUTENCAO_PREVENTIVA`, `PECA_REVENDA`, `DESLOCAMENTO`, `OUTROS`).
- **US-CR-009 (M-FIN-002):** Pagamento grava `valor_atualizado_snapshot_em_pagamento` — fotografa juros+multa do instante da baixa.

AC binários: cada US tem GIVEN-WHEN-THEN com flag observável (status, evento emitido, registro audit).

## 8. NFR

- Emissão boleto/PIX < 3s p95
- Webhook gateway → baixa < 60s
- Idempotência obrigatória (gateway pode reenviar webhook)

## 9. Invariantes citadas

- **INV-026** — preço não-retroativo: alteração de tabela não recalcula títulos já emitidos.
- INV-008 — toda emissão/baixa registrada em audit log.
- **INV-FIN-REATIV-001** — `ContasReceber.Pago` da última fatura vencida publica `Cliente.Desbloqueado` ≤5min (GATE-CLI-6).
- **INV-FIN-INAD-001** — inadimplência do cliente do tenant ≠ inadimplência do tenant; políticas não cruzam.
- **INV-FIN-GW-001** — webhook gateway exige HMAC + idempotência.
- **INV-FIN-GW-002** — `meio=pix_recorrente` exige `convenio_pix_id` NOT NULL (BCB 1.071/2024).

## 10. Dependências

- Foundation: identidade tenant + cliente único
- OP7 (fiscal) — opcional: emissão de NFS-e junto com boleto
- **ADR-0050** — porta `PaymentGatewayProvider` (3 modos: cartão recorrente, PIX recorrente, boleto). Default Asaas; configurável por tenant.
- **ADR-0051** — propagação ADR-0023 (fatura por `AtividadeDaOS`).
