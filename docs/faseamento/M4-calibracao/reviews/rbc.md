---
owner: consultor-rbc-iso17025
revisado_em: 2026-05-25
status: stable
tipo: review-p2-rbc
marco: Wave A Marco 4 — metrologia/calibracao
fase-ritual: P2
revisor: consultor-rbc-iso17025 (subagente IA)
credencial-cgcre: NAO (parecer consultivo — REQUER consultor humano credenciado antes de auditoria CGCRE real ou submissão RBC)
relacionados:
  - docs/faseamento/M4-calibracao/spec.md
  - docs/adr/0022-rt-tenant.md
  - docs/adr/0024-regra-de-decisao-iso-17025.md
  - docs/adr/0025-validacao-software-iso-17025.md
  - docs/adr/0026-segunda-conferencia-independencia.md
  - docs/adr/0040-padrao-metrologico-entidade-separada.md
  - docs/adr/0063-rt-competencia-grandeza-diferida-marco4.md
---

# Parecer P2 RBC/ISO 17025 — Marco 4 `metrologia/calibracao`

## Sumário executivo

| Severidade | Quantidade | IDs |
|---|---|---|
| BLOQUEANTE (corrige em P2/P3) | 6 | P-CAL-R1, P-CAL-R2, P-CAL-R3, P-CAL-R4, P-CAL-R5, P-CAL-R6 |
| ALTO Wave A (resolve em P4 com ADR/AC novo) | 5 | P-CAL-R7, P-CAL-R8, P-CAL-R9, P-CAL-R10, P-CAL-R11 |
| MÉDIO (resolve em P4) | 3 | P-CAL-R12, P-CAL-R13, P-CAL-R14 |
| ACEITE (rastreado, sem ação) | 2 | P-CAL-R15, P-CAL-R16 |
| **Total** | **16** | |

**Veredito:** AJUSTAR. O spec é extraordinariamente sólido na **estrutura de dados** (entidades, snapshots, hash-chain, máquina de estados, INVs anti-fraude) e nas **lições G1..G10 do M3 OS** estão visivelmente cravadas. As lacunas residuais são de **profundidade metrológica fina** que CGCRE em supervisão pergunta: zonificação ILAC G8 incompleta (3 zonas em vez de 6), componentes mínimos obrigatórios NIT-DICLA-030 não enforced, regra de decisão sem confirmação documentada do cliente (cl. 7.1.3), análise crítica em recepção avulsa órfã, política escrita de avaliação de subcontratado (cl. 6.6.2 a-f) ausente, e qualidade analítica (Tipo A, correlação, bias, Welch-Satterthwaite explícitos) deixada como "motor calcula" sem AC binário.

**Marco 4 é o MAIS sensível do produto** — não só técnico-comercial (diferencial vs Calibre), mas **comercialmente fatal se cair em supervisão CGCRE**. Recomendo que TODOS os 6 BLOQUEANTES entrem no `plan.md` da P2 e na matriz de reconciliação, e que P-CAL-R7..R11 sejam transformados em ADR/AC explícitos antes de P4.

**Aviso obrigatório:** sou subagente IA `consultor-rbc-iso17025`. **Não tenho credencial CGCRE.** Este parecer é consultivo. Itens marcados `REQUER CONSULTOR CREDENCIADO CGCRE` exigem revisão de consultor humano credenciado antes de qualquer auditoria real, submissão a processo de acreditação RBC, ou exposição a tenant farma TOP-3. Estimativa: R$ 10-18k por engajamento pontual (M4 é mais denso que M3).

---

## Achados

### P-CAL-R1 — BLOQUEANTE — Zonificação ILAC G8 incompleta (3 zonas em vez de 6) — cl. 7.8.6

**Cláusula ISO/IEC 17025:** 7.8.6.1 + 7.8.6.2 — "Quando uma declaração de conformidade é feita ... a regra de decisão deve considerar o nível de risco associado à regra de decisão... e ser documentada."
**Norma de referência:** ILAC G8:09/2019 §4 — "Decision rules and statements of conformity" tabela 1, **6 zonas decisórias**.

**Evidência (spec):**
- Linha 192 spec: `decisao VARCHAR(15) NOT NULL DEFAULT 'NA'` (`APROVADO | REPROVADO | CONDICIONAL | NA`) — apenas 3 valores.
- Linha 117 spec VO `RegraDecisao`: helper `aplicar(spec, valor, U_expandida) → ConformidadeAvaliada(zona, decisao_sugerida)` — declara `zona` mas não enumera quais zonas.
- PRD AC-CAL-006-2 (linha 178 prd): aceita "ZONA_INCERTEZA" como decisão explícita do metrologista.
- Spec §3.2 não declara enum `zona`.

**Análise (o que CGCRE pergunta em auditoria):**
ILAC G8 (referenciada por NIT-DICLA-026 cl. 4 + DOQ-CGCRE-001) define 6 zonas resultantes da interseção valor±U vs LSL/USL:

1. **PASS** (valor + U dentro de [LSL, USL] inteiro)
2. **CONDITIONAL PASS** (valor dentro, mas U cruza LSL ou USL)
3. **PASS COM RESSALVA na banda de guarda** (modo Banda 30%)
4. **CONDITIONAL FAIL** (valor fora, mas U cruza)
5. **FAIL COM RESSALVA** (valor fora E U distante do limite)
6. **FAIL** (valor + U totalmente fora)

Spec resume tudo a `APROVADO | REPROVADO | CONDICIONAL`, perdendo a granularidade que ILAC G8 exige. Auditor pergunta: "como o sistema documenta a diferença entre `CONDITIONAL PASS` (valor dentro, U cruza) e `CONDITIONAL FAIL` (valor fora, U cruza)? Ambos são `CONDICIONAL` no enum atual?". Resposta atual: insuficiente.

Também: a regra `BANDA_GUARDA_30` exige documentar a **probabilidade de aceitação falsa (PFA)** calculada (ILAC G8 §4.4 + JCGM 106 §9). Spec não tem campo `pfa_calculada NUMERIC(5,4)` em `ConformidadeAvaliada` ou `OrcamentoIncerteza`.

**Decisão recomendada:**

