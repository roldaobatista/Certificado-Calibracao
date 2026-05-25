---
owner: roldao
revisado_em: 2026-05-25
proximo_review: 2026-08-25
status: stable
diataxis: reference
audiencia: agente
marco: Wave A Marco 4 — metrologia/calibracao
tipo: matriz-reconciliacao-P3
relacionados:
  - docs/faseamento/M4-calibracao/spec.md
  - docs/faseamento/M4-calibracao/plan.md
  - docs/faseamento/M4-calibracao/reviews/tech-lead.md
  - docs/faseamento/M4-calibracao/reviews/advogado.md
  - docs/faseamento/M4-calibracao/reviews/corretora.md
  - docs/faseamento/M4-calibracao/reviews/rbc.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de Reconciliação — Marco 4 (metrologia/calibracao) — P3 ritual Spec Kit

> **P3 do ritual (2026-05-25):** após P2 (4 reviews paralelos) + `plan.md` ata + retrofit `spec.md` §16 + retrofit `prd.md` §11 + ADR-0065 nova + retrofit ADR-0024 + retrofit ADR-0063 + 24 INVs em REGRAS, esta matriz consolida o estado canônico para verificar **zero conflito** PRD ↔ spec ↔ plan ↔ ADRs ↔ REGRAS.
>
> **Critério de fechamento P3:** todas as linhas mostram "consistente" em PRD / spec / plan / ADRs / REGRAS. Linha divergente bloqueia passagem para P4 (`tasks.md` + implement).

## 1. ACs ↔ INVs ↔ ADRs ↔ Hooks (ACs novos P3)

### US-CAL-001 (Recepcionar instrumento) + US-CAL-018 (Reclamação nova)

| AC | INV | ADR | Hook validador | spec.md ref | prd.md ref | Status |
|---|---|---|---|---|---|---|
| AC-CAL-001-3 (análise crítica avulsa + foto base legal) | INV-CAL-ANAL-001 | — | hook recepcao-avulsa-analise-check (P9) | §16.4 + §3.2 `Calibracao.analise_critica_pedido_inline_*` | §11.1 + §6 US-CAL-001 | ✅ consistente |
| AC-CAL-018-1 (abrir reclamação ≤90d) | — | — | — | §16.17 US-CAL-018 + entidade `ReclamacaoCalibracao` | §11.2 US-CAL-018 | ✅ consistente |
| AC-CAL-018-2 (RT independente atribuído) | — | ADR-0026 (independência paralela) | — | §16.17 | §11.2 | ✅ consistente |
| AC-CAL-018-3 (alerta P1 em 15d úteis) | — | — | job procrastinate `alertar_reclamacao_vencendo` | §16.17 | §11.2 | ✅ consistente |
| AC-CAL-018-4 (decisão dispara M5 recall) | — | ADR-0045 (M5 recall) | — | §16.15 evento `Calibracao.ReclamacaoRespondida` | §11.2 | ✅ consistente |

### US-CAL-002 (Configurar calibração)

| AC | INV | ADR | Hook validador | spec.md ref | prd.md ref | Status |
|---|---|---|---|---|---|---|
| AC-CAL-002-3 (override cliente exige cláusula + A3) | INV-CAL-DEC-002 | ADR-0024 revisado | hook `override-regra-decisao-contrato-check.sh` (P9) | §16.4 `Calibracao.regra_decisao_acordada_*` + §16.3 entidade `OverrideRegraDecisaoCliente` | §11.1 | ✅ consistente |

### US-CAL-004 (Registrar leituras)

| AC | INV | ADR | Hook validador | spec.md ref | prd.md ref | Status |
|---|---|---|---|---|---|---|
| AC-CAL-004-7 (UNIQUE composto ponto+repetição) | INV-CAL-CONC-001 | ADR-0065 | hook `migration-concorrencia-calibracao-check.sh` (P9) | §16.4 + §3.2 `Leitura` UNIQUE | §11.1 | ✅ consistente |
| AC-CAL-004-8 (condições ambientais fora bloqueia) | INV-CAL-AMB-001 | — | — | §16.13 `CondicoesAmbientais.dentro_tolerancia` | §11.1 | ✅ consistente |

