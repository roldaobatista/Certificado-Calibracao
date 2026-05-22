# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** Marco 1 **FECHADO** + Marco 2 `equipamentos` em P4 (T-EQP-001
+ 006 + 002 + 003 + US-EQP-007 + T-EQP-005 + T-EQP-007 + T-EQP-009 +
T-EQP-012 + T-EQP-016 + T-EQP-017 + T-EQP-013 doc+helper +
T-EQP-018+020+021+022 US-EQP-002b + T-EQP-019 SLA+job +
T-EQP-013 trigger PG + T-EQP-071 hook + módulo stub `certificados` +
T-EQP-024+030+031 ficha 360° + T-EQP-025+026+033 QR público 3 escopos +
T-EQP-034+035+036+040 transferência fundação +
T-EQP-037+038 Idempotency + termo v1.1 +
**T-EQP-039+041 consentimento histórico granular** entregues;
GATE-EQP-INV025-TRIGGER FECHADO).
**Sessão ativa 2026-05-23.**
**Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-23)

- T-EQP-009: **15/15 passed** em 4.8s
- T-EQP-012+016: **13/13 passed** em 4.0s
- T-EQP-017: **11/11 passed** em 8.0s
- T-EQP-013: **7/7 passed** em 0.7s (textos canônicos T1-T5 + anti-drift)
- T-EQP-018+020+021+022 (US-EQP-002b): **11/11 passed** em 3.5s
- T-EQP-019 (SLA workalendar + job): **8/8 passed** em 4.9s
- T-EQP-013 trigger PG + módulo `certificados`: **14/14 passed** em 4.2s
- Hooks: **192/192** verdes (22+1 ativos — novo `equipamento-imutabilidade-check.sh` com 13 casos EI1..EId)
- ⚠️→✅ **OOM resolvido**: docker-compose ganhou `mem_limit: 12g` (app) / 4g (db); `shm_size: 1g` (app) / 512m (db). **Suite completa: 621 passed em 37min sem OOM.**
- T-EQP-024+030+031 (ficha 360°): **9/9 passed** em 7.6s
- T-EQP-025+026+033 (QR público 3 escopos + timing): **10/10 passed** em 8.8s
- T-EQP-034+035+036+040 (transferência fundação): **12/12 passed** em 6.4s
- T-EQP-037+038 (Idempotency-Key + termo v1.1): **12/12 passed** em 8.0s
- T-EQP-039+041 (consentimento histórico granular): **13/13 passed** em 11.3s
- Regressão transferência (T-EQP-034+037+038): **24/24 passed** em 11.2s
- modelo_001 (regressão): **8/8 passed**
- inv_eqp_rt_001 (regressão): **3/3 passed**
- Hooks: **192/192** verdes (22+1 ativos — sem hook novo nesta T)
- `makemigrations --check`: limpo; ruff zero issues
- ⚠️ **Suite completa não roda** por OOM do WSL2 (exit 137); validação
  isolada cobriu 50 testes relacionados (T-EQP-009/012/016/017 + modelo
  + regressão RT) e zero regressão.

## Marco 1 `clientes` — FECHADO

P5 10 auditores Família 5 = ZERO CRÍTICO/ALTO/MÉDIO. Consolidado em
`docs/faseamento/M1-clientes/auditoria-familia5.md`. GATE-CLI-1..8
rastreados Wave A.

## Marco 2 `equipamentos` — em P4

- **P1+P2+P3**: spec forward (6 US + US-EQP-007, ~42 AC, 14 INVs) + plan
  com 4 reviews + matriz greenfield + 65 T-EQP-001..105 em 12 fases.
  Detalhes em `docs/faseamento/M2-equipamentos/`.
- **P4 T-EQP-001 ✅**: modelo `Equipamento` + migration RLS + 3 triggers PG
  (INV-EQP-001 snapshot imutável, anti-órfão LGPD, máquina 7 estados).
- **P4 T-EQP-006 ✅** (2026-05-21): SEC-QR-001 cravado — `QR_HMAC_KEY_REGISTRO`
  versionado prefixo `qrN:` + gate prod (chave dedicada ≥32, distinta de PII)
  + modelo `QRCode` (UNIQUE+RLS+trigger imutabilidade só `revogado_em` muta)
  + helper único `services_qr.py` + hook `qr-hmac-check.sh` (3 bloqueios) +
  18 regressão + SEC-QR-001 em `REGRAS-INEGOCIAVEIS.md`.
