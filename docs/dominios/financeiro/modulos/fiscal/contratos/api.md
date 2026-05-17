---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fiscal
dominio: financeiro
---

# Contrato API — Fiscal

## Recursos

### `POST /v1/fiscal/nfs-e`

Emite NFS-e.

Body: `{ cliente_id, valor_servico, descricao, codigo_lc116, os_id?, titulo_id?, campos_fiscais? }`

`campos_fiscais` (todos opcionais, valores informados — não calculados): `{ valor_iss_retido, valor_inss, valor_irrf, valor_pis, valor_cofins, valor_csll, aliquota_iss }`.

Idempotência: `Idempotency-Key` obrigatório (evita emissão dupla por clique).

Resposta `201`: `{ documento_id, numero, protocolo, xml_url, pdf_url, modo }`

Auth: MFA obrigatório (auditor segurança = FAIL se ausente).

### `POST /v1/fiscal/nfe` (V2)

Mesma estrutura adaptada pra padrão NFe.

### `POST /v1/fiscal/documentos/{id}/cancelar`

Body: `{ razao }`. Bloqueio se > 24h sem flag extemporâneo.

### `POST /v1/fiscal/documentos/{id}/cce`

Body: `{ texto_correcao }` (< 1000 chars). Bloqueio se mexer em campos não-corrigíveis.

### `POST /v1/fiscal/numeracao/inutilizar`

Body: `{ tipo, serie, numero_de, numero_ate, justificativa }`.

### `GET /v1/fiscal/documentos`

Lista. Query: `?status=&periodo_de=&periodo_ate=&cliente_id=&modo=&page=`.

### `GET /v1/fiscal/documentos/{id}`

Detalhe + eventos + verificação WORM (hash).

### `GET /v1/fiscal/documentos/{id}/xml` `GET .../pdf`

Download de cada artefato; audit registra acesso.

### `GET /v1/fiscal/status-servico`

Estado upstream: `{ municipio_X: ok|degraded|down, sefaz_uf_Y: ok|... }`. Alimenta banner contingência.

### `GET/POST /v1/fiscal/configuracao`

CRUD configuração fiscal do tenant.

## Webhooks de entrada (BaaS → Aferê)

### `POST /v1/webhooks/fiscal/{provider}`

Eventos: documento autorizado, rejeitado, cancelamento confirmado, status serviço.

- Assinatura HMAC obrigatória
- Idempotência por `protocolo`

## Webhooks de saída (Aferê → tenant)

- `nfse.emitida`
- `nfse.cancelada`
- `cce.emitida`
- `contingencia.ativada` / `contingencia.encerrada`
- `certificado.proximo-vencimento`

## Erros

| Código | Significado |
|---|---|
| `config_fiscal_incompleta` | falta cnpj/inscrição/regime |
| `certificado_expirado` | A1/A3 fora da validade |
| `municipio_nao_suportado` | BaaS sem cobertura |
| `cancelamento_extemporaneo` | > 24h — requer flag explícita |
| `cce_invalido` | tentou corrigir campo não-corrigível |
| `mfa_obrigatorio` | endpoint exige MFA, ausente |

## Rate limiting

- Emissão: 60/min/tenant; 1000/h.
- Listagem: 600/min/tenant.

## Audit obrigatório (INV-008)

Cada emissão/cancelamento/CC-e/inutilização/download registra `actor`, `tenant`, `documento`, `action`, `mfa_validado`, `mode` (normal/contingência), `ts`.

## Non-goals API

- Endpoint de "calcular imposto" (decisão fundadora)
- GraphQL
- Export SPED (V2)

## Referências

- ADR-0008 (FiscalProvider), ADR-0009 (A3)
- `docs/comum/integracoes-externas/plugnotas.md`, `focus-nfe.md`
- INV-007, INV-008
