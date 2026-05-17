---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-pagar
dominio: financeiro
---

# PRD — Contas a Pagar

> **Status: Wave C / Pós-MVP-1.** Documento de placeholder + decisão consciente. Quando MVP-1 estabilizar, abrir discovery próprio (entrevistas com 5 tenants reais sobre como pagam fornecedores hoje).

## 1. O que é

Lançamento, aprovação, pagamento e conciliação de obrigações do tenant com terceiros (fornecedores, impostos, salários, aluguel). Espelho de Contas a Receber, virado pro outro lado.

## 2. Por que não está no MVP-1 (gap consciente)

- Nenhuma das 12 dores fundadoras é "tenant não consegue pagar fornecedor".
- Roldão (founder = primeiro cliente) hoje resolve fora do Aferê (banco + planilha).
- Risco "customização disfarçada" alto: plano de contas + workflow de aprovação varia muito entre tenants.
- Prioridade: OP7 (NFS-e, deadline regulatório) + OP-FIN (receber) + OP3.2 (caixa técnico).

Decisão: postergar pra MVP-2 ou Wave C; revisar após primeiros 10 tenants pagantes.

## 3. Personas (quando entrar)

P-FIN-01 (financeiro do tenant), P-FIN-02 (dono — aprovação alto valor), persona "gerente operacional" (aprovação de despesa do setor — discovery futuro).

## 4. Escopo previsto (não-compromisso)

- Lançamento manual com anexo (boleto/NF)
- Captura via OCR do boleto (V2)
- Plano de contas configurável por tenant (template padrão)
- Centro de custo + rateio
- Fluxo de aprovação configurável (alçadas por valor)
- Pagamento manual com baixa
- Pagamento programado via Open Finance (depende de Pluggy/Belvo — V2)
- Conciliação ativa OFX

## 5. Non-goals (explícitos mesmo pós-discovery)

- Folha de pagamento (vai pra RH — V2)
- Apuração contábil completa (responsabilidade do contador externo)
- DDA (Débito Direto Autorizado) — V2+
- Substituição de ERP contábil do contador
- Cálculo de imposto a pagar (mesma postura do módulo Fiscal — Aferê não calcula)

## 6. User Stories (rascunho — revisar pós-discovery)

- US-CP-001: tenant lança boleto recebido com anexo, categoria e centro de custo.
- US-CP-002: lançamento > R$ X exige aprovação do dono antes de baixar.
- US-CP-003: tenant marca pago e anexa comprovante.
- US-CP-004: extrato OFX importado concilia pagamento automaticamente.

AC binários a definir pós-entrevistas.

## 7. Pré-requisitos pra abrir discovery

- MVP-1 estabilizado (OP7+OP-FIN+OP3.2 em produção com 10+ tenants)
- 5 entrevistas dedicadas sobre rotina de pagamento
- Decisão sobre plano de contas template (Aferê fornece? tenant cria? import contador?)

## 8. Invariantes

INV-008 (audit). Demais a definir.

## 9. Dependências futuras

- ADR sobre integração Open Finance (Pluggy/Belvo) pra débito programado.
- ADR sobre plano de contas template.
- Módulo Fornecedores (já planejado em suporte-plataforma).
