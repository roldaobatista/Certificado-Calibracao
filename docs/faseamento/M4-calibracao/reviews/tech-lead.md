---
owner: tech-lead-saas-regulado
revisado_em: 2026-05-25
status: stable
tipo: review-p2-tech-lead
marco: Wave A Marco 4 — metrologia/calibracao
fase-ritual: P2
relacionados:
  - docs/faseamento/M4-calibracao/spec.md
  - docs/faseamento/M3-os/reviews/tech-lead.md
  - docs/faseamento/auditorias/PRE-M4-CALIBRACAO-saneamento.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0024-regra-de-decisao-iso-17025.md
  - docs/adr/0025-validacao-software-iso-17025.md
  - docs/adr/0026-segunda-conferencia-independencia.md
  - docs/adr/0040-padrao-metrologico-entidade-separada.md
  - docs/adr/0056-numeracao-os-buracos-aceitos.md
  - docs/adr/0063-rt-competencia-grandeza-diferida-marco4.md
  - docs/adr/0064-rotacao-chave-hmac-retencao-metrologica-25a.md
---

# Tech Lead Review — M4 metrologia/calibracao (P2 do ritual Spec Kit)

**Arquivo revisado:** `docs/faseamento/M4-calibracao/spec.md` (677 linhas, status `draft`)
**Revisor:** `tech-lead-saas-regulado` (subagente)
**Data:** 2026-05-25

## Sumário executivo

A spec é **densa, ambiciosa e ancorada em 14 ADRs estruturais já aceitas** (0022/0024/0025/0026/0040/0063/0064). Aplicou conscientemente G1..G10 do M3 OS no §10 — visível inclusive nos R-M4-11..R-M4-17, que **mapeiam diretamente as fontes de falha do M3**. Pontos fortes evidentes: tabela §3.1 entidade × padrão soft-delete × imutabilidade (molde M3 evoluído); §4 máquina de estados explícita com 12 estados; §8 matriz de riscos com 17 itens; §10 explicitando aplicação das 10 lições do M3.

**Mas a spec repete 4 dos 6 erros do M3 OS em P2** (concorrência sub-especificada, performance ausente, watchdog/consumer cross-módulo sem contrato real, e — pior — afirma "aplicar G6 (predicates INVOCADOS)" sem provar AC × invocação). E adiciona **3 gaps novos próprios do domínio metrológico**: motor de cálculo é vapor (não existe `src/domain/metrologia/calibracao/motor_calculo/`), `AtividadeDaOS.grandeza` que o ADR-0063 promete plugar não foi adicionado no model M3 (grep zero), e o consumer `Acreditacao.Suspensa` aponta pra um módulo `licencas-acreditacoes` que tem PRD mas **nenhum produtor real do evento**.

| Severidade | Quantidade |
|---|---|
| BLOQUEANTE (impede passar P2 → P3) | 4 |
| MÉDIO (INV-RITUAL-001 — bloqueia fechamento; pode detalhar em plan.md/tasks.md) | 5 |
| ALTO Wave A (vira GATE-CAL-*) | 2 |
| ACEITE com observação | (resto) |

**Veredicto:** **AJUSTAR antes de aprovar P2.** 4 bloqueantes exigem alteração da spec.md ou ADR companion antes da matriz reconciliação. 5 médios podem ser detalhados em plan.md desde que rastreados como T-CAL-* explícitos com owner + critério binário. 2 altos viram GATE Wave A.

---

## Achados

### P-CAL-T1 — BLOQUEANTE — Concorrência em `registrar_leitura` e snapshot de padrão: spec não define mecanismo de serialização

**Evidência:**
- spec.md §3.2 `Leitura`: nenhuma constraint UNIQUE em `(tenant_id, calibracao_id, ponto_calibracao, numero_repeticao)`. Só há UNIQUE em `(tenant_id, calibracao_id, client_event_id)` "quando NOT NULL" — bypass total pra leitura manual (`origem=MANUAL` permite `client_event_id NULL`).
- spec.md §3.2 `PadraoUsado`: "INSERT bloqueado após `em_revisao_1` via trigger" — só. Dois INSERT concorrentes pré-revisão no mesmo `padrao_id` da mesma `calibracao_id`: nada impede.
- spec.md §4: transição `configurada → em_execucao` por "1ª leitura registrada" — duas requisições paralelas chegando como 1ª leitura: cada uma vê `status='configurada'` e cada uma faz `UPDATE status='em_execucao'`. Ambas commitam. Não tem `FOR UPDATE`, advisory lock, nem version column.
- grep confirma: `pg_advisory|FOR UPDATE|UNIQUE INDEX|partial index` retorna **zero matches na spec.md** inteira.

