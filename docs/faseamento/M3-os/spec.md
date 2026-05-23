---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: reference
audiencia: agente
marco: Wave A Marco 3 — operacao/os
tipo: especificacao-forward
relacionados:
  - .specify/memory/constitution.md
  - docs/dominios/operacao/modulos/os/prd.md
  - docs/dominios/operacao/modulos/os/modelo-de-dominio.md
  - docs/dominios/operacao/modulos/os/sagas.md
  - docs/dominios/operacao/modulos/os/personas.md
  - docs/dominios/operacao/modulos/os/metricas.md
  - docs/faseamento/M1-clientes/spec.md
  - docs/faseamento/M2-equipamentos/spec.md
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - docs/adr/0012-autorizacao-unificada.md
  - docs/adr/0021-anonimizacao-vs-retencao.md
  - docs/adr/0022-rt-tenant.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0027-sync-mobile-merge-atividade.md
  - docs/adr/0029-canonicalizacao-texto-probatorio.md
  - docs/adr/0030-vigencia-temporal-canonica.md
  - docs/adr/0031-soft-delete-tres-padroes.md
  - docs/adr/0032-fk-cross-modulo-anonimizacao.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0034-saga-compensacao-cross-modulo.md
  - docs/adr/0041-os-concorrencia-atividades.md
  - docs/adr/0042-os-cancelamento-parcial-faturamento.md
  - docs/adr/0051-propagacao-adr0023-modulos-wave-a.md
  - docs/conformidade/comum/dpia/dpia-os.md
  - REGRAS-INEGOCIAVEIS.md
---

# Wave A — Marco 3 (operacao/os) — Especificação (forward, autoritativa)

> **O que este documento é (Constituição §1, §2):** a fonte da verdade
> do que o Marco 3 `os` **deve fazer**. Spec-as-source: o código é
> derivado/validado contra esta spec. Onde código divergir (após
> revisão dos 4 subagentes em P2), **o código é corrigido**, não a
> spec.
>
> **Por que existe (decisão Roldão 2026-05-23):** Marco 1 `clientes` e
> Marco 2 `equipamentos` fecharam via ritual Spec Kit (P5 10 auditores
> Família 5, zero CRÍTICO/ALTO/MÉDIO). Marco 3 destrava agora após
> Onda 6 saneamento + 2 rodadas de auditoria 10 lentes + Onda 8
> auditoria projeto-inteiro (149 + 147 achados resolvidos).
>
> **Pra Roldão (uma frase):** este é o "contrato" do módulo que
> registra todo trabalho do laboratório/assistência técnica (Ordens de
> Serviço com várias atividades dentro — calibração, manutenção,
> instalação, vistoria — cada uma com seu próprio fluxo, técnico e
> aceite do cliente).

---

## 1. Escopo

CRUD completo de OS + N AtividadeDaOS (ADR-0023) com máquina de
estados explícita por entidade; checklist obrigatório por atividade
conforme tipo; atribuição de técnico geral + executor por atividade
(metrologista calibra, mecânico conserta na mesma OS); offline-first
mobile com sync determinístico por atividade (ADR-0027); aceite
biométrico do cliente (touch art. 11 LGPD); reabertura cria OS-filha
com rastreabilidade; cancelamento total + parcial com impacto
faturamento (ADR-0042); marca de não conformidade (NC) por atividade
sem invalidar OS toda; sucessão societária preserva audit
(INV-OS-SUC-001); geolocalização opt-in com RIPD.

### Non-goals explícitos (Constituição §5 — proibição positiva)

Marco 3 `os` **NÃO** entrega, e nenhum agente deve inferir que
entrega:

- **NG-OS-1**: emissão de certificado — fica em `metrologia/certificados` (Marco 4).
- **NG-OS-2**: cálculo de medição/incerteza — fica em `metrologia/calibracao` (Marco 4).
- **NG-OS-3**: roteirização inteligente da frota (PRD §5; Wave B).
- **NG-OS-4**: faturamento por atividade — MVP-1 fatura OS atômica; ADR-0042 abre exceção para cancelamento parcial × CR ainda não FATURADA.
- **NG-OS-5**: reabertura granular por atividade — MVP-1 reabre OS toda (PRD §5).
- **NG-OS-6**: atividades de tenants diferentes na mesma OS — proibido (INV-OS-ATIV-002 + INV-TENANT-001).
- **NG-OS-7**: OCR de fotos para extrair leitura — Wave B.
- **NG-OS-8**: customização do fluxo de OS por tenant — ANTI-11 (PRD §5).
- **NG-OS-9**: editor visual de checklist — Wave B.
- **NG-OS-10**: workflow paralelo de aprovação multi-nível — Wave B BPM.
- **NG-OS-11**: integração WhatsApp Business pra captura de aceite remoto — Wave B (MVP-1: aceite presencial via app do técnico).
- **NG-OS-12**: multimídia além de fotos (vídeos, áudios) — Wave B.
- **NG-OS-13**: app nativo iOS/Android sem PWA primeiro — ADR-0018.
- **NG-OS-14**: pagamento direto da OS pelo cliente — fica em Financeiro.

