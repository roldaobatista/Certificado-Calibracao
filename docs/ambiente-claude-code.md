# Estudo: ambiente Claude Code antes de qualquer linha de código

> **Versão 3** — passou por auditoria de 5 agentes isolados (fatos, omissões, ordem, Windows/segurança, coerência) e por um 6º agente cirúrgico que fechou os 4 pontos duvidosos. Achados aplicados no corpo do texto.
>
> Histórico de versões:
> - v1: estudo inicial baseado em 10 agentes pesquisando a doc oficial.
> - v2: auditoria por 5 agentes isolados; correções de fato, omissões, ordem, Windows e coerência.
> - v3: agente cirúrgico fechou os 4 TODOs. Resultado abaixo.

---

## 1. A ideia central (em 3 frases)

O Claude Code é um agente que **lê 4 a 6 arquivos toda vez que abre uma sessão** e usa o que está neles pra decidir como agir. Se esses arquivos estiverem bem feitos, ele acerta de primeira; se estiverem ausentes, vagos ou contraditórios, ele inventa, esquece e refaz trabalho. **Investir no ambiente antes de escrever produto é o que separa "ferramenta que ajuda" de "ferramenta que entrega sozinha".**

**Importante (correção aplicada após auditoria):** o Claude Code lê apenas `CLAUDE.md` automaticamente. `AGENTS.md` **só é lido se for explicitamente importado** com a sintaxe `@AGENTS.md` dentro do `CLAUDE.md`. Não é "automático" entre as duas ferramentas — precisa do import.

---

## 2. Árvore de arquivos (inventário-alvo vs. MVP inicial)

> **Distinção crítica:** a árvore abaixo é o **estado-alvo** depois que o projeto amadurecer. O **MVP inicial** (seção 4) é bem menor. Não criar tudo de uma vez.

```
Certificado de calibracao/
├── AGENTS.md                          ← contrato canônico (Claude + Codex), só lido via @import
├── CLAUDE.md                          ← contrato Claude Code (importa AGENTS.md)
├── CLAUDE.local.md                    ← memória pessoal, NÃO versionar
├── .gitignore                         ← inclui regras Claude
├── .mcp.json                          ← servidores MCP do projeto
├── .claude/
│   ├── settings.json                  ← permissões + hooks (versionado)
│   ├── settings.local.json            ← pessoal, segredos (NÃO versionar)
│   ├── agents/                        ← subagentes especialistas (.md)
│   ├── commands/                      ← atalhos /comando (.md) — legado; novo padrão é skills
│   ├── skills/                        ← procedimentos repetíveis (substituem commands)
│   │   └── <nome>/SKILL.md
│   ├── hooks/                         ← scripts bash de automação
│   ├── output-styles/                 ← CONFIRMADO: pasta com arquivos .md, frontmatter name+description. Built-in: Default, Proactive, Explanatory, Learning
│   └── rules/                         ← regras por pasta
│       ├── <nome>.md                  ← sem `paths:` → carrega em todo turno (eager)
│       └── <nome>.md                  ← com `paths: [src/**/*.ts]` → só carrega ao tocar arquivos match (lazy)
├── .claude-plugin/                    ← OPCIONAL: empacotar agents+skills+hooks como plugin reutilizável
│   └── plugin.json
├── docs/
│   ├── arquitetura.md
│   ├── roadmap.md
│   └── runbooks/
└── README.md
```

A pasta `memory/` (memória pessoal acumulada gerada pelo próprio Claude) **fica fora do repositório**, em `~/.claude/projects/<projeto>/memory/`. Cada máquina tem a sua.

---

## 3. Detalhamento das 10 frentes

### Frente 0 (NOVA) — Decidir e registrar a stack técnica

> Adicionada após auditoria: a doc oficial implicitamente assume que você sabe a stack ao criar AGENTS.md. Sem isso, todo o resto fica genérico.

**Antes de criar qualquer arquivo:** decidir e registrar (no próprio AGENTS.md) — linguagem(ns), runtime, banco, framework UI, ferramenta de build, formato de testes, formato de migrations. Sem essa decisão registrada, hooks, skills e MCP servers serão genéricos demais.

---

### Frente 1 — `CLAUDE.md` (contrato específico Claude Code)

