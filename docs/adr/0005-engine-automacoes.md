# ADR-0005 — Engine de automações e alertas

> **Status:** proposta (2026-05-17 noite final). Substitui o stub anterior "0005-reservado".
> **Bloqueia:** OP10 Agenda (alertas), OP1 Recalibração proativa (Wave B), OP12 Painel do Dono.
> **Depende de:** ADR-0001 (stack — Python + procrastinate), ADR-0007 (camada domínio + outbox).

---

## Contexto

BIG-11 ("CRM 360° + Automações") promete "automações sem programador" — usuário do tenant cria regra `gatilho → condição → ação` via UI. Exemplos:
- "Quando certificado vence em 30 dias → enviar WhatsApp + criar oportunidade"
- "Quando estoque mínimo de peça X → criar pedido de cotação"
- "Quando OS atrasa > 2h → notificar gerente"

Sem engine formal, agente IA constrói regra em código fixo, virando código ao invés de configuração.

---

## Decisão

**Engine caseiro sobre procrastinate + DSL declarativa em YAML/JSON**, NÃO ferramenta externa (Temporal/Inngest/n8n).

### Arquitetura

```
[evento de domínio] → outbox → procrastinate worker
                                     ↓
                          [engine de regras]
                                     ↓
                     [avalia condição YAML/JSON]
                                     ↓
                          [executa ação]
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

### Por que caseiro + não usar Temporal/Inngest

| Critério | Caseiro sobre procrastinate | Temporal/Inngest |
|---|---|---|
| Custo | $0 (já tem procrastinate na stack) | R$ 1k-5k/mês ou self-host caro |
| Lock-in | Nenhum | Forte |
| LGPD/dado regulado | Tudo no banco do Aferê | Dado vaza pra terceiro |
| Custo de troca | Baixo (porta anti-corrosion) | Alto |
| Maturidade pra caso simples | Suficiente | Over-engineering |
| ANTI-11 (sem customização infinita) | Catálogo fechado de cond/ações garante | Engine genérico abre brecha |

### Catálogo fechado é defesa contra ANTI-11

Roldão decidiu (`prd.md` non-goal): **sem customização por tenant**. Engine não permite código arbitrário do tenant — só **combinações de funções pré-aprovadas**. Tenant que quer ação fora do catálogo abre solicitação; Aferê adiciona ação ao catálogo (governança).

---

## Alternativas consideradas

| Alternativa | Por que rejeitada |
|---|---|
| **Temporal.io** | Over-engineering; custo + complexidade |
| **Inngest** | SaaS externo; LGPD compromete |
| **n8n / Make** | UX boa mas open ao mundo (abre brecha ANTI-11) |
| **Código fixo em Python** | Cada regra é deploy; quebra "sem programador" |
| **DSL com Python eval** | Brecha de segurança absurda (SEC-003 input untrusted) |

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

## Critério de mortalidade

Se em produção real:
- Catálogo cresce pra > 50 ações sem padronização → revisar arquitetura
- Tenants pedem >5x/semana ação fora do catálogo → considerar DSL mais aberta (com sandboxing)
- Engine fica gargalo de performance → considerar Temporal

---

## Implementação (esqueleto, quando Wave B começar)

```
apps/automacoes/
├── models.py              # Regra(tenant, nome, evento, condicao_yaml, acao_yaml, ativa)
├── catalogo_condicoes.py  # funções aprovadas
├── catalogo_acoes.py      # funções aprovadas
├── engine.py              # avalia + executa
├── sandbox.py             # testa com dados sintéticos
└── tasks.py               # procrastinate workers
```

---

## Referências

- ADR-0001 (stack), ADR-0007 (camada domínio)
- `docs/comum/integracoes-inter-modulos.md` (catálogo de eventos)
- `docs/discovery/jobs-to-be-done.md` BIG-10, BIG-11
- `docs/seguranca/agente-input-nao-confiavel.md` (SEC-003)
- `prd.md` §5 (non-goals — ANTI-11)
- `REGRAS-INEGOCIAVEIS.md` INV-AGENT-001
