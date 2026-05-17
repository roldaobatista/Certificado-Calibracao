---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: qualidade
dominio: rh-frota-qualidade
---

# Contrato API — Qualidade

> Stack pendente (ADR-0001). REST + JSON.

## NC

### `GET /api/v1/ncs`
- Query: `status?`, `severidade?`, `instrumento_id?`, `origem?`, `responsavel_id?`, `q?`.

### `POST /api/v1/ncs`
- Body: `{ descricao, origem, severidade, instrumento_id?, os_id?, certificado_id?, padrao_id?, evidencias: [...], responsavel_id }`.
- Audit INV-001 obrigatório.

### `GET|PATCH /api/v1/ncs/{id}`
- PATCH limitado por status (campos imutáveis após FECHADA — INV-001 + audit).

### `POST /api/v1/ncs/{id}/cinco-porques`
- Body: `{ pergunta_1, resposta_1, ..., causa_raiz_final }`.
- Erro 422 `CINCO_PORQUES_INCOMPLETO` se campos faltam.

### `POST /api/v1/ncs/{id}/plano-acao/tarefas`
- Body: `{ descricao, responsavel_id, prazo }`.

### `POST /api/v1/ncs/{id}/plano-acao/tarefas/{tarefa_id}:concluir`
- Body: `{ evidencia_url }`. Sem evidência → 422 `EVIDENCIA_OBRIGATORIA`.

### `POST /api/v1/ncs/{id}/eficacia:agendar`
- Body: `{ data_agendada }`. Data passada → 422 `DATA_INVALIDA`.

### `POST /api/v1/ncs/{id}/eficacia:registrar`
- Body: `{ eficacia_confirmada: bool, observacao }`.

### `POST /api/v1/ncs/{id}:transicionar`
- Body: `{ novo_status }`. Erros: `5PORQUES_INCOMPLETO`, `PLANO_ACAO_PENDENTE`, `EFICACIA_NAO_AGENDADA`, `EFICACIA_NAO_REALIZADA`, `TRANSICAO_INVALIDA`.

## Hook INV-012 (consumido por Metrologia)

### `GET /api/v1/inv012/check?instrumento_id=X&padrao_id=Y`
- **Sem efeito colateral.** Usado pelo módulo Metrologia ANTES de emitir certificado.
- Resposta:
  ```json
  {
    "pode_emitir": false,
    "ncs_bloqueantes": [
      { "nc_id": "...", "numero": "NC-2026-0042", "severidade": "CRITICA", "descricao_curta": "...", "url_detalhe": "/qualidade/ncs/..." }
    ]
  }
  ```

## Reclamações

### `GET|POST /api/v1/reclamacoes`
- POST disponível pra Andréia CS L1 (P-QUA-03).

### `POST /api/v1/reclamacoes/{id}:virar-nc`
- Cria NC com `origem=RECLAMACAO` + link.

## NPS

### `POST /api/v1/nps:disparar`
- Body: `{ os_id }`. Idempotente por `(tenant_id, os_id)`.

### `POST /api/v1/nps/{id}/responder`
- Endpoint público (token assinado no link enviado ao cliente).
- Body: `{ score, comentario? }`.

### `GET /api/v1/nps/dashboard`
- Resposta agregada (média, % promotor/neutro/detrator).

## Riscos / Oportunidades

### `GET|POST /api/v1/riscos-oportunidades`

## Documentos da qualidade

### `GET|POST /api/v1/documentos-qualidade`
- POST cria nova versão (versão anterior fica `superseded_by_id` apontando pra nova).

## Webhooks (saída)

- `nc.aberta_critica` — notifica responsável tenant + Aferê (se cliente farma TOP V2).
- `nc.bloqueou_emissao` — P0 (notifica dono).
- `eficacia.vencida` — diário.
- `nps.detrator_com_comentario` — sugere abrir reclamação.

## Erros padronizados

`NC_NAO_ENCONTRADA`, `5PORQUES_INCOMPLETO`, `PLANO_ACAO_PENDENTE`, `EFICACIA_NAO_AGENDADA`, `EFICACIA_NAO_REALIZADA`, `TRANSICAO_INVALIDA`, `EVIDENCIA_OBRIGATORIA`, `NC_FECHADA_NAO_EDITAVEL`, `INSTRUMENTO_NAO_ENCONTRADO`.

## Rate limit

[INFERÊNCIA] 60 req/min escrita. Endpoint INV-012 check: 300 req/min (chamado por cada emissão).

## Não-existem MVP-1

Endpoints de cartas de controle, Cpk/Cp, auditoria interna estruturada, matriz quantitativa de risco. → MVP-2 / V2.
