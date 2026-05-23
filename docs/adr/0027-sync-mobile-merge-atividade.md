---
adr: 0027
titulo: Sync mobile com merge por atividade (atualiza ADR-0004 pós-ADR-0023)
status: aceito
data: 2026-05-23
aceito-em: 2026-05-23 (Onda 6 saneamento — destravar Marco 3 OS + app-tecnico)
proposto-por: agente (auditoria 10 lentes — TEMA-F.4 + TEMA-C.7)
revisado-por: tech-lead-saas-regulado + corretora-seguros-saas
bloqueia-fase: Wave A Marco 3 (os) + Wave A app-tecnico
depende-de: ADR-0004 (sync mobile offline-first), ADR-0023 (OS com Atividades)
---

# ADR-0027 — Sync mobile com merge por atividade

## Contexto

ADR-0004 (sync mobile offline-first, proposta desde 2026-05-17) cobre OS atômica — todo dispositivo manda `client_event_id` + `client_timestamp` por OS, resolução por entidade (last-write-wins ou outro algoritmo a definir).

ADR-0023 (aceita 2026-05-23) introduziu `AtividadeDaOS` — N atividades editáveis independentemente. Cenário: técnico A conclui atividade 1 (manutenção) offline; técnico B conclui atividade 2 (calibração) offline da MESMA OS; ambos sincronizam após reconexão. Sem merge por atividade, há corrida no estado de `os.status` (computado a partir das atividades — INV-OS-ATIV-001).

Auditoria 10 lentes (tech-lead-saas-regulado — TEMA-F.4 + auditor-seguranca TEMA-C.7) marcou como ALTO antes de Marco 3 começar.

## Decisão

**Sync mobile reorienta granularidade pra ATIVIDADE, não pra OS.**

### 1. Idempotência por evento mobile

Cada operação mobile (iniciar/concluir/marcar-NC/cancelar atividade) carrega:

- `client_event_id` (UUID gerado no device — anti-replay).
- `client_timestamp` (UTC do device — anti-cronologia conflitante).
- `Idempotency-Key` header (no POST).

Servidor persiste em `idempotency_keys` (entidade horizontal F-A) por 7 dias. Replay retorna primeira resposta (IDEMP-001).

### 2. Merge por atividade (não por OS)

- Conflito entre 2 dispositivos só pode acontecer EM ATIVIDADES DIFERENTES da mesma OS (mesmo executor não conclui mesma atividade 2x — INV-OS-ATIV-005 + auth).
- **Last-write-wins por `atividade_id`** (não por OS): se atividade 1 chegou às 10h e atividade 2 chegou às 11h, ambas aplicadas independentemente.
- `os.estado` é COMPUTADO server-side após cada atividade migrar (INV-OS-ATIV-001) — sem corrida.

### 3. Backlog visível

- Métrica `backlog_mobile` (gauge — `os/metricas.md` cravado 2026-05-23): atividades concluídas offline pendentes de sync por device.
- Alerta P2 se device > 20 atividades em backlog há > 4h.
- App mobile mostra ao técnico "8 atividades aguardando sync — verifique conexão".

### 4. Resolução de conflito de atribuição

- Cenário: gerente reatribui atividade enquanto técnico A está offline executando.
- Servidor é fonte da verdade — server-side aceita ou rejeita `iniciarAtividade` baseado em `atividade.tecnico_executor_id` ATUAL (não no momento da reatribuição offline).
- Se rejeita (403 NaoEExecutor) — app exibe ao técnico: "Esta atividade foi reatribuída ao colega Y. Sincronize sua sessão."

### 5. Telemetria mobile com tenant_id

- Toda métrica mobile carrega `tenant_id` como dimensão (OBS-002).
- Telemetria expirada em 13 meses (anonimização — matriz retenção).

## Caminhos alternativos considerados

| Alternativa | Por que NÃO |
|---|---|
| Last-write-wins por OS toda | Atividade 2 atrasada sobrescreve atividade 1 concluída — perda de dado |
| Pessimist lock (atividade trava ao iniciar) | Mobile offline não consegue checar lock → bloqueio impossível |
| Operational Transform (OT) tipo Google Docs | Overkill pra granularidade de atividade; complexidade desproporcional |
| Sem sync (sempre online) | ANTI-12 — contradiz US-OS-003 "100% offline" |

## Consequências

### Positivas

- Conflitos isolados por atividade — sem corrida em `os.estado`.
- Idempotência cravada (IDEMP-001) — replay não duplica.
- Telemetria de backlog visível (OBS-002).
- App mobile guia técnico em caso de reatribuição.

### Negativas (mitigáveis)

- Custo de implementação: ~2-3 semanas Wave A Marco 3 + app-tecnico.
- Telemetria de backlog exige endpoint `/heartbeat` adicional.

## Non-goals

- NÃO permite edição concorrente da MESMA atividade (cada atividade tem único executor — INV-OS-ATIV-005).
- NÃO substitui ADR-0004 — atualiza-a (ADR-0004 vira "sync mobile offline-first; merge por atividade conforme ADR-0027").

## Invariantes novas

- **INV-OS-SYNC-001:** toda operação mobile POST carrega `Idempotency-Key` + `client_event_id`; servidor persiste 7 dias.
- **INV-OS-SYNC-002:** merge server-side é por `atividade_id` (LWW por timestamp), nunca por `os_id`.
- **INV-OS-SYNC-003:** `os.estado` é computado, não setado direto (já cravado em INV-OS-ATIV-001).

## Implicações pro faseamento

- Marco 3 implementa idempotency + merge por atividade.
- Wave A app-tecnico implementa backlog visível + UI de reatribuição.
- Telemetria de backlog roda na Foundation F-C (Grafana plugado).

## Status

Proposta — aguarda aceite Roldão antes de Marco 3 começar P4 codificação. Atualiza ADR-0004 (proposta também) — ambas devem ser aceitas conjuntamente.
