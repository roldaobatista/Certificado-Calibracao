---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: comissoes
dominio: financeiro
---

# Modelo de Domínio — Comissões

> **Decisão fundadora MVP-1:** apenas **1 fórmula** ativa — `% sobre valor bruto da OS, gatilho por recebimento`. Modelo permite extensibilidade pra Wave B, mas implementação inicia simples.

## Agregados

### `RegraComissao` (raiz)

Atributos:
- `id`, `tenant_id`, `beneficiario_id` (vendedor ou técnico)
- `tipo_formula`: `pct-bruto-recebimento` (único no MVP-1; enum extensível Wave B)
- `percentual` (decimal, ex: 0.05 = 5%)
- `vigente_de`, `vigente_ate` (nullable)
- `ativa`: bool

**Regra crítica (INV análogo INV-026):** alterar a regra **não recalcula** comissões já calculadas. Cria nova versão com `vigente_de` novo; comissões anteriores mantêm fórmula original.

### `Comissao` (raiz separada — uma por OS + beneficiário)

Atributos:
- `id`, `tenant_id`, `os_id`, `beneficiario_id`, `regra_id` (snapshot da regra usada)
- `base_calculo` (valor bruto OS no momento da concluão — snapshot)
- `percentual_aplicado` (snapshot do %)
- `valor` (calculado: base × pct)
- `status`: `prevista` | `devida` | `paga` | `estornada`
- `os_concluida_em`, `titulo_pago_em` (nullable), `paga_em` (nullable)
- `titulo_id` (referência ao título de origem)

### `PagamentoComissao` (entidade evento)

Quando financeiro paga lote de comissões devidas. Imutável.

Atributos: `id`, `beneficiario_id`, `valor_total`, `comissoes_ids[]`, `data`, `meio` (transferência/folha/dinheiro).

### `Estorno` (entidade evento)

Imutável. Quando título é cancelado pós-comissão `paga`. Cria contra-lançamento.

## Regras de negócio

- **Snapshot da regra:** Comissão guarda `base_calculo` + `percentual_aplicado` no momento. Mudança futura em RegraComissao não afeta esta Comissao.
- **Transição de status:** `prevista` → `devida` (evento `Pago`); `devida` → `paga` (PagamentoComissao); `paga` → `estornada` (cancelamento de título).
- **Idempotência:** mesmo `Pago` chegando 2× não duplica transição de status.
- **OS sem beneficiário atribuído:** não gera Comissao. Auditor de negócio alerta se > 5% das OSs ficam órfãs.

## Eventos consumidos

- `OSConcluida(os_id, valor_bruto, beneficiario_id)` → cria Comissao `prevista`
- `Pago(titulo_id)` → transita Comissao(os relacionada) pra `devida`
- `TituloCancelado(titulo_id)` → estorno se Comissao já estava paga

## Eventos emitidos

- `ComissaoPrevista(comissao_id, beneficiario_id, valor)`
- `ComissaoDevida(comissao_id, beneficiario_id, valor)`
- `ComissaoPaga(comissao_id, pagamento_id)`
- `ComissaoEstornada(comissao_id, razao)`

## Non-goals do modelo (MVP-1)

- Múltiplos beneficiários por OS (rateio) — Wave B
- Fórmula sobre margem (precisa custeio confiável) — MVP-2
- Fórmula escalonada / meta — Wave B
- Comissão de retenção contratual — Wave B
- Aprovação obrigatória pré-paga — V2

## Roadmap fórmulas futuras (Wave B/MVP-2)

Modelo extensível via `tipo_formula` enum + tabela `regra_comissao_parametros` (chave-valor) pra acomodar parâmetros adicionais sem rebuild. Discovery dedicado antes de cada nova fórmula.

## Invariantes

- INV-008 (audit), regra não-retroativa (análogo INV-026), estorno sempre explícito.

## Referências

- OP4
- `docs/comum/integracoes-inter-modulos.md`
- BIG-09
