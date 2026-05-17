# RACI — Incidente AI-driven

> **Quem responde quando agente vaza dado do tenant Y às 14h?** Anthropic? Hostinger? Roldão? Auditor 1 v2 alertou que sem RACI explícito, responsabilidade é indefinida.

---

## Matriz RACI (Responsible / Accountable / Consulted / Informed)

### Cenário 1 — Vazamento de dado de tenant
| Atividade | Roldão | Anthropic | Hostinger | AWS (KMS) | B2 (backup) |
|---|---|---|---|---|---|
| Detectar vazamento | R/A | I | I | I | I |
| Conter (revogar acessos, isolar tenant) | A | C | C | C | I |
| Investigação forense | A | R (logs IA) | R (logs infra) | R (logs KMS) | R (logs backup) |
| Comunicação ANPD (72h, LGPD art. 48) | A | I | I | I | I |
| Comunicação aos titulares afetados | A | I | I | I | I |
| Comunicação ao cliente (tenant afetado) | R/A | — | — | — | — |
| Mitigação + correção do bug | R/A | I | I | I | I |
| Postmortem (`incidente-postmortem.md`) | A | I | I | I | I |
| Atualização de invariantes / regras | A | I | I | I | I |

### Cenário 2 — Agente comprometido (prompt injection)
| Atividade | Roldão | Anthropic |
|---|---|---|
| Detectar (via trilha-auditoria-agentes ou auditor sentinela) | R/A | I |
| Suspender o agente afetado | A | C |
| Revogar tokens / sessions ativas | A | — |
| Auditar últimas 24h de ações do agente | R/A | C (suporta com logs do modelo) |
| Comunicar Anthropic se for falha do modelo | A | — |

### Cenário 3 — Indisponibilidade de provedor (Hostinger BR fora >2h)
| Atividade | Roldão | Hostinger | Provedor B (Magalu/AWS/Oracle) |
|---|---|---|---|
| Detectar (alerta Grafana/Axiom) | I | — | — |
| Decidir failover | A | I | I |
| Executar failover (via IaC) | R | — | — |
| Comunicar clientes | R/A | — | — |
| Postmortem | A | C | C |

### Cenário 4 — Incidente fiscal (NF-e bloqueada, SEFAZ recusa)
| Atividade | Roldão | Focus/NFE.io | SEFAZ | Contador |
|---|---|---|---|---|
| Detectar (alerta NF-e fail) | I | I | — | — |
| Identificar causa (NF-e malformada vs SEFAZ fora) | R/A | C | I | C |
| Mitigar (re-emitir, contingência SVC, EPEC) | A | R | — | C |
| Comunicar cliente afetado | R/A | — | — | — |

---

## Cláusulas DPA por provedor (a contratar)

> Sem DPA assinado, responsabilidade é nebulosa. Lista a obter antes de produção:

| Provedor | DPA | Status |
|---|---|---|
| **Anthropic** | Termos de uso da API Claude | Verificar cláusula de processamento de dados pessoais |
| **OpenAI (Codex)** | Termos OpenAI Enterprise/API | Mesmo |
| **Hostinger** | DPA Hostinger | Verificar localização (BR) e backup |
| **AWS** | DPA AWS | Verificar KMS specific terms |
| **Backblaze B2** | DPA B2 | Verificar object lock + retention |
| **Pluggy/Belvo** (open banking) | DPA + autorização BCB | Quando integrar |
| **Focus NFe / NFE.io** | DPA fiscal | Quando integrar |

---

## Quem assina o postmortem

- Roldão (sempre — accountable)
- Agente que conduziu a investigação (responsible)
- Auditor de Segurança (consulted)
- Cliente afetado é informed (não consulted — não pode vetar)

---

## Trilha forense mínima

A `trilha-auditoria-agentes.md` (a criar) precisa responder em <5 minutos:
- **Quem (agente, sessão Claude/Codex)** tocou tenant Y entre HH:MM e HH:MM?
- **Qual tool call** foi feito?
- **Hash do prompt** que originou a ação?
- **Diff aplicado**?
- **Retenção:** mínimo 2 anos (ISO 17025 + LGPD).

Query padrão testada em drill trimestral.

---

## Em caso de incidente: ordem de ação

1. **PARAR** — suspender o agente / serviço afetado.
2. **PRESERVAR** — congelar logs, snapshot, NÃO sobrescrever evidência.
3. **CONTER** — limitar dano (revogar token, isolar tenant, etc.).
4. **COMUNICAR** — segundo prioridade: titulares LGPD (72h) → cliente → equipe → público.
5. **INVESTIGAR** — causa raiz.
6. **MITIGAR** — corrigir bug.
7. **DOCUMENTAR** — postmortem.
8. **APRENDER** — atualizar invariante / regra / hook pra prevenir recorrência.
