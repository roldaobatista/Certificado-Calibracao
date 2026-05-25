---
owner: roldao
revisado_em: 2026-05-25
proximo_review: 2026-08-25
status: draft
diataxis: reference
audiencia: agente
marco: Wave A Marco 4 — metrologia/calibracao
tipo: especificacao-forward
relacionados:
  - .specify/memory/constitution.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/dominios/metrologia/modulos/calibracao/modelo-de-dominio.md
  - docs/dominios/metrologia/modulos/calibracao/personas.md
  - docs/dominios/metrologia/modulos/calibracao/metricas.md
  - docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md
  - docs/dominios/metrologia/modulos/calibracao/validacao-software.md
  - docs/dominios/metrologia/modulos/calibracao/responsabilidade-tecnica.md
  - docs/dominios/metrologia/modulos/calibracao/registros-tecnicos-7.5.md
  - docs/dominios/metrologia/modulos/calibracao/garantia-validade-7.7.md
  - docs/dominios/metrologia/modulos/calibracao/controle-certificado-emitido.md
  - docs/dominios/metrologia/modulos/calibracao/politica-verificacao-intermediaria.md
  - docs/dominios/metrologia/modulos/calibracao/glossario.md
  - docs/faseamento/M1-clientes/spec.md
  - docs/faseamento/M2-equipamentos/spec.md
  - docs/faseamento/M3-os/spec.md
  - docs/faseamento/auditorias/PRE-M4-CALIBRACAO-saneamento.md
  - docs/faseamento/auditorias/OS-CAL-CONSOLIDADO-rodada-1.md
  - docs/faseamento/auditorias/OS-CAL-CONSOLIDADO-rodada-2.md
  - docs/faseamento/auditorias/OS-CAL-RESOLUCAO-rodada-2.md
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - docs/adr/0012-autorizacao-unificada.md
  - docs/adr/0021-anonimizacao-vs-retencao.md
  - docs/adr/0022-rt-tenant.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0024-regra-de-decisao-iso-17025.md
  - docs/adr/0025-validacao-software-iso-17025.md
  - docs/adr/0026-segunda-conferencia-independencia.md
  - docs/adr/0027-sync-mobile-merge-atividade.md
  - docs/adr/0029-canonicalizacao-texto-probatorio.md
  - docs/adr/0030-vigencia-temporal-canonica.md
  - docs/adr/0031-soft-delete-tres-padroes.md
  - docs/adr/0032-fk-cross-modulo-anonimizacao.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0040-padrao-metrologico-entidade-separada.md
  - docs/adr/0063-rt-competencia-grandeza-diferida-marco4.md
  - docs/adr/0064-rotacao-chave-hmac-retencao-metrologica-25a.md
  - REGRAS-INEGOCIAVEIS.md
---

# Wave A — Marco 4 (`metrologia/calibracao`) — Especificação (forward, autoritativa)

> **O que este documento é (Constituição §1, §2):** a fonte da verdade do que o Marco 4 `calibracao` **deve fazer**. Spec-as-source: o código é derivado/validado contra esta spec. Onde código divergir (após revisão dos 4 subagentes em P2), **o código é corrigido**, não a spec.
>
> **Por que existe (decisão Roldão 2026-05-25):** Marco 3 OS fechou via ritual Spec Kit (10/10 auditores Família 5 PASS ZERO C/A/M). Saneamento pré-Marco 4 concluído (ADR-0040 + ADR-0064 aceitas, US-CAL-017 adicionada, drift AGENTS zerado). Dossiê `PRE-M4-CALIBRACAO-saneamento.md` cataloga 10 lições G1..G10 do M3 OS que **ESTE marco aplica desde a 1ª linha de código**.
>
> **Pra Roldão (uma frase):** este é o "contrato" do módulo de calibração metrológica — o coração técnico do produto. Recebe instrumento do cliente, configura calibração com padrões rastreáveis, registra leituras com rasura digital (cl. 7.5), calcula erro + incerteza orçada componente-a-componente (GUM), avalia conformidade com regra de decisão (ILAC G8 / cl. 7.8.6), passa por revisão técnica + 2ª conferência independente (cl. 6.2.5), publica decisão APROVADO/REPROVADO/CONDICIONAL para o módulo Certificados (Marco 5) emitir o PDF.

---

## 1. Escopo

CRUD completo da entidade `Calibracao` (raiz de agregado) acoplada a `AtividadeDaOS` (ADR-0023) ou a recepção avulsa; máquina de estados ISO 17025 com 10 estados terminais e intermediários; orçamento de incerteza ponto-a-ponto (NIT-DICLA-030 rev. 15) com `ComponenteIncerteza` 1:N + `OrcamentoPorPonto` 1:N; regra de decisão configurável (ADR-0024 — 3 modos + override por cliente + lock pós-emissão); revisão técnica + 2ª conferência independente (ADR-0026 — política exceção 4 condições + 5%/mês); rastreabilidade ao padrão via snapshot imutável (ADR-0040 — `PadraoUsado` com snapshot_capturado_at + lock pós-revisão); rasura digital de leitura (cl. 7.5 — `LeituraCorrecao` preserva original); ciclo CAPA fechado (cl. 7.10/8.7 — `NaoConformidade` com causa-raiz + ação corretiva + eficácia); validação de software (ADR-0025 — versão motor cálculo + replay determinístico + 2º caminho); subcontratação cl. 6.6 (US-CAL-017 — `LaboratorioSubcontratado` + `AceiteSubcontratacao`); ensaios complementares (linearidade, repetibilidade, excentricidade); verificação intermediária + comparação interlaboratorial + proficiência (cl. 7.7); escopo de acreditação + CMC binding (cl. 6.4.10); rotação HMAC anual com retenção 25a (ADR-0064 — INV-HMAC-001..005).

### Non-goals explícitos (Constituição §5 — proibição positiva)

Marco 4 `calibracao` **NÃO** entrega, e nenhum agente deve inferir que entrega:

- **NG-CAL-1**: emissão do certificado PDF — fica em `metrologia/certificados` (Marco 5).
- **NG-CAL-2**: NF-e/NFS-e — fica em `financeiro/fiscal` (Wave A).
- **NG-CAL-3**: gestão da acreditação CGCRE da empresa — fica em `metrologia/licencas-acreditacoes`.
- **NG-CAL-4**: manutenção do instrumento — fica em `operacao/os` (atividade tipo=manutenção; pode disparar OS de manutenção quando reprovado).
- **NG-CAL-5**: substituir planilha Excel pra cálculos exploratórios em P&D — é produção; cálculo exploratório fica em planilha externa.
- **NG-CAL-6**: customização do motor de cálculo de incerteza por tenant — único motor versionado (INV-CAL-VERSAO-001); customização exigiria ADR específica + validação ISO 17025 cl. 7.11.
- **NG-CAL-7**: aceitar leitura sem padrão associado — leitura órfã proibida (INV-CAL-RAST-001).
- **NG-CAL-8**: bypass de 2ª conferência sem ADR-0026 4 condições cumulativas — exceção objetiva, não discricionária.
- **NG-CAL-9**: recall/suspensão/errata de certificado emitido — fica em Marco 5 (ADR-0045).
- **NG-CAL-10**: integração com instrumento via Bluetooth/MQTT/WiFi — MVP-1 só Serial/USB (US-CAL-004).
- **NG-CAL-11**: ML/IA pra prever drift do instrumento — Wave B (analytics).
- **NG-CAL-12**: OCR de certificado externo de padrão — manual em US-CAL-011 MVP-1.
- **NG-CAL-13**: sub-subcontratação (subcontratado terceiriza pra outro) — non-goal Wave A US-CAL-017.
- **NG-CAL-14**: app nativo mobile pra registrar leitura — operação web na 1ª fase; calibração de campo via app técnico Marco 3 entrega só atividade tipo=calibracao_campo (não confundir com US-CAL-004 manual no laboratório).
- **NG-CAL-15**: assinatura A3 do RT na aprovação (cl. 7.8 + ICP-Brasil) — Marco 5 cert emissão usa A3; Marco 4 RT aprova com user+senha+MFA (predicate `aprovacao_2a_conferencia_autorizada`).

---

## 2. Premissas (ADRs, VOs, hooks já em vigor)

### 2.1 ADRs estruturais aceitas que governam o Marco 4

