# ADR-0004 — Sincronização offline-first do app técnico

> **Status:** proposta (2026-05-17 noite final). Substitui o stub anterior "0004-reservado".
> **Bloqueia:** F-D (mobile shell) da Foundation; OP3.1 (app de campo) na Wave A.
> **Depende de:** ADR-0001 (stack — Flutter), ADR-0002 (multi-tenancy + tenant_id), ADR-0003 (mobile-tecnico-campo — stub).

---

## Contexto

App técnico do Aferê tem requisito **offline-first** (rede 3G ruim em campo, áreas sem sinal). Mobile mantém estado local em SQLite (drift) e **sincroniza com servidor** quando rede volta. Conflitos vão acontecer — sem regra formal, decisão de "qual versão ganha" fica caso a caso, criando bugs silenciosos.

**Lente:** sem ADR-0004, agente IA que constrói o módulo decide sozinho ("last-write-wins") e a regra fica embutida em código, não documentada. ISO 17025 cl. 7.11 (controle de dados) exige rastreabilidade — conflito de sync mal-resolvido vira NC.

---

## Decisão

Sincronização **outbox pattern + pull/push + regras de conflito por entidade**, com servidor como **fonte de verdade primária**.

### Estratégia geral

1. **Outbox local (mobile):** toda mudança no SQLite local insere linha em `outbox_events` (mesma transação local).
2. **Sync worker:** quando há rede, processa outbox em ordem (FIFO por entidade).
3. **Conflict detection:** servidor compara `version` (vector clock ou timestamp + hash) do registro recebido com versão atual.
4. **Conflict resolution:** **regra explícita por entidade** (tabela abaixo).
5. **Sync result:** mobile recebe ack ou conflito; UI mostra fila pendente / conflitos pra revisão humana.

### Regras de conflito por entidade

| Entidade | Estratégia | Razão |
|---|---|---|
| **OS** (Ordem de Serviço) | **Last-write-wins** + fila humana se diff grande (> 3 campos divergem) | Técnico atualiza no campo; servidor pode ter ajuste do gerente. Diff pequeno = aceita; diff grande = humano resolve |
| **Foto / anexo** | **Append-only** (nunca conflita) | Foto não é editada, é adicionada; conflito impossível por design |
| **Estoque (movimento)** | **Transação atômica no servidor** — mobile envia "consumi peça X qtd Y", servidor decide se aprova (saldo + reserva) | Mobile pode estar otimisticamente desatualizado; servidor sabe estoque real |
| **Caixa do técnico (despesa)** | **Append-only** + reconciliação pelo gerente | Despesa é fato registrado; valor não muda retroativo |
| **Cliente / Equipamento (cadastro)** | **Servidor primário** — mobile não edita campos críticos; cria sugestão de edição pra gerente aprovar | Cadastros são compartilhados entre técnicos; conflito frequente |
| **Certificado de calibração** | **Imutável após emissão** (INV-025) — mobile não edita | WORM no servidor protege |
| **Status OS** (transição máquina estados) | **Servidor valida transição** — mobile sugere; servidor aceita ou rejeita | INV-027 máquina estados não-reversível |
| **Assinatura cliente** | **Append-only com timestamp + nonce** servidor-controlled | Anti-replay (ADR-0009 A3 cliente-side) |
| **Comentário/observação em OS** | **Append-only** | Não conflita por design |
| **Apontamento de tempo** | **Append-only** (cada entrada é um fato) | Não conflita |

### Vector clock vs timestamp + hash

**Decisão:** **timestamp + hash do conteúdo** (mais simples; vector clock seria over-engineering pra N pequeno de dispositivos por tenant).

```
client_version = (timestamp_local_ms, sha256(payload))
server_version = (timestamp_servidor_ms, sha256(payload))
```

Servidor compara hash; se diferente, dispara estratégia da tabela acima.

### Idempotência

