---
owner: roldao
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 220
proposito: fonte unica das regras que agentes e humanos nao podem violar no projeto
---

<!--
template: REGRAS-INEGOCIAVEIS.md
uso: copiar para a raiz do repositório.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C0
limite: ≤220 linhas. Fonte única de verdade das invariantes.
ordem: frontmatter → este HTML comment → corpo.
-->

# Regras inegociáveis — Aferê Prumo

> **Hierarquia de precedência (vale para os 4 contratos AI):**
> constitution.md > REGRAS-INEGOCIAVEIS.md > AGENTS.md > CLAUDE.md
> Em qualquer conflito, o documento mais alto vence. CLAUDE.md é o mais específico (canal Claude Code) e o mais fácil de mudar.

> Fonte única de verdade das invariantes operacionalizáveis. Toda outra doc referencia por ID, nunca redeclara. Cada INV declara: regra, motivação, hook que aplica e auditor relacionado. Invariante sem mecanismo de aplicação é decoração — não entra aqui.

## 1. Invariantes de produto (INV-NNN)

| ID | Regra | Por que (motivação) | Hook que aplica | Auditor relacionado |
|---|---|---|---|---|
| INV-001 | Toda query a tabela com `tenant_id` filtra por tenant. | Vazamento entre clientes = morte do produto. | `tenant-id-validator.sh` ‡ | `auditor-seguranca` |
| INV-TENANT-001 | RLS habilitado em toda tabela `_tenanted`. | Backup contra esquecimento de filtro aplicacional. | `migration-rls-check.sh` ‡ | `auditor-seguranca` |
| SEC-001 | Nenhum secret (chave, token, senha) em código-fonte ou histórico git. | Vazamento público irreversível. | `secrets-scanner.sh` | `auditor-seguranca` |
| TST-001 | Teste não pode ser silenciado, pulado ou afrouxado sem ADR. | Esconde bug e quebra confiança na suite. | `anti-mascaramento.sh` | `auditor-qualidade` |

> ‡ **Hook materializado no projeto-destino, não no meta-template.** Diferente dos hooks universais (`block-destructive.sh`, `secrets-scanner.sh`, `anti-mascaramento.sh`, `override-ledger.sh`, `frontmatter-validator.sh`...) que já vêm prontos em `templates/hook-*.template.sh`, estes dependem da stack/DB/fluxo decididos nos ADRs (ORM, dialeto SQL, política de PR) e por isso são criados no projeto quando a stack é conhecida — INV-001/INV-TENANT-001 só se aplicam a projetos multi-tenant; `inv-change-guard.sh` depende do fluxo de PR do repositório. Até serem criados, o auditor relacionado cobre a regra em pre-merge.

## 2. Invariantes para agentes IA (INV-AGENT-NNN)

