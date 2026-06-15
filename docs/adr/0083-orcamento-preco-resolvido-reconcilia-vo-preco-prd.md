---
owner: agente-ia
revisado-em: 2026-06-15
status: aceito
adr: 0083
relacionados: [0030, 0031, 0078, 0081, 0082]
---

# ADR-0083 — Snapshot de preço do orçamento é `PrecoResolvido`, reconciliando o VO `Preco` do PRD

**Status:** aceito (2026-06-15 — P8 da frente `orcamentos`; decisão cravada como D-ORC-1 na investigação T-ORC-000 §2 e implementada nas Fatias 1a..2. Esta ADR formaliza a reconciliação e emenda o PRD/modelo.)

## Contexto

O PRD do módulo `orcamentos` (`docs/dominios/comercial/modulos/orcamentos/prd.md`,
saneamento Onda 3 Batch B4, 2026-05-27) declarou um **VO novo** como snapshot canônico
de preço no item do orçamento:

```
Preco(valor_centavos: int, moeda: str, vigencia_inicio, vigencia_fim, fonte_tabela_id: UUID)
```

com a intenção de substituir o "snapshot vago" do INV-026 e cravar a não-retroatividade
(INV-ORC-PRECO-001). À época, a frente de preço (`produtos-pecas-servicos` #1,
`precificacao` #3) ainda não tinha fechado. Quando fechou, a investigação T-ORC-000
(§2) constatou que **já existe** um contrato de snapshot de preço probatório, mais rico
que o `Preco` proposto, reusado por toda a cadeia comercial:

```
PrecoResolvido(item_id, item_versao_n, linha_tabela_id, tabela_id, preco,
               data_referencia, origem_preco)          # src/domain/produtos_pecas_servicos/entities.py
```

resolvido por `preco_para_os(...)` (pps, fail-closed) e devolvido por `calcular_precos`
(precificacao) dentro de `ItemCalculado`. O `PrecoResolvido` carrega as **referências
probatórias** que o `Preco` não tinha (qual versão do item, qual linha de qual tabela,
data do fato gerador comercial, origem do preço) — exatamente o que a auditoria de preço
exige (ADR-0081 ponto 4) e o que torna a não-retroatividade auditável, não só afirmada.

Manter **dois** VOs de snapshot de preço (o `Preco` do PRD no orçamento + o
`PrecoResolvido` da cadeia) significaria: (a) tradução lossy na fronteira (o `Preco`
descartaria `item_versao_n`/`linha_tabela_id`/`origem_preco`); (b) dois pontos a manter
sincronizados sob INV-026; (c) divergência entre o que o orçamento carimba e o que a OS
(ADR-0082) e o certificado consomem.

## Decisão

1. **O item do orçamento (`ItemOrcamento`) carimba `PrecoResolvido`, NÃO um VO `Preco`
   novo.** Campo `preco_resolvido: PrecoResolvido` (reuso de `produtos-pecas-servicos`),
   preenchido por `calcular_precos`/`preco_para_os` na criação do item. O VO `Preco`
   `(valor_centavos, moeda, vigencia_inicio, vigencia_fim, fonte_tabela_id)` proposto no
   PRD **não é criado** — fica reconciliado/deprecado por esta ADR.

2. **Cada campo do `Preco` proposto tem destino canônico explícito:**
   - `valor_centavos`/`moeda` → VO `Dinheiro` (centavos + moeda; usado em `preco_final`,
     `desconto_valor`, `total`, e dentro de `PrecoResolvido.preco` via `Preco` do pps).
   - `fonte_tabela_id` → `PrecoResolvido.tabela_id` (+ `linha_tabela_id`, mais preciso).
   - `vigencia_inicio`/`vigencia_fim` → **não pertencem ao item**: a vigência comercial
     do orçamento é a `JanelaVigencia` do agregado `Orcamento.validade` (ADR-0030); a
     data probatória do preço é `PrecoResolvido.data_referencia` (fato gerador comercial,
     CDC art. 39 X). Não há vigência por-item separada.

3. **A não-retroatividade (INV-ORC-PRECO-001 / INV-026) é realizada pela imutabilidade
   do `ItemOrcamento`** (dataclass frozen) + pela imutabilidade do `PrecoResolvido`
   carimbado + pelo congelamento da `VersaoOrcamento` (Padrão B, trigger WORM — D-ORC-8).
   Mudança posterior na tabela/catálogo não toca item já gravado.

4. **VOs `Dinheiro`, `Desconto`, `CondicoesPagamento` do modelo permanecem** — não são
   afetados por esta reconciliação.

5. **Emenda PRD/modelo:** as referências ao VO `Preco` no PRD e no modelo-de-domínio
   passam a apontar para `PrecoResolvido` + `Dinheiro`, com nota de reconciliação citando
   esta ADR. O texto do PRD vira ponteiro histórico, não fonte divergente (D2 spec-as-source).

## Consequências

**Positivas:**
- Um único contrato de snapshot de preço em toda a cadeia comercial (pps → precificacao
  → orçamentos → OS ADR-0082 → certificado), sem tradução lossy na fronteira.
- Não-retroatividade auditável (referências probatórias completas), não só afirmada.
- Menos superfície a manter sob INV-026 (um VO, não dois).

**Negativas / limites:**
- O PRD original fica divergente do código até a emenda ser aplicada (feita junto desta
  ADR — T-ORC-060). Mitigado pela nota de reconciliação + ponteiro para esta ADR.
- `PrecoResolvido` é mais rico que o estritamente necessário para exibir um item ao
  cliente; o serializer público expõe só a allowlist (INV-ORC-MARGEM-OFF) — o excedente
  probatório nunca vaza.

## Non-goals

- **Não** redefine `PrecoResolvido` (é contrato de `produtos-pecas-servicos`, ADR-0081).
- **Não** altera a semântica de preço de venda × lista (ADR-0081) nem a numeração
  (ADR-0080) nem o envelope de OS (ADR-0082).
- **Não** introduz vigência de preço por-item (vigência é do agregado `Orcamento`).
