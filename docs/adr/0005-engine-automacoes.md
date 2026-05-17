# ADR-0005 — Engine de automações, workflow longo e alertas

> **Status:** proposta v2 (2026-05-17 madrugada — revisão pós-auditoria 10 agentes pós-48-módulos). Substitui o stub anterior "0005-reservado".
> **Bloqueia:** OP10 Agenda (alertas), OP1 Recalibração proativa (Wave B), OP12 Painel do Dono, módulo `suporte-plataforma/automacoes-bpm`.
> **Depende de:** ADR-0001 (stack — Python + Celery + Redis + procrastinate como fallback), ADR-0007 (camada domínio + outbox).
> **Origem v2:** Auditor 4 (Celery vs procrastinate, workflows longos) + Auditor 10 (porta `BpmEngineProvider` faltante) da auditoria pós-48-módulos. v1 deixou ambíguo qual motor de fila usar; v2 crava decisão explícita + critério de migração futura.

---

## Contexto

BIG-11 ("CRM 360° + Automações") promete "automações sem programador" — usuário do tenant cria regra `gatilho → condição → ação` via UI. Exemplos:
- "Quando certificado vence em 30 dias → enviar WhatsApp + criar oportunidade"
- "Quando estoque mínimo de peça X → criar pedido de cotação"
- "Quando OS atrasa > 2h → notificar gerente"

Sem engine formal, agente IA constrói regra em código fixo, virando código ao invés de configuração.

---

## Decisão

**3 camadas distintas, cada uma com motor próprio:**

| Camada | O que executa | Motor escolhido | Quando trocar |
|---|---|---|---|
| **1. Tarefas em segundo plano curtas (<5 min)** | Email, render PDF, sync mobile, OCR, NFS-e, retry simples | **Celery + Redis** (primário) | Nunca — é o padrão indústria pra esse caso |
| **2. Workflows longos com estado (horas a dias)** | OS state machine, dunning de cobrança, recalibração proativa, BPM (módulo `automacoes-bpm`) | **Django state machine + Celery + outbox pattern** | Quando workflows com >10 etapas + esperas humanas >48h virarem comuns → migrar pra **Temporal/Camunda** (porta `BpmEngineProvider` permite swap) |
| **3. Engine de regras (automação sem programador)** | Tenant cria regra `gatilho → condição → ação` via UI; catálogo fechado | **Engine caseiro Python + DSL YAML** rodando sobre Celery (ou procrastinate em fallback) | Quando catálogo passar de 50 ações OU tenant pedir 5+/sem feature fora do catálogo |

### Por que Celery (não procrastinate) como primário

A auditoria às cegas teve divergência: 5 de 6 auditores votaram Celery + Redis; 1 (BI) defendeu procrastinate. Decisão final crava Celery por 4 razões objetivas:

1. **Pool de exemplos pros agentes IA é ~10x maior em Celery** (~50k repos públicos vs ~500 do procrastinate). Agente IA escreve task Celery sem tropeçar.
2. **Maturidade operacional** — Celery tem 12+ anos de produção, retries+priorities+rate limits+monitoring testados em escala.
3. **Topologia clara** — workers especializados (default, PDF, sync-mobile) sem misturar carga; procrastinate roda tudo num pool único.
4. **Wrapper `run_in_tenant_context`** (ADR-0002) já foi especificado pra Celery + tem lint custom semgrep funcional.

