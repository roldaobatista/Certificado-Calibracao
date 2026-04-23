# Spec 0075 — V2 cadastros operacionais persistidos

## Contexto

A V1 foundation-first fechou autenticação, sessão, onboarding e o núcleo inicial persistido, mas os cadastros operacionais centrais ainda dependiam de catálogos canônicos estáticos. Isso impedia concluir `V2.1` a `V2.6` do backlog executável em `compliance/roadmap/execution-backlog.yaml`.

## Objetivo

Materializar a V2 completa sobre persistência real com:

- schema Prisma para clientes, padrões, históricos de calibração, procedimentos versionados, equipamentos e trilha mínima de cadastro;
- CRUD autenticado para usuários, clientes, padrões, procedimentos e equipamentos;
- filtros, busca local, arquivamento e leitura coerente entre os cadastros principais;
- páginas `apps/web` operando sobre o banco real sem depender de `?scenario=` no modo autenticado persistido.

## Escopo

- `packages/db/prisma/**`
- `apps/api/src/domain/auth/core-persistence.ts`
- `apps/api/src/domain/registry/**`
- `apps/api/src/interfaces/http/*registry*.ts`
- `apps/api/src/interfaces/http/user-directory.ts`
- `apps/api/src/app.ts`
- `apps/web/src/auth/user-directory-api.ts`
- `apps/web/src/registry/*`
- `apps/web/app/auth/users/page.tsx`
- `apps/web/app/registry/**`

## Regras

- `?scenario=` continua obrigatório como fallback para preservar a cobertura canônica e os testes existentes.
- Sem `scenario`, os cadastros V2 passam a preferir o caminho persistido protegido por sessão.
- Escrita e arquivamento exigem RBAC de gestão (`admin` ou `quality_manager`).
- Equipamentos falham fechado sem cliente, procedimento, padrão principal e endereço mínimo.
- A trilha mínima deve registrar criação, atualização e arquivamento em `registry_audit_events`.

## Aceite

- `pnpm db:generate` gera Prisma Client com o schema V2.
- A migração `202604230002_v2_registry_core` cria tabelas, índices, RLS e policies do núcleo de cadastros.
- `GET /auth/users`, `GET /registry/customers`, `GET /registry/equipment`, `GET /registry/standards` e `GET /registry/procedures` respondem com dados persistidos quando chamados sem `scenario`.
- `POST /auth/users/manage`, `POST /registry/customers/manage`, `POST /registry/equipment/manage`, `POST /registry/standards/manage` e `POST /registry/procedures/manage` criam, editam e arquivam dados reais do tenant.
- `apps/web` oferece filtros, formulários reais e navegação persistida nas páginas de usuários, clientes, equipamentos, padrões e procedimentos.

## Verificação

- `pnpm db:generate`
- `pnpm --filter @afere/api typecheck`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm --filter @afere/web typecheck`
- `pnpm check:all`
- `pnpm test:tenancy`
