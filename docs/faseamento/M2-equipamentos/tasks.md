---
owner: roldao
revisado_em: 2026-05-21
proximo_review: 2026-08-21
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 2 — equipamentos
tipo: matriz-spec-codigo + tarefas-causa-raiz
relacionados:
  - docs/faseamento/M2-equipamentos/spec.md
  - docs/faseamento/M2-equipamentos/plan.md
  - docs/faseamento/M1-clientes/tasks.md
---

# Marco 2 (equipamentos) — Matriz P3 + Tarefas P4 (causa-raiz)

> **P3 (matriz):** Marco 2 é **greenfield** — zero código no módulo
> `equipamentos`. Todos os AC viram GAP → T-EQP-NNN em P4. Esta é a
> diferença estrutural vs Marco 1 (que tinha código pré-existente).
> **P4 (causa-raiz):** cada T-EQP-NNN resolve raiz, nunca mascara
> (Constituição §6). Severidade MÉDIO+ no fechamento bloqueia
> (INV-RITUAL-001).

## Matriz P3 — Estado dos AC binários

Convenção:
- **GAP** → vira T-EQP-NNN em P4 (causa-raiz, bloqueia fechamento).
- **TRACK** → GATE-EQP-N Wave A (não bloqueia Marco 2 dogfooding).
- **OK** → herdado de F-A/F-B/Marco 1 (não precisa código novo).

### US-EQP-001 — Cadastrar equipamento com QR Code

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-001-1 | GAP | T-EQP-001 (modelo `Equipamento` + migration RLS + viewset POST) |
| AC-EQP-001-2 | **OK** | T-EQP-002 ✅ FECHADO 2026-05-21: WeasyPrint 62.3 + libpango/libcairo no `Dockerfile` (TL1 tech-lead) + `services_etiqueta.py` (`garantir_qrcode_vigente` idempotente + `gerar_etiqueta_pdf` 60×40mm) + template `templates/equipamentos/etiqueta_qr.html` (TAG+NS+fabricante+modelo+nome_fantasia, sem PII cliente) + `EquipamentoViewSet` action `etiqueta` (POST `/api/v1/equipamentos/{id}/etiqueta.pdf/`) + seed authz `equipamentos.ler`/`equipamentos.imprimir_etiqueta` (migration 0004) + 7 testes T-EQP-002 (happy + idempotência + cross-tenant 404 + authz 403 + anti-PII). Cache `private, max-age=60`. Suite 510 passed. |
| AC-EQP-001-2b | **OK** | T-EQP-003 ✅ FECHADO 2026-05-21: app horizontal `src/infrastructure/idempotencia/` (modelo `ChaveIdempotencia` + migration `0001_initial` com UNIQUE composto (tenant,endpoint,chave) + RLS pattern v2 + trigger `chave_idempotencia_imutavel_pos_terminal` bloqueando UPDATE pós `concluida`/`falhada`). `services_idempotencia.py` com `avaliar_chave_idempotencia()` (sealed types ErroValidacao/Replay/NovoProcessamento) + `concluir_chave()`/`falhar_chave()` via conexão `breaker_writer` autocommit (visibilidade imediata pra concorrência). `EquipamentoViewSet.etiqueta` integra: header `Idempotency-Key` UUID → política 400 (ausente/inválido) / 425 (em_processo, `Retry-After: 1`) / 422 (payload divergente) / 409 (expirada >24h) / 200 (replay re-renderiza idempotente via `garantir_qrcode_vigente`). 8 testes em `tests/test_equipamentos_etiqueta_idempotency_t_eqp_003.py` (header obrigatório + chave nova + replay + 422 + 409 + 425 + cross-tenant). |
| AC-EQP-001-3 | **OK** | T-EQP-004 ✅ FECHADO 2026-05-21 junto com T-EQP-001: `Equipamento.Meta.constraints` tem `UniqueConstraint(fields=['tenant','tag'], condition=Q(deletado_em__isnull=True), name='uq_equipamentos_tag_por_tenant_ativos')` — INV-049 cravada como UNIQUE parcial. Endpoint POST com mensagem 409 explícita ainda depende de T-EQP-005 (CRUD pleno). |
| AC-EQP-001-4 | **OK** | T-EQP-005 ✅ FECHADO 2026-05-22: `src/infrastructure/equipamentos/validators.py` com `conter_pii_direta()` + `validar_localizacao_fisica()` (regex CPF/CNPJ/email/telefone/≥2 nomes próprios consecutivos). `EquipamentoCriarSerializer.validate_localizacao_fisica` aplica anti-PII → 400 com texto canônico `LGPD art. 5º I + INV-EQP-LOC-001`. `EquipamentoViewSet.create` (POST `/api/v1/equipamentos/`) exige `Idempotency-Key` (P-EQP-T6) + autorização `equipamentos.criar` (seed migration `0005_seed_authz_criar` → admin_tenant + tecnico). TAG duplicada → 409 `tag_duplicada` com `equipamento_existente_id`. 12 testes. |
| AC-EQP-001-5 | **OK** | T-EQP-006 ✅ FECHADO 2026-05-21: `QR_HMAC_KEY_REGISTRO` em `config/settings/base.py` (reuso `_RegistroChavesPII` com prefixo `qrN:`) + helper único `src/infrastructure/equipamentos/services_qr.py` + modelo `QRCode` com UNIQUE+RLS+trigger imutabilidade em migration `0003_qrcode.py` + hook `qr-hmac-check.sh` (11 casos no `_test-runner`) + 18 testes em `tests/regressao/test_sec_qr_001_hmac_versionado.py` + entrada `SEC-QR-001` registrada em `REGRAS-INEGOCIAVEIS.md`. Suite 503 passed. |
| AC-EQP-001-6 | **OK** | T-EQP-007 ✅ FECHADO 2026-05-22: `criar_equipamento` em `services_equipamento.py` publica `equipamento.criado` (ação canônica em `acoes_canonicas.ACOES_EQUIPAMENTOS`) via `publicar_evento(outbox=True)`. Payload sanitizado: tenant_id, equipamento_id, tag_hash (HMAC versionado), numero_serie_hash, cliente_atual_id_hash, snapshot_schema_version, criado_em. NUNCA vaza TAG/NS crus (validado em `test_evento_publicado_nao_vaza_tag_crua`). |
| AC-EQP-001-7 | **OK** | T-EQP-008 ✅ FECHADO 2026-05-21 junto com T-EQP-001: `perfil_tenant_snapshot JSONField` em `Equipamento.models` + trigger PG `equipamento_perfil_snapshot_imutavel` na migration `0002_rls_policies_e_triggers.py` (INV-EQP-001 cravada — UPDATE bloqueado). |
| AC-EQP-001-7b | **OK** | T-EQP-009 ✅ FECHADO 2026-05-22: função PG `promover_perfil_equipamento_snapshot(uuid, text, uuid, text, uuid, uuid)` em migration `0006_promover_perfil_funcao.py` — `SECURITY DEFINER` re-aplica isolamento (`tenant_id == app.active_tenant_id`); direção D<C<B<A monotônica crescente (downgrade e mesmo perfil bloqueados; D não é destino); evidência+RT+decisor obrigatórios; justificativa ≥100 chars (PG) + anti-PII regex em Python via `services_perfil.promover_perfil_equipamento` (defesa em profundidade); libera trigger `equipamento_perfil_tenant_imutavel_trg` via `SET LOCAL app.perfil_promocao_permitida='1'` apenas durante o UPDATE. Service publica `equipamento.perfil_promovido` (ação canônica adicionada em `acoes_canonicas.py`; 25a WORM RBC) com payload sanitizado (justificativa_hash via HMAC tenant, NUNCA texto cru). NÃO cria `EquipamentoVersao` ainda — T-EQP-012 estende a função para INSERT em `equipamentos_versao` com `motivo_mudanca=mudanca_classe_metrologica`. 12 testes em `tests/test_equipamentos_promover_perfil_t_eqp_009.py` (3 happy + 5 direção inválida + 2 obrigatórios + 2 justificativa PII + cross-tenant + regressão INV-EQP-001 + evento). |
| AC-EQP-001-8 | **OK** | T-EQP-010 ✅ FECHADO 2026-05-21 junto com T-EQP-001: `cliente_atual = ForeignKey(Cliente, on_delete=SET_NULL, null=True, db_constraint=False)` + trigger `equipamento_anti_orfao_imediato` na migration `0002` (status passa a `orfao_pendente_decisao` quando cliente é eliminado — P-EQP-T9). `db_constraint=False` igual `ClienteIdentidadeHistorico` (Marco 1): evita validação FK passando por RLS na criação; integridade real via trigger PG. |
| AC-EQP-001-8b | **OK** | T-EQP-011 ✅ FECHADO 2026-05-21 junto com T-EQP-001: `Equipamento` tem `snapshot_schema_version CharField` + `perfil_tenant_snapshot JSONField` com helper de validação. Spec P-EQP-R1 lista 7 campos mínimos do snapshot — validador semântico do payload fica em camada de aplicação (Wave A enforce). Modelo + trigger imutabilidade já existem. |
| AC-EQP-001-9 | TRACK | GATE-EQP-S1 (evidência operacional 90d QR HMAC — Wave A) |

