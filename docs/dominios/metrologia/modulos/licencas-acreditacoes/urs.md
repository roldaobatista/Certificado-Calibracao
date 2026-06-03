---
owner: agente-ia
revisado-em: 2026-06-03
proximo-review: 2026-09-03
status: stable
diataxis: reference
audiencia: [agente, auditor, consultor-rbc, tech-lead]
modulo: metrologia/licencas-acreditacoes
tipo: validacao-software-cl-7.11
relacionados:
  - docs/adr/0025-validacao-software-iso-17025.md
  - docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md
  - docs/faseamento/M9-licencas-acreditacoes/matriz-reconciliacao.md
  - REGRAS-INEGOCIAVEIS.md
---

# Validação de software cl. 7.11 — `metrologia/licencas-acreditacoes` (URS/IQ/OQ/PQ)

> **ADR-0025 v2 (T-VAL-SW):** dossiê de validação do software que controla licenças,
> acreditações e vigência regulatória. Escopo cl. 7.11: o software **gere vigência,
> sincroniza o cache que classifica certificados RBC e bloqueia a assinatura sem
> signatário habilitado**. Perfil A = dossiê completo; B/C = IQ/OQ leve; D = drill
> estrutural. Validação formal por RT-vendor credenciado é **pré-produção**
> (`project_sem_contratacoes_externas_ate_producao`); este documento é a base redigida.

## 1. URS — Requisitos do usuário (alimentados pelas US do PRD)

| URS | Requisito (o que o laboratório exige do software) | Rastreio | Verificação |
|-----|---------------------------------------------------|----------|-------------|
| URS-LIC-01 | Registrar documento regulatório (licença/acreditação/ART/RRT/certidão) com **anexo probatório obrigatório** (sha256 server-side) | US-LIC-001 / AC-LIC-001-2 / INV-LIC-ANEXO-001 | OQ-01 |
| URS-LIC-02 | Só perfil A/B/C cadastra acreditação CGCRE; perfil é **server-side** (não forjável — defesa anti-fraude) | US-LIC-001 / AC-LIC-001-3 / INV-LIC-PERFIL-001 | OQ-02 |
| URS-LIC-03 | Vigência canônica (`vigencia_inicio ≤ vigencia_fim`, ADR-0030); status calculado (vigente/vence-em-breve/vencido/em-renovação) | US-LIC-001/002 / INV-VIG-001..004 | OQ-03 |
| URS-LIC-04 | Promover perfil regulatório (D→C→B→A) cadastrando a acreditação CGCRE **e** atualizando o cache do tenant **na mesma transação** (atômico) | US-LIC-001 AC-4 / INV-LIC-VIG-SYNC-001 / ADR-0079 | OQ-04 |
| URS-LIC-05 | Manter a vigência da acreditação no cache `Tenant.acreditacao_vigencia_fim` **exclusivamente** via função canônica (nunca alteração direta) — `cache == fonte` sem divergência | US-LIC-003 / INV-LIC-VIG-SYNC-001 | OQ-05 (não-drift) |
| URS-LIC-06 | Alertar o vencimento com antecedência (D-90/60/30/15/7), sem alerta duplicado | US-LIC-002 / AC-LIC-002 | OQ-06 |
| URS-LIC-07 | **Acreditação CGCRE vencida REBAIXA** a classificação RBC→não-RBC na emissão (não bloqueia com erro), via o cache que o módulo de certificados lê | US-LIC-003 / AC-LIC-003-1 / INV-LIC-BLOQUEIO-001 / INV-CER-CGCRE-VIG-001 | OQ-07 |
| URS-LIC-08 | **Signatário sem ART/RRT/e-CNPJ válido = inapto** a assinar qualquer certificado (cl. 6.2) — read-model `signatario_apto` | US-LIC-005 / AC-LIC-003-5 / INV-LIC-BLOQUEIO-001 | OQ-08 |
| URS-LIC-09 | Liberação em **modo emergencial** auditada: justificativa ≥100 chars + assinatura A3 + WORM + expira ≤7 dias; sobre CGCRE libera só não-RBC | US-LIC-003 / AC-LIC-003-2 / INV-033 | OQ-09 |
| URS-LIC-10 | **Histórico versionado imutável** (revisões append-only WORM) — nunca editar/excluir revisão anterior | US-LIC-004 / AC-LIC-004 / INV-LIC-WORM-001 | OQ-10 |
| URS-LIC-11 | Isolamento multi-tenant (RLS FORCE) — documentos de um tenant invisíveis a outro | transversal / INV-TENANT-001..003 | OQ-11 |

## 2. IQ — Installation Qualification (infraestrutura)

