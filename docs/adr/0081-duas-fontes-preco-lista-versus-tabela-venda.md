---
owner: agente-ia
revisado-em: 2026-06-11
status: proposta
adr: 0081
relacionados: [0030, 0031, 0080]
---

# ADR-0081 — Duas fontes de preço com papéis distintos (lista histórica × tabela de venda vigente)

**Status:** proposta (criada na P2 da frente `produtos-pecas-servicos` — TL-PPS-02;
promover a aceito no P8)

## Contexto

O catálogo (`produtos-pecas-servicos`) versiona `preco_padrao` por item
(`ItemCatalogoVersao`, INV-026 preço não-retroativo). A OS avulsa (US-OS-015) exige
consulta de preço vigente fail-closed — 422 `PrecoTabelaAusente`. As frentes
`precificacao` (#3) e `orcamentos` (#5) consumirão a mesma semântica. Hoje o preço da
OS avulsa é fornecido pelo caller da API (`ordens_servico/views.py:507` — estado
declarado; GATE-PPS-WIREIN-OS bloqueante pré-1º tenant externo).

Alternativa rejeitada: `LinhaTabelaPreco` referenciar a versão do item — acoplaria o
preço de VENDA ao ciclo de versão do CATÁLOGO (mudar nome/UM criaria versão e forçaria
re-apontamento ou mudaria preço implicitamente).

## Decisão

1. **`ItemCatalogoVersao.preco_padrao` = preço de LISTA** — histórico imutável
   (INV-026/INV-PPS-VERSAO-IMUTAVEL, molde `Imposto` da frente #1: trigger Padrão B +
   revogação one-shot + block DELETE + exclusion de não-sobreposição).
2. **`LinhaTabelaPreco` = preço de VENDA vigente** — o que `preco_para_os` resolve;
   igualmente imutável (linha errada → revogar+recriar via use case composto atômico).
3. **Sem fallback runtime tabela→lista.** Sem linha vigente → `PrecoTabelaAusente`
   (422 no caller). `preco_padrao` é apenas default SUGERIDO ao criar a linha.
4. **Contrato `PrecoResolvido` carrega referências probatórias**, não só valor:
   `(item_id, item_versao_n, linha_tabela_id, tabela_id, preco, data_referencia,
   origem_preco: manual|soma_partes, composicao_resolvida? [kit])`. Caller persiste as
   refs junto do snapshot (INV-026 ponto 3). `data_referencia` = data do fato gerador
   COMERCIAL (contratação/lançamento), não do faturamento (CDC art. 39 X).
5. **Kit exige linha própria na tabela** (sem soma runtime — evita 422 em cascata e
   N+1); soma das partes é default sugerido na criação da linha.
6. **TabelaPreco única por tenant no MVP** (`eh_padrao` UNIQUE parcial); schema já
   suporta N tabelas — multi-canal/cliente entra na frente `precificacao`/V2 sem
   migration de quebra.

## Consequências

- `precificacao` (#3) estende com N tabelas/segmentos SEM tocar o contrato da porta.
- `orcamentos` (#5) consome `preco_para_os` e persiste as refs — INV-026 fecha-se no
  consumidor (snapshot carimbado), como na ADR da frente #1.
- Defesa em disputa de preço (CDC art. 30/31/46): reconstrução completa "valor + fonte
  (linha N, tabela T, versão M) + data da contratação" por replay de vigências imutáveis.
- Dupla manutenção lista×venda é mitigada pelo default sugerido; o fail-closed impede o
  pior caso (venda por preço silenciosamente errado).

## Bloqueia

Frente `produtos-pecas-servicos` Fatia 2 (use cases/porta) em diante; consumida por
frentes #3/#5 e pelo GATE-PPS-WIREIN-OS.
