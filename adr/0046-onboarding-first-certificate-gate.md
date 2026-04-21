# ADR 0046 — Prontidão do onboarding bloqueia a primeira emissão até todos os pré-requisitos

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0043-prd-13-12-onboarding-wizard-blocks.md`, `PRD.md` §13.12

## Contexto

O wizard de onboarding ainda não existe como aplicação real. Para validar o requisito imediatamente, é suficiente um contrato puro que calcule a meta de 1 hora e a liberação da primeira emissão com base em pré-requisitos mandatórios.

## Decisão

1. `apps/api/src/domain/onboarding/onboarding-readiness.ts` passa a exportar `evaluateOnboardingReadiness()`.
2. A função calcula se o onboarding foi concluído em até 1 hora.
3. A primeira emissão permanece bloqueada enquanto faltar qualquer pré-requisito obrigatório.
4. `apps/web/src/onboarding/onboarding-wizard-summary.ts` transforma razões de bloqueio em etapas legíveis do wizard.
5. A decisão é fail-closed: ausência de signatário principal, numeração, escopo/CMC ou QR público impede a primeira emissão.

## Consequências

- O PRD §13.12 ganha evidência executável sem depender da UI final.
- O futuro wizard pode consumir diretamente a lista de bloqueios produzida pela camada de domínio.
- A meta temporal e o gate de primeira emissão ficam explícitos e testáveis.

## Limitações honestas

- A ADR não mede tempo real de interação do usuário; opera sobre timestamps informados.
- Não existe persistência nem workflow real de conclusão de etapas.
- O contrato ainda não cobre analytics de abandono, convites ou automações de e-mail.
