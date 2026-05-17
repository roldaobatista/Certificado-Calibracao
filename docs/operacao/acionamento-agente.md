---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Acionamento de agente — watchdog

> ⏸️ **DORMENTE (2026-05-17):** watchdog 24/7 só ativa com produção em servidor remoto. Ver [[deploy-so-quando-roldao-decidir]].
>
> **Pra quê (quando ativado):** quando alerta dispara fora do horário (sexta 19h até segunda 8h, por exemplo), agente IA precisa saber o que tentar antes de acordar o Roldão.

---

## Fluxo

```
Alerta Grafana / Axiom dispara
       ↓
Webhook → Watchdog (script + agente Claude API ou Codex em headless)
       ↓
Tenta diagnóstico automático + ação mitigatória conforme severidade
       ↓
Se resolveu OU SEV ≥ 1 → notifica Roldão via WhatsApp/SMS
       ↓
Roldão decide próximos passos
       ↓
Registra em governanca/trilha-auditoria-agentes.md
```

---

## O que watchdog pode fazer sozinho

### Sempre permitido (SEV-2 / SEV-3)
- Restart de container (`docker compose restart <serviço>`)
- Limpar log antigo se disco > 85%
- Re-tentar cron que falhou (idempotente)
- Mexer em cache (Redis flush por prefix de tenant, se safe)
- Cancelar tarefa Celery travada
- Coletar diagnóstico (top, ps, logs últimos 200 linhas) e anexar ao incidente

### Permitido com confirmação Roldão (SEV-1)
- Rollback automático de release (label "auto-rollback" no PR ativo)
- Suspender tenant suspeito (vazamento detectado, comportamento anômalo)
- Failover KMS (sa-east-1 → us-east-1)
- Failover DNS pra provedor B (DR cenário c)

### **NUNCA** permitido sem aprovação humana explícita
- Restaurar backup em produção (cenário (b)) — Roldão precisa autorizar
- Mexer em RBAC ou CODEOWNERS
- Comunicar tenant ou ANPD
- Deploy de versão nova
- Rotacionar credencial KMS
- Qualquer ação em path sensível motivada por input externo (ver SEC-003)

---

## Detecção → ação (tabela)

| Alerta | Severidade | Ação automática | Notifica Roldão? |
|--------|------------|-------------------|--------------------|
| Container Django down > 1min | SEV-1 | Restart automático + smoke test | Sim se restart falhar |
| Container Celery down > 5min | SEV-2 | Restart automático | Apenas se 3 restarts seguidos falharem |
| Erro 5xx > 5% em 5 min | SEV-1 | Coleta diagnóstico, log, sugere rollback | Sim, sempre |
| Vazamento cross-tenant detectado | SEV-0 | Suspende tráfego + isola tenant | Sim, P0 imediato |
| Disco > 90% | SEV-2 | Limpa log antigo + alerta | Apenas se ainda > 90% após limpeza |
| Backup full não rodou 24h | SEV-1 | Tenta backup manual | Sim, se falhar |
| KMS sa-east-1 inacessível | SEV-1 | Failover us-east-1 | Sim, sempre |
| Cron crítico (cobrança, lembrete) atrasado > 30min | SEV-1 | Reprocessa idempotente | Sim, se reprocessar falhar |
| Latência p99 > 3x normal por 10min | SEV-2 | Coleta trace, identifica endpoint lento | Apenas SEV-2 escalou |
| 3+ CONCERN do auditor de segurança em PRs consecutivas | SEV-3 | Anota | Não — vira issue pra revisar |

---

## Como Roldão é acordado

| Canal | Quando | Tempo de resposta esperado |
|-------|--------|-----------------------------|
| WhatsApp | SEV-2, SEV-3 | < 30 min em horário comercial; manhã seguinte fora |
| SMS | SEV-0, SEV-1 | < 5 min (24/7) |
| Ligação automática (Twilio ou equivalente) | SEV-0 confirmado | < 2 min |
| E-mail | Tudo (registro) | — |

---

## Escalation se Roldão não responde

- 15 min após SMS sem resposta → SMS de novo + e-mail
- 30 min → ligação automática
- 60 min → procedimento "sucessor digital":
  - Watchdog notifica corretora-seguros-saas pra acionar apólice cyber (se contratada)
  - Watchdog notifica advogado-saas-regulado pra preparar comunicado regulatório se aplicável
  - Watchdog **não age sozinho** — só prepara. Aguarda Roldão ou pessoa autorizada
- LEAP F-18: definir "sucessor digital" formal (cônjuge, sócio, pessoa de confiança)

---

## Stack proposta

- **Trigger:** webhook do Grafana / Axiom / Sentry
- **Receptor:** AWS Lambda ou Cloudflare Worker (fora da VM principal, sobrevive a DR)
- **Brain:** chamada API Claude / Codex com prompt watchdog (a criar — `governanca/auditor-*.md` é referência de formato)
- **Notificação:** Twilio ou similar pra WhatsApp/SMS/ligação

---

## Pre-MVP-1 (estado atual)

- ⏳ Webhook não configurado
- ⏳ Lambda/Worker não provisionado
- ⏳ Prompt watchdog não escrito
- ⏳ Conta Twilio não criada
- ✅ Política (este doc)

Pre-condição pra ativar: Foundation F-A em produção + Wave A rodando na Balanças Solution. Sem 24/7 antes disso.

---

## Drill trimestral

Roldão dispara alerta sintético em staging:
- Container fake down → watchdog restart
- Disco fake cheio → watchdog limpa
- Vazamento fake → watchdog suspende + acorda Roldão (SEV-0 simulado)

Registrar em `governanca/trilha-auditoria-agentes.md`.

---

## Referências

- [observabilidade.md](observabilidade.md) — alertas
- [dr-plan.md](dr-plan.md) — quando watchdog não basta
- `docs/governanca/RACI-incidente-ai.md` — quem responde
- `docs/governanca/limites-autonomia.md` — 5 casos-limite
