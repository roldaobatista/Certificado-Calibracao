---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
---

# Glossário do módulo Marketplace

> Termos específicos deste módulo. Termos transversais ficam em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| vitrine | Página pública/privada que lista produtos e serviços do tenant | "loja", "shop", "storefront" | tela do catálogo online vista pelo visitante/cliente | módulo Marketplace |
| carrinho de solicitação | Coleção temporária de itens que o visitante quer cotar (NÃO é checkout) | "cart" sem qualificar, "pedido" | lista de itens selecionados que vai virar solicitação de orçamento | US-MKT-002 |
| solicitação de orçamento | Pedido enviado pelo visitante via marketplace que gera lead + rascunho de orçamento | "pedido", "encomenda", "venda" | registro inicial pré-orçamento criado pelo marketplace | US-MKT-002 |
| área do cliente | Espaço autenticado onde cliente vê histórico, orçamentos, contratos, faturas | "portal do cliente", "customer panel" | tela logada com abas de relacionamento | US-MKT-003 |
| tabela pública | Tabela de preço visível a qualquer visitante anônimo | "preço de balcão", "preço cheio" | preços mostrados sem login | US-MKT-004 |
| tabela privada | Tabela de preço visível só a cliente logado com atribuição específica | "preço VIP", "preço negociado" | preços diferenciados por cliente | US-MKT-004 |
| destaque | Marcação que coloca item em posição prioritária na vitrine | "featured", "promoção" sem qualificar | item curado pelo gestor para aparecer primeiro | US-MKT-005 |
| serviço recorrente | Serviço que gera contrato + OS periódica (ex: calibração anual) | "assinatura", "plano" sem qualificar | item cuja contratação inicia ciclo automático | US-MKT-006 |
| funil de conversão | Métrica que mede etapas visita → carrinho → solicitação → orçamento → fechamento | "funnel" sem qualificar | dashboard de etapas e taxas de conversão | US-MKT-007 |
| evento de visualização | Registro anônimo (sem PII) de visita a item da vitrine | "page view", "hit" | log de telemetria respeitando LGPD | RAT-04 |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Termo descontinuado → marcar `@deprecated` + janela de migração 3 meses.
- Mudança de definição → bump no CHANGELOG seção "Modificado".

## Convenções

- Termos em PT-BR. Quando termo técnico em inglês for inevitável (ex: "cart", "checkout"), incluir tradução de campo.
- Definição em 1 linha.
- Origem obrigatória para termos regulados.
