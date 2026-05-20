---
owner: roldao + agente
revisado-em: 2026-05-20
status: stable
---

> **Histórico do ritual (P2 endurecido):** este design saiu em DRAFT,
> entrou em paralelo nos subagentes `tech-lead-saas-regulado` e
> `corretora-seguros-saas` (2026-05-20). 5 bloqueantes (CRÍTICO T2 +
> ALTOS T3, C2 + MÉDIOS T4, T5 + design.md:99) foram absorvidos.
> Pareceres em `review-tech-lead.md` e `review-corretora.md`.

# T-CLI-104 — design final (pós-revisão)

## Escopo

**AC-CLI-002-6** (tech-lead §B item 2 + corretora §B item 1):
circuit breaker **observado** para gravação em `AcessoDadosCliente`.
Falha de gravação ≥ 0.1% em 5min (com total ≥ 1000) **OU** ≥ 3
falhas absolutas em 5min dispara evento P1 imutável na cadeia F-A.
Fail-loud preservado — endpoint NÃO degrada para "permitir sem
registro" (LGPD art. 37).

## Contratos não-negociáveis

1. **Fail-loud preservado.** Se `registrar_acesso_dados_cliente`
   levanta, o caller propaga — sem fallback.
2. **Contagem SOBREVIVE ao rollback do request** (CRÍTICO T2 do
   tech-lead). Conexão paralela autocommit `breaker_writer` registra
   evento `(tenant_id, ts, ok)` ANTES do raise no caller.
3. **Threshold OR** (ALTO C2 corretora + tech-lead): `(pct ≥ 0.1% AND
   total ≥ 1000) OR (falhas_absolutas ≥ 3 em 5min)`. Em dogfooding
   o ramo absoluto cobre janela onde pct é estatisticamente
   irrelevante.
4. **Sliding window** (ALTO T3 tech-lead): consulta `now() - interval
   '5 minutes'` sobre tabela de eventos crus — sem bucket fixo
   subestimando borda.
5. **Sumário de transição na cadeia F-A** (MÉDIO C3 corretora):
   eventos `sistema.breaker_acesso_pii.disparado` e
   `sistema.breaker_acesso_pii.normalizado` na cadeia hash F-A (25
   anos) — não gravar `ok` por chamada (gargalo).
6. **Idempotência do command** (MÉDIO T4 tech-lead): chave
   `(tenant_id, janela_inicio_5min_truncado)` no `causation_id` →
   UNIQUE no `bus_outbox` impede duplicação.

## Design final

### Alias de conexão `breaker_writer` (DATABASES)

```python
# config/settings/base.py — DATABASES
"breaker_writer": {
    **env.db("DATABASE_URL"),  # mesmo banco do `default`
    "ATOMIC_REQUESTS": False,   # AUTOCOMMIT (sobrevive rollback do request)
    "CONN_MAX_AGE": 60,
    "OPTIONS": {"application_name": "afere-breaker-writer"},
    "TEST": {"NAME": "test_afere", "MIGRATE": False, "DEPENDENCIES": []},
}
```

Router já ignora migrations em alias != `migrator` (`allow_migrate
return db == "migrator"`) — `breaker_writer` não cria schema, só
escreve.

### Tabela `breaker_acesso_pii_evento` (migration `audit/0012`)

| coluna | tipo | obs |
|---|---|---|
| `id` | UUID PK | `gen_random_uuid()` default |
| `tenant_id` | UUID NOT NULL | sempre conhecido |
| `ts` | timestamptz NOT NULL DEFAULT now() | |
| `ok` | bool NOT NULL | True = gravação OK; False = falhou |

Índice: `(tenant_id, ts DESC)` pra sliding window.

**RLS:** ENABLE + FORCE. Mesmo padrão do `bus_outbox`:
- SELECT/UPDATE: modo_sistema vê TUDO (cross-tenant pra command de
  avaliação); senão tenant_id do contexto.
