---
owner: roldao
revisado_em: 2026-05-25
proximo_review: 2026-08-25
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 4 — metrologia/calibracao
tipo: matriz-spec-codigo + tarefas-causa-raiz
relacionados:
  - docs/faseamento/M4-calibracao/spec.md
  - docs/faseamento/M4-calibracao/plan.md
  - docs/faseamento/M4-calibracao/matriz-reconciliacao.md
  - docs/faseamento/M4-calibracao/reviews/tech-lead.md
  - docs/faseamento/M4-calibracao/reviews/advogado.md
  - docs/faseamento/M4-calibracao/reviews/corretora.md
  - docs/faseamento/M4-calibracao/reviews/rbc.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/faseamento/M3-os/tasks.md
---

# Marco 4 (metrologia/calibracao) — Tarefas P4 (causa-raiz)

> **P4 do ritual Spec Kit (2026-05-25):** Marco 4 é **greenfield** — zero código no módulo `calibracao`. Cada T-CAL-NNN resolve causa-raiz (Constituição §6, nunca mascara). Severidade MÉDIO+ no fechamento bloqueia (INV-RITUAL-001).

## Convenções

- **PENDENTE** → tarefa em P4 (vai ser implementada).
- **TRACK** → GATE Wave A (não bloqueia M4 dogfooding).
- **OK** → herdado de F-A/F-B/M1/M2/M3 (sem código novo).
- Toda tarefa carrega: critério binário (pronto-quando) + caminhos de arquivo afetados + INV/ADR de referência.

## Sumário por fase

| Fase | Tema | T-CAL range | Quantidade | Status |
|---|---|---|---|---|
| 1 | Migrations + DDL constraints | T-CAL-001..025 | 25 | PENDENTE |
| 2 | Domain (entities + VOs + helpers crypto) | T-CAL-026..045 | 20 | PENDENTE |
| 3 | Motor de cálculo (§3.3 spec) | T-CAL-046..060 | 15 | PENDENTE |
| 4 | Predicates + authz | T-CAL-061..075 | 15 | PENDENTE |
| 5 | Use cases (application) | T-CAL-076..105 | 30 | PENDENTE |
| 6 | Query services | T-CAL-106..113 | 8 | PENDENTE |
| 7 | Jobs procrastinate | T-CAL-114..122 | 9 | PENDENTE |
| 8 | Views + Serializers REST | T-CAL-123..136 | 14 | PENDENTE |
| 9 | Hooks novos M4 P9 | T-CAL-137..144 | 8 | PENDENTE |
| 10 | Regressões + drill `validar_m4_calibracao` | T-CAL-145..160 | 16 | PENDENTE |
| **Total** | | | **160** | **PENDENTE** |

## Fase 1 — Migrations + DDL constraints (T-CAL-001..025)

