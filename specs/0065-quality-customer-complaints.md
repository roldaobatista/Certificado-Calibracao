# 0065 - Modulo canonico de reclamacoes de clientes

## Contexto

O PRD em `17.9.5` descreve a leitura operacional de uma reclamacao de cliente com severidade, prazo de resposta, vinculo a NC, gatilho de reemissao e resposta formal. O repositório ja possui hub de Qualidade, trilha de auditoria e nao conformidades, mas ainda trata reclamacoes apenas como backlog explicito dentro do hub.

Sem esta fatia, o gestor da qualidade enxerga a contagem de reclamacoes no hub, porém continua sem uma rota canonica para inspecionar relato, prazo, checklist de resposta e vinculos com NC, trilha e reemissao.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - resumo do modulo de reclamacoes;
  - lista de reclamacoes no recorte selecionado;
  - detalhe da reclamacao com checklist de acoes;
  - links para NC, trilha, workspace e OS relacionada.
- Implementar em `apps/api/src/domain/quality` um builder canonico com cenarios para:
  - acompanhamento aberto;
  - resposta critica com reemissao pendente;
  - historico resolvido.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /quality/complaints`.
- Materializar em `apps/web/src` o loader e o view model do modulo.
- Adicionar a pagina `apps/web/app/quality/complaints/page.tsx`.
- Integrar o modulo ao hub de Qualidade e costurar navegacao minima a partir de trilha e NC.

## Fora de escopo

- Persistencia real das reclamacoes, envio de e-mail, SLA transacional, anexos binarios, workflow de aprovacao, tickets ou reemissao real.
- Substituir NC, trilha de auditoria ou reemissao controlada; o modulo apenas aponta para esses fluxos canonicos.
- Criar analytics de produtividade, exportacao ou portal externo de atendimento.

## Criterios de aceite

- O contrato compartilhado representa resumo, itens, detalhe e checklist de acoes da reclamacao com links de contexto.
- O builder backend oferece:
  - um cenario aberto em acompanhamento;
  - um cenario critico com reemissao e resposta formal pendentes;
  - um cenario resolvido mantido para historico auditavel.
- O endpoint `GET /quality/complaints` responde com catalogo tipado e permite selecionar cenario e reclamacao por querystring.
- A pagina web traduz relato, prazo, acoes, bloqueios, warnings e atalhos para NC, trilha, workspace e OS.
- O hub de Qualidade passa a tratar reclamacoes como modulo implementado, com link clicavel em vez de backlog apenas planejado.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/quality/complaint-registry-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/complaint-registry-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
