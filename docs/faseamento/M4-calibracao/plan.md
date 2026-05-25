---
owner: roldao
revisado_em: 2026-05-25
proximo_review: 2026-08-25
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 4 — metrologia/calibracao
tipo: plan-ritual-spec-kit-P2
relacionados:
  - docs/faseamento/M4-calibracao/spec.md
  - docs/faseamento/M4-calibracao/reviews/tech-lead.md
  - docs/faseamento/M4-calibracao/reviews/advogado.md
  - docs/faseamento/M4-calibracao/reviews/corretora.md
  - docs/faseamento/M4-calibracao/reviews/rbc.md
  - docs/faseamento/auditorias/PRE-M4-CALIBRACAO-saneamento.md
  - docs/faseamento/M3-os/plan.md
---

# Marco 4 (metrologia/calibracao) — Plan P2 (4 reviews paralelos)

> **P2 do ritual Spec Kit (2026-05-25):** spec FORWARD criada em P1
> (`spec.md`, 676 linhas) foi revisada em PARALELO pelos 4 subagentes
> humano-substitutos: `tech-lead-saas-regulado`, `advogado-saas-regulado`,
> `corretora-seguros-saas`, `consultor-rbc-iso17025`. Esta ata
> registra as decisões absorvidas — bloqueantes viram correções na
> spec; MÉDIOs (INV-RITUAL-001) viram ACs/INVs/tarefas T-CAL; ALTOs
> ficam rastreados como GATE Wave A; ACEITES ficam como confirmação.

## Sumário dos vereditos

| Revisor | BLOQUEANTE | MÉDIO INV-RITUAL-001 | ALTO Wave A / GATE | ACEITE | Total |
|---|---|---|---|---|---|
| `tech-lead-saas-regulado` | 4 (T1, T2, T3, T4) | 5 (T5, T6, T7, T8, T9) | 2 (T10, T11) | — | 11 |
| `advogado-saas-regulado` | 0 | 6 (A1, A2, A3, A4, A5, A6) | 2 (A7, A8 — GATE Wave A) | — | 8 |
| `corretora-seguros-saas` | 0 | 4 (S6, S7, S8, S9 ajustado MÉDIO) + 5 (S1..S5 ajustado ALTO) | 5 ALTO (S1..S5) | 1 (S10 ACEITE) | 10 |
| `consultor-rbc-iso17025` | 6 (R1, R2, R3, R4, R5, R6) | 3 (R12, R13, R14) | 5 (R7, R8, R9, R10, R11) | 2 (R15, R16) | 16 |
| **Total** | **10** | **23** | **14** | **3** | **45** |

**BLOQUEANTE (corrige na spec.md antes de P3 reconciliação):** 10 itens.
**MÉDIO INV-RITUAL-001 (vira AC/INV/T-CAL em P3/P4 — bloqueia fechamento de fase):** 23 itens.
**ALTO Wave A / GATE (rastreado, não bloqueia fechamento M4 dogfooding):** 14 itens.
**ACEITE (confirmação, sem ação):** 3 itens.

**Densidade vs M3 OS:** o M3 OS produziu 27 achados em P2; o M4 produziu **45 — 67% mais**. Coerente: M4 é o coração técnico do produto, com profundidade metrológica + cascata segurável + densidade regulatória CGCRE/RBC + lacunas LGPD novas (subcontratação 6.6 + override de regra + foto cliente farma).

---

## Decisões absorvidas na spec (retrofit pré-P3)

### Bloco A — Concorrência & integridade transacional (tech-lead)

#### P-CAL-T1 — Lock pra concorrência em `registrar_leitura` + `selecionar_padrao` + transições de estado (BLOQUEANTE)

**Análise:** spec não tinha mecanismo de serialização. 3 metrologistas concorrentes no mesmo dispositivo serial multiplexado quebrariam INV-CAL-WORM-001.

**Decisão:** spec.md §3.2 ganha 3 constraints obrigatórias + cravar **ADR-0065 "Concorrência em calibração metrológica"** (paralela a ADR-0041):

```sql
CREATE UNIQUE INDEX idx_leitura_unica ON leitura
  (tenant_id, calibracao_id, ponto_calibracao, numero_repeticao);

CREATE UNIQUE INDEX idx_padrao_usado_unico ON padrao_usado
  (tenant_id, calibracao_id, padrao_id) WHERE snapshot_lock = false;

ALTER TABLE calibracao ADD COLUMN revision INTEGER NOT NULL DEFAULT 0;
-- UPDATE com CAS: WHERE revision = :expected RETURNING revision+1
```

Promover **INV-CAL-CONC-001..004** em REGRAS-INEGOCIAVEIS no P3. Criar hook `migration-concorrencia-calibracao-check.sh` no P9. `calcular_incerteza` usa `pg_advisory_xact_lock(hashtext(tenant_id::text || calibracao_id::text))`.

#### P-CAL-T2 — Motor de cálculo + replay determinístico + 2º caminho (BLOQUEANTE)

**Análise:** spec promete `replay_determinismo_hash` + `versao_motor_calculo` + alerta divergência 0.1%/bloqueio 1%, mas zero código existente. Vapor.

**Decisão:** spec.md §3 ganha **§3.3 "Motor de cálculo — contrato"**:

1. **1º caminho:** GUM clássico em `src/domain/metrologia/calibracao/motor_calculo/gum_classico.py` (Decimal, não float).
2. **2º caminho:** Monte Carlo BIPM JCGM 101 em `src/domain/metrologia/calibracao/motor_calculo/monte_carlo.py` (NumPy + seed cravado em `Calibracao.id`).
3. **VO `VersaoMotorCalculo`:** `{semver, commit_hash, algoritmo_id IN ('GUM_CLASSICO_v1', 'MONTE_CARLO_v1'), janela_vigencia}`.
4. **`replay_determinismo_hash`:** HMAC de inputs ordenados canonicamente + outputs separadamente — regressão de cálculo (mesmo input, output diferente) detectada em CI.
5. **CI replay:** `tests/replay_metrologico/` com 30 fixtures `fixture_<grandeza>_<faixa>.json`. Hook `metrology-replay-fixtures-versionadas.sh` bloqueia mudança de `outputs_esperados_*` sem aceite.
6. **Alerta divergência:** `OrcamentoIncerteza.calcular()` dispara ambos; >1% → `DivergenciaCalculoInaceitavel` → estado calibração volta `em_execucao` + NC automática (CAPA aberto).

