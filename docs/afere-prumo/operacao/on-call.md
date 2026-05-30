---
owner: <responsavel-operacao>
ultima-conferencia: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 120
proposito: escala e protocolo de plantao para incidentes fora do horario normal
---

<!-- proposito: escala e protocolo de plantao (quem atende incidente fora do horario, como passa o bastao, SLA por severidade) | renomear-para: docs/operacao/on-call.md -->

# Plantão (On-Call) — <nome-do-projeto>

> **On-call** (plantão) = profissional de sobreaviso, fora do horário comercial, responsável por atender alerta crítico e responder cliente quando o time normal não está disponível.

## 1. Escala

Turno semanal (segunda 09:00 até segunda seguinte 09:00, fuso `America/Sao_Paulo`).

| Semana | Início | Fim | Plantonista | Backup |
|---|---|---|---|---|
| atual | 2026-05-28 | 2026-05-28 | <nome-1> | <nome-2> |
| próxima | 2026-05-28 | 2026-05-28 | <nome-2> | <nome-3> |
| +2 | 2026-05-28 | 2026-05-28 | <nome-3> | <nome-1> |

Exemplo preenchido:
| 2026-S22 | 2026-05-25 | 2026-06-01 | Maria Silva | João Souza |

Escala publicada com 30 dias de antecedência em `docs/operacao/escala-oncall.md` (link para calendário compartilhado se houver).

## 2. Handover (passagem de turno)

Toda segunda 09:00, o plantonista que sai entrega o turno para quem entra.

Mensagem obrigatória em `#oncall-handover` cobrindo:
- **Pendências:** incidentes ainda abertos, com link e status.
- **Contexto recente:** mudanças em produção da última semana que podem causar alerta.
- **Alertas ativos:** rules silenciados temporariamente (com prazo para reativar).
- **Aviso de manutenção:** janelas agendadas para a semana entrante.
- **Saúde geral:** algo do sistema está instável? alguma métrica degradando?

## 3. Resposta esperada (SLA)

| Severidade | Definição curta | Ack (acusar recebimento) | Começo da ação | Resolução alvo |
|---|---|---|---|---|
| SEV1 (CRÍTICO) | serviço fora ou perda de dado em curso | 5 min | 15 min | 1 hora |
| SEV2 (ALTO) | degradação séria ou bug afetando muitos clientes | 30 min | 1 hora | 4 horas |
| SEV3 (MÉDIO) | bug afetando cliente específico ou funcionalidade não-crítica | 4 horas | próximo dia útil | 3 dias úteis |
| SEV4 (BAIXO) | cosmético, sem impacto operacional | próximo dia útil | sprint atual | sem SLA rígido |

> **Ack** = "acknowledge", confirmar que recebeu o alerta e está cuidando. Não significa que já resolveu.

## 4. Escalonamento

Quando o plantonista não consegue resolver sozinho, escalar conforme tabela:

| Nível | Quem | Quando acionar | Como |
|---|---|---|---|
| L1 | plantonista da semana | primeiro a atender qualquer alerta | paging automático |
| L2 | engenheiro especialista do domínio afetado | plantonista não identificou causa em 30min | mensagem direta + paging manual |
| L3 | tech lead / arquiteto | L2 não resolveu em 1h OU SEV1 com cliente impactado | telefonema direto |
| L4 | CTO / diretor técnico | crise prolongada (>2h sem caminho de solução) OU vazamento confirmado | telefonema direto |

Contatos atualizados em `docs/operacao/contatos.md` (NÃO commitar telefone pessoal aqui).

## 5. Compensação

Política da empresa para quem entra de plantão:

- **Folga compensatória:** 1 dia útil de folga a cada semana de plantão, usável em até 90 dias.
- **Acionamento fora do horário:** se for chamado fora do horário comercial (19h-08h ou fim de semana/feriado), conta hora extra com adicional de <X>%.
- **Plantão em feriado nacional:** adicional de <Y>% sobre a hora normal.
- **Revisão:** política revisada anualmente com RH.

> Detalhes contratuais em `docs/rh/politica-plantao.md`.

## 6. Ferramenta de paging

> **Paging** = sistema que aciona o plantonista (telefone, SMS, app) quando alerta dispara.

- **Ferramenta atual:** `<PagerDuty | Opsgenie | Better Stack | telefone direto>`.
- **Canal primário:** notificação push no celular do plantonista.
- **Canal secundário (escalonamento automático):** SMS após 5min sem ack.
- **Canal terciário:** ligação telefônica após 10min sem ack, depois aciona backup.
- **Testes:** simulação mensal de paging para confirmar que celular do plantonista está recebendo.

## 7. Pós-plantão (relato semanal)

Toda segunda 10:00, o plantonista que terminou o turno publica relato em `#oncall-relato`:

- **Incidentes atendidos:** lista com SEV, tempo de resolução, link do post-mortem (se SEV1/SEV2).
- **Falsos positivos:** alertas que dispararam mas não eram problema real. Sugerir ajuste do threshold.
- **Sugestões de melhoria:** runbook que faltou, métrica que ajudaria, automação que evitaria acionamento.
- **Carga subjetiva:** noite mal dormida? muitas interrupções? sinalizar para não virar burnout.

## 8. Histórico de revisões

| Data | Revisor | Mudança |
|---|---|---|
| 2026-05-28 | <nome> | criação inicial |
