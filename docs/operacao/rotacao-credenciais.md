---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Rotação de credenciais ⚪ (stub)

> **Status:** ⚪ lazy — preencher depois do 1º tenant pago + 1ª credencial real em produção.

---

## O que vai aqui (quando preencher)

- Calendário de rotação (90 dias default, 30 dias pra critical)
- Procedimento por tipo de credencial:
  - AWS KMS — schedule-key-deletion + create new + re-encrypt
  - API token PlugNotas / Pluggy / Belvo / Twilio
  - Senha de usuário operacional do Aferê
  - SSH keys de acesso à VPS
  - GitHub tokens
- Quem é notificado em cada rotação (subagent `corretora-seguros-saas` valida se apólice cobre)
- Rollback se rotação falhar
- Drill anual: rotacionar tudo no mesmo dia em staging, medir RTO

---

## Por enquanto

Lista informal das credenciais ativas (manter atualizada):

| Credencial | Onde está | Última rotação | Próxima |
|------------|-----------|-----------------|---------|
| GitHub token (Claude Code) | `~/.claude/secrets` | 2026-05 (criado) | 2026-08 |
| Outras | — | — | — |

Quando entrar em produção, este doc vira completo.
