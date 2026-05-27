---
adr: 0060
titulo: Porta EmailTemplateProvider + INV-MAIL-001 (dedup + backoff + opt-out)
owner: roldao
revisado-em: 2026-05-27
status: reservada
data: 2026-05-23
reservado-em: 2026-05-23 (Onda 0 plano-v2)
arquivo-fisico-criado-em: 2026-05-27 (Onda PRE-A.2 auditoria 10 lentes pré-Wave A — resolve drift estrutural §11 AGENTS)
ativacao-em: antes Marco 4/5 — JÁ EM ATRASO (M4 fechou sem)
bloqueia-fase: módulos que disparam e-mail transacional (régua cobrança, notificação ANPD/CGCRE, evento crítico operacional)
depende-de: ADR-0033 (idempotência consumer), ADR-0067 (perfil regulatório do tenant)
---

# ADR-0060 — Porta EmailTemplateProvider + INV-MAIL-001

> **Status:** **RESERVADA** — esqueleto criado em 2026-05-27 (Onda PRE-A.2 auditoria 10 lentes pré-Wave A) pra resolver drift de §11 AGENTS.md que citava esta ADR sem arquivo físico. M4 já fechou sem ADR-0060 — mas o módulo `comunicacao-omnichannel` Wave A vai precisar. Promover quando arquitetura de notificação for cravada.

## Escopo previsto (a detalhar)

- Porta canônica `EmailTemplateProvider` na anti-corrosion-layer.
- Adapters: SendGrid, AWS SES, eventual SMTP nativo Hostinger.
- **INV-MAIL-001:** dedup por hash `(event_id, template_id, destinatario)` numa janela de 24h — bloqueia mesma cobrança/régua/notificação ser enviada 2× se consumer reprocessar.
- **Tabela backoff explícita:** 1ª tentativa imediata → 5min → 30min → 4h → 24h → dead_letter (5 tentativas total).
- **Opt-out** registrado por destinatário+tipo (LGPD + CAN-SPAM/CASL alinhamento).
- **Bounce handling:** soft bounce vira retry; hard bounce vira opt-out automático.
- **Matriz feature×perfil ADR-0067:**
  - Perfil A: notificação ANPD/CGCRE obrigatória em incidentes (≤24h LGPD; ≤30d NC CGCRE).
  - Perfil D: só notificações comerciais (cobrança, recibo, lembrete OS).

## Templates Wave A previstos

- Régua cobrança D+3 / D+7 / D+15 / D+30 / D+60 / D+89 (ADR-0015 lifecycle tenant).
- Notificação tenant suspenso (ADR-0035 quando promover).
- Cliente desbloqueado pós-pagamento (GATE-CLI-6).
- Equipamento vencimento recalibração (M2).
- OS aberta / atrasada / concluída (M3).
- Certificado emitido (M4 + Wave A certificados).
- Convite onboarding tenant novo (provisionar_tenant).

## Quando promover

Quando módulo `comunicacao-omnichannel` Wave A entrar em saneamento PRD (Onda PRE-A.3). Roldão pode adiar pra Wave B se decidir que dogfooding inicial sem e-mail é tolerável (notificação via WhatsApp Business API direto).
