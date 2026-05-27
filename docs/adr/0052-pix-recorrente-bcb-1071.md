---
owner: roldao
revisado_em: 2026-05-27
proximo_review: 2026-08-27
status: aceito
aceito-em: 2026-05-27
diataxis: explanation
audiencia: agente
relacionados:
  - docs/adr/0008-fiscal-pluggable.md
  - docs/adr/0013-pricing-composicional.md
  - docs/arquitetura/anti-corrosion-layer.md
  - docs/dominios/financeiro/modulos/billing-saas/prd.md
---

# ADR-0052 — PIX Recorrente (BCB Resolução 1.071/2024) integrado via `PaymentGatewayProvider`

> **Status:** proposta (auditoria Onda 10 — Wave B + ACL portas novas, 2026-05-23). Resolve achado **G-BIL-2** (PIX recorrente não estava modelado em `billing-saas`). Complementa ADR-0050 (`PaymentGatewayProvider`) referenciada na Onda 9.
> **Decisor:** Roldão.
> **Bloqueia:** US-BIL-002 (cobrança recorrente), MetodoPagamento.tipo.

---

## Glossário (Roldão)

| Termo | Tradução |
|---|---|
| **PIX recorrente** | Cliente autoriza UMA vez no app do banco; Aferê cobra todo mês automaticamente, sem cartão. |
| **BCB 1.071/2024** | Resolução do Banco Central que regulou cobrança PIX recorrente (vigência mar/2025). |
| **Mandato** | "Autorização eletrônica" que o cliente assina no Internet Banking; vincula cliente × Aferê × valor máximo × periodicidade. |

---

## Contexto

Hoje `billing-saas` modela `MetodoPagamento` genérico (cartão tokenizado). A Resolução BCB 1.071/2024 (vigência mar/2025) abriu cobrança PIX recorrente — ICs (Itaú, BB, Bradesco, Caixa, Santander, Nubank) expõem APIs de mandato. Para SaaS B2B brasileiro, PIX recorrente reduz MDR (de ~3,5% cartão → ~0,4% PIX) e elimina chargeback. Sem modelar agora, billing nasce limitado a cartão + boleto.

## Decisão

Modelar `MetodoPagamento.tipo` como enum **fechado** com 4 valores:

| Valor | Descrição |
|---|---|
| `cartao_recorrente` | Token opaco do gateway (Stripe/PagSeguro/MP) — fluxo PCI atual |
| `pix_recorrente` | Mandato BCB 1.071/2024 — `mandato_id` opaco do gateway |
| `boleto` | Linha digitável por fatura (não-recorrente) |
| `pix_unico` | QRCode por fatura (não-recorrente) |

`pix_recorrente` é **consumido via `PaymentGatewayProvider.criar_cobranca(metodo=pix_recorrente, mandato_id=…)`** — sem porta nova; reuso da porta #11 da ACL. Tenant configura no checkout: cliente é redirecionado pro Internet Banking do banco escolhido, autoriza mandato, banco devolve `mandato_id` ao gateway.

### INV-BIL-PIX-001

**Tentativa de cobrança PIX recorrente sem `mandato_id` válido e vigente (não revogado, não expirado, valor da fatura ≤ teto do mandato) é rejeitada antes de chamar gateway.** Veredito: ALTO. Hook bloqueia. Cobrar sem mandato = TED não-autorizado = passivo regulatório BCB + LGPD.

### Eventos

- `BillingSaas.MandatoPixCriado(tenant_id, cliente_id, mandato_id, valor_teto, periodicidade)`
- `BillingSaas.MandatoPixRevogado(mandato_id, motivo)` — cliente revogou no banco; consumer pausa cobrança recorrente.

## Alternativas rejeitadas

1. **Continuar só com cartão** — perde 50% mercado BR PME que prefere PIX; MDR 3,5% reduz margem.
2. **PIX QR único por fatura** — cobra mas exige cliente abrir app todo mês; churn alto por esquecimento.
3. **Cobrança via Open Finance** — complexidade regulatória 10× pra ganho marginal.

## Consequências

**Positivas:** MDR cai de 3,5% → 0,4%; chargeback zero (PIX irrevogável após confirmação); UX melhor (autoriza 1×).
**Negativas:** dependência de banco aprovar mandato (~24h); revogação unilateral pelo cliente; teto fixo no mandato (subir requer novo mandato).

## Referências

- BCB Resolução 1.071/2024
- ADR-0013 (componentes de preço cobrados pelo método)
- ACL porta #11 `PaymentGatewayProvider`
