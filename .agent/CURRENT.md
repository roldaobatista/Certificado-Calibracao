# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** Marco 1 **FECHADO** + Marco 2 `equipamentos` em P4 (T-EQP-001
+ T-EQP-006 + T-EQP-002 + T-EQP-003 + US-EQP-007 entregues). Sessão 2026-05-22.
**Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-22 após T-EQP-005+007)

- Suite: **531 + 12 novos** (cadastro happy + 409 tag duplicada + 5 INV-EQP-LOC-001
  + idempotência + 400 sem header + authz) — alvo **543**
- Hooks: **179/179** verdes (22 ativos — sem hook novo)
- Cobertura: ≥85% global; ≥90% agregado clientes/ (Marco 1)
- Drills: `validar_f_a` 5/5 + `validar_f_b` + `validar_m1_clientes` verdes
- `makemigrations --check`: limpo; ruff + mypy zero issues (133 source files)

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

1. **T-EQP-009** (função PG `promover_perfil_equipamento_snapshot` D→A):
   `SECURITY DEFINER` com direção obrigatória (downgrade proibido), cria
   `EquipamentoVersao` + A3 RT, publica `Equipamento.PerfilPromovido`.
2. **US-EQP-002 versionamento** (T-EQP-012..017): depende do RT
   (US-EQP-007 ✅) — motivo `mudanca_classe_metrologica` exige A3 RT.
3. Sequência em `docs/faseamento/M2-equipamentos/tasks.md` §"Próximo passo".

## Pendências rastreadas (não bloqueiam)

- ADR-0018 (PWA scanner QR) — aguardando aceite Roldão antes de US-EQP-003.
- ADR-0019 Pilar 2 — apólice cyber+E&O pré-1º tenant externo pago.
- GATE-EQP-1..PENTEST (14 itens Wave A — `docs/faseamento/M2-equipamentos/plan.md`).