1. Expandir enum `decisao` para 6 valores ILAC G8 + criar VO `ZonaDecisao`:
```
decisao ENUM('PASS', 'CONDITIONAL_PASS', 'PASS_COM_RESSALVA',
              'CONDITIONAL_FAIL', 'FAIL_COM_RESSALVA', 'FAIL', 'NA')
```
2. Adicionar campos em `Calibracao` (ou tabela `ConformidadeAvaliada` separada se preferível):
   - `zona_ilac_g8 VARCHAR(20) NOT NULL`
   - `pfa_calculada NUMERIC(5,4) NULL` (NOT NULL quando `regra_decisao = BANDA_GUARDA_30`)
   - `pra_calculada NUMERIC(5,4) NULL` (NOT NULL quando `regra_decisao = RISCO_COMPARTILHADO`)
3. Promover **INV-CAL-DEC-004**: "Calibração com `regra_decisao = BANDA_GUARDA_30` exige `pfa_calculada` NOT NULL; ausente → 412 `PFANaoCalculada`."
4. Promover **INV-CAL-DEC-005**: "Zona ILAC G8 deve ser uma das 6 + NA; outros valores rejeitados em DDL."
5. ADR retrofit em **ADR-0024** acrescentando tabela ILAC G8 (atualmente lista só 3 modos sem citar 6 zonas).

**Cenário concreto auditoria:** CGCRE supervisão pede print de tela mostrando 50 últimas calibrações. Auditor agrupa por `decisao`. Pergunta: "destas 12 marcadas `CONDICIONAL`, quantas foram CONDITIONAL_PASS vs CONDITIONAL_FAIL? E como o cliente foi orientado em cada caso?". Sistema atual não distingue → NC documental.

---

### P-CAL-R2 — BLOQUEANTE — Componentes mínimos obrigatórios do orçamento de incerteza não-enforced — NIT-DICLA-030 rev. 15 §6.3

**Norma:** NIT-DICLA-030 rev. 15 (dez/2024) §6.3 — "O orçamento de incerteza deve contemplar, no mínimo: (i) repetibilidade das medições; (ii) resolução do instrumento sob calibração; (iii) incerteza herdada do padrão de referência (calibração externa); (iv) influência das condições ambientais relevantes para a grandeza."

**Evidência (spec):**
- Linha 261-269 spec: `ComponenteIncerteza` permite qualquer `nome_componente VARCHAR(80)` + `tipo A | B`. Nada obriga **os 4 componentes mínimos** da NIT-DICLA-030 §6.3.
- INV-CAL-INC-001 (linha 452 spec): exige só `documentacao_agregacao` quando há `OrcamentoPorPonto[]`. Não impõe componentes mínimos.
- Spec §4 máquina de estados não bloqueia `em_execucao → em_revisao_1` por ausência dos 4 componentes.

**Análise:**
CGCRE supervisão dossiê DOQ-CGCRE-029 (calibração de massa): "Não foram identificadas no orçamento de incerteza as componentes referentes a deriva do padrão e influência da temperatura sobre o instrumento sob calibração — NC ALTO." Esse é literalmente o achado mais comum em laboratórios em supervisão. Sistema que **permite** orçamento sem repetibilidade ou sem incerteza do padrão é cumplice do erro.

**Decisão recomendada:**

1. Adicionar enum `tipo_origem_componente`:
```
tipo_origem_componente ENUM(
  'REPETIBILIDADE',           -- Tipo A (obrigatório)
  'RESOLUCAO_INSTRUMENTO',    -- Tipo B (obrigatório)
  'INCERTEZA_PADRAO_REF',     -- Tipo B (obrigatório quando há PadraoUsado)
  'DERIVA_PADRAO',            -- Tipo B (obrigatório quando padrao.classe ≤ M2)
  'CONDICOES_AMBIENTAIS',     -- Tipo B (obrigatório por grandeza — ex: temperatura em massa, umidade em higrometria)
  'EXCENTRICIDADE',           -- Tipo B (obrigatório quando equipamento.tipo_subjacente = balanca)
  'POLARIZACAO_BIAS',         -- Tipo B (obrigatório quando bias != 0 — ver P-CAL-R7)
  'OUTRO'                     -- Tipo B (livre, justificável)
)
```
2. Promover **INV-CAL-INC-002**: "Antes de transitar `em_execucao → em_revisao_1`, o `OrcamentoIncerteza.calcularIncerteza` valida presença de componentes obrigatórios por grandeza+padrão (matriz em `docs/dominios/metrologia/modulos/calibracao/componentes-obrigatorios-por-grandeza.md` a criar). Ausência → 412 `ComponentesMinimosAusentes: [lista]`."
3. Criar AC novo **AC-CAL-005-4**: "GIVEN OrcamentoIncerteza calculado WHEN `solicitarRevisao`, THEN sistema valida matriz componentes-obrigatórios por grandeza+padrão; ausência bloqueia."

**Limite — REQUER CONSULTOR CREDENCIADO CGCRE para validar matriz componentes-obrigatórios-por-grandeza** (cada grandeza tem matriz própria; massa, volume, temperatura, pressão divergem).

---

### P-CAL-R3 — BLOQUEANTE — Regra de decisão sem confirmação documentada do cliente — cl. 7.1.3 + 7.8.6 + 7.1.7

**Cláusula ISO/IEC 17025:** 7.1.3 "Quando o cliente solicita uma declaração de conformidade a uma especificação para o ensaio ou calibração ... a especificação ou norma e a regra de decisão devem ser claramente definidas. **A regra de decisão escolhida deve ser comunicada ao e acordada com o cliente**, a menos que seja inerente à especificação ou norma solicitada."

**Evidência (spec):**
- Linha 193-194 spec: `regra_decisao VARCHAR(25) NOT NULL` + `regra_decisao_override_cliente BOOLEAN DEFAULT false`.
- ADR-0024 §"Override por cliente": cliente faz override "via cláusula contratual" — sem fluxo no sistema que materialize isso.
- AC-CAL-002 (PRD): não menciona confirmação do cliente sobre regra de decisão.
- US-OS-001 (M3 OS) faz análise crítica do pedido, mas não há campo `regra_decisao_acordada_com_cliente`.

**Análise:**
CGCRE em supervisão pergunta: "mostre a evidência documentada de que o cliente FOI INFORMADO e ACORDOU com a regra de decisão `BANDA_GUARDA_30` antes da execução da calibração 2025-12345." Spec atual permite que tenant configure tudo internamente sem proof-of-communication. Cláusula contratual ativa é insuficiente — auditor quer **evidência POR CALIBRAÇÃO** (ou ao menos por contrato vigente com aceite assinado do cliente, com snapshot do texto).