---

## 2. Premissas (ADRs, VOs, hooks já em vigor)

### 2.1 ADRs estruturais aceitas que governam o Marco 3

| ADR | Tema | Aplicação no M3 |
|---|---|---|
| 0002 | Multi-tenancy (RLS + middleware) | Toda tabela do M3 leva `tenant_id` + policy RLS |
| 0007 | Camada domínio + gerador spec→código | Entidades do M3 ficam em `src/domain/operacao/` |
| 0012 | Autorização unificada | Predicates: `pode_iniciar_atividade`, `pode_concluir_atividade`, `pode_cancelar_os`, `pode_reabrir_os`, `pode_dispensar_aceite` |
| 0021 | Anonimização vs retenção | Zona A/B: OS preserva `cliente_id_hash` quando cliente anonimizado |
| 0022 | RT tenant | `requer_competencia_rt=true` valida via predicate `tenant_tem_rt_ativo_competencia(grandeza)` |
| 0023 | OS com Atividades | Estrutura 1:N OS↔Atividade; tipos enum fechado (6 tipos) |
| 0027 | Sync mobile merge por atividade | LWW por atividade_id + append-only para fotos (INV-OS-SYNC-001) |
| 0029 | Canonicalização texto probatório | AceiteAtividade UTF-8 + LF + NFC + marcadores |
| 0030 | Vigência temporal canônica | `TipoAtividadeConfig` usa `JanelaVigencia` |
| 0031 | Soft-delete 3 padrões | OS/Atividade → Padrão A (estado-máquina); AceiteAtividade → Padrão B; TipoAtividadeConfig → Padrão C |
| 0032 | FK cross-módulo + anonimização | OS guarda `cliente_referencia_hash` + `cliente_id` nullable |
| 0033 | Bus idempotência consumer | Consumers OS gravam em `consumer_idempotencia` |
| 0034 | Saga compensação cross-módulo | 4 sagas críticas mapeadas em `docs/comum/sagas-cross-modulo.md` e `os/sagas.md` |
| 0041 | OS concorrência atividades | Matriz tipo×tipo: bloqueia 2 atividades simultâneas em mesmo equipamento |
| 0042 | OS cancelamento parcial × faturamento | `OS.EscopoAlterado` recalcula CR se ainda não FATURADA |
| 0051 | Propagação ADR-0023 nos módulos Wave A | Orçamento item→atividade; agenda evento→atividade; CR faturamento por atividade |

### 2.2 VOs disponíveis (Onda 2)

- `JanelaVigencia`, `ReferenciaPIIAnonimizavel`, `Telefone`, `UF`, `Dinheiro` em `src/domain/shared/value_objects.py`.
- `Grandeza`, `FaixaMedicao`, `IncertezaExpandida` em `src/domain/metrologia/value_objects.py` — usados em atividades tipo `calibracao` para guardar leitura prévia (não calcula incerteza — isso é Marco 4).
- `TenantLifecycleEstado` — consumer OS bloqueia operação se `tenant.estado IN (suspenso, encerrado)` (ADR-0035).

### 2.3 Hooks pré-commit aplicáveis

Já registrados em `.claude/settings.json` (Onda 4):

- `vigencia-canonica-check` — bloqueia coluna `validade_inicio` / `data_fim_vigencia` (não-canônico).
- `soft-delete-padrao-check` — Padrão A obrigatório em OS/Atividade; Padrão B em AceiteAtividade.
- `fk-pii-anonimizavel-check` — FK PII Zona B exige par `hash + key_id`.
- `biometria-key-validator` — `BIOMETRIA_KEY_*` dedicada por tenant.
- `os-conclusao-todas-terminais-check` — INV-OS-ATIV-001 (OS só conclui quando TODAS atividades em estado terminal).
- `frontmatter-revisado-em-check` — frontmatter obrigatório em docs.
- `spec-ac-binario-check` — AC BDD GIVEN/WHEN/THEN obrigatório.
- `bus-envelope-validator` v10 — eventos com `event_id`, `_schema_version`, `occurred_at`, `correlation_id`, `actor`.
- `migration-rls-check` — toda tabela com `tenant_id` exige policy RLS.

### 2.4 DPIA aprovada (minuta OAB pendente)

`docs/conformidade/comum/dpia/dpia-os.md` — avalia biometria touch
(art. 11 LGPD), geolocalização (RAT-07), foto evidence em campo,
audit log com motivo_hash (anti-PII).

---

## 3. Entidades + schema sketch

### 3.1 Tabela resumo

