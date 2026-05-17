---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Deploy

> ⏸️ **DORMENTE (2026-05-17):** Roldão decidiu que **não haverá deploy a servidor remoto** até autorização explícita. Foundation F-A + Wave A construídas em ambiente local (Docker compose). Este doc fica de prontidão; política preservada mas inativa. Ver memória [[deploy-so-quando-roldao-decidir]].
>
> **Pra quê (quando ativado):** procedimento padrão pra subir versão nova em produção.

---

## Fluxo padrão

1. **Branch off `main` → feature branch** (`feature/<US-XXX>` ou `fix/<descrição>`)
2. **Commits atômicos** com mensagem clara + `Co-Authored-By: Claude`
3. **PR aberto** com link pro US/AC + descrição do que muda
4. **Hooks pre-commit** rodaram local (block-destructive, secrets, anti-mascaramento, tenant-id-validator, paths-frontmatter, INV-checker)
5. **GitHub Actions:** auditor-seguranca + auditor-qualidade rodam automático
6. **Label `ready-for-merge`** quando US completo → dispara auditor-produto
7. **Aprovação Roldão** (CODEOWNERS) — exigida pra paths sensíveis
8. **Merge pra `main`** — fast-forward sempre que possível
9. **Tag de release** seguindo SemVer (`v0.1.0` → `v0.2.0` etc.)
10. **CI Build:** Docker image + push pra registry com tag
11. **Janela de manutenção** (ver `maintenance-windows.md`) — só sáb 02-05 BRT salvo P0
12. **Deploy via Ansible playbook** → SSH → docker compose pull + up
13. **Smoke test pós-deploy** automático (10 endpoints críticos)
14. **Monitorar 30 min** em Grafana — alerta P0 = rollback imediato
15. **Anotar em CHANGELOG.md + atualizar status semanal**

---

## Pré-requisitos por release

- [ ] PR sem CONCERN do auditor-seguranca em path sensível
- [ ] PR sem FAIL de nenhum auditor
- [ ] Auditor-produto PASS (todos AC ✅)
- [ ] CHANGELOG.md entrada criada
- [ ] Migration revisada por subagent tech-lead se altera schema
- [ ] Nenhuma feature flag pendente de decisão
- [ ] Backup full nas últimas 24h (semanal não conta — se ficou 6 dias, refazer)
- [ ] Janela de manutenção declarada ou P0 justificada

---

## Rollback

**Rollback é primeiro recurso. Fix em produção é exceção.**

```bash
# Identificar tag anterior
TAG_ANTERIOR=v0.1.5
# Ansible playbook reverte pra tag anterior
ansible-playbook deploy.yml --extra-vars "image_tag=$TAG_ANTERIOR"
# Restore de banco SE migration nova quebrou — usar backup-restore.md
```

Critérios de rollback automático (acionamento-agente):
- Erro 5xx > 5% em 5 min
- Latência p99 > 3x a normal por 10 min
- Cobertura ANPD: vazamento detectado → rollback + isolamento imediato

---

## Após deploy bem-sucedido

- Anotar tag + timestamp em `governanca/trilha-auditoria-agentes.md`
- Atualizar `painel-do-dono.md` com "última versão em produção"
- Status semanal menciona release
- Comunicar tenants se há mudança visível na UX (e-mail templates em `externos/comunicado-release.md` — a criar)

---

## Pre-MVP-1 (estado atual)

Não há código de produto ainda. Quando Foundation F-A começar:
- Criar `.github/workflows/build-image.yml`
- Criar `ansible/deploy.yml`
- Provisionar VPS Hostinger via `provisionamento.md`
- Calibrar este runbook após 1º deploy real

---

## Referências

- [go-live-checklist.md](go-live-checklist.md) — antes de 1º deploy a tenant externo
- [maintenance-windows.md](maintenance-windows.md) — quando deployar
- [dr-plan.md](dr-plan.md) — quando algo der errado
- ADR-0001 — stack candidata (Django + Flutter + PG)
