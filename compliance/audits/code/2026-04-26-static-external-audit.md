---
auditor: senior-reviewer
release: pre-v1
verdict: PASS_WITH_FINDINGS
findings:
  - 2026-04-26-float-metrology-risk
  - 2026-04-26-session-security-gaps
  - 2026-04-26-enum-domain-drift
  - 2026-04-26-email-global-unique
  - 2026-04-26-audit-sequence-anchor
  - 2026-04-26-tctx-missing
  - 2026-04-26-android-kotlin-gap
  - 2026-04-26-certificate-hash-artifact
  - 2026-04-26-scenario-bypass-prod
  - 2026-04-26-ratelimit-absent
  - 2026-04-26-trpc-auth-context
  - 2026-04-26-cseq-race-condition
  - 2026-04-26-certificate-model-missing
  - 2026-04-26-e2e-absent
  - 2026-04-26-security-scan-absent
  - 2026-04-26-pdfa-external-pending
  - 2026-04-26-load-chaos-absent
blockers:
  - 2026-04-26-float-metrology-risk
  - 2026-04-26-session-security-gaps
  - 2026-04-26-tctx-missing
  - 2026-04-26-certificate-hash-artifact
  - 2026-04-26-scenario-bypass-prod
date: 2026-04-26T13:22:00-04:00
---

# Auditoria estática externa — Certificado-Calibracao / Aferê

> Data: 2026-04-26
> Tipo: auditoria estática via inspeção remota de código, estrutura, README, migrations, schema, CI e harness.
> Execução local: NÃO. Testes (`pnpm check:all`, migrações, E2E) não foram executados pelo auditor.
> Ferramenta: inspeção via GitHub + análise estática de arquivos fonte.

## Veredito executivo

O projeto tem uma **base arquitetural e regulatória incomum e bem estruturada**: spec-as-source, ADRs, agentes, gates, dossiê de validação, scripts de tenancy/RLS/WORM/snapshots e CI já documentados. O principal risco não é "falta de visão"; é **maturidade operacional**. Há forte evidência de que parte relevante do produto ainda está em transição entre *harness/cenários canônicos* e *produção real*.

**Maturidade estimada:** arquitetura 7/10; compliance design 8/10; banco 5.5/10; backend 6/10; frontend 6/10; testes estruturais 7/10; testes E2E/segurança/performance 4/10; prontidão para produção regulada 4/10.

**Prioridade P0:** fechar isolamento multitenant real no runtime, endurecer autenticação/sessão, remover ou isolar cenários estáticos em produção, persistir artefato certificado/PDF com hash do documento real, usar tipos numéricos adequados para medições oficiais, validar PDF/A externamente, ativar KMS real, e transformar o Android/offline-first em implementação nativa ou remover a promessa de Kotlin até existir.

---

## 1. Pontos fortes

A estrutura do monorepo é coerente: `apps/api`, `apps/web`, `apps/portal`, `packages`, `specs`, `adr`, `compliance`, `harness`, referências ISO 17025 e normas Inmetro. O README também define premissas metrológicas corretas: resultado e incerteza não omitidos, validade não automática de certificado, bloqueio de emissão com padrão vencido/fora de faixa, offline com oficialização posterior no backend e preparação para DCC.

O `AGENTS.md` é forte para operação assistida por IA: define o produto, princípios não negociáveis, papéis de agentes, áreas críticas, regra de que auditor não edita o que audita, gates e handoff obrigatório.

Há CI configurado com `required-gates`, Postgres em Docker, `pnpm check:all`, reconciliação de issues de verificação, flake gate noturno para tenancy e relatório semanal de budget.

---

## 2. Arquitetura

### O que está bom

A separação pretendida é adequada: backend técnico em Fastify/Prisma, web back-office, portal público/cliente, pacotes compartilhados de contracts, DB, audit-log, normative-rules, copy-lint e engine de incerteza. O backend declara domínio, infra e interfaces; o domínio de emissão é explicitamente marcado como área crítica que aciona regressão completa.