**Análise:** isso é exatamente o P-OS-T1 do M3 (que virou ADR-0041 + INV-OS-CONC-001 + hook `migration-concorrencia-os-check`). A spec M4 reconhece G1..G10 mas ESQUECEU de aplicar a lição equivalente de concorrência. Em produção com 3 metrologistas concorrentes no mesmo lab usando o mesmo dispositivo serial multiplexado, duas leituras com `ponto=10kg, repeticao=3` viram duas linhas legítimas na tabela. Cálculo de incerteza puxa N=4 quando deveria ser N=3 → `u_combinada` errada → certificado com incerteza errada → cadeia de rastreabilidade ISO 17025 cl. 7.5 **rasgada**.

**Decisão recomendada:** spec.md §3.2 ganha **3 constraints obrigatórias** antes de P3:

```sql
-- 1. Leitura: idempotência forte mesmo com client_event_id NULL
CREATE UNIQUE INDEX idx_leitura_unica ON leitura (
  tenant_id, calibracao_id, ponto_calibracao, numero_repeticao
);

-- 2. PadraoUsado: evita duplicação cross-snapshot
CREATE UNIQUE INDEX idx_padrao_usado_unico ON padrao_usado (
  tenant_id, calibracao_id, padrao_id
) WHERE snapshot_lock = false;

-- 3. Calibracao: optimistic locking via revision column
ALTER TABLE calibracao ADD COLUMN revision INTEGER NOT NULL DEFAULT 0;
-- UPDATE ... WHERE revision = :expected_revision RETURNING revision+1;
```

Criar **ADR-0065 "Concorrência em calibração metrológica"** companion (paralelo a ADR-0041) com matriz:

| Operação | Mecanismo |
|---|---|
| `registrar_leitura` | UNIQUE composto (ponto+repeticao) → 412 `LeituraDuplicada` |
| `selecionar_padrao` | UNIQUE parcial `WHERE snapshot_lock=false` + INSERT → trigger snapshot_lock no transição em_revisao_1 |
| `aprovar_revisao` / `aprovar_2a_conferencia` | optimistic lock via `revision` column → 409 `ConflitoVersao` |
| transição estado-máquina | `UPDATE calibracao SET status=:novo WHERE id=:id AND status=:esperado RETURNING id` (CAS) |

Adicionar INV-CAL-CONC-001..004 em REGRAS-INEGOCIAVEIS no P3. Criar hook `migration-concorrencia-calibracao-check.sh` (paralelo a `migration-concorrencia-os-check.sh`).

> **Limite de honestidade:** UNIQUE composto e CAS resolvem o caso comum, mas pra `OrcamentoIncerteza.calcular()` (que lê todas as leituras + componentes) ainda há race entre "duas thread chamando calcular_incerteza" — uma escreve, outra sobrescreve. Recomendo serialização por `calibracao_id` via `pg_advisory_xact_lock(hashtext(tenant_id::text || calibracao_id::text))` dentro de `calcular_incerteza`. Não tenho cicatriz de produção pra provar — drill com 4 workers procrastinate em P4 obrigatório.

---

### P-CAL-T2 — BLOQUEANTE — Motor de cálculo + replay determinístico + 2º caminho são VAPOR: spec promete em §3.2 mas grep mostra zero código existente

**Evidência:**
- spec.md §3.2 `OrcamentoIncerteza.replay_determinismo_hash CHAR(80) NOT NULL` + `versao_motor_calculo VARCHAR(50) NOT NULL` + `segundo_caminho_calculo_valor` + `segundo_caminho_calculo_divergencia_pct NUMERIC(5,3) NULL`.
- spec.md §3.2: "alerta P3 se > 0.1%; bloqueia se > 1%" — quem dispara? Onde está o código?
- spec.md §8 R-M4-01 cita "replay determinístico em CI + 2º caminho de cálculo" — sem caminho de arquivo.
- Grep `VersaoMotorCalculo|replay_determinismo|segundo_caminho|motor_calculo` em **toda a árvore `src/`**: **zero matches**. Só docs.
- Spec não diz: qual algoritmo é o 1º caminho? Qual é o 2º? Lib externa (e.g. `metas-uncertainty`) ou implementação própria? Como CI roda o replay (fixture de inputs + hash esperado em arquivo versionado)?

**Análise:** isso é o equivalente metrológico do `sanitizar_payload_audit` que passou em PASS dos 3 auditores e quebrou em produção (memória `project_flake_visao360`). ADR-0025 está aceita mas inexistente em código; a spec do M4 fala como se existisse. Sob ISO 17025 cl. 7.11.3, um certificado emitido **sem replay reproduzível** é não-conforme — auditor CGCRE pede pra recalcular um certificado de 2026 em 2028 com a mesma versão; se não der o mesmo número, não-conformidade crítica.

