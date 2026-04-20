# 08 — Simulador determinístico de sync/conflito offline

> **P1-1**: substitui a "suite volumétrica de 10k eventos" por teste de propriedades com seeds canônicos.

## Racional

O PRD §7.7 e §10 exigem:
- Event sourcing por OS (Ordem de Serviço).
- Idempotência por `(device_id, client_event_id)`.
- *Optimistic locking* por agregado.
- Lock exclusivo por OS no momento da assinatura.
- Matriz formal de conflitos.

Sem simulador determinístico, bugs de concorrência só aparecem em produção.

## Estrutura

```
evals/sync-simulator/
├─ engine/                       # motor determinístico, seed fixo
│  ├─ clock.ts                   # relógio lógico (Lamport timestamps)
│  ├─ network.ts                 # modelo de perda/reordenação/partição
│  ├─ device.ts                  # estado local do Android simulado
│  └─ server.ts                  # reconciliação server-side
├─ scenarios/
│  ├─ 01-two-devices-same-os.yaml
│  ├─ 02-signature-during-edit.yaml
│  ├─ 03-reemission-vs-new.yaml
│  ├─ 04-network-partition-heal.yaml
│  └─ ...
├─ properties/
│  ├─ convergence.ts             # todos os dispositivos chegam ao mesmo estado final
│  ├─ hash-chain-integrity.ts    # audit log não diverge
│  ├─ signature-lock.ts          # assinatura é mutuamente exclusiva
│  └─ idempotency.ts             # replay de evento não muda estado
├─ seeds/
│  ├─ canonical/                 # seeds fixos, sempre rodados em CI
│  └─ weekly/                    # seeds aleatórios regenerados semanalmente
└─ reports/                      # traces de falha arquivados
```

## Matriz de conflitos (obrigatória)

| # | Cenário | Resultado esperado |
|---|---------|-------------------|
| C1 | Mesma OS editada em 2 dispositivos offline, sync simultâneo | Last-write-wins por agregado + evento de conflito em fila de revisão |
| C2 | Dispositivo A assina OS, Dispositivo B tenta editar após lock | B recebe erro `OS_LOCKED_FOR_SIGNATURE`, evento rejeitado |
| C3 | Dispositivo A assina OS, Dispositivo B tenta assinar em paralelo | Apenas um sucesso; outro recebe erro determinístico |
| C4 | Reemissão criada em A enquanto B tenta nova emissão | Reemissão preserva hash-chain; nova emissão bloqueada se OS já finalizada |
| C5 | Partição de rede: 3 dispositivos editam, rede volta | Convergência em ordem determinística (Lamport + tiebreaker por device_id) |
| C6 | Replay de evento com `(device_id, client_event_id)` duplicado | Idempotente; nenhum efeito colateral |
| C7 | Evento chega fora de ordem | Buffer server-side reordena por Lamport antes de aplicar |
| C8 | Dispositivo com clock adulterado envia evento futuro | Server normaliza por seu próprio relógio; audit registra divergência |

## Propriedades verificadas (property-based testing)

Para cada scenario, as 4 propriedades são verificadas:

1. **Convergência** — após sync completo, todos os dispositivos têm o mesmo estado observável.
2. **Integridade da hash-chain** — audit log do servidor tem cadeia válida independente da ordem de chegada.
3. **Lock de assinatura** — nunca existem 2 assinaturas concorrentes para a mesma OS.
4. **Idempotência** — replay de qualquer subset de eventos produz o mesmo estado final.

## Execução

- **CI a cada PR** que toca `apps/api/src/domain/sync/**`, `apps/android/src/sync/**`, `packages/db/**`.
- **Seeds canônicos**: todos (100%) devem passar sempre.
- **Seeds weekly**: gerados por job agendado com seed da semana; falha = incident ticket automático com trace em `reports/`.

## Reprodutibilidade

Todo teste registra `seed` + `scenario` + `event trace`. Falha local reproduz com:

```
pnpm sync-sim --scenario 02 --seed 0xdeadbeef
```

## Integração com dossiê

Execução verde arquiva evidência em `compliance/validation-dossier/evidence/REQ-§7.7-SYNC/<timestamp>/`.

## Fila de revisão humana de conflitos

Quando o cenário C1 (e variações) produzem conflito que o sistema **não resolve automaticamente**, o evento vai para fila humana.

### Ownership
- **Dono da fila**: `backend-api` (implementa endpoints e UI de triagem no back-office).
- **Revisor humano**: papel "Responsável Técnico da OS" — definido por tenant no onboarding.
- **Escalação em 2º nível**: `regulator` se o conflito envolve interpretação normativa.

### SLA
| Estado | Prazo | Ação automática ao estourar |
|--------|-------|------------------------------|
| Conflito aberto → triagem inicial | 24h úteis | Notificação ao revisor + cópia ao gestor da organização |
| Triagem → resolução | 48h úteis | Escalação para `regulator`; OS marcada como "pendente de resolução regulatória" |
| Resolução → arquivamento | 24h úteis | Auto-arquivamento com log de decisão |

### Regras duras
- OS com conflito aberto **não emite certificado** (bloqueio por arquitetura, §9).
- Decisão humana é registrada em audit log com `resolver_id`, `timestamp`, `justificativa`, `evento_vencedor_id`.
- Decisões recorrentes (mesmo padrão > 3×) geram sugestão de regra automática para a próxima versão do pacote normativo.

### Evidência
Cada resolução arquiva trace em `compliance/validation-dossier/evidence/REQ-§7.7-CONFLICT-RESOLUTION/<os_id>/`.
