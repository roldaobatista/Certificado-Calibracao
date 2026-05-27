---
owner: roldao
status: stable
revisado-em: 2026-05-27
proximo_review: 2026-08-27
diataxis: reference
audiencia: agente
marco: Saneamento pré-Wave A — perfil regulatório do tenant
fase-ritual: P3-aprovada (P1+P2+P3 entregues; spec absorve 13 BLOQ + 17 MÉD + 10 ALT do plan.md)
tipo: especificacao-forward
relacionados:
  - docs/faseamento/SAN-PERFIL-TENANT/plan.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/prd.md
  - docs/discovery/sintese-final.md
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0006-feature-flags.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - docs/adr/0012-autorizacao-unificada.md
  - docs/adr/0015-lifecycle-tenant.md
  - docs/adr/0019-responsabilidade-codigo-agente-ia.md
  - docs/adr/0021-anonimizacao-vs-retencao.md
  - docs/adr/0028-mapa-coberturas-wave-a.md
  - docs/adr/0030-vigencia-temporal-canonica.md
  - docs/adr/0031-soft-delete-tres-padroes.md
  - docs/adr/0024-regra-de-decisao-iso-17025.md
  - docs/adr/0025-validacao-software-iso-17025.md
  - docs/adr/0026-segunda-conferencia-independencia.md
  - docs/adr/0047-carimbo-tsa-iti-pades-ltv.md
  - docs/adr/0054-webhook-out-provider.md
  - docs/adr/0064-rotacao-chave-hmac-retencao-metrologica-25a.md
  - REGRAS-INEGOCIAVEIS.md
  - docs/faseamento/M2-equipamentos/spec.md
  - docs/faseamento/M3-os/spec.md
  - docs/faseamento/M4-calibracao/spec.md
---

# SAN-PERFIL-TENANT — Saneamento pré-Wave A — Especificação forward (P3)

## 1. Origem e justificativa

Auditoria 10 lentes em 2026-05-27 (pedido Roldão "ver se o sistema grava o tipo de empresa") detectou gap estrutural confirmado por 10/10 agentes. PRD master `docs/prd.md` §2 declara 4 perfis configuráveis (A acreditado RBC / B rastreável / C em preparação / D comercial puro) mas `src/infrastructure/tenant/models.py` não tem campo de perfil regulatório. Foundation F-A, F-B, M1, M2, F-C1, M3, M4 fecharam tratando todo tenant como genérico.

ADR-0067 (aceita 2026-05-27) decidiu manter os 4 perfis + consertar antes de Wave A. P2 do ritual rodou 4 reviews paralelos (`docs/faseamento/SAN-PERFIL-TENANT/plan.md`) e gerou 41 achados — esta spec absorve os 13 BLOQUEANTES + 17 MÉDIO + 10 ALTO.

Achados consolidados em ADR-0067 §"Achados das 10 lentes" + plan.md §"Sumário dos vereditos". Os mais graves:
- FAIL ALTO L6 — predicate `cmc_cobre` em `src/infrastructure/calibracao/predicates_calibracao.py:88` lê `tipo_acreditacao` do payload JSON. Self-attestation = fraude documental viável.
- FAIL CRÍTICO L5 — snapshot existe no nível errado (equipamento, não tenant).
- FAIL ALTO L4 — BIG-03 (trilha D→A) atravessou 7 Marcos sem código.

## 2. Escopo

### 2.1 Dentro do escopo

**Sprint 1 — Schema multi-step + retrofit dados** (T1 + R1 + T6):
- Migration `tenant/0003_perfil_regulatorio_add_nullable.py` — `ADD COLUMN perfil_regulatorio CHAR(1) NULL`.
- Migration `tenant/0004_perfil_regulatorio_backfill.py` — `RunPython` faz `SELECT FOR UPDATE` por tenant + INSERT em `TenantPerfilHistorico` com `direcao=PROVISIONAMENTO_INICIAL`. Balanças Solution = `B`.
- Migration `tenant/0005_perfil_regulatorio_not_null.py` — `SET NOT NULL` + `CHECK (perfil_regulatorio IN ('A','B','C','D'))`.
- Migration `tenant/0006_acreditacao_cgcre_campos.py` — `acreditacao_cgcre_numero VARCHAR(20) NULL`, `acreditacao_suspensa_em DATE NULL`, `acreditacao_suspensa_ate DATE NULL`, `ilac_mra_aderido BOOLEAN NOT NULL DEFAULT FALSE`.
- Tabela `TenantPerfilHistorico` (append-only + RLS + trigger anti-mutação) — enum direcao com 7 valores (R3 + A1).
- Função SECURITY DEFINER `aplicar_evento_cgcre(direcao, ...)` (substitui `promover/rebaixar` da spec original — máquina de estados).
- Função SECURITY DEFINER `rebaixar_perfil_tenant_voluntario_cliente()` (A1) com cooldown 30 dias.
- Outbox: evento `TenantPerfilAlterado` emitido em transação SECURITY DEFINER (S2).
- Hook `tenant-perfil-imutavel-check.sh`.
- **Ordem cross-app:** tenant/0003 → 0004 → 0005 → 0006 → audit/00XX → calibracao/00XX → os/00XX → equipamentos/00XX (T6).

**Sprint 2 — Predicate canônico + retrofit fraude L6 + migração testes M4** (T2 + T3):
- Predicate `tenant_perfil_e(perfis_aceitos)` em `src/infrastructure/authz/predicates.py`. **Fail-closed via ContextVar** + timeout 50ms.
- Retrofit `cmc_cobre`: consulta tenant (não payload).
- Predicate invocado nos 6 use cases críticos.
- Compat-shim payload obsoleto + hook `payload-tipo-acreditacao-obsoleto-check`.
- Fixture `tenant_a/b/c/d` em `conftest.py`. `TenantFactory.perfil_X()` traits.
- ≥40 testes retrofitados + ≥20 testes regressão UNHAPPY.
- INVs `INV-TENANT-PERFIL-001..007` em `REGRAS-INEGOCIAVEIS.md`.