| ADR | Tema | Aplicação no M4 |
|---|---|---|
| 0002 | Multi-tenancy (RLS + middleware) | Toda tabela do M4 leva `tenant_id` + policy RLS (INV-TENANT-001..003) |
| 0007 | Camada domínio + gerador spec→código | Entidades do M4 ficam em `src/domain/metrologia/calibracao/` |
| 0012 | Autorização unificada | Predicates novos: `pode_configurar_calibracao`, `pode_registrar_leitura`, `pode_corrigir_leitura`, `pode_aprovar_revisao`, `pode_aprovar_2a_conferencia`, `pode_marcar_nc_calibracao`, `pode_subcontratar`, `cmc_cobre`, `padrao_vigente_no_uso`, `procedimento_vigente_para`, `regra_decisao_aplicavel` |
| 0021 | Anonimização vs retenção | Calibração preserva `cliente_referencia_hash` quando cliente anonimizado (Zona B); WORM metrológico 25a > LGPD eliminação |
| 0022 | RT tenant | Predicate `rt_competencia_cobre(grandeza)` ATIVADO em M4 (ADR-0063 — fail-open M3 fecha) |
| 0023 | OS com Atividades | `Calibracao.atividade_os_id` FK opcional (recepção avulsa permite NULL) |
| 0024 | Regra de decisão ISO 17025 cl. 7.8.6 | 3 modos (ACEITACAO_SIMPLES, BANDA_GUARDA_30, RISCO_COMPARTILHADO) + override por cliente + lock pós-emissão |
| 0025 | Validação de software ISO 17025 cl. 7.11 | URS/IQ/OQ/PQ documentado + replay determinístico + 2º caminho de cálculo + INV-CAL-VERSAO-001 |
| 0026 | 2ª conferência + independência RT | Política exceção 4 condições cumulativas + 5%/mês limite + 412 `Excecao62_5InaceitavelSemCondicoes` |
| 0027 | Sync mobile merge por atividade | Atividade calibração de campo herda LWW + append-only (não usado em M4 core lab — só Marco 3) |
| 0029 | Canonicalização texto probatório | `NaoConformidade.descricao` + `LeituraCorrecao.razao_correcao` + `AceiteSubcontratacao.texto_canonicalizado` UTF-8 + LF + NFC + marcadores |
| 0030 | Vigência temporal canônica | `ProcedimentoCalibracao` + `Escopo` + `PadraoMetrologico` usam `JanelaVigencia` VO |
| 0031 | Soft-delete 3 padrões | Calibracao → Padrão A (estado-máquina); EventoDeCalibracao → Padrão B; ConfiguracaoCalibracao → Padrão A |
| 0032 | FK cross-módulo + anonimização | Calibração guarda `cliente_referencia_hash` + `cliente_id` nullable (ADR-0021 Zona B) |
| 0033 | Bus idempotência consumer | Consumers M4 gravam em `consumer_idempotencia` + `dead_letter_events` (INV-IDEMP-001/002) |
| 0040 | Padrão metrológico entidade separada | Módulo `padroes` distinto; `PadraoUsado` é snapshot capturado no momento da seleção; INV-PAD-001..006 |
| 0063 | RT competência diferida M4 | M4 PLUGA `AtividadeDaOS.grandeza` → predicate `rt_competencia_cobre` bloqueia automaticamente nos 3 use cases M3 fail-open |
| 0064 | Rotação HMAC + KMS Multi-Region 25a | TODO hash HMAC persistido em entidade WORM usa formato `v<NN>$<base64>`; INV-HMAC-001..005 |

### 2.2 VOs disponíveis

- `JanelaVigencia`, `ReferenciaPIIAnonimizavel`, `Dinheiro` em `src/domain/shared/value_objects.py`.
- `Grandeza`, `FaixaMedicao`, `IncertezaExpandida` em `src/domain/metrologia/value_objects.py` (já existem desde Marco 2; Marco 4 é o **consumidor canônico**).
- `RegraDecisao` (NOVO M4 P3) — enum `ACEITACAO_SIMPLES | BANDA_GUARDA_30 | RISCO_COMPARTILHADO` + helper `aplicar(spec, valor, U_expandida) → ConformidadeAvaliada(zona, decisao_sugerida)` (cl. 7.8.6 + ILAC G8).
- `VersaoMotorCalculo` (NOVO M4 P3) — semver + commit-hash + algoritmo_id + janela_vigencia; cravado por calibração em `Calibracao.versao_motor_calculo` (ADR-0025).
- `HashVersionado` (NOVO M4 P3) — string canônica `v<NN>$<base64(hmac_sha256)>` com helpers `gerar/verificar` via KMS (ADR-0064).

### 2.3 Hooks pré-commit aplicáveis

Já registrados em `.claude/settings.json` + 4 novos a criar no M4 P9:

**Herdados (já ativos):**
- `vigencia-canonica-check`, `soft-delete-padrao-check`, `fk-pii-anonimizavel-check`, `biometria-key-validator`, `frontmatter-revisado-em-check`, `spec-ac-binario-check`, `bus-envelope-validator` v10, `migration-rls-check`, `audit-immutability-check`, `bus-envelope-validator`, `authz-check` (estendido com 5 predicates M4).

**Novos M4 (P9):**
- `cmc-binding-check.sh` (INV-002 + INV-CAL-CMC-001) — bloqueia configurar calibração RBC sem CMC vigente cobrindo grandeza+faixa.
- `incerteza-versao-motor-check.sh` (INV-CAL-VERSAO-001) — bloqueia `OrcamentoIncerteza.criado_em` sem `versao_motor_calculo` cravada.
- `hmac-versao-formato-check.sh` (INV-HMAC-001) — bloqueia hash HMAC persistido em entidade WORM sem formato `v<NN>$<base64>`.
- `migration-metrology-classifier.sh` (ADR-0025 cl. 7.11.3 + GATE-CAL-MIG-CLASSIF) — bloqueia migration que toca tabela metrológica sem categorização IQ/OQ/PQ + replay test associado.

### 2.4 DPIA em minuta (aprovação OAB pendente)

`docs/conformidade/comum/dpia/dpia-calibracao.md` (a criar — `status: minuta`, `aguarda-revisao-oab: true`) — avalia:
- Foto de instrumento do cliente com NS/etiqueta visível (potencial PII vazada em metadata EXIF — strip obrigatório como M3).
- Subcontratação cl. 6.6 (DPA cl. 4.7 obrigatório com subcontratado — INV-CAL-SUBC-001).
- Geolocalização opt-in em recepção de campo (RAT-07 herdado de M3).

**Marco 4 dogfooding-only (Balanças Solution) não exige DPIA OAB-aprovada;** 1º tenant externo pago bloqueia em GATE-CAL-DPIA-OAB (§9). Subagente IA `advogado-saas-regulado` emite parecer consultivo em P2; OAB humana revalida antes de produção externa.

---

## 3. Entidades + schema sketch

### 3.1 Tabela resumo

| Entidade | Padrão soft-delete | Vigência? | FK PII? | Imutável pós-INSERT? |
|---|---|---|---|---|
| `Calibracao` | A (estado-máquina) | não | sim — `cliente_referencia_hash` | parcial (snapshots + máquina estados) |
| `ConfiguracaoCalibracao` | A (estado por revisão) | não | não | parcial (lock pós EM_EXECUCAO) |
| `Leitura` | B (raro; auditável metrologicamente) | não | sim — `executor_id_hash` HMAC | sim (cl. 7.5 — `LeituraCorrecao` substitui) |
| `LeituraCorrecao` | B (audit imutável) | não | sim — `corretor_id_hash` HMAC | sim |
| `CondicoesAmbientais` | B (snapshot WORM) | não | não | sim |
| `OrcamentoIncerteza` | B (snapshot pós-calculo) | não | não | sim (pós EM_REVISAO_1 lock) |
| `ComponenteIncerteza` | B (children imutáveis) | não | não | sim |
| `OrcamentoPorPonto` | B (children imutáveis) | não | não | sim |
| `PadraoUsado` | B (snapshot imutável) | não | não | sim (snapshot_lock pós EM_REVISAO_1) |
| `RecepcaoItemCalibracao` | B (audit cl. 7.4) | não | sim — `cliente_referencia_hash` | sim |
| `MedicaoControle` | B (WORM gráfico controle) | não | sim — `executor_id_hash` | sim |
| `EventoDeCalibracao` | B (append-only WORM) | não | sim (hash sanitizado) | sim |
| `NaoConformidade` | B (`revogado_em` raro; preserva CAPA) | não | sim — `descricao_hash` HMAC | parcial (CAPA progressivo) |
| `AnaliseImpactoNCProficiência` | B (audit imutável) | não | não | sim (decisão por cert WORM) |
| `LaboratorioSubcontratado` | C (`deletado_em` configuração) | sim — `acreditacoes_vigentes` | sim — CNPJ + contatos | não (cadastro mutável) |
| `AceiteSubcontratacao` | B (audit imutável + assinatura cliente) | não | sim — biometria/A3 cliente | sim |
| `ProcedimentoCalibracaoVigenteSnapshot` | B (snapshot em `Calibracao.procedimento_versao_snapshot`) | não | não | sim |

### 3.2 Campos principais (sketch — refinamento final em P4)

