---
owner: <responsavel>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 200
proposito: convenções de documentação do projeto — nomenclatura, kebab-case, idioma, ordem de seções, frontmatter
---

<!--
template: CONVENCOES-DOC.md
destino: docs/CONVENCOES-DOC.md
uso: política única de nomenclatura, IDs e links do projeto.
-->

# Convenções de Documentação — Aferê Prumo

## 1. Idioma
- Idioma padrão: **PT-BR** em todo o conteúdo.
- Termos técnicos podem ser mantidos no original (ex: `endpoint`, `runbook`, `token`), mas **exigem tradução em primeira ocorrência** dentro do documento ou link para `GLOSSARIO-ROLDAO.md` na raiz do método (e/ou `docs/glossario.md` no projeto destino).
- Strings de interface, mensagens de erro e exemplos de código seguem a língua do produto.

## 2. Nomes de arquivos e pastas
- **SEM acentos, SEM cedilha, SEM espaços** em qualquer nome de arquivo, pasta ou identificador.
- Dentro de `docs/`: `kebab-case` (ex: `politica-de-retencao.md`, `catalogo-auditores.md`).
- Na raiz do repositório: `UPPER-CASE` para documentos contratuais (`AGENTS.md`, `REGRAS-INEGOCIAVEIS.md`, `README.md`) ou `MixedCase` quando já consagrado.
- Pastas: sempre `kebab-case` minúsculo.
- Sufixo de template: `<nome>.template.md`.

## 3. Formato de identificadores
Padrão geral:
```
<PREFIXO>-<ESCOPO>-NNN
```
- `PREFIXO`: tipo do artefato (ver §4).
- `ESCOPO`: domínio, módulo ou área (ex: `FIN`, `AUTH`, `BILLING`). Pode ser omitido em prefixos globais.
- `NNN`: numeração sequencial com no mínimo 3 dígitos (`001`, `042`). ADR usa 4 dígitos (`0001`).

Exemplos:
- `US-FIN-014` — user story 14 do domínio Financeiro.
- `T-AUTH-003` — tarefa 3 do módulo de Autenticação.
- `INV-TENANT-007` — invariante de isolamento multi-tenant.
- `ADR-0012` — decisão arquitetural 12.

## 4. Lista canônica de prefixos
| Prefixo | Significado | Onde mora |
|---|---|---|
| US | User Story | `docs/dominios/<dom>/modulos/<mod>/stories/` |
| AC | Critério de Aceite | dentro da US correspondente |
| T | Tarefa de implementação | `docs/dominios/<dom>/modulos/<mod>/tarefas/` |
| INV | Invariante de negócio | `docs/dominios/<dom>/invariantes/` |
| INV-TENANT | Invariante de isolamento multi-tenant | `docs/seguranca/invariantes-tenant.md` |
| INV-AGENT | Invariante observada por subagente | `docs/governanca/invariantes-agente.md` |
| SEC | Requisito de segurança | `docs/seguranca/` |
| TST | Caso de teste rastreável | `docs/qualidade/casos-de-teste/` |
| OBS | Item de observabilidade (métrica, log, trace) | `docs/operacao/observabilidade.md` |
| DAT | Requisito de dados (modelo, retenção) | `docs/dados/` |
| OPS | Item operacional (runbook, on-call) | `docs/operacao/` |
| LEG | Requisito legal/regulatório | `docs/conformidade/` |
| R | Risco mapeado | `docs/governanca/registro-de-riscos.md` |
| EE | Entrevista de Exploração | `docs/descoberta/entrevistas/` |
| ADR | Decisão arquitetural (4 dígitos) | `docs/adr/` |
| GATE | Critério binário de avanço de fase | `docs/faseamento/<fase>/gates.md` |
| D | Decisão fundadora | `AGENTS.md` §4 |

## 5. Links entre documentos
- Sempre **relativos**, nunca absolutos do sistema de arquivos.
- Preferir caminho a partir do arquivo atual: `../adr/ADR-0001-stack.md`.
- Linkar pela primeira menção de um ID: `[US-FIN-014](../dominios/financeiro/modulos/cobranca/stories/US-FIN-014.md)`.
- Evitar links externos voláteis (encurtadores, paginação dinâmica).

## 6. TODO e FIXME
Comentários de pendência sempre com **data ISO e dono**:
```
<!-- TODO 2026-MM-DD @nome: descrição curta da pendência -->
<!-- FIXME 2026-MM-DD @nome: comportamento errado que precisa correção -->
```
- `TODO` para item planejado ainda não feito.
- `FIXME` para defeito conhecido.
- Sem dono = não entra. Sem data = não entra.

## 7. Frontmatter obrigatório
Todo documento sob `docs/` e `.agent/` deve ter:
```
---
owner: <responsavel>
revisado-em: 2026-05-28      # OU `ultima-conferencia` para registros vivos (runbook, slo-sli, backup, on-call, DR, retencao-dados, catalogo-auditores, SECURITY, change-management, documentos-do-projeto, CONVENCOES-DOC)
status: <draft|stable|deprecated>
idioma: pt-BR
limite-linhas: <numero>
---
```

Use `revisado-em` quando o documento é decisão histórica (problema, spec, plan, tasks, CHECKLIST, CURRENT, kickoff). Use `ultima-conferencia` quando o documento é registro vivo que precisa ser reconferido periodicamente.

> **Política de `limite-linhas` (decisão do dono, 2026-05-28):** o campo `limite-linhas` é um
> **alvo orientativo, não um teto rígido**. **Completude vence concisão** — nenhum documento deve
> ser cortado/empobrecido por causa do limite. Documentos podem **exceder à vontade** quando o
> conteúdo justifica. O verificador `doc-line-counter.sh` foi ajustado para **apenas avisar** (não
> bloqueia). Mantenha o campo no frontmatter como referência de "tamanho-alvo"; fatiar em arquivos
> irmãos é opcional, só quando ajudar a navegação.

## 8. Estrutura mínima por documento
- Título `# ` na primeira linha após o frontmatter.
- Numeração de seções (`## 1.`, `## 2.`) quando o documento for contratual.
- Tabelas com cabeçalho explícito.
- Sem emoji.

## 9. Datas e timestamps
- Datas em prosa, frontmatter e nomes de arquivo usam `2026-05-28` **sem timezone** (ex.: `2026-05-27`).
- Quando for necessário timestamp com hora (logs, post-mortem, eventos de auditoria), usar **ISO-8601 UTC** com sufixo `Z` (ex.: `2026-05-27T14:30:00Z`).
- Não usar formatos locais (`27/05/2026`, `05-27-2026`).

## 10. Memória do agente — `.claude/memory/` e `.agent/`
Cada pasta hospeda um tipo distinto de memória — **não há duplicação nem fallback**:

| Pasta | Conteúdo canônico | Quem lê |
|---|---|---|
| `.claude/memory/constitution.md` | Princípios fundadores (estáticos, mudam raramente) | Claude Code carrega automaticamente. Outros harnesses leem via `additionalDirectories` em `settings.json` ou referência explícita. |
| `.agent/CURRENT.md` | Estado vivo (foco da sessão, último T, próximo passo) | Cross-harness. Único arquivo de "estado atual" — sem cópia em `.claude/memory/`. |

Regra: **um arquivo, um lugar.** Não criar `.claude/memory/CURRENT.md`. Não criar `.agent/constitution.md`. Manter a separação evita drift entre cópias.
