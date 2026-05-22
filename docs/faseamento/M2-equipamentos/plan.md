---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 2 — equipamentos
tipo: plan-ritual-spec-kit-P2
relacionados:
  - docs/faseamento/M2-equipamentos/spec.md
  - docs/faseamento/M1-clientes/plan.md
---

# Marco 2 (equipamentos) — Plan P2 (4 reviews paralelos)

> **P2 do ritual Spec Kit (2026-05-21):** spec forward criada em P1
> (`spec.md`) foi revisada em PARALELO pelos 4 subagentes
> humano-substitutos: `tech-lead-saas-regulado`, `advogado-saas-regulado`,
> `consultor-rbc-iso17025`, `corretora-seguros-saas`. Esta ata
> registra as decisões absorvidas — bloqueantes viram correções na
> spec; MÉDIOs (INV-RITUAL-001) viram ACs/INVs novos; ALTOs ficam
> rastreados como GATE Wave A; ACEITES ficam como confirmação.

## Sumário dos vereditos

| Revisor | BLOQUEANTE | AJUSTADO | ACEITE | Total |
|---|---|---|---|---|
| `tech-lead-saas-regulado` | 2 (T1, T2) | 6 (T3, T4, T5, T6, T8, T9) | 1 (T7) | 9 |
| `advogado-saas-regulado` | 1 (A3) | 6 (A1, A2, A4, A5, A7, A8) | 1 (A6) | 8 |
| `consultor-rbc-iso17025` | 1 (R10) + 3 ALTOS (R1, R3, R4) | 5 (R2, R5, R6, R7, R9) | 1 (R8) | 10 |
| `corretora-seguros-saas` | 3 MÉDIO (S2, S3, S6) + 2 ALTO Wave A (S5, S8) + 1 ALTO Wave A (S7) | 1 (S1 acréscimo) | 2 (S4, S9) | 9 |

**Total:** 36 pontos. **Absorvidos na spec (BLOQUEANTE + MÉDIO INV-RITUAL-001 antes de P3):** 12 itens. **Diferidos rastreados como GATE-EQP-1..N (não bloqueiam fechamento Marco 2 dogfooding):** 14 itens. **ACEITES (confirmação, ação cosmética):** 10 itens.

---

## Decisões absorvidas na spec (rodada de update pré-P3)

### P-EQP-T1 — KMS_qr_secret versionada igual `PII_HASH_KEY` (BLOQUEANTE)

**Análise tech-lead:** etiquetas físicas com hash QR são impressas pelo cliente; rotação de chave sem versionamento invalida todas. Spec atual diz "env var dev/prod distintos" mas falta padrão FA-A1 (registry + prefixo `qrN:` + verificação que resolve versão).

**Decisão:** AC-EQP-001-5 reescrito para usar registro `QR_HMAC_KEY_REGISTRO` (mesmo padrão de `PII_HASH_KEY_REGISTRO`); prefixo `qrN:` no hash armazenado; verificação via `verificar_qr_hash()` que resolve versão. NG-EQP-13 adicionado: KMS MRK real é GATE-EQP-KMS Wave A pré-1º tenant pago. INV-EQP-QR-NUNCA-RECOMPUTA: validação sempre consulta tabela `qrcode.hash` (UNIQUE index), proibido recomputar HMAC na validação.

### P-EQP-T2 — Máquina de estados `Equipamento.status` separada do `status_fluxo_lab` (BLOQUEANTE)

**Análise tech-lead:** spec misturou as 8 fases do `EquipamentoRecebimento.status_fluxo_lab` com transições do `Equipamento.status` (7 valores do modelo-de-dominio). Faltam transições críticas: `ativo↔inativo_temporario`, `ativo↔aposentado` (reversível com avaliação), `orfao_pendente_decisao→ativo`, `extraviado→ativo`.

**Decisão:** AC-EQP-006-3 desdobrado em AC-EQP-006-3a (máquina `Equipamento.status` — 7 valores + matriz reversíveis/terminais + `aposentado→ativo` exige A3 RT + audit) e AC-EQP-006-3b (máquina `EquipamentoRecebimento.status_fluxo_lab` — 8 fases + 2 alternativos, mantém). Trigger PG `bloquear_transicao_status_equipamento_invalida` com função `transicao_status_permitida(de, para)`.

### P-EQP-A3 — 5 textos canônicos 422 materializados AGORA (BLOQUEANTE)

