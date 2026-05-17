---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Certificados

> Como saber se este módulo está entregando valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Gaps de numeração | Quantidade de números pulados na sequência por tenant/tipo/ano | 0 | Job diário verifica continuidade | diária |
| Tempo médio emissão→assinatura | Minutos entre criar certificado e ser assinado pelo RT | ≤ 5 min mediana | Diff timestamps | semanal |
| Taxa de entrega e-mail cliente | E-mails entregues (não bounce) ÷ enviados | ≥ 98% | Webhook do provedor SMTP | semanal |
| Taxa de reemissões | % certificados reemitidos no primeiro mês | ≤ 2% | Reemissões ÷ emissões | mensal |
| Adoção do portal pelo cliente | % clientes que baixaram pelo portal nos últimos 90 dias | ≥ 60% | Eventos `Certificados.Baixado` | mensal |
| Verificações via QR Code | Quantidade de acessos à página pública verificadora | crescente | Eventos `Certificados.VerificacaoPublica` | mensal |
| Cobertura PDF/A-1 | % certificados emitidos em PDF/A-1 | 100% | Validação no pipeline emissão | semanal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade | 99.9% | 43min |
| Latência geração PDF p95 | < 3s | — |
| Latência assinatura A3 (round-trip) p95 | < 10s | — |
| Latência página pública verificadora p95 | < 500ms | — |
| Taxa de erro emissão | < 0.1% | — |

---

## Dashboards canônicos

- **Grafana:** a definir pós ADR-0001.
- **Axiom (logs):** a definir.

---

## Alertas

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Gap detectado na sequência | Job diário acha número pulado | RT + admin tenant + watchdog | P0 |
| Falha repetida na assinatura A3 | ≥3 tentativas falhas em 5min | RT + watchdog | P1 |
| Bounce e-mail cliente | E-mail não entregue após 3 tentativas | RT | P2 |
| Latência geração PDF > 10s | p95 acima de threshold | Watchdog | P1 |
| Tentativa de edição em cert emitido | Bloqueado pelo INV-014 | Watchdog (suspeita) | P0 |

---

## Métricas de saúde dos AGENTES

- Tokens por feature deste módulo.
- Taxa de retrabalho em US-CER-NNN.

---

## Como esta lista evolui

- Métrica nova → adicionar + coleta + CHANGELOG.
- Obsoleta → `@deprecated`.
- Mudança de target → ADR.