Pior: a spec não decide se o "2º caminho" é (a) **dois algoritmos diferentes implementados** (e.g. GUM clássico + Monte Carlo), (b) **mesma implementação rodada com tipos diferentes** (Decimal vs float), (c) **lib externa de referência** comparada com a interna. Cada uma tem custo e semântica diferentes.

**Decisão recomendada:** ANTES de P3, spec.md §3 ganha **§3.3 "Motor de cálculo — contrato"** definindo:

1. **Algoritmo 1º caminho:** GUM clássico (NIT-DICLA-030 rev. 15) — implementação Python pura em `src/domain/metrologia/calibracao/motor_calculo/gum_classico.py`. Decimal (não float).
2. **Algoritmo 2º caminho:** Monte Carlo (BIPM JCGM 101) — `src/domain/metrologia/calibracao/motor_calculo/monte_carlo.py`. NumPy + np.random com seed cravado em `Calibracao.id` (replay determinístico).
3. **`VersaoMotorCalculo` VO:** estrutura `{semver, commit_hash, algoritmo_id IN ('GUM_CLASSICO_v1', 'MONTE_CARLO_v1'), janela_vigencia}`.
4. **`replay_determinismo_hash`:** HMAC dos inputs ordenados canônicamente (JSON com `sort_keys=True`) + dos outputs (`u_combinada`, `U_expandida`, `k`, `grau_liberdade`) — separar inputs de outputs **explicitamente** pra que regressão de cálculo (mudança de output com mesmo input) seja detectada em CI.
5. **CI replay:** `tests/replay_metrologico/` com 30+ fixtures (`fixture_<grandeza>_<faixa>.json`) contendo `inputs` + `outputs_esperados_v<NN>`. Hook `metrology-replay-fixtures-versionadas.sh` bloqueia mudança em `outputs_esperados_*` sem aceite explícito.
6. **Alerta divergência:** quem calcula? Recomendo: `OrcamentoIncerteza.calcular()` dispara ambos e popula `segundo_caminho_calculo_divergencia_pct`; se > 1% lança `DivergenciaCalculoInaceitavel` → estado calibração vai pra `em_execucao` + `NaoConformidade` automática (CAPA aberto).

Criar T-CAL-MOTOR-1..10 no tasks.md. Sem essa definição, P4 vai inventar implementação e P5 reprova auditor-llm-correctness em "stub que mente".

---

### P-CAL-T3 — BLOQUEANTE — Hash-chain `EventoDeCalibracao`: spec não define ordem em insert concorrente

**Evidência:**
- spec.md §3.2 `EventoDeCalibracao.evento_anterior_hash CHAR(80) NULL` + `evento_hash CHAR(80) NOT NULL`.
- spec.md §3.2: "HMAC do payload + evento_anterior_hash + tenant_id + occurred_at".
- Nenhuma menção a: **qual é o "evento anterior" quando duas transações commitam em paralelo na mesma calibracao_id?**
- Grep mostra que o M3 OS resolveu hash-chain authz com `src/infrastructure/multitenant/migrations/0004_audit_hash_chain_por_tenant.py` — chain por tenant_id (uma cadeia global por tenant). M4 propõe chain por calibracao_id? Por tenant_id? Spec é ambígua.

**Análise:** se duas transações T1 (registra leitura) e T2 (corrige leitura anterior) inserem `EventoDeCalibracao` simultâneas, ambas leem o mesmo `evento_anterior_hash` (último commit visível em snapshot READ COMMITTED). Ambas commitam com mesmo `evento_anterior_hash` → cadeia **garfada**. Auditor CGCRE rastreando "qual foi o evento exato antes de RevisaoAprovada?" não consegue ordenar deterministicamente. Não é só estética — fere INV-CAL-AUD-001 "hash-chain" prometido.

**Decisão recomendada:** spec.md §3.2 cravar EXPLICITAMENTE:

- **Chain por (tenant_id, calibracao_id)** — não chain global.
- **Serialização via `SELECT pg_advisory_xact_lock(hashtext(tenant_id::text || calibracao_id::text))`** no início da função `append_evento_calibracao()` — garante ordem total dentro da calibração.
- **Constraint `UNIQUE(tenant_id, calibracao_id, sequencia_local)`** com `sequencia_local BIGINT GENERATED BY ALWAYS AS IDENTITY` por calibracao — auditor pode ler `sequencia_local` 1, 2, 3, ... sem ambiguidade.
- **Drill `validar_hash_chain_calibracao`** que insere 100 eventos concorrentes em 4 workers e valida cadeia inteira recomputada bate.