### US-EQP-002 — Editar equipamento com versionamento pós-emissão

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-002-1 | **OK** | T-EQP-012 ✅ FECHADO 2026-05-23: modelo `EquipamentoVersao` em `src/infrastructure/equipamentos/models.py` com 14 campos (id, tenant, equipamento, campo, valor_anterior_hash, valor_novo_hash, motivo_mudanca, motivo_detalhe, snapshot_jsonb, cliente_atual_id_no_momento, criado_por, assinatura_a3_referencia/assinada_em/certificado_emissor_hash, criado_em) + enum `MotivoMudancaEquipamentoVersao` 9 valores (P-EQP-R2: + `ajuste_pos_calibracao` + `substituicao_componente_critico` + `atualizacao_firmware`) + constante `MOTIVOS_QUE_OBRIGAM_APROVACAO` frozenset. Migration `0007_equipamentoversao.py` com RLS pattern v2 (4 policies SELECT/UPDATE/DELETE/INSERT) + CHECK `ck_eqp_versao_a3_all_or_nothing` (P-EQP-T5 — A3 referência+assinada_em+certificado_emissor_hash all-or-nothing). INSERT-only em Python (save() e delete() levantam RuntimeError; trigger PG fica T-EQP-013 quando módulo certificados existir). 13/13 testes passed. |
| AC-EQP-002-2 | **OK** | T-EQP-013 ✅ FECHADO 2026-05-23 (completo): doc `textos-rejeicao-422.md` v1.0.0 (5 textos T1-T5 advogado) + helper Python + **trigger PG real** `equipamento_imutabilidade_pos_cert_trg` em `certificados/migrations/0001_initial.py` (BEFORE UPDATE em `equipamentos` consulta tabela `certificados` — bloqueia mutação em tag/numero_serie/fabricante quando cert vigente; emite mensagem com chave T1/T2/T3) + módulo stub `certificados` (modelo `Certificado` + porta `query_service.tem_emitido`/`equipamentos_com_cert_vigente`) + hook `equipamento-imutabilidade-check.sh` (T-EQP-071) cravando regra como código (13 casos no `_test-runner`). 14/14 testes do trigger + 7/7 do helper. GATE-EQP-INV025-TRIGGER **fechado**. Wave A expandirá o modelo `certificados` (emissão A3, PDF, RBC, NIT-DICLA) sem migration destrutiva. |
| AC-EQP-002-3 | TRACK | GATE-EQP-1 (A3 RT cliente-side via Lacuna — Wave A); endpoint contrato em T-EQP-014 |
| AC-EQP-002-4 | GAP | T-EQP-015 (motivo=`outros`/`substituicao_componente`/`atualizacao_firmware` exige aprovação — P-EQP-R2) |
| AC-EQP-002-5 | **OK** | T-EQP-016 ✅ FECHADO 2026-05-23 junto com T-EQP-012: `validators.validar_motivo_detalhe` (anti-PII via reuso `conter_pii_direta` + ≥100 chars quando motivo ∈ MOTIVOS_QUE_OBRIGAM_APROVACAO). Aplicado no `clean()` do modelo → `ValidationError`. 4 testes anti-PII (CPF, email, nome próprio consecutivo, justificativa curta). |
| AC-EQP-002-6 | **OK** | T-EQP-017 ✅ FECHADO 2026-05-23: service `services_versao.criar_versao_equipamento` orquestra INSERT + publica `equipamento.versao_criada` (ação canônica nova em `acoes_canonicas.py`) com payload sanitizado. `CAMPOS_PAYLOAD_PERMITIDOS` (whitelist FECHADA, 14 campos: 5 básicos + 9 derivados/hashes incluindo `assinatura_a3_referencia` UUID + `assinatura_a3_certificado_emissor_hash`) + `CAMPOS_PAYLOAD_PROIBIDOS` (lista negativa explícita, 7 campos). Helper `_validar_payload_anti_vaza` bloqueia `motivo_detalhe` cru, `valor_anterior`/`valor_novo` cru, `cliente_atual_id` cru, `assinatura_a3_hash` truncado (P-EQP-T5), `numero_serie` cru, ou campo fora da whitelist. `valor_anterior`/`valor_novo` passam por HMAC do tenant ANTES de serem gravados — modelo nunca enxerga valor cru. 11/11 testes (happy + payload conforma whitelist + 3 não-vaza-cru + 4 assert anti-vaza + cross-tenant defesa em profundidade). |