| Entidade | Padrão soft-delete | Vigência? | FK PII? | Imutável pós-INSERT? |
|---|---|---|---|---|
| `OS` | A (estado-máquina) | não | sim — `cliente_referencia_hash` | parcial (snapshot inicial + máquina estados) |
| `AtividadeDaOS` | A (estado-máquina) | não | sim (via OS) | parcial |
| `EventoDeOS` | B (`revogado_em` raro; uso normal append-only) | não | sim — hash sanitizado | sim (append-only) |
| `AceiteAtividade` | B (imutável pós-coleta) | não | sim — biometria + cliente | sim |
| `DispensaAceiteAtividade` | B (audit imutável) | não | sim — gerente_id + cliente_hash | sim |
| `DelegacaoExecucao` | B (audit imutável) | não | sim — técnico delegante + delegado | sim |
| `ChecklistDaAtividade` | A (estado por item) | não | não | não (preenchimento progressivo) |
| `TipoAtividadeConfig` | C (`deletado_em`) | sim (procedimento vinculado) | não | não |
| `SLAContrato` | A (revogado_em) | sim (vigência) | sim — cliente_id | não |
| `NaoConformidadeAtividade` | B (revogado_em raro) | não | sim — descrição_hash | sim |

### 3.2 Campos principais (sketch — refinamento final em P4)

**`OS`:**
- `id UUID PK`
- `tenant_id UUID NOT NULL` (RLS)
- `numero_os VARCHAR(20)` — gerado pela sequence `os_numero_seq_<tenant>`
- `cliente_id UUID NULL` (FK → clientes; pode ficar NULL pós-anonimização)
- `cliente_referencia_hash CHAR(64)` (HMAC-SHA256 do cliente_id original — preserva audit pós-anonimização ADR-0032)
- `cliente_key_id VARCHAR(40)` (kms key id)
- `equipamento_id UUID NOT NULL` (FK → equipamentos)
- `orcamento_origem_id UUID NULL` (FK; null em OS avulsa)
- `os_origem_id UUID NULL` (FK reabertura)
- `sucessao_societaria_id UUID NULL` (FK quando reabertura cross-cliente M&A)
- `estado VARCHAR(20) NOT NULL DEFAULT 'rascunho'` (rascunho|agendada|em_execucao|concluida|cancelada|faturada|paga)
- `tipo_predominante VARCHAR(30)` (calculado em transição → CONCLUIDA; regra empate: calibracao vence)
- `nao_conformidade_global BOOLEAN DEFAULT false`
- `valor_total NUMERIC(14,2)` (snapshot inicial vindo do orçamento)
- `valor_total_atualizado NUMERIC(14,2)` (recalculado a cada cancelamento parcial — ADR-0042)
- `criada_em / atualizada_em TIMESTAMPTZ`
- `criada_por_user_id UUID`

**`AtividadeDaOS`:**
- `id UUID PK`
- `tenant_id UUID NOT NULL` (RLS — herda da OS via INV-TENANT-001)
- `os_id UUID NOT NULL FK`
- `tipo VARCHAR(30) NOT NULL` (calibracao|manutencao_corretiva|manutencao_preventiva|instalacao|verificacao_inmetro|vistoria)
- `sequencia INTEGER NOT NULL` (ordem de execução; gate sequência ADR-0041)
- `estado VARCHAR(20) NOT NULL DEFAULT 'pendente'` (pendente|agendada|em_execucao|concluida|nao_conforme|cancelada)
- `tecnico_executor_id UUID` (FK → user; pode variar entre atividades)
- `agendada_para TIMESTAMPTZ`
- `iniciada_em TIMESTAMPTZ`
- `concluida_em TIMESTAMPTZ`
- `valor_unitario_snapshot NUMERIC(14,2)`
- `link_modulo_tecnico_id UUID` (FK reversa pra Calibracao/Manutencao — preenchido pelo módulo técnico em ≤24h via INV-OS-CAL-LINK-001)
- `geo_ponto GEOGRAPHY(POINT, 4326) NULL` (opt-in; precisão limitada INV-OS-GEO-001)

**`AceiteAtividade`** (entidade imutável — Padrão B):
- `id UUID PK`
- `tenant_id UUID NOT NULL`
- `atividade_id UUID NOT NULL FK`
- `cliente_referencia_hash CHAR(64)` (HMAC PII)
- `cliente_key_id VARCHAR(40)`
- `texto_canonicalizado TEXT NOT NULL` (UTF-8 + LF + NFC + marcadores `<<<CORPO INICIO/FIM>>>`)
- `texto_hash CHAR(64)` (SHA-256 do texto pós-canonicalização — INV-DOC-CANON-001)
- `biometria_payload_encrypted BYTEA` (criptografado com `BIOMETRIA_KEY_<tenant>` — INV-OS-ACEITE-BIO-001)
- `biometria_key_id VARCHAR(40)`
- `coletado_em TIMESTAMPTZ NOT NULL`
- `geo_ponto GEOGRAPHY(POINT, 4326) NULL` (opt-in)
- **Trigger:** bloqueia UPDATE/DELETE pós-INSERT (audit-immutability).

---

## 4. Máquina de estados

### 4.1 OS

```
[rascunho] → [agendada] → [em_execucao] → [concluida] → [faturada] → [paga]
     ↘            ↘            ↘
   [cancelada] [cancelada] [cancelada]
```

