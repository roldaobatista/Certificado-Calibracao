---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Configurações do Sistema

> Como saber se a central de configurações está entregando valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % de tenants com config 100% default | Tenants que não mudaram nenhuma config além do mínimo do onboarding | ≤ 30% (indica produto bem ajustado SEM ser engessado) | flag por config | mensal |
| Tempo médio de aplicação de mudança | Segundos entre salvar config e refletir nos módulos consumidores | ≤ 5s | event timestamps | semanal |
| Self-service de configuração | % de mudanças feitas pelo cliente vs suporte Aferê | ≥ 90% | origem do ator | mensal |
| Configurações sensíveis com auditoria | % de mudanças críticas (RBAC, fiscal, retenção, integrações) com registro de auditoria | 100% | obrigatório | contínuo |
| Bloqueios de mudança ilegal | Nº de tentativas de baixar retenção abaixo do legal / mês | tendência ↓ | log de bloqueios | mensal |
| Tempo de leitura de config (cache hit) | Latência p95 de leitura de config no path crítico | < 50ms | APM | contínuo |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade do módulo | 99.95% | ~22min/mês |
| Latência p95 de leitura | < 50ms | — |
| Latência p95 de escrita | < 300ms | — |
| Taxa de erro em escrita | < 0.1% | — |
| Lag de invalidação de cache | < 5s | — |

---

## Dashboards canônicos

- **Grafana:** "Configurações por tenant", "Mudanças sensíveis (RBAC, fiscal, KMS)", "Cache hit rate".
- **Axiom:** logs de auditoria de configuração.

---

## Alertas

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Tentativa de remover último admin | bloqueio executado | admin tenant + watchdog Aferê | P2 |
| Mudança em config fiscal pós-emissão | tentativa bloqueada | contador do tenant + auditor | P1 |
| Credencial de integração com falha de teste | teste pós-save falha | admin tenant | P2 |
| Cache miss rate elevado | > 20% por 5min | infra Aferê | P2 |
| Retenção abaixo do legal | tentativa bloqueada | DPO do tenant + auditor Aferê | P1 |

---

## Métricas de saúde dos AGENTES

- Tokens consumidos por US-CFG.
- Taxa de retrabalho em US-CFG.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta.
- Mudança de target → ADR explicando.
