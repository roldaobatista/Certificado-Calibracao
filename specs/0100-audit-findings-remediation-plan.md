---
spec_id: SPEC-0100
title: Plano de remediação dos achados da auditoria estática 2026-04-26
author: senior-reviewer
status: proposed
date: 2026-04-26
linked_requirements:
  - REQ-PRD-13-11-AUTH-SSO-MFA
  - REQ-PRD-13-15-REGULATORY-PROFILES-PDF
  - REQ-PRD-13-17-PUBLIC-QR-MINIMAL-METADATA
  - REQ-PRD-13-20-OFFLINE-SYNC-CHAOS
  - REQ-PRD-13-22-NORMATIVE-GOVERNANCE-OWNER
blocker_for: []
estimated_effort: 6 semanas (2 P0, 2 P1, 1 P2, 1 P3)
---

# SPEC-0100 — Plano de remediação dos achados da auditoria estática 2026-04-26

> **Fonte de verdade.** Este documento consolida os 35 findings (F-001 a F-035) da auditoria estática externa realizada em 2026-04-26 sobre o repositório `Certificado-Calibracao / Aferê`, mapeia o estado atual pós-commits de remediação (`01d56f3`, `4edae2a`, `ca54fa2`, `29c238f`, `daf81ea`) e define waves executáveis de fechamento.
>
> **Regra:** código que divergir deste plano é bug; evidência de execução deve ser arquivada em `compliance/validation-dossier/evidence/`.

---

## 1. Resumo executivo

A auditoria estática identificou 35 findings em segurança, autorização, arquitetura, banco, DevOps, testes e conformidade regulatória. Cinco commits de remediação já fecharam parcialmente os itens mais críticos: `withTenant()` transacional, `Decimal` para medições oficiais, cookie `Secure/Strict`, allowlist de redirect em auth, proteção de `?scenario=` em `emission-workspace`, split do monolito `app.test.ts`, stubs de infra (KMS, queue, storage, PDF/A), matriz de autorização em YAML com teste de cobertura, e runbooks R5-R8.

**Restam 28 findings abertos ou parcialmente abertos**, sendo 8 de prioridade P0 (segurança/isolamento), 15 de P1 (endurecimento operacional) e 5 de P2/P3 (arquitetura, qualidade, longo prazo).

Este plano organiza o fechamento em **4 waves sequenciais** com dependências explícitas, critérios de aceitação (AC) por wave e owner de agente.

---

## 2. Inventário de findings (estado atual)