**Onde:** raiz do projeto.
**Por que importa:** é lido em todo turno de conversa. É o **único arquivo de memória** que o Claude Code lê automaticamente. `AGENTS.md` só entra via import.
**Tamanho-alvo:** **100-150 linhas**. Passou de 180, mover regras técnicas pra `.claude/rules/*.md` com `paths:` frontmatter (lazy load — só carrega ao tocar arquivos correspondentes).
**Estratégia recomendada:** CLAUDE.md fino que começa com `@AGENTS.md` e só adiciona o que é específico do Claude Code (memória automática, skills, hooks, regras de jargão pro Roldão).

**Hierarquia de CLAUDE.md (importante — corrigido após auditoria):**
- **Memória COMBINA, não sobrescreve.** Todos os CLAUDE.md em cascata são lidos juntos:
  - `~/.claude/CLAUDE.md` (global pessoal)
  - `CLAUDE.md` na raiz do repositório
  - `CLAUDE.md` em subpastas (carregam só ao tocar arquivos da subpasta — lazy)
  - `CLAUDE.local.md` (pessoal, não versionado)

**Seções mínimas do CLAUDE.md:**
- Descrição do produto em 1-2 linhas
- `@AGENTS.md` (import)
- Perfil do usuário (Roldão — não programa, linguagem traduzida obrigatória)
- Regra de investigar antes de mexer
- O que confirmar antes vs. o que fazer direto

---

### Frente 2 — `AGENTS.md` (contrato canônico, compartilhado)

**Onde:** raiz do projeto, **versionado**.
**Por que importa:** padrão aberto compatível com Claude Code, Codex CLI e outras ferramentas — **desde que cada ferramenta o importe explicitamente**. Pro Claude Code, isso significa ter `@AGENTS.md` no CLAUDE.md.
**Conteúdo:** stack técnica, comandos (instalar/build/testar/conferir), convenções, política de commits, segurança, pontos de extensão.
**Em monorepo:** `AGENTS.md` raiz + `apps/*/AGENTS.md` quando uma pasta tem regras próprias.
**Pegadinha:** drift entre AGENTS.md e CLAUDE.md. Mitigação: manter regras técnicas só no AGENTS.md; CLAUDE.md fica com o que é específico Claude Code (perfil do Roldão, regra de jargão, regra de investigar).

---

### Frente 3 — Subagentes (`.claude/agents/`)

**O que são:** especialistas com **contexto isolado**, prompt próprio e ferramentas restritas. Quando algo bate com a descrição deles, o Claude principal delega — o subagente trabalha, devolve só o resumo, e o contexto do principal fica limpo.
**Quando criar:** quando a tarefa **polui muito contexto** (logs grandes, varreduras, análises pesadas).

**Inventário-alvo (futuro, sob demanda):**

| Subagente | Quando dispara | Ferramentas | Modelo |
|---|---|---|---|
| code-reviewer | após editar código crítico | Read, Grep, Glob, Bash | sonnet |
| test-runner | "rodar testes" / falhas em CI | Bash, Read | haiku |
| security-auditor | quando análise ficar pesada (logs/varreduras) | Read, Grep, Glob, Bash | opus |
| doc-writer | "escreve documentação de X" | Write, Read | sonnet |
| performance-profiler | "otimiza isso" | Bash, Read, Grep | sonnet |

**Removidos do inventário após auditoria (eram redundância):**
- ~~db-migration-reviewer~~ → coberto pela skill `db-migration`
- ~~dependency-auditor~~ → vira slash command quando padrão se repetir
- ~~ux-copy-reviewer~~ → vira slash command quando padrão se repetir

**Pegadinha:** descrição vaga = o Claude não delega. Sempre começar com **gatilho concreto**: "Use após X", "Use quando Y".

---

### Frente 4 — Slash commands (`.claude/commands/`) — legado

**Status (corrigido após auditoria):** a doc oficial menciona que slash commands foram **mesclados em skills**. Arquivos antigos em `.claude/commands/` continuam funcionando, mas o padrão novo é criar como skill (`.claude/skills/<nome>/SKILL.md`). Resultado é o mesmo — `/comando` funciona em ambos.

**Recomendação:** criar tudo novo como **skill**. Manter `.claude/commands/` só pra compatibilidade se já existir.

---

### Frente 5 — Hooks (`.claude/hooks/` + `.claude/settings.json`)