Rastrear T-CAL-MOTOR-1..10 no tasks.md.

#### P-CAL-T3 — Hash-chain `EventoDeCalibracao` serializado por calibracao_id (BLOQUEANTE)

**Análise:** chain global por tenant não basta — 2 transações concorrentes na mesma calibração leem o mesmo `evento_anterior_hash` e cadeia garfa.

**Decisão:** spec.md §3.2 cravar:
- Chain por **(tenant_id, calibracao_id)** — não global.
- Serialização via `pg_advisory_xact_lock(hashtext(tenant_id::text || calibracao_id::text))` em `append_evento_calibracao()`.
- Constraint `UNIQUE(tenant_id, calibracao_id, sequencia_local)` + `sequencia_local BIGINT GENERATED BY ALWAYS AS IDENTITY` por calibração.
- Drill `validar_hash_chain_calibracao` — 100 eventos concorrentes em 4 workers, cadeia recomputada bate.

Promover **INV-CAL-AUD-002**.

#### P-CAL-T4 — ADR-0063 revisada: predicate `rt_competencia_cobre` invocado em 3 use cases pós-configuracao (BLOQUEANTE)

**Análise:** spec §10 G6 diz "ATIVADO via ADR-0063 quando M4 P3 setar `AtividadeDaOS.grandeza`" — mas em `iniciar_atividade(tipo=calibracao)` a grandeza AINDA não existe (configuração vem depois). Predicate fica fail-open eternamente lá.

**Decisão (Opção A — preferível):** spec.md §10 G6 + ADR-0063 corrigidos:
- `AtividadeDaOS.grandeza` é populada LAZY em `configurar_calibracao` (US-CAL-002) — não em `iniciar_atividade`.
- Predicate `rt_competencia_cobre` invocado em **3 pontos**, não no iniciar:
  - `configurar_calibracao` (US-CAL-002) — primeira chance de saber a grandeza.
  - `aprovar_revisao` (US-CAL-007) — RT 1ª.
  - `aprovar_2a_conferencia` (US-CAL-008) — RT 2ª.
- Em `iniciar_atividade(tipo=calibracao)` continua fail-open com `grandeza=""` — **documentado como proposital**, não débito.

Rastrear T-CAL-RT-COMP-1..5 (migration M3 + backfill + invocação nos 3 use cases + teste regressão + drill `validar_rt_competencia_bloqueia_grandeza_setada.py`).

---

### Bloco B — Profundidade metrológica ISO 17025 (RBC)

#### P-CAL-R1 — Zonificação ILAC G8 6 zonas + PFA + PRA (BLOQUEANTE)

**Análise:** spec tem só `APROVADO | REPROVADO | CONDICIONAL`. ILAC G8 exige 6 zonas. `BANDA_GUARDA_30` exige `pfa_calculada` documentada.

**Decisão:** spec.md §3.2 + ADR-0024 retrofit:
- `decisao ENUM('PASS', 'CONDITIONAL_PASS', 'PASS_COM_RESSALVA', 'CONDITIONAL_FAIL', 'FAIL_COM_RESSALVA', 'FAIL', 'NA')`.
- Adicionar `zona_ilac_g8 VARCHAR(20) NOT NULL`, `pfa_calculada NUMERIC(5,4) NULL`, `pra_calculada NUMERIC(5,4) NULL`.
- Promover **INV-CAL-DEC-004** (BANDA_GUARDA_30 exige PFA) + **INV-CAL-DEC-005** (zona é uma das 6).
- ADR-0024 ganha tabela ILAC G8 6 zonas + PFA + acordo cliente.

#### P-CAL-R2 — Componentes mínimos obrigatórios NIT-DICLA-030 §6.3 (BLOQUEANTE)

**Análise:** `ComponenteIncerteza` aceita qualquer `nome_componente VARCHAR(80)`. Sistema permite orçamento sem repetibilidade, sem incerteza do padrão → NC ALTO CGCRE comum.

**Decisão:** spec.md §3.2:
- Enum `tipo_origem_componente IN ('REPETIBILIDADE', 'RESOLUCAO_INSTRUMENTO', 'INCERTEZA_PADRAO_REF', 'DERIVA_PADRAO', 'CONDICOES_AMBIENTAIS', 'EXCENTRICIDADE', 'POLARIZACAO_BIAS', 'OUTRO')`.
- Promover **INV-CAL-INC-002:** transição `em_execucao → em_revisao_1` valida componentes obrigatórios por grandeza+padrão (matriz `docs/dominios/metrologia/modulos/calibracao/componentes-obrigatorios-por-grandeza.md` a criar — **REQUER CGCRE humano**).
- AC-CAL-005-4 novo.

🔴 **REQUER CGCRE humano credenciado** para validar a matriz componentes-obrigatórios por grandeza.

#### P-CAL-R3 — Acordo documentado do cliente sobre regra de decisão cl. 7.1.3 (BLOQUEANTE)

**Análise:** spec permite `regra_decisao_override_cliente=true` com snapshot mas sem proof-of-communication com cliente. CGCRE supervisão pede evidência POR CALIBRAÇÃO.

**Decisão:** spec.md §3.2 ganha nova entidade `AceiteRegraDecisao` (Padrão B imutável) + `Calibracao` ganha:
```
- regra_decisao_acordada_em TIMESTAMPTZ NOT NULL
- regra_decisao_acordada_documento_id UUID NOT NULL FK
- regra_decisao_acordada_hash CHAR(80) NOT NULL
```
Promover **INV-CAL-DEC-006** (RBC exige acordo) + AC-CAL-002-X novo.

🔴 **REQUER CGCRE + OAB humano** — texto canônico `aceite-regra-decisao-v1.0.md`.

#### P-CAL-R4 — Análise crítica de pedido em recepção AVULSA (BLOQUEANTE)

**Análise:** `RecepcaoItemCalibracao` tem `avaliacao_aptidao` mas isso é análise do ITEM (cl. 7.4), não do PEDIDO (cl. 7.1.1). Recepção AVULSA sem OS fica órfã.

