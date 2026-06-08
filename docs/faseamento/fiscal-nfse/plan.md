---
owner: agente-ia
revisado-em: 2026-06-08
proximo-review: 2026-09-08
status: draft
diataxis: reference
audiencia: [agente, auditor, advogado, tech-lead, consultor-rbc]
frente: fiscal-nfse
tipo: plan-faseamento
estado-ritual: ready-for-tasks
relacionados:
  - docs/faseamento/fiscal-nfse/spec.md
  - docs/faseamento/fiscal-nfse/reviews-consolidado.md
  - docs/faseamento/fiscal-nfse/T-FIS-000-investigacao.md
  - docs/adr/0008-fiscal-pluggable.md
  - docs/adr/0073-validacao-metrologica-no-use-case.md
  - docs/dominios/financeiro/modulos/fiscal/prd.md
---

# Plan de faseamento — frente `fiscal/NFS-e` (núcleo de emissão agnóstica)

> **Entrada:** spec P1 (`spec.md`) + 3 revisões P2 (`reviews-consolidado.md`, 26
> achados, 3× APROVA COM CORREÇÕES) + decisão Roldão sobre terminologia perfil D.
> Este plan **incorpora os 26 achados**, crava decisões D-FIS-1..10, numera a família
> INV-FIS-001..009, define as emendas (ADR-0008 + PRD; **sem ADR nova**) e detalha as
> fatias com tasks T-FIS-NNN. **Saída:** `ready-for-tasks` → `/tasks` → implement
> Fatia 1a. Path raiz própria `src/{domain,application,infrastructure}/fiscal/`.

## 1. Decisões cravadas (D-FIS)

- **D-FIS-1 — VO agnóstico enxuto (TL-01).** O Protocol `FiscalProvider` e os VOs
  `InvoicePayload`/`InvoiceResult`/`InvoiceStatus` **não conhecem** NFS-e/SEFAZ/
  chave-de-acesso. Campos BR (`chave_acesso_44`, `numero`, `protocolo`,
  `codigo_municipal`) moram em `InvoiceResult.metadata: dict` / `raw_response`, **nunca**
  atributo nomeado. O VO **não valida** formato BR (responsabilidade do `Cliente`
  a montante, ADR-0017). A tradução BR só no serializer de infra. → **emenda ADR-0008**.
- **D-FIS-2 — Duas camadas de idempotência (TL-02/03).** (a) `Idempotency-Key` via
  **serviço central reusado** (`src.infrastructure.idempotencia.services_idempotencia`,
  molde M8) — replay de request; **nenhuma constraint nova**. (b) UNIQUE de **negócio**
  `(tenant_id, origem_id, versao)` + `existe_chave(...)` no use case — protege contra
  dupla emissão da mesma origem mesmo com Idempotency-Key diferente. A "UNIQUE no
  Idempotency-Key" da spec Fatia 1b **sai** do escopo.
- **D-FIS-3 — Máquina de estados final (TL-04).** `PENDING → AUTHORIZED | REJECTED`;
  `AUTHORIZED → CANCELED`; **REJECTED e CANCELED terminais**. `consultar_status_nfse` é
  o **único** caminho `PENDING → terminal`. `network_timeout` ≠ estado da nota:
  **nenhuma persistência** de `NotaFiscalServico` + `falhar_chave` + 503/504 (erro de
  transporte, não estado). Nova tentativa após REJECTED = **nova origem/nova nota**.
- **D-FIS-4 — Cancelamento = Padrão B (TL-05).** A entidade transiciona
  `AUTHORIZED → CANCELED` (a linha reflete o estado atual — toda consulta fiscal lê
  assim); a **imutabilidade probatória** vem do **evento WORM append-only**
  `fiscal.nfse_cancelada` na cadeia hash + XML de cancelamento canonicalizado
  (ADR-0029), **não** de proibir o UPDATE da coluna `status`. Advisory lock
  `pg_advisory_xact_lock` por `(tenant, nfse_id)` (molde `_advisory_lock_cert` do M8).
