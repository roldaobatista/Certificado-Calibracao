# ADR 0026 — fallback de `epic-review-flag` via roadmap canônico

Status: Aprovado

Data: 2026-04-20

## Contexto

A ADR 0025 tornou `epic-review-flag` executável, mas a agregação L0 ainda dependia de tokens `L0/<EPIC-ID>` nos próprios logs de verificação. Isso mantinha uma limitação operacional clara: uma equipe podia registrar corretamente a propagação L1 por requisito e, ainda assim, perder a re-auditoria de épico se esquecesse de escrever a referência L0.

Ao mesmo tempo, o repositório já tinha uma fonte canônica para o roadmap V1-V5 em `compliance/roadmap/v1-v5.yaml`, mas ela ainda não carregava metadados suficientes para servir como mapa estável de `REQ -> EPIC`.

## Decisão

Adicionar ao roadmap canônico, por fatia:

- `epic_id`: identificador estável do épico L0;
- `linked_requirements`: requisitos associados à fatia.

`tools/roadmap-check.ts` passa a tratar esses campos como obrigatórios.

`tools/verification-cascade.ts` passa a carregar um mapa permissivo de `REQ -> EPIC` a partir do roadmap e a usá-lo apenas como fallback quando um registro não trouxer `L0/<EPIC-ID>` explícito em `propagated_up` ou `re_audits_completed`.

## Consequências

`CASCADE-008` deixa de depender exclusivamente da disciplina manual do log e passa a aproveitar a fonte canônica já governada pelo gate de roadmap.

O contrato fica mais coerente:

- `roadmap-check` garante que a metadata existe e é versionada;
- `verification-cascade` consome essa metadata sem transformar falha documental em finding operacional espúrio.

Referências L0 explícitas continuam soberanas, preservando a rastreabilidade local quando ela existir.

## Limitação

O fallback continua tão bom quanto o mapeamento mantido em `compliance/roadmap/v1-v5.yaml`. Se um REQ estiver associado ao épico errado ou permanecer sem vínculo canônico, a agregação automática continuará incompleta.