| ID | Regra | Por que (motivação) | Hook que aplica | Auditor relacionado |
|---|---|---|---|---|
| INV-AGENT-001 | Agente IA NÃO deleta dado de produção sem confirmação humana explícita. | Perda irreversível, sem backup viável em janela curta. | `block-destructive.sh` | `auditor-limites-agente` |
| INV-AGENT-002 | Proibido `--no-verify` e `--force` puro em qualquer branch. `--force-with-lease` permitido em branch própria (feature/fix); em `main`/`master`/`release/*` exige `.claude/.override-reason` registrado. `git reset --hard` em ref local exige override-reason; em ref remota (`origin/*`) é PROIBIDO sem exceção. | Pula quality gate e/ou destrói histórico compartilhado. Lease em branch própria é prática moderna segura. | `block-destructive.sh` + `no-verify-bypass.sh` + `override-ledger.sh` | `auditor-limites-agente` |
| INV-AGENT-003 | Investigar antes de mexer em lógica de negócio: ler banco/log/payload/console **antes** de editar código. | Mudar template/UI sem confirmar o estado real produz voltas e bug pior. | `pre-edit-evidence.sh` | `auditor-doc-quality` (sub-regra B: ação sem evidência de leitura prévia) |
| INV-AGENT-004 | Pró-atividade: executar ações reversíveis sem perguntar (matriz 2×2 em `AGENTS.md §13.1`). Confirmar antes só para irreversíveis ou com custo > 0: `npm publish`, `drop table`, `git push --force`, `git reset --hard` em remoto, `rm -rf`, migration destrutiva, gasto financeiro, mudança de visibilidade do repo, rotação de credencial fora de janela. | Empurrar tarefa executável pro dono quebra fluxo e ele não programa. | `override-ledger.sh` | `auditor-pro-atividade` / `auditor-limites-agente` |
| INV-AGENT-005 | Validar antes de afirmar: nunca dizer "pronto/implementado/corrigido" sem rodar verificação e mostrar resultado. | Afirmação sem evidência erode confiança e mascara regressões. | `post-claim-evidence.sh` | `auditor-revisao` (verifica seção "Evidência verificada" no relatório/PR) |
| INV-AGENT-006 | Causa raiz, nunca sintoma. Proibido `skip`, `assertTrue(true)`, `@ts-ignore`, `eslint-disable`, `\|\| true`, `--quiet`, baseline pra esconder erro, asserção relaxada. | Mascarar erro transforma bug pequeno em incidente caro. | `anti-mascaramento.sh` | `auditor-qualidade` |
| INV-AGENT-007 | Commits atômicos. Antes de cada `git commit`: rodar `git status` + `git diff --staged` + `git log -3 --oneline`. Proibido `git add .` / `git add -A` cego quando há outras frentes dirty. Stage seletivo por arquivo nomeado. | Commit misto polui histórico e impede revert cirúrgico. | `auditor-commit-hygiene.sh` | `auditor-commit-hygiene` |
| INV-AGENT-008 | PII (CPF, e-mail, telefone, endereço, dado sensível) nunca em logs nem em prints. Mascarar/tokenizar antes de logar. Projeto que **não trata PII de terceiros** pode marcar N/A em [`docs/nao-aplica.md`](./docs/nao-aplica.md) com gatilho de reavaliação. Projeto que trata PII **só em contexto específico** (ex: snapshots de teste em lib OSS) pode especializar (mas não enfraquecer) a regra em sua própria REGRAS-INEGOCIAVEIS.md, preservando o ID. | LGPD Art. 46 + risco reputacional + obrigação contratual. | `secrets-scanner.sh` (ampliado para PII) | `auditor-seguranca` |
| INV-AGENT-009 | Nenhum segredo (chave, token, credencial, certificado) em arquivo versionado. Usa `.env` local + cofre. | Histórico git é eterno; segredo vazado = rotação imediata. | `secrets-scanner.sh` | `auditor-seguranca` |
| INV-AGENT-010 | Linguagem acessível: traduzir jargão técnico na primeira ocorrência por canal. Dono não programa. Tabela de tradução canônica no anexo 2.A abaixo. | Jargão sem tradução exclui o tomador de decisão do loop. | — (sem hook: detecção de jargão é semântica, não mecânica) | `auditor-doc-quality` (regra E: jargão sem glosa) |
| INV-AGENT-011 | Alteração de qualquer INV-AGENT-NNN exige PR dedicado + aprovação do dono + entrada em `docs/governanca/decisoes-inv.md`. | INV é contrato; mudança silenciosa destrói o contrato. | `inv-change-guard.sh` ‡ | `auditor-processo` |

### 2.A — Anexo da INV-AGENT-010: tradução canônica de jargão

A fonte única de verdade da tradução de jargão **NÃO vive aqui** — vive em [`GLOSSARIO-ROLDAO.md`](./GLOSSARIO-ROLDAO.md) do meta-template (no projeto destino: copiar para `GLOSSARIO-ROLDAO.md` da raiz). Este anexo apenas referencia.

Regra (sustentada por INV-AGENT-010): ao usar qualquer termo do glossário em conversa com o dono, traduzir na primeira ocorrência por canal. Auditor `auditor-doc-quality` (regra E) verifica.

**Não duplicar a tabela aqui** — drift garantido se houver duas fontes.

**Pró-atividade (referência a INV-AGENT-004):** o agente executa ações reversíveis sem perguntar e reporta no formato "fiz X, resolvi Y, já comecei Z". Detalhes e lista destrutiva vivem em INV-AGENT-004; este anexo é só de linguagem.

## 3. Processo de alteração das INVs

1. PR dedicado, **um INV por PR**, mensagem cita o ID alterado.
2. Aprovação do dono (humano) obrigatória — não há override por agente.
3. Entrada em `docs/governanca/decisoes-inv.md` com: data, ID, motivo, antes/depois, aprovador.
4. Atualização (ou criação) do hook/auditor correspondente no mesmo PR. INV sem mecanismo não é aceito.
5. `CHANGELOG.md` registra a mudança.

## 4. Referências

- [`constitution.md`](./.claude/memory/constitution.md) — princípios fundadores (autoridade máxima).
- [`AGENTS.md`](./AGENTS.md) — canônico de produto.
- [`CLAUDE.md`](./CLAUDE.md) — adendo do harness Claude Code.
- [`docs/governanca/catalogo-auditores.md`](./docs/governanca/catalogo-auditores.md) — auditores citados acima.
- [`docs/governanca/decisoes-inv.md`](./docs/governanca/decisoes-inv.md) — histórico de alterações de INV.