**Decisão:** spec.md §3.2 `Calibracao` ganha:
```
- analise_critica_pedido_id UUID NULL FK (quando atividade_os_id NOT NULL)
- analise_critica_pedido_inline_hash CHAR(80) NULL (canonicalizado)
- analise_critica_pedido_inline_canonicalizada TEXT NULL (≥100 chars + anti-PII)
- capacidade_tecnica_confirmada_por_user_id UUID NOT NULL
CHECK ((atividade_os_id IS NOT NULL AND analise_critica_pedido_id IS NOT NULL)
       OR (atividade_os_id IS NULL AND analise_critica_pedido_inline_hash IS NOT NULL))
```
Promover **INV-CAL-ANAL-001** (paralelo INV-OS-ANAL-001) + AC-CAL-001-3 novo.

#### P-CAL-R5 — Política escrita + avaliação periódica de subcontratado cl. 6.6.2 a-f (BLOQUEANTE)

**Análise:** `LaboratorioSubcontratado` tem cadastro técnico mas zero governança (política, avaliação periódica, KPIs). CGCRE pede ao supervisor.

**Decisão:** spec.md §3.2 `LaboratorioSubcontratado` ganha:
```
- criterio_selecao_documento_id UUID NULL FK
- ultima_avaliacao_periodica_em TIMESTAMPTZ NULL
- proxima_avaliacao_periodica_em TIMESTAMPTZ NOT NULL (default vigencia_inicio + 12 months)
- score_avaliacao_atual NUMERIC(3,1) NULL
```
Criar entidade `AvaliacaoPeriodicaSubcontratado` (1:N, WORM, 4 critérios mínimos). Promover **INV-CAL-SUBC-005** (proxima_avaliacao > 12 meses atrás) + job procrastinate `verificar_avaliacoes_subcontratados_vencendo`. **GATE-CAL-SUBC-AVAL** Wave A.

🔴 **REQUER CGCRE humano** — template `criterio-selecao-subcontratado-v1.0.md`.

#### P-CAL-R6 — Decisão "continuar ou parar" + notificação cliente cl. 7.10.1 (BLOQUEANTE)

**Análise:** `NaoConformidade` cobre CAPA mas NÃO cobre: decisão parar/continuar, notificação cliente, autorização retomada. cl. 7.10.1 a-f.

**Decisão:** spec.md §3.2 `NaoConformidade` ganha:
```
- decisao_continuar_ou_parar VARCHAR(20) NOT NULL DEFAULT 'A_DEFINIR'
  CHECK IN ('PARAR_TRABALHO', 'CONTINUAR_COM_CONTROLE', 'A_DEFINIR')
- cliente_notificado_em TIMESTAMPTZ NULL
- cliente_notificado_via VARCHAR(20) NULL (EMAIL_PORTAL | A3_ASSINATURA | TERMO_PRESENCIAL)
- cliente_notificado_documento_id UUID NULL FK
- autorizacao_retomada_user_id UUID NULL
- autorizacao_retomada_em TIMESTAMPTZ NULL
```
CHECK na transição `→ ACAO_EXECUTADA` exige `decisao != 'A_DEFINIR'`. PARAR_TRABALHO exige `cliente_notificado_em NOT NULL`. Promover **INV-CAL-NC-002** + **INV-CAL-NC-003** + AC-CAL-014-5 novo + saga consumer `Calibracao.NCAberta` publica `Cliente.NotificacaoPendente`.

---

## Decisões absorvidas em plan.md/tasks.md (MÉDIO INV-RITUAL-001)

### Bloco C — Performance + idempotência + consumer (tech-lead)

#### P-CAL-T5 — Performance & queries + budgets p95 + 4 índices

**Decisão:** plan.md (esta seção) cria seção dedicada (§ Performance — abaixo) com:
- p95 budget: visão-360 calibração ≤400ms; painel-orcamento ≤300ms; lista calibrações ≤500ms.
- 3 query services em `src/application/metrologia/calibracao/queries/`.
- 4 índices adicionais.
- Teste `tests/performance/test_calibracao_n_plus_one.py` com `assertNumQueries(<=6)`.

Rastrear T-CAL-PERF-1..5.

#### P-CAL-T6 — Consumer `Acreditacao.Suspensa` fail-closed + GATE-CAL-ACREDITACAO-CONSUMER

**Decisão:** M4 entrega placeholder fail-closed (bloqueia TODA calibração RBC até consumer real existir). ADR-0014 fica como pré-requisito Wave A; GATE-CAL-ACREDITACAO-CONSUMER. Compatível com G1 do dossiê (STUB documentado).

#### P-CAL-T7 — ACTION_IDEMPOTENT map por endpoint

**Decisão:** plan.md (esta seção) cria tabela canônica de 18 endpoints com chave de idempotência por action + window + TTL. Promover **INV-CAL-IDEMP-001** (chave inclui hash do payload). Hook `idempotency-key-header-check` estendido pra `src/infrastructure/calibracao/`.

#### P-CAL-T8 — `AnaliseImpactoNCProficiência` reescrito: janela ao invés de certs_no_periodo

**Decisão:** spec.md §3.2 reescreve a entidade:
- Armazena `janela_inicio TIMESTAMPTZ NOT NULL` + `janela_fim TIMESTAMPTZ NOT NULL`.
- `certificados_no_periodo JSONB` vira **nullable** + preenchido em batch DEPOIS pelo M5 via consumer `Calibracao.EpUnacceptableImpactoCriado`.
- Janela: se nunca houve PT PASSED, `janela_inicio = tenant.created_at` (documentado).
- Status `RECALL_PENDENTE_M5` quando M4 emite mas M5 ainda não preencheu.

Rastrear T-CAL-EP-1..3.

#### P-CAL-T9 — Executor nullable em fluxo subcontratado + `recebedor_user_id`

**Decisão:** spec.md §3.2 cravar:
- `Calibracao.executor_id` NULLABLE quando `subcontratado_id NOT NULL`.
- INV-CAL-FRAUDE-EXEC-001 reescrito: condicionado a `subcontratado_id IS NULL`.
- Novo campo `recebedor_user_id UUID NULL FK` + INV-CAL-FRAUDE-RECEB-001.
- 2ª conferência exige `conferente_id != recebedor_id` paralelo a `!= revisor_id`.

### Bloco D — LGPD + canonicalização contratual (advogado)