**O que são:** scripts shell executados automaticamente em pontos do ciclo de vida. Podem **bloquear** ações saindo com código 2.

**Eventos disponíveis (lista completa corrigida após auditoria):**
- `SessionStart`, `SessionEnd`
- `Setup`
- `UserPromptSubmit`, `UserPromptExpansion`
- `PreToolUse`, `PostToolUse`, `PostToolUseFailure`
- `PermissionRequest`
- `Stop`, `StopFailure`
- `PreCompact`, `PostCompact`
- `InstructionsLoaded` (útil pra debugar quais regras carregaram)
- `Notification`

**Tipos de hook handler (corrigido após auditoria):** além de comando shell, a doc lista HTTP, MCP Tool, Prompt e Agent. Pra projeto novo, ficar com Command (bash) é suficiente.

**Hooks essenciais (MVP):**

| Hook | Evento | O que faz |
|---|---|---|
| block-destructive | PreToolUse(Bash) | Bloqueia `rm -rf*`, `git push --force*`, `drop table`, `git reset --hard` |
| secrets-scanner | PreToolUse(Write) | Bloqueia gravação de `.env`, credenciais, chaves |
| session-start | SessionStart | Mostra branch ativa, git status, tarefas pendentes |

**Hooks de luxo (depois):** `quality-gates` (lint+format em PostToolUse), `audit-log`, `commit-lint`.

**Atenção Windows + bash (corrigido após auditoria):**
- A stack é Windows 11 + Git Bash. `chmod +x` não é confiável — sempre invocar via `bash script.sh`.
- **`jq` não vem no Git Bash padrão.** Hooks que precisam parsear JSON devem usar bash puro ou `python -m json.tool`. Se quiser usar `jq`, listar como pré-requisito explícito.
- **Path com espaços** (`C:\PROJETOS\Certificado de calibracao`): toda referência a `${CLAUDE_PROJECT_DIR}` em hook deve estar entre aspas duplas: `"${CLAUDE_PROJECT_DIR}"`.
- Se Git Bash não estiver em `C:\Program Files\Git\bin\bash.exe`, setar `CLAUDE_CODE_GIT_BASH_PATH` em `~/.claude/settings.json`.
- Não escrever no stdout — polui o JSON que o Claude espera. Redirecionar erros pra stderr (`>&2`).
- **Testar todo hook manualmente antes** de plugar: `echo '{}' | bash .claude/hooks/script.sh`. Hook bugado trava a sessão.
- **Sandboxing não suportado em Windows nativo** (só WSL2). Limitação a aceitar.

---

### Frente 6 — MCP servers (`.mcp.json`)

**O que é:** Model Context Protocol — conecta o Claude Code a sistemas externos (GitHub, banco, Sentry, Slack, Playwright). Tools do MCP são **carregadas sob demanda** (schema completo só quando usado) — economiza contexto.

**Inventário inicial recomendado:**

| Servidor | Pra quê | Escopo | Risco |
|---|---|---|---|
| github | PRs, issues, code review | projeto (versionado) | baixo |
| filesystem | navegação ampla de arquivos | projeto | baixo |
| playwright | testes E2E e automação de navegador | projeto | médio |
| postgres / sqlite | consultar banco read-only | local (segredos) | alto se write |
| sentry | erros em produção | local | médio |
| context7 | docs atualizadas de bibliotecas | **projeto** (corrigido — é ferramenta do time, não pessoal) | baixo |

**Pegadinha:** chave de API **nunca** em `.mcp.json` versionado — usar `${VAR}` e `.env` local. No Windows, exportar a variável no shell que vai rodar o Claude Code (Git Bash usa `export VAR=...`; PowerShell usa `$env:VAR = ...`).

---

### Frente 7 — Settings & permissões

**Hierarquia (corrigida após auditoria):** **Managed** → **CLI args** → **Local** → **Project** → **User**.

> **Lógica IMPORTANTE (corrigido após auditoria):** memória (`CLAUDE.md`) **combina** todos os níveis em cascata. Settings (`.claude/settings.json`) **sobrescreve** em cascata — quem está mais alto na hierarquia ganha. São duas lógicas diferentes.

**O que vai onde:**

