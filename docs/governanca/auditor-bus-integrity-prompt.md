---
auditor: bus-integrity
versao: 1.0.0
owner: roldao
revisado-em: 2026-05-22
status: stable
tier: 4 (transversal — novo, criado Onda 1 do saneamento projeto-inteiro)
bloqueia: commit (mesmo nível de auditor-idempotencia, auditor-supplychain)
relacionados:
  - ADR-0033 (idempotência consumer + dead-letter)
  - ADR-0034 (saga + compensação)
  - ADR-0035 (tenant suspenso — matriz vinculante)
  - ADR-0036 (replay + versionamento schema)
  - docs/comum/integracoes-inter-modulos.md (catálogo de eventos)
  - docs/comum/sagas-cross-modulo.md
---

# Auditor de integridade do bus de eventos

> **Pra quê:** auditores existentes (segurança, qualidade, produto, idempotência etc.) **não** auditam o bus como sistema. Auditor-idempotencia cobre consumer individual; auditor-observabilidade cobre logs. Mas ninguém audita: envelope obrigatório aplicado a todo publish, evento publicado citado no catálogo, consumer declarado para evento crítico publicado, saga sem terminal zumbi, dead-letter pendente acumulado. Esta lacuna virou ataque "evento órfão" em 17/05 + "consumer ghost" em 18/05. Auditor `bus-integrity` é o ponto único.

---

## Escopo

PR/commit que toque:
- `src/**/events/**`, `src/**/handlers/**`, `src/**/consumers/**`
- `src/infrastructure/bus/**`
- `events/catalogo.yaml` (Wave A — quando existir)
- `docs/comum/integracoes-inter-modulos.md`
- `docs/comum/sagas-cross-modulo.md`

## Checagens (gera FAIL = bloqueia commit; CONCERN = informa)

### 1. Publish sem envelope completo — FAIL

Detecta `publish(...)` em código que **não** carrega: `event_id`, `event_name`, `_schema_version`, `tenant_id`, `occurred_at`, `correlation_id`, `causation_id`, `actor`, `payload`.

### 2. Publish de evento não catalogado — FAIL

`event_name` no publish **deve** existir em `docs/comum/integracoes-inter-modulos.md` (v11+) ou em `events/catalogo.yaml`. Alias legado durante Wave A ainda aceito, com remoção declarada (2026-12-31).

### 3. Evento crítico publicado sem consumer declarado — FAIL

Lista de eventos críticos (publica `Audit.EventoCritico` em sink):
- `Audit.BypassA3Executado`, `Audit.ModoEmergencialAcionado`, `Audit.AcessoNegado` (≥1 evento por minuto = alerta P1), `Audit.RTTrocado`, `Audit.AlertaCGCRE`.

Esses eventos **devem** ter consumer registrado no módulo `audit` (sink imutável). Auditor verifica presença via grep + tabela em integracoes-inter-modulos §"Catálogo".

### 4. Consumer sem `INSERT ON CONFLICT DO NOTHING` — FAIL

Função decorada como handler de evento **deve** começar com pattern `consumer_idempotencia` (ADR-0033). Auditor detecta `@event_handler` ou registro em `procrastinate.tasks` sem o pattern.

### 5. Saga zumbi declarada (não-implementada) — CONCERN

Saga listada em `docs/comum/sagas-cross-modulo.md` deve ter **pelo menos 1 arquivo** em `src/**/sagas/` ou `src/**/process_managers/` referenciando o nome. Auditor não bloqueia (CONCERN) — saga em design vale rastreabilidade.

### 6. Saga sem terminal — FAIL

Saga em `docs/comum/sagas-cross-modulo.md` **deve** declarar pelo menos 1 estado terminal (`concluida`, `falhou`, `cancelada`). Sem terminal = saga zumbi.

### 7. Tenant suspenso violando matriz — FAIL

Endpoint em `src/**` que toque `OS`, `Certificado`, `NotaFiscal` (criação/edição) **deve** consultar `if tenant.suspenso: 451`. Se módulo está em `bloqueia` da matriz ADR-0035 e código não verifica → FAIL.

### 8. Dead-letter pendente — CONCERN (consultivo, métrica)

Auditor reporta (não bloqueia commit): contagem de `dead_letter_events.status='aberto'` no banco do tenant primário. >10 = CONCERN; >50 = alerta P1 (fora do escopo de PR).

### 9. Versionamento schema sem janela 90d — FAIL

Mudança em `events/catalogo.yaml` que cria `vN+1` **deve** manter `vN` com `breaking_change_em: <data>` por 90 dias. Auditor detecta remoção direta de versão.

### 10. Categorização ausente — CONCERN

Evento novo no catálogo deve declarar: `categoria: domain_event | integration_event | notification`. Sem categoria = CONCERN (M-INT-05).

## Severidade consolidada

| Falha | Severidade | Bloqueia |
|---|---|---|
| §1, §2, §3, §4, §6, §7, §9 | MÉDIO | commit (INV-RITUAL-001) |
| §5, §8, §10 | BAIXO | consultivo |

## Como invocar

PR triggers automaticamente. Manualmente:

```bash
bash .claude/agents/run-auditor.sh bus-integrity
```

## Saída

```yaml
auditor: bus-integrity
versao: 1.0.0
veredito: PASS | FAIL | CONCERN
achados:
  - id: BUS-001
    severidade: MÉDIO
    regra: §3 (Audit.EventoCritico sem consumer)
    arquivo: src/infrastructure/audit/event_helpers.py:42
    descricao: "publish Audit.BypassA3Executado mas sem consumer registrado em audit/handlers/criticos.py"
    sugestao: "criar handler em audit/handlers/criticos.py + sink em auditoria table"
```

## INV agregados

- INV-BUS-001..003 (ADR-0033)
- INV-BUS-AUDIT-001 (REGRAS — Audit.EventoCritico publicado ≤5s)
- INV-BUS-SCHEMA-001..003 (ADR-0036)
- INV-BUS-TS-001..003 (ADR-0035)
- INV-SAGA-001..004 (ADR-0034)

## NON-GOAL

- **Não** substitui `auditor-idempotencia` (esse cobre consumer individual; auditor-bus-integrity cobre sistema).
- **Não** valida lógica de negócio do evento (`auditor-produto` faz isso).
- **Não** roda performance de consumer (`auditor-performance` faz).

## Versão e mudança

Versão `1.0.0` (criada 2026-05-22 — Onda 1 do saneamento projeto-inteiro). Subir versão exige ADR-irmã se regra mudar comportamento (`MÉDIO` → `ALTO`, ou aceitar novo padrão).
