---
owner: roldao
status: aceito
revisado-em: 2026-05-27
adr: 0067
titulo: Perfil regulatório do tenant como entidade temporal de 1ª classe (4 perfis A/B/C/D)
data: 2026-05-27
aceito-em: 2026-05-27 (decisão Roldão via AskUserQuestion + comando "continui")
proposto-por: agente (auditoria 10 lentes — pedido do Roldão "ver se o sistema grava o tipo de empresa")
revisado-por: 10/10 auditores Família 5 (auditoria 2026-05-27) — convergência total
bloqueia-fase: Wave A (1º tenant externo pago)
depende-de: ADR-0002, ADR-0007, ADR-0030, ADR-0031
---

# ADR-0067 — Perfil regulatório do tenant como entidade temporal de 1ª classe

## Contexto

Auditoria conjunta de 10 lentes em 2026-05-27 (resposta a pedido do Roldão "auditoria com 10 agentes diferentes — ver se o sistema grava o tipo de empresa") revelou gap estrutural confirmado por 10 de 10 agentes:

**O PRD master `docs/prd.md` §2 (linhas 23-49) declara 4 perfis configuráveis de cliente:**
- **Perfil A** — Laboratório acreditado RBC/CGCRE com escopo formal (5-10% do ICP, DAP R$ 1.500-3.000/mês)
- **Perfil B** — Lab rastreável não-acreditado (20-30%, núcleo MVP-1, perfil da Balanças Solution)
- **Perfil C** — Lab em preparação para acreditar (~30%, trilha D→A)
- **Perfil D** — Calibração comercial pura sem rituais 17025 (raro nuclear, DAP R$ 300-500)

**O sistema NÃO persiste qual dos 4 perfis cada tenant é.** `src/infrastructure/tenant/models.py` (linhas 23-65) tem apenas `slug`, `nome_fantasia`, `plano="placeholder"`, `status_lifecycle`. Zero campo `perfil_regulatorio`. Zero tabela histórico. Zero predicate consulta perfil.

### Achados das 10 lentes (resumo)

| Lente | Veredito | Achado-chave |
|---|---|---|
| L1 Modelo de dados | FAIL ALTO | Campo não existe. ADR-0006:39 e ADR-0009:27 citam `tenant.perfil` como se já existisse — referência fantasma. |
| L2 M4 calibração | CONCERN ALTO | M4 colapsou 4 perfis em binário RBC/NAO_RBC NO NÍVEL DA CALIBRAÇÃO (não do tenant). Único ponto de ramificação: `configurar_calibracao.py:156`. |
| L3 Templates certificado | CONCERN ALTO | Sem campo + sem template diferenciado = Perfil B/C/D pode emitir certificado com selo RBC → fraude CGCRE NIT-DICLA-016. |
| L4 Drift PRD vs código | FAIL ALTO | 8 drifts. "Trilha D→A" (BIG-03 do discovery) atravessou 7 Marcos sem 1 linha de código. |
| L5 Onboarding/migração | FAIL CRÍTICO | Não existe comando `provisionar_tenant`. Snapshot existe em `equipamentos` (nível errado). Default silencioso `D` pode estar marcando Balanças Solution errado. |
| L6 Autorização/fraude | FAIL ALTO | Predicate `cmc_cobre` recebe `tipo_acreditacao` **do payload JSON da request**, não consulta tenant. Self-attestation = fraude documental viável hoje. |
| L7 Billing/contrato | FAIL ALTO | DAP varia 10x mas sistema cobra igual. Contrato único viola CDC art. 39 V. Apólice E&O dimensionada errada à seguradora. |
| L8 LGPD retenção | FAIL ALTO | Retém 25a para todos — over-retention LGPD art. 6º III em perfil D. Trunca geo 5a para todos — under-retention CGCRE em perfil A. |
| L9 Testes | FAIL ALTO | Cobertura: D 100% / C <1% / B 0% / A 5%. ~85 testes literalizam "D" como default. Bug perfil-A passa toda a suite verde. |
| L10 Observabilidade | CONCERN MÉDIO | 5 KPIs estratégicos inviáveis: trilha D→A, ARPU por perfil, cohort retenção, tempo médio emissão por perfil, adoção feature por perfil. |

