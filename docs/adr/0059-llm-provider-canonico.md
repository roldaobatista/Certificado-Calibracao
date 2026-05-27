---
adr: 0059
titulo: Porta LLMProvider canônica + INV-LLM-001..010
owner: roldao
revisado-em: 2026-05-27
status: reservada
data: 2026-05-23
reservado-em: 2026-05-23 (Onda 0 plano-v2)
arquivo-fisico-criado-em: 2026-05-27 (Onda PRE-A.2 auditoria 10 lentes pré-Wave A — resolve drift estrutural §11 AGENTS)
ativacao-em: antes 1ª feature LLM-em-produto (Wave B)
bloqueia-fase: Wave B (qualquer módulo que use LLM em produto — chatbot suporte, classificador NC, copilot técnico)
depende-de: ADR-0021 (anonimização vs retenção LGPD), ADR-0067 (perfil regulatório do tenant)
---

# ADR-0059 — Porta LLMProvider canônica + INV-LLM-001..010

> **Status:** **RESERVADA** — esqueleto criado em 2026-05-27 (Onda PRE-A.2 auditoria 10 lentes pré-Wave A) pra resolver drift de §11 AGENTS.md que citava esta ADR sem arquivo físico existir. Conteúdo será preenchido **antes da 1ª feature LLM em produto** (Wave B).
>
> **Não tratar como decidida.** Hoje Aferê usa Claude Code para desenvolvimento (não em produto). Quando aparecer LLM em produto (chatbot suporte, classificador NC, copilot técnico), esta ADR é pré-requisito.

## Escopo previsto (a detalhar)

- Porta canônica `LLMProvider` na anti-corrosion-layer (19ª porta — ver `docs/arquitetura/anti-corrosion-layer.md`).
- Adapters: Anthropic Claude (Trust Policy + Zero Data Retention), OpenAI, eventual self-hosted.
- **INV-LLM-001..010 a redigir** cobrindo:
  - Redaction PII pré-envio (CPF, e-mail, endereço, dado biométrico).
  - Vector DB tenant namespace (cada tenant tem espaço isolado em embeddings).
  - Jailbreak/injection tests obrigatórios em CI.
  - Orçamento por usuário (rate-limit + cost cap).
  - Audit log prompt/resposta (sem PII, com hash).
  - Retenção ≤30d (alinhada ZDR Anthropic).
  - Sanitize resposta (saída não contém PII de outros tenants).
- Hook `llm-pii-redaction-check`.
- Matriz feature×perfil ADR-0067: perfil A pode ter LLM em assistente ISO; perfil D pode ter chatbot comercial.

## Why reservada hoje

Memória `project_sem_contratacoes_externas_ate_producao` 2026-05-27 + `project_sem_cliente_externo_agora` 2026-05-17: sem cliente externo + sem produto LLM-em-produto, ADR não tem urgência.

## Quando promover

Quando Roldão decidir adicionar feature LLM em módulo de produto. Trigger possíveis:
- Wave B `suporte-saas` com chatbot.
- Wave B `qualidade` com classificador NC.
- V2 BI semântico em linguagem natural.
