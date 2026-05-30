---
owner: roldao
revisado-em: 2026-05-29
status: stable
idioma: pt-BR
limite-linhas: 320
proposito: comparar custo × qualidade dos provedores de IA (texto, áudio→texto, busca por significado) para a decisão multi-modelo do ADR-0000
relacionado: [ADR-0000-uso-de-ia.md, ADR-0002-multi-empresa-e-armazenamento.md, ../descoberta/estimativa-custo-viabilidade.md]
---

# Benchmark de IA — custo × qualidade (apoio ao ADR-0000)

> **Pedido do dono (2026-05-29):** *"ter opções, pesquisar custo, qualidade etc; não ficar preso a apenas uma LLM."*
> Este documento é a **1ª versão** dessa pesquisa. Preços de IA mudam quase toda semana — as fontes estão no fim;
> reconferir antes de fechar contrato. Câmbio usado: **US$ 1 ≈ R$ 5,40** (referência de maio/2026; ajustar ao dia).

---

## 📌 Resumo pro dono (sem termo técnico)

O "cérebro" do Aferê Prumo não é **uma** inteligência só — são **três tipos de IA** trabalhando juntos:

1. **A que entende e escreve mensagens** (texto) — lê o que o cliente mandou e redige a resposta/orçamento.
2. **A que transforma áudio em texto** — como o atendimento é majoritariamente por áudio, ela "ouve" o WhatsApp.
3. **A que busca por significado** — acha a informação certa no cérebro pela intenção, não pela palavra exata.

**As três notícias boas:**

- **Custo é baixíssimo.** Em qualquer combinação, a IA custa **centavos de real por atendimento** (entre ~R$ 0,02 e ~R$ 0,50). O que pesa é o volume, não o preço unitário — cabe folgado na margem da assinatura.
- **Transcrever áudio pode custar ZERO.** Já temos um transcritor que roda **na nossa própria máquina** (foi ele que passou seus 1.120 áudios pra texto de graça). Isso significa custo zero **e** o áudio do cliente **não sai do Brasil** — ótimo pra lei de proteção de dados.
- **Tem opção brasileira forte.** A **Maritaca (modelo Sabiá)** cobra **em reais**, processa **no Brasil** e, num teste oficial de português, foi **melhor que o Claude "básico" custando 9× menos**. Encaixa direitinho na sua decisão de manter os dados no Brasil.

**A estratégia que recomendo** (detalhe na §6): não casar com um fornecedor só. Montar um **"roteador"** que escolhe a IA certa pra cada tarefa — a **mais barata** pras tarefas simples e de volume, a **melhor em português** pra falar com o cliente, e a **mais forte** só quando a conversa é difícil (orçamento alto, diagnóstico técnico). Trocar de fornecedor fica fácil — exatamente o que você pediu.

---

## 1. Os três tipos de IA que o produto usa

| Tipo | O que faz no Aferê Prumo | Onde aparece |
|---|---|---|
| **Texto (LLM)** | Entende a intenção, redige resposta, monta rascunho de orçamento/OS, classifica e roteia | Todos os agentes |
| **Áudio→texto (STT)** | Transcreve as mensagens de voz do WhatsApp antes de o cérebro entender | Atendimento (D-PROD-013) |
| **Busca por significado (embeddings + busca vetorial)** | Acha o trecho certo no cérebro de 1.099 fontes pela intenção | Cérebro / RAG (D-PROD-014) |

As três decisões de preço/qualidade são independentes — dá pra escolher um fornecedor diferente pra cada uma.

---

## 2. Modelos de TEXTO — custo (maio/2026)

Preço por **1 milhão de tokens** (≈ 750 mil palavras). "Entrada" = o que mandamos pra IA (pergunta + contexto);
"Saída" = o que ela escreve. A saída custa mais.

