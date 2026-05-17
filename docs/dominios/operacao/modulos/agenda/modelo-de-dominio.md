---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: agenda
dominio: operacao
---

# Modelo de domínio — Módulo Agenda

> Técnico, Cliente vivem em `docs/comum/modelo-de-dominio.md`. Hook valida não-duplicação.

---

## Entidades

### Agenda — agregado raiz (por técnico × período)

A Agenda é a coleção de slots de UM técnico. Composição é virtual (não é tabela única) — slots vivem na tabela `evento_agenda` indexados por `tecnico_id` + `inicia_at`.

### EventoAgenda

- **Obrigatórios:** `id`, `tenant_id`, `tecnico_id`, `inicia_at`, `termina_at`, `tipo` (enum: os | bloqueio | descanso_legal | deslocamento | almoco | manutencao_interna | feriado), `criado_at`, `criado_por`.
- **Opcionais:** `os_id` (se tipo=os), `motivo` (se tipo=bloqueio), `recorrencia_id`, `geo_origem`, `geo_destino` (deslocamento), `aprovado_pelo_cliente_at`, `notas`.
- **Invariantes:** `INV-020` (jornada UMC), regra de não-conflito (`unique(tecnico_id, inicia_at, termina_at)` com overlap proibido), RAT-08.
- **Ciclo de vida:** criado em qualquer momento futuro; eventos passados ficam imutáveis (audit). Move = update de timestamps + audit.

### Bloqueio

Tipo especial de EventoAgenda com `tipo=bloqueio`. `motivo` ∈ {ferias, treinamento, atestado, outro}. Não aceita OS sobreposta.

### Feriado

`tipo=feriado`. Pode ser nacional (catálogo nacional default), estadual, municipal ou custom do tenant. Bloqueia agendamento de OS default; gerente pode forçar com confirmação.

### Recorrencia

- `id`, `tecnico_id`, `template_evento` (JSON), `regra_rrule` (RFC 5545 — ex: `FREQ=WEEKLY;BYDAY=MO`), `inicia_em`, `termina_em`, `criada_at`.
- Job diário materializa os próximos 90 dias em EventoAgenda.

### CapacidadeTecnico

- `tecnico_id`, `dia_semana` (0-6), `horas_uteis_max`, `inicio_jornada`, `fim_jornada`.
- Snapshot por período (versionado quando muda contrato/CLT).

### EventoAuditoria (append-only)

`evento_agenda_id`, `acao` (criado | movido | cancelado | aprovado), `de`, `para`, `at`, `ator_id`. Cobre RAT-08.

---

## Validação INV-020 — Lei 13.103 + CLT 235-C (CRÍTICA)

Hook `validar_jornada_umc(tecnico_id, inicia_at, termina_at)`:

1. **Identifica se técnico opera UMC** (flag no perfil).
2. **Carrega jornada das últimas 24h + próximas 24h** do técnico.
3. **Regra 1 (11h ininterruptas):** entre término da última jornada e início da próxima, ≥ 11h.
4. **Regra 2 (30min/5h30):** dentro de uma jornada contínua de direção, a cada 5h30 deve haver ≥ 30min de descanso (tipo `descanso_legal`).
5. **Regra 3 (tempo-espera):** se evento marca `tempo_espera=true`, conta como 1/3 (sobreaviso).
6. Retorna `{ok: bool, violacao?: string, sugestao_proximo_slot?: timestamp}`.

**Comportamento:**
- API bloqueia POST/PATCH com 422 se violação.
- UI mostra **antes** de salvar (validação no drag) — não pode aceitar e rejeitar depois.
- Audit log grava TODA tentativa que foi bloqueada (compliance trabalhista).

---

## Detecção de conflito

Função `detectar_conflito(tecnico_id, inicia_at, termina_at, exclude_id?)`:
1. Busca eventos do técnico com overlap temporal.
2. Se houver: bloqueia salvar; UI mostra evento conflitante.
3. **Nunca move automaticamente** — gerente decide.

---

## Agregados

| Raiz | Inclui | Invariantes |
|---|---|---|
| EventoAgenda | EventoAuditoria | INV-020, unique-overlap, RAT-08 |
| Recorrencia | (materializa em EventoAgenda) | — |

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| TipoEvento | enum (7) | Sim |
| Janela | {inicia_at, termina_at} | Sim |
| RegraRecorrencia | RRULE RFC 5545 | Sim |

## Eventos publicados

| Evento | Quando | Payload | Consumidores |
|---|---|---|---|
| `AgendaSlotAlocado` | EventoAgenda criado com tipo=os | `{tenant_id, tecnico_id, os_id, slot}` | os (estado AGENDADA), crm |
| `AgendaReagendada` | move de EventoAgenda tipo=os | `{tenant_id, os_id, slot_antigo, slot_novo}` | os, crm (notifica cliente) |
| `AgendaBloqueada` | tipo=bloqueio criado | `{tenant_id, tecnico_id, slot, motivo}` | rh, observabilidade |
| `JornadaUMCViolada` | hook bloqueou tentativa | `{tenant_id, tecnico_id, tentativa, violacao}` | auditor, dpo |

## Comandos

| Comando | Pré | Pós |
|---|---|---|
| `criarEvento` | sem conflito + INV-020 ok | EventoAgenda criado + evento |
| `moverEvento` | mesmas pré + audit do antigo slot | EventoAgenda atualizado + AgendaReagendada |
| `criarBloqueio` | gerente; motivo válido | EventoAgenda tipo=bloqueio |
| `materializarRecorrencia` | job interno | EventoAgenda para próximos 90d |
| `aprovarReagendamento` | cliente via portal | `aprovado_pelo_cliente_at` setado |

## Schema físico

Tabelas: `evento_agenda` (com índices em tecnico_id + tempo), `recorrencia`, `capacidade_tecnico`, `feriado`, `evento_auditoria_agenda`.

## Diagrama

```mermaid
classDiagram
    Tecnico --> EventoAgenda : 1..*
    EventoAgenda --> OS : 0..1 (tipo=os)
    EventoAgenda --> Recorrencia : 0..1
    EventoAgenda --> EventoAuditoria : 1..*
```

## Como evolui

Atributo novo → migration. Mudança em regra INV-020 → ADR (regulado por lei federal).
