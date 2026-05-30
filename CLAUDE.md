# Contrato Claude Code — projeto

@AGENTS.md

> **Status (2026-05-29):** 7 Foundations/Marcos FECHADOS (F-A, F-B, M1, M2, F-C1, M3 OS, M4 calibração) + SAN-PERFIL-TENANT Sprints 1-4 FECHADOS (ADR-0067). **Wave A arrancada — M5 `metrologia/padroes` em curso (P1-P7 entregues).** ADRs ativas 0000..0072 (0059/0060/0061 reservadas; M5 acrescentou 0070 carta Shewhart híbrida + 0071 2 implementações cl. 7.11 + 0072 path aninhado). 58 hooks ativos / 474 casos verdes em `_test-runner` (+4 M5 padroes P7; +3 M6 escopos-cmc P7). Suite M4 chave 629/629; suite ampla regression+audit+M3+M4 exit 0 pós-saneamento. Auditoria 10 lentes pré-Wave A em execução (`docs/faseamento/auditorias/PRE-WAVE-A-CONSOLIDADO-rodada-1.md` — 5 ondas, ~150 achados). Este arquivo é adendo do harness Claude Code; produto/arquitetura ficam em `AGENTS.md` (importado acima).

---

## Perfil do usuário (CRÍTICO — ler sempre)

**Roldão NÃO programa.** É dono/idealizador de produto, não desenvolvedor. A regra abaixo vale em qualquer interação:

### Linguagem obrigatória
- **NUNCA usar jargão técnico** sem traduzir.
- **Tabela de tradução:**
  - "salvei a correção no sistema" em vez de "fiz commit/push"
  - "está funcionando, validei" em vez de "CI verde / testes passando"
  - "tem erro, vou investigar" em vez de "tests failing / build red"
  - "voltar pra versão anterior" em vez de "rollback / revert"
  - "subir pro servidor que o cliente usa" em vez de "deploy em produção"
  - "robô que simula o usuário" em vez de "E2E tests"
  - "reorganizar essa parte (sem mudar o que aparece pro usuário)" em vez de "refactor"
  - "mudança na estrutura dos dados salvos" em vez de "migration"
  - "dados falsos pros testes" em vez de "mock/fixture"
- Ao reportar erro: dizer **efeito visível** ("a tela X não carrega"), nunca stack trace cru.
- Ao terminar: dizer o que mudou na prática + se o cliente vai ver diferença.

### Pró-atividade total — NÃO perguntar permissão
- Ao identificar gap, erro, débito, bug ou inconsistência: **resolver imediatamente**, nunca perguntar "quer que eu corrija?".
- Ao terminar tarefa: NÃO perguntar "o que faço agora?" — seguir próximo passo lógico.
- Reportar SEMPRE no formato: "fiz X, resolvi Y, já comecei Z" (nunca "posso fazer Y?").
- **Confirmar antes APENAS para:** deletar dados de produção, drop table, rotação de credenciais, mudanças legais públicas, gastos com terceiros pagos, push --force, reset --hard, rm -rf, migration destrutiva.

---

## Regra #0 — Investigar antes de mexer em lógica de negócio

Quando o usuário reportar bug em comportamento (tela errada, cálculo errado, mensagem confusa, dado salvo errado):

1. **NÃO mexer no código antes de entender a causa.** Mudar template/UI sem investigar o que está nos dados já produziu 3 voltas em uma mesma sessão em projetos anteriores.
2. **Primeiro: ler o estado real.** Banco (`sqlite3` / SELECT direto), logs do app, payload de IPC, console do navegador, arquivo de configuração. O que está **salvo** lá?
3. **Segundo: rastrear o fluxo.** Onde o dado é gerado? Onde é salvo? Onde é lido? Existem dois caminhos ou builders duplicados?
4. **Terceiro: confirmar entendimento com o usuário antes de mudar** se houver ambiguidade. Uma pergunta curta economiza 10 idas e voltas.
5. **Só então: implementar.** E mexer no **ponto raiz** — não no sintoma. Se a flag está 0 no banco quando devia estar 1, conserte **onde a flag é gravada errada**. Não conserte mudando o template pra ignorar a flag.

---

## Idioma

Comunicar em **Português (Brasil)** por padrão.

---

## Estado do ambiente

Ambiente operacional, sem código de produto ainda. Discovery concluída; arquitetura cravada em ADRs; primeiro código depende de fechar Portão 1 (cliente externo) e definir PRD/faseamento do MVP-1.

