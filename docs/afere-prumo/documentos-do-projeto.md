---
owner: <Responsavel>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 150
proposito: tabela central com status de cada documento obrigatório do projeto — usada pelo auditor-doc-quality em PASS ZERO
---

<!--
template: documentos-do-projeto.md
destino: docs/documentos-do-projeto.md
uso: registro central do status de cada documento contratual.
-->

# Documentos do Projeto — Aferê Prumo

Lista única e canônica de documentos contratuais do projeto. Sempre que um documento for criado, promovido ou marcado como obsoleto, atualizar a tabela abaixo.

## 1. Legenda de status
- `draft` — em construção, conteúdo ainda pode mudar substancialmente.
- `stable` — aprovado, qualquer mudança exige ADR ou aprovação do owner.
- `deprecated` — não usar; manter por referência histórica até remoção combinada.

## 2. Tabela

Lista mínima de documentos contratuais que todo projeto deve registrar (adicione/remova linhas conforme o tipo do projeto):

| Caminho | Status | Owner | Última revisão | Bloqueia próxima fase? |
|---|---|---|---|---|
| `README.md` | draft | <nome> | 2026-05-28 | não |
| `AGENTS.md` | draft | <nome> | 2026-05-28 | sim |
| `CLAUDE.md` | draft | <nome> | 2026-05-28 | sim |
| `CONTRIBUTING.md` | draft | <nome> | 2026-05-28 | não |
| `MAINTAINERS.md` | draft | <nome> | 2026-05-28 | não |
| `SECURITY.md` | draft | <nome> | 2026-05-28 | sim |
| `REGRAS-INEGOCIAVEIS.md` | stable | <nome> | 2026-05-28 | sim |
| `CHECKLIST-PRONTO-PRA-CODAR.md` | draft | <nome> | 2026-05-28 | sim |
| `docs/INDICE.md` | draft | <nome> | 2026-05-28 | sim |
| `docs/CONVENCOES-DOC.md` | draft | <nome> | 2026-05-28 | sim |
| `docs/glossario.md` | draft | <nome> | 2026-05-28 | sim |
| `docs/nao-aplica.md` | draft | <nome> | 2026-05-28 | sim |
| `docs/adr/ADR-0001-stack.md` | draft | <nome> | 2026-05-28 | sim |
| `docs/conformidade/lgpd/ropa.md` | draft | <nome> | 2026-05-28 | sim (se trata dado pessoal) |
| `docs/conformidade/lgpd/retencao-dados.md` | draft | <nome> | 2026-05-28 | sim (se trata dado pessoal) |
| `docs/governanca/catalogo-auditores.md` | draft | <nome> | 2026-05-28 | sim (se houver >1 auditor) |
| `.claude/agents/maestro.md` | draft | <nome> | 2026-05-28 | sim |
| `docs/operacao/slo-sli.md` | draft | <nome> | 2026-05-28 | não |
| `docs/operacao/runbooks/` (pasta) | draft | <nome> | 2026-05-28 | sim (se serviço crítico) |
| `docs/operacao/on-call.md` | draft | <nome> | 2026-05-28 | sim (se há plantão) |
| `docs/operacao/backup.md` | draft | <nome> | 2026-05-28 | sim (se persiste dado) |
| `docs/operacao/disaster-recovery.md` | draft | <nome> | 2026-05-28 | sim (se há RTO/RPO) |
| `docs/operacao/change-management.md` | draft | <nome> | 2026-05-28 | sim |
| `.claude/memory/constitution.md` | draft | <nome> | 2026-05-28 | sim |
| `.agent/CURRENT.md` | draft | <nome> | 2026-05-28 | não |

## 3. Regras de manutenção
- Promover `draft` → `stable` exige aprovação explícita do owner registrada em commit.
- Promover qualquer documento como bloqueante de fase exige amarração no `kickoff.md` da fase correspondente.
- Documento `deprecated` deve manter no topo um aviso indicando substituto.
