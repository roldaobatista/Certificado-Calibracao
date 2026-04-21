# Spec 0026 — trilhas transversais canônicas para exclusões do roadmap

## Objetivo

Remover a ambiguidade das exclusões em `coverage.excluded_requirements`: todo requisito de produto excluído do V1-V5 deve ser materializado em uma trilha transversal canônica, com owner, decisão de harness de referência e comandos de gate que já cobrem aquele requisito.

## Escopo

- Adicionar `compliance/roadmap/transversal-tracks.yaml` como artefato canônico complementar ao roadmap V1-V5.
- Fazer `roadmap-check` falhar quando `coverage.excluded_requirements` estiver preenchido e o artefato transversal estiver ausente.
- Fazer `roadmap-check` falhar quando um requisito excluído não estiver mapeado em nenhuma trilha transversal.
- Fazer `roadmap-check` falhar quando uma trilha transversal referenciar requisito fora de `coverage.excluded_requirements`.
- Validar `gate_commands` das trilhas contra scripts reais do `package.json`.

## Critérios de aceite

- `roadmap-check` falha com `ROADMAP-008` se `compliance/roadmap/transversal-tracks.yaml` estiver ausente enquanto houver exclusões no roadmap vertical.
- `roadmap-check` falha com `ROADMAP-008` se um `REQ-ID` de `coverage.excluded_requirements` não aparecer em exatamente uma trilha transversal.
- `roadmap-check` falha com `ROADMAP-008` se uma trilha transversal apontar para `REQ-ID` que não está em `coverage.excluded_requirements`.
- `roadmap-check` falha com `ROADMAP-008` se uma trilha transversal declarar `gate_commands` sem script real no `package.json`.
- `compliance-structure-check` passa a exigir `compliance/roadmap/transversal-tracks.yaml` como artefato canônico.

## Fora de escopo

- Criar um scheduler separado para trilhas transversais.
- Alterar a cobertura real dos gates transversais já implementados.
- Validar semântica profunda dos comandos além de sua existência canônica no `package.json`.
