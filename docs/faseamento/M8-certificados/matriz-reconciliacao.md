---
owner: agente-ia
revisado-em: 2026-06-01
proximo-review: 2026-09-01
status: stable
diataxis: reference
audiencia: [agente, auditor]
marco: M8-certificados
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/M8-certificados/spec.md
  - docs/faseamento/M8-certificados/plan.md
  - docs/faseamento/M8-certificados/tasks.md
  - docs/dominios/metrologia/modulos/certificados/prd.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de reconciliação spec↔código — M8 `metrologia/certificados`

> **Pra quê:** provar, item por item, que cada US/AC/INV da spec do núcleo de **emissão
> metrológica** virou código real + teste + hook, e apontar o arquivo. Pré-requisito do
> ritual P9 (reconciliação antes dos auditores roteados — INV-RITUAL-003).
> **Escopo desta frente:** núcleo lógico/metrológico da emissão (reconciliação
> ponto-a-ponto `pontos ⊆ declarada ⊆ escopo` + `U(ponto) ≥ CMC(ponto)`, numeração dual,
> snapshots WORM, perfil server-side, reemissão versionada). **PDF/A3/OCSP/TSA/portal/
> recall/export DIFERIDOS** (infra externa — GATE-CER-* Wave A).
> Path híbrido **ADR-0078**: tabela física `certificados` achatada em
> `src/infrastructure/certificados/` (contrato de trigger INV-025); lógica de emissão no
> path aninhado `src/{domain,infrastructure}/metrologia/certificados/` (ADR-0072).

## 1. US ↔ AC ↔ INV ↔ ADR ↔ Hook ↔ código

| US | ACs | INV | ADR | Hook validador | Arquivo de código | Status |
|----|-----|-----|-----|----------------|-------------------|--------|
| US-CER-001 Gerar certificado (emissão metrológica lógica) | AC-CER-001-1/2/3/4/5 | **INV-CER-EMISSAO-001 / RECONCILIA-001..005 / PERFIL-001 / SNAPSHOT-PERFIL-001 / CGCRE-VIG-001 / RESSALVA-001 / PADRAO-VIG-001 / REGRA-DEC-001** | 0076/0074/0073/0077/0067/0024/0026 | **cert-reconcilia-fail-closed** · **cert-perfil-rbc-so-A** | `application/.../certificados/emitir_certificado.py` (atômico fail-closed) + `domain/.../certificados/reconciliacao.py` + `transicoes.py` + REST `infrastructure/metrologia/certificados/views.py::emitir` | ✅ |
| US-CER-001 (decisão RT por ponto) | AC-CER-001 (reconciliação) | INV-CER-RECONCILIA-003 + RESSALVA-001 + WORM-001 | 0075/0031 | cert-perfil-rbc-so-A | `application/.../certificados/decidir_ponto_reconciliacao.py` (pré-condição WORM, idempotente por ponto) + `domain/.../transicoes.py::aplicar_decisoes_rt` + REST `views.py::decidir_ponto` | ✅ |
| US-CER-003 Numeração sequencial inviolável | AC-CER-001-1 (numeração) | **INV-CER-NUM-001 / NUM-002** | 0056 (paralelo OS) | — (triggers PG) | VO `domain/.../certificados/numeracao.py` + tabela `numero_certificado_reservado` (migration 0008, TTL 5min, 3 triggers PG) + sequence `certificado_numero_seq` (0007) + advisory lock `repositories.py` | ✅ |
| US-CER-004 Reemissão versionada | AC-CER-004 | INV-CER-WORM-001 | 0031 (Padrão B) | — (trigger WORM) | `application/.../certificados/reemitir_certificado.py` (`v(N+1)`↔`v(N)`, motivo ≥50ch, `v(N)`→SUBSTITUIDA CAS por `revision`) + REST `views.py::reemitir` (advisory lock TL-A1) | ✅ |
| US-CER-013 Cert com equipamento baixado (paridade snapshot) | AC-CER-001-1 (snapshot) | INV-CER-WORM-001 + INV-025 | 0021/0031 | equipamento-imutabilidade-check | `emitir_certificado.py` (`snapshot_equipamento_json` herdado da calibração, imutável) + trigger cross-app `equipamento_imutabilidade_pos_cert_check` (M2, contrato ADR-0078) | ✅ |
| US-CER-001 (read-path WORM) | AC-CER-001-1 | **INV-CER-SNAPSHOT-CMC-001** | 0077/0067 | **cert-snapshot-nao-reconsulta** | REST `views.py::retrieve` (lê só snapshot persistido — NUNCA `cmc_para`/`tenant_perfil_e`) + serializer `serializers.py` | ✅ |

