---
owner: roldao
revisado-em: 2026-05-29
status: stable
idioma: pt-BR
proposito: resultado da auditoria CEGA das decisões de arquitetura (10 arquitetos Opus independentes + 1 auditor-chefe), sem viés, comparada às decisões da equipe
relacionado: [ADR-0000-uso-de-ia.md, ADR-0001-stack-e-integracao-afere.md, ADR-0002-multi-empresa-e-armazenamento.md]
dados-brutos: auditoria-cega-arquitetura-2026-05-29.json
---

# Auditoria cega da arquitetura — Aferê Prumo (2026-05-29)

> **Método (pedido do dono):** 10 arquitetos independentes rodando em **Opus 4.8, esforço máximo**, isolados,
> cada um decidindo a arquitetura **do zero** a partir de um briefing neutro do produto — **sem ver nenhuma
> decisão da equipe** e instruídos a não ler o repositório. Depois, um **auditor-chefe** (11º agente) mediu o
> consenso e comparou com as decisões já tomadas. 461k tokens, ~7 min.

## Placar: 5 validadas · 2 parciais · 1 desafiada

| Tema | Veredito | Consenso independente |
|---|---|---|
| Arquitetura (serviço vizinho Python, só via API do Aferê) | ✅ **VALIDADA** | **10/10** serviço separado + Python + integra só por REST/DRF |
| Hospedagem (Brasil / AWS São Paulo) | ✅ **VALIDADA** | **10/10** Brasil · 9/10 AWS sa-east-1 |
| Busca semântica (pgvector no Postgres) | ✅ **VALIDADA** | **10/10** pgvector sem banco vetorial dedicado |
| Isolamento multi-tenant (RLS herdado do Aferê) | ✅ **VALIDADA** | **10/10** RLS no banco + defesa em profundidade |
| Canais (WhatsApp oficial via BSP) | ✅ **VALIDADA** | **10/10** Cloud API oficial via BSP, zero não-oficial |
| LLM (multi-modelo) | 🟡 **PARCIAL** | Estratégia 10/10 validada; **default Sabiá-na-frente: 0/10 citaram Maritaca** |
| Transcrição (whisper local) | 🟡 **PARCIAL** | Direção local 9/10; mas 6/10 começariam com API paga e migrariam |
| Orquestração (ferramenta visual própria) | 🔴 **DESAFIADA** | Código próprio: consenso ✅; **ferramenta visual própria: 8/10 REJEITAM** |

## Veredito geral do auditor-chefe

> As decisões da equipe se sustentam **bem**. Em **5 dos 8 temas** são **idênticas** ao consenso de 10
> arquitetos cegos (serviço Python separado falando só via DRF; Brasil/AWS; pgvector no Postgres; RLS herdado
> do Aferê; WhatsApp oficial via BSP) — convergência independente desse tipo raramente é coincidência, é sinal
> forte. As 2 apostas que divergem (Maritaca/Sabiá na frente; whisper local desde o dia 1) **não são erros** —
> são coerentes com uma prioridade que a equipe tem e os independentes em maioria não tiveram: **fechar toda a
> porta de saída de dado do Brasil, até a inferência** (força real de LGPD). O **único ponto reprovado de forma
> contundente** é "construir ferramenta visual de fluxos própria desde o início": **8/10 rejeitam** como
> scope-creep para equipe pequena, e **nenhum endossa**.

## O que reconsiderar (5)

1. **Orquestração (prioridade máxima):** NÃO construir editor visual de fluxos próprio desde o início (8/10 rejeitam). Manter o "código próprio" (acertado), modelar fluxos em **LangGraph** (interrupt nativo para aprovação humana) e entregar a flexibilidade-por-empresa como **configuração em dados** (tabelas por tenant: setores ativos, prompts, tom, limiares) — dá ~90% do valor sem construir o editor. Builder visual, se um dia, é fase tardia.
2. **LLM default:** antes de cravar Sabiá na frente, **teste cego Sabiá × Claude Haiku** em tool-calling (acionar a API do Aferê sem alucinar parâmetro) e raciocínio metrológico. Manter Sabiá no volume barato pt-BR e rotear o **difícil/tool-use crítico para o Claude** (o roteador já permite).
3. **Transcrição:** mesmo indo de whisper local, adotar (a) interface plugável com **fallback gerenciado** para picos; (b) **glossário de domínio** no Whisper (OIML, Inmetro, "célula de carga", "classe III", números de série) — STT genérico erra jargão e nº de série errado vira orçamento errado; (c) cravar **large-v3** como modelo.
4. **Busca semântica:** adicionar **busca HÍBRIDA** (vetor + full-text/BM25 do Postgres) — códigos de norma/portaria são termos exatos que a busca por significado pura erra. E separar **normas públicas** (namespace global) de docs por-tenant.
5. **Canais:** tornar **explícito o painel/console web de aprovação humana** como item da V1 (7/10 o tratam como canal obrigatório — "sem ele o human-in-the-loop não tem onde acontecer"). No BSP, preferir modelo **own-your-WABA** (ex.: 360dialog): a conta WhatsApp fica no nome do cliente, portável, sem lock-in.

## Pontos cegos (8) — o que ninguém da equipe tinha verbalizado

1. **Vazamento no tier assíncrono:** job Celery sem tenant setado pode varrer dados de todas as empresas → middleware que **falha fechado** + tenant_id obrigatório no payload de toda task.
2. **Filtro de tenant no pgvector ANTES do ranqueamento** — senão um vizinho semântico de outra empresa vem no topo e vaza.
3. **Segredos/tokens por tenant** (token WhatsApp, chave da API do Aferê) em cofre — nunca um global.
4. **Testes automatizados de vazamento cross-tenant como gate de CI** — isolamento vira invariante verificada por robô, não promessa.
5. **Co-desenhar JÁ os contratos REST do Aferê** (idempotência nas escritas, webhooks de evento, paginação, batch) — o Aferê está em construção; é a janela barata para acertar a fronteira.
6. **Citação de fonte no RAG** (documento + trecho) — em metrologia legal, resposta sem origem auditável vira não-conformidade.
7. **Janela de 24h + templates aprovados da Meta restringem proatividade** — avisos de recalibração precisam virar **templates pré-aprovados** na Meta (planejar, não descobrir em produção).
8. **Cache de prompt** (system prompt longo + contexto RAG repetido) corta muito o custo de LLM — alavanca de margem.

## Encaminhamento

- **Refinamentos técnicos (2–5 e pontos cegos):** são melhorias que **enriquecem** as decisões sem mudá-las → incorporar nos ADRs (trabalho do agente).
- **LLM e transcrição:** decisões da equipe mantidas como **apostas conscientes de LGPD**, com a ação "testar no piloto antes de cravar" (já era o plano).
- **Ferramenta visual própria:** único ponto que a auditoria reprova → **decisão do dono** (o valor "configurável por empresa" se entrega por configuração em tabelas; o editor visual é que é o scope-creep).
