# ADR 0002 — Estratégia de sync offline-first

- **Status:** aceito
- **Data:** 2026-04-19
- **Aprovado em:** 2026-04-19 pelo usuário (product owner)
- **Autor:** bootstrap (Claude Code)
- **Revisores:** `android` + `backend-api` + `metrology-auditor` + `product-governance` (revisão formal pós-MVP, quando agentes estiverem operacionais)
- **Relacionado:** `harness/08-sync-simulator.md`, P1-1 em `harness/STATUS.md`, `adr/0001-backend-framework.md`

## Contexto

`apps/android` coleta dados em campo sem conectividade (PRD §6.4, §7.7). Ao voltar online, precisa sincronizar com `apps/api` mantendo: (1) idempotência (reenvio seguro), (2) rastreabilidade completa, (3) **nunca** resolução automática de conflito regulatório — em ISO 17025, conflito de dados de calibração exige revisão humana documentada.

`harness/08-sync-simulator.md` define 8 classes de conflito (C1-C8) e exige fila de revisão humana determinística.

## Opções consideradas

| Opção | Prós | Contras |
|-------|------|---------|
| **Event log server-driven + idempotency keys + fila humana** | Determinístico, totalmente auditável, alinha com audit log imutável, simples de testar com `evals/sync-simulator/` | Cliente envia eventos em vez de estado — exige modelagem cuidadosa de eventos |
| CRDTs (Yjs, Automerge) | Resolve conflito automaticamente | Perde trilha humana em conflitos regulatórios (inaceitável em 17025), mais complexidade, library em JS/Kotlin com footprint alto no Android |
| Last-Write-Wins ingênuo | Simples | Perde dados silenciosamente — inaceitável regulatoriamente (C2/C3 viram bug) |
| Sync bidirecional com merge (Git-like) | Flexível | Complexidade alta, difícil provar auditabilidade |

## Decisão

Adotar **Event log server-driven com idempotency keys + fila de revisão humana para conflitos regulatórios**.

### Protocolo concreto

1. **Cliente Android** mantém log local em SQLCipher: cada ação em campo gera um evento `{uuid, org_id, user_id, device_id, ts_local, kind, payload, local_prev_hash}` append-only.
2. **Envio** usa idempotency key = `uuid` do evento. Reenvio é seguro (servidor deduplica).
3. **Servidor** (`apps/api`) valida evento:
   - RBAC + tenant match.
   - Invariantes de domínio (regras de `packages/normative-rules`).
   - Ordem: `ts_local` não pode ser menor que `ts_local` do último evento aceito do mesmo `device_id` (detecta clock skew).
4. **Se válido** → grava em `audit_log` (hash-chain append-only) + aplica efeito no estado canônico.
5. **Se conflita** (uma das 8 classes C1-C8):
   - Não resolve automaticamente.
   - Grava em `sync_conflicts` com contexto completo + classe + fingerprint.
   - Expõe em fila de revisão humana (`apps/web`, role de supervisor).
   - Notifica cliente via push: "pendente de revisão manual".
6. **Resolução humana** vira novo evento server-side com justificativa escrita → audit log.

### Stack

- Cliente: **Kotlin + SQLCipher + OkHttp + Protobuf** (serialização de evento).
- Servidor: **Fastify + Postgres** (tabela `outbox_events` + `audit_log` + `sync_conflicts`).
- Fila interna: **pg-boss** (Postgres-based queue — evita Redis só para isso; Redis fica para cache/BullMQ de outras filas).

### Cenários C1-C8 (de `harness/08-sync-simulator.md`)

Simulador determinístico em `evals/sync-simulator/` gera cada cenário, executa protocolo e verifica:
- Evento aceito termina em `audit_log` com hash-chain válida.
- Evento conflituoso termina em `sync_conflicts` + fila humana, nunca resolvido automaticamente.
- Reenvio do mesmo `uuid` é idempotente.

## Consequências

**Positivas:**
- Determinismo + auditabilidade totais (cada decisão sync tem trilha).
- Alinha com cascata L4/L5 em `harness/14-verification-cascade.md`.
- Sem lib de CRDT = footprint Android menor + menos superfície de ataque.

**Negativas / mitigadas:**
- Conflitos geram trabalho humano — aceito, é o comportamento desejado em 17025.
- Cliente precisa modelar eventos (não apenas "salvar estado") — disciplina de design na V1.

**Consequências regulatórias:**
- Cada conflito resolvido produz evidência em `compliance/validation-dossier/evidence/` — requerido por auditoria.
- Fila humana vira requisito funcional da web (back-office) — adicionar à spec da V1.

## Como validar

- `evals/sync-simulator/` implementa C1-C8 com 500 seeds por classe (property test, conforme `harness/15-redundancy-and-loops.md`).
- Critério de pass: 100% dos conflitos determinísticos terminam na fila humana; 100% dos eventos válidos entram no audit log com hash-chain íntegra.
- Fail-gate antes de V2 (sync robusto): bloqueia release se qualquer seed falhar.

## Revisão

- Re-revisar esta decisão se aparecer caso de uso onde conflito pode ser automatizado com segurança (unlikely em 17025; possible em metadados não-metrológicos).
- `metrology-auditor` aprova ou veta com base em "resolução automática de conflito regulatório = inaceitável".
