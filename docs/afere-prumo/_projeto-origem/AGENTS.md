---
owner: roldao
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 300
proposito: contrato canônico para agentes IA no projeto destino
tipo: <saas|lib|cli|oss|interno|solo>
licenca: <MIT|Apache-2.0|proprietaria>
modo: <equipe|solo>
---

<!--
template: AGENTS.md
uso: copiar para a raiz do repositório.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C0
limite: ≤300 linhas. Se passar, fatie em sub-docs.
ordem: frontmatter → este HTML comment → corpo.

AUTONOMIA NA INSTANCIAÇÃO (regra mestre — ver INV-AGENT-004):
Ao copiar este template para um projeto novo, preencha CADA <placeholder> com a MELHOR
INFERÊNCIA a partir de: git config user.name/email, manifestos (package.json, Cargo.toml,
pyproject.toml, go.mod, pom.xml), README existente, exemplos em templates/exemplos/.
Use "PROVISÓRIO" quando inferir com baixa confiança. NUNCA pergunte ao dono campos que
tenham default razoável ou possam ser detectados do contexto.

Defaults por tipo (aplicar automaticamente sem perguntar):
- tipo=solo: modo=solo, licenca=proprietaria (default), sem owner separado de tech-lead.
- tipo=oss: licenca=MIT, modo=equipe.
- tipo=lib: licenca=MIT, modo=equipe.
- tipo=cli: licenca=MIT, modo=solo se 1 dev, equipe se >1.
- tipo=saas: licenca=proprietaria, modo=equipe.
- tipo=interno: licenca=proprietaria.
- idioma: pt-BR (herdado do frontmatter). Só alterar se projeto for OSS internacional.

Detecção de stack:
- package.json → Node/JS/TS (frameworks via dependencies).
- Cargo.toml → Rust.
- pyproject.toml/requirements.txt → Python.
- go.mod → Go.
- pom.xml/build.gradle → Java/Kotlin.
Se nenhum manifesto existe, escolha default do tipo (saas→TS+Postgres+React; cli→Rust;
lib→TS; interno→qualquer linguagem do time) e marque "candidata".
-->

# AGENTS.md — Aferê Prumo

> **Hierarquia de precedência (vale para os 4 contratos AI):**
> constitution.md > REGRAS-INEGOCIAVEIS.md > AGENTS.md > CLAUDE.md
> Em qualquer conflito, o documento mais alto vence. CLAUDE.md é o mais específico (canal Claude Code) e o mais fácil de mudar.

**Status:** draft · **Última revisão:** 2026-05-28

## 1. Identidade do produto

> Inferir do contexto (README, mensagem do dono, nome do diretório). Marcar `PROVISÓRIO` quando inferir. Não perguntar ao dono — ele revisa depois.

- Nome: <Nome>
- Escopo: <1 parágrafo>
- Modelo de negócio: <SaaS B2B|B2C|interno|OSS|...>
- Cliente piloto: <quem ou "próprio dono" para projetos solo>

## 2. Stack candidata

> Detectar a partir dos manifestos do projeto (package.json, Cargo.toml, requirements.txt, pyproject.toml, go.mod, pom.xml). Se ausente, escolher default do tipo detectado (ver HTML comment do cabeçalho) e marcar "candidata". Não perguntar.

| Camada | Escolha | Notas |
|---|---|---|
| Backend | <...> | candidata |
| Banco | <...> | candidata |
| Frontend | <...> | candidata |

## 3. Princípios não-negociáveis

Detalhes completos (regra, motivação, hook, auditor) em [`REGRAS-INEGOCIAVEIS.md`](./REGRAS-INEGOCIAVEIS.md). Resumo dos 11 IDs vigentes:

- **INV-AGENT-001** — agente IA não deleta dado de produção sem confirmação humana.
- **INV-AGENT-002** — proibido `--no-verify`, `--force`, `--force-with-lease` em `main`.
- **INV-AGENT-003** — investigar (banco/log/payload) antes de editar lógica de negócio.
- **INV-AGENT-004** — pró-atividade: executa reversíveis sem perguntar; confirma só destrutivos.
- **INV-AGENT-005** — validar antes de afirmar "pronto"; evidência obrigatória.
- **INV-AGENT-006** — causa raiz, nunca sintoma; proibido mascarar erro.
- **INV-AGENT-007** — commits atômicos; sem `git add .` cego.
- **INV-AGENT-008** — PII nunca em logs/prints; mascarar antes.
- **INV-AGENT-009** — segredos nunca em arquivo versionado.
- **INV-AGENT-010** — linguagem acessível; traduzir jargão na 1ª ocorrência (tabela canônica no anexo 2.A da INV).
- **INV-AGENT-011** — alteração de qualquer INV-AGENT exige PR dedicado + aprovação do dono.

