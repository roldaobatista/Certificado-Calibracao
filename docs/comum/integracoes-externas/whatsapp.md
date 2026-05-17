---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# WhatsApp Business — BSP (mensageria transacional)

## Resumo

| Item | Detalhe |
|------|---------|
| Função | Lembretes de recalibração, status OS, comunicação cliente |
| Status | ⏳ F-E (Foundation) → ativação plena na Wave B (recalibração proativa) |
| Anti-corrosion | `infrastructure/messaging/whatsapp_provider.py` |
| Custo aprox | R$ 0,30-1,50 por conversa template (varia BSP) |

---

## Decisão de BSP (pendente)

Opções:
- **Take Blip** — BR-based, atendimento PT-BR, mais caro
- **Gupshup** — mais barato, suporte internacional
- **Meta direct** — sem intermediário (precisa qualificação)

Decisão diferida pra F-E. ADR específica quando começar.

---

## Princípios

- **Opt-in obrigatório** do destinatário (LGPD + boas práticas Meta)
- **Templates aprovados** pelo Meta antes de envio em massa
- **Sem spam** — bloqueio se Meta detectar abuse
- **Auditoria** de cada envio + opt-out fácil

---

## Templates planejados

- Lembrete recalibração: "Olá {nome}, seu equipamento {x} vence calibração em {data}. Quer agendar?"
- Status OS: "Sua OS #{n} mudou pra {status}. Acompanhe em {link}"
- Cobrança: "Boleto #{n} vence amanhã ({valor})."
- Aceite de orçamento: "Orçamento #{n}: aprovar ou recusar?"

Cada template aprovado por Roldão + auditor produto (mensagem em PT-BR claro, sem jargão).

---

## Retry / Timeout / Idempotência

Padrão da `cross-cutting/`:
- Timeout 35s
- 5 tentativas (backoff 2s base, max 120s)
- Idempotência via UUID por mensagem
- Dead letter se 5 falhas seguidas

---

## DPA / LGPD

Telefone do destinatário é PII. Tratamento:
- Base legal: execução de contrato (V) + opt-in registrado
- Retenção: até opt-out
- Não logar conteúdo da mensagem
- Anonimizar em audit log

---

## Pendências

- [ ] Escolher BSP (F-E)
- [ ] ADR específico do BSP
- [ ] Cadastro de templates no Meta
- [ ] Implementação `MessagingProvider`
- [ ] UI de opt-in/opt-out pro cliente final

---

## Referências

- ADR a criar (F-E)
- `arquitetura/anti-corrosion-layer.md` (porta Messaging)
- `lgpd-rat.md` RAT-06
