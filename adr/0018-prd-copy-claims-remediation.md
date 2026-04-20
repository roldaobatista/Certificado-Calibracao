# ADR 0018 — Correção de claims proibidos no PRD

Status: Aprovado

Data: 2026-04-20

## Contexto

O finding `FINDING-2026-04-19-001` registrou que o próprio `PRD.md` continha exemplos de copy comercial bloqueados pelas regras CL-001, CL-002 e CL-006 do `copy-lint`.

Essas frases estavam em áreas de wireframe e orientação comercial, não em requisitos funcionais. Mesmo assim, manter os exemplos literais criava risco de propagação para site, portal, contratos ou materiais comerciais.

## Decisão

Substituir os claims absolutos por linguagem escopada:

- foco em bloqueios normativos automatizáveis;
- trilha rastreável e evidência;
- classes específicas de erro listadas no PRD;
- ausência de promessa de aprovação, auditoria garantida ou eliminação absoluta de erro.

Adicionar `tools/copy-lint-prd.test.ts` para tornar o `PRD.md` uma regressão permanente do copy-lint.

## Consequências

O PRD deixa de acionar erros do `copy-lint`, e alterações futuras no documento passam a ser testadas de forma explícita em `pnpm test:tools` e `pnpm check:all`.

## Limitação

Esta decisão fecha o finding técnico do copy-lint no PRD. O claim-set completo continua em estado draft até revisão jurídica humana antes de P0-5 ser considerado aprovado para go-live.
