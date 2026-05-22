---
adr: 0023
titulo: OS com Atividades (1 OS contém N atividades de tipos distintos)
status: aceito
data: 2026-05-23
proposto-por: roldao + agente
revisado-por: tech-lead-saas-regulado (review pré-Marco 3)
aceito-em: 2026-05-23 (decisão Roldão — Caminho B em AskUserQuestion)
bloqueia-fase: Wave A (Marco 3 `os` + Marco 4 `calibracao`)
depende-de: ADR-0002 (multi-tenancy), ADR-0007 (camada domínio)
---

# ADR-0023 — OS com Atividades

## Contexto

O modelo atual de OS (`docs/dominios/operacao/modulos/os/modelo-de-dominio.md`)
define `OS.tipo` como **enum único** (`calibracao | manutencao |
instalacao | verificacao_inmetro | vistoria`). O ChecklistDeOS depende
desse tipo único — "calibração exige padrao_usado + assinatura;
manutenção exige peca_consumida + foto". A máquina de estados (INV-027)
trata a OS inteira como um único trabalho.

Levantamento de operação real (Roldão, 2026-05-23) identificou que o
cenário **OS combinando manutenção corretiva/preventiva + calibração**
é comum no setor de assistência técnica metrológica:

- Cliente traz instrumento com problema mecânico e pede "consertem e
  calibrem" — é UM atendimento, mas com 2 trabalhos sequenciais.
- Contrato de manutenção preventiva trimestral inclui ajuste + calibração
  de verificação em cada visita.
- Instalação de balança nova exige instalação + calibração inicial.
- Verificação INMETRO pode requerer ajuste antes da emissão do laudo.

Com o modelo atual, atendente é forçado a:

1. Abrir 2 OS separadas (Caminho C avaliado e rejeitado) — cliente vê
   "2 OS" do mesmo serviço, recebe 2 documentos, parece duplicado e
   espelha mal a realidade operacional.
2. Escolher 1 tipo dominante e perder o checklist do outro — quebra
   ISO 17025 (registro incompleto do trabalho técnico).

## Decisão

**Adotar Caminho B: 1 OS contém N AtividadeDaOS.**

- A **OS continua sendo o container comercial/financeiro/atendimento**
  (1 cliente, 1 instrumento, 1 técnico atribuído, 1 fatura, 1 link
  pro portal).
- O **trabalho técnico se divide em N entidades `AtividadeDaOS`** —
  cada uma com:
  - `tipo` (mesmo enum atual: `calibracao | manutencao_corretiva |
    manutencao_preventiva | instalacao | verificacao_inmetro |
    vistoria`).
  - `checklist` próprio do tipo (validado pelo módulo correspondente).
  - `estado` próprio (PENDENTE → EM_EXECUÇÃO → CONCLUÍDA / NÃO_CONFORME).
  - `sequencia` opcional (manutenção precede calibração na mesma OS).
  - `tecnico_executor_id` (pode variar entre atividades da mesma OS —
    metrologista calibra, mecânico conserta).
- **Relação com módulo técnico (revisado NOVO-CRIT-1 R2 — 2026-05-23):** a FK
  fica **no módulo técnico, NÃO na AtividadeDaOS**. Exemplo:
  `Calibracao.atividade_os_id` aponta pra `AtividadeDaOS.id`. Query
  reversa via `AtividadeDaOS.calibracao_set` ou JOIN explícito.
  Decisão evita FK polimórfica não-tipada na AtividadeDaOS (que era
  string genérica `link_modulo_tecnico` no design original).
  Vantagens: (a) FK tipada com validação de tenant em trigger PG
  (INV-OS-ATIV-005c); (b) fonte única de verdade; (c) compatibilidade
  com RLS PostgreSQL nativa.
- **OS só fecha (CONCLUÍDA) quando TODAS as atividades concluem.**
- **Calibração técnica é disparada por `AtividadeDaOS.tipo=calibracao`**,
  não pela OS toda. AC-CAL-001-1 passa a aceitar "atividade de OS de
  tipo calibração" como porta de entrada (mantém "recepção avulsa"
  como alternativa).

## Caminhos alternativos considerados

| Caminho | Por que NÃO foi escolhido |
|---|---|
| **A — OS mãe + OS filhas** | Modelo limpo arquitetonicamente, mas força cliente a ver "1 atendimento e várias OS" — pior UX. Também complica faturamento (decisão entre NF única agregada vs NFs separadas vira problema fiscal por tenant). |
| **C — 2 OS sequenciais separadas** | Preserva modelo atual, mas espelha mal a realidade operacional. Atendente é forçado a quebrar mentalmente um serviço único em 2 registros, e o cliente recebe 2 OS no portal — confusão certa. |