### US-EQP-002b — Aprovação gestor_qualidade

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-002b-1 | **OK** | T-EQP-018 ✅ FECHADO 2026-05-23: modelo `AprovacaoPendenteEquipamentoVersao` (16 campos) em `models.py` + enum `StatusAprovacaoVersao` (4: pendente/aprovada/rejeitada/expirada) + constante `STATUS_TERMINAIS_APROVACAO`. Migration `0008` com RLS pattern v2 + trigger PG `aprovacao_versao_anti_mutacao_terminal_trg` (BEFORE UPDATE bloqueia mutação em 12 campos quando `OLD.status ∈ {aprovada,rejeitada,expirada}`). |
| AC-EQP-002b-2 | **PARCIAL** | T-EQP-019 ✅ SLA + job FECHADO 2026-05-23: `services_aprovacao.calcular_sla_vencimento(tem_cert_vigente, base)` usando `workalendar.america.Brazil` (D+3 sem cert / D+7 com cert; dias úteis BR incluindo feriados móveis Carnaval+Corpus Christi). Dep `workalendar ^17.0.0` em `pyproject.toml` (MIT, sem CVE recente). `expirar_aprovacoes_vencidas(tenant_id)` itera PENDENTEs com `sla_vencimento <= now()` e chama `expirar`. Management command `processar_aprovacoes_expiradas_equipamento` (multi-tenant). 8/8 testes. **PARCIAL pois faltam**: pausa SLA (`sla_pausado_em`/`sla_retomado_em` + enum status `pausada_aguardando_cliente`) + alerta D-1 (Procrastinate Wave A) + extensão estadual (subclass `BrazilSaoPaulo`/etc quando tenant tiver UF) + agendamento Procrastinate diário 03:00 BRT (atualmente roda manualmente ou via cron externo). |
| AC-EQP-002b-3 | **OK** | T-EQP-020 ✅ FECHADO 2026-05-23: CHECK `ck_aprovacao_solicitante_neq_decisor` na Meta.constraints (`~Q(solicitante=F('decisor'))`) + validação no `clean()` do modelo + assert no `services_aprovacao._decidir` (3 camadas — defesa em profundidade ISO 17025 cl. 6.2). |
| AC-EQP-002b-4 | **OK** (sem admin) | T-EQP-021 ✅ FECHADO 2026-05-23 (validator parte): `validators.validar_parecer_gestor_texto` (>=30 chars + anti-PII via `conter_pii_direta`). Aplicado no `clean()` quando status=APROVADA/REJEITADA. Django admin (UI) fica Wave A com restante de telas. |
| AC-EQP-002b-5 | **OK** | T-EQP-022 ✅ FECHADO 2026-05-23: services `aprovar`/`rejeitar`/`expirar` publicam 3 ações canônicas novas (`equipamento.versao_aprovada/rejeitada/expirada`) registradas em `acoes_canonicas.ACOES_EQUIPAMENTOS` com payload sanitizado (hashes HMAC do tenant para parecer/IDs; lista positiva implícita — não vaza texto cru). |
| AC-EQP-002b-6 | **OK** | T-EQP-023 ✅ FECHADO 2026-05-22 junto com US-EQP-007: `predicates.decisor_tem_competencia_para_atividade` em `responsavel_tecnico/predicates.py`. |