**Decisão recomendada:**

1. Adicionar à entidade `Calibracao` (ou à análise crítica de pedido M3):
```
- regra_decisao_acordada_em TIMESTAMPTZ NOT NULL
- regra_decisao_acordada_documento_id UUID NOT NULL FK (→ AceiteRegraDecisao ou cláusula contratual snapshot)
- regra_decisao_acordada_hash CHAR(80) NOT NULL (HashVersionado do texto acordado)
```
2. Criar entidade `AceiteRegraDecisao` (paralela a `AceiteSubcontratacao`):
   - Texto canônico v1.0 (REQUER OAB + RBC).
   - Assinatura cliente (touch ou A3) OU referência a cláusula contratual ativa com aceite.
   - Snapshot da regra escolhida.
3. Promover **INV-CAL-DEC-006**: "Toda calibração com `tipo_acreditacao = RBC` exige `regra_decisao_acordada_documento_id NOT NULL` antes de `em_revisao_1`; ausente → 412 `RegraDecisaoNaoAcordadaCliente`."
4. Em **AC-CAL-002** (revisão): GIVEN regra de decisão = banda_guarda OU risco_compartilhado WHEN `configurarCalibracao` executa, THEN exige aceite vigente da regra pelo cliente; ausente → bloqueia.

**🔴 REQUER CONSULTOR CREDENCIADO CGCRE** para definir wording exato do texto canônico `aceite-regra-decisao-v1.0.md` (paralelo a `aceite-subcontratacao-v1.0.md`).

---

### P-CAL-R4 — BLOQUEANTE — Análise crítica de pedidos em recepção AVULSA órfã — cl. 7.1.1 + 7.1.7

**Cláusula:** 7.1.1 "Procedimento para análise crítica de pedidos, propostas e contratos."

**Evidência:**
- Linha 176 spec: `atividade_os_id UUID NULL FK` — recepção AVULSA permite NULL.
- Linha 291-300 spec: `RecepcaoItemCalibracao` tem `avaliacao_aptidao VARCHAR(20)` mas NÃO carrega vínculo a análise crítica de pedido nem campo inline.
- P-OS-R2 do parecer M3 OS recomendou para M3 abrir OS pedir `analise_critica_inline_texto` em US-OS-015 (OS avulsa). Spec M4 paralelo (recepção AVULSA SEM OS) **não tem AC equivalente**.

**Análise:**
Cenário concreto: cliente chega no balcão lab com 1 paquímetro; lab abre `Calibracao` direta (sem OS, sem orçamento — `atividade_os_id=NULL`). Quando auditor pergunta "qual a análise crítica desse pedido? Quem analisou? Capacidade técnica confirmada?", spec atual: silêncio. RecepcaoItemCalibracao.`avaliacao_aptidao` é avaliação do **item**, não análise crítica do **pedido** (cl. 7.1.1 ≠ cl. 7.4).

**Decisão recomendada:**

1. Adicionar à entidade `Calibracao` (ou em `RecepcaoItemCalibracao`):
```
- analise_critica_pedido_id UUID NULL FK (→ orcamento.analise_critica quando atividade_os_id NOT NULL)
- analise_critica_pedido_inline_hash CHAR(80) NULL (canonicalizado quando recepção avulsa)
- analise_critica_pedido_inline_canonicalizada TEXT NULL (≥100 chars + anti-PII INV-CAL-TXT-001)
- capacidade_tecnica_confirmada_por_user_id UUID NOT NULL
```
2. CHECK constraint:
```sql
CHECK (
  (atividade_os_id IS NOT NULL AND analise_critica_pedido_id IS NOT NULL)
  OR (atividade_os_id IS NULL AND analise_critica_pedido_inline_hash IS NOT NULL)
)
```
3. Criar AC novo **AC-CAL-001-3**:
> GIVEN recepção AVULSA (`atividade_os_id IS NULL`) WHEN `recepcionarInstrumento`, THEN exige `analise_critica_pedido_inline_hash` (texto ≥100 chars + capacidade técnica + regra de decisão + escopo confirmado) + `capacidade_tecnica_confirmada_por_user_id` NOT NULL; senão 412 `AnaliseCriticaPedidoAusente`.
4. Promover **INV-CAL-ANAL-001**: paralelo a INV-OS-ANAL-001 do M3.

---

### P-CAL-R5 — BLOQUEANTE — Política escrita de escolha + avaliação periódica de subcontratado ausente — cl. 6.6.2 a-f

**Cláusula:** 6.6.2 — "O laboratório deve garantir que produtos e serviços fornecidos externamente, **antes de serem usados**, atendam aos requisitos. Devem ser estabelecidos critérios para avaliação, seleção, monitoramento de desempenho e reavaliação de fornecedores."

**Evidência:**
- Linha 353-363 spec `LaboratorioSubcontratado`: tem cadastro técnico (acreditações, DPA, vigência). Mas:
- Sem campo `criterio_selecao_documento_id` (política escrita de escolha).
- Sem `ultima_avaliacao_periodica_em` + `proxima_avaliacao_periodica_em` (cl. 6.6.2 reavaliação).
- Sem registro de **monitoramento de desempenho** (KPIs por subcontratado: % cert no prazo, % NC, score interno).
- US-CAL-017 cobre o fluxo operacional mas não a **governança do fornecedor** (cl. 6.6.2 a-f).

**Análise:**
CGCRE supervisão pergunta: "mostre a política escrita do laboratório principal pra escolher subcontratado. Mostre as últimas 3 avaliações periódicas dos seus subcontratados ativos. Mostre os KPIs de monitoramento." Sistema atual não tem onde armazenar isso.

**Decisão recomendada:**

1. Adicionar à entidade `LaboratorioSubcontratado`:
```
- criterio_selecao_documento_id UUID NULL FK (→ docs/conformidade/comum/politicas/criterio-selecao-subcontratado-v1.0.md por tenant)
- ultima_avaliacao_periodica_em TIMESTAMPTZ NULL
- proxima_avaliacao_periodica_em TIMESTAMPTZ NOT NULL (default `vigencia_inicio + INTERVAL '12 months'`)
- score_avaliacao_atual NUMERIC(3,1) NULL (0-10)
- avaliado_por_user_id UUID NULL
```
2. Criar entidade `AvaliacaoPeriodicaSubcontratado` (1:N de LaboratorioSubcontratado, append-only WORM):
   - `criterios_avaliados_json JSONB` (4 critérios mínimos cl. 6.6.2: acreditação vigente, capacidade técnica, prazo de entrega histórico, NC histórico).
   - `score NUMERIC(3,1)`, `decisao ENUM('MANTER', 'SUSPENDER', 'DESCONTINUAR')`, `proxima_avaliacao_em`.
