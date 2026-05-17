---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: caixa-tecnico
dominio: financeiro
---

# Modelo de Domínio — Caixa do Técnico

## Agregados

### `CaixaTecnico` (raiz por técnico)

Atributos:
- `id`, `tenant_id`, `tecnico_id`
- `saldo_atual` (calculado: soma adiantamentos − soma despesas validadas)
- `politica_id` (referência à política vigente do tenant)
- `prestacao_em_aberto_id` (nullable)

### `Adiantamento` (raiz separada — vinculado a CaixaTecnico)

Atributos:
- `id`, `caixa_id`, `tenant_id`
- `valor`, `solicitado_em`, `aprovado_em`, `entregue_em`
- `status`: `solicitado` | `aprovado` | `entregue` | `rejeitado` | `cancelado`
- `aprovado_por`, `motivo_rejeicao` (nullable)
- `meio_entrega`: `pix` | `transferencia` | `dinheiro`
- `os_referencia` (nullable — adiantamento pode ser pra OS específica)

### `Despesa` (raiz separada — pode ou não vincular a OS)

Atributos:
- `id`, `caixa_id`, `tenant_id`, `tecnico_id`
- `valor`, `data`, `categoria` (combustível/alimentação/pedágio/hospedagem/peça/deslocamento)
- `os_id` (nullable; recomendado)
- `foto_comprovante_url` (**obrigatória** — INV)
- `foto_hash` (anti-duplicata)
- `gps_lat`, `gps_lng` (opcional — consentimento LGPD)
- `descricao_livre`
- `status`: `pendente` | `validada` | `rejeitada`
- `validada_por`, `validada_em`, `motivo_rejeicao` (nullable)
- `km_percorridos` (só pra deslocamento; sistema calcula valor automático conforme política)

### `Politica` (entidade por tenant)

Atributos:
- `limite_por_categoria` (map categoria → R$)
- `alcada_aprovacao` (map valor → papel)
- `tarifa_km` (R$/km)
- `exige_gps`: bool (default false — consentimento)
- `prazo_prestacao_dias` (default 30)

### `PrestacaoContas` (entidade evento)

Quando técnico fecha o mês.

Atributos:
- `id`, `caixa_id`, `periodo_de`, `periodo_ate`
- `total_adiantado`, `total_despesas_validadas`, `saldo_final`
- `direcao`: `tecnico-deve` | `tenant-deve` | `quitado`
- `fechada_em`, `fechada_por`
- Imutável — correções viram novas despesas/lançamentos no próximo período.

## Regras de negócio

- **INV: despesa sem foto-comprovante = rejeitada em criação.** Bloqueio total. Equivalente conceitual ao INV-007 fiscal.
- **Despesa validada é imutável.** Correção = nova despesa de ajuste com referência à original.
- **Adiantamento entregue não pode ser cancelado.** Pode virar despesa "devolução de adiantamento".
- **GPS opcional + consentimento explícito.** Tenant pode forçar via política, mas precisa avisar técnico (LGPD).
- **Hash de foto:** mesma foto em 2 despesas = bloqueio (anti-fraude simples).
- **Vínculo OS:** alimenta custeio Wave B; opcional MVP-1, recomendado.

## Eventos emitidos

- `AdiantamentoSolicitado(caixa_id, valor)`
- `AdiantamentoAprovado(adiantamento_id, valor, meio)`
- `DespesaLancada(despesa_id, caixa_id, valor, os_id?)`
- `DespesaValidada(despesa_id)` → consumido por custeio OS (Wave B)
- `DespesaRejeitada(despesa_id, motivo)`
- `PrestacaoFechada(prestacao_id, saldo, direcao)`

## Eventos consumidos

- `OSCriada` / `OSConcluida` (Operação) — disponibiliza OS pra vínculo
- (V2) Webhook Pluggy: cartão corporativo lança despesa automática

## Non-goals do modelo

- Múltiplas moedas (técnico viajando internacional)
- OCR de recibo (V2)
- Integração cartão corporativo (V2 Pluggy)
- Adiantamento via folha de pagamento

## Offline-first

App mobile mantém fila local. Conflitos resolvidos no servidor (server-wins por timestamp); técnico vê notificação se algo foi rejeitado durante sync.

## Invariantes

- INV-008 (audit), INV "foto obrigatória" (análogo INV-007), despesa validada imutável, anti-duplicata por hash.

## Referências

- OP3.2, BIG-08
- `docs/comum/integracoes-inter-modulos.md`
- `REGRAS-INEGOCIAVEIS.md`