| Modelo | Entrada (US$/1M) | Saída (US$/1M) | Em R$ aprox. (in/out) | Faixa |
|---|---|---|---|---|
| Gemini 2.5 Flash-Lite | 0,10 | 0,40 | 0,54 / 2,16 | 🟢 ultra-barato |
| GPT-4o mini | 0,15 | 0,60 | 0,81 / 3,24 | 🟢 barato |
| GPT-5.4 Nano | 0,20 | 1,25 | 1,08 / 6,75 | 🟢 barato |
| Gemini 3.1 Flash-Lite | 0,25 | 1,50 | 1,35 / 8,10 | 🟢 barato |
| DeepSeek V4 (pesos abertos) | 0,30 | 0,50 | 1,62 / 2,70 | 🟢 barato (China) |
| Gemini 2.5 Flash | 0,30 | 2,50 | 1,62 / 13,50 | 🟡 médio-baixo |
| **Maritaca Sabiazinho** | **R$ 1,00** | **R$ 3,00** | **1,00 / 3,00** | 🟢 **barato + 🇧🇷 reais** |
| GPT-5.4 Mini | 0,75 | 4,50 | 4,05 / 24,30 | 🟡 médio |
| **Claude Haiku 4.5** | 1,00 | 5,00 | 5,40 / 27,00 | 🟡 médio (ótimo pt-BR) |
| **Maritaca Sabiá-3** | **R$ 5,00** | **R$ 10,00** | **5,00 / 10,00** | 🟡 **médio + 🇧🇷 reais** |
| Gemini 3.5 Flash | 1,50 | 9,00 | 8,10 / 48,60 | 🟡 médio |
| Gemini 3.1 Pro | 2,00 | 12,00 | 10,80 / 64,80 | 🟠 caro |
| GPT-5.4 | 2,50 | 15,00 | 13,50 / 81,00 | 🟠 caro |
| **Claude Sonnet 4.6** | 3,00 | 15,00 | 16,20 / 81,00 | 🟠 caro (referência qualidade) |
| Claude Opus 4.7 | 5,00 | 25,00 | 27,00 / 135,00 | 🔴 top de linha |
| GPT-5.5 | 5,00 | 30,00 | 27,00 / 162,00 | 🔴 flagship OpenAI |

