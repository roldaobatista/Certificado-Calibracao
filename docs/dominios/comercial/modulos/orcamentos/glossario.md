---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: orcamentos
dominio: comercial
diataxis: reference
---

# Glossário — Módulo Orçamentos

> Termos específicos. Transversais em `docs/comum/glossario-roldao.md`.

| Termo | Definição | Sinônimos proibidos | Se vir na tela/log significa | Origem |
|---|---|---|---|---|
| Orçamento | Documento comercial com preço, escopo, prazo, validade — emitido ANTES da OS para aprovação do cliente | "proposta", "cotação" | Pode virar PDF/Link/WhatsApp para cliente decidir | OP15 + JTBD-041 |
| Item de orçamento | Linha do orçamento (serviço ou produto do catálogo, qtd, preço unitário, desconto, total) | "linha", "produto" | Tabela dentro do orçamento | OP15.1 |
| Versão de orçamento | Snapshot imutável de uma revisão; cada revisão cria nova versão (V1, V2, V3) | "revisão" sem ID | Histórico mostra V1, V2... | OP15.2 |
| Validade | Data limite de aceitação. Após esta, orçamento expira automaticamente | "vencimento do orçamento" | Selo "expira em X dias" / "expirado" | INFERÊNCIA |
| Aprovação digital | Cliente aceita orçamento via link público (1 clique) sem precisar imprimir/assinar | "aceite digital" | Botão "Aprovar" no link público | OP15.3 + OP8.2 |
| Tracking de leitura | Sinal de "cliente abriu o link X horas atrás" | "rastreamento" | Marca "visualizado" + horário | OP15.2 |
| Condições comerciais | Forma de pagamento + prazo + observações jurídicas | "termos" | Bloco de texto no rodapé do PDF | — |
| Conversão em OS | Ato de aprovar orçamento e o sistema gerar OS rascunho automaticamente | "transformar em OS" | Botão "Aprovar e abrir OS" | OP15.4 |
| Template de orçamento | Modelo pré-configurado pelo tenant (calibração padrão, manutenção, instalação) | "modelo" | Atalho na criação | OP15.1 |
| Desconto | Redução de preço (% ou R$) sobre item ou total | — | Linha "desconto" + impacto em comissão prevista (JTBD-075) | — |
| Impacto em comissão | Preview que mostra ao vendedor quanto ele perde de comissão ao dar desconto X | — | Selo cinza ao lado do campo desconto | JTBD-075 |
| Orçamento perdido | Estado terminal quando cliente recusa explicitamente ou expira sem resposta | "rejeitado" | Aparece no funil CRM como motivo de perda | OP15 + OP5 |

## Convenções

- "Proposta" e "cotação" são sinônimos coloquiais — sempre normalizar para "orçamento" em UI/log.
- "Pedido" é diferente — pertence a OS após conversão.
