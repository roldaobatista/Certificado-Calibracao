---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-002b
---

# Plano US-EQP-002b — Workflow gestor_qualidade aprovando versionamento `motivo=outros`

> **Origem:** decisão Roldão 2026-05-18 noite após review tech-lead US-EQP-002 R3 — fatiar workflow async em US separada pra reduzir risco de Marco 2 escorregar.
>
> **Pré-requisitos:** US-EQP-002 entregue (`EquipamentoVersao` + `motivo_mudanca` enum + A3 RT). Stub de tabela `AprovacaoPendenteEquipamentoVersao` já criado em T-EQP-024.
>
> **Revisão:** as decisões do tech-lead US-EQP-002 (TL3) + advogado US-EQP-002 (R2 16 campos + ISO cl. 6.2 + SLA D+3/D+7) **aplicam diretamente aqui**. Sem revisão adicional necessária.

## Resumo

Implementar workflow async de aprovação de versionamento com `motivo_mudanca=outros`: (a) tabela `AprovacaoPendenteEquipamentoVersao` completa com 16 campos (advogado US-002 R2), (b) Django admin com botão "aprovar / rejeitar" + justificativa do gestor, (c) segregação de funções ISO 17025 cl. 6.2 (solicitante ≠ aprovador), (d) SLA diferenciado D+3 (sem cert) / D+7 (com cert), (e) job de escalação SLA + alerta P2.

## Sequência de tasks

- **T-EQP-002b-001**: migration `0021_aprovacao_pendente_equipamento_versao_completa` — 16 campos da R2 do advogado US-002:
  - `equipamento_versao_id: FK NOT NULL`
  - `solicitante_user_id: FK NOT NULL`
  - `solicitante_user_id_hash: bytes(32)` (sobrevive crypto-shredding)
  - `motivo_detalhe: text NOT NULL` (≥100 chars, regex anti-PII INV-EQP-VERSAO-001)
  - `motivo_detalhe_hash: bytes(32)`
  - `data_solicitacao: timestamp NOT NULL`
  - `sla_prazo: timestamp NOT NULL` (D+3 sem cert; D+7 com cert)
  - `gestor_user_id: FK NULL` (preenchido na decisão)
  - `gestor_user_id_hash: bytes(32) NULL`
  - `parecer_gestor_texto: text NULL` (regex anti-PII INV-EQP-VERSAO-001)
  - `parecer_gestor_texto_hash: bytes(32) NULL`
  - `decisao: enum NULL {aprovada, rejeitada}`
  - `decisao_em: timestamp NULL`
  - `decisao_ip_hash: bytes(32) NULL` (salgado por tenant — INV-AUTHZ-002)
  - `decisao_assinatura_hash: text NULL` (HMAC com `tenant_id + decisao + decisao_em` salt — prova de integridade)
  - `status: enum {pendente, decidida, expirada} NOT NULL`
  - RLS policy `aprovacao_pendente_tenant_isolation`.
- **T-EQP-002b-002**: trigger PG `bloquear_update_decisao_aprovacao` — uma vez `decisao IS NOT NULL`, qualquer UPDATE no parecer/decisão/decisao_em/gestor_user_id é REJECTED. Estende hook `audit-immutability-check.sh`.
- **T-EQP-002b-003**: validador ISO 17025 cl. 6.2 — segregação de funções: `solicitante_user_id != gestor_user_id` no momento da decisão. Validado em camada application + check constraint PG.
- **T-EQP-002b-004**: SLA diferenciado — função `calcular_sla_prazo(equipamento_id, tenant_id) -> timestamp`:
  - Consulta porta `CertificadoQueryService.equipamento_tem_certificado_emitido()`.
  - Sem cert → D+3 dias úteis.
  - Com cert → D+7 dias úteis.
- **T-EQP-002b-005**: Django admin `AprovacaoPendenteEquipamentoVersaoAdmin`:
  - List view com filtros (status, perfil tenant, equipamento, solicitante, sla_prazo vencendo).
  - Detail view com texto da solicitação + campos editáveis (`parecer_gestor_texto`, `decisao`).
  - Botão "aprovar" valida regex anti-PII no parecer + gera `decisao_assinatura_hash` + grava trigger-protected.
  - Botão "rejeitar" idem + força resposta 422 da `EquipamentoVersao` original (status=rejeitada na versão).
  - Hide-on-save: após decisão, formulário fica read-only (refletindo trigger).
- **T-EQP-002b-006**: use case `AprovarVersionamento` em `src/application/.../aprovar_versionamento.py`:
  - Validar `solicitante_user_id != gestor_user_id` (ISO 17025 cl. 6.2).
  - Validar regex anti-PII em `parecer_gestor_texto`.
  - Gerar `decisao_assinatura_hash` = `HMAC-SHA256(f"{tenant_id}|{decisao}|{decisao_em}", chave_audit_global)`.
  - Aplicar a versão (se aprovada) — promove `EquipamentoVersao` de `pendente_aprovacao` pra `ativa`.
  - Gravar audit `equipamento.versao_criada_aprovada_por_gestor` com payload sanitizado (INV-EQP-VERSAO-002).