### US-CAL-005 (Calcular incerteza)

| AC | INV | ADR | Hook validador | spec.md ref | prd.md ref | Status |
|---|---|---|---|---|---|---|
| AC-CAL-005-4 (componentes mínimos por grandeza) | INV-CAL-INC-002 | NIT-DICLA-030 §6.3 | — (matriz preliminar pelo agente; REQUER CGCRE) | §16.6 `ComponenteIncerteza.tipo_origem_componente` ENUM | §11.1 | ✅ consistente |
| AC-CAL-005-5 (Tipo A n≥6 + s_x) | INV-CAL-INC-003 | NIT-DICLA-030 §7.4 + GUM JCGM 100 §4.2 | CHECK DDL | §16.6 `ComponenteIncerteza.n_amostras CHECK >= 6` | §11.1 | ✅ consistente |
| AC-CAL-005-6 (correlação cross-componente) | INV-CAL-INC-004 | GUM §5.2.2 | job `analisar_correlacao_componentes` | §16.6 `correlacao_com_componente_id` | §11.1 | ✅ consistente |
| AC-CAL-005-7 (arredondamento NIT-DICLA-030 §7.5) | — | NIT-DICLA-030 §7.5 + cl. 7.8.3.1.h | — | §16.6 `arredondamento_aplicado_regra` | §11.1 | ✅ consistente |

### US-CAL-006 (Avaliar conformidade)

| AC | INV | ADR | Hook validador | spec.md ref | prd.md ref | Status |
|---|---|---|---|---|---|---|
| AC-CAL-006-1 MODIFICADO (6 zonas ILAC G8) | INV-CAL-DEC-005 | ADR-0024 revisado + ILAC G8:09/2019 §4 | CHECK DDL `zona_ilac_g8 ENUM` | §16.4 + §3.2 `Calibracao.zona_ilac_g8` ENUM 7 valores | §11.1 | ✅ consistente |
| AC-CAL-006-4 (PFA/PRA documentados) | INV-CAL-DEC-004 | ADR-0024 revisado + ILAC G8 §4.4 + JCGM 106 §9 | — | §16.4 `pfa_calculada` / `pra_calculada` NOT NULL condicional | §11.1 | ✅ consistente |

### US-CAL-007 + US-CAL-008 (Revisão + 2ª conferência)

| AC | INV | ADR | Hook validador | spec.md ref | prd.md ref | Status |
|---|---|---|---|---|---|---|
| AC-CAL-007-5 (snapshot competência revisor) | INV-CAL-RT-002 | ADR-0022 + ADR-0063 Opção A | — | §16.4 `snapshot_competencia_revisor_json` | §11.1 | ✅ consistente |
| AC-CAL-008-4 (snapshot competência conferente + invariância) | INV-CAL-RT-002 + INV-CAL-CONF-001 + INV-CAL-FRAUDE-CONF-001 | ADR-0026 + ADR-0063 Opção A | — | §16.4 `snapshot_competencia_conferente_json` | §11.1 | ✅ consistente |
| AC-CAL-008-5 (alerta P2 em 3%/mês exceção) | — | ADR-0026 + P-CAL-S9 corretora | job `analisar_uso_excecao_2a_conferencia` | (entra em §3.3 motor + §3.2 `Excecao2aConferencia`) | §11.1 | ✅ consistente |

### US-CAL-014 (Proficiência + impacto)

| AC | INV | ADR | Hook validador | spec.md ref | prd.md ref | Status |
|---|---|---|---|---|---|---|
| AC-CAL-014-5 (decisão parar/continuar + notificação cliente) | INV-CAL-NC-002 + INV-CAL-NC-003 | cl. 7.10.1/2 | CHECK constraint composta | §16.9 `NaoConformidade.decisao_continuar_ou_parar` + `cliente_notificado_em` | §11.1 | ✅ consistente |

### US-CAL-017 (Subcontratar cl. 6.6)