## 2. INV-CER-001..016 ↔ teste nomeado (TST-004) ↔ enforcement

> Família canônica (16 invariantes) em `REGRAS-INEGOCIAVEIS.md` §`INV-CER-*` (M8). Classes
> nomeadas em `tests/regressao/test_inv_cer_classes_nomeadas.py` (17 testes — a
> `TestINV_CER_SNAPSHOT_CMC_001` consolida o anti-reconsulta T-CER-052 com mock que FALHA
> se o `retrieve` chamar `cmc_para`/`tenant_perfil_e`).

| INV | Enforcement real | Teste (cita o ID) | Hook (camada A) |
|-----|------------------|-------------------|-----------------|
| INV-CER-EMISSAO-001 | `emitir_certificado` fail-closed (`cal.status is APROVADA`→422) + `existe_chave` idempotência + UNIQUE `(tenant,calibracao_id,versao)` | `TestINV_CER_EMISSAO_001` | — (use case puro) |
| INV-CER-RECONCILIA-001 | `reconciliar_pontos` (`FaixaMedicao.contem` — `∀ ponto ∈ faixa_declarada`; fora → `FORA_DECLARADA`) | `TestINV_CER_RECONCILIA_001` | **cert-reconcilia-fail-closed** |
| INV-CER-RECONCILIA-002 | `reconciliar_pontos` (`cobertura.avaliar_u_cmc` via porta `cmc_para`; `U<CMC` sem decisão → bloqueia) | `TestINV_CER_RECONCILIA_002` | **cert-reconcilia-fail-closed** |
| INV-CER-RECONCILIA-003 | `emitir_certificado` (`faixa_min/max` derivada dos pontos VÁLIDOS incluídos) + WORM trigger | `TestINV_CER_RECONCILIA_003` | — |
| INV-CER-RECONCILIA-004 | `reconciliar_pontos` (sort `ponto_calibracao` ASC antes do hash) + `reconciliacao_hash` | `TestINV_CER_RECONCILIA_004` | — (puro, replay cl. 7.11) |
| INV-CER-RECONCILIA-005 | `reconciliar_pontos` (`_indexar_orcamentos` lookup 1:1; duplicidade → `ORCAMENTO_PONTO_AMBIGUO`) | `TestINV_CER_RECONCILIA_005` | **cert-reconcilia-fail-closed** |
| INV-CER-NUM-001 | VO `NumeroCertificado` + tabela `numero_certificado_reservado` (TTL 5min) + 3 triggers PG (migration 0008) + advisory lock no repo | `TestINV_CER_NUM_001` | — (triggers PG) |
| INV-CER-NUM-002 | sequence `certificado_numero_seq` interna (0007, buracos OK) ≠ `numero_certificado` visível (0008, sem buracos) | `TestINV_CER_NUM_002` | — (triggers PG) |
| INV-CER-PERFIL-001 | view deriva perfil server-side (`tenant_perfil_e`); `tipo_acreditacao=RBC` NUNCA do payload (defesa L6) | `TestINV_CER_PERFIL_001` | **cert-perfil-rbc-so-A** |
| INV-CER-SNAPSHOT-PERFIL-001 | coluna `perfil_emissor_no_momento CHAR(1) NOT NULL` cravada no INSERT (emissão) + WORM trigger | `TestINV_CER_SNAPSHOT_PERFIL_001` | — (schema NOT NULL) |
| INV-CER-SNAPSHOT-CMC-001 | `retrieve` lê só snapshot persistido — NUNCA reconsulta `cmc_para`/`tenant_perfil_e` (WORM por leitura — TL-04) | `TestINV_CER_SNAPSHOT_CMC_001` (mock falha se reconsultar) | **cert-snapshot-nao-reconsulta** |
| INV-CER-REGRA-DEC-001 | `regra_decisao_snapshot` congelado na emissão (de `cal.regra_decisao` — cl. 7.8.6/ADR-0024) + WORM trigger | `TestINV_CER_REGRA_DEC_001` | — |
| INV-CER-WORM-001 | trigger WORM `certificado` (migration 0004) + `marcar_substituida` CAS por `revision`; DELETE bloqueado | `TestINV_CER_WORM_001` | audit-immutability-check (Padrão B) |
| INV-CER-CGCRE-VIG-001 | `acreditacao_vigente_para_rbc` no use case (rebaixa `cmc_efetivo=None` se vencida `>=`/suspensa por janela na data de emissão; `None`=fail-open lazy) | `TestINV_CER_CGCRE_VIG_001` | — (use case) |
| INV-CER-RESSALVA-001 | `exigir_ressalva_nao_rbc` no domínio (ponto `EMITIR_NAO_RBC_NO_PONTO` exige `ressalva_nao_rbc`) | `TestINV_CER_RESSALVA_001` | **cert-perfil-rbc-so-A** |
| INV-CER-PADRAO-VIG-001 | `validar_vigencia_padroes` no use case (cl. 6.5/NC-07; padrão vencido bloqueia RBC perfil A; ausente=fail-open lazy) | `TestINV_CER_PADRAO_VIG_001` | — (use case) |

