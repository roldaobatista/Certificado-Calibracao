# Spec 0077 — V3 completa do fluxo persistido de emissao

## Contexto

A V3.1 abriu a ordem de servico real, mas o restante do fluxo central ainda dependia de cenarios canonicos. O backlog executavel define `V3.2` a `V3.5` como a conclusao do nucleo operacional: resultado tecnico persistido, revisao formal, assinatura eletronica e emissao com numeracao e trilha critica reais.

## Objetivo

Fechar a V3 completa sobre registros persistidos do tenant autenticado com:

- resultados tecnicos e declaracoes metrologicas gravados na OS real;
- workflow persistido de revisao tecnica com revisor, parecer, comentario e device;
- assinatura eletronica real antes da emissao;
- emissao oficial com numeracao sequencial, hash documental, token publico e trilha critica append-only;
- `apps/web` navegando no modo persistido entre dry-run, previa, workflow, fila e auditoria sem regressao para `?scenario=`.

## Escopo

- `packages/db/prisma/**`
- `packages/contracts/src/service-order-review.ts`
- `apps/api/src/domain/emission/**`
- `apps/api/src/interfaces/http/emission-dry-run.ts`
- `apps/api/src/interfaces/http/certificate-preview.ts`
- `apps/api/src/interfaces/http/review-signature.ts`
- `apps/api/src/interfaces/http/signature-queue.ts`
- `apps/api/src/interfaces/http/audit-trail.ts`
- `apps/api/src/interfaces/http/service-order-review.ts`
- `apps/api/src/app.ts`
- `apps/web/app/emission/**`
- `apps/web/app/quality/audit-trail/page.tsx`
- `apps/web/src/emission/**`
- `apps/web/src/quality/audit-trail-api.ts`

## Regras

- `?scenario=` continua existindo como fallback canonico; sem `scenario`, as rotas V3 preferem leitura persistida protegida por sessao.
- Nenhuma emissao avanca sem revisao aprovada, signatario com papel elegivel e MFA ativo.
- A numeracao sequencial falha fechado se houver colisao, prefixo invalido ou historico inconsistente.
- A trilha critica de emissao e append-only e precisa verificar hash-chain, eventos criticos e coerencia de revisao/assinatura.
- O front em modo persistido deve propagar o `item` atual entre paginas da V3 para evitar cair acidentalmente no fluxo demonstrativo.

## Aceite

- A OS persistida guarda resultado de medicao, U expandida, fator de abrangencia, unidade, regra de decisao, resultado da decisao e declaracao livre.
- `GET /emission/dry-run`, `GET /emission/certificate-preview`, `GET /emission/review-signature`, `GET /emission/signature-queue` e `GET /quality/audit-trail` respondem com catalogos persistidos quando chamados sem `scenario` e com cookie valido.
- `POST /emission/review-signature/manage` registra revisor, signatario, decisao, comentario, device e transicao de workflow.
- `POST /emission/signature-queue/manage` conclui assinatura e emissao com numero sequencial, hash documental, token publico e eventos criticos append-only.
- `apps/web` mantem navegacao persistida ponta a ponta e expoe os campos tecnicos reais na tela de OS.
- O seed local demonstra pelo menos um item em revisao aprovada, um emitido e um bloqueado com trilha critica correspondente.

## Verificacao

- `pnpm db:generate`
- `pnpm --filter @afere/contracts build`
- `pnpm --filter @afere/api typecheck`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm --filter @afere/web typecheck`
- `pnpm check:all`
- `pnpm test:tenancy`
