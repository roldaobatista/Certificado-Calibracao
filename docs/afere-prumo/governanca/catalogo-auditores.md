---
owner: <tech-lead-ou-governanca>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 100
proposito: catálogo único dos auditores ativos no projeto
---

<!-- proposito: catálogo único dos auditores ativos no projeto (subagentes/scripts que validam código e docs) | renomear-para: docs/governanca/catalogo-auditores.md -->

# Catálogo de Auditores — Aferê Prumo

## 1. Como ler este catálogo

> **Auditor** = robô (subagente ou script) que olha o código/docs e aponta problema antes do commit ou do merge.

Cada linha da tabela abaixo descreve **um** auditor ativo: o que ele faz, quando roda, qual é a severidade padrão quando ele acha algo, quem cuida dele, e onde mora a definição completa.

## 2. Auditores ativos

> **Coluna `ativo-em`**: tipos de projeto onde este auditor é aplicável. O maestro lê o `tipo` do frontmatter de `AGENTS.md` e ativa só os auditores cuja coluna `ativo-em` casa. **Sem perguntar.**

| ID | Nome | Função | Quando roda (gatilho) | Severidade default | Ativo-em | Owner | Arquivo de definição |
|---|---|---|---|---|---|---|---|
| A-001 | `auditor-doc-quality` | valida qualidade e consistência de toda documentação (placeholders não resolvidos, links quebrados, drift entre doc e código, cascata de renomeação) | pre-commit em `**/*.md` + pre-merge | ALTO | todos | <nome-do-owner> | `.claude/agents/auditor-doc-quality.md` |
| A-002 | `auditor-lgpd` | confere se operação que toca dado pessoal tem linha no ROPA + base legal válida | pre-commit em código que toca tabelas com dado pessoal | CRÍTICO | saas-regulado, qualquer projeto que trata PII | <nome-DPO> | `.claude/agents/auditor-lgpd.md` |
| A-003 | `auditor-seguranca` | procura segredo hardcoded, dependência com CVE, sanitização ausente | pre-commit + scan semanal agendado | CRÍTICO | saas, saas-regulado, lib, oss-lib, cli | <nome-seguranca> | `.claude/agents/auditor-seguranca.md` |
| A-004 | `auditor-meta` | valida que todo novo auditor tem golden cases + frontmatter completo | pre-commit em `.claude/agents/**` | ALTO | todos | <nome-tech-lead> | `.claude/agents/auditor-meta.md` |
| A-005 | `auditor-stack` | confere conformidade da stack com decisões ADR (versão, dependência proibida) | pre-merge | MÉDIO | todos exceto experimento ≤2d | <nome-arquiteto> | `.claude/agents/auditor-stack.md` |
| A-006 | `auditor-pro-atividade` | conta perguntas/turno em transcripts; flagra quando agente excede limite (>1 pergunta por 10 ações reversíveis) | pós-sessão | MÉDIO | todos (especialmente solo) | maestro | `.claude/agents/auditor-pro-atividade.md` |
| A-007 | `auditor-commit-hygiene` | valida commits atômicos, mensagem citando T-NNN, sem `git add .` cego | pre-commit + pre-push | ALTO | todos | <nome-tech-lead> | `.claude/agents/auditor-commit-hygiene.md` |
| A-008 | `auditor-limites-agente` | confere que o agente IA respeitou os limites de ação (não deletou produção sem confirmação, não usou `--force`/`--no-verify` indevido) — par de revisão dos hooks `block-destructive`/`no-verify-bypass` | pós-sessão + pre-merge | CRÍTICO | todos | maestro | `.claude/agents/auditor-limites-agente.md` |
| A-009 | `auditor-revisao` | verifica que todo relatório/PR de tarefa concluída tem seção "Evidência verificada" com saída real do comando de verificação (INV-AGENT-005) | pre-merge | ALTO | todos | <nome-tech-lead> | `.claude/agents/auditor-revisao.md` |
| A-010 | `auditor-processo` | valida o processo de alteração de INV (PR dedicado, um INV por PR, registro em `decisoes-inv.md`, hook/auditor atualizado no mesmo PR) — INV-AGENT-011 | pre-merge em `REGRAS-INEGOCIAVEIS.md` | CRÍTICO | todos | <nome-governanca> | `.claude/agents/auditor-processo.md` |
| A-011 | `auditor-qualidade` | procura mascaramento de teste/lint não pego pelo hook (asserção relaxada semântica, cobertura caindo, teste tautológico) — par de revisão do `anti-mascaramento` | pre-merge | ALTO | todos exceto experimento ≤2d | <nome-tech-lead> | `.claude/agents/auditor-qualidade.md` |