O projeto adota `contracts` com schemas compartilhados. O pacote `engine-uncertainty` aparece como componente separado, o que é correto para cálculo metrológico e decisão regulatória.

### Gaps arquiteturais

**P0 — diferença entre arquitetura declarada e implementação real.** A documentação de `apps/api/src/infra` fala em persistência, filas, KMS, QR e sync server-side, mas a árvore visível da pasta mostra essencialmente runtime-readiness/testes, `.gitkeep` e README. Isso indica que boa parte da "infra real" ainda está ausente ou fora do local esperado.

**P1 — interfaces citam HTTP/tRPC/GraphQL, mas a implementação visível está concentrada em HTTP e um plugin tRPC.** A pasta `interfaces` lista `http`, e `plugins` lista apenas `trpc.ts`; não vi camada GraphQL real. Isso não é problema se GraphQL foi abandonado, mas vira drift de documentação se permanecer como promessa arquitetural.

**P0 — Android declarado como Kotlin offline-first, mas a implementação visível é mínima e em TypeScript.** A pasta `apps/android` contém `README`, `.gitkeep` e `src` com arquivos TypeScript de workflow/sync; o README diz "Kotlin offline-first" e SQLCipher, enquanto o README raiz lista Android Kotlin real como limitação pendente.

**P1 — sem release publicado.** O GitHub mostra "No releases published". Para software regulado, releases versionadas com evidência, manifesto, SBOM e assinatura devem ser parte do fluxo.

---

## 3. Banco de dados e multitenancy

### O que está bom

O schema Prisma usa Postgres, contém modelos para organização, usuários, sessões, onboarding, padrões, calibrações, ordens de serviço, publicações de certificado, eventos de auditoria e qualidade. Há migrations com RLS, inclusive correção posterior para tabelas multitenant criadas em fases tardias.

A modelagem de `CertificatePublication` inclui token público, hash do documento, host QR, revisão, superseded/replacement, previousHash, notificação e motivo de reemissão. Isso é uma boa direção para reemissão controlada e verificação pública.

### Gaps críticos

**P0 — RLS depende de `app.current_organization_id`, mas não encontrei wrapper central que defina esse contexto em cada transação.** As policies usam `current_setting('app.current_organization_id', true)`. O factory `createPrismaClient` apenas cria um `PrismaClient`; não define `SET LOCAL app.current_organization_id`. O `CorePersistence` usa consultas Prisma normais com filtros por `organizationId`, mas isso não equivale a contexto RLS transacional. Resultado provável: se o usuário do banco não for owner/superuser, consultas podem falhar/retornar vazio sem GUC; se for owner/superuser e RLS não estiver forçada, o app pode depender apenas de filtros de aplicação.

**Correção recomendada:** criar um wrapper obrigatório, por exemplo `withTenant(organizationId, fn)`, que faça `SET LOCAL app.current_organization_id = ...` dentro de `$transaction`, e proibir acesso direto ao Prisma nas persistências multitenant. Também revisar se as tabelas estão com `FORCE ROW LEVEL SECURITY` quando aplicável e se o usuário de runtime não é owner das tabelas.

**P0 — campos oficiais de resultado e incerteza em `ServiceOrder` usam `Float?`.** Para resultado metrológico oficial, incerteza expandida e fator `k`, persistir em `Float` cria risco de arredondamento binário e divergência auditável. O modelo `Standard` usa `Decimal`, mas `ServiceOrder` usa `Float` para `measurementResultValue`, `measurementExpandedUncertaintyValue` e `k`.

**Correção recomendada:** trocar para `Decimal` com escala definida ou armazenar representação textual normalizada mais unidade, resolução e casas decimais. Para certificado regulado, a renderização deve ser derivada de uma representação canônica, não de float IEEE.

**P1 — excesso de estados em `String`/arrays livres.** `AppUser.roles` é `String[]`, `status` é `String`, e `ServiceOrder.workflowStatus`/`reviewDecision` também aparecem como strings. Há validação em contracts, mas o banco permite drift se alguém escrever por migration/script/import.

