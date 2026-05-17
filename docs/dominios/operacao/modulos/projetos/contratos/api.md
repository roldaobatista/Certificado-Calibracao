---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: projetos
dominio: operacao
---

# Contratos de API — Módulo Gestão de Projetos

> Endpoints REST candidatos (ADR-0001 confirma).

## Convenções

- Versão `/v1/`.
- Auth `Authorization: Bearer ...`.
- Tenant `X-Tenant-ID` obrigatório (`INV-TENANT-001`).
- Erros: RFC 7807.
- Mutação aceita `Idempotency-Key`.

---

## Endpoints

### `POST /v1/projetos`
**Papel:** GERENTE_PROJETO, DONO.
**Request:**
```json
{
  "codigo": "PRJ-2026-001",
  "nome": "Instalação Balança Rodoviária — Fazenda X",
  "cliente_id": "uuid",
  "responsavel_id": "uuid",
  "data_inicio_prevista": "2026-06-01",
  "data_fim_prevista": "2026-09-30",
  "orcamento_previsto": 150000.00,
  "receita_prevista": 220000.00
}
```
**Response 201:** entidade criada (status PLANEJADO).
**Códigos:** 201, 400, 403, 409 (código duplicado no tenant), 422.
**Invariantes:** `INV-001`, `INV-TENANT-001`.
**US:** `US-PRJ-001`.
**Eventos:** `Projeto.Aberto`.

---

### `GET /v1/projetos?status=EM_EXECUCAO&cliente_id=...`
**Response 200:** array paginado.

---

### `GET /v1/projetos/{id}`
**Response 200:** entidade completa com agregados (etapas, marcos, orçamento, riscos resumidos).

---

### `POST /v1/projetos/{id}/iniciar`
**Pré:** status PLANEJADO.
**Pós:** EM_EXECUCAO + data_inicio_real = now.

### `POST /v1/projetos/{id}/pausar`
**Request:** `{ "motivo": "..." }`.
**Pós:** PAUSADO.

### `POST /v1/projetos/{id}/concluir`
**Pré:** todas etapas CONCLUIDAS + aceites registrados.
**Pós:** CONCLUIDO + data_fim_real.
**Eventos:** `Projeto.Concluido`.

---

### `POST /v1/projetos/{id}/etapas`
**Request:** `{ "ordem": 1, "nome": "...", "responsavel_id": "...", "data_prev_inicio": "...", "data_prev_fim": "...", "marco_de_faturamento": true, "valor_faturamento": 50000 }`
**Response 201:** etapa.
**US:** `US-PRJ-002`.

### `PATCH /v1/projetos/{projeto_id}/etapas/{id}`
Atualiza datas, % concluído, status (com transições válidas).
**US:** `US-PRJ-002`, `US-PRJ-004`.

### `POST /v1/projetos/{projeto_id}/etapas/{id}/concluir`
**Pré:** entregáveis ENTREGUE.
**Pós:** Etapa CONCLUIDA.
**Eventos:** `Etapa.Concluida` + `Marco.Atingido` se marco.

---

### `POST /v1/projetos/{projeto_id}/etapas/{id}/aceite`
**Request:**
```json
{
  "cliente_representante_nome": "...",
  "cliente_representante_cpf": "...",
  "observacoes": "...",
  "assinatura_digital_evidencia": "base64..."  // opcional
}
```
**Response 201:** aceite criado, imutável.
**US:** `US-PRJ-007`.
**Invariantes:** `INV-001`, `INV-017` análogo se assinatura digital.

---

### `POST /v1/projetos/{projeto_id}/aditivos`
**Request:**
```json
{
  "motivo": "...",
  "alteracao_escopo": "...",
  "alteracao_prazo_dias": 30,
  "alteracao_valor": 25000.00
}
```
**Response 201:** Aditivo PROPOSTO.
**US:** `US-PRJ-008`.

### `POST /v1/projetos/{projeto_id}/aditivos/{id}/aprovar`
**Papel:** GERENTE_PROJETO, DONO.
**Pós:** Aditivo APROVADO + atualiza orçamento e data_fim_prevista (sem retroceder original — `INV-026` análogo).
**Eventos:** `Aditivo.Aprovado`.

### `POST /v1/projetos/{projeto_id}/aditivos/{id}/rejeitar`
**Request:** `{ "motivo": "..." }`.

---

### `POST /v1/projetos/{projeto_id}/riscos`
**Request:**
```json
{
  "descricao": "...",
  "probabilidade": 4,
  "impacto": 5,
  "categoria": "TECNICO",
  "plano_mitigacao": "...",
  "responsavel_id": "uuid",
  "prazo": "2026-07-15"
}
```
**Response 201:** risco com nível calculado.
**US:** `US-PRJ-006`.

### `PATCH /v1/projetos/{projeto_id}/riscos/{id}`
Atualiza status (MITIGADO, MATERIALIZADO, ENCERRADO).
**Eventos:** `Risco.Materializado` se aplicável.

---

### `POST /v1/projetos/{projeto_id}/diario`
**Request:**
```json
{
  "data": "2026-06-15",
  "texto": "...",
  "anexos": ["s3://..."]
}
```
**Response 201:** entrada imutável + hash.
**Invariantes:** `INV-001`.
**US:** `US-PRJ-006`.

---

### `POST /v1/projetos/{projeto_id}/documentos`
Multipart upload. Versiona automático.
**Pós:** Documento com nova versão.

### `GET /v1/projetos/{projeto_id}/documentos?tipo=CONTRATO`
**Response 200:** lista com versões.

---

### `POST /v1/projetos/{projeto_id}/reunioes`
**Request:** participantes[], pauta, ata, decisoes[], proximos_passos[].
**Response 201:** reunião gravada.

---

### `GET /v1/projetos/{projeto_id}/orcamento`
**Response 200:** itens com previsto + realizado + % consumido.
**US:** `US-PRJ-005`.

### `GET /v1/projetos/{projeto_id}/gantt`
**Response 200:** estrutura otimizada pra render Gantt (etapas, marcos, dependências).
**US:** `US-PRJ-004`.

---

## Eventos consumidos

- `OS.Concluida` (módulo OS) → agrega custo realizado em OrcamentoItem.
- `Compra.Recebida` (módulo Compras) → agrega custo.
- `Estoque.Baixado` (módulo Estoque) → agrega custo de peça.
- `Faturamento.Emitido` (módulo Financeiro) → agrega receita realizada.

Ver `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- `POST /v1/projetos`: 30 req/min/tenant.
- `GET /v1/projetos/{id}/gantt`: 60 req/min/tenant.

## Versionamento

v1, v2 coexistem 6 meses. Quebra → ADR + CHANGELOG.
