# 0068 - Modulo canonico de indicadores da qualidade

## Contexto

O PRD em `17.9.9` descreve um painel de indicadores da Qualidade com recorte dos ultimos 12 meses, metas explicitas e consolidacao para analise critica. O hub de Qualidade ja sinaliza a necessidade de indicadores, mas ainda trata a area apenas como backlog planejado, sem uma rota canonica para inspecionar tendencias de reemissao, NC, tempo medio por OS, SLA de acoes corretivas, eficacia das acoes e satisfacao do cliente.

Sem esta fatia, o gestor da Qualidade continua dependendo do hub, de NCs, reclamacoes e riscos em separado, sem uma leitura gerencial unica que sustente a pauta automatica prevista no PRD para analise critica.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - resumo executivo do painel de indicadores;
  - lista de indicadores com valor atual, meta, tendencia e owner;
  - detalhe do indicador selecionado com snapshots mensais, evidencia e links contextuais.
- Implementar em `apps/api/src/domain/quality` um builder canonico com cenarios para:
  - baseline estavel dentro da meta;
  - degradacao preventiva com SLA de acoes corretivas abaixo do objetivo;
  - deriva critica com impacto em reemissao, eficacia CAPA e satisfacao do cliente.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /quality/indicators`.
- Materializar em `apps/web/src` o loader e o view model do modulo.
- Adicionar a pagina `apps/web/app/quality/indicators/page.tsx`.
- Integrar o modulo ao hub de Qualidade, promovendo `indicators` de planejado para implementado.

## Fora de escopo

- BI real, graficos interativos, filtros persistidos, exportacao binaria, job mensal de snapshot ou integracao com data warehouse.
- Substituir analise critica, auditoria interna, NC, reclamacoes ou riscos; o modulo apenas consolida leituras canonicas e aponta contexto.
- Persistencia real dos snapshots ou definicao configuravel de metas por tenant.

## Criterios de aceite

- O contrato compartilhado representa resumo, lista, detalhe, snapshots mensais e links contextuais do painel.
- O builder backend oferece:
  - um cenario operacional estavel com indicadores dentro da meta;
  - um cenario de atencao com queda de SLA de acoes corretivas e alerta de tendencia;
  - um cenario bloqueado para deriva critica que exige resposta extraordinaria.
- O endpoint `GET /quality/indicators` responde com catalogo tipado e permite selecionar cenario e indicador por querystring.
- A pagina web traduz valor atual, meta, tendencia, snapshots, evidencia, warnings, bloqueios e atalhos para hub, NCs, reclamacoes e riscos quando aplicavel.
- O hub de Qualidade passa a tratar `indicators` como modulo implementado com link clicavel.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/quality/quality-indicator-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/quality-indicator-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/api/src/domain/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
