# ADR 0035 — Contrato estruturado para declaracao metrologica do certificado

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0032-prd-13-03-measurement-declarations.md`, `PRD.md` §13.3, §7.8 e §17.5.4

## Contexto

O PRD exige que o certificado declare resultado, incerteza expandida e fator `k`. Sem esse trio, o certificado fica tecnicamente incompleto. O pacote `@afere/engine-uncertainty`, porém, ainda nao oferecia nem mesmo um contrato minimo garantindo que o payload tecnico so pudesse ser montado com esses campos.

## Decisão

1. `@afere/engine-uncertainty` passa a exportar `buildCertificateMeasurementDeclaration()`.
2. A funcao retorna um objeto estruturado com:
   - `result`;
   - `expandedUncertainty`;
   - `coverageFactor`;
   - `summary`.
3. A funcao falha fechado para:
   - unidade ausente;
   - resultado nao finito;
   - incerteza expandida negativa ou nao finita;
   - fator `k` nao positivo ou nao finito.
4. O pipeline raiz passa a executar:
   - testes unitarios de `packages/engine-uncertainty/src/*.test.ts`;
   - testes de aceite de `evals/ac/*.test.ts`.

## Consequências

- O PRD §13.3 deixa de depender apenas de texto e passa a ter um contrato executavel.
- `apps/api` ganha um payload tecnico futuro estavel para popular a previa e o certificado final.
- O fail-closed impede emissao com declaracao tecnica incompleta ou numericamente invalida.

## Limitações honestas

- Esta ADR nao implementa o calculo completo da incerteza nem o balanco metrologico.
- O arredondamento metrologico ainda usa serializacao numerica simples.
- A integracao com renderer real de certificado permanece para fatias posteriores.
