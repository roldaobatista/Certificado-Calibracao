# ADR 0060 — Pós-V5: assinatura mínima persistida da análise crítica

## Status

Aceito

## Contexto

Com a V5 e a fatia pós-V5 de calendário, a análise crítica passou a ter reunião persistida, agenda consolidada e exportação `.ics`, mas ainda sem fechamento formal da ata no nível da própria reunião. A próxima evolução natural é registrar assinatura mínima antes de investir em ata binária ou PKI mais pesada.

## Decisão

Adotar uma assinatura mínima persistida da análise crítica:

1. Acrescentar metadados mínimos de assinatura diretamente em `management_review_meetings`.
2. Reusar o usuário autenticado da sessão como ator da assinatura.
3. Expor o estado da assinatura no payload já existente de `GET /quality/management-review`.
4. Reusar `POST /quality/management-review/manage` com `action=sign` em vez de abrir endpoint paralelo.
5. Falhar fechado quando a reunião ainda não foi registrada como realizada ou quando a ata já estiver assinada.

## Consequências

### Positivas

- Fecha a lacuna mais imediata entre reunião persistida e ata formalmente encerrada.
- Mantém o fluxo simples, sem dependência externa e sem GED nesta fase.
- Preserva coerência entre cenário canônico, modo persistido e UI do back-office.

### Limitações honestas

- A assinatura é apenas metadado persistido do sistema, não assinatura digital qualificada.
- Ainda não existe ata binária, hash do anexo ou carimbo do tempo oficial.
- Fluxos multiassinatura e integrações externas continuam como evoluções futuras.