**Sprint 3 — Provisioning + PDF CGCRE + capacidade contratual + verificação periódica** (A5/S4 + A6 + S5):
- Comando `provisionar_tenant --perfil {A|B|C|D} --motivo "..."` em `src/infrastructure/tenant/management/commands/`.
- Para `--perfil A`: exige `--numero-rbc` (regex `^CRL \d{4}(-\d{2})?$`) + `--certificado-acreditacao-pdf-path` + `--auditor-cgcre-nome` + `--processo-cgcre-numero` (A5/S4).
- Emenda ADR-0015 (state machine — etapa 0).
- `AFERE_OPERADOR_HUMANO_CPF` + nome obrigatório em env; modo IA exige `--autorizado-por-roldao-issue-id` (A6).
- Job mensal `verificar_vigencia_acreditacao_perfil_a` (S5) — alerta 60 dias antes de expirar.
- Documento `docs/conformidade/comum/matriz-feature-perfil.md`.
- Hook `feature-perfil-matriz-validator.sh`.

**Sprint 4 — Snapshot WORM + evidência defensiva pré-saneamento** (T4 + A4 + R7):
- `Equipamento.perfil_tenant_snapshot` deixa de ser auto-declarado → COPY de `Tenant.perfil_regulatorio`.
- Coluna `perfil_no_evento CHAR(1) NOT NULL` em `auditoria` + `evento_de_calibracao` + `evento_de_os` via `GENERATED ALWAYS AS ... STORED` (não dispara trigger anti-mutação).
- Coluna `escopos_acreditados_vigentes_no_momento JSONB NOT NULL DEFAULT '[]'` em `evento_de_calibracao` + `certificado` (snapshot quando `perfil_no_evento='A'`) (R7).
- Relatório `validar_san_perfil_tenant_eventos_historicos` (CSV+A3) listando eventos pré-saneamento (A4).
- Drill `validar_san_perfil_tenant_snapshots`.

**Sprint 5 (Wave A módulo `certificados`) — Templates por perfil + TSA-ITI condicional** (R9):
- 4 templates obrigatórios; ILAC-MRA só com `tenant.ilac_mra_aderido=TRUE`.
- Pre-flight check em `emitir_certificado`.
- Hook `template-perfil-d-anti-iso.sh` + hook irmão `template-ilac-mra-coerencia.sh`.

**Sprint 6 (Wave A módulo `onboarding` + `direitos-titular` + LGPD)** — Coleta perfil UX + aviso titular D→A + base legal nomeada + export evidência sinistro + cobrança contratual.
- US-SAN-PERFIL-007 aviso titular (A3).
- AC base legal nomeada na recusa (A2).
- Export evidência sinistro (S3).
- Trilha D→A controlada pelo RT do tenant, não Aferê (A7).
- Cláusula "Mudança de perfil" no termo de uso (A1).

### 2.2 Fora do escopo (non-goals)

- NÃO decidir se trilha D→A é automática ou manual no use case workflow — diferido pra Wave A módulo `onboarding` com decisão "RT do tenant decide" (A7).
- NÃO tratar matriz A + filial B multi-filial — diferido para Discovery pós-1º tenant multi-filial.
- NÃO entregar UX/telas de mudança de perfil — Wave A.
- NÃO fechar layout PDF dos templates de certificado — Wave A módulo `certificados`.
- NÃO entregar dashboards "trilha D→A taxa de conversão" — F-C2 observabilidade.
- **NÃO modelar escopo CGCRE** (grandeza × faixa × CMC × vigência por escopo) — responsabilidade do módulo `licencas-acreditacoes` Wave A. Esta spec só persiste perfil agregado (R1).
- **NÃO toca apólice BPT** (ADR-0028 mod 4 — depositário CC art. 627) — BPT é independente do perfil (S8).
- **NÃO modela subestados C1..C5 da trilha D→A** — `licencas-acreditacoes` Wave A (R4).

## 3. User stories

### US-SAN-PERFIL-001 — Sistema persiste perfil regulatório por tenant (entidade temporal)

**Como** dono da plataforma Aferê,
**Quero** que cada tenant tenha um perfil regulatório persistido (A/B/C/D) com trilha histórica imutável,
**Para** evitar fraude documental (FAIL L6), habilitar BIG-03 (trilha D→A) e separar PII de hash-chain WORM.

**Critérios de aceite (binários):**

