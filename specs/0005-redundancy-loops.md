# 0005 — Redundância, loops e auto-consistência

## Contexto

O harness P0-11 exige múltiplas execuções e dupla checagem onde falso-negativo cria risco regulatório. Antes desta spec, o fuzz RLS já rodava 500 iterações, mas não havia configuração canônica de propriedades, gate estrutural para flake log ou registro de precedentes regulatórios.

## Escopo

- Criar `evals/property-config.yaml` como fonte de N por criticidade.
- Criar `tools/redundancy-check.ts`.
- Validar N mínimo e seeds canônicos por propriedade.
- Validar artefatos de flake gate noturno.
- Criar `compliance/regulator-decisions/` para precedentes e self-consistency.
- Planejar dupla checagem regulatória e reviews adjacentes por path alterado.
- Integrar `pnpm redundancy-check` ao `pnpm check:all`.
- Integrar o gate P0-11 ao pre-commit canônico para deltas relacionados.

## Fora de escopo

- Executar self-consistency real com agente `regulator`.
- Abrir issues automaticamente quando o flake gate falhar.
- Gravar traces de seed automaticamente.
- Classificar falhas `flake` vs `infra` sem intervenção de `qa-acceptance`.
- Aplicar branch protection real no GitHub para exigir reviews adjacentes.

## Requisitos

- REQ-HARNESS-P0-11-REDUNDANCY-LOOPS

## Critérios de aceite

- `pnpm redundancy-check` falha sem `evals/property-config.yaml`.
- Property `blocker` com `N < 500` falha fechado.
- Property sem `canonical_seeds` falha fechado.
- Property que aponta para requisito inexistente no dossiê falha fechado.
- Flake gate exige `compliance/validation-dossier/flake-log/README.md` e workflow noturno.
- Precedentes regulatórios exigem `compliance/regulator-decisions/README.md`.
- `pnpm redundancy-check:plan --changed packages/normative-rules/src/rules.ts` marca dupla checagem regulatória.
- `pnpm check:all` executa `pnpm redundancy-check`.
- `.githooks/pre-commit` executa `redundancy-check` quando arquivos P0-11 entram no delta.

## Evidência

- Configuração de propriedades: `evals/property-config.yaml`.
- Traces de seed: `evals/**/reports/<seed>.trace`.
- Flake log: `compliance/validation-dossier/flake-log/YYYY-MM-DD.yaml`.
- Precedentes regulatórios: `compliance/regulator-decisions/<norma>-<caso>.md`.
