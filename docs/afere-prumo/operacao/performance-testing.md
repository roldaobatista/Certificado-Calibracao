---
template: performance-testing.template.md
destino: docs/operacao/performance-testing.md
owner: <eng-performance>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
proposito: definir como medir performance, prevenir regressao e bloquear release degradada
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C8
limite-linhas: 200
---

<!--
Agente IA: este documento define o contrato de performance. Sem baseline, todo numero e arbitrario — coletar baseline e o passo 0.
Preencha cenarios reais por servico critico. Use placeholders <...> quando o dado ainda nao existe e marque tarefa.
-->

# Performance Testing — <nome-do-projeto>

## 1. Tipos de teste

| Tipo | O que mede | Quando rodar |
|---|---|---|
| **Load** | comportamento sob carga **esperada** (cenario tipico) | a cada release candidate |
| **Stress** | onde o sistema **quebra** (carga crescente ate falhar) | trimestral OU antes de campanha grande |
| **Soak** (endurance) | comportamento sob carga sustentada por **horas/dias** (vazamento de memoria, conexao, disco) | mensal em staging |
| **Spike** | resposta a **subida abrupta** de trafego (10x em segundos) | trimestral OU antes de evento previsto |
| **Scalability** | quanto o auto-scaling responde corretamente | sempre que policy §3 de `capacity-planning.md` mudar |

## 2. Baseline e regressao

> Sem baseline gravado, nao existe regressao detectavel. Coletar antes de comparar.

### 2.1 Baseline

Baseline atual por servico critico (medido em <data> em staging com dataset padrao §5):

| Servico | Cenario | Latencia p50 | p95 | p99 | Throughput | Error rate |
|---|---|---|---|---|---|---|
| <api-publica> | <GET /v1/items> | <N ms> | <N ms> | <N ms> | <N rps> | <%> |
| <api-publica> | <POST /v1/orders> | <N ms> | <N ms> | <N ms> | <N rps> | <%> |
| <worker-cobranca> | processa 1k jobs | — | <N s> | <N s> | <N jobs/s> | <%> |
| <servico-3> | <cenario> | <N> | <N> | <N> | <N> | <%> |

Baseline e atualizado **so** quando uma mudanca intencional de performance e aprovada. Nunca atualizar baseline para esconder regressao.

### 2.2 Degradacao maxima aceitavel

| Metrica | Degradacao maxima entre release N-1 e N |
|---|---|
| Latencia p50 | + 10% |
| Latencia p95 | + 15% |
| Latencia p99 | + 20% |
| Throughput | - 10% |
| Error rate sob carga | + 0 (zero tolerancia a aumento) |
| Uso de CPU/RAM ao mesmo trafego | + 15% |

Acima do limite -> **bloqueia release** (gate §7). Bypass exige ADR justificando trade-off.

## 3. Ferramentas

| Camada | Ferramenta sugerida | Quando preferir |
|---|---|---|
| HTTP/API load | <k6 \| Locust \| JMeter> | k6 para script em JS, Locust para Python, JMeter para suites legadas |
| Browser / fluxo real de usuario | <Playwright + traces> | medir tempo end-to-end percebido pelo usuario |
| Banco isolado | <pgbench \| sysbench> | medir DB sem ruido da aplicacao |
| Stress de fila | <script custom + producer batch> | medir consumidor especificamente |

Ferramenta escolhida deve gerar relatorio comparavel entre execucoes (CSV/JSON exportavel).

## 4. Cenarios obrigatorios por servico critico

Cada servico critico tem **no minimo** os 4 cenarios abaixo:

| Cenario | Tipo | Carga | Duracao | Aprovacao se |
|---|---|---|---|---|
| Carga esperada (dia normal) | Load | <N rps> | 15 min | p95 dentro de baseline + 15% |
| Pico previsto (campanha) | Load | <2x N rps> | 15 min | p95 dentro de baseline + 25% |
| Stress ate quebrar | Stress | rampa 0 ate falha | ate quebrar | sistema degrada graciosamente (sem erro 500 em massa antes do limite documentado) |
| Endurance | Soak | <N rps constante> | 4-8h | sem leak de memoria, sem crescimento de latencia |