### Decisão estratégica do Roldão (2026-05-27)

Perante o relatório consolidado, Roldão decidiu via AskUserQuestion:
1. **Manter os 4 perfis A/B/C/D** — confirma o PRD; trilha D→A vira feature codificada; é o diferencial competitivo principal do discovery.
2. **Consertar agora, antes de Wave A** — cria esta ADR, abre gate bloqueante, retrofit Foundation+M1-M4 antes de Wave A arrancar.

## Decisão

### 1. Schema canônico — `Tenant.perfil_regulatorio` + `TenantPerfilHistorico`

Adicionar:

- **Coluna `Tenant.perfil_regulatorio`** enum `{A_ACREDITADO_RBC, B_RASTREAVEL, C_EM_PREPARACAO, D_COMERCIAL_PURO}` NOT NULL.
- **Coluna `Tenant.acreditacao_cgcre_numero`** VARCHAR(50) NULL (preenchido apenas se Perfil A).
- **Coluna `Tenant.acreditacao_vigencia_inicio` / `Tenant.acreditacao_vigencia_fim`** DATE NULL (Perfil A).
- **Tabela nova `TenantPerfilHistorico`** (shared-across-tenants, mesmo padrão de `Tenant` per ADR-0002 §8):
  - `id UUID PK`
  - `tenant_id UUID FK → tenants(id)`
  - `perfil_anterior CHAR(1) NULL` (NULL quando provisioning inicial)
  - `perfil_novo CHAR(1) NOT NULL`
  - `direcao ENUM{PROVISIONAMENTO_INICIAL, PROMOCAO_REGULATORIA, REBAIXAMENTO_POR_SUSPENSAO_CGCRE, CORRECAO_ADMINISTRATIVA}`
  - `motivo TEXT NOT NULL` (≥100 chars)
  - `evento_origem_id UUID NULL` (FK para evento WORM em `auditoria` ou `licencas_acreditacoes`)
  - `auditor_cgcre VARCHAR(200) NULL` (preenchido quando direcao=PROMOCAO_REGULATORIA pra A)
  - `certificado_acreditacao_documento_id UUID NULL` (FK pra documento que comprova)
  - `registrado_em TIMESTAMPTZ NOT NULL DEFAULT now()`
  - `registrado_por_usuario_id UUID NOT NULL FK → usuarios(id)`
  - `assinatura_a3_id UUID NULL` (obrigatória quando direcao=PROMOCAO_REGULATORIA)
- **UNIQUE parcial** em `(tenant_id) WHERE vigencia_fim IS NULL` na visão materializada `tenant_perfil_vigente` — 1 perfil vigente por tenant.
- **Append-only + RLS:** tabela imutável após INSERT (trigger anti-UPDATE/anti-DELETE estilo `auditoria_anti_*` da F-A).

### 2. Predicate canônico `tenant_perfil_e(perfis_aceitos)`

Implementado em `src/infrastructure/authz/predicates.py`. Consulta `Tenant.objects.only("perfil_regulatorio").get(id=tenant_id)`. **Fail-closed** (default deny) — nunca fail-open.

Invocado obrigatoriamente em:
1. `emitir_certificado_rbc` — exige `perfil ∈ {A}` AND `acreditacao_vigencia_fim > today`.
2. `configurar_calibracao` com `tipo_acreditacao=RBC` — exige `perfil ∈ {A}`. Substitui o atual self-attestation por payload (corrige FAIL L6).
3. `aprovar_2a_conferencia` — obrigatório se `perfil ∈ {A}`; opcional para B/C; desabilitado para D.
4. `validar_software_iso17025` (ADR-0025) — feature liberada se `perfil ∈ {A}`; opcional B/C; bloqueada D.
5. `eliminar_dados_titular` — perfil A com certificado emitido = recusa fundamentada (ISO 17025 cl. 8.4); perfil D = elimina em 5a.
6. `truncar_geo_5a` (job) — pula tenants `perfil ∈ {A}`.

### 3. Snapshot `perfil_no_evento` em eventos WORM

