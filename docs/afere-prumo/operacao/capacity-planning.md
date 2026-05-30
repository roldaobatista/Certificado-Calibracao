---
template: capacity-planning.template.md
destino: docs/operacao/capacity-planning.md
owner: <lider-operacao>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
proposito: prever crescimento, dimensionar recursos antes de saturar e controlar custo por unidade de negocio
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C8
limite-linhas: 200
---

<!--
Agente IA: este documento mantem o sistema dimensionado para os proximos 6-12 meses.
Preencha numeros reais. Sem numero, o documento e teatro. Se nao houver dado historico, marque "baseline a coletar — alvo: <data>" e pendure tarefa.
Revisao trimestral obrigatoria (§7).
-->

# Capacity Planning — <nome-do-projeto>

## 1. Forecast de crescimento

Projecao do uso para os proximos **12 meses**, baseada em dados historicos das ultimas <6-12> semanas.

| Dimensao | Baseline atual | +3 meses | +6 meses | +12 meses | Fonte |
|---|---|---|---|---|---|
| Assinaturas ativas | <N> | <N> | <N> | <N> | banco / financeiro |
| Requests/segundo (pico) | <N rps> | <N rps> | <N rps> | <N rps> | observabilidade §2 |
| Requests/segundo (medio) | <N rps> | <N rps> | <N rps> | <N rps> | observabilidade §2 |
| Eventos em fila/dia | <N> | <N> | <N> | <N> | metricas de fila |
| Storage total (DB principal) | <N GB> | <N GB> | <N GB> | <N GB> | metricas DB |
| Storage total (objetos / arquivos) | <N GB> | <N GB> | <N GB> | <N GB> | storage provider |
| Egress / banda saida | <N TB/mes> | <N TB/mes> | <N TB/mes> | <N TB/mes> | provider |

Premissa de crescimento: <ex: 8% ao mes baseado em ultimos 6 meses + campanha planejada para Q3>.

> Forecast tem incerteza. Reavaliar quando metrica real divergir > 20% do projetado.

## 2. Dimensionamento atual vs projetado

### 2.1 Computacao (por servico)

| Servico | CPU atual (vCPU) | CPU 6 meses | RAM atual (GB) | RAM 6 meses | Replicas atual | Replicas 6 meses |
|---|---|---|---|---|---|---|
| <api-gateway> | <N> | <N> | <N> | <N> | <N> | <N> |
| <worker-cobranca> | <N> | <N> | <N> | <N> | <N> | <N> |
| <servico-3> | <N> | <N> | <N> | <N> | <N> | <N> |

### 2.2 Banco de dados

| Item | Atual | Projetado 6 meses | Limite tecnico |
|---|---|---|---|
| Storage usado | <N GB> | <N GB> | <N GB do plano> |
| IOPS pico | <N> | <N> | <N> |
| Conexoes simultaneas (pico) | <N> | <N> | <N max do plano> |
| Tamanho da maior tabela | <N GB / N linhas> | <N GB / N linhas> | — |
| Replica lag p95 | <N ms> | <N ms> | <N ms aceitavel> |

### 2.3 Filas / cache / dependencias

| Recurso | Capacidade atual | Uso atual | Uso projetado 6 meses |
|---|---|---|---|
| Fila <nome> | <N msg/s vazao> | <%> | <%> |
| Cache <redis> | <N GB> | <%> | <%> |
| External API <provider> | <N req/min quota> | <%> | <%> |

## 3. Auto-scaling policies

| Servico | Min | Max | Metrica gatilho | Scale-up | Scale-down |
|---|---|---|---|---|---|
| <api-gateway> | 3 | 30 | CPU > 65% por 3min | +2 replicas | CPU < 30% por 10min, -1 replica |
| <worker-cobranca> | 2 | 20 | queue_depth > 1000 por 5min | +1 replica | queue_depth < 100 por 15min, -1 replica |
| <servico-3> | <N> | <N> | <metrica> | <acao> | <acao> |

Regras:
- `min` sempre >= 2 para servicos com SLO (zero downtime em rolling deploy).
- `max` dimensionado para 2x do pico projetado em 6 meses (margem de seguranca).
- Cooldown de scale-down >= 10min para evitar oscilacao.
- Auto-scaling so e confiavel se o gargalo estiver no recurso medido — verificar §4 antes de subir limites.

## 4. Saturation thresholds (alarmes preventivos)

> Alerta dispara **antes** do recurso saturar, para dar tempo de provisionar.

