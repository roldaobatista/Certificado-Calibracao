# 0031 — Bloqueio de emissao por escopo e CMC em laboratorio acreditado

## Contexto

O PRD §13.10 exige que certificado emitido por laboratorio acreditado respeite escopo e CMC. O mesmo PRD detalha, para o perfil regulatorio Tipo A, que:

- o simbolo Cgcre/RBC so pode aparecer dentro do escopo acreditado;
- item fora do escopo exige supressao do simbolo com aviso ao signatario;
- `U` expandida menor que a CMC declarada caracteriza inconsistencia tecnica e bloqueia a emissao do ponto;
- o perfil Tipo A nao pode operar sem cadastro formal de `scope_items` e `cmc_items`.

Ja existe uma politica executavel para perfis regulatorios A/B/C em `@afere/normative-rules`, mas o requisito vizinho de escopo/CMC ainda nao possui API dedicada nem teste regulatorio ativo.

## Escopo

- Adicionar em `packages/normative-rules` uma regra executavel para avaliar elegibilidade de emissao acreditada Tipo A.
- Diferenciar supressao de simbolo de bloqueio total de emissao.
- Bloquear ausencia de cadastro formal de escopo/CMC para perfil Tipo A.
- Bloquear `U` expandida inferior a CMC declarada.
- Validar o comportamento por teste regulatorio ativo em `evals/regulatory/prd-13-10-scope-cmc-block.test.ts`.
- Promover `REQ-PRD-13-10-SCOPE-CMC-BLOCK` para `validated` se a evidencia ficar verde.

## Fora de escopo

- Implementar matching real de `scope_items` por instrumento/faixa/classe.
- Consultar escopo Cgcre externo em runtime.
- Alterar renderer de PDF ou fluxo real de emissao em `apps/api`.
- Cobrir o requisito de competencia de signatario ou aprovacao de Gestor da Qualidade.

## Critérios de aceite

- Perfil `A` com acreditacao ativa, cadastro de escopo/CMC, item dentro do escopo e `U >= CMC` permite emissao acreditada com simbolo.
- Perfil `A` fora do escopo acreditado suprime o simbolo, registra aviso e ainda permite emissao sem simbolo.
- Perfil `A` com `U < CMC` bloqueia a emissao do ponto.
- Perfil `A` sem `scope_items` ou sem `cmc_items` bloqueia a emissao acreditada.
- O teste regulatorio falha se a API nao for exportada por `packages/normative-rules/src/index.ts`.

## Evidencia

- `pnpm exec tsx --test evals/regulatory/prd-13-10-scope-cmc-block.test.ts`
- `pnpm test:regulatory`
- `pnpm check:all`