- **AC-SAN-PERFIL-001-1a** — Migration `tenant/0003_perfil_regulatorio_add_nullable.py` adiciona `Tenant.perfil_regulatorio CHAR(1) NULL`. Migration idempotente (re-run no-op).
- **AC-SAN-PERFIL-001-1b** — Migration `tenant/0004_perfil_regulatorio_backfill.py` faz `RunPython`: `SELECT FOR UPDATE` em todos tenants existentes + UPDATE com perfil + INSERT em `TenantPerfilHistorico` com `direcao=PROVISIONAMENTO_INICIAL` + `motivo` ≥100 chars. Balanças Solution = `B` justificado em `motivo`. Falha do step preserva sistema em estado degraded operável.
- **AC-SAN-PERFIL-001-1c** — Migration `tenant/0005_perfil_regulatorio_not_null.py` faz `ALTER COLUMN SET NOT NULL` + `CHECK (perfil_regulatorio IN ('A','B','C','D'))`. PG ENUM type NÃO é usado (custo de ALTER TYPE em produção); CHAR+CHECK é a escolha (T8). Enum de domínio em `src/domain/tenant/enums.py` é fonte da verdade.
- **AC-SAN-PERFIL-001-1d** — Migration `tenant/0006_acreditacao_cgcre_campos.py` adiciona `acreditacao_cgcre_numero VARCHAR(20) NULL` + `acreditacao_suspensa_em DATE NULL` + `acreditacao_suspensa_ate DATE NULL` + `ilac_mra_aderido BOOLEAN NOT NULL DEFAULT FALSE`. Não adiciona `acreditacao_vigencia_inicio/fim` (R1 — vigência por escopo migra para `licencas-acreditacoes` Wave A).
- **AC-SAN-PERFIL-001-1e** — Quando `perfil_regulatorio = 'A'`, `acreditacao_cgcre_numero` valida regex `^CRL \d{4}(-\d{2})?$` em `Tenant.clean()` + erro `NumeroRBCFormatoInvalido` (R2).
- **AC-SAN-PERFIL-001-2** — Tabela nova `TenantPerfilHistorico` (shared-across-tenants, padrão ADR-0002 §8) com campos do schema ADR-0067 §1 + direção expandida:
  - `direcao ENUM{PROVISIONAMENTO_INICIAL, PROMOCAO_REGULATORIA, SUSPENSAO_TEMPORARIA_CGCRE, CANCELAMENTO_CGCRE, REDUCAO_ESCOPO_CGCRE, CORRECAO_ADMINISTRATIVA, REBAIXAMENTO_VOLUNTARIO_CLIENTE}` (R3 + A1).
  - Append-only + trigger anti-mutação estilo `auditoria_anti_*`.
- **AC-SAN-PERFIL-001-3** — UPDATE direto em `tenants.perfil_regulatorio` fora das 2 funções SECURITY DEFINER falha com trigger raise "Mutação proibida — use aplicar_evento_cgcre ou rebaixar_perfil_tenant_voluntario_cliente".
- **AC-SAN-PERFIL-001-4** — `Tenant.perfil_vigente()` retorna perfil atual via cache `perfil_tenant_context` (ContextVar populado pelo middleware). Cache miss = re-fetch com timeout 50ms.
- **AC-SAN-PERFIL-001-4b** — Benchmark `tests/perf/test_perfil_tenant_lookup.py` mede p95 ≤5ms em PG real (5k tenants seeded). GATE-TENANT-PERFIL-PERF Wave A se p95 >5ms (T7).
- **AC-SAN-PERFIL-001-5** — Hook `tenant-perfil-imutavel-check.sh` bloqueia migration nova que altere `tenant.perfil_regulatorio` fora das 2 funções SECURITY DEFINER.
- **AC-SAN-PERFIL-001-6** — Funções SECURITY DEFINER `aplicar_evento_cgcre(direcao, ...)` e `rebaixar_perfil_tenant_voluntario_cliente()` INSERT em outbox event `TenantPerfilAlterado` na mesma transação da mutação. Payload anonimizado (slug hash + perfil_anterior + perfil_novo + direcao + registrado_em + assinatura_a3_id). Sem PII (S2 + A8).
- **AC-SAN-PERFIL-001-7** — Drill `validar_san_perfil_tenant_migrations` aplica migrations em ambiente zerado E em ambiente já-M4; ambos terminam idênticos (schema snapshot + COUNT TenantPerfilHistorico igual). Migration declara `dependencies=[...]` explícito (T6).
- **AC-SAN-PERFIL-001-8** — Matriz de transições válidas (T11):
  - Promoção UP-only monotônica: D→C, C→B, B→A. Jumps (ex: D→A) = 3 promoções separadas com motivo cada.
  - Suspensão temporária: A → A com flag `acreditacao_suspensa_em/ate` (preserva perfil).
  - Cancelamento CGCRE: A → B.
  - Rebaixamento voluntário cliente: B→D, B→C, C→D (apenas para baixo; cooldown 30 dias entre rebaixamentos).
- **AC-SAN-PERFIL-001-9** — Função `rebaixar_perfil_tenant_voluntario_cliente()` (A1):
  - Cooldown ≥30 dias entre rebaixamentos voluntários (raise `RebaixamentoEmCooldown` se violado).
  - Pré-aviso obrigatório (parâmetro `confirmado_pelo_tenant_em` ≥7 dias antes da chamada).
  - INSERT em outbox `TenantRebaixamentoVoluntarioPrePosicionado` para notificar AdmAferê (suporte).
  - Cláusula "Mudança de perfil regulatório" no termo de uso é pré-requisito (Sprint 6 Wave A).
- **AC-SAN-PERFIL-001-10** — `TenantPerfilHistorico.motivo` passa por `sanitizar_payload_audit()` antes do INSERT (A8). View materializada `tenant_perfil_historico_titular(titular_cpf_hash)` retorna apenas linhas onde titular foi referenciado, com RLS forte. (Sprint 6.)

### US-SAN-PERFIL-002 — Predicate canônico bloqueia fraude L6 com graceful degradation

**Como** auditor regulatório,
**Quero** que o sistema bloqueie operadores que tentem emitir certificado RBC quando o tenant não é Perfil A,
**Para** evitar fraude documental cofabricada pela plataforma.

**Critérios de aceite (binários):**

