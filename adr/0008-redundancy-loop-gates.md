# ADR 0008 — Gates de redundância e loops

## Status

Proposto para P0-11 em 2026-04-20.

## Contexto

O harness define que "passou uma vez" não é evidência suficiente em áreas regulatórias. O repositório já tinha fuzz RLS com 500 iterações, mas faltavam:

1. um inventário auditável de propriedades e N por criticidade;
2. um gate local que rejeite política de seeds fraca;
3. um registro canônico para flakes;
4. um registro canônico para decisões regulatórias novas;
5. um plano determinístico para dupla checagem regulatória e reviews adjacentes.

## Decisão

1. `evals/property-config.yaml` passa a declarar propriedades, requisito rastreado, criticidade, N, seeds canônicos, comando e caminho de reports.
2. `tools/redundancy-check.ts` valida:
   - `blocker >= 500`;
   - `high >= 100`;
   - `medium >= 50`;
   - `low >= 10`;
   - `canonical_seeds` não vazio;
   - teste referenciado existente;
   - requisito existente no dossiê e criticidade consistente.
3. O flake gate noturno é representado por `.github/workflows/nightly-flake-gate.yml` e por logs em `compliance/validation-dossier/flake-log/`.
4. Interpretações normativas inéditas são registradas em `compliance/regulator-decisions/`.
5. `redundancy-check plan` sinaliza dupla checagem regulatória para `packages/normative-rules/**` e `apps/api/src/domain/emission/**`.
6. `redundancy-check plan` lista reviews adjacentes conforme `harness/15-redundancy-and-loops.md` §5.
7. `pnpm redundancy-check` entra em `pnpm check:all`.
8. `.claude/hooks/redundancy-check.sh` conecta o gate ao pre-commit canônico para deltas P0-11.

## Consequências

- Configuração de property testing fica versionada e auditável.
- Redução de N ou remoção de seeds canônicos passa a bloquear localmente.
- O flake gate noturno ainda depende de CI real e da classificação manual de `qa-acceptance`.
- Reviews adjacentes são planejados por ferramenta, mas a exigência no GitHub ainda depende de branch protection/CODEOWNERS.
- Self-consistency regulatória fica preparada por template e registro, mas execução real ainda ocorre por processo de revisão.