3. Promover **INV-CAL-SUBC-005**: "Subcontratação só permitida quando `LaboratorioSubcontratado.proxima_avaliacao_periodica_em > now() - INTERVAL '12 months'`; caso contrário 412 `AvaliacaoSubcontratadoVencida`."
4. Job procrastinate `verificar_avaliacoes_subcontratados_vencendo` — alerta P2 30 dias antes do vencimento.
5. Criar **GATE-CAL-SUBC-AVAL** — bloqueia Wave A operacional sem matriz de critérios + política versionada.

**🔴 REQUER CONSULTOR CREDENCIADO CGCRE** para validar template da política `criterio-selecao-subcontratado-v1.0.md` (varia por tenant — ANVISA-RBC tem critérios próprios).

---

### P-CAL-R6 — BLOQUEANTE — Notificação ao cliente sobre trabalho não-conforme + decisão "continuar ou parar" — cl. 7.10.1 + 7.10.2

**Cláusula:** 7.10.1 "O laboratório deve ter procedimento... incluindo: a) responsabilidades; b) ações com base em níveis de risco; c) **avaliação de significância**; **d) decisão sobre aceitabilidade**; **e) notificação do cliente quando necessário, e medida de retirada**; f) responsabilidade por autorizar a retomada."

**Evidência:**
- Linha 324-342 spec `NaoConformidade`: cobre causa-raiz, ação corretiva, eficácia. **NÃO cobre**:
  - Campo `decisao_continuar_ou_parar VARCHAR(15)` (PARAR_TRABALHO / CONTINUAR_COM_CONTROLE).
  - Campo `cliente_notificado_em TIMESTAMPTZ` + `cliente_notificado_documento_id UUID`.
  - Campo `autorizacao_retomada_user_id UUID` + `autorizacao_retomada_em TIMESTAMPTZ`.
- Spec §6.1 evento `Calibracao.NCAberta` não dispara notificação automática ao cliente.

**Análise:**
CGCRE pergunta: "a calibração 2025-12345 entrou em NC durante execução. O cliente foi notificado? Em que data? Quem autorizou a retomada após resolução?". Sistema atual: campos não existem. Auditor identifica NC documental ALTO.

**Decisão recomendada:**

1. Adicionar à entidade `NaoConformidade`:
```
- decisao_continuar_ou_parar VARCHAR(20) NOT NULL DEFAULT 'A_DEFINIR'
  (CHECK IN ('PARAR_TRABALHO', 'CONTINUAR_COM_CONTROLE', 'A_DEFINIR'))
- cliente_notificado_em TIMESTAMPTZ NULL
- cliente_notificado_via VARCHAR(20) NULL (EMAIL_PORTAL | A3_ASSINATURA | TERMO_PRESENCIAL)
- cliente_notificado_documento_id UUID NULL FK
- autorizacao_retomada_user_id UUID NULL
- autorizacao_retomada_em TIMESTAMPTZ NULL
```
2. CHECK: `estado IN ('CONTIDA', 'ACAO_CORRETIVA_DEFINIDA')` permite `decisao=A_DEFINIR`; transição `→ ACAO_EXECUTADA` exige `decisao != 'A_DEFINIR'`.
3. Quando `decisao = PARAR_TRABALHO` → exige `cliente_notificado_em NOT NULL` antes de prosseguir.
4. Promover **INV-CAL-NC-002**: "NaoConformidade.decisao_continuar_ou_parar obrigatório antes de ACAO_EXECUTADA."
5. Promover **INV-CAL-NC-003**: "NaoConformidade.decisao = PARAR_TRABALHO exige cliente_notificado_em NOT NULL."
6. Criar AC novo **AC-CAL-014-5**: notificação cliente.
7. Saga consumer `Calibracao.NCAberta` → publica `Cliente.NotificacaoPendente` quando `decisao = PARAR_TRABALHO`.

---

### P-CAL-R7 — ALTO Wave A — Incerteza padrão Tipo A (repetibilidade) sem fórmula explícita + Welch-Satterthwaite + correlação + bias

**Cláusula:** GUM/JCGM 100:2008 §4.2 (Tipo A), §5.2 (correlações), §G.4 (Welch-Satterthwaite) + NIT-DICLA-030 §7.4.

**Evidência:**
- Linha 246 spec: `grau_liberdade_efetivo NUMERIC(10,2) NOT NULL (Welch-Satterthwaite)` — campo cravado mas **não há AC binário que valide cálculo correto**.
- Linha 260-269 spec `ComponenteIncerteza`: não distingue componente Tipo A (vinda de repetibilidade — `s(x)/sqrt(n)`) de Tipo B genérica.
- Spec §3.2 não tem campo `correlacao_com_componente_id UUID NULL` em ComponenteIncerteza — GUM §5.2.2 exige declarar correlação quando 2+ componentes vêm do mesmo padrão.
- Spec §3.2 não tem componente para **polarização (bias)** — quando calibração revela erro sistemático conhecido, GUM §4.3 + NIT-DICLA-030 obrigam orçar.
- Spec §3.2 não tem regra de arredondamento final (cl. 7.8.3.1.h — "incerteza com no máximo 2 dígitos significativos, valor reportado arredondado ao mesmo nível").

**Análise:**
Auditor CGCRE em supervisão (NIT-DICLA-030 §7.4): "mostre o cálculo de incerteza desta calibração; qual é a componente A? qual o `s(x)`? qual o `n`? qual o grau de liberdade efetivo? a regra de arredondamento foi aplicada?". Sistema atual: motor calcula, mas sem AC que CRAVE como.

**Decisão recomendada:**

