# Spec 0082 — Pós-V5: assinatura persistida da análise crítica

## Contexto

Depois da V5 e do calendário mínimo pós-V5, a análise crítica já possui reunião persistida, agenda consolidada e exportação `.ics`, mas a ata continua sem metadado formal de assinatura. Isso deixa a reunião visível e agendada, porém ainda fraca como evidência de fechamento gerencial auditável.

Sem esta fatia pós-V5, a direção consegue registrar pauta e calendário, mas não consegue marcar formalmente que a ata da análise crítica foi assinada no tenant real.

## Escopo

- Persistir metadados mínimos de assinatura da análise crítica em `management_review_meetings`.
- Expandir o contrato compartilhado da análise crítica com o estado de assinatura da reunião selecionada.
- Adicionar ação autenticada de assinatura em `POST /quality/management-review/manage` sem abrir endpoint paralelo.
- Exibir estado, bloqueios e ação de assinatura na página web da análise crítica quando a leitura vier da camada persistida do tenant.
- Reaproveitar o usuário autenticado da sessão como ator da assinatura.

## Fora de escopo

- Assinatura ICP-Brasil, certificado digital externo, carimbo do tempo oficial ou qualquer PKI regulatória.
- Ata binária, upload/download de PDF, GED, storage WORM de anexo ou hash do binário da ata.
- Fluxo multiaprovador, contrassinatura, assinatura do cliente ou coautoria.
- Integração com portal externo, Android ou calendário bidirecional.

## Critérios de aceite

- `packages/db/prisma/schema.prisma` materializa os campos mínimos de assinatura da análise crítica, com migração dedicada.
- `apps/api/src/domain/quality/quality-persistence.ts` preserva e persiste `signedByUserId`, `signedByLabel`, `signatureDeviceId`, `signatureStatement` e `signedAtUtc`.
- `POST /quality/management-review/manage` aceita `action=sign` autenticado e falha fechado quando a reunião ainda não foi registrada como realizada ou quando a ata já estiver assinada.
- `GET /quality/management-review` expõe estado de assinatura tanto em cenários canônicos quanto na leitura persistida.
- `apps/web/app/quality/management-review/page.tsx` mostra estado da assinatura e libera o botão de assinar somente no modo persistido e com papel autorizado.
- Os testes do backend cobrem catálogo, fluxo persistido de assinatura e leitura posterior da ata assinada.

## Evidência

- `pnpm --filter @afere/contracts build`
- `pnpm --filter @afere/db build`
- `pnpm exec tsx --test apps/api/src/domain/quality/management-review-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/management-review-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm test:tenancy`
- `pnpm harness-dashboard:write`
- `pnpm check:all`
