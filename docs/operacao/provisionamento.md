---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Provisionamento ⚪ (stub)

> ⏸️ **DORMENTE (2026-05-17):** provisionamento de servidor remoto só quando Roldão autorizar deploy. Ver [[deploy-so-quando-roldao-decidir]].
>
> **Status:** ⚪ lazy — preencher quando Roldão autorizar deploy + Ansible playbook existir.

---

## O que vai aqui (quando preencher)

- **Playbook Ansible** pra provisionar VPS Hostinger do zero:
  - SO base (Ubuntu LTS)
  - Hardening (firewall, fail2ban, SSH key only, sudo audit)
  - Docker + docker compose
  - PostgreSQL com RLS habilitada + roles `app_user`, `app_migrator`, `support_user` (todos NOBYPASSRLS)
  - Redis pra cache + Celery
  - Nginx reverso + TLS Let's Encrypt
  - Backup pgBackRest agendado
  - OpenTelemetry collector
  - Aferê application via docker compose
- **Playbook pra provedor secundário** (Magalu/Oracle/AWS sa-east-1) — DR cenário (c)
- **Inventário de inventories.yml** (lista de VMs gerenciadas)
- **Variáveis sensíveis** em Ansible Vault (não em git puro)
- **Smoke test pós-provisão:** "sobe stack do zero em < 30min e emite primeira request"

---

## Por enquanto

- Decisão fundadora: VPS Hostinger SP/BR (`discovery/sintese-final.md`)
- Provedor B a decidir antes do 1º tenant pago
- Quando playbook existir, este doc vira completo
