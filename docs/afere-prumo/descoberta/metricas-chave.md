---
owner: roldao
revisado-em: 2026-05-28
status: stable
ordem-descoberta: 12/17
proximo: docs/descoberta/mercado-regulatorio.md
idioma: pt-BR
limite-linhas: 150
proposito: North Star Metric + guardrails do produto.
---

<!--
template: metricas-chave.md
destino: docs/descoberta/metricas-chave.md
uso: 1 North Star + 3-5 guardrails. Cada métrica com fonte, fórmula e cadência.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3
limite: ≤150 linhas.
-->

# Métricas-chave — Aferê Prumo

> Métricas de produto/negócio. Distinguir de SLI/SLO (operacionais) — esses ficam em `docs/operacao/slo-sli.md`.

> Ferramenta interna: as métricas medem **valor para a operação** (tempo, prazos, adoção),
> não receita de venda. Metas numéricas `(A VALIDAR)` dependem da linha de base medida (ver hipóteses).

## 1. North Star Metric (NSM) — 1 só

- **Métrica**: nº de atendimentos/orçamentos resolvidos com apoio da IA por semana.
- **Por que esta**: reflete a dor central (tempo de atendimento) e a adoção real da ferramenta; se sobe, a equipe está usando e o cliente está sendo atendido.
- **Fonte**: registro de atendimentos da ferramenta.
- **Fórmula**: `COUNT(atendimentos com rascunho/resposta da IA usados) por semana`.
- **Cadência de leitura**: semanal.
- **Linha de base hoje**: **0** atendimentos com apoio de IA (não existe a ferramenta ainda).
- **Meta Fase 1 — rampa sugerida** *(proposta minha, refinar com a linha de base real de H-001):* **≥10/semana** no 1º mês do piloto → **≥25/semana** no 2º → **≥30/semana** em regime (cobre os ~30 orçamentos/semana de H-001). O número de regime se fecha quando o tempo médio por orçamento for medido no piloto. *Confirmar a rampa com o dono.*

## 2. Guardrails (não podem degradar quando a NSM sobe)

### G-001: orçamento errado enviado ao cliente sem revisão = 0
- **Fórmula**: `COUNT(orçamentos enviados pela IA sem aprovação humana)`.
- **Fonte**: log da ferramenta.
- **Cadência**: contínua.
- **Limite (alarme)**: qualquer ocorrência > 0 → alarme (ligado a NF-002).

### G-002: satisfação do cliente no atendimento por IA
- **Fórmula**: % de conversas sem reclamação / pedido de "falar com humano insatisfeito".
- **Fonte**: marcação no atendimento + amostragem manual.
- **Cadência**: mensal.
- **Limite**: cair abaixo de `(A VALIDAR)`% → revisar.

### G-003: prazos de calibração avisados antes de vencer
- **Fórmula**: `prazos avisados com antecedência / total de prazos no período`.
- **Fonte**: módulo de prazos.
- **Cadência**: mensal.
- **Linha de base hoje**: **0%** (o dono não controla nenhum prazo — H-002 confirmada).
- **Limite**: qualquer evolução acima de 0% já é ganho; meta de regime a definir → alarme se cair (dor H-002).

### G-004: adoção da equipe
- **Fórmula**: `% de orçamentos/OS feitos pela ferramenta / total`.
- **Fonte**: ferramenta + conferência.
- **Cadência**: mensal.
- **Limite**: < 80% após 30 dias de piloto → risco R-002 ativo (H-004).

### G-005: custo de IA/mensageria por atendimento
- **Fórmula**: `(custo LLM + custo WhatsApp + custo transcrição STT) no mês / nº de atendimentos`.
- **3 linhas separadas** (áudio é 50%+ do atendimento — D-PROD-013 — então a transcrição não pode ficar escondida):
  - **LLM** por token (cérebro + agentes).
  - **WhatsApp** por conversa.
  - **Transcrição (STT)** por minuto — se serviço pago, R$/min; se local, custo ≈ 0 mas medir tempo de máquina/demora e quantos processos em paralelo são necessários em escala.
- **Métrica separada**: **minutos de áudio transcritos/mês por tenant** (base real: 1.120 áudios em 5 conversas — pode chegar a horas/dia em escala).
- **Fonte**: faturas dos provedores + contagem + log de transcrição.
- **Cadência**: mensal.
- **Limite**: acima de `(A VALIDAR)` R$/atendimento → revisar (R-005, R-019); kill-switch por tenant se estourar.

### G-007: saúde e cobertura do cérebro técnico
- **Por que**: o cérebro (1.099 fontes — D-PROD-014) é diferencial central; sem medir, não há visibilidade do valor nem do risco (R-017, R-018).
- **Fórmula**: `% de perguntas técnicas respondidas pelo cérebro (acima do limiar de confiança) / total de perguntas técnicas`; **% com citação de fonte correta**; **taxa de lacuna detectada** (perguntas que viram backlog de cadastro); **cobertura por marca/modelo** (ex.: Toledo IND780/IND560, Saturno, Filizola).
- **Saúde da base (qualidade, não só cobertura — A-12 da auditoria)**: **taxa de conflito entre fontes** (ex.: Toledo × Inmetro divergem); **cobertura de dedupe** (% de duplicatas resolvidas — há pastas Toledo duplicadas); **acurácia de leitura/OCR** (corrigir as **48 falhas de OCR** pendentes antes do piloto); **tempo entre lacuna detectada e cérebro atualizado** (mede a curadoria). Responsável: curador do cérebro (ver `agentes.md`); ciclo de revisão mensal (R-018).
- **Fonte**: log do cérebro + amostragem manual.
- **Cadência**: mensal (e a cada carga nova de acervo).
- **Limite (alarme)**: `(A VALIDAR — sugestão: ≥80% respondidas, 100% com citação)`; abaixo disso, priorizar carga de acervo.

