# Discovery — Precificação de mercado

> **Artefato Rodada 0** (agente). Como o mercado precifica + WTP observado nas entrevistas → recomendação de modelo de pricing pro Aferê.

---

## Pra preencher

### Modelos comuns de pricing SaaS BR

| Modelo | Quem usa | Vantagem | Desvantagem |
|---|---|---|---|
| **Per-user** | Pipedrive, RD Station | Justo pra empresas que crescem | Penaliza adoção interna |
| **Per-módulo (à la carte)** | Omie | Cliente paga só o que usa | Complexo de explicar |
| **Flat por porte** | Bling, Tiny (planos pequeno/médio/grande) | Simples | Cliente pequeno paga "demais" relativo |
| **% de transação** | gateway pagamento, alguns ERPs financeiros | Alinhado a sucesso do cliente | Pode escalar exponencialmente |
| **Híbrido (base + per-uso)** | Stripe, Twilio | Flexível | Difícil prever conta |

### Pesquisa de pricing dos concorrentes

(Cruzar com `concorrentes.md`)

| Concorrente | Modelo | Faixa preço | Inclui calibração ISO 17025? |
|---|---|---|---|
| Bling | flat por plano | R$ 39 – 339 / mês | ❌ |
| Tiny | flat por plano | R$ 50 – 280 / mês | ❌ |
| Omie | per-módulo | R$ 80 – 800+ / mês | ❌ |
| Conta Azul | flat | R$ 50 – 200 / mês | ❌ |
| Granatum | flat | R$ 40 – 150 / mês | ❌ |
| (nichos calibração) | (a pesquisar) | ? | ✅ |

### WTP observado (de `validacao-ativa.md`)

(Preencher após pesquisa Van Westendorp nas entrevistas)

- Faixa cara mas compraria: R$ ... – R$ .../mês
- Faixa ótima: R$ ... – R$ .../mês

### Análise de oportunidade

- **Premium pro diferencial ISO 17025:** mercado paga mais por software regulado. Justifica preço acima do range Bling/Tiny pra clientes com calibração.
- **Risco de over-pricing pra assistências sem calibração:** pode perder fatia "ERP genérico".

### Recomendação preliminar

(A confirmar após `validacao-ativa.md` e `sintese-final.md`):

- **Plano Calibração:** R$ XXX/mês (premium pelo diferencial)
- **Plano Assistência:** R$ YYY/mês (competitivo vs Bling/Tiny)
- **Add-ons:** ...
- **Free trial:** 14 ou 30 dias (a decidir)

---

## Saída esperada
- Modelo de pricing recomendado
- Faixas de preço por persona/segmento
- Comparativo competitivo
- Entrada pra `sintese-final.md` (modelo de negócio)
