# 0066 - Modulo canonico de imparcialidade e gestao de riscos

## Contexto

O PRD em `17.9.6` descreve o modulo de Qualidade para declaracoes anuais de conflito de interesse e matriz de riscos a imparcialidade/operacao. O hub de Qualidade ja expõe contagem de riscos ativos, mas ainda trata a area como backlog planejado, sem rota canonica para inspecionar declaracoes vigentes, riscos monitorados, mitigacoes ou exportacao para analise critica.

Sem esta fatia, o gestor da qualidade enxerga a pressao operacional no hub, porém continua sem uma leitura dedicada para revisar conflitos declarados, riscos criticos e responsaveis, o que empurra a governanca para memoria efemera e controles paralelos.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - resumo do modulo de imparcialidade/riscos;
  - lista de declaracoes anuais de conflito;
  - matriz de riscos com selecao do risco ativo;
  - detalhe do risco com plano de mitigacao, checklist e links contextuais.
- Implementar em `apps/api/src/domain/quality` um builder canonico com cenarios para:
  - rodada anual de declaracoes com pendencia;
  - pressao comercial critica escalada;
  - monitoramento estavel com riscos mitigados.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /quality/risk-register`.
- Materializar em `apps/web/src` o loader e o view model do modulo.
- Adicionar a pagina `apps/web/app/quality/risk-register/page.tsx`.
- Integrar o modulo ao hub de Qualidade, promovendo `risk-impartiality` de planejado para implementado.

## Fora de escopo

- Workflow transacional real de coleta de assinaturas, upload/download de PDF, envio de notificacao, exportacao efetiva de ata ou aprovacao colegiada.
- Motor de scoring quantitativo, heatmap grafico, BI externo ou integracao com RH/comercial.
- Substituir julgamento humano de imparcialidade; o sistema apenas registra declaracoes, riscos, responsaveis e mitigacoes.

## Criterios de aceite

- O contrato compartilhado representa resumo, declaracoes, matriz de riscos, detalhe do risco selecionado e links contextuais.
- O builder backend oferece:
  - um cenario de rodada anual com declaracao pendente;
  - um cenario critico com pressao comercial escalada e exportacao para analise critica pendente;
  - um cenario estavel com monitoramento e mitigacoes arquivadas.
- O endpoint `GET /quality/risk-register` responde com catalogo tipado e permite selecionar cenario e risco por querystring.
- A pagina web traduz declaracoes, risco selecionado, mitigacoes, checklist, bloqueios, warnings e atalhos para hub, configuracoes, reclamacoes e NC quando houver contexto.
- O hub de Qualidade passa a tratar imparcialidade/riscos como modulo implementado, com link clicavel em vez de backlog apenas planejado.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/quality/risk-register-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/risk-register-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
