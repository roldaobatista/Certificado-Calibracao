# Spec 0021 — `spec-review-flag` e template canônico do verification log

## Objetivo

Fechar a próxima lacuna de P0-10: o harness já definia `spec-review-flag` para reabrir L1 após 3 correções consecutivas na mesma spec, mas o repositório ainda não materializava esse gatilho nem a base canônica do `verification-log`.

## Escopo

- Exigir `compliance/verification-log/_template.yaml` como artefato canônico.
- Fazer `tools/verification-cascade.ts` ler `compliance/verification-log/*.yaml`.
- Detectar `CASCADE-007` quando 3 correções consecutivas alterarem `ac_changed` ou `reqs_changed` sem evidência de re-auditoria L1.
- Gerar draft determinístico de issue para `spec-review-flag` usando a mesma raiz `compliance/verification-log/issues/`.
- Tornar o template de issue genérico para múltiplos findings de cascata.
- Ampliar `tools/compliance-structure-check.ts` para exigir o `_template.yaml`.

## Critérios de aceite

- Repositório sem `compliance/verification-log/_template.yaml` falha fechado em `CASCADE-006`.
- Três correções consecutivas com alteração de AC/REQ e sem `L1/` em `re_audits_completed` geram `CASCADE-007`.
- Se a última correção já registrar re-auditoria L1, o finding não é emitido.
- `pnpm verification-cascade:issue-drafts -- --write` grava draft Markdown determinístico para `spec-review-flag`.
- Snapshot diff e `spec-review-flag` podem coexistir na mesma execução sem colidir no agrupamento de drafts.

## Fora de escopo

- Detectar automaticamente o mesmo padrão no nível de épico L0.
- Fechar issues automaticamente após a re-auditoria.
- Substituir a futura bateria de 30 certificados canônicos em PDF/A.
