---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Anthropic API — LLM (Claude)

## Resumo

| Item | Detalhe |
|------|---------|
| Função | Modelo LLM principal — Claude Code (Sonnet/Opus) usado em desenvolvimento + auditores Família 5 |
| Status | ✅ ativo (uso em desenvolvimento já acontece) |
| Anti-corrosion | LiteLLM gateway (planejado quando código existir) — `infrastructure/llm/litellm_provider.py` |
| Custo aprox | tokens — R$ 0.50-2 por sessão Claude Code; auditores ~R$ 1.50 por PR |

---

## Por que Anthropic

- Modelos avançados (Opus 4.7, Sonnet 4.6) competitivos com GPT-4 e Gemini
- Política "não-treinar com dados de cliente API" — adequado pra dado regulado
- Anthropic Brasil tem suporte
- Claude Code é parte do harness deste projeto

---

## Uso atual

1. **Claude Code (desenvolvimento)** — Roldão usa direto pra construir o produto
2. **Auditores Família 5** (camada A subagent + camada B GitHub Action) — Sonnet/Opus em pre-commit/pre-merge
3. **Subagents especialistas** (tech-lead, advogado, corretora, RBC) — invocados sob demanda

---

## Uso futuro (V2)

- Chatbot CS (cliente final do tenant pergunta status OS, fatura) — Sonnet via LiteLLM
- Classificação de e-mail / triagem de reclamação
- Sumarização de incidente

Tudo passando por LiteLLM gateway com sanitização de PII.

---

## LiteLLM gateway (planejado)

Camada intermediária pra:
- Sanitizar PII antes de enviar prompt
- Audit log de cada invocação
- Rate limit por tenant
- Fallback pra outro provider (Bedrock, etc.) se Anthropic indisponível
- Cache de respostas idênticas

---

## DPA / LGPD

Ver `conformidade/comum/transferencia-internacional.md` §5:
- Anthropic é provedor USA — transferência internacional
- Base legal: legítimo interesse + execução de contrato
- DPA Anthropic (Data Processing Addendum) — verificar termos atuais quando contratar conta empresarial
- Subprocessadores listados na lista pública Aferê (V2)

---

## Custo monitorado

- API Anthropic billing — verificar mensal
- Threshold inicial: R$ 1.500/mês durante Foundation F-A (critério ADR-0001 Portão 3)
- Recalibrar pós-Wave A

---

## Pendências

- [ ] Configurar LiteLLM self-hosted (Foundation F-G)
- [ ] DPA empresarial Anthropic (quando 1º cliente externo aparecer — V2)
- [ ] Lista pública de subprocessadores (V2)
- [ ] Painel Grafana de uso/custo (V2 quando deploy)

---

## Referências

- `arquitetura/anti-corrosion-layer.md` (porta LLM)
- `conformidade/comum/transferencia-internacional.md` §5
- `seguranca/agente-input-nao-confiavel.md`
- `governanca/metricas-operacao-agentes.md`
- ADR-0000 (uso de IA)