### US-EQP-003 — Ficha 360° + scan QR + PWA

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-003-1 | **OK** | T-EQP-024 ✅ FECHADO 2026-05-23: GET `/api/v1/equipamentos/{id}/ficha360/?finalidade=<enum>` retorna dict com equipamento + perfil_no_momento_do_cadastro (P-EQP-R1) + versoes + aprovacoes_pendentes + certificados.tem_vigente (porta stub) + eventos (Auditoria filtrada por payload_jsonb.equipamento_id, ultimos 50, payload sanitizado). INV-013 grava `AcessoDadosCliente` ANTES via `registrar_acesso_dados_cliente_com_breaker` (sobrevive a rollback). Service `services_ficha360.construir_ficha_360` agnostico de HTTP. Seed authz `equipamentos.ficha360` em `migrations/0009` (admin_tenant + tecnico + rt_signatario). 9/9 testes (happy + bloco perfil + INV-013 + finalidade enum 2 casos + cross-tenant 404 + authz 403 + unauth + anti-PII). |
| AC-EQP-003-2 | **OK** | T-EQP-025 ✅ FECHADO 2026-05-23: GET `/api/v1/qr/{hash}/` `QRPublicoView(PublicEndpoint, APIView)` em `views_qr_publico.py`. Escopo A: usuário autenticado + header `X-Afere-Active-Tenant` → resolve via `verificar_qr_hash_em_tabela` em `run_in_tenant_context`; mesmo tenant → 200 ficha completa; outro tenant ou hash inválido → 404 indistinguível. Escopo C anônimo: chama função PG `resolver_qr_publico` SECURITY DEFINER (migration 0010 + 0011 patch) com policy `equipamentos_qrcode_publico_resolver` ativada via `app.scope='qr_publico_check'` GUC local — devolve allowlist mínima (tipo/fabricante/modelo/status/mensagem/url institucional). URL `/api/v1/qr/<path:hash>/` registrada antes do router; middleware tenant ganhou `/api/v1/qr/` na PUBLIC_PATHS_PREFIX. |
| AC-EQP-003-3 | **PARCIAL** | T-EQP-026 ✅ timing constant FECHADO 2026-05-23: `services_qr_publico.aplicar_timing_constant_se_necessario(inicio, alvo=200ms)` mede via `time.perf_counter()` e dorme até alvo. View chama no 200 e 404 (todos caminhos). Teste sanity (`test_timing_constant_404_proximo_de_alvo` + `test_timing_404_e_200_anonimo_similares`) valida normalização. **Pendente Wave A**: fuzzing Mann-Whitney 1000 amostras p>0.05 (GATE-EQP-PENTEST). |
| AC-EQP-003-4 | **OK** | T-EQP-027 ✅ FECHADO 2026-05-23: service `services_ratelimit` com `avaliar_limite_ip` (60 req/min) + `registrar_4xx_ip` (>=100 4xx/h dispara lockout 24h). Backing `caches['ratelimit']` (Redis DB 2 prod, LocMem em test). Integrado no `QRPublicoView.get` ANTES de qualquer resolução de hash (anti-oráculo). 429 com `Retry-After`. `_publicar_lockout_disparado` publica ação canônica nova `sistema.qr_lockout_disparado` em `run_as_system` (payload: ip_hash HMAC salt global, contagem_4xx, limite, lockout_ate_unix). Helper `_hash_ip_simples` HMAC salt GLOBAL (não por tenant — escopo trans-tenant; override audit-pii-salt justificado). |
| AC-EQP-003-5 | GAP | T-EQP-028 (PWA `BarcodeDetector` + jsQR fallback + SW `/scan/sw.js` + filtro QR-only — P-EQP-T8) |
| AC-EQP-003-6 | **OK** | T-EQP-029 ✅ FECHADO 2026-05-23: `_avaliar_filtro_historico_cessionario` em `services_ficha360.py` consulta `TransferenciaEquipamentoAceite` EFETIVADA + `ConsentimentoHistoricoEquipamento` vigente. Cessionário sem consentimento (nível `nada`) → versões/eventos pré-corte (`transferencia.efetivada_em`) ocultos no payload + flag `aviso_historico_filtrado.ativo=True` com banner canônico "Histórico preservado e confidencial conforme RBC ISO/IEC 17025 cl. 4.2". `completo` mostra tudo; `sem_filtro` (sem transferência ou cliente original) sem banner. Nível `resumo` STUB Marco 2 (equivale a `nada` aqui; Wave A expande com bloco agregado). |
| AC-EQP-003-7 | **OK** | T-EQP-030 ✅ FECHADO 2026-05-23 junto com T-EQP-024: bloco `perfil_no_momento_do_cadastro` cravado em `services_ficha360.construir_ficha_360` retornando `{snapshot: equipamento.perfil_tenant_snapshot, snapshot_schema_version: equipamento.snapshot_schema_version}`. Mesmo após `promover_perfil_equipamento_snapshot` (T-EQP-009), a ficha refletirá o snapshot ATUAL — Wave A introduzirá histórico explícito de promoções quando necessário. |
| AC-EQP-003-8 | **PARCIAL** | T-EQP-031 ✅ enum FECHADO 2026-05-23: `?finalidade=<enum>` reusa `FinalidadeAcessoCliente` (9 valores; equipamento mantém alinhamento com cliente — gravado em `AcessoDadosCliente.finalidade`). Helper `services_ficha360.descrever_finalidade` para UI. Validação no viewset (400 se ausente/inválido). **Pendente Wave A**: alerta P2 acesso massivo >500 fichas/h por usuário (depende job + métrica observabilidade — fica `GATE-EQP-ACESSO-MASSIVO`). |
| AC-EQP-003-9 | **OK** | T-EQP-032 ✅ FECHADO 2026-05-23: `avaliar_limite_tenant_qr(tenant_id, n_equipamentos_ativos)` → limite `100 × n_equip`/dia em `/v1/qr/*` cross-tenant ou anônimo. Integrado no `QRPublicoView` para Escopo A (após resolver tenant do QR) + Escopo C (anônimo — tenant via nova função SECURITY DEFINER `resolver_qr_publico_tenant_id` migration `0016` usando mesma policy `app.scope='qr_publico_check'` do migration 0011; tenant_id NÃO vaza no payload público). Excesso publica ação canônica nova `sistema.qr_scraping_suspeito` em `run_as_system` 1 vez por dia por tenant (idempotência via `cache.add` na chave `qr:tnt:scraping:{uuid}:{dia}`). Helper `_contar_equipamentos_ativos_tenant` com cache 5min para reduzir round-trip. |
| AC-EQP-003-10 | **OK** | T-EQP-033 ✅ FECHADO 2026-05-23 junto com T-EQP-025: Escopo B (autenticado outro tenant) cai no ramo `if qrcode is None` retornando `_resposta_404_indistinguivel` com mesmo body `{"detail":"qr_nao_encontrado"}` que hash inválido (P-EQP-S2 — sem oracle cross-tenant). Teste `test_escopo_b_autenticado_outro_tenant_retorna_404` valida assert sobre body igual ao 404 de hash inválido. |

