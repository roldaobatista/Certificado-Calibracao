---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# PlugNotas — NFS-e (primeiro `FiscalProvider`)

## Resumo

| Item | Detalhe |
|------|---------|
| Função | Emissão NFS-e via BaaS fiscal multi-município |
| Status | ⏳ Wave A — primeira implementação `FiscalProvider` (ADR-0008) |
| Anti-corrosion | `infrastructure/fiscal/plugnotas_provider.py` (a criar) |
| Sandbox | sim |
| DPA | nacional — contrato comercial cobre |
| Custo aprox | R$ 0,30-0,80 por NFS-e (varia por município) |

---

## Auth

API key por tenant da PlugNotas (não compartilhada com Aferê). Aferê gerencia onboarding:
- Tenant cadastra credencial PlugNotas
- Aferê armazena criptografada (KMS por tenant)
- Renovação via UI do tenant

---

## Endpoints principais (planejados)

- `POST /nfse/emit` — emite (idempotência via `external_id` do Aferê)
- `GET /nfse/{id}` — consulta
- `POST /nfse/cancel` — cancela / CC-e
- `GET /municipios/suportados` — lista de prefeituras com suporte

---

## Retry policy

Ver `arquitetura/cross-cutting/retry.md` — perfil "parceiro lento":
- 3 tentativas
- Base 5s, max 30s
- Após esgotar → fila `failed_nfse` + alerta SEV-2

---

## Idempotência

Chave: UUID gerado pelo Aferê (`certificado_id` ou `pedido_id` + UUID v4) enviado em campo `external_id`. PlugNotas usa pra deduplicar.

---

## Fallback

Focus NFe (`focus-nfe.md`). Smoke test trimestral confirma que Focus continua funcionando como segundo provider. Decisão de fallback automática se PlugNotas tem 50%+ erro em 1h.

---

## Monitoramento

- Tempo médio de emissão (alerta se > 2x baseline)
- Taxa de erro por município
- Custo mensal
- Cota de uso

---

## DPA / LGPD

PlugNotas trata dados pessoais (tomador, prestador). DPA comercial inclui:
- Tratamento conforme instrução
- Confidencialidade
- Notificação de incidente
- Subprocessadores (datacenters)

Verificar termos atuais em https://plugnotas.com.br (V2 quando contratado).

---

## Pendências

- [ ] Contrato comercial PlugNotas (quando Wave A começar)
- [ ] Implementação `FiscalProvider` interface
- [ ] Testes em sandbox por município
- [ ] Smoke test Focus NFe trimestral

---

## Referências

- ADR-0008 (fiscal pluggable)
- `cross-cutting/retry.md`, `idempotencia.md`, `timeout.md`
- `arquitetura/anti-corrosion-layer.md` (porta Fiscal)