> Exemplo preenchido (linha A-001) é a referência canônica para entender o formato.
> Rótulos válidos em `ativo-em`: os tipos canônicos definidos em `AGENTS.md §2.1` (fonte única) — `solo`, `experimento`, `cli`, `lib`, `oss-lib`, `interno`, `saas`, `saas-regulado`, `mobile`, `desktop`, `ia-ml`, `pipeline`, `bot`, `browser-ext`, `ide-ext`, `embedded`, `jogo`, `smart-contract`, `api-microservice` — mais o meta-valor `todos` (deste catálogo, significa "ativo em qualquer tipo"; não é um tipo de projeto). Use exatamente os rótulos de `AGENTS.md §2.1`: qualquer divergência impede o maestro de casar `tipo` × `ativo-em`.

## 3. Processo de adicionar / remover auditor

**Mudança estrutural** (remover / aposentar / mudar severidade default):
1. **ADR** justificando a decisão (`docs/adr/ADR-NNNN-<slug>.md`).
2. **Pull request** com definição, golden cases, atualização da tabela.
3. **Aprovação** do owner do domínio afetado + tech lead.
4. **Validação** do `auditor-meta` antes do merge.

**Adição de auditor novo** (cobertura nova de regra que não existia):
1. ADR auto-redigido pelo agente IA (template `ADR.template.md`) — basta justificar lacuna e regra coberta.
2. Definição em `.claude/agents/<nome>.md` (seguindo `templates/auditor.template.md`).
3. Golden cases (positivos e negativos) por regra declarada.
4. Atualização desta tabela.
5. **Validação** do `auditor-meta` antes do merge. **Aprovação humana é opcional se golden cases passam** (auto-aprovação em modo solo).

Diferença-chave: adição amplia cobertura sem destruir o existente — não exige aprovação humana se passar nos gates. Remoção/aposentadoria destrói cobertura — exige aprovação.

## 4. Auditores aposentados (histórico)

> Auditores que existiram em algum momento mas não rodam mais. Manter por rastreabilidade.

| ID antigo | Nome | Aposentado em | Motivo | Sucessor |
|---|---|---|---|---|
| A-X01 | `auditor-cascata-substituicao` | 2026-05-28 | escopo absorvido por `auditor-doc-quality` | A-001 |
| A-X02 | `auditor-conteudo-placeholder` | 2026-05-28 | escopo absorvido por `auditor-doc-quality` | A-001 |
| A-X03 | `auditor-drift-docs` | 2026-05-28 | escopo absorvido por `auditor-doc-quality` | A-001 |

Quando um auditor é aposentado:
- arquivo de definição move para `docs/governanca/aposentados/<nome>.md` (preserva histórico).
- golden cases podem ser arquivados ou migrados para o sucessor (decisão registrada em ADR).
- regras que ficaram órfãs (nenhum sucessor cobre) são re-avaliadas: ou viram novo auditor, ou viram apenas guideline humano, com justificativa.

## 5. Convenções

- **ID** segue padrão `A-NNN` (numérico, sequencial, não reutilizado).
- **Severidade default** = nível atribuído quando o auditor acha violação SEM contexto extra. Pode ser elevada em regras específicas dentro do próprio auditor.
- **Owner** é pessoa, não time. Quem assume a manutenção e a evolução dos golden cases.
- Severidades válidas: `CRÍTICO`, `ALTO`, `MÉDIO`, `BAIXO`.

## 6. Histórico de revisões

| Data | Revisor | Mudança |
|---|---|---|
| 2026-05-28 | <nome> | criação inicial |