Regras (INV-027 + INV-OS-ATIV-001):

- `rascunho → agendada` quando `atribuirTecnico` executa.
- `agendada → em_execucao` quando 1ª atividade inicia.
- `em_execucao → concluida` quando **TODAS** atividades em estado terminal (CONCLUIDA / NAO_CONFORME / CANCELADA).
- `qualquer estado não-terminal → cancelada` via `cancelarOS` com razão ≥30 chars.
- `concluida → faturada` (módulo Financeiro publica `OS.Faturada`).
- `faturada → paga` (módulo Financeiro publica `OS.Paga`).

### 4.2 AtividadeDaOS

```
[pendente] → [agendada] → [em_execucao] → [concluida]
                  ↓             ↓             ↘
                  ↓             → [nao_conforme] → [em_execucao] (resolverNC)
                  ↓                       ↓
                  → [cancelada] ← [cancelada]
```

Regras (INV-OS-ATIV-*):

- `pendente → agendada` quando técnico atribuído + data definida.
- `agendada → em_execucao` por `iniciarAtividade` (executor designado, INV-OS-ATIV-005).
- `em_execucao → concluida` por `concluirAtividade` (checklist 100% + AceiteAtividade quando exigido).
- `em_execucao → nao_conforme` por `marcarNaoConformidadeAtividade` (CAPA TEMA-B.2).
- `nao_conforme → em_execucao` por `resolverNC` (causa-raiz + ação corretiva + eficácia).
- Qualquer estado não-terminal → `cancelada` via `cancelarAtividade`.

---

## 5. INVs aplicáveis (consolidação)

### 5.1 INVs específicos do Marco 3 (cravados em REGRAS-INEGOCIAVEIS.md)

| INV | Tema |
|---|---|
| INV-OS-ATIV-001 | OS conclui quando TODAS atividades em estado terminal |
| INV-OS-ATIV-002 | Atividade nunca cross-tenant da OS (mesmo tenant_id) |
| INV-OS-ATIV-003 | Tipo da atividade do enum fechado (6 tipos) |
| INV-OS-ATIV-004 | Sequência crescente + gate de sequência pos-terminal |
| INV-OS-ATIV-005 | Executor designado é único autorizado a iniciar/concluir |
| INV-OS-EQP-001 | Equipamento BAIXADO/DESCARTADO bloqueia abrir OS |
| INV-OS-ANON-001 | Anonimização bloqueada se cliente tem OS aberta |
| INV-OS-CAL-LINK-001 | Calibracao.atividade_os_id em ≤24h via watchdog |
| INV-OS-FAT-001 | Faturamento = sum(atividades não canceladas) |
| INV-OS-CONC-001 | Concorrência matriz tipo×tipo (ADR-0041) |
| INV-OS-SUC-001 | Reabertura cross-cliente em sucessão preserva audit |
| INV-OS-SYNC-001 | Append-only pra fotos no sync mobile |
| INV-OS-GEO-001 | Geolocalização precisão limitada + opt-in + RIPD |
| INV-OS-TXT-001 | Anti-PII em texto livre (razão, observação) |
| INV-OS-AUD-001 | Audit sanitizado escrita |
| INV-OS-ACEITE-BIO-001 | Biometria touch criptografada com BIOMETRIA_KEY_<tenant> |
| INV-DOC-CANON-001 | Canonicalização texto probatório (AceiteAtividade) |

### 5.2 INVs herdados aplicáveis

- **F-A:** INV-TENANT-001..003 (RLS), INV-027 (estado explícito), INV-AUTHZ-001 (predicate).
- **F-B:** INV-AUTH-001..005 (lockout, MFA, sessão idle, ip_hash, retenção 365d).
- **M1 clientes:** INV-CLI-CONTATO/ENDERECO/SUCESSAO/REATIV/PRICE.
- **M2 equipamentos:** INV-EQP-MOV-001..002, INV-EQP-RT, INV-EQP-DEP.
- **Comum:** INV-IDEMP-001 (POST com Idempotency-Key), INV-BUS-001..003 (envelope v10).
- **LGPD:** RAT-07 (geolocalização), RAT-08 (audit log com finalidade).

---

## 6. Eventos publicados + consumidos (envelope v10)

### 6.1 Publicados pelo Marco 3

Todos com envelope v10 (`event_id`, `_schema_version: v1`, `occurred_at`, `correlation_id`, `actor`, `tenant_id`).

