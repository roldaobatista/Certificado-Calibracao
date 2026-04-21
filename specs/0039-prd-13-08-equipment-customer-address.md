# 0039 — Cadastro de equipamento exige cliente e endereço

## Contexto

O PRD §13.8 exige que o cadastro de equipamento tenha vínculo obrigatório com cliente e endereço. Ainda não há um contrato executável no backend que bloqueie o cadastro incompleto em fail-closed.

## Escopo

- Adicionar em `apps/api/src/domain/equipment` uma API que valide o payload mínimo de cadastro de equipamento.
- Exigir `customerId` e endereço completo do local do equipamento.
- Tratar campos vazios ou em branco como ausentes.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-08-equipment-customer-address.test.ts`.
- Promover `REQ-PRD-13-08-EQUIPMENT-CUSTOMER-ADDRESS` para `validated` se a evidência ficar verde.

## Fora de escopo

- Persistência real em banco.
- Geocodificação, CEP, coordenadas ou múltiplos endereços.
- Regras comerciais além do vínculo obrigatório com cliente.

## Critérios de aceite

- A API aceita o cadastro quando cliente e endereço completo estiverem presentes.
- A API falha fechado quando `customerId` faltar.
- A API falha fechado quando qualquer campo obrigatório do endereço estiver ausente ou em branco.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/equipment/equipment-registration.test.ts`
- `pnpm exec tsx --test evals/ac/prd-13-08-equipment-customer-address.test.ts`
- `pnpm check:all`