- **AC-SAN-PERFIL-002-1** — Predicate `tenant_perfil_e(perfis_aceitos)` registrado em `authz_predicates` retorna `(False, "tenant_perfil_nao_autorizado: {perfil_atual} ∉ {aceitos}")` quando perfil ∉ conjunto.
- **AC-SAN-PERFIL-002-2** — `cmc_cobre` (`src/infrastructure/calibracao/predicates_calibracao.py`) deixa de ler `resource["tipo_acreditacao"]`; passa a consultar via `perfil_tenant_context`. Quando operador envia `tipo_acreditacao=RBC` no payload mas tenant ≠ A, sistema responde 412 `TipoAcreditacaoDivergenteDoTenant` + registra evento `tentativa_downgrade_perfil` em auditoria WORM.
- **AC-SAN-PERFIL-002-3** — `emitir_certificado_rbc` invoca `tenant_perfil_e({"A"})` AND verifica `acreditacao_suspensa_em IS NULL OR today > acreditacao_suspensa_ate` AND delega vigência por escopo a `escopo_cgcre_cobre(grandeza, faixa)` (módulo `licencas-acreditacoes` Wave A — fail-open lazy padrão ADR-0063/0066 enquanto módulo não existir).
- **AC-SAN-PERFIL-002-4** — `aprovar_2a_conferencia` invocação refinada (R5): perfil A **AND** `regra_decisao.modo != NENHUMA` → 2ª conferência obrigatória; perfil A **AND** `regra_decisao.modo == NENHUMA` → recomendada (warning, não bloqueio); B/C → opcional; D → desabilitado. Predicate `requer_segunda_conferencia(certificado_id)` em `metrologia/calibracao`.
- **AC-SAN-PERFIL-002-5** — Predicate ContextVar + timeout 50ms (T2):
  - Cache hit (ContextVar resolvido pelo middleware) = retorna direto.
  - Cache miss = re-fetch com `select_for_share` + timeout 50ms.
  - Timeout/erro DB = DENY com reason `tenant_perfil_indisponivel` + log WARN.
  - Linha `perfil_regulatorio IS NULL` (estado inválido pós-backfill) = DENY com reason `tenant_perfil_nao_definido` + log ERROR + alerta.
  - NÃO usa retry/circuit-breaker.
- **AC-SAN-PERFIL-002-6** — ≥20 testes regressão UNHAPPY path em `tests/regressao/test_inv_tenant_perfil_001..007.py`.
- **AC-SAN-PERFIL-002-7** — Predicate `tenant_perfil_e({"A"})` retorna False se `acreditacao_suspensa_em IS NOT NULL AND today < acreditacao_suspensa_ate` (R3).
- **AC-SAN-PERFIL-002-7b** — Evento `TenantPerfilAlterado` com `direcao=CANCELAMENTO_CGCRE` adiciona flag `notifica_d_e_o=true` para consumer S2 (corretora prepara reservation of rights ≤30d).
- **AC-SAN-PERFIL-002-8** — Predicate é consultado UMA vez por request via ContextVar — elimina N+1 (T2).

### US-SAN-PERFIL-003 — Snapshot `perfil_no_evento` + escopos vigentes preservam contexto WORM

**Como** auditor CGCRE em auditoria retroativa 2030,
**Quero** consultar perfil + escopos do tenant no momento exato de cada evento histórico,
**Para** que mudança de perfil futura não corrompa defesa de eventos antigos. (NIT-DICLA-030 rev. 15 item 8.2.6 + ISO 17025 cl. 8.4.2.)

**Critérios de aceite (binários):**

- **AC-SAN-PERFIL-003-1** — Coluna `perfil_no_evento CHAR(1) NOT NULL` adicionada em `auditoria` + `evento_de_calibracao` + `evento_de_os` via `GENERATED ALWAYS AS ((SELECT perfil_regulatorio FROM tenants WHERE id = NEW.tenant_id)) STORED`. Após backfill completo, `DROP EXPRESSION` + manter coluna como CHAR(1) NOT NULL comum (T4). Não dispara trigger anti-mutação porque não emite UPDATE.
- **AC-SAN-PERFIL-003-1b** — Coluna `escopos_acreditados_vigentes_no_momento JSONB NOT NULL DEFAULT '[]'` adicionada em `evento_de_calibracao` + `certificado`. Quando `perfil_no_evento='A'`, snapshot inclui array de `{grandeza, faixa, vigencia_inicio, vigencia_fim, numero_rbc}` lido de `licencas-acreditacoes`. Fail-open lazy '[]' até módulo Wave A existir (R7).
- **AC-SAN-PERFIL-003-2** — `registrar_auditoria()` lê `perfil_tenant_context` (ContextVar setado pelo middleware) e crava no evento. NÃO faz SELECT direto em Tenant no INSERT (preserva fidelidade temporal e elimina N+1).
- **AC-SAN-PERFIL-003-2b** — Hook `metrology-replay-fixtures-versionadas` (já existente) estendido para validar que toda fixture de `evento_de_calibracao` tem `perfil_no_evento` cravado a partir de ContextVar (T9).
- **AC-SAN-PERFIL-003-3** — Backfill via GENERATED conforme AC-003-1. Drill `validar_san_perfil_tenant_snapshots` reporta 100% preenchidos.
- **AC-SAN-PERFIL-003-4** — Trigger anti-mutação em `auditoria.perfil_no_evento` herda da trigger geral `auditoria_anti_*`.
- **AC-SAN-PERFIL-003-5** — `TenantMiddleware` popula `perfil_tenant_context` ao ativar tenant em `src/infrastructure/multitenant/middleware.py`.
- **AC-SAN-PERFIL-003-6** — Relatório `validar_san_perfil_tenant_eventos_historicos` (A4) gera CSV assinado A3 listando todos os eventos cravados entre 2026-05-17 (início Marco 1) e Sprint 4-merge contendo `(event_id, tenant_id, tipo_acreditacao_declarado, perfil_no_evento_backfill)`. Roldão arquiva em B2 WORM como evidência defensiva em `docs/governanca/evidencia-defensiva/`.