| Evento | Payload essencial | Consumidores |
|---|---|---|
| `OSAberta` | `os_id, cliente_id_hash, atividades_planejadas` | mobile.sync, CRM |
| `OSAtribuida` | `os_id, tecnico_geral_id, executores_por_atividade` | agenda, portal-cliente |
| `OSConcluida` | `os_id, tipo_predominante, valor_total_atualizado` | financeiro, certificados, portal-cliente |
| `OSCancelada` | `os_id, razao_hash, atividades_canceladas` | agenda, financeiro, portal-cliente |
| `OS.EscopoAlterado` (ADR-0042) | `os_id, atividade_id_cancelada, valor_removido, valor_total_atualizado` | financeiro/contas-receber |
| `OS.Reaberta` | `os_id (nova), os_origem_id, chamado_origem_id, motivo, garantia_procedente` | caixa-tecnico, chamados, portal-cliente |
| `AtividadeAdicionada` | `os_id, atividade_id, tipo, sequencia` | agenda, mobile.sync |
| `AtividadeIniciada` | `atividade_id, tecnico_executor_id, geo, client_event_id` | mobile.sync |
| `AtividadeConcluida` | `atividade_id, tipo, checklist_id, aceite_id` | certificados (se tipo=calibracao), portal-cliente, omni |
| `AtividadeNaoConforme` | `atividade_id, razao_hash` | qualidade (CAPA), certificados (bloqueio) |
| `AtividadeNCResolvida` | `atividade_id, causa_raiz_hash, acao_corretiva_id` | certificados (libera) |
| `AtividadeCancelada` | `atividade_id, razao_hash` | financeiro (via OS.EscopoAlterado) |
| `AceiteColetado` | `aceite_id, atividade_id, texto_hash, coletado_em` | certificados |
| `DispensaAceiteEmitida` | `dispensa_id, atividade_id, gerente_id, termo_pdf_id` | portal-cliente |

### 6.2 Consumidos pelo Marco 3

| Evento | Origem | Ação |
|---|---|---|
| `Orcamento.Aprovado` | comercial/orcamentos | abre OS RASCUNHO + N AtividadeDaOS |
| `Cliente.Anonimizado` | comercial/clientes | propaga `cliente_id=null` + preserva `cliente_referencia_hash` |
| `Calibracao.Iniciada` / `Calibracao.Concluida` | metrologia/calibracao | atualiza `link_modulo_tecnico_id` (INV-OS-CAL-LINK-001) |
| `OS.Faturada` / `OS.Paga` | financeiro/contas-receber | transição de estado da OS |
| `Tenant.Suspenso` / `Tenant.Encerrado` | suporte-plataforma/billing-saas | bloqueia operação (ADR-0035) |
| `Equipamento.Baixado` / `Equipamento.Descartado` | suporte-plataforma/equipamentos | bloqueia abrir OS (INV-OS-EQP-001) |

---

## 7. AC binários (referência canônica)

Fonte da verdade dos AC BDD GIVEN/WHEN/THEN está no PRD:
`docs/dominios/operacao/modulos/os/prd.md` §6 — 15 user stories
US-OS-001..015 com 4 a 7 AC cada (total ≥70 AC binários).

Sumário (numeração estável pós-Onda 6 auditor 5):

| US | Operação | AC count | INVs centrais |
|---|---|---|---|
| US-OS-001 | abrirOS | 6 | INV-OS-EQP-001, INV-OS-ANON-001, INV-TENANT-001 |
| US-OS-002 | adicionarAtividade (inicial) | 4 | INV-OS-ATIV-001/003, INV-CAL-RT-001 |
| US-OS-002b | atribuirTecnico geral + executor | 3 | INV-020, INV-AUTHZ-001, INV-027 |
| US-OS-003 | iniciarAtividade (mobile offline) | 5 | INV-OS-ATIV-005, IDEMP-001, INV-OS-GEO-001 |
| US-OS-004 | concluirAtividade | 6 | INV-OS-ATIV-001/005, INV-OS-CAL-LINK-001 |
| US-OS-005 | marcarNaoConformidadeAtividade | 4 | INV-012, INV-OS-TXT-001 |
| US-OS-006 | reabrirOS | 7 | INV-OS-ATIV-002/005, INV-OS-SUC-001 |
| US-OS-007 | cancelarOS | 4 | INV-027, INV-OS-TXT-001 |
| US-OS-008 | cancelarAtividade (escopo alterado) | 4 | INV-OS-ATIV-001, INV-OS-FAT-001 |
| US-OS-009 | OS combinada (mant + cal) | 5 | INV-OS-ATIV-001/003 |
| US-OS-010 | adicionarAtividade (em andamento) | 4 | INV-OS-ATIV-001/003 |
| US-OS-011 | reagendarAtividade | 3 | INV-OS-TXT-001, INV-AUTHZ-001 |
| US-OS-012 | transferirTecnico | 3 | INV-AUTHZ-001, INV-CAL-RT-001 |
| US-OS-013 | dispensarAceiteCliente | 4 | INV-AUTHZ-001, INV-OS-TXT-001, RAT-08 |
| US-OS-014 | marcarNoShow | 2 | RAT-07, RAT-08 |
| US-OS-015 | criarOSAvulsa (balcão) | 3 | INV-026, INV-CLI-PRICE-001 |

Aceitar PRD §6 como fonte canônica obriga implementação a satisfazer
**todos os AC numerados** — se algum AC for "ajustado" durante
implementação, o ritual exige PR contra `prd.md` revisado pelos 4
subagentes (ADR-equivalente).

---

