# 0002 — Rastreabilidade dos critérios de aceite do MVP

## Contexto

O PRD §13 define 22 critérios de aceite do MVP. A primeira fatia do dossiê validava apenas os gates executáveis do harness, deixando 19 critérios sem requisito formal em `requirements.yaml`.

Esta spec transforma todos os critérios do PRD §13 em requisitos rastreáveis sem declarar como validado aquilo que ainda não possui implementação e teste ativo.

## Escopo

- Mapear cada critério do PRD §13 para um requisito estável `REQ-PRD-13-*`.
- Diferenciar requisitos planejados de requisitos validados por teste ativo.
- Registrar caminhos de testes planejados para orientar as próximas fatias verticais.
- Manter o relatório de cobertura honesto: mapeado não significa implementado.

## Fora de escopo

- Implementar as fatias de produto do Android, web, portal ou backend.
- Criar testes de domínio ainda sem código correspondente.
- Marcar P0-3 como concluído.
- Alterar o texto do PRD §13.

## Requisitos

- REQ-PRD-13-01-MOBILE-OFFLINE-CALIBRATION
- REQ-PRD-13-02-STANDARD-ELIGIBILITY-BLOCK
- REQ-PRD-13-03-CERTIFICATE-MEASUREMENT-DECLARATIONS
- REQ-PRD-13-04-TECHNICAL-REVIEW-SIGNATURE-AUDIT
- REQ-PRD-13-05-PUBLIC-QR-AUTHENTICITY
- REQ-PRD-13-06-CRITICAL-EVENT-AUDIT-TRAIL
- REQ-PRD-13-07-ANDROID-SYNC-IDEMPOTENCY
- REQ-PRD-13-08-EQUIPMENT-CUSTOMER-ADDRESS
- REQ-PRD-13-09-SIGNATORY-COMPETENCE-BLOCK
- REQ-PRD-13-10-SCOPE-CMC-BLOCK
- REQ-PRD-13-11-AUTH-SSO-MFA
- REQ-PRD-13-12-ONBOARDING-WIZARD-BLOCKS
- REQ-PRD-13-14-SEQUENTIAL-NUMBERING
- REQ-PRD-13-15-REGULATORY-PROFILES-PDF
- REQ-PRD-13-16-CONTROLLED-REISSUE
- REQ-PRD-13-17-PUBLIC-QR-MINIMAL-METADATA
- REQ-PRD-13-20-OFFLINE-SYNC-CHAOS
- REQ-PRD-13-21-LEGAL-OPINION-DPA
- REQ-PRD-13-22-NORMATIVE-GOVERNANCE-OWNER

## Critérios de aceite

- `pnpm validation-dossier:check --strict-prd` não falha por critério do PRD §13 sem requisito mapeado.
- `coverage-report.md` separa critérios validados por teste ativo de critérios apenas mapeados.
- Requisitos planejados usam `validation_status: planned` e não exigem arquivo de teste existente.
- Requisitos validados continuam exigindo `linked_tests` existentes.
- Próximas fatias de produto convertem requisitos planejados para `validation_status: validated` somente quando houver implementação e teste ativo.

## Evidência

Evidência de execução permanece em `compliance/validation-dossier/evidence/<REQ-id>/`. Enquanto o requisito estiver planejado, o dossiê lista `planned_tests` como alvo de validação futura, sem criar evidência artificial.