| ID | Área | Severidade | Status pós-remediação | Ação necessária | Owner | Prioridade | Esforço |
|----|------|------------|----------------------|-----------------|-------|------------|---------|
| F-001 | Segurança | Alta | **Aberto** | Remover `default` de `COOKIE_SECRET` em produção; falhar se ausente | backend-api | P0 | P |
| F-002 | Banco/Segurança | Alta | **Aberto** | Em `production`, exigir `DATABASE_OWNER_URL` + `DATABASE_APP_URL` sem fallback para `DATABASE_URL` | backend-api, db-schema | P0 | M |
| F-003 | Auth/MFA | Alta | **Aberto** | Implementar challenge MFA real (TOTP) para `admin`/`signatory`; sessão parcial antes da final | backend-api, lgpd-security | P0 | M |
| F-004 | Autorização | Alta | **Aberto** | Hook global deve aplicar matriz também a GET/HEAD, ou gerar testes que provem `require*Access` em cada GET privado | backend-api | P0 | M |
| F-005 | Autorização/API | Média | **Aberto** | `/sync/review-queue` handler não autentica mas matriz diz `public: false`; exigir auth ou justificar público | backend-api | P0 | P |
| F-006 | API/Segurança | Média | **Parcial** | `emission-workspace` e `onboarding/readiness` já bloqueiam `scenario` em prod; `customer-registry` e `quality-hub` ainda retornam cenários sem auth | backend-api | P0 | M |
| F-007 | API pública | Média | **Aberto** | `/portal/verify` precisa de validação de formato/tamanho máximo, token assinado e rate-limit específico | backend-api | P1 | M |
| F-008 | Bootstrap/Auth | Alta | **Parcial** | Bootstrap já protegido contra org duplicada, mas falta flag `BOOTSTRAP_ENABLED` explícita e token one-time/allowlist | backend-api | P0 | P |
| F-009 | Redirecionamento | Média | **Parcial** | `auth-session` e `onboarding/readiness` têm `isRedirectAllowed`; `customer-registry.ts` e `review-signature.ts` usam `readRedirectTarget` sem allowlist | backend-api | P1 | P |
| F-010 | Sessão | Média | **Aberto** | Idle timeout, rotação pós-login, revogação por dispositivo, sessão curta para papéis críticos | backend-api | P1 | M |
| F-011 | Segurança positiva | Info | **Fechado** | Helmet, CORS, cookie secure, CSRF, rate limit globais mantidos | — | P2 | P |
| F-012 | Arquitetura | Média | **Aberto** | Quebrar `app.ts` em módulos de registro (`registerAuth`, `registerRegistry`, etc.) | backend-api | P2 | M |
| F-013 | Arquitetura/Infra | Média | **Aberto** | `apps/api/src/infra/README.md` promete persistência/filas/KMS/QR/sync, mas pasta só tem `runtime-readiness` | backend-api | P2 | P |
| F-014 | Infra/DevOps | Alta | **Parcial** | `infra/modules` agora tem stubs (KMS, queue, storage, PDF/A), mas falta IaC real (Terraform) e pipeline de deploy | backend-api | P1 | G |
| F-015 | DevOps | Alta | **Aberto** | Limitações explícitas (KMS real, PDF/A externo, staging drills, piloto) precisam virar épicos P0/P1 com AC | product-governance | P1 | M |
| F-016 | Android/Produto | Alta | **Aberto** | Android ainda é TypeScript/placeholder; decisão: Kotlin/SQLCipher real ou ajustar documentação | android, product-governance | P2 | G |
| F-017 | Banco | Média | **Aberto** | `apps/api/.env.example` não espelha `DATABASE_OWNER_URL`, `DATABASE_APP_URL`, `COOKIE_SECRET`, `REDIRECT_ALLOWLIST`, `ALLOW_SCENARIO_ROUTES` | backend-api | P0 | P |
| F-018 | Banco | Info | **Fechado** | Migrations V1-V5 com RLS mantidas; continuar testes forward/backward | db-schema | P2 | M |
| F-019 | Observabilidade | Média | **Aberto** | Adicionar `/metrics`, OpenTelemetry, logs estruturados por tenant/request | backend-api | P1 | M |
| F-020 | Performance/API | Média | **Aberto** | Paginação, limites, filtros e projeções em listagens (`customers`, `equipment`, `serviceOrders`, etc.) | backend-api | P2 | M |
| F-021 | Frontend | Média | **Aberto** | Adicionar headers de segurança em `next.config.mjs` (web e portal): CSP, frame-ancestors, HSTS | web-ui | P1 | P |
| F-022 | Frontend/Testes | Média | **Parcial** | Playwright configs e specs existem, mas `apps/web/package.json` e `apps/portal/package.json` não têm script `test` | web-ui | P1 | P |
| F-023 | Testes | Média | **Aberto** | `pnpm test` chama `turbo run test`, mas `apps/api`, `apps/web`, `apps/portal` não definem `test`; alinhar ou documentar | qa-acceptance | P0 | P |
| F-024 | Testes | Média | **Fechado** | `app.test.ts` monolítico dividido em domínios (`auth.test.ts`, `catalogs.test.ts`, etc.) | backend-api | P2 | M |
| F-025 | Dependências | Média | **Aberto** | `@trpc/server` ainda em RC; libs críticas usam ranges `^` | backend-api | P1 | P |
| F-026 | Supply chain | Média | **Aberto** | Adicionar Dependabot/Renovate, CodeQL, npm audit, secret scanning | lgpd-security | P1 | P |
| F-027 | DevOps | Baixa | **Aberto** | Manter `docker-compose.yml` dev-only; criar compose separado para CI | backend-api | P3 | P |
| F-028 | CI/Governança | Info | **Fechado** | CI `required-gates`, `nightly-flake-gate` mantidos | qa-acceptance | P2 | M |
| F-029 | Governança | Média | **Aberto** | PR template diferenciar claramente "auditoria automatizada/agente" vs "auditoria humana externa" | product-governance | P1 | P |
| F-030 | Documentação | Info | **Fechado** | Documentação regulatória extensa mantida | product-governance | P2 | M |
| F-031 | Produto/UX | Média | **Aberto** | Adicionar axe, smoke E2E, navegação por teclado | web-ui | P2 | M |
| F-032 | Produto/Compliance | Alta | **Parcial** | Stubs KMS/PDF-A existem em `infra/modules`, mas não há ativação real com credenciais/infra | backend-api, regulator | P1 | G |
| F-033 | Qualidade de código | Média | **Aberto** | Mesmo que F-004: executor único da matriz ou testes que provem cada flag (`csrf`, `audit`, `tenant`, `rateLimit`) | backend-api | P1 | M |
| F-034 | Frontend/API | Baixa | **Aberto** | Manter fail-closed; adicionar timeout curto, cache seletivo e retry nos loaders | web-ui | P3 | P |
| F-035 | Releases | Média | **Aberto** | Pipeline de release: tag, changelog, SBOM, dossiê, assinatura | product-governance | P2 | M |

