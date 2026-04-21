# ADR 0029 — trilhas transversais para exclusões do roadmap

Status: Aprovado

Data: 2026-04-20

## Contexto

A ADR 0028 tornou explícito quais `REQ-PRD-*` o roadmap V1-V5 cobre e quais ficam excluídos por pertencerem a gates transversais. Ainda faltava uma garantia operacional: as exclusões estavam nomeadas, mas não havia um artefato canônico dizendo quem responde por cada uma, em qual decisão do harness ela se apoia e quais comandos comprovam sua cobertura.

Sem essa materialização, `coverage.excluded_requirements` continuava sendo uma lista estática sujeita a drift.

## Decisão

Adicionar `compliance/roadmap/transversal-tracks.yaml` como complemento obrigatório do roadmap quando houver requisitos excluídos do V1-V5.

Cada trilha transversal deve declarar:

- `id` e `title`;
- `owner`;
- `harness_refs`;
- `gate_commands`;
- `linked_requirements`.

`tools/roadmap-check.ts` passa a validar que:

1. toda exclusão em `coverage.excluded_requirements` apareça em exatamente uma trilha transversal;
2. nenhuma trilha transversal aponte para requisito fora de `coverage.excluded_requirements`;
3. os `gate_commands` apontem para scripts reais do `package.json`;
4. as referências de harness existam.

No estado atual do repositório, as trilhas transversais canônicas são:

- `T1-VALIDATION-DOSSIER` para `REQ-PRD-13-18-VALIDATION-DOSSIER`;
- `T2-TENANCY-GATE` para `REQ-PRD-13-19-TENANT-SQL-LINTER`;
- `T3-AUDIT-IMMUTABILITY` para `REQ-PRD-13-19-AUDIT-HASH-CHAIN`;
- `T4-WORM-RETENTION` para `REQ-PRD-13-19-WORM-STORAGE-CHECK`.

## Consequências

As exclusões do roadmap deixam de ser apenas exceções listadas e passam a compor uma trilha canônica, auditável e ligada aos gates reais do repositório.

Isso reduz drift de governança: requisito excluído sem trilha vira erro estrutural, e trilha sem gate canônico também.

## Limitação

O gate valida a existência e o vínculo estrutural dos comandos, não a suficiência semântica desses comandos para cobrir todo o requisito.