| ID | Tarefa | Pronto-quando | Caminho | INV/ADR |
|---|---|---|---|---|
| T-CAL-001 | Migration 0001 — `calibracao` (raiz agregado) + campos §16.4 + revision INTEGER + zona_ilac_g8 ENUM + pfa/pra NUMERIC + regra_decisao_acordada_* + analise_critica_pedido_* + snapshot_competencia_*_json + recebedor_user_id NULLABLE | `python manage.py migrate --database=migrator` aplica sem erro; CHECK constraint composta presente | `src/infrastructure/calibracao/migrations/0001_calibracao.py` | ADR-0023, ADR-0024 revisado, ADR-0065 |
| T-CAL-002 | Migration 0002 — `leitura` + UNIQUE composto `(tenant_id, calibracao_id, ponto, repeticao)` (idx_leitura_unica) + trigger imutabilidade pós-INSERT | hook `migration-concorrencia-calibracao-check` valida | `migrations/0002_leitura.py` | INV-CAL-CONC-001, ADR-0065 |
| T-CAL-003 | Migration 0003 — `leitura_correcao` (cl. 7.5 rasura digital) + trigger imutabilidade | OK | `0003_leitura_correcao.py` | INV-CAL-WORM-001 |
| T-CAL-004 | Migration 0004 — `condicoes_ambientais` detalhada §16.13 + GENERATED `dentro_tolerancia` | CHECK constraint funciona; teste DDL aceita/rejeita | `0004_condicoes_ambientais.py` | INV-CAL-AMB-001 |
| T-CAL-005 | Migration 0005 — `orcamento_incerteza` + algoritmo_1_resultado JSONB + algoritmo_2_resultado JSONB + divergencia_pct + replay_determinismo_hash + bias_orcado + arredondamento_aplicado_regra | OK | `0005_orcamento_incerteza.py` | ADR-0025, ADR-0064, §3.3 spec |
| T-CAL-006 | Migration 0006 — `componente_incerteza` + tipo_origem_componente ENUM + formula_calculo + correlacao_com_componente_id + coeficiente_correlacao + n_amostras (CHECK ≥6 quando tipo=A) + s_x | CHECK rejeita Tipo A com n<6 | `0006_componente_incerteza.py` | INV-CAL-INC-002/003/004 |
| T-CAL-007 | Migration 0007 — `orcamento_por_ponto` (1:N) + trigger imutabilidade | OK | `0007_orcamento_por_ponto.py` | INV-CAL-WORM-001 |
| T-CAL-008 | Migration 0008 — `padrao_usado` + UNIQUE parcial `WHERE snapshot_lock=false` + vinculacao_si_tipo ENUM + cadeia_rastreabilidade_documento_id + trigger snapshot_lock pós em_revisao_1 | UNIQUE parcial funciona; teste regressão | `0008_padrao_usado.py` | INV-CAL-CONC-002, INV-CAL-RAST-002, INV-CAL-RT-COMP-001 |
| T-CAL-009 | Migration 0009 — `recepcao_item_calibracao` + foto_evidencia_id NULL + foto_evidencia_recusa_id NULL + aviso_foto_texto_canonico_id NOT NULL + condicoes_ambientais_id NOT NULL + CHECK foto XOR recusa | OK | `0009_recepcao.py` | INV-CAL-ANAL-001 |
| T-CAL-010 | Migration 0010 — `medicao_controle` + escore_z + regra_western_electric_violada + trigger imutabilidade | OK | `0010_medicao_controle.py` | — |
| T-CAL-011 | Migration 0011 — `evento_de_calibracao` + sequencia_local BIGINT IDENTITY por (tenant_id, calibracao_id) + UNIQUE composto + trigger append-only + hash-chain via advisory lock | hook `audit-immutability-check` valida; drill 100 inserts concorrentes valida ordem | `0011_evento_de_calibracao.py` | INV-CAL-AUD-001/002, ADR-0065 |
| T-CAL-012 | Migration 0012 — `nao_conformidade` + decisao_continuar_ou_parar ENUM + cliente_notificado_* + autorizacao_retomada_* + responsavel_acao_user_id_hash + CHECK composta transição → ACAO_EXECUTADA | CHECK rejeita transição com decisao=A_DEFINIR | `0012_nao_conformidade.py` | INV-CAL-NC-002/003 |
| T-CAL-013 | Migration 0013 — `analise_impacto_nc_proficiencia` (janela ao invés de certs_no_periodo array — P-CAL-T8) | OK | `0013_analise_impacto_pt.py` | INV-CAL-NC-PT-001 |
| T-CAL-014 | Migration 0014 — `laboratorio_subcontratado` + criterio_selecao_documento_id + ultima/proxima_avaliacao_periodica_em + score_avaliacao_atual + pais + dpa_clausulas_internacionais_id | OK | `0014_laboratorio_subcontratado.py` | INV-CAL-SUBC-005 |
| T-CAL-015 | Migration 0015 — `aceite_subcontratacao` + assinatura_modo ENUM + declaracao_aceite_touch_alto_risco_id + consentimento_contato_id + trigger imutabilidade | OK | `0015_aceite_subcontratacao.py` | INV-CAL-SUBC-001, INV-CAL-CONT-001 |
| T-CAL-016 | Migration 0016 — `aceite_regra_decisao` (entidade nova ADR-0024 revisado §16.3) + trigger imutabilidade | OK | `0016_aceite_regra_decisao.py` | INV-CAL-DEC-006 |
| T-CAL-017 | Migration 0017 — `override_regra_decisao_cliente` (entidade nova P-CAL-A3) + trigger imutabilidade | OK | `0017_override_regra_decisao_cliente.py` | INV-CAL-DEC-002 |
| T-CAL-018 | Migration 0018 — `reclamacao_calibracao` (entidade nova US-CAL-018) + estado-máquina + trigger parcial | OK | `0018_reclamacao_calibracao.py` | US-CAL-018 |
| T-CAL-019 | Migration 0019 — `consentimento_contato_tecnico_cliente` (entidade nova P-CAL-A6) + trigger imutabilidade | OK | `0019_consentimento_contato.py` | INV-CAL-CONT-001 |
| T-CAL-020 | Migration 0020 — `consentimento_foto_recusado` (entidade nova P-CAL-A5) + trigger imutabilidade | OK | `0020_consentimento_foto_recusado.py` | — |
| T-CAL-021 | Migration 0021 — `avaliacao_periodica_subcontratado` (1:N de `LaboratorioSubcontratado`) + trigger imutabilidade | OK | `0021_avaliacao_periodica_subcontratado.py` | INV-CAL-SUBC-005 |
| T-CAL-022 | Migration 0022 — `plano_acao_proficiencia_warning` (paralelo `AnaliseImpactoNCProficiência` para WARNING |z|>2) | OK | `0022_plano_acao_pt_warning.py` | P-CAL-R8 |
| T-CAL-023 | Migration 0023 — `evento_backup_metrologico` (append-only WORM) + trigger imutabilidade | OK | `0023_evento_backup_metrologico.py` | INV-CAL-BACKUP-001 |
| T-CAL-024 | Migration 0024 (cross-marco M3) — `AtividadeDaOS.grandeza VARCHAR(50) NULL` + backfill default `""` | hook `migration-rls-check` valida; teste regressão M3 verde | `src/infrastructure/ordens_servico/migrations/0XYZ_atividade_grandeza.py` | ADR-0063 Opção A |
| T-CAL-025 | Migration 0025 — RLS policies em todas as 19 tabelas M4 + seed `app_user` permissões | drill `validar_m4_calibracao` item 1 PASS | `0025_rls_calibracao.py` | INV-TENANT-001..003 |

## Fase 2 — Domain (entities + VOs + helpers crypto) (T-CAL-026..045)