Toda tabela append-only que preserva contexto regulatório ganha coluna `perfil_no_evento CHAR(1) NOT NULL`:
- `auditoria` (Marco F-A) — preenchida por `registrar_auditoria()` lendo `perfil_tenant_context`.
- `evento_de_calibracao` (Marco 4) — `perfil_no_evento` no momento da calibração.
- `evento_de_os` (Marco 3) — `perfil_no_evento` no momento da OS.
- `certificado` (Wave A) — `perfil_emissor_no_momento` cravado na assinatura.

Justificativa regulatória: ISO 17025 cl. 8.4 (preservar contexto da época) + LGPD art. 37 (registro de tratamento) + defesa em auditoria CGCRE retroativa.

### 4. Matriz canônica "feature × perfil"

Documento novo `docs/conformidade/comum/matriz-feature-perfil.md` declara, para cada feature crítica, o comportamento por perfil (obrigatório / opcional / desabilitado). Hook `feature-perfil-matriz-validator` bloqueia commit que adiciona feature crítica sem entrada na matriz.

### 5. Coleta no provisioning (ADR-0015 emenda)

State machine de ADR-0015 ganha etapa **0 — COLETA_PERFIL_REGULATORIO** antes de `TENANT_DB_CRIADO`. Sem perfil, provisioning não avança. Comando `provisionar_tenant` novo em `src/infrastructure/tenant/management/commands/` exige `--perfil {A|B|C|D}`.

### 6. Retrofit equipamento snapshot (Marco 2)

`Equipamento.perfil_tenant_snapshot` deixa de ser auto-declarado e vira COPY do `Tenant.perfil_regulatorio` no momento do INSERT. Migration de dados copia `tenant.perfil_atual` para snapshots vazios; bloqueia COALESCE silencioso `D` que pode estar errado.

### 7. Hook `tenant-perfil-imutavel-check`

Bloqueia UPDATE direto em `tenants.perfil_regulatorio` fora das funções SECURITY DEFINER `promover_perfil_tenant()` e `rebaixar_perfil_tenant_por_suspensao_cgcre()`. Similar a `cliente-canonico-imutavel-check` (Marco 1).

### 8. Templates de certificado diferenciados (Wave A módulo `certificados`)

4 templates obrigatórios:
- **Perfil A**: selo CGCRE + número RBC + ILAC-MRA + TSA-ITI qualificado (ADR-0047) + retenção 25a.
- **Perfil B/C**: bloco "Certificado com rastreabilidade declarada (não-acreditado)" obrigatório; TSA-ITI recomendado; retenção desejável 25a.
- **Perfil D**: renomeado para "**Relatório de Aferição/Verificação**"; proibida palavra "ISO 17025"; retenção 5a (Receita). Hook `template-perfil-d-anti-iso` valida.

Pre-flight check em `emitir_certificado`: valida que `template.perfil_alvo == tenant.perfil_regulatorio_vigente`.

### 9. Testes parametrizados por perfil

`TenantFactory` com traits factory-boy: `TenantFactory.perfil_a()`, `.perfil_b()`, `.perfil_c()`, `.perfil_d()`. Fixtures em `conftest.py`: `tenant_a`, `tenant_b`, `tenant_c`, `tenant_d`. Marcador `@pytest.mark.perfil("A")` + parametrize matrix em testes que tocam regras ISO 17025.

### 10. Observabilidade

Novo `perfil_tenant_context: ContextVar[str]` em `multitenant/context.py`. Middleware popula ao ativar tenant. Structlog processor (F-C2) injeta automaticamente em todo log. Métricas Prometheus (F-C2) usam label `perfil_tenant`.

## Non-goals desta ADR

- NÃO entrega templates de certificado agora — pertence ao módulo `metrologia/certificados` Wave A.
- NÃO entrega comando `provisionar_tenant` agora — pertence ao módulo `onboarding` Wave A.
- NÃO decide se perfil muda automaticamente após N meses (trilha D→A automática vs manual) — decisão diferida pra Wave A.
- NÃO trata "tenant matriz A + filial B" (multi-filial) — diferido para entrevista Discovery pós-1º tenant multi-filial.

## Consequências

