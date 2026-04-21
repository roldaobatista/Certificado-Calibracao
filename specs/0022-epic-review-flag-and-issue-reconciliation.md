# Spec 0022 — `epic-review-flag` e reconciliação automática de verification issues

## Objetivo

Fechar a próxima lacuna de P0-10 após `spec-review-flag`: materializar o gatilho análogo no nível de épico L0 e fazer o ciclo de vida das verification issues acompanhar o estado atual do repositório, sem depender de fechamento manual.

## Escopo

- Detectar `CASCADE-008` quando 3 correções consecutivas em múltiplas specs do mesmo épico alterarem AC/REQ sem evidência de re-auditoria L0.
- Inferir o épico a partir de referências `L0/<EPIC-ID>` em `propagated_up` e `re_audits_completed`.
- Gerar draft determinístico de issue para `epic-review-flag`.
- Expor um reconciliador puro de issues gerenciadas para decidir `create`, `reopen`, `keepOpen` e `close`.
- Fazer o workflow `required-gates` gerar drafts sempre, montar um plano de reconciliação e aplicar create/reopen/update/close no GitHub.

## Critérios de aceite

- Três correções consecutivas em ao menos 2 specs do mesmo épico, sem `L0/<EPIC-ID>` em `re_audits_completed`, geram `CASCADE-008`.
- Se a última correção já registrar re-auditoria L0, o finding não é emitido.
- `pnpm verification-cascade:issue-drafts -- --write` grava draft Markdown determinístico para `epic-review-flag`.
- O reconciliador ignora issues manuais fora do frontmatter `verification-cascade-*`.
- Em `push` para `main`, issues gerenciadas deixam de ficar abertas quando o finding correspondente some.

## Fora de escopo

- Deduplcar épicos por fonte externa de roadmap ou ADR; a inferência continua baseada nos próprios logs.
- Sincronizar automaticamente comentários históricos ou milestones das issues gerenciadas.
- Substituir a futura bateria de 30 certificados canônicos em PDF/A.
