# 0057 — Trilha de auditoria canônica no back-office V1

## Contexto

O PRD detalha uma tela de trilha de auditoria append-only no back-office (§17.4.14), com filtros operacionais e leitura exportável por evento, usuário, ação e entidade. O repositório já possui regras executáveis para hash-chain, eventos críticos, revisão/assinatura e reemissão controlada, mas ainda não materializa uma leitura canônica navegável dessa trilha no backend e na web.

Sem essa fatia, a operação valida audit trail apenas indiretamente por meio do dry-run e dos testes, mas ainda não consegue inspecionar uma timeline auditável de eventos, confirmar integridade da cadeia e navegar do evento para a OS ou o fluxo operacional correspondente.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - lista canônica de eventos da trilha de auditoria;
  - resumo com contagem de eventos críticos, reemissões e falhas de integridade;
  - detalhe do evento/chain selecionado no próprio catálogo.
- Implementar em `apps/api/src/domain/audit` um builder canônico usando `@afere/audit-log`.
- Expor em `apps/api/src/interfaces/http` o endpoint canônico `GET /quality/audit-trail`.
- Materializar em `apps/web/src/quality` o loader e o view model legível para a trilha.
- Adicionar a página `apps/web/app/quality/audit-trail/page.tsx`.
- Integrar atalhos da trilha de auditoria a partir do workspace e da revisão técnica da OS.

## Fora de escopo

- Exportação CSV real, filtros persistidos, busca full-text real e leitura do banco.
- Navegação por paginação real, stream de eventos em tempo real ou trilha multi-tenant persistida.
- Reparo de hash-chain ou workflow transacional de investigação de incidente.

## Critérios de aceite

- O contrato compartilhado representa lista de eventos, resumo operacional, filtros apresentados e detalhe da chain selecionada.
- O builder canônico usa `verifyAuditHashChain`, `verifyCriticalEventAuditTrail`, `verifyTechnicalReviewSignatureAudit` e `verifyControlledReissueAuditTrail` para classificar cenários.
- Um cenário pronto mostra cadeia íntegra com emissão recente e eventos críticos completos.
- Um cenário em atenção mostra reemissão controlada auditável, sem falha de integridade.
- Um cenário bloqueado mostra divergência de integridade ou ausência de evento crítico e permanece fail-closed.
- O endpoint `GET /quality/audit-trail` responde com catálogo tipado e seleção por querystring.
- A página web traduz a trilha de auditoria em leitura operacional legível e permanece fail-closed sem payload válido do backend.
- Workspace e revisão técnica da OS passam a oferecer atalhos coerentes para a trilha de auditoria.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/audit/audit-trail-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/audit-trail-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