| Recurso | Warning (SEV3) | Critical (SEV2) | Acao |
|---|---|---|---|
| CPU servico | > 70% por 15min | > 85% por 5min | escalar horizontalmente, investigar query/loop quente |
| RAM servico | > 75% por 15min | > 90% por 5min | escalar vertical/horizontal, investigar leak |
| Conexoes DB | > 70% do max por 10min | > 85% do max por 5min | aumentar pool ou plano, investigar conexao vazada |
| Storage DB | > 70% | > 85% | provisionar +N GB, revisar retencao |
| Fila depth | crescente por 30min | > <N> por 10min | escalar consumidores, investigar lentidao |
| Egress | > 70% do contratado/mes | > 90% | revisar plano, investigar trafego anormal |

Todo alerta aponta para runbook conforme `observabilidade.md` §7.

### 4.1 Gate de capacidade — bloqueia lancamento

> **Regra dura**: se o forecast (§1) projetar que um recurso vai cruzar o limiar **Critical** (§4) dentro da janela do lancamento, o lancamento e **bloqueado** ate a capacidade ser provisionada.

- Antes de aprovar um lancamento que aumente carga (campanha, onboarding grande, feature de alto trafego), conferir §1 e §2: o recurso projetado fica abaixo do Critical no horizonte do evento?
- Saturacao prevista acima do limiar = **gate vermelho**. Provisionar primeiro (escalar, subir plano, reservar §6), depois liberar.
- Override exige justificativa registrada em ADR + plano de contingencia (rollback de carga, fila de espera).
- Vinculado a `change-management.md` §1 (janela de mudanca) — gate de capacidade entra como pre-condicao da aprovacao.

## 5. Custo por unidade

Indicador para detectar regressao de eficiencia (custo crescendo mais rapido que receita = problema).

| Metrica | Valor atual | Tendencia 3 meses | Alvo |
|---|---|---|---|
| Custo total infra / mes | R$ <N> | <+/-N%> | — |
| Custo por **assinatura ativa** / mes | R$ <N> | <+/-N%> | <= R$ <N> |
| Custo por **1k requests** | R$ <N> | <+/-N%> | <= R$ <N> |
| Custo por **GB storage** / mes | R$ <N> | <+/-N%> | — |
| Custo de observabilidade / custo total | <%> | <%> | <= 15% |

> Crescimento de custo/unidade > 10% trimestre a trimestre exige investigacao registrada.

## 6. Capacidade reservada vs sob demanda

Compromissos de longo prazo (reserved instances, savings plans) reduzem custo mas exigem previsao confiavel.

| Recurso | Reservado | Sob demanda | % reservado |
|---|---|---|---|
| Computacao baseline | <N vCPU> | <N vCPU> | <%> |
| Storage | <N GB> | <N GB> | <%> |

Diretriz: reservar ate o **piso historico dos ultimos 6 meses**, deixar o resto sob demanda. Renovar so quando o piso confirmar.

## 7. Revisao trimestral (obrigatoria)

A cada **3 meses**, owner executa:

- [ ] Comparar metricas reais com forecast da revisao anterior. Divergencia > 20% -> recalibrar premissa.
- [ ] Atualizar tabelas §1 e §2 com numeros do ultimo trimestre.
- [ ] Revisar policies de auto-scaling §3 — algum servico bateu max? algum nunca usou alem do min?
- [ ] Revisar custo/unidade §5 — alguma regressao?
- [ ] Provisionar/desprovisionar capacidade reservada §6 conforme piso atualizado.
- [ ] Registrar a revisao em §8.

## 8. Historico de revisoes

| Data | Revisor | Mudancas principais | Proxima revisao |
|---|---|---|---|
| 2026-05-28 | <nome> | criacao inicial | <YYYY-MM-DD + 3 meses> |

## 9. Vinculacao com

- `docs/operacao/observabilidade.md` — fonte das metricas de saturacao e baseline.
- `docs/operacao/slo-sli.md` — saturacao excessiva degrada SLO; capacity protege error budget.
- `docs/operacao/deployment-strategy.md` — auto-scaling depende de min >= 2 para rolling deploy.
- `docs/operacao/runbooks/recurso-saturado.md` (instanciar via `runbook.template.md`) — execucao quando alerta de §4 dispara.
- `docs/decisoes/ADR-XXXX-provider-infra.md` — escolha do provedor e limites contratuais.
- `auditores/capacity-auditor.md` — valida que revisao trimestral foi feita no prazo.
