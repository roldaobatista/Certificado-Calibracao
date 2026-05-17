---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Métricas de sucesso — transversais ⚪

> **Pra quê:** consolidação das metas globais do produto. Métricas específicas por módulo ficam no `metricas.md` do módulo.
>
> **Status:** ⚪ lazy — calibrar quando MVP-1 rodar em produção real.

---

## Métricas do MVP-1 (do `prd.md` §7)

| Métrica | Meta 12 meses | Como medir |
|---------|----------------|------------|
| Tenants ativos | ≥ 1 (Balanças Solution dogfooding) — diferido pra mais quando deploy autorizado | Painel-do-dono |
| NFS-e emitidas sem erro fatal | ≥ 95% | Log fiscal |
| Certificados sem retrabalho | ≥ 90% | Auditor Produto + NPS |
| Tempo "cadastro → 1ª OS emitida" | ≤ 15 min | Telemetria onboarding |
| Churn 90 dias | ≤ 15% (diferido — sem cliente externo) | Cobrança + CS |
| Auditor Segurança em 3 portões ADR-0001 | passou | `trilha-auditoria-agentes.md` |
| R-001 (founder is customer) | ≤ 9 (aceito em 12 conscientemente) | `discovery/riscos.md` |

---

## North star metric (a calibrar)

Candidatos:
1. **% certificados emitidos sem retrabalho** (proxy de qualidade do produto)
2. **Tempo médio entre OS aberta e certificado emitido** (proxy de fluidez do processo)
3. **NFS-e/mês por tenant** (proxy de uso real do módulo fiscal)

Decisão diferida pro pós-Wave A.

---

## Métricas que **não** importam (anti-vanity)

- ❌ Quantidade de features lançadas
- ❌ Linhas de código
- ❌ % de cobertura sozinho (sem qualidade do teste)
- ❌ Tempo médio de PR (vanity sem contexto)

---

## Drill

Revisão mensal por Roldão via `status-semanal.md`.

---

## Referências

- `prd.md` §7
- `governanca/status-semanal.md`
- `governanca/metricas-operacao-agentes.md` (custo/tokens — operação do agente)
- `discovery/sintese-final.md` §6 (modelo de negócio)
