# ADR 0028 — cobertura explícita de requisitos de produto no roadmap

Status: Aprovado

Data: 2026-04-20

## Contexto

A ADR 0027 endureceu a integridade de `linked_requirements`, mas ainda deixava uma lacuna de governança: o roadmap não dizia explicitamente quais requisitos de produto ele pretendia cobrir e quais ficavam fora do V1-V5 por serem tratados como gates transversais.

Sem esse contrato, a ausência de um `REQ-PRD-*` no roadmap continuava ambígua: podia ser esquecimento ou decisão arquitetural não registrada.

## Decisão

Adicionar ao roadmap canônico um bloco `coverage` com dois campos:

- `tracked_requirement_prefixes`: prefixes de requisitos que o roadmap deve cobrir explicitamente;
- `excluded_requirements`: requisitos rastreados que ficam fora das fatias e precisam ser nomeados.

`tools/roadmap-check.ts` passa a validar que todo requisito rastreado esteja em exatamente um destes estados:

1. ligado a uma fatia por `linked_requirements`; ou
2. listado em `coverage.excluded_requirements`.

Para o estado atual do repositório, as exclusões explícitas são os requisitos de plataforma e governança transversal:

- `REQ-PRD-13-18-VALIDATION-DOSSIER`
- `REQ-PRD-13-19-AUDIT-HASH-CHAIN`
- `REQ-PRD-13-19-TENANT-SQL-LINTER`
- `REQ-PRD-13-19-WORM-STORAGE-CHECK`

## Consequências

O roadmap deixa de ser apenas um mapa parcial de fatias e passa a declarar, de forma auditável, o que ele cobre e o que fica fora do V1-V5.

Isso reduz ambiguidade em revisões futuras: requisito ausente sem exclusão explícita passa a ser bug de governança, não interpretação.

## Limitação

A cobertura continua sendo estrutural. O gate não garante que a fatia escolhida seja a melhor para aquele requisito; apenas garante que a decisão esteja registrada de forma explícita.
