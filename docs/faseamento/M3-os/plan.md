---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 3 — operacao/os
tipo: plan-ritual-spec-kit-P2
relacionados:
  - docs/faseamento/M3-os/spec.md
  - docs/faseamento/M3-os/reviews/tech-lead.md
  - docs/faseamento/M3-os/reviews/advogado.md
  - docs/faseamento/M3-os/reviews/corretora.md
  - docs/faseamento/M3-os/reviews/rbc.md
  - docs/faseamento/M2-equipamentos/plan.md
---

# Marco 3 (operacao/os) — Plan P2 (4 reviews paralelos)

> **P2 do ritual Spec Kit (2026-05-23):** spec forward criada em P1
> (`spec.md`) foi revisada em PARALELO pelos 4 subagentes
> humano-substitutos: `tech-lead-saas-regulado`, `advogado-saas-regulado`,
> `consultor-rbc-iso17025`, `corretora-seguros-saas`. Esta ata
> registra as decisões absorvidas — bloqueantes viram correções na
> spec; MÉDIOs (INV-RITUAL-001) viram ACs/INVs novos; ALTOs ficam
> rastreados como GATE Wave A; ACEITES ficam como confirmação.

## Sumário dos vereditos

| Revisor | BLOQUEANTE | MÉDIO INV-RITUAL-001 | ALTO Wave A / ACEITE | Total |
|---|---|---|---|---|
| `tech-lead-saas-regulado` | 2 (T1, T2) | 3 (T3, T4, T5) | 1 ALTO Wave A (T6) | 6 |
| `advogado-saas-regulado` | 0 | 5 (A1, A2, A3, A4, A6) | 2 GATE (A5, A7) | 7 |
| `corretora-seguros-saas` | 1 (S1) | 3 ALTO + 2 MÉDIO (S2, S3, S4, S5, S6) | (intercalado) | 6 |
| `consultor-rbc-iso17025` | 3 (R1, R2, R3) | 4 (R4, R5, R6, R7) | 1 ACEITE (R8) | 8 |

**Total:** 27 pontos.
- **BLOQUEANTE (corrige na spec.md antes de P3 reconciliação):** 6 itens.
- **MÉDIO INV-RITUAL-001 (vira AC/INV/tarefa em P3/P4 — bloqueia fechamento de fase):** 12 itens.
- **ALTO Wave A / GATE / ACEITE (rastreado, não bloqueia fechamento Marco 3 dogfooding):** 9 itens.

---

## Decisões absorvidas na spec (retrofit pré-P3)

### P-OS-T1 — Lock pra INV-OS-CONC-001 (BLOQUEANTE tech-lead)

**Análise:** AC-OS-002-3 + ADR-0041 fazem leitura sem lock — race condition sob carga concorrente quebra a matriz tipo×tipo. Sob 50 clientes concorrentes esse bug aparece em 1-2% das tentativas, invisível em teste single-thread mas devastador (medições paralelas inválidas).

**Decisão:** spec §3.2 + ADR-0041 cravam **unique partial index** como mecanismo primário:

```sql
CREATE UNIQUE INDEX idx_atividade_em_execucao_por_equip
ON atividade_da_os (tenant_id, equipamento_id)
WHERE estado='em_execucao' AND tipo_bloqueia_concorrencia=true;
```

Adicionar coluna `tipo_bloqueia_concorrencia BOOLEAN` em `TipoAtividadeConfig` derivada da matriz ADR-0041. INSERT/UPDATE de transição estoura unique violation → 412 determinístico. Promover INV-OS-CONC-001 com lista positiva (constraint declarativa).

Teste de carga obrigatório: `tests/carga/test_concorrencia_iniciar_atividade.py` (50 threads).

### P-OS-T2 — Numeração OS gap-less? (BLOQUEANTE tech-lead)

**Análise:** spec não decide entre sequence PG / sequence global / tabela `numerador_os`. Receita não exige gap-less em OS (só em NFS-e). Mas DDL por tenant não escala (1000 tenants = 1000 sequences).

