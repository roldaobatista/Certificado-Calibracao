# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + M3 OS FECHADAS. **M4 calibracao P3 ENTREGUE + P4 Fase 1 FECHADA (25/25) + P4 Fase 2 FECHADA (105 tests) + P4 Fase 3 PARCIAL (88 tests; Batch C BLOQUEADO numpy) + P4 Fase 4 FECHADA (8 tests) + P4 Fase 5 FECHADA (21 use cases) + P4 Fase 7 PARCIAL (5 de 9 jobs entregues — alertar_reclamacao_vencendo + pseudonimizar_responsavel_nc + analisar_uso_excecao_2a_conferencia + verificar_avaliacoes_subcontratados_vencendo + analisar_padrao_medicoes_controle [Western Electric 4 regras]) + P4 Fase 9 FECHADA (6 hooks); 508 tests M4 verdes.**
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-25)

- pytest geral: **905/0/0** em 26min (último run 2026-05-24).
- Hooks `_test-runner.sh`: **377/377** verdes / **48 hooks ativos** (M4 P9 FECHADA — 6 hooks: +hmac-versao-formato +incerteza-versao-motor +cmc-binding +migration-concorrencia-calibracao +migration-metrology-classifier +metrology-replay-fixtures-versionadas).
- ruff/mypy: limpos nos paths novos.

## M4 calibracao — P3 entregue (matriz reconciliação + tasks.md)

P3 do ritual Spec Kit completo em 3 commits hoje:

- `b1c1d6a` — ADR-0065 nova (concorrência calibração — UNIQUE composto + CAS + advisory lock) + retrofit ADR-0024 (6 zonas ILAC G8 + PFA/PRA + AceiteRegraDecisao) + retrofit ADR-0063 (Opção A lazy — predicate em 3 use cases pós-config) + 24 INVs CAL novos em REGRAS-INEGOCIAVEIS.md.
- `e8c4126` — spec.md §16 absorve 10 BLOQUEANTE + 23 MÉDIO dos 4 reviews + PRD §11 com 11 ACs novos + US-CAL-018 nova (reclamação CDC art. 26). Status spec.md + prd.md draft → stable.
- (este commit) — matriz-reconciliacao.md (zero conflito PRD ↔ spec ↔ plan ↔ ADRs ↔ REGRAS) + tasks.md com 160 T-CAL-NNN em 10 fases (Fase 1 migrations 25 / Fase 2 domain 20 / Fase 3 motor §3.3 15 / Fase 4 predicates+authz 15 / Fase 5 use cases 30 / Fase 6 queries 8 / Fase 7 jobs 9 / Fase 8 views REST 14 / Fase 9 hooks novos 8 / Fase 10 regressões+drill 16) + 14 tarefas P3.5 paralelas (minutas OAB + matrizes CGCRE + ADR-0028 rev 3 + DPIA).

## Decisões cravadas (P2 → P3)

- D-M4-1: GUM Decimal + Monte Carlo NumPy ✓
- D-M4-2: ADR-0063 Opção A lazy ✓
- D-M4-3, D-M4-4, D-M4-5: sem previsão de contratação → agente cria minutas/matrizes preliminares com selos REQUER {OAB,CGCRE,SUSEP} HUMANO.

## P4 Fase 1 — 23/25 migrations entregues hoje (23 entidades + triggers + cross-marco M3)

T-CAL-001..014 + T-CAL-015..017+021 + T-CAL-018..020+023 + T-CAL-024 fechadas em 12 commits incrementais (ac71dc0 → 3eb9b74 → 7780511 → 5754785 → bfd49b4 → 9e45e28 → e20f86a → [batch] → 65a75e0 → 774ba76 → a5aa840 → a40dcdd → 736e61b):

