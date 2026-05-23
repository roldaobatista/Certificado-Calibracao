---
adr: 0050
titulo: Gateway de pagamento como porta (3 modos — cartão recorrente, PIX recorrente, boleto)
status: proposta
data: 2026-05-23
proposto-por: agente (Onda 9 — auditoria Wave A operacional, achado A-FIN-001)
revisado-por: tech-lead-saas-regulado (pendente)
aceito-em: —
bloqueia-fase: Wave A (`contas-receber` + `billing-saas`)
depende-de: ADR-0008 (fiscal pluggable), ADR-0015 (lifecycle tenant)
---

# ADR-0050 — Gateway de pagamento como porta

## Contexto

`docs/dominios/financeiro/modulos/contas-receber/prd.md` declara "1 gateway no MVP-1" e cita `ADR a definir: qual gateway (Asaas/Iugu/Gerencianet) — bloqueio` (§10). `billing-saas` (cobrança do tenant) depende do mesmo provedor.

Sem porta abstrata:
- Trocar provedor exige rewriting espalhado em `contas-receber/` + `billing-saas/` + webhooks + serializers.
- Multi-tenant Aferê é heterogêneo: alguns tenants já têm conta Iugu/Asaas/Stone e querem manter (auditoria integrações 17/05).
- BCB Resolução 1.071/2024 (vigência 2025) introduziu **PIX recorrente automático** com fluxo distinto de boleto — não modelar como caso particular do boleto/cartão.

## Decisão

Criar porta `PaymentGatewayProvider` (anti-corrosion layer §arquitetura) com **3 modos obrigatórios** que toda implementação deve oferecer:

| Modo | Caso | Mecanismo |
|---|---|---|
| `cartao_recorrente` | Assinatura SaaS billing, contrato mensal | Tokenização cliente-side (SEC-PCI-001) + cobrança recorrente programada |
| `pix_recorrente` | BCB 1.071/2024 — débito automático PIX | Convênio JRP-DCT + jornada de autorização do pagador no app do banco dele |
| `boleto` | Avulso / cliente que não aceita PIX | Linha digitável + QR estático |

### Operações da porta

```
PaymentGatewayProvider.criar_cobranca(meio, valor, vencimento, cliente_id, idempotency_key) -> CobrancaCriada
PaymentGatewayProvider.cancelar_cobranca(gateway_id, motivo) -> CobrancaCancelada
PaymentGatewayProvider.criar_recorrencia(modo, plano_id, cliente_id, valor, periodicidade) -> RecorrenciaCriada
PaymentGatewayProvider.cancelar_recorrencia(recorrencia_id, efetivo_em) -> RecorrenciaCancelada
PaymentGatewayProvider.verificar_webhook(payload, signature) -> EventoNormalizado  # HMAC obrigatório
```

### Implementação default

**Asaas** (cobertura PIX recorrente + cartão + boleto + webhook HMAC + sandbox). Não fecha o ADR para Asaas — abre porta. Provedor configurável por tenant via `tenant_features.payment_gateway_provider`.

### Multi-gateway por tenant (M-FIN-001)

Feature flag `gateway_provider_override` em `billing-saas/tenant_features` permite tenant escolher provedor distinto do default. Configuração via tela admin. Onda 10 (billing-saas) consolida.

## Consequências

**Positivas:**
- Trocar Asaas por Iugu/Stone vira impl da porta, zero mudança em domínio.
- PIX recorrente vira primeiro-classe — não improviso em cima de boleto.
- Idempotência (IDEMP-001) + HMAC webhook (SEC-PCI-001) viram contrato da porta, não detalhe de impl.

**Negativas:**
- Toda nova feature de gateway exige adapter em N provedores (mitigação: roadmap 1 provedor no MVP-1, escalar conforme demanda).

## Non-goals

- Open Finance bidirecional — Wave B/V2.
- Antecipação de recebíveis — Wave B.
- Múltiplos gateways simultâneos em UM tenant — Wave B (multi-acquirer).

## Invariantes derivadas

- **INV-FIN-GW-001** — webhook gateway exige HMAC válido + idempotência por `gateway_event_id` (reuso de SEC-PCI-001 + IDEMP-001).
- **INV-FIN-GW-002** — PIX recorrente exige `convenio_pix_id` no `Titulo` quando `meio=pix_recorrente`.

## Referências

- BCB Resolução 1.071/2024 (PIX automático).
- SEC-PCI-001, IDEMP-001 em `REGRAS-INEGOCIAVEIS.md`.
- `docs/arquitetura/anti-corrosion-layer.md` §PaymentGatewayProvider (a estender).
