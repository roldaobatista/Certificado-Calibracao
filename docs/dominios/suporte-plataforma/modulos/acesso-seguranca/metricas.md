---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
relacionados:
  - docs/arquitetura/cross-cutting/auth-rbac.md
  - docs/conformidade/comum/seguranca-dados.md
  - docs/conformidade/comum/lgpd-rat.md
  - docs/comum/isolamento-multi-tenant.md
---

# Métricas — Módulo Acesso, Segurança e Controle de Usuários (ACS)

> Como saber se o módulo está entregando valor + segurança. Mistura KPI de negócio (adoção, atendimento LGPD) com SLI/SLO técnico (latência, disponibilidade) e métricas de risco (incidentes, bypass).

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Taxa de adesão MFA em perfis sensíveis | % usuários com MFA ativo em perfis Admin Tenant / Financeiro / Metrologista | 100% | Query `acs_usuarios WHERE perfil IN (...) AND mfa_ativo = true / total` | Semanal |
| Tempo médio para atender solicitação LGPD | Mediana de horas entre abertura e conclusão de pedido de exportação/anonimização/exclusão | < 5 dias úteis (limite legal 15 dias — `INV-001`) | Trilha `acs.lgpd.solicitacao` (created_at → completed_at) | Mensal |
| Solicitações LGPD vencidas | Pedidos abertos há > 15 dias sem conclusão | 0 | Query trilha LGPD | Diário |
| Tempo de provisionamento de novo usuário | Mediana de minutos entre admin clicar "Novo" e usuário fazer 1º login | < 30 min | Trilha `acs.usuario.criado` → `acs.login.sucesso` (mesmo user) | Mensal |
| Tickets de suporte sobre acesso | % de tickets categorizados "esqueci senha / não consigo entrar / MFA perdido" sobre total | < 5% (gargalo é fluxo confuso) | Helpdesk + categoria | Mensal |
| Taxa de revogação de consentimento | % titulares que revogam consentimento em < 30 dias do cadastro | < 10% (sinaliza fricção no termo) | Trilha `acs.consentimento.revogado` | Mensal |

---

## Métricas de risco / segurança

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Incidentes cross-tenant | Eventos onde dado de tenant A foi visto por tenant B | **0** (qualquer ocorrência = P0) | Hook tenant-id-validator + alerta `SEC-TENANT-001` | Tempo real |
| Tentativas de login bloqueadas / total | % logins barrados por rate-limit ou conta bloqueada | < 5% (acima sugere ataque) | Trilha `acs.login.bloqueado / acs.login.tentativa` | Diário |
| Acessos negados por permissão (`acs.acesso.negado`) | Volume por usuário/perfil — identificar perfis mal-configurados | Linha-base por tenant; alerta se >10x baseline | Trilha | Semanal |
| Sessões expiradas por timeout vs logout explícito | Razão entre os dois | Não-target — observação para ajustar timeout | Trilha `acs.sessao.encerrada` (motivo) | Mensal |
| Reset de senha / mês / usuário ativo | Indicador de senha fraca ou phishing | < 0.5/mês/usuário | Trilha `acs.senha.redefinida` | Mensal |
| Sessões marcadas "esse não fui eu" | Reports de acesso suspeito por usuários | 0 (qualquer ocorrência abre investigação) | Trilha `acs.sessao.repudiada` | Tempo real |
| Janela entre rotação de chave KMS | Dias entre rotações da chave que cifra dados sensíveis do tenant | < 365 dias (política `seguranca-dados.md`) | KMS audit + cron de rotação | Mensal |
| Cobertura de auditoria (% ações de escrita auditadas) | Toda mutação grava evento? | 100% (`INV-001`) | Teste de invariante (hook anti-mascaramento) | Cada CI |
| Tempo médio de revogação de acesso após desligamento | Da marcação "desativado" ao fim de todas as sessões + revogação de tokens | < 5 min (limite SLO operacional) | Trilha `acs.usuario.desativado` → `acs.sessao.encerrada` | Mensal |

---

## SLI/SLO técnico

Detalhes em `../../../operacao/observabilidade.md`. Resumo:

| SLI | SLO | Erro orçamento mensal |
|---|---|---|
| Disponibilidade do login | 99.9% | ~43min/mês |
| Latência login completo (senha + MFA) p95 | < 2s | — |
| Latência verificação de permissão p99 (cache hit) | < 50ms | — |
| Latência verificação de permissão p99 (cache miss) | < 200ms | — |
| Disponibilidade do portal LGPD do titular | 99.5% | ~3.6h/mês |
| Taxa de erro 5xx em endpoints de auth | < 0.1% | — |
| Disponibilidade da trilha de auditoria (gravação) | 99.99% | ~4min/mês (perda de evento de auditoria é P0) |

---

## Dashboards canônicos

- **Grafana:** painel "ACS — Autenticação e Sessões" (link após ADR-0001 fechar).
- **Grafana:** painel "ACS — LGPD" (solicitações abertas, prazo, status).
- **Grafana:** painel "ACS — Tenant Isolation" (queries sem tenant_id detectadas = sempre 0).
- **Axiom:** logs estruturados com `module=acs`, índices por `tenant_id`, `user_id`, `event_type`.

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| `acs.cross_tenant.violacao` | Hook `tenant-id-validator` detecta query sem tenant_id ou cruzando tenants | Roldão + agente segurança + para sistema | **P0** |
| `acs.login.bloqueado_burst` | > 50 bloqueios de login do mesmo IP em 5min | Watchdog → agente segurança | P1 |
| `acs.lgpd.prazo_vencido` | Solicitação LGPD ultrapassa 12 dias sem conclusão (3 dias antes do limite legal) | Roldão | P1 |
| `acs.sessao.repudiada` | Usuário marca "esse não fui eu" | Watchdog → agente segurança → Roldão | P1 |
| `acs.audit_trail.gravacao_falhou` | Evento de auditoria perdido (DB indisponível) | Roldão + agente operação | **P0** |
| `acs.kms.rotacao_atrasada` | Rotação > 365 dias | Agente segurança | P2 |
| `acs.mfa.cobertura_quebrada` | Usuário com perfil sensível sem MFA ativo | Admin do tenant + agente segurança | P2 |
| `acs.admin_global.acao_destrutiva` | Admin global Aferê fez ação destrutiva (sem violar tenant) | Roldão (sempre) | P1 |

---

## Métricas de saúde dos AGENTES neste módulo

(parte da Família 5 Governança IA)

- Tokens consumidos / US-ACS implementada.
- Taxa de retrabalho em US deste módulo (US reverted ou re-aberta).
- Findings de auditor Segurança em código deste módulo (deve ser zero pra mergear).

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Métrica obsoleta → marcar `@deprecated` (não apagar — manter histórico).
- Mudança de target → ADR justificando.
