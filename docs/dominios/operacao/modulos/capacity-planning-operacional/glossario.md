---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: capacity-planning-operacional
dominio: operacao
---

# Glossário — Capacity Planning Operacional

> Específicos. Transversais em `docs/comum/glossario.md`.

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Capacidade base | Horas semanais teoricamente disponíveis de um recurso, sem férias/ausências | "carga horária" (ambíguo) | número de horas/semana | spec módulo |
| Capacidade efetiva | Capacidade base menos férias, feriados, ausências, manutenções | "líquida" | número real de horas no período | spec módulo |
| Horas ocupadas | Soma de horas alocadas a OS/agenda no período | "alocação" | já comprometido | spec módulo |
| Taxa de ocupação | Horas ocupadas / capacidade efetiva | "utilização" | porcentagem 0-100% | spec módulo |
| Gargalo | Recurso com taxa de ocupação > 85% por janela contínua de N dias (default 14) | "engargalado" | flag vermelha | spec módulo |
| Sobrecarga | Taxa de ocupação > 100% (mais demanda que capacidade) | "overbooking" | flag crítica | spec módulo |
| Tempo médio realizado | Média ponderada do tempo gasto em OS daquele tipo nos últimos 90 dias | "estimativa" | usado em projeção | spec módulo |
| Tempo previsto | Tempo médio realizado OU override manual por tipo de OS | "previsto" | usado pra calcular ocupação futura | spec módulo |
| Demanda em fila | Chamados/OS abertos ainda não agendados | "backlog" (técnico em demais módulos) | input do cálculo de capacidade futura | spec módulo |
| Previsão de demanda | Estimativa futura de horas necessárias por tipo de serviço | "forecast" | combina histórico + fila + sazonalidade | spec módulo |
| Capacidade futura | Capacidade efetiva projetada para janelas N (4/8/12 semanas) | "projeção" | usada em simulações | spec módulo |
| Simulação | Cenário hipotético "e se" rodado sem afetar dados reais | "what-if" | resultados isolados, descartáveis | spec módulo |
| Distribuição sugerida | Recomendação de alocação OS→técnico/equipe que humano confirma | "auto-assign" (NUNCA — sempre humano confirma) | sugestão, não comando | spec módulo |
| Recurso | Técnico, equipe ou laboratório capaz de executar tipo de serviço | "agente" (ambíguo com IA) | entidade alocável | spec módulo |
| Necessidade de contratação | Delta entre demanda projetada e capacidade futura, em FTE | "vagas abertas" | sugestão, não autorização | spec módulo |
| FTE | Full-Time Equivalent — 1 técnico × 40h semanais | "equivalente integral" | unidade de medida de capacidade | gestão de operações (geral) |

## Convenções

- "Capacity planning" no nome do módulo é tolerado (termo de mercado); na UI usar "planejamento de capacidade".
- "Agendamento" ≠ "alocação" ≠ "distribuição": agendamento gera evento na Agenda; alocação reserva capacidade; distribuição = ato de atribuir OS a recurso.
