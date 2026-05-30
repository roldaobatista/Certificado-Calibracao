---
owner: roldao
revisado-em: 2026-05-28
status: stable
ordem-descoberta: 16/17
proximo: docs/descoberta/sintese-final.md
idioma: pt-BR
limite-linhas: 300
proposito: glossário de termos do produto e do domínio para manter linguagem comum entre dono, equipe e agente IA
---

<!--
template: glossario.md
destino: docs/glossario.md
uso: glossário de termos do produto/negócio do projeto destino.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C1
-->

# Glossário do Produto — Aferê Prumo

> **Escopo deste glossário:** termos do **domínio do produto** — entidades de negócio, papéis, estados de máquina, abreviações usadas em código.
>
> **Não confundir com `GLOSSARIO-ROLDAO.md` (raiz):** aquele traduz jargão TÉCNICO (PR, commit, lint, deploy, build, CI...) para linguagem de dono não-técnico. Este aqui é jargão de NEGÓCIO/PRODUTO. Não duplicar entradas entre os dois.

> Toda outra doc usa estes termos. Inconsistência de termo = bug.
> Sinônimos NÃO entram. Se faltar termo, adicionar aqui antes de escrever doc/código novo.

## Tabela canônica

| Termo | Definição | Tradução PT↔EN | Evite sinônimos de |
|---|---|---|---|
| aferição | Verificação se o instrumento mede dentro da tolerância legal (sem necessariamente ajustar). | verification | conferência, teste |
| agendamento | Marcação de uma visita/serviço (calibração, manutenção, entrega/retirada de locação) em data e responsável. | scheduling | marcação, booking |
| atendimento | Interação com um cliente (dúvida, pedido, orçamento), tipicamente iniciada no WhatsApp. | service interaction | conversa, chamado, ticket |
| balança | Instrumento de medição de massa, comercial ou industrial — o objeto central do negócio. | scale | balança, equipamento (quando genérico) |
| calibração | Serviço de comparar a balança com padrão e ajustar/atestar, gerando certificado com prazo. | calibration | aferição (são distintas), regulagem |
| certificado de calibração | Documento que atesta a calibração conforme norma (Inmetro/RBC), com validade/prazo. | calibration certificate | laudo, atestado |
| cliente | Pessoa física ou jurídica atendida pela Balanças Solution (compra, aluga, conserta ou calibra). | customer | usuário, comprador, lead, contratante |
| contrato | Acordo recorrente com cliente (ex.: calibração periódica, locação) com prazo a renovar. | contract | acordo, plano |
| equipamento | Item físico associado a um cliente (uma balança específica) com histórico próprio. | equipment | aparelho, item, máquina |
| guardrail | Métrica que não pode piorar quando a métrica principal melhora (ver `metricas-chave.md`). | guardrail | trava, limite |
| histórico do equipamento | Registro de todos os serviços, peças e calibrações feitos num equipamento. | equipment history | ficha, prontuário |
| IA / LLM | "Cérebro" de linguagem natural que entende mensagens e gera respostas/rascunhos. | AI / LLM | bot, robô, assistente (quando genérico) |
| lead | Contato ainda sem relação comercial fechada. | lead | prospect, interessado, contato |
| locação | Aluguel temporário de balança, com ciclo de entrega, prazo e retirada/cobrança. | rental | aluguel, leasing |
| manutenção | Serviço de conserto (corretiva) ou prevenção (preventiva) de um equipamento. | maintenance | assistência, reparo, conserto |
| módulo | Recorte funcional do produto com spec.md, plan.md e tasks.md próprios. | module | feature, área, seção |
| ordem de serviço (OS) | Registro de um serviço a executar/executado (manutenção/calibração), com itens e status. | work order | chamado, ticket de serviço |
| orçamento | Proposta de preço para um pedido do cliente (venda, serviço ou locação). | quote | proposta, cotação, estimativa |
| prazo de calibração | Data em que a calibração de um equipamento vence e precisa renovar. | calibration due date | vencimento, validade |
| rascunho (de orçamento/resposta) | Conteúdo gerado pela IA que precisa de revisão humana antes de ir ao cliente. | draft | minuta, pré-orçamento |
| RBC | Rede Brasileira de Calibração — credenciamento de laboratórios (contexto do certificado). | RBC | — |
| revisão humana | Passo obrigatório em que uma pessoa aprova o que a IA produziu antes de enviar/fechar. | human review | aprovação, conferência |
| selo / Inmetro / IPEM | Marca legal de conformidade metrológica; Inmetro (federal) e IPEM (estadual) fiscalizam. | seal / Inmetro / IPEM | lacre, certificação |
| usuário | Pessoa que opera o sistema (equipe interna) ou interage com a IA (cliente). | user | operador, conta, perfil |