## 8. Sagas inter-modulares (referência canônica)

Fonte da verdade dos fluxos cross-módulo está em
`docs/dominios/operacao/modulos/os/sagas.md` (11 sagas) +
`docs/comum/sagas-cross-modulo.md` (4 sagas críticas mapeadas no
ADR-0034).

Sagas críticas que o M3 precisa entregar funcionando:

1. **Abrir OS via Orçamento aprovado** (consumer + idempotência ADR-0033).
2. **Cancelamento parcial × Financeiro** (`OS.EscopoAlterado` → CR — ADR-0042).
3. **Atividade calibração → Metrologia** (`AtividadeConcluida` + watchdog `os-calibracao-link-watchdog` INV-OS-CAL-LINK-001).
4. **Anonimização Cliente × OS aberta** (INV-OS-ANON-001 bloqueia; consumer retentivo quando OS conclui).
5. **Reabertura cross-cliente M&A** (preserva audit INV-OS-SUC-001).
6. **Sync mobile com fotos** (LWW por atividade + append-only fotos INV-OS-SYNC-001).
7. **Notificação ao cliente** (portal-cliente + OmniChannel opt-in).
8. **Reagendamento + troca técnico** (US-OS-011/012; valida competência + agenda).
9. **No-show do cliente** (US-OS-014; deslocamento gera CR em Wave B).
10. **Dispensa de aceite cliente** (US-OS-013; entidade `DispensaAceiteAtividade`).

---

## 9. GATEs Wave A (subset Marco 3)

Catálogo em `docs/governanca/gates-wave-a-consolidado.md`. Subset
relevante ao M3 (não bloqueiam fechamento do M3, mas precisam ficar
rastreados):

- **GATE-BUS-CONSUMER-IDEMP** — migration `consumer_idempotencia` precisa estar criada antes de qualquer consumer M3 entrar em produção (ADR-0033).
- **GATE-BUS-HANDLERS** — registry de consumers + DLQ ativos (ADR-0033).
- **GATE-EQP-PWA-ADR** — ADR-0018 aceite (necessário antes do app-tecnico em Wave A; M3 backend não bloqueado).
- **GATE-RBC-ANAL-PEDIDOS-1** — ISO 17025 cl. 7.1 análise crítica (gate operacional Wave A).
- **GATE-LGPD-ART18-MODULOS** — endpoint art. 18 em OS quando módulo Clientes implementa fluxo completo.
- **GATE-SEG-VIST-1** — cláusula E&O `pareceres técnicos` quando tipo atividade=vistoria.
- **GATE-OS-CAL-LINK-WATCHDOG** — operacional: deployar watchdog `os-calibracao-link-watchdog` (cron + procrastinate) com alertas P2/72h.
- **GATE-OS-BIOMETRIA-KMS** — KMS key `BIOMETRIA_KEY_<tenant>` provisionada por tenant antes de coletar AceiteAtividade.
- **GATE-OS-DPIA-OAB** — minuta DPIA-OS revisada por OAB humana antes do 1º tenant externo pago.

---

## 10. Hooks pré-commit aplicáveis (manter PASS durante implementação)

Já estão registrados em `.claude/settings.json`; cada commit M3
precisa passar:

- `vigencia-canonica-check` — TipoAtividadeConfig usa `JanelaVigencia`.
- `soft-delete-padrao-check` — OS/Atividade=A, AceiteAtividade=B, TipoAtividadeConfig=C.
- `fk-pii-anonimizavel-check` — `cliente_referencia_hash + cliente_key_id` em OS.
- `biometria-key-validator` — AceiteAtividade.biometria_key_id presente.
- `os-conclusao-todas-terminais-check` — INV-OS-ATIV-001 no código.
- `bus-envelope-validator` — eventos M3 carregam envelope v10.
- `migration-rls-check` — tabela `os`, `atividade_da_os`, `aceite_atividade`, `dispensa_aceite_atividade`, `evento_de_os`, `checklist_da_atividade`, `tipo_atividade_config`, `nao_conformidade_atividade` com policy RLS.
- `authz-check` — predicates `pode_iniciar_atividade`, `pode_concluir_atividade`, `pode_cancelar_os`, `pode_reabrir_os`, `pode_dispensar_aceite` registrados.
- `port-binding-validator` — `metrologia/calibracao` não importa de `operacao/os/models` direto; query service obrigatório.
- `audit-immutability-check` — trigger anti-mutation em AceiteAtividade, DispensaAceiteAtividade, EventoDeOS.
- `spec-ac-binario-check` — referências de US/AC nos commits.

---

## 11. Mapa de testes (regressão + integração)

### 11.1 Testes de regressão de INV (1 por INV)

