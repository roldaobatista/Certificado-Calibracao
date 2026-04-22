# 0048 — RBAC basico e workflow de revisao/assinatura para V1

## Contexto

O roadmap V1 exige backend com auth, RBAC basico, emissao, assinatura e QR. O repositorio ja possui contratos executaveis para auto-cadastro, onboarding, dry-run de emissao e verificacao publica, mas ainda nao materializa o workflow web de revisao tecnica e assinatura com segregacao de funcoes `executor != revisor != signatario`.

Sem essa leitura canonica, o back-office continua sem uma forma auditavel de mostrar quem pode revisar, quem pode assinar, quais atribuicoes estao bloqueadas e quais reasignacoes sao necessarias antes da emissao oficial.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para o workflow de revisao/assinatura e os papeis de membership relevantes de V1.
- Implementar em `apps/api/src/domain/emission` uma politica executavel de RBAC basico e segregacao para `executor`, `revisor` e `signatario`.
- Selecionar sugestoes deterministicas de revisor e signatario entre candidatos elegiveis com menor fila.
- Expor em `apps/api/src/interfaces/http` um endpoint canonico `GET /emission/review-signature`.
- Materializar em `apps/web/src/emission` um view model legivel para o workflow web de revisao e assinatura.
- Adicionar a pagina `apps/web/app/emission/review-signature/page.tsx` e integrar essa leitura na home operacional do back-office.

## Fora de escopo

- Sessao autenticada real, JWT, cookies, OAuth/OIDC, SAML ou SCIM.
- Persistencia real de memberships, work orders, reviews, approvals ou assinatura no banco.
- Assinatura eletronica real, PDF/A final ou envio de e-mail transacional.
- Workflow completo de reemissao, dupla aprovacao de mudanca de perfil ou excecoes Tipo A com diretor da qualidade.

## Criterios de aceite

- O contrato compartilhado representa papeis, checks, atribuicoes, sugestoes e estados do workflow de revisao/assinatura.
- A politica falha fechado quando `executor`, `revisor` e `signatario` violam segregacao de funcoes ou nao pertencem a organizacao ativa.
- O workflow falha fechado quando o revisor nao possui papel elegivel para revisao tecnica.
- O workflow falha fechado quando o signatario nao possui papel elegivel, nao tem MFA ou nao cobre o tipo de instrumento.
- As sugestoes de revisor e signatario sao deterministicas e escolhem o elegivel com menor fila.
- O endpoint `GET /emission/review-signature` responde com catalogo tipado e selecao por querystring.
- A pagina web traduz o workflow em estado operacional legivel e permanece fail-closed sem payload valido do backend.
- A home do back-office passa a resumir tambem a leitura canonica de revisao/assinatura.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/emission/review-signature-workflow.test.ts`
- `pnpm exec tsx --test apps/api/src/domain/emission/review-signature-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/emission/review-signature-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm test:tenancy`
- `pnpm check:all`
