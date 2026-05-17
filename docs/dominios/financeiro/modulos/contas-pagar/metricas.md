---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-pagar
dominio: financeiro
---

# Métricas — Contas a Pagar

> Wave C. Targets são hipóteses; refinar pós-discovery.

## Primárias hipotéticas

| Métrica | Target hipotético | Como medir |
|---|---|---|
| % lançamentos pagos no prazo | ≥ 95% | pagos até vencimento ÷ total |
| Tempo médio entre lançamento e aprovação | < 24h | data lançamento → data aprovação |
| Pagamentos duplicados | 0 | mesmo fornecedor + valor + período = alerta |
| % lançamentos com categoria + centro de custo | ≥ 90% | obrigar UI |

## Secundárias

| Métrica | Target | Notas |
|---|---|---|
| Tempo p95 cadastro lançamento | < 90s | UI tem que ser rápida |
| Taxa de conciliação automática OFX | ≥ 80% (V2) | depende de chave de match |
| % aprovações na alçada certa | 100% | auditoria mensal |

## Indicadores de qualidade de dados

- % lançamentos sem anexo (boleto/NF): meta < 5%
- % lançamentos com plano de contas "outros": meta < 10% (sinaliza plano mal modelado)

## Adoção

- Não exigir % no MVP-2 (módulo opcional). Acompanhar curva.

## Alertas

- Lançamento pendente aprovação > 5 dias → notifica dono.
- Mesma chave (fornecedor + valor + mês) detectada 2x → suspeita duplicata.
- Diferença caixa contábil vs banco > limiar → reconciliação obrigatória.

## Referências

- A definir pós-discovery
