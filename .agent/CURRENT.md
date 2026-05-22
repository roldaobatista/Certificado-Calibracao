# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** Marco 1 **FECHADO** + Marco 2 `equipamentos` em P4 (T-EQP-001
+ 006 + 002 + 003 + US-EQP-007 + T-EQP-005 + T-EQP-007 + T-EQP-009 +
T-EQP-012 + T-EQP-016 + T-EQP-017 + T-EQP-013 doc+helper +
T-EQP-018+020+021+022 US-EQP-002b + T-EQP-019 SLA+job +
T-EQP-013 trigger PG + T-EQP-071 hook + módulo stub `certificados` +
**T-EQP-024+030+031 ficha 360°** entregues; GATE-EQP-INV025-TRIGGER
FECHADO).
**Sessão em curso 2026-05-23** (US-EQP-003 ficha 360° fase 1).
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
- modelo_001 (regressão): **8/8 passed**
- inv_eqp_rt_001 (regressão): **3/3 passed**
- Hooks: **179/179** verdes (22 ativos — sem hook novo nesta T)
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

1. **US-EQP-003 fase 2** (T-EQP-025+026+033): GET `/v1/qr/{hash}` 3
   escopos A/B/C (autenticado-mesmo-tenant / autenticado-outro-tenant /
   anônimo) + timing constant `time.perf_counter` ±5ms + Escopo B 404
   indistinguível.
2. **US-EQP-003 fase 3** (T-EQP-027+029+032): rate-limit 60req/min IP
   + cessionário pós-transferência sem consentimento + rate-limit
   global por tenant.
3. **US-EQP-003 fase 4** (T-EQP-028): PWA scanner `/scan/`
   (BarcodeDetector + jsQR fallback + SW).
4. **US-EQP-004 transferir** (T-EQP-034..041): POST `/transferir/` +
   3 vias aceite + Idempotency-Key + consentimento histórico granular.
5. **US-EQP-005 sucatamento** + **US-EQP-006 recebimento**.
6. Sequência em `docs/faseamento/M2-equipamentos/tasks.md`.

## Pendências rastreadas (não bloqueiam)

- ADR-0018 (PWA scanner QR) — aguardando aceite Roldão antes de US-EQP-003.
- ADR-0019 Pilar 2 — apólice cyber+E&O pré-1º tenant externo pago.
- GATE-EQP-1..PENTEST (14 itens Wave A — `docs/faseamento/M2-equipamentos/plan.md`).