**Decisão (depende de Roldão — ver §"Decisões pendentes do Roldão"):**
- Default recomendado: **sequence global + unique composto** `(tenant_id, numero)` — buracos aceitos.
- Criar ADR-0056 "Numeração OS — sequence global + unique composto, buracos aceitos".
- INV-OS-NUM-001: "Numeração da OS é per-tenant via tabela `numero_os_seq(tenant_id)` ou sequence global com unique composto; buracos por rollback são aceitos."

### P-OS-T5 — Foto append-only em atividade terminal (MÉDIO INV-RITUAL-001 tech-lead)

**Análise:** INV-OS-SYNC-001 "append-only para fotos" sem entidade definida + sem regra sobre atividades terminais.

**Decisão:** spec §3 ganha entidade `EvidenciaFotoAtividade`:
- Padrão B (imutável pós-INSERT) com `revogado_em` apenas para LGPD art. 18.
- FK `atividade_id` + `tenant_id`.
- INSERT permitido em qualquer estado da atividade — gera `EventoDeOS(tipo='foto_evidencia_tardia')` automaticamente + alerta P3 ao RT.
- INV-OS-SYNC-001 reescrito.

### P-OS-R1 — Competência do EXECUTOR cl. 6.2 (BLOQUEANTE RBC)

**Análise:** AC valida competência do TENANT, não do executor designado. Auditor CGCRE pergunta competência do EXECUTOR na DATA de execução — atual implementação não responde.

**Decisão:** adicionar AC-OS-002b-4 + AC-OS-003-6:

- **AC-OS-002b-4:** GIVEN tipo IN (calibracao, verificacao_inmetro), WHEN atribui técnico, THEN `rt_competencia_cobre(tecnico_executor_id, grandeza, data_atual)` (ADR-0022); falso → 422 `ExecutorSemCompetencia`.
- **AC-OS-003-6:** GIVEN tipo IN (calibracao, verificacao_inmetro), WHEN inicia atividade, THEN re-executa `rt_competencia_cobre(usuario, grandeza, data_inicio)` (competência pode revogar entre atribuição e início — vigência ADR-0030).

Promover INV-OS-ATIV-005-EXEC-COMP. Estender ADR-0012 com predicate `rt_competencia_cobre(user_id, grandeza, data)`.

### P-OS-R2 — cl. 7.1 análise crítica de pedidos (BLOQUEANTE RBC)

**Análise:** auditor CGCRE pede evidência NO REGISTRO TÉCNICO (a OS). Hoje não há campo `analise_critica_id` na OS — a evidência fica só no orçamento, que pode ser arquivado/alterado.

**Decisão:** spec §3.2 OS ganha:
- `analise_critica_id UUID NOT NULL` (FK → orcamento.analise_critica)
- `analise_critica_snapshot_hash CHAR(64)` (snapshot probatório — INV-DOC-CANON-001)
- `regra_decisao_acordada VARCHAR(20) NULL`

AC-OS-001-7 novo: snapshot copiado na abertura; orçamento sem análise crítica → 412 `OrcamentoSemAnaliseCritica`.

Em US-OS-015 (OS avulsa balcão): atendente registra análise crítica inline (`analise_critica_inline_texto` + `capacidade_tecnica_confirmada_por`).

Promover INV-OS-ANAL-001.

### P-OS-R3 — Escopo acreditado vigente (BLOQUEANTE RBC — NIT-DICLA-030)

**Análise:** AC valida competência por grandeza mas não valida se a faixa+procedimento está dentro do escopo acreditado vigente do tenant. Cenário real: tenant tem acreditação "massa até 30 kg"; abre OS calibração balança 100 kg → sistema atual aceita → certificado emitido fora do escopo → NC formal CGCRE.

**Decisão:** ADR-0012 ganha predicate `tenant_dentro_escopo_acreditado(tenant_id, grandeza, faixa_min, faixa_max, data)`.

AC-OS-002-3 revisado em DOIS predicates em ordem:
1. `tenant_dentro_escopo_acreditado(...)` — se falso E tenant perfil A/RBC → 422 `ForaDoEscopoAcreditado`. Tenants B/C/D apenas marcam `EventoDeOS.tipo=fora_escopo_aceito_perfil_BCD`.
2. `tenant_tem_rt_ativo_competencia(grandeza)` (já existente).