**23 entidades persistidas em PG (todas com RLS + triggers WORM/transição):**
1. `calibracao` (raiz agregado — 50 campos + CAS revision + 6 zonas ILAC G8 + PFA/PRA).
2. `leitura` (UNIQUE composto ADR-0065 + INV-CAL-CONC-001).
3. `leitura_correcao` (rasura digital cl. 7.5).
4. `condicoes_ambientais` (`dentro_tolerancia` GENERATED ABS+CASE).
5. `orcamento_incerteza` (algoritmo_1/2 JSONB + divergencia + replay_hash + bias).
6. `componente_incerteza` (Tipo A n≥6 CHECK + correlação self-FK CHECK).
7. `orcamento_por_ponto` (UNIQUE ponto).
8. `padrao_usado` (snapshot ADR-0040 + UNIQUE parcial + snapshot_lock one-way + trigger anti-snapshot-retroativo INV-CAL-RT-COMP-001 + vinculacao SI estruturada).
9. `recepcao_item_calibracao` (cl. 7.4 + CHECK XOR foto/recusa + CHECK INAPTO motivo).
10. `medicao_controle` (Western Electric + escore_z + trigger EXCEÇÃO job atualiza regra_we).
11. `evento_de_calibracao` (hash-chain por calibracao + sequencia_local IDENTITY via trigger + UNIQUE seq + append-only WORM).
12. `nao_conformidade` (CHECK XOR origem + trigger INV-CAL-NC-002/003 transição + estado-máquina 6 estados).
13. `analise_impacto_nc_proficiencia` (janela ao invés array — P-CAL-T8 + status RECALL_PENDENTE_M5).
14. `plano_acao_proficiencia_warning` (P-CAL-R8 |z|∈(2,3] + WORM full).
15. `laboratorio_subcontratado` (Padrão C soft-delete + PII Zona B + CHECK DPA internacional + vigencia ADR-0030).
16. `aceite_subcontratacao` (WORM + CHECK TOUCH→declaração + INV-CAL-SUBC-001).
17. `avaliacao_periodica_subcontratado` (WORM 1:N + CHECK score 0-10 + decisão MANTER/ACOMPANHAMENTO/DESCREDENCIAR).
18. `aceite_regra_decisao` (WORM + CHECK nivel_confianca [0.80, 0.99] + ADR-0024 revisado).
19. `override_regra_decisao_cliente` (WORM + contrato_clausula_id + justificativa ≥50 chars).
20. `reclamacao_calibracao` (estado-máquina RECEBIDA→EM_ANALISE→RESPONDIDA→ARQUIVADA + CHECK respondida completa + US-CAL-018 + CDC art. 26).
21. `consentimento_contato_tecnico_cliente` (WORM parcial + revogado_em LGPD art. 18 + CHECK temporal + trigger des-revogar bloqueado).
22. `consentimento_foto_recusado` (WORM + motivo ≥30 chars + texto_aviso REQUER OAB + P-CAL-A5).
23. `evento_backup_metrologico` (WORM append-only + resultado OK/FALHA_PARCIAL/FALHA_TOTAL + INV-CAL-BACKUP-001 retenção 25a).

**Cross-marco M3 (T-CAL-024):** `AtividadeDaOS.grandeza VARCHAR(50) DEFAULT ''` + index parcial `atv_tenant_grandeza_partial_idx` (ADR-0063 Opção A lazy).

**Total artefatos PG criados nesta sessão (12 commits):** ~27 funções PL/pgSQL + ~27 triggers + ~12 CHECK constraints + ~16 UNIQUE constraints + ~52 policies RLS + 1 GENERATED column + 1 sequence global + 1 index parcial cross-marco. Hooks `_test-runner.sh` 312/312 verdes ao longo dos 12 commits.

## Próxima fatia

**P4 Fase 2 FECHADA** (3 batches em 3 commits):
- Batch A (`ac33195`) — T-CAL-026..030: 5 VOs novos M4 — `VersaoMotorCalculo`, `EscoreZ`+`ClassificacaoZ`, `ZonaILACG8`, `HashVersionadoV0`, `IncertezaCombinada`. 36 testes.
- Batch B (`c8a3710`) — T-CAL-031..036: helpers crypto puros em `src/domain/metrologia/calibracao/hash_versionado.py` — `validar_versao`, `parsear_hash_versionado`, `formatar_hash_versionado`, `canonicalizar_payload_para_hmac`. 46 testes (replay determinístico 50x + 1-bit-diff).
- Batch C (`7088fc7`) — T-CAL-037..039: 3 predicates ABAC em `src/infrastructure/calibracao/predicates_calibracao.py` — `cmc_cobre` (STUB Wave A), `procedimento_vigente_para` (STUB Wave A), `pode_aprovar_revisao_2a_conferencia` (REAL — segregação funções cl. 6.2.5 + ADR-0026 exceção 4 condições). 23 testes.

**Total Fase 2: 105 testes verdes** + ruff/mypy limpos + hooks 312/312.

