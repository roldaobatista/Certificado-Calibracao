# ADR 0027 — integridade do vínculo `linked_requirements` no roadmap

Status: Aprovado

Data: 2026-04-20

## Contexto

A ADR 0026 passou a usar `compliance/roadmap/v1-v5.yaml` como fallback canônico para o agrupamento L0 da cascata. Isso resolveu a dependência exclusiva de `L0/<EPIC-ID>` no log, mas deixou uma fragilidade nova: o gate ainda aceitava qualquer string em `linked_requirements`, inclusive IDs inexistentes ou repetidos entre fatias.

Se isso ficasse solto, o fallback da cascata passaria a depender de cadastro manual sem integridade.

## Decisão

`tools/roadmap-check.ts` passa a validar a integridade de `linked_requirements` contra `compliance/validation-dossier/requirements.yaml`:

- cada `REQ-ID` referenciado precisa existir na fonte canônica de requisitos;
- um mesmo `REQ-ID` não pode aparecer em mais de uma fatia do roadmap.

Essas violações passam a emitir `ROADMAP-006`.

## Consequências

O roadmap deixa de ser apenas uma lista ordenada de fatias e passa a carregar um mapa `REQ -> EPIC` com integridade mínima executável.

Isso reduz o risco de falso agrupamento na cascata e mantém uma única fonte de verdade para IDs válidos: `requirements.yaml`.

## Limitação

A regra garante existência e unicidade, mas não garante completude semântica. Um requisito ainda pode estar vinculado à fatia errada e continuar passando pelo gate se o ID existir e for único.