Spec §6.2 ganha consumer `Acreditacao.Suspensa` / `Acreditacao.Vencida` (bloqueia abertura de novas atividades calibração/verificação_INMETRO).

GATE-RBC-ESCOPO-1 novo (Wave A — antes 1º tenant perfil A).

### P-OS-S1 — GATE-SEG-BPT-1 no DoD (BLOQUEANTE corretora)

**Análise:** spec §14 DoD lista 11 critérios técnicos, mas nenhum vincula entrada em produção dogfooding ao GATE-SEG-BPT-1. M3 em dogfooding = registro formal de custódia BPT (CC art. 627 depositário) sem apólice — agrava risco vs. operação papel/planilha atual (audit digital comprova custódia formal).

**Decisão:** spec §14 DoD ganha item separado:

```
[ ] GATE-SEG-BPT-1 emitido (apólice BPT real ≥ R$ 500k/sinistro, franquia
    fixa R$ 10-15k) ANTES de a 1ª OS produtiva criar AtividadeDaOS de
    tipo manutencao_*/calibracao/instalacao em Balanças Solution.
```

Plan.md (esta ata) ganha "**fase 0 pré-dogfooding**":
- feature flag `OS_PRODUTIVO_DOGFOODING_BS=false` por default;
- flag só liga após corretora SUSEP confirmar apólice arquivada em `docs/conformidade/comum/seguros/apolices/`;
- predicate authz `pode_criar_os_produtiva_balancas` checa a flag.

Spec §12 ganha R-OS-11 novo: "Marco 3 em dogfooding sem apólice BPT → exposição CC art. 627 sem cobertura".

---

## Decisões absorvidas em plan.md/tasks.md (MÉDIO INV-RITUAL-001)

### P-OS-T3 — Watchdog cal-link: idempotência + backpressure + janela por-tenant

**Decisão:** detalhar no plan.md (esta seção) + tasks.md:
- tabela `tenant_config.watchdog_cal_link_janela_alerta_h` e `..._nc_dias_uteis` (NULL=default).
- predicate `pode_estender_janela_cal_link_atividade` em §10 spec.
- chave de idempotência `(atividade_id, regra, dia_processamento)` em `consumer_idempotencia`.
- batch size 100 + `FOR UPDATE SKIP LOCKED`.

Rastrear como T-OS-WATCHDOG-1..5 no tasks.md.

### P-OS-T4 — Performance: visão 360 + listagem (anti-N+1)

**Decisão:** spec §3 ganha seção "Performance & Queries":
- p95 budget: visão 360 OS ≤300ms; listagem ≤500ms.
- Query service `OSVisao360QueryService` em `src/application/operacao/os/queries/` com 1 query agregadora.
- Matriz endpoint × prefetch.
- Índices adicionais: `evento_de_os(tenant_id, os_id, occurred_at DESC)` + `aceite_atividade(tenant_id, atividade_id) WHERE revogado_em IS NULL` + `atividade_da_os(tenant_id, tecnico_executor_id, estado)`.
- Teste `tests/performance/test_visao_360_n_plus_one.py` com `assertNumQueries(<=5)`.

Rastrear T-OS-PERF-1..4.

### P-OS-A1 — Consentimento art. 11 LGPD para biometria touch

**Decisão:** spec §3 ganha entidade `ConsentimentoBiometriaTouch` (Padrão B imutável) com `id`, `tenant_id`, `atividade_id`, `cliente_referencia_hash`, `texto_canonico_id`, `texto_hash`, `versao_politica`, `concedido_em`, `tela_renderizada_evidencia`.

AC-OS-004-7 novo: tela de aceite com texto canônico + botão "concordo e assino" SEPARADO de "concluir"; consentimento gravado ANTES de AceiteAtividade (FK 1:1).

INV-OS-CONSBIO-001 promovido em REGRAS-INEGOCIAVEIS.md.

Texto canônico vai em `docs/conformidade/comum/termos/` — **REQUER OAB HUMANA** antes do 1º tenant externo.

### P-OS-A2 — TTL da coordenada exata (geo opt-in)