Adicionar INV-CAL-AUD-002 "hash-chain por calibracao_id serializado via advisory lock". Sem isso o INV-CAL-AUD-001 é teatro.

---

### P-CAL-T4 — BLOQUEANTE — `AtividadeDaOS.grandeza` que ADR-0063 promete PLUGAR não existe em M3; spec M4 §10 G6 mente

**Evidência:**
- spec.md §10 G6: "`rt_competencia_cobre` ATIVADO via ADR-0063 quando M4 P3 setar `AtividadeDaOS.grandeza`."
- spec.md §9 GATE-OS-GRANDEZA-EM-ATIVIDADE: "M4 P3 PLUGA `AtividadeDaOS.grandeza` via migration".
- Grep em `src/infrastructure/ordens_servico/models.py` por "grandeza": **zero matches**. O model `AtividadeDaOS` do M3 NÃO tem o campo.
- Grep em `src/infrastructure/ordens_servico/predicates_os.py`: `rt_competencia_cobre` existe como predicate mas o argumento `grandeza` recebe valor default `""` (fail-open, conforme ADR-0063 — correto).

**Análise:** este é **exatamente o PROD-M3-02 que o M3 OS levou 2 passadas pra consertar** (consta no §5 do dossiê pré-M4). A spec M4 §10 afirma que G6 está aplicado ("Auditor-produto rastreia AC × invocação"), mas o que ela está prometendo é uma **migration retrofit no model M3** dentro do escopo M4. Isso é **mudança cross-marco** que precisa:

1. Migration em `src/infrastructure/ordens_servico/migrations/` (M3) — não em M4.
2. Backfill estratégia: atividades existentes em produção têm `grandeza=NULL` ou `grandeza=""`? Qual o default seguro?
3. Lugar onde a grandeza é CAPTURADA — `iniciar_atividade(tipo=calibracao, ...)` recebe grandeza de onde? Do `Calibracao.ConfiguracaoCalibracao.grandeza`? Mas configuracao só é criada DEPOIS de iniciar_atividade!

Existe inversão temporal não-resolvida: M3 cria `AtividadeDaOS(tipo=calibracao)` ANTES de existir `Calibracao` (consumer cria Calibração em resposta a `Atividade.Iniciada`). Logo no momento de `iniciar_atividade`, ninguém ainda escolheu a grandeza. Predicate `rt_competencia_cobre` na hora de iniciar continua fail-open eternamente.

**Decisão recomendada:** revisar ADR-0063 + spec.md §10 G6 ANTES de P3. Dois caminhos:

**Opção A (preferível):** `AtividadeDaOS.grandeza` é populada lazy quando `ConfiguracaoCalibracao` é cravada. Predicate `rt_competencia_cobre` é invocado em **3 pontos**, não no `iniciar_atividade`:
- `configurar_calibracao` (US-CAL-002) — primeira chance de saber a grandeza.
- `aprovar_revisao` (US-CAL-007) — RT 1ª conferência.
- `aprovar_2a_conferencia` (US-CAL-008) — RT 2ª.

Em `iniciar_atividade(tipo=calibracao)` continua fail-open com `grandeza=""` (documentado como **proposital, não débito**).

**Opção B:** OS exige grandeza obrigatória em `criar_os` (análise crítica cl. 7.1). Requer mudança no Marco 3 OS retroativa + retrofit dados existentes. Mais custoso.

Cravar a opção escolhida + criar T-CAL-RT-COMP-1..5 (migration M3 + backfill + invocação nos 3 use cases + teste regressão + drill `validar_rt_competencia_bloqueia_grandeza_sem_competencia.py`). Sem isso, spec mente igual ao M3 — vai voltar em P5.

---

### P-CAL-T5 — MÉDIO (INV-RITUAL-001) — Performance ausente: visão 360 calibração + painel orçamento incerteza sem budget p95

**Evidência:**
- spec.md não tem seção dedicada a performance budgets nem queries N+1.
- spec.md §3.2 lista entidades com 1:N pesado: `Calibracao` → N×Leitura (40-200) + N×PadraoUsado + 1×OrcamentoIncerteza → N×ComponenteIncerteza (5-12) + N×OrcamentoPorPonto (5-15) + N×EventoDeCalibracao (50-100 por calibração) + N×NaoConformidade.
- Visão 360 da calibração (US-CAL-009 "histórico por instrumento") carrega N calibrações × tudo isso. Sem prefetches isso é apocalipse de queries.
- Grep `performance|p95|N\+1|select_related|prefetch` retorna **zero matches** na spec inteira.

**Análise:** mesma pegadinha do P-OS-T4 do M3 que virou ALTO drift. Tela "painel-orcamento-incerteza" §13 vai mostrar 5-15 pontos × 4-8 componentes = 20-120 linhas + lookup de fonte default padrão. Sem `prefetch_related('componenteincerteza_set', 'orcamentoporponto_set')` + `select_related('calibracao__configuracao')` vira 100+ queries.

