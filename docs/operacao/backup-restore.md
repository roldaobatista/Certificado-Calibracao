---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Backup e restore

> ⏸️ **DORMENTE PARCIALMENTE (2026-05-17):** pgBackRest agendado + B2 WORM só com deploy a servidor. Em ambiente local, `pg_dump` manual basta. Ver [[deploy-so-quando-roldao-decidir]].
>
> **Pra quê (quando ativado):** garantir que dados perdidos sejam recuperáveis e que o "recuperar" foi testado, não só presumido. Distingue trilha imutável (eventos) vs estado mutável (documentos fiscais corrigíveis).

---

## Estratégia

- **Banco PostgreSQL:** pgBackRest com backup full semanal + diff diário + WAL archive contínuo (RPO ≤ 1h em condição normal)
- **Backups armazenados em:**
  - Local: Hostinger SP (cópia quente, retenção 30 dias)
  - Remoto: Backblaze B2 EU Central (cópia fria, retenção conforme `retencao-matriz.md`)
- **Criptografia:** cada tenant tem chave KMS própria (AWS KMS Multi-Region sa-east-1 ↔ us-east-1). Backups criptografados com envelope encryption por tenant
- **Storage WORM (B2 Object Lock):** trilha de eventos imutáveis (audit, certificados ISO, NF-e finalizada) — não pode ser modificada nem por root

---

## Trilha imutável vs estado mutável

| Categoria | Estado | Como tratar |
|-----------|--------|-------------|
| Audit log | Append-only WORM | Nunca regravar; comparação de hash em restore |
| Certificado de calibração emitido | WORM | Revisão = nova versão (não sobrescrever) |
| NF-e finalizada | WORM | Cancelamento via CC-e (não delete) |
| Cadastro cliente | Mutável | Restore pode sobrescrever |
| OS aberta | Mutável | Restore pode sobrescrever |
| Documento de configuração (settings, RBAC) | Mutável | Restore pode sobrescrever (com cuidado — pode reverter mudança de segurança) |

---

## Procedimento de backup (automatizado)

```bash
# Semanal — sábado 02:00 BRT (dentro de maintenance window)
pgBackRest --stanza=afere backup --type=full

# Diário — diário 03:00 BRT
pgBackRest --stanza=afere backup --type=diff

# WAL contínuo (RPO ≤ 1h)
# Configurado via archive_command no postgresql.conf
```

Validação pós-backup:
- Hash do backup registrado em audit WORM
- Tamanho confere com estimativa (alert se variação > 30%)
- Tag do commit Git correspondente registrada

---

## Procedimento de restore (manual + ensaiado)

### Cenário comum: restore de tenant individual
```bash
# 1. Identificar timestamp alvo
# 2. Provisionar instância de restore (não tocar prod)
# 3. Restore só do schema do tenant
pgBackRest --stanza=afere restore --target=schema:tenant_42 --target-time="2026-05-15 14:30:00"
# 4. Validar integridade (registro contador, hash de audit)
# 5. Decidir: replay parcial vs full restore + reconciliação
```

### Cenário grave: restore total
Ver [dr-plan.md](dr-plan.md) — cenário (b) e (c).

---

## Drill de restore (obrigatório trimestral; 1 vez no MVP-1)

Conforme ADR-0001 Portão 3:
- **Mensal antes do 1º tenant pago:** 1 drill
- **Trimestral após 5 tenants ativos:** 3 drills

Cada drill:
1. Provisionar VM nova (provedor B — Magalu/Oracle/AWS sa-east-1)
2. Restore do último backup full + diff + WAL
3. Cronometrar: tempo de restore + tempo até "consigo emitir NF-e ok"
4. Registrar em `governanca/trilha-auditoria-agentes.md`
5. Postmortem se passar do RTO

**RTO alvo (recovery time objective):**
- Cenário (a) — falha de serviço único: 15 min
- Cenário (b) — VM corrompida: 1h
- Cenário (c) — Hostinger BR fora: 4h via provedor secundário

---

## O que NÃO é coberto

- **Dados em cache LLM externo** (OpenAI/Anthropic) — fora do escopo
- **Dados em e-mails enviados** — não voltam
- **Logs Grafana/Axiom** — anonimizados na entrada, retenção própria
- **Hostinger inteiro perdido por > 4h** → cenário (c) DR; aceita-se downtime

---

## Referências

- [dr-plan.md](dr-plan.md) — 3 cenários de desastre
- [multi-tenant-ops.md](multi-tenant-ops.md) — restore por tenant
- `docs/conformidade/comum/retencao-matriz.md` — prazos
- ADR-0001 Portão 3 — drill obrigatório