**Decisão:** tarefa T-OS-NNN: job procrastinate periódico `os-geo-truncamento` — após 5 anos da `AtividadeDaOS.concluida_em` faz UPDATE `os_evento` SET `geo_lat=NULL, geo_long=NULL, geo_municipio_hash=...` + audit-trail `GeoTruncadoLGPD`.

Drill `validar_m3_os` item 21 novo: job agendado + teste regressão com `freezegun`.

INV-OS-GEO-001 estendido (item d): retenção máxima 5 anos pós-conclusão; trigger `os_geo_truncamento_trg` agendado.

### P-OS-A3 — Anti-PII texto livre estendido (4 falsos negativos)

**Decisão:** INV-OS-TXT-001 estendido com:
- (a) regex endereço (`\d+\s*(ap|apto|apt|bloco|sala|conjunto|cj)\.?\s*\d+`);
- (b) regex sequência numérica ≥7 dígitos não-CNPJ/CPF (protocolo/CRM);
- (c) lista palavra-chave saúde mínima (`paciente|leito|prontuário|menor|criança|gestante|HIV|positivo`) — dispara revisão de gerente em vez de bloqueio;
- (d) normalização Unicode NFC + lowercase antes da regex.

Campo `motivo_texto_revisao_gerente_pendente BOOLEAN` em entidades com texto livre. Quarentena 24h.

DPIA-OS §10 atualizada: "regex anti-PII é defesa em profundidade".

**REQUER OAB:** lista de palavras-chave saúde art. 11.

### P-OS-A4 — Dispensa de aceite (US-OS-013) formal vs CDC art. 39

**Decisão:** AC-OS-013-5 novo: `TermoDispensaAceite` canonicalizado (INV-DOC-CANON-001) contendo OBRIGATORIAMENTE:
(a) descrição objetiva da circunstância (3 cenários: recusa formal / ausência pós no-show / impossibilidade técnica);
(b) referência ao no-show vinculado quando aplicável;
(c) hash da foto de evidência (no-show ou recusa);
(d) declaração de boa-fé do gerente;
(e) **assinatura A3 do gerente** (não só sessão autenticada).

Restringir base de uso: dispensa **só** após no-show prévio (US-OS-014) OU recusa explícita gravada. Sem precedente → 412 `DispensaSemPrecedente`.

Marca "aceite dispensado" no rodapé certificado/fatura deve incluir link público (QR) — direito à informação CDC art. 6º III.

**REQUER OAB:** modelo do `TermoDispensaAceite`.

### P-OS-A6 — Spec §2.4 declara DPIA "aprovada" (drift)

**Decisão:** spec §2.4 reescrito: "DPIA em minuta (aprovação OAB pendente — GATE-OS-DPIA-OAB pré-tenant externo pago)".

§15 ganha nota: "Marco 3 dogfooding-only (Balanças Solution) não exige DPIA OAB-aprovada; 1º tenant externo pago bloqueia em GATE-OS-DPIA-OAB."

Campo `Cliente.permite_persistencia_25a` (consent regulatório explícito) que dispara retenção 25a.

### P-OS-S2..S5 — Cláusulas seguráveis (Cyber + E&O ampliado)

**Decisão:** ADR-0028 rev 2 ganha cláusulas:
- **Modalidade 2 (Cyber):** `Sensitive personal data — LGPD art. 11 (biometric, racial, health, religion) — affirmative coverage, no sub-aggregate restriction`.
- **Modalidade 2 (Cyber):** `Image rights — incidental third-party capture in field service photo`.
- **Modalidade 1 (E&O):** `Wrongful billing` com franquia R$ 5k (sem gatilho R$ 50k).
- **Modalidade 1 (E&O):** `Tax penalty exposure — incorrect cancellation / late tax document` nomeando Receita + SEFAZ.
- **Modalidade 1 (E&O):** `Software validation defect causing accreditation suspension` — cobre vetores upstream M3 (não só M4).
- **Modalidade 1 (E&O):** `Vicarious liability — tenant operative on-site OR tenant administrative decision via platform`.

Briefing-corretora §5 ganha caso narrativo R-OS-6 (vetor concorrência cascateia recall farma).

Spec §12 ganha R-OS-11 (foto terceiros), R-OS-12 (dispensa vicarious admin).