- **P4 T-EQP-002 ✅** (2026-05-21): etiqueta PDF — WeasyPrint 62.3+libpango/libcairo
  no Dockerfile + service `gerar_etiqueta_pdf` (60×40mm; TAG+NS+fabricante+
  nome_fantasia, sem PII) + `garantir_qrcode_vigente` idempotente consumindo
  T-EQP-006 + endpoint POST `/api/v1/equipamentos/{id}/etiqueta.pdf/` com
  Cache-Control private 60s + matriz authz (`equipamentos.ler` +
  `equipamentos.imprimir_etiqueta`) + 7 testes (happy + idempotência +
  cross-tenant 404 + authz 403 + anti-PII).
- **P4 T-EQP-003 ✅** (2026-05-22): `Idempotency-Key` em POST `/etiqueta.pdf/`
  (P-EQP-T6) — app horizontal F-A `src/infrastructure/idempotencia/`
  (modelo `ChaveIdempotencia` + UNIQUE (tenant,endpoint,chave) + RLS v2 +
  trigger imutabilidade pós-terminal) + `services_idempotencia.py` (sealed
  types + `breaker_writer` autocommit pra visibilidade imediata) +
  integração no `EquipamentoViewSet.etiqueta`: política 400 (ausente/
  inválido) / 425 (em_processo, `Retry-After: 1`) / 422 (payload divergente)
  / 409 (expirada >24h) / 200 (replay determinístico) + 8 testes
  `tests/test_equipamentos_etiqueta_idempotency_t_eqp_003.py`. Tabela
  reusável por US-EQP-002b/004/005/006.
- **P4 US-EQP-007 ✅** (2026-05-22): RT do tenant (P-EQP-R10 BLOQUEANTE
  RBC). App `src/infrastructure/responsavel_tecnico/` com 2 modelos
  (`ResponsavelTecnicoTenant` + `RTCompetencia`), migration `0001`
  com RLS v2 + extensão `btree_gist` + `EXCLUDE USING GIST` cravando
  INV-EQP-RT-001 (sem sobreposição temporal por tenant+grandeza) +
  trigger `rt_imutavel_pos_insert` (12 campos imutáveis, encerramento
  atômico em 4 campos). Services `cadastrar_rt`/`encerrar_rt`/`trocar_rt`/
  `declarar_competencia` publicam 4 ações no bus_outbox (`tenant.rt.{
  cadastrado,encerrado,trocado,competencia_declarada}`). Predicate
  `decisor_tem_competencia_para_atividade()` em `predicates.py` (Wave A
  usa em US-EQP-002b-6). Endpoints DRF: POST cadastrar/encerrar/trocar/
  competencias. 10 testes integrados + 3 anti-regressão T-EQP-094.
- **P4 T-EQP-039+041 ✅** (2026-05-23): US-EQP-004 fase 3 — consentimento
  histórico granular do cedente (P-EQP-R6). Enum
  `NivelConsentimentoHistorico` (3 valores: `nada`/`resumo`/`completo`)
  + modelo `ConsentimentoHistoricoEquipamento` (12 campos CORE
  imutáveis + 4 campos one-shot de revogação) + migration `0014`
  RLS v2 + trigger PG `consent_hist_imutavel_trg` (bloqueia mutação em
  campo CORE; bloqueia re-revogação one-shot) + `UNIQUE` parcial
  (`transferencia_origem` WHERE `revogado_em IS NULL`). Service
  `services_consentimento_historico` com `conceder` + `revogar` +
  helper `derivar_nivel_do_aceite_dump` (retrocompat com
  `consentimento_historico_expresso` bool legacy). Integração na
  efetivação de transferência: `solicitar_transferencia` chama
  `conceder_consentimento_historico` no MESMO bloco transacional,
  passando nível derivado de `aceite_cedente.nivel_consentimento_
  historico` (ou bool legacy). Validator
  `validar_justificativa_revogacao_consentimento` (≥30 chars + anti-PII
  reuso `conter_pii_direta`). 2 ações canônicas novas
  (`equipamento.consentimento_historico_concedido` /
  `_revogado`) — payload sanitizado com hashes HMAC tenant
  (justificativa cru e cedente_id cru NUNCA vazam). Endpoint POST
  `/api/v1/equipamentos/{id}/consentimento-historico/revogar/`
  (action no `EquipamentoViewSet`): 200 happy / 400 validação /
  404 inexistente / 412 já-revogado / 403 sem authz. Seed authz
  migration `0015` (`admin_tenant` + `tecnico`). 13/13 testes
  (3 níveis + payload sanitizado concedido + revogação happy +
  one-shot 412 + justificativa curta 400 + justificativa PII 400 +
  perfil sem authz 403 + 404 inexistente + payload sanitizado
  revogado + trigger PG mutação CORE + RLS cross-tenant). Sem
  regressão nos 24 testes T-EQP-034+037+038.