### US-EQP-004 — Transferir equipamento

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-004-1 | **OK** | T-EQP-034 ✅ FECHADO 2026-05-23: modelo `TransferenciaEquipamentoAceite` (3 enums: `MotivoCategoriaTransferencia` 5, `StatusTransferencia` 3, `ViaAceiteTransferencia` 3) + migration `0012` RLS v2 + endpoint POST `/api/v1/equipamentos/{id}/transferir/`. Service `services_transferencia.solicitar_transferencia`: efetiva imediatamente quando ambos aceites válidos no payload (atualiza `Equipamento.cliente_atual_id` + publica `equipamento.transferido`); senão fica PENDENTE (Wave A: endpoint aceite tardio). Seed authz `equipamentos.transferir` em `migrations/0013` (admin_tenant + tecnico). |
| AC-EQP-004-2 | **OK** | T-EQP-035 ✅ FECHADO 2026-05-23 junto com T-EQP-034: cessionário cross-tenant → `CessionarioCrossTenant("cliente nao encontrado neste tenant")` → 422 com mensagem genérica (sem oracle). RLS filter na consulta de `Cliente.objects.filter(id=cessionario_id)` + service compara `tenant_id` (defesa em profundidade). |
| AC-EQP-004-3 | **OK** | T-EQP-036 ✅ FECHADO 2026-05-23 junto com T-EQP-034: reuso `clientes.predicates_authz.cliente_nao_bloqueado` Marco 1. Cedente bloqueado → 412 `lado=cedente`; cessionário bloqueado → 412 `lado=cessionario`; motivo estável (`cliente_bloqueado_inadimplencia`/`cliente_bloqueado_manual`). |
| AC-EQP-004-4 | **OK** | T-EQP-037 ✅ FECHADO 2026-05-22: `Idempotency-Key` integrado no POST `/transferir/` reusando horizontal F-A `idempotencia.avaliar_chave_idempotencia`. Política 400 (ausente/inválido) / 422 (payload divergente) / 200 (replay determinístico mesmo `transferencia_id`) / `falhar_chave` em todos os caminhos de erro 4xx/5xx. 4 testes em `tests/test_equipamentos_transferir_idempotency_t_eqp_037.py`. |
| AC-EQP-004-5 | **OK** | T-EQP-038 ✅ FECHADO 2026-05-22: doc `docs/conformidade/equipamentos/transferencia-termo.md` v1.1-2026-05-22 com 4 cláusulas (P-EQP-A1 — advogado-saas-regulado): (1) LGPD art. 18; (2) Lei 14.063/2020 art. 4º + CP arts. 299/171 + CLT art. 482; (3) não-cessão de garantia/contrato/cert (ISO 17025 cl. 8.4); (4) **NOVA v1.1** titularidade do dado pessoal NÃO é cedida (LGPD art. 5º VI/VII). Helper `validators.texto_termo_transferencia(versao)` + constante `TEXTO_TERMO_TRANSFERENCIA_VERSAO_CANONICA` + teste anti-drift. `TransferenciaEquipamentoAceite.texto_termo_versao_id` aponta para versão exibida. 8 testes. |
| AC-EQP-004-6 | **OK** | T-EQP-039 ✅ FECHADO 2026-05-23: enum `NivelConsentimentoHistorico` (3 valores: `nada`/`resumo`/`completo`) + modelo `ConsentimentoHistoricoEquipamento` (12 campos CORE imutáveis + 4 campos one-shot de revogação) + migration `0014` RLS v2 + trigger PG `consent_hist_imutavel_trg` (bloqueia mutação CORE; bloqueia re-revogação) + UNIQUE parcial `(transferencia_origem)` WHERE `revogado_em IS NULL`. Integração automática em `solicitar_transferencia`: efetivação grava 1 consentimento no MESMO bloco transacional (nível via `derivar_nivel_do_aceite_dump` — retrocompat com `consentimento_historico_expresso` bool). Ação canônica nova `equipamento.consentimento_historico_concedido` (payload sanitizado com hash HMAC tenant do `cedente_id`). Filtro real no `construir_ficha_360` baseado no nível fica em **US-EQP-003 fase 3 (T-EQP-029)**. |
| AC-EQP-004-7 | **PARCIAL** | T-EQP-040 ✅ FECHADO 2026-05-23 junto com T-EQP-034 (versão mínima 8 campos): ação canônica `equipamento.transferido` em `acoes_canonicas.ACOES_EQUIPAMENTOS`. Payload sanitizado: `tenant_id, equipamento_id, transferencia_id, cedente_id_hash, cessionario_id_hash, motivo_categoria, texto_termo_versao_id, transferido_em`. **Pendente Wave A**: 5 campos extras de P-EQP-A4 (`motivo_detalhe_hash, aceite_origem_ts/via, aceite_destino_ts/via, consentimento_compartilhamento_historico, causation_id`) — fica `GATE-EQP-TRANSF-PAYLOAD-COMPLETO` Wave A. |
| AC-EQP-004-8 | **OK** | T-EQP-041 ✅ FECHADO 2026-05-23: endpoint POST `/api/v1/equipamentos/{id}/consentimento-historico/revogar/` (action no `EquipamentoViewSet`). Service `revogar_consentimento_historico` valida justificativa (≥30 chars + anti-PII reuso `conter_pii_direta`), grava `revogado_em/por/via/justificativa_hash` (HMAC com salt tenant — texto cru NUNCA persistido), publica `equipamento.consentimento_historico_revogado` no MESMO bloco transacional. One-shot — segunda revogação retorna 412 (defesa em A: service raise; B: trigger PG). Authz `equipamentos.revogar_consentimento_historico` em migration `0015` (admin_tenant + tecnico). Códigos: 200 happy / 400 validação / 404 inexistente / 412 já-revogado / 403 sem authz. 7 testes específicos. |

### US-EQP-005 — Sucatar equipamento

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-005-1 | **OK** | T-EQP-042 ✅ FECHADO 2026-05-23: POST `/api/v1/equipamentos/{id}/sucatear/` (action no `EquipamentoViewSet`). Service `sucatear_equipamento` valida justificativa (≥30 + anti-PII), grava `EquipamentoSucatamento` (1:1 com Equipamento, migration 0017 RLS v2 + trigger PG imutabilidade pos-INSERT + CHECK `ck_sucatamento_cert_vigente_exige_dupla_confirmacao`), atualiza `Equipamento.status` para `sucata` (trigger PG `transicao_status_permitida` do migration 0002 valida), publica ação canônica nova `equipamento.sucateado` com payload sanitizado (`justificativa_hash` HMAC tenant, NUNCA texto cru). Seed authz `equipamentos.sucatear` em migration `0018` (admin_tenant + tecnico). |
| AC-EQP-005-2 | **OK** | T-EQP-043 ✅ FECHADO 2026-05-23: porta `certificados.tem_emitido` consulta cert vigente no momento. Cert vigente sem `confirmacao_dupla=True` E `ciencia_validade_tecnica_registrada=True` → 422 com texto canônico do modal (helper `texto_modal_sucatamento_cert_vigente` lista FECHADA, anti-LLM) + `texto_modal_versao_id`. Cert vigente happy publica adicionalmente ação canônica nova `equipamento.sucateado_com_cert_vigente` (P-EQP-S9) com `ciencia_validade_tecnica_registrada=True` no payload. |
| AC-EQP-005-3 | **OK** | T-EQP-044 ✅ FECHADO (já entregue em 2026-05-21 no migration `0002_rls_policies_e_triggers.py` — função PG `transicao_status_permitida` cobre matriz fechada com `sucata→extraviado` como única exceção válida). Testes anti-regressão em `tests/test_equipamentos_sucatar_t_eqp_042_046.py` (`sucata→ativo` bloqueado + `sucata→extraviado` permitido). |
| AC-EQP-005-4 | **OK** | T-EQP-045 ✅ FECHADO 2026-05-23: doc canônico `docs/conformidade/equipamentos/template-notificacao-sucatamento.md` v1.0 (advogado-saas-regulado) — 4 cláusulas no modal (validade técnica ISO 17025 §7.1.1 + decisão operacional + LGPD/CDC anti-CTA + estado terminal) + template notificação cliente STUB Wave A + allowlist semântica anti-CTA. Constantes `TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA` + `TEXTO_MODAL_SUCATAMENTO_CERT_VIGENTE` em `validators.py`; teste anti-drift versão↔frontmatter. |
| AC-EQP-005-5 | **OK** | T-EQP-046 ✅ FECHADO 2026-05-23: campo `ciencia_validade_tecnica_registrada` no modelo `EquipamentoSucatamento` + CHECK constraint Django `ck_sucatamento_cert_vigente_exige_dupla_confirmacao` (cert vigente exige `confirmacao_dupla=True` E `ciencia_validade_tecnica_registrada=True`) + defesa A no service (`CertVigenteSemConfirmacaoDupla` → 422). Validator `validar_justificativa_sucatamento` (≥30 chars + anti-PII reuso `conter_pii_direta`). |

