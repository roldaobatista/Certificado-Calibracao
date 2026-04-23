# ADR 0059 — Pós-V5: calendário mínimo e exportação ICS da análise crítica

## Status

Aceito

## Contexto

Após a V5, a análise crítica já opera sobre registros reais do tenant, inclusive com `scheduledForUtc` persistido por reunião. Mesmo assim, o módulo ainda se comportava como leitura isolada do back-office, sem agenda consolidada mínima nem exportação simples para ferramentas externas.

Entre as evoluções sugeridas para o pós-V5, calendário da análise crítica é a menor fatia que adiciona coordenação operacional sem abrir o custo e o risco de ata binária ou assinatura eletrônica.

## Decisão

Adotar um calendário mínimo da análise crítica reutilizando a base já persistida na V5:

1. Expandir o contrato compartilhado da análise crítica com resumo de calendário, rótulo de agendamento e link de exportação `.ics`.
2. Centralizar a lógica de calendário e geração `.ics` em helper único no domínio de Qualidade.
3. Reusar `scheduledForUtc` existente, sem nova migração de banco.
4. Expor `GET /quality/management-review/calendar.ics` como exportação mínima, protegida por sessão na leitura persistida e liberada por `?scenario=` na leitura canônica.
5. Manter fora desta decisão qualquer integração bidirecional, GED binário ou assinatura eletrônica de reunião.

## Consequências

### Positivas

- Fecha uma lacuna operacional da análise crítica sem aumentar o acoplamento com infra externa.
- Mantém coerência entre cenário canônico, payload persistido e arquivo `.ics`.
- Reaproveita integralmente o dado já persistido na V5, sem tocar schema.

### Limitações honestas

- O `.ics` é apenas exportação pontual, sem sincronização posterior com agendas externas.
- Não há recorrência automática, lembretes nem notificações nesta fatia.
- Ata binária e assinatura eletrônica da análise crítica continuam como evoluções independentes.
