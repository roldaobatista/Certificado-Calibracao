# Spec 0076 — V3.1 ordem de serviço persistida

## Contexto

A V2 fechou os cadastros operacionais persistidos, mas a tela de OS em `apps/web` e o endpoint `GET /emission/service-order-review` continuam presos a cenarios canônicos. Isso impede abrir `V3.1` do backlog executavel com criacao, edicao e transicao basica da ordem de servico sobre registros reais.

## Objetivo

Materializar a primeira fatia persistida de OS com:

- schema Prisma para ordens de servico vinculadas a cliente, equipamento, procedimento, padrao e atores reais;
- leitura autenticada de `GET /emission/service-order-review` sem `?scenario=`, reaproveitando o contrato canonico atual;
- escrita autenticada em `POST /emission/service-order-review/manage` para criar, editar e mover a OS pelo ciclo basico;
- `apps/web` operando sobre o tenant autenticado com formulario real de abertura e manutencao da OS.

## Escopo

- `packages/db/prisma/**`
- `apps/api/src/domain/emission/**`
- `apps/api/src/interfaces/http/service-order-review.ts`
- `apps/api/src/interfaces/http/auth-session.ts`
- `apps/api/src/app.ts`
- `apps/web/src/emission/service-order-review-api.ts`
- `apps/web/app/emission/service-order-review/page.tsx`
- `apps/web/app/page.tsx`

## Regras

- `?scenario=` continua como fallback canonico para preservar a cobertura existente.
- Sem `scenario`, a rota de OS passa a preferir o caminho persistido protegido por sessao.
- A OS falha fechado se cliente, equipamento, procedimento, padrao principal ou tecnico nao existirem no tenant autenticado.
- O equipamento selecionado deve pertencer ao cliente informado.
- Se o equipamento ja tiver procedimento ou padrao principal vinculado, a OS so pode persistir com o mesmo recorte.
- A trilha V3.1 registra timestamps minimos do ciclo (`created`, `accepted`, `in_execution`, `executed`, `review`, `signature`, `emitted`) sem se apresentar como substituta do audit trail critico de emissao.

## Aceite

- `pnpm db:generate` gera Prisma Client com o schema V3.1.
- A migracao `202604230003_v3_service_orders` cria tabela, indices, RLS e policies das OS persistidas.
- `GET /emission/service-order-review` responde com dados persistidos quando chamado sem `scenario` e com cookie valido.
- `POST /emission/service-order-review/manage` cria e atualiza OS reais do tenant, incluindo transicao basica de status.
- `apps/web/app/emission/service-order-review/page.tsx` oferece formulario real de abertura e manutencao da OS quando autenticado.
- A home operacional passa a ler o catalogo real de OS com o cookie atual.

## Verificacao

- `pnpm db:generate`
- `pnpm --filter @afere/api typecheck`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm --filter @afere/web typecheck`
- `pnpm check:all`
- `pnpm test:tenancy`