### US-EQP-006 — Receber equipamento (ISO 17025 cl. 7.4)

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-006-1 | **OK** | T-EQP-047 ✅ FECHADO 2026-05-23: POST `/api/v1/equipamentos/{id}/recebimentos/` (action no `EquipamentoViewSet`, multipart-form para foto opcional). Modelo `EquipamentoRecebimento` (6 enum condição visual + 4 enum decisão + 11 enum status_fluxo_lab + foto_storage_key + foto_sha256 + 9 campos). Migration `0019` RLS pattern v2 + trigger PG `recebimento_foto_imutavel_trg` (T-EQP-058) + trigger PG `transicao_status_fluxo_lab_trg` (T-EQP-050). Service `services_recebimento.criar_recebimento` orquestra: valida condição+anomalias+decisão+justificativa, prepara foto (`preparar_foto` ANTES do INSERT — evita UPDATE pós-INSERT bloqueado pelo trigger), grava recebimento já com `foto_storage_key`+`foto_sha256` no INSERT, persiste BLOB foto na tabela 1:1 `EquipamentoRecebimentoFoto`, publica `equipamento.recebido`. Seed authz `equipamentos.receber` em migration `0020` (admin_tenant + tecnico). Doc canônico `aviso-foto-recebimento.md` v1.0 (P-EQP-A6+A8+S4 — advogado) com aviso UX + cláusula contratual + allowlist anti-CTA; helper `aviso_ux_foto_recebimento(versao)` fail-loud + constante anti-drift. |
| AC-EQP-006-2 | **OK** | T-EQP-048 ✅ FECHADO 2026-05-23: `decisao_apos_anomalia` enum 4 valores (`prosseguir`, `contatar_cliente_aguardando`, `recusar_recebimento`, `aceitar_com_ressalva`) + `justificativa_decisao` ≥30 chars + anti-PII (validator `validar_justificativa_decisao` novo / INV-EQP-ANOM-002). Anti-PII em `anomalias_observadas` (validator `validar_anomalias_observadas` / INV-EQP-ANOM-001). CHECK Django `ck_recebimento_anomalia_exige_decisao` reforça (condicao!=integro → decisao + justificativa preenchidos). Decisao=`contatar_cliente_aguardando` publica ação canônica nova `equipamento.notificacao_cliente_aguardando` (consumer real Wave A `comunicacao-omnichannel`). |
| AC-EQP-006-3a | **OK** | T-EQP-049 ✅ FECHADO (já entregue no migration `0002_rls_policies_e_triggers.py` — função PG `transicao_status_permitida` cobre matriz fechada da máquina `Equipamento.status` 7 valores + trigger `bloquear_transicao_status_equipamento_invalida`). Testes anti-regressão nos testes de sucatamento + recebimento. |
| AC-EQP-006-3b | **OK** | T-EQP-050 ✅ FECHADO 2026-05-23: função PG `transicao_status_fluxo_lab_permitida(de, para)` em migration `0019` cobre matriz fechada das 9 fases + 2 alternativos terminais (NC recebimento sai de `recebido_pendente`/`em_inspecao_visual`; NC calibração sai de `em_calibracao`/`aguardando_aprovacao`/`aguardando_padrao_disponivel`). Trigger PG `transicao_status_fluxo_lab_trg` valida BEFORE UPDATE; estados terminais (`devolvido`/`nao_conformidade_*`) bloqueiam UPDATE. Service `transicionar_status_fluxo_lab` + endpoint POST `/equipamentos/{id}/recebimentos/{rec_id}/transicionar/` (action). 409 transição inválida; publica ação canônica nova `equipamento.recebimento_transicionado`. **CAPA stub fica em entrega futura** (porta `CAPAQueryService` Wave A). |
| AC-EQP-006-4 | **OK** | T-EQP-051 ✅ FECHADO 2026-05-23: POST `/api/v1/equipamentos/{id}/recebimentos/{rec_id}/devolver/` (action no `EquipamentoViewSet`, multipart-form). Modelo `EquipamentoDevolucao` (1:1 com recebimento, 7 campos: condicao_visual_devolucao + foto_storage_key + foto_sha256 + termo_devolucao_versao_id + termo_aceite_hash + devolvido_por + devolvido_em). Tabela paralela `EquipamentoDevolucaoFoto` (1:1 com devolução, BLOB inline). Migration `0021` RLS v2 + trigger PG `devolucao_imutavel_trg` (registro terminal); migration `0022` RLS pra foto. Service `devolver_equipamento` valida `recebimento.status_fluxo_lab=aguardando_devolucao` + foto obrigatória (Marco 2 dogfooding) + condição enum + termo versão; prepara foto via `preparar_foto`, grava devolução com `foto_storage_key`+`foto_sha256` no INSERT (evita UPDATE pós-INSERT bloqueado pelo trigger), persiste BLOB na tabela paralela, transiciona `recebimento.status_fluxo_lab` → `devolvido` (trigger 0019 valida), atualiza `Equipamento.status` → `ativo`, publica ação canônica nova `equipamento.devolvido` com `termo_aceite_hash` = HMAC-SHA256 salt-tenant de `{texto_termo|usuario_id|ip_hash|aceite_em_iso}`. Doc canônico `termo-devolucao.md` v1.0 (advogado): 4 cláusulas (ISO 17025 cl. 7.4.5 + CC art. 624 fim do depósito + cert válido pós-devolução + foto+LGPD+EXIF). Constantes anti-drift `TEXTO_TERMO_DEVOLUCAO_VERSAO_CANONICA` + helper `texto_termo_devolucao(versao)` fail-loud. Seed authz `equipamentos.devolver` em migration `0023` (admin_tenant + tecnico). 13 testes verdes; 210/210 suíte completa equipamentos. |
| AC-EQP-006-5 | **OK** | T-EQP-052 ✅ FECHADO 2026-05-23: service `services_foto_storage` com `preparar_foto` (valida MIME `image/jpeg|image/png`, tamanho ≤5MB, decode via Pillow, EXIF strip via `ImageOps.exif_transpose` + re-encode JPEG/PNG limpo, calcula SHA-256 do binário final, gera `storage_key` UUID opaco) + `persistir_foto_preparada` (grava BLOB na tabela 1:1 após INSERT do recebimento). Override do `audit-pii-salt-check` justificado em helper `_hash_binario_foto` (SHA-256 de BINÁRIO de imagem — não PII textual; integridade WORM 25a cross-tenant). Marco 2: BLOB inline na tabela `EquipamentoRecebimentoFoto`; Wave A: B2 (GATE-EQP-2). |
| AC-EQP-006-6 | GAP | T-EQP-053 (`RecebimentoProvisorio` separado + TTL D+7 + métrica + trigger FK bloqueio cert) |
| AC-EQP-006-7 | GAP | T-EQP-054 (jobs Marco 2 via `processar_em_contexto_tenant` — P-EQP-T9) |
| AC-EQP-006-7b | GAP | T-EQP-055 (campos ambientais `temp_ambiente_c`, `ur_percentual`, `pressao_kpa` + CAPA link — P-EQP-R3) |
| AC-EQP-006-8 | GAP | T-EQP-056 (devolução exige promoção prévia de provisório — P-EQP-R9) |
| AC-EQP-006-9 | GAP | T-EQP-057 (métrica `taxa_provisorios_mensal` + alerta >5%) |
| AC-EQP-006-10 | **OK** | T-EQP-058 ✅ FECHADO 2026-05-23: campo `EquipamentoRecebimento.foto_sha256` (CharField 64-hex) calculado em `_hash_binario_foto` (SHA-256 do binário pós EXIF strip). Trigger PG `recebimento_foto_imutavel_check` (migration `0019`) bloqueia mutação em `foto_storage_key` OU `foto_sha256` pós-INSERT (defesa contra adulteração — corretora RAT-EQP-FOTO). CHECK Django `ck_recebimento_foto_storage_e_sha_all_or_nothing` garante consistência (ambos vazios OU ambos preenchidos). |
| AC-EQP-006-11 | **OK** | T-EQP-059 ✅ FECHADO 2026-05-23: ação canônica nova `equipamento.recebido` publicada por `criar_recebimento` com payload sanitizado incluindo `foto_sha256` quando `tem_foto=True` + `condicao_visual_chegada` + `status_fluxo_lab` + (se anomalia) `decisao_apos_anomalia`. Cliente NUNCA vaza no payload. 25a WORM ISO 17025 cl. 7.4 + RBC NIT-DICLA-021. |
| AC-EQP-006-12 | GAP | T-EQP-060 (cláusula contratual direito recusar recebimento se cliente recusa foto — P-EQP-S4) |