**Decisão recomendada:** plan.md (P3) cria seção "§ Performance & Queries calibração" com:
- p95 budget por endpoint: visão-360 calibração ≤400ms; painel-orcamento ≤300ms; lista calibrações ≤500ms.
- Query services em `src/application/metrologia/calibracao/queries/`:
  - `CalibracaoVisao360QueryService` — 1 query agregadora.
  - `OrcamentoIncertezaQueryService` — prefetch tudo aninhado.
  - `HistoricoCalibracaoPorInstrumentoQueryService` — paginação obrigatória + ordenação por `criada_em DESC`.
- Índices adicionais:
  - `leitura (tenant_id, calibracao_id, ponto_calibracao, numero_repeticao)`
  - `evento_de_calibracao (tenant_id, calibracao_id, occurred_at DESC)`
  - `componente_incerteza (tenant_id, orcamento_incerteza_id)`
  - `historico (tenant_id, instrumento_id, criada_em DESC) WHERE status='aprovada'`
- Teste `tests/performance/test_calibracao_n_plus_one.py` com `assertNumQueries(<=6)`.

Rastrear T-CAL-PERF-1..5. **GATE-CAL-PERF-NPLUS1 Wave A** se não couber em M4 P4.

---

### P-CAL-T6 — MÉDIO (INV-RITUAL-001) — Consumer `Acreditacao.Suspensa/Vencida`: módulo `licencas-acreditacoes` tem PRD mas nenhum produtor de evento real

**Evidência:**
- spec.md §6.2 lista `Acreditacao.Vencida` / `Acreditacao.Suspensa` como consumidos pelo M4.
- Grep mostra: existe `docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md` mas grep em `src/` por "Acreditacao.Suspensa|Acreditacao.Vencida" → zero matches em produtores. Só consumer stub em `src/infrastructure/ordens_servico/consumers/acreditacao.py` (M3 STUB).
- Spec não diz se M4 recebe esse evento via STUB (paralelo a G1 do dossiê) ou via produtor real. ADR-0014 (transições regulatórias) está PROPOSTA, não aceita.

**Análise:** mesmo padrão do P-OS-T6 do M3 com Tenant.Suspenso. Sem evento produzido, o consumer M4 fica vapor: "bloqueia novas calibrações `tipo_acreditacao=RBC` em tenant perfil A" — ok, mas baseado em quê? Se `tenant.perfil` muda manualmente em admin sem disparar evento, M4 não bloqueia.

**Decisão recomendada:** GATE-CAL-ACREDITACAO-CONSUMER Wave A — antes do 1º tenant pago RBC:
- ADR-0014 aceita.
- Produtor real de `Acreditacao.Suspensa` no módulo `licencas-acreditacoes` (mesmo que módulo seja Wave A operacional).
- Consumer M4 com teste regressão `test_calibracao_rbc_bloqueada_acreditacao_suspensa.py`.

M4 entrega placeholder "fail-closed" (bloqueia TODA calibração RBC enquanto consumer não existir) — defensivo. Adicionar como GATE no §9. Status M4 fechado: aceita STUB documentado conforme G1 do dossiê.

---

### P-CAL-T7 — MÉDIO (INV-RITUAL-001) — Idempotência POSTs: spec §10 G3 lista 18 endpoints mas não crava `ACTION_IDEMPOTENT` map

**Evidência:**
- spec.md §10 G3 lista os 18 POSTs com `IdempotencyMixin`.
- spec.md não cita `ACTION_IDEMPOTENT` map nem chave de idempotência por action (window + qual ID compõe a chave).
- Grep mostra que M3 OS tem `IdempotencyMixin` em `src/infrastructure/bus/consumer_base.py` + hook `.claude/hooks/idempotency-key-header-check.sh` ATIVO — bom. Mas a chave por action no M3 não está cravada na spec; foi inferida em código.

**Análise:** lição P-OS-T3 (idempotência watchdog) repete forma diferente: SEM chave bem definida, replay de POST `corrigir-leitura` com mesmo Idempotency-Key mas payloads diferentes pode retornar OK (chave existe) sem aplicar a 2ª correção. Cliente legítimo perde correção.

**Decisão recomendada:** plan.md P3 cria tabela canônica:

| Endpoint | Chave idempotência | Window | TTL |
|---|---|---|---|
| `POST /calibracao/{id}/registrar-leitura` | `(tenant_id, calibracao_id, idempotency_key)` + hash do payload (ponto+repeticao+valor) | 24h | 30d |
| `POST /calibracao/{id}/corrigir-leitura` | `(tenant_id, leitura_id, idempotency_key)` | 24h | 30d |
| `POST /calibracao/{id}/aprovar-revisao` | `(tenant_id, calibracao_id, idempotency_key, revisor_id)` | 24h | 30d |
| ... | ... | ... | ... |