| ID | Tarefa | Pronto-quando | Caminho |
|---|---|---|---|
| T-CAL-026 | `src/domain/metrologia/calibracao/__init__.py` + estrutura de módulo (entities, value_objects, regras, repository, events) | OK | `src/domain/metrologia/calibracao/` |
| T-CAL-027 | Entidades: `Calibracao` (raiz agregado) + máquina estados §4 + transições nomeadas | mypy clean | `entities/calibracao.py` |
| T-CAL-028 | Entidades: `Leitura`, `LeituraCorrecao`, `CondicoesAmbientais` | mypy clean | `entities/leitura.py` |
| T-CAL-029 | Entidades: `OrcamentoIncerteza`, `ComponenteIncerteza`, `OrcamentoPorPonto` | mypy clean | `entities/orcamento.py` |
| T-CAL-030 | Entidades: `PadraoUsado`, `RecepcaoItemCalibracao`, `MedicaoControle` | mypy clean | `entities/padrao_recepcao.py` |
| T-CAL-031 | Entidades: `EventoDeCalibracao` + helpers de hash-chain via advisory lock | mypy clean | `entities/eventos.py` |
| T-CAL-032 | Entidades: `NaoConformidade` + `AnaliseImpactoNCProficiência` + `PlanoAcaoProficienciaWarning` | mypy clean | `entities/nao_conformidade.py` |
| T-CAL-033 | Entidades: `LaboratorioSubcontratado`, `AceiteSubcontratacao`, `AvaliacaoPeriodicaSubcontratado`, `ConsentimentoContatoTecnicoCliente`, `ConsentimentoFotoRecusado` | mypy clean | `entities/subcontratacao.py` |
| T-CAL-034 | Entidades novas P3: `AceiteRegraDecisao`, `OverrideRegraDecisaoCliente`, `ReclamacaoCalibracao` | mypy clean | `entities/aceite_regra_e_reclamacao.py` |
| T-CAL-035 | Entidade: `EventoBackupMetrologico` (append-only) | mypy clean | `entities/backup.py` |
| T-CAL-036 | VO `RegraDecisao` enum + helper `aplicar(spec, valor, U_expandida) → ConformidadeAvaliada(zona, decisao_sugerida)` | mypy clean; teste unidade 6 zonas | `src/domain/metrologia/value_objects.py` |
| T-CAL-037 | VO `VersaoMotorCalculo` (semver + commit_hash + algoritmo_id + janela_vigencia) | mypy clean | idem |
| T-CAL-038 | VO `HashVersionado` (formato `v<NN>$<base64>` + helpers `gerar(payload, key_id)` + `verificar(hash, payload)` via KMS) | testes verificam round-trip | `src/domain/shared/hash_versionado.py` + helpers crypto |
| T-CAL-039 | VO `ZonaDecisao` enum + transição `decisao → zona` | OK | idem |
| T-CAL-040 | Regras de domínio: máquina estados `Calibracao` com 12 estados + transições | mypy clean; teste cobre transição inválida | `regras/maquina_estados.py` |
| T-CAL-041 | Regras de domínio: máquina estados `NaoConformidade` (5 estados + REABERTA) | OK | `regras/nc_maquina.py` |
| T-CAL-042 | Repositório: `CalibracaoRepository` interface + implementação Django ORM com CAS (revision) | unit + integration tests | `repository/calibracao_repository.py` |
| T-CAL-043 | Helpers crypto: `evento_hash_versionado.py` (HMAC payload + evento_anterior_hash + tenant_id + occurred_at) | teste round-trip | `src/domain/shared/evento_hash.py` |
| T-CAL-044 | Sanitizer único `sanitizar_payload_evento_calibracao()` (G2 dossiê pré-M4) — cobre 23 eventos publicados | teste com 5000 UUIDs digit-heavy | `src/infrastructure/calibracao/event_sanitizer.py` |
| T-CAL-045 | Eventos de domínio: 23 publicados § (modelo + payload) — `Calibracao.Recepcionada`, `.Configurada`, ..., `.Aprovada`, +9 P3 §16.15 | mypy clean | `events/__init__.py` |

## Fase 3 — Motor de cálculo (§3.3 spec) (T-CAL-046..060)

