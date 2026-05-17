---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: orcamentos
dominio: comercial
diataxis: reference
---

# Contratos API — Módulo Orçamentos

## Convenções

- Prefixo `/v1/orcamentos`.
- Endpoint público (cliente externo): `/v1/public/orcamentos/{token}` — sem auth, com rate limit forte.
- `X-Tenant-ID` obrigatório nos endpoints autenticados.
- Erros RFC 7807.

## Endpoints internos

### `POST /v1/orcamentos`
Criar rascunho.
**Body:** `{cliente_id, template_id?, validade_ate, condicoes_pagamento, responsavel_id}`
**Resposta 201:** `{id, numero, estado: "rascunho", ...}`
**Invariantes:** INV-TENANT-001, cliente não bloqueado.
**US:** US-ORC-001.

### `POST /v1/orcamentos/{id}/itens`
Adicionar item.
**Body:** `{catalogo_item_id, quantidade, desconto?}`
**Resposta:** item criado + totais recalculados + comissão prevista.

### `PATCH /v1/orcamentos/{id}/itens/{item_id}`
Alterar quantidade/desconto.

### `DELETE /v1/orcamentos/{id}/itens/{item_id}`
Remover item (somente em rascunho).

### `GET /v1/orcamentos`
Lista filtrada.
**Query:** `estado[]`, `cliente_id`, `responsavel_id`, `de`, `ate`, `valor_min`, `valor_max`.

### `GET /v1/orcamentos/{id}`
Detalhes + versão ativa + histórico.

### `POST /v1/orcamentos/{id}/enviar`
Mudar de rascunho → enviado + gerar link público + disparar WhatsApp/e-mail.
**Body:** `{canal: "whatsapp|email|ambos", mensagem_extra?}`
**Resposta:** `{link_publico_url, expira_em}`
**Evento:** `Orcamento.Enviado`.

### `POST /v1/orcamentos/{id}/nova-versao` (Wave B)
Gerar nova versão a partir da ativa.
**Body:** snapshot da nova versão (itens, condições).
**Efeito:** revoga link antigo + cria nova versão ativa.

### `POST /v1/orcamentos/{id}/aprovar-manual`
Vendedor marca como aprovado (ex: cliente assinou em papel ou aprovou por WhatsApp).
**Body:** `{canal, observacao, anexo_url?}`
**Permissão:** vendedor responsável ou dono.
**Evento:** `Orcamento.Aprovado` → **trigger OS rascunho**.

### `POST /v1/orcamentos/{id}/recusar-manual`
**Body:** `{motivo}`.
**Evento:** `Orcamento.Recusado`.

### `POST /v1/orcamentos/{id}/cancelar`
Só em rascunho.

### `GET /v1/orcamentos/{id}/pdf`
Download do PDF.
**Resposta:** binário ou URL S3 assinada.
Ver `exports.md`.

### `POST /v1/orcamentos/{id}/aprovacao-interna` (Wave B)
Dono aprova internamente orçamento com desconto fora do limite.
**Body:** `{aprovado: bool, justificativa}`

## Endpoints públicos (sem auth — token)

### `GET /v1/public/orcamentos/{token}`
Carregar orçamento via link.
**Rate limit:** 30 req/min/IP.
**Resposta:** dados resumidos para cliente final (sem dados sensíveis como comissão).

### `POST /v1/public/orcamentos/{token}/aprovar`
Cliente aprova.
**Body:** `{nome_aprovador, email_aprovador, lgpd_aceite: true, observacao?}`
**Captura:** IP, user-agent, timestamp.
**Evento:** `Orcamento.Aprovado` → OS rascunho.
**US:** US-ORC-002.

### `POST /v1/public/orcamentos/{token}/recusar`
**Body:** `{motivo?}`

### `POST /v1/public/orcamentos/{token}/comentar`
Cliente pede ajuste (sem aprovar/recusar).
**Body:** `{texto}`
**Efeito:** notificação ao vendedor responsável.

### `GET /v1/public/orcamentos/{token}/pdf`
PDF público (sem dados de comissão).

### tracking pixel (Wave B): `GET /v1/public/orcamentos/{token}/leitura.gif`
Marca leitura.

## Eventos consumidos

- `Cliente.Bloqueado` → impede envio de orçamento novo.
- `Catalogo.PrecoAlterado` → **NÃO retroage** em orçamentos enviados (INV-026); só afeta rascunhos.

## Rate limits

- POST internos: 120 req/min/usuário.
- Endpoint público: 30 req/min/IP (anti-bot).
- POST aprovar público: 5 req/min/IP (anti-fraude).

## Versionamento

v1 → v2 com janela de 6 meses.

## Como evolui

Endpoint novo → US-ORC-NNN. Quebra de público → comunicação pra clientes.