- **P4 T-EQP-037+038 ✅** (2026-05-22): US-EQP-004 fase 2 — Idempotency-Key
  no POST transferir + texto canônico do termo v1.1 com 4 cláusulas.
  T-EQP-037: integração `avaliar_chave_idempotencia` no endpoint (reusa
  horizontal F-A); política 400 ausente/inválido / 422 payload divergente
  / 200 replay determinístico (mesmo `transferencia_id`); `falhar_chave`
  em todos os erros 4xx/5xx. T-EQP-038: doc
  `docs/conformidade/equipamentos/transferencia-termo.md` v1.1-2026-05-22
  com 4 cláusulas pré-aprovadas advogado (LGPD art. 18 + Lei 14.063
  art. 4º/CP/CLT + não-cessão garantia/cert ISO 17025 cl. 8.4 +
  **NOVA v1.1 titularidade do dado pessoal não é cedida** LGPD art. 5º
  VI/VII); helper `validators.texto_termo_transferencia(versao)` +
  constante `TEXTO_TERMO_TRANSFERENCIA_VERSAO_CANONICA` + teste
  anti-drift Python↔frontmatter. 12 testes (4 idempotency + 8 termo).
- **P4 T-EQP-034+035+036+040 ✅** (2026-05-22): US-EQP-004 fase 1
  transferência fundação. Modelo `TransferenciaEquipamentoAceite` (3
  enums novos: `MotivoCategoriaTransferencia` 5 valores,
  `StatusTransferencia` 3, `ViaAceiteTransferencia` 3) +
  migration `0012` RLS v2. Service
  `services_transferencia.solicitar_transferencia`: efetiva
  imediatamente quando ambos aceites válidos (atualiza
  `Equipamento.cliente_atual_id` + publica `equipamento.transferido`),
  senão fica PENDENTE (Wave A: endpoint aceite tardio). INV-050
  cravado: `CessionarioCrossTenant("cliente nao encontrado neste
  tenant")` — 422 sem oracle. INV-INT-010: reuso `cliente_nao_bloqueado`
  Marco 1; cedente/cessionário bloqueado → 412 `lado=...`. Action
  canônica nova `equipamento.transferido` (payload sanitizado: hashes
  HMAC de cedente/cessionário, NUNCA UUIDs crus). Endpoint POST
  `/api/v1/equipamentos/{id}/transferir/` no `EquipamentoViewSet` +
  seed authz `equipamentos.transferir` em `migrations/0013`. **T-EQP-040
  PARCIAL** — 8 campos hoje vs 13 do P-EQP-A4 (motivo_detalhe_hash +
  aceite_origem/destino timestamps/vias + consentimento +
  causation_id) ficam `GATE-EQP-TRANSF-PAYLOAD-COMPLETO` Wave A.
  12/12 testes (happy + aceite parcial → pendente + INV-050 422 +
  INV-INT-010 cedente/cessionário 412 + 3 validações 400 + 403 +
  payload sanitizado + RLS cross-tenant + status efetivada).