| IQ | Item verificado | Como |
|----|-----------------|------|
| IQ-01 | 5 tabelas (`documento_regulatorio`, `revisao_documento`, `alerta_vencimento`, `bloqueio_operacional`, `evento_emergencial_licenca`) com **RLS FORCE + 4 policies** | drill `validar_licencas_acreditacoes` + `test_inv_lic_p2_schema_triggers` |
| IQ-02 | Triggers WORM Padrão B (revisão/evento append-only; documento identidade imutável + revogação one-shot) instalados | drill (check triggers) + `test_inv_lic_p2_schema_triggers` |
| IQ-03 | Grants `app_user` (SELECT/INSERT/UPDATE/DELETE) presentes nas 5 tabelas | drill (check grants) |
| IQ-04 | Função `aplicar_evento_cgcre` (14 params, +`renovacao_vigencia_cgcre`) instalada e `SECURITY DEFINER` | `test_m9_aplicar_evento_cgcre_vigencia` |
| IQ-05 | UNIQUE idempotência de alertas `(tenant, documento, janela_dias)` | `test_inv_lic_p2_schema_triggers` |

## 3. OQ — Operational Qualification (cenários funcionais entregues)

| OQ | Cenário | Teste automatizado | Resultado |
|----|---------|--------------------|-----------|
| OQ-01 | Cadastro sem anexo → 422; com anexo → 201 | `test_m9_licencas_use_cases_p2` / `TestINV_LIC_ANEXO_001` | ✅ |
| OQ-02 | CGCRE perfil D → 403; perfil A → OK | `test_m9_licencas_api_p2` / `TestINV_LIC_PERFIL_001` | ✅ |
| OQ-03 | Status calculado nas 4 bordas (vigente/vence-em/vencido/renovação) | `test_m9_licencas_dominio_p1` | ✅ |
| OQ-04 | Promoção B→A atômica popula o cache do tenant | `test_m9_licencas_api_p2::test_promover_b_para_a_popula_cache` | ✅ |
| OQ-05 | **Não-drift** `cache == fonte` após promover + renovar | `test_licencas_nao_drift` | ✅ |
| OQ-06 | Alertas D-90/60/30/15/7 (idempotentes); revogado ignorado | `test_m9_licencas_fatia3_p3::TestVerificarAlertasLicencas` | ✅ |
| OQ-07 | Cache populado **rebaixa** RBC→não-RBC na emissão (reverde M8) | `test_licencas_nao_drift::test_reverde_m8_cache_populado_rebaixa_real` | ✅ |
| OQ-08 | ART vencida → `signatario_apto = False` + lista vencidos; vigente/ausente → apto | `test_m9_licencas_fatia4_p4` / `TestINV_LIC_BLOQUEIO_001` | ✅ |
| OQ-09 | Modo emergencial: justif curta → 422; CGCRE libera só não-RBC; ART não | `test_m9_licencas_use_cases_p2::TestModoEmergencial` | ✅ |
| OQ-10 | Histórico lista revisões append-only; UPDATE de revisão → bloqueado (WORM) | `test_m9_licencas_fatia4_p4::test_historico` + `TestINV_LIC_WORM_001` | ✅ |
| OQ-11 | RLS cross-tenant: documento de A invisível a B | `test_inv_lic_p2_schema_triggers::test_rls_documento_nao_vaza` | ✅ |

## 4. PQ — Performance Qualification (desempenho em produção controlada)

- **Diferido (dogfooding Balanças Solution + pré-produção):** o PQ formal (replay
  determinístico de relatório/dossiê PDF byte-a-byte + carga de alertas em produção)
  depende do **GATE-LIC-PDF** (relatório real — Wave B) e do **GATE-LIC-PQ** (smoke de
  produção). O núcleo entrega export estruturado; o replay determinístico do **conteúdo
  probatório** (justificativa emergencial canonicalizada + hash versionado, ADR-0029/0064)
  já é exercitado nos testes WORM. Sem release pública até o dossiê estar assinado pelo
  RT-vendor (INV-CAL-VAL-001 reforçada — V2).

## 5. Matriz perfil (profundidade do dossiê — ADR-0025 v2)

| Perfil | Dossiê exigido | Estado nesta frente |
|--------|----------------|---------------------|
| **A** (acreditado RBC) | URS + IQ + OQ + PQ completos | URS/IQ/OQ ✅ entregues; PQ diferido (GATE-LIC-PDF/PQ) |
| **B/C** (capacidade interna) | IQ/OQ leve (sem PQ formal) | ✅ coberto pelos mesmos testes (perfil-agnósticos no núcleo) |
| **D** (sem metrologia regulada) | drill estrutural | ✅ drill `validar_licencas_acreditacoes` 42/42 |

## 6. Pendências de validação (declaradas)

- **Validação formal cl. 7.11 por RT-vendor credenciado** — pré-produção
  (`project_sem_contratacoes_externas_ate_producao`). Este documento é a base redigida
  que o RT-vendor assina em V2.
- **PQ (replay PDF + carga)** — depende de GATE-LIC-PDF (relatório real Wave B) + GATE-LIC-PQ.
- **GATE-LIC-EMISSAO-HARDBLOCK** — consumo do read-model `signatario_apto` pela emissão
  M8 (409 hard) = Wave B; a porta já está validada por OQ-08.
