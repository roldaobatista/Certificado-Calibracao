# Dossiê de Validação — Onda metrológica assistida no fluxo de emissão

## Escopo validado

- Persistência da captura bruta de medições na OS e derivação de labels de execução a partir desse conteúdo.
- Perfis metrológicos persistidos para equipamentos e padrões, com snapshots metrológicos materializados na OS.
- Análise estruturada de medições brutas, EMA indicativa da Portaria 157, orçamento preliminar e regra decisória indicativa em `packages/engine-uncertainty`.
- Exposição da assistência decisória em review técnico, prévia do certificado, fila de assinatura e trilha de auditoria.
- Gate fail-closed para exigir decisão oficial explícita e justificativa quando houver divergência da avaliação indicativa.
- Sincronização da bateria canônica de 30 certificados para refletir o checklist de captura bruta metrológica.

## Evidências executadas

- `pnpm db:generate` — verde.
- `pnpm --filter @afere/contracts build` — verde.
- `pnpm --filter @afere/api typecheck` — verde.
- `pnpm --filter @afere/web typecheck` — verde.
- `pnpm exec tsx --test apps/api/src/app.test.ts` — verde, incluindo captura bruta, labels derivados, decisão assistida e bloqueios da decisão oficial.
- `pnpm exec tsx --test apps/web/src/quality/audit-trail-scenarios.test.ts` — verde.
- `pnpm test:tenancy` — verde.
- `pnpm snapshot-diff:write-current` — verde.
- `pnpm check:all` — verde.
- `bash .githooks/pre-commit` — verde.

## Resultado

PASS

## Limitações honestas

- A decisão indicativa continua assistiva e não substitui o cálculo oficial final do certificado.
- A conformidade PDF/A formal continua dependente de validação externa.
- A decisão/revisão persistidas continuam sem PKI externa qualificada.
