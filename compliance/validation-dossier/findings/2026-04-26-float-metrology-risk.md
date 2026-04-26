# Finding — Campos metrológicos oficiais em Float no ServiceOrder

## Status

Mitigado em 2026-04-26. Migration aplicada em dev; typecheck e testes verdes.

## Contexto

O schema Prisma em `packages/db/prisma/schema.prisma` define `ServiceOrder` com:

- `measurementResultValue Float?`
- `measurementExpandedUncertaintyValue Float?`
- `k Float?`

Para resultado metrológico oficial, incerteza expandida e fator de abrangência, persistir em `Float` (IEEE 754 binary64) cria risco de arredondamento binário não determinístico entre runtime, banco e renderização. Isso pode gerar divergência auditável entre o valor persistido, o valor exibido no certificado e o valor recalculado pelo engine de incerteza.

O modelo `Standard` já usa `Decimal`, o que demonstra que a preocupação existe em parte do domínio, mas não foi estendida aos resultados oficiais da ordem de serviço.

## Impacto

- Risco de divergência centesimal/milesimal entre backend, PDF e re-auditoria.
- Dificuldade para garantir representação canônica do resultado em certificado regulado.
- Possível não conformidade com requisitos de exatidão e rastreabilidade metrológica.

## Reprodução / Evidência

Inspeção estática de `schema.prisma`, modelo `ServiceOrder`:
```prisma
model ServiceOrder {
  // ...
  measurementResultValue              Float?
  measurementExpandedUncertaintyValue Float?
  k                                   Float?
  // ...
}
```

## Correção recomendada

1. Migrar os três campos para `Decimal` com escala e precisão definidas (ex: `Decimal @db.Decimal(28, 12)`).
2. Ou, alternativamente, armazenar representação textual normalizada mais unidade, resolução e casas decimais em campos separados, garantindo que a renderização seja derivada da representação canônica.
3. Atualizar contracts, tipos TypeScript e engine de incerteza para refletir o tipo seguro.
4. Criar teste de regressão que valida idempotência de serialização/deserialização do valor canônico.

## Rastreamento

- Área crítica: `packages/db/prisma/schema.prisma`, `packages/engine-uncertainty/`, `apps/api/src/domain/emission/`
- Requisito PRD: §13.03 (declarações de medição no certificado)
- AC relacionado: `prd-13-03-certificate-measurement-declarations.test.ts` (precisará evoluir para cobertura de tipo de persistência)