> **Alavancas que cortam custo (valem pra quase todos):** *cache* de contexto repetido (−90% na entrada repetida),
> processamento em lote/*batch* (−50%) para o que não é urgente. Na prática derrubam a conta bem abaixo da tabela.

### 2.1 Traduzindo para "custo por atendimento"

Atendimento-modelo: ~8 trocas de mensagem, **15.000 tokens de entrada** (com busca no cérebro) + **2.500 de saída**.

| Modelo de texto | Custo do atendimento (texto) |
|---|---|
| Gemini 2.5 Flash-Lite | ~R$ 0,01 |
| GPT-4o mini | ~R$ 0,02 |
| Maritaca Sabiazinho | ~R$ 0,02 |
| Maritaca Sabiá-3 | ~R$ 0,10 |
| Claude Haiku 4.5 | ~R$ 0,15 |
| Claude Sonnet 4.6 | ~R$ 0,45 |

> Ou seja: mesmo no modelo "caro", um atendimento custa **menos de meio real** em texto. Com cache/lote, menos ainda.

---

## 3. Qualidade em PORTUGUÊS (o que importa pra falar com o cliente)

Os rankings famosos medem inglês, código e ciência — **não** medem português brasileiro. O teste mais relevante
pra nós é o **CAPITU** (segue-instruções em pt-BR) e o **Revalida** (prova médica em pt-BR):

- **CAPITU (seguir instruções em pt-BR):** modelos de raciocínio de ponta lideram (GPT-5.2 com raciocínio ≈ 98,5%).
  O dado que mais importa pra nós: **Sabiazinho-4 = 87,0%** a um custo de US$ 0,13, **contra Claude Haiku 4.5 = 73,5%**
  a US$ 1,12 — ou seja, **o modelo brasileiro foi melhor em português custando ~1/9**.
- **Revalida (prova de medicina, pt-BR):** GPT-4o e Claude Opus na frente (86,8% e 83,8%); vários Claude e Gemini
  acima da média humana. Confirma que os modelos "fortes" (Opus/Sonnet/GPT-5.x) são os mais confiáveis quando a
  resposta **não pode errar** (ex.: diagnóstico técnico, orçamento alto).

**Leitura prática:**
- Pra **conversa do dia a dia em português** (a maioria), um modelo barato bom em pt-BR (Sabiá/Sabiazinho, Gemini
  Flash, Claude Haiku) resolve com folga.
- Pra **raciocínio difícil que não pode errar** (orçamento alto, diagnóstico, conferência), vale pagar o modelo
  forte (Claude Sonnet/Opus ou GPT-5.4) — **mas só nesses casos**, porque é onde o erro custa caro.

---

## 4. Transcrição de ÁUDIO (capacidade central — o atendimento é por voz)

| Opção | Custo | Roda onde? | Observações |
|---|---|---|---|
| **whisper.cpp LOCAL** ⭐ | **R$ 0 (só nossa infra)** | **No Brasil, na nossa máquina** | **Já validado** — transcreveu seus 1.120 áudios. Dado **não sai**. Sem streaming ao vivo. |
| OpenAI GPT-4o mini transcribe | US$ 0,003/min (~R$ 0,016/min) | Fora (EUA) | Barato, simples, 99+ idiomas. Sem "quem-falou". |
| OpenAI Whisper / GPT-4o transcribe | US$ 0,006/min (~R$ 0,032/min) | Fora (EUA) | Padrão de mercado. |
| Deepgram Nova-3 (lote) | US$ 0,0043/min (~R$ 0,023/min) | Fora | Mais barato em escala; tem "quem-falou"; US$ 200 grátis. |
| Deepgram / AssemblyAI (tempo real) | US$ 0,0077–0,0092/min | Fora | Pra voz ao vivo (não é nosso caso hoje — WhatsApp é mensagem gravada). |

**Recomendação:** **whisper.cpp local como padrão** — é grátis, já funciona, e mantém o áudio do cliente **no Brasil**
(grande vantagem de LGPD e de marketing: "seu áudio não sai do país"). Deixar **OpenAI mini ou Deepgram como
reserva/transbordo** para picos de volume ou se precisarmos de "quem-falou" (separar vozes). Um atendimento com ~2 min
de áudio custa **R$ 0** (local) ou **~R$ 0,03** (pago).

---

## 5. Busca por significado (cérebro / embeddings)

Para a busca semântica do cérebro (D-PROD-014), o custo de "vetorizar" o conteúdo é **muito baixo** (modelos de
embedding ficam na casa de US$ 0,02–0,13 por 1M tokens) e é **uma vez só** por documento. Opções: modelos de
embedding da OpenAI/Google/Voyage, **ou um modelo aberto rodando local** (mantém tudo no Brasil, custo zero de API).
Como o acervo (1.099 fontes) já está coletado, a carga inicial é barata. Decisão fina vai junto com o pgvector (ADR-0002).

---

## 6. Estratégia recomendada — o "roteador" multi-modelo (atende ao pedido do dono)

Em vez de um fornecedor só, um **roteador de modelos** escolhe a IA certa por tarefa. Isto **é** o "não ficar preso a
uma LLM": trocar qualquer peça abaixo não mexe nos agentes.

| Tarefa | Modelo sugerido (1ª escolha) | Reserva | Por quê |
|---|---|---|---|
| Classificar/rotear mensagem (volume) | Gemini Flash-Lite **ou** Sabiazinho | GPT-4o mini | Centavos; tarefa simples |
| **Falar com o cliente em pt-BR** (compor resposta) | **Sabiá-4 (Maritaca)** | Claude Haiku / Gemini Flash | 🇧🇷 em reais, dado no Brasil, ótimo pt-BR/custo |
| Raciocínio difícil (orçamento alto, diagnóstico, conferência) | **Claude Sonnet 4.6** | GPT-5.4 / Opus | Mais confiável onde erro custa caro |
| **Transcrever áudio** | **whisper.cpp local** | OpenAI mini / Deepgram | Grátis + fica no Brasil |
| Busca por significado | Embedding local/barato | OpenAI/Voyage | Custo único, baixo |

> **Como isso protege você:** se a Maritaca subir preço, troco por Gemini/Claude sem reescrever nada. Se a OpenAI cair,
> uso outro. O roteador também é o **freio de custo**: tarefa cara só usa modelo caro quando realmente precisa.

---

## 7. Privacidade e "dados no Brasil" (liga com a hospedagem — ADR-0002)

Você decidiu guardar os dados **no Brasil**. Os modelos de IA, porém, processam o texto onde o fornecedor está:

- **whisper.cpp local** e **modelos abertos locais**: 100% no Brasil, dado **não sai**. ✅ Melhor cenário LGPD.
- **Maritaca/Sabiá**: empresa brasileira; **descarta o dado após a resposta** e não usa pra treino. Forte pra LGPD.
- **Claude / GPT / Gemini**: processam **fora** (EUA). Por isso a regra do ADR-0000 é obrigatória: **tirar o que
  identifica a pessoa antes de enviar** (nome, CPF, telefone) + **contrato de proteção de dados (DPA)** com cada um.

> Conclusão: priorizar **local + brasileiro** onde a qualidade permite (boa parte do volume), e mandar pra fora só o
> texto **já despersonalizado** quando precisar do modelo forte. Casa com a hospedagem no Brasil sem abrir mão de qualidade.

---

## 8. Recomendação final + o que falta você decidir

**Recomendo (técnico — pode seguir sem mexer):**
1. **Arquitetura multi-modelo com roteador** (já é a decisão de princípio do ADR-0000). ✅
2. **Transcrição local (whisper.cpp) como padrão.** ✅
3. **Embeddings/busca local ou barato.** ✅

**Precisa de você (decisão de produto/custo, na hora de cravar — não bloqueia começar):**
- Qual o **par default** pra falar com o cliente: começar pela **opção brasileira (Sabiá-4)** e medir qualidade no
  piloto, ou começar pelo **Claude (Haiku/Sonnet)** que é referência e medir custo? *(Minha recomendação: testar
  Sabiá-4 primeiro pelo casamento com "dados no Brasil" + custo, com Claude como rede de segurança nos casos difíceis.)*
- Esses números viram **decisão fechada (sub-ADR)** depois que o piloto medir qualidade real em pt-BR no nosso domínio
  (balanças/calibração) — aí escolhemos os modelos default com dado de verdade, não só benchmark de fora.

---

## 9. Fontes (maio/2026 — reconferir antes de contratar)

- Anthropic Claude — pricing: platform.claude.com/docs/en/about-claude/pricing
- OpenAI — pricing: developers.openai.com/api/docs/pricing
- Google Gemini — pricing: ai.google.dev/gemini-api/docs/pricing
- Maritaca AI (Sabiá) — maritaca.ai/api + docs.maritaca.ai
- DeepSeek — api-docs.deepseek.com/quick_start/pricing
- STT (Whisper/Deepgram) — comparativos diyai.io, deepgram.com/learn, tokenmix.ai
- Qualidade pt-BR — CAPITU (arxiv.org/pdf/2603.22576) e Revalida (PMC12082654)

> ⚠️ Preços e modelos mudam rápido. Esta tabela é fotografia de **maio/2026**. O valor do documento está na
> **estratégia** (multi-modelo + local + brasileiro), que não envelhece; os números, sim — reconferir na hora.