Teste obrigatório: `tests/sagas/test_saga_vicio_concorrencia_cascateia_cert.py`.

**REQUER CORRETORA SUSEP HUMANA.**

### P-OS-R4 — Vínculo `EquipamentoRecebimento` na OS (cl. 7.5)

**Decisão:** OS §3.2 ganha `equipamento_recebimento_id UUID NULL` (FK → EquipamentoRecebimento).

AC-OS-001-8 novo: OS de bancada exige `equipamento_recebimento_id` vinculado ao recebimento mais recente; ausente → 412 `EquipamentoSemRecebimentoRegistrado`. OS de campo: NULL permitido (condição registrada em ChecklistDaAtividade in loco).

Saga 1 em `sagas.md` ganha nota sobre propagação `EquipamentoRecebimento → OS`.

### P-OS-R5 — CAPA FK no `NaoConformidadeAtividade` (cl. 8.7)

**Decisão:** `NaoConformidadeAtividade` ganha:
- `registro_capa_id UUID NULL` (FK → qualidade.registro_capa, Wave B)
- `causa_raiz_hash CHAR(64) NULL` (anti-PII)
- `acao_corretiva_descricao_hash CHAR(64) NULL`
- `eficacia_verificada_em TIMESTAMPTZ NULL`
- `eficacia_verificada_por_user_id UUID NULL`

AC-OS-005-5 novo: `resolverNC` exige TODOS dos 4 campos ≠ NULL; ausente → 412 `CAPAIncompleto`.

GATE-RBC-CAPA-1 novo (Wave B — qualidade consume `AtividadeNaoConforme`/`AtividadeNCResolvida`).

### P-OS-R6 — Watchdog cal-link: janela 24h/72h apertada vs bancada real

**Decisão (depende de Roldão — ver §"Decisões pendentes do Roldão"):**

Default recomendado:
- Alerta P2 em **72h** (não 24h).
- NC automática em **15 dias úteis** (não 72h).
- Configurável por tenant via `TipoAtividadeConfig.prazo_link_calibracao_alerta_h` e `..._nc_dias_uteis`.
- Defaults RBC perfil A: 72h alerta / 15 dias NC. Perfis B/C/D: 7 dias alerta / 30 dias NC.
- Permitir extensão manual pelo RT (audit `EventoDeOS.tipo=watchdog_estendido` com justificativa ≥100 chars).

### P-OS-R7 — Independência executor↔revisor (cl. 6.2.5 + ADR-0026)

**Decisão:** spec §6.1 explicita que `AtividadeConcluida` payload carrega `tecnico_executor_id` (consumer M4 valida independência ao criar Calibracao com `revisor != tecnico_executor`).

`sagas.md` ganha saga "Independência executor↔revisor M3→M4". M3 não muda schema.

---

## Bloqueantes Wave A (não bloqueiam fechamento Marco 3 dogfooding)

- **GATE-OS-TENANT-SUSPENSO** (P-OS-T6) — matriz operações M3 × estado tenant (operacional/suspenso/encerrado) cravada em `docs/dominios/operacao/modulos/os/operacao-suspenso-matriz.md`. ADR-0035 aceita por Roldão antes do 1º tenant pago. M3 entrega placeholder "bloqueio total em suspenso".
- **GATE-OS-FOTO-NOSHOW-BLUR** (P-OS-A5) — blur automático de rostos antes do upload (modelo on-device). Até lá, AC-OS-014 inclui aviso "evite enquadrar pessoas; capture só fachada".
- **GATE-OS-SUCESSAO-EVIDENCIA** (P-OS-A7) — entidade `SucessaoSocietaria` com PDF do ato societário + assinatura A3 do admin. AC-OS-006-8: reabertura cross-cliente sem A3 do admin → 412 `SucessaoSemEvidencia`.
- **GATE-OS-CONSBIO-TEXTO-OAB** (P-OS-A1) — texto canônico do consentimento biométrico OAB-aprovado.
- **GATE-RBC-ESCOPO-1** (P-OS-R3) — predicate `tenant_dentro_escopo_acreditado` ativo + módulo `licencas-acreditacoes` operacional.
- **GATE-RBC-CAPA-1** (P-OS-R5) — módulo qualidade Wave B implementa `RegistroCAPA`.
- **GATE-SEG-INMETRO-PRAZO-1** (P-OS-S6) — cláusula `consequential regulatory damages` cobre prazo INMETRO de equipamento de cliente final do tenant.
- **GATE-SEG-CYBER-1** (P-OS-S2) — cláusula sensitive data art. 11 na apólice Cyber.
- **GATE-SEG-EO-1** (P-OS-S3, P-OS-S4) — franquia R$ 5k wrongful billing + software validation defect upstream.