**Contagem:** 8 P0 abertos, 15 P1 abertos/parciais, 5 P2/P3 abertos.

---

## 3. Waves de execução

### Wave 1 — P0: Isolamento e segurança runtime (semana 1-2)

**Objetivo:** remover vetores de comprometimento de autenticação, sessão, multitenancy e autorização antes de qualquer deploy em ambiente não-controlado.

**Tarefas:**

1. **F-001 — `COOKIE_SECRET` sem default em produção**
   - Remover `.default("change-me-in-production-32-chars-min")` de `COOKIE_SECRET` em `apps/api/src/config/env.ts`.
   - Em `production`, se ausente, `loadEnv` deve falhar com `process.exit(1)`.
   - Adicionar teste em `apps/api/src/tests/security/auth-negative.test.ts` que prove bootstrap falho sem secret.

2. **F-002 — URLs owner/app obrigatórias em produção**
   - Em `apps/api/src/config/env.ts`, quando `NODE_ENV === "production"`, exigir `DATABASE_OWNER_URL` e `DATABASE_APP_URL` (não permitir fallback para `DATABASE_URL`).
   - Em `apps/api/src/app.ts`, remover fallback `?? env.DATABASE_URL` para as URLs owner/app em modo produção.
   - Adicionar teste que valide falha de boot se apenas `DATABASE_URL` for fornecida em produção.

3. **F-008 — Bootstrap endurecido**
   - Adicionar `BOOTSTRAP_ENABLED` em `env.ts` (default `false` em produção).
   - Em `apps/api/src/interfaces/http/auth-session.ts`, antes de `hasAnyOrganization()`, verificar `env.BOOTSTRAP_ENABLED`.
   - Opcional: adicionar `BOOTSTRAP_TOKEN` one-time ou allowlist de IP para primeira instalação.
   - Atualizar `apps/api/.env.example` com todas as novas variáveis.

4. **F-017 — `.env.example` completo**
   - `apps/api/.env.example` deve conter: `COOKIE_SECRET`, `DATABASE_OWNER_URL`, `DATABASE_APP_URL`, `REDIRECT_ALLOWLIST`, `ALLOW_SCENARIO_ROUTES`, `BOOTSTRAP_ENABLED`, `RATE_LIMIT_MAX`, `RATE_LIMIT_WINDOW_MS`.