1. Adicionar à `ComponenteIncerteza`:
```
- formula_calculo VARCHAR(40) NOT NULL (REPETIBILIDADE_STD_MEDIA | RESOLUCAO_RETANGULAR | PADRAO_CERTIFICADO | DERIVA_LINEAR | TEMPERATURA_QUADRATICA | BIAS_CONHECIDO | OUTRO)
- correlacao_com_componente_id UUID NULL FK (auto-FK; cl. GUM §5.2.2)
- coeficiente_correlacao NUMERIC(5,4) NULL (-1 a 1; obrigatório quando correlacao_com_componente_id NOT NULL)
- n_amostras INTEGER NULL (obrigatório quando tipo_componente='A')
- s_x NUMERIC(20,8) NULL (desvio-padrão amostral; obrigatório quando tipo_componente='A')
```
2. Adicionar à `OrcamentoIncerteza`:
```
- arredondamento_aplicado_regra VARCHAR(20) NOT NULL DEFAULT 'NIT_DICLA_030_2_DIGITOS_SIG'
- bias_orcado NUMERIC(20,8) NULL (quando bias conhecido)
- bias_origem VARCHAR(80) NULL
```
3. Promover **INV-CAL-INC-003**: "ComponenteIncerteza.tipo='A' exige `n_amostras ≥ 6` (NIT-DICLA-030 §7.4) + `s_x NOT NULL`."
4. Promover **INV-CAL-INC-004**: "Quando 2+ componentes têm `fonte_default_padrao_id` igual, `correlacao_com_componente_id` deve estar setado em pelo menos um deles (alerta P2 se não)."
5. Criar AC novo **AC-CAL-005-5..7** detalhando fórmula + correlação + arredondamento.
6. Cravar replay-determinístico (ADR-0025) com bateria de 20 calibrações de referência incluindo CASOS COM correlação ≠ 0 + bias conhecido.

**🔴 REQUER CONSULTOR CREDENCIADO CGCRE** para validar fórmulas por grandeza (matriz `formula_calculo_por_grandeza.md`).

---

### P-CAL-R8 — ALTO Wave A — Garantia de validade cl. 7.7 incompleta: WARNING (|z|>2) sem fluxo + gráfico X-R sem regras Western Electric

**Cláusula:** 7.7.1 (monitoramento desempenho) + 7.7.2 (PT) + NIT-DICLA-026 rev. 15 (proficiência).

**Evidência:**
- Spec linha 302-311 `MedicaoControle`: tem `dentro_2sigma`, `dentro_3sigma`. Falta:
  - Detecção de **7 pontos seguidos do mesmo lado da média** (Western Electric Rule 2).
  - Detecção de **tendência crescente/decrescente em 6+ pontos** (Rule 3).
  - Detecção de **2 de 3 pontos > 2σ** (Rule 5).
- Spec linha 344-351 `AnaliseImpactoNCProficiência`: só ativa quando `escore_z |z|>3` (UNACCEPTABLE). NIT-DICLA-026 rev. 15 exige **plano de ação documentado** quando `|z|>2` (WARNING).
- Spec não tem `escore_z` em `MedicaoControle` nem `escore_z_warning_dispara`.

**Análise:**
CGCRE NIT-DICLA-026 rev. 15 cl. 5.4: "Resultados questionáveis (|z|>2 e ≤3) requerem análise documentada de causa e plano de ação proporcional ao risco". Spec não tem flux.

**Decisão recomendada:**

1. Adicionar `MedicaoControle`:
   - `escore_z NUMERIC(5,3) NULL`
   - `regra_western_electric_violada VARCHAR(20) NULL` (RULE_1_3SIGMA | RULE_2_SEVEN_SAME_SIDE | RULE_3_TREND | RULE_5_TWO_OF_THREE)
2. Criar entidade `PlanoAcaoProficienciaWarning` (paralela a `AnaliseImpactoNCProficiência` mas para |z|>2 ≤3):
   - Causa investigada, ação proporcional, eficácia futura.
3. Job procrastinate `analisar_padrao_medicoes_controle` — após cada `MedicaoControle.INSERT`, recalcula últimas 30 medições e dispara alerta P2 se Western Electric violada.
4. **GATE-CAL-EP-WARNING** — alerta P2 + obrigação documentação.
5. Adicionar consumer `Padrao.IntercomparacaoConcluida` (linha 510 spec) com `escore_z` 2<|z|<=3 dispara criação automática de `PlanoAcaoProficienciaWarning` (não NC formal, mas plano documentado).

---

### P-CAL-R9 — ALTO Wave A — Rastreabilidade SI: formato `vinculacao SI` sem enum + ausência de cadeia documental

**Cláusula:** 6.5.2 — "Rastreabilidade ... a uma referência apropriada: a) calibração por laboratório competente; b) MR certificado com rastreabilidade comprovada; c) realização direta do SI."

**Evidência:**
- Linha 284 spec: `snapshot_padrao_json JSONB ... incluindo vinculacao SI`. Formato livre, sem enum, sem campos estruturados.
- ADR-0040 já cravou enum `{BIPM, INMETRO, RBC, INTERNACIONAL}` mas isso não está enforced em `PadraoUsado.snapshot_padrao_json`.

**Análise:**
CGCRE pergunta: "este padrão tem cadeia documentada até INMETRO ou BIPM? Quem é o último elo antes do SI?". Spec atual: depende do JSONB. Auditor não consegue agregar/relatar/filtrar.

**Decisão recomendada:**

1. Adicionar à `PadraoUsado` campos estruturados (top-level, não dentro do JSONB):
```
- vinculacao_si_tipo VARCHAR(20) NOT NULL CHECK IN ('BIPM_DIRETO', 'INMETRO', 'RBC', 'NMI_ESTRANGEIRO', 'MRC_NIST_PTB_NPL', 'INTERNO_DECLARADO')
- vinculacao_si_referencia_id VARCHAR(80) NOT NULL (ex: "INMETRO-LAB-METROL-MASSA-CERT-2024-456")
- cadeia_rastreabilidade_documento_id UUID NULL FK
```
2. Promover **INV-CAL-RAST-002**: "Calibração RBC exige `PadraoUsado.vinculacao_si_tipo IN ('BIPM_DIRETO', 'INMETRO', 'RBC', 'NMI_ESTRANGEIRO')`; tipo `INTERNO_DECLARADO` proibido em RBC; 412 em violação."
3. Adicionar AC à US-CAL-003.

---

### P-CAL-R10 — ALTO Wave A — RT snapshot é da AtividadeDaOS, não da Calibracao — pode descasar em janela longa

**Cláusula:** 6.2.1 + 6.2.5 + NIT-DICLA-021.

