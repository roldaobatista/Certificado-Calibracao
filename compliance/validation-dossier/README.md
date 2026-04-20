# compliance/validation-dossier/ — Dossiê de validação

**Owner:** `qa-acceptance`. `requirements.yaml`, `traceability-matrix.yaml`, evidências assinadas por execução. Ver `harness/04-compliance-pipeline.md` Parte B.

## Arquivos canônicos

- `requirements.yaml` — fonte única dos requisitos rastreáveis já ativados.
- `traceability-matrix.yaml` — gerado por `pnpm validation-dossier:write`; não editar manualmente.
- `coverage-report.md` — relatório humano de cobertura do PRD §13.
- `evidence/<REQ-id>/` — destino dos artefatos de execução por requisito.
- `snapshots/` — manifesto, baseline e current do Gate 7 para snapshot-diff canônico.

## Comandos

```bash
pnpm validation-dossier:write   # regenera matriz e relatório
pnpm validation-dossier:check   # valida schema, links e matriz atualizada
```

O check padrão registra pendências do PRD §13 como warnings enquanto o MVP ainda não existe. Para release, use `tsx tools/validation-dossier.ts check --strict-prd`, que transforma qualquer critério sem requisito em erro.
