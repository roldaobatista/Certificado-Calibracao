# 0062 - Visualizador canonico de certificado no portal V1

## Contexto

O PRD descreve um visualizador autenticado do certificado no portal na secao 17.5.5, com status, hash, assinatura verificada e acoes como baixar PDF, compartilhar link publico e imprimir. As fatias anteriores entregaram dashboard, carteira e detalhe do equipamento, mas o fluxo ainda termina apenas na verificacao publica.

Sem essa fatia, o cliente consegue confirmar autenticidade minimizada, porem ainda nao navega por uma leitura canonica do certificado logado com metadados, acoes e orientacao de verificacao.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - lista canonica de certificados do recorte selecionado;
  - resumo do visualizador;
  - detalhe do certificado com metadados, acoes e orientacao de verificacao.
- Implementar em `apps/api/src/domain/portal` um builder canonico do visualizador autenticado.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /portal/certificate`.
- Materializar em `apps/portal/src` o loader e o view model para a leitura do certificado.
- Adicionar a pagina `apps/portal/app/certificate/page.tsx`.
- Integrar dashboard e detalhe do equipamento com atalhos para o visualizador do certificado.

## Fora de escopo

- Download real de PDF, streaming do arquivo, impressao real ou compartilhamento transacional do link.
- Sessao autenticada real, controle fino de permissao por usuario final ou expiracao de signed URL.
- Comparativo binario de revisoes, anotacoes do cliente ou comentario persistido.

## Criterios de aceite

- O contrato compartilhado representa lista, resumo e detalhe do certificado selecionado com hash, assinatura, metadados, acoes e orientacao de verificacao.
- O builder canonico oferece um cenario valido, um cenario de reemissao rastreada e um cenario fail-closed para visualizacao bloqueada.
- O endpoint `GET /portal/certificate` responde com catalogo tipado e selecao por querystring.
- A pagina do portal traduz o visualizador autenticado do certificado e permanece fail-closed sem payload valido do backend.
- Dashboard e detalhe do equipamento passam a abrir o visualizador canonico do certificado.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/portal/portal-certificate-scenarios.test.ts`
- `pnpm exec tsx --test apps/portal/src/portal-certificate-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
