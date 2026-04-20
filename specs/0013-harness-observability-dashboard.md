# Spec 0013 — Dashboard de observabilidade do harness

## Objetivo

Implementar a primeira fatia funcional do P2-3: um dashboard Markdown gerado que consolida status do harness, cobertura do PRD §13 e gates ativos em `check:all`.

## Escopo

- Artefato gerado em `compliance/harness-dashboard.md`.
- Gerador/checker `tools/harness-dashboard.ts`.
- Testes em `tools/harness-dashboard.test.ts`.
- Scripts `pnpm harness-dashboard:write` e `pnpm harness-dashboard:check`.
- Integração em `pnpm check:all` e pre-commit.

## Critérios de aceite

- O dashboard resume P0/P1/P2 por total, em implementação, implementado, proposto e rejeitado.
- O dashboard exibe cobertura atual do PRD §13 a partir de `coverage-report.md`.
- O dashboard lista os gates executados por `pnpm check:all`.
- O dashboard lista itens abertos do `harness/STATUS.md`.
- O gate falha se `compliance/harness-dashboard.md` estiver ausente ou desatualizado.

## Fora de escopo

- Não cria UI web nem integração com Grafana/Axiom.
- Não mede duração histórica dos gates.
- Não substitui `harness/STATUS.md`; o dashboard é derivado e não deve ser editado manualmente.
