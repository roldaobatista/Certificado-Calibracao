---
template: observabilidade.template.md
destino: docs/operacao/observabilidade.md
owner: <lider-operacao>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
proposito: definir como o sistema e observado em producao (logs, metricas, traces) e quando alguem e acordado
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C8
limite-linhas: 200
---

<!--
Agente IA: este documento define o contrato de observabilidade. Cada servico novo precisa cumprir §6 antes de subir em producao.
Preencha ferramentas reais nos placeholders <ferramenta-X>. Se ainda nao escolhidas, deixar marcado "a definir — ADR pendente".
-->

# Observabilidade — <nome-do-projeto>

## 1. Os tres pilares

| Pilar | O que e | Ferramenta | Retencao padrao |
|---|---|---|---|
| **Logs** | eventos discretos com contexto textual ou JSON | <ex: Loki, CloudWatch, Datadog Logs> | §5 |
| **Metricas** | series temporais numericas agregadas | <ex: Prometheus, CloudWatch Metrics> | 13 meses |
| **Traces** | linha do tempo de uma requisicao atravessando servicos | <ex: Tempo, Jaeger, Datadog APM> | 30 dias (com sampling §8) |

Correlacao entre os tres via **`trace_id`** propagado em header `traceparent` (W3C Trace Context).

## 2. Golden signals (por servico)

Quatro indicadores obrigatorios em todo servico critico (referencia: Google SRE Book).

| Sinal | O que mede | Como expor |
|---|---|---|
| **Latency** | tempo de resposta — separar sucesso de erro | histograma com buckets (p50, p95, p99) |
| **Traffic** | demanda no servico | counter de requisicoes por segundo |
| **Errors** | taxa de falhas | counter de erros / counter total |
| **Saturation** | quao cheio o servico esta | gauge de % CPU, RAM, fila, conexoes DB |

Dashboard de cada servico em §7 expoe os quatro lado a lado.

## 3. Instrumentacao obrigatoria por componente

> Servico sem instrumentacao nao sobe em producao. Verificado pelo auditor §10.

| Componente | Metricas obrigatorias | Logs obrigatorios | Trace |
|---|---|---|---|
| **HTTP server** | requests_total{method,route,status}, request_duration_seconds | acesso (1 linha/req) + erro detalhado | span por requisicao |
| **HTTP client** | outbound_requests_total{target,status}, outbound_duration_seconds | erro (timeout, 5xx) | span filho |
| **DB (SQL/NoSQL)** | query_duration_seconds{operation}, pool_connections_used | query lenta (> <500ms>), erro de conexao | span por query |
| **Queue (producer)** | jobs_enqueued_total{queue}, enqueue_duration_seconds | falha de enqueue | span de publish |
| **Queue (consumer)** | jobs_processed_total{queue,outcome}, processing_duration_seconds | inicio, sucesso, erro, retry | span de consume |
| **Cache** | cache_hits_total, cache_misses_total, cache_errors_total | erro de conexao | tag em span pai |
| **External API** | external_calls_total{provider,status}, external_duration_seconds, circuit_breaker_state | falha, timeout, circuit aberto | span filho |

## 4. Schema de log estruturado

Todo log e JSON em uma linha (`ndjson`). Campos:

| Campo | Obrigatorio | Tipo | Exemplo |
|---|---|---|---|
| `timestamp` | sim | ISO-8601 UTC | `2026-05-27T14:32:01.234Z` |
| `level` | sim | enum | `debug` \| `info` \| `warn` \| `error` \| `fatal` |
| `service` | sim | string | `api-gateway` |
| `version` | sim | string | `2026.05.3` |
| `env` | sim | string | `prod` \| `staging` \| `dev` |
| `trace_id` | sim (quando em request) | string | `4bf92f3577b34da6a3ce929d0e0e4736` |
| `span_id` | sim (quando em request) | string | `00f067aa0ba902b7` |
| `tenant_id` | sim (multi-tenant) | string | `tnt_abc123` |
| `user_id` | quando aplicavel | string | hash ou id opaco — **nunca PII** |
| `message` | sim | string curta | `payment processed` |
| `event` | quando aplicavel | string | nome canonico do evento de negocio |
| `error.type`, `error.message`, `error.stack` | quando level >= error | string | — |

> Log nao-estruturado (`console.log` cru, printf solto) e proibido em producao. Auditor §10 falha o build se encontrar.

## 5. Retencao de logs (hot/warm/cold)

| Camada | Janela | Acessibilidade | Custo relativo |
|---|---|---|---|
| **Hot** | ultimos 7 dias | busca interativa, dashboards | alto |
| **Warm** | 8-30 dias | busca em background, alertas pos-fato | medio |
| **Cold** | 31 dias - 1 ano | restauracao sob demanda, auditoria | baixo |
| **Descarte** | > 1 ano | apagado, exceto logs de auditoria legal | — |

Logs marcados `audit: true` (autenticacao, autorizacao, mudanca de dado sensivel) tem retencao minima de **<5 anos>** conforme LGPD/contrato.

