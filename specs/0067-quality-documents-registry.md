# 0067 - Modulo canonico de documentos da qualidade

## Contexto

O PRD em `17.9.8` descreve o modulo de documentos da Qualidade com lista de MQ/PG/PT/IT/FR, revisao, vigencia e consulta de historico obsoleto. O repositório ja possui `registry/procedures`, mas esse cadastro cobre o recorte tecnico-operacional e nao substitui a governanca do SGQ prevista no hub de Qualidade.

Sem esta fatia, o gestor da qualidade continua vendo a area de documentos apenas como backlog no hub, sem uma rota canonica para revisar manual, procedimentos gerais, formularios, revisoes vigentes e historico obsoleto.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - resumo do modulo documental;
  - lista de documentos MQ/PG/PT/IT/FR;
  - detalhe do documento selecionado;
  - links contextuais para configuracoes, riscos e procedimentos tecnicos quando aplicavel.
- Implementar em `apps/api/src/domain/quality` um builder canonico com cenarios para:
  - carteira vigente e rastreavel;
  - revisao preventiva em andamento;
  - consulta bloqueada de revisao obsoleta.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /quality/documents`.
- Materializar em `apps/web/src` o loader e o view model do modulo.
- Adicionar a pagina `apps/web/app/quality/documents/page.tsx`.
- Integrar o modulo ao hub de Qualidade, promovendo `documents` de planejado para implementado.

## Fora de escopo

- Workflow transacional real de aprovacao, assinatura eletrônica, upload/download binario ou publicacao com versionamento persistido.
- Editor rich-text, diff documental, comentarios colaborativos ou integracao externa com GED.
- Substituir `registry/procedures`; o modulo de Qualidade apenas referencia documentos e liga o contexto quando o item for tecnico.

## Criterios de aceite

- O contrato compartilhado representa resumo, lista, detalhe e links contextuais do modulo documental.
- O builder backend oferece:
  - um cenario operacional com documentos vigentes;
  - um cenario de revisao preventiva em andamento;
  - um cenario bloqueado para revisao obsoleta mantida apenas para historico.
- O endpoint `GET /quality/documents` responde com catalogo tipado e permite selecionar cenario e documento por querystring.
- A pagina web traduz classificacao, vigencia, revisao, artefatos relacionados, bloqueios, warnings e atalhos para hub, configuracoes, riscos e procedimentos.
- O hub de Qualidade passa a tratar `documents` como modulo implementado com link clicavel.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/quality/quality-document-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/quality-document-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