**`Calibracao`** (raiz de agregado):
- `id UUID PK`
- `tenant_id UUID NOT NULL` (RLS)
- `numero_interno BIGINT NOT NULL DEFAULT nextval('calibracao_numero_seq_global')` — sequence global PG; `UNIQUE(tenant_id, numero_interno)`; buracos aceitos (paralelo a ADR-0056 + INV-CAL-NUM-001).
- `numero_exibido VARCHAR(20)` GENERATED ALWAYS AS (`'CAL-' || EXTRACT(YEAR FROM criada_em) || '-' || LPAD(numero_interno::text, 6, '0')`) STORED
- `atividade_os_id UUID NULL FK` (`AtividadeDaOS`; NULL em recepção avulsa)
- `cliente_id UUID NULL` (FK clientes; pode ficar NULL pós-anonimização)
- `cliente_referencia_hash CHAR(80)` (HashVersionado canônico `v<NN>$<base64>` — ADR-0064)
- `cliente_key_id VARCHAR(40)`
- `instrumento_id UUID NOT NULL FK` (Equipamento — M2)
- `snapshot_equipamento_json JSONB NOT NULL` (imutável: nome, tag, NS, fabricante, modelo, `perfil_tenant_snapshot` ADR-0022 — capturado em `recepcionarInstrumento` cl. 7.4)
- `procedimento_id UUID NOT NULL FK` (`ProcedimentoCalibracao` — módulo `procedimentos`)
- `procedimento_versao_snapshot JSONB NOT NULL` (snapshot ProcedimentoCalibracaoVigenteSnapshot: codigo + versao_semver + hash_anexo_pdf — capturado em `configurarCalibracao` US-CAL-016)
- `tipo_acreditacao VARCHAR(10) NOT NULL` (RBC | NAO_RBC)
- `escopo_id UUID NULL FK` (`Escopo` — null se NAO_RBC)
- `configuracao_id UUID NULL FK` (`ConfiguracaoCalibracao`)
- `status VARCHAR(30) NOT NULL DEFAULT 'recepcionada'` (`recepcionada | configurada | em_execucao | em_revisao_1 | aguardando_2a_conferencia | aprovada | rejeitada | cancelada | nao_conforme | pendente_resolucao_nc | aguardando_subcontratado | recebida_do_subcontratado`)
- `executor_id UUID FK` (metrologista que registra leituras; valida `executor_id == request.user.id` em registrar_leitura — INV-CAL-FRAUDE-EXEC-001)
- `revisor_id UUID NULL FK` (RT 1ª conferência; valida `revisor_id == request.user.id` em aprovar_revisao — INV-CAL-FRAUDE-REV-001)
- `conferente_id UUID NULL FK` (RT 2ª conferência; valida `conferente_id == request.user.id` + `conferente_id != revisor_id` em aprovar_2a_conferencia — INV-CAL-FRAUDE-CONF-001 + ADR-0026)
- `excecao_2a_conf_id UUID NULL FK` (`Excecao2aConferencia` — populated se aplicou ADR-0026 4 condições)
- `decisao VARCHAR(15) NOT NULL DEFAULT 'NA'` (`APROVADO | REPROVADO | CONDICIONAL | NA`)
- `regra_decisao VARCHAR(25) NOT NULL` (`ACEITACAO_SIMPLES | BANDA_GUARDA_30 | RISCO_COMPARTILHADO` — ADR-0024; snapshot do que foi acordado em US-OS-001 análise crítica)
- `regra_decisao_override_cliente BOOLEAN DEFAULT false` (true se cliente requisitou override em US-CAL-002 com assinatura ADR-0029)
- `versao_motor_calculo VARCHAR(50) NOT NULL` (semver + commit-hash do motor; ADR-0025 + INV-CAL-VERSAO-001)
- `subcontratado_id UUID NULL FK` (`LaboratorioSubcontratado` — populated quando subcontrata; US-CAL-017)
- `aceite_subcontratacao_id UUID NULL FK` (`AceiteSubcontratacao` — NOT NULL quando subcontratado_id NOT NULL; INV-CAL-SUBC-001)
- `certificado_subcontratado_snapshot_json JSONB NULL` (imutável; cravado em `registrarRecebimentoSubcontratado`)
- `observacoes_gerais TEXT NULL` (≤500 chars + anti-PII INV-CAL-TXT-001)
- `motivo_cancelamento_hash CHAR(80) NULL` (HashVersionado — quando status='cancelada')
- `correlation_id UUID NOT NULL` (cadeia forense — NOVO-ALTO-1 Onda 7B retrofit M3 + paralelo M4)
- `causation_id UUID NULL` (FK calibracao_id que originou — reprocessamento)
- `criada_em / atualizada_em TIMESTAMPTZ`
- `criada_por_user_id UUID`
- **INVs:** INV-002 (CMC), INV-003 (rastreabilidade), INV-CAL-VERSAO-001, INV-CAL-CONF-001 (2ª conferência obrigatória — promovida 2026-05-23 Onda 7A), INV-CAL-RT-001 (RT habilitado por grandeza — ADR-0022 + ADR-0063), INV-CAL-RT-COMP-001 (snapshot retroativo bloqueado), INV-CAL-WORM-001, INV-CAL-TXT-001, INV-CAL-AUD-001, INV-TENANT-001, INV-OS-ATIV-002 (herança tenant quando atividade_os_id NOT NULL).

**`Leitura`** (cl. 7.5 — imutável):
- `id UUID PK`
- `tenant_id UUID NOT NULL` (RLS)
- `calibracao_id UUID NOT NULL FK`
- `ponto_calibracao NUMERIC(20,8) NOT NULL` (valor do ponto)
- `numero_repeticao INTEGER NOT NULL`
- `valor_lido NUMERIC(20,8) NOT NULL`
- `unidade VARCHAR(20) NOT NULL`
- `origem VARCHAR(20) NOT NULL` (`MANUAL | INTEGRACAO_SERIAL | INTEGRACAO_USB`)
- `timestamp TIMESTAMPTZ NOT NULL`
- `executor_id_hash CHAR(80) NOT NULL` (HashVersionado — ADR-0064 + TEMA-C.12)
- `client_event_id UUID NULL` (sync calibração de campo via app — ADR-0027; null se laboratório)
- `correlation_id UUID NOT NULL`
- **Trigger:** bloqueia UPDATE/DELETE pós-INSERT (`audit-immutability-check`). Correções pré-aprovação via `LeituraCorrecao` (cl. 7.5 rasura digital — TEMA-B.3 Onda 7B).
- **Idempotência:** UNIQUE(`tenant_id`, `calibracao_id`, `client_event_id`) quando `client_event_id NOT NULL`.

**`LeituraCorrecao`** (cl. 7.5 — rasura digital):
- `id UUID PK`
- `tenant_id UUID NOT NULL`
- `leitura_id UUID NOT NULL FK` (preserva valor_original — não muta a Leitura)
- `valor_original NUMERIC(20,8) NOT NULL` (snapshot do valor antes da correção)
- `valor_corrigido NUMERIC(20,8) NOT NULL`
- `razao_correcao TEXT NOT NULL` (≥30 chars + anti-PII INV-CAL-TXT-001 + canonicalização INV-DOC-CANON-001)
- `razao_correcao_canonicalizada TEXT NOT NULL` (UTF-8 + LF + NFC + marcadores `<<<CORPO INICIO/FIM>>>`)
- `razao_correcao_hash CHAR(80) NOT NULL` (HashVersionado — ADR-0064)
- `corretor_id_hash CHAR(80) NOT NULL` (HashVersionado)
- `corretor_user_id UUID NOT NULL` (validação INV-CAL-FRAUDE-COR-001: `corretor_user_id == request.user.id`)
- `corrigido_em TIMESTAMPTZ NOT NULL`
- `correlation_id UUID NOT NULL`
- **AC-CAL-004-7:** `corrigirLeitura` só permitido quando `calibracao.status IN ('CONFIGURADA', 'EM_EXECUCAO')`. Após `EM_REVISAO_1` correção exige reabertura formal via CAPA (gera `NaoConformidade`).
- **Trigger:** UPDATE/DELETE bloqueado pós-INSERT.

**`OrcamentoIncerteza`** (cl. 7.6 — orçamento ponto-a-ponto NIT-DICLA-030 rev. 15):
- `id UUID PK`
- `tenant_id UUID NOT NULL`
- `calibracao_id UUID NOT NULL FK`
- `u_combinada NUMERIC(20,8) NOT NULL` (consolidada — pior caso da faixa quando OrcamentoPorPonto existe; constante quando aplicável)
- `documentacao_agregacao TEXT NOT NULL` (≥50 chars — INV-CAL-INC-001 NOVO-3 RBC R2 — quando `OrcamentoPorPonto[]` existe, declara como `u_combinada` agregada)
- `grau_liberdade_efetivo NUMERIC(10,2) NOT NULL` (Welch-Satterthwaite)
- `k NUMERIC(5,2) NOT NULL DEFAULT 2.0` (fator de abrangência)
- `U_expandida NUMERIC(20,8) NOT NULL` (`= u_combinada * k`)
- `nivel_confianca NUMERIC(5,3) NOT NULL DEFAULT 0.9545` (95.45%)
- `versao_motor_calculo VARCHAR(50) NOT NULL` (snapshot herdado de Calibracao — INV-CAL-VERSAO-001)
- `replay_determinismo_hash CHAR(80) NOT NULL` (HashVersionado dos inputs + outputs — ADR-0025 cl. 7.11 replay determinístico)
- `segundo_caminho_calculo_valor NUMERIC(20,8) NULL` (ADR-0025 — quando 2º caminho aplicável)
- `segundo_caminho_calculo_divergencia_pct NUMERIC(5,3) NULL` (alerta P3 se > 0.1%; bloqueia se > 1%)
- `calculado_em TIMESTAMPTZ NOT NULL`
- `correlation_id UUID NOT NULL`
- **Relação 1:N com `ComponenteIncerteza`** (substituiu `componentes_json` JSONB).
- **Relação 1:N com `OrcamentoPorPonto`** (incerteza por ponto).
- **Invariantes:** INV-004 (GUM), INV-CAL-VERSAO-001, INV-CAL-INC-001, INV-CAL-WORM-001.
- **Trigger:** lock pós-EM_REVISAO_1 (não pode recalcular sem reabrir calibração).