Adicionar INV-CAL-IDEMP-001 "Idempotency-Key obrigatória em 18 POSTs; chave inclui hash do payload pra detectar mismatch payload-key". Hook `idempotency-key-header-check` precisa ser ESTENDIDO pra checar ACTION_IDEMPOTENT no `src/infrastructure/calibracao/`.

---

### P-CAL-T8 — MÉDIO (INV-RITUAL-001) — `AnaliseImpactoNCProficiência` §3.2: spec não define janela temporal nem como descobrir "certs no período"

**Evidência:**
- spec.md §3.2 `AnaliseImpactoNCProficiência.certificados_no_periodo JSONB NOT NULL` — "array no intervalo última PT PASSED → atual".
- Spec não diz: e se nunca houve PT PASSED anterior (primeira PT da história)? Janela infinita?
- Spec não diz: certificados ficam em M5 (Marco 5). M4 está consultando algo que **ainda não existe em produção**. Como o painel `EP-painel` mostra certs afetados antes do M5 estar pronto?
- AC-CAL-014-3 referenciado mas não copiado pro spec — depende de leitura cruzada com PRD.

**Análise:** acoplamento temporal mal definido. M4 deveria emitir evento `Calibracao.EpUnacceptableImpactoCriado` com a janela calculada, e M5 (consumer) faria o lookup de certs. Mas spec coloca `certificados_no_periodo` armazenado **dentro da entidade M4** — viola separação de marcos.

**Decisão recomendada:** spec.md §3.2 reescreve `AnaliseImpactoNCProficiência`:
- Armazena `janela_inicio TIMESTAMPTZ NOT NULL` + `janela_fim TIMESTAMPTZ NOT NULL` (calculado).
- `certificados_no_periodo JSONB` vira **nullable** + preenchido em batch DEPOIS pelo M5 via consumer `Calibracao.EpUnacceptableImpactoCriado`.
- Janela: se nunca houve PT PASSED, `janela_inicio = tenant.created_at` (documentado).
- Status `RECALL_PENDENTE_M5` quando M4 emite mas M5 ainda não preencheu.

Adicionar T-CAL-EP-1..3 + 1 teste regressão.

---

### P-CAL-T9 — MÉDIO (INV-RITUAL-001) — Estado `aguardando_subcontratado → recebida_do_subcontratado → em_revisao_1`: papel do executor não fica claro

**Evidência:**
- spec.md §4: fluxo subcontratação cai em `em_revisao_1` após receber cert externo.
- spec.md §3.2 `Calibracao.executor_id UUID FK` "metrologista que registra leituras; valida `executor_id == request.user.id` em registrar_leitura" — mas no fluxo subcontratado **ninguém do tenant registra leitura** (subcontratado faz).
- `INV-CAL-FRAUDE-EXEC-001` "registrar_leitura valida `calibracao.executor_id == request.user.id`": no fluxo subcontratado, `executor_id` é quem? Subcontratado não tem user no sistema do tenant.

**Análise:** ambiguidade vai virar bug em P4. RT principal carimba o cert externo recebido mas a entidade `Calibracao` espera `executor_id` populado. Sem regra clara, P4 vai escolher "RT vira executor" — fere INV-CAL-FRAUDE-CONF-001 (`conferente_id != revisor_id`) se RT for o único que tocou.

**Decisão recomendada:** spec.md §3.2 cravar:
- `Calibracao.executor_id` é NULLABLE quando `subcontratado_id IS NOT NULL`.
- `INV-CAL-FRAUDE-EXEC-001` reescrito: "se `subcontratado_id IS NULL`, validar executor=user; se subcontratado, validar `recebedor_user_id == request.user.id` em `registrar_recebimento_subcontratado`".
- Adicionar campo `recebedor_user_id UUID NULL FK` + INV-CAL-FRAUDE-RECEB-001.
- 2ª conferência exige conferente ≠ recebedor (paralelo ao caso normal).

---

### P-CAL-T10 — ALTO Wave A (vira GATE-CAL-*) — Hook `migration-metrology-classifier.sh` declarado mas não definido: como detecta "tabela metrológica"?