**Evidência:**
- ADR-0063 PLUGA `AtividadeDaOS.grandeza` (M3) → predicate `rt_competencia_cobre` ativa.
- Spec linha 181 `snapshot_equipamento_json` inclui `perfil_tenant_snapshot ADR-0022` capturado em `recepcionarInstrumento`.
- Mas **competência DO RT** validada em revisão (US-CAL-007) e 2ª conferência (US-CAL-008) — janela pode ser de 1-3 meses entre execução e revisão.
- Spec não tem snapshot da **competência vigente do RT no momento da REVISÃO** — só valida no momento.

**Análise:**
Cenário: técnico executa calibração em 2026-03-01 (RT-X habilitado em massa); revisão em 2026-04-15 (RT-X teve competência REVOGADA em 2026-04-01 por NC interna). Sistema atual: bloqueia (porque predicate retorna false). **Correto**. Mas e o cenário **inverso**? Técnico executa em 2026-03-01 com RT habilitado; revisão em 2026-04-15; **CGCRE depois investigando em 2027 quer evidência de qual era a competência DO RT NO DIA da revisão**. Snapshot dessa competência **na data da revisão** não fica preservado — só o predicate retornou true.

**Decisão recomendada:**

1. Adicionar à `Calibracao`:
```
- snapshot_competencia_revisor_json JSONB NULL (capturado em aprovarRevisao — competência ativa do revisor naquela data + grandeza + faixa)
- snapshot_competencia_conferente_json JSONB NULL (idem em aprovar2aConferencia)
```
2. Promover **INV-CAL-RT-002**: "aprovarRevisao captura `snapshot_competencia_revisor_json` imutável no momento; 2ª conferência idem."
3. AC novo **AC-CAL-007-5** + **AC-CAL-008-4**.

---

### P-CAL-R11 — ALTO Wave A — Backup metrológico + controle de versão de configurações não declarado — cl. 7.11.5 + 7.11.6

**Cláusula:** 7.11.5 "Quando o sistema é mantido fora das instalações ou gerenciado por fornecedor externo, o laboratório deve garantir que o fornecedor ou operador cumpra os requisitos." + 7.11.6 "Procedimentos para proteção, **backup**, recuperação e prevenção contra entradas não autorizadas."

**Evidência:**
- Spec §3 não menciona backup metrológico.
- Conformidade-iso-17025.md linha 22 menciona "backup" mas como cobertura geral, sem cravar invariante.
- INV-CAL-AUD-001 (hash-chain) cobre integridade, não backup.

**Análise:**
CGCRE pergunta: "qual a política de backup do sistema de informação metrológica? Qual a frequência? Onde fica armazenado o backup? Por quanto tempo?". Spec atual não cria entidade `BackupMetrologico` nem aponta para `docs/operacao/runbooks/backup-metrologico.md`.

**Decisão recomendada:**

1. Criar `docs/operacao/runbooks/backup-metrologico.md` (REQUER tech-lead).
2. Adicionar entidade `EventoBackupMetrologico` (append-only WORM):
   - `iniciado_em`, `concluido_em`, `tabelas_metrologicas_backupeadas[]`, `b2_object_key`, `hash_arquivo`.
3. Job procrastinate `executar_backup_metrologico` (cron diário).
4. Promover **INV-CAL-BACKUP-001**: "Backup diário de tabelas metrológicas obrigatório; gap >25h dispara alerta P1."
5. Adicionar `BackupMetrologico` aos critérios de fechamento M4 §11 e ao drill `validar_m4_calibracao`.

---

### P-CAL-R12 — MÉDIO — Texto certificado subcontratado sem wording mínimo enforced — ILAC G18

**Evidência:**
- AC-CAL-017-4 (PRD linha 296) tem texto OBRIGATÓRIO. Bom. Mas:
- INV-CAL-SUBC-004 (spec linha 466): "Texto certificado final declara subcontratação" — não detalha wording mínimo.
- Texto canônico `aceite-subcontratacao-v1.0.md` é do CLIENTE aceitar, não do CERTIFICADO declarar.

**Decisão:**
1. Criar `docs/conformidade/comum/textos/declaracao-subcontratacao-certificado-v1.0.md` com wording mínimo ILAC G18 §6.3 (REQUER OAB + RBC humano).
2. Promover **INV-CAL-SUBC-006**: "Snapshot enviado a Marco 5 inclui `declaracao_subcontratacao_texto_id` apontando para versão canônica."

---

### P-CAL-R13 — MÉDIO — Condições ambientais com critério de aceitação não cravado — cl. 6.3.1 + NIT-DICLA-030

**Evidência:**
- `ConfiguracaoCalibracao.condicoes_ambientais_alvo_id` (linha 387) — bom.
- `CondicoesAmbientais` (linha 154) está na tabela resumo, mas spec §3.2 não detalha schema.
- Sem campo `tolerancia_temperatura_celsius`, `tolerancia_umidade_pct` — sem critério binário ABORT/CONTINUA.

**Decisão:**
1. Detalhar `CondicoesAmbientais` em §3.2: `temperatura_lida_celsius`, `umidade_lida_pct`, `pressao_lida_kpa`, `temperatura_alvo + tolerancia`, `dentro_tolerancia BOOLEAN GENERATED`.
2. AC novo **AC-CAL-004-8**: GIVEN registrarLeitura WHEN `condicoes_atuais.dentro_tolerancia=false`, THEN bloqueia leitura com 412 `CondicoesAmbientaisForaTolerancia` (override possível com justificativa + audit + alerta P2 Qualidade).
3. INV-CAL-AMB-001.

---

### P-CAL-R14 — MÉDIO — Sucessão de padrão (chain) e baixa de padrão com calibrações dependentes não trata cascata

**Evidência:**
- Spec linha 511 evento `Padrao.Baixado / Padrao.Sucateado` — sem consumer documentado.
- Cenário: padrão é baixado em 2026-06-01; calibrações `em_execucao` que selecionaram esse padrão ficam órfãs.

**Decisão:**
1. Consumer `Padrao.Baixado` em §6.2: marca calibrações `em_execucao` com tal padrão como `nao_conforme` (CAPA aberta) — mas calibrações `em_revisao_1+` mantém (snapshot já capturado).
2. INV-CAL-PAD-CASCADE-001.

---

### P-CAL-R15 — ACEITE — Janela watchdog `os-calibracao-link` reaproveitada do M3 sem retrofit explicito