| AC | INV | ADR | Hook validador | spec.md ref | prd.md ref | Status |
|---|---|---|---|---|---|---|
| AC-CAL-017-7 (touch alto risco exige declaração extra) | INV-CAL-SUBC-005 (parcial) | Lei 14.063 art. 4º + P-CAL-A1 | — | §16.11 `AceiteSubcontratacao.assinatura_modo` + `declaracao_aceite_touch_alto_risco_id` | §11.1 | ✅ consistente |
| AC-CAL-017-8 (transferência internacional sem base) | INV-CAL-SUBC-005 | LGPD art. 33 + P-CAL-A1 | — | §16.10 `LaboratorioSubcontratado.pais` + `dpa_clausulas_internacionais_id` | §11.1 | ✅ consistente |

## 2. INVs novas ↔ Drills/Testes

| INV | Origem | Drill / teste obrigatório | Hook | Fase |
|---|---|---|---|---|
| INV-CAL-CONC-001 | ADR-0065 + P-CAL-T1 | `tests/carga/test_concorrencia_registrar_leitura.py` (50 threads) | migration-concorrencia-calibracao-check | P10 |
| INV-CAL-CONC-002 | ADR-0065 | `tests/regressao/test_padrao_usado_unico_parcial.py` | idem | P10 |
| INV-CAL-CONC-003 | ADR-0065 | `tests/carga/test_calibracao_revision_cas.py` (50 threads aprovar_revisao) | idem | P10 |
| INV-CAL-CONC-004 | ADR-0065 | `tests/regressao/test_advisory_lock_calcular_incerteza.py` (4 workers) | idem | P10 |
| INV-CAL-AUD-002 | ADR-0065 | `tests/regressao/test_hash_chain_calibracao_concorrente.py` (100 inserts) | idem | P10 |
| INV-CAL-DEC-004 | ADR-0024 revisado + P-CAL-R1 | `tests/regressao/test_pfa_obrigatorio_banda_guarda.py` | — | P10 |
| INV-CAL-DEC-005 | ADR-0024 revisado + ILAC G8 | `tests/regressao/test_zona_ilac_g8_enum.py` | CHECK DDL | P1 |
| INV-CAL-DEC-006 | ADR-0024 revisado + cl. 7.1.3 | `tests/regressao/test_acordo_cliente_rbc.py` | override-regra-decisao-contrato-check | P10 |
| INV-CAL-INC-002 | NIT-DICLA-030 §6.3 + P-CAL-R2 | `tests/regressao/test_componentes_minimos_grandeza.py` | — | P10 |
| INV-CAL-INC-003 | NIT-DICLA-030 §7.4 + P-CAL-R7 | `tests/regressao/test_tipo_a_n_amostras_seis.py` | CHECK DDL | P10 |
| INV-CAL-INC-004 | GUM §5.2.2 + P-CAL-R7 | `tests/regressao/test_correlacao_componentes.py` | — | P10 |
| INV-CAL-ANAL-001 | cl. 7.1.1 + P-CAL-R4 | `tests/regressao/test_recepcao_avulsa_analise_critica.py` | — | P10 |
| INV-CAL-RT-002 | ADR-0022 + P-CAL-R10 | `tests/regressao/test_snapshot_competencia_rt_aprovacao.py` | — | P10 |
| INV-CAL-RAST-002 | cl. 6.5.2 + P-CAL-R9 | `tests/regressao/test_rastreabilidade_si_rbc_interno_proibido.py` | CHECK DDL | P10 |
| INV-CAL-SUBC-005 | cl. 6.6.2 + P-CAL-R5 | `tests/regressao/test_subcontratado_avaliacao_vencida.py` | — | P10 |
| INV-CAL-SUBC-006 | ILAC G18 + P-CAL-R12 | `tests/regressao/test_declaracao_subcontratacao_cert.py` | — | P10 |
| INV-CAL-NC-002 | cl. 7.10.1 + P-CAL-R6 | `tests/regressao/test_nc_decisao_continuar_parar.py` | CHECK composta | P10 |
| INV-CAL-NC-003 | cl. 7.10.2 + P-CAL-R6 | `tests/regressao/test_nc_parar_exige_cliente_notificado.py` | CHECK composta | P10 |
| INV-CAL-AMB-001 | cl. 6.3.1 + P-CAL-R13 | `tests/regressao/test_condicoes_ambientais_tolerancia.py` | — | P10 |
| INV-CAL-BACKUP-001 | cl. 7.11.6 + P-CAL-R11 | `tests/regressao/test_backup_metrologico_gap_alerta.py` | — | P10 |
| INV-CAL-PAD-CASCADE-001 | ADR-0040 + P-CAL-R14 | `tests/regressao/test_consumer_padrao_baixado_cascata.py` | — | P10 |
| INV-CAL-ANON-001 | LGPD art. 16 + ADR-0021 + P-CAL-A8 | `tests/regressao/test_anonimizacao_bloqueada_calibracao_aberta.py` | — | P10 |
| INV-CAL-IDEMP-001 | IDEMP-001 + P-CAL-T7 | `tests/regressao/test_idempotency_payload_mismatch.py` | idempotency-key-header-check estendido | P10 |
| INV-CAL-CONT-001 | LGPD art. 11 + P-CAL-A6 | `tests/regressao/test_consentimento_contato_pf.py` | — | P10 |
| INV-CAL-FRAUDE-RECEB-001 | cl. 6.2.5 + P-CAL-T9 | `tests/regressao/test_drill_fraude_cal_5_recebedor.py` (DRILL-FRAUDE-CAL-5) | — | P10 |

