# Spec 0025 — cobertura explícita de requisitos de produto no roadmap V1-V5

## Objetivo

Transformar o roadmap V1-V5 em contrato explícito de cobertura dos requisitos de produto: cada `REQ-PRD-*` deve estar ligado a uma fatia do roadmap ou explicitamente excluído por ser coberto por um gate transversal fora das fatias.

## Escopo

- Adicionar um bloco `coverage` em `compliance/roadmap/v1-v5.yaml`.
- Declarar em `coverage.tracked_requirement_prefixes` quais prefixes de requisito o roadmap cobre.
- Declarar em `coverage.excluded_requirements` os `REQ-ID`s de produto que ficam fora do V1-V5 por pertencerem a guardrails transversais.
- Fazer `roadmap-check` falhar quando um requisito rastreado não estiver nem ligado a uma fatia nem excluído explicitamente.
- Fazer `roadmap-check` falhar quando um requisito excluído também estiver ligado a uma fatia.

## Critérios de aceite

- `roadmap-check` falha com `ROADMAP-007` se `coverage.tracked_requirement_prefixes` estiver ausente ou vazio.
- `roadmap-check` falha com `ROADMAP-007` se um `REQ-PRD-*` rastreado não estiver coberto por `linked_requirements` nem por `coverage.excluded_requirements`.
- `roadmap-check` falha com `ROADMAP-007` se um `REQ-ID` excluído também aparecer em `linked_requirements`.
- O roadmap canônico do repositório declara explicitamente as exceções transversais hoje cobertas pelos gates de plataforma (`§13.18` e `§13.19`).

## Fora de escopo

- Garantir correção semântica do vínculo requisito↔fatia.
- Alterar a cobertura real dos gates de plataforma.
- Exigir cobertura explícita para `REQ-HARNESS-*`.