### US-EQP-007 — Gestão do Responsável Técnico do tenant (P-EQP-R10 BLOQUEANTE)

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-007-1 | **OK** | T-EQP-061 ✅ FECHADO 2026-05-22: app `src/infrastructure/responsavel_tecnico/` + modelo `ResponsavelTecnicoTenant` (12 campos: identidade + vigência + encerramento) + migration `0001_initial` com RLS pattern v2 + endpoints CRUD `/api/v1/responsaveis-tecnicos/` (list/retrieve/create/encerrar/trocar/competencias) + seed authz em `0002_seed_authz_acoes` (admin_tenant gerencia; rt_signatario+tecnico leem; gestor_qualidade fica GATE-EQP-RT-AUTHZ Wave A). |
| AC-EQP-007-2 | **OK** | T-EQP-062 ✅ FECHADO 2026-05-22: `EXCLUDE USING GIST` em `RTCompetencia` `(tenant_id =, grandeza =, daterange(declarado_em, COALESCE(vigente_ate, infinity), '[)') &&)` na migration `0001_initial` (extensão `btree_gist`). Service `declarar_competencia` captura `IntegrityError` e levanta `CompetenciaSobreposta` → endpoint retorna 409. Anti-regressão `tests/regressao/test_inv_eqp_rt_001.py` (happy + unhappy + cross-tenant). |
| AC-EQP-007-3 | **OK** | T-EQP-063 ✅ FECHADO 2026-05-22: modelo `RTCompetencia(rt_id, grandeza, carta_competencia_anexo_id, declarado_em, vigente_ate)` + predicate `decisor_tem_competencia_para_atividade(decisor_id, atividade, grandeza, tenant_id)` em `predicates.py`. Atividade reservada pra Wave A (matriz separa por categoria); Marco 2 gate é existência de competência. |
| AC-EQP-007-4 | **OK** | T-EQP-064 ✅ FECHADO 2026-05-22: services `cadastrar_rt`/`encerrar_rt`/`trocar_rt`/`declarar_competencia` publicam eventos via `publicar_evento(outbox=True)`. Ações canônicas adicionadas em `acoes_canonicas.py`: `tenant.rt.cadastrado`/`encerrado`/`trocado`/`competencia_declarada`. Troca dispara 3 eventos (encerrado+cadastrado+trocado agregador). Notificação ANPD/CGCRE 30d via consumer Wave A → GATE-EQP-RT-NOTIF. |
| AC-EQP-007-5 | **OK** | T-EQP-065 ✅ FECHADO 2026-05-22: trigger PG `rt_imutavel_pos_insert` bloqueia UPDATE em todos os campos exceto `encerrado_em/encerrado_por/motivo_encerramento/motivo_detalhe` (transição única ativo→encerrado). Após `encerrado_em NOT NULL` a linha vira totalmente imutável. CHECK em-trigger garante `encerrado_por` e `motivo_encerramento` obrigatórios em encerramento (atomicidade). |

### Tarefas transversais (hooks, docs canônicos, suite anti-regressão)