Cada mudança no outbox tem `client_event_id` UUID (gerado uma vez, reusado em retry). Servidor deduplica por `(tenant_id, client_event_id)` — replay seguro.

### Ordem de processamento

- **Por entidade:** ordem FIFO preservada (outbox processa em ordem de insert)
- **Cross-entity:** sem garantia; handler tolera out-of-order ou consulta estado atual

### Conexão & resiliência

- **Connection check:** mobile tenta sync a cada 30s quando há rede + na volta do app pra foreground
- **Backoff:** exponencial 1s → 60s em caso de falha (`cross-cutting/retry.md`)
- **Token JWT:** refresh automático em background; se expirou e sem rede, mobile usa cache local + sync atrasado

---

## Alternativas consideradas

| Alternativa | Por que rejeitada |
|---|---|
| **CRDT (Conflict-free Replicated Data Types)** | Over-engineering pro caso de uso; biblioteca Dart imatura |
| **Last-write-wins absoluto pra tudo** | Perde dado quando 2 técnicos editam mesma OS em paralelo |
| **Servidor manda tudo (mobile só lê)** | Quebra offline-first; técnico não pode operar sem rede |
| **Sync manual pelo técnico** | UX ruim; técnico esquece + dado perdido |
| **PowerSync / Replicache** (libs SaaS) | Custo extra; dependência adicional; queremos controle total da regra ISO 17025 |

---

## Consequências

### Positivas
- Conflitos têm regra clara, auditável
- INV-027 (máquina estados OS) reforçada pela estratégia "servidor valida transição"
- Audit log de cada decisão de conflito (rastreabilidade ISO 17025)
- Mobile resiliente a 4h+ sem rede

### Negativas
- Complexidade adicional no servidor (handler de conflito por entidade)
- UX de "conflito a resolver" precisa ser bem desenhada (gerente lê + decide)
- Drift entre mobile e servidor pode atingir minutos em rede ruim (aceito conscientemente)

### Riscos
- Bug em vector hash → falsa coincidência → dado perdido (mitigação: SHA-256, colisão astronomicamente improvável)
- Outbox cresce sem limpeza → app fica lento (mitigação: purge de outbox > 30 dias após ack)

---

## Critério de mortalidade (LEAP)

Se em produção real (após Wave A em Balanças Solution) acontecer:
- > 5% de conflitos não-resolvidos automaticamente em 30 dias
- > 1 incidente de perda de dado por conflito mal-resolvido
- > 3 NC de auditoria CGCRE relacionadas a sync (V2)

→ Reabrir esta ADR; considerar migração pra CRDT ou solução pronta.

---

## Implementação

A ser detalhada quando F-D mobile começar. Esqueleto:

```
infrastructure/sync/
├── outbox.dart                  # SQLite outbox local
├── sync_worker.dart             # processa fila quando há rede
├── conflict_resolver.dart       # despacha pra estratégia por entidade
└── strategies/
    ├── last_write_wins.dart
    ├── append_only.dart
    ├── server_authoritative.dart
    └── transactional_atomic.dart
```

Backend (Django + DRF):

```
apps/sync/
├── views/sync_endpoint.py       # POST /sync/push, GET /sync/pull
├── conflict_handler.py          # decide aceita / rejeita / sugere
└── audit.py                     # registra cada decisão em audit trail
```

---

## Referências

- ADR-0001 (stack), ADR-0002 (multi-tenancy), ADR-0003 (mobile stub)
- `docs/arquitetura/anti-corrosion-layer.md` (porta Sync — `infrastructure/sync/`)
- `docs/arquitetura/cross-cutting/{retry,timeout,idempotencia,transacao}.md`
- `REGRAS-INEGOCIAVEIS.md` INV-025 (equipamento imutável), INV-027 (OS máquina estados)
- ISO/IEC 17025:2017 cl. 7.11 (controle de dados e gestão da informação)
