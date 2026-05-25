---
adr: 0065
titulo: Concorrência em calibração metrológica — UNIQUE composto + optimistic locking + advisory lock por calibracao_id
status: aceito
data: 2026-05-25
aceito-em: 2026-05-25 (P3 ritual Spec Kit M4 — bloqueio P-CAL-T1 + P-CAL-T3 do review tech-lead)
proposto-por: tech-lead-saas-regulado (review P2 M4)
revisado-por: roldao
bloqueia-fase: Wave A Marco 4 (calibracao)
depende-de: ADR-0041 (OS concorrência atividades — paralelo), ADR-0007 (camada domínio), ADR-0033 (bus idempotência)
---

# ADR-0065 — Concorrência em calibração metrológica

## Contexto

Review P2 do tech-lead-saas-regulado (P-CAL-T1 + P-CAL-T3) identificou que a spec do M4 declara entidades sem mecanismo de serialização concorrente. Em produção com 3 metrologistas concorrentes no mesmo dispositivo serial multiplexado, ou em retry de procrastinate sob carga, há 4 vetores de quebra:

1. **`registrar_leitura`** — duas leituras paralelas com mesmo `(calibracao_id, ponto_calibracao, numero_repeticao)` viram duas linhas legítimas. `OrcamentoIncerteza.calcular()` puxa N=4 quando deveria N=3 → `u_combinada` errada → cert com incerteza errada → cadeia ISO 17025 cl. 7.5 **rasgada**.

2. **`PadraoUsado`** — INSERT duplo do mesmo padrão na mesma calibração pré-revisão. Snapshot rastreabilidade duplicado.

3. **Transição estado-máquina** — `configurada → em_execucao` por "1ª leitura registrada". Duas requisições paralelas: cada uma vê `status='configurada'`, ambas executam UPDATE. Sem CAS, ambas commitam. Estado consistente, eventos duplicados, INV-CAL-WORM-001 silenciosamente burlado.

4. **Hash-chain `EventoDeCalibracao`** — duas transações T1 (registra leitura) e T2 (corrige leitura anterior) inserindo `EventoDeCalibracao` simultâneas leem o mesmo `evento_anterior_hash` em snapshot READ COMMITTED. Ambas commitam com mesmo predecessor → cadeia **garfada**. Auditor CGCRE rastreando "qual foi o evento antes de RevisaoAprovada?" não consegue ordenar deterministicamente — fere INV-CAL-AUD-001 hash-chain prometido.

ADR-0041 resolveu cenário paralelo no Marco 3 OS (concorrência de atividades). M4 metrológico tem **superfície maior** (leituras + padrões + cálculos + hash-chain) e **consequência maior** (cert metrológico errado = recall + suspensão CGCRE).

## Decisão

**4 mecanismos cumulativos** aplicados desde a 1ª migration M4 P1, com hook validador:

### 1. UNIQUE composto em `leitura` (idempotência forte mesmo com `client_event_id NULL`)

```sql
CREATE UNIQUE INDEX idx_leitura_unica ON leitura (
  tenant_id, calibracao_id, ponto_calibracao, numero_repeticao
);
```

INSERT/UPDATE duplicado estoura `unique_violation` → application retorna `412 LeituraDuplicada` (idempotente — mesma `(ponto, repeticao)` cliente legítimo recebe `200` no replay com mesmo `Idempotency-Key`).

### 2. UNIQUE parcial em `padrao_usado` (anti-duplicação pré-snapshot-lock)

```sql
CREATE UNIQUE INDEX idx_padrao_usado_unico ON padrao_usado (
  tenant_id, calibracao_id, padrao_id
) WHERE snapshot_lock = false;
```

Dois INSERTs do mesmo padrão na mesma calibração pré-revisão → unique violation → 412. Após `snapshot_lock=true` (transição `→ em_revisao_1`), índice parcial libera entrada (mas trigger PG separado bloqueia INSERT pós-lock).

### 3. Optimistic locking em `calibracao` via `revision INTEGER`

