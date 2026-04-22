# 0071 - Modulo canonico de trabalho nao conforme

## Contexto

O PRD posiciona `trabalho nao conforme` como area propria do modulo de Qualidade em `17.9.1`, mas o unico fluxo detalhado de `7.10` aparece embutido em `17.9.4`, dentro da tratativa de nao conformidade. Ali, a acao imediata obriga suspensao ou contencao explicita antes de qualquer liberacao do recorte afetado. O PRD tambem bloqueia reemissao quando a correcao tentaria alterar leitura bruta, padrao ou ambiente, exigindo nova OS.

Hoje o hub de Qualidade apenas sinaliza essa area como backlog planejado. Sem uma leitura dedicada, o gestor precisa inferir `trabalho nao conforme` a partir de NCs, workspace, trilha, reclamacoes e documentos, o que enfraquece a rastreabilidade operacional da contencao.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - resumo executivo do recorte de `trabalho nao conforme`;
  - lista de casos internos de contencao/liberacao;
  - detalhe do caso selecionado com classificacao, entidade afetada, regra de liberacao e evidencias.
- Implementar em `apps/api/src/domain/quality` um builder canonico com cenarios para:
  - contencao preventiva ainda em acompanhamento;
  - bloqueio critico de liberacao/reemissao;
  - historico de contencao encerrado e arquivado.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /quality/nonconforming-work`.
- Materializar em `apps/web/src` o loader e o view model do modulo.
- Adicionar a pagina `apps/web/app/quality/nonconforming-work/page.tsx`.
- Integrar o modulo ao hub de Qualidade, promovendo `nonconforming-work` de planejado para implementado.

## Fora de escopo

- Criar workflow transacional real de congelar/liberar OS, lote, certificado, procedimento ou equipamento.
- Criar aprovacao eletrônica, assinatura, voto, reexecucao automatica ou abertura real de nova OS.
- Substituir NC, reclamacao, trilha, documentos, revisao tecnica ou auditoria interna; o modulo apenas consolida a leitura de contencao e liberacao a partir dessas origens.

## Criterios de aceite

- O contrato compartilhado representa resumo, lista e detalhe do recorte de `trabalho nao conforme`, incluindo regra de liberacao e evidencias.
- O builder backend oferece:
  - um cenario de atencao com contencao preventiva formalizada;
  - um cenario bloqueado com liberacao/reemissao vedadas ate decisao formal;
  - um cenario estavel com historico encerrado e mantido apenas para rastreabilidade.
- O endpoint `GET /quality/nonconforming-work` responde com catalogo tipado e permite selecionar cenario e caso por querystring.
- A pagina web traduz classificacao, entidade afetada, contencao, regra de liberacao, evidencias, warnings, bloqueios e atalhos para NC, trilha, OS, reclamacao, documentos e procedimentos quando houver contexto.
- O hub de Qualidade passa a tratar `nonconforming-work` como modulo implementado com link clicavel.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/quality/nonconforming-work-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/nonconforming-work-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/api/src/domain/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