**Correção recomendada:** usar enums Prisma/Postgres ou tabelas de domínio; manter contracts como validação de borda, não como única linha de defesa.

**P1 — e-mail globalmente único em `AppUser`.** `email String @unique` impede que o mesmo e-mail exista em mais de uma organização. Pode ser intencional se houver identidade global, mas então falta um modelo explícito de identidade global + memberships por organização. Para SaaS multitenant, normalmente o índice deve ser `(organizationId, email)` ou haver tabela `Identity` separada.

**P1 — trilha de auditoria tem `prevHash`/`hash`, mas não vi sequência monotônica explícita.** `EmissionAuditEvent` tem `prevHash` e `hash`, mas não aparece um campo de sequência por ordem/certificado. Sem sequência monotônica e âncora de cadeia, a ordenação pode depender de timestamp e ficar frágil sob concorrência, replay ou eventos no mesmo instante.

**P1 — certificado é tratado por `ServiceOrder` + `CertificatePublication`, mas não há `model Certificate` nem `enum CertificateStatus`.** Isso pode ser uma decisão de modelagem, mas em produto regulado vale separar claramente: ordem de serviço, artefato de certificado, publicação pública, revisão, reemissão e status jurídico/técnico.

---

## 4. Backend/API

### O que está bom

A API usa Fastify, Prisma, zod, tRPC, CORS, Redis e contratos compartilhados. O `env.ts` valida variáveis e falha com `process.exit(1)` quando inválidas; isso é adequado para fail-closed.

Há guardas de autenticação/roles em `auth-session.ts`, incluindo papéis para onboarding, diretório, registry, workspace, portal, service-order, quality e settings.

### Gaps críticos

**P0 — cookie de sessão sem `Secure`.** O cookie `afere_session` é `HttpOnly` e `SameSite=Lax`, mas a serialização visível não adiciona `Secure`. Em produção HTTPS, isso deve ser obrigatório.

**Correção recomendada:** `Secure` obrigatório em `NODE_ENV=production`, `SameSite=Strict` onde possível, rotação de sessão em login, expiração curta ou renovação controlada, invalidação por device, e auditoria de sessão privilegiada.

**P0 — risco de open redirect.** `auth/login`, `auth/logout` e `onboarding/bootstrap` aceitam `redirectTo` e chamam `reply.redirect(...)` sem allowlist visível. Rotas de review/signature também aceitam redirect. Isso precisa de validação estrita para rotas internas ou domínios permitidos.

**P0 — modo `scenario` pode contornar autenticação em endpoints operacionais.** Em `emission/workspace`, `review-signature` e `signature-queue`, quando `scenario` está presente, a rota retorna catálogo/cenário sem passar pelos mesmos guards usados no fluxo persistido. Isso pode ser aceitável para demo/eval, mas em produção deve estar atrás de feature flag, ambiente não produtivo ou rota separada.

**P0 — hash do certificado parece ser calculado de campos selecionados, não dos bytes canônicos do documento.** Na emissão, `documentHash` é derivado de `workOrderNumber`, cliente, equipamento, número, resultado e incerteza. Isso não prova que o PDF/documento publicado é exatamente aquele hash; prova apenas um subconjunto lógico. Para certificado regulado, o hash deve ser do artefato canônico final, idealmente PDF/A ou envelope DCC, com metadados e assinatura.

**P1 — tRPC sem contexto de auth/tenant.** O plugin tRPC cria contexto com `requestId` apenas; não vi sessão, organização ou papéis no contexto. Se qualquer procedure sensível existir ou for adicionada, isso vira vetor de bypass.

**P1 — ausência visível de rate limiting e proteção anti-bruteforce.** O `package.json` da API lista Fastify, CORS, formbody, Prisma, tRPC, Redis, zod etc., mas não identifiquei plugin de rate-limit/captcha/throttling; login público e verificação pública devem ter limitação por IP, tenant, conta e token.

