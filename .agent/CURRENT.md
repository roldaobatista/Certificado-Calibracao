# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** Marco 1 **FECHADO** + Marco 2 `equipamentos` em P4 (T-EQP-001
+ 006 + 002 + 003 + US-EQP-007 + T-EQP-005 + T-EQP-007 + T-EQP-009 +
T-EQP-012 + T-EQP-016 + **T-EQP-017** entregues).
**Sessão em curso 2026-05-23** (T-EQP-017 evento sanitizado).
**Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-23)

- T-EQP-009: **15/15 passed** em 4.8s
- T-EQP-012+016: **13/13 passed** em 4.0s
- T-EQP-017: **11/11 passed** em 8.0s
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

1. **T-EQP-013** (`INV-025` imutabilidade pós-cert + textos 422 T1-T5):
   doc `docs/conformidade/equipamentos/textos-rejeicao-422.md` com 5
   variantes; entrada `INV-025` em `REGRAS-INEGOCIAVEIS.md`; trigger PG
   fica dependente do módulo `certificados` (Wave A) — gate explícito.
2. **US-EQP-002b** (T-EQP-018..023): aprovação gestor_qualidade. SLA
   D+3/D+7 + competência declarada (US-EQP-007 ✅ já tem predicate).
3. **T-EQP-014** (endpoint POST `/equipamentos/{id}/versao/assinar/`):
   contrato pra A3 cliente-side via Lacuna (GATE-EQP-1 Wave A).
4. Quando T-EQP-013 fechar, estender `services_perfil.promover_perfil_equipamento`
   pra criar `EquipamentoVersao` (via `services_versao.criar_versao_equipamento`)
   com `motivo_mudanca=mudanca_classe_metrologica` na mesma transação.
5. Sequência em `docs/faseamento/M2-equipamentos/tasks.md`.

## Pendências rastreadas (não bloqueiam)

- ADR-0018 (PWA scanner QR) — aguardando aceite Roldão antes de US-EQP-003.
- ADR-0019 Pilar 2 — apólice cyber+E&O pré-1º tenant externo pago.
- GATE-EQP-1..PENTEST (14 itens Wave A — `docs/faseamento/M2-equipamentos/plan.md`).
