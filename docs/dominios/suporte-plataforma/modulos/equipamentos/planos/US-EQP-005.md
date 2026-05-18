---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-005
---

# Plano US-EQP-005 — Sucatar equipamento com notificação ao cliente

> Story em `prd.md` §6 (US-EQP-005).
>
> **Pré-requisitos:** US-EQP-001 + porta `CertificadoQueryService.equipamento_tem_certificado_vigente()` (stub).
>
> **Revisão (2026-05-18 noite):** APROVADO COM RESSALVAS — 6 tech-lead + 6 advogado. Pareceres em `revisoes/US-EQP-005-{tech-lead,advogado}.md`. **Correção atômica já aplicada:** porta `OSQueryService` → `CertificadoQueryService` em api.md:143 (tech-lead TL2).

## Resumo

Implementar endpoint `POST /v1/equipamentos/{id}/sucatear` com (a) bloqueio se OS aberta (consulta porta `OSQueryService`), (b) confirmação dupla obrigatória se há cert vigente (RBC B5), (c) evento `equipamento.sucateado_com_certificado_vigente` que dispara notificação automática via porta `NotificacaoClienteService` (stub `EmptyNotificacaoClienteService` Wave A — grava evento que `comunicacao-omnichannel` processa quando nascer), (d) foto evidência opcional (recomendação corretora C1).

## Sequência de tasks

- **T-EQP-049**: porta `NotificacaoClienteService` em `src/domain/.../ports/` + `EmptyNotificacaoClienteService` (loga warning) + binding em settings. Override skip-empty permitido em dev/test (mesma lógica US-EQP-004).
- **T-EQP-050**: estender porta `CertificadoQueryService` adicionando `equipamento_tem_certificado_vigente() -> CertificadoSummary | None` (já listado no modelo-de-dominio v2 — confirmar adapter `EmptyCertificadoQueryService` retorna `None`).
- **T-EQP-051**: campo `foto_evidencia_sucatamento_url` no model `Equipamento` (migration 0015) — opcional, EXIF removido server-side se enviado.
- **T-EQP-052**: enum status novos no model `Equipamento`: garantir que `sucata` é estado terminal — trigger PG `bloquear_saida_de_sucata` (migration 0016) impede UPDATE para outros status exceto `extraviado` (admin via Django admin).
- **T-EQP-053**: use case `SucatarEquipamento`:
  - Validar status atual != `sucata` (idempotência: se já sucata → 200 com mesma resposta).
  - Validar sem OS aberta via porta `OSQueryService.equipamento_tem_os_aberta()` — senão 409.
  - Verificar cert vigente via porta `CertificadoQueryService.equipamento_tem_certificado_vigente()`.
  - Se há cert vigente + `confirmacao_dupla=false` → 412 "confirmação dupla obrigatória".
  - Se há cert vigente + `confirmacao_dupla=true` → status=sucata + audit `equipamento.sucateado_com_certificado_vigente` (payload `{equipamento_id, certificado_numero, cert_validade, cliente_atual_id_hash}`) + chamar `NotificacaoClienteService.notificar_sucatamento_com_cert_vigente()`.
  - Se não há cert vigente → status=sucata + audit `equipamento.sucateado` (payload `{equipamento_id, motivo, ts_marcacao}`).
  - Foto evidência: se enviada, EXIF removido + URL gravada em `foto_evidencia_sucatamento_url`.
- **T-EQP-054**: action `equipamento.sucatear` no seed authz (migration 0017). Atribuir aos perfis admin, metrologista (não atendente, não almoxarife).
- **T-EQP-055**: rate limit 10 req/min/usuário (mutação destrutiva).
- **T-EQP-056**: testes:
  - `test_sucatar_happy_path_sem_cert_vigente` (audit `equipamento.sucateado`)
  - `test_sucatar_com_cert_vigente_sem_confirmacao_dupla_retorna_412`
  - `test_sucatar_com_cert_vigente_com_confirmacao_dupla_grava_evento_especial` (RBC B5)
  - `test_sucatar_com_cert_vigente_dispara_notificacao_cliente_via_porta` (mock `NotificacaoClienteService`)
  - `test_sucatar_com_os_aberta_retorna_409` (porta `OSQueryService` mockada retornando True)
  - `test_sucatar_idempotente_segundo_call_retorna_200_mesmo_estado`
  - `test_sucata_nao_pode_voltar_para_ativo_trigger_pg` (RBC C5 — terminal)
  - `test_sucata_pode_ir_para_extraviado_admin_django` (apenas admin Django)
  - `test_foto_evidencia_exif_removido` (corretora C1)
  - `test_payload_audit_cert_vigente_so_hash_de_cliente` (sanitização)
  - `test_authz_metrologista_pode_sucatear` / `test_authz_atendente_nao_pode`
  - `test_idempotency_key_24h_recusa_reuso_destrutivo`

## Modelos/tabelas envolvidos

- **Já existe:** `equipamento` — adicionar `foto_evidencia_sucatamento_url`
- **Trigger novo:** `bloquear_saida_de_sucata`
- **Já existe:** `audit_trail.eventos`

## Endpoints envolvidos

- `POST /v1/equipamentos/{id}/sucatear`

## Hooks ativados

- Todos anteriores. Trigger PG `bloquear_saida_de_sucata` exige `# tests-coverage` apontando teste happy+unhappy.

## Testes obrigatórios

Ver T-EQP-056 (12 testes). Cobertura ≥85%.

## Riscos / pontos sensíveis