- **P4 T-EQP-025+026+033 ✅** (2026-05-23): QR público 3 escopos +
  timing constant + 404 indistinguível. GET `/api/v1/qr/{hash}/` via
  `QRPublicoView(PublicEndpoint, APIView)` em `views_qr_publico.py`.
  Escopo A (autenticado + header `X-Afere-Active-Tenant` mesmo tenant) →
  200 ficha completa (reusa `construir_ficha_360`). Escopo B (outro
  tenant) → 404 body idêntico ao 404 de hash inválido (P-EQP-S2 — sem
  oracle cross-tenant). Escopo C (anônimo) → 200 allowlist mínima via
  função PG `resolver_qr_publico` SECURITY DEFINER (migration 0010 +
  patch 0011 com policy bypass `app.scope='qr_publico_check'` GUC
  local). Timing constant `aplicar_timing_constant_se_necessario`
  normaliza latência total para 200ms (`time.perf_counter` +
  `time.sleep`). URL registrada antes do router; middleware tenant
  ganhou `/api/v1/qr/` na PUBLIC_PATHS_PREFIX. 10/10 testes (3 escopos
  + 4 cenários 404 indistinguível + 2 timing sanity + anti-vaza
  tenant/cliente/tag/NS no payload anônimo).
- **P4 T-EQP-024+030+031 ✅** (2026-05-23): ficha 360° US-EQP-003 fase 1.
  GET `/api/v1/equipamentos/{id}/ficha360/?finalidade=<enum>` retorna
  dict com (a) equipamento base, (b) bloco
  `perfil_no_momento_do_cadastro` (P-EQP-R1 — snapshot + schema_version),
  (c) últimas 50 versões, (d) aprovações pendentes, (e)
  `certificados.tem_vigente` (porta stub), (f) últimos 50 eventos
  `Auditoria` filtrados por `payload_jsonb.equipamento_id` e sanitizados.
  INV-013 grava `AcessoDadosCliente` ANTES via `breaker_writer` (sobrevive
  rollback). Seed authz `equipamentos.ficha360` em
  `migrations/0009_seed_authz_ficha360.py` (admin_tenant + tecnico +
  rt_signatario). Service `services_ficha360.construir_ficha_360`
  agnóstico de HTTP. 9/9 testes (happy + bloco perfil + INV-013 +
  finalidade enum 2 + cross-tenant 404 + 403 + 401 + anti-PII).
  T-EQP-031 PARCIAL — alerta acesso massivo >500 fichas/h é
  `GATE-EQP-ACESSO-MASSIVO` (depende job + métrica Wave A).
- **P4 T-EQP-013 trigger PG + T-EQP-071 hook + módulo stub `certificados` ✅**
  (2026-05-23): GATE-EQP-INV025-TRIGGER fechado. App stub
  `src/infrastructure/certificados/` registrado no INSTALLED_APPS,
  modelo `Certificado` (id, tenant, equipamento, status, emitido_em,
  revogado_em, criado_em) com enum `StatusCertificado` (rascunho/
  emitido/revogado) + default manager `vigentes` (filtra status=emitido
  + revogado_em IS NULL). Migration `0001_initial` cria tabela + RLS
  v2 + **trigger PG `equipamento_imutabilidade_pos_cert_trg`** (BEFORE
  UPDATE em `equipamentos` consulta `certificados`; se cert vigente,
  bloqueia mutação em tag/numero_serie/fabricante com mensagem T1/T2/T3
  citando ISO/IEC 17025 cl. 8.4). Porta `query_service`:
  `tem_emitido(eq_id)` + `equipamentos_com_cert_vigente(ids)`. Hook
  `equipamento-imutabilidade-check.sh` (T-EQP-071) crava regra como
  código: bloqueia assignment `eq.tag = X` ou `.update(tag=)` sem
  consultar `tem_emitido`/`ImutabilidadePosCertificado`/`texto_rejeicao_422_pos_cert`;
  bloqueia mutação direta de `perfil_tenant_snapshot` via update; allow
  `services_perfil.py` (única via legítima D→A) + tests + migrations +
  override consciente. 14/14 testes do trigger + 13 casos no
  `_test-runner` (192/192 verdes).
- **P4 T-EQP-019 ✅** (2026-05-23): SLA workalendar + job de expiração.
  Dep nova `workalendar ^17.0.0` (MIT, sem CVE recente) em `pyproject.toml`.
  `services_aprovacao.calcular_sla_vencimento(tem_cert_vigente, base)`
  usa `workalendar.america.Brazil` — dias úteis BR incluindo feriados
  móveis Carnaval+Corpus Christi (D+3 sem cert / D+7 com cert).
  `expirar_aprovacoes_vencidas(tenant_id)` itera PENDENTEs vencidas e
  chama `expirar`. Management command
  `processar_aprovacoes_expiradas_equipamento` itera multi-tenant.
  PARCIAL: faltam pausa SLA + alerta D-1 + extensão estadual +
  agendamento Procrastinate (Wave A). 8/8 testes em 4.9s.
