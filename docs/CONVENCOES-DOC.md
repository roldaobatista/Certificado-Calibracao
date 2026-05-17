# CONVENÇÕES DE DOCUMENTAÇÃO

> Regras de doc-as-code do projeto. Aplica a todo arquivo `.md` em `docs/`, raiz e subpastas.

---

## 1. Idioma

- **Português brasileiro (PT-BR)** em tudo — exceto 7 arquivos que ferramenta lê pelo nome (D3 da constituição): `README.md`, `CHANGELOG.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CODEOWNERS`, `.env.example`. O **conteúdo** desses 7 também em PT-BR.

## 2. Frontmatter obrigatório

Todo doc em `docs/dominios/*/` e `docs/conformidade/*/` deve ter frontmatter YAML:

```markdown
---
owner: roldao
revisado_em: 2026-05-16
proximo_review: 2026-08-16
status: draft | stable | deprecated
diataxis: tutorial | how-to | reference | explanation
audiencia: dono | agente | cliente | regulador | auditor
relacionados:
  - docs/comum/glossario.md
  - INV-007
---
```

Docs de fundação (raiz, `comum/`, `discovery/`, `governanca/`) podem omitir frontmatter mas devem ter cabeçalho equivalente em texto.

## 3. IDs e linkagem cruzada

- IDs do REGRAS-INEGOCIAVEIS: `INV-NNN`, `INV-TENANT-NNN`, `TST-NNN`, `SEC-NNN`. Sempre maiúsculos, sempre 3 dígitos.
- IDs de spec: `US-<MOD>-NNN` (user story), `AC-<MOD>-NNN-N` (critério de aceite), `T-<MOD>NNN` (tarefa).
- IDs de ADR: `ADR-NNNN`.

**Linkagem entre docs:**
- Para outro doc: link relativo Markdown padrão `[texto](../comum/glossario.md)`.
- Para regra: citar o ID puro `INV-007`. Hook valida que ID existe no `REGRAS-INEGOCIAVEIS.md`.
- Para entidade do glossário: usar `[[termo]]` com termo igual ao slug no glossário.

## 4. Regra "comum vs módulo" (governança-modelo-comum)

Detalhada em `comum/governanca-modelo-comum.md`. Resumo:
- Entidade é **comum** se ≥2 módulos usam SEM extensão de campos.
- Entidade é **específica de módulo** se tem campos próprios obrigatórios.
- Quando módulo precisa estender entidade comum: extension table OU JSONB OU herança (decisão no ADR do módulo).
- **Hook valida:** não criar entidade duplicada com mesmo nome em comum + módulo.

## 5. Tamanho

- `CLAUDE.md ≤ 150 linhas`, `AGENTS.md ≤ 250 linhas`, `REGRAS-INEGOCIAVEIS.md ≤ 120 linhas` (D3 da constituição).
- Outros docs sem teto rígido, mas se passar 500 linhas, considerar quebrar.
- Hook `context-budget` tokeniza (não conta linhas) e falha acima do teto.

## 6. Diátaxis (tipo de doc)

Cada doc é UMA das 4 categorias:
- **Tutorial** — aprende fazendo. Linear, mão-na-massa. Audiência: iniciante.
- **How-to** — resolve tarefa específica. Lista de passos. Audiência: usuário experiente.
- **Reference** — consulta fato. Tabular, denso, completo. Audiência: técnico procurando dado.
- **Explanation** — entende porquê. Discussivo, contexto. Audiência: quem quer profundidade.

**Misturar tipos no mesmo doc é proibido** — quebra navegação. Se a sua frase puxa pra outro tipo, criar doc separado e linkar.

## 7. Versionamento

- Doc importante (REGRAS, constitution, ADR) tem `revisado_em` no frontmatter.
- ADR é **imutável** após status `stable`. Mudança = novo ADR que substitui (`Substitui ADR-NNNN`).
- Glossário versiona via git; quebra de contrato (renomear termo) exige aviso no CHANGELOG.

## 8. Linguagem

- **Pra dono não-técnico:** PT-BR claro, sem jargão. Quando jargão é inevitável, glossário define + tutorial explica.
- **Pra agente:** PT-BR + pode usar jargão técnico (agente entende). Mas evitar jargão **inventado** sem definir.
- Banido em todo doc: emojis sem propósito (só os funcionais 🔴🟡⚪✅⏳⭐ e variantes), gírias, marketing.

## 9. Quem aprova mudança

- Doc em `docs/conformidade/` ou `REGRAS-INEGOCIAVEIS.md` ou `.specify/memory/constitution.md` → CODEOWNERS (humano).
- Outros docs → agente comita direto na main; auditor de produto revisa post-facto.

## 10. Como esta convenção evolui

Discussão → proposta de mudança → consenso entre os 3 auditores-agentes + Roldão → atualizar este arquivo + adicionar entrada no CHANGELOG na seção `Modificado`.
