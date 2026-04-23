# 0087 - Gate de captura bruta no dry-run de emissao

## Contexto

A spec `0086-raw-measurement-analysis-engine.md` introduziu analise inicial de repetitividade, excentricidade e linearidade a partir do bruto estruturado da OS.

O fluxo persistido ja mostra esse sinal em revisao, previa e fila de assinatura, mas o dry-run de emissao ainda nao trata a captura bruta como um check formal do motor de emissao.

## Objetivo

Adicionar ao dry-run um check explicito de captura bruta metrologica, para que a emissao falhe fechada quando o bruto estiver ausente ou estruturalmente inadequado para sustentar revisao/emissao.

## Escopo

- estender o contrato de `EmissionDryRunCheckId` com um check especifico para captura bruta;
- estender `RunCertificateEmissionDryRunInput` com um bloco resumido de prontidao da captura bruta;
- marcar o dry-run como bloqueado quando a captura bruta nao estiver pronta;
- propagar warnings e blockers desse bloco para o resultado do dry-run;
- atualizar os cenarios canonicos para alimentar esse novo check;
- atualizar o mapeamento de passos sugeridos do preview.

## Fora de escopo

- recalcular ainda `U` expandida final a partir do bruto;
- substituir os checks existentes de declaracao metrologica;
- modelar ainda a regra completa de incerteza e decisao normativa.

## Criterios de aceite

- o dry-run passa a emitir o check `raw_measurement_capture`;
- quando a captura bruta estiver incoerente, o dry-run entra em `blocked`;
- quando a captura estiver pronta, o check passa e o resumo fica explicito;
- os cenarios canonicos e persistidos continuam válidos no contrato atualizado.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/emission/dry-run.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm --filter @afere/api typecheck`