**Evidência:**
- spec.md §2.3: "novo hook `migration-metrology-classifier.sh` (ADR-0025 cl. 7.11.3 + GATE-CAL-MIG-CLASSIF) — bloqueia migration que toca tabela metrológica sem categorização IQ/OQ/PQ + replay test associado".
- Grep `migration-metrology-classifier` em `.claude/hooks/`: zero matches (hook ainda não criado).
- Spec não diz: COMO o hook detecta que uma tabela é "metrológica"? Allow-list por nome (`leitura`, `orcamento_incerteza`, `padrao_usado`...)? Convention `# metrologia: classificacao=PQ` em arquivos de migration? Tag em comment SQL?

**Análise:** sem critério algorítmico, hook vira teatro de segurança. Migration que muda `leitura` sem ter o tag passa; auditor CGCRE acha "Calibracao.leituras_temp" não classificada → não-conformidade ADR-0025.

**Decisão recomendada:** GATE-CAL-MIG-CLASSIF Wave A — antes de Fase 9 M4:
- Cravar **allow-list explícita** em hook (lista de 18 tabelas metrológicas no header do hook).
- OU adotar convenção: arquivo de migration que toca tabela metrológica DEVE ter `# metrologia-classificacao: IQ|OQ|PQ` + `# replay-fixture: tests/replay_metrologico/<grandeza>.json` no topo.
- Recomendo **convenção**: mais robusto a refactor de nomes.

Adicionar T-CAL-HOOK-CLASSIF-1..3.

---

### P-CAL-T11 — ALTO Wave A (vira GATE-CAL-*) — Drill `validar_m4_calibracao`: spec §11 promete mas escopo é vago

**Evidência:**
- spec.md §11: "Drill `validar_m4_calibracao` PASS — equivalente a `validar_m3_os`. Comando de gerência que executa caminho feliz: recepcionar → configurar → ... → APROVADA".
- M3 OS `validar_m3_os` tem 20 checagens (RLS + triggers + predicates + consumers + watchdog + KMS + hooks + cobertura + auditores) conforme P-OS-T4 do tech-lead M3.
- Spec M4 não lista as checagens equivalentes.

**Decisão recomendada:** plan.md P3 cria seção "§ Drill `validar_m4_calibracao` — 25 checagens" detalhando:
1. RLS em 17 tabelas M4.
2. Triggers append-only em 8 entidades imutáveis.
3. Invocação dos 5 predicates.
4. 6 consumers idempotência.
5. Idempotency-Key em 18 POSTs.
6. Replay determinístico do motor em 30 fixtures.
7. Divergência 2º caminho dentro do limite.
8. Hash-chain `EventoDeCalibracao` sem garfo após 100 inserts concorrentes.
9. KMS rotação anual + verificação 25a (drill `validar_kms_retencao_hmac`).
10. Snapshot `PadraoUsado` lock pós em_revisao_1.
11. ... (mais 15)

Adicionar GATE-CAL-DRILL Wave A.

---

## Pontos fortes da spec (manter)

- **§10 G1..G10 explícito** — aplicação das lições M3 é demonstrável, não promessa vaga. Vai facilitar P5 do auditor-llm-correctness.
- **§3.1 tabela resumo entidade × padrão soft-delete × imutabilidade × FK PII** — molde M3 evoluído; 17 entidades cobertas.
- **§4 máquina de estados explícita** com 12 estados + transições nomeadas por use case + estado terminal `aprovada` IMUTÁVEL.
- **§6 mapa de eventos completo** — 23 publicados + 8 consumidos com payload essencial.
- **§8 matriz de riscos com 17 itens** — R-M4-11..R-M4-17 mapeiam fontes de falha M3 (G1..G10 reverso). Excelente.
- **§3.2 `RegraDecisao` + `VersaoMotorCalculo` + `HashVersionado` como VOs** — separação de domínio limpa.
- **Non-goals NG-CAL-1..15** — Constituição §5 respeitada com rigor; 15 itens proibitivos claros.

---

## Sugestões de teste adicional (não bloqueantes)

- **`tests/carga/test_concorrencia_registrar_leitura.py`** — 50 threads concorrentes mesmo `(calibracao_id, ponto, repeticao)`; deve ter 1 sucesso + 49 retornos 412 `LeituraDuplicada` (valida P-CAL-T1).
- **`tests/replay_metrologico/test_replay_30_fixtures.py`** — 30 fixtures × {GUM_CLASSICO, MONTE_CARLO}; recomputar bate até 9 casas decimais (valida P-CAL-T2).
- **`tests/regressao/test_hash_chain_calibracao_concorrente.py`** — 100 INSERTs concorrentes na mesma calibração; recompute chain bate (valida P-CAL-T3).
- **`tests/regressao/test_rt_competencia_bloqueia_grandeza_setada.py`** — atividade com `grandeza=MASSA` + RT sem competência massa → 412 (valida P-CAL-T4 opção A).
- **`tests/performance/test_orcamento_painel_n_plus_one.py`** — `assertNumQueries(<=6)` (valida P-CAL-T5).
- **`tests/regressao/test_subcontratado_executor_nullable.py`** — fluxo subcontratado sem executor (valida P-CAL-T9).

