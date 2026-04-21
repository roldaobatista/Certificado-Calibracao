# ADR 0042 — Payload mínimo obrigatório para cadastro de equipamento

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0039-prd-13-08-equipment-customer-address.md`, `PRD.md` §13.8

## Contexto

O cadastro de equipamento não pode seguir para persistência sem vínculo com cliente e endereço mínimo. A ausência dessa validação hoje impediria uma prova executável do requisito.

## Decisão

1. `apps/api/src/domain/equipment` passa a exportar `validateEquipmentRegistration()`.
2. O contrato exige:
   - `customerId`;
   - `address.line1`;
   - `address.city`;
   - `address.state`;
   - `address.postalCode`;
   - `address.country`.
3. Strings vazias ou em branco contam como ausentes.
4. A decisão é fail-closed quando qualquer campo obrigatório faltar.

## Consequências

- O PRD §13.8 ganha evidência executável no domínio do backend.
- O contrato pode ser reaproveitado por API, onboarding e importadores.
- Endereço incompleto deixa de chegar à persistência por acidente.
