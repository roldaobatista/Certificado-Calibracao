# 0054 — Cadastro canonico de clientes e equipamentos para V1

## Contexto

O PRD detalha no back-office uma lista de clientes (§17.4.7), um detalhe do cliente em abas (§17.4.8) e uma lista global de equipamentos (§17.4.9). O repositorio ja possui dry-run de emissao, revisao tecnica de OS, previa do certificado e fila de assinatura, mas ainda nao materializa a leitura canonica dos cadastros que sustentam o requisito de equipamento vinculado a cliente com endereco minimo valido (§13.08).

Sem essa fatia, o operador consegue revisar a emissao, mas ainda nao enxerga de forma auditavel quais clientes estao ativos, quais equipamentos dependem de saneamento cadastral e qual detalhe do cliente sustenta a operacao antes da emissao.

## Escopo

- Adicionar em `packages/contracts` contratos compartilhados para:
  - lista e detalhe canonico de clientes;
  - lista global e detalhe resumido de equipamentos;
  - status e cenarios canonicos de cadastro.
- Implementar em `apps/api/src/domain/registry` builders canonicos para clientes e equipamentos, reaproveitando o dominio ja existente de validacao de cadastro do equipamento.
- Expor em `apps/api/src/interfaces/http` os endpoints canonicos:
  - `GET /registry/customers`
  - `GET /registry/equipment`
- Materializar em `apps/web/src/registry` view models e loaders legiveis para os catalogos.
- Adicionar as paginas:
  - `apps/web/app/registry/customers/page.tsx`
  - `apps/web/app/registry/customer-detail/page.tsx`
  - `apps/web/app/registry/equipment/page.tsx`
- Integrar atalhos para os novos cadastros a partir do workspace e da revisao tecnica da OS.

## Fora de escopo

- CRUD real de clientes, equipamentos, contratos, anexos ou certificados no banco.
- Filtros reais, paginacao real, busca textual persistida ou upload/download de anexos.
- Detalhe completo de equipamento em tela propria dedicada.
- Portal autenticado do cliente, notificacoes e emissao transacional real.

## Critérios de aceite

- O contrato compartilhado representa resumo da lista de clientes, detalhe do cliente em abas e lista global de equipamentos com detalhe resumido do item selecionado.
- O builder canonico marca equipamentos com cadastro incompleto usando a regra de `validateEquipmentRegistration`, sem inventar estado fora do backend.
- Um cenario operacional mostra clientes ativos, equipamentos validos e navegacao relacionada para OS, dry-run e cadastros.
- Um cenario de atencao destaca vencimentos proximos e clientes com proximas calibracoes iminentes.
- Um cenario bloqueado destaca cadastro incompleto do equipamento e falha fechada para continuidade da emissao.
- Os endpoints `GET /registry/customers` e `GET /registry/equipment` respondem com catalogos tipados e selecao por querystring.
- As paginas web traduzem os cadastros em leitura operacional legivel e permanecem fail-closed sem payload valido do backend.
- Workspace e revisao tecnica da OS passam a oferecer atalhos para clientes e equipamentos.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/registry/customer-equipment-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/registry/customer-registry-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/registry/equipment-registry-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
