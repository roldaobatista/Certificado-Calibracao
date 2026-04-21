# 0034 — Cobertura obrigatória de eventos críticos na trilha de auditoria

## Contexto

O PRD §13.6 exige que todo evento crítico do ciclo de calibração, revisão, assinatura, emissão e reemissão apareça na trilha de auditoria imutável. O PRD §7.10 detalha que a trilha é append-only, com hash do evento anterior, e precisa ser exportável para auditoria.

O pacote `@afere/audit-log` já verifica integridade da hash-chain, mas ainda não existe uma regra executável provando que um fluxo completo contém os eventos críticos mínimos do ciclo.

## Escopo

- Adicionar em `packages/audit-log` uma API que valide cobertura de eventos críticos sobre uma hash-chain já encadeada.
- Exigir, no mínimo, os eventos de calibração executada, revisão técnica concluída, assinatura do certificado e emissão oficial.
- Permitir exigir reemissão formal quando o cenário a demandar.
- Falhar fechado quando a hash-chain estiver inválida ou quando algum evento crítico estiver ausente.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-06-critical-event-audit-trail.test.ts`.
- Promover `REQ-PRD-13-06-CRITICAL-EVENT-AUDIT-TRAIL` para `validated` se a evidência ficar verde.

## Fora de escopo

- Modelar payload completo de cada evento com todos os campos do backend.
- Cobrir identidade, timestamp e dispositivo dos eventos de revisão/assinatura; isso fica no requisito vizinho §13.4.
- Integrar com `apps/api/src/domain/**` ou persistência real.

## Critérios de aceite

- A API rejeita trilha válida por hash quando faltar qualquer evento crítico obrigatório.
- A API reprova a trilha imediatamente se a hash-chain estiver adulterada.
- Quando `requireReissue` estiver ativo, `certificate.reissued` passa a ser obrigatório.
- O teste de aceite falha se a API não for exportada por `packages/audit-log/src/index.ts`.

## Evidência

- `pnpm exec tsx --test packages/audit-log/src/critical-events.test.ts`
- `pnpm exec tsx --test evals/ac/prd-13-06-critical-event-audit-trail.test.ts`
- `pnpm check:all`
