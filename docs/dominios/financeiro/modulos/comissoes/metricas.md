---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: comissoes
dominio: financeiro
---

# Métricas — Comissões

## Primárias

| Métrica | Target MVP-1 | Como medir |
|---|---|---|
| % contestações resolvidas com rastro granular | ≥ 95% | contestações onde demonstrativo reconstrói exatamente o valor ÷ total |
| Tempo médio Pago → comissão devida | p95 < 60s | webhook `Pago` → mudança de status |
| Estornos por título cancelado pós-pagamento | 100% automáticos | nunca manual; sempre via evento |
| % vendedores que abriram "Minha comissão" no mês | ≥ 80% após 30d | adoção do app |

## Secundárias

| Métrica | Target | Notas |
|---|---|---|
| Cálculo OS concluída → comissão prevista | < 2s | medido no evento handler |
| Erro de cálculo (auditoria manual) | 0 | sempre que ocorrer = bug crítico |
| Tempo configurar nova regra | < 60s | UI rápida |

## Indicadores de confiança do beneficiário

- NPS específico "Você confia no cálculo da comissão?" — V2
- Volume de contestações ↓ ao longo do tempo

## Alertas

- Cálculo divergente de auditoria semanal → ticket crítico.
- Comissão prevista > 30 dias sem virar devida (título em aberto longo) → notifica vendedor + financeiro.
- Estorno > limiar % no mês → revisar (sinal de OS sendo canceladas).

## Não-métricas

- Volume de comissão paga em R$ — métrica de venda, não do módulo. Pertence ao painel-do-dono.
- Número de regras cadastradas — pode crescer sem efeito.

## Referências

- OP4
- JTBD-072, JTBD-078, JTBD-082
- OP12 painel do dono (consome)
