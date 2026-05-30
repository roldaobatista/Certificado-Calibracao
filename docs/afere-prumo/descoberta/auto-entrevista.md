---
owner: roldao
revisado-em: 2026-05-28
status: stable
idioma: pt-BR
limite-linhas: 120
proposito: registro da conversa inicial com o dono (Roldão) que sustenta a dor do problema.md, na ausência de entrevista externa formal.
---

# Auto-entrevista do dono — Aferê Prumo

> Projeto do próprio dono. Esta auto-entrevista (`EE-AUTO-NNN`) substitui a entrevista
> externa enquanto não houver conversa registrada com clientes reais. Cada afirmação
> de número ainda não medido está marcada como `(A VALIDAR)` e replicada em
> `hipoteses-a-validar.md`.

## EE-AUTO-001 — Roldão (dono/idealizador), 2026-05-28

**Sobre a empresa (Balanças Solution):** empresa full-service de balanças. Atua em
quatro frentes ao mesmo tempo:

1. **Venda** de balanças (comerciais e industriais).
2. **Manutenção e assistência técnica** (conserto, preventiva/corretiva, peças, ordens de serviço).
3. **Calibração e aferição** com selo (Inmetro / IPEM / RBC), com emissão de certificado.
4. **Locação** de balanças.

**O que ele quer da IA (visão, na palavra dele "tudo"):**

- **Atender o cliente** — responder dúvidas, montar orçamento, agendar visita (canal típico: WhatsApp).
- **Automatizar o interno** — orçamentos, ordens de serviço, agendamento de calibração, lembretes de prazo.
- **Analisar dados** — relatórios, previsão de demanda, controle de clientes e contratos.
- **Servir de "cérebro" da empresa** — uma base de conhecimento única que ajuda em tudo.

**Quem vai usar:** *ambos* — a equipe interna por dentro e os clientes por fora.

**Dores (todas reais, segundo o dono):**

- 🔴 Tempo gasto no atendimento (mesmas perguntas, orçamentos repetidos).
- 🔴 Processos manuais (planilha / papel / WhatsApp solto; retrabalho; informação perdida).
- 🔴 Prazos de calibração / garantia / contrato perdidos (cliente só lembra atrasado).
- 🔴 Falta de organização (dados de clientes, equipamentos e histórico espalhados).

## EE-AUTO-002 — Roldão, 2026-05-28 (números da operação)

- **Volume de atendimentos**: ~**50 por semana**.
- **Tempo de execução do serviço**: muito variável — de **2 horas a 2 dias** por caso (depende do serviço: dúvida rápida vs. conserto/calibração em campo).
- **Equipe — 9 pessoas no total**:
  - Roldão — proprietário (gestão).
  - **2 pessoas no escritório** (atendimento/comercial/administrativo).
  - **5 técnicos em campo** (manutenção/calibração).
  - **1 motorista** (logística — entrega/retirada, deslocamento).
- **Observação do agente**: "tempo de atendimento" (responder + orçar) ≠ "tempo de execução do serviço" (2h–2 dias). O número que importa para a Fase 1 (atendimento/orçamento) é quanto do tempo do escritório vai em responder e montar orçamento — ainda a medir no piloto.
- O dono tem **ideias próprias para a descoberta** a registrar (pendente de coletar nesta conversa).

## EE-AUTO-003 — Roldão, 2026-05-28 (números que fecham a dor)

- **Dos ~50 atendimentos/semana, ~30 são orçamento.** Orçamento é o maior bloco de trabalho do escritório.
- **Prazos de calibração: o dono NÃO controla → perde 100%.** Não há acompanhamento de vencimento; toda renovação depende exclusivamente de o cliente lembrar. Isso significa que a receita recorrente de recalibração hoje é, na prática, **deixada na mesa**.
- **Implicação para o sequenciamento**: confirma a Onda 1 (atendimento/orçamento) pela dor de volume, e dá à Onda de **prazos/Metrologia** um valor financeiro potencialmente altíssimo (de 0% controlado para controle proativo).

## Leitura do agente (interpretação a confirmar com o dono)

- A visão é ampla e válida, mas **não cabe numa primeira entrega**. O recomendado é
  documentar tudo aqui e **fatiar em fases** — a Fase 1 ataca a dor mais aguda e
  serve de fundação para o resto. Proposta de sequenciamento em `sintese-final.md`.
- O negócio **trata dado pessoal de cliente** (nome, telefone, CNPJ, endereço,
  histórico de equipamento) → LGPD se aplica (decisão de materializar C6 na fase-2).
- Usa **IA/LLM em produção** → exige ADR-0000 (uso de IA) com escopo, risco e custo.

## Números ainda não medidos (vão para hipóteses-a-validar.md)

- Quantos atendimentos/orçamentos por semana e tempo médio de cada um. `(A VALIDAR)`
- Quantas calibrações com prazo controladas por mês e quantos prazos são perdidos. `(A VALIDAR)`
- Tamanho da equipe e quem faz cada papel. `(A VALIDAR)`
- Volume de clientes ativos e de equipamentos em base. `(A VALIDAR)`