## 6. Dashboards minimos por servico

Cada servico tem um dashboard com no minimo:

1. **Golden signals** (§2) — 4 paineis lado a lado.
2. **Top 5 endpoints/operacoes por volume** e por latencia p95.
3. **Top 5 erros** (mensagem + contagem) ultimas 24h.
4. **Saturacao de dependencias** — DB pool, cache, fila.
5. **Versao em producao** (anotacao com timestamp de cada deploy).

Link do dashboard: `<url>` (publicado em `docs/operacao/dashboards.md`).

## 7. Alerting (limites e runbook)

Todo alerta segue regra: **dispara -> aponta para runbook executavel**. Alerta sem runbook e proibido (vira ruido).

| Alerta | Condicao | Severidade | Runbook |
|---|---|---|---|
| API erro elevado | error_rate > 1% por 5min | SEV2 | `docs/operacao/runbooks/api-erro-elevado.md` (instanciar via runbook.template.md) |
| API latencia degradada | p95 > <800ms> por 10min | SEV3 | `docs/operacao/runbooks/api-latencia.md` (instanciar via runbook.template.md) |
| Fila travada | depth crescente por 15min | SEV2 | `docs/operacao/runbooks/fila-travada.md` (instanciar via runbook.template.md) |
| DB saturado | pool_used > 85% por 5min | SEV2 | `docs/operacao/runbooks/db-saturado.md` (instanciar via runbook.template.md) |
| Servico down | health check falha 3x consecutivas | SEV1 | `docs/operacao/runbooks/servico-down.md` (instanciar via runbook.template.md) |
| Error budget queima > 10%/1h | ver `slo-sli.md` §4b | SEV1 | `docs/operacao/runbooks/error-budget-critico.md` (instanciar via runbook.template.md) |

> Os runbooks acima nao sao arquivos prontos: cada caminho `docs/operacao/runbooks/<nome>.md` e **instanciado a partir de `runbook.template.md`** no projeto-destino. A severidade do alerta define a gravidade do runbook acionado.

Severidades, escalonamento e tempo de resposta: ver `docs/operacao/on-call.md`.

## 8. Sampling e custo de traces

Trace 100% e caro em alto volume. Politica:

- **Erros**: sempre 100% (head + tail-based onde aplicavel).
- **Requisicoes lentas** (acima de p95): 100%.
- **Trafego normal**: <1-10>% sampling — ajustar conforme custo mensal.
- **Health checks e endpoints triviais**: 0% (excluir).

Revisao trimestral do custo de observabilidade contra valor entregue. Owner: <lider-operacao>.

## 9. PII e segredo em logs — proibido

> **Regra dura**: PII (CPF, e-mail, nome, telefone, endereco, cartao) e segredo (token, senha, chave) **NUNCA** podem aparecer em log, mesmo em `debug`.

Mitigacoes obrigatorias:
- Bibliotecas de log com filtro de campos sensiveis configurado (`password`, `token`, `secret`, `authorization`, `cpf`, `email`, `cardNumber`, ...).
- Auditor automatico de logs em CI: regex contra padroes conhecidos (CPF, e-mail, JWT, chave AWS).
- Em caso de vazamento detectado: rotacao imediata do segredo, purge do log, incidente SEV1.

Vinculado a `INV-AGENT-008` (proibicao de PII/segredo em log).

## 10. Onboarding de novo servico (checklist)

Antes do primeiro deploy em producao, novo servico cumpre:

- [ ] `/health` e `/ready` implementados e respondendo.
- [ ] Logs estruturados em ndjson conforme §4.
- [ ] `trace_id` propagado em todos handlers de entrada e saida.
- [ ] Golden signals (§2) expostos em `/metrics`.
- [ ] Instrumentacao por componente (§3) para os componentes que usa.
- [ ] Dashboard criado conforme §6 e linkado em `docs/operacao/dashboards.md`.
- [ ] Pelo menos 1 alerta por golden signal com runbook vinculado.
- [ ] Filtro de PII/segredo configurado no logger (§9).
- [ ] SLI/SLO definido em `docs/operacao/slo-sli.md`.
- [ ] Owner tecnico identificado em `docs/decisoes/owners.md`.

Auditor `auditores/observabilidade-auditor.md` valida o checklist no CI.

## 11. Vinculacao com

- `docs/operacao/slo-sli.md` — SLIs sao derivados das metricas definidas aqui.
- `docs/operacao/on-call.md` — severidade dos alertas e escalonamento.
- `docs/operacao/runbooks/` — todo alerta de §7 aponta para um arquivo desta pasta.
- `docs/operacao/dashboards.md` — indice de dashboards publicados.
- `INV-AGENT-008` — proibicao de PII e segredo em log.
- `auditores/observabilidade-auditor.md` — valida onboarding e schema de log.
- `auditores/log-pii-auditor.md` — varredura regex contra padroes sensiveis.
- `docs/decisoes/ADR-XXXX-stack-observabilidade.md` — escolha das ferramentas.
