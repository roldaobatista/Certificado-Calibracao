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
| AC-EQP-001-2 | GAP | T-EQP-002 (PDF etiqueta WeasyPrint + libpango) |
| AC-EQP-001-2b | GAP | T-EQP-003 (POST /etiqueta.pdf exige `Idempotency-Key` — P-EQP-T6) |
| AC-EQP-001-3 | GAP | T-EQP-004 (UNIQUE parcial `(tenant_id, tag) WHERE deletado_em IS NULL`) |
| AC-EQP-001-4 | GAP | T-EQP-005 (`INV-EQP-LOC-001` validator + serializer) |
| AC-EQP-001-5 | **OK** | T-EQP-006 ✅ FECHADO 2026-05-21: `QR_HMAC_KEY_REGISTRO` em `config/settings/base.py` (reuso `_RegistroChavesPII` com prefixo `qrN:`) + helper único `src/infrastructure/equipamentos/services_qr.py` + modelo `QRCode` com UNIQUE+RLS+trigger imutabilidade em migration `0003_qrcode.py` + hook `qr-hmac-check.sh` (11 casos no `_test-runner`) + 18 testes em `tests/regressao/test_sec_qr_001_hmac_versionado.py` + entrada `SEC-QR-001` registrada em `REGRAS-INEGOCIAVEIS.md`. Suite 503 passed. |
| AC-EQP-001-6 | GAP | T-EQP-007 (evento `Equipamento.Criado` via `publicar_evento(outbox=True)`) |
| AC-EQP-001-7 | GAP | T-EQP-008 (`INV-EQP-001` — `perfil_tenant_snapshot` JSONB imutável via trigger PG) |
| AC-EQP-001-7b | GAP | T-EQP-009 (função `promover_perfil_equipamento_snapshot` D→A — P-EQP-T4) |
| AC-EQP-001-8 | GAP | T-EQP-010 (`cliente_atual_id` FK `ON DELETE SET NULL` + trigger anti-órfão — P-EQP-T9) |
| AC-EQP-001-8b | GAP | T-EQP-011 (snapshot 7 campos mínimos + `snapshot_schema_version` — P-EQP-R1) |
| AC-EQP-001-9 | TRACK | GATE-EQP-S1 (evidência operacional 90d QR HMAC — Wave A) |

### US-EQP-002 — Editar equipamento com versionamento pós-emissão

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-002-1 | GAP | T-EQP-012 (`EquipamentoVersao` + enum 9 valores `motivo_mudanca` — P-EQP-R2) |
| AC-EQP-002-2 | GAP | T-EQP-013 (`INV-025` imutabilidade pós-cert + texto canônico 422 T1-T5) |
| AC-EQP-002-3 | TRACK | GATE-EQP-1 (A3 RT cliente-side via Lacuna — Wave A); endpoint contrato em T-EQP-014 |
| AC-EQP-002-4 | GAP | T-EQP-015 (motivo=`outros`/`substituicao_componente`/`atualizacao_firmware` exige aprovação — P-EQP-R2) |
| AC-EQP-002-5 | GAP | T-EQP-016 (`INV-EQP-VERSAO-001` — regex anti-PII em `motivo_detalhe`) |
| AC-EQP-002-6 | GAP | T-EQP-017 (`INV-EQP-VERSAO-002` — payload com `assinatura_a3_referencia` UUID; lista positiva/negativa — P-EQP-T5) |

### US-EQP-002b — Aprovação gestor_qualidade

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-002b-1 | GAP | T-EQP-018 (tabela `AprovacaoPendenteEquipamentoVersao` 16 campos + trigger anti-mutation status terminal) |
| AC-EQP-002b-2 | GAP | T-EQP-019 (SLA D+3/D+7 + `workalendar.america.Brazil` + pausa SLA + alerta D-1 — P-EQP-R5) |
| AC-EQP-002b-3 | GAP | T-EQP-020 (`INV-EQP-002` — CHECK `solicitante_id != decisor_id` + competência declarada) |
| AC-EQP-002b-4 | GAP | T-EQP-021 (Django admin botão aprovar/rejeitar + `parecer_gestor_texto` anti-PII) |
| AC-EQP-002b-5 | GAP | T-EQP-022 (eventos aprovada/rejeitada/expirada via `publicar_evento`) |
| AC-EQP-002b-6 | GAP | T-EQP-023 (predicate `decisor_tem_competencia_para_atividade` + stub `CompetenciaDeclarada` — P-EQP-R4) |