- **P4 T-EQP-018+020+021+022 ✅** (2026-05-23): fundação **US-EQP-002b**
  (aprovação gestor_qualidade) — modelo `AprovacaoPendenteEquipamentoVersao`
  (16 campos), enum `StatusAprovacaoVersao` 4 valores, constante
  `STATUS_TERMINAIS_APROVACAO`. Migration `0008_aprovacaopendenteequipamentoversao`
  com RLS v2 + CHECK `ck_aprovacao_solicitante_neq_decisor` (INV-EQP-002
  ISO 17025 cl. 6.2 segregação) + trigger PG
  `aprovacao_versao_anti_mutacao_terminal_trg` (bloqueia mutação em 12
  campos quando status terminal). Service `services_aprovacao.py` com
  `solicitar_aprovacao`/`aprovar`/`rejeitar`/`expirar`; 3 camadas defesa
  INV-EQP-002 (CHECK PG + clean() modelo + assert service). Validator
  `validar_parecer_gestor_texto` (>=30 chars + anti-PII reuso de
  `conter_pii_direta`). 3 ações canônicas novas registradas
  (`equipamento.versao_aprovada/rejeitada/expirada`) com payload
  sanitizado (HMAC de parecer/IDs). Predicate
  `decisor_tem_competencia_para_atividade` já existia (US-EQP-007).
  T-EQP-019 (workalendar SLA D+3/D+7 + job Procrastinate) pendente —
  placeholder dias-corridos no service. T-EQP-021 admin Django (UI)
  fica Wave A. 11/11 testes em 3.5s.
- **P4 T-EQP-013 ✅ doc + helper** (2026-05-23): doc
  `docs/conformidade/equipamentos/textos-rejeicao-422.md` v1.0.0 com 5
  textos canônicos pré-aprovados pelo `advogado-saas-regulado` (T1 TAG,
  T2 NS, T3 fabricante, T4 fallback genérico, T5 delete de versão);
  helper `validators.texto_rejeicao_422_pos_cert(campo)` retorna texto
  canônico (lista FECHADA — não compõe inline, não passa por LLM). Teste
  anti-drift garante constante `TEXTOS_REJEICAO_422_VERSAO_CANONICA`
  sincronizada com frontmatter do doc. 7/7 testes. **GATE-EQP-INV025-TRIGGER
  Wave A**: trigger PG depende de módulo `certificados` existir.
- **P4 T-EQP-017 ✅** (2026-05-23): service `services_versao.criar_versao_equipamento`
  orquestra INSERT + publica `equipamento.versao_criada` (ação canônica
  nova) com payload sanitizado. Whitelist FECHADA `CAMPOS_PAYLOAD_PERMITIDOS`
  (14 campos: 5 básicos + 9 derivados/hashes) + blacklist explícita
  `CAMPOS_PAYLOAD_PROIBIDOS` (7 campos). Helper `_validar_payload_anti_vaza`
  levanta `PayloadVazandoPII` se aparecer `motivo_detalhe` cru,
  `valor_anterior`/`valor_novo` cru, `cliente_atual_id` cru,
  `assinatura_a3_hash` truncado (P-EQP-T5), `numero_serie` cru, ou campo
  fora da whitelist. `valor_anterior`/`valor_novo` passam por HMAC
  ANTES de entrar no modelo. 11/11 testes em 8.0s.
- **P4 T-EQP-012 + T-EQP-016 ✅** (2026-05-23): modelo `EquipamentoVersao`
  (US-EQP-002 fundação) — 14 campos, enum `MotivoMudancaEquipamentoVersao`
  9 valores (P-EQP-R2), constante `MOTIVOS_QUE_OBRIGAM_APROVACAO` (3 que
  disparam US-EQP-002b: `outros` + `substituicao_componente_critico` +
  `atualizacao_firmware`). Migration `0007_equipamentoversao.py` com RLS
  pattern v2 (4 policies SELECT/UPDATE/DELETE/INSERT) + CHECK
  `ck_eqp_versao_a3_all_or_nothing` (P-EQP-T5: A3 referência+assinada_em+
  certificado_emissor_hash all-or-nothing — proíbe referência sozinha).
  INSERT-only em Python via `save()`/`delete()` (trigger PG INV-025 fica
  T-EQP-013 quando módulo certificados existir). `validators.validar_motivo_detalhe`
  cravado em `clean()` (anti-PII via `conter_pii_direta` + ≥100 chars
  quando motivo obriga aprovação). 13/13 testes (1 happy + enum 9 +
  motivos obrigatórios + 3 PII: CPF/email/nome + curta + opcional vazio
  + RLS cross-tenant + INSERT-only save + INSERT-only delete + CHECK A3
  sozinha falha + CHECK A3 NULL OK).