- **D-FIS-5 — Trava de perfil no use case + fonte de verdade RBC (TL-06 + RBC-01/02/03).**
  **CONVERGÊNCIA dos 3 revisores.** A validação metrológica roda **DENTRO do
  `emitir_nfse`** (regra de negócio com estado persistido — coerência **ADR-0073**),
  NÃO em `authz/predicates.py`. Composição:
  - **Camada DRF:** só `tenant_perfil_e(...)` server-side via ContextVar (reuso
    `perfil_tenant_helper.py` — defesa L6; barra quem nem tem perfil/está suspenso).
  - **Use case:** função PURA `documento_metrologico_obrigatorio_por_perfil(perfil,
    tipo_servico, certificado_carregado)` em `src/domain/fiscal/`, recebendo o
    `Certificado` **já carregado** (snapshot do M8) → decide compatibilidade
    RBC/simples/declaração/incompatível → erro de domínio (→422/403 na view).
  - **Fonte de verdade do vínculo RBC = `Certificado.tipo_acreditacao` snapshotado pelo
    M8.** O fiscal **NUNCA** reconsulta `Tenant.acreditacao_vigencia_fim`. A vigência
    RBC foi avaliada **uma única vez**, na data de emissão do certificado (M8,
    `acreditacao_vigente_para_rbc`, INV-CER-CGCRE-VIG-001). A NFS-e **herda** o snapshot
    (fatura serviço já prestado e documentado). → **emenda ADR-0008 + INV-FIS-PERFIL-002**.
- **D-FIS-6 — Borda simétrica perfil A + cert NAO_RBC (RBC-04).** Perfil A exige
  `certificado_id` **vinculado**, **não** `tipo_acreditacao==RBC` obrigatório. Um lab
  acreditado pode legitimamente faturar calibração não-RBC. AC novo: perfil A + cert
  NAO_RBC → emite normalmente (sem selo RBC na NFS-e). A obrigatoriedade RBC do perfil A
  é sobre *capacidade*, não sobre *todo certificado*.
