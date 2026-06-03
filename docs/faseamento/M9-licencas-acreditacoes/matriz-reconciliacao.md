---
owner: agente-ia
revisado-em: 2026-06-03
proximo-review: 2026-09-03
status: stable
diataxis: reference
audiencia: [agente, auditor, tech-lead, consultor-rbc]
marco: M9-licencas-acreditacoes
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/M9-licencas-acreditacoes/spec.md
  - docs/faseamento/M9-licencas-acreditacoes/plan.md
  - docs/faseamento/M9-licencas-acreditacoes/tasks.md
  - docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de reconciliação spec↔código — M9 `metrologia/licencas-acreditacoes`

> Último módulo do bloco metrologia da Wave A (5º). Fecha o ciclo com o M8 populando
> o cache `Tenant.acreditacao_vigencia_fim` (ADR-0079). Molde M7 §8.

## 1. US ↔ AC ↔ INV ↔ ADR ↔ Hook ↔ código

| US | ACs | INV | ADR | Hook validador | Arquivo de código | Status |
|----|-----|-----|-----|----------------|-------------------|--------|
| US-LIC-001 Cadastrar documento regulatório (+ anexo) | AC-LIC-001-1/2/3 | INV-LIC-ANEXO-001 / INV-LIC-PERFIL-001 | 0030/0031/0067 | **lic-anexo-obrigatorio-check** + **lic-perfil-cgcre-check** | `application/.../cadastrar_documento_regulatorio.py` + `domain/.../entities.py`/`transicoes.py` + migrations 0001 | ✅ |
| US-LIC-001 AC-4 Promover perfil A (cadastra Licença CGCRE + `aplicar_evento_cgcre`) | AC-LIC-001-4 | INV-LIC-VIG-SYNC-001 / INV-LIC-PERFIL-001 | 0079/0067 | **tenant-perfil-imutavel-check** (estendido D-LIC-8) | `application/.../promover_perfil_a.py` + `infrastructure/.../eventos_cgcre.py` + `tenant/migrations/0012` | ✅ (D-LIC-4 atômico) |
| US-LIC-002 Alertas de vencimento (D-90/60/30/15/7) | AC-LIC-002 | INV-LIC-WORM-001 (alerta idempotente) | 0030/0060 | — (UNIQUE migration) | `application/.../jobs/verificar_alertas_licencas.py` + command `verificar_alertas_licencas.py` + refino `application/tenant/jobs/verificar_vigencia_acreditacao_perfil_a.py` | ✅ |
| US-LIC-003 Bloqueio por documento vencido (2 fronteiras D-LIC-5) | AC-LIC-003-1/2/3/4/5 | **INV-LIC-BLOQUEIO-001** / INV-033 | 0079/0073 | **lic-emergencial-a3-check** | `domain/.../transicoes.py` (`fronteira_bloqueio`/`validar_modo_emergencial`) + `application/.../acionar_modo_emergencial.py` + `application/.../verificar_signatario.py` + `query_service.signatario_apto_em` | ✅ (rebaixa via cache; hard-block emissão = GATE Wave B) |
| US-LIC-003 Sincronização Licença(CGCRE)→cache (fecha gate M8) | AC-LIC-003-1 (rebaixa) | **INV-LIC-VIG-SYNC-001** | 0079 | **tenant-perfil-imutavel-check** | `application/.../renovar_documento.py` (`RenovarVigenciaCgcrePort`) + `infrastructure/.../eventos_cgcre.py` (`renovar_vigencia`) + `query_service.vigencia_fim_acreditacao_cgcre` | ✅ (GATE-CER-CGCRE-VIG-DATA-POPULAR FECHADO) |
| US-LIC-004 Histórico versionado (revisões append-only) | AC-LIC-004 | INV-LIC-WORM-001 | 0031 | — (trigger WORM) | `infrastructure/.../views.py` (`historico`) + `serializers.serializar_historico_revisoes` + `repositories.DjangoRevisaoRepository.listar_por_documento` + migration 0003 (trigger) | ✅ |
| US-LIC-005 ART/RRT do RT (vínculo + 409 hard) | AC-LIC-003-5 | INV-LIC-BLOQUEIO-001 | 0073 | **lic-emergencial-a3-check** (indireto) | `application/.../verificar_signatario.py` + `infrastructure/.../views.py` (`signatario_apto`) + `query_service.documentos_signatario_vencidos_em` + enum `bloqueia_assinatura_hard` | ✅ (read-model; hard-block emissão Wave B) |

## 2. INV-LIC-* ↔ teste nomeado (TST-004) ↔ enforcement