**`ComponenteIncerteza`** (1:N de OrcamentoIncerteza):
- `id UUID PK`, `tenant_id UUID NOT NULL`, `orcamento_incerteza_id UUID NOT NULL FK`
- `nome_componente VARCHAR(80) NOT NULL` (ex: "Resolução do indicador", "Repetibilidade", "Deriva do padrão")
- `tipo_componente VARCHAR(1) NOT NULL` (`A` | `B`)
- `distribuicao VARCHAR(20) NOT NULL` (`NORMAL` | `RETANGULAR` | `TRIANGULAR` | `U` | `OUTRA`)
- `divisor NUMERIC(15,5) NOT NULL` (sqrt(3), sqrt(6), etc.)
- `valor_estimativa NUMERIC(20,8) NOT NULL`
- `contribuicao NUMERIC(20,8) NOT NULL`
- `grau_liberdade NUMERIC(10,2) NOT NULL DEFAULT 50.0`
- `fonte_default_padrao_id UUID NULL FK` (`PadraoMetrologico` — Tipo B vem de defaults configuráveis por padrão+grandeza; AC-CAL-005-2)
- **Imutável pós-INSERT.**

**`OrcamentoPorPonto`** (1:N de OrcamentoIncerteza):
- `id UUID PK`, `tenant_id UUID NOT NULL`, `orcamento_incerteza_id UUID NOT NULL FK`
- `ponto_calibracao NUMERIC(20,8) NOT NULL`
- `u_combinada_no_ponto NUMERIC(20,8) NOT NULL`
- `U_expandida_no_ponto NUMERIC(20,8) NOT NULL`
- `k_no_ponto NUMERIC(5,2) NOT NULL DEFAULT 2.0`
- **Imutável pós-INSERT.**

**`PadraoUsado`** (snapshot — ADR-0040 + TEMA-B.1 Onda 7B):
- `id UUID PK`, `tenant_id UUID NOT NULL`, `calibracao_id UUID NOT NULL FK`
- `padrao_id UUID NOT NULL FK` (`PadraoMetrologico` — módulo `padroes` separado)
- `padrao_id_hash CHAR(80) NOT NULL` (HashVersionado — proteção cross-tenant + ADR-0064)
- `snapshot_padrao_json JSONB NOT NULL` (imutável: cert externo, validade, classe, valor convencional, incertezas_certificado, vinculacao SI)
- `snapshot_capturado_at TIMESTAMPTZ NOT NULL` (TEMA-B.1 — momento em que snapshot foi tirado, não retroativo)
- `snapshot_lock BOOLEAN NOT NULL DEFAULT false` (true quando `calibracao.status >= 'em_revisao_1'`)
- **INV-CAL-RT-COMP-001:** snapshot só pode ser feito enquanto `calibracao.status IN ('recepcionada', 'configurada')`; após `em_revisao_1` snapshot_lock=true e qualquer tentativa de INSERT em PadraoUsado é bloqueada (trigger).
- **INV-PAD-003:** `padrao.estado IN ('EM_RECAL_EXTERNO', 'BAIXADO', 'SUCATEADO')` bloqueia uso (predicate `padrao_vigente_no_uso`).
- **INV-PAD-004:** `padrao.validade_certificado_rastreabilidade < snapshot_capturado_at` bloqueia uso (paralelo INV-011).

**`RecepcaoItemCalibracao`** (cl. 7.4 — TEMA-B.4 Onda 7B):
- `id UUID PK`, `tenant_id UUID NOT NULL`, `calibracao_id UUID NOT NULL FK`
- `cliente_referencia_hash CHAR(80) NOT NULL`
- `instrumento_recebido_em TIMESTAMPTZ NOT NULL`
- `condicoes_recebidas TEXT NOT NULL` (≥30 chars + anti-PII)
- `avaliacao_aptidao VARCHAR(20) NOT NULL` (`APTO | APTO_COM_RESSALVA | INAPTO`)
- `fluxo_subcontratacao_id UUID NULL FK` (US-CAL-017 — quando recepção decide subcontratar)
- `foto_evidencia_id UUID NULL FK` (`EvidenciaFotoAtividade` — opcional; cliente pode recusar foto)
- `correlation_id UUID NOT NULL`
- **Trigger:** imutável pós-INSERT.

**`MedicaoControle`** (cl. 7.7.1 — gráfico de controle X-R/CUSUM — TEMA-B.6 Onda 7B):
- `id UUID PK`, `tenant_id UUID NOT NULL`
- `padrao_id UUID NOT NULL FK`
- `grandeza VARCHAR(50) NOT NULL`, `faixa_min/faixa_max NUMERIC`
- `valor_medido NUMERIC(20,8) NOT NULL`, `valor_esperado NUMERIC(20,8) NOT NULL`
- `desvio NUMERIC(20,8) NOT NULL`, `dentro_2sigma BOOLEAN`, `dentro_3sigma BOOLEAN`
- `executor_id_hash CHAR(80) NOT NULL`
- `executado_em TIMESTAMPTZ NOT NULL`
- **Trigger:** imutável pós-INSERT (NOVO-CONCERN-4 Onda 7D).
- **Alerta:** `dentro_3sigma=false` ou 3 medições consecutivas mesmo lado → alerta P2 Qualidade (cl. 7.7.1).

**`EventoDeCalibracao`** (audit WORM paralelo a `EventoDeOS` — TEMA-C.5 Onda 7B):
- `id UUID PK`, `tenant_id UUID NOT NULL`, `calibracao_id UUID NOT NULL FK`
- `tipo VARCHAR(40) NOT NULL` (CalibracaoRecepcionada, ConfiguracaoSalva, LeituraRegistrada, LeituraCorrigida, IncertezaCalculada, ConformidadeAvaliada, RevisaoAprovada, RevisaoRejeitada, SegundaConferenciaAprovada, NCAberta, NCResolvida, Aprovada, Rejeitada, Cancelada, SubcontratadaParaLab, RecebidaDoSubcontratado, EpUnacceptableImpactoCriado)
- `payload_sanitizado JSONB NOT NULL` (sanitizado via helper único `sanitizar_payload_evento_calibracao()` — G2 do dossiê pré-M4 + SEC-SANITIZE-001)
- `evento_anterior_hash CHAR(80) NULL` (hash-chain — INV-CAL-AUD-001; null no 1º evento da calibração)
- `evento_hash CHAR(80) NOT NULL` (HashVersionado — ADR-0064; HMAC do payload + evento_anterior_hash + tenant_id + occurred_at)
- `correlation_id UUID NOT NULL`, `causation_id UUID NULL`
- `actor_user_id UUID NOT NULL`, `actor_user_id_hash CHAR(80) NOT NULL`
- `occurred_at TIMESTAMPTZ NOT NULL`
- **Trigger:** append-only (audit-immutability-check); RLS por tenant_id.

**`NaoConformidade`** (ciclo CAPA fechado — TEMA-B.2 Onda 7B + AC-CAL-014-3):
- `id UUID PK`, `tenant_id UUID NOT NULL`
- `calibracao_id UUID NULL FK` (NULL quando NC originada de Proficiência via `AnaliseImpactoNCProficiência`)
- `origem_proficiencia_id UUID NULL FK` (mutuamente exclusivo com calibracao_id)
- `descricao_hash CHAR(80) NOT NULL` (HashVersionado + anti-PII INV-CAL-TXT-001)
- `descricao_canonicalizada TEXT NOT NULL` (cl. 7.10 — INV-DOC-CANON-001)
- `estado VARCHAR(30) NOT NULL DEFAULT 'CONTIDA'` (`CONTIDA | ACAO_CORRETIVA_DEFINIDA | ACAO_EXECUTADA | EFICACIA_VERIFICADA | FECHADA | REABERTA`)
- `causa_raiz_hash CHAR(80) NULL`
- `causa_raiz_canonicalizada TEXT NULL`
- `acao_corretiva_descricao_hash CHAR(80) NULL`
- `acao_corretiva_tipo VARCHAR(30) NULL` (`RE_EXECUTAR | AJUSTE_ADMINISTRATIVO` — NOVO-2 RBC R2)
- `acao_executada_em TIMESTAMPTZ NULL`
- `eficacia_verificada_em TIMESTAMPTZ NULL`
- `eficacia_verificada_por_user_id UUID NULL`
- `responsavel_acao_user_id UUID NOT NULL`
- `correlation_id UUID NOT NULL`
- **Transição CONTIDA → ACAO_CORRETIVA_DEFINIDA → ACAO_EXECUTADA → EFICACIA_VERIFICADA → FECHADA** — cl. 8.7.2.
- **Transição REABERTA → CONTIDA** (re-análise causa-raiz cl. 8.7.2 — NOVO-1 RBC R2).
- **AC-CAL-NC-1:** `fecharNaoConformidade` exige TODOS dos 4 campos CAPA ≠ NULL; ausente → 412 `CAPAIncompleto`.

**`AnaliseImpactoNCProficiência`** (cl. 7.7.2 — AC-CAL-014-3 — NOVO Onda 7 M2-CAL):
- `id UUID PK`, `tenant_id UUID NOT NULL`
- `rodada_proficiencia_id UUID NOT NULL FK`
- `certificados_no_periodo JSONB NOT NULL` (array de `{cert_id, emitido_em, grandeza, faixa}` no intervalo última PT PASSED → atual)
- `gestor_qualidade_decisao JSONB NOT NULL` (array por cert: `{cert_id, decisao: 'RECALL' | 'SUSPENSAO' | 'SEM_IMPACTO', justificativa_hash}`)
- `decidida_em TIMESTAMPTZ NOT NULL`
- `decidida_por_user_id UUID NOT NULL`
- **Trigger:** imutável pós-INSERT.

