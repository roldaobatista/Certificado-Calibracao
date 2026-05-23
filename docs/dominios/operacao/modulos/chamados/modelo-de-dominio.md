---
owner: Roldão
revisado-em: 2026-05-23
status: draft
modulo: chamados
dominio: operacao
---

# Modelo de domínio — Módulo Chamados

> Cliente e Equipamento vivem em `docs/comum/modelo-de-dominio.md`. Hook valida não-duplicação.

---

## Entidades

### Chamado — agregado raiz

- **Atributos obrigatórios:** `id`, `tenant_id`, `canal_origem` (enum: whatsapp | telefone | portal | email | presencial), `cliente_id`, `texto_inicial`, `estado` (enum: ABERTO | TRIADO | EM_ANDAMENTO | FECHADO | CANCELADO), `criado_at`, `criado_por`, `tempo_triagem_ms` (preenchido na triagem — A-CH-002).
- **Atributos opcionais:** `equipamento_id`, `tipo` (preenchido na triagem), `urgencia` (baixa | media | alta | critica), `sla_alvo_at`, `atribuido_a`, `os_id` (preenchido quando converte direto chamado→OS), `orcamento_id` (Wave B — quando vira orçamento antes de OS), `razao_fechamento`, `duplicado_de_id` (se humano marcou).
- **Invariantes:** RAT-08 (audit), LGPD RAT-03 (telefone do cliente é dado pessoal), regra de duplicação documental (não automática), **INV-CHM-RAST-001** (rastreabilidade chamado→orçamento→OS).

### ConfigEscalonamentoTenant (M-CH-002)

- Atributos: `tenant_id`, `papel_gerente_id` (perfil que recebe escalação 100%), `percentual_trigger` (default 100%; ajustável por tenant), `percentual_aviso` (default 75%).
- Sem essa config, default global aplica (75/100).

### MensagemDoChamado

- Histórico de interação (cliente↔atendente). Append-only.
- Atributos: `chamado_id`, `direcao` (entrada | saida), `canal`, `texto`, `at`, `autor_id`.

### EventoDoChamado (audit imutável)

- `chamado_id`, `evento_tipo`, `payload`, `at`, `ator_id`.

### SLAConfig (config por tenant)

- Tabela tenant × tipo × urgência → prazo (minutos para triagem, minutos para resolução).
- Mutável; mudança gera versão (snapshot no chamado preserva SLA original).

---

## Máquina de estados

```mermaid
stateDiagram-v2
    [*] --> ABERTO
    ABERTO --> TRIADO: atendente classifica (tipo + urgência) ≤ 30s
    ABERTO --> CANCELADO: cliente desistiu antes da triagem
    TRIADO --> EM_ANDAMENTO: atendente assume / responde
    TRIADO --> FECHADO: orientação resolveu, sem OS
    EM_ANDAMENTO --> FECHADO: resolveu sem OS OR convertido em OS (preserva os_id)
    EM_ANDAMENTO --> CANCELADO: cliente desistiu
    FECHADO --> [*]
    CANCELADO --> [*]
```

**Regras:**
- **Conversão (INV-CHM-RAST-001):** chamado pode virar **OR (a)** orçamento (Wave B — `orcamento_id` setado; `Orcamento.chamado_origem_id` preenchido) **OR (b)** OS direta (`os_id` setado; `OS.chamado_origem_id` preenchido, `OS.orcamento_origem_id IS NULL`). Os dois caminhos publicam evento distinto. Quando orçamento vira OS depois, `OS.orcamento_origem_id` é preenchido e a rastreabilidade tripla fica completa.
- **SLA herdado (M-CH-001):** OS gerada de chamado herda SLA contratual do chamado; SLAs não somam — vence o mais restritivo (chamado vs contrato cliente).
- FECHADO sem OS exige `razao_fechamento` ≠ null.
- CANCELADO exige razão.
- Transição reversa proibida.
- Audit em toda transição (RAT-08).

---

## Detecção de duplicados (regra crítica)

Função `detectar_duplicado(cliente_id, equipamento_id?, janela=7dias)`:
1. Busca chamados do mesmo cliente nos últimos 7 dias.
2. Se `equipamento_id` informado: filtra por mesmo equipamento.
3. Retorna lista ordenada por proximidade temporal.
4. **Nunca mescla sozinho.** UI mostra "Possível duplicado de #1234 (3 dias atrás). Confirma?" — humano decide.
5. Se humano confirma: novo chamado salvo com `duplicado_de_id`. Não apaga; apenas marca.

---

## Escalonamento de SLA

Job recorrente (1 min):
1. Pra cada chamado ≠ FECHADO/CANCELADO: calcula `% sla_consumido = (now - criado_at) / (sla_alvo_at - criado_at)`.
2. Se `% >= 75%` e não notificou ainda: envia notificação ao `atribuido_a`. Marca `notificado_75=true`.
3. Se `% >= 100%` e não escalou ainda: muda `atribuido_a` pro `gerente_operacional` (config do tenant) + notifica. Marca `escalado_100=true`. Não fecha automaticamente.

---

## Agregados

| Raiz | Inclui | Invariantes |
|---|---|---|
| Chamado | MensagemDoChamado, EventoDoChamado | RAT-08, RAT-03 |

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| EstadoChamado | enum | Sim |
| CanalOrigem | enum (5) | Sim |
| Urgencia | enum (baixa, media, alta, critica) | Sim |
| SLAAlvo | timestamp calculado na triagem; snapshot no chamado | Sim |

## Eventos publicados

| Evento | Quando | Payload | Consumidores |
|---|---|---|---|
| `ChamadoAberto` | ABERTO criado | `{tenant_id, chamado_id, cliente_id, canal}` | crm (timeline) |
| `ChamadoTriado` | TRIADO setado | `{chamado_id, tipo, urgencia, sla_alvo_at}` | observabilidade |
| `ChamadoConvertidoEmOS` | FECHADO + `os_id` setado | `{chamado_id, os_id}` | os (cria com origem) |
| `ChamadoFechado` | FECHADO | `{chamado_id, razao, os_id?}` | crm |
| `ChamadoSLAEscalado` | escalonamento 100% | `{chamado_id, novo_atribuido}` | observabilidade |

## Comandos

| Comando | Pré | Pós |
|---|---|---|
| `abrirChamado` | cliente válido | ABERTO + evento |
| `triagem` | ABERTO | TRIADO + SLA calculado |
| `marcarDuplicado` | humano confirma | `duplicado_de_id` setado |
| `converterEmOS` | TRIADO/EM_ANDAMENTO | FECHADO + cria OS RASCUNHO |
| `fechar` | razão não-vazia | FECHADO |
| `cancelar` | razão | CANCELADO |

## Schema físico

Tabelas: `chamado`, `chamado_mensagem`, `chamado_evento`, `sla_config`.

## Como evolui

Atributo novo → migration. Mudança em máquina estados → ADR.