**Procrastinate fica como fallback documentado** (porta `QueueProvider` no anti-corrosion-layer.md #7). Se Redis virar problema (custo, complexidade, ataque), troca em 1 sprint sem mudar domínio.

### Por que NÃO Temporal/Camunda no MVP-1 (mas SIM como porta)

- **Custo:** Temporal Cloud ~R$ 1-5k/mês; Camunda Cloud ~R$ 800-2k/mês — fora do orçamento ano 1
- **Complexidade operacional:** Temporal exige Cassandra ou MySQL/Postgres com schemas dedicados; Camunda exige JVM + DB próprio
- **Workflows do MVP-1 cabem em Django state machine + Celery:**
  - OS state machine (INV-027): RASCUNHO → AGENDADA → EM_EXECUCAO → CONCLUIDA → FATURADA → PAGA — 6 estados, transições determinísticas, sem espera >24h em produção
  - Dunning billing (US-BIL-002/003): retry 1d/3d/7d — Celery Beat + persistir estado em `BillingDunningState` Django model
  - Recalibração proativa (Wave B): job Celery agendado 30 dias antes do vencimento — não precisa orquestrador
  - BPM (`automacoes-bpm`): engine caseiro sobre procrastinate (camada 3 abaixo) com catálogo fechado

**Critério explícito de migração pra Temporal/Camunda (porta `BpmEngineProvider` ativa fallback):**
- ≥ 5 workflows distintos com mais de 10 etapas
- ≥ 3 workflows que esperam evento humano por mais de 48h
- Falha de orquestração causando SEV-1 mais de 2× por mês
- Cliente farma TOP exigir engine BPM certificada (21 CFR Part 11)

Antes desses gates, Django state machine + outbox + Celery cobre.

### Camada 3 detalhe — Engine caseiro sobre Celery (não procrastinate)

> **Mudança v2:** v1 dizia "Engine caseiro sobre **procrastinate**". v2 troca pra **Celery** pelos motivos acima. Procrastinate continua como fallback documentado, não primário.

**Engine de regras (catálogo fechado) + DSL declarativa em YAML/JSON** rodando sobre Celery + Redis, NÃO ferramenta externa (Temporal/Inngest/n8n).

### Arquitetura (Camada 3 — Engine de regras)

```
[evento de domínio] → outbox → Celery worker (fila "automacoes")
                                     ↓
                          [engine de regras]
                                     ↓
                     [avalia condição YAML/JSON contra catálogo fechado]
                                     ↓
                          [executa ação do catálogo fechado]
                                     ↓
                          [audit trail síncrono]
```

### Arquitetura (Camada 2 — Workflow longo com estado)

```
[evento de início] → use case Django → 
                            ↓
              [BpmEngineProvider.execute_workflow()]   (porta ADR-0012 + ACL #13)
                            ↓
              ┌─────────────────────────────────────┐
              │ ProcrastinateBpmEngine (MVP-1):     │
              │  - cria Django model State          │
              │  - schedula passos via Celery Beat  │
              │  - outbox grava transições          │
              │  - state machine valida transição   │
              └─────────────────────────────────────┘
                            ↓
              [audit trail por transição (INV-027, INV-040, etc)]

# Quando gates dispararem (≥5 workflows >10 etapas + >48h espera humana):
              ┌─────────────────────────────────────┐
              │ TemporalProvider (Wave C+):         │
              │  - mesma porta BpmEngineProvider    │
              │  - Temporal workflows substituem    │
              │    Django state machine             │
              │  - domínio NÃO muda                 │
              └─────────────────────────────────────┘
```

### Componentes

1. **Catálogo de eventos (`docs/comum/integracoes-inter-modulos.md`):** lista versionada de eventos disponíveis (`OSConcluida`, `CertificadoEmitido`, `BoletoGerado`, etc.)
2. **Catálogo de condições:** funções pré-aprovadas (sem código arbitrário do tenant):
   - `comparar(campo, operador, valor)` — `valor > 100`, `status = "EMITIDO"`, etc.
   - `intervalo_tempo(campo, "30d", "antes")` — vencimento próximo
   - `contagem(entidade, filtro) >= N` — "≥ 5 OS atrasadas"
3. **Catálogo de ações:** funções pré-aprovadas:
   - `enviar_whatsapp(template, destinatário)`
   - `enviar_email(template, destinatário)`
   - `criar_os(template, cliente)`
   - `notificar_painel(severidade, mensagem)`
   - `escalar_para(papel)`
4. **DSL YAML versionada por tenant:**
   ```yaml
   nome: "Lembrete recalibração 30d"
   evento: CertificadoEmitido
   condicao:
     - intervalo_tempo: { campo: validade, antes: "30d" }
   acao:
     - enviar_whatsapp: { template: lembrete-recal-30d, destinatário: cliente.telefone }
   ativa: true
   ```
5. **Sandbox de teste:** tenant testa regra com dados sintéticos antes de ativar em produção (JTBD-087)

### Por que caseiro sobre Celery + NÃO Temporal/Inngest NO MVP-1 (mas porta pronta)

| Critério | Caseiro sobre Celery (MVP-1) | Temporal/Camunda (Wave C+ se necessário) |
|---|---|---|
| Custo | R$ 0 (Celery + Redis já na stack) | R$ 1k-5k/mês (Temporal Cloud) ou R$ 800/mês self-host |
| Lock-in | Nenhum (engine em Python no repo Aferê) | Forte (Temporal SDK + schemas) |
| LGPD/dado regulado | Tudo dentro do Aferê | Dado vaza pra terceiro (Temporal Cloud é multi-tenant SaaS) |
| Custo de troca futuro | Baixo (porta `BpmEngineProvider` anti-corrosion) | Alto (mas porta protege) |
| Maturidade pra workflow do MVP-1 | Suficiente — Django state machine + outbox + Celery cobre OS/dunning/recalibração | Over-engineering pra MVP |
| Maturidade pra workflow Wave C+ (>10 etapas, >48h espera) | Fica frágil (Beat + cron + custom state) | Excelente (workflows duráveis nativos) |
| ANTI-11 (sem customização infinita) | Catálogo fechado de cond/ações garante | Engine genérico abre brecha |
| Pool agente IA | Celery TOP 5 corpus público | Temporal corpus crescente mas menor |

### Catálogo fechado é defesa contra ANTI-11

Roldão decidiu (`prd.md` non-goal): **sem customização por tenant**. Engine não permite código arbitrário do tenant — só **combinações de funções pré-aprovadas**. Tenant que quer ação fora do catálogo abre solicitação; Aferê adiciona ação ao catálogo (governança).

---

## Alternativas consideradas

| Alternativa | Por que rejeitada (mas pode entrar via porta `BpmEngineProvider`) |
|---|---|
| **Temporal.io** no MVP-1 | Over-engineering; custo + complexidade. Reconsiderar quando gates explícitos dispararem (≥5 workflows >10 etapas + >48h espera humana). |
| **Camunda** no MVP-1 | JVM + DB dedicado pesa demais; pool agente IA menor. Reconsiderar se cliente farma TOP exigir engine certificada. |
| **Inngest** | SaaS externo; LGPD compromete (dado pessoal sai do BR sem DPA aprovado). |
| **n8n / Make** | UX boa mas catálogo aberto ao mundo (brecha ANTI-11). |
| **procrastinate como primário** (em vez de Celery) | Pool agente IA menor (~10x); maturidade operacional menor; topologia única vs Celery com workers especializados. Procrastinate fica fallback no anti-corrosion-layer. |
| **Apenas Celery puro (sem state machine Django + outbox)** | Workflows com retry exponencial + esperas humanas viram código frágil; Celery Beat sozinho não dá conta de dunning/BPM. |
| **Código fixo em Python pra cada regra** | Cada regra é deploy; quebra "sem programador". |
| **DSL com Python `eval`** | Brecha de segurança absurda (SEC-003 input untrusted). |

---

## Limites legítimos

- Tenant **não escreve código** — só usa catálogo fechado
- Aferê **versiona o catálogo** — mudança de catálogo é release com semver
- Auditor de Segurança **revisa cada item adicionado** ao catálogo (pre-merge)
- **Logs de execução** de cada regra em audit trail (`metricas-operacao-agentes.md` cobre lado IA)

---

## Consequências

### Positivas
- "Automação sem programador" entregue sem brecha de segurança
- Catálogo fechado é defesa contra ANTI-11
- Custo $0 incremental
- Tudo dentro do Aferê (LGPD + WORM)

### Negativas
- Tenant pode pedir ação fora do catálogo → backlog Aferê
- Engine caseiro precisa de manutenção (testes, retry, monitoramento)
- Catálogo cresce com o tempo → governança de catálogo precisa

### Riscos
- Regras mal escritas geram spam de WhatsApp → mitigação: rate limit por tenant + opt-out forte
- Loop infinito (regra A dispara regra B que dispara regra A) → mitigação: detecção de ciclo no engine + timeout

---

## Critério de mortalidade (gates explícitos pra trocar de motor)

### Camada 1 (Celery + Redis) — quase nunca troca
- Redis virar gargalo de memória (improvável <1k tenants) → migrar pra Redis cluster
- Custo Redis > R$ 500/mês → considerar procrastinate (fallback documentado, sem Redis)

### Camada 2 (Django state machine + Celery + outbox) — troca pra Temporal/Camunda quando:
- ≥ 5 workflows distintos com mais de 10 etapas em produção
- ≥ 3 workflows que esperam evento humano por mais de 48h
- Falha de orquestração causando SEV-1 mais de 2× por mês
- Cliente farma TOP exigir engine BPM certificada (21 CFR Part 11)
- **Porta `BpmEngineProvider` (anti-corrosion layer #13) permite swap sem reescrever domínio.**

### Camada 3 (Engine de regras caseiro) — troca quando:
- Catálogo cresce pra > 50 ações sem padronização → revisar arquitetura
- Tenants pedem >5x/semana ação fora do catálogo → considerar DSL mais aberta (com sandboxing)
- Engine fica gargalo de performance → considerar mover regras pra Temporal workflows

---

## Implementação (esqueleto)

### Camada 1 — Celery workers (Foundation F-A)
```
infrastructure/queue/
├── celery_app.py              # Celery + Redis broker
├── workers/
│   ├── default.py             # email, NFS-e, OCR
│   ├── pdf.py                 # CPU-bound: render PDF + PAdES-LTV
│   ├── sync_mobile.py         # offline sync com prioridade
│   └── automacoes.py          # camada 3 — engine de regras
└── tenant_context.py          # run_in_tenant_context wrapper
```

### Camada 2 — Workflow longo (Wave A + Wave B)
```
infrastructure/bpm/
├── provider.py                # BpmEngineProvider Protocol
├── procrastinate_engine.py    # ProcrastinateBpmEngine (MVP-1)
├── temporal_engine.py         # TemporalProvider (stub Wave C+)
└── django_state_machine.py    # mixin pros models terem state machine validada

domain/
├── operacao/os/state.py       # OS state machine (INV-027)
├── financeiro/billing/dunning_state.py
└── metrologia/certificados/state.py
```

### Camada 3 — Engine de regras (Wave B — módulo `automacoes-bpm`)
```
apps/automacoes/
├── models.py                  # Regra(tenant, nome, evento, condicao_yaml, acao_yaml, ativa)
├── catalogo_condicoes.py      # funções aprovadas
├── catalogo_acoes.py          # funções aprovadas
├── engine.py                  # avalia + executa via Celery
├── sandbox.py                 # testa com dados sintéticos
└── tasks.py                   # Celery tasks de execução
```

---

## Referências

- ADR-0001 (stack), ADR-0007 (camada domínio)
- `docs/comum/integracoes-inter-modulos.md` (catálogo de eventos)
- `docs/discovery/jobs-to-be-done.md` BIG-10, BIG-11
- `docs/seguranca/agente-input-nao-confiavel.md` (SEC-003)
- `prd.md` §5 (non-goals — ANTI-11)
- `REGRAS-INEGOCIAVEIS.md` INV-AGENT-001
