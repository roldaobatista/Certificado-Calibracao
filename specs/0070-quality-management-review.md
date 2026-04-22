# 0070 - Modulo canonico de analise critica pela direcao

## Contexto

O PRD em `17.9.7` descreve a analise critica pela direcao com pauta padrao, entradas automaticas do sistema, ata e deliberacoes. O hub de Qualidade hoje preserva apenas a proxima janela da reuniao, mas ainda trata a area como backlog planejado, sem uma rota canonica para consolidar inputs de NCs, reclamacoes, riscos, indicadores e auditoria interna em uma mesma leitura.

Sem esta fatia, o gestor da Qualidade continua navegando por modulos isolados para preparar a reuniao, sem um painel unico que represente pauta, entradas automaticas e decisoes abertas de forma auditavel.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - resumo executivo da analise critica;
  - historico/lista de reunioes e pautas;
  - detalhe da reuniao selecionada com agenda, entradas automaticas e deliberacoes.
- Implementar em `apps/api/src/domain/quality` um builder canonico com cenarios para:
  - reuniao ordinaria encerrada e arquivada;
  - pauta ordinaria preparada, mas com pendencias preventivas;
  - reuniao extraordinaria bloqueante para recorte critico.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /quality/management-review`.
- Materializar em `apps/web/src` o loader e o view model do modulo.
- Adicionar a pagina `apps/web/app/quality/management-review/page.tsx`.
- Integrar o modulo ao hub de Qualidade, promovendo `management-review` de planejado para implementado.

## Fora de escopo

- Workflow transacional real de iniciar ata, colher assinaturas, convocar participantes ou sincronizar calendario.
- Geracao automatica de PDF/ata binaria, voto formal ou aprovacao eletrônica.
- Substituir NCs, riscos, indicadores, auditoria interna, reclamacoes ou trilha; o modulo apenas consolida essas leituras quando houver contexto.

## Criterios de aceite

- O contrato compartilhado representa resumo, historico de reunioes, pauta, entradas automaticas e deliberacoes do modulo.
- O builder backend oferece:
  - um cenario estavel com reuniao ordinaria arquivada;
  - um cenario de atencao com pauta pronta, mas pendencias preventivas abertas;
  - um cenario bloqueado para reuniao extraordinaria antes de qualquer liberacao do caso critico.
- O endpoint `GET /quality/management-review` responde com catalogo tipado e permite selecionar cenario e reuniao por querystring.
- A pagina web traduz pauta, entradas automaticas, deliberacoes, warnings, bloqueios e atalhos para os modulos de origem quando houver contexto.
- O hub de Qualidade passa a tratar `management-review` como modulo implementado com link clicavel.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/quality/management-review-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/management-review-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/api/src/domain/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
