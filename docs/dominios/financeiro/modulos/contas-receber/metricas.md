---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-receber
dominio: financeiro
---

# Métricas — Contas a Receber

## Primárias (resultado de negócio)

| Métrica | Target MVP-1 | Como medir |
|---|---|---|
| Inadimplência > 30 dias | redução de 30% em 6 meses no tenant médio | (Σ títulos vencidos > 30d) ÷ (Σ títulos emitidos no período) |
| Prazo médio recebimento (DSO) | redução de 15% | dias entre emissão e baixa, média ponderada |
| % títulos pagos em dia | ≥ 70% | títulos baixados no/antes vencimento ÷ total emitido |
| Taxa de conciliação automática (Wave B) | ≥ 95% | títulos baixados por webhook ou OFX ÷ total baixados |

## Secundárias (operação)

| Métrica | Target | Notas |
|---|---|---|
| Tempo emissão boleto/PIX | p95 < 3s | medido na API |
| Falha emissão (4xx/5xx gateway) | < 0,5% | excluindo dados inválidos do tenant |
| Webhook → baixa | p95 < 60s | da chegada do webhook até `Pago` emitido |
| Idempotência violada | 0 | webhook duplicado nunca duplica baixa |

## Adoção

- % tenants que emitiram ≥ 1 título no mês: ≥ 80% após 30d de onboarding
- % tenants que configuraram régua (Wave B): ≥ 50% em 90d

## Não-métricas (não otimizar)

- Volume bruto de títulos emitidos — pode crescer artificial sem efeito de receita.
- Número de baixas manuais — Wave A esperado alto; Wave B precisa cair.

## Como métricas viram alarme

- Inadimplência > 30d cresce > 20% no tenant em 30 dias → alerta no painel-do-dono (OP12).
- Webhook falhando > 5% em 1h → on-call Plataforma.
- Falha emissão gateway > 2% em 15min → degraded mode + comunicado.

## Referências

- OP-FIN, OP11
- `docs/dominios/operacao/observabilidade.md`
- OP12 painel do dono (consome estas métricas)
