---
owner: <lider-tecnico>
ultima-conferencia: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 140
proposito: politica de janela de mudanca e freeze para reduzir risco em producao
---

<!-- proposito: politica de janela de mudanca e freeze (quando pode subir versao nova, quando nao pode) | renomear-para: docs/operacao/change-management.md -->

# Janela de Mudança e Freeze — <nome-do-projeto>

> **Janela de mudança** = período do dia/semana em que é permitido **subir versão nova** (deploy) ou aplicar mudança em produção.
> **Freeze** = "congelamento", período em que NADA não-crítico sobe (mesmo dentro da janela).
>
> Objetivo: reduzir risco de quebrar o sistema em horário em que o impacto é maior ou o time está indisponível.

## 1. Janela padrão

| Item | Definição |
|---|---|
| Dias permitidos | terça, quarta, quinta |
| Horário permitido | 10:00 - 16:00 (fuso `America/Sao_Paulo`) |
| Dias bloqueados sempre | sexta, sábado, domingo, segunda |
| Vésperas de feriado | bloqueado nas 24h anteriores |

Justificativa do bloqueio de sexta/segunda:
- Sexta: se quebrar, fim de semana sem time para corrigir.
- Segunda: primeira hora de operação com volume alto, evitar.

Exemplo preenchido:
> Deploy de versão `1.4.2` agendado para terça 2026-06-02 às 11:00.

## 2. Freeze (congelamento)

Períodos em que NADA não-crítico sobe, mesmo dentro da janela padrão:

| Tipo de freeze | Quando | Quem aprova |
|---|---|---|
| Freeze comercial | dia de evento comercial relevante (lançamento, campanha grande do cliente) | produto |
| Freeze fiscal | último dia útil do mês + primeiro dia útil do mês (fechamento) | financeiro + tech lead |
| Freeze de release importante | véspera e dia de release de versão major | tech lead |
| Freeze de fim de ano | 20 de dezembro a 05 de janeiro | tech lead + direção |
| Freeze a pedido do cliente | conforme contrato (ex: cliente em auditoria externa) | comercial + tech lead |

## 3. Quem aprova mudança dentro de freeze

> Em freeze, o padrão é **não subir**. Exceção precisa de aprovação formal.

| Tipo de mudança | Pode subir em freeze? | Quem aprova |
|---|---|---|
| Nova feature | não | n/a |
| Refator interno (sem mudança de comportamento) | não | n/a |
| Bug não-crítico | não, espera passar o freeze | n/a |
| Bug crítico afetando produção | sim, com processo expresso | tech lead + 1 revisor (2-eyes) |
| Correção de segurança crítica | sim, com processo expresso | tech lead + líder de segurança |

## 4. Processo expresso (correção crítica em freeze)

> "2-eyes" = "quatro olhos", duas pessoas precisam validar antes de subir. Evita decisão solitária sob pressão.

1. Abrir incidente classificado como SEV1 ou vulnerabilidade CRÍTICO/ALTO.
2. Tech lead aprova explicitamente em `#change-approvals`.
3. Segundo revisor valida o diff em até 30min.
4. Deploy executado com rollback plan pronto e canal `#war-room` aberto.
5. Smoke test pós-deploy obrigatório (ver §8).
6. Comunicação ao cliente se houver indisponibilidade prevista.
7. Registro em `docs/operacao/historico-mudancas.md` justificando a quebra de freeze.

## 5. Comunicação da mudança

| Tipo | Antecedência mínima | Canal |
|---|---|---|
| Mudança de rotina (janela padrão) | 24h | `#change-announcements` |
| Mudança com indisponibilidade prevista | 72h | `#change-announcements` + e-mail cliente |
| Mudança destrutiva (migration de schema, etc) | 1 semana | aviso em release notes + e-mail cliente |
| Correção expressa em freeze | imediato (após aprovação) | `#war-room` + status page |

## 6. Registro de mudanças

Toda mudança em produção gera linha em `docs/operacao/historico-mudancas.md`:

| Campo | Conteúdo |
|---|---|
| Data/hora | <YYYY-MM-DD HH:MM> |
| Versão | tag do release |
| Tipo | feature \| bugfix \| segurança \| refator \| infra |
| Autor / aprovador | nomes |
| Link da decisão | ADR se for decisão arquitetural |
| Alertas esperados | alertas que **vão disparar e são normais** por causa desta mudança (ex: pico de latência no aquecimento de cache, fila subindo durante migração) — para não reverter por alerta legítimo |
| Resultado | ok \| rollback \| parcial |

> **Regra dura:** toda mudança lista seus **alertas esperados** antes de subir. Alerta previsto na lista = comportamento conhecido, **não** dispara rollback. Só alerta fora da lista (§8) justifica reverter.

## 7. Plano de rollback (obrigatório)

Toda mudança, sem exceção, sobe com plano de rollback pronto:
- **Como reverter:** comando exato OU passo a passo.
- **Tempo esperado de rollback:** geralmente < 5min.
- **Sinal de quando reverter:** métrica X passa de Y, ou erro Z aparece em logs.
- **Testado em staging:** rollback do deploy anterior foi exercitado no ambiente de teste.

## 8. Pós-mudança (verificação obrigatória)

Após qualquer deploy:
1. Smoke test automático passou (suite mínima de validação).
2. Métricas de SLO continuam dentro do alvo (ver `slo-sli.md`).
3. Sem alerta novo nos 15min seguintes **fora da lista de alertas esperados** (§6). Alerta previsto não conta como falha.
4. Operador permanece "de prontidão" por 1h após deploy (não iniciar outra tarefa pesada).

Se algum passo falhar -> rollback imediato. Investigação depois.

## 9. Histórico de revisões

| Data | Revisor | Mudança |
|---|---|---|
| 2026-05-28 | <nome> | criação inicial |
