---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
us: US-EQP-002b
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-002b.md
historico:
  - 2026-05-18 noite final — criado forward-looking. Fatiamento decidido por Roldão (TL3 US-002).
---

# Tasks T-EQP-002b-001..009 — US-EQP-002b (workflow gestor_qualidade aprovando `motivo=outros`)

> Forward-looking. Pré-requisito: US-EQP-002 entregue (stub `AprovacaoPendenteEquipamentoVersao` + `EquipamentoVersao` + enum `motivo_mudanca`). Decisões dos pareceres US-002 (TL3 + R2 advogado 16 campos + ISO 17025 cl. 6.2 + SLA D+3/D+7) aplicam diretamente.

## Mapa task → arquivo/migration → AC → INV → endereça ressalva

| Task | Descrição | Arquivo/Migration | AC | INV | Endereça |
|---|---|---|---|---|---|
| T-EQP-002b-001 | Migration `0021_aprovacao_pendente_equipamento_versao_completa` — 16 campos R2 advogado (solicitante/gestor com `_user_id` + `_user_id_hash`, `motivo_detalhe` + `motivo_detalhe_hash`, `parecer_gestor_texto` + `parecer_gestor_texto_hash`, `decisao`, `decisao_em`, `decisao_ip_hash` salgado por tenant, `decisao_assinatura_hash` HMAC, `sla_prazo`, `status`) + RLS policy `aprovacao_pendente_tenant_isolation` | `0021_aprovacao_pendente_completa.py` | AC-1 | INV-AUTHZ-002 | R2 advogado (BLOQUEADOR — 16 campos + sobrevive crypto-shredding) |
| T-EQP-002b-002 | Trigger PG `bloquear_update_decisao_aprovacao` — uma vez `decisao IS NOT NULL`, qualquer UPDATE em parecer/decisão/decisao_em/gestor_user_id REJECTED. Estende `audit-immutability-check.sh` pra cobrir `aprovacao_pendente_*` | `0022_trigger_imutabilidade_decisao.py` + hook | AC-2 | — | R2 advogado (audit aprovação imutável) |
| T-EQP-002b-003 | Validador ISO 17025 cl. 6.2 — segregação `solicitante_user_id != gestor_user_id` em camada application + CHECK CONSTRAINT PG | `src/application/.../aprovar_versionamento.py` + migration | AC-3 | — | ISO 17025 cl. 6.2 |
| T-EQP-002b-004 | Função `calcular_sla_prazo(equipamento_id, tenant_id)` — consulta `CertificadoQueryService.equipamento_tem_certificado_emitido()`; sem cert → D+3 dias úteis; com cert → D+7 dias úteis | `src/application/.../sla_aprovacao.py` | AC-4 | — | advogado US-002 R2 (SLA diferenciado) |
| T-EQP-002b-005 | Django admin `AprovacaoPendenteEquipamentoVersaoAdmin` — list view (filtros), detail view (parecer + decisão), botões aprovar/rejeitar com validação anti-PII no parecer + gera `decisao_assinatura_hash` + read-only pós-decisão | `src/infrastructure/equipamentos/admin.py` | AC-1, AC-2 | INV-EQP-VERSAO-001 | TL3 US-002 (workflow Django admin Marco 2) |
| T-EQP-002b-006 | Use case `AprovarVersionamento` — valida segregação, regex anti-PII em `parecer_gestor_texto`, gera `decisao_assinatura_hash = HMAC-SHA256(f"{tenant_id}|{decisao}|{decisao_em}", AUDIT_HMAC_KEY)`, promove `EquipamentoVersao.status` → `ativa` (ou marca `rejeitada`), grava audit `equipamento.versao_criada_aprovada_por_gestor` sanitizado | `src/application/.../aprovar_versionamento.py` | AC-1, AC-2, AC-3 | INV-EQP-VERSAO-001/002 | INV-EQP-VERSAO-002 (envelope sanitizado) |
| T-EQP-002b-007 | Management command `python manage.py escalar_aprovacoes_vencidas` (diário 09:00 BRT via cron externo) — marca `status=expirada` + publica `aprovacao_versao.expirada_sem_decisao` + alerta P2 | `src/infrastructure/equipamentos/management/commands/escalar_aprovacoes_vencidas.py` | AC-4 | — | risco workflow async (SLA) |
| T-EQP-002b-008 | Action `equipamento.aprovar_versionamento` no seed authz; perfil novo `gestor_qualidade`; NÃO atribuída a metrologista (segregação cl. 6.2). Endpoint `/v1/.../aprovar` deferido pra Wave A+ (Marco 2 = Django admin) | `0023_seed_authz_aprovar_versionamento.py` | AC-1 | SEC-LEAST-PRIV | ISO 17025 cl. 6.2 |
| T-EQP-002b-009 | Suite 13 testes: cria pendente 202; solicitante = gestor rejeita 400; parecer com PII 400; decidida imutável (trigger); SLA D+3 sem cert; SLA D+7 com cert; escalação diária `expirada`; `decisao_assinatura_hash` HMAC verificável; aprovada promove `ativa`; rejeitada promove `rejeitada`; metrologista não pode aprovar própria; gestor_qualidade pode aprovar; audit sanitizado | `tests/equipamentos/test_us_eqp_002b_workflow.py` | todas | INV-EQP-VERSAO-001/002, INV-AUTHZ-002 | todas |

## Pareceres aplicados

- US-EQP-002 (tech-lead + advogado) — decisões aplicáveis aqui (TL3 fatiamento, R2 16 campos, SLA D+3/D+7, ISO cl. 6.2)
- Sem revisão adicional necessária (decidido no plano).

## Total

9 tasks · 13 testes · 3 migrations · 1 management command · 1 perfil novo no seed authz.
