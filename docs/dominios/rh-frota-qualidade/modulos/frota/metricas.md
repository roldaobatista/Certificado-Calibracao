---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: frota
dominio: rh-frota-qualidade
---

# Métricas — Frota

## North Star

**Zero violação confirmada da Lei 13.103/2015 (INV-020) em tenants ativos** — meta absoluta.

## Métricas de compliance (INV-020)

| ID | Métrica | Meta | Como medir | Fonte |
|---|---|---|---|---|
| M-FRT-01 | Nº de tentativas bloqueadas de agendamento que violariam INV-020 | Reportar (informa Roldão) | Log do hook | App |
| M-FRT-02 | Nº de violações confirmadas (motorista dirigiu além do permitido) | **0** | Comparação jornada registrada vs limite | DB |
| M-FRT-03 | % motoristas UMC com CNH categoria adequada cadastrada | 100% (bloqueio) | DB | DB |
| M-FRT-04 | Tempo médio pra gerar comprovante de jornada PDF | ≤ 5s | Telemetria | Front |
| M-FRT-05 | % motoristas que recebem alerta no minuto 5h25 de direção | 100% | Log push | App |

## Métricas operacionais

| ID | Métrica | Meta M+3 | Fonte |
|---|---|---|---|
| M-FRT-06 | % tenants com ≥1 veículo cadastrado (entre tenants UMC) | ≥ 90% | DB |
| M-FRT-07 | % OS de campo (UMC) com checklist pré-viagem completo | ≥ 85% | DB |
| M-FRT-08 | % abastecimentos com km registrado (input pra consumo) | ≥ 90% | DB |
| M-FRT-09 | Manutenções preventivas registradas no prazo (km/tempo) | ≥ 70% | DB |

## Métricas de caixa do técnico (OP3.2)

| ID | Métrica | Meta | Fonte |
|---|---|---|---|
| M-FRT-10 | % caixas reconciliadas ≤ 7 dias após retorno | ≥ 80% | DB |
| M-FRT-11 | % despesas com nota fiscal anexada | ≥ 75% | DB |
| M-FRT-12 | Saldo divergente médio por caixa | < R$ 20,00 | DB |

## Métricas que NÃO mediremos no MVP-1

- TCO consolidado (Wave C)
- Consumo km/L por veículo (depende de N abastecimentos com km — Wave B quando dados suficientes)
- Tempo médio entre falhas (MTBF) — Wave C
- ROI de UMC vs calibração em lab — Wave C+

## Telemetria mínima

Eventos: `veiculo_cadastrado`, `veiculo_atribuido`, `jornada_iniciada`, `jornada_pausa`, `jornada_encerrada`, `os_bloqueada_inv020`, `alerta_5h25_enviado`, `checklist_completado`, `manutencao_registrada`, `abastecimento_registrado`, `caixa_aberto`, `caixa_reconciliado`.

## Alarmes

- M-FRT-02 > 0 → P0 — incidente crítico, notificar Roldão + DPO + responsável tenant em ≤ 1h.
- M-FRT-03 < 100% → P0 — investigação imediata (significa motorista sem CNH operando).
- M-FRT-12 > R$ 100 médio → revisar fluxo OP3.2.