### US-SAN-PERFIL-004 — Comando provisionar_tenant exige perfil + evidência documental + responsável humano

**Como** operador da plataforma Aferê,
**Quero** comando rigoroso de provisionamento que exija evidência documental e responsável humano nomeado,
**Para** evitar fraude na declaração inicial (falsidade material que pode invalidar apólice E&O).

**Critérios de aceite (binários):**

- **AC-SAN-PERFIL-004-1** — Comando `python manage.py provisionar_tenant --slug X --nome-fantasia "..." --perfil {A|B|C|D} --motivo "..." [...]` em `src/infrastructure/tenant/management/commands/`.
- **AC-SAN-PERFIL-004-2** — Provisioning falha com `MissingPerfilRegulatorio` se `--perfil` ausente. Sem default.
- **AC-SAN-PERFIL-004-3** — Provisioning falha com `JustificativaMuitoCurta` se `--motivo` <100 chars.
- **AC-SAN-PERFIL-004-4** — Provisioning cria 1 linha em `TenantPerfilHistorico` direção `PROVISIONAMENTO_INICIAL` + 1 linha em `auditoria` ação `tenant.provisionado`.
- **AC-SAN-PERFIL-004-5** — Se `--perfil A`, exige adicionalmente (A5/S4):
  - `--numero-rbc` (regex `^CRL \d{4}(-\d{2})?$`).
  - `--certificado-acreditacao-pdf-path` (PDF do certificado CGCRE; upload em B2 com hash SHA-256 + assinatura A3 do Roldão).
  - `--auditor-cgcre-nome` (nome do auditor CGCRE responsável pela deliberação).
  - `--processo-cgcre-numero` (número do processo CGCRE).
  - `--ilac-mra-aderido` (boolean explícito).
  - O `certificado_acreditacao_documento_id` (FK) é cravado em `TenantPerfilHistorico`.
- **AC-SAN-PERFIL-004-6** — Comandos `popular_drill.py` retrofitados para passar `--perfil B` explícito (Balanças Solution).
- **AC-SAN-PERFIL-004-7** — Comando exige variáveis de ambiente `AFERE_OPERADOR_HUMANO_CPF` + `AFERE_OPERADOR_HUMANO_NOME` registradas em auditoria (A6). Em modo agente IA exige flag `--autorizado-por-roldao-issue-id` apontando issue GitHub aprovada manualmente — vincular a ADR-0019.
- **AC-SAN-PERFIL-004-8** — Job mensal `verificar_vigencia_acreditacao_perfil_a` (S5): itera tenants Perfil A, valida que `acreditacao_cgcre_numero` está vigente em `licencas-acreditacoes` (Wave A — fail-open quando módulo não existe), alerta operador 60 dias antes da vigência expirar. Defesa contra alegação de má-fé.

### US-SAN-PERFIL-005 — Matriz feature × perfil + retenção em camadas

**Como** desenvolvedor adicionando nova feature crítica,
**Quero** declarar comportamento por perfil em documento canônico com matriz de retenção em camadas,
**Para** que ninguém esqueça os 4 perfis e o conflito HMAC vs PII fique explícito.

**Critérios de aceite (binários):**

- **AC-SAN-PERFIL-005-1** — Documento `docs/conformidade/comum/matriz-feature-perfil.md` criado em status `stable`.
- **AC-SAN-PERFIL-005-2** — Matriz lista, por feature crítica, comportamento por perfil: `OBRIGATORIO` / `OBRIGATORIO_PARCIAL` / `OPCIONAL_RECOMENDADO` / `OPCIONAL` / `DESABILITADO`.
- **AC-SAN-PERFIL-005-3** — Hook `feature-perfil-matriz-validator.sh` (T12 — reescrito): bloqueia commit de PRD novo (`docs/dominios/.../prd.md`) ou ADR novo que adicione US-XXX ou AC binário em feature listada na matriz. Match por path + grep `US-` no diff, não palavra "feature" no título.
- **AC-SAN-PERFIL-005-4** — Matriz cobre mínimo:
  - **Regra de decisão 7.8.6 (ADR-0024)**: A=OBRIGATORIO / B/C=OPCIONAL / D=DESABILITADO.
  - **2ª conferência (ADR-0026)**: A=OBRIGATORIO se modo≠NENHUMA / B/C=OPCIONAL / D=DESABILITADO (R5).
  - **Validação software 7.11 (ADR-0025)** (R6): A=OBRIGATORIO_FULL_URS_IQ_OQ_PQ / B=OPCIONAL_RECOMENDADO_URS / C=OBRIGATORIO_PARCIAL_URS_OQ (gate trilha D→A) / D=DESABILITADO.
  - **TSA-ITI qualificado (ADR-0047)**: A=OBRIGATORIO / B/C=OPCIONAL / D=DESABILITADO.
  - **Selo ILAC-MRA (R9)**: A=OBRIGATORIO se `ilac_mra_aderido=TRUE` / A=DESABILITADO se `ilac_mra_aderido=FALSE` / B/C/D=DESABILITADO.
  - **A3 obrigatório (ADR-0009)**: A=OBRIGATORIO / B/C/D=OPCIONAL_RECOMENDADO.
  - **GUM/MC**: A/B/C=OBRIGATORIO / D=OPCIONAL.
- **AC-SAN-PERFIL-005-5** — Matriz de **retenção em camadas** (R10):