## 3. Hooks novos M8 Fatia 3 (camada A pré-commit)

| Hook | INV | Criado | Casos `_test-runner` | Status |
|------|-----|--------|----------------------|--------|
| cert-reconcilia-fail-closed-check.sh | INV-CER-RECONCILIA-001/002/005 | Fatia 3 (`8617c37`) | 6 (CRFC1..6) | ✅ |
| cert-snapshot-nao-reconsulta-check.sh | INV-CER-SNAPSHOT-CMC-001 | Fatia 3 (`8617c37`) | 5 (CSNR1..5) | ✅ |
| cert-perfil-rbc-so-A-check.sh | INV-CER-PERFIL-001 / RESSALVA-001 | Fatia 3 (`8617c37`) | 6 (CPRA1..6) | ✅ |

Total `_test-runner`: **508/508 verdes / 64 hooks ativos** (491 + 17). Sentinela anti-drift
(`status-projeto.sh --check`): 3 hooks ↔ 17 casos ↔ 16 INV-CER ↔ 16 classes Test — verde
(hooks=64 casos=508 ADRs=79 INVs=139).

## 4. Entregas por fase

| Fase | Entrega | Verificação | Commit |
|------|---------|-------------|--------|
| #0 SAN-INCERTEZA-PONTO | retrofit M4 ADR-0077 (orçamento por ponto: domínio+schema migrations 0018/0019+use case+replay+drill 56/56) — `U(ponto)` por ponto pré-requisito da reconciliação | 72 testes SAN + replay golden cl. 7.11 + drill `validar_m4_calibracao` 56/56 | `81a90a5`/`1bed40c`/`6f60356`/`fab581b` |
| Fatia 0 reconciliação pura | `domain/.../certificados/{enums,erros,portas,reconciliacao}.py` — `reconciliar_pontos` COMPÕE FaixaMedicao.contem + avaliar_u_cmc + lookup 1:1 (INV-CER-RECONCILIA-005) + precedência FORA_DECLARADA>SEM_CMC>U_MENOR_CMC>RBC_OK | 14 testes puros | `1a94178` |
| Fatia 1a domínio puro | enums ciclo-vida + `reconciliacao_hash` (replica cadeia_pontos_hash ADR-0077) + entities (PontoReconciliadoSnapshot/CertificadoSnapshot/AnaliseReconciliacaoCertificado) + transicoes (RASCUNHO não-materializado; `validar_completude_decisoes_rt`) + repository Protocols | 18 testes puros | `aff9565` |
| Fatia 1b schema+adapters | tabela achatada ADR-0078 (6 migrations aditivas 0002-0008 — INV-025 INTOCADO; choice `substituida`; RLS v2; WORM Padrão B cert terminal imutável + ponto/análise append-only; grants; seed authz; sequence) + mappers/repositories aninhados + drill `validar_certificados` 34/34 | 13 testes schema PG-real + INV-025 14/14 sem regressão | `f0cd30d` |
| Fatia 1b-numeração | número visível sem buracos (tabela `numero_certificado_reservado` TTL 5min + 3 triggers PG + domínio puro + repo advisory-lock) | 13 testes PG | `7517473` |
| Fatia 2 use cases | `decidir_ponto_reconciliacao` (pré-condição WORM NC-03) + `emitir_certificado` ATÔMICO fail-closed (reconcilia ADR-0076→completude RT→aplica decisões→tipo RBC/NÃO-RBC→faixa válidos→snapshot+hash→salvar) | 14 testes Fakes (5 decidir + 9 emitir) | `0e26797` |
| Fatia 2b domínio+schema+REST | INV-CER-CGCRE-VIG-001 (`acreditacao_vigente_para_rbc`) + INV-CER-PADRAO-VIG-001 + `reemitir_certificado` + `Tenant.acreditacao_vigencia_fim` (0011) + fix-M4 `arredondamento_aplicado_regra` varchar(20)→(40) + adapters + CertificadoViewSet (emitir/reemitir/decidir/retrieve) | 57 testes M8 PG-real (8 REST end-to-end RBC com escopo real — fecha GATE-CAL-EMISSAO-RECONCILIA-FAIXA + GATE-ECMC-U-MAIOR-CMC) | `3414649`/`e038bb1`/`cd58ed4`/`a23f6ac`/`e04a113` |
| Fatia 3 (Blocos 1+3) | família `INV-CER-*` (16) em REGRAS (consolida placeholder INV-CER-NUM-001) + `TestINV_CER_*` (17) + 3 hooks + 17 casos `_test-runner` | TestINV_CER 17/17 + hooks 508/508 | `eec6428`/`8617c37` |
| Fatia 3 (Bloco 4 — P8) | matriz-reconciliacao (este doc) + emenda PRD/spec evento `CertificadoReconciliado` (T-CER-070, NC-08) + promoção ADR-0078 a aceito §11 AGENTS (T-CER-071) | grep `CertificadoEmitido` só Wave A/normativo + `--check` anti-drift OK | (este P8) |

