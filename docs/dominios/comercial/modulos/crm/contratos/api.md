---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: crm
dominio: comercial
diataxis: reference
---

# Contratos API — Módulo CRM

## Convenções

- Prefixo `/v1/crm`.
- Endpoint público NPS: `/v1/public/nps/{token}`.
- Bearer + `X-Tenant-ID` nos internos.

## Leads

### `POST /v1/crm/leads`
Criar lead (manual ou webhook futuro).
**Body:** `{origem, nome, telefone?, email?, mensagem_inicial?}`
**Evento:** `Lead.Criado`.

### `GET /v1/crm/leads`
Lista caixa de entrada.
**Query:** `estado`, `origem`, `vendedor_id`.

### `POST /v1/crm/leads/{id}/converter` (US-CRM-001)
Converter em cliente + oportunidade.
**Body:** `{tipo: "PF|PJ", documento, dados_completos, vendedor_responsavel_id}`
**Resposta:** `{cliente_id, oportunidade_id}`.
**Evento:** `Lead.Convertido`.

### `POST /v1/crm/leads/{id}/descartar`
**Body:** `{motivo}`.

## Oportunidades

### `POST /v1/crm/oportunidades`
**Body:** `{cliente_id, titulo, valor_estimado, funil_id?, responsavel_id, descricao?}`
**Evento:** criada na etapa inicial.

### `GET /v1/crm/oportunidades`
**Query:** `funil_id`, `etapa_id`, `responsavel_id`, `cliente_id`, `valor_min`, `valor_max`, `criada_de`, `criada_ate`.

### `GET /v1/crm/oportunidades/{id}`
Detalhes + histórico de etapas.

### `PATCH /v1/crm/oportunidades/{id}`
Atualizar campos.

### `POST /v1/crm/oportunidades/{id}/mover-etapa`
**Body:** `{etapa_id, motivo_perda_id?, observacao?}`
**Validação:** se etapa.tipo='perda' → motivo_perda_id obrigatório.
**Evento:** `Oportunidade.MovidaEtapa` (+ `.Ganha` ou `.Perdida` se terminal).

## Funis

### `GET /v1/crm/funis`
Listar funis do tenant.

### `POST /v1/crm/funis`
Criar funil custom.
**Body:** `{nome, etapas: [{nome, ordem, tipo}]}`

### `PATCH /v1/crm/funis/{id}`
Alterar etapas (com cuidado — mover oportunidades existentes).

## Tarefas

### `POST /v1/crm/tarefas`
**Body:** `{tipo, titulo, responsavel_id, prazo, relacionado_cliente_id?, relacionado_oportunidade_id?}`
**Origem:** manual ou automação (via header interno).

### `GET /v1/crm/tarefas`
**Query:** `responsavel_id`, `estado`, `prazo_de`, `prazo_ate`, `relacionado_cliente_id`.

### `PATCH /v1/crm/tarefas/{id}`
**Body:** `{estado: "feita|cancelada", observacao?}`

### `GET /v1/crm/lista-do-dia` (US-CRM-002)
**Query:** `responsavel_id` (default: usuário logado), `limite` (default 30).
**Resposta:** `{itens: [{cliente_id, score, sinais_ativos, ultima_interacao}]}`.
**Performance:** p95 < 2s.

## Automações

### `POST /v1/crm/automacoes`
Criar rascunho.
**Body:** `{nome, gatilho, condicao, acao}`
**Estado inicial:** `ativa=false, sandbox_ok=false`.

### `POST /v1/crm/automacoes/{id}/sandbox` (US-CRM-004)
Simula execução.
**Resposta:** `{clientes_afetados: [{id, nome, motivo}], total, exemplos_mensagem}`
**Efeito:** marca `sandbox_ok=true` se revisado.

### `POST /v1/crm/automacoes/{id}/ativar`
Ativa.
**Validação:** `sandbox_ok=true` (INV específica — bloqueia se false).
**Evento:** `Automacao.Ativada`.

### `POST /v1/crm/automacoes/{id}/desativar`
Pausar (não deletar).

### `GET /v1/crm/automacoes/{id}/execucoes`
Histórico de execuções (auditoria — JTBD-099).

## NPS

### `POST /v1/crm/nps/disparar` (interno — via job)
Cria token + envia link via WhatsApp/e-mail.
**Body:** `{cliente_id, os_id, canal}`

### Público `GET /v1/public/nps/{token}`
Carregar formulário (sem dados sensíveis).

### Público `POST /v1/public/nps/{token}`
Cliente responde.
**Body:** `{nota: 0-10, comentario?}`
**Rate limit:** 3 req/min/IP.
**Evento:** `NPS.Respondido`.

### `GET /v1/crm/nps`
Lista respostas (interno).
**Query:** `de`, `ate`, `categoria`, `cliente_id`.

## Eventos consumidos

- `Cliente.Criado` → cria oportunidade implícita (se config tenant ativa).
- `OS.Concluida` → dispara NPS + recalcula lead score.
- `Certificado.VencendoEm30d` → gatilho automação OP1.
- `Orcamento.Aprovado/Recusado` → move oportunidade.
- `Fatura.Vencida` → atualiza sinal lead score.

## Rate limits

- POST internos: 120 req/min/usuário.
- Mover etapa: 60 req/min (anti-spam).
- Endpoint NPS público: 3 req/min/IP.
- Automação ativar: 10 req/hora/tenant (anti-erro).

## Versionamento

v1 → v2 janela 6 meses.

## Como evolui

Endpoint novo → US-CRM-NNN.