#### P-CAL-A1 — Subcontratação: 4 lacunas cumulativas (DPA + sub-subcontratação + touch alto risco + transferência internacional)

**Decisão:** criar 3 documentos canônicos + 2 ACs novos + 1 INV novo:
- `docs/conformidade/comum/minutas/dpa-laboratorio-subcontratado-v1.0.md` (8 cláusulas mínimas).
- `docs/conformidade/comum/termos/aceite-subcontratacao-v1.0.md` (5 informações ao cliente).
- AC-CAL-017-7: touch em alto risco exige declaração canônica extra; default é A3.
- AC-CAL-017-8: `LaboratorioSubcontratado.pais != BR` exige cláusulas-padrão ANPD aprovadas.
- **INV-CAL-SUBC-005**: `dpa_versao` deve resolver para arquivo existente com status != minuta.

🔴 **REQUER OAB humana** — 3 textos canônicos + GATE-CAL-SUBC-OAB.

#### P-CAL-A2 — INV-CAL-TXT-001 estendido pra saúde + UUID cru em NaoConformidade

**Decisão:**
1. INV-CAL-TXT-001 reescrito referenciando extensão saúde de INV-OS-TXT-001 (P-OS-A3 do M3): regex endereço + sequência ≥7 dígitos + palavra-chave saúde + NFC + lowercase + quarentena 24h.
2. `NaoConformidade.responsavel_acao_user_id_hash CHAR(80) NOT NULL` adicionado. UUID cru fica em campo auxiliar 90d → job procrastinate `nc-responsavel-pseudonimizacao` zera. INV-CAL-NC-002 NOVA (lá já estava reservada).

🔴 **REQUER OAB** — lista palavra-chave saúde art. 11 LGPD + GATE-CAL-PII-SAUDE-OAB.

#### P-CAL-A3 — Override de regra de decisão pelo cliente: cláusula contratual verificada

**Decisão:** spec.md §3 ganha nova entidade `OverrideRegraDecisaoCliente` (Padrão B imutável) + AC-CAL-002-3 novo + INV-CAL-DEC-002 com hook `override-regra-decisao-contrato-check.sh` + texto canônico `clausula-override-regra-decisao-v1.0.md`.

🔴 **REQUER OAB** — texto da cláusula passa pelo controle CDC art. 25 + 51 + GATE-CAL-OVERRIDE-OAB.

#### P-CAL-A4 — Reclamação CDC art. 26 + cl. 7.9 ISO

**Decisão:** spec.md §3.2 ganha entidade `ReclamacaoCalibracao` (Padrão B imutável + estado-máquina). Adicionar **US-CAL-018** "Reclamação do cliente sobre calibração emitida" — 4 AC novos. Adicionar ao §15 Sumário pra Roldão. **GATE-CAL-RECLAMACAO-FLUXO** Wave A.

#### P-CAL-A5 — Base legal foto recepção + EXIF strip hook

**Decisão:** criar texto canônico `docs/conformidade/comum/termos/aviso-foto-recepcao-v1.0.md` (legítimo interesse + RIPD-Calibracao). AC-CAL-001-3 ganha aviso renderizado antes da captura + entidade `ConsentimentoFotoRecusado` quando recusa. Hook `foto-exif-strip-check.sh` no §2.3 (5º hook M4 P9, não 4).

🔴 **REQUER OAB** — texto + RIPD-Calibracao + GATE-CAL-FOTO-OAB.

#### P-CAL-A6 — Consentimento contato técnico cliente PJ (biometria art. 11)

**Decisão:** adicionar RAT-CAL-01 (renumerar) + entidade `ConsentimentoContatoTecnicoCliente` (paralelo INV-OS-CONSBIO-001 do M3) + INV-CAL-CONT-001 (sem consentimento → 412).

🔴 **REQUER OAB** — texto canônico do consentimento + análise se consentimento B2B é livre + GATE-CAL-CONT-OAB.

### Bloco E — Profundidade metrológica ALTOS Wave A (RBC)

#### P-CAL-R7 — Tipo A + correlação + bias + Welch-Satterthwaite + arredondamento (ALTO Wave A)

**Decisão:** spec.md §3.2 `ComponenteIncerteza` + `OrcamentoIncerteza` ganham 5 + 2 campos novos (vide review RBC). Promover **INV-CAL-INC-003** (Tipo A exige n_amostras ≥ 6 + s_x) + **INV-CAL-INC-004** (correlação cross-componente). AC-CAL-005-5..7 novos. Replay-fixtures incluem CASOS COM correlação ≠ 0 + bias conhecido.

🔴 **REQUER CGCRE humano** — fórmulas por grandeza + GATE-CAL-INC-FORMULA.

#### P-CAL-R8 — Western Electric + WARNING |z|>2 (ALTO Wave A)

**Decisão:** spec.md §3.2 `MedicaoControle` ganha `escore_z NUMERIC(5,3) NULL` + `regra_western_electric_violada VARCHAR(20) NULL`. Criar entidade `PlanoAcaoProficienciaWarning` (paralelo `AnaliseImpactoNCProficiência` para WARNING). Job procrastinate `analisar_padrao_medicoes_controle`. **GATE-CAL-EP-WARNING**.

#### P-CAL-R9 — Rastreabilidade SI: enum + cadeia documental (ALTO Wave A)

**Decisão:** spec.md §3.2 `PadraoUsado` ganha campos top-level (não dentro do JSONB):
```
- vinculacao_si_tipo VARCHAR(20) NOT NULL CHECK IN ('BIPM_DIRETO', 'INMETRO', 'RBC', 'NMI_ESTRANGEIRO', 'MRC_NIST_PTB_NPL', 'INTERNO_DECLARADO')
- vinculacao_si_referencia_id VARCHAR(80) NOT NULL
- cadeia_rastreabilidade_documento_id UUID NULL FK
```
Promover **INV-CAL-RAST-002** (RBC proíbe `INTERNO_DECLARADO`) + AC US-CAL-003 novo. **GATE-CAL-RAST-SI-ENUM**.

#### P-CAL-R10 — Snapshot competência RT no momento da revisão (ALTO Wave A)