5. **F-004 / F-033 — Autorização GET/HEAD**
   - **Opção A (recomendada):** estender `registerRouteAuthorizationHook` em `apps/api/src/domain/auth/route-authorization.ts` para aplicar matriz também a GET/HEAD, com exceções públicas explícitas (`public: true`).
   - **Opção B (fallback):** se houver razão arquitetural para manter GET/HEAD por handler, criar `tools/get-route-auth-coverage.test.ts` que percorre `route-authorization-matrix.yaml`, filtra GETs com `public: false`, e prova via reflexão/AST que cada rota correspondente chama `require*Access` antes de responder.
   - A Opção A é preferida porque elimina drift declarado-vs-executado.

6. **F-005 — `/sync/review-queue` alinhado com matriz**
   - O handler em `apps/api/src/interfaces/http/offline-sync.ts` não autentica, mas a matriz diz `public: false`.
   - Decisão: como `sync/review-queue` é fila de revisão de conflitos offline, deve ser privada.
   - Adicionar `requireWorkspaceAccess` (ou role adequado) no handler.
   - Se mantida como pública por decisão de produto, alterar matriz para `public: true` com ADR justificando.

7. **F-006 — `scenario` uniforme em todos os handlers GET**
   - `customer-registry.ts` (linha 65-70) e `quality-hub.ts` (linha 35-36) retornam cenários antes de autenticar.
   - Adicionar `if (query.data.scenario && !env.ALLOW_SCENARIO_ROUTES) return 403` nesses handlers, igual feito em `emission-workspace.ts` e `onboarding.ts`.
   - Verificar `review-signature.ts` e `signature-queue.ts` para mesma proteção.

8. **F-023 — Alinhar `pnpm test`**
   - Adicionar script `"test": "echo 'Use test:tools, test:integration, test:e2e or check:all' && exit 1"` em `apps/api/package.json`, `apps/web/package.json`, `apps/portal/package.json`.
   - Ou, melhor: fazer `apps/api/package.json` ter `"test": "pnpm run test:integration && pnpm run test:security"`, `apps/web` ter `"test": "pnpm exec playwright test"`, etc.
   - Documentar no `README.md` que `pnpm test` na raiz dispara suites reais.

**Critérios de aceitação Wave 1:**
- [ ] `pnpm check:all` passa após mudanças.
- [ ] Teste de segurança prova que boot falha em produção sem `COOKIE_SECRET` ou `DATABASE_APP_URL`/`OWNER`.
- [ ] Teste de cobertura da matriz prova que nenhum GET privado responde sem autenticação.
- [ ] `apps/api/.env.example` contém todas as variáveis obrigatórias.
- [ ] Bootstrap retorna 403 em produção quando `BOOTSTRAP_ENABLED=false`, mesmo sem organização.
- [ ] `?scenario=` retorna 403 em produção (`ALLOW_SCENARIO_ROUTES=false`) em todos os handlers operacionais.
- [ ] `pnpm test` na raiz executa testes reais dos apps.

---

### Wave 2 — P1: Endurecimento operacional (semana 3-4)

**Objetivo:** fechar MFA real, hardening de sessão, headers frontend, infra mínima, supply chain e validação de portal público.

**Tarefas:**

1. **F-003 — MFA real (TOTP)**
   - Criar tabela/modelo `UserMfaCredential` (secret cifrado, algoritmo, dígitos, janela).
   - Implementar `POST /auth/mfa/enroll` (gera secret, retorna QR code URI) e `POST /auth/mfa/verify` (valida TOTP).
   - Alterar `POST /auth/login`: se usuário privilegiado e `mfaEnrolled`, retornar `mfa_required` + `mfaToken` (JWT de curta duração para etapa 2).
   - Criar `POST /auth/mfa/challenge`: recebe `mfaToken` + `code`; se válido, emite sessão final.
   - Atualizar `evals/ac/prd-13-11-auth-sso-mfa.test.ts` para cobrir challenge real.

