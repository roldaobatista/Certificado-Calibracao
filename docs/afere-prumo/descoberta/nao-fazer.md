---
owner: roldao
revisado-em: 2026-05-28
status: stable
ordem-descoberta: 08/17
proximo: docs/descoberta/riscos.md
idioma: pt-BR
limite-linhas: 120
proposito: lista do que o produto NUNCA fará (ou não fará na V1).
---

<!--
template: nao-fazer.md
destino: docs/descoberta/nao-fazer.md
uso: define non-goals em nível de produto. Cada item bloqueia adição não-solicitada.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3 + Princípio §1.4 (Non-goals explícitos).
limite: ≤120 linhas.
-->

# Não-fazer — Aferê Prumo

> Tudo aqui é proibido sem aprovação explícita do dono. Cada item evita escopo inflado por agente IA ou contributor entusiasmado.

## 1. Não-fazer nunca (princípios)

> **Princípio-mãe (do plano do dono):** *"uma IA que opera **com você, não no lugar de você**".*
> 100% das ações visíveis ao cliente passam pela Inbox de aprovação; decisão irreversível nunca
> sai sem humano. Tudo começa no **Nível 1 (assistido)** e só sobe de automação quando os dados provarem.
>
> **Nível de automação é graduável POR TIPO DE AÇÃO (não um dial único)** — lição da análise de
> concorrentes: orçamento/cobrança/oferta/**certificado** = travados em aprovação humana **sempre**
> (NF-001/NF-002). FAQ pura/horário são os candidatos naturais a soltar primeiro, **mas nada vira
> auto-envio sem o dono decidir caso a caso** (D-PROD-010): por ora, **tudo que vai ao cliente passa
> pela Inbox**. H-006 valida o critério numérico; a decisão de soltar é do dono.
>
> **Gatilhos de escalonamento nomeados** (além de "tudo passa pela Inbox") — marcam o MOTIVO no item
> para priorizar a fila: (a) baixa confiança da IA; (b) cliente irritado/insatisfeito; (c) assunto
> fora do domínio do agente; (d) **orçamento/serviço acima de R$ 10.000** → a IA **monta o rascunho** e o
> escala pro dono **revisar/aprovar** com marcação "valor alto" (D-PROD-019 — não é mais "nem rascunha"); (e) dado
> não encontrado no Aferê; (f) assunto quente/regulado (certificado, prazo legal, cobrança, cancelamento) → nem
> vira rascunho automático, vai direto pro humano; (g) **cliente pede humano / reclama do atendimento da IA**
> ("quero falar com alguém/uma pessoa", "quero reclamar do atendimento") → **handoff IMEDIATO** pro atendente,
> sem insistir nem deixar na fila (D-PROD-020, CDC).

| ID | Item | Motivo |
|---|---|---|
| NF-001 | A IA não emite certificado nem assina por conta própria | Conteúdo técnico segue Inmetro/RBC; exige **2 conferências** (Metrologia + Responsável pela Emissão). |
| NF-002 | A IA não envia ao cliente resposta, orçamento, cobrança ou oferta sem aprovação humana | "Com você, não no lugar de você"; protege CDC. (H-005) |
| NF-003 | A IA **nunca afirma** acreditação RBC ou ISO/IEC 17025, nem usa o termo "RT" | A empresa não tem RT habilitado (CREA/CRQ); usar "Responsável pela Emissão" + Disclaimer A sempre. |
| NF-004 | Nenhum agente **inventa** dado (nome, prazo, valor, nº de série) **nem diagnóstico/procedimento técnico** | Dado operacional → consulta o Aferê. Conhecimento técnico (código de erro, procedimento de calibração, diagnóstico) → só do **cérebro curado** acima do limiar de confiança; se não achar, marca **lacuna de conhecimento** e escala — nunca chuta diagnóstico (R-017). Cita a fonte sempre. |
| NF-005 | Nenhum agente **sai do próprio domínio** | Atendimento não mexe em financeiro; estoque não emite certificado — permissão por setor. |
| NF-006 | Não enviar PII desnecessária do cliente ao LLM | Minimização (LGPD); **pseudonimização pré-LLM por tokens reversíveis** (cofre de chave fora do LLM) — política operacional, exemplo antes→depois e log em `conformidade/lgpd/retencao-dados.md §7.1`. Falha de mascaramento → não envia, vai para revisão humana (R-004). |
| NF-007 | Não substituir o instrumento de medição nem fazer pesagem fiscal | É camada de gestão/atendimento, não metrologia legal. |
| NF-008 | A IA **não responde sobre marca/modelo fora do acervo** do cérebro | O cérebro cobre principalmente Toledo + marcas do acervo (R-018); pergunta sobre marca não coberta → fila com motivo "acervo incompleto", vira backlog de cadastro. Evita diagnóstico sem base (liga a NF-004). |
| NF-009 | A IA **não passa conhecimento técnico de acesso restrito a cliente externo** | Cliente só recebe informação de **uso/operação da balança** + seus próprios dados (OS, certificado, prazo). Procedimentos internos de calibração/manutenção, diagnóstico profundo, códigos de erro internos, ajustes e parâmetros metrológicos são **restritos a técnicos/funcionários autenticados** (D-PROD-016). Pergunta técnica restrita de cliente → resposta de uso + oferta de serviço, nunca o procedimento. |
| NF-010 | A IA **nunca orienta o cliente a abrir a balança ou a romper lacre/selo metrológico** (Inmetro/IPEM) | Regra dura do dono (2026-05-29). Romper lacre/selo é **infração de metrologia legal** (Lei 9.933/99) e **invalida a balança** para uso comercial/fiscal. Qualquer dúvida que levaria a abrir o equipamento (ajuste de span/ganho, troca de peça interna, acesso ao modo calibração lacrado) vira **oferta de visita técnica** — nunca instrução. O lacre só é rompido por técnico autorizado, em serviço, com registro e relacre conforme a norma. Liga a NF-007/NF-009 e D-PROD-016. |

## 2. Não-fazer na V1 (escopo da primeira entrega)

> Pode entrar em fases seguintes; agora, não.

| ID | Item | Quando reavaliar (gatilho) |
|---|---|---|
| NF-V1-001 | ~~Revender para outras empresas~~ **(REVOGADO 2026-05-28)** — vender por assinatura É o objetivo. A arquitetura nasce **multi-tenant + configurável** desde o dia 1. O que fica para depois é **só abrir comercialmente** para clientes externos pagantes — **após o dogfooding** na Balanças Solution validar. | Sequência (dogfooding → abrir), não non-goal. |
| NF-V1-002 | Integração fiscal / emissão de NF-e | Quando a gestão de orçamento/OS estiver consolidada e houver necessidade real. |
| NF-V1-003 | Previsão de demanda e relatórios analíticos avançados | Depois de acumular dados das fases iniciais. |
| NF-V1-004 | App mobile nativo dedicado | Começar por WhatsApp + web responsivo; reavaliar se a equipe de campo precisar. |

## 3. Não-fazer porque outro produto/serviço faz melhor

> Onde integrar em vez de construir.

| ID | Função | Por quem | Como integrar |
|---|---|---|---|
| NF-OUT-001 | Canal de mensagem com o cliente | WhatsApp Business (Meta/BSP) | API oficial |
| NF-OUT-002 | "Cérebro" de linguagem natural (LLM) | Provedor de IA (ex.: Anthropic) | API, via camada de adaptação |
| NF-OUT-003 | Emissão de NF-e (se um dia precisar) | Provedor fiscal (ex.: NFe.io/Focus) | API |

## 4. Tentações que voltam (refresh periódico)

- "Fazer tudo de uma vez (atendimento + interno + análise + cérebro)" — motivo: trava o projeto; contramedida: **CONSTRUÇÃO** faseada (R-001). A visão completa fica documentada, a entrega técnica é fatiada. ⚠️ **Exceção decidida pelo dono (D-PROD-018, 2026-05-29):** no **piloto** (dogfooding interno) todos os agentes são **ligados juntos**, mas **em Nível 1** (nada ao cliente sem aprovação) — ligar ≠ dar autonomia; a maturação de cada agente segue gradual.
- "Deixar a IA fechar venda/orçamento sozinha pra ser mais rápido" — motivo: risco de erro vinculante (NF-002).
- **Anti-suite (não-vire):** (a) não adotar plataforma horizontal de prateleira (Dynamics/Salesforce/ServiceNow/Zoho) **como núcleo** só para ter agente pronto — o valor está no domínio + Aferê, não na camada genérica; (b) não virar central de atendimento/CRM/helpdesk genérico (tickets, FAQ avançada, relatórios estilo Freshdesk) — **integrar, não reconstruir**; (c) não virar plataforma de RPA/automação genérica ("robôs que clicam em telas"); (d) não responder dúvida por "achismo do LLM" — só do cérebro curado + Aferê. Motivo: comoditização (R-009) — nosso fosso é domínio + fonte de verdade própria.
- "Acelerar além do Nível 1 porque o concorrente resolve sozinho" — motivo: fere D-PROD-006 e expõe a CDC/certificado (R-011). Só graduar por métrica de saúde do agente.

## Como mudar este arquivo

- Mover item de "V1 não" para "V1 sim" exige ADR + atualização do faseamento.
- Adicionar `NF-NNN` novo: PR dedicado, justificativa, link para evidência (entrevista, dado, decisão).
- Remover item: exige reunião explícita com dono — não basta consenso de devs.

## Critério para promover de `draft` para `stable`

- [ ] ≥3 itens em §1 (não-fazer-nunca) com motivo.
- [ ] Itens da V1 têm gatilho de reavaliação concreto.
- [ ] §3 (parceria) tem ≥1 caso quando aplicável (ou marcado N/A).
