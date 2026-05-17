---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
---

# Glossário do módulo Automações & BPM

> Termos específicos deste módulo. Transversais ficam em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Fluxo | Sequência de etapas com transições, condições e aprovações | "processo", "workflow" | desenho cadastrado no editor visual | ADR-0005 |
| Etapa | Nó do fluxo onde algo acontece (decisão humana ou ação automática) | "passo", "step" | parada do fluxo com responsável | — |
| Transição | Caminho entre duas etapas, condicionado a uma regra | "edge", "seta" | regra `de → para` | — |
| Alçada | Limite de valor/categoria que define quem pode aprovar | "limite de aprovação" | quem assina decisão até X reais | — |
| Pendência | Instância de aprovação aguardando ação humana | "tarefa", "ticket" | item no painel "Minhas Aprovações" | — |
| Delegação | Atribuição temporária de pendências do titular ao substituto | "procuração" | aprovador A respondendo por B | — |
| SLA de Etapa | Prazo configurado para conclusão da etapa | "deadline" | prazo, conta da entrada na etapa | — |
| Escalonamento | Ação automática quando SLA estoura (notifica nível superior) | "escalation" | alerta + roteamento ao gestor | — |
| Evento | Mensagem publicada por módulo de negócio que pode disparar regra | "trigger" | gatilho (ex: `Orcamentos.Submetido`) | ADR-0007 |
| Condição | Predicado booleano avaliado sobre payload do evento | "filtro", "where" | "se desconto > 20% e cliente novo" | — |
| Ação | Operação executada após condição verdadeira | "task", "job" | enviar e-mail, criar OS, bloquear | — |
| Catálogo | Lista pesquisável de eventos/condições/ações pré-aprovadas | "biblioteca" | menu de blocos pro editor visual | — |
| Regra | Tripla `evento + condição + ação` cadastrada no editor | "automação" | linha do catálogo de regras ativas | — |
| Versão de Fluxo | Snapshot imutável do fluxo no momento da publicação | "release" | número incrementado a cada save publicado | — |
| Instância | Execução concreta de um fluxo (orçamento X passando por etapas) | "caso", "process instance" | linha do log de execução | — |
| Shadow Mode | Modo de teste onde regra executa mas não aplica ação | "dry-run", "modo simulação" | "vai disparar mas não envia" | — |
| Reprocessamento | Re-execução manual ou automática de instância falhada | "retry" | linha duplicada no log com link à original | — |
| Log de Execução | Trilha imutável de cada disparo de regra/fluxo | "audit log" | quem/quando/qual versão/resultado | — |
| Substituto Temporário | Pessoa cadastrada pra receber pendências durante ausência | "férias", "stand-in" | aprovação roteada a outro | — |
| Painel de Pendências | Tela com lista filtrada de aprovações esperando ação | "inbox" | "Minhas Aprovações" / "Aprovações da Equipe" | — |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum (hook).
- Termo descontinuado → marcar `@deprecated` + janela de migração 3 meses.
- Mudança de definição → bump no CHANGELOG seção "Modificado" + aviso.

## Convenções

- Termos em PT-BR. Inglês mantido apenas quando virou jargão do mercado (BPM, SLA, shadow mode).
- Definição em 1 linha. Detalhe vai pra `docs/explicacoes/<termo>.md`.