1. **`NotificacaoClienteService` stub:** Marco 2 só grava evento em audit. Cliente final NÃO recebe e-mail até `comunicacao-omnichannel` nascer. Mitigação: documentar em CURRENT.md + plano Wave B mostra que consumer real fica nessa porta.
2. **Trigger anti-saída de sucata:** admin Django ainda precisa poder mudar pra `extraviado` (cenário: cliente reportou roubo após sucatar). Trigger permite essa transição específica.
3. **Foto evidência:** advogado disse "RAT-EQP-FOTO se aplica". EXIF removed + se rosto identificável tenant assume controlador. Marco 2 deixa aviso textual + EXIF strip; blur facial fica V2.
4. **Idempotência:** segundo sucatear do mesmo equipamento deve retornar mesmo status + audit já gravado (não duplicar). Idempotency-Key TTL 24h.

## Subagentes a consultar

- `tech-lead-saas-regulado`: validar porta `NotificacaoClienteService` + trigger PG terminal.
- `advogado-saas-regulado`: validar texto do e-mail de notificação ao cliente (Marco 2 deixa template em constants; advogado revisa).
- `consultor-rbc-iso17025`: confirmar que `equipamento.sucateado_com_certificado_vigente` atende cl. 7.10 (trabalho não-conforme).

## Non-goals deste plano

- NÃO implementar consumer real em `comunicacao-omnichannel` (porta stub).
- NÃO implementar blur facial em fotos (V2).
- NÃO implementar reativação automática de sucata (terminal).
- NÃO implementar geolocalização do sucatamento (corretora C1 falava em hash da foto + timestamp; geolocalização exige opt-in — V2).
- **NÃO entregar foto evidência opcional nesta US** (TL6) — migra para US-EQP-006 que cria a porta `FotoStorageService` formal. T-EQP-051 + ramo foto em T-EQP-053 removidos.

---

## Endereçamento da revisão (12 ressalvas)

### Tech-lead

- **TL1 (CRÍTICA — trigger sucata):** padrão `BEFORE UPDATE` bloqueia tudo + função PG `SECURITY DEFINER marcar_extraviado_de_sucata()` + flag `set_config('afere.bypass_sucata_trigger', 'on', true)` local à transação (espelho `auditoria_bloqueia_mutation`). Evita brechas via shell/ORM/raw SQL.
- **TL2 (CRÍTICA — porta errada):** api.md:143 chamava `OSQueryService.equipamento_tem_certificado_vigente()` (errado) → corrigido para `CertificadoQueryService.equipamento_tem_certificado_vigente()` em commit atômico antes do `/tasks`.
- **TL3 (ALTA — idempotência):** `transaction.atomic` + `select_for_update` no `Equipamento` + tabela `idempotency_keys` (T-EQP-049/050 US-EQP-004). Sem `select_for_update`, mesma key não protege contra concorrência real.
- **TL4 (ALTA — Empty em prod):** payload `notificacao_status="pendente_consumer"` no audit + doc `controles-compensatorios-codigo-ia.md` (criado) + hook `port-binding-validator` falha se `settings.production` aponta `Empty*` sem override.
- **TL5 (MÉDIA — confirmacao_dupla extensível):** contrato como **objeto** `{ tipo: enum, ts_marcacao, ts_confirmacao, intervalo_min_ms: 1500 }` em vez de boolean — Marco 2 só `tipo="checkbox_modal"`; A3 entra V2 sem breaking change.
- **TL6 (MÉDIA — foto evidência migra):** removida desta US — entra em US-EQP-006 que cria `FotoStorageService` formal.

### Advogado

- **R1 (CONCERN — template sem CTA comercial):** teste de whitelist semântica falha em palavras-chave (`agende`, `promoção`, `desconto`, `clique aqui`). Comentário no código explícito.
- **R2 (CONCERN — payload audit completo):** `notificacao_template_versao` + `notificacao_canal` (enum: `email`/`whatsapp`/`sms`/`pendente_consumer`) no payload.
- **R3 (CONCERN — teste negativo):** asserir ausência de `cliente_atual_nome`, `cliente_atual_cpf/cnpj`, `cliente_atual_email`; só `cliente_atual_id_hash` permitido.
- **R4 (CONCERN — aviso UX foto):** TL6 migra foto pra US-006; aviso UX vai junto.
- **R5 (CONCERN — Aferê é operador):** template usa `{tenant_canal_atendimento}` (NUNCA canal do Aferê). Contestação cliente→tenant em 24h.
- **R6 (CONCERN — dispensa dogfooding):** se `cliente_atual_id == tenant_proprietario_id`, pula notificação (Balanças Solution sucatando equipamento próprio não dispara e-mail dele pra ele mesmo). Registra audit variante `_uso_interno`.

## Sequência revisada de tasks

- **T-EQP-049**: porta `NotificacaoClienteService` + `EmptyNotificacaoClienteServiceAdapter` (TL4 payload `pendente_consumer`)
- **T-EQP-050**: estender `CertificadoQueryService` com `equipamento_tem_certificado_vigente`
- **T-EQP-051**: ~~foto evidência~~ → REMOVIDA (migra US-EQP-006)
- **T-EQP-052**: trigger `bloquear_saida_de_sucata` padrão SECURITY DEFINER + `set_config bypass` (TL1)
- **T-EQP-053**: use case `SucatarEquipamento` com `confirmacao_dupla` como objeto extensível (TL5) + dispensa dogfooding (R6) + payload com `notificacao_template_versao`/`canal` (R2)
- **T-EQP-053a (NOVA)**: template e-mail PT v1.0-2026-05-18 (R1 — whitelist semântica anti-CTA + Aferê é operador R5)
- **T-EQP-054**: action `equipamento.sucatear` no seed authz
- **T-EQP-055**: rate limit 10 req/min
- **T-EQP-056**: testes (12 + R3 teste negativo PII + R1 whitelist semântica + TL1 trigger bypass + R6 dispensa dogfooding)
