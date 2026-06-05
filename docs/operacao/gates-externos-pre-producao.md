---
owner: agente-ia
revisado-em: 2026-06-05
proximo-review: 2026-09-05
status: draft
diataxis: how-to
audiencia: [agente, operacao, tech-lead]
frente: consolidacao-base
tipo: runbook
relacionados:
  - src/infrastructure/observabilidade/desligamento.py
  - src/infrastructure/observabilidade/health.py
  - src/infrastructure/observabilidade/logging_config.py
---

# Gates externos pré-produção (observabilidade F-C2)

> Itens que **só fecham num ambiente de deploy real** (gunicorn + orquestrador +
> coletor de métricas/logs). O código app-level já está pronto e testado; aqui
> ficam os passos de wiring que dependem de infra que **ainda não existe**
> (decisão Roldão: deploy só quando ele quiser). Não bloqueiam dogfooding local.

## 1. Graceful shutdown / drain (SIGTERM)

**App-level (PRONTO):** `observabilidade/desligamento.py` expõe
`iniciar_desligamento()` / `esta_desligando()` / `registrar_handler_sigterm()`.
O `/readyz` responde **503 `draining`** quando o processo está drenando; o
`/livez` segue **200** (processo vivo — matar abortaria requests em voo).

**Wiring de deploy (PENDENTE — fazer no `gunicorn.conf.py`):**

```python
# gunicorn.conf.py
graceful_timeout = 30          # tempo p/ requests em voo terminarem
timeout = 60

def post_fork(server, worker):
    # cada worker registra o handler de SIGTERM (drena antes de morrer)
    from src.infrastructure.observabilidade.desligamento import (
        registrar_handler_sigterm,
    )
    registrar_handler_sigterm()
```

Sequência esperada no rollout: orquestrador manda SIGTERM → handler chama
`iniciar_desligamento()` → `/readyz` vira 503 → LB tira o pod do pool →
requests em voo terminam (≤ `graceful_timeout`) → worker encerra.

**Workers de fila (procrastinate):** drenam nativamente no SIGTERM (terminam o
job atual antes de sair). Conferir `--shutdown-timeout` ao subir o worker.

- [ ] `GATE-OBS-GRACEFUL-1` — `gunicorn.conf.py` com `post_fork` + `graceful_timeout`
- [ ] readiness probe do orquestrador aponta pra `/readyz` (não `/livez`)
- [ ] liveness probe aponta pra `/livez`

## 2. Ingestão de logs estruturados

**App-level (PRONTO):** logs já saem em JSON 1-linha-por-evento em prod
(`json_logs=not DEBUG`), com `correlation_id`/`tenant_id`/`usuario_id`.

**Pendente (deploy):**
- [ ] `GATE-OBS-LOG-INGEST-1` — coletor (Grafana Agent/Alloy ou vector) lendo
      stdout dos containers → Loki/Axiom.
- [ ] retenção: logs de acesso ≥6 meses (INV-008).
- [ ] dashboard de busca por `correlation_id` (rastreio cross-request).

## 3. Métricas (Prometheus) — fecha OBS-003

Ver F-C2 Fatia D (`/metrics`). Pendente de deploy:
- [ ] `GATE-OBS-METRIC-SCRAPE-1` — Prometheus/Grafana Agent fazendo scrape do
      `/metrics` de cada pod.
- [ ] dashboards Golden Signals (latência, tráfego, erros, saturação) por tenant.
- [ ] fecha o OBS-003 BAIXO carryover de TODOS os módulos de metrologia
      (GATE-OBS-METRIC-* — M5..M9).

## 4. NTP / relógio (trilha WORM)

- [ ] `GATE-NTP-1` — chrony/systemd-timesyncd no host (timestamps WORM confiáveis).
