---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
diataxis: explanation
audiencia: agente
modulo: integracoes-externas
dominio: suporte-plataforma
relacionados:
  - docs/dominios/suporte-plataforma/modulos/webhook-out/prd.md
  - docs/arquitetura/anti-corrosion-layer.md
---

# PRD — Módulo Integrações Externas (esqueleto — Wave B)

> Camada de **entrada/IN + adaptadores específicos** de sistemas externos do tenant. Webhook OUT vive em módulo próprio (`webhook-out`). Aqui ficam: webhook IN, OAuth out, adaptadores Bling/Conta Azul/Omie (Wave B sob demanda), conectores Zapier/Make oficiais.

## 1. O que este módulo é

Hub de integrações **bidirecionais ad-hoc** que não cabem nas portas canônicas da ACL (fiscal, pagamento, omnichannel já têm porta). Aqui entra: receber webhook de ERP externo do cliente (Bling chamou Aferê dizendo "produto cadastrado"), OAuth out pra autorizar Aferê a acessar Google Drive/Dropbox do tenant, conectores oficiais Zapier/Make (Aferê publica app no marketplace deles).

## 2. Por que existe

Cliente PME BR usa Bling/Conta Azul/Omie pra fiscal-leve; Aferê precisa **co-existir** sem virar substituto. Sem este módulo, cada integração ad-hoc vira código em domínio (proibido pela ACL). Módulo concentra adapters com governança.

## 3. Personas

- **P-INT-01 Admin tenant** — autoriza OAuth, mapeia campos.
- **P-INT-02 Parceiro técnico** — desenvolve adapter sob contrato.

## 4. Escopo (Wave B sob demanda — não Wave A)

- **Webhook IN** com validação HMAC + IP allowlist.
- **OAuth out** (porta `OAuthClientProvider` — Wave B, achado G-INT-5).
- **Adapter Bling** — sync produto/estoque (Wave B sob demanda).
- **Adapter Conta Azul** — sync cliente/NFS-e (Wave B sob demanda).
- **Adapter Omie** — idem (Wave B sob demanda).
- **App oficial Zapier** (Aferê listado no marketplace Zapier).
- **App oficial Make** (idem).

## 5. Non-goals

- **Bling/Conta Azul/Omie no Wave A** — non-goal explícito (G-INT-1). Wave B sob demanda; cliente prioritário paga adapter.
- **Marketplaces retail** (Mercado Livre, Amazon, Shopee) — non-goal explícito (G-INT-2). Fora do escopo Aferê (não é vertical e-commerce).
- **iPaaS completo** (estilo Zapier/Make competidor) — Aferê É a **fonte**, não o orquestrador; integra-se ao Zapier/Make como app.
- **SAP/Oracle/TOTVS Protheus** — enterprise; demanda projeto custom, não escopo SaaS.

## 6. User Stories (placeholders Wave B)

- **US-INT-001**: Tenant autoriza OAuth out pra Google Drive — Aferê salva backup mensal de certificados emitidos (Wave B).
- **US-INT-002**: Tenant configura webhook IN do Bling — produto cadastrado lá entra no catálogo Aferê (Wave B sob demanda).
- **US-INT-003**: Aferê publica app oficial no Zapier — tenant configura trigger sem código (Wave B).

ACs detalhados serão escritos quando US correspondente entrar em sprint.

## 7. Métricas (definir Wave B)

- % adapters com SLO 99% disponibilidade.
- Tempo médio adapter novo (parceiro técnico) < 4 semanas.

## 8. NFR

- **Segurança:** webhook IN com HMAC; OAuth out com PKCE; secrets em KMS (`INV-009`).
- **LGPD:** cada adapter exige DPA assinado com terceiro (subprocessador).
- **Audit:** toda chamada IN/OUT em `audit_trail.integracoes_externas`.

## 9. Glossário

Termos canônicos.

## 10. Como evolui

- Adapter novo → cliente prioritário paga desenvolvimento + ADR.
- OAuth out → ADR de criação da porta `OAuthClientProvider`.
