---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Comunicação Omnichannel

> Como saber se o módulo entrega valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| TMR (Tempo Médio Primeira Resposta) | minutos entre mensagem do cliente e primeira resposta humana | ≤ 5 min horário comercial | diff timestamps em thread | diário |
| TMA (Tempo Médio Atendimento) | minutos entre abertura e encerramento da thread | ≤ 30 min | diff timestamps | semanal |
| % opt-in registrado em contato novo | (contatos novos com opt-in / total contatos novos) × 100 | ≥ 95% | query consentimentos | semanal |
| Envios para opt-out (vazamentos) | qtd mensagens enviadas a clientes em opt-out | 0 (zero tolerância) | log de bloqueios + alerta crítico | tempo real |
| Conversão conversa→chamado | (threads convertidas em chamado / threads totais) × 100 | informativo | eventos `Comunicacao.ConvertidoEmChamado` | mensal |
| Conversão conversa→lead | idem para lead | informativo | eventos `Comunicacao.ConvertidoEmLead` | mensal |
| Taxa de leitura WhatsApp | (mensagens lidas / entregues) × 100 | ≥ 70% | callbacks da Meta | semanal |
| Taxa de bounce e-mail | (e-mails com bounce / enviados) × 100 | ≤ 2% | provedor SMTP | semanal |

---

## SLI/SLO técnico

Detalhes em `../../../operacao/observabilidade.md`. Resumo:

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade da caixa unificada | 99.5% | 3h36min/mês |
| Latência atualização de status | < 2s p95 | — |
| Taxa de webhook perdido | < 0.1% | — |
| Tempo de aplicação de opt-out | < 5s p99 | crítico — falha bloqueia compliance |

---

## Dashboards canônicos

- **Grafana:** painel "Atendimento — Volume e TMA".
- **Grafana:** painel "Compliance LGPD — Opt-in / Opt-out".
- **Axiom (logs):** trilha de consentimento.

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Envio para opt-out | qualquer mensagem enviada a cliente em opt-out | DPO + watchdog | P0 |
| Webhook canal externo caindo | falha > 5 min | operações | P1 |
| Template WhatsApp rejeitado | callback rejeição Meta | gerente atendimento | P2 |
| TMR > 10 min em horário comercial | janela 15 min | gerente atendimento | P2 |
| Fila de conversas não atribuídas > N | watermark configurável | gerente | P2 |

---

## Métricas de saúde dos AGENTES neste módulo

- Tokens consumidos por feature.
- Taxa de retrabalho por US.
- Tempo médio de entrega por US.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta.
- Métrica obsoleta → `@deprecated`.
- Mudança de target → ADR.
