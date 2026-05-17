# Orçamento de contexto (tokens) dos agentes

> Janela de contexto do LLM é finita (típico: 200k tokens). Doc grande consumido sem critério = agente "burro" porque sobra pouco pra raciocinar. Este arquivo define o teto por arquivo e a regra de carregamento sob demanda.

---

## Tetos por arquivo (enforced por hook)

| Arquivo | Teto (tokens) | Equivalente aprox. (linhas) | Hook |
|---|---|---|---|
| `CLAUDE.md` | 5.000 | ~150 | `context-budget` (a criar) |
| `AGENTS.md` | 8.000 | ~250 | `context-budget` (a criar) |
| `REGRAS-INEGOCIAVEIS.md` | 4.000 | ~120 | `context-budget` (a criar) |
| `.agent/CURRENT.md` | 500 | ~10 | `context-budget` (a criar) |
| `.specify/memory/constitution.md` | 3.000 | ~100 | `context-budget` (a criar) |
| Outros docs sem teto rígido | — | — | mas se >500 linhas, considerar quebrar |

**Importante:** hook **tokeniza** (usa biblioteca real, ex: `tiktoken` ou `@anthropic-ai/tokenizer`); NÃO conta linhas. 1 linha YAML densa pode ter 200 tokens; 1 linha de prosa solta tem ~15.

---

## Regra de carregamento sob demanda

`docs/INDEX.yaml` mapeia cada arquivo com `carrega_quando`:
- `sempre` — entra no contexto inicial de toda sessão
- `discovery` — carrega só quando fase atual = discovery
- `mvp1` — carrega quando agente trabalha em código do MVP-1
- `modulo:<nome>` — carrega só quando agente trabalha NESSE módulo
- `sob-demanda` — carrega só se agente pedir explicitamente via `@path`

**Hook `session-start` (a criar):**
1. Lê `.agent/CURRENT.md` (fase, módulo em foco).
2. Lê `INDEX.yaml`, filtra entradas com `carrega_quando` compatível.
3. Soma tokens estimados → se passar 50% da janela, ALERTA e exige Roldão escolher.
4. Injeta seleção via `@path` no contexto.

---

## Orçamento de contexto por auditor (Família 5)

Cada um dos 3 auditores-agentes consome contexto separado quando roda. Set MÍNIMO por auditor:

| Auditor | Lê | Não lê |
|---|---|---|
| **Segurança** | `REGRAS-INEGOCIAVEIS.md` (filtrado SEC-*, INV-TENANT-*) + `docs/seguranca/` + spec atual + código diff | Resto |
| **Qualidade** | `REGRAS-INEGOCIAVEIS.md` (filtrado TST-*) + `tests/` + spec atual + código diff | Resto |
| **Produto** | `docs/dominios/<mod>/prd.md` (módulo em foco) + `docs/comum/glossario.md` (relevante) + spec atual | Código, regras de segurança/teste |

**Sem essa limitação,** os 3 auditores rodando em cada PR consomem 3× a janela do implementador. Drift garantido.

---

## Como saber se está esgotando contexto

Sinais (a serem monitorados via `metricas-operacao-agentes.md` quando existir):
- Agente faz pergunta cuja resposta está em arquivo carregado.
- Agente contradiz decisão registrada em ADR.
- Agente "esquece" regra mestre 1 ou 2 (constituição).
- Resposta superficial demais pra tarefa complexa.

Se aparecer, **rever INDEX.yaml** — provavelmente carregando demais ou de menos.

---

## Manutenção

- Toda mudança de teto → atualizar este arquivo + constituição (se afetar regra mestre).
- Doc novo → adicionar entrada no `INDEX.yaml` com tokens estimados.
- Hook `context-budget` deve ser criado na Rodada 4 (Trava de segurança).
