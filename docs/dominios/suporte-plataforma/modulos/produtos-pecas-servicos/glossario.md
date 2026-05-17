---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: produtos-pecas-servicos
dominio: suporte-plataforma
---

# Glossário — Catálogo de Produtos / Peças / Serviços

> Específico do módulo. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Produto | Item físico revendido pelo tenant (ex: balança nova) | "mercadoria" só | Item de venda direta | Gap MVP-2 |
| Peça | Componente físico consumível em OS (ex: bateria, sensor) | "insumo" | Item de reposição usado em manutenção/calibração | BIG-12 |
| Serviço | Item não-físico cobrado em OS (ex: hora técnica, deslocamento) | "atividade" | Linha cobrável sem baixar estoque | Gap MVP-2 |
| Kit | Agrupamento de peças/serviços vendidos juntos com preço único | "combo" | Composição pré-definida | MVP-2 |
| Item de catálogo | Termo guarda-chuva pra produto/peça/serviço/kit | "SKU" cru | Qualquer linha do catálogo | MVP-2 |
| Preço vigente | Preço válido em uma janela de datas | "preço atual" só | Preço aplicável conforme `data_referencia` | INV-026 |
| Versão de catálogo | Snapshot do item com preço/composição em uma data específica | "histórico de preço" | Linha histórica de preço | INV-026 |
| Tabela de preço | Conjunto nomeado de preços (ex: tabela "atacado", "varejo") | "lista de preço" | Política comercial | [INFERÊNCIA] V2 |
| Unidade de medida (UM) | Unidade do item: un, kg, h, km, etc. | "medida" | Coluna nas telas de OS/estoque | MVP-2 |
| Estoque-controlado | Flag indicando se o item baixa estoque ao ser usado | — | Serviço/kit puro pode ser `false` | BIG-12 |
| Item ativo/inativo | Status do item no catálogo (não excluído) | "deletado" | Item descontinuado preserva histórico | INV-026 |

---

## Como evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Termo descontinuado → `@deprecated` + janela 3 meses.