## 5. GATEs do módulo

| GATE | Estado | Evidência / pendência |
|------|--------|------------------------|
| GATE-CAL-EMISSAO-RECONCILIA-FAIXA | ✅ FECHADO | reconciliação `pontos ⊆ declarada` + `faixa_certificado` dos válidos, leitura real de `faixa_calibrada_declarada` da calibração APROVADA + fail-closed `FAIXA_DECLARADA_AUSENTE` (ADR-0076) — 8 testes REST RBC end-to-end |
| GATE-ECMC-U-MAIOR-CMC | ✅ FECHADO | porta `cmc_para` injetada + `U(ponto) ≥ CMC(ponto)` via `avaliar_u_cmc` (ADR-0074 cond. 2 / INV-ECMC-009) |
| GATE-CER-CGCRE-VIG-DATA-POPULAR | 🟡 fail-open lazy | `acreditacao_vigente_para_rbc` ativo, mas `acreditacao_vigencia_fim is None` = fail-open; torna-se efetivo quando `licencas-acreditacoes` (Wave A) popular a data |
| GATE-CER-PADRAO-VIG-SNAPSHOT | 🟡 fail-open lazy | `validar_vigencia_padroes` ativo; vigência ausente/malformada no snapshot = fail-open até wiring M5 `padroes` (Wave A) |
| GATE-CER-DRILL-LOCAL | 🟡 parcial | drill `validar_certificados` 34/34 + 13 testes schema PG-real (RLS/WORM/INV-025/numeração) entregues; **comportamentais PG-real threaded** (imutabilidade cruzada equipamento INV-025 com cert REAL, numeração sem buraco concorrente, concorrência reemissão) = TRACK Wave A |
| GATE-CER-PDF / A3 / OCSP / TSA / PORTAL / QR / EMAIL / EXPORT / POSEMISSAO | 🟡 diferido | infra externa (motor PDF/A-3, Lacuna, OCSP/CRL, TSA-ITI, portal, QR público, EmailTemplateProvider, export ANVISA, recall/suspensão/errata) — todos rastreados Wave A; a emissão lógica produz o snapshot WORM imutável sobre o qual PDF/assinatura plugam depois |