### US-EQP-003 — Ficha 360° + scan QR + PWA

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-003-1 | GAP | T-EQP-024 (GET `/equipamentos/{id}/` + ficha 360° + `INV-013` `AcessoDadosCliente`) |
| AC-EQP-003-2 | GAP | T-EQP-025 (GET `/v1/qr/{hash}` 3 escopos A/B/C + allowlist `qr-publico-allowlist.md`) |
| AC-EQP-003-3 | GAP | T-EQP-026 (timing constant + Mann-Whitney + target p99 medido — P-EQP-T3) |
| AC-EQP-003-4 | GAP | T-EQP-027 (rate-limit 60 req/min + lockout 24h via Redis) |
| AC-EQP-003-5 | GAP | T-EQP-028 (PWA `BarcodeDetector` + jsQR fallback + SW `/scan/sw.js` + filtro QR-only — P-EQP-T8) |
| AC-EQP-003-6 | GAP | T-EQP-029 (banner histórico oculto cessionário sem consentimento + toggle) |
| AC-EQP-003-7 | GAP | T-EQP-030 (ficha 360° exibe bloco "Perfil no momento do cadastro" — P-EQP-R1) |
| AC-EQP-003-8 | GAP | T-EQP-031 (`finalidade_declarada` enum + alerta acesso massivo >500 fichas/h — P-EQP-R7) |
| AC-EQP-003-9 | GAP | T-EQP-032 (rate-limit GLOBAL por tenant + `sistema.qr_scraping_suspeito` — P-EQP-S2) |
| AC-EQP-003-10 | GAP | T-EQP-033 (Escopo B 404 indistinguível de 200 vazio — P-EQP-S2) |

### US-EQP-004 — Transferir equipamento

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-004-1 | GAP | T-EQP-034 (POST `/transferir/` + 3 vias aceite + tabela `TransferenciaEquipamentoAceite` + aviso atendente — P-EQP-A2) |
| AC-EQP-004-2 | GAP | T-EQP-035 (`INV-050` cross-tenant 422 sem oracle + RLS) |
| AC-EQP-004-3 | GAP | T-EQP-036 (predicate `cliente_nao_bloqueado` Marco 1 + cessionário/cedente bloqueado 412) |
| AC-EQP-004-4 | GAP | T-EQP-037 (`Idempotency-Key` 24h + concorrência 425 + payload diferente 422 — P-EQP-T6) |
| AC-EQP-004-5 | GAP | T-EQP-038 (texto termo v1.1 com 4 cláusulas — P-EQP-A1; `texto_versao_id` versionado) |
| AC-EQP-004-6 | GAP | T-EQP-039 (consentimento histórico granular cedente — P-EQP-R6) |
| AC-EQP-004-7 | GAP | T-EQP-040 (evento `Equipamento.Transferido` 13 campos — P-EQP-A4) |
| AC-EQP-004-8 | GAP | T-EQP-041 (endpoint revogação consentimento posterior — P-EQP-R6) |

### US-EQP-005 — Sucatar equipamento

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-005-1 | GAP | T-EQP-042 (POST `/sucatear/` simples + evento) |
| AC-EQP-005-2 | GAP | T-EQP-043 (sucata com cert vigente: modal + duplo consentimento + `texto_modal_versao` — P-EQP-S9) |
| AC-EQP-005-3 | GAP | T-EQP-044 (trigger PG `sucata→extraviado` exclusivo) |
| AC-EQP-005-4 | GAP | T-EQP-045 (template notificação + cláusula informativa validade técnica — P-EQP-A5) |
| AC-EQP-005-5 | GAP | T-EQP-046 (gravação `ciencia_validade_tecnica_registrada` — P-EQP-R8) |

