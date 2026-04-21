# 0032 — Declaracao estruturada de resultado, U expandida e fator k

## Contexto

O PRD §13.3 exige que todo certificado emitido declare, no minimo, resultado, incerteza expandida e fator `k`. O documento tambem reforca que:

- a engine calcula `U` expandida com `k=2` como base tipica do fluxo;
- a previa integral do certificado ja deve renderizar esses campos antes do fechamento da execucao;
- a emissao fail-closed e preferivel a um certificado com declaracao tecnica incompleta.

O pacote `@afere/engine-uncertainty` ainda esta em scaffold. Falta uma API minima que prove, por teste ativo, que o payload tecnico do certificado nao existe sem a triade `resultado + U expandida + k`.

## Escopo

- Adicionar em `packages/engine-uncertainty` uma API pequena para montar a declaracao tecnica de medicao do certificado.
- Exigir `resultado`, `incerteza expandida`, `fator k` e `unidade`.
- Formatar `U` com sinal `±` e `k` como campo explicito.
- Falhar fechado para entradas ausentes, negativas ou nao finitas.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-03-certificate-measurement-declarations.test.ts`.
- Promover `REQ-PRD-13-03-CERTIFICATE-MEASUREMENT-DECLARATIONS` para `validated` se a evidencia ficar verde.

## Fora de escopo

- Implementar o balanco completo de incerteza, combinacao Tipo A/B ou regra de decisao ILAC G8.
- Integrar com renderer real do certificado em `apps/api`.
- Modelar arredondamento metrologico fino por familia de instrumento.

## Critérios de aceite

- A API retorna declaracao estruturada contendo `result`, `expandedUncertainty`, `coverageFactor` e `summary`.
- `expandedUncertainty.formatted` usa `±` e a unidade declarada.
- `coverageFactor.formatted` explicita `k=<valor>`.
- Entrada ausente, negativa ou nao finita falha fechado.
- O teste de aceitacao falha se a API nao for exportada por `packages/engine-uncertainty/src/index.ts`.

## Evidencia

- `pnpm exec tsx --test evals/ac/prd-13-03-certificate-measurement-declarations.test.ts`
- `pnpm exec tsx --test packages/engine-uncertainty/src/measurement-declarations.test.ts`
- `pnpm check:all`
