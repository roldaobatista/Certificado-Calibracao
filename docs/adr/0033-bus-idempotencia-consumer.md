---
adr: 0033
titulo: Bus de eventos — idempotência de consumer + dead-letter
owner: roldao
revisado-em: 2026-05-22
status: proposta
proposto-por: agente (auditoria projeto-inteiro 10 lentes — Onda 1 transversal)
revisado-por: tech-lead-saas-regulado
bloqueia-fase: Wave A Marco 3 (`os` é primeiro consumer cross-módulo crítico)
depende-de: ADR-0007 (camada domínio), ADR-0015 (lifecycle tenant — outbox), IDEMP-002 (REGRAS)
---

# ADR-0033 — Idempotência de consumer + dead-letter no bus

## O QUE

Cravar **schema canônico** + **comportamento obrigatório** de 2 tabelas que destravam o bus de eventos:

- `consumer_idempotencia` — handler de evento marca `(consumer_id, event_id)` como processado.
- `dead_letter_events` — eventos que falharam ≥N tentativas vão para inspeção manual sem perder.

Hoje IDEMP-002 (REGRAS) **manda** que todo consumer seja replay-safe — mas o repositório não tem schema do banco nem política de retenção/limpeza. Cada Marco está implementando do seu jeito (drift detectado na auditoria Onda 1).

## PORQUE

- Bus = procrastinate (ADR-0007). Worker pode entregar o mesmo evento ≥2x (default de queue distribuída).
- Sem idempotência cravada: comissão paga 2x, OS criada 2x, e-mail enviado 2x (IDEMP-002 consequência).
- Sem dead-letter: handler com bug derruba toda a fila — replay infinito sufoca DB.
- Auditoria projeto-inteiro detectou: A-INT-08 (Onda 1) "tabela `consumer_idempotencia` referenciada em REGRAS e ADRs porém sem schema SQL canônico".

## COMO

### Schema canônico SQL

```sql
-- 1. consumer_idempotencia
CREATE TABLE consumer_idempotencia (
    consumer_id      varchar(120)  NOT NULL,
    event_id         uuid          NOT NULL,
    tenant_id        uuid          NOT NULL,
    processado_em    timestamptz   NOT NULL DEFAULT now(),
    resultado        varchar(16)   NOT NULL CHECK (resultado IN ('ok','skip','erro_rastreado')),
    PRIMARY KEY (consumer_id, event_id)
);
CREATE INDEX idx_cons_idemp_tenant_data ON consumer_idempotencia(tenant_id, processado_em);

-- 2. dead_letter_events
CREATE TABLE dead_letter_events (
    id                 uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
    consumer_id        varchar(120)  NOT NULL,
    event_id           uuid          NOT NULL,
    event_name         varchar(120)  NOT NULL,
    tenant_id          uuid          NOT NULL,
    payload            jsonb         NOT NULL,
    erro_classe        varchar(180)  NOT NULL,
    erro_mensagem      text          NOT NULL,
    erro_stack         text,
    tentativas         integer       NOT NULL,
    primeira_tentativa timestamptz   NOT NULL,
    ultima_tentativa   timestamptz   NOT NULL,
    status             varchar(16)   NOT NULL DEFAULT 'aberto'
                       CHECK (status IN ('aberto','reprocessar','descartado','resolvido')),
    resolucao_nota     text,
    resolvido_em       timestamptz,
    resolvido_por_id   uuid
);
CREATE INDEX idx_dle_status_data ON dead_letter_events(status, ultima_tentativa);
CREATE INDEX idx_dle_consumer    ON dead_letter_events(consumer_id);
```

### Comportamento obrigatório do consumer

1. `BEGIN` transação.
2. `INSERT INTO consumer_idempotencia (...) ON CONFLICT (consumer_id, event_id) DO NOTHING RETURNING 1`.
3. Se nenhuma linha voltou: handler já processou → `COMMIT` (no-op idempotente) e retorna.
4. Se inseriu: executa side-effect + `COMMIT`.
5. Em exceção: marca `consumer_idempotencia.resultado='erro_rastreado'` (não bloqueia retry) e re-raise.
6. Procrastinate aplica backoff (5s, 30s, 5min, 30min, 2h). Após **5 tentativas falhas**: dispatcher copia para `dead_letter_events` e remove da fila.

### Política de retenção

- `consumer_idempotencia`: 90 dias (TTL job diário). Evento mais antigo é descartado — replay > 90d cai para retry normal (raro porque queue não atrasa tanto).
- `dead_letter_events`: indefinido até `status IN ('descartado','resolvido')` + 1 ano.

### Operação humana

- Painel admin Aferê: lista `dead_letter_events.status='aberto'`, permite re-publicar (volta para fila) ou descartar (com nota ≥30 chars + audit).
- Alerta P1: ≥10 entries `aberto` por consumer em ≤1h.

## ID

- **INV-BUS-001** — todo consumer registrado no bus implementa o pattern `INSERT ON CONFLICT DO NOTHING` em `consumer_idempotencia` antes do side-effect. Hook `bus-envelope-validator.sh` estende-se na Onda 4.
- **INV-BUS-002** — evento que excede 5 tentativas vai automaticamente para `dead_letter_events` (não fica em loop infinito). Worker procrastinate configurado com `max_retries=5`.
- **INV-BUS-003** — `dead_letter_events` é **append-only operacional** — só `status` + `resolucao_nota` + `resolvido_em` + `resolvido_por_id` podem ser atualizados. Trigger PG bloqueia mudança em outras colunas (`audit-immutability-check`).

## NON-GOAL

- **Não** implementa exactly-once delivery — apenas at-least-once + idempotência do consumer.
- **Não** implementa replay seletivo por janela temporal (V2 — pode ser construído sobre o outbox quando demanda existir).
- **Não** substitui auditoria — `consumer_idempotencia` é operacional (90d); auditoria fica em `audit_trail` (25 anos).

## Consequências

**Boas:** consumer de qualquer módulo nasce com pattern único; auditor `auditor-idempotencia` valida mecanicamente; dead-letter dá controle operacional sem perder evento.

**Ruins:** custo de storage adicional (~estimado 50 MB/mês por 100k eventos/dia/tenant); job de limpeza diário.

## Referências cruzadas

- ADR-0007 (camada domínio + outbox)
- ADR-0036 (replay determinístico + versionamento schema) — par desta ADR
- IDEMP-001/002 (REGRAS-INEGOCIAVEIS.md)
- ADR-0015 fluxo 1 (provisioning state machine — exemplo de consumer multi-step)
