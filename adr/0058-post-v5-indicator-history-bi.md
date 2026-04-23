# ADR 0058 — Pós-V5: histórico persistido para BI mínimo dos indicadores

## Status

Aceito

## Contexto

Depois da V5, a Qualidade passou a operar sobre dados reais do tenant, mas o painel de indicadores ainda monta sua série mensal com snapshots sintéticos em memória. Isso deixa a leitura gerencial útil para navegação, porém fraca como evidência histórica consolidada.

Ao mesmo tempo, a próxima evolução sugerida pelo backlog pós-V5 inclui alternativas mais caras em infraestrutura e integração, como calendário externo, ata binária ou assinatura eletrônica da análise crítica.

## Decisão

Adotar como primeira fatia pós-V5 um BI histórico mínimo e persistido dos indicadores:

1. Criar uma tabela dedicada de snapshots mensais por tenant e por indicador.
2. Preservar o contrato atual de `GET /quality/indicators`, trocando a origem dos snapshots de sintética para persistida quando houver histórico disponível.
3. Abrir uma escrita mínima em `POST /quality/indicators/manage` para registrar consolidado mensal sem inventar um submódulo analítico paralelo.
4. Reusar o mesmo histórico persistido para coerência do painel e do hub da Qualidade.
5. Manter fora desta decisão qualquer dependência de calendário externo, GED binário, assinatura eletrônica de reunião ou warehouse dedicado.

## Consequências

### Positivas

- Fecha a principal lacuna explícita do módulo de indicadores após a V5.
- Entrega série histórica auditável sem quebrar o payload já consumido pelo back-office.
- Mantém a evolução pós-V5 em uma trilha de baixo acoplamento externo e baixo risco operacional.

### Limitações honestas

- Ainda não existe job mensal automático nem meta configurável por tenant.
- O histórico é um BI mínimo de snapshots consolidados, não um warehouse analítico completo.
- Calendário, ata binária e assinatura eletrônica da análise crítica continuam pendências independentes.