**Decisão:** spec.md §3.2 `Calibracao` ganha:
- `snapshot_competencia_revisor_json JSONB NULL` (capturado em aprovarRevisao).
- `snapshot_competencia_conferente_json JSONB NULL` (idem em aprovar2aConferencia).

Promover **INV-CAL-RT-002** + AC-CAL-007-5 + AC-CAL-008-4 novos. **GATE-CAL-RT-SNAPSHOT**.

#### P-CAL-R11 — Backup metrológico cl. 7.11.6 (ALTO Wave A)

**Decisão:** criar `docs/operacao/runbooks/backup-metrologico.md` + entidade `EventoBackupMetrologico` (append-only WORM) + job procrastinate diário + **INV-CAL-BACKUP-001** (gap >25h dispara P1). Drill `validar_m4_calibracao` ganha checagem backup. **GATE-CAL-BACKUP-METROL** Wave A.

### Bloco F — Cláusulas seguráveis (corretora)

#### P-CAL-S1..S10 — ADR-0028 rev 3 com 8 cláusulas novas + Modalidade 8 NOVA

**Decisão:** spec.md §8 + §9.1 ganham:
- **R-M4-18** (subcontratado erro), **R-M4-19** (fraude criminal), **R-M4-20** (padrão próprio), **R-M4-21** (foto paciente farma), **R-M4-22** (consent vicioso).
- AC novo em US-CAL-008: "plataforma emite alerta P2 quando uso de exceção 2ª conferência atinge 3%/mês (1/3 do limite ADR-0026)".

ADR-0028 rev 3 (proposta — Roldão aprova em P3) ganha:
- 5 cláusulas novas em Modalidade 1 (E&O): multi-tier vicarious, sub-contracted quality, investigation defense tenant admin, fraud prevention defect, wrongful consent capture.
- 2 cláusulas novas em Modalidade 2 (Cyber): cryptographic proof integrity defect (HMAC 25a), sensitive personal data third-party (patient farma).
- 1 cláusula nova em Modalidade 7 (Accreditation Loss): governance defect exceção 2ª conferência.
- **Modalidade 8 NOVA** — Owned Metrological Standards Property Coverage (padrão próprio R$ 50k-500k).

**9 GATEs novos:** GATE-SEG-EO-CAL-1, GATE-SEG-SUBC-1, GATE-SEG-CYBER-HMAC-1, GATE-SEG-EO-INVEST-1, GATE-SEG-EO-FRAUDE-1, GATE-SEG-BPT-PADROES-1, GATE-SEG-CYBER-PATIENT-1, GATE-SEG-EO-CONSENT-1, GATE-SEG-ACR-EXCECAO-1.

