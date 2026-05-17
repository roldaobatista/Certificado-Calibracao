---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fiscal
dominio: financeiro
---

# Métricas — Fiscal

## Primárias (resultado regulatório + negócio)

| Métrica | Target MVP-1 | Como medir |
|---|---|---|
| % emissões com sucesso na 1ª tentativa | ≥ 95% | autorização SEFAZ/município ÷ tentativas |
| Cobertura municípios (tenants ativos) | ≥ 90% dos tenants conseguem emitir | tenants emitindo ÷ tenants ativos |
| Tempo emissão (p95) | < 5s | tentativa → autorização ou erro |
| Disponibilidade contingência automática | 99,9% | detecção SEFAZ-down → troca de modo |
| % XML em WORM verificado | 100% | hash verifica imutabilidade |

## Cutover NFS-e nacional 01/09/2026

| Métrica | Target |
|---|---|
| Smoke test cutover D-30 | aprovado |
| Tenants comunicados D-15 | 100% |
| Falhas durante semana cutover | < 5% (vs baseline) |
| Postmortem entregue D+7 | sim |

## Secundárias

| Métrica | Target | Notas |
|---|---|---|
| Tempo cancelamento | p95 < 5s | < 24h após emissão |
| CC-e processada | p95 < 10s | depende município |
| Inutilização processada | p95 < 30s | volume baixo |
| Erros 4xx (dados inválidos do tenant) | acompanhar — feedback UX | |

## Compliance / auditoria

- 100% emissões com audit log completo (INV-008)
- 0 NFs sem XML em WORM (alarme crítico se ocorrer)
- 0 endpoints de emissão sem MFA (auditor segurança)

## Alertas

- Taxa erro emissão > 5% em 15min → on-call + degraded mode
- SEFAZ/município fora detectado → ativa contingência + comunicado
- Numeração com buraco > 25 dias → notifica financeiro (prazo inutilização)
- BaaS upstream com SLA degradado → comunicado + watcher

## Não-métricas

- Volume bruto NFs emitidas — métrica de venda do tenant, não do módulo.

## Referências

- OP7
- BIG-04
- `docs/conformidade/comum/fiscal.md` + `fiscal-contingencia.md`
- INV-007, INV-008