- `tests/regressao/test_inv_os_ativ_001_terminal.py`
- `tests/regressao/test_inv_os_ativ_002_cross_tenant.py`
- `tests/regressao/test_inv_os_ativ_005_executor_exclusivo.py`
- `tests/regressao/test_inv_os_eqp_001_baixado.py`
- `tests/regressao/test_inv_os_anon_001_anonimizacao_bloqueada.py`
- `tests/regressao/test_inv_os_cal_link_001_watchdog.py`
- `tests/regressao/test_inv_os_fat_001_cancelamento_parcial.py`
- `tests/regressao/test_inv_os_conc_001_concorrencia_matriz.py`
- `tests/regressao/test_inv_os_suc_001_sucessao_societaria.py`
- `tests/regressao/test_inv_os_sync_001_fotos_append_only.py`
- `tests/regressao/test_inv_os_geo_001_precisao_limitada.py`
- `tests/regressao/test_inv_os_aceite_bio_001_biometria_kms.py`
- `tests/regressao/test_inv_doc_canon_001_aceite_canonicalizado.py`

### 11.2 Testes de integração (1 por US — happy path + unhappy path crítico)

- `tests/integracao/test_us_os_001_abrir_via_orcamento.py`
- ... (US-OS-002 a US-OS-015 — 15 arquivos)

### 11.3 Testes de saga (1 por saga inter-modular)

- `tests/sagas/test_saga_abrir_via_orcamento.py`
- `tests/sagas/test_saga_cancelamento_parcial_cr.py`
- `tests/sagas/test_saga_atividade_calibracao_link.py`
- `tests/sagas/test_saga_anonimizacao_bloqueada.py`
- `tests/sagas/test_saga_reabertura_sucessao.py`
- `tests/sagas/test_saga_sync_mobile_fotos.py`
- `tests/sagas/test_saga_notificacao_cliente.py`
- `tests/sagas/test_saga_reagendamento_troca_tecnico.py`
- `tests/sagas/test_saga_no_show.py`
- `tests/sagas/test_saga_dispensa_aceite.py`

### 11.4 Drill operacional

- `manage.py validar_m3_os` — verifica 20+ pontos:
  - schema OS + AtividadeDaOS + 6 outras entidades criadas
  - policies RLS ativas em todas
  - triggers anti-mutation em AceiteAtividade, DispensaAceiteAtividade, EventoDeOS
  - predicates authz registrados
  - consumers ativos (Orcamento.Aprovado, Cliente.Anonimizado, OS.Faturada, OS.Paga, Tenant.Suspenso, Equipamento.Baixado)
  - watchdog `os-calibracao-link-watchdog` agendado
  - sequence `os_numero_seq_<tenant>` por tenant
  - INV-OS-* todos testados (cobertura 100% em path crítico)

### 11.5 Meta de testes

- Suite total verde (≥865 passed pós-M3 = 621 atuais + ~150 novos M3 + ~94 sagas/integração).
- `_test-runner.sh` mantém 207/207 verdes (sem regressão em hooks).
- Cobertura ≥85% em `src/domain/operacao/os/`.

---

## 12. Mapa de riscos do Marco 3

| ID | Risco | Probab | Impacto | Mitigação |
|---|---|---|---|---|
| R-OS-1 | Sync mobile com foto perde dado em conflito LWW | média | alto (legal, perda evidência) | INV-OS-SYNC-001 + append-only fotos + teste saga |
| R-OS-2 | Watchdog cal-link false positive (alerta excessivo) | média | médio | janela 24h ajustável por tenant + override RT |
| R-OS-3 | Biometria coletada em key_id errada (cross-tenant) | baixa | crítico (LGPD art. 11) | hook biometria-key-validator + RLS no AceiteAtividade |
| R-OS-4 | OS reaberta com cliente anonimizado sem sucessão | média | alto (audit perdido) | INV-OS-SUC-001 + AC-OS-006-7 bloqueio 412 |
| R-OS-5 | Faturamento incorreto após cancelamento parcial pós-fatura | média | alto (fiscal) | NG-OS-4 + gate `GATE-FIN-CR-AJUSTE-POS-FATURA` Wave B + INV-OS-FAT-001 |
| R-OS-6 | Concorrência 2 atividades simultâneas mesmo equipamento corrompe ambas | média | alto (medição) | INV-OS-CONC-001 + matriz ADR-0041 + lock por equipamento_id |
| R-OS-7 | Texto AceiteAtividade não canonicalizado quebra hash em re-verificação | baixa | médio (probatório) | INV-DOC-CANON-001 + teste regressão |
| R-OS-8 | Geo coletado sem opt-in viola LGPD | média | alto (ANPD) | RAT-07 + flag opt-in obrigatória + RIPD aprovado |
| R-OS-9 | Cancelamento múltiplo concorrente vira inconsistência valor_total | média | médio | SELECT FOR UPDATE no cálculo `valor_total_atualizado` |
| R-OS-10 | OS combinada (US-OS-009) com manutenção NC trava calibração indefinidamente | média | médio | resolução NC clara + cancelamento manutenção libera calibração |

---

## 13. AC operacionais (drill `validar_m3_os`)

Marco 3 só fecha quando `python manage.py validar_m3_os` retorna **PASS em 20/20 verificações**:

