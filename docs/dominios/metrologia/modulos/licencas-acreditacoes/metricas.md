---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Licenças e Acreditações

> Como saber se este módulo está entregando valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Taxa de operações com documento bloqueante vencido | % de operações executadas com documento bloqueante expirado (sem modo emergencial) | 0% | Contar eventos `bloqueio.bypass` ÷ total operações | semanal |
| Antecedência de renovação | Dias entre início da renovação e data validade | mediana ≥ 30 dias | Diferença entre evento `renovacao.iniciada` e validade | mensal |
| Alertas reconhecidos | % de alertas vistos pelo responsável em até 48h | ≥ 95% | Eventos `alerta.lido` ÷ `alerta.disparado` | semanal |
| Cobertura documental | % de documentos regulatórios obrigatórios cadastrados no sistema | 100% | Auditoria checklist vs base | trimestral |
| Tempo de geração relatório auditoria | Minutos pra gerar PDF consolidado | ≤ 30s p95 | Tempo do endpoint export | mensal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade dashboard | 99.9% | 43min |
| Latência consulta licenças p95 | < 500ms | — |
| Latência geração relatório p95 | < 30s | — |
| Taxa de erro no disparo de alerta | < 0.1% | — |

---

## Dashboards canônicos

- **Grafana:** a definir pós ADR-0001.
- **Axiom (logs):** a definir.

---

## Alertas configurados (sistema → equipe)

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Licença vence em 90/60/30/15/7 dias | Cron diário verifica validades | Responsável do documento + admin tenant | P2 → P1 conforme aproxima |
| Licença vencida | T+1 dia após validade | Admin tenant + watchdog | P1 |
| Bloqueio por documento vencido | Operação tentou rodar com doc bloqueante expirado | Admin tenant | P0 |
| Modo emergencial acionado | Admin liberou operação com doc vencido | Watchdog + auditor | P0 (auditoria) |
| Falha disparo de alerta | Erro no envio e-mail/notificação | Watchdog | P1 |

---

## Métricas de saúde dos AGENTES neste módulo

- Tokens consumidos por feature de licença.
- Taxa de retrabalho em US-LIC-NNN.
- Tempo médio de entrega de US.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Métrica obsoleta → `@deprecated`.
- Mudança de target → ADR.
