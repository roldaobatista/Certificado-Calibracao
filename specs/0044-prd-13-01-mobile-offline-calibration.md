# 0044 — Calibração Android offline do início ao certificado local

## Contexto

O PRD §13.1 exige que a calibração IPNA possa ser executada do início ao certificado exclusivamente pelo Android, inclusive offline. Como o app Kotlin real ainda não existe nesta base, a melhor evidência executável imediata é um workflow offline-first em `apps/android` que gere um rascunho local de certificado sem roundtrip ao backend.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para sessão de calibração offline e rascunho local de certificado.
- Adicionar em `apps/android/src` um workflow que consuma a sessão offline e produza o rascunho local do certificado.
- Exigir número de certificado previamente reservado para permitir finalização offline sem depender do backend.
- Exigir medições, revisão técnica e assinatura no próprio dispositivo.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-01-mobile-offline-calibration.test.ts`.
- Promover `REQ-PRD-13-01-MOBILE-OFFLINE-CALIBRATION` para `validated` se a evidência ficar verde.

## Fora de escopo

- Aplicativo Kotlin/Gradle real.
- Renderização PDF/A final do certificado.
- Sync server-side, envio para API e resolução de conflitos pós-offline.

## Critérios de aceite

- O workflow conclui a sessão exclusivamente no Android quando `networkState=offline`, medições estão presentes, revisão técnica foi concluída e a assinatura ocorreu no dispositivo.
- O resultado gera um rascunho local com `generatedOnDevice=true` e `syncState=pending_sync`.
- O workflow falha fechado quando faltar número reservado, medições, revisão técnica ou assinatura.
- O contrato compartilhado em `packages/contracts` descreve a sessão offline e o rascunho local do certificado.

## Evidência

- `pnpm exec tsx --test apps/android/src/offline-calibration-workflow.test.ts`
- `pnpm exec tsx --test evals/ac/prd-13-01-mobile-offline-calibration.test.ts`
- `pnpm check:all`