| Camada | A | B | C | D |
|---|---|---|---|---|
| **PII cliente/titular** (ADR-0021 zonas) | 25a (ISO 8.4) | 25a (recomendado) | 25a | **5a (Receita) + anonimização** |
| **Eventos WORM hash-chain** (INV-HMAC-001..005) | 25a (invariante) | 25a (invariante) | 25a (invariante) | **25a (invariante)** |
| **Geo-truncamento** (job `geo_truncamento_calibracao_5a`) | NUNCA trunca | 5a | 5a | 5a + anonimização |

Hash-chain WORM SEMPRE 25a (INV-HMAC vence). PII Perfil D anonimizada em 5a. Documentar em ADR-0021 §nova "Camadas de retenção condicional por perfil" antes do Sprint 6.

- **AC-SAN-PERFIL-005-6** — Job `geo_truncamento_calibracao_5a` ganha predicate `tenant.perfil_regulatorio`. Perfil A: NUNCA trunca. Perfil B/C/D: trunca 5a com anonimização agressiva para D.
- **AC-SAN-PERFIL-005-7** — Linha matriz "verificação periódica acreditação" (S5): Perfil A = job mensal valida vigência, alerta 60 dias antes; B/C/D = N/A.

### US-SAN-PERFIL-006 — Migração suite de testes M4 + compat-shim

**Como** mantenedor da suite,
**Quero** que retrofit do predicate canônico não quebre a suite 629/629,
**Para** preservar INV-RITUAL-001 (causa-raiz, nunca mascarar).

**Critérios de aceite (binários):**

- **AC-SAN-PERFIL-006-1** — Fixture `tenant_a/b/c/d` em `conftest.py` raiz. `TenantFactory` ganha traits factory-boy `.perfil_a()` `.perfil_b()` `.perfil_c()` `.perfil_d()`.
- **AC-SAN-PERFIL-006-2** — Testes M4 que literalizam `tipo_acreditacao=RBC` no payload (≥67 ocorrências) retrofitados para usar fixture `tenant_a`.
- **AC-SAN-PERFIL-006-3** — Compat-shim: se payload AINDA mandar `tipo_acreditacao`, predicate IGNORA + loga WARN `payload_tipo_acreditacao_obsoleto`. Compat-shim vigora por 1 Marco (Sprint 2 → fim de Wave A módulo `certificados`). Após esse marco, hook bloqueia novo uso.
- **AC-SAN-PERFIL-006-4** — Hook `payload-tipo-acreditacao-obsoleto-check.sh` bloqueia commit de código novo que use o campo (T3).
- **AC-SAN-PERFIL-006-5** — Marcador `@pytest.mark.perfil("A")` + parametrize matrix em testes que tocam regras ISO 17025. Mínimo 40 testes M4 retrofitados, 20 M3, 10 M2.
- **AC-SAN-PERFIL-006-6** — Drill final da suite: pytest count após retrofit é ≥629/629 verde + ≥40 novos. Suite total alvo ≥669.

### US-SAN-PERFIL-007 — Aviso ao titular em promoção D→A (LGPD art. 9)

**Como** titular vinculado a tenant que promove de D para A,
**Quero** ser notificado sobre a mudança de retenção (5a → 25a),
**Para** entender o impacto e meus direitos (LGPD art. 9 + 18 IX).

**Critérios de aceite (binários):**

- **AC-SAN-PERFIL-007-1** — Consumer `notificar_titulares_mudanca_retencao_d_para_a` consome evento `TenantPerfilAlterado` com `direcao=PROMOCAO_REGULATORIA` AND `perfil_anterior IN ('D', 'C', 'B')` AND `perfil_novo='A'`.
- **AC-SAN-PERFIL-007-2** — Job assíncrono identifica titulares com dados ativos no tenant + envia notificação via email/SMS: "Sua prestadora foi acreditada CGCRE — seus dados de calibração agora têm retenção 25a por força da ISO 17025 cl. 8.4. Direitos LGPD preservados em modo restrito — contate DPO@..."
- **AC-SAN-PERFIL-007-3** — Janela: 15 dias antes da promoção efetivar OU 5 dias úteis após (se promoção urgente).
- **AC-SAN-PERFIL-007-4** — Resposta padrão de recusa de eliminação para titular vinculado a tenant Perfil A traz literalmente (A2 — base legal nomeada):
  - LGPD art. 16 II (cumprimento de obrigação legal/regulatória — ISO 17025 cl. 8.4 + RBC CGCRE NIT-DICLA-016) + ADR-0021 zona B.
  - Nº RBC + vigência da acreditação na época.
  - Prazo após o qual eliminação fica possível (25a) com data exata.
  - Canal de contestação DPO.
  - Menção que dados foram anonimizados-em-lugar para zona B.
- **AC-SAN-PERFIL-007-5** — Template `docs/runbooks/dpo-encarregado-resposta-padrao.md` antecipado em Sprint 3 mesmo que Wave A ainda não implemente o módulo.

### US-SAN-PERFIL-008 — Exportação trimestral de distribuição book para subscrição

**Como** dono da plataforma Aferê em renovação anual da apólice E&O+Cyber+D&O,
**Quero** gerar relatório trimestral de distribuição do book por perfil regulatório assinado,
**Para** que corretora SUSEP submeta à seguradora cumprindo cláusula `material change` (Lei 4.594/64 + CNSP) e evite negativa de sinistro por subdeclaração.

**Critérios de aceite (binários):**