- **P4 T-EQP-009 ✅** (2026-05-23): função PG SECURITY DEFINER
  `promover_perfil_equipamento_snapshot(uuid, text, uuid, text, uuid,
  uuid)` em migration `0006_promover_perfil_funcao.py` — direção
  D<C<B<A monotônica crescente (downgrade e mesmo perfil bloqueados;
  D não é destino), evidência+RT+decisor obrigatórios, justificativa
  ≥100 chars no PG + anti-PII regex no Python (defesa em profundidade),
  re-aplica isolamento `tenant_id == app.active_tenant_id` (SECURITY
  DEFINER não pode virar bypass), libera trigger imutabilidade via
  `SET LOCAL app.perfil_promocao_permitida='1'` apenas durante UPDATE,
  zera de volta no fim. GRANT EXECUTE TO app_user. Service
  `services_perfil.promover_perfil_equipamento` publica
  `equipamento.perfil_promovido` (ação canônica nova; 25a WORM RBC)
  com payload sanitizado (`justificativa_hash` HMAC tenant — texto cru
  NUNCA vaza). NÃO cria `EquipamentoVersao` ainda (T-EQP-012 estende).
  15 testes (3 happy: D→A salto, D→C minímo, D→C→B; 5 direção inválida:
  downgrade A→B, mesmo perfil C→C, destino D, destino X; 2 args
  obrigatórios: evidência, rt_id; 2 justificativa PII: <100 chars, CPF,
  email; cross-tenant; regressão INV-EQP-001 UPDATE direto pós-promoção;
  evento publicado em cadeia). 15/15 PASS em 4.8s.
- **P4 T-EQP-005+007 ✅** (2026-05-22): CRUD POST do Equipamento.
  `validators.py` com `conter_pii_direta()` (regex CPF/CNPJ/email/
  telefone/≥2 nomes próprios) + `EquipamentoCriarSerializer` aplica
  INV-EQP-LOC-001 → 400. `services_equipamento.criar_equipamento`
  publica `equipamento.criado` no bus_outbox com payload sanitizado
  (tag_hash + numero_serie_hash + cliente_atual_id_hash — TAG cru
  NUNCA vaza). `EquipamentoViewSet.create` exige `Idempotency-Key`
  (P-EQP-T6) + authz `equipamentos.criar` (admin_tenant + tecnico via
  migration `0005_seed_authz_criar`). TAG duplicada → 409 com link
  pro existente. 12 testes (happy + 409 + 5 cenários INV-EQP-LOC-001 +
  idempotência + 400 sem header + authz).

## Próximo passo

1. **US-EQP-003 fase 3** (T-EQP-027+029+032): rate-limit 60req/min IP
   (Redis) + filtro histórico no `construir_ficha_360` baseado em
   `ConsentimentoHistoricoEquipamento` (cessionário pós-transferência
   sem consentimento `completo`/`resumo` NÃO vê histórico — agora
   destravado pelo modelo de T-EQP-039) + rate-limit global por tenant.
2. **US-EQP-003 fase 4** (T-EQP-028): PWA scanner.
3. **US-EQP-005 sucatamento** + **US-EQP-006 recebimento**.
4. Sequência em `docs/faseamento/M2-equipamentos/tasks.md`.

## Pendências rastreadas (não bloqueiam)

- ADR-0018 (PWA scanner QR) — aguardando aceite Roldão antes de US-EQP-003.
- ADR-0019 Pilar 2 — apólice cyber+E&O pré-1º tenant externo pago.
- GATE-EQP-1..PENTEST (14 itens Wave A — `docs/faseamento/M2-equipamentos/plan.md`).
