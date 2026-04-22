# 0064 - Hub canonico do modulo Qualidade

## Contexto

O PRD em `17.9.1` descreve um hub de Qualidade que concentra NCs abertas, acoes vencidas, auditoria programada, reclamacoes, riscos ativos e a proxima analise critica. O repositorio ja materializa leituras canonicas de trilha de auditoria e nao conformidades, mas ainda nao possui uma porta de entrada unica para o gestor da qualidade enxergar o recorte operacional e distinguir claramente o que ja esta implementado do que continua planejado.

Sem esse hub, o back-office depende de links soltos entre workspace, trilha e NC, enquanto areas previstas no PRD como reclamacoes, riscos/imparcialidade, analise critica, documentos e indicadores permanecem invisiveis como backlog auditavel.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para o hub de Qualidade contendo:
  - resumo executivo do recorte;
  - modulos do hub com status operacional;
  - disponibilidade explicita (`implemented` ou `planned`) para cada area;
  - links de contexto para workspace, configuracoes, trilha e NC.
- Implementar em `apps/api/src/domain/quality` um builder canonico do hub com cenarios deterministas para:
  - acompanhamento preventivo;
  - resposta critica;
  - baseline estavel.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /quality`.
- Materializar em `apps/web/src` o loader e o view model do hub.
- Adicionar a pagina `apps/web/app/quality/page.tsx`.
- Integrar o hub na home do back-office e costurar a navegacao com as leituras ja existentes de Qualidade.

## Fora de escopo

- Criar workflows transacionais reais de reclamacoes, riscos/imparcialidade, analise critica, documentos ou indicadores.
- Persistir backlog de Qualidade em banco, anexos binarios, aprovacoes, tarefas, SLA real ou exportacoes.
- Substituir os modulos canonicos de trilha de auditoria e nao conformidades ja existentes; o hub apenas os consolida.

## Criterios de aceite

- O contrato compartilhado representa resumo executivo, modulos, disponibilidade de implementacao e links de contexto do hub.
- O builder backend oferece tres cenarios canonicos e marca fail-closed apenas quando o recorte indicar bloqueio operacional real, nao apenas backlog planejado.
- O endpoint `GET /quality` responde com catalogo tipado e permite selecionar cenario e modulo por querystring.
- A pagina web explicita:
  - contadores executivos do hub;
  - modulos ja implementados com links clicaveis;
  - areas ainda planejadas sem inventar payload transacional;
  - links de retorno para workspace, trilha e NC coerentes com o recorte selecionado.
- A home operacional passa a expor o hub de Qualidade como mais uma rota canonica do back-office.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