**`LaboratorioSubcontratado`** (US-CAL-017):
- `id UUID PK`, `tenant_id UUID NOT NULL` (RLS — cada tenant tem seu cadastro de subcontratados)
- `razao_social_hash CHAR(80) NOT NULL`, `razao_social_key_id VARCHAR(40)` (PII Zona B)
- `cnpj_hash CHAR(80) NOT NULL`, `cnpj_key_id VARCHAR(40)`
- `credenciamento_atual VARCHAR(50) NOT NULL` (ex: "CGCRE-CAL-0123")
- `acreditacoes_vigentes JSONB NOT NULL` (array `{grandeza, faixa_min, faixa_max, validade}`)
- `contato_comercial_hash CHAR(80) NOT NULL` (PII Zona B)
- `contato_tecnico_hash CHAR(80) NOT NULL`
- `dpa_versao VARCHAR(20) NOT NULL` (cl. 4.7 ISO 17025)
- `vigencia_inicio/vigencia_fim TIMESTAMPTZ` (ADR-0030)
- `deletado_em TIMESTAMPTZ NULL` (Padrão C — soft-delete configuração)

**`AceiteSubcontratacao`** (US-CAL-017 — imutável + assinatura cliente):
- `id UUID PK`, `tenant_id UUID NOT NULL`, `calibracao_id UUID NOT NULL FK`
- `cliente_referencia_hash CHAR(80) NOT NULL`
- `texto_canonico_id UUID NOT NULL` (FK → `docs/conformidade/comum/termos/aceite-subcontratacao-v1.0.md` — REQUER OAB)
- `texto_hash CHAR(80) NOT NULL` (SHA-256 do texto exibido — INV-DOC-CANON-001)
- `assinatura_payload_encrypted BYTEA NULL` (touch ou A3; criptografado com `BIOMETRIA_KEY_<tenant>` se touch — INV-OS-ACEITE-BIO-001 herdado)
- `motivo_subcontratacao_canonicalizado TEXT NOT NULL` (≥30 chars + anti-PII)
- `motivo_hash CHAR(80) NOT NULL` (HashVersionado)
- `ip_hash CHAR(80) NOT NULL` (HashVersionado do IP cliente — política IP nunca persiste cleartext)
- `concedido_em TIMESTAMPTZ NOT NULL`
- `correlation_id UUID NOT NULL`
- **Trigger:** UPDATE/DELETE bloqueado pós-INSERT.

**`ConfiguracaoCalibracao`:**
- `id UUID PK`, `tenant_id UUID NOT NULL`, `calibracao_id UUID NOT NULL FK`
- `grandeza VARCHAR(50) NOT NULL`
- `faixa_min/faixa_max NUMERIC(20,8) NOT NULL`
- `unidade VARCHAR(20) NOT NULL`
- `metodo_referencia VARCHAR(80) NOT NULL` (NIT-DICLA / norma técnica)
- `pontos_calibracao NUMERIC(20,8)[] NOT NULL`
- `repeticoes_por_ponto INTEGER NOT NULL DEFAULT 3`
- `regra_decisao VARCHAR(25) NOT NULL` (snapshot de Calibracao.regra_decisao)
- `condicoes_ambientais_alvo_id UUID NULL FK`
- **INV-002:** pontos dentro da faixa CMC quando `tipo_acreditacao = 'RBC'` (predicate `cmc_cobre(grandeza, faixa)`).

---

## 4. Máquina de estados

### 4.1 Calibracao

```
[recepcionada] → [configurada] → [em_execucao] → [em_revisao_1] → [aguardando_2a_conferencia] → [aprovada]
       ↓             ↓              ↓                    ↓                       ↓                   ↘
       ↓             ↓              ↓                    → [rejeitada]           → [rejeitada]        [emite Certificado.Emitido — Marco 5]
       ↓             ↓              ↓                                                                
       ↓             ↓              → [nao_conforme] → [pendente_resolucao_nc] → [em_execucao] (resolverNC)
       ↓             ↓              ↓
       → [aguardando_subcontratado] → [recebida_do_subcontratado] → [em_revisao_1] (mesmo fluxo)
       ↓
       → [cancelada] (qualquer estado não-terminal)
```

**Regras (INV-CAL-WORM-001 + INV-CAL-CONF-001):**

- `recepcionada → configurada` por `configurarCalibracao` (US-CAL-002) — predicate `cmc_cobre` se RBC + predicate `procedimento_vigente_para` (US-CAL-016).
- `configurada → em_execucao` por `iniciarLeituras` (1ª leitura registrada).
- `em_execucao → em_revisao_1` por `solicitarRevisao` (cálculo de incerteza + avaliação conformidade concluídos).
- `em_revisao_1 → aguardando_2a_conferencia` por `aprovarRevisao` (US-CAL-007) — predicate `pode_aprovar_revisao` + INV-CAL-FRAUDE-REV-001 + ADR-0026 (se revisor=executor, 4 condições).
- `em_revisao_1 → rejeitada` por `rejeitarRevisao` (US-CAL-007) — volta atividade na fila do metrologista com nota.
- `aguardando_2a_conferencia → aprovada` por `aprovar2aConferencia` (US-CAL-008) — predicate INV-CAL-FRAUDE-CONF-001 + `conferente_id != revisor_id`.
- `aguardando_2a_conferencia → rejeitada` idem.
- `em_execucao → nao_conforme` por `marcarNaoConformidade` (US-CAL-014 PT UNACCEPTABLE / fora de tolerância).
- `nao_conforme → pendente_resolucao_nc → em_execucao` por `resolverNaoConformidade` (CAPA fechado — TEMA-B.2).
- `configurada → aguardando_subcontratado` por `subcontratarCalibracao` (US-CAL-017) — predicate `pode_subcontratar` + `aceite_subcontratacao_id NOT NULL`.
- `aguardando_subcontratado → recebida_do_subcontratado` por `registrarRecebimentoSubcontratado` — valida acreditação subcontratado vigente.
- `recebida_do_subcontratado → em_revisao_1` — segue fluxo normal de revisão (RT principal valida cert externo).
- Qualquer estado não-terminal → `cancelada` por `cancelarCalibracao` (motivo ≥30 chars anti-PII canonicalizado).
- **Estado `aprovada` é IMUTÁVEL** — reprocessar exige nova calibração com `causation_id` apontando à anterior.

### 4.2 NaoConformidade

```
[CONTIDA] → [ACAO_CORRETIVA_DEFINIDA] → [ACAO_EXECUTADA] → [EFICACIA_VERIFICADA] → [FECHADA]
   ↑                                                                                    ↓
   ← [REABERTA] ←────────────────────────────────────────────────────────────────── (re-análise causa-raiz)
```

cl. 8.7.2 — REABERTA SEMPRE volta a CONTIDA obrigatoriamente (NOVO-1 RBC R2).

---

## 5. INVs aplicáveis (consolidação)

### 5.1 INVs específicos do Marco 4 (cravados em REGRAS-INEGOCIAVEIS.md em P3)

