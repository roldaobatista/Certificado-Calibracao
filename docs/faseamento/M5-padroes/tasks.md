---
owner: roldao
revisado-em: 2026-05-28
status: draft
fase: M5-padroes
dominio: metrologia
modulo: padroes
ritual: tasks
versao: 1
depende-de:
  - docs/faseamento/M5-padroes/plan.md (v2 ready-for-tasks)
  - docs/faseamento/M5-padroes/reviews-consolidado.md
  - docs/adr/0070-carta-controle-shewhart-hibrida-readmodel-worm.md
  - docs/adr/0071-segundo-caminho-calculo-duas-implementacoes-mesmo-mensurando.md
  - docs/adr/0072-path-infra-metrologia-aninhado.md
---

# Tasks — M5 `metrologia/padroes` (1º módulo Wave A)

> Deriva do plan v2 (P1-P9 + §14 deltas). IDs `T-PAD-NNN`. Path
> `src/infrastructure/metrologia/padroes/` (ADR-0072). Reuso explícito M4 (plan §6).
> **`/implement` segue esta ordem.** Auditores Família 5 no fim (P9 — INV-RITUAL-001).

## P1 — Domínio puro (sem Django)

| ID | Tarefa | Saída/teste |
|----|--------|-------------|
| T-PAD-001 | `enums.py`: EstadoPadrao (+`RECAL_RETORNADO_PENDENTE_APROVACAO` — C-4), VinculacaoCadeia, ClassePadrao (E1/E2/F1/F2/M1/M2/M3/OUTRA), SubtipoPadrao (PRINCIPAL/AUXILIAR_*), StatusRecal, ResultadoVI, ResultadoPT, RegraWesternElectric, DecisaoRTCarta | testes enum + propriedades terminal/aceita_uso |
| T-PAD-002 | `entities.py`: `PadraoMetrologicoSnapshot` (+ `revision`, vigência ADR-0030, soft-delete B, `subtipo`, `criterio_intervalo` C-9, `rastreabilidade_origem_revogada` C-5) + filhas (RecalExterno, VI, IntercomparacaoPT, **AnaliseCartaControle** ADR-0070, **VinculoAuxiliar** C-8) | frozen dataclasses + testes |
| T-PAD-003 | reuso VOs `src/domain/metrologia/value_objects.py` (Grandeza/FaixaMedicao/IncertezaExpandida) — NÃO recriar | teste import |
| T-PAD-004 | `shewhart.py` puro Decimal: LC/UCL/LCL/σ + regras WE (1: 1 fora ±3σ; 2: 2-de-3 ±2σ **mesmo lado**; 3: 4-de-5 ±1σ **mesmo lado**; 4: 8 run; **5 TENDÊNCIA: 7 monotônicos** C-3) + `versao_motor_shewhart` | testes por regra + falso-positivo "lados opostos" + tendência |
| T-PAD-005 | `valor_convencional.py` puro: 2 implementações independentes do MESMO mensurando (ADR-0071) + Welch-Satterthwaite/t-Student quando ν_eff<30 (reuso `gum_classico.py`) | teste convergência + divergência=bug |
| T-PAD-006 | `repository.py` Protocols (Padrao/Recal/VI/PT/AnaliseCarta/VinculoAuxiliar) | runtime_checkable + Fake no teste |
| T-PAD-007 | máquina de estados + invariantes puras INV-PAD-001..010 (transições válidas; bloqueios) | testes de transição |

## P2 — Schema + migrations + RLS + WORM (`migrations/0001_initial.py`)

| ID | Tarefa | Nota |
|----|--------|------|
| T-PAD-010 | `padrao_metrologico` + UNIQUE `(tenant_id, numero_serie)` + RLS pattern v2 + `revision` + vigência + soft-delete B | INV-PAD-001 |
| T-PAD-011 | `recal_externo_padrao` + RLS + WORM pós-`retornado_em` | |
| T-PAD-012 | `verificacao_intermediaria` + `intercomparacao_pt` + RLS + WORM | |
| T-PAD-013 | `analise_carta_controle` (ADR-0070) + RLS + WORM trigger | INV-PAD-010 |
| T-PAD-014 | `vinculo_auxiliar` (C-8) N:N temporal + grandeza de influência + RLS | ADR-0030 |
| T-PAD-015 | **DECISÃO C-10:** incertezas como read-model do último recal retornado (trigger bloqueia UPDATE direto) **OU** GUC `app.padrao_recal_em_curso` no RESET do pool (`connection.py`) + SET LOCAL. Avaliar complexidade migration | INV-PAD-006 |
| T-PAD-016 | trigger `padrao_block_delete` (INV-SOFT-002) + grants app_user/app_migrator | |

