---
description: Verifica cobertura de AC por REQ no dossiê de validação
---

Objetivo: garantir que todo AC do PRD §13 tem entrada em `compliance/validation-dossier/requirements.yaml` + pelo menos 1 teste em `evals/ac/` + linha em `traceability-matrix.yaml`.

Passos:

1. Parse `PRD.md` §13 → lista de AC com ID e descrição.
2. Parse `compliance/validation-dossier/requirements.yaml` → mapeamento AC → REQ → teste.
3. Reporte gaps em 3 colunas: `AC sem REQ`, `REQ sem teste`, `teste sem evidência arquivada`.
4. Escalar qualquer gap em área crítica para `qa-acceptance` como blocker de release.

Se `$ARGUMENTS` for fornecido, limitar verificação ao REQ/AC específico. Sem argumento, rodar full.

Ver `harness/04-compliance-pipeline.md` Parte B (regras de gate).
