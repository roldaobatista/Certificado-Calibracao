---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Operação multi-tenant — runbook por tenant

> ⏸️ **DORMENTE (2026-05-17):** operações de tenant em produção só com deploy a servidor. Em ambiente local, tenant é apenas dado lógico. Ver [[deploy-so-quando-roldao-decidir]].
>
> **Pra quê (quando ativado):** "reiniciar / restaurar / suspender tenant X sem afetar tenant Y" precisa ser procedimento operacional definido.

---

## Princípio

- Toda operação que toca dado tem `tenant_id` no escopo
- Toda operação registrada em audit log com `tenant_id` label
- "Operação cross-tenant" (afeta múltiplos) exige aprovação humana explícita (`APROVADO POR ROLDAO`)

---

## Operações comuns

### A. Reiniciar serviço do tenant X (sem afetar outros)

Como schema-shared, **não há "container do tenant X"** — todos compartilham app. "Reiniciar tenant X" geralmente significa:

- Invalidar sessões / tokens do tenant X
- Limpar cache do tenant X (`redis-cli --scan --pattern 't:42:*' | xargs redis-cli DEL`)
- Reprocessar última fila de jobs Celery do tenant X (`afere reprocess --tenant=42 --queue=cobranca`)

Comandos:
```bash
# 1. Invalidar sessões
afere manage invalidate_sessions --tenant=42

# 2. Limpar cache redis do tenant
redis-cli --scan --pattern "t:42:*" | xargs redis-cli DEL

# 3. Reprocessar Celery queue
afere manage reprocess --tenant=42
```

---

### B. Suspender tenant X (não-pagamento, suspeita de fraude, vazamento detectado)

```bash
# 1. Marca tenant.suspended = true (curto-circuita middleware)
afere manage suspend_tenant --id=42 --reason="<motivo>" --approved-by=Roldao

# 2. Invalida sessões ativas
afere manage invalidate_sessions --tenant=42

# 3. Logout forçado de mobile
afere manage push_logout --tenant=42

# 4. Registra em audit
# (automático via signal Django)
```

**Importante:** suspensão NÃO deleta dados. Cliente cancelou → próximo procedimento.

---

### C. Restaurar tenant X (rollback de incidente nele)

Restore parcial (só o schema do tenant):
```bash
# 1. Identificar timestamp alvo (anterior ao incidente)
TS="2026-05-15 14:30:00"

# 2. Restore num banco temporário
pgBackRest --stanza=afere restore \
  --target-time="$TS" \
  --target=tenant_42 \
  --pg-restore-target=/var/lib/postgresql/restore_t42

# 3. Validar integridade (audit hash bate?)
afere manage validate_tenant_restore --tenant=42 --restore-path=/var/lib/postgresql/restore_t42

# 4. Decidir: copy table-a-table OU swap schema inteiro
# (em geral copy do que está corrompido, manter o resto)

# 5. Atualizar audit WORM com registro da operação
```

Tempo esperado: < 30 min. Drill mensal antes do 1º tenant pago testa isso.

---

### D. Excluir tenant X (cancelamento de contrato + 15 dias de carência)

Ver `docs/conformidade/comum/retencao-matriz.md` §3 cenário C. Resumo:

```bash
# 1. Anuncia exclusão (30 dias de retenção quente pra reativação)
afere manage announce_deletion --tenant=42 --carencia=30d

# 2. Após 30 dias: export completo dos dados pro tenant
afere manage export_tenant --tenant=42 --output=/tmp/tenant42_export.zip
# (entregar via canal seguro)

# 3. Após 15 dias adicionais (LGPD): crypto-shredding
aws kms schedule-key-deletion --key-id <arn-da-chave-tenant-42> --pending-window-in-days 7

# 4. Cleanup quente dos dados restantes (anonimizar nomes em audit compartilhado)
afere manage anonymize_residual --tenant=42

# 5. WORM permanece (NF-e, certificados ISO 17025 — base legal regulatória)
# Não há ação aqui — apenas cuidar de não cruzar reference de outro tenant
```

---

### E. Debug em produção pra tenant X (sem violar isolamento dos outros)

Role separada `support_user` com permissões enxutas + audit reforçado:
```bash
# Login como support_user (MFA obrigatório)
ssh -i ~/.ssh/aferê_support root@vm.afere.com.br
sudo -u support psql -d afere -c "SET LOCAL app.tenant_id = '42';"
# A partir daqui, queries enxergam só tenant 42 via RLS
```

**Importante:** toda query roda com `tenant_id` setado, RLS enforce. Tentativa de cross-tenant retorna 0 rows. Audit WORM registra sessão completa.

---

## Operações cross-tenant (sempre exigem aprovação)

| Operação | Aprovação |
|----------|-----------|
| Bulk update em tabela de domínio comum | `APROVADO POR ROLDAO: <razão>` |
| Migração de schema que afeta todos | ADR + revisão |
| Métricas agregadas com PII | Anonimização obrigatória |
| Comunicação a múltiplos tenants | Template aprovado |
| Crypto-shredding em batch | Lista revisada + aprovada |

---

## Drill trimestral

| ID | Cenário | Esperado |
|----|---------|----------|
| DRILL-MT-01 | Suspender tenant 42; tenant 43 segue acessando normal | ✓ |
| DRILL-MT-02 | Restore tenant 42 sem afetar 43-99 | ✓ (RTO < 30min) |
| DRILL-MT-03 | Excluir tenant 42; backup futuro com chave nova; restore impossível ler dados do 42 | ✓ |
| DRILL-MT-04 | Suporte debugar tenant 42; auditar que não viu dados do 43 | log WORM mostra só queries com `tenant_id=42` |
| DRILL-MT-05 | Tentar query manual sem `tenant_id` na sessão `support_user` | falha (RLS) |

---

## Observabilidade tenant-aware

- Painel Grafana "Por tenant" mostra:
  - Uso de recursos (vCPU, RAM, disco) por tenant
  - Volume de OS/certificados/NF-e do dia
  - Últimos incidentes do tenant
  - Custo agregado (tokens LLM, infra prorata)
  - Aderência ao SLO por módulo

---

## Pre-MVP-1 (estado atual)

- ✅ Política (este doc)
- ⏳ Comandos `afere manage *` não existem (Django manage commands a criar)
- ⏳ Role `support_user` não criada
- ⏳ Drills não executados

---

## Referências

- `docs/comum/isolamento-multi-tenant.md` — RLS, tenant_id, INV-TENANT-*
- `docs/conformidade/comum/retencao-matriz.md` — crypto-shredding
- [backup-restore.md](backup-restore.md) — restore parcial por tenant
- [dr-plan.md](dr-plan.md) — quando incidente vira DR
- ADR-0002 — multi-tenancy