## P3 — Use cases (`src/application/metrologia/padroes/`)

| ID | Tarefa |
|----|--------|
| T-PAD-020 | `cadastrar_padrao` (perfil A p/ RBC — `tenant_perfil_e`; INV-PAD-002 incerteza+valor) |
| T-PAD-021 | `registrar_recal_envio` → EM_RECAL_EXTERNO |
| T-PAD-022 | `registrar_recal_retorno` → **RECAL_RETORNADO_PENDENTE_APROVACAO** (C-4) |
| T-PAD-023 | `aprovar_recal_rt` (análise crítica RT) → EM_USO (libera uso) |
| T-PAD-024 | `registrar_verificacao_intermediaria` (+ dispara `AnaliseCartaControle` se WE viola/alerta — ADR-0070) |
| T-PAD-025 | `registrar_intercomparacao_inicio` / `_resultado` (perfil A) |
| T-PAD-026 | `registrar_analise_carta_controle` (decisão RT — ADR-0070) |
| T-PAD-027 | `calcular_valor_convencional` (2 implementações — ADR-0071) |
| T-PAD-028 | `baixar_padrao` / `sucatar` (A3 RT ADR-0022 v2/0068; bloqueia se cal em curso) |
| T-PAD-029 | `revogar_rastreabilidade_origem` (evento externo — C-5 FURO-4) |

## P4 — Porta M4 + GATE-PAD-PORTA-M4 (C-6 — fail-closed)

| ID | Tarefa |
|----|--------|
| T-PAD-030 | `query_service.py` funções de módulo (estilo `certificados/query_service.py`): `buscar_disponivel_para_calibracao`, `snapshot_para_uso` (PadraoUsadoSnapshot + leitura ambiental auxiliares C-8), `padrao_bloqueado_para_uso` (**fail-closed** — todos os bloqueios C-4/C-5/C-16 + saúde) |
| T-PAD-031 | **GATE-PAD-PORTA-M4:** M4 chama `padrao_bloqueado_para_uso` antes de gravar `PadraoUsado` (ADIÇÃO; faixa/grandeza adequação fica no M4 — C-15 delegação explícita) |
| T-PAD-032 | testes NOVOS M4: rejeita padrão vencido/VI-reprovada/PT-rejeitado/carta-violada/recal-pendente/origem-revogada/cross-tenant + **suíte M4 chave 629 reverde** |

## P5 — REST `PadraoViewSet` (T-CAL-130) + serializers + urls

| ID | Tarefa |
|----|--------|
| T-PAD-040 | serializers DRF (validação payload; sem PII em localizacao/cert) |
| T-PAD-041 | `PadraoViewSet` (cadastrar + recal-envio/retorno/aprovar + VI + PT + baixar/sucatar + carta-controle) + ACTION_MAP authz + paginação F-C3 herdada |
| T-PAD-042 | `urls.py` + plug em `config/urls.py` raiz (evitar órfã — lição T-CAL-124) |

## P6 — Jobs procrastinate

| ID | Tarefa |
|----|--------|
| T-PAD-050 | alerta recal vencendo (P2) / VI pendente por classe (P2) / recal pendente retorno >90d (P2) / recal retornado pendente aprovação RT >Nd (P2) |

## P7 — INVs em REGRAS + hooks ✅ COMPLETO (2026-05-29)

