"""App `webhook_out` — adapter canonico OutboundWebhookProvider (F-C1 P4).

Quem deve usar: qualquer modulo em `src/infrastructure/**` que precise
chamar URL HTTP externa (Lacuna, AWS KMS, Asaas, INMETRO, SendGrid,
webhooks de tenant). Uso direto de `requests`/`httpx`/`urllib*` em
outras infrastructure apps fica PROIBIDO pelo hook
`outbound-webhook-ssrf-check.sh`.

Camadas:
- ssrf_guard.py — validacao IP/hostname contra 8 faixas + porta
- hmac_sign.py — canonical string + HMAC-SHA256
- models.py — WebhookDestino (cadastro DPA + chave HMAC)
- adapter.py — HttpxWebhookOut implementando Protocol
"""