| INV | Tema |
|---|---|
| INV-CAL-WORM-001 | Calibração + Leitura + OrcamentoIncerteza + Evento imutáveis pós-aprovação (cl. 7.5) |
| INV-CAL-VERSAO-001 | Versão do motor de cálculo cravada por calibração (ADR-0025 + cl. 7.11) |
| INV-CAL-DEC-001 | Regra de decisão snapshot por calibração (ADR-0024 + cl. 7.8.6); lock pós-emissão |
| INV-CAL-CONF-001 | 2ª conferência obrigatória; exceção objetiva ADR-0026 (4 condições + 5%/mês) |
| INV-CAL-RT-001 | RT habilitado por grandeza na data de execução (ADR-0022 + predicate `rt_competencia_cobre`) |
| INV-CAL-RT-COMP-001 | Snapshot de PadraoUsado capturado em momento da seleção; lock pós em_revisao_1 (TEMA-B.1) |
| INV-CAL-RAST-001 | Rastreabilidade ao SI via PadraoUsado.snapshot_padrao_json (cl. 6.5) |
| INV-CAL-SNAP-001 | Snapshot do padrão imutável (PadraoUsado.snapshot_padrao_json) |
| INV-CAL-VI-001 | Verificação intermediária programada por padrão (cl. 6.4.10) |
| INV-CAL-INC-001 | OrcamentoIncerteza com `documentacao_agregacao` quando `OrcamentoPorPonto[]` existe (NIT-DICLA-030 rev. 15 — NOVO-3 RBC R2) |
| INV-CAL-TXT-001 | Anti-PII em texto livre (10 campos: observacoes_gerais, razao_correcao, motivo_cancelamento, descricao_nc, causa_raiz, acao_corretiva, motivo_subcontratacao, justificativa_excecao_2a_conf, etc.) |
| INV-CAL-AUD-001 | EventoDeCalibracao append-only WORM com hash-chain |
| INV-CAL-NC-001 | NaoConformidade ciclo CAPA fechado obrigatório (cl. 7.10) |
| INV-CAL-NC-PT-001 | Resultado UNACCEPTABLE em proficiência dispara `AnaliseImpactoNCProficiência` automaticamente |
| INV-CAL-NUM-001 | Numero interno via sequence global + UNIQUE(tenant_id, numero_interno); buracos aceitos |
| INV-CAL-FRAUDE-EXEC-001 | `registrarLeitura` valida `calibracao.executor_id == request.user.id` ou DelegacaoExecucao válida |
| INV-CAL-FRAUDE-REV-001 | `aprovarRevisao` valida `calibracao.revisor_id == request.user.id` |
| INV-CAL-FRAUDE-CONF-001 | `aprovar2aConferencia` valida `calibracao.conferente_id == request.user.id` + `conferente_id != revisor_id` |
| INV-CAL-FRAUDE-COR-001 | `corrigirLeitura` valida `corretor_user_id == request.user.id` |
| INV-CAL-CMC-001 | `tipo_acreditacao=RBC` exige predicate `cmc_cobre` retornar true antes de configurar (cl. 6.4.10 + INV-002) |
| INV-CAL-SUBC-001 | Subcontratação cl. 6.6 exige `AceiteSubcontratacao` com assinatura cliente |
| INV-CAL-SUBC-002 | Subcontratado deve ter acreditação vigente na data do serviço (predicate `subcontratado_vigente_para`) |
| INV-CAL-SUBC-003 | Snapshot certificado externo do subcontratado imutável |
| INV-CAL-SUBC-004 | Texto certificado final declara subcontratação (cl. 6.6.2 + ILAC G18) — propagado a Marco 5 |
| INV-HMAC-001..005 | Formato canônico `v<NN>$<base64>` + KMS Multi-Region histórico 25a + rotação anual (ADR-0064) |
| INV-PAD-001..006 | PadraoMetrologico — UNIQUE numero_serie por tenant, vigência, estado bloqueante, rastreabilidade SI (ADR-0040) |
| INV-DOC-CANON-001 | Canonicalização texto probatório aplicada em LeituraCorrecao + NaoConformidade + AceiteSubcontratacao |

### 5.2 INVs herdados aplicáveis

- **F-A:** INV-TENANT-001..003 (RLS), INV-027 (estado explícito), INV-AUTHZ-001 (predicate).
- **F-B:** INV-AUTH-001..005 (lockout, MFA, sessão idle, ip_hash, retenção 365d).
- **M1 clientes:** INV-CLI-CONTATO/ENDERECO/SUCESSAO; INV-CLI-BLOQ-001 (inadimplência) — bloqueia subcontratação.
- **M2 equipamentos:** INV-EQP-MOV-001..002, INV-EQP-RT, INV-EQP-DEP (CVE WeasyPrint mitigado).
- **M3 OS:** INV-OS-ATIV-002 (herança tenant via atividade_os_id), INV-OS-CAL-LINK-001 (calibração reversa em ≤janela_tenant via watchdog), INV-OS-CONSBIO-001 (consentimento biometria).
- **Comum:** INV-IDEMP-001 (POST com Idempotency-Key), INV-BUS-001..003 (envelope v10), INV-OBS-001..003 (correlation_id + tenant_id em logs).
- **LGPD:** RAT-07 (geolocalização), RAT-08 (audit log com finalidade), RAT-09 (calibração — cliente PJ→contato PF).

---

## 6. Eventos publicados + consumidos (envelope v10)

### 6.1 Publicados pelo Marco 4

Todos com envelope v10 (`event_id`, `_schema_version: v1`, `occurred_at`, `correlation_id`, `actor`, `tenant_id`). Payload sanitizado via `sanitizar_payload_evento_calibracao()` (G2 do dossiê pré-M4).

| Evento | Payload essencial | Consumidores |
|---|---|---|
| `Calibracao.Recepcionada` | `calibracao_id, atividade_os_id, instrumento_id, cliente_referencia_hash` | M3 OS (atualiza link reverso) |
| `Calibracao.Configurada` | `calibracao_id, configuracao_id, regra_decisao, procedimento_versao_snapshot` | mobile.sync (calibração de campo), portal-cliente |
| `Calibracao.LeituraRegistrada` | `calibracao_id, leitura_id, ponto, valor, client_event_id` | observabilidade (métrica) |
| `Calibracao.LeituraCorrigida` | `calibracao_id, leitura_id, leitura_correcao_id, razao_hash, corretor_id_hash` | qualidade (alerta se >10% correções — GATE-CAL-LEITURA-CORR-TAXA) |
| `Calibracao.IncertezaCalculada` | `calibracao_id, orcamento_incerteza_id, u_combinada, k, U_expandida, versao_motor_calculo` | observabilidade (alerta divergência 2º caminho) |
| `Calibracao.ConformidadeAvaliada` | `calibracao_id, regra_decisao, zona, decisao_sugerida` | — |
| `Calibracao.RevisaoAprovada` | `calibracao_id, revisor_id` | M5 certificados (libera próximo passo) |
| `Calibracao.RevisaoRejeitada` | `calibracao_id, revisor_id, nota_hash` | — |
| `Calibracao.SegundaConferenciaAprovada` | `calibracao_id, conferente_id, excecao_2a_conf_id` | M5 certificados (gatilho emissão) |
| `Calibracao.Aprovada` | `calibracao_id, atividade_os_id, os_id, decisao, regra_decisao, padrao_usado_ids[], procedimento_versao_snapshot` | **M5 certificados** (emissão), **M3 OS** (libera AtividadeNCResolvida se NC bloqueava) |
| `Calibracao.Rejeitada` | `calibracao_id, atividade_os_id, motivo_hash` | **M3 OS** (atividade marca NC via encadeamento Atividade.NaoConforme — NOVO-ALTO-13) |
| `Calibracao.Cancelada` | `calibracao_id, motivo_hash` | — |
| `Calibracao.NCAberta` | `calibracao_id, nao_conformidade_id, origem` | qualidade (CAPA) |
| `Calibracao.NCFechada` | `calibracao_id, nao_conformidade_id, acao_corretiva_tipo, eficacia_verificada_em` | qualidade |
| `Calibracao.SubcontratadaParaLab` | `calibracao_id, subcontratado_id, motivo_hash, aceite_cliente_id` | observabilidade, financeiro (taxa subcontratação) |
| `Calibracao.RecebidaDoSubcontratado` | `calibracao_id, cert_externo_snapshot_hash, validacao_acreditacao_ok` | — |
| `Padrao.Cadastrado` | `padrao_id, grandezas, vinculacao` | — (módulo `padroes` Marco 4 P3) |
| `Padrao.RecalExternoIniciado` | `padrao_id, lab_destino, prazo_estimado` | observabilidade |
| `Padrao.RecalExternoConcluido` | `padrao_id, novo_cert_hash, nova_validade, novas_incertezas` | — |
| `Padrao.IntercomparacaoConcluida` | `padrao_id, rodada_id, escore_z, status` | qualidade (UNACCEPTABLE dispara `AnaliseImpactoNCProficiência`) |
| `Padrao.Baixado` / `Padrao.Sucateado` | `padrao_id, motivo` | — |
| `Calibracao.EpUnacceptableImpactoCriado` | `analise_impacto_id, rodada_id, certs_afetados_count` | qualidade |

### 6.2 Consumidos pelo Marco 4

| Evento | Origem | Ação |
|---|---|---|
| `Atividade.Iniciada(tipo=calibracao)` | `operacao/os` | Cria `Calibracao` em status `recepcionada` + `RecepcaoItemCalibracao` automaticamente + publica `Calibracao.Recepcionada` (AC-CAL-007-4) |
| `Cliente.Anonimizado` | `comercial/clientes` | Propaga `cliente_id=null` + preserva `cliente_referencia_hash` em Calibracao + AceiteSubcontratacao + RecepcaoItemCalibracao |
| `Padrao.CalibracaoExternaVencida` | `metrologia/padroes` | Bloqueia novas calibrações que selecionariam o padrão (predicate `padrao_vigente_no_uso`) |
| `Equipamento.PerfilTenantAlterado` | `suporte-plataforma/equipamentos` | Atualiza `snapshot_equipamento_json` se calibração em `recepcionada\|configurada` (não em `em_execucao` ou superior — INV-CAL-WORM-001) |
| `Colaborador.Desligado` | `rh-frota-qualidade/rh` | Bloqueia novas atribuições como revisor/conferente; calibrações em curso seguem (executor preservado) |
| `RT.CompetenciaRevogada` | `metrologia/responsabilidade-tecnica` | Bloqueia novas atribuições; auditoria registra |
| `Tenant.Suspenso` / `Tenant.Encerrado` | `suporte-plataforma/billing-saas` | Bloqueia operação (ADR-0035 herdado de M3) |
| `Acreditacao.Vencida` / `Acreditacao.Suspensa` | `metrologia/licencas-acreditacoes` | Bloqueia novas calibrações `tipo_acreditacao=RBC` em tenant perfil A |

---

## 7. AC binários (referência canônica)

Fonte da verdade dos AC BDD GIVEN/WHEN/THEN está no PRD: `docs/dominios/metrologia/modulos/calibracao/prd.md` §6 — **17 user stories US-CAL-001..017** com 2 a 7 AC cada (total ≥60 AC binários).