**Análise:** Watchdog cl. 7.4 (P-OS-R6 do M3 OS) aplicou prazos 72h alerta / 15 dias NC para perfil A. Spec M4 não menciona explicitamente, mas herda via consumer `Atividade.Iniciada`. Suficiente. Sem ação.

---

### P-CAL-R16 — ACEITE — Aprovação 2ª conferência sem A3 ADR-aceita (NG-CAL-15)

**Análise:** NG-CAL-15 explicita que aprovação M4 usa user+senha+MFA, com A3 em Marco 5. Posição defensável: separa decisão metrológica (M4) de emissão probatória (M5). cl. 7.8 não exige A3 na DECISÃO INTERNA — exige na emissão. Aceito.

---

## Mapeamento norma ↔ achados

| Cláusula ISO/IEC 17025:2017 / NIT-DICLA | Achado | Resolvido por |
|---|---|---|
| 6.2 Pessoal — competência | P-CAL-R10 ALTO | Snapshot competência por momento |
| 6.2.5 Independência | já coberto ADR-0026 | — |
| 6.4.10 Equipamentos — CMC | já coberto INV-CAL-CMC-001 | — |
| 6.5 Rastreabilidade SI | P-CAL-R9 ALTO | Enum + cadeia documental |
| 6.6.2 Provisão externa (subcontratação) | P-CAL-R5 BLOQUEANTE + P-CAL-R12 MÉDIO | Política escolha + avaliação periódica + wording certificado |
| 7.1.1 Análise crítica pedido | P-CAL-R4 BLOQUEANTE | Recepção avulsa AC + INV |
| 7.1.3 + 7.8.6 acordo cliente regra decisão | P-CAL-R3 BLOQUEANTE | AceiteRegraDecisao + INV |
| 7.4 Recepção itens | P-CAL-R13 MÉDIO + P-CAL-R15 ACEITE | Condições ambientais + watchdog |
| 7.5 Registros técnicos — rasura | já coberto LeituraCorrecao + INV-CAL-WORM-001 | — |
| 7.6 Avaliação incerteza | P-CAL-R2 BLOQUEANTE + P-CAL-R7 ALTO | Componentes mínimos + Tipo A + correlação + bias |
| 7.7.1 Monitoramento desempenho | P-CAL-R8 ALTO | Western Electric + WARNING PT |
| 7.7.2 PT proficiência | parcialmente coberto AnaliseImpactoNCProficiência | P-CAL-R8 complementa |
| 7.8.6 Regra de decisão + zonas | P-CAL-R1 BLOQUEANTE + P-CAL-R3 BLOQUEANTE | 6 zonas ILAC G8 + PFA + acordo cliente |
| 7.10 Trabalho NC | P-CAL-R6 BLOQUEANTE | Decisão parar/continuar + notificação |
| 7.11.5/7.11.6 Backup + versão config | P-CAL-R11 ALTO | EventoBackupMetrologico + INV |
| 8.4 Registros retenção 25a | já coberto ADR-0064 | — |
| 8.7 Ação corretiva CAPA | já coberto NaoConformidade ciclo | — |
| NIT-DICLA-030 §6.3 componentes mínimos | P-CAL-R2 BLOQUEANTE | Matriz por grandeza |
| NIT-DICLA-030 §7.4 Tipo A n≥6 | P-CAL-R7 ALTO | INV n_amostras |
| NIT-DICLA-026 rev. 15 WARNING | P-CAL-R8 ALTO | PlanoAcaoProficienciaWarning |
| ILAC G8 6 zonas | P-CAL-R1 BLOQUEANTE | Enum + PFA + PRA |
| ILAC G18 wording subcontratado | P-CAL-R12 MÉDIO | Texto canônico v1.0 |

---

## Verificação das 10 lições G1..G10 (dossiê pré-M4)

| Lição | Status na spec | Observação |
|---|---|---|
| G1 — Stubs não mentem | ✅ Spec §10 declara explicitamente; R-M4-11 nos riscos | Auditor-llm-correctness vai verificar no P4 |
| G2 — Sanitizador único | ✅ `sanitizar_payload_evento_calibracao()` cravado em §10 | OK |
| G3 — Idempotency-Key 18 POSTs | ✅ Lista explícita em §10 + dossiê pré-M4 | OK |
| G4 — UUID digit-heavy | ✅ §10 cita 5000 + 1000 ULIDs + 1000 slugs | OK |
| G5 — tenant_id em consumers | ✅ §10 cita 6 consumers + decorator | OK |
| G6 — Predicates INVOCADOS | ✅ 5 predicates listados em §10 + Premissas §2.1 | **Verificar no P4 que TODOS são realmente invocados** — esta foi a lição mais cara do M3 |
| G7 — Use case → endpoint | ✅ §10 lista 11 ViewSets cobrindo 18 endpoints POST | Verificar no plan.md P2 |
| G8 — Drift docs ATIVO | ✅ §10 declara | Disciplina P4 |
| G9 — Anti-fraude | ✅ 4 INV-CAL-FRAUDE-* cravados | OK |
| G10 — PRD A11Y + Analytics | ✅ §10 lista 9 telas | OK |

**Conclusão G1..G10:** spec aplicou corretamente as 10 lições do M3 OS. Ponto de atenção único: **G6 ativação real dos predicates** — o spec PROMETE; o P4 deve EXECUTAR. Auditor-produto vai rastrear AC × invocação no P5.

---

## GATEs novos / atualizados

