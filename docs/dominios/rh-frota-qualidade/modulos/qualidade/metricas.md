---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: qualidade
dominio: rh-frota-qualidade
---

# Métricas — Qualidade

## North Star

**Tempo médio de resolução de NC Crítica** ≤ 14 dias (do registro à eficácia verificada).

## Métricas de compliance (INV-012)

| ID | Métrica | Meta | Como medir | Fonte |
|---|---|---|---|---|
| M-QUA-01 | Nº de emissões bloqueadas por NC ativa (INV-012) | Reportar (informa Roldão + tenant) | Log do hook | App |
| M-QUA-02 | % NC Crítica com 5 Porquês preenchido | 100% (bloqueio) | DB | DB |
| M-QUA-03 | % NC fechadas com revisão de eficácia agendada | 100% (bloqueio) | DB | DB |
| M-QUA-04 | % revisões de eficácia realizadas no prazo | ≥ 90% | DB | DB |

## Métricas de adoção MVP-1

| ID | Métrica | Meta M+3 | Fonte |
|---|---|---|---|
| M-QUA-05 | % tenants ISO 17025 com ≥1 NC registrada no Aferê (vs Excel paralelo) | ≥ 80% | DB |
| M-QUA-06 | Tempo médio de registro de NC (form submit) | ≤ 2 min | Telemetria |
| M-QUA-07 | % OS concluídas com NPS enviado | ≥ 95% | DB |
| M-QUA-08 | Taxa de resposta NPS | ≥ 25% | DB |
| M-QUA-09 | % reclamações que viram NC | Reportar (telemetria) | DB |

## Métricas de qualidade real

| ID | Métrica | Meta | Fonte |
|---|---|---|---|
| M-QUA-10 | NPS médio dos tenants (do produto Aferê — não do serviço do tenant) | ≥ 50 | Survey |
| M-QUA-11 | NC reincidente (mesma causa em < 90 dias) | < 10% | DB |
| M-QUA-12 | Tempo médio resolução NC (registro → fechada com eficácia) | ≤ 14 dias (Crítica) / ≤ 30 (Maior) / ≤ 60 (Menor) | DB |
| M-QUA-13 | % NC originadas em PT/proficiency testing (INV-023) | Reportar (informa V2 quando ativar perfil A) | DB |

## Métricas que NÃO mediremos MVP-1

- Cartas de controle / Cpk / Cp (MVP-2).
- Tendência estatística por instrumento (MVP-2).
- Score de saúde do sistema da qualidade (V2).
- Cobertura de auditoria interna por cláusula (V2).

## Telemetria mínima

Eventos: `nc_aberta`, `nc_bloqueio_emissao`, `nc_5porques_preenchido`, `nc_plano_acao_criado`, `nc_fechada`, `eficacia_agendada`, `eficacia_realizada`, `eficacia_vencida`, `nps_enviado`, `nps_respondido`, `reclamacao_aberta`, `reclamacao_virou_nc`.

## Alarmes

- M-QUA-02 < 100% → bug crítico (hook deveria bloquear).
- M-QUA-04 < 70% → revisar fluxo (eficácia virando burocracia).
- M-QUA-11 > 20% → investigar causas-raiz superficiais.
- M-QUA-01 > 5/mês em mesmo tenant → contato proativo (cliente em risco operacional).
