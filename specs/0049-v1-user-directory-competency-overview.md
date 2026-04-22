# 0049 — Gestao basica de usuarios e competencias para V1

## Contexto

O PRD §7.13 pede gestao basica de usuarios, equipes e competencias, com lista de usuarios, detalhe operacional, rastreio de dispositivos e matriz de competencias por tipo de instrumento. O repositorio ja cobre auto-cadastro, onboarding, dry-run, verificacao publica e o workflow de revisao/assinatura, mas ainda nao materializa uma leitura canonica do estado da equipe e das competencias que sustentam o RBAC de V1.

Sem essa fatia, o back-office nao consegue mostrar de forma auditavel quais usuarios estao ativos, convidados ou suspensos, nem quais competencias estao autorizadas, expirando ou expiradas para o laboratorio antes da primeira emissao.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para o diretorio de usuarios e o overview de competencias.
- Implementar em `apps/api/src/domain/auth` uma classificacao executavel de competencias em `authorized`, `expiring` e `expired`.
- Expor em `apps/api/src/interfaces/http` um endpoint canonico `GET /auth/users`.
- Materializar em `apps/web/src/auth` um view model para o diretorio de usuarios e competencias.
- Adicionar a pagina `apps/web/app/auth/users/page.tsx`.
- Integrar o estado resumido da equipe na home operacional do back-office.

## Fora de escopo

- Persistencia real de memberships, convites, equipes, dispositivos ou historico de login.
- Envio real de convites por e-mail, aceite de convite em 72h ou revogacao de sessoes.
- SCIM, SAML ou detalhe completo de avaliacao periodica de desempenho.
- CRUD real de usuarios, equipes e evidencias de treinamento.

## Criterios de aceite

- O contrato representa usuarios, papeis, status de lifecycle, dispositivos e competencias classificadas.
- A classificacao marca competencias vencidas como `expired` e competencias com vencimento em ate 90 dias como `expiring`.
- O endpoint `GET /auth/users` responde com catalogo tipado e selecao por querystring.
- A pagina web traduz o diretorio em resumo operacional, lista de usuarios e leitura de competencias.
- A home do back-office passa a resumir tambem o estado canonico da equipe.
- Sem payload valido do backend, a leitura web permanece fail-closed.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/auth/user-directory.test.ts`
- `pnpm exec tsx --test apps/api/src/domain/auth/user-directory-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/auth/user-directory-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm check:all`