## 4. Decisões fundadoras (D-NNN)
| ID | Decisão | Status |
|---|---|---|
| D-001 | Adoção do meta-template (AGENTS + REGRAS-INEGOCIAVEIS + constitution + CLAUDE.md) | aceita |

> O agente adiciona D-002, D-003... conforme decisões reais surgem (escolha de stack, modelo de tenancy, política de branch). Não pedir ao dono para listar decisões — registrar conforme acontecem.

## 5. Modelo de agentes
Ver [`docs/governanca/catalogo-auditores.md`](./docs/governanca/catalogo-auditores.md).

## 6. Comandos canônicos

> Extrair de scripts existentes (`package.json#scripts`, `Makefile`, `justfile`, `Cargo.toml`, `pyproject.toml`). Se nada existir ainda, propor defaults do ecossistema detectado. Não perguntar ao dono — preencher e ele ajusta.

| Operação | Comando |
|---|---|
| Rodar dev | <...> |
| Rodar testes | <...> |
| Migration nova | <...> |
| Auditores locais | <...> |

## 7. Política de commits

**Antes de QUALQUER `git commit`** (obrigatório para commits atômicos — INV-AGENT-007):
1. `git status` — ver o que está dirty.
2. `git diff --staged` — ver o que vai entrar no commit.
3. `git log -3 --oneline` — conferir estilo do histórico do repo.
4. `git add <arquivos-específicos>` — nunca `git add .` quando há outras frentes dirty.
5. Mensagem citando `T-<MOD>-NNN` ou contexto da mudança.

**Operações git pró-ativas** (agente FAZ sem pedir permissão — INV-AGENT-004):
- `git push origin <branch>` em fast-forward (não force).
- `gh pr create`, `gh pr comment`, `gh pr view`, `gh pr checks`.
- `gh issue create`, `gh issue comment`, `gh issue close`.
- `gh release create`, `gh release view`, `gh release upload`.
- `gh repo view`, `gh repo edit --add-topic`, `gh repo set-default`.
- `git revert <sha>` (cria commit reverso, seguro) em vez de `git reset --hard` em remoto.

**Flags proibidas / restritas** (ver INV-AGENT-002):
- `--no-verify` em qualquer commit ou push: PROIBIDO sem exceção.
- `--force` (`-f`) puro em qualquer branch: PROIBIDO sem exceção.
- `--force-with-lease` em `main`/`master`/`release/*`: PROIBIDO. Em branch própria (feature/fix): exige `.claude/.override-reason` registrado.
- `git reset --hard` em ref remota (`origin/*`): PROIBIDO. Em ref local: exige `.claude/.override-reason`.

**Caminhos com espaço (importante em git bash no Windows):** sempre entre aspas duplas — `cd "C:/PROJETOS/Modelo projeto novo"`, nunca `cd $VAR` sem aspas.

## 8. Convenções
- Idioma: pt-BR (herdado do frontmatter; alterar só se projeto for explicitamente bilíngue/EN).
- Ver [`docs/CONVENCOES-DOC.md`](./docs/CONVENCOES-DOC.md).

## 9. Segurança/dados

> **Se tipo de projeto for CLI/lib/OSS sem dados pessoais, marcar todos os campos abaixo como `N/A` sem perguntar.** Só investigar se for SaaS multi-tenant ou app que trata dados de terceiros (detectável pelo contexto/manifestos/README).

- Multi-tenant: <RLS|schema|tenant_id|N/A>.
- Secrets: <onde|cadência rotação>.
- WORM: <quais entidades>.
- PII em logs: PROIBIDO (ver INV-AGENT-008).

## 10. ADRs ativas

ADRs vivem em [`docs/adr/ADR-NNNN-<slug>.md`](./docs/adr/). Status válidos: `proposta | aceita | substituida | deprecada`.

| # | Tema | Arquivo | Status | Bloqueia fase | Depende de |
|---|---|---|---|---|---|
| 0000 | Uso de IA | [`docs/adr/ADR-0000-uso-de-ia.md`](./docs/adr/ADR-0000-uso-de-ia.md) | aceita | — | — |
| 0001 | Stack | [`docs/adr/ADR-0001-stack.md`](./docs/adr/ADR-0001-stack.md) | aceita | — | — |

## 11. Pendências (GATEs)
<!-- vazio até que o dono ou o agente identifique o primeiro gate real. Não perguntar; manter "_(nenhum gate ativo)_" se nada definido. -->
_(nenhum gate ativo)_

