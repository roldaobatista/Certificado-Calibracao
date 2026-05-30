---
owner: roldao
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 200
proposito: regras para contribuição externa — fluxo de PR, padrão de commit, quality gates, código de conduta
---

<!--
template: CONTRIBUTING.md
uso: copiar para a raiz do repositório.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C0
-->

# CONTRIBUTING — Aferê Prumo

> Como humanos e agentes contribuem com este repositório. Fonte canônica de processo. Fonte canônica de produto: [`AGENTS.md`](./AGENTS.md).

> **Dono não-técnico?** Veja [`GLOSSARIO-ROLDAO.md`](./GLOSSARIO-ROLDAO.md) para tradução do jargão (PR, commit, branch, lint, build, etc.) antes de continuar. (O glossário fica na raiz do projeto destino, ao lado deste `CONTRIBUTING.md`.)

## 0. Glossário

Tradução de jargão técnico (lint, type-check, dry-run, baseline, `--no-verify`, `--force-with-lease`, etc.) vive em [`GLOSSARIO-ROLDAO.md`](./GLOSSARIO-ROLDAO.md) na raiz. Não duplicamos aqui.

Termos do domínio do produto (entidades, papéis, estados) vivem em [`docs/glossario.md`](./docs/glossario.md).

> Se um termo crítico aparece em CONTRIBUTING e não está em nenhum dos dois glossários, **adicione ao glossário antes de mergir o PR** (regra de consistência).

## 1. Fluxo do agente

1. **Ler a spec.** Localizar `docs/dominios/<dom>/modulos/<modulo>/spec.md` e os ACs binários referentes à tarefa.
2. **Propor plano.** Esboçar passos, arquivos a tocar, riscos. Se a tarefa for não-trivial, gravar em `plan.md`.
3. **Revisão de plano.** Submeter ao humano OU ao auditor de plano configurado. Não pular para implementação.
4. **Implementar.** Editar código + testes na mesma mudança. Mexer no ponto raiz, não no sintoma.
5. **Auditar.** Rodar auditores locais relevantes ao escopo da mudança (ver §6).
6. **Commit.** Atômico, mensagem citando `T-<MOD>-NNN`. Sem `--no-verify`. Sem misturar fix + feature + refactor.

## 2. Fluxo do humano

- **Propor mudança de produto:** abrir issue com persona, dor, AC binário sugerido. Não enviar texto livre — usar o template de spec.
- **Propor mudança de arquitetura:** abrir ADR em `docs/adr/ADR-NNNN-<slug>.md` seguindo o padrão dos ADRs já existentes (ver, por exemplo, `docs/adr/ADR-0001-stack.md`). Status inicial: `proposta`.
- **Reportar bug:** descrever o efeito visível (o que o usuário vê), o passo-a-passo para reproduzir, e o estado real dos dados (printscreen, linha do banco, payload). NUNCA reportar só "não funciona".

## 3. Quality gates obrigatórios antes de commit

Proporcional ao escopo da mudança:

| Mudança em | Gates obrigatórios |
|---|---|
| Código de produto | lint + type-check + testes do módulo tocado |
| Migration | dry-run + check de RLS + diff do schema |
| Documentação | frontmatter-validator + link-checker |
| Auditor / hook | golden tests do próprio auditor |
| Spec / ADR | frontmatter-validator + revisão humana |

Suite completa só ao final da fase ou antes de release. Não rodar no meio da task.

## 4. O que NUNCA fazer

- `git commit --no-verify` ou qualquer `--skip-*` / `--ignore-*` que pule hook.
- `git push --force` ou `--force-with-lease` em `main` / branch protegida.
- `git reset --hard` em commit já publicado.
- Mascarar teste: `skip`, `xit`, `assertTrue(true)`, assertion relaxada para passar.
- `eslint-disable` / `@ts-ignore` / `# noqa` sem comentário justificando + ID de issue.
- Adicionar baseline para esconder erro existente.
- Mexer em `aparência/template/CSS` quando o problema é de dado/lógica (ver Regra #0 em CLAUDE.md).
- Commitar dado real de cliente, credencial, `.env`, dump de banco.

## 5. Política de commits

**Antes de cada `git commit`** (obrigatório — INV-AGENT-007):
1. `git status` — ver o que está dirty.
2. `git diff --staged` — ver o que vai entrar no commit.
3. `git log -3 --oneline` — conferir estilo do histórico.
4. `git add <arquivos-específicos>` — nunca `git add .` se houver outras frentes dirty.

- Atômicos: 1 commit = 1 propósito claro.
- Mensagem: `ia-ml(<modulo>): <resumo>` + corpo opcional + referência a `T-<MOD>-NNN`.
- Tipos: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `adr`.

## 5.1 Uso de `gh` CLI (canônico — não empurrar pro humano)

Operações de PR/issue/release são feitas pelo agente IA via `gh` — sem empurrar trabalho executável pro dono não-técnico. Comandos canônicos:

| Operação | Comando |
|---|---|
| Criar PR | `gh pr create --base main --title "..." --body "..."` |
| Comentar em PR | `gh pr comment <num> --body "..."` |
| Ver status de checks do PR | `gh pr checks <num>` |
| Aprovar e fazer merge (com squash) | `gh pr merge <num> --squash --delete-branch` |
| Criar issue | `gh issue create --title "..." --body "..."` |
| Comentar em issue | `gh issue comment <num> --body "..."` |
| Fechar issue | `gh issue close <num>` |
| Criar release/tag | `gh release create v1.2.3 --notes "..."` |
| Adicionar topic ao repo | `gh repo edit --add-topic <topic>` |

**Estratégia de merge:**
- **Squash merge:** apropriado para libs OSS com histórico público navegável.
- **Fast-forward:** apropriado para projetos com tasks `T-<MOD>-NNN` rastreáveis (uma task por commit, histórico linear).
- **Rebase + merge não-FF:** desnecessariamente complexo — não usar.

A decisão fica em `documentos-do-projeto.md` campo `politica-branches`.

## 6. Como rodar auditores localmente

```bash
# Auditor único
<comando-base> .claude/agents/auditor-<dominio>.md --target <arquivo|diff>

# Todos os auditores relevantes ao diff atual
<comando-base> --diff HEAD

# Golden tests de um auditor (antes de bumpar versão)
<comando-base> --golden docs/governanca/golden/auditor-<dominio>/
```

<!-- Substituir <comando-base> pelo runner real do projeto.
     Listar auditores ativos em docs/governanca/catalogo-auditores.md. -->

## 7. Quando pedir ajuda humana

- Ambiguidade na spec que afeta o AC binário.
- Conflito entre dois auditores no mesmo achado (ver tie-break do template de auditor).
- Operação destrutiva: drop table, rotação de credencial, mudança legal pública, gasto com terceiro pago.
- Mudança que aparenta resolver mas mexe em sintoma — preferir confirmar a causa raiz antes.
