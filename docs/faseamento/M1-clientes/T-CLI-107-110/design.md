---
owner: roldao + agente
revisado-em: 2026-05-20
status: stable
---

> **Histórico do ritual (P2 endurecido):** este design saiu em DRAFT,
> entrou em paralelo nos subagentes `tech-lead-saas-regulado` e
> `advogado-saas-regulado` (2026-05-20). 11 bloqueantes (T4 + BLOQ-A
> + BLOQ-B + BLOQ-C + BLOQ-D + BLOQ-A1..A7) foram absorvidos como
> partes do design abaixo + matriz de retenção atualizada. Veredito
> final dos dois reviews: PROSSEGUIR/AJUSTAR (todos absorvidos), zero
> BLOQUEAR. Pareceres em `review-tech-lead.md` e `review-advogado.md`
> ao lado deste arquivo.

# T-CLI-107 + T-CLI-110 — design endurecido (pré-implementação)

> Ritual Spec Kit: este draft entra em paralelo nos subagentes
> `tech-lead-saas-regulado` + `advogado-saas-regulado` ANTES de codar.
> Bloqueantes absorvidos viram itens novos no design; só depois
> `/implement`. Espelha P2 do Marco 1 (mesma cadência).

## Escopo

- **T-CLI-107** (AC-CLI-004-7 / `INV-INT-010`): tabela `bus_outbox`
  multi-tenant + `publicar_evento(outbox=True)` no helper único
  `event_helpers.publicar_evento` (hoje levanta `OutboxNaoImplementado`).
- **T-CLI-110** (AC-CLI-004-11 — tech-lead §B item 3): helper
  `processar_outbox_em_contexto_tenant(linha)` em
  `src/infrastructure/audit/outbox_worker.py` garantindo
  `INV-TENANT-001..004` no caminho do worker.

## Contratos cravados em P2 (não-negociáveis)

1. **Atomicidade.** INSERT em `bus_outbox` no MESMO `transaction.atomic`
   do chamador, junto com `registrar_em_cadeia`. Helper não abre
   transação própria.
2. **Idempotência** `(causation_id, acao)`: UNIQUE no banco; reentrância
   da chamada não duplica linha.
3. **Sanitização em ESCRITA.** Payload já passa por
   `sanitizar_payload_audit` antes de chegar ao outbox (helper único —
   garantia 1 do `publicar_evento`).
4. **Worker opera em contexto multi-tenant** (`run_in_tenant_context` /
   `run_as_system` quando `tenant_id IS NULL`). Consumer nunca recebe
   mensagem de tenant ≠ contexto ativo.
5. **Hook `event-helper-unico.sh`** já bloqueia INSERT em `bus_outbox`
   fora de `audit/`, `multitenant/`, `tests/`, `migrations/`.

## Design final (P2 endurecido — absorvidos 11 bloqueantes dos 2 reviews)

### Tabela `bus_outbox` (migration `audit/0011_bus_outbox.py`)

| coluna | tipo | obs |
|---|---|---|
| `id` | UUID PK | `gen_random_uuid()` default |
| `causation_id` | UUID NOT NULL | parte da chave de idempotência |
| `acao` | varchar(100) NOT NULL | enum canônico — CHECK anti-PII (BLOQ-A1) |
| `envelope_jsonb` | JSONB NOT NULL | já sanitizado por `publicar_evento` em ESCRITA |
| `tenant_id` | UUID NULL | NULL = evento sistema (provisioning, manutenção) |
| `criado_em` | timestamptz NOT NULL DEFAULT now() | |
| `processado_em` | timestamptz NULL | NULL = pendente; preenchido pelo worker |
| `tentativas` | smallint NOT NULL DEFAULT 0 | dead-letter lógica em `tentativas >= 5` (BLOQ-B) |
| `ultimo_erro` | text NULL | sanitizado + truncado 500c por `sanitizar_erro_para_outbox` (BLOQ-A4) |

**Constraints:**

```sql
-- Idempotência (T-CLI-107 contrato 4)
ALTER TABLE bus_outbox ADD CONSTRAINT bus_outbox_idempotencia
  UNIQUE (causation_id, acao);

-- BLOQ-A1: CHECK constraint anti-PII na `acao` (enum semântico — slug)
ALTER TABLE bus_outbox ADD CONSTRAINT bus_outbox_acao_enum_semantico
  CHECK (
    acao ~ '^[a-z][a-z0-9_]{0,40}(\.[a-z][a-z0-9_]{0,40}){1,3}$'
    AND length(acao) <= 100
  );

-- MED-2: limite de tamanho do envelope (falha alto > disco cheio)
ALTER TABLE bus_outbox ADD CONSTRAINT bus_outbox_envelope_limite_64kb
  CHECK (pg_column_size(envelope_jsonb) < 65536);
```

