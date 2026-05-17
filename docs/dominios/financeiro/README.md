---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Domínio: Financeiro

## O que é este domínio

Financeiro agrupa **tudo do dinheiro**: contas a receber, contas a pagar, comissões, despesas, caixa do técnico, faturamento, documentos fiscais (NFS-e/NFe), conciliação bancária, relatórios financeiros (DRE/fluxo de caixa).

## Fronteiras com outros domínios

- **Entra:** fatura, NFS-e, conta a receber/pagar, comissão, despesa, caixa do técnico, conciliação, boleto, PIX, cartão, relatórios financeiros (DRE/fluxo caixa).
- **NÃO entra (vai pra Operação):** OS concluída — embora dispare cobrança.
- **NÃO entra (vai pra Comercial):** orçamento, contrato — embora alimentem o financeiro.
- **NÃO entra (vai pra Suporte-Plataforma):** custo de peça em estoque — embora a peça vendida vire receita financeira.
- **NÃO entra (vai pra RH):** folha de pagamento (V2/Wave C — non-goal MVP-1).

## Módulos deste domínio

| Módulo | Status | Pasta | Cobertura discovery |
|---|---|---|---|
| Contas a Receber | ⏳ a especificar | `modulos/contas-receber/` | OP-FIN (Wave A) + OP11 cobrança (Wave B) |
| Contas a Pagar | ⏳ a especificar | `modulos/contas-pagar/` | **Gap MVP-1** — não mencionado; MVP-2 |
| Comissões | ⏳ a especificar | `modulos/comissoes/` | OP4 (Wave A 1 fórmula; Wave B as outras 7) |
| Caixa do Técnico | ⏳ a especificar | `modulos/caixa-tecnico/` | OP3.2 (Wave A) — robusto |
| Fiscal (NFS-e/NFe) | ⏳ a especificar | `modulos/fiscal/` | OP7 (Wave A) + `fiscal.md` + `fiscal-contingencia.md` |

## Personas que tocam este domínio

Ver `personas.md` deste domínio. Núcleo:
- **Financeiro** (emite NFS-e, conciliação, cobrança)
- **Dono** (vê DRE / fluxo de caixa / inadimplência)
- **Vendedor** (vê demonstrativo de comissão)
- **Técnico de campo** (caixa do técnico via app)
- **Contador externo** (export SPED — V2)

## Compliance específico

- **Receita Federal:** retenção fiscal 5 anos (`retencao-matriz.md`); SPED export (V2)
- **NFS-e municipal:** cutover nacional 01/09/2026 (Dor #10 — janela competitiva)
- **LGPD RAT-05 (NFS-e), RAT-08 (audit fiscal)**
- **Lei Complementar 116/2003** — ISS; alíquota varia por município
- **BACEN:** Open Banking via Pluggy/Belvo BaaS (V2 quando Wave B)

## Integrações com outros domínios

Eventos:
- Operação → Financeiro: `OSConcluida` dispara `BoletoGerado` + opcional `NFSeEmitida`
- Operação → Financeiro: `OSConcluida` dispara cálculo de comissão (gatilho por recebimento — JTBD-082)
- Comercial → Financeiro: contrato recorrente dispara cobrança mensal
- Financeiro → Externo: PlugNotas (NFS-e), Pluggy/Belvo (banking), gateway (boleto/PIX)
- Financeiro → Comercial: `Pago` alimenta timeline 360° + libera comissão proporcional

## ADRs específicos do domínio

- ADR-0008 — Fiscal pluggable (FiscalProvider) ✅ proposta
- ADR-0009 — Onde A3 assina ✅ proposta (toca fiscal pela NFS-e)

## Status do domínio

🟡 **OP-FIN mínimo + OP3.2 + OP4 (Wave A) cobrem básico; contas a pagar + DRE + fluxo projetado são gaps de MVP-1.** Decisão design: **Aferê NÃO calcula imposto** — tenant configura com contador. Fiscal contingência criada. Banking via BaaS difere pra Wave B.