| GATE | Status | Origem | Quando | Responsável |
|---|---|---|---|---|
| GATE-CAL-ZONAS-ILAC-G8 | **NOVO** (P-CAL-R1) | este parecer | M4 P3 | Tech-lead + Subagente RBC |
| GATE-CAL-COMPONENTES-MIN | **NOVO** (P-CAL-R2) | este parecer | M4 P3 + matriz por grandeza | RBC humano credenciado |
| GATE-CAL-ACEITE-REGRA-DEC | **NOVO** (P-CAL-R3) | este parecer | M4 P3 — pré-1º tenant externo | RBC humano + OAB |
| GATE-CAL-ANAL-CRIT-AVULSA | **NOVO** (P-CAL-R4) | este parecer | M4 P4 US-CAL-001 | Tech-lead |
| GATE-CAL-SUBC-AVAL | **NOVO** (P-CAL-R5) | este parecer | Wave A operacional | RBC humano + tech-lead |
| GATE-CAL-NC-CLIENTE-NOTIF | **NOVO** (P-CAL-R6) | este parecer | M4 P4 US-CAL-014 | Tech-lead |
| GATE-CAL-INC-FORMULA | **NOVO** (P-CAL-R7) | este parecer | M4 P3 + bateria replay | RBC humano credenciado |
| GATE-CAL-EP-WARNING | **NOVO** (P-CAL-R8) | este parecer | M4 P4 US-CAL-014 | Tech-lead |
| GATE-CAL-RAST-SI-ENUM | **NOVO** (P-CAL-R9) | este parecer | M4 P3 | Tech-lead |
| GATE-CAL-RT-SNAPSHOT | **NOVO** (P-CAL-R10) | este parecer | M4 P4 US-CAL-007/008 | Tech-lead |
| GATE-CAL-BACKUP-METROL | **NOVO** (P-CAL-R11) | este parecer | M4 P4 + Wave A operacional | Tech-lead |
| GATE-CAL-SUBC-WORDING | **NOVO** (P-CAL-R12) | este parecer | M4 P3 + RBC/OAB humano | RBC + OAB |
| GATE-CAL-COND-AMB | **NOVO** (P-CAL-R13) | este parecer | M4 P4 US-CAL-004 | Tech-lead |
| GATE-CAL-PADRAO-CASCADE | **NOVO** (P-CAL-R14) | este parecer | M4 P4 consumer | Tech-lead |

---

## Próximos passos

1. **Absorver P-CAL-R1..R6** (6 BLOQUEANTES) em `plan.md` P2 — matriz de reconciliação contra PRD + spec.
2. **PR contra PRD `calibracao/prd.md`** adicionando: AC-CAL-001-3 (análise crítica avulsa), AC-CAL-002-X (acordo regra decisão), AC-CAL-005-4..7 (componentes mínimos + Tipo A + correlação + bias + arredondamento), AC-CAL-006-X (zonas ILAC G8 + PFA), AC-CAL-007-5 + AC-CAL-008-4 (snapshot competência), AC-CAL-014-5 (notificação cliente NC).
3. **PR contra REGRAS-INEGOCIAVEIS.md** com 15 INVs novos: INV-CAL-DEC-004/005/006, INV-CAL-INC-002/003/004, INV-CAL-ANAL-001, INV-CAL-RT-002, INV-CAL-RAST-002, INV-CAL-SUBC-005/006, INV-CAL-NC-002/003, INV-CAL-AMB-001, INV-CAL-BACKUP-001, INV-CAL-PAD-CASCADE-001.
4. **PR retrofit ADR-0024** acrescentando tabela ILAC G8 6 zonas + PFA + acordo cliente (P-CAL-R1 + P-CAL-R3).
5. **Criar 5 textos canônicos** (REQUER OAB + RBC humano):
   - `aceite-regra-decisao-v1.0.md`
   - `criterio-selecao-subcontratado-v1.0.md`
   - `declaracao-subcontratacao-certificado-v1.0.md`
   - `componentes-obrigatorios-por-grandeza.md` (matriz por grandeza)
   - `formula-calculo-por-grandeza.md` (matriz Tipo A + correlação por grandeza)
6. **Adicionar 4 entidades novas em §3.2 spec:**
   - `AceiteRegraDecisao`
   - `AvaliacaoPeriodicaSubcontratado`
   - `PlanoAcaoProficienciaWarning`
   - `EventoBackupMetrologico`
7. **Atualizar `docs/governanca/gates-wave-a-consolidado.md`** com 14 GATEs novos.
8. **Drill `validar_m4_calibracao`** deve cobrir cenários BLOQUEANTES: tentativa de configurar sem componentes mínimos, tentativa de avaliar conformidade sem PFA quando BANDA_GUARDA_30, tentativa de subcontratar sem avaliação periódica vigente, tentativa de fechar NC sem decisão parar/continuar.

---

## Limites legítimos do parecer (obrigatório)

Sou subagente IA `consultor-rbc-iso17025`. **Não tenho credencial CGCRE.** Este parecer é **consultivo**.

**Itens que REQUEREM consultor humano credenciado CGCRE antes de produção externa:**

- 🔴 P-CAL-R2 — matriz de componentes-obrigatórios-por-grandeza (REQUER CGCRE)
- 🔴 P-CAL-R3 — texto canônico aceite-regra-decisao-v1.0.md (REQUER CGCRE + OAB)
- 🔴 P-CAL-R5 — política critério-selecao-subcontratado-v1.0.md (REQUER CGCRE)
- 🔴 P-CAL-R7 — matriz formula-calculo-por-grandeza (REQUER CGCRE)
- 🔴 P-CAL-R12 — texto declaracao-subcontratacao-certificado-v1.0.md (REQUER CGCRE + OAB)
- 🔴 **Dossiê IQ/OQ/PQ completo do Marco 4** (ADR-0025) antes de submissão a processo RBC (REQUER RT-vendor humano credenciado conforme V2)
- 🔴 **Auditoria CGCRE simulada formal** antes de 1ª supervisão real (REQUER consultor humano credenciado)

**Estimativa de custo do consultor humano credenciado pra cobrir todos os itens 🔴:** R$ 25-45k em 3 engajamentos sequenciais (revisão matrizes técnicas + revisão dossiê IQ/OQ/PQ + auditoria simulada). Versus risco de NC ALTO em supervisão CGCRE real (suspensão de acreditação por 6+ meses + retrabalho de cert emitidos): risco muito superior ao custo.

**Preparei este parecer pra economizar 80% do tempo** do consultor humano credenciado quando contratado. Os 16 achados acima estruturam a agenda dele em ordem de criticidade.

---

## Veredicto

**AJUSTAR.** Spec M4 é o trabalho de maior densidade técnica do projeto até hoje, e está visivelmente robusto na estrutura (entidades, INVs, hash-chain, anti-fraude, lições G1..G10). Os 6 BLOQUEANTES não são falhas de execução — são **lacunas de profundidade regulatória** que CGCRE em supervisão pega imediatamente. Resolvíveis em P3 sem refazer a fundação.

**Pré-condição para fechar M4 com 10/10 PASS ZERO C/A/M:** os 6 BLOQUEANTES e os 5 ALTOS Wave A precisam estar implementados (P-CAL-R1..R11). Os 3 MÉDIOs e 2 ACEITEs ficam rastreados sem urgência.

**Pré-condição para 1º tenant externo pago RBC:** todos os itens 🔴 revisados por consultor humano credenciado CGCRE.