**Análise advogado:** spec aponta arquivo `textos-rejeicao-422.md` a criar mas conteúdo dos 5 textos pré-aprovados não existe em lugar nenhum. P3/P4 não pode improvisar.

**Decisão:** 5 textos T1-T5 materializados no review do advogado (TAG, NS, fabricante, fallback genérico, delete de versão) ficam absorvidos na P3 (`tasks.md`) como conteúdo da T-EQP-NNN "criar `textos-rejeicao-422.md`". AC-EQP-002-2 da spec aponta pra eles.

### P-EQP-T3 — Timing constant medido em ambiente populado (MÉDIO INV-RITUAL-001)

**Decisão:** AC-EQP-003-3 reescrito para incluir target p99 medido em banco populado (drill `validar_m2_equipamentos`); teto operacional 200ms (alerta P2 se estourar); estratégia híbrida `time.perf_counter` busy-wait nos últimos ms + `time.sleep` início; teste Mann-Whitney 1000 amostras `p>0.05`; pentest externo cronometrado é GATE-EQP-PENTEST Wave A.

### P-EQP-T4 — Exceção controlada `promover_perfil_equipamento_snapshot` D→A (MÉDIO)

**Decisão:** AC-EQP-001-7b novo: função PG `SECURITY DEFINER promover_perfil_equipamento_snapshot(...)` única via legítima, exige direção D→C→B→A (downgrade proibido), `evidencia_documental_id` obrigatório, justificativa ≥100 chars anti-PII, cria `EquipamentoVersao` auto com `motivo_mudanca=mudanca_classe_metrologica` + A3 RT, publica `Equipamento.PerfilPromovido` (25a WORM). Hook `equipamento-imutabilidade-check.sh` reconhece exceção via `# perfil-snapshot: promocao-via-funcao -- <razão>`. NG-EQP-14 (promoção em lote = Wave B).

### P-EQP-T5 — `assinatura_a3_referencia` UUID em vez de hash truncado (MÉDIO)

**Decisão:** AC-EQP-002-6 reescrito: payload `Equipamento.VersaoCriada` traz `assinatura_a3_referencia: UUID` (campo novo em `EquipamentoVersao`) + `assinatura_a3_assinada_em` + `assinatura_a3_certificado_emissor_hash`. Proibido `assinatura_a3_hash` cru ou truncado. `INV-EQP-VERSAO-002` explicitado com lista positiva (5 permitidos) + negativa (7 proibidos).

### P-EQP-T6 — `Idempotency-Key` janela + concorrência + endpoints adicionais (MÉDIO)

**Decisão:** AC-EQP-004-4 estendido: chave válida por 24h; reuso pós-janela → 409 com texto PT-BR; concorrência → 425 Too Early + retry-after 1s; payload diferente com mesma chave → 422. AC-EQP-001-2b novo: POST de re-emissão de etiqueta exige `Idempotency-Key`. Tabela `idempotency_key` é F-A horizontal (será compartilhada com US-EQP-002b/005/006).

### P-EQP-T8 — PWA service worker scope + headers + filtro QR-only (MÉDIO)

**Decisão:** AC-EQP-003-5 estendido: SW servido em `/scan/sw.js` com header `Service-Worker-Allowed: /`; response `/v1/qr/*` carrega 6 headers (`Cache-Control: private, no-store`, `Vary`, etc) — puxados pro AC da spec; `BarcodeDetector({formats: ['qr_code']})` filtro explícito (anti bug iOS Safari 17 que retorna data-matrix/codabar misturados).

### P-EQP-T9 — FK `cliente_atual_id` ON DELETE SET NULL + trigger anti-órfão + helper contexto (MÉDIO)

**Decisão:** AC-EQP-001-8 novo: FK `Equipamento.cliente_atual_id` `ON DELETE SET NULL` + trigger `equipamento_anti_orfao_imediato` marca `status=orfao_pendente_decisao` ao detectar `cliente_atual_id IS NULL` por DELETE em cliente; publica `Equipamento.OrfaoDetectadoViaLGPDEliminacao`. AC-EQP-006-7 novo: jobs Marco 2 (`job_aprovacao_versionamento_escalacao`, `marcar_orfao`) rodam via helper `processar_em_contexto_tenant` herdado de F-A.

### P-EQP-A1 — 4ª cláusula no termo de transferência (MÉDIO)