2. **F-009 — Redirect allowlist unificado**
   - `customer-registry.ts` (linha 157-159) usa `readRedirectTarget` sem `isRedirectAllowed`.
   - `review-signature.ts` e `signature-queue.ts` também têm `isRedirectAllowed` local (cópia), mas `customer-registry.ts` não valida.
   - Extrair `isRedirectAllowed` para `apps/api/src/interfaces/http/redirect-helpers.ts` compartilhado.
   - Aplicar em todo handler que faz `reply.redirect`.

3. **F-010 — Sessão endurecida**
   - Idle timeout: `lastActivityAtUtc` no modelo `AppSession`; renovar a cada request autenticado; expirar se idle > 30 min para admins/signatários, 2h para demais.
   - Rotação: ao login bem-sucedido (incluindo pós-MFA), gerar novo token e invalidar anteriores do mesmo usuário (ou por device).
   - Sessão curta para papéis críticos: `createSessionExpiry` deve retornar 8h para `admin`/`signatory` em produção, mantendo 24h para demais.
   - Adicionar `deviceFingerprint` (hash de user-agent + IP subnet) e invalidar sessão se drift significativo.

4. **F-007 — `/portal/verify` endurecido**
   - Validar `certificate` com regex/formato (ex: `SO-[A-Z0-9]+` ou UUID) e tamanho máximo 64.
   - Validar `token` com tamanho máximo 128 e formato alfanumérico.
   - Adicionar rate-limit específico no handler (ex: 30 req/min por IP).
   - Logging estruturado de tentativas falhas (sem PII).

5. **F-021 — Headers de segurança Next.js**
   - Em `apps/web/next.config.mjs` e `apps/portal/next.config.mjs`, adicionar:
     - `headers()` com `Content-Security-Policy`, `X-Frame-Options`/`frame-ancestors`, `Strict-Transport-Security`, `Referrer-Policy`, `Permissions-Policy`.
   - Em produção, CSP deve ser `default-src 'self'` com relaxamento mínimo para API e assets.

6. **F-022 / F-023 — Scripts de teste nos apps**
   - `apps/web/package.json`: `"test": "pnpm exec playwright test"`, `"test:e2e": "pnpm exec playwright test"`.
   - `apps/portal/package.json`: idem.
   - `apps/api/package.json`: `"test": "pnpm run test:integration && pnpm run test:security"`.
   - Garantir que `turbo run test` execute suites significativas.

7. **F-025 — Pin de dependências críticas**
   - Trocar `@trpc/server` de `^11.0.0-rc.660` para versão estável (quando disponível) ou pinar exato.
   - Pin exato para `fastify`, `prisma`, `@prisma/client`, `zod`, `redis`, `helmet`, `csrf-protection`, `rate-limit`.
   - Adicionar `renovate.json` ou `dependabot.yml` com revisão obrigatória e changelog em PR.

8. **F-026 — Supply chain scanners**
   - Adicionar `.github/dependabot.yml` para npm/pnpm.
   - Adicionar workflow CodeQL para JavaScript/TypeScript.
   - Adicionar `npm audit` ou `pnpm audit` no CI (`required-gates.yml`).
   - Adicionar secret scanning GitHub habilitado no repositório.

9. **F-029 — PR template diferenciado**
   - Em `.github/pull_request_template.md`, separar seção:
     - "Auditoria automatizada por agentes (CI/gates)"
     - "Auditoria humana externa (quando exigida por caso-limite)"
   - Adicionar nota de que pareceres de agentes não substituem auditoria regulatória humana nos 5 casos-limite.

10. **F-014 / F-032 — IaC mínima e ativação de stubs**
    - Criar `infra/staging/` com Terraform/CDK mínimo: VPC/rede, Postgres RDS/Cloud SQL, Redis (Memorystore/Elasticache), secrets manager, bucket WORM para artefatos.
    - Ativar `infra/modules/kms.ts` com provider real (AWS KMS sa-east-1 conforme ADR 0003).
    - Ativar `infra/modules/pdfa-validator.ts` com serviço externo (ex: veraPDF CLI em container ou API contratada).
    - Criar pipeline de deploy dry-run em staging (GitHub Actions).