| ID | Tarefa | Pronto-quando | Caminho |
|---|---|---|---|
| T-CAL-046 | `motor_calculo/gum_classico.py` — implementação Python Decimal puro (NIT-DICLA-030 rev. 15) | testes replay determinístico em 10 fixtures de referência | `src/domain/metrologia/calibracao/motor_calculo/gum_classico.py` |
| T-CAL-047 | `motor_calculo/monte_carlo.py` — implementação NumPy BIPM JCGM 101 + seed em Calibracao.id | testes replay determinístico (mesmo seed → mesmo resultado) | `motor_calculo/monte_carlo.py` |
| T-CAL-048 | `motor_calculo/arredondamento.py` — regra NIT-DICLA-030 §7.5 (2 dígitos significativos da incerteza) | testes em 30 valores conhecidos | `motor_calculo/arredondamento.py` |
| T-CAL-049 | `motor_calculo/welch_satterthwaite.py` — grau de liberdade efetivo | testes contra valores GUM tabela G.4 | idem |
| T-CAL-050 | `motor_calculo/correlacao.py` — agregação de componentes correlacionados (GUM §5.2.2) | testes 5 cenários | idem |
| T-CAL-051 | `motor_calculo/bias.py` — orçamento de polarização | testes 3 cenários | idem |
| T-CAL-052 | `motor_calculo/pfa_pra.py` — cálculo PFA + PRA (JCGM 106 §9 fórmulas 9.1 + 9.2) | testes contra tabelas ILAC G8 | idem |
| T-CAL-053 | `motor_calculo/zona_ilac_g8.py` — derivação de zona a partir de valor + U + LSL + USL + modo regra | testes 6 zonas × 3 modos = 18 casos | idem |
| T-CAL-054 | `motor_calculo/validacao_replay.py` — gerador de `replay_determinismo_hash` (HMAC inputs ordenados + outputs separados) | round-trip valida hash | idem |
| T-CAL-055 | Comparador divergência 0.1%/1% → `DivergenciaCalculoInaceitavel` exception | teste 3 cenários (silent / alert P3 / block) | idem |
| T-CAL-056 | 30 fixtures `tests/replay_metrologico/fixture_<grandeza>_<faixa>.json` — massa, volume, temperatura, pressão, comprimento, força (5 cada × 6 grandezas) | fixtures versionadas em git | `tests/replay_metrologico/` |
| T-CAL-057 | CI replay: `tests/replay_metrologico/test_replay_30_fixtures.py` — recompute bate até 9 casas decimais | suite verde | idem |
| T-CAL-058 | Hook `metrology-replay-fixtures-versionadas.sh` — bloqueia mudança em `outputs_esperados_*` sem `# replay-fixture-aceite:` no commit | hook adicionado ao `_test-runner.sh` 313+/313+ | `.claude/hooks/` |
| T-CAL-059 | API motor: `Calibracao.calcular_incerteza()` use case dispara GUM + Monte Carlo + comparador via advisory lock | integration test | `src/application/metrologia/calibracao/use_cases/calcular_incerteza.py` |
| T-CAL-060 | Documentação motor: `docs/dominios/metrologia/modulos/calibracao/motor-calculo-incerteza.md` (validação ISO 17025 cl. 7.11 + replay + IQ/OQ/PQ) | review tech-lead | `docs/dominios/.../motor-calculo-incerteza.md` |

## Fase 4 — Predicates + authz (T-CAL-061..075)

| ID | Tarefa | Pronto-quando | Caminho |
|---|---|---|---|
| T-CAL-061 | Predicate `cmc_cobre(tenant_id, grandeza, faixa_min, faixa_max, em_data)` | teste positivo + negativo | `src/infrastructure/authz/predicates_calibracao.py` |
| T-CAL-062 | Predicate `padrao_vigente_no_uso(padrao_id, em_data)` (INV-PAD-003 + INV-PAD-004) | OK | idem |
| T-CAL-063 | Predicate `procedimento_vigente_para(procedimento_id, em_data)` | OK | idem |
| T-CAL-064 | Predicate `regra_decisao_aplicavel(tenant_id, cliente_id, regra, em_data)` | OK | idem |
| T-CAL-065 | Predicate `regra_decisao_acordada_cobre(cliente_id, regra, em_data)` — novo P3 (INV-CAL-DEC-006) | testes contrato + avulsa | idem |
| T-CAL-066 | Predicate `clausula_override_vigente(cliente_id, em_data)` — novo P3 (INV-CAL-DEC-002) | OK | idem |
| T-CAL-067 | Predicate `subcontratado_vigente_para(subcontratado_id, grandeza, em_data)` + valida avaliação periódica (INV-CAL-SUBC-005) | teste avaliação vencida bloqueia | idem |
| T-CAL-068 | Predicate `rt_competencia_cobre` invocação ATIVADA em 3 use cases M4 (ADR-0063 Opção A) | drill `validar_m4_calibracao` item 3 PASS | idem (predicate existe; invocação em use cases) |
| T-CAL-069 | Predicate `pode_aprovar_revisao(user_id, calibracao_id)` (papel RT) | OK | idem |
| T-CAL-070 | Predicate `pode_aprovar_2a_conferencia(user_id, calibracao_id)` + INV-CAL-FRAUDE-CONF-001 + ADR-0026 4 condições | testes 4 cenários ADR-0026 | idem |
| T-CAL-071 | Predicate `pode_subcontratar(user_id, tenant_id)` (papel gerente_qualidade) | OK | idem |
| T-CAL-072 | Predicate `pode_marcar_nc_calibracao(user_id, calibracao_id)` | OK | idem |
| T-CAL-073 | Predicate `pode_corrigir_leitura(user_id, leitura_id)` + INV-CAL-FRAUDE-COR-001 | testes corretor=user e ≠user | idem |
| T-CAL-074 | Predicate `pode_registrar_leitura(user_id, calibracao_id)` + INV-CAL-FRAUDE-EXEC-001 | testes | idem |
| T-CAL-075 | Seed authz migration: papéis `metrologista`, `rt_calibracao`, `gerente_qualidade`, `recepcionista_lab`, `dpo` + 14 predicates registrados | migration aplica; integration test | `src/infrastructure/calibracao/migrations/0026_seed_authz_calibracao.py` |