**Decisão:** AC-EQP-004-5 promovido de 3 pra **4 cláusulas mínimas**: (a) LGPD art. 18, (b) Lei 14.063 art. 4º, (c) não-cessão de garantia, (d) **NOVA — titularidade do dado pessoal do cedente NÃO é cedida ao cessionário** (LGPD art. 5º VI/VII; cedente preserva direitos do titular pós-transferência). Texto v1.1-2026-05-21 absorvido.

### P-EQP-A2 — Aceite presencial fraco com 3 camadas de mitigação (MÉDIO)

**Decisão:** AC-EQP-004-1 estendido: campos `evidencia_url` (URL opcional pra foto do termo físico em B2 WORM) + `atendente_user_id` (NOT NULL quando `via=presencial`); aviso UX responsabilização atendente em `docs/conformidade/equipamentos/aviso-aceite-presencial-atendente.md` (criar — §3 item 12 novo).

### P-EQP-A4 — Payload `Equipamento.Transferido` com 9 campos (MÉDIO)

**Decisão:** AC-EQP-004-7 reescrito com payload completo: `equipamento_id, cedente_id_hash, cessionario_id_hash, motivo_categoria, motivo_detalhe_hash, aceite_origem_ts, aceite_origem_via, aceite_destino_ts, aceite_destino_via, texto_versao_id, consentimento_compartilhamento_historico, transferencia_id, causation_id`. Nota: `INV-EQP-VERSAO-002` aplica-se também aqui.

### P-EQP-A5 — Template sucatamento com cláusula informativa sobre validade técnica (MÉDIO)

**Decisão:** AC-EQP-005-4 estendido: allowlist semântica anti-CTA + obrigação positiva — quando sucatamento ocorre com certificado vigente, template DEVE incluir parágrafo informativo sobre validade técnica do certificado (LGPD art. 5º IX boa-fé + CDC art. 6º III). Arquivo `template-notificacao-sucatamento.md` (criar — §3 item 13 novo).

### P-EQP-A7 — Fundamentação completa retenção 25a (MÉDIO)

**Decisão:** §4 tabela atualizada: todas as 6 linhas WORM citam 3 fundamentos: `ISO 17025 cl. 8.4 + LGPD art. 16 I + RBC cl. 4.2`. `retencao-matriz.md` ganha 5 linhas pra equipamento + transferência + foto + recebimento.

### P-EQP-A8 — Aviso pré-coleta no comprovante de entrada (MÉDIO)

**Decisão:** AC-EQP-006-1 estendido com cláusula: PDF do comprovante de entrada (gerado após POST `/recebimentos/`) inclui aviso ao cliente final no rodapé citando LGPD art. 7º V + ISO 17025 cl. 7.4 + canal LGPD do tenant. `aviso-foto-recebimento.md` (criar — §3 item 14 novo).

### P-EQP-R1 — Snapshot de perfil tenant comparável e renderizável (MÉDIO/ALTO RBC)

**Decisão:** AC-EQP-001-8b novo: snapshot tem 7 campos mínimos (`perfil` enum, `escopo_acreditacao_codigo`, `grandezas_acreditadas[]`, `incertezas_declaradas[]`, `signatarios_autorizados_ids[]`, `versao_nit_dicla_030_vigente`, `data_efetiva_perfil`) + `snapshot_schema_version` (semver) imutável. AC-EQP-003-7 novo: ficha 360° exibe bloco "Perfil no momento do cadastro" mesmo se perfil corrente difere.

### P-EQP-R2 — Enum `motivo_mudanca` ampliado (MÉDIO)

**Decisão:** AC-EQP-002-1 expandido de 6 pra 9 valores: + `ajuste_pos_calibracao` (cl. 6.4.10 — rotina, sem aprovação obrigatória), + `substituicao_componente_critico` (afeta rastreabilidade — exige aprovação), + `atualizacao_firmware` (OIML D 31 — exige aprovação). AC-EQP-002-4 ajustado: quais motivos disparam aprovação obrigatória.

### P-EQP-R3 — Condições ambientais na recepção + estado `aguardando_padrao_disponivel` + link com CAPA (MÉDIO/ALTO RBC)

**Decisão:** AC-EQP-006-1 estendido com campos ambientais (`temp_ambiente_c`, `ur_percentual`, `pressao_kpa`, NULL permitido com justificativa quando grandeza não exige); AC-EQP-006-3b expandido com novo estado `aguardando_padrao_disponivel`; AC-EQP-006-7b novo: NC link com `RegistroCAPA` (stub `CAPAQueryService` se módulo qualidade ainda não existe).

