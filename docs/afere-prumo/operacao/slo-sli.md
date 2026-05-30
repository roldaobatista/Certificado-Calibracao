---
owner: <responsavel>
ultima-conferencia: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 200
proposito: definir SLIs, SLOs e politica de queima de error budget por servico critico
---

<!--
template: slo-sli.md
destino: docs/operacao/slo-sli.md
uso: definir SLIs e SLOs por serviço crítico, com política de queima de error budget.
-->

# SLI/SLO — Aferê Prumo

## 1. Conceitos (em linguagem clara)

- **SLI** (Service Level Indicator) = **indicador**: o número que estamos medindo (ex: tempo de resposta médio em milissegundos, percentual de requisições bem-sucedidas).
- **SLO** (Service Level Objective) = **meta**: o valor que o SLI precisa atingir (ex: "o SLI tempo-de-resposta deve ficar abaixo de 500ms em 99% das requisições, dentro de um mês").
- **Error budget** = **margem de erro aceitável**: quanto o serviço pode falhar antes de a equipe parar de lançar novidade e focar em estabilidade (ex: se o SLO é 99%, o error budget é 1% do mês — cerca de 7 horas e 12 minutos de falha por mês).
- **Janela rolante** = **período móvel**: os últimos N dias contados para trás a partir de hoje (ex: "30 dias rolantes" hoje significa 27/04 a 27/05; amanhã significa 28/04 a 28/05). Diferente de "mês fechado", que reseta no dia 1.
- **Política de queima**: o que a equipe faz quando o error budget está sendo gasto rápido demais.

## 2. Serviços críticos

| Serviço | SLI (indicador medido) | SLO (meta) | Error budget (margem) | Janela | Política de queima |
|---|---|---|---|---|---|
| API pública `/v1/*` | % de respostas HTTP < 500 em < 800ms | 99,5% | 0,5% (~3,6h/mês) | 30 dias rolantes | queima > 2% em 1h → **para de lançar versão nova até o error budget recuperar**; queima > 5% em 6h → aciona on-call |
| Worker de cobrança | % de jobs concluídos sem retry final | 99,0% | 1,0% | 30 dias rolantes | queima > 5% em 24h → pausa novas remessas e abre incidente |
| <serviço-3> | <SLI> | <SLO%> | <budget> | <janela> | <política> |

## 3. Como cada SLI é medido

- **API pública**: indicador derivado de logs do gateway, filtrando `status >= 500` e `latency_ms`. Cálculo no agregador `<ferramenta>`.
- **Worker de cobrança**: contador `jobs_finalizados_ok / jobs_finalizados_total` exportado a cada 1 min.

## 4. Métricas de negócio (complementares aos SLIs técnicos)

Indicadores que medem o **resultado para o cliente**, não só a saúde técnica. Devem ser revisados junto com SLIs.

| Métrica | O que mede | Meta sugerida | Origem do dado |
|---|---|---|---|
| Taxa de sucesso de checkout | % de tentativas de pagamento que completam sem erro | ≥ 98% no mês | logs do worker de cobrança + retorno do intermediador |
| Tempo até primeiro PDF gerado | minutos entre cadastro do cliente e geração do primeiro documento | < 10 min em 95% dos casos | banco de dados (timestamps de cadastro e primeira emissão) |
| % de e-mails entregues sem bounce | e-mails aceitos pelo destinatário / e-mails enviados | ≥ 97% mensal | provedor de e-mail transacional |
| Clientes ativos por dia | quantidade de contas que fizeram pelo menos uma ação relevante no dia | crescimento positivo mês a mês | analytics / banco de dados |

> Métrica de negócio caindo pode ser sintoma de problema técnico não detectado pelos SLIs — por isso entram aqui.

## 4b. Política de queima — mapeamento para severidade

A velocidade com que o error budget está sendo consumido define a severidade do alerta. Mesma escala usada em `on-call.md`.

| Estado do error budget | Severidade | Ação obrigatória |
|---|---|---|
| Queima > 10% em 1h **OU** budget esgotado (saldo ≤ 0) | **CRÍTICO** (SEV1) | pausa imediata de novos deploys, aciona on-call, abre `#war-room`, comunica cliente se afetar SLA contratual |
| Queima > 5% em 6h **OU** saldo restante < 25% | **ALTO** (SEV2) | bloqueia features novas até saldo recuperar, prioriza correção de estabilidade, revisa runbook do serviço |
| Queima > 2% em 1h **OU** saldo restante < 50% | **MÉDIO** (SEV3) | sinaliza em standup, investiga causa nas próximas 48h, ajusta backlog para reduzir risco |
| Queima dentro do esperado, saldo > 50% | **BAIXO** (SEV4) | sem ação obrigatória, apenas acompanhamento normal |

> Quando o budget esgota completamente: regra dura — **proibido lançar versão nova** até saldo voltar a positivo na janela rolante. Exceção exige aprovação registrada em ADR.

## 5. Revisão dos SLOs

- Revisão **trimestral** obrigatória do owner da operação.
- Mudança de meta exige ADR.
- **Ajuste para baixo** (afrouxar SLO — exigir menos do serviço): exige justificativa explícita com dados das últimas 3 janelas. Não pode ser só "estamos estourando muito".
- **Ajuste para cima** (apertar SLO — exigir mais do serviço): obrigatório quando o SLI atual supera a meta por 3 janelas consecutivas com folga > 30% do error budget. Não deixe meta frouxa virar zona de conforto.

> A simetria é importante: relaxar SLO sem apertar quando dá certo gera cultura de só recuar.

## 6. Relação com runbooks

Cada queima crítica deve apontar para um runbook em `docs/operacao/runbooks/`. Esses arquivos não vêm prontos: cada caminho é **instanciado a partir de `runbook.template.md`** no projeto-destino.

A severidade da queima (§4b) define a gravidade do gatilho do runbook: queima **CRÍTICO/SEV1** aciona o runbook com prioridade de incidente imediato; **ALTO/SEV2** aciona com revisão de estabilidade antes de novo deploy.

| Queima | Severidade (§4b) | Runbook a executar |
|---|---|---|
| API > 5% em 6h | ALTO (SEV2) | `docs/operacao/runbooks/api-erro-elevado.md` (instanciar via runbook.template.md) |
| API queima > 10% em 1h | CRÍTICO (SEV1) | `docs/operacao/runbooks/error-budget-critico.md` (instanciar via runbook.template.md) |
| Worker cobrança > 5% em 24h | ALTO (SEV2) | `docs/operacao/runbooks/cobranca-fila-travada.md` (instanciar via runbook.template.md) |
