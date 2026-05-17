---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Cross-cutting — log

> **Pra quê:** sem padrão de log, debug em multi-tenant fica cego e LGPD/ISO 17025 perdem evidência.

---

## Formato estruturado (JSON)

```json
{
  "timestamp": "2026-05-17T14:30:00.123Z",
  "level": "INFO|WARN|ERROR|CRITICAL",
  "tenant_id": "T_42",
  "user_id_hash": "u_xyz789",
  "request_id": "req_abc123",
  "module": "calibracao",
  "env": "dev|staging|prod",
  "release_tag": "v0.3.2",
  "event": "certificate.emitted",
  "duration_ms": 1234,
  "meta": {"id_certificado": 42, "signatario": "u_xyz789"}
}
```

---

## Labels obrigatórias

| Label | Obrigatório? | Razão |
|-------|--------------|-------|
| `timestamp` | sim | ordering temporal |
| `level` | sim | filtro |
| `tenant_id` | sim (exceto cross-tenant) | debug multi-tenant + LGPD |
| `module` | sim | filtro por módulo |
| `request_id` | sim em request | correlação de log + trace |
| `user_id_hash` | sim em ação do usuário | LGPD: hash, não CPF |
| `env` | sim | distinguir dev/staging/prod |
| `release_tag` | sim em prod | correlacionar bug com versão |
| `event` | sim | nome estruturado da operação |

---

## **Nunca** logar (proibido — hook bloqueia)

- CPF/CNPJ em texto plano (usar hash ou parcial `XXX.XXX.123-45`)
- Senha (mesmo hash)
- Token / API key
- Conteúdo de e-mail/WhatsApp enviado
- Anexo de arquivo
- Chave privada / certificado A3
- Cookie de sessão
- Variável de ambiente sensível

Hook `secrets-scanner` cobre commit; hook adicional `log-redaction` (a criar) cobre runtime.

---

## Níveis

| Nível | Quando | Quem vê |
|-------|--------|---------|
| `DEBUG` | Dev e troubleshooting | Dev local; nunca em prod |
| `INFO` | Evento normal de negócio | Audit + observabilidade |
| `WARN` | Algo errado mas funcionou (degradação, retry) | Alertas SEV-3 |
| `ERROR` | Erro recuperável | Sentry + alertas SEV-2 |
| `CRITICAL` | Erro irrecuperável | Alertas SEV-0/1 + acordar Roldão |

---

## Padrão de event

Estilo dotted: `<modulo>.<entidade>.<ação>`.

Exemplos:
- `calibracao.certificado.emitted`
- `calibracao.certificado.revised`
- `fiscal.nfse.sent`
- `auth.login.success`
- `auth.login.failed`
- `tenant.suspended`
- `tenant.created`
- `mcp.tool.invoked`

---

## Audit log vs application log

- **Application log:** stack trace de bug, debug, observabilidade técnica → Axiom (30d quente)
- **Audit log:** quem fez o quê quando (LGPD + ISO 17025) → tabela `audit_event` no PG + WORM B2 (2 anos governance, 5+ anos regulado)

Auditor Segurança verifica em pre-commit que toda ação CRUD em paths sensíveis (`financeiro/`, `tenant/`, `kms/`) gera linha em `audit_event`.

---

## Onde logar (quando deploy autorizado)

```
app stdout/stderr
    ↓
OpenTelemetry collector (no host)
    ↓
Axiom (logs) + Grafana Cloud (métricas) + Tempo (traces) + B2 cold (audit WORM)
```

Em ambiente local: stdout suficiente; arquivos em `logs/` opcional.

---

## Referências

- `observabilidade.md` (⏸️ dormente — produção)
- `lgpd-rat.md` RAT-08 (audit log)
- `conformidade-iso-17025.md` cláusula 7.11
- `REGRAS-INEGOCIAVEIS.md` SEC-001 (segredos)