Resumo das US:

| US | Tema | Estado AC | ADR principal |
|---|---|---|---|
| US-CAL-001 | Recepcionar instrumento (consumer trigger ou avulsa) | 2 AC | ADR-0023 |
| US-CAL-002 | Configurar calibração + regra decisão | 2 AC | ADR-0024 |
| US-CAL-003 | Selecionar padrões com vigência válida | 3 AC | ADR-0040 |
| US-CAL-004 | Registrar leituras (manual ou integrada) | 3 AC | — |
| US-CAL-005 | Calcular erro + incerteza (GUM + ponto-a-ponto) | 3 AC | ADR-0025 |
| US-CAL-006 | Avaliar conformidade com regra de decisão | 3 AC | ADR-0024 |
| US-CAL-007 | Revisão técnica (1ª conferência) — política exceção | 4 AC | ADR-0026 |
| US-CAL-008 | Segunda conferência independente | 3 AC | ADR-0026 |
| US-CAL-009 | Histórico de calibrações por instrumento | 1 AC | — |
| US-CAL-010 | Controle de pesos padrão (catálogo) | 2 AC | ADR-0040 |
| US-CAL-011 | Registrar calibração externa do padrão | 2 AC | — |
| US-CAL-012 | Verificação intermediária | 2 AC | — |
| US-CAL-013 | Ensaios de linearidade, repetibilidade, excentricidade | 3 AC | — |
| US-CAL-014 | Comparação interlaboratorial / proficiência + impacto | 3 AC | ADR-0045 (depende Marco 5) |
| US-CAL-015 | Escopo de acreditação + CMC | 2 AC | — |
| US-CAL-016 | Vincular procedimento vigente | 3 AC | ADR-0030 |
| US-CAL-017 | Subcontratar calibração cl. 6.6 | 6 AC | NOVO 2026-05-25 |

**Espec não duplica AC**: 4 critérios novos M4 cruzam predicates ATIVADOS por ADR-0063 (RT competência); o spec garante a invocação real (G6 do dossiê pré-M4).

---

## 8. Riscos identificados

| ID | Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|---|
| R-M4-01 | Motor de cálculo de incerteza diverge entre versões (regressão silenciosa) | MÉDIA | ALTO | ADR-0025 + replay determinístico em CI + 2º caminho de cálculo com alerta P3 |0.1% / bloqueio 1% |
| R-M4-02 | Snapshot de padrão capturado retroativamente (não no momento da seleção) | BAIXA | ALTO | INV-CAL-RT-COMP-001 + trigger PG + `snapshot_lock` |
| R-M4-03 | RT revisor=executor sem 4 condições da ADR-0026 | MÉDIA | MÉDIO | Predicate `aprovacao_2a_conferencia_autorizada` + INV-CAL-CONF-001 |
| R-M4-04 | Calibração emitida com regra de decisão diferente da acordada em US-OS-001 | BAIXA | ALTO | Snapshot da regra em `Calibracao.regra_decisao` + lock pós-emissão (ADR-0024) |
| R-M4-05 | Subcontratado calibra fora do próprio escopo | BAIXA | ALTO | INV-CAL-SUBC-002 + predicate `subcontratado_vigente_para` + 412 bloqueio |
| R-M4-06 | LeituraCorrecao usada como bypass de auditoria (corrigir leitura ruim post-revisão) | BAIXA | ALTO | AC-CAL-004-7 trigger PG bloqueia pós EM_REVISAO_1 + CAPA obrigatório |
| R-M4-07 | Cliente PJ recebe cert subcontratado mas não foi informado | BAIXA | MÉDIO | INV-CAL-SUBC-001 + AceiteSubcontratacao texto v1.0 |
| R-M4-08 | Hash HMAC gerado em 2027 não-verificável em 2052 | BAIXA | CRÍTICO | ADR-0064 + INV-HMAC-002 + KMS DISABLED_BUT_RETAINED 25a |
| R-M4-09 | Resultado proficiência UNACCEPTABLE não dispara impacto retroativo | MÉDIA | CRÍTICO | INV-CAL-NC-PT-001 + consumer automático + AnaliseImpactoNCProficiência |
| R-M4-10 | Procedimento atualizado mid-calibração faz cert sair com versão errada | BAIXA | ALTO | US-CAL-016 + snapshot ProcedimentoCalibracaoVigenteSnapshot capturado em configurar |
| R-M4-11 | Stub público em saga "Recall" promete mas não implementa (igual M3 OS Q-OS-08) | MÉDIA | MÉDIO | **G1 do dossiê pré-M4** — todo stub raises NotImplementedError("GATE-CAL-RECALL Wave A") ou docstring marca STUB |
| R-M4-12 | Endpoint POST sem Idempotency-Key duplica leitura em retry (igual OS-IDEMP-001) | ALTA | CRÍTICO | **G3 do dossiê pré-M4** — 18 endpoints POST listados com IdempotencyMixin desde 1ª linha |
| R-M4-13 | Teste regressão anti-PII com `uuid4()` aleatório esconde bug `_SEQ_NUMERICA_RE` | MÉDIA | ALTO | **G4 do dossiê pré-M4** — 5000 UUIDs digit-heavy + 1000 ULIDs + 1000 slugs em test_inv_cal_aud_001_* |
| R-M4-14 | Consumer sem tenant_id explícito vaza calibração cross-tenant (igual SEG-M3-OS-01) | MÉDIA | CRÍTICO | **G5 do dossiê pré-M4** — `consumer_idempotente` seta `app.tenant_ids` antes do handler |
| R-M4-15 | Predicate `cmc_cobre` declarado mas não invocado em `configurar_calibracao` (igual PROD-M3-02) | MÉDIA | ALTO | **G6 do dossiê pré-M4** — 5 predicates invocados desde 1ª use case |
| R-M4-16 | Anti-fraude técnico assina por outro (igual INV-OS-ATIV-005) | MÉDIA | CRÍTICO | **G9 do dossiê pré-M4** — 4 INV-CAL-FRAUDE-* desde 1ª linha de cada use case |
| R-M4-17 | Drift docs massivo no fechamento M4 (igual D1-ALTA-1..4 do M3) | ALTA | MÉDIO | **G8 do dossiê pré-M4** — atualizar AGENTS/CURRENT/diário no MESMO commit da fase |

---

## 9. GATEs e DPIAs

### 9.1 GATEs Wave A operacionais rastreados (do dossiê pré-M4 + Onda 7C)

- **GATE-CAL-METODO-VAL** — fluxo validação método interno (cl. 7.2.2) — endereça em US-CAL-002.
- **GATE-CAL-EP-TEND** — painel histórico EP + alerta 3z mesmo sentido (cl. 7.7.3) — US-CAL-014.
- **GATE-CAL-VI-POL** — política VI por classe (cl. 6.4.10) — US-CAL-012.
- **GATE-CAL-MIG-CLASSIF** — hook `migration-metrology-classifier.sh` — Fase 9 M4.
- **GATE-CAL-MANUAL-QUAL** — página `/manual-qualidade` Wave A operacional (não M4 core).
- **GATE-CAL-LEITURA-CORR-TAXA** — alerta >10% leituras com LeituraCorrecao — US-CAL-004.
- **GATE-CAL-DPIA-OAB** — DPIA calibração revisada por advogado humano OAB pré-1º tenant externo.
- **GATE-HMAC-RETROFIT-MARCO-2-3** — script migração formato canônico Marco 2/3 Wave A operacional (ADR-0064).
- **GATE-KMS-IAM-LOCK** — IAM policy bloqueando kms:ScheduleKeyDeletion em chaves HMAC_KEY_* (Terraform Wave A).
- **GATE-HMAC-DRILL** — drill `validar_kms_retencao_hmac` integrado à suite verificação periódica.
- **GATE-OS-GRANDEZA-EM-ATIVIDADE** — M4 P3 PLUGA `AtividadeDaOS.grandeza` via migration → predicate `rt_competencia_cobre` bloqueia automaticamente (ADR-0063).
- **GATE-CAL-RECALL/SUSPENSAO/ERRATA** — pós-emissão fica em Marco 5 (ADR-0045); M4 publica `Calibracao.Aprovada` que Marco 5 consome.

### 9.2 DPIAs pendentes

- **`docs/conformidade/comum/dpia/dpia-calibracao.md`** — minuta a criar em P2 (revisão `advogado-saas-regulado`); aguardando OAB humana pré-tenant externo pago.

---

## 10. As 10 lições do Marco 3 OS aplicadas (G1..G10) — guard-rails M4

Aplicadas DESDE A 1ª LINHA de código M4 P4. Cada lição vira test/predicate/hook obrigatório.