**Critérios de aceitação Wave 2:**
- [ ] Login com MFA: senha correta + TOTP errado = 401; senha correta + TOTP correto = sessão.
- [ ] Todos os redirects passam por allowlist centralizada; teste falha se handler novo usar `reply.redirect` sem validação.
- [ ] Next.js responde com CSP, HSTS, X-Frame-Options nos headers.
- [ ] Dependabot/CodeQL/audit ativos e passando no CI.
- [ ] Staging deploy dry-run executa sem erros; KMS e PDF/A validam artefato canônico.
- [ ] `/portal/verify` rejeita certificate/token malformados e respeita rate limit.

---

### Wave 3 — P2: Arquitetura, performance e qualidade (semana 5)

**Objetivo:** modularizar, paginar, observar e melhorar manutenibilidade sem mudar comportamento funcional.

**Tarefas:**

1. **F-012 — Modularizar `app.ts`**
   - Criar `apps/api/src/bootstrap/register-routes.ts` que orquestra os `register*Routes`.
   - Criar `apps/api/src/bootstrap/register-plugins.ts` para helmet, cors, cookie, csrf, rateLimit.
   - Criar `apps/api/src/bootstrap/create-prisma-clients.ts` para lógica de owner/app.
   - Manter `app.ts` como composição de 3-4 chamadas.

2. **F-013 — Consistência `apps/api/src/infra`**
   - Mover stubs de `infra/modules/*` para `apps/api/src/infra/` **ou** atualizar `apps/api/src/infra/README.md` para refletir que persistência/filas/KMS/QR/sync estão em `infra/modules/` na raiz.
   - Preferir atualizar README para não quebrar imports existentes.

3. **F-019 — Observabilidade**
   - Adicionar endpoint `/metrics` com `fastify-metrics` ou solução manual (contadores de request, status code, latência p50/p95/p99).
   - Adicionar `requestId` em todos os logs; correlacionar com `tenant` (organizationId quando autenticado).
   - OpenTelemetry: tracing básico em rotas críticas (emissão, assinatura, verificação pública).

4. **F-020 — Paginação em listagens**
   - Adicionar `limit`/`cursor`/`offset` nos contratos (`@afere/contracts`) para `listCustomers`, `listEquipment`, `listServiceOrders`, `listCertificatePublications`.
   - Implementar nos persistences e handlers; default `limit=50`, max `limit=500`.
   - Adicionar testes de carga com 10k registros por tenant.

5. **F-031 — Acessibilidade e E2E**
   - Adicionar `@axe-core/playwright` nos testes E2E.
   - Smoke test de navegação por teclado (Tab, Enter, Escape) nos fluxos críticos: login, workspace, emissão.
   - Teste de contraste mínimo e roles ARIA nos formulários.

6. **F-035 — Pipeline de release**
   - Workflow GitHub Actions que gera tag semântica, changelog regulatório, SBOM (`pnpm sbom` ou `cyclonedx`), manifesto do dossiê e assinatura do artefato.
   - Arquivar em `compliance/release-norm/<versao>.md`.

**Critérios de aceitação Wave 3:**
- [ ] `app.ts` < 80 linhas; modularização não quebra `check:all`.
- [ ] `/metrics` exporta RED básico (Requests, Errors, Duration) por rota.
- [ ] Listagens com `limit` respeitam paginação; teste de carga não degrada p95.
- [ ] E2E com axe não reporta violações críticas.
- [ ] Release tag gera SBOM e dossiê arquivado.

---

### Wave 4 — P3: Longo prazo e produto (semana 6+)

**Objetivo:** decisões estratégicas que exigem mais tempo ou dependem de Wave 2/3.

**Tarefas:**

