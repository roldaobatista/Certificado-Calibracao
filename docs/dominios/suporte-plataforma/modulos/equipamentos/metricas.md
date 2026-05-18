---
owner: Roldão
revisado-em: 2026-05-18
status: stable
modulo: equipamentos
dominio: suporte-plataforma
versao: 2
---

# Métricas — Módulo Equipamentos do cliente

> **v2 (2026-05-18):** acréscimo de KPIs de ISO 17025 cl. 7.4 (recebimento) + SLI de scanner QR PWA.

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Tempo para localizar equipamento | Mediana entre abrir busca e abrir ficha 360° | ≤ 30s | telemetria UI | semanal |
| % equipamentos com QR impresso | (equip. com flag `qr_impresso=true`) / total | ≥ 90% | query | mensal |
| Taxa de escaneamento QR | scans/mês ÷ equipamentos ativos | ≥ 60% | log de leituras (`equipamento.qr_scanned`) | mensal |
| % equipamentos com histórico ≥ 1 certificado | (equip. com ≥1 cert.) / total | ≥ 80% após 6m | query | mensal |
| Equipamentos órfãos (sem cliente) | Contagem `status=orfao_pendente_decisao` | = 0 | query | diária |
| **% recebimentos com foto + condição visual (perfil A)** | recebimentos com `fotos_chegada ≥ 1 AND condicao_visual_chegada NOT NULL` / total recebimentos perfil A | **100%** | query | semanal |
| **Tempo médio de fluxo lab (recebimento → devolução)** | mediana de `data_hora_devolucao - data_hora_recebimento` | ≤ 7 dias | query | mensal |
| **% scans QR via PWA (Marco 2)** | scans/mês via user_agent PWA / total scans | ≥ 70% até Wave B chegar | telemetria | mensal |
| **% transferências com aceite duplo registrado** | transferências com `aceite_origem + aceite_destino` / total transferências | 100% | query | mensal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade | 99.9% | 43 min |
| Latência p95 ficha 360° | ≤ 1.5s | — |
| Latência p95 abrir via QR (resolução `/qr/{hash}`) | ≤ 2s | — |
| Taxa de erro endpoints | < 0.1% | — |
| **Latência p95 PWA scanner (detecção QR → resolução backend)** | ≤ 3s (inclui frame câmera) | — |
| **Disponibilidade `/qr/{hash}` mesmo sob ataque enumeração** | 99.95% (rate limit por IP defende) | — |

---

## Dashboards canônicos

- Grafana: dashboard `equipamentos-saude` (a criar) — KPIs negocio + SLI técnico.
- Axiom (logs): query saved `equipamento.qr_scanned by escopo (A/B/C)` — anomalia se Escopo C disparar fora do horário comercial.

---

## Alertas

| Alerta | Quando dispara | Severidade |
|---|---|---|
| QR sem destino | Scan em QR que aponta pra equip. inexistente / revogado | P3 |
| Tentativa de mutação INV-025 | Bloqueio de edição em campo imutável pós-cert | P3 |
| Equipamento órfão | Equip. sem cliente_atual_id válido > 12 meses | P2 |
| **IP bloqueado por enumeração** | 100+ 4xx do mesmo IP em 1h | P2 |
| **Foto faltante em recebimento perfil A** | Recebimento sem `fotos_chegada` em tenant perfil A | P2 |
| **Transferência cross-tenant tentada** | INV-050 disparou (tentativa de transferir entre tenants) | P1 |
| **Localização com PII rejeitada** | INV-EQP-LOC-001 (tentativa salvar localização com PII) | P3 (anomalia comportamental — atendente pode estar mal treinado) |
| **HMAC inválido em hash QR** | KMS_qr_secret problema / hash forjado | P1 |

---

## Métricas de saúde dos agentes

- Tokens por feature do módulo
- Taxa de retrabalho em US-EQP-*
- Tempo médio de entrega de US-EQP
- Cobertura de testes (target ≥80% no módulo equipamentos)
- Hooks 103/103 verdes (regressão zero)
- Ratio de CONCERNs/FAILs nos auditores Família 5 (target: FAIL = 0; CONCERN ≤2 por marco)

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Mudança de target → ADR.
- Alerta novo → cadastrar em `docs/operacao/runbooks-alertas.md` (a criar).
