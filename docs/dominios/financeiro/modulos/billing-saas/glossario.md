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

# Glossário do módulo Billing SaaS

> Termos específicos deste módulo. Transversais ficam em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Assinatura | Vínculo comercial vigente entre tenant e Aferê com plano, status e ciclo | "contrato", "subscription" | "esse tenant tem direito de usar o sistema, e está em qual plano" | PRD |
| Plano | Pacote comercial (Perfil A/B/C/D) com limites e preço | "tier", "subscription plan" | "qual pacote o tenant contratou" | PRD |
| Trial | Período de teste gratuito com fim automático | "free tier", "demo" | "tenant está testando, vai expirar" | linha 1495 `novas funcionalidades.txt` |
| Trial expirado | Assinatura cujo trial venceu sem método de pagamento ativo | "demo end" | "tenant não vai pagar — bloqueado" | PRD |
| Bloqueio progressivo | Sequência D+3 warning → D+7 read-only → D+15 suspensão | "dunning" (inglês) | "tenant está em alguma etapa de cobrança ativa" | linha 1505 `novas funcionalidades.txt` |
| Suspensão | Estado do tenant em que apenas área de regularização é acessível | "blocked", "cancelado" | "tenant bloqueado por inadimplência" | linha 1499 |
| Cancelamento | Encerramento voluntário da assinatura | "churn" | "tenant pediu pra sair" | linha 1498 |
| Upgrade | Mudança pra plano superior com efeito imediato e proporcionalização | "promoção" | "tenant cresceu de plano" | linha 1496 |
| Downgrade | Mudança pra plano inferior com efeito no próximo ciclo | "rebaixamento" | "tenant vai pagar menos no próximo ciclo" | linha 1497 |
| Cupom | Código promocional com desconto % ou valor fixo, único ou recorrente | "voucher", "promo code" | "tenant aplicou desconto" | linha 1502 |
| Fatura SaaS | Documento de cobrança do Aferê pro tenant (≠ NF-e dos clientes do tenant) | "boleto" (boleto é um meio) | "cobrança que o Aferê emitiu pra esse tenant" | linha 1501 |
| Gateway | Provedor de pagamento (Stripe, PagSeguro) que processa o cartão | "adquirente" | "quem processou o cartão" | ADR a criar |
| MRR | Monthly Recurring Revenue — receita recorrente mensal | "faturamento" (faturamento é mais amplo) | "indicador de saúde do SaaS" | métrica |
| Churn | Taxa de cancelamento de assinaturas no período | "evasão" | "% de tenants que saíram" | métrica |
| Limite de plano | Restrição quantitativa (nº usuários, módulos, volume) por plano | "quota" | "tenant atingiu limite, sugerir upgrade" | linha 1491 |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Termo descontinuado → marcar `@deprecated` + janela 3 meses.

## Convenções

- Termos em PT-BR; jargão inglês de mercado SaaS (MRR, churn, trial) mantido por uso consolidado, traduzido na coluna "Se vir na tela/log".
