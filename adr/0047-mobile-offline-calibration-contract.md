# ADR 0047 — Fluxo Android offline gera rascunho local de certificado sem backend

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0044-prd-13-01-mobile-offline-calibration.md`, `PRD.md` §13.1

## Contexto

O repositório ainda não possui app Android real nem toolchain Kotlin disponível neste ambiente. Mesmo assim, o requisito pode ganhar evidência executável com um contrato offline-first que represente a sessão capturada no dispositivo e o rascunho local de certificado produzido ali mesmo.

## Decisão

1. `packages/contracts/src/mobile-offline-calibration.ts` passa a definir os schemas compartilhados da sessão offline e do rascunho local do certificado.
2. `apps/android/src/offline-calibration-workflow.ts` passa a exportar `completeMobileOfflineCalibration()`.
3. A finalização offline exige número de certificado previamente reservado, medições válidas, revisão técnica concluída e assinatura no dispositivo.
4. Quando `networkState=offline`, o rascunho é gerado com `generatedOnDevice=true` e `syncState=pending_sync`.
5. A decisão é fail-closed: qualquer dado obrigatório ausente bloqueia o fechamento da sessão.

## Consequências

- O PRD §13.1 ganha uma evidência executável sem depender de Kotlin/Gradle no ambiente atual.
- O contrato compartilhado pode ser reaproveitado depois pelo app Android real e pelo backend de sync.
- O fluxo deixa explícito que o certificado local offline depende de numeração previamente reservada.

## Limitações honestas

- A ADR não entrega app Kotlin real nem persistência SQLCipher.
- O artefato gerado é um rascunho local do certificado, ainda sem renderização PDF/A final.
- O sync server-side, a emissão oficial e a reconciliação pós-offline permanecem pendentes.
