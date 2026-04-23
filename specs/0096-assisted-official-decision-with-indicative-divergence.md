# 0096 - Decisao Oficial Assistida com Divergencia Justificada

## Contexto

As ondas anteriores introduziram:

- captura bruta estruturada;
- analise metrologica preliminar;
- EMA indicativo da Portaria Inmetro 157/2022;
- decisao indicativa baseada em regra de decisao e `U` preliminar.

Faltava transformar essa analise em suporte controlado ao workflow oficial de revisao, sem converter a decisao indicativa em gate automatico de emissao.

## Objetivo

Implementar um modo de **decisao assistida** no fluxo de revisao tecnica, em que:

1. a OS persiste um snapshot da decisao indicativa vista pelo revisor;
2. o revisor precisa registrar explicitamente a decisao oficial ao aprovar a revisao;
3. qualquer divergencia entre decisao oficial e decisao indicativa exige justificativa formal;
4. review, preview e trilha de auditoria exibem esse contexto.

## Escopo

### Persistencia

- Adicionar campos canonicos na `ServiceOrder` para:
  - `indicativeDecisionSnapshot`
  - `officialDecisionDivergesFromIndicative`
  - `officialDecisionJustification`
- Mapear esses campos na persistencia em memoria e Prisma.

### Workflow de revisao

- Estender `saveServiceOrderWorkflow` para:
  - recomputar a decisao indicativa vigente da OS;
  - materializar e persistir o snapshot indicativo;
  - exigir `decisionOutcomeLabel` explicito ao aprovar a revisao;
  - exigir justificativa quando a decisao oficial divergir do snapshot indicativo.

### Exposicao no produto

- Exibir o contexto de decisao assistida em:
  - `service-order-review`
  - `review-signature`
  - `certificate-preview`
  - `audit-trail`

### Auditoria

- Registrar o contexto de decisao assistida como metadata do evento `technical_review.completed`.

## Fora de escopo

- Transformar a decisao indicativa em gate automatico por si so.
- Substituir a regra oficial do certificado por um calculo ainda classificado como preliminar.
- Implementar assinatura ICP-Brasil ou PDF/A formal.

## Regras

1. A decisao indicativa continua sendo **assistiva**, nao soberana.
2. A aprovacao do workflow exige decisao oficial explicita do revisor.
3. Divergencia sem justificativa falha fechado.
4. Divergencia com justificativa continua auditavel e visivel ao signatario.

## Critérios de aceite

- Aprovar revisao sem `decisionOutcomeLabel` retorna conflito.
- Aprovar revisao com decisao oficial divergente e sem justificativa retorna conflito.
- Aprovar revisao com decisao oficial alinhada persiste snapshot indicativo + decisao oficial.
- A previa do certificado mostra assistencia decisoria e justificativa quando houver.
- A trilha de auditoria do evento de revisao expõe metadados de decisao oficial, decisao indicativa e justificativa.
