---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fornecedores
dominio: suporte-plataforma
---

# Modelo de domínio — Fornecedores

## Entidades

### Fornecedor (agregado raiz)

- **Atributos imutáveis:** `cnpj`, `criado_em`
- **Atributos mutáveis:** `razao_social`, `nome_fantasia`, `categorias` (lista), `condicao_pagamento_padrao`, `dados_bancarios`
- **Atributos operacionais:** `status` (em_homologacao / ativo / inativo / bloqueado)
- **Invariantes:** `INV-TENANT-001`, CNPJ válido (algoritmo brasileiro).
- **Ciclo:** criado → em_homologacao → ativo → (inativo/bloqueado) → reativa.

### ContatoFornecedor

- `fornecedor_id`, `nome`, `papel` (vendedor/gerente/financeiro), `email`, `telefone`, `whatsapp`.
- LGPD: base legal "execução de contrato".

### DocumentoHomologacao

- `fornecedor_id`, `tipo` (contrato_social/comprovante_bancario/certidao_*), `url_arquivo`, `validade (nullable)`, `enviado_em`, `aprovado_por`, `aprovado_em`.

### Cotacao (agregado)

- `status` (rascunho / enviada / em_resposta / fechada / cancelada), `criado_por`, `criado_em`, `prazo_resposta`, `justificativa_escolha (nullable)`, `fornecedor_escolhido_id (nullable)`.
- Linhas filhas: `LinhaCotacao` com `item_id`, `quantidade`, `unidade_medida`, `observacao`.
- Convites: `ConviteCotacao` com `fornecedor_id`, `token_resposta`, `enviado_em`, `expira_em`.
- Respostas: `RespostaCotacao` por `(cotacao_id, fornecedor_id, item_id)` com `preco_unitario`, `prazo_entrega_dias`, `condicao_pagamento`, `observacao`, `respondido_em`.

### PedidoCompra

- `cotacao_id (nullable)`, `fornecedor_id`, `criado_em`, `status` (rascunho/enviado/recebido_parcial/recebido_total/cancelado), `valor_total`.
- Linhas: `item_id`, `quantidade`, `preco_unitario`, `total`.

### AvaliacaoFornecedor

- `pedido_id`, `fornecedor_id`, `avaliador_id`, `notas` (prazo, qualidade, preço — 0-10), `comentario`, `criado_em`.

### HistoricoPreco (projeção)

- Reconstruível: por `(fornecedor_id, item_id)`, lista de `(data, preco)` derivada de `RespostaCotacao` aceita + `PedidoCompra`.

---

## Token de resposta de cotação (regra)

- Cada `ConviteCotacao` gera token único, opaco (UUID v4 ou similar), válido por 7 dias.
- Endpoint público `GET /v1/cotacao-publica/{token}` retorna formulário; `POST` registra resposta.
- Tentativa após expiração → 410 Gone.
- Token NÃO concede acesso ao restante do sistema; escopo limitado àquela cotação.

---

## Agregados (DDD)

| Agregado raiz | Entidades | Invariantes |
|---|---|---|
| Fornecedor | Contato, Documento | CNPJ válido, `INV-TENANT-001` |
| Cotacao | Linha, Convite, Resposta | token único, expiração 7d |
| PedidoCompra | Linhas | requer cotação prévia se > teto config. |
| AvaliacaoFornecedor | — | 1 avaliação por pedido |

---

## Eventos publicados

| Evento | Quando | Consumidores |
|---|---|---|
| `Fornecedor.cadastrado` | INSERT | — |
| `Fornecedor.homologado` | status → ativo | Comercial (libera uso) |
| `Fornecedor.bloqueado` | status → bloqueado | Operação (alerta em cotação nova) |
| `Cotacao.enviada` | status → enviada | E-mail/WhatsApp gateway |
| `Cotacao.fechada` | escolha confirmada | PedidoCompra (cria rascunho) |
| `PedidoCompra.enviado` | status → enviado | Financeiro (contas a pagar futuro) |
| `PedidoCompra.recebido_total` | recebimento físico | Estoque (entrada), AvaliacaoFornecedor (gatilho) |
| `AvaliacaoFornecedor.registrada` | INSERT | Dashboards |

---

## Comandos

| Comando | Pré | Pós |
|---|---|---|
| `cadastrarFornecedor` | CNPJ válido + único | Fornecedor em_homologacao |
| `homologar` | docs completos | status ativo |
| `criarCotacao` | itens válidos | Cotacao rascunho |
| `enviarCotacao` | ≥ 1 fornecedor selecionado | Cotacao enviada + tokens |
| `registrarRespostaCotacao` | token válido | RespostaCotacao salva |
| `escolherFornecedor` | ≥ 1 resposta + justificativa se não-menor-preço | Cotacao fechada |
| `gerarPedidoCompra` | cotação fechada OU compra direta < teto | PedidoCompra |
| `avaliar` | pedido recebido_total | AvaliacaoFornecedor |

---

## Schema físico

Ver `../schema-banco.md` quando criado.

## Como evolui

- Atributo novo → migration.
- Regra de teto / cotação obrigatória → configuração por tenant + ADR.