## Fase 5 — Use cases (application) (T-CAL-076..105)

| ID | Tarefa | Pronto-quando | Caminho |
|---|---|---|---|
| T-CAL-076 | `recepcionarInstrumento` (US-CAL-001) + AC-CAL-001-3 (análise crítica inline + aviso foto) | integration test + INV-CAL-ANAL-001 | `src/application/metrologia/calibracao/use_cases/recepcionar.py` |
| T-CAL-077 | `configurarCalibracao` (US-CAL-002) + AC-CAL-002-3 (override + cláusula + A3) + ADR-0063 invoca `rt_competencia_cobre` | testes 5 cenários | `use_cases/configurar.py` |
| T-CAL-078 | `concederAceiteRegraDecisao` — novo P3 (cliente assina texto canônico) | OK | `use_cases/acordo_regra.py` |
| T-CAL-079 | `criarOverrideRegraDecisao` — novo P3 (com assinatura A3 + cláusula contratual) | OK | idem |
| T-CAL-080 | `selecionarPadrao` (US-CAL-003) + snapshot `PadraoUsado` + INV-CAL-CONC-002 + INV-CAL-RT-COMP-001 | testes concorrência | `use_cases/selecionar_padrao.py` |
| T-CAL-081 | `iniciarLeituras` (US-CAL-004) — transição configurada → em_execucao + CAS (INV-CAL-CONC-003) | testes 50 threads | `use_cases/iniciar_leituras.py` |
| T-CAL-082 | `registrarLeitura` (US-CAL-004) + AC-CAL-004-7 (UNIQUE composto) + AC-CAL-004-8 (condições ambientais) + INV-CAL-FRAUDE-EXEC-001 | DRILL-FRAUDE-CAL-1 | `use_cases/registrar_leitura.py` |
| T-CAL-083 | `corrigirLeitura` (cl. 7.5 rasura digital) + INV-CAL-FRAUDE-COR-001 | DRILL-FRAUDE-CAL-4 | `use_cases/corrigir_leitura.py` |
| T-CAL-084 | `registrarCondicoesAmbientais` (snapshot WORM) | OK | `use_cases/registrar_condicoes.py` |
| T-CAL-085 | `calcularIncerteza` (US-CAL-005) + AC-CAL-005-4..7 + motor §3.3 + advisory lock (INV-CAL-CONC-004) | testes replay 30 fixtures | `use_cases/calcular_incerteza.py` |
| T-CAL-086 | `avaliarConformidade` (US-CAL-006) + AC-CAL-006-1 6 zonas + AC-CAL-006-4 PFA/PRA | testes 18 cenários | `use_cases/avaliar_conformidade.py` |
| T-CAL-087 | `solicitarRevisao` (transição em_execucao → em_revisao_1) | OK | `use_cases/solicitar_revisao.py` |
| T-CAL-088 | `aprovarRevisao` (US-CAL-007) + AC-CAL-007-5 snapshot competência + INV-CAL-FRAUDE-REV-001 + invoca `rt_competencia_cobre` (ADR-0063) | DRILL-FRAUDE-CAL-2 | `use_cases/aprovar_revisao.py` |
| T-CAL-089 | `rejeitarRevisao` (US-CAL-007) — volta a em_execucao | OK | `use_cases/rejeitar_revisao.py` |
| T-CAL-090 | `aprovar2aConferencia` (US-CAL-008) + AC-CAL-008-4 + INV-CAL-FRAUDE-CONF-001 + ADR-0026 4 condições + invoca `rt_competencia_cobre` | DRILL-FRAUDE-CAL-3 + testes 4 condições | `use_cases/aprovar_2a_conferencia.py` |
| T-CAL-091 | `marcarNaoConformidade` (US-CAL-014) + AC-CAL-014-5 + decisão parar/continuar + cliente_notificado | testes INV-CAL-NC-002/003 | `use_cases/marcar_nao_conformidade.py` |
| T-CAL-092 | `resolverNaoConformidade` (CAPA fechado cl. 8.7) | testes 4 campos CAPA obrigatórios | `use_cases/resolver_nc.py` |
| T-CAL-093 | `subcontratarCalibracao` (US-CAL-017) + AC-CAL-017-7 touch alto risco + AC-CAL-017-8 transferência internacional + INV-CAL-SUBC-005 | testes 4 cenários | `use_cases/subcontratar.py` |
| T-CAL-094 | `registrarRecebimentoSubcontratado` + INV-CAL-FRAUDE-RECEB-001 | DRILL-FRAUDE-CAL-5 | `use_cases/registrar_recebimento_sub.py` |
| T-CAL-095 | `cancelarCalibracao` (motivo ≥30 chars anti-PII) | OK | `use_cases/cancelar.py` |
| T-CAL-096 | `abrirReclamacao` (US-CAL-018 novo) + AC-CAL-018-1 + canonicalização | OK | `use_cases/abrir_reclamacao.py` |
| T-CAL-097 | `atribuirRTReclamacao` (AC-CAL-018-2 RT independente) | OK | `use_cases/atribuir_rt_reclamacao.py` |
| T-CAL-098 | `responderReclamacao` (AC-CAL-018-4 dispara M5 recall/errata) | OK | `use_cases/responder_reclamacao.py` |
| T-CAL-099 | `cadastrarPadraoMetrologico` (US-CAL-010 + ADR-0040) | OK | `use_cases/cadastrar_padrao.py` |
| T-CAL-100 | `registrarCalibracaoExternaPadrao` (US-CAL-011) | OK | `use_cases/cal_externa_padrao.py` |
| T-CAL-101 | `executarVerificacaoIntermediaria` (US-CAL-012) | OK | `use_cases/vi_padrao.py` |
| T-CAL-102 | `registrarMedicaoControle` + Western Electric check (P-CAL-R8) | testes 4 regras WE | `use_cases/medicao_controle.py` |
| T-CAL-103 | `registrarIntercomparacao` (US-CAL-014) + `criarPlanoAcaoProficienciaWarning` (|z|∈(2,3]) + dispara `AnaliseImpactoNCProficiência` (|z|>3) | OK | `use_cases/intercomparacao.py` |
| T-CAL-104 | `gerenciarEscopoCMC` (US-CAL-015) | OK | `use_cases/escopo_cmc.py` |
| T-CAL-105 | `vincularProcedimentoVigente` (US-CAL-016) | OK | `use_cases/vincular_procedimento.py` |