| Arquivo | Conteúdo | Versionar? |
|---|---|---|
| `~/.claude/settings.json` | Preferências globais (modelo, idioma, estilo) | Não (é pessoal) |
| `.claude/settings.json` | Permissões do projeto, hooks, MCP habilitados | **Sim** |
| `.claude/settings.local.json` | Tokens, paths absolutos, preferência pessoal | **Não** (entra no `.gitignore`) |

**Modos de permissão:**
- `default` — pergunta antes de cada ação sensível
- `acceptEdits` — aprova edições automaticamente, só pergunta em shell
- `plan` — só lê e propõe, espera aprovação
- `auto` — modo automático
- `dontAsk` — não pergunta (cuidado)
- `bypassPermissions` — **nunca use** em projeto compartilhado

**Atenção (descoberta em v3):** `permissions.defaultMode` **NÃO É CAMPO VÁLIDO** em `settings.json`. A doc só lista `permissions.allow`, `permissions.deny`, `permissions.ask`. Pra forçar um modo, usar CLI: `claude --permission-mode plan` (ou similar). Em settings.json, controlar comportamento via allow/deny granulares.

**Allowlist recomendada inicial** (`permissions.allow`): `git status`, `git diff`, `git log`, `npm run lint`, `npm run test`, `npm run build`, `ls`, `node -v`.

**Denylist recomendada** (`permissions.deny`):
- `Bash(rm -rf*)` (matcher amplo, não só `/`)
- `Bash(rm -fr*)`
- `Bash(curl * | bash*)`
- `Bash(git push --force*)`
- `Bash(git push -f*)`
- `Bash(chmod 777*)`
- `Read(.env*)`, `Read(secrets/**)`, `Read(~/.ssh/**)`

**Campos confirmados na doc (v3):** `enableAllProjectMcpServers` (boolean), `autoMemoryEnabled` (boolean, default true), `autoMemoryDirectory` (path), `effortLevel` ("low"/"medium"/"high"/"xhigh"), `statusLine` (object), `editorMode` ("normal"/"vim"), `tui` ("fullscreen"/"default"), `language` (string), `model` (string com ID do modelo).

**Campos que NÃO existem (v3):** `permissions.defaultMode`, `apiKeyHelper`. Se aparecerem em algum exemplo, ignorar.

---

### Frente 8 — Skills (`.claude/skills/<nome>/SKILL.md`)

**O que são:** procedimentos repetíveis. Substituem slash commands. Podem carregar arquivos auxiliares sob demanda. O Claude **decide sozinho** quando invocar com base na descrição.

**Inventário-alvo (futuro):**

| Skill | Quando dispara |
|---|---|
| release-checklist | Pronto pra subir versão pro cliente |
| fix-broken-tests | Diagnosticar falha em teste |
| db-migration | Gerar ou revisar mudança no banco |
| security-review | Análise de segurança antes de release |
| simplify-changes | Revisar mudança procurando complexidade desnecessária |

**Pegadinha (mesma da Frente 3):** se já existe skill `security-review`, **não** criar subagente `security-auditor` paralelo — duplicação confunde o Claude.

---

### Frente 9 — Personalização da experiência

| Item | Onde | Recomendação (revisada após auditoria) |
|---|---|---|
| **Output style** | `.claude/output-styles/<nome>.md` (pasta confirmada em v3) com frontmatter `name` + `description`. Built-in disponíveis: Default, Proactive, Explanatory, Learning. Trocar via `/config` | Criar um único estilo PT-BR sem jargão |
| **Statusline** | `~/.claude/settings.json` campo `statusLine` | Opcional; ligar se ajudar visualizar modelo/branch (recomendação original "desligar" era opinião sem base na doc) |
| **Plan mode** | `Shift+Tab` ou `defaultMode: "plan"` | **Recomendado como default pro Roldão** (perfil não-técnico + regra "investigar antes de mexer" do CLAUDE.md global = plan mode é o casamento natural). Recomendação original "opt-in" contradiz o próprio perfil do usuário. |
| **Modelo** | `model` em settings | **Sonnet** como padrão; `/model opus` em arquitetura/segurança; haiku em varreduras |
| **Keybindings** | `~/.claude/keybindings.json` | Deixar defaults; customizar só se sentir falta |

---

### Frente 10 — Memória, contexto, worktrees, automação