1. Tabela `os` existe + RLS ativa + INDEX em (tenant_id, estado, criada_em).
2. Tabela `atividade_da_os` existe + RLS + INDEX em (tenant_id, os_id, sequencia).
3. Tabela `aceite_atividade` existe + RLS + trigger anti-mutation.
4. Tabela `dispensa_aceite_atividade` existe + RLS + trigger anti-mutation.
5. Tabela `evento_de_os` existe + RLS + append-only (trigger).
6. Tabela `checklist_da_atividade` existe + RLS.
7. Tabela `tipo_atividade_config` existe + RLS + `vigencia` (JanelaVigencia).
8. Tabela `nao_conformidade_atividade` existe + RLS.
9. Sequence `os_numero_seq_<tenant>` por tenant ativo.
10. Predicates authz registrados (5+): pode_iniciar_atividade, pode_concluir_atividade, pode_cancelar_os, pode_reabrir_os, pode_dispensar_aceite.
11. Consumers ativos no procrastinate (6+): Orcamento.Aprovado, Cliente.Anonimizado, OS.Faturada, OS.Paga, Tenant.Suspenso, Equipamento.Baixado.
12. Job `os-calibracao-link-watchdog` agendado (procrastinate periodic).
13. KMS keys `BIOMETRIA_KEY_<tenant>` provisionadas por tenant ativo.
14. Producers publicam envelope v10 (event_id, _schema_version, occurred_at, correlation_id, actor).
15. Idempotência POST com Idempotency-Key (IDEMP-001) em todos endpoints mutating.
16. Hooks `vigencia-canonica`, `soft-delete-padrao`, `fk-pii-anonimizavel`, `biometria-key-validator`, `os-conclusao-todas-terminais` passam.
17. Cobertura ≥85% em `src/domain/operacao/os/` + `src/infrastructure/operacao/os/`.
18. Suite regressão `tests/regressao/test_inv_os_*.py` 100% PASS.
19. Suite sagas `tests/sagas/test_saga_*.py` 100% PASS.
20. INV-RITUAL-001 — 10 auditores Família 5 ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO.

---

## 14. Definition of Done

Marco 3 está fechado quando:

- [ ] Spec.md em `stable` (este documento).
- [ ] Plan.md revisado pelos 4 subagentes (tech-lead, advogado, corretora, RBC).
- [ ] Matriz reconciliação fecha (zero conflito entre PRD ↔ Spec ↔ Plan).
- [ ] Tasks.md com ~100 T-OS-NNN endereçando 100% dos AC + INVs + sagas.
- [ ] Código entregue + suite **≥865 passed**.
- [ ] Drill `validar_m3_os` PASS 20/20.
- [ ] `_test-runner.sh` 207/207 verdes (sem regressão em hooks).
- [ ] 10 auditores Família 5 PASS ZERO C/A/M.
- [ ] `docs/faseamento/M3-os/auditoria-familia5.md` consolidado.
- [ ] CURRENT.md atualizado.
- [ ] AGENTS.md §12 reflete M3 fechado.

---

## 15. Não-bloqueio com fases anteriores

- F-A (multi-tenant + RLS + audit + PII HMAC) — DEPENDÊNCIA DURA. ✅ FECHADA.
- F-B (auth + authz + MFA) — DEPENDÊNCIA DURA. ✅ FECHADA.
- Marco 1 (clientes) — DEPENDÊNCIA DURA (OS aponta para cliente_id + cliente_referencia_hash). ✅ FECHADO.
- Marco 2 (equipamentos) — DEPENDÊNCIA DURA (OS aponta para equipamento_id; INV-OS-EQP-001). ✅ FECHADO.
- Marco 4 (calibracao + certificados) — DEPENDÊNCIA INVERTIDA. M4 aponta para Atividade.id via `Calibracao.atividade_os_id` + watchdog INV-OS-CAL-LINK-001. M3 publica `AtividadeConcluida`; M4 consome.
- Wave A módulos paralelos (orcamentos, agenda, app-tecnico, financeiro) — INTEGRAÇÃO via eventos; M3 NÃO bloqueia construção paralela desde que envelope v10 e idempotência ADR-0033 sejam respeitados.

---

## 16. Próximo passo

P2 do ritual: `plan.md` revisado pelos **4 subagentes em paralelo**:

- `tech-lead-saas-regulado` — arquitetura (camadas, ACL, port-binding, performance N+1, watchdog).
- `advogado-saas-regulado` — LGPD biometria art. 11, RAT-07/08, DPIA-OS, anonimização Zona A/B.
- `corretora-seguros-saas` — risco operacional (R-OS-1..10), GATE-SEG-VIST-1, cobertura E&O `pareceres técnicos`.
- `consultor-rbc-iso17025` — análise crítica de pedidos cl. 7.1, NC + CAPA cl. 8.7, vínculo calibração-atividade.

Depois: matriz reconciliação + tasks.md (~100 T-OS-NNN) + implement +
10 auditores Família 5.

**Sem isso, `/implement` está PROIBIDO (INV-RITUAL-001).**