**Positivas:**
- Fecha 10/10 achados da auditoria de 27/05/2026.
- Habilita BIG-03 (trilha D→A) como feature codificada — diferencial competitivo principal do discovery vira código.
- Resolve FAIL L6 (fraude documental): self-attestation por payload é substituída por consulta canônica ao Tenant.
- Resolve FAIL L7 (jurídico): clausulado modular vira possível via `Tenant.perfil_regulatorio`.
- Resolve FAIL L8 (LGPD): matriz de retenção condicional por perfil evita over-retention e under-retention.
- Resolve FAIL L9 (testes): TenantFactory parametrizado destrava cobertura 4 perfis × N módulos.
- Resolve CONCERN L10 (observabilidade): 5 KPIs estratégicos viáveis.

**Negativas (aceitas):**
- Retrofit em Marcos fechados (F-A audit, M1 clientes, M2 equipamentos, M3 OS, M4 calibração) — migration nova + ~40-60 testes novos. Estimativa: 5-10 dias de trabalho concentrado.
- Wave A atrasa 1-2 semanas pelo retrofit.
- Aumenta complexidade do schema (1 tabela nova + 4 colunas em Tenant + snapshot em 4 tabelas de evento).

## Gates Wave A (rastreados)

- `GATE-TENANT-PERFIL-SCHEMA` — migration + retrofit dados existentes (Balanças Solution = `B`).
- `GATE-TENANT-PERFIL-PROVISIONING` — comando `provisionar_tenant` + emenda ADR-0015 etapa 0.
- `GATE-TENANT-PERFIL-TEMPLATES-CERT` — 4 templates + pre-flight check + hook `template-perfil-d-anti-iso`.
- `GATE-TENANT-PERFIL-MATRIZ-RETENCAO` — emenda ADR-0021 com matriz LGPD condicional + drills DRILL-RET-12/13.
- `GATE-TENANT-PERFIL-AUTHZ-PREDICATE` — predicate `tenant_perfil_e` + retrofit `cmc_cobre` (fecha FAIL L6).
- `GATE-TENANT-PERFIL-TESTES-MATRIZ` — TenantFactory parametrizado + ≥40 testes novos.
- `GATE-TENANT-PERFIL-OBSERVABILIDADE` — label `perfil_tenant` em logger context + snapshot `perfil_no_evento` em audit/eventos.

## Plano de implementação Wave A (alto nível)

1. **Sprint 1 (5 dias)** — Schema + Tenant.perfil + TenantPerfilHistorico + migration + trigger imutabilidade + retrofit Balanças Solution (default `B`, justificado).
2. **Sprint 2 (5 dias)** — Predicate `tenant_perfil_e` + retrofit `cmc_cobre` (corrige FAIL L6) + invocação nos 6 use cases críticos + ≥20 testes regressão.
3. **Sprint 3 (5 dias)** — Comando `provisionar_tenant` + emenda ADR-0015 etapa 0 + matriz feature×perfil + hook `tenant-perfil-imutavel-check`.
4. **Sprint 4 (5 dias)** — Retrofit equipamento snapshot + snapshot `perfil_no_evento` em audit/evento_de_*/certificado + retrofit dados existentes.
5. **Sprint 5 (Wave A módulo `certificados`)** — 4 templates + pre-flight check + hook `template-perfil-d-anti-iso`.
6. **Sprint 6 (Wave A módulo `onboarding` + LGPD)** — UX coleta perfil + matriz retenção condicional + drills DRILL-RET-12/13.

Cada Sprint passa pelo ritual Spec Kit obrigatório (INV-RITUAL-001) com 10 auditores Família 5 verde.

## Histórico

- **2026-05-27 manhã** — Auditoria 10 lentes (pedido Roldão "ver se o sistema grava o tipo de empresa") detecta gap em 10/10 vereditos. Roldão decide via AskUserQuestion: manter 4 perfis + consertar antes de Wave A.
- **2026-05-27 tarde** — ADR redigida em proposta.
- **2026-05-27 tarde** — ADR aceita por decisão Roldão ("continui" = aceite). Status: aceito. Próximo passo: spec do Sprint 1 em `docs/faseamento/SAN-PERFIL-TENANT/spec.md` seguindo ritual Spec Kit (INV-RITUAL-001).
