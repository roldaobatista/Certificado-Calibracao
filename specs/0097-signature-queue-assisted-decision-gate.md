# 0097 - Gate de decisao assistida na fila de assinatura

## Contexto

A `spec 0096` levou a decisao assistida para a revisao tecnica, exigindo:

- decisao oficial explicita;
- snapshot da decisao indicativa;
- justificativa formal quando houver divergencia.

Faltava endurecer a camada seguinte do workflow para evitar bypass por chamada direta na fila de assinatura/emissao.

## Objetivo

Garantir que a fila de assinatura respeite a mesma politica fail-closed da revisao tecnica, de modo que:

1. a emissao direta nunca contorne a obrigatoriedade de decisao oficial;
2. divergencia sem justificativa continue bloqueando o fluxo mesmo apos a OS entrar em assinatura;
3. o signatario visualize o contexto de decisao assistida antes da assinatura.

## Escopo

### Persistencia de emissao

- Endurecer `emitServiceOrder` para revalidar:
  - `reviewDecision === approved`;
  - `decisionOutcomeLabel` presente;
  - justificativa obrigatoria quando `officialDecisionDivergesFromIndicative === true`.

### API da fila de assinatura

- Mapear conflitos de emissao para erros semanticamente estaveis no endpoint `/emission/signature-queue/manage`.
- Impedir que o precheck HTTP aceite emissao sem aprovacao formal de revisao.

### Exposicao no produto

- Exibir `decisionAssistance` no painel final da fila de assinatura com:
  - decisao oficial;
  - alinhamento ou divergencia;
  - snapshot da decisao indicativa;
  - aviso quando a justificativa for exigida;
  - justificativa registrada, quando houver.

## Fora de escopo

- Transformar a decisao indicativa em veredito automatico e soberano.
- Atualizar o baseline oficial de snapshots PDF.
- Introduzir ICP-Brasil, PAdES ou carimbo do tempo.

## Regras

1. A fila de assinatura herda o principio de `fail-closed`.
2. Emissao direta sem decisao oficial explicita retorna conflito.
3. Emissao direta com divergencia nao justificada retorna conflito.
4. O signatario deve enxergar o contexto decisorio antes de assinar.

## Critérios de aceite

- `emit` direto em OS aprovada sem `decisionOutcomeLabel` retorna `409 official_decision_required`.
- `emit` direto em OS aprovada com divergencia sem justificativa retorna `409 official_decision_divergence_justification_required`.
- A fila de assinatura persistida expõe `decisionAssistance` no painel de aprovacao.
- O fluxo autenticado de emissao continua funcionando quando a revisao esta aprovada e coerente.