## Fase 6 — Query services (T-CAL-106..113)

| ID | Tarefa | Budget p95 | Caminho |
|---|---|---|---|
| T-CAL-106 | `CalibracaoVisao360QueryService` (1 query agregadora) | ≤400ms | `src/application/metrologia/calibracao/queries/visao_360.py` |
| T-CAL-107 | `OrcamentoIncertezaQueryService` (prefetch aninhado componentes + pontos) | ≤300ms | `queries/orcamento.py` |
| T-CAL-108 | `HistoricoCalibracaoPorInstrumentoQueryService` (paginação + ordenação) | ≤500ms | `queries/historico.py` |
| T-CAL-109 | `EscopoCMCQueryService` (filtro grandeza+faixa) | ≤200ms | `queries/escopo.py` |
| T-CAL-110 | `ProficienciaPainelQueryService` (rodadas + impacto) | ≤500ms | `queries/proficiencia.py` |
| T-CAL-111 | `SubcontratacaoStatusQueryService` (avaliações vencendo) | ≤300ms | `queries/subcontratacao.py` |
| T-CAL-112 | `ReclamacoesAbertasQueryService` (prazo + RT atribuído) | ≤300ms | `queries/reclamacoes.py` |
| T-CAL-113 | Testes performance `tests/performance/test_calibracao_n_plus_one.py` `assertNumQueries(<=6)` em visão 360 + painel orçamento | suite verde | `tests/performance/` |

## Fase 7 — Jobs procrastinate (T-CAL-114..122)

| ID | Job | Cron | Caminho |
|---|---|---|---|
| T-CAL-114 | `executar_backup_metrologico` — backup diário das 19 tabelas + INSERT `EventoBackupMetrologico` | diário 02:00 BRT | `src/infrastructure/calibracao/jobs.py` |
| T-CAL-115 | `verificar_avaliacoes_subcontratados_vencendo` — alerta P2 30d antes (INV-CAL-SUBC-005) | semanal | idem |
| T-CAL-116 | `alertar_reclamacao_vencendo` — alerta P1 15d úteis pós-abertura (AC-CAL-018-3) | diário | idem |
| T-CAL-117 | `nc-responsavel-pseudonimizacao` — após 90d, zera UUID cru de `NaoConformidade.responsavel_acao_user_id` (P-CAL-A2) | diário | idem |
| T-CAL-118 | `analisar_padrao_medicoes_controle` — após cada `MedicaoControle.INSERT`, recalcula últimas 30 medições + Western Electric (P-CAL-R8) | trigger por evento | idem |
| T-CAL-119 | `analisar_correlacao_componentes` — alerta P2 quando 2+ componentes mesma `fonte_default_padrao_id` sem correlação declarada (INV-CAL-INC-004) | trigger por evento | idem |
| T-CAL-120 | `os-geo-truncamento-calibracao` — após 5a da `Calibracao.aprovada_em`, trunca geolocalização exata (P-CAL-A8 paralelo) | mensal | idem |
| T-CAL-121 | `analisar_uso_excecao_2a_conferencia` — alerta P2 em 3%/mês (AC-CAL-008-5 + P-CAL-S9) | diário | idem |
| T-CAL-122 | Management command `processar_jobs_calibracao` (wrapper) | OK | `src/infrastructure/calibracao/management/commands/processar_jobs_calibracao.py` |

## Fase 8 — Views + Serializers REST (T-CAL-123..136)

