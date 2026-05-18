---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
escopo: divida regulatoria documentada — aceite presencial em US-EQP-004
relacionados:
  - docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-004.md
  - docs/dominios/suporte-plataforma/modulos/equipamentos/revisoes/US-EQP-004-advogado.md
  - docs/adr/0019-responsabilidade-codigo-agente-ia.md
---

# Aceite presencial de transferência de equipamento — dívida regulatória Marco 2

> **Origem:** parecer subagente `advogado-saas-regulado` para US-EQP-004 (2026-05-18 noite) — R2 BLOQUEANTE: "aceite presencial é vetor de fraude do atendente; mitigação tríplice tolerada no MVP-1 dogfooding, mas portal-cliente com OTP em Wave B+ é dívida regulatória explícita".
>
> **Status:** **aceito como dívida**. Documentado aqui para não cair no esquecimento + apresentar a auditor LGPD/civil em fiscalização se for cobrado.

---

## O que é o problema

US-EQP-004 implementa transferência de equipamento entre clientes do mesmo tenant. Lei 14.063/2020 art. 4º I (assinatura eletrônica simples) é base legal padrão. Para isso funcionar com **boa-fé probatória**, o cessionário precisa receber o termo em **seu canal pessoal** (e-mail, WhatsApp, portal) e **assinar com algum nível de prova de presença** (clique + IP + timestamp + nonce).

**Marco 2 não tem portal-cliente nem comunicacao-omnichannel.** Logo, o aceite é capturado pelo **atendente do tenant** que preenche em UI HTMX:

- Botão "registrar aceite presencial do cedente: ✅ cliente assinou no balcão".
- Botão idem para cessionário.

O atendente é funcionário do tenant — pode forjar (cliente nunca assinou; atendente clicou no nome dele).

---

## Risco específico

1. **Cliente cedente nega autorização posteriormente.** "Não autorizei essa transferência."
   - Aferê é operador (LGPD art. 39). Tenant responde primariamente perante cliente.
   - Tenant aciona Aferê em recurso de regresso alegando falha no sistema. Risco real de o tenant alegar que o sistema deveria ter exigido aceite externo.

2. **Cessionário recebe equipamento que não pediu.**
   - Cliente B descobre que tem equipamento de outro cliente alocado a ele. Reclama por "imputação errada" ao tenant.
   - LGPD art. 18 V (alteração de dados incorretos) — Aferê precisa ter ferramenta de reversão (US futura).

3. **Atendente desonesto comete crime contra o cliente do tenant.**
   - Cliente B compra equipamento de cliente A, atendente forja aceite do A sem A saber, A descobre via auditoria.
   - Cliente A processa o tenant; tenant processa o atendente (CLT art. 482 "a" — ato de improbidade).
   - Aferê fica solidário se ficar comprovado que o sistema **facilitou a fraude por design**.

---

## Mitigação atual (Marco 2 — aceito como suficiente para dogfooding)

Implementação obrigatória de **3 camadas defensivas** (advogado US-EQP-004 R2):

### Camada 1 — Campos novos no model `TransferenciaEquipamentoAceite`

- `aceite_origem_atendente_user_id: FK NOT NULL` — quem registrou o aceite presencial pelo cliente cedente.
- `aceite_destino_atendente_user_id: FK NOT NULL` — quem registrou pelo cessionário.
- `aceite_origem_evidencia_storage_key: string NULL` — foto/scan do termo físico assinado pelo cedente (opcional Marco 2; **obrigatório quando portal-cliente nascer**).
- `aceite_destino_evidencia_storage_key: string NULL` — idem.

Sem isso, audit não tem rastreabilidade do funcionário que efetivou o aceite — o crime fica impune.

### Camada 2 — Aviso UX de responsabilização

Antes do botão "registrar aceite presencial", UI mostra modal:

> **Atenção — você está registrando aceite presencial em nome de [Razão Social cliente cedente/cessionário].**
>
> Esta ação só pode ser executada **com o cliente fisicamente presente** ou **com sua autorização documentada** (e-mail, mensagem, contrato assinado).
>
> Registros falsos constituem **ato de improbidade** (CLT art. 482 "a") e **falsidade ideológica** (CP art. 299), sujeitos a demissão por justa causa + responsabilização criminal pessoal.
>
> Seu nome ficará no registro permanentemente.
>
> [ ] Confirmo que cliente está presente OU com autorização documentada e estou ciente das consequências de registro falso.
> [ Registrar aceite ] [ Cancelar ]

Marco 2: chechbox de ciência **obrigatório**. UX text-pronto pra colar em contratos/ui.md Tela 8 (próximo passo).

### Camada 3 — `via` no payload do evento + audit

`audit_trail.eventos action=equipamento.transferido` payload inclui:
- `aceite_origem_via: enum {portal_cliente_otp, email_confirmado, presencial_atendente, contrato_fisico_digitalizado}`
- `aceite_destino_via: enum` (mesmas opções)

**Marco 2 só permite `presencial_atendente` e `contrato_fisico_digitalizado`.** Outras opções entram quando módulos correspondentes nascerem.

`via = presencial_atendente` é **classificada como evidência fraca** em qualquer drill de auditoria. Tenant é alertado em onboarding sobre o risco e assina contrato (DPA cláusula nova) reconhecendo que esse modo é aceitável apenas em ambiente dogfooding/MVP-1, e que está obrigado a colher evidência física do cliente.

---

## Dívida regulatória explícita — Wave B+

Quando módulo `portal-cliente` nascer (Wave B+):

1. **Transferência envia link OTP ao e-mail/WhatsApp do cliente cedente** via `comunicacao-omnichannel`.
2. Cliente clica no link autenticado por código de 6 dígitos, lê o termo `v1.0-2026-05-18` (ou versão vigente) e clica "aceitar".
3. Sistema grava `aceite_origem_via=portal_cliente_otp` + IP do dispositivo do cliente + timestamp + nonce.
4. Mesmo fluxo para o cessionário.
5. **`presencial_atendente` continua disponível** como fallback (cliente sem e-mail, ambiente sem internet), mas começa a exigir foto da assinatura física (camada 1 obrigatória) + assinatura digital simples do atendente declarando que viu o cliente assinar.

**Quando isso destrava:**
- ✅ Lei 14.063/2020 art. 4º I plenamente cumprido para via=portal_cliente_otp.
- ✅ Mitigação de R-027 (fraude cross-canal).
- ✅ Subscritor cyber + RC aceita "controles compensatórios fortes".

**Estimativa:** Wave B (depois de portal-cliente + comunicacao-omnichannel — ~3-4 meses depois de Marco 2 fechar).

---

## Auditoria humana antes do go-live público

Antes de Aferê aceitar 1º tenant externo pago (não dogfooding), advogado humano com OAB ativa precisa:

1. Revisar o texto do termo `v1.0-2026-05-18` (advogado-saas-regulado US-EQP-004 R1) → ajustes finais.
2. Revisar o aviso UX da Camada 2 (este doc) → ajustes finais.
3. Revisar a cláusula nova do DPA "transferência presencial é evidência fraca" → confirmar redação contratualmente vinculante.
4. Validar se `via=contrato_fisico_digitalizado` precisa de **firma reconhecida** ou se eletrônica simples basta dependendo do valor do equipamento (alto valor → reconhecida).

Estimativa: 2-3h de consulta pontual + 2-3 dias de revisão de contratos.

---

## Como esta dívida é monitorada

- **Auditor Família 5 (Qualidade)** marca esta dívida no Marco 2 + cada Marco subsequente até portal-cliente nascer.
- **Auditor Família 5 (Segurança)** verifica que `via=presencial_atendente` NÃO está sendo usado em volume desproporcional (>10% transferências/mês = alerta P2).
- **Auditor Família 5 (Produto)** verifica se UX (Camada 2) está sendo respeitado (checkbox de ciência marcado em 100%).
- **Roldão decide:** quando Marco N tiver portal-cliente em operação, FECHA esta dívida formalmente (move de `stable` pra `closed` + bump CHANGELOG).