**P1 — numeração sequencial pode sofrer corrida concorrente.** O fluxo de assinatura carrega `records`, calcula o próximo número e emite. Mesmo com unique index no banco, duas emissões concorrentes podem competir. Deve haver reserva transacional com lock/sequence por organização, retry controlado e evento auditável de reserva.

---

## 5. Frontend web e portal

### O que está bom

O back-office e portal são Next.js 14, React 18, com `@afere/contracts` como dependência. A home do web usa `force-dynamic`, carrega catálogos do backend, usa cookies server-side e declara comportamento fail-closed quando a carga canônica falha.

As funções de API do web/portal validam payloads com zod schemas de `@afere/contracts` e retornam `null` em caso de erro ou payload inválido.

O portal público declara princípio de exposição mínima: sem cliente final, sem resultado metrológico e sem hash completo em tela pública.

### Gaps

**P1 — fallback de API para `http://127.0.0.1:3000`.** Web e portal usam default local quando `AFERE_API_BASE_URL` não está definido. Em produção, isso deve falhar fechado com erro explícito de configuração, não tentar localhost.

**P1 — falta evidência de E2E real de browser.** Os packages de web/portal têm Next, React e TypeScript; não vi Playwright/Cypress nas dependências desses apps. Para produto com emissão/revisão/assinatura, precisa haver testes E2E cobrindo onboarding, login, RBAC, emissão, reemissão, portal público e falhas de backend.

**P1 — observabilidade de erro é limitada.** As funções de fetch engolem exceções e retornam `null`. Isso é bom para fail-closed na UI, mas ruim para diagnóstico. Deve haver logging/telemetria server-side sem vazar PII.

**P1 — portal público precisa de anti-enumeração.** O endpoint público aceita `certificate` e `token`; a API lista publicações por service order quando `certificate` é fornecido. É preciso confirmar se esse identificador nunca é interno/sensível e se a resposta é constante o suficiente para não permitir enumeração.

---

## 6. Testes, gates e qualidade

### O que está bom

O root `package.json` declara uma malha extensa: build, typecheck, lint, testes, AC, regulatory, RLS, fuzz, sync simulator, tenancy, audit-chain, WORM, governance, escalation, auditors, roadmap, snapshots, redundancy, budget, normative package, validation dossier e `check:all`.

O README orienta `pnpm check:all` e `pnpm test:tenancy` como verificação local, e o CI `required-gates` sobe Postgres e executa `pnpm check:all`.

O harness registra status detalhado de P0/P1/P2, incluindo RLS estrutural, tenancy smoke/fuzz, audit hash chain, WORM, snapshots, dossiê e limitações como PDF/A externo e KMS real.

### Gaps

**P0 — não assumir que gates verdes equivalem a produto pronto.** O próprio status marca vários P0 como "em implementação", incluindo backend, normative package, dossiê, guardrails, governança, runbooks, cascata e redundância.

**P1 — ausência visível de security scanning formal.** Não vi CodeQL, Dependabot, SCA, secret scanning workflow, container scan, SBOM ou assinatura de imagem no CI aberto.

**P1 — validação PDF/A ainda externa/pendente.** Isso é um blocker real para certificado regulado se o artefato final for PDF/A.

**P1 — faltam testes de carga, concorrência e caos de produção.** O harness fala muito de tenancy/sync/snapshots, mas para emissão regulada é necessário simular concorrência em numeração, emissão simultânea, reemissão, fila de assinatura, indisponibilidade Redis/Postgres, expiração de sessão, rotação de KMS e rollback de migration.

---

## 7. Segurança, LGPD e governança

### Pontos fortes

O Dockerfile da API usa multi-stage build e runtime com usuário não-root. O `docker-compose` inclui Postgres, Redis, API, web e portal para dev, com healthchecks e readiness.

O CODEOWNERS define áreas críticas e mapeia agent-owners para domínio de emissão, auditoria, engine de incerteza, normative-rules, audit-log, compliance e PRD.

