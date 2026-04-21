# 0038 — Bloqueio de assinatura por competência vigente

## Contexto

O PRD §13.9 exige que um signatário sem competência vigente para o tipo de instrumento não possa assinar. Ainda não existe um contrato executável no backend que valide competência por tipo de instrumento e janela temporal da assinatura.

## Escopo

- Adicionar em `apps/api/src/domain/competencies` uma API que avalie se um signatário pode assinar um instrumento em determinado instante.
- Exigir correspondência de tipo de instrumento e janela de vigência da competência.
- Falhar fechado quando faltarem dados mínimos ou quando o cadastro de competência estiver inconsistente.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-09-signatory-competence-block.test.ts`.
- Promover `REQ-PRD-13-09-SIGNATORY-COMPETENCE-BLOCK` para `validated` se a evidência ficar verde.

## Fora de escopo

- MFA, identidade jurídica da assinatura e RBAC.
- Persistência real de competências no banco.
- Assinatura eletrônica ou certificado ICP.

## Critérios de aceite

- A API permite assinatura quando existir competência vigente para o tipo de instrumento no instante informado.
- A API bloqueia assinatura quando a competência estiver vencida ou quando não houver competência para o instrumento.
- A API falha fechado quando faltarem dados obrigatórios ou quando o cadastro de competência estiver inválido.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/competencies/signatory-competence.test.ts`
- `pnpm exec tsx --test evals/ac/prd-13-09-signatory-competence-block.test.ts`
- `pnpm check:all`
