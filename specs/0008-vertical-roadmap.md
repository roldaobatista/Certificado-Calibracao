# Spec 0008 — Roadmap em fatias verticais V1-V5

## Objetivo

Implementar o P1-4 como roadmap executável e verificável antes de iniciar V1.

## Escopo

- Criar `compliance/roadmap/v1-v5.yaml` como fonte canônica operacional.
- Manter `harness/10-roadmap.md` como decisão arquitetural explicativa.
- Validar ordem estrita V1-V5, dependências sequenciais e gates de saída.
- Integrar `pnpm roadmap-check` ao `pnpm check:all` e ao pre-commit.

## Critérios de aceite

- O gate falha se `compliance/roadmap/README.md`, `v1-v5.yaml` ou `harness/10-roadmap.md` estiverem ausentes.
- O gate falha se o YAML não contiver exatamente V1, V2, V3, V4 e V5 nessa ordem.
- O gate falha se V2-V5 não dependerem da fatia anterior.
- O gate falha se policy não exigir gate anterior, release-norm, dossiê e pacote normativo.
- O gate falha se uma fatia não declarar escopo, agentes primários, release-norm, dossiê e gates de saída.

## Fora de escopo

- Não implementa produto funcional de V1-V5.
- Não substitui specs específicas de cada fatia.
- Não aprova release-norm de fatias futuras.
