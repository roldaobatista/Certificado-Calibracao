---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Observabilidade

> ⏸️ **DORMENTE (2026-05-17):** observabilidade cloud (Grafana, Axiom, Sentry) só ativa com deploy a servidor. Em ambiente local, logs Python padrão + pytest bastam. Ver [[deploy-so-quando-roldao-decidir]].
>
> **Pra quê (quando ativado):** sem observabilidade tenant-aware, debug em multi-tenant é cego e LGPD/ISO 17025 ficam sem evidência. Exige **SLO por módulo**, não SLO único.

---

## Stack

- **Métricas:** OpenTelemetry → Grafana Cloud (free tier inicial)
- **Logs:** OpenTelemetry → Axiom (free tier + B2 cold storage)
- **Traces:** OpenTelemetry → Grafana Tempo (free tier)
- **Erros estruturados:** Sentry (decidir entre self-hosted vs SaaS)

**Tudo encaminhado via Aferê → LiteLLM gateway → provedor.** Anonimização aplicada antes de sair da rede do projeto.

---

## SLO por módulo (não SLO único pra ERP inteiro)

| Módulo | SLO disponibilidade | Latência p99 | Erro 5xx |
|--------|---------------------|--------------|----------|
| **Financeiro** (NFS-e, cobrança) | **99.95%** | < 2s | < 0.1% |
| **Billing SaaS** (assinatura/cobrança do próprio Aferê) | **99.95%** | < 2s | < 0.1% |
| **Calibração** (emissão certificado, cálculo incerteza) | **99.9%** | < 5s | < 0.1% |
| **Precificação** (motor de preço — bloqueia orçamento) | **99.9%** | < 500ms | < 0.2% |
| **CRM** (cadastros, agenda) | **99.5%** | < 1s | < 0.5% |
| **Mobile** (técnico de campo, offline-first) | **99% (sync)** | offline ok | < 1% (sync) |
| **WhatsApp BSP** (lembretes) | **99% (entrega)** | < 30s | < 2% |
| **Auth** | **99.95%** | < 500ms | < 0.05% |
| **Multi-tenant infra** | **99.99%** | < 200ms (overhead) | 0% (qualquer vazamento = SEV-0) |

Por que SLO diferente: emissão de certificado é mais crítica que CRM porque tem implicação regulatória; auth é caminho crítico de tudo; mobile aceita degradação parcial por design (offline-first).

---

## Labels obrigatórias em todos sinais

Todo log, métrica, trace, alerta **DEVE** ter:
- `tenant_id` (exceto sinais cross-tenant explicitamente marcados)
- `module` (financeiro, calibracao, crm, mobile, etc.)
- `env` (dev, staging, prod)
- `release_tag` (ex: `v0.3.2`)
- `request_id` (UUID por request)

Sem `tenant_id` em log → hook anti-mascaramento + auditor de segurança FAIL.

---

## Alertas críticos (PagerDuty / WhatsApp)

| Alerta | Severidade | Ação |
|--------|------------|------|
| Erro 5xx > 5% em 5 min num módulo | SEV-1 | Acionamento-agente desperta Roldão |
| Vazamento cross-tenant detectado (query SQL com tenant_id de A retornou linha do B) | SEV-0 | Suspende sistema imediato + ANPD 72h |
| Latência p99 > 3x normal por 10 min | SEV-2 | Notifica Roldão; possível DR cenário (a) |
| Backup full não rodou em 24h | SEV-1 | Notifica + tenta novamente |
| KMS sa-east-1 inacessível | SEV-1 | Failover us-east-1; comunicar |
| Disco > 85% | SEV-2 | Limpar logs antigos + alertar |
| RAM > 90% por 30 min | SEV-2 | Análise + possível scale up |
| Auditor de segurança FAIL em 3 PRs consecutivas | SEV-3 | Revisar prompt do auditor |
| Cron crítico (cobrança, lembrete) não rodou | SEV-1 | Investigar + reprocessar |

---

## Dashboards Grafana

Painéis a criar (quando código existir):
- **Dono (Roldão):** topo-100 — números do dia + alertas abertos
- **Por módulo:** SLO atingido, erros, latência, top endpoints lentos
- **Por tenant:** uso, custo, último incidente
- **Custo:** tokens LLM / tenant, infra mensal, projeção
- **Conformidade:** % requests com tenant_id label, % com release_tag, etc.

---

## Logs — formato estruturado

```json
{
  "timestamp": "2026-05-17T14:30:00Z",
  "level": "INFO",
  "tenant_id": "T_42",
  "module": "calibracao",
  "env": "prod",
  "release_tag": "v0.3.2",
  "request_id": "req_abc123",
  "user_id_hash": "u_xyz789",
  "event": "certificate.emitted",
  "duration_ms": 1234,
  "meta": {...}
}
```

**Nunca** logar:
- CPF/CNPJ em texto plano (usar hash ou parcial XXX.XXX.123-45)
- Senha
- Token / chave
- Conteúdo de e-mail enviado
- Anexo de arquivo

---

## Traces (OpenTelemetry)

Sampling:
- 100% em rotas críticas (NFS-e emissão, certificado emissão, login, fatura)
- 10% em rotas normais (CRM, listagem)
- 1% em rotas internas (health, metrics)
- 100% em erro

Cada trace propaga `tenant_id` como atributo OTel.

---

## Custos esperados (estimativa)

| Serviço | Tier inicial | Estimativa Mês 12 |
|---------|--------------|---------------------|
| Grafana Cloud | Free (10k métricas) | ~R$ 200/mês |
| Axiom logs | Free (500GB/mês) | ~R$ 300/mês |
| Sentry | Free (5k erros) → Team | ~R$ 150/mês |
| AWS KMS | $1/chave/mês × N tenants | ~R$ 50 × tenants |

Threshold pra revisar: > R$ 1000/mês total de observabilidade dispara revisão.

---

## Pre-MVP-1 (estado atual)

- ⏳ OTel não plugado (depende de código)
- ⏳ Contas Grafana / Axiom / Sentry a criar
- ⏳ Dashboards não montados
- ✅ Política aqui (este doc)

Antes de 1º tenant pago: SLOs por módulo monitorados + alertas SEV-0/1 configurados + drill de detecção (Roldão simula vazamento; alerta dispara?).

---

## Referências

- [acionamento-agente.md](acionamento-agente.md) — watchdog
- [dr-plan.md](dr-plan.md) — quando alerta vira DR
- `docs/governanca/trilha-auditoria-agentes.md` — append-only audit
- `docs/comum/isolamento-multi-tenant.md` — tenant_id label