| ID | ViewSet/Endpoint | Idempotency | Caminho |
|---|---|---|---|
| T-CAL-123 | `CalibracaoViewSet` (recepcionar, configurar, cancelar) — 3 POSTs | `IdempotencyMixin` + ACTION_IDEMPOTENT mapeado plan.md | `src/infrastructure/calibracao/views.py` |
| T-CAL-124 | `LeituraViewSet` (registrar-leitura, corrigir-leitura) — 2 POSTs | idem | idem |
| T-CAL-125 | `OrcamentoIncertezaViewSet` (calcular-incerteza, avaliar-conformidade) — 2 POSTs | idem | idem |
| T-CAL-126 | `RevisaoViewSet` (aprovar-revisao, rejeitar-revisao) — 2 POSTs | idem | idem |
| T-CAL-127 | `ConferenciaViewSet` (aprovar-2a-conferencia) — 1 POST | idem | idem |
| T-CAL-128 | `NaoConformidadeViewSet` (marcar-nc, resolver-nc) — 2 POSTs | idem | idem |
| T-CAL-129 | `SubcontratacaoViewSet` (subcontratar, registrar-recebimento, gerar-aceite) — 3 POSTs | idem | idem |
| T-CAL-130 | `PadraoViewSet` (cadastrar, recal-externo, intercomparacao, medicao-controle, baixar, sucatear) — 6 POSTs | idem | idem |
| T-CAL-131 | `EscopoViewSet` + `ProficienciaViewSet` + `VerificacaoIntermediariaViewSet` — 3 POSTs | idem | idem |
| T-CAL-132 | `ReclamacaoViewSet` (abrir, atribuir-rt, responder) — 3 POSTs (US-CAL-018) | idem | idem |
| T-CAL-133 | `AceiteRegraDecisaoViewSet` + `OverrideRegraDecisaoViewSet` — 2 POSTs | idem | idem |
| T-CAL-134 | Serializers DRF (1 por entidade visível na API; ~25 serializers) | mypy clean | `src/infrastructure/calibracao/serializers.py` |
| T-CAL-135 | URLs + roteamento `urls.py` (`/api/v1/calibracao/...`) | OK | `src/infrastructure/calibracao/urls.py` |
| T-CAL-136 | Hook `idempotency-key-header-check` estendido pra `src/infrastructure/calibracao/` validar ACTION_IDEMPOTENT map (INV-CAL-IDEMP-001) | hook 313+/313+ | `.claude/hooks/idempotency-key-header-check.sh` |

## Fase 9 — Hooks novos M4 P9 (T-CAL-137..144)

| ID | Hook | INVs |
|---|---|---|
| T-CAL-137 | `cmc-binding-check.sh` | INV-002, INV-CAL-CMC-001 |
| T-CAL-138 | `incerteza-versao-motor-check.sh` | INV-CAL-VERSAO-001 |
| T-CAL-139 | `hmac-versao-formato-check.sh` | INV-HMAC-001 |
| T-CAL-140 | `migration-metrology-classifier.sh` (convenção tag em migration) | ADR-0025 cl. 7.11.3 + GATE-CAL-MIG-CLASSIF |
| T-CAL-141 | `migration-concorrencia-calibracao-check.sh` | INV-CAL-CONC-001..004 |
| T-CAL-142 | `metrology-replay-fixtures-versionadas.sh` (já criado em T-CAL-058) | INV-CAL-VERSAO-001 + §3.3 |
| T-CAL-143 | `foto-exif-strip-check.sh` | INV-CAL-FOTO-001 + LPI art. 195 |
| T-CAL-144 | `override-regra-decisao-contrato-check.sh` | INV-CAL-DEC-002 + CDC art. 25/51 |

**Cobertura no `_test-runner.sh` esperada após T-CAL-137..144:** **312 (atual) + 8 hooks × ~10 casos cada = ~80 casos novos = ~392/392.**

## Fase 10 — Regressões + drill `validar_m4_calibracao` (T-CAL-145..160)

| ID | Tarefa | Cobertura |
|---|---|---|
| T-CAL-145 | Testes regressão INV-CAL-CONC-001..004 + AUD-002 | 5 arquivos |
| T-CAL-146 | Testes regressão INV-CAL-DEC-004..006 | 3 arquivos |
| T-CAL-147 | Testes regressão INV-CAL-INC-002..004 | 3 arquivos |
| T-CAL-148 | Testes regressão INV-CAL-ANAL-001 + INV-CAL-RT-002 + INV-CAL-RAST-002 | 3 arquivos |
| T-CAL-149 | Testes regressão INV-CAL-SUBC-005..006 + INV-CAL-NC-002..003 | 4 arquivos |
| T-CAL-150 | Testes regressão INV-CAL-AMB-001 + INV-CAL-BACKUP-001 + INV-CAL-PAD-CASCADE-001 + INV-CAL-ANON-001 + INV-CAL-CONT-001 | 5 arquivos |
| T-CAL-151 | Testes regressão INV-CAL-IDEMP-001 + INV-CAL-FRAUDE-RECEB-001 + DRILL-FRAUDE-CAL-1..5 | 5+5 arquivos |
| T-CAL-152 | Testes carga concorrência: `test_concorrencia_registrar_leitura.py` (50 threads) + `test_calibracao_revision_cas.py` (50 threads aprovar_revisao) + `test_hash_chain_calibracao_concorrente.py` (100 inserts em 4 workers) | 3 arquivos |
| T-CAL-153 | Testes replay metrológico `tests/replay_metrologico/test_replay_30_fixtures.py` — 30 fixtures × 2 algoritmos = 60 testes | suite verde |
| T-CAL-154 | Testes performance `tests/performance/test_calibracao_n_plus_one.py` + `test_orcamento_painel_n_plus_one.py` `assertNumQueries(<=6)` | 2 arquivos |
| T-CAL-155 | Testes integração: fluxo feliz completo (recepcionar → configurar → registrar 5 leituras → calcular incerteza → avaliar → aprovar revisão → aprovar 2ª → publicar `Calibracao.Aprovada`) | 1 arquivo |
| T-CAL-156 | Testes saga: subcontratação (configurar → subcontratar → aceite cliente A3 → registrar recebimento → revisão → 2ª → aprovada) | 1 arquivo |
| T-CAL-157 | Testes consumer: `Cliente.AnonimizacaoSolicitada` bloqueia + `Padrao.Baixado` cascateia | 2 arquivos |
| T-CAL-158 | Management command `validar_m4_calibracao` — 25 checagens listadas em plan.md §"Drill" | comando aprovado | `src/infrastructure/calibracao/management/commands/validar_m4_calibracao.py` |
| T-CAL-159 | Drill `validar_m4_calibracao` PASS em ambiente local dogfooding (Balanças Solution) | 25/25 PASS | — |
| T-CAL-160 | Snapshot estado pós-P4: pytest geral ≥985/0/0, hooks 392+/392+, ruff zero, mypy zero, drift docs ZERADO (CURRENT.md + AGENTS.md + diário fase) | atualização final commit | `.agent/CURRENT.md` + `AGENTS.md` |

