# 0088 - Derivacao de labels operacionais a partir do bruto estruturado

## Contexto

O fluxo atual ainda depende de varios campos-resumo digitados manualmente na OS, mesmo quando o bruto estruturado ja existe.

Depois das specs `0086` e `0087`, o sistema ja:

- persiste o bruto;
- analisa repetitividade, excentricidade e linearidade;
- usa esse sinal como gate visual e como check do dry-run.

Falta reduzir a dependencia de labels manuais nas areas em que a derivacao e segura.

## Objetivo

Permitir que a OS derive automaticamente labels operacionais a partir do bruto estruturado, quando esses labels nao forem informados manualmente.

## Escopo

- tornar opcionais na rota de save os labels que podem ser derivados com baixo risco:
  - `environmentLabel`
  - `curvePointsLabel`
  - `evidenceLabel`
  - `conformityLabel`
- derivar esses labels no backend quando houver `measurementRawData`;
- manter `uncertaintyLabel` como manual por enquanto;
- falhar fechado quando o label estiver ausente e tambem nao houver bruto suficiente para derivacao.

## Fora de escopo

- derivar automaticamente `uncertaintyLabel`;
- derivar `measurementResultValue`, `U` expandida ou `k` final;
- remover imediatamente os campos-resumo do frontend.

## Criterios de aceite

- a OS pode ser salva com esses labels omitidos quando houver bruto suficiente;
- o backend preenche esses labels de forma deterministica;
- sem bruto e sem label manual, o save continua falhando fechado;
- existe teste cobrindo save com labels derivados.

## Evidencia

- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm --filter @afere/api typecheck`