- **AC-SAN-PERFIL-008-1** — Comando `python manage.py exportar_distribuicao_perfil_seguradora --trimestre YYYY-Q` produz CSV agregado (sem PII) + PDF/A-3 assinado A3 com 4 linhas (A/B/C/D) + delta vs trimestre anterior + total.
- **AC-SAN-PERFIL-008-2** — Saída inclui hash SHA-256 do conteúdo + carimbo TSA-ITI PAdES-LTV (ADR-0047) para evidência probatória.
- **AC-SAN-PERFIL-008-3** — Job procrastinate trimestral agendado (cron `0 0 1 1,4,7,10 *`) executa e envia para fila outbox webhook corretora.
- **AC-SAN-PERFIL-008-4** — Retenção do arquivo 25a (B2 WORM).

### US-SAN-PERFIL-009 — Export evidência sinistro (Sprint 6 Wave A)

**Como** corretora SUSEP da Aferê em sinistro real,
**Quero** dossiê assinado contendo histórico de perfis + hash-chain do tenant em janela específica,
**Para** defesa contra alegação de subdeclaração ou falsidade documental (S3).

**Critérios de aceite (binários):**

- **AC-SAN-PERFIL-009-1** — Comando `exportar_historico_perfil_evidencia_sinistro --tenant <id> --janela <data_inicio> <data_fim>` produz dossiê PDF/A-3 com:
  - Hash-chain WORM da janela + TSA-ITI PAdES-LTV (ADR-0047).
  - XML estruturado com cada linha de `TenantPerfilHistorico`.
  - Assinatura A3 do gestor (Roldão até Wave A; depois admin Aferê designado).
- **AC-SAN-PERFIL-009-2** — Sprint 6 Wave A — não bloqueia P5 desta spec.

## 4. INVs novas em REGRAS-INEGOCIAVEIS.md

- **INV-TENANT-PERFIL-001** — Toda função de aplicação que decide rituais ISO 17025 invoca `tenant_perfil_e(...)` consultando `Tenant.perfil_regulatorio` via `perfil_tenant_context`. **Proibido** ler `tipo_acreditacao` ou similar do payload da request como fonte primária.
- **INV-TENANT-PERFIL-002** — `Tenant.perfil_regulatorio` é mutável APENAS via funções SECURITY DEFINER `aplicar_evento_cgcre(direcao, ...)` (CGCRE) e `rebaixar_perfil_tenant_voluntario_cliente()` (autonomia tenant). UPDATE direto = trigger raise.
- **INV-TENANT-PERFIL-003** — Toda tabela WORM (`auditoria`, `evento_de_*`, `certificado`) tem coluna `perfil_no_evento CHAR(1) NOT NULL` cravada via GENERATED ALWAYS AS ... STORED OU lida de `perfil_tenant_context` no momento do INSERT (Sprint 4 escolhe um e crava em P4).
- **INV-TENANT-PERFIL-004** — Predicate `tenant_perfil_e` é **fail-closed** com timeout 50ms. Falha de consulta = nega. Nunca fail-open silencioso. Eliminação N+1 via ContextVar obrigatória.
- **INV-TENANT-PERFIL-005** — Tenant não pode ser criado sem perfil definido. Default implícito = erro. Comando `provisionar_tenant` exige `--perfil` explícito + justificativa ≥100 chars. Perfil A exige adicionalmente PDF certificado CGCRE + número RBC + auditor + processo.
- **INV-TENANT-PERFIL-006** — Toda mutação em `Tenant.perfil_regulatorio` emite evento `TenantPerfilAlterado` em outbox transacional. Webhook out para corretora SUSEP é obrigatório em `direcao ∈ {PROMOCAO_REGULATORIA, CANCELAMENTO_CGCRE, SUSPENSAO_TEMPORARIA_CGCRE, REBAIXAMENTO_VOLUNTARIO_CLIENTE}`. `PROVISIONAMENTO_INICIAL` + `CORRECAO_ADMINISTRATIVA` + `REDUCAO_ESCOPO_CGCRE` consolidam no relatório trimestral (US-008).
- **INV-TENANT-PERFIL-007** — Provisioning Perfil A só fecha com:
  - PDF documento CGCRE anexado (com hash SHA-256 + A3 do Roldão).
  - Número RBC validando regex `^CRL \d{4}(-\d{2})?$`.
  - Job mensal de verificação de vigência ativo em `licencas-acreditacoes` (Wave A — checkpoint na ausência).
  - `ilac_mra_aderido` declarado explicitamente.

## 5. Hooks novos

- `tenant-perfil-imutavel-check.sh` — bloqueia migration ou UPDATE direto em `tenants.perfil_regulatorio` fora das 2 funções SECURITY DEFINER.
- `feature-perfil-matriz-validator.sh` (T12 reescrito) — bloqueia commit de PRD/ADR novo com US ou AC em feature listada na matriz `docs/conformidade/comum/matriz-feature-perfil.md` sem entrada correspondente. Match por path + grep `US-` no diff.
- `payload-tipo-acreditacao-obsoleto-check.sh` — bloqueia código novo que use `tipo_acreditacao` no payload da request (T3 — após fim do compat-shim).
- `template-perfil-d-anti-iso.sh` (Sprint 5 Wave A) — bloqueia template de certificado Perfil D que contenha "ISO 17025".
- `template-ilac-mra-coerencia.sh` (Sprint 5 Wave A) — bloqueia template com selo ILAC-MRA quando `tenant.ilac_mra_aderido=FALSE` (R9).

## 6. Gates Wave A rastreados

