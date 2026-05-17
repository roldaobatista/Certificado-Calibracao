---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Plano de Disaster Recovery (DR)

> ⏸️ **DORMENTE (2026-05-17):** sem deploy a servidor remoto, não há DR a executar. Doc preservado pra ativação quando Roldão autorizar produção. Ver [[deploy-so-quando-roldao-decidir]].
>
> **Pra quê (quando ativado):** sair de "espero que dê tudo certo" pra "quando der errado, faço X em N minutos". Auditor 4 da 2ª auditoria promoveu este doc a 🔴 — 3 cenários explícitos.

---

## RTO / RPO targets

| Categoria | RTO (recovery time) | RPO (recovery point) |
|-----------|---------------------|------------------------|
| Falha de serviço único (Django down, Celery hung) | 15 min | 0 (sem perda) |
| VM corrompida (disco, FS, banco corrompido) | 1h | ≤ 1h (último WAL) |
| Hostinger BR inteiro fora > 4h | 4h | ≤ 4h (WAL replicado) |

---

## Cenário (a) — Falha de serviço único

**Sintoma:** Django/Celery/Postgres travado, mas VM acessível.

| Passo | Ação | Tempo |
|-------|------|-------|
| 1 | Alerta Grafana dispara — acionamento-agente acorda watchdog | T+0 |
| 2 | Watchdog tenta restart automático (`docker compose restart <serviço>`) | T+1min |
| 3 | Smoke test endpoints críticos | T+3min |
| 4 | Se passa: registrar incidente SEV-2 + postmortem leve | T+5min |
| 5 | Se falha: escalar pra Roldão via WhatsApp/SMS | T+5min |
| 6 | Roldão decide: rollback de release recente? backup? | T+15min |

---

## Cenário (b) — VM corrompida

**Sintoma:** disco com erro I/O, banco quebrado, OOM persistente. VM precisa ser recriada.

| Passo | Ação | Tempo |
|-------|------|-------|
| 1 | Alerta Grafana → acionamento-agente desperta Roldão (SEV-1) | T+0 |
| 2 | Roldão (ou watchdog autorizado) suspende DNS pra tenant externo | T+5min |
| 3 | Provisionar VM nova em Hostinger SP (Ansible playbook) | T+15min |
| 4 | Restore pgBackRest do último backup full + diff + WAL | T+30min |
| 5 | Smoke test endpoints + drill de query tenant_id | T+45min |
| 6 | Restaurar DNS | T+50min |
| 7 | Comunicar tenants afetados (e-mail + WhatsApp) | T+55min |
| 8 | Postmortem completo em ≤ 7 dias | T+7d |

**Pré-requisitos pra ser viável:**
- ✅ Ansible playbook pronto e testado (drill mensal)
- ✅ Backup pgBackRest testado restoring em VM provisória
- ✅ DNS gerenciado por API (Cloudflare ou equivalente) pra suspender automático
- ⏳ Lista de tenants ativos sincronizada fora da VM (em B2 metadados)

---

## Cenário (c) — Hostinger BR inteiro fora > 4h

**Sintoma:** provedor primário inacessível. Status page Hostinger confirma incidente prolongado.

| Passo | Ação | Tempo |
|-------|------|-------|
| 1 | Alerta + status page Hostinger checado | T+0 |
| 2 | Decidir: aguardar (< 4h) ou ativar DR? | T+30min |
| 3 | Se ativar: provisionar VPS em **provedor B** (Magalu/Oracle/AWS sa-east-1) via Ansible | T+1h |
| 4 | Restore do backup B2 EU Central → VPS provedor B | T+2h |
| 5 | Validar KMS (AWS KMS sa-east-1 sobrevive a Hostinger fora) | T+2h30 |
| 6 | DNS aponta pra provedor B | T+3h |
| 7 | Comunicar tenants — apólice cyber inclui DR (se contratada) | T+3h30 |
| 8 | Postmortem em ≤ 14 dias | T+14d |

**Pré-requisitos pra ser viável (CRÍTICO em V2):**
- ⏳ Conta ativa em provedor B (Magalu/Oracle/AWS) com payment method
- ⏳ Ansible playbook **testado em provedor B** (não só Hostinger)
- ⏳ Backup B2 EU Central confirmado acessível de IPs do provedor B
- ⏳ KMS sa-east-1 (AWS) acessível de qualquer provedor (multi-cloud por design)
- ⏳ **Apólice cyber acionável (DIFERIDA pra V2 — quando 1º cliente externo aparecer)** — dogfooding Balanças Solution não exige; Roldão aceita risco conscientemente. Ver [[sem-cliente-externo-na-janela-atual]].
- ⏳ Comunicação template pronta em PT-BR (só Balanças Solution na janela atual; templates externos diferidos)

**Drill:** após 5 tenants pagos ativos, drill anual obrigatório (provisionar provedor B inteiro do zero, ler RTO).

---

## DNS e ponteiros externos

- Domínio definitivo: a definir após batismo do produto (Aferê é provisório)
- DNS gerenciado por Cloudflare (proposto)
- TTL agressivo (5 min) pros A records de produção → DR rápido

---

## Comunicação com stakeholders durante DR

| Quem | Quando | Canal | Template |
|------|--------|-------|----------|
| Roldão | Imediato | WhatsApp/SMS via watchdog | "DR ativado, cenário (b/c), tempo estimado X" |
| Tenants ativos | T+30 min em (b); T+1h em (c) | E-mail + WhatsApp | "Estamos com indisponibilidade, ETA X. Acompanhar status.aferê.com.br (a criar)" |
| ANPD | Se vazamento confirmado: T+72h | Formulário oficial | Ver `lgpd-rat.md` §5 |
| Imprensa / mídia social | Roldão decide | Após resolver | — |

---

## Lições aprendidas (atualizar após cada drill ou incidente real)

| Data | Cenário | Tempo real | RTO atingido? | Aprendizado |
|------|---------|------------|---------------|-------------|
| — | — | — | — | (preencher após 1º drill) |

---

## Pre-MVP-1 (estado atual)

- ✅ Estratégia documentada (este doc)
- ⏳ Conta provedor B (aguardando decisão de qual)
- ⏳ Ansible playbook não escrito (parte da Foundation F-A)
- ⏳ Apólice cyber não contratada (depende de 1º tenant pago)
- ⏳ DNS provider não escolhido

Antes do 1º deploy a tenant externo: **drill obrigatório de cenário (b)** com restore cronometrado.

---

## Referências

- [backup-restore.md](backup-restore.md) — mecanismo
- [acionamento-agente.md](acionamento-agente.md) — watchdog
- [multi-tenant-ops.md](multi-tenant-ops.md) — restore por tenant
- [incidente-postmortem.md](incidente-postmortem.md) — template pós-DR
- ADR-0001 Portão 3 — drill obrigatório
