# 0061 - Lista e detalhe canonicos de equipamentos do cliente no portal V1

## Contexto

O PRD descreve a lista de equipamentos do cliente e o detalhe do equipamento com historico de certificados nas secoes 17.5.3 e 17.5.4. A fatia anterior entregou o dashboard do cliente, mas ele ainda nao desemboca em uma leitura canonica da carteira de equipamentos.

Sem essa fatia, o portal aponta vencimentos e certificados recentes, porem o cliente ainda nao consegue navegar para a lista consolidada dos seus instrumentos nem para o detalhe do item selecionado.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - lista canonica dos equipamentos do cliente;
  - resumo da carteira do recorte selecionado;
  - detalhe do equipamento com historico de certificados.
- Implementar em `apps/api/src/domain/portal` um builder canonico para a carteira do cliente.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /portal/equipment`.
- Materializar em `apps/portal/src` o loader e o view model para a lista e o detalhe.
- Adicionar a pagina `apps/portal/app/equipment/page.tsx`.
- Integrar o dashboard do portal com atalhos para a lista e o detalhe do equipamento.

## Fora de escopo

- Busca real com indice, filtros persistidos, paginacao ou permissao por usuario final.
- Download autenticado de PDF, visualizador integral do certificado e solicitacao transacional de nova calibracao.
- Edicao do cadastro do equipamento pelo cliente.

## Criterios de aceite

- O contrato compartilhado representa lista, resumo e detalhe do equipamento selecionado com historico de certificados.
- O builder canonico oferece um cenario estavel, um cenario com vencimentos proximos e um cenario bloqueado por equipamento vencido.
- O endpoint `GET /portal/equipment` responde com catalogo tipado e selecao por querystring.
- A pagina do portal traduz a carteira do cliente em leitura operacional e permanece fail-closed sem payload valido do backend.
- O dashboard do portal passa a abrir a lista/detalhe canonicamente tipados do equipamento.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/portal/portal-equipment-scenarios.test.ts`
- `pnpm exec tsx --test apps/portal/src/portal-equipment-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
