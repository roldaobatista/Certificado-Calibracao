---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Janelas de manutenção

> ⏸️ **DORMENTE (2026-05-17):** janelas só fazem sentido com produção em servidor remoto. Ver [[deploy-so-quando-roldao-decidir]].
>
> **Pra quê (quando ativado):** declarar quando é seguro deployar / reiniciar / fazer migration sem irritar tenant.

---

## Janela padrão

**Sábado das 02:00 às 05:00 (BRT)** — 3 horas/semana.

Razão: dia útil 8h-20h é hora de pico (lab e assistência técnica operam em horário comercial). Domingo cliente pode estar fazendo serviço; sábado madrugada é o ponto mais quieto.

---

## Tipos de ação por janela

### Sempre permitido fora de janela (sem aviso)
- Restart de container individual (rolling, sem downtime)
- Aplicar hotfix de release SEV-3 (cosmético)
- Limpar log / cache
- Backup automatizado (ocorre 3h BRT diário — dentro de janela)

### Permitido fora de janela com aviso ≥ 24h (banner no app)
- Release de versão minor sem migration destrutiva
- Mudança de configuração (feature flag, RBAC novo)
- Atualização de dependência crítica de segurança (CVE Critical)

### Só em janela
- Migration de schema que envolve `ALTER TABLE`, `ADD COLUMN NOT NULL`, índice grande
- Upgrade de versão major
- Mudança de infra (vCPU/RAM, mudança de provedor)
- Failover de DNS (cenário c DR planejado)
- Operações cross-tenant em batch

### NUNCA, mesmo em janela
- `DROP TABLE` em produção sem ADR aprovada + backup confirmado < 24h
- `git push --force` em main
- Rotação de KMS sem failover testado

---

## Aviso a tenants

| Janela | Comunicação |
|--------|--------------|
| Sáb 02-05 BRT (regular) | Banner no app de seg pra quarta + e-mail terça |
| Janela extraordinária | Banner + e-mail + WhatsApp opt-in ≥ 48h antes |
| Emergência P0 (manutenção forçada) | Banner imediato + e-mail + status page |

Template em `externos/comunicado-manutencao.md` (a criar quando 1º tenant externo aparecer).

---

## P0 — exceções

P0 = produção quebrada **ou** vulnerabilidade ativa **ou** vazamento confirmado. Nesse caso:
1. Roldão autoriza fora de janela (`APROVADO POR ROLDAO: P0 motivo`)
2. Comunicado a tenants em ≤ 30 min
3. Postmortem obrigatório em ≤ 7 dias (mesmo que tudo deu certo)

---

## Como agendar janela extraordinária

1. Subagente `tech-lead-saas-regulado` revisa: "isso poderia esperar próximo sábado?"
2. Se não: justificativa em `governanca/auditoria-decisoes-autonomas.md`
3. Roldão aprova
4. Aviso aos tenants ≥ 48h antes
5. Janela registrada em `governanca/trilha-auditoria-agentes.md`

---

## Calendário 2026 (esboço)

| Janela | Tipo | Atividade prevista |
|--------|------|---------------------|
| Todo sábado 02-05 BRT | Regular | Releases + migrations + manutenção |
| Sáb 01/09/2026 | Extraordinária | Cutover NFS-e nacional (Dor #10) — drill a marcar |
| Sáb 21/06/2026 | Extraordinária | Drill DR cenário (b) — VM corrompida simulada |

---

## Pre-MVP-1 (estado atual)

- ✅ Política definida (este doc)
- ⏳ Comunicado template não existe
- ⏳ Status page não publicada
- ⏳ Banner no app — depende de UI existir

---

## Referências

- [deploy.md](deploy.md) — quando aplicar releases
- [dr-plan.md](dr-plan.md) — DR em janela vs P0
- `docs/operacao/incidente-postmortem.md` — postmortem após P0
