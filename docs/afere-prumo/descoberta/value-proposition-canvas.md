---
owner: roldao
revisado-em: 2026-05-28
status: stable
ordem-descoberta: 05/17
proximo: docs/descoberta/gtm-pricing.md
idioma: pt-BR
limite-linhas: 150
proposito: Value Proposition Canvas — encaixe produto/cliente (ganhos, dores, pílulas).
---

<!--
template: value-proposition-canvas.md
destino: docs/descoberta/value-proposition-canvas.md
uso: Canvas de proposta de valor. 1 página por segmento de cliente.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3
limite: ≤150 linhas. Se passar, fatiar por segmento.
-->

# Value Proposition Canvas — Aferê Prumo

> Preencha aqui o **encaixe dor ↔ solução** por segmento. Não repetir estrutura de receita/canais do BMC nem tabela de planos do GTM.

## Segmento A: Equipe interna (atendimento + técnico) — P-001/P-002

### Lado do cliente (perfil)

#### 1. Jobs
- **Funcional**: atender cliente, montar orçamento, executar serviço com histórico, registrar OS, controlar prazos.
- **Emocional**: não ficar sobrecarregado nem com medo de "esquecer algo".
- **Social**: passar profissionalismo (resposta rápida, nada esquecido).

#### 2. Dores
- "Respondo as mesmas perguntas o dia todo" — **alta**.
- "Refaço orçamento do zero e caço informação em planilha" — **alta**.
- "Chego no cliente sem o histórico do equipamento" — **média/alta**.
- "Prazo de calibração não tem alarme" — **alta**.

#### 3. Ganhos
- **Esperados**: responder/orçar em minutos; achar histórico na hora.
- **Desejados**: prazos agendados automaticamente; OS sem papel.
- **Inesperados (delight)**: a IA já sugere o orçamento certo só revisar.
- **Emocional (governança) — "nada avança errado"**: a OS não fatura sem revisão; o certificado não sai sem 2 conferências e peso válido. Tira o **medo de esquecer ou emitir errado** — ganho de tranquilidade, não só de tempo.

### Lado do produto (proposta)

#### 4. Pílulas (como apaga as dores)

| Dor | Pílula |
|---|---|
| Perguntas repetidas | IA responde as comuns sozinha |
| Orçamento do zero | IA monta rascunho a partir da base de preços |
| Sem histórico em campo | Equipamento e histórico no celular |
| Prazo sem alarme | Agendamento e aviso automáticos |

#### 5. Geradores de ganho

| Ganho | Como entrega |
|---|---|
| Orçar em minutos | Rascunho automático + revisão |
| Nada esquecido | Calendário de prazos com aviso proativo |

#### 6. Produtos e serviços
- Atendimento por IA no WhatsApp (com fallback humano).
- Gerador de orçamento (rascunho para revisão).
- Cadastro central de clientes/equipamentos/histórico + OS digital.
- Módulo de prazos de calibração com aviso.

#### 7. Diferencial estrutural — o EQUIPAMENTO como entidade central

> Lição da análise de concorrentes (2026-05-28): todo CRM/atendimento genérico gira em torno de
> **contato/negócio/ticket** ou **FAQ estática**. A nossa proposta gira em torno do **equipamento
> vivo** — nº de série, classe, capacidade, última OS, peças trocadas, **próximo prazo de
> calibração** — consultado no Aferê em tempo real. É a fronteira que nenhum concorrente atravessa,
> e o que torna o "aviso proativo de prazo" e o "histórico na mão do técnico" possíveis.

## Segmento B: Cliente final — P-003

- **Jobs**: pedir balança/serviço, ser atendido rápido, não perder prazo de calibração.
- **Dores**: demora de resposta; ele que tem de lembrar do prazo; sem consulta ao histórico.
- **Pílulas**: resposta em segundos no WhatsApp; aviso proativo de prazo; histórico acessível.

### Encaixe (fit)

- **Problem-Solution Fit**: as pílulas batem direto com as 4 dores da auto-entrevista (`EE-AUTO-001`); falta validar com a equipe e clientes reais (H-001 a H-004).
- **Fit alvo (Fase 1)**: ≥80% dos orçamentos/atendimentos passando pela ferramenta após 30 dias de piloto (H-004).

## Critério para promover de `draft` para `stable`

- [ ] Cada dor tem pílula correspondente.
- [ ] Cada ganho esperado tem gerador correspondente.
- [ ] Severidade das dores classificada.
- [ ] Fit declarado (mesmo que "ainda não validado").