## Tarefas P3.5 paralelas (não bloqueiam P4 dogfooding)

| ID | Tarefa | Bloqueia | Status |
|---|---|---|---|
| T-CAL-P35-1 | Minuta `docs/conformidade/comum/minutas/dpa-laboratorio-subcontratado-v1.0.md` (selo REQUER OAB) | 1º tenant externo | PENDENTE |
| T-CAL-P35-2 | Minuta `docs/conformidade/comum/termos/aceite-subcontratacao-v1.0.md` (selo REQUER OAB) | 1º tenant externo | PENDENTE |
| T-CAL-P35-3 | Minuta `docs/conformidade/comum/minutas/clausula-override-regra-decisao-v1.0.md` (selo REQUER OAB) | 1º tenant externo | PENDENTE |
| T-CAL-P35-4 | Minuta `docs/conformidade/comum/termos/aviso-foto-recepcao-v1.0.md` (selo REQUER OAB) | 1º tenant externo | PENDENTE |
| T-CAL-P35-5 | Minuta `docs/conformidade/comum/termos/aceite-regra-decisao-v1.0.md` (selo REQUER OAB) | 1º tenant externo | PENDENTE |
| T-CAL-P35-6 | Minuta `docs/conformidade/comum/termos/consentimento-contato-tecnico-cliente-v1.0.md` (selo REQUER OAB) | 1º tenant externo | PENDENTE |
| T-CAL-P35-7 | Matriz `docs/dominios/metrologia/modulos/calibracao/componentes-obrigatorios-por-grandeza.md` (selo REQUER CGCRE — NIT-DICLA-030 §6.3) | 1º tenant externo RBC | PENDENTE |
| T-CAL-P35-8 | Matriz `docs/dominios/metrologia/modulos/calibracao/formula-calculo-por-grandeza.md` (selo REQUER CGCRE — Tipo A + correlação + arredondamento) | 1º tenant externo RBC | PENDENTE |
| T-CAL-P35-9 | Política `docs/conformidade/comum/politicas/criterio-selecao-subcontratado-v1.0.md` (selo REQUER CGCRE — cl. 6.6.2 a-f) | 1º tenant externo | PENDENTE |
| T-CAL-P35-10 | Texto canônico `docs/conformidade/comum/textos/declaracao-subcontratacao-certificado-v1.0.md` (selo REQUER OAB+CGCRE — ILAC G18 §6.3) | 1º tenant externo | PENDENTE |
| T-CAL-P35-11 | ADR-0028 rev 3 com 8 cláusulas novas + Modalidade 8 NOVA (Property — Owned Metrological Standards) | 1º tenant externo + GATE-SEG-BPT-PADROES-1 dogfooding | PENDENTE |
| T-CAL-P35-12 | DPIA-calibracao `docs/conformidade/comum/dpia/dpia-calibracao.md` (selo REQUER OAB) | 1º tenant externo | PENDENTE |
| T-CAL-P35-13 | Atualização `docs/governanca/gates-wave-a-consolidado.md` com 33 GATEs M4 | tracking Wave A | PENDENTE |
| T-CAL-P35-14 | `docs/conformidade/comum/seguros/briefing-corretora-susep.md` atualizado com 9 cláusulas M4 + casos narrativos | corretora SUSEP humana | PENDENTE |

## Critérios binários de fechamento P4

- 160 T-CAL marcadas ✅ (ou TRACK Wave A com gate rastreado).
- Suite pytest chave M4 ≥80 testes verdes.
- pytest geral ≥985/0/0 (atual 905 + ~80 M4).
- Hooks `_test-runner.sh` ≥392/392.
- ruff + mypy zero issues em `src/{domain/metrologia/calibracao,infrastructure/calibracao,application/metrologia/calibracao}/**`.
- Drill `validar_m4_calibracao` 25/25 PASS.
- Anti-replay `pytest --randomly-seed=$(date +%s)` 3x zero flake.
- Drift docs ZERADO (CURRENT.md ≤40 linhas, AGENTS.md contagens reais).

## Próximo passo

Iniciar **Fase 1 (T-CAL-001..025 — migrations + DDL constraints)** assim que Roldão autorizar entrar em P4.