### Termos adicionados em 2026-05-29 (reordenar alfabeticamente na próxima revisão)

| Termo | Definição | Tradução PT↔EN | Evite sinônimos de |
|---|---|---|---|
| agente (de IA) | Componente de IA responsável por um setor/tarefa, com contrato próprio (o que faz, o que nunca faz, quando escala) — ver `agentes.md`. | AI agent | bot, assistente (genérico) |
| busca semântica / RAG | Achar a informação certa pela **intenção/significado**, não pela palavra exata; base do cérebro (D-PROD-014). | semantic search / RAG | busca por palavra-chave |
| cérebro (técnico) | Base de conhecimento **não-estruturado** com busca por significado (manuais, calibração, erros, normas, Aferê) que dá autoridade técnica à IA. | knowledge base / brain | banco de dados (é diferente do Aferê) |
| classe de exatidão | Categoria metrológica do instrumento/peso (ex.: pesos E1/E2/F1/F2/M1/M2/M3 — OIML R111). | accuracy class | precisão |
| metrologia legal | Campo regulado que controla instrumentos de medição de uso obrigatório legal (balança é metrologia legal). | legal metrology | metrologia (genérica) |
| multi-tenant (multi-empresa) | Arquitetura em que várias empresas-clientes usam o mesmo sistema com **isolamento total** entre elas. | multi-tenant | multiusuário |
| OIML | Organização Internacional de Metrologia Legal — emite recomendações (R76 balanças, R111 pesos) base das portarias brasileiras. | OIML | — |
| peso padrão | Massa de referência rastreável usada para calibrar/verificar balanças (Portaria Inmetro 289/2021). | standard weight / mass standard | peso (genérico) |
| RTM | Regulamento Técnico Metrológico — a norma do Inmetro que rege um tipo de instrumento (ex.: Portaria 157/2022 p/ balanças). | technical metrological regulation | norma (genérica) |
| transcrição / STT | Conversão de **áudio (voz) em texto** — capacidade central, pois o atendimento é majoritariamente por áudio (D-PROD-013). | transcription / speech-to-text | legenda |
| handoff | Passagem imediata de um atendimento da IA para um **humano** (ou entre agentes), levando o contexto. Gatilho forte quando o cliente pede pessoa ou reclama da IA (D-PROD-020). | handoff | transferência, repasse |
| UMC (Unidade Móvel de Calibração) | **Caminhão** da Balanças Solution **carregado com os pesos padrão**, usado para calibrar balanças **rodoviárias** e **industriais de alta capacidade**; tem **motorista próprio**. O **técnico vai à parte (carro pequeno)** — para serviços menores, vai só o técnico, sem o UMC. Base do R$/km de deslocamento do caminhão. | mobile calibration unit | caminhão (genérico), munck |
| multimodal (visão) | Capacidade da IA de **ler imagem** (foto/print do cliente — ex.: erro no display) além de texto e áudio, respondendo no nível de acesso certo (D-PROD-016, NF-010). | multimodal / vision | — |
| **Aferê Prumo** | **Nome do PRODUTO** (a camada de IA, add-on do ERP). Tagline: "a IA que mantém sua operação no prumo". **Não confundir:** *Aferê* = ERP-núcleo; *Balanças Solution* = 1º cliente (empresa). Substitui o provisório "Balanças Solution IA" (D-PROD-023). | (nome próprio) | "a IA", "infra de IA", "Balanças Solution IA" |

## Como atualizar

1. Adicionar linha nova respeitando ordem alfabética por termo.
2. Preencher TODAS as colunas. Coluna "Evite sinônimos de" é OBRIGATÓRIA — é o que blinda contra termo solto em outra doc.
3. Bump de `revisado-em` no frontmatter.
4. Se o termo aparece em código, abrir ADR se mudar a tradução PT↔EN (rename custa).

## Critério para promover de `draft` para `stable`

- [ ] ≥20 termos do domínio cadastrados na tabela canônica.
- [ ] Todas as colunas preenchidas em cada linha, inclusive "Evite sinônimos de".
- [ ] Tabela em ordem alfabética por termo.
- [ ] Nenhuma entrada duplica jargão técnico já coberto por `GLOSSARIO-ROLDAO.md`.
- [ ] Termos usados nas outras docs de Descoberta estão todos definidos aqui.
