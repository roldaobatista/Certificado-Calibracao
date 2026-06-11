---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: produtos-pecas-servicos
dominio: suporte-plataforma
---

# Modelo de domínio — Catálogo (Produtos / Peças / Serviços / Kits)

## Entidades

### ItemCatalogo (agregado raiz)

- **Atributos imutáveis:** `codigo_interno`, `tipo` (produto/peca/servico/kit), `criado_em`
- **Atributos estruturais (mutáveis com auditoria):** `controla_estoque` *(movido da versão
  em 2026-06-11 — P2 frente, TL-PPS-12: é propriedade estrutural do item, não atributo
  temporal de preço/apresentação)*, `status` (ativo/inativo)
- **Atributos versionáveis (via ItemCatalogoVersao):** `nome`, `descricao`, `categoria`, `unidade_medida`, `preco_padrao`
- **Invariantes:** `INV-026` (preço não-retroativo), `INV-PPS-CODIGO-UNICO`, `INV-TENANT-001`
- **Ciclo de vida:** criada → ativa → inativa (terminal lógico; nunca deletada).

### ItemCatalogoVersao (entidade filha)

- **Atributos:** `item_id`, `versao_n`, `snapshot (JSONB)`, `vigente_de`, `vigente_ate (nullable)`, `criado_por`, `motivo`
- **Imutável após criada.** Consultas com `data_referencia` retornam a versão vigente naquela data.

### KitComposicao

- **Atributos:** `kit_item_id`, `item_filho_id`, `quantidade` *(UM **derivada da versão
  vigente do filho** — campo próprio removido em 2026-06-11, P2 TL-PPS-11: duplicar
  divergia kit "un" × filho "kg")*
- **Restrições:** kit não pode conter kit (anti-ciclo estrutural, 1 nível). Item filho deve ser produto/peça/serviço.

### TabelaPreco (PROMOVIDA pra Wave A — 2026-06-11, frente #2 do plano de dependência)

> Era "V2 / Wave futura"; **US-OS-015 (OS avulsa, Wave A) exige consulta de preço vigente
> fail-closed (422 `PrecoTabelaAusente`)** → entra no núcleo da frente. **ADR-0081** (duas
> fontes com papéis distintos: `preco_padrao` = LISTA histórica; `LinhaTabelaPreco` = VENDA
> vigente; sem fallback runtime). Spec: `docs/faseamento/produtos-pecas-servicos/spec.md`.

- **`TabelaPreco`:** `nome`, `descricao`, `eh_padrao` (ÚNICA por tenant no MVP — UNIQUE
  parcial; schema já suporta N tabelas pra V2 sem migration de quebra).
- **`LinhaTabelaPreco`:** `(tabela_id, item_id, preco > 0, JanelaVigencia)` — **imutável**
  pós-INSERT (molde `Imposto`: trigger Padrão B + revogação one-shot + block DELETE +
  exclusion de não-sobreposição por `(tenant, tabela, item)`); correção = use case composto
  revoga+recria atômico. Kit exige **linha própria** (soma das partes é default sugerido na
  criação, nunca resolução em runtime).
- **Porta `preco_para_os(tenant, item, data_referencia)`** → `PrecoResolvido (item_id,
  item_versao_n, linha_tabela_id, tabela_id, preco, data_referencia, origem_preco,
  composicao_resolvida?)` | `PrecoTabelaAusente`. `data_referencia` = data do fato gerador
  COMERCIAL (contratação), não do faturamento.

---

## INV-026 — Preço não-retroativo (detalhe)

**Regra:** alteração de `preco_padrao` ou de qualquer atributo versionável **cria nova versão** com `vigente_de = data_da_mudanca` (ou data futura). Nunca altera versão existente.

1. **Consulta de preço sempre exige `data_referencia`** (default = hoje). A camada de aplicação seleciona a versão tal que `vigente_de ≤ data_referencia` e (`vigente_ate IS NULL OR vigente_ate > data_referencia`).
2. **OS aberta** captura `data_referencia` da abertura. Lançamento de item na OS resolve preço com aquela data.
3. **Auditoria:** OS fechada referencia explicitamente `(item_id, versao_n)` usado — preço da OS é "carimbado".
4. **Bloqueio:** UPDATE direto em `ItemCatalogoVersao` retorna 422.

---

## Agregados

| Agregado raiz | Entidades incluídas | Invariantes |
|---|---|---|
| ItemCatalogo | ItemCatalogoVersao, KitComposicao | `INV-026`/`INV-PPS-VERSAO-IMUTAVEL`, `INV-PPS-CODIGO-UNICO`, `INV-PPS-PRECO-NAO-RETROATIVO`, `INV-PPS-KIT-SEM-CICLO`, `INV-TENANT-001` |
| TabelaPreco (Wave A — ADR-0081) | LinhaTabelaPreco | `INV-PPS-LINHA-IMUTAVEL`, `INV-PPS-LINHA-SEM-SOBREPOSICAO`, `INV-TENANT-001` |

---

## Eventos publicados

> **Nomenclatura canônica:** PascalCase no segundo segmento (ex: `Catalogo.ItemCadastrado`). Aliases snake_case ficam como **deprecated** até V2.
>
> **Núcleo Wave A (P2 2026-06-11):** eventos vão SÓ na cadeia hash (`outbox=False`, molde
> `Config.*`) — promoção a outbox com `_schema_version: v1` quando estoque/orçamentos
> chegarem (**GATE-PPS-OUTBOX-ESTOQUE**, TL-PPS-05). **LGPD (ADV-PPS-01/02):** payload leva
> `criado_por_id_hash` (nunca UUID/nome em claro) e `descricao`/`motivo` como hash
> canonicalizado ADR-0029; `nome` do item em claro passa pelo sanitizador padrão.

| Evento | Quando dispara | Payload | Consumidores |
|---|---|---|---|
| `Catalogo.ItemCadastrado` | INSERT | `{tenant_id, item_id, codigo, tipo}` | Estoque (inicializa saldo), Financeiro |
| `Catalogo.ItemAtualizado` | UPDATE de descrição, especificação, status, kit ou criação de nova `ItemCatalogoVersao` (qualquer mudança que afete preço/disponibilidade — evento agregador) | `{tenant_id, item_id, versao_id, campos_alterados[]}` | comercial/marketplace (atualiza vitrine), comercial/precificacao (revisa regras), Operação |
| `Catalogo.PrecoAlterado` | Nova `ItemCatalogoVersao` com preço diferente | `{tenant_id, item_id, versao_id, preco_antigo, preco_novo}` | Financeiro (recalcula orçamentos abertos), comercial/marketplace |
| `Catalogo.ItemInativado` | status=inativo | `{tenant_id, item_id, motivo}` | Operação (esconde de seletor de OS), comercial/marketplace (remove vitrine) |
| `Catalogo.KitAlterado` | Composição mudou | `{tenant_id, kit_id, diff_componentes}` | Operação |

---

## Comandos

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| `cadastrarItem` | UI/API | código único | Item + versão 1 criados |
| `atualizarItem` | UI/API | item existe | Nova `ItemCatalogoVersao` |
| `inativarItem` | UI/API | item existe | status=inativo |
| `montarKit` | UI/API | itens filhos existem, sem ciclo | Kit + composição |
| `importarPlanilha` | UI | arquivo válido | Linha-a-linha com aceite |

---

## Schema físico

Ver `../schema-banco.md` quando criado.

## Como evolui

- Atributo novo → migration + decidir imutável vs versionável.
- Mudança em INV-026 → ADR.
