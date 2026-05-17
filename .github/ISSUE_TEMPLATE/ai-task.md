---
name: Tarefa pra agente de IA
about: Template padrão de tarefa que vai ser executada por agente (Claude Code ou Codex)
title: '[MOD-XXX] Descrição curta da tarefa'
labels: ai-task
---

## Contexto
<!-- Por que essa tarefa existe? Qual a dor real? Citar US/spec se aplicável. -->

## Critério de aceite (binário — passa/não passa)
<!-- Lista de AC-MOD-NNN-X verificáveis. Cada um deve ser uma assertion clara. -->

- [ ] AC-XXX-1: ...
- [ ] AC-XXX-2: ...

## Comando literal de validação
<!-- Comando exato que prova que terminou. Sem isso, agente decide sozinho quando terminou. -->

```
# exemplo:
npm test -- --grep "AC-XXX"
```

## Non-goals (o que esta tarefa NÃO faz)
<!-- LLM não infere por omissão. Listar proibições positivas. -->

- ...
- ...

## Dependências
<!-- US/T/ADR/INV que precisam estar prontos antes. -->

- Bloqueado por: #...
- Bloqueia: #...

## Spec relacionada
<!-- Path do spec.md / plan.md / tasks.md -->

- `docs/dominios/<dom>/modulos/<mod>/specs/<NNN>/spec.md`

## Notas pra o auditor
<!-- O que o auditor deve checar com atenção. -->