| T-EQP | Conserto |
|-------|----------|
| T-EQP-070 | Hook `qr-hmac-check.sh` + 9 casos `_test-runner.sh` (`INV-EQP-QR-NUNCA-RECOMPUTA`) |
| T-EQP-071 | ✅ FECHADO 2026-05-23: Hook `equipamento-imutabilidade-check.sh` (192/192 verde) + 13 casos no `_test-runner.sh` (EI1..EId — assignment + ORM update em tag/numero_serie/fabricante; perfil_tenant_snapshot direto; allowlist services_perfil/tests/migrations; override consciente). |
| T-EQP-072 | Hook `port-binding-validator.sh` + 9 casos (ADR-0007 — proibir import direto de adapter) |
| T-EQP-073 | Hook `trigger-stub-sweep.sh` + 4 casos (bloqueia release prod com `_v0_stub`) |
| T-EQP-080 | `docs/conformidade/equipamentos/textos-rejeicao-422.md` (T1-T5 P-EQP-A3) |
| T-EQP-081 | `docs/conformidade/equipamentos/aviso-aceite-presencial-atendente.md` (P-EQP-A2) |
| T-EQP-082 | `docs/conformidade/equipamentos/template-notificacao-sucatamento.md` (P-EQP-A5) |
| T-EQP-083 | `docs/conformidade/equipamentos/aviso-foto-recebimento.md` (P-EQP-A8) |
| T-EQP-084 | `docs/conformidade/comum/retencao-matriz.md` ganha 5 entradas Marco 2 (P-EQP-A7) |
| T-EQP-085 | ADR-0022 (gestão do RT do tenant) — proposta |
| T-EQP-090 | `tests/regressao/inv_eqp_001.py` (perfil_tenant snapshot — 3+ testes) |
| T-EQP-091 | `tests/regressao/inv_eqp_002.py` (segregação solicitante≠decisor + competência — 3+ testes) |
| T-EQP-092 | `tests/regressao/sec_qr_001.py` (QR HMAC versionado — 3+ testes) |
| T-EQP-093 | `tests/regressao/inv_eqp_qr_nunca_recomputa.py` (consulta tabela, nunca recomputa) |
| T-EQP-094 | `tests/regressao/inv_eqp_rt_001.py` (RT sem sobreposição temporal — `EXCLUDE USING GIST`) |
| T-EQP-095 | `tests/regressao/inv_049_tag_unica.py` (TAG única por tenant — 3+ testes) |
| T-EQP-096 | `tests/regressao/inv_050_transferencia_mesmo_tenant.py` (cross-tenant 422 — 3+ testes) |
| T-EQP-097 | `tests/regressao/inv_051_qr_hmac.py` (HMAC payload + allowlist anônima — 3+ testes) |
| T-EQP-098 | `tests/regressao/inv_025_imutabilidade_pos_cert.py` (5 textos 422 + trigger PG) |
| T-EQP-099 | `tests/regressao/inv_eqp_loc_001.py` (`localizacao_fisica` anti-PII) |
| T-EQP-100 | `tests/regressao/inv_eqp_versao_001.py` (`motivo_detalhe` anti-PII) |
| T-EQP-101 | `tests/regressao/inv_eqp_versao_002.py` (payload sanitizado evento versão) |
| T-EQP-102 | `tests/regressao/inv_eqp_anom_001.py` (`anomalias_observadas` anti-PII) |
| T-EQP-103 | `tests/regressao/inv_eqp_anom_002.py` (`justificativa_decisao` anti-PII) |
| T-EQP-104 | `tests/regressao/inv_eqp_prov_001.py` (RecebimentoProvisorio FK bloqueia cert) |
| T-EQP-105 | Drill `validar_m2_equipamentos` (management command — multi-tenant cadastro+QR+transferência+recebimento) |

### GATEs Wave A rastreados (não bloqueiam fechamento Marco 2 dogfooding)

| GATE | Item |
|------|------|
| GATE-EQP-1 | A3 cliente-side via Lacuna (assinatura RT) |
| GATE-EQP-2 | B2 Backblaze produção pra `FotoStorageService` |
| GATE-EQP-3 | Portal-cliente OTP (aceite forte) — Wave B Q2-2027 |
| GATE-EQP-4 | Matriz competências real (módulo `qualidade/competencias`) |
| GATE-EQP-5 | Timestamp RFC 3161 ICP-Brasil em foto |
| GATE-EQP-KMS | AWS KMS MRK real |
| GATE-EQP-PENTEST | Pentest externo cronometrado pra timing oracle |
| GATE-EQP-S1 | Evidência operacional 90d QR HMAC |
| GATE-EQP-S5 | Cláusula cap responsabilidade em contrato tenant |
| GATE-EQP-S6 | RIPD por módulo (Marco 1 + Marco 2) |
| GATE-EQP-S7 | DR drill anual (PG + B2) |
| GATE-EQP-S8 | Certificado RC do tenant exigido em contrato |
| GATE-EQP-RT | Carta de competência declarada do RT humano (NIT-DICLA-021) |

## Resumo P3

- **GAPs / a fechar em P4:** **65 T-EQP-NNN** (T-EQP-001..105 numerados
  esparsos por categoria; principal carga em viewset/migration/trigger).
- **TRACK / GATE Wave A:** 13 (GATE-EQP-1..RT) — nenhum bloqueia
  fechamento Marco 2 dogfooding.
- **OK herdado:** F-A multi-tenant + audit + PII HMAC + bus_outbox;
  F-B authz + MFA; Marco 1 cliente + bloqueio + identidade canônica +
  política LGPD única.

---

## Próximo passo (P4 — execução causa-raiz)

Implementação por T-EQP em sequência lógica (cada T-EQP = 1 commit
atômico mínimo). Ordem sugerida pra reduzir retrabalho:

1. **Fundação** (T-EQP-001..011): modelo `Equipamento` + migration RLS
   + `cliente_atual_id` FK SET NULL + `perfil_tenant_snapshot` imutável.
2. **QR + etiqueta** (T-EQP-002, 006, 070): `QR_HMAC_KEY_REGISTRO` +
   hook + endpoint + PDF.
3. **US-EQP-007 RT** (T-EQP-061..065): nasce cedo porque US-EQP-002
   precisa do RT (motivo `mudanca_classe_metrologica` exige A3).
4. **Versionamento** (T-EQP-012..017): `EquipamentoVersao` + textos 422
   + `INV-EQP-VERSAO-002`.
5. **Aprovação** (T-EQP-018..023): fluxo gestor_qualidade.
6. **Ficha + QR público** (T-EQP-024..033): viewset + timing constant
   + rate-limit + PWA.
7. **Transferência** (T-EQP-034..041): termo + consentimento + Idempotency.
8. **Sucatamento** (T-EQP-042..046): modal + template.
9. **Recebimento** (T-EQP-047..060): cl. 7.4 + foto + máquina estados.
10. **Hooks + docs** (T-EQP-070..085): cravar regras como código.
11. **Suite anti-regressão** (T-EQP-090..104): ≥42 testes happy + unhappy + cross-tenant.
12. **Drill** (T-EQP-105): `validar_m2_equipamentos` PASS multi-tenant.

P5 (10 auditores Família 5) destrava quando P4 concluído + suite verde
+ hooks ≥168+casos + makemigrations limpo + drill verde.