```sql
ALTER TABLE calibracao ADD COLUMN revision INTEGER NOT NULL DEFAULT 0;

-- Update com CAS:
UPDATE calibracao
SET status = :novo, revision = revision + 1
WHERE id = :id AND revision = :expected_revision
RETURNING revision;
-- 0 rows affected → 409 ConflitoVersao
```

Aplicado em todas as transições de estado (`configurarCalibracao`, `iniciarLeituras`, `solicitarRevisao`, `aprovarRevisao`, `rejeitarRevisao`, `aprovar2aConferencia`, `marcarNaoConformidade`, `resolverNaoConformidade`, `subcontratarCalibracao`, `registrarRecebimentoSubcontratado`, `cancelarCalibracao`).

### 4. Advisory lock por `(tenant_id, calibracao_id)` em `calcular_incerteza` + `append_evento_calibracao`

```python
def calcular_incerteza(calibracao_id: UUID, tenant_id: UUID) -> OrcamentoIncerteza:
    with transaction.atomic():
        # Serializa cálculo + persistência pra essa calibracao
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s || %s::text))",
            [str(tenant_id), str(calibracao_id)]
        )
        # leitura completa de leituras + componentes + cálculo + INSERT OrcamentoIncerteza
        ...

def append_evento_calibracao(calibracao_id, tenant_id, payload):
    with transaction.atomic():
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s || %s::text))",
            [str(tenant_id), str(calibracao_id)]
        )
        # SELECT MAX(sequencia_local) WHERE calibracao_id=... → próxima
        # INSERT EventoDeCalibracao com evento_anterior_hash = MAX(evento_hash)
        ...
```

Garante:
- Dois `calcular_incerteza` paralelos na mesma calibração ficam em fila (não corrida).
- Dois `append_evento_calibracao` paralelos na mesma calibração ficam em fila → hash-chain ordenada deterministicamente.

### 5. Constraint `UNIQUE(tenant_id, calibracao_id, sequencia_local)` + IDENTITY por calibração

```sql
ALTER TABLE evento_de_calibracao
  ADD COLUMN sequencia_local BIGINT NOT NULL;

-- Trigger BEFORE INSERT: sequencia_local = COALESCE(MAX, 0) + 1 por (tenant_id, calibracao_id)

CREATE UNIQUE INDEX idx_evento_calibracao_seq
  ON evento_de_calibracao (tenant_id, calibracao_id, sequencia_local);
```

Auditor CGCRE lê `sequencia_local` 1, 2, 3, ... sem ambiguidade. Combinado com advisory lock no append, sequência é monotônica dentro de cada calibração.

## Invariantes novas

- **INV-CAL-CONC-001:** `leitura` tem UNIQUE composto `(tenant_id, calibracao_id, ponto_calibracao, numero_repeticao)`; INSERT duplicado retorna 412 `LeituraDuplicada`.
- **INV-CAL-CONC-002:** `padrao_usado` tem UNIQUE parcial `(tenant_id, calibracao_id, padrao_id) WHERE snapshot_lock=false`; INSERT duplicado retorna 412 `PadraoUsadoDuplicado`.
- **INV-CAL-CONC-003:** `calibracao.revision` é coluna de optimistic lock; UPDATE com `WHERE revision != esperado` retorna 0 rows → 409 `ConflitoVersao`.
- **INV-CAL-CONC-004:** `calcular_incerteza` e `append_evento_calibracao` adquirem `pg_advisory_xact_lock(hashtext(tenant_id::text || calibracao_id::text))` antes de qualquer SELECT/INSERT.
- **INV-CAL-AUD-002:** Hash-chain `EventoDeCalibracao` é serializada por `(tenant_id, calibracao_id)` via advisory lock + UNIQUE `sequencia_local` BIGINT IDENTITY por calibração.

## Hook validador

