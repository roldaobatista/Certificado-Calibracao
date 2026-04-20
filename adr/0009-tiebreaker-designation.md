# ADR 0009 — Designação do tiebreaker

Status: Aprovado

Data: 2026-04-20

## Contexto

O P0-8 define que divergências entre agentes autoritativos não podem travar merge indefinidamente. O harness já tinha ADR 0002 para estratégia de sincronização, então a designação do tiebreaker passa a viver nesta ADR 0009.

## Decisão

O tiebreaker humano único para escalations D1-D9 é o **Responsável Técnico do Produto**.

A decisão do tiebreaker é final para a escalation específica, desde que registrada em `compliance/escalations/<YYYY-MM-DD>-<slug>.md` com:

- timestamp ISO-8601;
- papel assinado;
- resolução explícita;
- impacto aceito;
- aprendizado ou ADR/spec complementar quando a lacuna for estrutural.

## Sucessão

A substituição do Responsável Técnico do Produto exige nova ADR aprovada por `product-governance`. Enquanto não houver sucessor designado por ADR, o tiebreaker anterior permanece a autoridade formal ou a release fica congelada.

## Overrides

Override de gate automático continua exigindo ADR dedicada, aprovação de `product-governance`, registro em `compliance/overrides-log.md` com data de expiração e revisão na release seguinte.