## 6. Pendências (não bloqueiam fechamento do módulo)

- **GATE-CER-DRILL-LOCAL (comportamentais threaded)** — imutabilidade cruzada de
  equipamento (INV-025) com cert `status='emitido'` REAL inserido pela emissão (não stub),
  numeração visível sem buraco sob concorrência, concorrência de reemissão (CAS por
  `revision` + advisory lock TL-A1) = TRACK Wave A (PG-real threaded, padrão M4/M6/M7). O
  invariante WORM e a numeração já estão garantidos por trigger PG + UNIQUE + advisory
  lock e testados estruturalmente (13 testes schema + 34/34 drill).
- **Job de vigência sinaliza INCONSISTENCIA** quando `acreditacao_vigencia_fim` é NULL em
  tenant perfil A (RBC-Corr3 do consultor-rbc) — Wave A (`licencas-acreditacoes`).
- **Motivo do rebaixamento no evento WORM** (TL-M1) — distinguir [acreditação vencida vs
  suspensa vs perfil-nativo não-acreditado] no payload do evento — Wave A.
- **Achados BAIXO do P9 rastreados como GATE não-bloqueante** (resolver na Wave A — não
  são específicos do núcleo metrológico desta frente):
  - **GATE-IDEMP-REPLAY-TRANSITORIO** — `services_idempotencia._avaliar_existente` trata
    chave `falhada` como terminal; falha transitória (ex. 409 reserva expirada) trava retry
    com a MESMA chave por 24h. Camada de idempotência COMPARTILHADA (afeta todos os módulos)
    — mudança transversal Wave A/F-C, não no M8.
  - **GATE-IDEMP-REAPER-ORFAS** — crash entre commit do `atomic` e `concluir_chave` deixa
    chave `em_processo` órfã até TTL. Reaper/cron de recuperação = infra F-C (transversal).
  - **GATE-CER-DECISAO-RT-CADEIA** — publicar elo na cadeia hash central para a decisão WORM
    do RT (`decidir_ponto`). Hoje a decisão já é append-only/imutável por trigger (0004) +
    log estruturado; o elo central adicional é melhoria Wave A.
  - **AC-CER-001-5 materialização (perfil D)** — `Certificado.tipo = RELATORIO_AFERICAO` +
    sequência de numeração por tipo-de-documento = Wave A (frente UI/perfil D); nesta frente
    perfil D produz `NAO_RBC` derivado. O enum tem só RBC/NAO_RBC (`enums.py`).
  - **TL-M1** (já rastreado) — distinguir o MOTIVO do rebaixamento RBC→não-RBC [acreditação
    vencida vs suspensa vs perfil-nativo] no payload do evento WORM — Wave A.
- **Pendências escaladas a humano credenciado** (diferidas —
  `project_sem_contratacoes_externas_ate_producao`): homologação cl. 7.11 do motor de
  incerteza por ponto; dossiê RBC da reconciliação (partição rbc/não-rbc + decisões RT)
  para CGCRE; validação de método (proc não-normalizado) e parecer de exclusão de ponto;
  política "indicação única com s_pooled" (n=1 RBC) — todas pré-produção, revisão/
  assinatura humana legal. A frente entrega a lógica + snapshots probatórios + trilha WORM
  que as suportam.

## 7. Veredito de reconciliação

Todas as 16 INV-CER têm enforcement real + teste nomeado (TST-004, 17 classes) + (onde
aplicável) hook camada A (3 hooks, 17 casos). As 6 US do núcleo têm código + status. Os 2
GATEs centrais da frente (GATE-CAL-EMISSAO-RECONCILIA-FAIXA + GATE-ECMC-U-MAIOR-CMC)
FECHADOS com 8 testes REST RBC end-to-end usando escopo CMC real. Família INV-CER cravada
em REGRAS consolidando o placeholder histórico INV-CER-NUM-001 (sem ID duplicado). Evento
da frente alinhado (`CertificadoReconciliado`); fronteira com o evento normativo
`CertificadoEmitido` (cl. 7.8 / A3 Wave A) documentada (NC-08). ADR-0078 promovida a
aceito. Suíte: 508/508 hooks + ~74 testes M8 + 17 INV-CER + drill 34/34; reverde global
M4/M6/M7/SAN-INCERTEZA-PONTO sem regressão. **Pronto para P9.**