- `GATE-TENANT-PERFIL-SCHEMA` — Sprint 1 (migration 3-step + TenantPerfilHistorico + funções SECURITY DEFINER).
- `GATE-TENANT-PERFIL-PROVISIONING` — Sprint 3 (comando + emenda ADR-0015 etapa 0 + matriz feature×perfil).
- `GATE-TENANT-PERFIL-AUTHZ-PREDICATE` — Sprint 2 (predicate + retrofit `cmc_cobre` fechando FAIL L6).
- `GATE-TENANT-PERFIL-TESTES-MATRIZ` — Sprint 2 + cross-sprints (US-006 + 40 testes parametrizados).
- `GATE-TENANT-PERFIL-MATRIZ-RETENCAO` — Sprint 6 Wave A (emenda ADR-0021 + DRILL-RET-12/13).
- `GATE-TENANT-PERFIL-TEMPLATES-CERT` — Sprint 5 Wave A módulo `certificados`.
- `GATE-TENANT-PERFIL-OBSERVABILIDADE` — Sprint 4 (snapshot `perfil_no_evento`) + F-C2 (label `perfil_tenant` em structlog).
- `GATE-TENANT-PERFIL-CONCORRENCIA-PROMOCAO` — Sprint 1 (advisory lock `pg_advisory_xact_lock`) (T5).
- `GATE-TENANT-PERFIL-CERT-SNAPSHOT` — Sprint 5 Wave A (snapshot `escopos_acreditados_vigentes_no_momento` em certificados) (T13).
- `GATE-TENANT-PERFIL-DRILL-PG-REAL` — Wave A (drill em PG real, não SQLite) (T14).
- `GATE-TENANT-PERFIL-EVIDENCIA-EVENTOS-PRE-SANEAMENTO` — Sprint 4 (relatório A4 — defesa retroativa de eventos cravados pré-saneamento).
- `GATE-TENANT-PERFIL-PDF-CERT-CGCRE` — Sprint 3 (A5+S4 — exigir PDF certificado em provisionamento A).
- `GATE-TENANT-PERFIL-EXPORT-EVIDENCIA-SINISTRO` — Sprint 6 Wave A (US-009) (S3).
- `GATE-TENANT-PERFIL-VERIFICACAO-PERIODICA-VIGENCIA` — Sprint 3 (job mensal AC-004-8) (S5).
- `GATE-TENANT-PERFIL-WEBHOOK-CORRETORA` — Sprint 2/3 (webhook out + drill mock saneamento; real em Wave A com contrato firmado) (S2).
- `GATE-TENANT-PERFIL-SNAPSHOT-ESCOPOS-VIGENTES` — Sprint 4 (AC-003-1b — JSONB) (R7).
- `GATE-LICENCAS-SUBESTADOS-C1-C5` — Wave A módulo `licencas-acreditacoes` (subestados trilha D→A) (R4).
- `GATE-TENANT-PERFIL-PERF` — Wave A (benchmark p95 ≤5ms em PG real) (T7).

## 7. Critérios de saída do saneamento (P5 ritual)

- 10 auditores Família 5 — todos PASS ZERO CRÍTICO/ALTO/MÉDIO em 2ª passada.
- Suite pytest ≥669/669 verde (629 atual + ≥40 novos).
- Drill `validar_san_perfil_tenant` ≥30 checks 100% verde:
  - Schema (4 colunas Tenant + 1 tabela histórico + trigger imutabilidade).
  - 2 funções SECURITY DEFINER (aplicar_evento_cgcre + rebaixar_voluntario).
  - 7 direções de transição (PROVISIONAMENTO + PROMOCAO + 3 CGCRE + CORRECAO + REBAIXAMENTO_VOLUNTARIO).
  - Matriz transições válidas (8 ACs em AC-001-8).
  - Snapshot `perfil_no_evento` em 4 tabelas WORM via GENERATED.
  - Snapshot `escopos_acreditados_vigentes_no_momento` JSONB.
  - Predicate consulta tenant via ContextVar (não payload).
  - Comando provisionar exige flags + PDF CGCRE para A.
  - Matriz feature×perfil ≥7 entradas mínimas.
  - Matriz retenção em camadas explícita.
  - Hooks 5 novos verde no `_test-runner.sh`.
  - Job mensal `verificar_vigencia_acreditacao_perfil_a` ativo.
  - Outbox event `TenantPerfilAlterado` emitido em 5 das 7 direções.
- ADR-0067 status `aceito` (já marcado 2026-05-27).
- ADR-0021 emenda "Camadas de retenção condicional por perfil" aceita.
- Hook `_test-runner.sh` cobertura ≥385 casos (379 atual + ≥6 novos hooks).
- Nenhuma INV-TENANT-PERFIL-001..007 violada em grep estrutural.

## 8. Histórico

- **2026-05-27 manhã** — Auditoria 10 lentes (pedido Roldão "ver se o sistema grava o tipo de empresa") detecta gap. 10/10 vereditos FAIL. ADR-0067 redigida.
- **2026-05-27 meio-dia** — Roldão decide via AskUserQuestion: manter 4 perfis + consertar antes de Wave A. ADR-0067 status `aceito`.
- **2026-05-27 tarde** — P1 spec.md criada (versão inicial — 5 USs).
- **2026-05-27 tarde** — P2 4 reviews paralelos disparados. Retornaram 41 achados (13 BLOQ + 17 MÉDIO + 10 ALTO + 1 ACEITE). Densidade comparável a M4 (45).
- **2026-05-27 noite** — P3 plan.md consolida P2 → reconciliação.
- **2026-05-27 noite** — P3 spec.md reescrita (este documento) absorve 13 BLOQUEANTES por causa-raiz. Expandida de 5 USs → 9 USs. INVs expandidas 5 → 7. Hooks 3 → 5. Gates 7 → 18.
- **Estimativa ajustada (T15 ACEITE):** 8-14 dias com causa-raiz (era 5-10). 5 dias só se cortar telemetria/drill em PG real (T14 + T7 → GATEs).
- **Próximo:** P4 tasks.md (T-SAN-PERFIL-NNN — desdobrar ACs em ~40-60 tarefas executáveis).
