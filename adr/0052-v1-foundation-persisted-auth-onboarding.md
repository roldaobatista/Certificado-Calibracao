# ADR 0052 — Fundacao persistida de V1 para auth, onboarding e workspace

## Status

Aceito

## Contexto

Os catalogos canonicos de V1 eram uteis para leitura e ACs, mas ainda nao sustentavam sessao, onboarding e workspace sobre dados persistidos. O backlog foundation-first passou a exigir fundacao real antes de abrir V2.

## Decisao

Adotar uma fundacao persistida enxuta para V1 com os seguintes pilares:

1. `packages/db/prisma/schema.prisma` passa a modelar `organizations`, `app_users`, `user_competencies`, `app_sessions` e `onboarding_states`.
2. A primeira migracao V1 registra as tabelas em Postgres e habilita RLS/policies basicas com `organization_id`.
3. O backend usa cookie HTTP-only (`afere_session`) e sessao persistida para `GET /auth/session`, `POST /auth/login` e `POST /auth/logout`.
4. `GET /auth/users`, `GET /onboarding/readiness` e `GET /emission/workspace` passam a preferir persistencia real quando chamados sem `scenario`.
5. `POST /onboarding/bootstrap` cria tenant + admin iniciais e `POST /onboarding/readiness` persiste o wizard do tenant autenticado.
6. A web passa a encaminhar o cookie da requisicao atual para a API e a oferecer login/bootstrap reais.

## Consequencias

### Positivas

- Fecha a lacuna entre catalogos de demonstracao e a fundacao real exigida por `V1.1` a `V1.5`.
- Permite validar sessao, RBAC e onboarding sobre banco real sem desmontar os cenarios canonicos existentes.
- Preserva a cobertura atual de testes via `?scenario=` enquanto introduz o caminho persistido como default operacional.

### Limitacoes honestas

- O fluxo ainda nao fecha release-norm V1 nem aprova pacote normativo `v1.0.0`; isso continua dependente da governanca regulatoria do projeto.
- O onboarding persistido cobre bootstrap e prerequisitos, mas nao implementa ainda SSO/OAuth real.
- O workspace persistido ancora auth/equipe/onboarding reais, enquanto os modulos posteriores do fluxo central ainda usam leituras canonicas de V1/V3.
