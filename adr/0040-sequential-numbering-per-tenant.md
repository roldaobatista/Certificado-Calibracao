# ADR 0040 — Reserva de número de certificado com isolamento por tenant

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0037-prd-13-14-sequential-numbering.md`, `PRD.md` §13.14

## Contexto

A numeração de certificados precisa ser sequencial por organização sem permitir colisão entre tenants. Como ainda não existe persistência real desse fluxo, o contrato mais imediato é uma função pura que receba o histórico emitido e reserve o próximo número de forma determinística.

## Decisão

1. `packages/db` passa a exportar `reserveSequentialCertificateNumber()`.
2. O número público segue o formato `<ORGCODE>-<NNNNNN>`.
3. A sequência ordinal é calculada por `organizationId`.
4. O contrato falha fechado quando detectar colisão prévia, prefixo inconsistente para a mesma organização ou dados mínimos ausentes.

## Consequências

- O requisito do PRD ganha evidência executável sem depender de banco real.
- O backend futuro pode reaproveitar a mesma lógica como camada de domínio antes da transação.
- O número público fica naturalmente isolado entre tenants pelo prefixo.