---

## ACEITES (confirmação, sem mudança estrutural)

- **P-OS-R8** — dispensa + no-show em atividade calibração cumpre cl. 7.8.1.2 ISO 17025 via termo PDF + portal-cliente. Reforço cosmético no termo: "comunicação alternativa via portal-cliente (link/QR)".

---

## Decisões pendentes do Roldão

Antes de partir para P3 (matriz reconciliação) + atualizar a spec.md, **3 decisões dependem do Roldão**:

| Decisão | Origem | Opções | Recomendação default |
|---|---|---|---|
| **D-M3-1: Numeração OS aceita buracos?** | P-OS-T2 | (A) sequence global + unique composto, buracos aceitos / (B) tabela `numerador_os` com `SELECT FOR UPDATE`, gap-less | **(A)** padrão SaaS; Receita não exige; ADR-0056 nova |
| **D-M3-2: Janela watchdog cal-link** | P-OS-R6 | (A) 72h alerta + 15 dias NC (recomendação RBC) / (B) 24h alerta + 72h NC (default da spec atual) | **(A)** mais alinhado à realidade de bancada laboratório calibração |
| **D-M3-3: Feature flag dogfooding bloqueia produção sem BPT?** | P-OS-S1 | (A) DoD inclui flag bloqueante; M3 não vai para produção sem BPT / (B) DoD não inclui; risco aceito | **(A)** prática mínima de segurabilidade — CC art. 627 depositário |

---

## Decisão arquitetural geral

- **Hooks já cobrem o saneamento estrutural** (vigência, soft-delete, FK anonimização, biometria-key, os-conclusao-terminais, spec-ac-binario, bus-envelope-validator v10).
- **Eventos via `audit/event_helpers.publicar_evento`** (helper único Marco 1+2) — M3 herda; hook `event-helper-unico.sh` valida.
- **Predicates authz herdam de ADR-0012** — extensão necessária: `rt_competencia_cobre(user_id, grandeza, data)` + `tenant_dentro_escopo_acreditado(...)` + `pode_estender_janela_cal_link_atividade(...)` + `pode_dispensar_aceite(...)` + `pode_criar_os_produtiva_balancas(...)`.

---

## Próximo passo (P3 — matriz reconciliação)

Após decisões D-M3-1, D-M3-2, D-M3-3 do Roldão:

1. **Atualizar spec.md** absorvendo os 6 BLOQUEANTE + 12 MÉDIO INV-RITUAL-001 (retrofit em §3.1, §3.2, §6.1, §6.2, §9, §12, §13, §14).
2. **Criar ADR-0056** (numeração OS) se D-M3-1 = (A).
3. **PR contra `docs/dominios/operacao/modulos/os/prd.md`** com ACs novos (AC-OS-001-7, AC-OS-001-8, AC-OS-002b-4, AC-OS-003-6, AC-OS-004-7, AC-OS-005-5, AC-OS-013-5).
4. **PR contra REGRAS-INEGOCIAVEIS.md** com INVs novos (INV-OS-ATIV-005-EXEC-COMP, INV-OS-ANAL-001, INV-OS-CONSBIO-001, INV-OS-NUM-001).
5. **PR contra ADR-0012** (predicates novos) + ADR-0028 (cláusulas seguráveis rev 2).
6. **Matriz reconciliação** (`docs/faseamento/M3-os/matriz-reconciliacao.md`): PRD ↔ spec ↔ plan — zero conflito.
7. **tasks.md** com ~100 T-OS-NNN endereçando 100% dos AC + INVs + sagas + GATEs.
8. **Implement** (fases) + **P5** (10 auditores Família 5).