---

## Resumo decisões pendentes (Roldão + matriz P3)

| ID | Decisão | Bloqueia |
|---|---|---|
| P-CAL-T1 | Concorrência: UNIQUE composto + CAS optimistic + advisory lock em `calcular_incerteza` (ADR-0065 nova) | P3 reconciliação |
| P-CAL-T2 | Motor de cálculo: GUM clássico (1º) + Monte Carlo (2º) + 30 fixtures replay + alerta divergência em código | P3 reconciliação |
| P-CAL-T3 | Hash-chain por (tenant_id, calibracao_id) serializado via advisory lock + sequencia_local | P3 reconciliação |
| P-CAL-T4 | ADR-0063 revisada: predicate invocado nos 3 use cases pós-configuracao (NÃO em iniciar_atividade) | P3 reconciliação |
| P-CAL-T5 | Performance & queries em plan.md + 3 query services + budgets p95 + 4 índices | P4 implement |
| P-CAL-T6 | GATE-CAL-ACREDITACAO-CONSUMER Wave A + ADR-0014 aceita + fail-closed em M4 | P5 auditoria |
| P-CAL-T7 | ACTION_IDEMPOTENT map cravado em plan.md por endpoint | P4 implement |
| P-CAL-T8 | `AnaliseImpactoNCProficiência` reescrito: janela ao invés de certs_no_periodo + consumer M5 | P3 reconciliação |
| P-CAL-T9 | `executor_id` nullable em fluxo subcontratado + `recebedor_user_id` + INV-CAL-FRAUDE-RECEB-001 | P3 reconciliação |
| P-CAL-T10 | Hook `migration-metrology-classifier.sh`: convenção `# metrologia-classificacao:` cravada | P4 implement |
| P-CAL-T11 | Drill `validar_m4_calibracao` 25 checagens explícitas em plan.md | P4 implement |

---

## Limites de honestidade

- **Race em `calcular_incerteza` sob 200 calibrações/min** — recomendei advisory lock por calibracao_id, mas sob 1000 calibrações concorrentes em tenants diferentes pode dar contenção no `hashtext` (collision rate baixo mas não-zero). Não tenho cicatriz pra provar — drill cronometrado obrigatório em P4 com 4 workers procrastinate.
- **Monte Carlo determinístico com NumPy** — fixei seed em `Calibracao.id`, mas mudança de versão do NumPy pode quebrar reprodutibilidade. ISO 17025 cl. 7.11.3 não diz quanto tempo o replay precisa ser válido — se exigir 25 anos, NumPy SOZINHO não dá; precisaria reimplementar Mersenne Twister em código próprio. Não consigo bater isso sem consultor metrológico humano (ADR-0025 V2 RT vendor pode atacar).
- **Verificação KMS em 2052** — ADR-0064 promete histórico 25a no KMS Multi-Region. AWS não garante API estável 25 anos. Recomendo pentest + drill anual obrigatório + offline backup das chaves wrapped por GPG em B2 WORM, fora do KMS. Fora do meu escopo de tech-lead — escalar `corretora-seguros-saas` (risco continuidade) + advogado OAB (cláusula contrato AWS) antes do 1º tenant farma.
- **Sub-subcontratação** — NG-CAL-13 declara non-goal, mas auditor CGCRE pode interpretar cl. 6.6 diferente. Não tenho parecer OAB pra cravar — escalar `consultor-rbc-iso17025` na P2 review.

---

## Veredicto

**AJUSTAR antes de aprovar P2.**

Bloqueantes P-CAL-T1, P-CAL-T2, P-CAL-T3 e P-CAL-T4 exigem alteração da spec.md (ou ADR-0065 nova + revisão de ADR-0063) **antes da matriz reconciliação P3**. P-CAL-T5..T9 podem ser detalhados em plan.md desde que rastreados como T-CAL-* explícitos com owner + critério binário. P-CAL-T10 e T11 viram GATE-CAL-* Wave A.

Sem isso, o ritual Spec Kit (INV-RITUAL-001) será violado em P5 — auditor-llm-correctness vai pegar "motor de cálculo é stub que mente" (R-M4-11), auditor-performance vai pegar N+1 (R-M4-12 paralelo), auditor-idempotencia vai pegar `ACTION_IDEMPOTENT` ad-hoc, auditor-produto vai pegar "predicate rt_competencia_cobre não invocado de verdade" (PROD-M3-02 redux). Exatamente o tipo de drift que o ritual existe pra impedir.

A spec É forte na intenção; precisa ser firme nos contratos antes de virar tasks.md.
