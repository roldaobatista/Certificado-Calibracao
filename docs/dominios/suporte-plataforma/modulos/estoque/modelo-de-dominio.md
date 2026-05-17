---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: estoque
dominio: suporte-plataforma
---

# Modelo de domínio — Estoque multi-local

## Entidades

### LocalEstoque

- **Atributos:** `nome`, `tipo` (central/veiculo/tecnico/cliente/outros), `responsavel_usuario_id (nullable)`, `ativo`
- **Invariantes:** `INV-TENANT-001`.

### Saldo (projeção)

- **Atributos:** `item_id`, `local_id`, `lote (nullable)`, `numero_serie (nullable)`, `validade (nullable)`, `quantidade`, `quantidade_reservada`, `quantidade_em_transito`
- **Reconstruível** a partir de `Movimento` (event sourcing leve).

### Movimento (append-only)

- **Atributos:** `id`, `item_id`, `tipo` (entrada/saida/transferencia_emissao/transferencia_aceite/transferencia_recusa/ajuste_inventario/reserva/liberacao_reserva/consumo), `local_origem_id (nullable)`, `local_destino_id (nullable)`, `quantidade`, `lote (nullable)`, `numero_serie (nullable)`, `validade (nullable)`, `os_id (nullable)`, `nfe_id (nullable)`, `motivo`, `usuario_id`, `timestamp`, `transferencia_pai_id (nullable)`, `foto_url (nullable)`
- **Imutável.** Nunca UPDATE/DELETE.

### Transferencia (agregado)

- **Atributos:** `id`, `status` (emitida/em_transito/aceita/recusada/cancelada), `emitido_por`, `emitido_em`, `aceite_por (nullable)`, `aceite_em (nullable)`, `foto_url (nullable)`, `recusa_motivo (nullable)`
- **Estado deriva de movimentos filhos.**

### InventarioSnapshot

- `local_id`, `iniciado_em`, `finalizado_em`, `status`, `responsavel_id`. Linhas: `(item, lote, contagem_fisica, saldo_sistema, diferenca)`.

### EstoqueMinimo

- `item_id`, `local_id`, `quantidade_minima`, `quantidade_critica`. Dispara alerta quando saldo cai.

---

## Transferência 2-etapas (detalhe — BIG-12 JTBD-104)

**Etapa 1 (emissão):**
1. Almoxarife cria `Transferencia` (origem, destino, item, qtd, lote/NS).
2. Sistema cria `Movimento(tipo=transferencia_emissao)`: saldo origem cai, `em_transito` sobe.
3. `Transferencia.status = em_transito`.

**Etapa 2 (aceite) — INVARIANTE FOTO:**
1. Técnico do destino abre transferência no app.
2. **Captura foto obrigatória** do lacre/peça recebida.
3. Sistema valida: `foto_url IS NOT NULL` → senão erro 422 PT "foto do lacre obrigatória" (BIG-12).
4. Sistema cria `Movimento(tipo=transferencia_aceite)`: `em_transito` cai, saldo destino sobe.
5. `Transferencia.status = aceita`; `foto_url` salva.

**Recusa:**
1. Técnico marca "recusar" + motivo obrigatório (texto livre + categoria).
2. Sistema cria `Movimento(tipo=transferencia_recusa)`: `em_transito` cai, saldo origem sobe.
3. `Transferencia.status = recusada`.

**Cancelamento (antes do aceite):** só pelo emitente. Reverte para origem.

---

## Lote / Validade / NS (detalhe)

- **Lote:** identificador do fabricante; um item pode ter múltiplos lotes em estoque.
- **Validade:** consulta de consumo filtra por `validade > hoje`. Tentativa de consumir lote vencido → 422 PT "lote L123 venceu em DD/MM/AAAA".
- **NS:** quando item tem `controla_serie=true` (ex: padrão metrológico), cada unidade tem NS único; movimento sempre referencia NS.

---

## Agregados

| Agregado raiz | Entidades incluídas | Invariantes |
|---|---|---|
| LocalEstoque | Saldo (projeção) | `INV-TENANT-001` |
| Transferencia | Movimento (emissão, aceite, recusa) | `INV-TENANT-001`, foto obrigatória no aceite (BIG-12) |
| InventarioSnapshot | linhas de conferência | `INV-TENANT-001` |

---

## Eventos publicados

> **Nomenclatura canônica:** PascalCase no segundo segmento (ex: `Estoque.MovimentacaoRegistrada`). Aliases `Estoque.movimento_registrado` (snake) ficam como **deprecated** até remoção em V2.

| Evento | Quando | Payload | Consumidores |
|---|---|---|---|
| `Estoque.MovimentacaoRegistrada` | Após INSERT Movimento (qualquer tipo: entrada/saída/transferência/ajuste) | `{tenant_id, movimento_id, item_id, tipo, qtd, deposito_id, custo_unit, os_id?}` | Financeiro (CMP), Operação (saldo OS), BI (dashboards) |
| `Estoque.SaidaPeca` | Subtipo de movimentação (tipo=saida) — emitido em paralelo pra consumers que só querem saídas | `{tenant_id, movimento_id, item_id, qtd, os_id?, motivo}` | financeiro/custeio-real (linha de custo `pecas`), Operação |
| `Estoque.EntradaPeca` | Subtipo (tipo=entrada) | `{tenant_id, movimento_id, item_id, qtd, custo_unit, nota_compra_id?}` | financeiro/contas-pagar (vínculo), BI |
| `Estoque.TransferenciaEmitida` | etapa 1 | `{tenant_id, transferencia_id, deposito_origem, deposito_destino, itens[]}` | Operação (notifica destinatário) |
| `Estoque.TransferenciaAceita` | etapa 2 aceite | `{tenant_id, transferencia_id, aceita_em, foto_url}` | Operação |
| `Estoque.TransferenciaRecusada` | etapa 2 recusa | `{tenant_id, transferencia_id, motivo}` | Operação, Almoxarife (notif) |
| `Estoque.MinimoAtingido` | saldo ≤ mínimo | `{tenant_id, item_id, saldo, minimo}` | Operação, suporte-plataforma/fornecedores (sugere cotação) |
| `Estoque.LoteVencendo` | validade ≤ 30d | `{tenant_id, item_id, lote, validade}` | Almoxarife (notif) |
| `Estoque.InventarioFinalizado` | snapshot fechado | `{tenant_id, snapshot_id, ajustes_qtd, divergencia_total}` | Financeiro |
| `Estoque.ItemEsgotado` | saldo = 0 | `{tenant_id, item_id}` | comercial/marketplace (marca ItemVitrine indisponível) |

---

## Comandos

| Comando | Pré-condição | Pós-condição |
|---|---|---|
| `darEntrada` | item ativo | Movimento entrada |
| `emitirTransferencia` | saldo origem ≥ qtd | Movimento emissão + Transferencia em_transito |
| `aceitarTransferencia` | foto anexada | Movimento aceite + Transferencia aceita |
| `recusarTransferencia` | motivo informado | Movimento recusa |
| `consumirParaOS` | reserva válida OU saldo livre | Movimento saída/consumo |
| `ajusteInventario` | snapshot ativo | Movimento ajuste com motivo |

---

## Schema físico

Ver `../schema-banco.md` quando criado.

## Como evolui

- Tipo novo de movimento → migration + ADR.
- Mudança na regra foto obrigatória → ADR (regra BIG-12).
