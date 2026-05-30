---
owner: roldao
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 150
proposito: adendo específico do Claude Code que aponta para o contrato canônico AGENTS.md
---

<!--
template: CLAUDE.md
uso: copiar para a raiz do repositório.
escopo: adendo específico do harness Claude Code. Tudo que é canônico de produto/processo fica em AGENTS.md.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C0
limite: ≤150 linhas.
ordem: frontmatter → este HTML comment → corpo.
-->

@AGENTS.md

# CLAUDE.md — Aferê Prumo

> **Hierarquia de contratos**: reafirmada no cabeçalho dos 4 contratos (AGENTS.md, REGRAS-INEGOCIAVEIS.md, constitution.md e este), com [`.claude/memory/constitution.md`](./.claude/memory/constitution.md) como autoridade máxima. Este arquivo é o **mais específico** (canal Claude Code) e o **mais fácil de mudar**; em qualquer conflito, perde para AGENTS.md, REGRAS-INEGOCIAVEIS.md e constitution.md.

## 1. Perfil do usuário e linguagem

O dono do projeto **não programa**. É idealizador/dono de produto, não desenvolvedor. Conhece o produto melhor que ninguém, mas não lê código nem stack trace.

**Antes de perguntar qualquer coisa, cheque:** a ação é reversível E sem custo? Se sim, FAÇA e reporte. Não escrever `"Quer que eu...?"` / `"Posso fazer X?"` para autorização de ação técnica reversível — use a matriz §13.1 do `AGENTS.md`.

Regra de linguagem e tabela de tradução de jargão: ver **INV-AGENT-010** em [`REGRAS-INEGOCIAVEIS.md`](./REGRAS-INEGOCIAVEIS.md).
Regra de pró-atividade: ver **INV-AGENT-004** em [`REGRAS-INEGOCIAVEIS.md`](./REGRAS-INEGOCIAVEIS.md).

## 2. Regra de investigação antes de editar

Ver **INV-AGENT-003** em [`REGRAS-INEGOCIAVEIS.md`](./REGRAS-INEGOCIAVEIS.md).

## 3. Idioma do canal

> **Defaults (não perguntar — sobrescrever só se diferente):**

- Conversar em **pt-BR**.
- Código, identificadores e nomes de arquivo em **inglês**.
- Mensagens de commit em **pt-BR**.

## 4. Estado do ambiente

> **Defaults para o ambiente do dono Roldão (Windows 11 + Git Bash). Detectar do contexto real do projeto e ajustar; não perguntar.**

| Item | Valor padrão |
|---|---|
| Sistema operacional padrão | Windows 11 |
| Shell | bash (Git for Windows ≥ 2.40) |
| Gerenciador de pacotes | detectar do manifesto (npm/pnpm/yarn/cargo/pip/poetry/uv) |
| Versão da runtime | última LTS estável do ecossistema |
| Banco local | detectar (SQLite local / Postgres docker / ...) |

## 5. Notas de plataforma

- **Windows + Git Bash (default do dono):**
  - Usar `/` em paths, nunca `\`.
  - `NUL` não existe no bash — usar `/dev/null`.
  - **Caminhos com espaço sempre entre aspas duplas** — `cd "C:/PROJETOS/Modelo projeto novo"`, nunca `cd $VAR` solto. Hooks usam `bash "$CLAUDE_PROJECT_DIR/..."` corretamente.
  - `CRLF` vs `LF`: forçar LF via `.gitattributes` (`* text=auto eol=lf`).
  - Configurar Claude Code para usar bash de `C:\Program Files\Git\bin\bash.exe` (env var `CLAUDE_CODE_BASH_PATH` no Windows).
  - Hooks shell assumem `bash ≥ 4` (Git for Windows ≥ 2.40 inclui) + GNU coreutils (`date -d` em `hook-check-deps.sh` detecta BusyBox/macOS antigo e cai em `python3` fallback).
- **macOS:** `sed -i` exige sufixo (`sed -i ''`).
- **Linux:** pacotes de sistema podem precisar de `sudo` — sempre pedir confirmação.

## 6. O que NÃO repetir aqui

Itens já cobertos em outros contratos. **Não duplicar — referenciar**:

- Política de commits (atômicos, sem `--no-verify`, sem `--force` em main). → `REGRAS-INEGOCIAVEIS.md` INV-AGENT-002, INV-AGENT-007.
- Stack, comandos canônicos, ADRs ativas. → `AGENTS.md §2, §6, §10`.
- Invariantes de produto/agente (INV-NNN, INV-AGENT-NNN). → `REGRAS-INEGOCIAVEIS.md`.
- Princípios fundadores. → `constitution.md`.
- Fluxo de PR/auditor/quality gate. → `CONTRIBUTING.md`.
- Glossário de termos do domínio. → `docs/glossario.md`.

<!-- Se sentir vontade de copiar conteúdo dos arquivos acima pra cá, PARE.
     Adicione referência, não cópia. CLAUDE.md fala só do que é específico do harness Claude Code. -->