1. **F-016 — Android real**
   - Decisão arquitetural (ADR): Kotlin nativo + SQLCipher offline-first ou remover promessa de Kotlin e manter TypeScript como simulador de contratos.
   - Se Kotlin: MVP com auth, cache local, outbox, sync e conflito.
   - Se manter TS: atualizar todos os READMEs e PRD para não citar Kotlin/SQLCipher como entregável de produto.

2. **F-027 — Docker compose para CI**
   - Criar `docker-compose.ci.yml` com imagens pré-buildadas, sem instalação de dependências em startup.

3. **F-034 — Resiliência dos loaders frontend**
   - Adicionar `AbortSignal` com timeout (5s) nos loaders server-side.
   - Cache seletivo (SWR/React Query) para catálogos canônicos que mudam pouco.
   - Estados de retry e skeleton na UI.

4. **F-015 — Drills de staging**
   - Executar runbooks R1-R8 em ambiente de staging real (não local).
   - Evidência arquivada em `compliance/runbooks/evidence/`.

5. **F-032 / F-014 — Produção regulada**
   - Piloto controlado com 1-2 laboratórios; validação externa PDF/A; auditoria humana contratada para os 5 casos-limite.

**Critérios de aceitação Wave 4:**
- [ ] ADR publicada para decisão Android.
- [ ] Drill de pelo menos 2 runbooks executado em staging com evidência.
- [ ] Piloto produtivo documentado com limitações honestas.

---

## 4. Dependências entre waves

```
Wave 1 (P0 segurança)
  ├─► Wave 2 (P1 endurecimento)
  │     ├─► Wave 3 (P2 arquitetura/performance)
  │     └─► Wave 4 (P3 longo prazo)
  └─► Wave 2 F-003 (MFA) depende de Wave 1 F-004 (auth hook estável)

Wave 2 F-014 (IaC) depende de Wave 1 F-002 (roles DB estáveis)
Wave 3 F-019 (observabilidade) depende de Wave 3 F-012 (app.ts modular)
Wave 4 F-015 (drills) depende de Wave 2 F-014 (staging real)
```

---

## 5. Riscos do plano e mitigações

| Risco | Mitigação |
|-------|-----------|
| Wave 1 quebra `check:all` por mudança em env/auth | Executar `pnpm check:all` a cada tarefa; nunca commitar com vermelho. |
| MFA real atrasar e bloquear Wave 2 | Fallback: manter flag `mfaEnrolled` como declarativo temporário, mas bloquear login de admin/signatory com mensagem clara até TOTP pronto. |
| IaC staging demandar mais tempo que 1 semana | Staging mínimo (Docker Compose em VM) é aceitável como MVP; Terraform pode vir em P2. |
| `route-authorization.ts` para GET/HEAD quebrar rotas públicas | Manter `public: true` na matriz para `/auth/session`, `/portal/verify`, `/healthz`, `/readyz`, `/auth/self-signup`. Testar exhaustivamente. |
| Pin de dependências travar atualizações de segurança | Renovate/Dependabot com schedule semanal e revisão obrigatória; nunca auto-merge em libs críticas. |

---

## 6. Checklist de fechamento do plano

- [ ] Wave 1 mergeada em `main` com `check:all` verde.
- [ ] Wave 2 mergeada em `main` com `check:all` verde + testes E2E passando.
- [ ] Wave 3 mergeada em `main` com `check:all` verde + release tag publicada.
- [ ] Wave 4: ADR Android publicada; drills arquivados.
- [ ] Dossiê de remediação arquivado em `compliance/validation-dossier/releases/2026-04-26-audit-findings-remediation.md`.
- [ ] Handoff de sessão em `compliance/sessions-log/` se execução for assistida por agente.

---

## 7. Referências

- Auditoria original: `compliance/audits/code/2026-04-26-static-external-audit.md`
- Status do harness: `harness/STATUS.md`
- AGENTS.md: `AGENTS.md` §4 (papéis), §6 (pipeline), §10 (commit/push)
- PRD: `PRD.md` v1.8