| ID | Tarefa | Status |
|----|--------|--------|
| T-PAD-060 | cravar INV-PAD-001..010 em REGRAS-INEGOCIAVEIS.md (incl. INV-PAD-009 redefinida ADR-0071 + INV-PAD-010 ADR-0070) | ✅ INV-PAD-001..006 reconciliados (002 GAP CHECK fechado migration 0006; 003/004/006 nomes corrigidos) + 007..010 cravados. Classes `TestINV_PAD_001..010` (TST-004) em `tests/regressao/test_inv_pad_classes_nomeadas.py` (19 testes) |
| T-PAD-061 | hooks: `padrao-incertezas-so-via-recal` (INV-PAD-006), `padrao-auxiliar-em-controle` (INV-PAD-007), `shewhart-perfil-A` (INV-PAD-008), `analise-carta-worm` (INV-PAD-010) + casos no `_test-runner` | ✅ 4 hooks criados + registrados em settings.json + 37 casos no `_test-runner` (450/450 verdes). **Causa-raiz extra:** INV-PAD-007 runtime IMPLEMENTADO na porta `_bloqueado_por_auxiliar` (não estava — auxiliar só era lido p/ grandeza); INV-PAD-002 CHECK `jsonb_array_length>0` (migration 0006) |

## P8 — Emendas docs + reconciliação + drill ✅ COMPLETO (2026-05-29)

| ID | Tarefa | Status |
|----|--------|--------|
| T-PAD-070 | emendar PRD: AC-PAD-008-2 (regras WE + tendência), US-PAD-009 (2 implementações), AC-PAD-007-4 (intervalos próprios) — refletir ADR-0070/0071 | ✅ 3 ACs emendados + AC-PAD-008-2b (alerta/trend WORM) + AC-PAD-007-5 (INV-PAD-007 runtime) + AC-PAD-009-3 (Welch-Satterthwaite) + coerência (lista ADRs 0070/0071/0072 + INV-PAD-010, métrica, glossário Shewhart híbrido) |
| T-PAD-071 | matriz retenção: linha "Executor/responsável de evento de padrão" (5a quente/25a evidência) + PDF cert externo cifrado (C-13/C-14) + drill análogo DRILL-RET-07 | ✅ 2 linhas (nome desnormalizado C-13 + PDF cert externo C-13/C-14 standalone) + DRILL-RET-PAD-01 (não-duplicando linhas 80-83 já existentes) |
| T-PAD-072 | drill `validar_m5_padroes` (estrutural) + **GATE-PAD-DRILL-LOCAL** (PG real: UNIQUE, RLS cross-tenant, triggers WORM/incertezas, perfil A bloqueia RBC, **teste concorrência GUC/pool** se C-10 manter GUC) | ✅ drill estrutural 43/43 PASS (6 tabelas + RLS ENABLE/FORCE + 4 policies + UNIQUE + 6 triggers + 3 CHECK jsonb + grants + GUC reset + índices). GATE-PAD-DRILL-LOCAL coberto por test_inv_pad_p2_schema_triggers + test_inv_pad_classes_nomeadas; teste concorrência GUC/pool dedicado fica pré-1º-tenant |
| T-PAD-073 | reconciliação spec↔código (matriz) | ✅ `docs/faseamento/M5-padroes/matriz-reconciliacao.md` (US↔AC↔INV↔ADR↔hook↔código + INV↔teste + GATEs + pendências P9) |

## P9 — Ritual auditores

| ID | Tarefa |
|----|--------|
| T-PAD-080 | 10 auditores Família 5 (INV-RITUAL-001: MÉDIO+ bloqueia). Especial: seguranca (porta fail-closed + RLS), llm-correctness (2 implementações batem docstring), produto (AC binários), qualidade (INV testados) |

## GATEs do módulo

GATE-PAD-PORTA-M4 (T-PAD-031/032) · GATE-PAD-DRILL-LOCAL (T-PAD-072) ·
GATE-PAD-SHEWHART-RBC (revisão humana credenciada pré-tenant-A — diferido) ·
GATE-CAL-CMC/PROC-PREDICATE (destravam com `escopos-cmc`+`procedimentos` — próximos módulos).

## Pendências externas (diferidas — memória `project_sem_contratacoes_externas_ate_producao`)

Parecer RBC credenciado do OQ motor incerteza+Shewhart · DPA PII-terceiro OAB ·
E&O ampliada SUSEP (ADR-0028) — todas pré-produção, NÃO agora.

## Próximo passo

`/implement` começando por **P1 (domínio puro)**. Reuso M4 (plan §6). Commits
atômicos por task/grupo. Verificar (`--no-cov --reuse-db`) antes de afirmar
(memória `feedback_test_db_nao_dropar_create_db`).