**Memória persistente:**
- `CLAUDE.md` = instruções que você escreve e **sempre carregam**
- `CLAUDE.local.md` = memória pessoal, não versionada (análogo a `settings.local.json`)
- `~/.claude/projects/<projeto>/memory/` = aprendizados que o Claude grava sozinho. **Não versionar** — é por máquina
- **Comando `#` NÃO existe** (descoberto em v3 — o agente verificou a tabela completa de comandos da doc oficial). Pra gerenciar memória, usar `/memory` (abre editor).

**Gestão de contexto:** `/context`, `/compact`, `/clear`.

**Worktrees:** `EnterWorktree`/`ExitWorktree` ou parâmetro `isolation: "worktree"` ao delegar pra agente. Arquivo `.worktreeinclude` na raiz copia automaticamente arquivos ignorados (como `.env`) pra cada worktree novo.

**Background tasks:** `run_in_background: true` em Bash e Agent — não bloqueia.

**Routines (cloud, em preview):** tarefas agendadas que rodam na infra da Anthropic, com triggers de schedule/GitHub/API. Útil pra checks diários (status de PRs, monitorar deploy) sem precisar abrir sessão. Confirmar disponibilidade na sua versão.

**Modo headless / CI** (NOVO, após auditoria): `claude --print "prompt"` ou `claude -p` permite chamar o Claude Code dentro de scripts e GitHub Actions. Útil pra automação não-interativa.

---

### Frente 11 (NOVA) — Plugins

> Adicionada após auditoria. Auditor 2 apontou que plugins são o mecanismo oficial pra empacotar+compartilhar conjunto (agents+skills+hooks+commands) entre projetos.

**O que é:** um plugin = pasta `.claude-plugin/` com `plugin.json` declarando o que oferece (agents, skills, hooks, MCP servers, commands com namespace `plugin:nome`).

**Quando criar:** depois que o projeto amadurecer e você quiser reusar a configuração em outro projeto, ou compartilhar com time/cliente. Não é necessário pra começar.

**Distribuição:** via marketplace oficial ou repositório git.

---

## 4. Ordem revisada de execução (após auditoria)

> Mudanças vs. plano original: adicionado passo zero (stack), adicionado `/init`, MCP movido pra antes dos agentes, hooks com nota explícita de teste manual, validação do ambiente no fim.

Antes de qualquer código de produto:

0. **Decidir e registrar stack técnica** (linguagem, runtime, banco, UI, build, testes) — passa direto pro AGENTS.md
1. **`.gitignore`** com regras Claude (`.claude/settings.local.json`, `CLAUDE.local.md`, `.env*`, `secrets/`, `.claude/.credentials.json`, `.claude/logs/`)
2. **`AGENTS.md`** raiz — define stack, comandos, convenções (baseado na decisão do passo 0)
3. **Rodar `/init`** dentro de uma sessão Claude Code — gera CLAUDE.md base scaneando o repo
4. **Refinar `CLAUDE.md`** — adicionar `@AGENTS.md`, perfil do Roldão, regra de investigar antes de mexer, regra de jargão traduzido
5. **`.claude/settings.json`** com permissões mínimas + denylist robusta. (NOTA: `defaultMode` é campo INVÁLIDO conforme v3 desta auditoria; pra usar plan mode como padrão, ativar via `Shift+Tab` na sessão ou CLI `claude --permission-mode plan` — não via settings.json.)
6. **`.claude/hooks/`**: criar `block-destructive.sh` e `secrets-scanner.sh`. **Testar cada um manualmente** com `echo '{}' | bash .claude/hooks/script.sh` antes de plugar no settings.json
7. **`.mcp.json`** com 2-3 servidores essenciais (filesystem, github quando tiver token, playwright se for usar testes E2E)
8. **Validar ambiente:** rodar `claude mcp list`, `/permissions`, `/hooks` (se existirem) pra conferir tudo plugado
9. **`.claude/agents/`** — só quando primeiro padrão repetir 3 vezes. Começar pelo `code-reviewer` ou `test-runner`
10. **`.claude/skills/`** — só quando primeiro padrão repetir 3 vezes. Começar por `release-checklist`
11. **Output style** — opcional, pra padronizar tom em PT-BR
12. **Plugins** — só quando quiser empacotar tudo pra reusar em outro projeto

Só depois disso, abrir o primeiro arquivo de produto.

---

## 5. Armadilhas universais (consolidadas após auditoria)