**Arquivos canônicos:**
- `AGENTS.md` ✅ — fonte canônica de produto/arquitetura (importado no topo deste arquivo)
- `CLAUDE.md` ✅ — este arquivo; adendo do harness Claude Code
- `REGRAS-INEGOCIAVEIS.md` ✅ — IDs `INV-`, `INV-TENANT-`, `TST-`, `SEC-`, `INV-AGENT-`
- `CONTRIBUTING.md` ✅ — fluxo do agente
- `.specify/memory/constitution.md` ✅ — princípios não-negociáveis

**`.claude/` (versionado):**
- `settings.json` ✅ — permissões + hooks
- `hooks/` ✅ — **58 hooks ativos**, **474 casos** no `_test-runner` (lista completa em AGENTS §3; +3 do Marco 6 P7 escopos-cmc: escopo-rbc-perfil-a + escopo-cobre-fail-closed + escopo-extracao-nao-auto-persiste; +4 do Marco 5 P7 padroes: padrao-incertezas-so-via-recal + padrao-auxiliar-em-controle + shewhart-perfil-A + analise-carta-worm).
- `agents/` ✅ — 4 subagentes humanos-substitutos: `tech-lead-saas-regulado`, `advogado-saas-regulado`, `corretora-seguros-saas`, `consultor-rbc-iso17025`
- `output-styles/pt-br-conciso.md` ✅
- `skills/`, `commands/`, `rules/` — vazios por escolha; criar quando padrão repetir 3 vezes
- `.mcp.json` ✅ — github plugado; outros sob demanda

**Estado do produto (resumo):**
- Nome **"Aferê" provisório** (decidir antes de domínio/INPI)
- Escopo: ERP completo de N módulos (mín 6 confirmados; total saída do discovery)
- Cliente piloto: Balanças Solution (empresa do Roldão) — dogfooding; não substitui cliente externo pago
- Stack candidata: Django + Flutter + PostgreSQL (ADR-0001 — 3 portões)
- Hospedagem: Hostinger SP + Backblaze B2 + AWS KMS MRK
- Modelo 100% agentes IA (4 subagentes especialistas + 3 auditores Família 5 + humano sob demanda)

Mapa navegável completo em `docs/INDICE.md` e tabela de docs em `docs/documentos-do-projeto.md`.

---

## Princípios universais (defaults)

### Verificar antes de afirmar
NUNCA dizer "pronto", "implementado" ou "corrigido" sem ter rodado o comando de verificação e mostrado o resultado. Evidência antes de afirmação.

### Causa raiz, nunca sintoma
Teste falhou = problema no sistema. Corrigir o código, nunca mascarar (skip, `assertTrue(true)`, `eslint-disable`, `@ts-ignore`, regra desligada, `--quiet`, `|| true`).

### Commits atômicos
Cada commit com propósito único e claro. Não misturar correção + funcionalidade nova + reorganização no mesmo commit. Adicionar arquivos de forma seletiva — nunca `git add .` cego com outras frentes sujas.

### Perguntar antes de destruir
Confirmar antes de operações irreversíveis: `git reset --hard`, `git push --force`, `git branch -D`, `rm -rf`, `drop table`, migration destrutiva.

---

## Estrutura `.claude/` neste projeto

```
.claude/
├── settings.json          ← permissões + hooks (versionado)
├── settings.local.json    ← pessoal (NÃO versionar)
├── agents/                ← 4 subagentes humanos-substitutos (tech-lead, advogado, corretora, RBC)
├── skills/                ← vazio (criar quando padrão repetir 3x)
├── commands/              ← vazio (preferir skills no padrão novo)
├── hooks/                 ← 58 hooks ativos (474 casos no _test-runner) — lista completa em AGENTS §3
├── rules/                 ← vazio (criar com `paths:` frontmatter — lazy)
└── output-styles/         ← pt-br-conciso.md
```

Mapa completo do repositório em `docs/INDICE.md`.

---

## Notas sobre Windows + Git Bash

A máquina é Windows 11. Hooks rodam via Git Bash. Considerar:
- `jq` **não vem por padrão** no Git Bash. Hooks usam `perl -MJSON::PP` (perl 5.14+, sempre presente) pra parsear o JSON enviado pelo Claude Code. Tentativa anterior com `sed` puro vazava: quebrava na primeira aspa escapada, deixando comandos como `sqlite3 db "DROP TABLE x"` passarem sem bloqueio.
- Path com espaços (`C:\PROJETOS\Certificado de calibracao`) — sempre usar `"${CLAUDE_PROJECT_DIR}"` com aspas.
- `chmod +x` não é confiável no Windows — invocar hooks via `bash script.sh`.
- Sandboxing nativo não suportado (só WSL2).
- Validar mudanças nos hooks rodando `bash .claude/hooks/_test-runner.sh` — 474 casos cobrindo bypass conhecidos e regressões.