- INSERT: modo_sistema com tenant_id=qualquer (escrita autocommit do
  helper roda sem contexto de tenant); OU tenant_id casa contexto.
- DELETE: modo_sistema (cleanup job futuro).

Sob conexão `breaker_writer`, abrimos `run_as_system` interno apenas
pra INSERT.

**Retenção:** 7 dias (cleanup job Wave A; documentado em
`retencao-matriz.md`).

### Função `registrar_acesso_dados_cliente_com_breaker`

```python
def registrar_acesso_dados_cliente_com_breaker(**kwargs):
    try:
        return registrar_acesso_dados_cliente(**kwargs)
    except Exception as exc:
        # Conexão paralela autocommit — sobrevive rollback do caller
        _gravar_evento_breaker(tenant_id=kwargs["tenant_id"], ok=False)
        raise
    finally:
        # Em sucesso: registra ok=True; em falha: ok=False já foi acima
        ...
```

Implementação real: gravar ok=True ANTES do try (a tentativa já
ocorreu), `ok=False` se exceção. Detalhe na implementação.

### Command `avaliar_circuit_breaker_acesso_pii`

```sql
WITH ultimos_5min AS (
    SELECT
        tenant_id,
        COUNT(*) FILTER (WHERE NOT ok) AS falhas,
        COUNT(*) AS total,
        date_trunc('minute', now())
            - interval '1 min' * (extract(minute from now())::int % 5)
            AS janela_inicio
    FROM breaker_acesso_pii_evento
    WHERE ts >= now() - interval '5 minutes'
    GROUP BY tenant_id
)
SELECT tenant_id, falhas, total, janela_inicio
FROM ultimos_5min
WHERE (falhas >= 3)
   OR (total >= 1000 AND falhas * 1000 >= total);
```

Cada linha → `publicar_evento(acao="sistema.breaker_acesso_pii.disparado",
tenant_id=tenant_id, causation_id=uuid5(NAMESPACE_OID, f"breaker:{tenant_id}:{janela_inicio}"),
payload={...})`. UUID5 determinístico → UNIQUE `(causation_id, acao)`
no `bus_outbox` faz idempotência (rodar 2x na mesma janela = não
duplica).

### Eventos canônicos novos

Adicionar a `acoes_canonicas.py`:
- `sistema.breaker_acesso_pii.disparado`
- `sistema.breaker_acesso_pii.normalizado` (Wave A — quando taxa
  volta abaixo do limiar)

### Drill

- `test_breaker_grava_evento_sob_rollback_do_request` — golden test
  do CRÍTICO T2: mock `registrar_acesso_dados_cliente` levantar,
  rodar dentro de `transaction.atomic()`, assertar que linha do
  evento de falha está no banco mesmo com rollback do atomic externo.
- `test_breaker_dispara_em_3_falhas_absolutas` — ramo absoluto.
- `test_breaker_dispara_em_0_1_pct_com_1000_total` — ramo percentual.
- `test_breaker_idempotente_na_mesma_janela` — rodar command 2x =
  1 evento na cadeia.
- `test_breaker_threshold_abaixo_nao_dispara`.
- `test_breaker_ok_e_falha_isolados_por_tenant`.

## Non-goals

- Push real (PagerDuty/Slack/SMS). Wave A.
- Dashboard Grafana. F-C.
- Auto-recovery (breaker que abre/fecha). Hoje só observado.
- Evento `normalizado` ativo (apenas o canônico criado pra futuro).
  Marco 1 entrega só `disparado`.
- Cleanup automático (job Wave A — coleta `ts < now() - 7d`).
- Push real do alerta P1 — corretora C1 cravou em ADR pendente que
  é PRÉ-REQUISITO 1º tenant externo pago.

## Rastreabilidade

- AC-CLI-002-6 (`spec.md` L209-216)
- Tech-lead §B item 2 + corretora §B item 1
- `INV-013` (REGRAS-INEGOCIAVEIS.md)
- ADR cyber Wave A pendente (corretora C1)
