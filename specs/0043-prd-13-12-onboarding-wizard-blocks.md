# 0043 — Wizard de onboarding com meta de 1 hora e bloqueio da primeira emissão

## Contexto

O PRD §13.12 exige que o onboarding do administrador inicial seja concluível em até 1 hora e que a primeira emissão de certificado permaneça bloqueada até os pré-requisitos obrigatórios estarem concluídos. O repositório ainda não possui um contrato executável para essa prontidão.

## Escopo

- Adicionar em `apps/api/src/domain/onboarding` uma função que avalie prontidão do onboarding.
- Calcular se a conclusão ocorreu dentro da meta de 1 hora.
- Bloquear a primeira emissão enquanto faltarem pré-requisitos obrigatórios.
- Materializar em `apps/web/src/onboarding` um resumo de wizard com etapas bloqueantes legíveis.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-12-onboarding-wizard-blocks.test.ts`.
- Promover `REQ-PRD-13-12-ONBOARDING-WIZARD-BLOCKS` para `validated` se a evidência ficar verde.

## Fora de escopo

- UI real em Next.js com persistência.
- Cronometria observável no browser ou analytics do funil.
- Disparo do fluxo real de emissão.

## Critérios de aceite

- O contrato marca onboarding como dentro da meta quando a janela `startedAtUtc -> completedAtUtc` é menor ou igual a 1 hora.
- O contrato libera a primeira emissão quando todos os pré-requisitos obrigatórios estão completos.
- O contrato bloqueia a primeira emissão quando faltar signatário principal, numeração, revisão de escopo ou QR público.
- O resumo do wizard do back-office traduz os bloqueios para passos legíveis.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/onboarding/onboarding-readiness.test.ts`
- `pnpm exec tsx --test apps/web/src/onboarding/onboarding-wizard-summary.test.ts`
- `pnpm exec tsx --test evals/ac/prd-13-12-onboarding-wizard-blocks.test.ts`
- `pnpm check:all`
