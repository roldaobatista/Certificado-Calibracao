# Roteamento dual — Claude Code + Codex CLI

> **Fronteira detalhada** entre as duas ferramentas de agente e os 3 auditores-agentes. Sem isso, comportamento divergente garantido em 2 semanas (Auditor 7 v2 alertou).

---

## Princípio: `AGENTS.md` é canônico; `CLAUDE.md` é adendo

```
AGENTS.md  ←──── canônico (lido por TODAS as ferramentas)
   ↑
   │ @import
   │
CLAUDE.md  ←──── adendo só de harness Claude Code (hooks, skills, comandos slash)
```

Resultado:
- **Codex CLI** lê só `AGENTS.md`.
- **Claude Code** lê `CLAUDE.md`, que puxa `@AGENTS.md` no topo.
- Comportamento IDÊNTICO em decisões de produto e arquitetura; pode divergir apenas em features específicas de harness.

**Hook de drift (a criar):** detecta se `CLAUDE.md` contém regra de produto que devia estar em `AGENTS.md` — alerta.

---

## Quem faz o quê

### Claude Code (esta ferramenta)
**Fortes em:**
- Conversa longa, interativa, com feedback rápido
- Tasks complexas com múltiplos passos
- Uso de hooks (.claude/hooks/), skills (.claude/skills/), comandos slash (.claude/commands/)
- Auto-memory entre sessões (`~/.claude/projects/.../MEMORY.md`)
- Integração com plugin VS Code / IDE

**Usar quando:**
- Tarefas que exigem várias rodadas de discussão
- Refatoração que toca múltiplos arquivos
- Discovery, planejamento de arquitetura, decisão de produto
- Qualquer coisa que envolva o Roldão de perto

### Codex CLI
**Fortes em:**
- Execução em lote, sem supervisão
- Tarefas bem-especificadas em `tasks.md` do Spec Kit
- CI/CD integration
- Headless mode

**Usar quando:**
- Implementação de US bem-especificada com AC binário
- Tarefas T-MOD-NNN do Spec Kit (uma por vez)
- Rodar pipeline de auditoria automaticamente

### Os 3 auditores-agentes (rodam em ambas as ferramentas)

A definir formalmente em `governanca/catalogo-auditores.md`. Esboço:

| Auditor | Trigger | Lê | Bloqueia |
|---|---|---|---|
| **Segurança** | Pre-commit em código que toca `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/`, `.claude/hooks/` | SEC-*, INV-TENANT-* + `seguranca/` + diff | Commit |
| **Qualidade** | Pre-commit em qualquer código | TST-* + `tests/` + diff | Commit se teste falhar / coverage abaixo do mínimo |
| **Produto** | Pre-merge em feature | `prd.md` do módulo + US relacionada + diff | Merge se AC binário não passar |

---

## Quando agente Claude/Codex chama outro agente?

- **Subagente Explore** (Claude Code): tarefa "achar onde X está definido no código" → spawna subagente, lê resultado, descarta contexto.
- **Subagente Plan** (Claude Code): tarefa "fazer plano de implementação de feature Y" → spawna subagente, traz plano, descarta contexto.
- **3 auditores**: triggers automáticos definidos em `catalogo-auditores.md`.

**Cuidado:** cada subagente consome contexto separado. Limite por sessão a definir.

---

## Em caso de conflito (Claude vs Codex)

1. Se contradição vier de `AGENTS.md` (canônico) lido com versões diferentes → checar git pull.
2. Se `CLAUDE.md` adicionou regra que conflita com `AGENTS.md` → bug; corrigir CLAUDE.md.
3. Se decisão de produto/arquitetura: `.specify/memory/constitution.md` > `AGENTS.md` > demais (ordem de precedência).
4. Se ainda assim houver conflito: parar e escalar pro Roldão.

---

## Hierarquia de fontes (Auditor 7 v2 alertou — 6 fontes potenciais)

Ordem de precedência (em caso de conflito):

1. `.specify/memory/constitution.md` — princípios não-negociáveis
2. `REGRAS-INEGOCIAVEIS.md` — regras críticas
3. `AGENTS.md` — canônico de produto
4. `docs/adr/NNNN-*.md` — decisões registradas
5. `CLAUDE.md` projeto — adendo de harness
6. `CLAUDE.md` global (`~/.claude/CLAUDE.md`) — defaults universais
7. `.agent/CURRENT.md` — estado de agora
8. `.agent/SESSION.md` — histórico curto
9. auto-memory do Claude Code — preferências do humano

**Hook de drift (a criar):** detecta divergência entre fontes nos pontos espelhados.
