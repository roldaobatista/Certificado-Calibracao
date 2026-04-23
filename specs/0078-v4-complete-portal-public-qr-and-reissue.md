# Spec 0078 — V4 completa do portal, QR público e reemissão controlada

## Contexto

A V3 fechou o fluxo operacional central com OS, revisão, assinatura e emissão persistidas. A V4 precisava remover o caráter demonstrativo do acesso externo ao certificado, abrindo o portal autenticado do cliente, a verificação pública por QR e a reemissão controlada sem quebrar a trilha auditável. O backlog executável também reserva a V4.5 para manter o canal mobile/offline e a fila humana verdes como extensão operacional controlada.

## Objetivo

Fechar a V4 sobre registros persistidos do tenant autenticado com:

- verificação pública por QR real, limitada a metadados mínimos e autenticidade fail-closed;
- portal autenticado do cliente operando sobre carteira, equipamentos e certificados reais;
- workflow real de reemissão controlada preservando histórico, hash anterior, QR anterior e trilha de aprovação;
- seed e testes cobrindo o cliente externo, a publicação persistida e a transição de `R0` para `R1`;
- evidência de que o canal mobile/offline continua verde no recorte contratual da V4.

## Escopo

- `packages/db/prisma/**`
- `apps/api/src/domain/certificates/**`
- `apps/api/src/domain/portal/**`
- `apps/api/src/domain/emission/service-order-persistence.ts`
- `apps/api/src/interfaces/http/{auth-session,portal-dashboard,portal-equipment,portal-certificate,public-certificate,signature-queue}.ts`
- `apps/api/src/app.ts`
- `apps/api/src/app.test.ts`
- `apps/portal/app/**`
- `apps/portal/src/{auth-session-api,portal-dashboard-api,portal-equipment-api,portal-certificate-api,public-certificate-api}.ts`
- `packages/contracts/src/{portal-dashboard,portal-equipment,portal-certificate,public-certificate,offline-sync}.ts`
- `apps/android/src/{offline-sync,offline-calibration-workflow}.ts`

## Regras

- `?scenario=` continua existindo como fallback canônico; sem `scenario`, as rotas V4 preferem leitura persistida protegida por sessão.
- Somente usuários com papel `external_client` podem abrir o portal real do cliente.
- A verificação pública falha fechada quando faltarem `certificate`, `token`, hash-chain íntegra, evento de emissão ou evidência mínima de reemissão.
- A reemissão exige dois aprovadores distintos, preserva o hash anterior, supersede a publicação antiga e cria uma nova publicação rastreável.
- A trilha crítica precisa persistir também os metadados usados no hash dos eventos de reemissão, para evitar auditoria “adivinhada”.
- O canal mobile/offline continua tratado como extensão operacional: deve permanecer verde em contratos, outbox Android e fila humana, sem reabrir o núcleo V3/V4.

## Aceite

- `GET /portal/verify` responde com catálogo persistido quando recebe `certificate` e `token` válidos.
- `GET /portal/dashboard`, `GET /portal/equipment` e `GET /portal/certificate` respondem com catálogos persistidos do cliente quando chamados sem `scenario` e com cookie válido de `external_client`.
- `POST /emission/signature-queue/manage` com `action=reissue` cria `R1/R2`, supersede a publicação anterior, preserva `previousCertificateHash` e registra aprovação/notificação.
- `apps/portal` mantém navegação persistida entre login, dashboard, equipamentos, certificado e verificação pública sem regressão involuntária para `?scenario=`.
- O seed local demonstra um cliente externo autenticável e pelo menos uma publicação persistida para o portal/QR.
- A suíte automatizada consegue verificar QR autêntico, QR reemitido e viewer autenticado em histórico de reemissão.

## Verificação

- `pnpm --filter @afere/db exec prisma generate --no-engine`
- `pnpm --filter @afere/api typecheck`
- `pnpm --filter @afere/portal typecheck`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/android/src/offline-sync.test.ts apps/android/src/offline-calibration-workflow.test.ts apps/api/src/domain/sync/offline-sync-scenarios.test.ts`
- `pnpm test:tenancy`
- `pnpm check:all`
