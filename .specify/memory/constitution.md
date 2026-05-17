# Constituição do projeto Aferê (provisório)

> **Princípios não-negociáveis** lidos por todo comando do Spec Kit (`/specify`, `/plan`, `/tasks`, `/implement`) e por qualquer agente trabalhando no projeto.
>
> Mudanças aqui exigem aprovação humana via CODEOWNERS (D5 — este arquivo é um dos 5 paths anti-bypass).
>
> Esta constituição **complementa** `CLAUDE.md` global (instruções gerais Roldão), `CLAUDE.md` projeto (subordinado a este arquivo) e `AGENTS.md` (canônico de produto). Em caso de conflito, ordem de precedência:
>
> **`.specify/memory/constitution.md` > `AGENTS.md` > `CLAUDE.md` projeto > `CLAUDE.md` global**

---

## Os 6 princípios

1. **Documento = estado compartilhado.** Quando a conversa não cabe na janela do agente, o arquivo no disco é a verdade. Cada agente lê de um lugar previsível e escreve em outro.

2. **Spec gera código (spec-as-source).** A especificação em PT é a fonte da verdade. Agente traduz spec → código. Mudou código sem atualizar spec no mesmo commit = bug, não funcionalidade nova.

3. **Conciso vence completo.** Se o agente faz pergunta respondida em `CLAUDE.md` ou `AGENTS.md`, o arquivo está longo demais. Tetos: `CLAUDE.md ≤ 150 linhas`, `AGENTS.md ≤ 250 linhas`, `REGRAS-INEGOCIAVEIS.md ≤ 120 linhas`. Hooks contam tokens (não linhas) e falham acima.

4. **Fases de 5–15 minutos** com critério de aceite binário (passou / não passou). Agentes performam mal em feature holística; bem em fases sequenciais.

5. **Non-goals explícitos.** Agente não infere por omissão — precisa de proibição positiva. Toda feature lista "o que esta feature NÃO faz".

6. **IDs rastreáveis.** `US-<MOD>-NNN` (user story por módulo) → `AC-<MOD>-NNN-N` (critério de aceite) → `T-<MOD>NNN` (tarefa) → commit. Sem isso, não há auditoria.

---

## Regras mestras

### Regra mestre 1 — Regra crítica vira hook, não doc
Anti-mascaramento (`TST-001`, `TST-002`, `TST-003`), invariantes (`INV-NNN`), teto de tokens, `INV-TENANT-001` (todo query SQL tem `tenant_id`): tudo o que precisa ser FORÇADO é hook. Doc explica o hook; não substitui o hook.

### Regra mestre 2 — Fonte única por tipo de informação
- Regras críticas: `REGRAS-INEGOCIAVEIS.md` é fonte única (IDs `INV-`, `INV-TENANT-`, `TST-`, `SEC-`). Outros docs **citam IDs**, não duplicam texto.
- Decisões arquiteturais: `docs/adr/NNNN-*.md`.
- Estado entre sessões: `.agent/CURRENT.md` (agora) + `.agent/SESSION.md` (histórico curto).
- Mudanças do produto: `CHANGELOG.md`.

---

## 5 decisões fundadoras

| # | Decisão | Detalhe |
|---|---------|---------|
| **D1** | Adotar **Spec Kit** | Framework leve de spec. Coexiste com docs custom. |
| **D2** | **Spec-as-source** | Spec PT é a verdade. Auditor 1 garante que não apodreça. |
| **D3** | **Nomenclatura híbrida** | PT em tudo, exceto 7 arquivos que ferramentas leem pelo nome: `README.md`, `CHANGELOG.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CODEOWNERS`, `.env.example`. Conteúdo desses 7 também em PT. |
| **D4** | **Devcontainer** como sandbox | Container Docker isola execução do agente. Criar APÓS ADR-0001. |
| **D5** | **CODEOWNERS expandido** (revisada 2026-05-16) | Não só os 5 paths "anti-bypass" originais; também 5 pastas críticas de ERP financeiro: `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/`. Total 10 paths exigem aprovação humana mecânica. |

**Decisão NÃO-numerada (mesmo peso, decidida 2026-05-16):**
> Família 0 Discovery rigorosa **não se reduz** por argumento "lean" ou "MVP rápido". Mitigação obrigatória do risco "founder is customer = customização disfarçada". Roldão vetou explicitamente.

---

## Pra quê servem essas regras

Roldão NÃO programa. Sem regras travadas em hook + spec PT canônica, agente diferente reescreve o sistema de outro jeito a cada conversa. **A constituição é o trilho que impede descarrilhar.**

Mudança aqui exige:
1. ADR formal (`docs/adr/NNNN-*.md`) explicando o porquê.
2. Aprovação humana via CODEOWNERS.
3. Atualização sincronizada de `AGENTS.md`, `CLAUDE.md` projeto, `REGRAS-INEGOCIAVEIS.md` se afetados.
