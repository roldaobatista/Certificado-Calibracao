# ADR 0005 — Semântica de cobertura do dossiê de validação

## Status

Proposto para P0-3 em 2026-04-20.

## Contexto

O dossiê de validação precisa rastrear todos os critérios de aceite do PRD §13, mas o MVP ainda não possui implementação e testes ativos para todas as fatias de produto.

A semântica anterior do relatório tratava qualquer requisito como `covered`. Isso é adequado para gates já executáveis, mas seria enganoso ao mapear requisitos futuros: um critério pode estar rastreado no dossiê sem estar implementado, testado ou apto para release.

## Decisão

1. `requirements.yaml` passa a aceitar `validation_status`.
2. `validation_status: validated` é o padrão para requisitos existentes e exige `linked_tests` existentes.
3. `validation_status: planned` permite requisito rastreável sem teste ativo, desde que declare `planned_tests`.
4. A matriz passa a classificar critérios do PRD §13 como:
   - `validated`: possui requisito validado por teste ativo.
   - `mapped`: possui requisito rastreado, mas ainda planejado.
   - `missing`: não possui requisito.
5. O relatório de cobertura passa a separar critérios mapeados de critérios validados por teste ativo.
6. `--strict-prd` bloqueia apenas critério sem requisito mapeado. Critérios mapeados, mas ainda planejados, continuam bloqueados para release pelo status e pela ausência de evidência ativa.

## Consequências

- O dossiê pode alcançar rastreabilidade completa do PRD §13 sem inflar a cobertura validada.
- Próximas fatias verticais recebem uma lista explícita de testes planejados.
- A passagem de `planned` para `validated` exige código, teste ativo e evidência.
- P0-3 continua em implementação até que os critérios críticos estejam validados por testes e evidências reais.
