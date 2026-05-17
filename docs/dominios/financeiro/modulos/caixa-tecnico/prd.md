---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: caixa-tecnico
dominio: financeiro
---

# PRD — Caixa do Técnico

## 1. O que é

Controle financeiro individual de cada técnico de campo: adiantamentos recebidos, despesas executadas, fotos de recibo, prestação de contas mensal. Vinculado a OS quando aplicável.

## 2. Por que existe

BIG-08 (frota + UMC + caixa). Hoje em tenants reais: técnico recebe R$ 500 em dinheiro, anota recibos em papel, no fim do mês entrega pasta amassada → financeiro perde 4-8h pra conciliar. JTBD-060/061/062/064. **Wave A robusto** (não simplificado) — decisão estratégica pra ganhar técnicos como evangelizadores.

## 3. Personas

P-OP-01 (técnico de campo — primária), P-FIN-01 (financeiro — valida e fecha mês), P-FIN-02 (dono — vê total adiantado).

## 4. Escopo MVP-1 (Wave A)

- Solicitação de adiantamento via app (técnico → aprovação financeiro/dono)
- Lançamento de despesa via app com foto-comprovante obrigatória
- Vincular despesa a OS (opcional, recomendado)
- Categorização (combustível, alimentação, pedágio, hospedagem, peça, deslocamento)
- Reembolso de km automático (km × tarifa configurada pelo tenant)
- Prestação de contas em ≤ 5 min (JTBD-062): saldo aberto + lista validada + 1 toque fecha mês
- Validação financeiro: 1 swipe valida/rejeita com motivo
- Audit completo (foto + GPS + timestamp)
- Política do tenant: limites por categoria, alçada de aprovação

## 5. Non-goals MVP-1

- OCR automático do recibo (V2)
- Integração com gateway de cartão corporativo (V2 — depende Pluggy)
- Reembolso via PIX instantâneo (V2)
- Múltiplas moedas / técnico em viagem internacional
- Adiantamento via folha de pagamento

## 6. User Stories

- **US-CT-001:** técnico solicita adiantamento → notificação dono → aprovado em 1 toque → técnico recebe via PIX/transferência (manual ou V2 automático).
- **US-CT-002:** técnico tira foto do recibo + escolhe categoria + valor → despesa lançada offline; sincroniza quando volta sinal.
- **US-CT-003:** despesa vinculada a OS aparece no custeio da OS (rastreabilidade pra Wave B).
- **US-CT-004:** financeiro valida 50 despesas do mês em < 10 min (1 swipe cada).
- **US-CT-005:** despesa sem foto = bloqueada (não aceita lançamento).
- **US-CT-006:** técnico fecha prestação de contas em 5 min: vê saldo, dispara fechamento, sistema gera relatório.
- **US-CT-007:** rejeição: financeiro recusa com motivo → técnico reanexa foto melhor → revalidação.

## 7. NFR

- App offline-first: técnico em campo sem 4G consegue lançar; sincroniza ao voltar conectividade.
- Foto comprimida + armazenamento (S3/B2) — não inflar app.
- Prestação ≤ 5 min p95 (medido em telemetria).
- GPS opcional (com consentimento — LGPD), pra evidenciar local da despesa.

## 8. Invariantes

- **INV análogo INV-007:** despesa sem foto-comprovante = não aceita (regra inegociável; análoga a NF-e em contingência).
- INV-008: audit completo (foto, timestamp, GPS opcional, actor).
- Despesa validada não pode ser editada (só nova despesa de correção).

## 9. Dependências

- Operação: cadastro de técnico + OS
- Financeiro: contas a pagar (lançar reembolsos — quando módulo entrar; até lá, manual)
- Armazenamento de fotos (B2/S3)

## 10. Integração com OS

Despesa vinculada a OS aparece em:
- Painel da OS (custos diretos)
- Custeio da OS (Wave B — habilita comissão sobre margem)
- Relatório "OSs deficitárias" (V2)