**Lista canônica de ações:** `src/infrastructure/audit/acoes_canonicas.py`
(módulo de constantes; cada módulo Wave A adiciona suas ações com PR
revisado).

**RLS:** ENABLE + FORCE. **BLOQ-A:** replicar byte-a-byte o predicate
da policy de `Auditoria` (`audit/0002_initial.py`). Verificar antes da
implementação (lendo o SQL existente) — não improvisar.

**Comentário na migration (BLOQ-A5):** "`causation_id` é dado pessoal
indireto sob LGPD art. 12 — restringir SELECT direto a perfis `dpo` +
`sre_aferê` em Wave A (AuthorizationProvider ADR-0012)."

### `publicar_evento(outbox=True)` no `event_helpers.py`

```python
if outbox:
    envelope = {
        "acao": acao,
        "payload": payload_sanitizado,
        "causation_id": str(causation_id),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "usuario_id": str(usuario_id) if usuario_id else None,
        "resource_summary": resource_summary,
    }
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bus_outbox
                (id, causation_id, acao, envelope_jsonb, tenant_id)
            VALUES (gen_random_uuid(), %s, %s, %s::jsonb, %s)
            ON CONFLICT (causation_id, acao) DO NOTHING
            RETURNING id;
            """,
            [str(causation_id), acao, json.dumps(envelope), tenant_id],
        )
        row = cur.fetchone()
        outbox_enfileirado = row is not None  # False = já estava lá
```

- `outbox_enfileirado=False` quando ON CONFLICT atinge linha
  pré-existente (idempotência observável — chamador pode logar mas
  não é erro).
- INSERT roda no `transaction.atomic` do CALLER — `publicar_evento`
  não abre tx própria. Garantia 3 não-negociável (contrato 1).

### `src/infrastructure/audit/outbox_worker.py`

**Helper de sanitização de erro (BLOQ-A4):**

```python
_LIMITE_ULTIMO_ERRO = 500

def sanitizar_erro_para_outbox(exc: BaseException) -> str:
    tipo = type(exc).__name__
    msg = str(exc).splitlines()[0] if str(exc) else ""
    bruto = f"{tipo}: {msg}"
    sanitizado: str = sanitizar_payload_audit({"erro": bruto})["erro"]
    if len(sanitizado) > _LIMITE_ULTIMO_ERRO:
        sanitizado = sanitizado[: _LIMITE_ULTIMO_ERRO - 14] + "...[truncado]"
    return sanitizado
```

**Função pública:** `processar_outbox_em_contexto_tenant(linha_id: UUID)
-> ResultadoOutbox`

**T4 (2 transações):**

```python
def processar_outbox_em_contexto_tenant(linha_id: UUID) -> ResultadoOutbox:
    # Pré-condição: NÃO estar em contexto de tenant (worker entra no certo)
    if active_tenant_context.get(None) is not None:
        raise RuntimeError(
            "processar_outbox_em_contexto_tenant chamado dentro de "
            "run_in_tenant_context — worker deve entrar no contexto certo "
            "ele mesmo (proteção contra troca de tenant no meio)."
        )

    # Tx-1 (curta): lockeia + incrementa tentativas + commit imediato.
    # Sobrevive a crash. Garante que poison message é contabilizado
    # mesmo se o consumer derrubar o processo.
    with run_as_system():
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT id, tenant_id, acao, envelope_jsonb, tentativas
                FROM bus_outbox
                WHERE id = %s AND processado_em IS NULL
                FOR UPDATE SKIP LOCKED
                """,
                [str(linha_id)],
            )
            row = cur.fetchone()
            if row is None:
                return ResultadoOutbox(linha_id=linha_id, status="ja_processada_ou_lockada")
            id_, tenant_id, acao, envelope, tentativas = row
            cur.execute(
                "UPDATE bus_outbox SET tentativas = tentativas + 1, ultimo_erro = NULL "
                "WHERE id = %s",
                [id_],
            )
        # commit da Tx-1 ao sair do `run_as_system`

    # Tx-2: dispatch + marca processado. Se consumer levanta, rollback
    # de processado_em — mas tentativas já foi contabilizado na Tx-1.
    if tenant_id is None:
        ctx = run_as_system()
    else:
        ctx = run_in_tenant_context(UUID(str(tenant_id)))
    try:
        with ctx:
            try:
                dispatch_event(envelope)
                with connection.cursor() as cur:
                    cur.execute(
                        "UPDATE bus_outbox SET processado_em = now() WHERE id = %s",
                        [id_],
                    )
                return ResultadoOutbox(linha_id=linha_id, status="processada")
            except Exception as exc:
                # Tx-2 vai rollback ao sair pelo raise — `processado_em`
                # fica NULL. Grava ultimo_erro numa Tx-3 separada.
                erro_sanitizado = sanitizar_erro_para_outbox(exc)
                raise _ErroConsumer(linha_id=id_, erro=erro_sanitizado) from exc
    except _ErroConsumer as wrapped:
        # Tx-3 (curta): grava ultimo_erro fora do rollback da Tx-2.
        with run_as_system():
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE bus_outbox SET ultimo_erro = %s WHERE id = %s",
                    [wrapped.erro, wrapped.linha_id],
                )
        return ResultadoOutbox(
            linha_id=linha_id, status="falhou", erro=wrapped.erro
        )
```