Cenarios extras conforme servico (ex: API publica adiciona Spike; worker adiciona burst de fila).

## 5. Dados de teste

> Dado de teste e parte do contrato. Lixo dentro = lixo fora.

| Origem | Permitido? | Condicao |
|---|---|---|
| Dados **sinteticos** gerados por fixture | sim | preferencia para reproducibilidade |
| Dados **anonimizados** de producao | sim | passou por processo de anonimizacao validado (hash de identificadores, mascaramento de PII) |
| Dados **brutos** de producao com PII | **NAO** | proibido em qualquer ambiente nao-prod — viola `INV-AGENT-008` |

Dataset versionado em <local> com tamanho e distribuicao representativos (nao testar com 100 linhas se prod tem 10M).

## 6. Execucao

| Item | Padrao |
|---|---|
| Frequencia | Load: por RC. Stress/Spike/Scalability: trimestral. Soak: mensal. |
| Ambiente | **staging** com escala equivalente a prod (mesmo tipo de instancia, mesmo schema, mesmo volume de dado representativo) |
| Janela | fora de horario de uso de staging por outros times |
| Quem analisa | <eng-performance> com revisao de <lider-tecnico> |
| Relatorio | publicado em `docs/operacao/performance-reports/2026-05-28-<release>.md` |
| Retencao do relatorio | 1 ano minimo (para comparacao historica) |

> Rodar performance test em prod e proibido salvo com canary muito limitado e aprovacao explicita — risco de impactar cliente.

## 7. Criterio de aprovacao para release (gate)

Release **so passa** o gate de performance se:

- [ ] Cenarios de §4 marcados como obrigatorios para o servico foram executados na RC.
- [ ] Resultados estao dentro dos limites de §2.2 contra baseline atual.
- [ ] Relatorio §6 publicado e linkado no PR/issue da release.
- [ ] Em caso de degradacao acima do limite: ADR aprovado **antes** do release explicando o trade-off (e atualizando baseline em §2.1).
- [ ] Endurance (Soak) executado nos ultimos 30 dias sem leak detectado.

Falha do gate -> bloqueia promotion staging -> prod conforme `deployment-strategy.md` §8.

## 8. Resposta a regressao detectada

1. **Identificar** ponto de introducao: comparar com release anterior e bisseccionar commits se necessario.
2. **Classificar**: intencional (otimizacao adiada) ou nao-intencional (bug de performance).
3. **Decisao**:
   - Nao-intencional + acima do limite -> **rollback ou correcao antes do release**.
   - Intencional + aceita -> ADR + atualizacao de baseline.
4. **Registrar** em `docs/operacao/performance-reports/` com link para fix ou ADR.

## 9. Historico de execucao

| Data | Release | Tipo | Resultado | Link relatorio |
|---|---|---|---|---|
| 2026-05-28 | <versao> | <Load\|Stress\|Soak\|Spike> | <ok\|regressao bloqueante\|regressao aceita por ADR> | `<link>` |

## 10. Vinculacao com

- `docs/operacao/release-process.md` — gate de §7 e pre-condicao para tag e publish.
- `docs/operacao/deployment-strategy.md` — gate em promotion staging -> prod.
- `docs/operacao/capacity-planning.md` — resultados alimentam previsao de saturacao e auto-scaling.
- `docs/operacao/observabilidade.md` — metricas usadas no teste sao as mesmas medidas em producao.
- `docs/operacao/slo-sli.md` — limites de §2.2 sao compativeis com SLOs publicados.
- `INV-AGENT-008` — proibe uso de PII real em dataset de teste.
- `auditores/performance-auditor.md` — valida que cenarios obrigatorios rodaram na RC.
- `docs/decisoes/ADR-XXXX-ferramenta-performance.md` — escolha da ferramenta de §3.
