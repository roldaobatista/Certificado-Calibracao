# 0030 — Perfis regulatorios A/B/C com template PDF e bloqueio de selo

## Contexto

O PRD §13.15 exige que o sistema reconheca os perfis regulatorios Tipo A, B e C, selecione automaticamente o template PDF correspondente e bloqueie uso indevido do selo Cgcre/RBC.

O repositorio ja tinha base documental para esse comportamento:

- PRD detalhando os tres perfis e os templates A/B/C;
- snapshots canonicos para perfis A/B/C;
- regra minima no pacote normativo baseline sobre uso do simbolo Cgcre/RBC;
- roadmap V3 exigindo bloqueio absoluto para Tipo B/C tentarem emitir com selo.

O gap era a ausencia de uma API executavel e pequena em `@afere/normative-rules` provando essa selecao e o bloqueio semantico.

## Escopo

- Adicionar em `packages/normative-rules` uma politica executavel para selecao de template por perfil.
- Modelar a politica de simbolo Cgcre/RBC como `allowed`, `suppressed` ou `blocked`.
- Bloquear semanticamente termos proibidos em texto livre do perfil C.
- Validar o comportamento por teste regulatorio ativo em `evals/regulatory/prd-13-15-regulatory-profiles-pdf.test.ts`.
- Promover `REQ-PRD-13-15-REGULATORY-PROFILES-PDF` para `validated` se a evidencia ficar verde.

## Fora de escopo

- Implementar renderer real de PDF em `apps/api/src/interfaces/pdf/**`.
- Implementar consulta real de escopo CMC ou tela de emissao.
- Cobrir o requisito vizinho `REQ-PRD-13-10-SCOPE-CMC-BLOCK`.

## Critérios de aceite

- Perfil `A` seleciona `template-a`.
- Perfil `A` fora do escopo acreditado suprime o simbolo, sem trocar o template.
- Perfil `B` seleciona `template-b` e bloqueia uso do simbolo.
- Perfil `C` seleciona `template-c`, bloqueia uso do simbolo e rejeita `RBC`/`Cgcre` em texto livre.
- O teste regulatorio falha se a API nao for exportada por `packages/normative-rules/src/index.ts`.

## Evidência

- `pnpm exec tsx --test evals/regulatory/prd-13-15-regulatory-profiles-pdf.test.ts`
- `pnpm test:regulatory`
- `pnpm check:all`