**Driver `drenar_outbox(limit=100)` — BLOQ-B aplicado:**

```python
def drenar_outbox(limit: int = 100) -> list[ResultadoOutbox]:
    """Worker em modo manual: drena até `limit` linhas pendentes.

    BLOQ-B: filtra `tentativas < 5` — linhas envenenadas ficam
    visíveis no management command `listar_outbox_envenenado` pra
    inspeção de DPO/SRE; param de drenar automaticamente.

    MED-3: pega IDs sem lock; helper individual lockeia cada linha
    no SELECT FOR UPDATE SKIP LOCKED.
    """
    with run_as_system():
        with connection.cursor() as cur:
            cur.execute(
                "SELECT id FROM bus_outbox "
                "WHERE processado_em IS NULL AND tentativas < 5 "
                "ORDER BY criado_em LIMIT %s",
                [limit],
            )
            ids = [row[0] for row in cur.fetchall()]
    return [processar_outbox_em_contexto_tenant(UUID(str(id_))) for id_ in ids]
```

### Registry de consumers (ponto de extensão)

```python
_REGISTRY: dict[str, Callable[[dict], None]] = {}

def registrar_consumer(acao: str, fn: Callable[[dict], None]) -> None:
    if acao in _REGISTRY:
        raise ValueError(f"consumer ja registrado para acao={acao}")
    _REGISTRY[acao] = fn

def _noop(envelope: dict) -> None:
    pass  # Wave A default: nenhum consumer registrado

def dispatch_event(envelope: dict) -> None:
    fn = _REGISTRY.get(envelope["acao"], _noop)
    fn(envelope)

# SUG-4: testes resetam o registry via fixture autouse `clear_outbox_registry`.
```

### Management commands

- **`drenar_outbox_uma_vez`** (T-CLI-107): chama `drenar_outbox()` uma
  vez. Cron real é Wave A.
- **`listar_outbox_envenenado`** (BLOQ-B + parte de BLOQ-A7): lista
  linhas com `tentativas >= 5` exibindo `id, causation_id, acao,
  tenant_id, tentativas, ultimo_erro, criado_em` — **sem
  `envelope_jsonb`** (defesa em profundidade contra exposição de PII
  pelo operador). Endpoint REST `/dpo/outbox-quarentena` fica como
  BACKLOG-WAVE-A documentado (Wave A entrega com perfil dedicado +
  AuthorizationProvider).

### Política LGPD (BLOQ-A6 + SUG-3)

Adicionar a `src/domain/comercial/clientes/lgpd_policy.py`
(`INV-CLI-002`):

```python
POLITICA_BUS_OUTBOX = {
    "natureza": "fila intermediaria nao-evidencia regulatoria",
    "base_legal_herdada": "art. 7 V (execucao contrato) | art. 7 II (obrigacao legal)",
    "prazo_retencao_pos_processado_dias": 7,
    "cascata_offboarding_tenant": True,
    "afetado_por_art18_eliminacao_titular_individual": False,
    "afetado_por_art18_acesso_portabilidade": False,
    "fonte_da_verdade_para_art18": "cadeia_hash_f_a",
    "vetor_pii_acoes_mitigadas": [
        "envelope_jsonb (sanitizado em escrita)",
        "acao (CHECK constraint enum semantico)",
        "ultimo_erro (sanitizar_erro_para_outbox)",
        "causation_id (acesso restrito a dpo+sre)",
    ],
}
```

### Matriz de retenção (BLOQ-A2)

Adicionar linha em `docs/conformidade/comum/retencao-matriz.md` §2:

| Categoria | Prazo mín | Prazo máx | Base legal | Local | Ação fim |
|---|---|---|---|---|---|
| `bus_outbox` (fila intermediária de eventos de domínio) | processado_em + 0 | processado_em + 7 dias | LGPD art. 6º III (minimização) | PG | DELETE físico (cleanup; cascata via `tenant_id` em offboarding) |

DRILL-RET-11 em §5: "linhas em `bus_outbox` com `processado_em <
now() - 7 dias` retornam zero". Mensal.

### Contrato pra consumers Wave A (BLOQ-C)

Documentar no `outbox_worker.py` docstring de `registrar_consumer`:

> **Contrato at-least-once.** O outbox garante entrega ao menos uma
> vez; consumer pode receber o mesmo `(causation_id, acao)` em mais
> de uma chamada (crash entre side-effect e commit, replay manual,
> etc). Consumers Wave A DEVEM ser idempotentes em
> `envelope['causation_id']`: side-effects externos (HTTP, e-mail,
> fiscal) sob responsabilidade do consumer registrar tabela
> `consumer_idempotencia(consumer_name, causation_id)` UNIQUE com
> `ON CONFLICT DO NOTHING` antes do side-effect.

### Testes (consolidados)

**T-CLI-107 (outbox + helper):**
- `test_publicar_evento_outbox_true_grava_linha`
- `test_publicar_evento_outbox_idempotente_em_causation_acao`
- `test_publicar_evento_outbox_sob_rls_tenant_a_nao_ve_b`
- `test_publicar_evento_outbox_payload_ja_sanitizado`
- `test_publicar_evento_outbox_no_mesmo_atomic_do_caller` (cadeia +
  outbox commitam OU rolam JUNTOS)
- `test_acao_check_constraint_rejeita_string_com_cpf` (BLOQ-A1)
- `test_envelope_check_constraint_rejeita_64kb_plus` (MED-2)
- `test_predicado_rls_bus_outbox_byte_a_byte_igual_ao_de_auditoria`
  (BLOQ-A)

**T-CLI-110 (worker):**
- `test_worker_processa_linha_em_contexto_correto`
- `test_worker_3_tenants_intercalados_zero_vazamento` (drill principal)
- `test_worker_consumer_falha_tentativas_incrementa_processado_em_NULL`
  (T4 — Tx-1 commitou; Tx-2 rolled-back)
- `test_worker_poison_message_para_apos_5_tentativas` (BLOQ-B)
- `test_worker_skip_locked_dois_workers_separados_nao_dupla_processa`
- `test_worker_tenant_null_so_processa_em_modo_sistema`
- `test_worker_fail_loud_se_chamado_dentro_de_contexto_tenant`
- `test_worker_envelope_entregue_eh_byte_a_byte_o_gravado` (SUG-3)
- `test_worker_ultimo_erro_sanitiza_pii_em_stack_trace` (BLOQ-A4)
- `test_worker_ultimo_erro_truncado_em_500_chars` (BLOQ-A4)
- `test_worker_registry_isolado_entre_testes` (SUG-4)
- `test_listar_outbox_envenenado_command_oculta_envelope` (BLOQ-A7)

## Non-goals (cravados)

- **Cron/Procrastinate real do worker.** Wave A entrega; aqui só
  helper + management command pra invocar manual + testes.
- **Consumers reais.** São módulos Wave A (`operacao/agenda`,
  `operacao/certificados`, `comunicacao-omnichannel`); aqui só
  registry vazio.
- **Métricas / observabilidade do outbox** (lag, taxa de erro, PII
  slip-through). Wave A com OBS-003.
- **Cleanup automático** (job que remove `processado_em < now() - 7d`).
  Job separado em Wave A.
- **Endpoint REST `/dpo/outbox-quarentena`** (BLOQ-A7). Wave A com
  perfil dedicado AuthorizationProvider. Aqui só management command.
- **Ordering por consumer** (BLOQ-D). `SKIP LOCKED` quebra ordem;
  consumers que precisem de causalidade implementam saga pattern por
  conta própria.
- **Drill cronometrado de carga concorrente real** (k6/locust). Pré-1º
  tenant pago. Marco 1 fica no drill serial 3 tenants intercalados.
- **DPO formalmente designado** (LGPD art. 41). Pré-1º tenant
  externo pago.

## Rastreabilidade

- AC-CLI-004-7, AC-CLI-004-11 (`spec.md`)
- P-CLI-T2 ajustado, tech-lead §A/§B/§D (`plan.md`)
- `INV-INT-010` (`REGRAS-INEGOCIAVEIS.md`)
- Hook `event-helper-unico.sh` (já existe)
- Sucessor: P5 — auditores Família 5.