### Gaps

**P0 — separação real de aprovação ainda depende de estrutura GitHub.** O CODEOWNERS aponta para `@roldaobatista`; os papéis de agentes aparecem como comentários/metadados. O harness reconhece que review obrigatório por CODEOWNERS depende de segundo colaborador/time GitHub real.

**P1 — `.env.example` não inclui segredos/configurações essenciais de produção.** O exemplo contém Postgres, Redis e base URLs, mas não mostra variáveis de sessão, KMS, storage de artefatos, URL pública de QR, flags de modo demo/scenario, Sentry/OpenTelemetry, SMTP, ou chaves de assinatura.

**P1 — credenciais dev simples são aceitáveis apenas em dev.** O compose usa `afere/afere` para Postgres; isso precisa estar bloqueado por ambiente e nunca migrar para staging/produção.

**P1 — falta `SECURITY.md`/política de disclosure visível na raiz.** A listagem raiz não mostra arquivo de política de segurança ou licença. Para produto regulado, disclosure, processo de incidentes e classificação de vulnerabilidades devem ser explícitos.

---

## 8. Compliance metrológico

O desenho regulatório está acima da média: usa PRD, specs, ADRs, dossiê, release-norm, runbooks, audit trail, copy-lint, engine de incerteza e normative-rules. O projeto também cita ISO/IEC 17025, Inmetro/Cgcre, ILAC P10/P14 e EURAMET cg-18 como base normativa.

Os gaps relevantes são de **evidência operacional**: validação externa PDF/A, KMS real, piloto controlado, drills de staging e Android real ainda aparecem como pendentes. Para auditoria real, não basta o harness afirmar "PASS"; é preciso evidência executável, artefatos assinados, trilha de versão normativa, laudos de validação e escopo/CMC vinculados aos certificados.

---

## 9. Lista priorizada de correções

### P0 — bloquear antes de produção regulada

1. **Tenant/RLS runtime:** implementar `withTenant()` transacional obrigatório, `SET LOCAL app.current_organization_id`, usuário DB não-owner, testes que provem falha cross-tenant no runtime real.
2. **Artefato certificado:** gerar documento canônico, persistir bytes ou content-address, hash do artefato final, metadata de assinatura, PDF/A externo, versão normativa e cadeia de auditoria.
3. **Medições oficiais:** migrar `Float` de resultado/incerteza/k para `Decimal` ou string canônica com escala.
4. **Sessão/auth:** cookie `Secure`, allowlist de redirect, CSRF para POSTs com cookie, rate-limit login/portal, rotação e revogação robusta.
5. **Cenários estáticos:** remover de produção ou proteger com flag/admin; não permitir `?scenario=` em endpoints operacionais produtivos.
6. **KMS real:** ativar assinatura com infraestrutura/credenciais reais, rotação, runbook testado e evidência arquivada.
7. **Android:** implementar nativo Kotlin/SQLCipher ou ajustar documentação para declarar que Android é simulação/contrato, não app real.

### P1 — endurecer antes de beta controlado

1. Enums/tabelas de domínio para roles, status, workflow e review decisions.
2. Modelo de identidade multitenant: email global + memberships ou unique `(organizationId, email)`.
3. Sequência monotônica em audit events e âncora de hash-chain.
4. Reserva de número de certificado por transação/lock/sequence.
5. E2E Playwright/Cypress para web/portal.
6. CodeQL/SCA/Dependabot/container scan/SBOM/attestations.
7. Observabilidade: logs estruturados, trace id, auditoria de falhas, métricas de emissão.
8. Política `SECURITY.md`, incident response e LGPD breach procedure.

### P2 — melhoria contínua

1. Separar docs aspiracionais de features implementadas.
2. Criar matriz "requisito → código → teste → evidência → release".
3. Criar dashboards de prontidão por módulo.
4. Publicar releases assinadas com changelog regulatório.
5. Adicionar testes de carga e concorrência para emissão/reemissão.
