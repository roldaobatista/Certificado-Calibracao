# Auditoria de decisões autônomas dos agentes

> **Lista do que os agentes decidiram SEM consultar o Roldão** (dentro dos `limites-autonomia.md`). Roldão lê pra estar informado; pode discordar (vira ADR de reversão).
>
> Auditor 2 v2 alertou: sem essa filtragem dedicada, autonomia vira caixa-preta.

---

## Formato de cada entrada

```markdown
### YYYY-MM-DD — [Resumo em PT-BR de 1 linha]
- **Decisão:** [o que foi decidido]
- **Por quê:** [razão objetiva]
- **Quem decidiu:** [agente Claude Code / Codex CLI / Auditor X]
- **Sessão:** [hash ou link pra `.agent/SESSION.md` da época]
- **Impacto:** [reversível / irreversível / parcialmente reversível]
- **Caso-limite (do limites-autonomia)?** [Caso N — sim/não] (se sim, deveria ter escalado — bug do agente)
- **Link pra ADR (se criado):** [path]
- **Roldão revisou?** ⏳ pendente / ✅ aprovou / ❌ discordou (ver ADR-NNNN de reversão)
```

---

## Entradas (cronológico reverso)

### 2026-05-16 — Estrutura inicial de documentação criada
- **Decisão:** criação de ~33 arquivos de fundação + estrutura de pastas seguindo `documentos-do-projeto.md` v5; ~100 arquivos lazy do v5 NÃO foram criados conforme regra do próprio doc.
- **Por quê:** Roldão autorizou "criar toda estrutura"; agente seguiu regra do doc "não criar template vazio pra preencher depois".
- **Quem decidiu:** Claude Code (Opus 4.7)
- **Sessão:** ver `.agent/SESSION.md` entrada 2026-05-16
- **Impacto:** reversível (arquivos podem ser deletados)
- **Caso-limite?** Não — está dentro da autonomia
- **Link pra ADR:** N/A
- **Roldão revisou?** ⏳ pendente (este é o primeiro item da lista)

---

## Como agente atualiza esta lista

A cada decisão autônoma significativa (que valha registrar):
1. Adiciona entrada NO TOPO (cronológico reverso).
2. Atualiza `status-semanal.md` referenciando esta entrada.
3. Atualiza `trilha-auditoria-agentes.md` com detalhe técnico.

## Critério "significativa" pra registrar

- Mudança em arquivo de `REGRAS-INEGOCIAVEIS.md`, `governanca/`, `conformidade/`, `adr/`, `comum/`.
- Mudança em > 5 arquivos numa única sessão.
- Adoção/descontinuação de ferramenta, biblioteca, padrão.
- Decisão arquitetural não-trivial.
- Tudo que poderia ter escalado mas foi decidido autonomamente.

**Não registrar:** correção de typo, atualização de status, edição de comentário.
