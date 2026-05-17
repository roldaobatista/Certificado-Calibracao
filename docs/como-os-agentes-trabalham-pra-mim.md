# Como os agentes trabalham pra mim

> **Pra quê:** explicar em PT-BR puro, sem jargão, como o sistema de agentes de IA funciona pro Roldão. **1 página.** Sem isso, Família 1 (.claude, .agent, MCP, hooks, etc.) vira floresta opaca.

---

## A versão de 1 minuto

Você (Roldão) **fala em português** com agentes de IA — Claude Code e Codex CLI. Eles **escrevem o sistema** seguindo as regras que combinamos. **3 auditores-agentes** revisam o trabalho deles. Você só precisa olhar 7 documentos e aprovar mudanças em 10 pastas críticas. **Tudo o mais é automático.**

---

## Os atores

```
       VOCÊ (Roldão)
            ↓
            ↓ fala em português
            ↓
  ┌─────────┴──────────┐
  │                    │
CLAUDE CODE        CODEX CLI
(esta ferramenta)   (alternativa)
  │                    │
  └─────────┬──────────┘
            ↓
            ↓ ambos leem AGENTS.md e CLAUDE.md
            ↓
       SISTEMA AFERÊ
       (código + docs)
            ↓
            ↓ revisado por
            ↓
  ┌─────────┼──────────┐
  │         │          │
AUDITOR  AUDITOR    AUDITOR
SEGURANÇA QUALIDADE PRODUTO
```

---

## O que cada um faz

| Ator | Função | Quem é "humano" |
|---|---|---|
| **Você (Roldão)** | Dono. Diz o que quer. Aprova decisões irreversíveis (10 paths CODEOWNERS). É o primeiro cliente. | Sim |
| **Claude Code** | Agente principal de desenvolvimento. Implementa features, lê specs, atualiza docs. | Não (IA) |
| **Codex CLI** | Agente alternativo. Mesmas instruções (`AGENTS.md`), pode ser usado em paralelo. | Não (IA) |
| **3 auditores-agentes** | Revisam trabalho dos 2 acima. Veto materializado (bloqueia merge se algo crítico falhar). | Não (IA) |
| **3 humanos de exceção** | Em 5 casos-limite (a definir em `limites-autonomia.md`), agente para e te avisa. | Sim — você ou contratado pontual |

---

## O fluxo típico de uma feature

1. **Você diz** em PT: "Quero que cliente possa exportar relatório de OS em PDF".
2. **Agente lê** spec (se já existir) ou cria nova spec (com user story, AC, non-goals).
3. **Auditor de produto** revisa spec.
4. **Agente implementa** em tarefas de 5–15 minutos.
5. **Auditor de qualidade** checa código (testes, padrões).
6. **Auditor de segurança** checa risco (vazamento de dado, prompt injection).
7. **Agente commita** com ID rastreável e atualiza CHANGELOG.
8. **Você lê** o CHANGELOG: "✅ Exportação de OS em PDF disponível".

**Em momento nenhum você precisa abrir código.** Tudo é traduzido pra PT no painel-do-dono.

---

## Quando o agente para e te avisa

Os **5 casos-limite** (a definir formalmente em `governanca/limites-autonomia.md`):

1. **Decisão irreversível** — apagar dados de cliente, drop table, push --force.
2. **Mudança em 1 dos 10 paths CODEOWNERS** — afrouxar segurança, mudar conformidade.
3. **Gasto com terceiro** — antes de comprar API paga, contratar SaaS.
4. **Decisão de produto estratégica** — adicionar módulo novo, mudar pricing, descontinuar feature.
5. **Bloqueio técnico real** — agente não consegue resolver após N tentativas, precisa de sua decisão de negócio.

---

## Como você fala com os agentes

- **Claude Code** — terminal: você digita aqui mesmo. Conversa.
- **Codex CLI** — terminal alternativo. Mesmas instruções.
- **Ambos leem** o mesmo `AGENTS.md` — não importa qual usa, comportamento é igual.
- **Você não precisa** decorar comandos ou jargão. Pede em PT, agente faz.

---

## Pra aprofundar (só se quiser)

- `roteamento-dual.md` — fronteira detalhada entre Claude e Codex
- `governanca/catalogo-auditores.md` — detalhes dos 3 auditores (a criar)
- `governanca/limites-autonomia.md` — os 5 casos-limite (a criar)
- `documentos-do-projeto.md` — mapa completo da documentação
- `tutoriais/dono/` — 3 tutoriais mão-na-massa
