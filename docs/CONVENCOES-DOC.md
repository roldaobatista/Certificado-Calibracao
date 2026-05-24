# CONVENÇÕES DE DOCUMENTAÇÃO

> Regras de doc-as-code do projeto. Aplica a todo arquivo `.md` em `docs/`, raiz e subpastas.

---

## 1. Idioma

- **Português brasileiro (PT-BR)** em tudo — exceto 7 arquivos que ferramenta lê pelo nome (D3 da constituição): `README.md`, `CHANGELOG.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CODEOWNERS`, `.env.example`. O **conteúdo** desses 7 também em PT-BR.

## 2. Frontmatter obrigatório

> **Decisão canônica (Onda 0 plano-v2, 2026-05-23):** o nome do campo é **`revisado-em`** (com hífen).
> Motivo: o hook ativo `.claude/hooks/frontmatter-revisado-em-check.sh` valida hífen; AGENTS.md §8 usa hífen; contagem real no repositório aponta 352 docs com hífen vs 339 com underscore — hífen é maioria operacional. Underscore (`revisado_em`) era a forma antiga deste exemplo e gerava drift conflitante com o hook.
> **GATE-FRONTMATTER-RETROFIT-339:** rastreado pra Onda 0 estendida — migrar os 339 docs que ainda usam underscore para hífen num único commit. Até lá, o hook tolera ambas (warning silencioso); após o retrofit, hífen vira único aceito.

Todo doc em `docs/dominios/*/` e `docs/conformidade/*/` deve ter frontmatter YAML:

```markdown
---
owner: roldao
revisado-em: 2026-05-16
proximo-review: 2026-08-16
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

## 5.bis Seção obrigatória em PRD — UX dos estados não-felizes (Onda 2 plano-v2)

> **Decisão Onda 2 plano-v2 (2026-05-23):** auditor de produto da auditoria projeto-inteiro detectou que PRDs cobrem o caminho feliz mas omitem regras dos estados não-felizes, gerando o erro "feature implementada, mas sem critério de aceitação" (item 1200 da checklist de problemas IA).

Todo PRD novo (`docs/dominios/*/modulos/*/prd.md`) DEVE conter uma seção `## N. UX dos estados não-felizes` declarando, por tela ou fluxo, AC binário para:

| Estado | Pergunta a responder no PRD |
|---|---|
| **Empty state** | O que o usuário vê quando a lista/dashboard está vazio? Tem texto orientador? Tem CTA pra primeira ação? |
| **Loading state** | O que aparece enquanto a requisição roda? Skeleton, spinner, mensagem "Carregando..."? Tem timeout? |
| **Erro do servidor (5xx)** | O que aparece quando o backend falha? Tem botão "Tentar de novo"? A mensagem é humana? Disparou audit log? |
| **Erro de rede (offline / timeout)** | App técnico em campo: o que faz quando rede some? Salva local + sincroniza? Mostra ícone offline? |
| **Permissão negada (403)** | O usuário não-autorizado tenta a ação: vê 404 (indistinguível) ou 403 explícito? Aparece "Sem permissão" sem revelar se recurso existe? |
| **Sessão expirada / não-autenticado (401)** | Redireciona pra login preservando contexto (deep-link de retorno)? Salva form em rascunho? |
| **Duplo submit / dupla submissão** | O botão fica desabilitado após clique? `Idempotency-Key` no header? O servidor dedupe? |
| **Validação falhou (422)** | Erro de campo mostrado inline + `aria-invalid` (INV-A11Y-005)? Foco move pro 1º erro? |
| **Recurso não-existe (404)** | Tela de "Não encontrado" tem CTA de volta? Tem link pra busca? |
| **Conflito (409)** | "Outro usuário editou enquanto você editava" — apresenta diff ou força recarregar? |

Hook `prd-ux-states-check.sh` valida presença desta seção em PRD novo. Cada linha da tabela acima é "✅ AC-XXX-N" ou "n/a (motivo)".

Para fluxos que claramente não têm um estado (ex: tela `/health` sem permissão negada porque é público), declarar `n/a` com motivo curto. `n/a` sem motivo = bloqueio do hook.

## 6. Diátaxis (tipo de doc)

Cada doc é UMA das 4 categorias:
- **Tutorial** — aprende fazendo. Linear, mão-na-massa. Audiência: iniciante.
- **How-to** — resolve tarefa específica. Lista de passos. Audiência: usuário experiente.
- **Reference** — consulta fato. Tabular, denso, completo. Audiência: técnico procurando dado.
- **Explanation** — entende porquê. Discussivo, contexto. Audiência: quem quer profundidade.

**Misturar tipos no mesmo doc é proibido** — quebra navegação. Se a sua frase puxa pra outro tipo, criar doc separado e linkar.

## 7. Versionamento

- Doc importante (REGRAS, constitution, ADR) tem `revisado-em` no frontmatter (hífen — ver §2 sobre decisão canônica Onda 0).
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
