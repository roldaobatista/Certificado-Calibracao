---
owner: tech-lead-saas-regulado (subagente)
revisado-em: 2026-05-20
status: stable
---

# Review tech-lead — T-CLI-107 + T-CLI-110

Veredito: **AJUSTAR antes de `/implement`** (todos absorvidos — ver
`design.md`).

## Decisões T1..T5

- **T1** (`FOR UPDATE SKIP LOCKED`) → **manter**. Idiomático Postgres,
  bate com `procrastinate` futuro (Wave A) sem retrabalho.
- **T2** (RLS predicate único) → **manter, com refinamento BLOQ-A**
  (replicar byte-a-byte o predicate de `Auditoria`).
- **T3** (`processado_em` + 7 dias vs DELETE imediato) → **manter 7
  dias**. Mas exige linha explícita na `retencao-matriz.md` antes do
  merge (BLOQ-A2 do advogado).
- **T4** (dono da transação) → **2 transações no worker**. Tx-1 curta
  incrementa `tentativas` antes do dispatch (commit imediato — sobrevive
  a crash). Tx-2 envolve dispatch + `processado_em=now()`. Sem isso,
  poison message vira loop infinito sem contabilidade.
- **T5** (drill multi-tenant serial vs xdist) → **serial intercalado
  basta agora** + nota "drill cronometrado pré-1º tenant externo" em
  `limites-honestos.md`.

## Bloqueantes adicionais

- **BLOQ-A** → predicate RLS de `bus_outbox` deve ser **byte-a-byte
  idêntico** ao de `Auditoria` (`tenant_id = ANY(...)` + cast +
  predicate `tenant_id IS NULL AND modo_sistema='1'`).
- **BLOQ-B** → SELECT do `drenar_outbox` filtra `tentativas < 5` +
  management command `listar_outbox_envenenado` pra DPO/SRE inspecionar
  poison messages.
- **BLOQ-C** → Contrato **at-least-once** explícito no design.
  Consumers Wave A obrigatoriamente idempotentes em `causation_id` (com
  tabela `consumer_idempotencia` per-consumer).
- **BLOQ-D** → **Non-goal ordering por consumer.** Outbox não preserva
  ordem causal sob `SKIP LOCKED`; saga pattern é responsabilidade do
  consumer Wave A.

## Sugestões (SUG)

- SUG-1: `ultimo_erro` precisa sanitizar (concordância com A4 do
  advogado).
- SUG-2: `causation_id` UNIQUE assume `acao` semântica suficiente —
  nota no design pra chamador.
- SUG-3: drill T-CLI-110 inclui golden contract test
  `envelope_entregue == envelope_gravado byte-a-byte`.
- SUG-4: `_REGISTRY` é módulo-level — fixture pytest autouse pra reset
  entre testes.

## Médios (anotar — não bloqueia)

- MED-1: política DELETE da RLS — job de cleanup roda em
  `run_as_system`.
- MED-2: CHECK `pg_column_size(envelope_jsonb) < 64 KiB` (falha alto
  melhor que disco cheio).
- MED-3: `drenar_outbox` pega IDs sem lock; helper individual
  lockeia por linha.

## Limites honestos

- T4 (2 Tx vs 1 Tx) decidido sob teoria, não sob carga concorrente
  real. Reauditoria pré-1º tenant pago obrigatória.
- BLOQ-D (ordering): se Wave A descobrir necessidade de ordem causal
  (ex: `comunicacao-omnichannel` precisa notificar criação antes da
  alteração), fix é saga no consumer, NÃO virar outbox em fila
  ordenada.
- `SKIP LOCKED` aceito sob teoria — pentest ASVS L2 + drill de carga
  (k6/locust/pgbench) antes do 1º tenant externo. Não-goal Marco 1.