### G-006: frequência de aviso proativo ao cliente (anti-spam)
- **Fórmula**: `nº de mensagens proativas enviadas a um cliente / período`.
- **Fonte**: log de notificações.
- **Cadência**: contínua.
- **Limite**: **máx. 1 mensagem do mesmo assunto por cliente por semana** (decisão do dono) → acima disso, suprime; sempre com opt-out. Aviso sem governança queima a confiança (oposto do diferencial).

## 3. Métricas de uso (operacionais — segunda linha, do plano do dono)

- **Inbox — tempo médio por item**: alvo ~30–45s (apresentação mostra ~42s). Fonte: Inbox.
- **Inbox — fila zerada/dia**: dono zera a fila em 15–20 min. Fonte: Inbox.
- **Item mais antigo aguardando**: alarme se passar de X horas (evita cliente esquecido). Fonte: Inbox.
- **Saúde das regras aprendidas**: % de aceite por regra (gradua com ≥80%); nº de regras ativas/aprendendo. Fonte: tela "Minhas Regras".
- **Custo de IA (LLM) no mês**: R$ e % do orçamento; **kill-switch** se estourar. Fonte: monitor de custo (ligado a G-005).
- **Tempo de 1ª resposta ao cliente**: alvo < 30 min (hoje pode levar horas). Fonte: WhatsApp/Inbox.

### 3.1 Saúde do agente (loop humano-IA) — sinal para graduar automação

> Lição da análise de concorrentes (2026-05-28): métricas distintas do volume (NSM). É o que **objetivamente** autoriza subir o nível de automação por tipo de ação.

- **Aprovação SEM edição vs COM edição vs rejeitado**, por tipo de agente/ação — é o gatilho de graduação (ver H-006).
- **Taxa de escalonamento para humano + MOTIVO** (baixa confiança / fora de escopo / cliente pediu / dado não achado no Aferê / assunto quente).
- **Tempo na fila da Inbox por TIPO de item** (não só o agregado ~42s).
- **Ações/etapas que mais falham** (onde o agente erra a ação certa).
- **CSAT por conversa atendida com IA**.
- ⚠️ **Deflexão (resolvido sem humano) é guardrail OBSERVADO, nunca meta a maximizar** — maximizar deflexão conflita com o princípio-mãe (D-PROD-006).

### 3.2 Métricas de produto SaaS (multi-cliente — virada de escopo 2026-05-28)

> Como é produto vendido por assinatura (D-PROD-011), há um nível de métrica acima do operacional.

- **Assinantes ativos** do add-on de IA (total e por perfil A/B/C/D). Fonte: faturamento do Aferê.
- **Engajamento por tenant**: % de assinantes que de fato usam a IA (Inbox com atividade) — assinante que não usa vira candidato a churn.
- **MRR** (receita recorrente mensal) do add-on de IA. Fonte: faturamento.
- **Churn mensal** do add-on (e motivo). Alvo `(A VALIDAR)`.
- **Margem por tenant** = `mensalidade da faixa − custo de IA daquele tenant (LLM + WhatsApp + transcrição STT + infra)`. **Guardrail crítico**: margem por tenant não pode ficar negativa (liga ao excedente de uso e ao kill-switch G-005). **Definir margem mínima-alvo** (ex.: ≥40%) `(A VALIDAR com o dono)` — vira alarme/kill-switch.
- **TTFV por novo assinante**: tempo do "ligou o add-on" até o 1º atendimento assistido com valor.

## 4. Anti-métricas (NÃO usar)

- **"Taxa de deflexão"** (conversas fechadas sem humano) — é a métrica-troféu do mundo de suporte, mas para nós é **anti-métrica**: conflita direto com o princípio-mãe (D-PROD-006). Nossa meta é resolução COM aprovação rápida, não ausência de humano.
- "Número de mensagens trocadas pela IA" — vaidade; o objetivo é resolver, não conversar muito.
- "Tempo que a equipe passa na ferramenta" — em ferramenta operacional, MENOS tempo para o mesmo resultado é melhor.

## 5. Dashboards

- **Operacional** (time interno): <link/caminho>
- **Cliente** (se aplicável): <link/caminho>
- **Investidor** (se aplicável): <link/caminho>

## Critério para promover de `draft` para `stable`

- [ ] 1 NSM definida com fonte e fórmula.
- [ ] ≥3 guardrails (qualidade, satisfação, retenção/churn).
- [ ] Cada métrica tem fonte concreta (não "estimativa").
- [ ] Limites de alarme numéricos (não "muito alto").
