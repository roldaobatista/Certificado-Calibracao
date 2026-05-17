---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Runbook — operação dia-a-dia

> **Pra quê:** hub central pra encontrar o procedimento certo na hora certa. Sem esse índice, agente perde 10 minutos procurando "como reinicio o servidor de prod?".

---

## Onde achar cada coisa

| Necessidade | Doc |
|-------------|-----|
| Deploy pra produção | [deploy.md](deploy.md) |
| Backup e restore | [backup-restore.md](backup-restore.md) |
| Plano de desastre (provedor caiu, VM corrompida) | [dr-plan.md](dr-plan.md) |
| Métricas, alertas, SLOs | [observabilidade.md](observabilidade.md) |
| Quando subir release pro cliente | [go-live-checklist.md](go-live-checklist.md) |
| Watchdog disparou alerta — quem age? | [acionamento-agente.md](acionamento-agente.md) |
| Aconteceu incidente — escrever postmortem | [incidente-postmortem.md](incidente-postmortem.md) |
| Capacidade do servidor estourando | [capacity-planning.md](capacity-planning.md) |
| Operar um tenant específico (reiniciar, suspender, restaurar) | [multi-tenant-ops.md](multi-tenant-ops.md) |
| Quando posso deployar? | [maintenance-windows.md](maintenance-windows.md) |
| Trocar credencial (KMS, API, senha) | [rotacao-credenciais.md](rotacao-credenciais.md) |
| Subir nova VM / provisionar ambiente | [provisionamento.md](provisionamento.md) |

---

## Quem opera o quê

- **Roldão:** decisor final em incidente; aprovar deploy a produção; assinar comunicado a tenants
- **Subagent `tech-lead-saas-regulado`:** code review de rollout; verificar checklist de deploy
- **Subagent `auditor-seguranca`:** pre-commit + pre-merge; bloqueia rollout se SEC-* violado
- **Watchdog (acionamento-agente):** detecta sinal anormal → dispara protocolo de acionamento

---

## Princípios de operação

1. **Zero deploy em dia útil 8h-20h** salvo P0 (ver `maintenance-windows.md`)
2. **Crypto-shredding por tenant** ao excluir (ver `retencao-matriz.md`)
3. **Toda ação registrada** em `governanca/trilha-auditoria-agentes.md`
4. **Rollback é primeiro recurso**; fix em produção é exceção
5. **Postmortem obrigatório** em ≤ 30 dias após qualquer SEV-0 ou SEV-1

---

## Severidades

| Severidade | Definição | SLA inicial |
|------------|-----------|-------------|
| SEV-0 | Vazamento cross-tenant; dado fiscal corrompido em produção; KMS perdido | T+15min Roldão + contenção |
| SEV-1 | Módulo MVP-1 fora do ar > 5 min; certificado emitido com erro | T+30min Roldão + contenção |
| SEV-2 | Funcionalidade não-crítica degradada | T+4h |
| SEV-3 | Cosmético; UX degrade | Próxima janela de manutenção |
