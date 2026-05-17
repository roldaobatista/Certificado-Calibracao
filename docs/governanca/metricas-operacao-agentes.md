---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Métricas de operação dos agentes

> **Pra quê:** medir se "100% agentes IA" entrega valor real ou queima orçamento. Sem essas métricas, LEAP F-1 não é falsificável.

---

## 1. Eixos de medição

| Eixo | Mede | Meta janela atual |
|------|------|---------------------|
| **Custo (tokens/$)** | Quanto se gasta em LLM por unidade entregue | ≤ R$ 1.500 por mês durante F-A (4-6 semanas); calibrar depois |
| **Retrabalho** | % de PRs/commits que foram desfeitos ou reescritos em ≤ 7 dias | ≤ 15% |
| **Intervenção Roldão** | Vezes/semana que Roldão precisou entrar no código | ≤ 2/semana (critério mortalidade ADR-0001 Portão 3) |
| **Bugs SEV-1 em prod** | Bugs graves chegando a usuário (dogfooding ou externo) | ≤ 3 no período de avaliação |
| **Tempo até entrega** | Tempo de "tarefa aberta" → "PR mergeada" | Acompanhar tendência |
| **Falsos positivos auditores** | Vezes que auditor bloqueou mas Roldão derrubou veto | ≤ 10% dos vetos |
| **Falsos negativos** | Bug entrou apesar de PASS dos auditores | 0 idealmente; >2/mês dispara revisão de prompt |

---

## 2. Como coletar

Janela atual (sem deploy):
- Tokens: consumir API Anthropic billing (manualmente — Roldão verifica mensal)
- Retrabalho: `git log` + análise de mensagens "revert", "redo"
- Intervenção Roldão: log da sessão Claude Code (`~/.claude/projects/...`)
- Bugs SEV-1: anotação manual em `governanca/trilha-auditoria-agentes.md`
- Tempo até entrega: timestamp de issue / PR
- Falsos positivos auditores: log de quando Roldão usou `APROVADO POR ROLDAO` pra derrubar veto

V2 (deploy autorizado): automatizar via Grafana dashboard "Operação dos agentes".

---

## 3. Drill mensal

Roldão faz revisão mensal:

1. **Tokens gastos no mês:** vs orçamento (R$ 1.500 alvo Foundation; recalibrar pós-Wave A)
2. **Tarefas entregues:** quantas, qual qualidade
3. **% de PASS dos auditores:** se cai muito, revisar prompts
4. **% de retrabalho:** se sobe, investigar causa
5. **Roldão se sente "preso ao código"?** Resposta subjetiva — sinal qualitativo

Registrar em `status-semanal.md`.

---

## 4. Gatilhos de revisão de modelo

| Sinal | Ação |
|-------|------|
| Tokens > R$ 1.500/mês 2 meses seguidos | Investigar; revisar prompts dos auditores (caros) ou trocar modelo padrão |
| Roldão intervindo > 2x/sem por 4 semanas | Disparar plano B (tech-lead consultivo R$ 8-15k/mês) |
| Bugs SEV-1 > 3 no mês | Revisar suite de testes + critérios de auditor |
| Falsos positivos auditor > 20% | Revisar prompt do auditor (versão nova `versao_prompt`) |
| Falsos negativos | Adicionar regra/teste; revisar prompt |

---

## 5. Reporting

- **Status semanal:** topo do `governanca/status-semanal.md` mostra métricas da semana
- **Status mensal:** revisão completa + decisão (continua, ajusta prompt, troca modelo, plano B)
- **Status trimestral:** revisão estratégica (LEAP F-1 ainda válido? está funcionando?)

---

## 6. Custo médio (referência)

| Operação | Custo aprox em tokens (estimativa) |
|----------|-------------------------------------|
| Sessão Claude Code média | ~50k-200k tokens |
| Auditor Segurança em 1 PR | ~30k tokens (Sonnet) |
| Auditor Qualidade em 1 PR | ~25k tokens (Sonnet) |
| Auditor Produto em 1 PR | ~50k tokens (Opus) |
| Discovery batch (12 agentes paralelo) | ~1M tokens (Sonnet) |

Convertendo: ~R$ 0.50-2.00 por sessão; ~R$ 0.50-1.50 por PR auditada; ~R$ 30-60 por discovery batch grande.

---

## 7. Pendências

- [ ] Coleta automatizada (Grafana dashboard) — V2 com deploy
- [ ] Integração API Anthropic billing — verificar se há endpoint público de uso
- [ ] Hook de tracking de "Roldão intervindo" — semi-automático via análise de sessão
- [ ] Lista de falsos positivos auditores — começar a coletar

---

## 8. Referências

- ADR-0001 Portão 3 (critérios de mortalidade)
- `auditor-*-prompt.md` (calibração)
- `status-semanal.md`
- `trilha-auditoria-agentes.md`