| INV | Enforcement real | Teste (cita o ID) | Hook (camada A) |
|-----|------------------|-------------------|-----------------|
| INV-LIC-PERFIL-001 | `validar_tipo_x_perfil` no use case `cadastrar` (perfil server-side ADR-0067); D → 403 | `TestINV_LIC_PERFIL_001` + `test_m9_licencas_api_p2` (CGCRE perfil D 403) | **lic-perfil-cgcre-check** |
| INV-LIC-ANEXO-001 | `validar_anexo` no use case (sha256 server-side) + CHECK/entidade; vazio → 422 | `TestINV_LIC_ANEXO_001` + `test_m9_licencas_use_cases_p2` | **lic-anexo-obrigatorio-check** |
| INV-LIC-VIG-SYNC-001 | cache mantido só via `aplicar_evento_cgcre`; `cache == fonte` (não-drift) | `TestINV_LIC_VIG_SYNC_001` + **`test_licencas_nao_drift`** (promover+renovar) | **tenant-perfil-imutavel-check** (estendido) |
| INV-LIC-WORM-001 | trigger PG WORM `revisao_documento`/`evento_emergencial_licenca` (UPDATE/DELETE RAISE) | `TestINV_LIC_WORM_001` + `test_inv_lic_p2_schema_triggers` | audit-immutability-check |
| INV-LIC-BLOQUEIO-001 | `fronteira_bloqueio` (REBAIXA vs HARD) + `signatario_apto` + `validar_modo_emergencial` | `TestINV_LIC_BLOQUEIO_001` + `test_m9_licencas_fatia4_p4` | **lic-emergencial-a3-check** |

## 3. Hooks novos M9 Fatia 4 (camada A pré-commit)

| Hook | INV | Criado | Casos `_test-runner` | Status |
|------|-----|--------|----------------------|--------|
| lic-anexo-obrigatorio-check.sh | INV-LIC-ANEXO-001 | Fatia 4 | 5 (LAO1..5) | ✅ |
| lic-perfil-cgcre-check.sh | INV-LIC-PERFIL-001 | Fatia 4 | 6 (LPC1..6) | ✅ |
| lic-emergencial-a3-check.sh | INV-033 / INV-LIC-BLOQUEIO-001 | Fatia 4 | 5 (LEA1..5) | ✅ |
| tenant-perfil-imutavel-check.sh (estendido) | INV-LIC-VIG-SYNC-001 | Fatia 1c (D-LIC-8) | 3 (estendidos) | ✅ |

## 4. Entregas por fase

| Fase | Entrega | Verificação |
|------|---------|-------------|
| 1a | domínio puro (enums + 5 entidades + transições WORM + validações + repository Protocols) | 35 testes puros |
| 1b | schema infra (path aninhado ADR-0072) — 5 tabelas + 5 migrations RLS v2/WORM/grants/seed + UNIQUE alertas + mappers/repositories/query_service + drill | 11 testes PG-real + drill |
| 1c | extensão `tenant/0012` (`aplicar_evento_cgcre` +vigência +`renovacao_vigencia_cgcre`) + hook estendido | 4 testes função PG + 3 casos hook |
| 2 | use cases cadastrar/renovar/promover(D-LIC-4 atômico)/acionar-emergencial + ViewSet REST + idempotência + eventos WORM + ADR-0079 promovida | 52 puros + 8 API + drill 42/42 |
| 3 | sync Licença(CGCRE)→cache no renovar + job alertas (D-90..7) + refino job perfil A + **teste não-drift** | 30 puros + 14 PG-real (não-drift + reverde M8) |
| 4 | US-LIC-004 histórico + US-LIC-005 ART/RRT (`signatario_apto`) + **P7** (INV-LIC-* + `TestINV_LIC_*` + 3 hooks) + retenção-matriz | 6 puros + 28 PG-real + hooks 527/527 |
| P8 | emenda PRD (AC-LIC-003-1/5 fronteiras D-LIC-5) + URS (ADR-0025 v2) + esta reconciliação | matriz + `--check` anti-drift OK |

## 5. GATEs do módulo

| GATE | Estado | Evidência / pendência |
|------|--------|------------------------|
| GATE-CER-CGCRE-VIG-DATA-POPULAR | ✅ FECHADO | Fatia 3 — promover/renovar populam `Tenant.acreditacao_vigencia_fim`; reverde M8 rebaixa real (`test_licencas_nao_drift`) |
| GATE-LIC-DRIFT | ✅ FECHADO | invariante `cache == fonte` provado end-to-end (`test_licencas_nao_drift`) |
| GATE-LIC-DRILL-LOCAL | ✅ entregue | drill `validar_licencas_acreditacoes` 42/42 + `test_inv_lic_p2_schema_triggers` (RLS/WORM/UNIQUE) PG-real |
| GATE-LIC-EMISSAO-HARDBLOCK | 🟡 Wave B | read-model `signatario_apto` entregue; consumo do 409 na emissão M8 = Wave B (TL-M9-07) |
| GATE-LIC-EMERGENCIAL-A3-CRIPTO | 🟡 Wave B | `assinatura_a3_id` registrado (fail-open lazy declarado); validação OCSP/LTV diferida |
| GATE-LIC-ESCOPO-SYNC | 🟡 resolvido | escopo vive na `Licenca` (fonte rica); vigência via cache D-LIC-2; M6/M8 leem escopo do evento WORM já existente — sem retrabalho |
| GATE-LIC-PDF | 🟡 Wave B | relatório/dossiê PDF real; núcleo entrega export estruturado |
| GATE-LIC-PQ | 🟡 pré-produção | smoke de produção |
| Validação cl. 7.11 (parecer RBC credenciado) | 🟡 pré-produção | `project_sem_contratacoes_externas_ate_producao` |