🔴 **REQUER CORRETORA SUSEP HUMANA** — todos os wordings + cotação. Marsh/AON/Howden (`multi-tier vicarious` + `cryptographic proof integrity defect` provavelmente Lloyd's).

### Bloco G — GATEs ALTO Wave A não-segurabilidade

#### P-CAL-T10 — Hook `migration-metrology-classifier.sh` (ALTO Wave A → GATE-CAL-MIG-CLASSIF)

**Decisão:** convenção `# metrologia-classificacao: IQ|OQ|PQ` + `# replay-fixture: tests/replay_metrologico/<grandeza>.json` no topo de migration que toca tabela metrológica. Mais robusto que allow-list por nome.

#### P-CAL-T11 — Drill `validar_m4_calibracao` 25 checagens explícitas (ALTO Wave A → GATE-CAL-DRILL)

**Decisão:** plan.md (esta seção) cria seção "§ Drill `validar_m4_calibracao` — 25 checagens" detalhando RLS + triggers + predicates + consumers + idempotency + replay + divergência + hash-chain + KMS + snapshot + backup + etc.

#### P-CAL-A7 — `foto-exif-strip-check.sh` (GATE Wave A)

**Decisão:** já endereçado em P-CAL-A5. Hook adicionado a §2.3 como 5º hook M4 P9.

#### P-CAL-A8 — INV-CAL-ANON-001 paralelo INV-OS-ANON-001 (GATE Wave A)

**Decisão:** promover **INV-CAL-ANON-001** "Cliente com Calibracao em status NOT IN ('aprovada','rejeitada','cancelada') bloqueia anonimização Zona A/B". Consumer M1/M4 cross-check em `Cliente.AnonimizacaoSolicitada`. **GATE-CAL-ANON-CONCORRENCIA**.

### Bloco H — MÉDIOS finais (RBC)

#### P-CAL-R12 — Wording mínimo certificado subcontratado ILAC G18 (MÉDIO)

**Decisão:** criar `docs/conformidade/comum/textos/declaracao-subcontratacao-certificado-v1.0.md` (REQUER OAB + RBC). Promover **INV-CAL-SUBC-006** (snapshot Marco 5 inclui texto canônico).

#### P-CAL-R13 — Condições ambientais com critério binário (MÉDIO)

**Decisão:** spec.md §3.2 detalhar `CondicoesAmbientais` (temperatura/umidade/pressão lidas + alvo + tolerancia + `dentro_tolerancia BOOLEAN GENERATED`). AC-CAL-004-8 novo (bloqueia leitura fora de tolerância com override + audit + P2). **INV-CAL-AMB-001**.

#### P-CAL-R14 — Cascata `Padrao.Baixado` (MÉDIO)

**Decisão:** consumer em §6.2: `Padrao.Baixado` marca calibrações em status `em_execucao` que selecionaram o padrão como `nao_conforme` (CAPA aberta). Calibrações em `em_revisao_1+` mantêm (snapshot já capturado). **INV-CAL-PAD-CASCADE-001**.

---

## § Performance — Budgets + Query Services (P-CAL-T5)

### p95 budgets por endpoint

| Endpoint | p95 budget | Mecanismo |
|---|---|---|
| GET `/calibracao/{id}/visao-360` | ≤400ms | `CalibracaoVisao360QueryService` — 1 query agregadora |
| GET `/calibracao/{id}/painel-orcamento-incerteza` | ≤300ms | `OrcamentoIncertezaQueryService` — prefetch aninhado |
| GET `/instrumento/{id}/historico-calibracoes` | ≤500ms | `HistoricoCalibracaoPorInstrumentoQueryService` — paginação obrigatória |
| GET `/escopo-cmc` (filtro grandeza+faixa) | ≤200ms | `EscopoCMCQueryService` |
| GET `/proficiencia/painel` | ≤500ms | `ProficienciaPainelQueryService` |

### Índices adicionais (em migration M4 P1)

```sql
CREATE INDEX idx_leitura_calib_ponto_rep ON leitura
  (tenant_id, calibracao_id, ponto_calibracao, numero_repeticao);

CREATE INDEX idx_evento_calib_occurred ON evento_de_calibracao
  (tenant_id, calibracao_id, occurred_at DESC);

CREATE INDEX idx_componente_inc_orcamento ON componente_incerteza
  (tenant_id, orcamento_incerteza_id);

CREATE INDEX idx_historico_calib_inst ON calibracao
  (tenant_id, instrumento_id, criada_em DESC)
  WHERE status = 'aprovada';
```

### Testes obrigatórios

- `tests/performance/test_calibracao_visao_360_n_plus_one.py` — `assertNumQueries(<=6)`.
- `tests/performance/test_painel_orcamento_n_plus_one.py` — `assertNumQueries(<=8)`.

---

## § ACTION_IDEMPOTENT map por endpoint (P-CAL-T7)

| Endpoint | Chave idempotência | Window | TTL |
|---|---|---|---|
| `POST /calibracao/recepcionar` | `(tenant_id, idempotency_key)` + hash payload | 24h | 30d |
| `POST /calibracao/{id}/configurar` | `(tenant_id, calibracao_id, idempotency_key)` | 24h | 30d |
| `POST /calibracao/{id}/registrar-leitura` | `(tenant_id, calibracao_id, idempotency_key)` + hash (ponto+rep+valor) | 24h | 30d |
| `POST /calibracao/{id}/corrigir-leitura` | `(tenant_id, leitura_id, idempotency_key)` | 24h | 30d |
| `POST /calibracao/{id}/calcular-incerteza` | `(tenant_id, calibracao_id, idempotency_key)` | 24h | 30d |
| `POST /calibracao/{id}/avaliar-conformidade` | `(tenant_id, calibracao_id, idempotency_key)` | 24h | 30d |
| `POST /calibracao/{id}/aprovar-revisao` | `(tenant_id, calibracao_id, idempotency_key, revisor_id)` | 24h | 30d |
| `POST /calibracao/{id}/rejeitar-revisao` | `(tenant_id, calibracao_id, idempotency_key, revisor_id)` | 24h | 30d |
| `POST /calibracao/{id}/aprovar-2a-conferencia` | `(tenant_id, calibracao_id, idempotency_key, conferente_id)` | 24h | 30d |
| `POST /calibracao/{id}/cancelar` | `(tenant_id, calibracao_id, idempotency_key)` | 24h | 30d |
| `POST /calibracao/{id}/subcontratar` | `(tenant_id, calibracao_id, idempotency_key, subcontratado_id)` | 24h | 30d |
| `POST /calibracao/{id}/registrar-recebimento-subcontratado` | `(tenant_id, calibracao_id, idempotency_key)` | 24h | 30d |
| `POST /nc/{id}/resolver` | `(tenant_id, nc_id, idempotency_key)` | 24h | 30d |
| `POST /padrao` (cadastro) | `(tenant_id, idempotency_key)` + hash (NS+grandeza) | 24h | 30d |
| `POST /padrao/{id}/recal-externo` | `(tenant_id, padrao_id, idempotency_key)` | 24h | 30d |
| `POST /padrao/{id}/intercomparacao` | `(tenant_id, padrao_id, idempotency_key, rodada_id)` | 24h | 30d |
| `POST /padrao/{id}/medicao-controle` | `(tenant_id, padrao_id, idempotency_key)` + hash (valor+executado_em) | 24h | 30d |
| `POST /proficiencia/{id}/analise-impacto` | `(tenant_id, rodada_id, idempotency_key)` | 24h | 30d |

Promover **INV-CAL-IDEMP-001**: "Idempotency-Key obrigatória em 18 POSTs; chave inclui hash do payload pra detectar mismatch payload-key (replay com payload diferente retorna 422 `IdempotencyPayloadMismatch`)."

---

## § Drill `validar_m4_calibracao` — 25 checagens (P-CAL-T11)

1. RLS habilitada em 19 tabelas M4 + roles `NOBYPASSRLS`.
2. Triggers append-only em 9 entidades imutáveis (`Leitura`, `LeituraCorrecao`, `CondicoesAmbientais`, `OrcamentoIncerteza`, `ComponenteIncerteza`, `OrcamentoPorPonto`, `PadraoUsado`, `RecepcaoItemCalibracao`, `MedicaoControle`, `EventoDeCalibracao`, `AnaliseImpactoNCProficiência`, `AceiteSubcontratacao`, `AceiteRegraDecisao`, `OverrideRegraDecisaoCliente`, `EventoBackupMetrologico`).
3. Invocação real dos 5 predicates em AC binário (cmc_cobre, padrao_vigente_no_uso, procedimento_vigente_para, regra_decisao_aplicavel, rt_competencia_cobre).
4. 6 consumers M4 protegidos por `consumer_idempotente` + tenant_id explícito.
5. Idempotency-Key validada em 18 POSTs.
6. Replay determinístico do motor em 30 fixtures (GUM clássico + Monte Carlo).
7. Divergência 2º caminho dentro do limite (0.1% alerta, 1% bloqueio).
8. Hash-chain `EventoDeCalibracao` sem garfo após 100 inserts concorrentes em 4 workers.
9. KMS rotação anual + verificação 25a (drill `validar_kms_retencao_hmac`).
10. Snapshot `PadraoUsado` lock pós `em_revisao_1` (trigger PG).
11. Snapshot `Calibracao.snapshot_competencia_revisor_json` capturado em aprovarRevisao.
12. Snapshot `Calibracao.snapshot_competencia_conferente_json` capturado em aprovar2aConferencia.
13. Concorrência: 50 threads tentando registrar mesma `(calibracao_id, ponto, repeticao)` → 1 sucesso + 49×412.
14. Concorrência: 50 threads tentando `iniciarLeituras` na mesma calibração → 1 sucesso + 49 ConflitoVersao.
15. Anti-fraude: 4 DRILL-FRAUDE-CAL com user ≠ designado retornam 403.
16. Componentes mínimos: orçamento sem REPETIBILIDADE → 412 ComponentesMinimosAusentes.
17. ILAC G8: BANDA_GUARDA_30 sem PFA → 412 PFANaoCalculada.
18. Acordo cliente: RBC sem `AceiteRegraDecisao` → 412 RegraDecisaoNaoAcordadaCliente.
19. Recepção avulsa: sem `analise_critica_pedido_inline` → 412 AnaliseCriticaPedidoAusente.
20. Subcontratação: avaliação vencida → 412 AvaliacaoSubcontratadoVencida.
21. NC: transição `→ ACAO_EXECUTADA` com decisao A_DEFINIR → 412.
22. NC PARAR_TRABALHO sem cliente_notificado → 412.
23. Backup diário: gap >25h dispara alerta P1.
24. Suite pytest M4 chave: ≥80 testes verdes em ≤8min.
25. Hooks `_test-runner.sh`: 312/312 + ≥5 hooks novos M4 (cmc-binding, incerteza-versao-motor, hmac-versao-formato, migration-metrology-classifier, foto-exif-strip, override-regra-decisao-contrato).

---

## Bloqueantes Wave A (não bloqueiam fechamento M4 dogfooding)

Consolidação dos GATEs Wave A novos (rastreados em `docs/governanca/gates-wave-a-consolidado.md`):

**De RBC (12):**
- GATE-CAL-ZONAS-ILAC-G8 (P3)
- GATE-CAL-COMPONENTES-MIN 🔴 CGCRE (P3)
- GATE-CAL-ACEITE-REGRA-DEC 🔴 CGCRE+OAB (P3 — pré 1º tenant externo)
- GATE-CAL-ANAL-CRIT-AVULSA (P4)
- GATE-CAL-SUBC-AVAL 🔴 CGCRE (Wave A operacional)
- GATE-CAL-NC-CLIENTE-NOTIF (P4)
- GATE-CAL-INC-FORMULA 🔴 CGCRE (P3 + bateria replay)
- GATE-CAL-EP-WARNING (P4)
- GATE-CAL-RAST-SI-ENUM (P3)
- GATE-CAL-RT-SNAPSHOT (P4)
- GATE-CAL-BACKUP-METROL (P4 + Wave A operacional)
- GATE-CAL-SUBC-WORDING 🔴 CGCRE+OAB (P3)

**De advogado (8 — todos REQUEREM OAB humana antes do 1º tenant externo pago):**
- 🔴 GATE-CAL-SUBC-OAB (DPA + texto aceite-subcontratacao-v1.0.md + touch alto risco)
- 🔴 GATE-CAL-PII-SAUDE-OAB (lista palavra-chave saúde art. 11)
- 🔴 GATE-CAL-OVERRIDE-OAB (clausula-override-regra-decisao-v1.0.md)
- GATE-CAL-RECLAMACAO-FLUXO (Wave A; ReclamacaoCalibracao + US-CAL-018)
- 🔴 GATE-CAL-FOTO-OAB (aviso-foto-recepcao-v1.0.md + RIPD-Calibracao)
- 🔴 GATE-CAL-CONT-OAB (consentimento contato técnico PF)
- GATE-CAL-FOTO-EXIF-HOOK (Wave A pré-tenant externo)
- GATE-CAL-ANON-CONCORRENCIA (Wave A pré-tenant externo PF)

**De corretora (9 — todos REQUEREM CORRETORA SUSEP humana antes do 1º tenant externo pago):**
- 🔴 GATE-SEG-EO-CAL-1 (multi-tier vicarious — farma/saúde)
- 🔴 GATE-SEG-SUBC-1 (sub-contracted quality liability)
- 🔴 GATE-SEG-CYBER-HMAC-1 (cryptographic proof integrity 25a)
- 🔴 GATE-SEG-EO-INVEST-1 (investigation defense tenant admin)
- 🔴 GATE-SEG-EO-FRAUDE-1 (fraud prevention defect)
- 🔴 GATE-SEG-BPT-PADROES-1 (Modalidade 8 NOVA — padrão próprio R$ 500k)
- 🔴 GATE-SEG-CYBER-PATIENT-1 (sensitive personal data third-party)
- 🔴 GATE-SEG-EO-CONSENT-1 (wrongful consent capture)
- 🔴 GATE-SEG-ACR-EXCECAO-1 (governance defect exceção 2ª conferência)

**De tech-lead (3):**
- GATE-CAL-ACREDITACAO-CONSUMER (Wave A — ADR-0014 aceita + produtor real)
- GATE-CAL-MIG-CLASSIF (Wave A — convenção tag em migration)
- GATE-CAL-DRILL (P4 — 25 checagens)
- GATE-CAL-PERF-NPLUS1 (Wave A se não couber em M4 P4)

**Total: 32 GATEs Wave A novos M4.** Nenhum bloqueia M4 dogfooding Balanças Solution; todos bloqueiam 1º tenant externo pago em grau variável (alguns só farma/saúde, outros qualquer tenant).

---

## ACEITES (confirmação, sem mudança estrutural)

- **P-CAL-R15** — watchdog `os-calibracao-link` herdado do M3 (P-OS-R6) sem retrofit. Suficiente.
- **P-CAL-R16** — NG-CAL-15 (aprovação M4 user+senha+MFA, A3 fica em Marco 5). Defensável — cl. 7.8 ISO exige A3 na EMISSÃO probatória, não na decisão técnica interna.
- **P-CAL-S10** — divergência 0.1%-1% emite cert e descobre erro depois → ADR-0045 Marco 5 cobre via consumer + Modalidade 1 + Modalidade 7. Sem ação adicional.

---

## Decisões pendentes do Roldão

Antes de partir para P3 (matriz reconciliação + atualizar spec.md + ADR-0024/0028/0063 + criar ADR-0065), **5 decisões dependem do Roldão**:

| Decisão | Origem | Opções | Recomendação default |
|---|---|---|---|
| **D-M4-1: Motor de cálculo — 2º caminho** | P-CAL-T2 | (A) GUM clássico Python + Monte Carlo NumPy / (B) GUM clássico + lib externa de referência (`metas-uncertainty`) / (C) Mesma impl com Decimal vs float | **(A)** — defensável ISO 17025 cl. 7.11; 2 algoritmos diferentes |
| **D-M4-2: Predicate `rt_competencia_cobre` ATIVAÇÃO** | P-CAL-T4 | (A) Lazy em configurar_calibracao + 3 use cases pós (NÃO em iniciar_atividade) / (B) Grandeza obrigatória em criar_os (retrofit M3) | **(A)** — sem retrofit destrutivo M3; semântica defensável |
| **D-M4-3: ADR-0028 rev 3 com Modalidade 8 NOVA — autorizar corretora SUSEP agora** | P-CAL-S1..S10 | (A) Solicitar 3 propostas Marsh/AON/Howden em paralelo a M4 P3-P4 / (B) Aguardar M4 fechado / (C) Aguardar 1º tenant externo definido | **(A)** — wordings novos são complexos (Lloyd's via Marsh); negociação leva 2-3 meses |
| **D-M4-4: Consultor CGCRE humano credenciado — contratar agora** | P-CAL-R2/R3/R5/R7/R12 + RBC §"Limites" | (A) Contratar 3 engajamentos sequenciais agora (matrizes + dossiê IQ/OQ/PQ + auditoria simulada — R$ 25-45k total) / (B) Aguardar M4 fechado pra contratar / (C) Adiar até 1º tenant externo | **(A)** — matrizes técnicas (componentes-obrigatórios + fórmulas) bloqueiam fechamento M4 mesmo dogfooding; 1º engajamento (R$ 10-15k) é pré-requisito P3 |
| **D-M4-5: OAB humana — engajamento focado 6-8h** | P-CAL-A1/A2/A3/A5/A6 | (A) Contratar 1 consulta OAB focada antes do 1º tenant externo (6 documentos canônicos + DPIA) / (B) Aguardar 1º tenant ser identificado | **(A)** — preparei o material; advogado(a) cobre 6 docs em uma sessão consolidada |

---

## Decisão arquitetural geral

- **Hooks já cobrem o saneamento estrutural M3** (vigência, soft-delete, FK anonimização, biometria-key, os-conclusao-terminais, spec-ac-binario, bus-envelope-validator v10, migration-rls-check, audit-immutability-check, idempotency-key-header-check, migration-concorrencia-os-check, sync-merge-foto-appendonly).
- **M4 acrescenta 6 hooks novos no P9** (não 4): cmc-binding-check + incerteza-versao-motor-check + hmac-versao-formato-check + migration-metrology-classifier + foto-exif-strip-check + override-regra-decisao-contrato-check + migration-concorrencia-calibracao-check + metrology-replay-fixtures-versionadas. Total: **8 hooks novos M4**.
- **Eventos via `audit/event_helpers.publicar_evento`** (helper único M1+M2+M3) — M4 herda; sanitizer próprio `sanitizar_payload_evento_calibracao` (G2 do dossiê).
- **Predicates authz** — extensão necessária ADR-0012: `cmc_cobre`, `padrao_vigente_no_uso`, `procedimento_vigente_para`, `regra_decisao_aplicavel`, `rt_competencia_cobre` ATIVADO M4, `clausula_override_vigente` (P-CAL-A3), `pode_aprovar_revisao`, `pode_aprovar_2a_conferencia`, `pode_subcontratar`, `subcontratado_vigente_para`, `pode_marcar_nc_calibracao`, `pode_corrigir_leitura`, `pode_registrar_leitura`, `pode_configurar_calibracao`. **14 predicates M4.**

---

## Próximo passo (P3 — matriz reconciliação)

Após decisões D-M4-1..D-M4-5 do Roldão:

1. **Atualizar spec.md** absorvendo os 10 BLOQUEANTE + 23 MÉDIO INV-RITUAL-001 (retrofit em §3.1, §3.2, §3.3 nova, §4, §5, §6, §8, §9, §10).
2. **Criar ADR-0065** "Concorrência em calibração metrológica" (paralelo ADR-0041).
3. **PR retrofit ADR-0024** com 6 zonas ILAC G8 + PFA + acordo cliente.
4. **PR retrofit ADR-0028** rev 3 com 8 cláusulas novas + Modalidade 8 NOVA + 9 GATEs SEG novos.
5. **PR retrofit ADR-0063** Opção A (lazy em configurar_calibracao + 3 use cases pós).
6. **PR contra `docs/dominios/metrologia/modulos/calibracao/prd.md`** com ACs novos (AC-CAL-001-3, AC-CAL-002-3, AC-CAL-002-X acordo, AC-CAL-004-7..8, AC-CAL-005-4..7, AC-CAL-006-X zonas, AC-CAL-007-5, AC-CAL-008-4, AC-CAL-014-5, AC-CAL-017-7..8).
7. **PR contra REGRAS-INEGOCIAVEIS.md** com 24 INVs novos M4 (lista consolidada nas seções acima).
8. **Adicionar 6 entidades novas em §3.2 spec:** `AceiteRegraDecisao`, `OverrideRegraDecisaoCliente`, `ReclamacaoCalibracao`, `ConsentimentoContatoTecnicoCliente`, `AvaliacaoPeriodicaSubcontratado`, `PlanoAcaoProficienciaWarning`, `EventoBackupMetrologico`, `ConsentimentoFotoRecusado` (8 entidades — somam às 17 já em spec.md).
9. **Adicionar US-CAL-018** "Reclamação do cliente sobre calibração emitida".
10. **Matriz reconciliação** (`docs/faseamento/M4-calibracao/matriz-reconciliacao.md`): PRD ↔ spec ↔ plan — zero conflito.
11. **tasks.md** com ~150 T-CAL-NNN endereçando 100% dos AC + INVs + sagas + GATEs (M4 é 25% maior que M3).
12. **5 minutas canônicas pra OAB humana**: aceite-subcontratacao-v1.0.md + dpa-laboratorio-subcontratado-v1.0.md + clausula-override-regra-decisao-v1.0.md + aviso-foto-recepcao-v1.0.md + aceite-regra-decisao-v1.0.md.
13. **2 matrizes técnicas pra CGCRE humano**: componentes-obrigatorios-por-grandeza.md + formula-calculo-por-grandeza.md.
14. **Atualizar `docs/governanca/gates-wave-a-consolidado.md`** com 32 GATEs novos M4.
15. **Implement (P4) em 10 fases** + **P5** (10 auditores Família 5).