| Lição | Aplicação concreta M4 |
|---|---|
| **G1 — Stubs não mentem** | Sagas `recall-cert-calibracao` + `errata-cert-calibracao` + `suspension-cert-calibracao` (todas Marco 5 GATE) → raise `NotImplementedError("GATE-CAL-RECALL Wave A")` em M4 OU docstring marca STUB explícito. Auditor-llm-correctness valida. |
| **G2 — Sanitizador único** | `src/infrastructure/calibracao/event_sanitizer.py::sanitizar_payload_evento_calibracao()` criado em P3 ANTES do 1º consumer. Cobre 17 eventos publicados M4. |
| **G3 — Idempotency-Key 18 POSTs** | `IdempotencyMixin` aplicado em `CalibracaoViewSet`, `LeituraViewSet`, `OrcamentoIncertezaViewSet`, `RevisaoViewSet`, `ConferenciaViewSet`, `NaoConformidadeViewSet`, `SubcontratacaoViewSet`, `PadraoViewSet`, `EscopoViewSet`, `ProficienciaViewSet`. `ACTION_IDEMPOTENT` map em P4. Hook `idempotency-key-header-check` detecta `@action(methods=POST)`. |
| **G4 — UUID digit-heavy** | `tests/regressao/test_inv_cal_aud_001_sanitize.py` com 5000 UUIDs digit-heavy + 1000 ULIDs + 1000 slugs + literais explícitos `00000000-0000-4000-8000-000000000000`, `33333333-3333-4333-8333-333333333333`, `99999999-9999-4999-8999-999999999999`, etc. Cobertura também em `test_inv_hmac_001_formato.py`. |
| **G5 — tenant_id em consumers** | `consumer_idempotente` decorator obrigatório em 6 consumers M4 (`Atividade.Iniciada(tipo=calibracao)`, `Cliente.Anonimizado`, `Padrao.CalibracaoExternaVencida`, `Equipamento.PerfilTenantAlterado`, `Colaborador.Desligado`, `RT.CompetenciaRevogada`). Seta `app.tenant_ids` ANTES do handler. Queries ORM checam `tenant_id` explícito mesmo com RLS. |
| **G6 — Predicates INVOCADOS** | 5 predicates invocados desde 1ª use case: `cmc_cobre`, `padrao_vigente_no_uso`, `procedimento_vigente_para`, `regra_decisao_aplicavel`, `rt_competencia_cobre` (ATIVADO via ADR-0063 quando M4 P3 setar `AtividadeDaOS.grandeza`). Auditor-produto rastreia AC × invocação. |
| **G7 — Use case → endpoint REST** | `plan.md` P2 cria tabela `use_case → endpoint` 100% coberta. ViewSets: `CalibracaoViewSet`, `LeituraViewSet`, `OrcamentoIncertezaViewSet`, `RevisaoViewSet`, `ConferenciaViewSet`, `NaoConformidadeViewSet`, `SubcontratacaoViewSet`, `PadraoViewSet`, `EscopoViewSet`, `ProficienciaViewSet`, `VerificacaoIntermediariaViewSet`. |
| **G8 — Drift docs ATIVO** | A cada fase concluída (P4 Fase N), mesmo commit: marca `✅` em tasks.md + atualiza AGENTS §11/§12 + atualiza `.agent/CURRENT.md` (≤40 linhas) + cria `docs/faseamento/diario/2026-MM-DD-marco4-fase-N.md` + atualiza `revisado_em` nos docs tocados. Hook `frontmatter-revisado-em-check` valida. |
| **G9 — Anti-fraude** | 4 INVs cravadas em REGRAS-INEGOCIAVEIS.md no P3: INV-CAL-FRAUDE-EXEC-001 (executor=user), INV-CAL-FRAUDE-REV-001 (revisor=user), INV-CAL-FRAUDE-CONF-001 (conferente=user + conferente≠revisor), INV-CAL-FRAUDE-COR-001 (corretor=user). Tests E2E DRILL-FRAUDE-CAL-1..4 com user diferente do designado retornando 403. |
| **G10 — PRD A11Y + Analytics por tela** | 9 telas M4 candidatas: `configurar-calibracao`, `registrar-leitura`, `painel-orcamento-incerteza`, `revisao-1a`, `conferencia-2a`, `recepcao`, `gestao-padroes`, `escopo-CMC`, `EP-painel`. Cada uma com PRD A11Y (ADR-0057) + PRD ProductAnalytics (ADR-0058) ANTES da 1ª UI. GATE-A11Y-4 + GATE-PRODANALYTICS-4 bloqueiam Fase 5 do M4 sem PRDs. |

---

## 11. Critérios de fechamento do Marco 4

Marco 4 só fecha sob INV-RITUAL-001 com:

- **10/10 auditores Família 5 PASS ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO** (P5 — auditoria estado reconciliado).
- Suite pytest chave M4 verde (esperado ≥80 testes — `tests/test_m4_calibracao_*.py` + `tests/regressao/test_inv_cal_*.py` + `tests/regressao/test_inv_hmac_*.py` + `tests/regressao/test_inv_pad_*.py`).
- Hooks `_test-runner.sh` permanecem 312/312 + ≥4 hooks novos M4 (cmc-binding, incerteza-versao-motor, hmac-versao-formato, migration-metrology-classifier).
- `ruff check src/domain/metrologia src/infrastructure/calibracao` zero issues.
- `mypy src/domain/metrologia src/infrastructure/calibracao` zero issues.
- Drill `validar_m4_calibracao` PASS — equivalente a `validar_m3_os`. Comando de gerência que executa caminho feliz: recepcionar → configurar → registrar 5 leituras → calcular incerteza → avaliar conformidade → aprovar revisão → aprovar 2ª conferência → publicar `Calibracao.Aprovada` (Marco 5 fora de escopo — para em APROVADA).
- Anti-replay teste: pytest `--randomly-seed=$(date +%s)` 3x; zero flake.
- Drift docs RESET: CURRENT.md ≤40 linhas, AGENTS contagens reais, tasks.md ✅ onde entregue, diário M4 completo.

---

## 12. Dependências entre fases (P1 → P5)

- **P1 (este doc)** — spec FORWARD do M4 calibracao. Saída: `docs/faseamento/M4-calibracao/spec.md`.
- **P2** — `plan.md` revisado pelos 4 subagentes (`tech-lead-saas-regulado`, `advogado-saas-regulado`, `corretora-seguros-saas`, `consultor-rbc-iso17025`). Saída: `plan.md` + `reviews/{4 reviews}.md` + DPIA minuta.
- **P3** — `tasks.md` com NN T-CAL granulares (esperado ~120 tasks em 10 fases similar a M3 OS); cravar INVs novos em REGRAS-INEGOCIAVEIS.md; cravar VOs novos (`RegraDecisao`, `VersaoMotorCalculo`, `HashVersionado`); criar 5 predicates.
- **P4** — implementação fase-a-fase. 10 fases esperadas: (1) modelos+migrations; (2) VOs+helpers crypto; (3) predicates+authz; (4) use cases base; (5) UI/endpoints; (6) consumers+sagas; (7) jobs procrastinate; (8) integrações cross-módulo; (9) hooks novos; (10) regressões+drill.
- **P5** — 10 auditores Família 5 sobre estado reconciliado. Vide M3 OS auditoria-familia5.md — esperado 1ª passada com achados, 5 batches conserto causa-raiz, 2ª/3ª passada zerando.

---

## 13. Sumário pra Roldão (linguagem de produto)

O Marco 4 é o **coração do produto**: tudo que o sistema sabe fazer de calibração metrológica está aqui. É também o **diferencial vs Calibre.Software** — cálculo de incerteza nativo + auditoria GUM + 2ª conferência independente + rastreabilidade até o padrão nacional.

**Tamanho:** comparável ao Marco 3 OS (~120 tasks; ~80 testes chave; 10 fases de implementação; 5 ADRs aplicadas + 11 herdadas).

**O que o cliente vê de novo:**

1. **Tela de recepção** — operador do lab dá entrada no instrumento, fotografa, gera etiqueta QR interna.
2. **Tela de configuração** — metrologista escolhe grandeza, faixa, pontos, padrões a usar. Sistema bloqueia se padrão venceu, se procedimento mudou, se CMC não cobre.
3. **Tela de registro de leitura** — manual ou puxando direto do instrumento via cabo USB/Serial. Se errar, corrige com rasura digital (preserva valor original).
4. **Painel de orçamento de incerteza** — sistema mostra cada componente (resolução, repetibilidade, deriva do padrão, condições ambientais), edita Tipo B, combina por GUM, mostra incerteza expandida com k=2.
5. **Tela de revisão técnica (1ª conferência)** — RT vê tudo, aprova/rejeita/pede correção.
6. **Tela de 2ª conferência** — outro RT confere; se único RT habilitado, sistema deixa EXCEÇÃO documentada (4 condições objetivas, máximo 5%/mês).
7. **Painel de proficiência** — registra rodada interlaboratorial; se UNACCEPTABLE, sistema lista TODOS os certs emitidos no período afetado e o gestor decide cert-a-cert: recall / suspensão / sem impacto.
8. **Cadastro de padrão** — peso, classe, valor convencional, certificado externo, validade, localização, ciclo de recal externo.
9. **Subcontratação** — se a empresa não pode calibrar (fora do escopo CMC), aceita o instrumento, pede consentimento do cliente, manda pra outro lab acreditado, recebe o cert externo, embute no cert final declarando "calibrado por <lab subcontratado>".

**O que NÃO faz neste Marco:**

- NÃO emite o PDF do certificado (Marco 5).
- NÃO assina digitalmente com A3 (Marco 5).
- NÃO faz NF-e (Wave A financeiro).
- NÃO gera recall/suspensão/errata (Marco 5).
- NÃO faz OCR de cert externo (manual).

**Próximo passo:** P2 — pedir review do plano de implementação aos 4 subagentes especialistas (tech-lead, advogado, corretora, consultor RBC).
