# Spec 0074 — V1 foundation persistida para auth, onboarding e workspace

## Contexto

O roadmap foundation-first deslocou a V1 para uma base tecnica real, mas o nucleo ainda dependia de catalogos canonicos sem persistencia para auth, onboarding e workspace. Isso impedia fechar `V1.1` a `V1.5` do backlog executavel em `compliance/roadmap/execution-backlog.yaml`.

## Objetivo

Materializar a fundacao persistida de V1 com:

- schema inicial Prisma para organizacoes, usuarios, competencias, sessoes e onboarding;
- migracao versionada e seed deterministico do tenant demo;
- login real com sessao HTTP-only e RBAC nas rotas centrais;
- bootstrap inicial do tenant e atualizacao persistida do onboarding;
- pages `apps/web` lendo cookie de sessao e operando em fail-closed quando a sessao faltar.

## Escopo

- `packages/db/prisma/**`
- `apps/api/src/domain/auth/**`
- `apps/api/src/interfaces/http/auth-session.ts`
- `apps/api/src/interfaces/http/onboarding.ts`
- `apps/api/src/interfaces/http/user-directory.ts`
- `apps/api/src/interfaces/http/emission-workspace.ts`
- `apps/web/app/auth/login/**`
- `apps/web/app/onboarding/page.tsx`
- `apps/web/app/auth/users/page.tsx`
- `apps/web/app/emission/workspace/page.tsx`
- `apps/web/app/page.tsx`

## Regras

- `?scenario=` continua existindo para preservar cobertura dos catalogos canonicos e testes atuais.
- Sem `scenario`, as rotas centrais passam a preferir o caminho persistido.
- Rotas protegidas falham fechado com `401/403` quando a sessao ou o papel nao atendem ao gate.
- O seed deve gerar um tenant demo deterministico com credencial operacional previsivel.
- Scripts de banco precisam funcionar em workspace PNPM sem assumir `node_modules` local da pasta.

## Aceite

- `pnpm db:generate` gera Prisma Client para o schema V1.
- A migracao `202604230001_v1_core_foundation` cria as tabelas e policies multitenant basicas.
- `POST /auth/login` cria sessao persistida e `GET /auth/session` reflete o tenant autenticado.
- `GET /auth/users`, `GET /onboarding/readiness` e `GET /emission/workspace` passam a responder com dados persistidos quando chamados sem `scenario`.
- `POST /onboarding/bootstrap` cria organizacao + admin iniciais.
- `POST /onboarding/readiness` atualiza o wizard persistido do tenant autenticado.
- `apps/web` oferece login real, bootstrap inicial e leitura protegida das paginas V1.

## Verificacao

- `pnpm typecheck`
- `pnpm test:tools`
- `pnpm test:tenancy`
- `pnpm check:all`
