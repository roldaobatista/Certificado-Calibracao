---
owner: <responsavel>
ultima-conferencia: 2026-05-28
severidade-procedimento: <rotina|emergencia|destrutivo>
status: draft
idioma: pt-BR
limite-linhas: 200
proposito: procedimento operacional executavel passo a passo
---

<!--
template: runbook.md
destino: docs/operacao/runbooks/<procedimento>.md
uso: procedimento operacional executável passo a passo.
Se passar do limite de linhas, fatie em sub-runbooks.

Campo `severidade-procedimento`:
- rotina: operação cotidiana, execução por um operador.
- emergencia: resposta a incidente, exige notificação no canal `#ops` antes/durante.
- destrutivo: exige aprovação de 2 pessoas (2-eyes) antes da execução. Ex: apagar dado, restaurar backup sobre produção, rotacionar segredo de produção fora de janela.
-->


# Runbook — <Nome do Procedimento>

## 1. Objetivo
<1 parágrafo explicando o que este runbook resolve. Ex: restaurar banco a partir de backup diário, rotacionar credenciais do provedor X, etc.>

## 2. Quando rodar
- Gatilho 1: <ex: alerta "fila travada > 5min">
- Gatilho 2: <ex: cliente reporta falha de login em massa>
- Janela recomendada: <ex: fora do horário comercial, ou imediato>

## 3. Pré-condições
- [ ] Acesso a <ferramenta/console> confirmado.
- [ ] Backup recente verificado (timestamp < 24h).
- [ ] Comunicar canal `#ops` antes de iniciar.
- [ ] Owner do serviço notificado (ver §7).

## 3.5 Diagnóstico rápido (antes de mexer)

Antes de executar qualquer ação corretiva, conferir o estado real do sistema. Mexer sem diagnosticar costuma piorar:

- [ ] **Logs recentes**: últimos 30 min do serviço afetado. O que mudou no padrão?
- [ ] **Métricas / dashboard**: CPU, memória, latência, taxa de erro, fila pendente. Comparar com baseline da última semana.
- [ ] **Últimos deploys / mudanças**: houve release, migração de dados ou mudança de configuração nas últimas 24h? (Causa #1 de incidente.)
- [ ] **Alertas correlatos**: outros serviços/alertas dispararam junto? Pode ser causa comum (ex: rede, provedor externo fora).
- [ ] **Status do provedor externo** (quando aplicável): página de status do fornecedor afetado.
- [ ] **Reprodução**: o problema é confirmável agora? Em qual ambiente?

Registrar o que foi observado em §8 (Histórico) mesmo que não exija ação.

## 4. Passos
1. <ação 1> — comando: `<comando>`.
2. <ação 2> — comando: `<comando>`. Resultado esperado: `<saída>`.
3. <ação 3>.
4. <ação 4>.

> Se qualquer passo falhar de forma inesperada, parar e seguir §6 (Rollback).
> Se `severidade-procedimento: destrutivo`, exigir confirmação explícita de uma segunda pessoa antes de cada passo marcado com `[2-eyes]`.

## 5. Verificação de sucesso
- [ ] Métrica `<nome>` voltou ao baseline em <janela>.
- [ ] Endpoint `<url>` responde 200 em verificação manual.
- [ ] Log `<padrão>` parou de aparecer.
- [ ] Cliente afetado confirmou retorno ao normal (quando aplicável).

## 6. Rollback
1. <ação reversa 1>.
2. <ação reversa 2>.
3. Restaurar estado anterior a partir de `<snapshot|backup|tag>`.
4. Confirmar restauração pelos mesmos checks de §5.

## 7. Escalonamento em camadas

Acionar de baixo para cima. Subir camada só quando o critério for atingido.

| Camada | Quem | Quando acionar |
|---|---|---|
| **L1 — Operador de plantão** | <nome/escala on-call> | imediato: faz a resposta inicial e segue este runbook |
| **L2 — Engenheiro do domínio** | <nome do owner técnico> | se L1 falhar 2 vezes consecutivas em mitigar **OU** 30 minutos sem mitigação |
| **L3 — Líder técnico** | <nome do líder> | se L2 não responder em 15 minutos **OU** se o incidente é classificado como SEV1 (impacto crítico em produção) |
| **Comercial** | <nome do contato comercial> | se o incidente afetar **cliente pagante** — independente da camada técnica em curso |
| **Fornecedor externo** | <nome / portal / telefone> | quando o diagnóstico apontar problema no fornecedor |

> Acionar significa: ligar (não só mensagem) + abrir thread no canal `#ops` com o estado atual.

## 8. Histórico de execução
| Data | Operador | Motivo | Resultado | Observações |
|---|---|---|---|---|
| 2026-05-28 | <nome> | <gatilho> | <ok|rollback|parcial> | <link p/ incidente, se houver> |

## 9. Pós-execução

Se este runbook foi acionado por **incidente real** (não execução de rotina), abrir **post-mortem em até 48 horas** usando `templates/post-mortem.template.md`.

Critério para abrir post-mortem:
- Houve impacto perceptível ao cliente (erro visível, lentidão acima do limite, perda de funcionalidade).
- Houve perda ou corrupção de dado (qualquer volume).
- O runbook precisou de rollback (§6).
- A causa raiz ainda é desconhecida ao fim da execução.

Não exige post-mortem: execução agendada de rotina sem ocorrência.
