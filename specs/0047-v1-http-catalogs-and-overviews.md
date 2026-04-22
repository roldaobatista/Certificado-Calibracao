# 0047 — Catálogos HTTP canônicos e homes operacionais de V1

## Contexto

As regras executáveis de `auth`, `onboarding`, `dry-run` de emissão e verificação pública já existem em contratos e funções de domínio, mas `apps/web` e `apps/portal` ainda dependem de leitura local para renderizar cenários. Isso abre espaço para drift entre UI e backend técnico, exatamente no momento em que a fatia V1 precisa mostrar prontidão operacional e fail-closed de forma auditável.

## Escopo

- Expor em `apps/api/src/interfaces/http` endpoints HTTP canônicos para os catálogos de `auth`, `onboarding`, `emission` e `portal`.
- Materializar em `packages/contracts` os schemas Zod compartilhados dos catálogos HTTP consumidos por `apps/web` e `apps/portal`.
- Fazer `apps/web` carregar os catálogos de `self-signup`, `onboarding` e `dry-run` exclusivamente a partir do backend.
- Fazer `apps/portal` carregar o catálogo público de verificação exclusivamente a partir do backend.
- Adicionar homes operacionais em `apps/web/app/page.tsx` e `apps/portal/app/page.tsx` que resumam a disponibilidade das leituras canônicas e os principais estados de V1.
- Preservar comportamento fail-closed quando o backend não responder com payload válido.

## Fora de escopo

- Persistência real de organizações, certificados, sessões ou usuários.
- OAuth/SSO real, sessão autenticada, RBAC completo ou fluxo humano de aprovação.
- Geração final de PDF/A, assinatura eletrônica real ou envio de notificações.
- Portal autenticado do cliente além da vitrine pública de verificação.

## Critérios de aceite

- O backend responde com catálogos tipados para `GET /auth/self-signup`, `GET /onboarding/readiness`, `GET /emission/dry-run` e `GET /portal/verify`.
- Cada endpoint aceita a seleção de cenário por querystring e falha fechado com `400` quando a query for inválida.
- `apps/web` renderiza os estados de auth, onboarding e dry-run a partir dos catálogos do backend, sem duplicar regra crítica no cliente.
- `apps/portal` renderiza a vitrine pública e a página de verificação a partir do catálogo do backend, mantendo o recorte mínimo de metadados.
- As homes de `apps/web` e `apps/portal` resumem a disponibilidade dos catálogos canônicos e deixam explícito quando a leitura está indisponível.
- Quando o backend estiver indisponível ou responder payload inválido, web e portal permanecem em fail-closed, sem assumir preview local.

## Evidência

- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/web/src/auth/self-signup-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/onboarding/onboarding-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/emission/emission-dry-run-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm exec tsx --test apps/portal/src/public-certificate-scenarios.test.ts`
- `pnpm exec tsx --test apps/portal/src/home/public-verification-overview.test.ts`
- `pnpm check:all`