## 6. Pendências (não bloqueiam fechamento do módulo)

- **GATE-LIC-EMISSAO-HARDBLOCK** — o 409 hard de signatário inapto na emissão M8 entra
  em Wave B (a integração lê a porta `signatario_apto` já entregue). Hoje o M9 expõe o
  read-model; a emissão não consome.
- **GATE-LIC-EMERGENCIAL-A3-CRIPTO** — validação criptográfica da A3 do modo emergencial
  (OCSP/LTV) é Wave B; hoje fail-open lazy (registra `assinatura_a3_id`, como os demais módulos).
- **GATE-LIC-PDF** — relatório/dossiê consolidado real (Wave B).
- **Pendências externas** (diferidas — `project_sem_contratacoes_externas_ate_producao`):
  parecer RBC credenciado da validação cl. 7.11 + smoke de produção — pré-produção.

## 7. Veredito de reconciliação

Todas as 5 INV-LIC têm enforcement real + teste nomeado (TST-004) + (onde aplicável)
hook camada A. As 7 linhas de US/sub-US têm código + status ✅. Os 2 GATEs centrais
(GATE-CER-CGCRE-VIG-DATA-POPULAR + GATE-LIC-DRIFT) FECHADOS; o invariante de não-drift
`cache == fonte` provado end-to-end; reverde M8 confirma rebaixamento real. Pronto para P9.

## 8. P9 — ritual auditores roteados (INV-RITUAL-003) — FECHADO 2026-06-03

6 auditores roteados por risco (tenant/authz + WORM + REST path crítico + idempotência):
**6/6 PASS — ZERO CRÍTICO/ALTO/MÉDIO** (INV-RITUAL-001 satisfeito):

| Auditor | Veredito | Achado |
|---------|----------|--------|
| seguranca | ✅ PASS | perfil server-side em 3 camadas (ContextVar → app gate "A" fixo → função PG lê perfil persistido + RAISE); `tenant_id` explícito em todas as queries; raw cursor só `%s` named params; 3 hooks com override real; `signatario_apto` fail-closed correto. ZERO C/A/M |
| llm-correctness | ✅ PASS | docstrings fiéis ao corpo (signatario_apto / verificar_alertas / vigencia_fim_acreditacao); `Any` só na fronteira I/O DRF; testes não-tautológicos; refino job perfil A sem caminho morto; rastreabilidade US/AC/INV. ZERO C/A/M |
| produto | ✅ PASS | AC-LIC-003-1/5 emendados fiéis a D-LIC-5 e ao código; US-LIC-004/005 entregues; non-goals diferidos honestamente (PDF/A3/OCSP/e-mail = GATE Wave B, código não finge); zero scope creep; terminologia coerente; matriz/URS fiéis. ZERO C/A/M |
| qualidade | ✅ PASS | 5 INV-LIC com `TestINV_LIC_*` nomeada exercitando barreira real (puro/PG-real/trigger); asserts significativos; sem type:ignore/noqa/`\|\| true`; não-drift + reverde M8 cobrem path crítico; 16 casos hook + E2E das actions novas. ZERO C/A/M |
| observabilidade | ✅ PASS | OBS-001 (WORM em renovar/promover/cadastrar/emergencial + `tenant_perfil_historico`) + OBS-002 (log estruturado tenant_id+correlation_id no feliz e no `_falha`) atendidos; correlation_id real (chave idempotência). OBS-003 métrica = **CONCERN BAIXO** carryover M5-M8 rastreado GATE-OBS-METRIC-* (não bloqueia). ZERO C/A/M |
| idempotência | ✅ PASS | `renovar` mantém Idempotency-Key obrigatória; replay não re-executa o sync (vigência não avança 2×); sync atômico no `transaction.atomic`, `concluir_chave` fora do bloco, falha → rollback total; GET sem chave; job de alertas idempotente (UNIQUE + ignore_conflicts). ZERO C/A/M |

**Nenhum achado sobreviveu à verificação adversarial** (cada auditor leu o código real e confirmou
defesa em profundidade). Único débito = OBS-003 (métrica) BAIXO, idêntico ao carryover aceito de
M5-M8, rastreado por GATE-OBS-METRIC-* (Foundation F-C). INV-RITUAL-001 satisfeito.

**M9 `metrologia/licencas-acreditacoes` FECHADO — 5º e último módulo do bloco metrologia Wave A.**
Com ele, o bloco metrologia (padrões → escopos-cmc → procedimentos → certificados → licenças) está
completo (5/5).