- **D-FIS-7 — Terminologia perfil D = "calibração" (decisão Roldão 2026-06-08).** O
  `tipo_servico` perfil D usa **"calibracao"** (termo simples, sem sufixo `_basica`) —
  Roldão decidiu (regra #0.5 caso B, terminologia que o cliente lê). Razão de produto:
  "calibração" sozinha é serviço comercial genérico; só "calibração **RBC/acreditada**"
  exige acreditação. **Invariante anti-uso-indevido permanece (RBC-05/06):**
  `service_description` e campos impressos da NFS-e **proibidos** de conter
  "RBC"/"ISO 17025"/"acreditada"/"acreditado" para perfis B/C/D; a flag
  `em_preparacao_para_rbc` (perfil C) é **metadado interno**, proibida na descrição.
  Hook `fiscal-anti-rbc-em-descricao`. → AC-FIS-001-9 emendado (remove `_basica`).
- **D-FIS-8 — Mock no domínio, breaker na infra (TL-07).** `MockFiscalProvider`
  (determinístico, 4 modos, sem I/O) vive em `src/domain/fiscal/` (implementação de
  referência do Protocol). `CircuitBreakerFiscalProvider` (`pybreaker`, diferido) vive
  em `src/infrastructure/fiscal/` como wrapper. O use case **sempre recebe um
  `FiscalProvider` injetado** — agnóstico de qual implementação. Hook anti-import cobre
  `plugnotas*`, `focus*` **e** `pybreaker` fora de `infrastructure/fiscal/`.
- **D-FIS-9 — Evento ao outbox, nome lowercase (TL-dec7).** `fiscal.nfse_emitida` vai ao
  **outbox** (`outbox=True`) porque tem consumer cross-módulo previsto (`contas-receber`,
  inexistente → fica drenável, seam pronto). Nome **lowercase** `fiscal.nfse_emitida`/
  `fiscal.nfse_cancelada` (CHECK do `bus_outbox`). Eventos da cadeia hash WORM:
  `Fiscal.NFSeEmitida`/`Fiscal.NFSeCancelada` (probatórios, append-only).
- **D-FIS-10 — Retenção 5a + nota prudencial; PII em 2 regimes (FIS-J-02/03/04/05/07).**
  Prazo legal = **5 anos** (art. 173/174 CTN + art. 195 §único CTN + legislação
  municipal ISS), **não** 10a fiscal autônomo; nota prudencial até 10a quando o XML
  compõe audit de path sensível. NFS-e + XML = **zona B** (ADR-0021):
  **INV-FIS-RETENCAO-001**. PII em 2 objetos/2 regimes: `InvoicePayload`→provider = PII
  clara (base art. 7º II, só a operador sob DPA, diferido); evento WORM = só
  `cliente_referencia_hash` (ADR-0064). Cadeia LGPD: tenant=controlador, Aferê=operador
  (art. 39), BaaS=sub-operador (art. 39 §único).

## 2. Emendas (sem ADR nova)

- **Emenda ADR-0008** (Onda fiscal-nfse Wave A): (a) fronteira fiscal↔M8 (D-FIS-5 — vínculo
  RBC do snapshot, nunca reconsulta Tenant); (b) VO agnóstico (D-FIS-1 — campos BR em
  `metadata`); (c) **14 cláusulas** mínimas do contrato BaaS (substituem as 6 da §5 —
  ver §5 Gates).
- **Emenda PRD fiscal** §11 + §7: predicate roda no **use case** (D-FIS-5, ADR-0073),
  não em `authz/predicates.py`; AC-FIS-001 ganha borda perfil A+NAO_RBC (D-FIS-6),
  anti-RBC na descrição (D-FIS-7); AC-FIS-001-9 remove `_basica` (D-FIS-7).
- **ADR-0073** citada como precedente — **não reabrir**.

## 3. Invariantes — família INV-FIS-* (numeração definitiva)

- **INV-FIS-001 (perfil server-side, use case).** Emissão de NFS-e `tipo_servico` que
  exige documento metrológico valida compatibilidade `perfil × Certificado.tipo_
  acreditacao` **dentro do use case** (ADR-0073); perfil lido **server-side via
  ContextVar, NUNCA do payload** (defesa L6); incompatível → 422/403 fail-closed.
  (formaliza INV-INT-001 do PRD; ex-INV-FIS-PERFIL-001 da spec)
- **INV-FIS-002 (fonte de verdade RBC).** O vínculo RBC da NFS-e provém
  **exclusivamente** do `Certificado.tipo_acreditacao` snapshotado pelo M8; a NFS-e
  **nunca** reavalia a vigência da acreditação nem reconsulta `Tenant.acreditacao_
  vigencia_fim`. (D-FIS-5; ex-INV-FIS-PERFIL-002)
- **INV-FIS-003 (porta agnóstica).** Domínio/use case **nunca** importam SDK de
  fornecedor; toda emissão passa pela porta `FiscalProvider`. `import plugnotas*`/
  `focus*`/`pybreaker` só em `infrastructure/fiscal/`. (hook de fronteira; D-FIS-8)
- **INV-FIS-004 (WORM).** `NotaFiscalServico` emitida + eventos `Fiscal.NFSeEmitida`/
  `Fiscal.NFSeCancelada` na cadeia hash são append-only (WORM Padrão B); cancelamento é
  **transição de estado + evento append-only**, não UPDATE destrutivo; XML/JSON
  probatório canonicalizado (ADR-0029) + hash versionado (ADR-0064). (D-FIS-4)
- **INV-FIS-005 (idempotência de negócio).** `emitir_nfse` é idempotente: (a)
  `Idempotency-Key` (serviço central) — replay de request; (b) UNIQUE
  `(tenant_id, origem_id, versao)` + `existe_chave` — dupla emissão da mesma origem →
  409 retorna nota existente. (D-FIS-2/3)
- **INV-FIS-006 (cross-tenant).** Payload referenciando cliente/cert de outro tenant →
  bloqueio hard anti-oracle (reusa INV-TENANT-001; AC-FIS-001-4).
- **INV-FIS-007 (anti-RBC na descrição).** `service_description` + campos impressos da
  NFS-e perfis B/C/D **proibidos** de conter "RBC"/"ISO 17025"/"acreditada"/"acreditado";
  flag `em_preparacao_para_rbc` é metadado interno. (D-FIS-7; RBC-05/06; cl. 8.1.3)
- **INV-FIS-008 (retenção zona B).** NFS-e emitida + XML probatório = zona B (ADR-0021);
  pedido de eliminação do titular = recusa fundamentada (art. 16 I LGPD); anonimização
  só **após** o prazo fiscal de 5 anos, preservando dados fiscais obrigatórios. (D-FIS-10)
- **INV-FIS-009 (PII em 2 regimes).** `InvoicePayload` ao provider = PII clara (base
  art. 7º II, só a operador sob DPA); evento WORM = só `cliente_referencia_hash`
  (ADR-0064) — PII clara **nunca** vaza para a trilha de eventos. (D-FIS-10; FIS-J-05)
- **Reusadas:** INV-INT-001, INV-FIS-CR-001 (evento dispara título — consumer diferido),
  INV-007/008 (audit + contingência — contingência diferida), INV-TENANT-001..004,
  INV-TENANT-PERFIL-001/003/004, INV-HMAC-001..005, INV-DOC-CANON-001, INV-ANON-001..004.

## 4. Fatias + tasks (T-FIS-NNN)

### Fatia 1a — domínio puro (zero Django)
- **T-FIS-010** VOs `InvoicePayload`/`InvoiceResult`/`InvoiceStatus` (PENDING/AUTHORIZED/
  REJECTED/CANCELED) — agnósticos, campos BR em `metadata` (D-FIS-1).
- **T-FIS-011** porta `FiscalProvider` (Protocol: `emit_invoice`/`cancel_invoice`/
  `query_status`/`store_xml`/`supported_countries`/`health_check`).
- **T-FIS-012** `MockFiscalProvider` — 4 modos determinísticos por hash do payload
  (`always_authorize`/`always_reject`/`pending_then_authorize`/`network_timeout`).
- **T-FIS-013** entidade `NotaFiscalServico` + máquina de estados (D-FIS-3) +
  transições WORM + canonicalização (ADR-0029) + hash versionado (ADR-0064).
- **T-FIS-014** função pura `documento_metrologico_obrigatorio_por_perfil(perfil,
  tipo_servico, certificado)` (D-FIS-5/6) + erros de domínio.
- **T-FIS-015** repository Protocols + testes puros (Fakes).

### Fatia 1b — schema (infra)
- **T-FIS-020** model `nota_fiscal_servico` (achatada, colunas tipadas) + migration
  RLS v2 + WORM Padrão B (triggers anti-mutação respeitando D-FIS-4: status mutável por
  transição; eventos append-only) + grants.
- **T-FIS-021** UNIQUE de negócio `(tenant_id, origem_id, versao)` (D-FIS-2) + seed
  authz `fiscal.*` (emitir/cancelar/consultar/retrieve).
- **T-FIS-022** mappers + repositories aninhados + `existe_chave(...)`.
- **T-FIS-023** drill `validar_fiscal_nfse` (colunas/RLS/WORM/grants/UNIQUE) + teste
  schema PG-real (RLS cross-tenant UNHAPPY + WORM).

### Fatia 2 — use cases + REST
- **T-FIS-030** `emitir_nfse` — carrega Cliente (customer_taxid/name) + Certificado
  (snapshot RBC) + amount input → `tenant_perfil_e` (DRF, antes) → valida compatibilidade
  no use case (D-FIS-5) → chama provider injetado → persiste + evento WORM cadeia +
  outbox `fiscal.nfse_emitida` (D-FIS-9) + stub `store_xml` → idempotência 2 camadas.
- **T-FIS-031** `cancelar_nfse` (motivo ≥30ch + janela 24h + advisory lock + transição
  CANCELED + evento append-only) + `consultar_status_nfse` (PENDING→terminal).
- **T-FIS-032** `NotaFiscalServicoViewSet` (emitir/cancelar/consultar/retrieve) +
  ACTION_MAP/`get_authz_action` + Idempotency-Key (serviço central) + perfil server-side
  + serializer traduz `metadata` BR (D-FIS-1) — molde M8.
- **T-FIS-033** testes: API E2E (happy mock + perfil incompatível 403 + perfil A NAO_RBC
  ok + cross-tenant + idempotência + PENDING→AUTHORIZED via consultar + timeout 503).

### Fatia 3 — P7 (REGRAS + hooks + matrizes)
- **T-FIS-040** família INV-FIS-001..009 em `REGRAS-INEGOCIAVEIS.md` +
  `tests/regressao/test_inv_fis_classes_nomeadas.py` (`TestINV_FIS_*`, TST-004).
- **T-FIS-041** hooks: `fiscal-perfil-server-side-check` (INV-FIS-001 — perfil nunca do
  payload) + `fiscal-provider-import-fronteira-check` (INV-FIS-003 — anti-import SDK +
  pybreaker) + `fiscal-anti-rbc-em-descricao` (INV-FIS-007) + casos `_test-runner`.
- **T-FIS-042** `retencao-matriz.md`: corrigir citação (art. 173/174 + 195 §único CTN +
  ISS municipal — FIS-J-02) + nota prudencial 10a (FIS-J-03) + linha NFS-e zona B.
- **T-FIS-043** `matriz-feature-perfil.md`: linhas US-FIS por perfil (A RBC obrigatório /
  B-C-D documento × perfil / anti-RBC descrição).

### P8/P9
- **T-FIS-050** matriz-reconciliacao (molde M7, 8 seções) + emenda PRD (AC núcleo vs
  diferido; D-FIS-6/7; predicate no use case) + emenda ADR-0008 (D-FIS-1/5 + 14 cláusulas).
- **T-FIS-051** P9 auditores roteados (INV-RITUAL-003: + **auditor-supplychain** pela
  porta agnóstica/futura dep `pybreaker`/`plugnotas-sdk` + **auditor-conformidade-lgpd**
  pelo PII do tomador + seguranca/llm/produto/idempotencia/observabilidade).

## 5. Gates rastreados (não bloqueiam o núcleo — pré-produção)

- **GATE-FIS-PLUGNOTAS-REAL** / **GATE-FIS-FOCUS-REAL** — adapters reais + sandbox E2E
  (pagos; `project_sem_contratacoes_externas_ate_producao`).
- **GATE-FIS-B2-XML** — `store_xml` em B2 Object Lock (stub agora).
- **GATE-FIS-SMOKE-TRIMESTRAL** — cron + drill de chaos swap primary→fallback sob carga
  (tech-lead: não fecha só em code review).
- **GATE-FIS-CIRCUIT-BREAKER** — wrapper `pybreaker` primary→fallback (infra).
- **GATE-FIS-A3-OCSP** — A3/OCSP real do tenant (US-FIS-001 AC-2/6; depende de
  `seguranca/certificados-digitais`, ADR-0048/0046).
- **GATE-FIS-CONTRATO** — minuta do contrato BaaS **escrita agora** (14 cláusulas
  abaixo), **assinada só pré-produção** + revisão advogado OAB. Cobre só **Aferê↔BaaS**
  (ToS/DPA Aferê↔tenant = frente billing-saas).
  1. SLA ≥ 99,5%/mês + crédito; 2. DPA back-to-back (art. 39); 3. aviso ≥90d reajuste
  acima IPCA; 4. aviso ≥180d descontinuação; 5. direito de retirada de TODOS os XMLs
  (XSD); 6. sub-processadores transparentes + objeção; 7. papel LGPD explícito
  (sub-operador, vedado uso secundário); 8. resp. por erro de transmissão vs conteúdo
  fiscal (tenant responde pelo conteúdo); 9. notificação de incidente ≤24h; 10. direito
  de auditoria / SOC 2-ISO 27001; 11. retenção/devolução ao término; 12. localização
  dos dados / transferência internacional (art. 33); 13. lei BR + foro; 14. limitação
  de resp. + seguro RC profissional do BaaS.
- **Diferidos Wave B/V2:** contingência US-FIS-002, CC-e US-FIS-004, inutilização
  US-FIS-005, devolução US-FIS-009, ajuste extemporâneo US-FIS-010, tabelas fiscais
  US-FIS-008, export contador US-FIS-006, cutover drill US-FIS-CUT-001, CT-e/NFC-e
  (ADR-0049), farma TOP-3/BPF (V2-V3).

## 6. Confirmações metrológicas (consultor-rbc)

- Fiscal **só LÊ** o vínculo (`certificado_id`/`declaracao_id`); não emite, não recalcula
  incerteza, não estabelece/verifica rastreabilidade. **NIT-DICLA-030 N/A** (M4/M5/M8).
- Perfil D `declaracao_calibracao_basica_id` = vínculo fiscal aceitável (não invoca
  acreditação) — condicionado a INV-FIS-007 (terminologia).

**Próximo:** `/tasks` (detalha T-FIS-010..051 com AC binário por task) → implement
Fatia 1a → … → P9 auditores. Reconciliação final em `matriz-reconciliacao.md` (P8).
