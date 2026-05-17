# Tutorial — seu primeiro pedido ao agente

> Tutorial Diátaxis: aprenda fazendo. Audiência: Roldão (não-técnico) na primeira vez usando agentes de IA pro projeto.

---

## O que você vai aprender (em 5 minutos)

1. Como abrir conversa com agente Claude Code
2. Como pedir uma tarefa em PT
3. Como ler resposta do agente
4. Quando dizer "sim" / "não" / "espera"

---

## Passo 1 — Abrir conversa

Abra o **Claude Code** (terminal do Windows com `claude` digitado). Ele já está configurado pro projeto Aferê — leu `CLAUDE.md`, `AGENTS.md`, e a `.specify/memory/constitution.md` automaticamente.

**Você não precisa decorar comandos.** Pode digitar em PT normal.

---

## Passo 2 — Fazer pedido em PT

Exemplos de pedidos válidos (e como o agente vai interpretar):

| Você digita | Agente entende como | O que faz |
|---|---|---|
| "Liste os documentos que ainda faltam criar" | Status report | Lê `docs/documentos-do-projeto.md`, retorna lista filtrada por status ⏳ |
| "Crie o glossário do domínio" | Tarefa de implementação | **PARA e avisa:** "glossário sai do discovery; quer começar o discovery?" |
| "Quero que cliente possa exportar OS em PDF" | Nova feature | Cria spec → plan → tasks (Spec Kit), implementa, audita |
| "Renomeie 'cliente' pra 'parceiro'" | Refactor grande | **PARA e avisa:** "afeta INV-007 + glossário comum + N módulos; confirma?" |
| "Apague todos os clientes de teste" | Operação destrutiva | **PARA e exige sua aprovação** (Caso 1 de `limites-autonomia.md`) |

---

## Passo 3 — Ler resposta do agente

Toda resposta tem 3 partes implícitas:
1. **O que ele entendeu** do seu pedido (parafraseado em PT)
2. **O que ele fez ou vai fazer** (lista clara)
3. **O que ele precisa de você** (se algo)

Se o agente NÃO te perguntar nada e não pedir aprovação, ele fez/vai fazer dentro dos `limites-autonomia.md`.

Se ele PERGUNTAR, é um dos 5 casos-limite. Veja `MAPA-DO-DONO.md`.

---

## Passo 4 — Quando dizer sim / não / espera

| Situação | Você diz | Por quê |
|---|---|---|
| Agente propõe ação dentro de autonomia | (não precisa responder, ele faz) | Roldão não fica gargalo |
| Agente pede aprovação em path CODEOWNERS | "sim" ou "não" | Decisão irreversível ou afrouxa segurança |
| Agente parece estar indo pra direção errada | "espera, deixa eu explicar" | Sempre pode interromper |
| Agente te pergunta sobre escopo / produto / decisão de negócio | Responde em PT | Só você sabe |
| Agente vai gastar com terceiro | "sim" ou "não" + valor | Caso 3 (gasto) |

---

## Passo 5 — Erros comuns (não cometa)

❌ **Pedir várias coisas diferentes na mesma mensagem.** Agente trabalha melhor em 1 tarefa atômica por vez. Quebra em pedidos sequenciais.

❌ **Não responder quando ele pergunta.** Ele para e fica bloqueado. Vê em `.agent/CURRENT.md` que ele está em `BLOQUEADO: aguardando decisão`.

❌ **Aceitar qualquer resposta sem ler o `painel-do-dono.md`.** O painel é a fonte da verdade do que está acontecendo.

❌ **Pedir pra ele "fazer rápido" e pular auditor.** Auditores existem pra te proteger; pular = você fica refém de bug.

---

## Próximo tutorial

`ler-status-semanal.md` — como interpretar o relatório semanal auto-gerado.