### P-EQP-R4 — Predicate competência declarada do decisor (MÉDIO/ALTO RBC)

**Decisão:** AC-EQP-002b-6 novo: predicate `decisor_tem_competencia_para_atividade(decisor_id, atividade, grandeza)` em `predicates_authz.py` + tabela stub `CompetenciaDeclarada` retornando `True` para qualquer `gestor_qualidade` em Marco 2. GATE-EQP-4: matriz de competências real (módulo `qualidade/competencias`) é Wave A. INV-EQP-002 ampliado: identidade distinta + competência.

### P-EQP-R5 — Calendário feriados + pausa SLA + alerta D-1 (MÉDIO)

**Decisão:** AC-EQP-002b-2 estendido: `workalendar.america.Brazil` + extensão estadual via config tenant; campos `sla_pausado_em` / `sla_retomado_em` no `AprovacaoPendenteEquipamentoVersao` + enum status `pausada_aguardando_cliente`; job alerta D-1.

### P-EQP-R6 — Granularidade de consentimento de histórico + revogabilidade (MÉDIO)

**Decisão:** AC-EQP-004-6 reescrito: consentimento DO CEDENTE (titular dos dados), 3 níveis de granularidade (nada / resumo / completo); log dedicado `ConsentimentoHistoricoEquipamento`; AC-EQP-004-8 novo: endpoint de revogação posterior `POST /equipamentos/{id}/consentimento-historico/revogar/`; evento `Equipamento.ConsentimentoHistoricoConcedido/Revogado` na §4.

### P-EQP-R7 — `finalidade_declarada` + retenção alinhada + alerta acesso massivo (MÉDIO)

**Decisão:** AC-EQP-003-1 ampliado com `finalidade_declarada` enum 5 valores + `outros`; AC-EQP-003-8 novo: alerta acesso massivo (>500 fichas/h por usuário); retenção `AcessoDadosCliente` alinhada (25a WORM em campos críticos).

### P-EQP-R9 — TTL do RecebimentoProvisorio + bloqueio devolução + métrica (MÉDIO)

**Decisão:** AC-EQP-006-6 expandido com TTL D+7 + escalação P2; AC-EQP-006-8 novo: devolução exige promoção prévia; AC-EQP-006-9 novo: métrica `taxa_provisorios_mensal` com alerta se >5%.

### P-EQP-R10 — US-EQP-007 Gestão do Responsável Técnico do tenant (BLOQUEANTE RBC)

**Decisão:** NOVA US-EQP-007 cravada na spec — `ResponsavelTecnicoTenant` (vigência + competência declarada + cartas anexadas + histórico imutável). 4 ACs (cadastro, vigência, troca com aviso 30 dias ANPD+CGCRE, histórico). INV-EQP-RT-001: RT único por tenant + grandeza em janela temporal sem sobreposição. A3 cliente-side via Lacuna fica GATE-EQP-1 Wave A; modelo de dados nasce em Marco 2.

### P-EQP-S2 — Rate-limit global por tenant + Escopo B 404 (MÉDIO INV-RITUAL-001)

**Decisão:** AC-EQP-003-9 novo: rate-limit global por tenant (`100 × n_equipamentos_ativos` requests/dia em `/v1/qr/*` cross-tenant ou anônimo); excedente dispara P1 + `sistema.qr_scraping_suspeito`. AC-EQP-003-10 novo: Escopo B 404 indistinguível (NÃO 200 com payload vazio) — teste fuzzing valida.

### P-EQP-S3 — `foto_sha256` na cadeia + RFC 3161 GATE (MÉDIO INV-RITUAL-001)

**Decisão:** AC-EQP-006-10 novo: `EquipamentoRecebimento.foto_sha256` calculado pós EXIF strip, gravado mesma tx, imutável via trigger. AC-EQP-006-11 novo: evento `Equipamento.Recebido` no bus inclui `foto_sha256`. GATE-EQP-5 novo: timestamp RFC 3161 (ICP-Brasil) é Wave A pré-1º tenant pago.

### P-EQP-S6 — Contagem 14 INVs + ≥42 testes anti-regressão (MÉDIO INV-RITUAL-001)

