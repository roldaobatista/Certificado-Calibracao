# ADR 0033 — Politica executavel de perfis regulatorios para PDF

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0030-prd-13-15-regulatory-profiles-pdf.md`, `PRD.md` §6.5, §8.14 e §13.15

## Contexto

O PRD define tres perfis regulatorios com consequencias diretas no certificado:

- Tipo A: pode usar simbolo Cgcre/RBC quando estiver dentro do escopo acreditado;
- Tipo B: usa rastreabilidade via RBC, mas sem simbolo;
- Tipo C: sem referencia a RBC/Cgcre no certificado.

O repo ja possuia regras textuais e snapshots estruturais, mas nao havia ainda uma API normativa minima tornando esse comportamento executavel e testavel.

## Decisão

1. `@afere/normative-rules` passa a exportar `resolveRegulatoryPdfPolicy()`.
2. A funcao retorna, no minimo:
   - `templateId`;
   - `symbolPolicy`;
   - `allowedStandardSources`;
   - `forbiddenFreeTextTerms`;
   - `warnings`.
3. `symbolPolicy` segue tres estados:
   - `allowed` para Tipo A dentro do escopo;
   - `suppressed` para Tipo A fora do escopo;
   - `blocked` para Tipos B e C.
4. `validateRegulatoryFreeText()` aplica bloqueio semantico minimo para o perfil C, rejeitando `RBC` e `Cgcre` em texto livre.

## Consequências

- O requisito do PRD §13.15 deixa de depender apenas de documento e vira comportamento executavel.
- `apps/api` ganha um contrato minimo futuro para escolher template e aplicar politica de simbolo.
- O bloqueio semantico do perfil C passa a ser validado por teste ativo.

## Limitações honestas

- Esta ADR nao implementa renderer de PDF nem consulta de escopo CMC real.
- O comportamento do perfil B ainda nao valida toda a elegibilidade dos padroes; isso permanece no requisito de escopo/CMC e fontes permitidas.
- A politica atual cobre o nucleo A/B/C e o bloqueio semantico minimo, nao a matriz inteira de campos do certificado.