## 3. ADRs ↔ entidades novas ↔ hooks

| ADR | Entidades afetadas | Hook | Migration |
|---|---|---|---|
| ADR-0065 (concorrência) | `Leitura` UNIQUE, `PadraoUsado` UNIQUE parcial, `Calibracao.revision`, `EventoDeCalibracao.sequencia_local` | migration-concorrencia-calibracao-check | P1 (M4) |
| ADR-0024 revisado (6 zonas + PFA + AceiteRegraDecisao) | `Calibracao.zona_ilac_g8`, `pfa_calculada`, `pra_calculada`, `regra_decisao_acordada_*`, `AceiteRegraDecisao` (nova), `OverrideRegraDecisaoCliente` (nova) | override-regra-decisao-contrato-check | P1+P3 (M4) |
| ADR-0025 (validação software) → §3.3 motor | `OrcamentoIncerteza.algoritmo_1_resultado`, `algoritmo_2_resultado`, `divergencia_pct`, `replay_determinismo_hash` | metrology-replay-fixtures-versionadas, incerteza-versao-motor-check | P1+P2 (M4) |
| ADR-0063 Opção A (lazy) | `AtividadeDaOS.grandeza` (migration cross-marco M3), invocação em 3 use cases M4 | — | P1+P4 (M4) |
| ADR-0040 (padrão entidade separada) | `PadraoUsado.vinculacao_si_*` (estruturado top-level) | — | P1 (M4) |
| ADR-0064 (rotação HMAC 25a) | Todos `*_hash CHAR(80)` em formato `v<NN>$<base64>` | hmac-versao-formato-check | P2 (M4) |

## 4. GATEs Wave A ↔ dependências externas

