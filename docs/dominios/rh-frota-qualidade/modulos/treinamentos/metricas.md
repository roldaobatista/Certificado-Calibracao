---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
modulo: treinamentos
---

# Métricas — Módulo Treinamentos e Certificações Internas

> Como saber se o módulo está mantendo a equipe competente para ISO 17025 cl. 6.2 + ISO 9001 cap. 7.2.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Aderência à trilha por função | % colaboradores com 100% da trilha válida | 100% | Matriz competência | mensal |
| Emissões de certificado de calibração com técnico não-habilitado | Eventos de bypass auditados | 0 | Audit log + INV-002 | semanal |
| Tempo médio entre vencimento e reciclagem | Dias entre data-validade e novo evento | ≤30 dias | Eventos x certificados | mensal |
| Treinamentos vencidos em vigor | Certificados expirados ainda referenciados | 0 | Query certificados x trilhas | semanal |
| Custo médio por colaborador / ano | Soma custos / nº colaboradores ativos | a definir | Quando módulo financeiro existir | anual |
| Taxa de aprovação em provas | aprovados / (aprovados + reprovados) | ≥85% | Eventos x notas | trimestral |
| Cobertura matriz por equipamento | % equipamentos com ≥1 técnico habilitado | 100% | Trilha equipamento x certificados | mensal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade matriz competência | 99.9% | 43min |
| Latência p95 matriz (100 col × 50 hab) | <3s | — |
| Disponibilidade endpoint bloqueio execução | 99.95% | — |

> Bloqueio de execução é caminho crítico de calibração — SLO mais rígido que padrão do produto.

---

## Dashboards canônicos

- **Grafana:** a definir pós ADR-0001.
- **Axiom (logs):** trilha de bypass + emissão certificado.

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Treinamento vencendo em 30 dias | Daily job | Gerente RH + colaborador | P3 |
| Trilha incompleta para colaborador ativo em função | Job semanal | Gerente Qualidade | P2 |
| Bypass de bloqueio executado | Tempo real | Gerente Qualidade + Dono + auditor | P1 |
| Certificado emitido com técnico não-habilitado (falha de invariante) | Tempo real | Gerente Qualidade + governança | P0 |
| Equipamento sem técnico habilitado | Job diário | Gerente Operacional | P1 |

---

## Métricas de saúde dos agentes

- Tokens consumidos / feature do módulo.
- Taxa de retrabalho US-TRE-*.
- Tempo médio de entrega.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Mudança de target → ADR.
