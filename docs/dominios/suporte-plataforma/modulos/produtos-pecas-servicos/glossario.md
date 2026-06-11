---
owner: Roldão
revisado-em: 2026-06-11
status: stable
modulo: produtos-pecas-servicos
dominio: suporte-plataforma
---

# Glossário — Catálogo de Produtos / Peças / Serviços

> Específico do módulo. Transversais em `docs/comum/glossario.md`.
> **Emendado no P9 da frente (2026-06-11, achado PROD-M1):** TabelaPreco foi
> PROMOVIDA de V2 pro núcleo Wave A (US-OS-015) e a ADR-0081 canonizou o par
> **preço de LISTA × preço de VENDA** — "lista de preço" deixou de ser sinônimo
> proibido e virou conceito de 1ª classe distinto da tabela.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Produto | Item físico revendido pelo tenant (ex: balança nova) | "mercadoria" só | Item de venda direta | Gap MVP-2 |
| Peça | Componente físico consumível em OS (ex: bateria, sensor) | "insumo" | Item de reposição usado em manutenção/calibração | BIG-12 |
| Serviço | Item não-físico cobrado em OS (ex: hora técnica, deslocamento) | "atividade" | Linha cobrável sem baixar estoque | Gap MVP-2 |
| Kit | Agrupamento de peças/serviços vendidos juntos com preço único (linha PRÓPRIA na tabela — soma das partes é só sugestão na criação) | "combo" | Composição pré-definida | MVP-2 + ADR-0081 |
| Item de catálogo | Termo guarda-chuva pra produto/peça/serviço/kit | "SKU" cru | Qualquer linha do catálogo | MVP-2 |
| **Preço de lista** | Preço de REFERÊNCIA histórico do item (`preco_padrao` da versão de catálogo) — imutável, NUNCA usado como fallback de venda | "preço sugerido" como se fosse venda | "sem versão de lista vigente" = item sem referência naquela data | **ADR-0081** |
| **Preço de venda** | Preço que a OS/orçamento COBRA — vem exclusivamente da linha vigente da tabela de preço (fail-closed: ausente = erro, nunca chuta) | "preço de tabela" ambíguo | 422 `PRECO_TABELA_AUSENTE` = cadastrar linha antes de vender | **ADR-0081** |
| Preço vigente | Preço (de lista OU de venda) válido em uma janela de datas | "preço atual" só | Preço aplicável conforme `data_referencia` (= data da CONTRATAÇÃO) | INV-026 |
| Versão de catálogo | Snapshot imutável do item com nome/UM/preço de lista em uma janela | "histórico de preço" | Linha histórica; corrigir = revogar+recriar | INV-026 / INV-PPS-VERSAO-IMUTAVEL |
| **Tabela de preço** | Conjunto nomeado de preços de VENDA (núcleo Wave A: 1 tabela PADRÃO por tenant; multi-tabela é V2) | "lista de preço" (é OUTRO conceito — ver preço de lista) | Política comercial que a OS consulta | **núcleo Wave A (promovida)** — ADR-0081/D-PPS-3 |
| **Linha de tabela** | Preço de venda imutável por (tabela, item) com vigência | "registro de preço" | Linha errada → corrigir (revoga+recria, auditado) | ADR-0081 / INV-PPS-LINHA-IMUTAVEL |
| **Origem do preço** | Como o VALOR da linha nasceu: `manual` (digitado/aceito) ou `soma_partes` (sugestão pela soma do kit) | — | Campo informativo em linha/contrato resolvido | ADV-PPS-08 |
| **Staging de importação** | Área temporária (90 dias) onde o CSV importado espera CONFERÊNCIA humana linha a linha — nada vira item sem aceite | "importação automática" | Linha `validada`/`rejeitada`/`aceita` | US-CAT-004 / INV-PPS-IMPORTACAO-STAGING |
| Unidade de medida (UM) | Unidade do item: un, kg, h, km, etc. | "medida" | Coluna nas telas de OS/estoque | MVP-2 |
| Estoque-controlado | Flag ESTRUTURAL do item indicando se baixa estoque ao ser usado | — | Serviço/kit nasce `false` por default | BIG-12 / TL-PPS-12 |
| Item ativo/inativo | Status do item no catálogo (não excluído) | "deletado" | Inativo some de venda NOVA; histórico preservado | INV-026 / AC-CAT-005-1 |

---

## Como evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Termo descontinuado → `@deprecated` + janela 3 meses.