- **T-EQP-002b-007**: job Celery (procrastinate quando Wave A late entregar; Marco 2 deixa management command `python manage.py escalar_aprovacoes_vencidas` rodado por cron externo):
  - Diariamente às 09:00 BRT.
  - Identifica `AprovacaoPendenteEquipamentoVersao` com `sla_prazo < now() AND status = pendente`.
  - Marca `status = expirada` + publica `aprovacao_versao.expirada_sem_decisao` em audit.
  - Alerta P2 pra suporte do tenant.
- **T-EQP-002b-008**: endpoint `POST /v1/equipamentos/{id}/versoes/{versao_id}/aprovar` (Wave A+ — Marco 2 deixa via Django admin):
  - Action `equipamento.aprovar_versionamento` no seed authz.
  - Atribuído ao perfil `gestor_qualidade` (perfil novo a criar no seed) + admin.
  - **NÃO** atribuído a metrologista (que é o solicitante típico — segregação ISO 17025 cl. 6.2).
- **T-EQP-002b-009**: testes:
  - `test_motivo_outros_cria_aprovacao_pendente_202`
  - `test_solicitante_mesmo_gestor_rejeita_400` (ISO 17025 cl. 6.2)
  - `test_parecer_gestor_com_pii_rejeita_400` (INV-EQP-VERSAO-001)
  - `test_aprovacao_decidida_imutavel_via_trigger` (R2 advogado)
  - `test_sla_d_mais_3_sem_cert`
  - `test_sla_d_mais_7_com_cert`
  - `test_escalacao_diaria_marca_expirada`
  - `test_decisao_assinatura_hash_hmac_verificavel`
  - `test_versao_aprovada_promove_status_para_ativa`
  - `test_versao_rejeitada_marca_status_pra_rejeitada`
  - `test_authz_metrologista_solicitante_nao_pode_aprovar_propria_versao`
  - `test_authz_gestor_qualidade_pode_aprovar`
  - `test_evento_aprovacao_grava_audit_sanitizado` (INV-EQP-VERSAO-002)

## Modelos/tabelas envolvidos

- **Novo (completo):** `aprovacao_pendente_equipamento_versao` (16 campos R2 advogado)
- **Trigger novo:** `bloquear_update_decisao_aprovacao`
- **Já existe:** `equipamento_versao` (US-EQP-002 ainda tem stub) — recebe status `pendente_aprovacao` adicional

## Endpoints envolvidos

- Django admin (Marco 2 + 002b)
- Endpoint API `/v1/equipamentos/{id}/versoes/{versao_id}/aprovar` (Wave A+, não Marco 2)

## Hooks ativados

- `audit-immutability-check.sh` estendido para `aprovacao_pendente_*` (T-EQP-002b-002)
- Hook `INV-checker` cobre INV-EQP-VERSAO-001/002

## Testes obrigatórios

Ver T-EQP-002b-009 (13 testes). Cobertura ≥85%.

## Riscos / pontos sensíveis

1. **Workflow async sem UI próprio:** Marco 2 entrega Django admin. Risco de gestor não acessar admin com frequência → SLA vence sem decisão. Mitigação: job de escalação T-EQP-002b-007 + alerta P2.
2. **`decisao_assinatura_hash` precisa `chave_audit_global`:** chave KMS separada de `KMS_qr_secret` — `settings.AUDIT_HMAC_KEY`. Sem isso, hash de decisão pode ser forjado. Hook `qr-hmac-check.sh` estende para validar.
3. **Segregação ISO 17025 cl. 6.2:** check constraint PG `solicitante_user_id != gestor_user_id` impede self-approval. Se gestor é o único do tenant — quem aprova? Mitigação: fluxo de exceção via admin Aferê (suporte) com A3 do dono do CNPJ.
4. **Perfil novo `gestor_qualidade` no seed authz:** Marco 2 cria o perfil + atribui action. Tenant pode não ter ninguém nesse perfil — versionamento `motivo=outros` fica eternamente em `pendente`. Documentar em `docs/dominios/.../equipamentos/runbook-tenant.md` (a criar Wave A+).

## Subagentes a consultar

- Já tratado nos pareceres US-EQP-002 (tech-lead + advogado).
- `consultor-rbc-iso17025`: confirmar segregação cl. 6.2 + SLA D+3/D+7 razoáveis (Wave A+).

## Non-goals

- NÃO entregar endpoint `/v1/equipamentos/{id}/versoes/{versao_id}/aprovar` no Marco 2 (Django admin é suficiente pra dogfooding).
- NÃO entregar UI HTMX externa do gestor (Wave A+).
- NÃO entregar notificação via comunicacao-omnichannel (porta ainda vazia).
- NÃO entregar fluxo de exceção (gestor único do tenant — caso-limite documentado).