## Consequências

### Positivas

- **UX natural**: cliente vê 1 OS que cobre o serviço completo,
  recebe 1 NF, 1 link de acompanhamento.
- **Cobrança correta**: itens da OS podem ser associados às atividades
  (peças da manutenção, hora-técnica da calibração) numa mesma fatura.
- **ISO 17025 preservada**: cada atividade de calibração mantém
  registro técnico completo (config, padrões, leituras, cálculo,
  2ª conferência), independente de existir manutenção na mesma OS.
- **Reabertura granular**: dá pra reabrir SÓ a atividade de calibração
  sem invalidar a manutenção concluída.
- **Faturamento por atividade** (Wave B possível): dono pode optar por
  faturar atividades concluídas antes da OS toda fechar — receita
  antecipada legítima.

### Negativas (mitigáveis)

- **Complexidade do agregado raiz** aumenta: OS deixa de ter
  `tipo` único + estado único; passa a ter `tipo_predominante`
  (estatística, opcional) + estado computado a partir das atividades.
- **Checklist sai do agregado OS** e vai pra AtividadeDaOS —
  refatoração antes do Marco 3 começar (zero código a quebrar hoje).
- **Eventos** mudam: `OSConcluida` continua existindo, mas ganha
  novos eventos `AtividadeIniciada`, `AtividadeConcluida`,
  `AtividadeNaoConforme`. Calibração consome o evento da atividade,
  não mais da OS.

### Tradeoffs aceitos

- **Faturamento atômico por OS** (não por atividade) na primeira
  versão Wave A — Wave B reavalia.
- **Reabertura granular por atividade** fica Wave B; Marco 3 reabre
  OS toda (modelo atual).

## Implicações pro faseamento

| Marco | Impacto |
|---|---|
| **Marco 3 `os`** | Construir OS + AtividadeDaOS desde o início. ChecklistDeOS migra pra dentro de AtividadeDaOS. Máquina de estados ganha camada (OS computa estado a partir das atividades). Eventos `AtividadeIniciada`/`AtividadeConcluida`/`AtividadeNaoConforme` adicionados. |
| **Marco 4 `calibracao`** | AC-CAL-001-1 atualizado: aceita "AtividadeDaOS tipo=calibracao" como porta de entrada (ou recepção avulsa). Trigger técnico parte do evento `AtividadeIniciada` filtrando por tipo. |
| **Marco N `manutencao`** | Mesmo pattern — `AtividadeDaOS tipo=manutencao_*` dispara fluxo de manutenção. |
| **Módulo `orcamentos`** | Conversão `Orcamento.Aprovado → OS rascunho` agora cria OS + N atividades a partir dos itens do orçamento (já são "itens", basta enriquecer com `tipo`). |
| **Módulo `fiscal`** | NF agrega itens de N atividades da MESMA OS — sem mudança estrutural; só ajustar query. |
| **Portal cliente** | Mostra "1 OS — 2 atividades em andamento" (sem confusão). |

## Non-goals (NÃO faz parte desta ADR)

- **NÃO** decide se faturamento por atividade entra no MVP-1 (fica
  Wave B com decisão própria).
- **NÃO** decide se OS pode ter atividades de tenants diferentes
  (resposta: NÃO — INV-TENANT-001 vale por OS inteira).
- **NÃO** redefine os 5 tipos de OS — só os move pra AtividadeDaOS.
- **NÃO** muda a relação OS ↔ Cliente (continua 1:1).
- **NÃO** muda RAT-08 (audit log continua, agora também por atividade).

## Invariantes novas

- **INV-OS-ATIV-001**: OS só pode transicionar pra CONCLUÍDA se TODAS
  as atividades estão em estado terminal (CONCLUÍDA ou CANCELADA).
- **INV-OS-ATIV-002**: AtividadeDaOS herda `tenant_id` + `cliente_id`
  + `equipamento_id` da OS pai (cross-tenant proibido).
- **INV-OS-ATIV-003**: Toda AtividadeDaOS tem `tipo` no enum fechado.
  Tipos novos exigem ADR + migration + atualização de hook.
- **INV-OS-ATIV-004**: ChecklistDaAtividade não migra entre atividades
  de tipos diferentes — cada tipo tem seu próprio modelo de checklist.

## Status

- 2026-05-23: **aceito** pelo Roldão via AskUserQuestion. Marco 3
  arranca já com este modelo; nenhum código a refatorar (Marco 3 é
  greenfield).