**Decisão:** §3 item 10 reescrito: 14 INVs (3 novos + 11 materializados); mínimo de 14 arquivos `tests/regressao/inv_eqp_*.py` (1 por INV); ≥3 testes por arquivo (happy + unhappy + cross-tenant) = ≥42 testes anti-regressão; padrão de nomenclatura `test_inv_eqp_NNN_*` (TST-004).

---

## Bloqueantes Wave A (não bloqueiam fechamento Marco 2 dogfooding)

- **GATE-EQP-1**: A3 cliente-side via Lacuna (assinatura RT) — Wave A pré-1º tenant pago.
- **GATE-EQP-2**: B2 Backblaze produção pra `FotoStorageService` — Wave A pré-1º tenant pago.
- **GATE-EQP-3**: portal-cliente OTP (aceite forte) — Wave B Q2-2027.
- **GATE-EQP-4**: matriz de competências real (módulo `qualidade/competencias`) — Wave A.
- **GATE-EQP-5**: timestamp RFC 3161 ICP-Brasil — Wave A pré-1º tenant pago.
- **GATE-EQP-KMS**: AWS KMS MRK (`GenerateMac`/`VerifyMac` real) — Wave A pré-1º tenant pago.
- **GATE-EQP-PENTEST**: pentest externo cronometrado pra timing oracle — Wave A pré-1º tenant pago.
- **GATE-EQP-S5**: Cláusula cap de responsabilidade no contrato tenant — pré-1º tenant pago.
- **GATE-EQP-S6**: RIPD por módulo (Marco 1 + Marco 2) — pré-1º tenant pago.
- **GATE-EQP-S7**: DR drill anual (PG + B2) — pré-1º tenant pago.
- **GATE-EQP-S8**: Certificado RC do tenant exigido em contrato — pré-1º tenant pago.
- **GATE-EQP-RT**: Carta de competência declarada do RT humano credenciada (NIT-DICLA-021) — pré-1ª supervisão CGCRE.

---

## ACEITES (confirmação, sem mudança estrutural)

- **P-EQP-T7**: trigger `_v0_stub` — adicionar hook `trigger-stub-sweep.sh` em §3 item 11 (varredura release prod).
- **P-EQP-A6**: aviso secundário sobre direitos de terceiros na foto — acrescentar item "d" em AC-EQP-006-5.
- **P-EQP-R8**: gravação de `ciencia_validade_tecnica_registrada` em campo dedicado (AC-EQP-005-5 novo).
- **P-EQP-S1**: AC-EQP-001-9 evidência operacional 90d de QR HMAC em `docs/governanca/evidencia-qr-hmac-90d.md`.
- **P-EQP-S4**: cláusula contratual de direito de recusar recebimento sem RC se cliente recusa fotografia (AC-EQP-006-12 novo).
- **P-EQP-S9**: payload `Equipamento.SucateadoComCertificadoVigente` inclui `texto_modal_versao`.

---

## Decisão arquitetural geral

- **Helper único `audit/event_helpers.publicar_evento`** (SANEA-08) é o ÚNICO ponto de gravação de eventos — Marco 2 herda; hook `event-helper-unico.sh` cobre.
- **`audit/politicas_lgpd.base_legal_aplicavel_pos_revogacao`** (Marco 1 INV-CLI-002) é o ÚNICO ponto de decisão LGPD — Marco 2 chama, não duplica.
- **`Cliente.objects.filter(tenant_id=active, id=...).get()`** (Marco 1 MÉDIO-1 SEC) é o padrão de defesa em profundidade ORM — Marco 2 usa para qualquer query em `Equipamento`, `EquipamentoRecebimento`, etc.
- **Trigger PG `*_v0_stub` sweep** (P-EQP-T7) + hook `port-binding-validator.sh` garantem que stubs não chegam a produção.

---

## Próximo passo (P3)

Atualizar `spec.md` absorvendo as 23 decisões BLOQUEANTE/MÉDIO acima, gerar `tasks.md` com matriz greenfield: cada AC vira T-EQP-NNN; INVs novos viram `tests/regressao/inv_eqp_*.py` happy + unhappy + cross-tenant; GATEs ficam rastreados em §3.

Conteúdo dos 5 textos 422 (P-EQP-A3) + textos PT-BR de seguros + briefing corretora SUSEP humana estão registrados nos pareceres `revisoes/M2-equipamentos-{tech-lead,advogado,rbc,corretora}.md` (a salvar separadamente).
