---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: comissoes
dominio: financeiro
---

# Contrato API — Comissões

## Recursos

### `GET /v1/comissoes`

Lista. Query: `?beneficiario_id=&status=&periodo_de=&periodo_ate=&page=`.

Permissão: vendedor/técnico só vê próprias; financeiro vê tudo do tenant.

### `GET /v1/comissoes/{id}`

Detalhe + cálculo transparente + linha do tempo + audit.

### `POST /v1/comissoes/{id}/contestar`

Body: `{ motivo, valor_proposto?, anexos[]? }`. Status muda pra `em-contestacao`.

### `POST /v1/comissoes/{id}/resolver-contestacao`

Body: `{ decisao: 'manter' | 'ajustar', valor_corrigido?, justificativa }`. Só financeiro/dono.

### `POST /v1/comissoes/lote-pagamento`

Fecha lote: junta todas `devida` do período → cria PagamentoComissao + transita pra `paga`.

Body: `{ periodo_de, periodo_ate, beneficiarios_ids[]? }`.

Resposta: `{ pagamento_lote_id, total_comissoes, valor_total }`.

### `GET/POST /v1/regras-comissao`

CRUD. POST cria nova versão com `vigente_de`. Não permite editar regra histórica.

### `GET /v1/comissoes/{id}/demonstrativo`

PDF do demonstrativo individual.

## Eventos consumidos (internos)

- `OSConcluida` → cria Comissao prevista
- `Pago` → transita pra devida
- `TituloCancelado` → estorno se devida/paga

## Webhooks de saída

- `comissao.prevista`
- `comissao.devida`
- `comissao.paga`
- `comissao.estornada`
- `comissao.contestada`

## Erros

| Código | Significado |
|---|---|
| `regra_ausente` | beneficiário sem regra ativa |
| `os_sem_beneficiario` | OS não tem vendedor/técnico atribuído |
| `lote_ja_fechado` | tentar fechar mesmo período 2× |
| `regra_retroativa` | tentativa de alterar regra histórica — bloqueado |

## Rate limiting

- Listagem: 600/min/tenant
- Lote: 5/min/tenant (operação cara)

## Audit

INV-008. Toda mudança de regra + cada cálculo + cada transição registra `actor`, `before`, `after`, `ts`.

## Non-goals API

- Endpoint de "simular fórmula nova" (Wave B / V2)
- API pública pro vendedor consumir externamente (V2)
- GraphQL

## Referências

- OP4
- `docs/comum/integracoes-inter-modulos.md`
