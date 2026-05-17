---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: caixa-tecnico
dominio: financeiro
---

# Métricas — Caixa do Técnico

## Primárias (resultado)

| Métrica | Target MVP-1 | Como medir |
|---|---|---|
| Tempo prestação de contas | p95 ≤ 5 min | telemetria UI: abrir prestação → confirmar fechamento |
| % despesas com foto-comprovante | 100% | invariante = bloqueio |
| % despesas validadas em < 48h | ≥ 90% | data lançamento → data validação |
| % técnicos que fecham caixa no prazo | ≥ 95% | fechado até dia X do mês seguinte |

## Secundárias

| Métrica | Target | Notas |
|---|---|---|
| Sincronização offline → online | p95 < 30s | medida quando rede volta |
| Despesas rejeitadas | < 10% | acima sinaliza problema (foto/política) |
| Tempo financeiro valida 1 despesa | p95 < 10s | swipe rápido |
| % despesas vinculadas a OS | ≥ 80% | habilita custeio Wave B |

## Indicadores de risco / fraude

- Despesa > 3σ da média da categoria → revisão obrigatória
- Mesma foto em 2 despesas (hash) → bloqueio + alerta
- Despesa fora do raio GPS da OS (se GPS habilitado) → warning

## Adoção

- % técnicos ativos no app: ≥ 90% após 30d
- % despesas via app (não papel): ≥ 95% após 60d

## Alertas

- Adiantamento aberto > 60 dias sem prestação → notifica técnico + dono
- Saldo negativo a reembolsar > 30 dias → notifica financeiro
- Despesa pendente validação > 7 dias → notifica financeiro

## Não-métricas

- Volume R$ em despesas — varia muito; não otimizar
- Número de despesas / técnico — depende do trabalho de campo

## Referências

- OP3.2
- BIG-08
- JTBD-062 (5 min)