**Decisão de escopo (P4 Fase 2 Batch C):** Entities domain (originalmente T-CAL-040..045) DIFERIDAS para Fase 5 (use cases). Criar dataclasses domain agora sem consumidor seria especulação — quando use case precisar, dataclass nasce alinhada ao consumo real.

**P4 Fase 3 ENTREGUE PARCIAL — 3/4 batches:**
- Batch A (`98a690b`) — T-CAL-046..049: `arredondamento.py` (NIT-DICLA-030 §7.5 — 2 dígitos significativos com banker's rounding). 33 testes.
- Batch B (`9bcfdd4`) — T-CAL-050..054: `gum_classico.py` (Decimal puro — combinar_tipo_a, combinar_componentes com correlação, welch_satterthwaite, fator_k tabela GUM G.2, propagar end-to-end). 39 testes.
- Batch D (`c0d7698`) — T-CAL-059..060: `validacao_replay.py` (comparar_algoritmos GUM vs MC, 3 zonas SILENCIOSO/ALERTA_P3/INACEITAVEL com DivergenciaCalculoInaceitavel). 16 testes.

**Batch C BLOQUEADO (T-CAL-055..058 Monte Carlo NumPy):** dep nova `numpy` não está em pyproject.toml; adição requer DEP-001 (auditor-supplychain — justificativa+CVE+pin+hash). Diferido até review do auditor via Agent. Batch D opera autonomamente sobre ResultadoMC dummies (não bloqueado).

**Total Fase 3: 88 testes verdes** + ruff/mypy limpos + hooks 312/312.

**P4 Fase 4 FECHADA — 2 batches:**
- Batch A (`653fb74`) — T-CAL-061..068: seed `0013_seed_authz_calibracao.py` com 6 actions × 5 perfis = 18 linhas em `authz_perfil_acao`. Segregação cl. 6.2.5: metrologista_bancada NÃO aprova próprio trabalho (só configurar+iniciar+solicitar); signatario aprova (aprovar_revisao+aprovar_2a_conferencia).
- Batch B (`73338a4`) — T-CAL-069..075: `CalibracaoConfig.ready()` registra 3 predicates ABAC com escopos declarados (anti-FB-A1). Migration tornada resiliente a `authz_perfil` vazio (test_afere TRUNCATE) — retorna cedo restaurando RLS quando perfis ausentes; fixture autouse re-aplica seeds via conftest atualizado.

**P4 Fase 5 ANDAMENTO (Batches A + B entregues — 2/18 use cases):**
- Batch A (`7d4d13a`) — T-CAL-076..080: domain skeleton (enums + entities + repository Protocol) + `criar_calibracao` US-CAL-001 + adapter Django + FakeCalibracaoRepository in-memory. 17 tests.
- Batch B (`5e8936e`) — T-CAL-081..083: `configurar_calibracao` US-CAL-002 — primeiro CAS optimistic ADR-0065 (RECEPCIONADA → CONFIGURADA). 3 exceções específicas (CalibracaoNaoEncontrada/EstadoInvalido/ConflitoVersao) + validação ADR-0023 (analise crítica coerente com origem) + RBC sem escopo recusa. Snapshot expandido com 6 campos de configuração. 17 tests novos.

**Padrão M3 OS estabelecido e aplicado:**
- Snapshot enxuto (frozen + slots) reflete defaults PG pos-INSERT.
- Use case puro (sem Django/authz check — caller=guard, use_case=transação).
- CAS via `repo.atualizar_com_lock(snapshot, revision_anterior)` retorna bool.
- ConflitoVersao carrega snapshot atualizado pra caller decidir retry/409.

**Batch C entregue (`46c5c79` next):**
- `iniciar_leituras` US-CAL-004 (CONFIGURADA → EM_EXECUCAO via CAS) — 5 tests.
- `registrar_leitura` (INSERT 1:N + idempotência sync mobile ADR-0027) — 13 tests + FakeLeituraRepository.
- `LeituraSnapshot` frozen no domain + `LeituraRepository` Protocol (3 métodos).
- `OrigemLeitura` enum (MANUAL/INTEGRACAO_SERIAL/INTEGRACAO_USB).

**Batch E entregue (`6d3ff98`):**
- `calcular_orcamento_incerteza` — orquestra `motor_calculo.gum_classico.propagar` + `arredondamento.arredondar_2_digitos_significativos` + `canonicalizar_payload_para_hmac` + persistência atômica.
- `OrcamentoIncertezaSnapshot` (17 campos) + `ComponenteIncertezaSnapshot` (12 campos) + `OrcamentoIncertezaRepository` Protocol no domain.
- 17 tests novos (FakeOrcamentoIncertezaRepository in-memory).
- Algoritmo 2 (Monte Carlo) NULL — BLOQUEADO DEP-001 numpy.

**Batch F entregue (`8cec1f4`):**
- 4 use cases novos (T-CAL-087..090): `solicitar_revisao` (EM_EXECUCAO → EM_REVISAO_1) + `aprovar_revisao` (EM_REVISAO_1 → AGUARDANDO_2A_CONFERENCIA + snapshot_competencia_revisor + INV-CAL-FRAUDE-REV-001) + `rejeitar_revisao` (EM_REVISAO_1 → EM_EXECUCAO, motivo ≥30 chars, não queima revisor_id) + `aprovar_2a_conferencia` (AGUARDANDO_2A_CONFERENCIA → APROVADA + INV-CAL-FRAUDE-CONF-001 + ADR-0026 4 condições + excecao_2a_conf_id FK obrigatória quando conferente colide).
- `CalibracaoSnapshot` ampliado: executor_id + revisor_id + conferente_id + snapshot_competencia_revisor_json + snapshot_competencia_conferente_json + excecao_2a_conf_id (6 campos).
- `iniciar_leituras` agora exige `executor_id` obrigatório (INV-CAL-FRAUDE-EXEC-001 cravado na transição CONFIGURADA → EM_EXECUCAO). Adapter `repositories.py` SQL UPDATE estendido com os 6 campos.
- Predicate `pode_aprovar_revisao_2a_conferencia` (Fase 2 Batch C) invocado dentro do use case com `action=revisao` / `action=2a_conferencia` — não fora do escopo (mais defensivo que o esperado do padrão "caller=guard"; padrão de segurança).
- 17 tests novos em `test_m4_uc_revisao_conferencia.py` (smoke E2E recepção→APROVADA com 3 atores distintos). 312/312 tests M4; hooks 312/312; ruff limpo.

**Batch G entregue (commit subsequente):**
- 2 motores novos (Decimal puro / IEEE 754): `motor_calculo/decisao_ilac.py` (classificar_zona_ilac_g8 - 7 zonas + 3 regras) + `motor_calculo/pfa_pra.py` (PFA/PRA via math.erf stdlib - sem numpy/DEP-001).
- Use case `avaliar_conformidade` (T-CAL-086 / US-CAL-006 + AC-CAL-006-1/4): EM_EXECUCAO/EM_REVISAO_1, CAS, classifica zona + decisao + PFA (BANDA_GUARDA_30) / PRA (RISCO_COMPARTILHADO).
- CalibracaoSnapshot ampliado com 4 campos (zona_ilac_g8, decisao, pfa_calculada, pra_calculada). _to_snapshot + UPDATE SQL atualizados.
- 48 tests novos (21 motor decisao + 14 motor PFA/PRA + 13 use case) — todos os 7 zonas cobertas + determinismo replay.

**Batch J entregue (`941ca1f`):**
- 3 use cases ReclamacaoCalibracao (US-CAL-018 + cl. 7.9 + CDC art. 26): `abrir` (RECEBIDA com janela CDC 90d) + `atribuir_rt` (RECEBIDA→EM_ANALISE com independência AC-CAL-018-2) + `responder` (EM_ANALISE→RESPONDIDA com decisão 3 valores; PROCEDENTE_RECALL sinaliza saga recall M5).
- Domain: EstadoReclamacao + DecisaoReclamacao + ReclamacaoCalibracaoSnapshot + ReclamacaoCalibracaoRepository Protocol.
- 23 tests: 7 abrir (janela CDC borda 90/91 + relato + tz) + 6 atribuir_rt (independência + exceção lab pequeno) + 7 responder (3 decisões + recall M5) + conflito estado + smoke E2E.

**Batch I entregue (`d7858d9`):**
- 2 use cases subcontratação cl. 6.6 (US-CAL-017): `subcontratar_calibracao` (CONFIGURADA→AGUARDANDO_SUBCONTRATADO + AC-CAL-017-1/7/8 + LGPD art. 33 + Lei 14.063 art. 4o) + `registrar_recebimento_subcontratado` (AGUARDANDO→RECEBIDA_DO_SUBCONTRATADO + INV-CAL-FRAUDE-RECEB-001 + AC-CAL-017-3).
- CalibracaoSnapshot ampliado com 4 campos (subcontratado_id, aceite_subcontratacao_id, certificado_subcontratado_snapshot_json, recebedor_user_id).
- 19 tests.

**Batch H entregue (`4c0b94b`):**
- 6 use cases consolidados em `application/metrologia/calibracao/nao_conformidade.py` cobrindo ciclo CAPA cl. 7.10 + cl. 8.7: abrir / definir_acao_corretiva / executar_acao / verificar_eficacia / fechar / reabrir.
- INV-CAL-NC-002 (decisao != A_DEFINIR antes de ACAO_EXECUTADA) + INV-CAL-NC-003 (PARAR_TRABALHO exige cliente_notificado_em+via) + P-CAL-A2 (responsavel_acao_user_id_hash sempre presente).
- Reabertura cl. 8.7.2: FECHADA → CONTIDA limpa campos do ciclo anterior.
- Domain ampliado: 4 enums novos (EstadoNaoConformidade, AcaoCorretivaTipo, DecisaoContinuarOuParar, ClienteNotificadoVia), NaoConformidadeSnapshot (20 campos), NaoConformidadeRepository Protocol.
- 26 tests novos cobrindo XOR origem + 6 transições + INV-CAL-NC-002/003 + concorrência + smoke E2E.

**P4 Fase 5 FECHADA — 21 use cases entregues, 431 tests verdes.**

**Próxima fatia M4 — P4 Fases 6-10 (queries + jobs + REST views + hooks + regressões):**
- Fase 6 (T-CAL-104..111): 4 query services (visao_360 calibracao, listagem RT, fila revisor, fila conferente, etc).
- Fase 7 (T-CAL-112..120): 9 jobs procrastinate (alerta prazo CDC 15d, alerta exceção 2ª conferência 3%/mês, job-pseudonimização-responsavel-NC após 90d, etc).
- Fase 8 (T-CAL-121..134): 14 endpoints REST views.
- Fase 9 (T-CAL-135..142): 8 hooks novos (predicate hmac-versao-formato + assinatura A3 e-CPF RT + autorização 2ª conferência etc).
- Fase 10 (T-CAL-143..160): 16 testes regressão INV-CAL-* + drill `validar_m4_calibracao`.

**Paralelizável P3.5 — 14 tarefas REQUER OAB/CGCRE/SUSEP** (não bloqueia dogfooding; bloqueia 1º tenant externo pago).

**Batches subsequentes (8 use cases restantes — 6 batches estimados):**
- Batch I-J: aceites regra decisão + override + reclamação CDC.
- Batch K-L: consentimento revogação + análise impacto PT + plano warning.
- Batch M: NC analise impacto PT + recall (cross-marco M5).

**Paralelizável (P3.5 — não bloqueia P4 dogfooding):** 14 tarefas T-CAL-P35-* (minutas OAB + matrizes CGCRE + ADR-0028 rev 3 + DPIA-calibracao). Bloqueia 1º tenant externo pago.

**Paralelizável (P3.5 — não bloqueia P4 dogfooding):** 14 tarefas T-CAL-P35-* (minutas OAB + matrizes CGCRE + ADR-0028 rev 3 + DPIA-calibracao). Bloqueia 1º tenant externo pago.

**Paralelizável (P3.5 — não bloqueia P4 dogfooding):** 14 tarefas T-CAL-P35-* (minutas canônicas OAB + matrizes técnicas CGCRE + ADR-0028 rev 3 + DPIA-calibracao). Bloqueia 1º tenant externo pago.

**Paralelizável (P3.5 — não bloqueia P4 dogfooding):** 14 tarefas T-CAL-P35-* (minutas canônicas OAB + matrizes técnicas CGCRE + ADR-0028 rev 3 + DPIA-calibracao). Bloqueia 1º tenant externo pago.

## Pendências Wave A rastreadas (33 GATEs novos M4 — somam aos herdados)

GATE-CAL-* (12 RBC + 8 advogado + 3 tech-lead + 1 matrizes-CGCRE) + GATE-SEG-* (9 corretora) = 33 GATEs novos M4 + GATE-OS-* (~20 M3) + GATE-CYBER-BREAKGLASS-U2F-ENFORCE + GATE-HMAC-RETROFIT-MARCO-2-3 + GATE-KMS-IAM-LOCK + GATE-HMAC-DRILL + GATE-SEG-BPT-1 (emergencial dogfooding).
