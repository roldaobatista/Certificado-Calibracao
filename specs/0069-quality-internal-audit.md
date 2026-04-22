# 0069 - Modulo canonico de auditoria interna da qualidade

## Contexto

O PRD em `17.9.2` e `17.9.3` descreve o programa anual de auditoria interna com ciclos, escopo auditado, checklist aplicado, evidencias e NCs geradas. O hub de Qualidade hoje preserva apenas a contagem de auditorias programadas, mas ainda trata a area como backlog planejado, sem uma rota canonica para navegar pelo programa anual, pelo ciclo em execucao ou por um caso extraordinario.

Sem esta fatia, o gestor da Qualidade continua dependendo do hub, de NCs e de indicadores em separado para reconstruir o contexto da auditoria interna, sem uma leitura unica que sustente o programa anual e a conexao com achados e follow-up.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - resumo executivo do programa anual de auditoria interna;
  - lista de ciclos com janela, escopo, auditor e status;
  - detalhe do ciclo selecionado com checklist, achados, evidencias e links contextuais.
- Implementar em `apps/api/src/domain/quality` um builder canonico com cenarios para:
  - programa anual em trilho;
  - follow-up de ciclo com NCs ainda em tratamento;
  - escalacao extraordinaria para um ciclo critico adicional.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /quality/internal-audit`.
- Materializar em `apps/web/src` o loader e o view model do modulo.
- Adicionar a pagina `apps/web/app/quality/internal-audit/page.tsx`.
- Integrar o modulo ao hub de Qualidade, promovendo `internal-audit` de planejado para implementado.

## Fora de escopo

- Workflow transacional real de abertura/encerramento de ciclo, upload binario de relatorio, assinatura eletrônica do parecer ou agenda/calendario.
- Geração automática de checklist a partir de template externo; o modulo apenas materializa uma leitura canonica deterministica.
- Substituir NCs, indicadores, documentos ou analise critica; o modulo apenas costura essas leituras quando houver contexto.

## Criterios de aceite

- O contrato compartilhado representa resumo, lista de ciclos, checklist, achados e links contextuais do modulo.
- O builder backend oferece:
  - um cenario estavel com programa anual controlado;
  - um cenario de atencao com ciclo concluido e NCs ainda em follow-up;
  - um cenario bloqueado para auditoria extraordinaria exigida por caso critico.
- O endpoint `GET /quality/internal-audit` responde com catalogo tipado e permite selecionar cenario e ciclo por querystring.
- A pagina web traduz janela, escopo, checklist, achados, evidencias, warnings, bloqueios e atalhos para hub e NCs quando aplicavel.
- O hub de Qualidade passa a tratar `internal-audit` como modulo implementado com link clicavel.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/quality/internal-audit-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/internal-audit-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/api/src/domain/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/quality-hub-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
