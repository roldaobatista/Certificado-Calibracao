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
- **Atributos versionáveis (via ItemCatalogoVersao):** `nome`, `descricao`, `categoria`, `unidade_medida`, `controla_estoque`, `preco_padrao`
- **Atributos operacionais:** `status` (ativo/inativo)
- **Invariantes:** `INV-026` (preço não-retroativo), `INV-TENANT-001`
- **Ciclo de vida:** criada → ativa → inativa (terminal lógico; nunca deletada).

### ItemCatalogoVersao (entidade filha)

- **Atributos:** `item_id`, `versao_n`, `snapshot (JSONB)`, `vigente_de`, `vigente_ate (nullable)`, `criado_por`, `motivo`
- **Imutável após criada.** Consultas com `data_referencia` retornam a versão vigente naquela data.

### KitComposicao

- **Atributos:** `kit_item_id`, `item_filho_id`, `quantidade`, `unidade_medida`
- **Restrições:** kit não pode conter kit (anti-ciclo). Item filho deve ser produto/peça/serviço.

### TabelaPreco (V2 / Wave futura)

- `nome`, `descricao`. Linhas: `(tabela_id, item_id, preco, vigente_de)`.

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
| ItemCatalogo | ItemCatalogoVersao, KitComposicao | `INV-026`, `INV-TENANT-001` |
| TabelaPreco (V2) | linhas de preço | `INV-026` |

---

## Eventos publicados

> **Nomenclatura canônica:** PascalCase no segundo segmento (ex: `Catalogo.ItemCadastrado`). Aliases snake_case ficam como **deprecated** até V2.

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