### US-EQP-006 — Receber equipamento (ISO 17025 cl. 7.4)

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-006-1 | GAP | T-EQP-047 (POST `/recebimentos/` + `EquipamentoRecebimento` + foto obrigatória perfil A + `aviso-foto-recebimento.md` — P-EQP-A8) |
| AC-EQP-006-2 | GAP | T-EQP-048 (decisão pós-anomalia enum + justificativa anti-PII) |
| AC-EQP-006-3a | GAP | T-EQP-049 (máquina `Equipamento.status` 7 valores + trigger PG — P-EQP-T2) |
| AC-EQP-006-3b | GAP | T-EQP-050 (máquina `EquipamentoRecebimento.status_fluxo_lab` 9 fases + 2 alternativos + CAPA stub — P-EQP-R3) |
| AC-EQP-006-4 | GAP | T-EQP-051 (POST `/devolucoes/` + termo presencial) |
| AC-EQP-006-5 | GAP | T-EQP-052 (`FotoStorageService` + EXIF strip + `storage_key` + aviso terceiros — P-EQP-A6) |
| AC-EQP-006-6 | GAP | T-EQP-053 (`RecebimentoProvisorio` separado + TTL D+7 + métrica + trigger FK bloqueio cert) |
| AC-EQP-006-7 | GAP | T-EQP-054 (jobs Marco 2 via `processar_em_contexto_tenant` — P-EQP-T9) |
| AC-EQP-006-7b | GAP | T-EQP-055 (campos ambientais `temp_ambiente_c`, `ur_percentual`, `pressao_kpa` + CAPA link — P-EQP-R3) |
| AC-EQP-006-8 | GAP | T-EQP-056 (devolução exige promoção prévia de provisório — P-EQP-R9) |
| AC-EQP-006-9 | GAP | T-EQP-057 (métrica `taxa_provisorios_mensal` + alerta >5%) |
| AC-EQP-006-10 | GAP | T-EQP-058 (`EquipamentoRecebimento.foto_sha256` pós EXIF + imutável trigger — P-EQP-S3) |
| AC-EQP-006-11 | GAP | T-EQP-059 (evento `Equipamento.Recebido` payload com `foto_sha256` — P-EQP-S3) |
| AC-EQP-006-12 | GAP | T-EQP-060 (cláusula contratual direito recusar recebimento se cliente recusa foto — P-EQP-S4) |

### US-EQP-007 — Gestão do Responsável Técnico do tenant (P-EQP-R10 BLOQUEANTE)

| AC | Estado | T-EQP / nota |
|----|--------|--------------|
| AC-EQP-007-1 | GAP | T-EQP-061 (tabela `ResponsavelTecnicoTenant` + endpoints CRUD) |
| AC-EQP-007-2 | GAP | T-EQP-062 (`INV-EQP-RT-001` — `EXCLUDE USING GIST` sem sobreposição temporal) |
| AC-EQP-007-3 | GAP | T-EQP-063 (`RTCompetencia` + carta competência anexo + predicate competência) |
| AC-EQP-007-4 | GAP | T-EQP-064 (evento `Tenant.RTTrocado` + notificação ANPD/CGCRE 30 dias) |
| AC-EQP-007-5 | GAP | T-EQP-065 (tabela INSERT-only + trigger anti-mutation) |

### Tarefas transversais (hooks, docs canônicos, suite anti-regressão)

| T-EQP | Conserto |
|-------|----------|
| T-EQP-070 | Hook `qr-hmac-check.sh` + 9 casos `_test-runner.sh` (`INV-EQP-QR-NUNCA-RECOMPUTA`) |
| T-EQP-071 | Hook `equipamento-imutabilidade-check.sh` + 9 casos (`INV-025` pós-cert) |
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