## 8. P9 — ritual auditores roteados (INV-RITUAL-003) — FECHADO 2026-06-01

6 auditores roteados por risco + **verificação adversarial de cada achado MÉDIO+** (um
verificador cético independente por achado, instruído a refutar). Dos 5 achados MÉDIO
levantados, **apenas 1 sobreviveu como MÉDIO** após a verificação; os demais foram
refutados (1 FALSO_POSITIVO) ou rebaixados a BAIXO. O único MÉDIO confirmado foi
**RESOLVIDO na causa-raiz** (regra "resolver TUDO crítico→baixo") — INV-RITUAL-001
satisfeito (zero MÉDIO+ remanescente).

| Auditor | Veredito | Achado | Verificação adversarial | Desfecho |
|---------|----------|--------|--------------------------|----------|
| seguranca | ✅ PASS | — | — | porta fail-CLOSED + RLS v2 (4 tabelas) + perfil server-side + retrieve sem reconsulta + WORM sem bypass + hooks ok; zero |
| llm-correctness | ✅ PASS | — | — | docstrings verazes, sem `Any` de escape, rastreabilidade INV-CER/US/AC; zero |
| idempotencia | ✅ PASS | 2 BAIXO | — | IDEMP-001 nos 3 POST + existe_chave/UNIQUE + advisory lock + CAS; 2 BAIXO de infra transversal → GATE rastreado |
| qualidade | 🟡 CONCERNS | 1 BAIXO (QLD-CER-01) | — | 16/16 INV testadas, anti-reconsulta provada por mutação, M4 reverde sem relaxamento; `type:ignore` com justificativa na linha acima → **RESOLVIDO** (movida p/ mesma linha) |
| produto | 🟡 CONCERNS | 2 MÉDIO + 1 BAIXO | ambos MÉDIO → **BAIXO** (drift de doc; comportamento real correto) | PROD-CER-01 (AC-CER-001-3 sem fronteira) **RESOLVIDO** (nota de fronteira); PROD-CER-02 (glossário) **RESOLVIDO** (+7 termos); PROD-CER-03 (RELATORIO_AFERICAO Wave A) **RESOLVIDO** (rastreado §6) |
| observabilidade | 🟡 CONCERNS | 3 MÉDIO + 1 BAIXO | OBS-1 → **FALSO_POSITIVO**; OBS-2 → **MÉDIO confirmado**; OBS-3 → **BAIXO** | OBS-2 (`_falha` sem log) **RESOLVIDO** (log.warning estruturado); OBS-3 (correlation_id no log sucesso) **RESOLVIDO**; OBS-4 (log decidir_ponto) **RESOLVIDO**; OBS-1 (rebaixamento "silencioso") refutado — observável via `tipo_acreditacao` no snapshot/evento (motivo no evento = TL-M1 rastreado) |

**Conserto causa-raiz do P9 (commit pós-auditoria):** `views.py` — log estruturado em
`_falha` (OBS-002, MÉDIO; `chave_id`=Idempotency-Key como correlador server-side),
`correlation_id` no log de sucesso de `_publicar_evento_cert`, log estruturado de sucesso
em `decidir_ponto`; `prd.md` AC-CER-001-3 nota de fronteira; `glossario.md` +7 termos
(RBC/não-RBC/Relatório de Aferição/capacidade interna/reconciliação/ressalva);
`test_m8_certificados_dominio_p1.py` justificativa `type:ignore` na mesma linha. Verificado:
ruff limpo, mypy zero erro novo (7 pré-existentes molde), 43/43 testes M8 (API+domínio+INV-CER)
verdes, hooks cert exit 0, 508/508 `_test-runner`.

**Veredito FINAL:** M8 `metrologia/certificados` (núcleo de emissão metrológica) **FECHADO**
— 3 PASS + 3 CONCERNS, todos os achados MÉDIO+ resolvidos na causa-raiz (1 MÉDIO + BAIXO),
demais BAIXO resolvidos ou rastreados como GATE não-bloqueante.