## 12. ROPA / LGPD

> **Se a aplicação NÃO trata PII de pessoa física no Brasil (CLI offline, lib utilitária OSS, ferramenta dev interna sem cadastro de cliente), substituir esta seção inteira por:** `_Não aplicável — projeto não trata PII (LGPD Art. 37). Reavaliar se entrar fluxo com dado de pessoa física brasileira._` **Não perguntar ao dono.**

Quando aplica:

- Template: [`templates/ropa.template.md`](./templates/ropa.template.md) → copiar para `docs/conformidade/lgpd/ropa.md`.
- Encarregado (DPO): <nome ou "ainda não designado">.
- Base legal padrão para clientes: <execução de contrato | consentimento | legítimo interesse>.
- Retenção: ver tabela em `docs/conformidade/lgpd/ropa.md` + `docs/conformidade/lgpd/retencao-dados.md`.
- Direitos do titular (acesso, correção, eliminação, portabilidade): canal em <e-mail ou rota>.
- Incidente de segurança: ver `docs/conformidade/lgpd/plano-incidente.md`; comunicação à ANPD em até 2 dias úteis.

PII em logs/prints é proibido (INV-AGENT-008). Mascarar/tokenizar antes de logar.

## 13. Pró-atividade e autorização

O agente IA opera com pró-atividade ampla. Ver INV-AGENT-004.

### 13.1 Matriz de decisão (regra mestre — 2×2)

|                          | **Reversível** (rollback fácil)               | **Irreversível** (sem rollback)              |
|--------------------------|------------------------------------------------|----------------------------------------------|
| **Custo zero**           | **FAZ sem perguntar**, reporta no fim          | **CONFIRMA antes** (toda ação irreversível)  |
| **Custo > 0** (R$/SaaS)  | FAZ sem perguntar se < limiar do projeto       | **CONFIRMA antes** (sempre)                  |

Regra única: **se reversível E sem custo, faz. Caso contrário, confirma.** As listas abaixo são EXEMPLOS, não exaustivas — diante de uma ação nova, aplicar a matriz.

### 13.2 Exemplos — FAZ sem perguntar (reversível + custo zero)

- Editar/criar/atualizar arquivos, configs, docs, memórias.
- Rodar testes, lint, build, type-check, auditores locais.
- Criar branch, commit atômico, abrir PR via `gh pr create`.
- Criar issue, comentar em PR via `gh issue create`, `gh pr comment`.
- `git push origin <branch>` em fast-forward (não force) em branch própria.
- `gh release create` / `gh release delete` (release é revertível).
- `gh repo edit --add-topic`, atualizar README, adicionar badges.
- `git checkout -- <arquivo>`, `git restore -- <arquivo>` (descarte de unstaged é recuperável via reflog/IDE).
- `git stash`, `git stash pop`, `git stash drop` (recuperável via reflog).
- `git revert <sha>` (cria commit reverso — preferir a reset).
- Rotação programada de credencial dentro da janela do runbook (compliance contínuo automatizado; notifica depois).
- Aplicar correções identificadas em auditoria.
- Continuar o próximo passo lógico de qualquer sequência iniciada (sem perguntar "posso continuar?").

### 13.3 Exemplos — EXIGE confirmação humana (irreversível OU custo > 0)

- `npm publish`, `cargo publish`, `pypi upload` (versão pública não rebobina).
- `drop table`, `truncate`, migration destrutiva (`DROP COLUMN`, etc.).
- `git push --force` puro / `git push --force-with-lease` em `main`/`master`/`release/*`.
- `git reset --hard origin/<remote>` ou `git reset --hard <sha-antigo>` (perda real de trabalho).
- `git branch -D` em branch compartilhada ou já mergeada em remoto.
- Deletar dado de produção (INV-AGENT-001).
- Rotação de credencial **fora de janela** ou **por incidente** (não programada).
- Restaurar backup sobre produção.
- Gasto financeiro (compra de domínio, plano de serviço, API paga).
- Mudança de visibilidade do repositório (público ↔ privado).
- Apagar repositório.
- Operações que exigem 2FA do dono.

### 13.4 Antídoto contra regressão a "perguntar a cada passo"

**Antes de escrever** `"Quer que eu...?"`, `"Posso fazer X?"`, `"Devo continuar?"`, `"Prefere A ou B?"` — pare. Cheque a matriz §13.1. Se a ação é reversível E sem custo, FAÇA e reporte. Use `AskUserQuestion` apenas para ambiguidade real de produto (não para autorização de ação técnica reversível).

Qualquer override desta política exige entrada em `docs/governanca/override-ledger.md`.