| GATE | Bloqueio | Dependência humana | Mitigação dogfooding |
|---|---|---|---|
| GATE-CAL-ZONAS-ILAC-G8 | M4 P4 | tech-lead + CGCRE consultivo | Implementação técnica suficiente; revisão CGCRE pré-tenant externo |
| GATE-CAL-COMPONENTES-MIN 🔴 | 1º tenant externo RBC | CGCRE humano (matriz por grandeza) | Matriz preliminar pelo agente baseada em NIT-DICLA-030 |
| GATE-CAL-ACEITE-REGRA-DEC 🔴 | 1º tenant externo RBC | CGCRE + OAB | Texto preliminar pelo agente; selo REQUER VALIDAÇÃO |
| GATE-CAL-ANAL-CRIT-AVULSA | M4 P4 | — | Implementado em §16.4 (validação CHECK constraint composta) |
| GATE-CAL-SUBC-AVAL 🔴 | Wave A operacional | CGCRE humano (template política) | Política preliminar pelo agente |
| GATE-CAL-NC-CLIENTE-NOTIF | M4 P4 | — | Implementado §16.9 |
| GATE-CAL-INC-FORMULA 🔴 | 1º tenant externo RBC | CGCRE humano | Fórmulas preliminares pelo agente |
| GATE-CAL-EP-WARNING | M4 P4 | — | Implementado §16.8 |
| GATE-CAL-RAST-SI-ENUM | M4 P4 | — | Implementado §16.7 + INV-CAL-RAST-002 |
| GATE-CAL-RT-SNAPSHOT | M4 P4 | — | Implementado §16.4 |
| GATE-CAL-BACKUP-METROL | M4 P4 + Wave A operacional | — | Implementado §16.3 entidade `EventoBackupMetrologico` |
| GATE-CAL-SUBC-WORDING 🔴 | 1º tenant externo | CGCRE + OAB | Wording preliminar pelo agente |
| GATE-CAL-SUBC-OAB 🔴 | 1º tenant externo | OAB humana | Minutas DPA + aceite + touch alto risco preliminares |
| GATE-CAL-PII-SAUDE-OAB 🔴 | 1º tenant externo farma/saúde | OAB humana | Lista palavra-chave preliminar pelo agente |
| GATE-CAL-OVERRIDE-OAB 🔴 | 1º tenant externo | OAB humana | Cláusula preliminar pelo agente |
| GATE-CAL-RECLAMACAO-FLUXO | 1º tenant externo | — | Implementado §16.17 |
| GATE-CAL-FOTO-OAB 🔴 | 1º tenant externo | OAB humana | Aviso + RIPD preliminares |
| GATE-CAL-CONT-OAB 🔴 | 1º tenant externo | OAB humana | Texto consentimento preliminar |
| GATE-CAL-FOTO-EXIF-HOOK | 1º tenant externo | — | Hook P9 |
| GATE-CAL-ANON-CONCORRENCIA | 1º tenant externo PF | — | INV-CAL-ANON-001 |
| GATE-SEG-EO-CAL-1 🔴 | 1º tenant externo farma | corretora SUSEP | Wordings prontos em plan.md |
| GATE-SEG-SUBC-1 🔴 | 1º tenant externo | corretora SUSEP | idem |
| GATE-SEG-CYBER-HMAC-1 🔴 | 1º tenant externo | corretora SUSEP (Lloyd's) | idem |
| GATE-SEG-EO-INVEST-1 🔴 | 1º tenant externo | corretora SUSEP | idem |
| GATE-SEG-EO-FRAUDE-1 🔴 | 1º tenant externo | corretora SUSEP | idem |
| GATE-SEG-BPT-PADROES-1 🔴 | Dogfooding com padrão R$ 500k | corretora SUSEP ou endosso multirrisco | Verificar apólice corporativa Balanças Solution |
| GATE-SEG-CYBER-PATIENT-1 🔴 | 1º tenant externo farma | corretora SUSEP | Wording em plan.md |
| GATE-SEG-EO-CONSENT-1 🔴 | 1º tenant externo | corretora SUSEP + OAB texto v1.0 | Wording em plan.md |
| GATE-SEG-ACR-EXCECAO-1 🔴 | 1º tenant externo | corretora SUSEP | Wording em plan.md |
| GATE-CAL-ACREDITACAO-CONSUMER | 1º tenant externo RBC | ADR-0014 aceita + produtor | M4 entrega fail-closed placeholder |
| GATE-CAL-MIG-CLASSIF | M4 P4 | — | Hook P9 |
| GATE-CAL-DRILL | M4 P4 | — | Drill `validar_m4_calibracao` 25 checagens |
| GATE-CAL-MATRIZES-CGCRE 🔴 | 1º tenant externo RBC | CGCRE humano | Matrizes preliminares pelo agente |

**Total: 33 GATEs Wave A novos M4** (32 listados na plan.md + GATE-CAL-MATRIZES-CGCRE que consolida D-M4-4).

## 5. Hooks novos M4 P9 (8 hooks)

| Hook | INVs validadas | Quando criado | Status atual |
|---|---|---|---|
| `cmc-binding-check.sh` | INV-002, INV-CAL-CMC-001 | P9 | pendente |
| `incerteza-versao-motor-check.sh` | INV-CAL-VERSAO-001 | P9 | pendente |
| `hmac-versao-formato-check.sh` | INV-HMAC-001 | P9 | pendente |
| `migration-metrology-classifier.sh` | ADR-0025 cl. 7.11.3 + GATE-CAL-MIG-CLASSIF | P9 | pendente |
| `migration-concorrencia-calibracao-check.sh` | INV-CAL-CONC-001..004 | P9 | pendente |
| `metrology-replay-fixtures-versionadas.sh` | INV-CAL-VERSAO-001 + §16.5 motor | P9 | pendente |
| `foto-exif-strip-check.sh` | INV-CAL-FOTO-001 + LPI art. 195 | P9 | pendente |
| `override-regra-decisao-contrato-check.sh` | INV-CAL-DEC-002 + CDC art. 25/51 | P9 | pendente |

## 6. Eventos publicados ↔ consumers

### Eventos novos M4 (9, somam aos da §6.1 original)

| Evento | Publicado por | Consumidores externos | INV |
|---|---|---|---|
| `Calibracao.AceiteRegraDecisaoConcedido` | `concederAceiteRegraDecisao` | M5 cert (informa cliente assinou) | INV-CAL-DEC-006 |
| `Calibracao.OverrideRegraDecisaoCriado` | `criarOverrideRegraDecisao` | M5 + observabilidade | INV-CAL-DEC-002 |
| `Calibracao.ReclamacaoAberta` | `abrirReclamacao` | M5 + DPO + observabilidade | — |
| `Calibracao.ReclamacaoRespondida` | `responderReclamacao` | M5 (saga recall/errata) | — |
| `Calibracao.NCDecisaoParar` | `marcarNaoConformidade(PARAR_TRABALHO)` | M3 OS (atividade marca NC bloqueante) | INV-CAL-NC-003 |
| `Calibracao.PlanoAcaoProficienciaWarningCriado` | consumer `Padrao.IntercomparacaoConcluida(WARNING)` | qualidade (não NC formal) | — |
| `Calibracao.BackupExecutado` | job procrastinate `executar_backup_metrologico` | observabilidade (alerta P1 se gap>25h) | INV-CAL-BACKUP-001 |
| `Calibracao.AvaliacaoSubcontratadoVencendo` | job procrastinate `verificar_avaliacoes_subcontratados_vencendo` | gerente qualidade | INV-CAL-SUBC-005 |
| `Calibracao.ConfiguradaComBloqueioConcorrencia` | quando 409 ConflitoVersao em transição | observabilidade (medir contenção) | INV-CAL-CONC-003 |

### Consumers novos M4 (2)

| Evento consumido | Origem | Ação no M4 | INV |
|---|---|---|---|
| `Cliente.AnonimizacaoSolicitada` | `comercial/clientes` | INV-CAL-ANON-001 — bloqueia se Calibracao aberta; publica `AnonimizacaoBloqueada` | INV-CAL-ANON-001 |
| `Padrao.Baixado` / `Padrao.Sucateado` | `metrologia/padroes` | INV-CAL-PAD-CASCADE-001 — marca calibrações em_execucao como nao_conforme | INV-CAL-PAD-CASCADE-001 |

## 7. Riscos novos ↔ Mitigações

| Risco | Severidade | Mitigação técnica | GATE Wave A |
|---|---|---|---|
| R-M4-18 (subcontratado erra) | ALTO | INV-CAL-SUBC-005 + INV-CAL-SUBC-002 | GATE-SEG-SUBC-1 |
| R-M4-19 (fraude criminal técnico) | CRÍTICO | 4 INV-CAL-FRAUDE-* + DRILL-FRAUDE-CAL-1..5 | GATE-SEG-EO-FRAUDE-1 |
| R-M4-20 (padrão próprio extraviado) | MÉDIO | — | GATE-SEG-BPT-PADROES-1 (Modalidade 8) |
| R-M4-21 (foto paciente farma) | ALTO | hook foto-exif-strip-check + DPIA + redação OCR | GATE-SEG-CYBER-PATIENT-1 |
| R-M4-22 (consent vicioso subcontratação) | MÉDIO | texto canônico OAB v1.0 + AceiteSubcontratacao hash | GATE-SEG-EO-CONSENT-1 |

## 8. Critérios de fechamento P3 (verificação binária)

- [x] 10 BLOQUEANTES dos 4 reviews absorvidos em spec.md §16 e/ou ADR.
- [x] 23 MÉDIOS absorvidos em spec.md §16 / prd.md §11 / REGRAS (INVs).
- [x] 14 ALTOs rastreados como GATEs Wave A em plan.md + matriz §4.
- [x] 3 ACEITEs rastreados (P-CAL-R15, R16, S10).
- [x] ADR-0065 nova criada e aceita (commit b1c1d6a).
- [x] ADR-0024 retrofit aceito (6 zonas + PFA + AceiteRegraDecisao).
- [x] ADR-0063 esclarecido aceito (Opção A lazy).
- [x] 24 INVs CAL novos cravados em REGRAS-INEGOCIAVEIS.md.
- [x] PRD §11 absorve 11 ACs novos + US-CAL-018 nova.
- [x] Spec.md §16 absorve mudanças de schema + entidades + motor §3.3.
- [x] 8 entidades novas em §16.3.
- [x] 9 eventos novos publicados + 2 consumers novos.
- [x] 5 riscos novos R-M4-18..22 mapeados.
- [x] 32+1 GATEs Wave A consolidados em §4 desta matriz.
- [x] 8 hooks novos M4 P9 listados em §5.
- [x] Drill `validar_m4_calibracao` 25 checagens em plan.md.
- [x] Hooks `_test-runner.sh` 312/312 verdes pós-P3 (commit `b1c1d6a`).
- [ ] 5 minutas canônicas preliminares geradas pelo agente (P3.5).
- [ ] 2 matrizes técnicas preliminares geradas pelo agente (P3.5).
- [ ] tasks.md com ~150 T-CAL-NNN (P3 final).

**Status P3:** 17 / 20 critérios ✅. Restam 3 itens (3 entregáveis documentais P3.5 + tasks.md) para destravar P4.

## 9. Pendências para fechar P3

1. **tasks.md** (~150 T-CAL-NNN em 10 fases) — destrava P4.
2. **5 minutas canônicas preliminares** (selo REQUER OAB) — destrava 1º tenant externo:
   - `docs/conformidade/comum/minutas/dpa-laboratorio-subcontratado-v1.0.md`
   - `docs/conformidade/comum/termos/aceite-subcontratacao-v1.0.md`
   - `docs/conformidade/comum/minutas/clausula-override-regra-decisao-v1.0.md`
   - `docs/conformidade/comum/termos/aviso-foto-recepcao-v1.0.md`
   - `docs/conformidade/comum/termos/aceite-regra-decisao-v1.0.md`
3. **2 matrizes técnicas preliminares** (selo REQUER CGCRE) — destrava 1º tenant externo RBC:
   - `docs/dominios/metrologia/modulos/calibracao/componentes-obrigatorios-por-grandeza.md`
   - `docs/dominios/metrologia/modulos/calibracao/formula-calculo-por-grandeza.md`

Item (1) **bloqueia P4**. Itens (2) e (3) **NÃO bloqueiam P4 dogfooding** — bloqueiam apenas 1º tenant externo pago.

## 10. Próximo passo

`tasks.md` ~150 T-CAL-NNN granulares em 10 fases — destrava P4 (`/implement`).