`migration-concorrencia-calibracao-check.sh` (criar em M4 P9):
- Bloqueia migration que cria tabela em `src/infrastructure/calibracao/migrations/**` sem UNIQUE índice declarado em `(tenant_id, calibracao_id, ...)`.
- Allow via `# concorrencia-calibracao: skip -- <razão ≥10 chars>`.
- Paralelo a `migration-concorrencia-os-check.sh`.

## Drill obrigatório

`tests/carga/test_concorrencia_registrar_leitura.py` (P4 M4):
- 50 threads concorrentes tentam INSERT mesma `(calibracao_id, ponto, repeticao)`.
- Esperado: **1 sucesso + 49 retornos 412 `LeituraDuplicada`**.

`tests/regressao/test_hash_chain_calibracao_concorrente.py`:
- 100 INSERTs concorrentes em 4 workers procrastinate.
- Recompute `evento_hash` a partir de `payload_sanitizado + evento_anterior_hash + tenant_id + occurred_at` para cada linha.
- Esperado: **cadeia inteira valida em ordem `sequencia_local 1..100`** sem garfo.

`tests/carga/test_calibracao_revision_cas.py`:
- 50 threads tentam `aprovar_revisao` simultâneo na mesma calibração.
- Esperado: **1 sucesso + 49 409 `ConflitoVersao`**.

## Caminhos alternativos considerados

| Alternativa | Por que NÃO |
|---|---|
| PG advisory lock como mecanismo primário (sem UNIQUE) | Sob bypass de aplicação (migration ad-hoc, admin Django, raw SQL) lock não protege. Constraint declarativa sobrevive. |
| Pessimistic locking via `SELECT FOR UPDATE` em todas as queries | Contenção excessiva sob 200 calibrações concorrentes em tenants diferentes; deadlocks frequentes em hot paths. |
| Append-only sem hash-chain (só timestamp ordering) | Auditor CGCRE exige integridade criptográfica entre eventos (cl. 7.5 + 8.4); timestamp não basta. |
| Hash-chain global por tenant (não por calibração) | Sob 50 calibrações concorrentes do mesmo tenant, lock global vira gargalo. Por calibração isola contenção. |

## Consequências

### Positivas

- Constraint declarativa em `(tenant_id, calibracao_id, ponto, repeticao)` sobrevive a bypass de aplicação.
- Hash-chain determinística por calibração — auditor CGCRE rastreia ordem 1, 2, 3 com `sequencia_local`.
- Optimistic locking via `revision` é low-contention vs `FOR UPDATE`.
- Drill cronometrado em P4 valida sob carga real (4 workers procrastinate).

### Negativas (mitigáveis)

- Contenção potencial no `hashtext` de advisory lock sob 1000 calibrações concorrentes em tenants diferentes (collision rate baixo mas não-zero). Drill em P4 mede.
- `revision INTEGER` adiciona 4 bytes por linha em `calibracao`. Negligível.
- Hook validador novo (`migration-concorrencia-calibracao-check.sh`) — 1 hook a manter; teste no `_test-runner.sh`.

## Non-goals

- NÃO aplica advisory lock global por tenant (não escala em multi-tenant).
- NÃO impede DROP/ALTER da tabela (DBA com acesso direto sempre pode). Hook só bloqueia migration via aplicação.
- NÃO substitui retry idempotente — INV-CAL-IDEMP-001 (chave com hash do payload) é complementar.

## Implicações pro faseamento

- **M4 P1 (modelos+migrations):** 5 UNIQUE índices + `revision` column criados desde a 1ª migration.
- **M4 P3 (predicates+authz):** sem mudança.
- **M4 P4 (use cases):** todas as 11 transições de estado fazem CAS via `revision`.
- **M4 P6 (consumers+sagas):** `consumer_idempotente` decorator usa advisory lock pra evitar replay garfando chain.
- **M4 P9 (hooks):** `migration-concorrencia-calibracao-check.sh` criado.
- **M4 P10 (regressões+drill):** 3 drills cronometrados obrigatórios.

## Status

**ACEITO 2026-05-25** — P3 ritual Spec Kit M4. Implementado em M4 P1+P4+P6+P9+P10.