> Antes havia "pegadinhas" nas frentes + "armadilhas" no fim, com sobreposição. Consolidado abaixo.

1. **`CLAUDE.md` gigante** — alvo 100-150 linhas. Passou de 180, mover regras técnicas pra `.claude/rules/*.md` com frontmatter `paths:` (lazy load).
2. **`.claude/rules/` sem `paths:` frontmatter** — carrega em todo turno (eager) e queima contexto à toa. Sempre escopar com `paths:`.
3. **Permissão `Bash(*)`** — equivale a entregar a máquina. Sempre granular: `Bash(npm run *)`.
4. **`bypassPermissions` em repo compartilhado** — bloqueia revisão e expõe a equipe.
5. **Segredo versionado** — token em `settings.local.json` ou `.mcp.json` sem `${VAR}`.
6. **Descrição vaga em agente/skill** — vira código morto. Sempre começar com gatilho concreto.
7. **Drift entre AGENTS.md e CLAUDE.md** — manter AGENTS.md como única fonte de regras técnicas; CLAUDE.md só com Claude-específicos.
8. **Hooks lentos** — todo turno atrasa. Cada hook deve ser sub-segundo idealmente.
9. **Hook não testado manualmente** — hook quebrado trava toda a sessão. Sempre rodar com input de teste antes de plugar.
10. **Hooks dependem de `jq` em Windows** — `jq` não vem no Git Bash. Usar bash puro ou Python; ou listar como pré-requisito.
11. **Path com espaços sem aspas** em hook — quebra silenciosamente em Windows. Sempre `"${CLAUDE_PROJECT_DIR}"`.
12. **Denylist com matcher específico demais** — `Bash(rm -rf /*)` não pega `rm -rf C:/foo`. Usar `Bash(rm -rf*)`.
13. **Pasta `.claude/` fora do git** — perde todo o investimento em hooks/agents/skills se trocar de máquina.
14. **Inventário inflado** — 8 agentes + 5 skills + 6 commands desde o dia 1. Começar com **2-3 no total** e crescer só por necessidade real.
15. **Redundância subagente vs skill** — não criar `security-auditor` (subagente) E `security-review` (skill). Escolher um.

---

## 6. Próximo passo concreto

Posso começar criando, nessa ordem revisada:

1. `.gitignore` com regras Claude
2. `AGENTS.md` (stack cravada na ADR-0001 como candidata: **Django + Flutter + PostgreSQL** — vira definitiva após 3 portões)
3. `CLAUDE.md` enxuto com `@AGENTS.md` + perfil do Roldão + regra de investigar
4. `.claude/settings.json` com permissões seguras + `defaultMode: "plan"` + denylist robusta
5. 2 hooks essenciais em bash puro (sem `jq`), testados manualmente antes
6. Validar ambiente (`claude mcp list`, etc.)

Camadas seguintes (MCP servers, agentes, skills) entram só quando o primeiro padrão se repetir.

---

## Notas de auditoria (rastro)

Esta versão 2 incorpora achados de 5 auditores isolados que checaram o plano original contra https://code.claude.com/docs/en/overview:

- **v2 — Fatos/alucinações**: corrigida hierarquia de settings, modos de permissão, eventos de hook, esclarecimento sobre `AGENTS.md` precisar de `@import`
- **v2 — Omissões**: adicionados `/init`, Plugins, Routines, modo headless, `paths:` em rules, validação de ambiente, `CLAUDE.local.md`, decisão de stack como passo zero
- **v2 — Ordem**: ordem revisada com 13 passos, validação de ambiente no fim
- **v2 — Windows/segurança**: `jq` ausente, paths com espaços, `CLAUDE_CODE_GIT_BASH_PATH`, denylist com matchers amplos, sandboxing limitação WSL2
- **v2 — Coerência**: inventários enxugados, `context7` movido pra escopo project, statusline neutralizado, pegadinhas e armadilhas consolidadas
- **v3 — TODOs fechados**: comando `#` confirmado como **inexistente** (remover); `enableAllProjectMcpServers` validado como real; `.claude/output-styles/` confirmado como pasta de `.md` com frontmatter `name`+`description` e 4 estilos built-in (Default, Proactive, Explanatory, Learning); `permissions.defaultMode` e `apiKeyHelper` identificados como **campos inválidos** que não existem na doc (não usar).
