---
owner: roldao
revisado-em: 2026-05-27
proximo-review: 2026-08-27
status: stable
diataxis: explanation
audiencia: agente
modulo: seguranca-trabalho
dominio: rh-frota-qualidade
historico:
  - 2026-05-27 — Onda PRE-A.3 saneamento pré-Wave A (BATCH B3): frontmatter canônico
    (hífens); perfil ADR-0067 declarado em §4 + matriz feature×perfil; matriz NR × perfil
    canônica (perfil A: NR-7 rigorosa + NR-35; B: NR-35 + NR-7 leve; C: igual A
    para preparar promoção; D: só NR básica) — resolve CRÍTICO L1#6; AC binário
    GIVEN-WHEN-THEN com ID; predicate `nr_exigida_por_perfil(tenant_id, atividade)`
    canônico; INV-AGENT-001 prompt injection em US texto livre; non-objetivos
    expandidos; métricas inline; glossário §11.
  - 2026-05-17 — versão inicial.
relacionados:
  - docs/dominios/rh-frota-qualidade/modulos/colaboradores/prd.md
  - docs/dominios/rh-frota-qualidade/modulos/treinamentos/prd.md
  - docs/dominios/operacao/modulos/ordens-de-servico/prd.md
  - docs/adr/0022-rt-tenant.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0068-sucessao-substituicao-rt.md
  - docs/adr/0069-bypass-competencia-cl-6-2-objetivo.md
  - docs/conformidade/comum/lgpd-rat.md#RAT-14
  - docs/conformidade/comum/dpia-modulos-novos.md#DPIA-03
  - docs/conformidade/comum/retencao-matriz.md
  - docs/conformidade/comum/matriz-feature-perfil.md
---

# PRD — Módulo Segurança do Trabalho (SST)

> Origem: `docs/novas funcionalidades.txt` linhas 1339-1364 (Adicional 9 — Módulo de Segurança do Trabalho).
>
> **v2 stable (2026-05-27):** saneamento pré-Wave A. AC-SST-004 reescrito com matriz NR × perfil (resolve CRÍTICO L1#6 — antes não diferenciava perfil A acreditado de perfil D comercial puro); predicate `nr_exigida_por_perfil(tenant_id, atividade)` canônico; ADR-0067 declarada.

---

## 1. O que este módulo é

Módulo de Segurança e Saúde do Trabalho voltado a empresas com técnicos em campo. Centraliza EPIs (cadastro, entrega, validade, termo assinado), treinamentos obrigatórios de segurança (NR-10, NR-12, NR-35), ASO, permissão de trabalho, APR, checklist de segurança pré-OS e registro de acidentes / quase-acidentes com evidências fotográficas. Atua como **trava operacional**: bloqueia técnico sem treinamento de segurança válido e bloqueia execução de OS sem checklist preenchido.

**Diferenciação por perfil ADR-0067**: perfil A (lab acreditado RBC) tem rigor NR-7/NR-35 elevado por exposição metrológica + altura em bancadas; perfil D (comercial puro) tem só NR básica.

## 2. Por que este módulo existe (problema a resolver)

Empresa de assistência técnica + calibração trabalha em campo (galpões, indústrias, altura, eletricidade) e responde por passivo trabalhista direto quando técnico se acidenta sem EPI/treinamento/ASO em dia. Sem trilha documental, multa MTE e ação trabalhista são quase certas. Operação do Roldão (Balanças Solution) já passou por situações de risco que motivam este módulo.

**Achado CRÍTICO L1#6 (auditoria 10 lentes 2026-05-27):** AC-SST-004 original tratava NR-* uniformemente — não diferenciava perfil A acreditado (que opera com PCMSO + ASO periódico rigoroso por exposição a campo elétrico de balanças industriais + altura em bancadas elevadas) de perfil D comercial puro (que só faz aferição básica e tem NR mínima). Sem diferenciação, perfil A operava com regra branda (under-protection) OU perfil D pagava SST cara que não precisa (sobre-custo). Resolvido pela matriz NR × perfil neste PRD v2.

## 3. Personas

- **P-RH-02 — Gerente SST do tenant** (principal): cadastra EPI, gerencia ASO, registra acidentes, mantém matriz NR × perfil.
- **P-OP-04 — Gestor de qualidade do tenant** (perfil A obrigatório — ADR-0067): assina A3 em bypass NR (paralelo ao bypass competência ADR-0069 — ver §"Glossário"); aprova plano PCMSO.
- **P-RH-03 — Médico do trabalho** (terceirizado): emite ASO; acessa ASO laudo (RBAC restrito — DPIA-03 R1).
- **P-OP-02 — Técnico de campo**: consumidor das travas (bloqueio sem NR-35 quando OS=altura).
- **P-COM-03 — Auditor MTE** (perfil A/B com risco trabalhista alto): consulta histórico acidentes + ASO.

Ver `personas.md` deste módulo + transversais em `../../personas.md`.

## 4. Perfil regulatório (ADR-0067) — Matriz NR × Perfil

| Perfil | NR-1 (geral) | NR-6 (EPI) | NR-7 (PCMSO + ASO) | NR-10 (eletricidade) | NR-12 (máquinas) | NR-35 (altura) | PT/APR |
|---|---|---|---|---|---|---|---|
| **A — Acreditado RBC** | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ RIGOROSA (PCMSO anual + ASO 6/6m em técnicos de bancada por exposição) | ✅ se atividade envolve | ✅ se atividade envolve | ✅ RIGOROSA (bancadas elevadas + campo em silos) | ✅ OBRIGATÓRIA por OS de risco elevado |
| **B — Rastreável** | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ NR-7 LEVE (ASO anual) | ✅ se atividade envolve | ✅ se atividade envolve | ✅ RIGOROSA (mesmo que A — altura é altura) | ✅ se atividade envolve |
| **C — Em preparação D→A** | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ IGUAL A (preparar promoção) | ✅ idem A | ✅ idem A | ✅ idem A | ✅ idem A |
| **D — Comercial puro** | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ⚪ ASO admissional + demissional só | ⚪ só se atividade clara | ⚪ só se atividade clara | ⚪ só se atividade clara (raro em comercial) | ⚪ opcional |

Predicate canônico: `nr_exigida_por_perfil(tenant_id, atividade_codigo)` lê `Tenant.perfil_regulatorio` + tabela de mapeamento e retorna lista de NRs exigidas. Fail-closed (ADR-0067 §"Decisão" item 2). Linha "NR-* por perfil" da matriz `docs/conformidade/comum/matriz-feature-perfil.md`.

## 5. Escopo (o que ESTÁ neste módulo)

- Cadastro de EPIs (nome, CA, validade do CA, fornecedor, foto).
- Entrega de EPI a colaborador com termo assinado eletronicamente + data + assinatura.
- Validade individual do EPI entregue (alerta de troca).
- Treinamentos obrigatórios de segurança: NR-10 (eletricidade), NR-12 (máquinas), NR-35 (altura) e outros configuráveis — **filtrados por perfil ADR-0067**.
- ASO (Atestado de Saúde Ocupacional): admissional, periódico (cadência por perfil), retorno, mudança de função, demissional, com validade.
- Permissão de Trabalho (PT) para serviços de risco (altura, espaço confinado, energizado).
- APR (Análise Preliminar de Risco) anexada à OS de risco elevado.
- Checklist de segurança pré-OS (configurável por tipo de serviço).
- Registro de acidente e quase-acidente com evidências fotográficas + descrição + ação corretiva.
- Bloqueio técnico sem treinamento de segurança válido (vínculo com módulo `treinamentos`).
- Bloqueio OS sem checklist de segurança preenchido (vínculo com OS).
- Relatório de segurança por período (acidentes, quase-acidentes, EPIs vencidos, ASOs vencidos).
- **Predicate canônico `nr_exigida_por_perfil`** + matriz NR × perfil (US-SST-004 reescrita).

## 6. Não-objetivos (o que NÃO está neste módulo)

> LLM não infere por omissão. Proibições positivas.

- **Folha de pagamento de adicional de periculosidade/insalubridade** — vive em `financeiro/` (não existe Wave A).
- **PCMSO / PGR como documento técnico autoral** — módulo armazena PDF gerado externamente; não gera o documento técnico.
- **eSocial S-2210 (CAT eletrônica)** — Wave B; Wave A só registra o acidente internamente.
- **Cálculo de afastamento INSS** — fora do escopo.
- **SIPAT / palestra anual** — fica em `treinamentos/` como evento; não tem fluxo próprio aqui.
- **Treinamento técnico de produto (calibração, regulagem balança)** — vive em `treinamentos/`. Aqui só treinamentos de **segurança**.
- **Brigada de incêndio / plano de emergência predial** — Wave B.
- **CIPA (eleição, ata, reuniões)** — Wave B.
- **eSocial S-2220 (monitoramento da saúde do trabalhador)** — Wave B.

## 7. User Stories

### US-SST-001: Cadastrar EPI com CA e validade

**Como** gerente operacional, **quero** cadastrar EPI com nº de CA e data de validade do CA, **para** garantir que estamos entregando EPI válido legalmente.

**Critérios de aceite:**
- **AC-SST-001-1**: GIVEN gerente autenticado, WHEN cadastra EPI com nº CA + validade + texto descritivo, THEN sistema valida CA contra base MTE (Wave A — fonte local; Wave B — API SISAVEN). Texto descritivo passa por sanitização anti-prompt-injection (INV-AGENT-001).
- **AC-SST-001-2**: GIVEN cadastro de EPI + nº CA vencido na data de hoje, WHEN salva, THEN sistema marca EPI como "CA vencido" e bloqueia entrega futura.
- **AC-SST-001-3**: GIVEN cadastro de EPI + nº de CA vazio, WHEN tenta salvar, THEN bloqueio (campo obrigatório).

**Invariantes:** `INV-001` (audit trail), `INV-TENANT-001`, `INV-AGENT-001` (prompt injection em texto livre).

---

### US-SST-002: Entregar EPI com termo assinado eletronicamente

**Como** técnico de SST, **quero** registrar entrega de EPI ao colaborador com termo de recebimento assinado eletronicamente, **para** ter prova jurídica de entrega em ação trabalhista.

**Critérios de aceite:**
- **AC-SST-002-1**: GIVEN entrega de EPI + colaborador presente, WHEN colaborador assina (touch / código de confirmação), THEN sistema grava PDF do termo + hash SHA-256 + timestamp em trilha imutável (B2 WORM + HMAC ADR-0064).
- **AC-SST-002-2**: GIVEN entrega sem assinatura, WHEN tenta salvar, THEN bloqueio com 422 `AssinaturaAusente`.

**Invariantes:** `INV-001`, `INV-017` (assinatura digital quando aplicável), `INV-HMAC-001..005`.

---

### US-SST-003: Alertar EPI / ASO / treinamento de segurança vencido

**Como** gerente SST, **quero** painel com EPIs, ASOs e treinamentos vencidos ou a vencer em 30/60/90 dias, **para** evitar trabalhar com colaborador irregular.

**Critérios de aceite:**
- **AC-SST-003-1**: GIVEN job diário em execução, WHEN detecta vencidos hoje + vence em ≤30 / ≤60 / ≤90 dias, THEN painel renderiza listagem com status colorido.
- **AC-SST-003-2**: GIVEN vencimento ≤30 dias, WHEN job dispara, THEN notificação automática 30 dias antes para o gerente SST.
- **AC-SST-003-3 (LGPD — dado sensível saúde)**: Tratamento do ASO atende base **Art. 11 II "a" — cumprimento de obrigação legal** (NR-7/PCMSO + CLT art. 168 + NR-35); SEM consentimento aplicável (vínculo trabalhista, RAT-14 + DPIA-03). Aferê armazena apenas resultado (apto/inapto/restrição) + validade + PDF — sem CID-10/diagnóstico.
- **AC-SST-003-4 (Retenção)**: ASO conforme `retencao-matriz.md` linha "ASO (Atestado de Saúde Ocupacional)" — **20 anos pós-vínculo (NR-7 item 7.4.5.1)**; obrigação legal vence direito de esquecimento LGPD; após prazo: anonimização (CPF → hash; nome → "Colaborador anonimizado #N") preservando aptidão+validade+médico para auditoria MTE histórica.
- **AC-SST-003-5 (RBAC)**: GIVEN acesso ao laudo ASO, WHEN usuário consulta, THEN sistema valida perfil ∈ {"gerente SST", "RH", "médico do trabalho", "auditor read-only"} (DPIA-03 R1); demais perfis veem só "apto/inapto/validade" sem laudo.
- **AC-SST-003-6 (cadência por perfil — ADR-0067)**: GIVEN `tenant_perfil_e(["A", "C"])` retorna TRUE + colaborador técnico de bancada (exposto a campo elétrico industrial), WHEN job calcula próximo ASO, THEN cadência **6 meses** (rigorosa NR-7); GIVEN perfil B, cadência **12 meses**; GIVEN perfil D + colaborador não-exposto, cadência **admissional + demissional apenas** (sem periódico obrigatório).

---

### US-SST-004: Bloquear técnico sem NR válida — matriz NR × perfil (reescrito)

**Como** sistema, **quero** bloquear alocação de técnico em OS que exija NR-* se o treinamento estiver vencido **OU** se o perfil do tenant exige NR-* que o técnico não possui, **para** evitar passivo trabalhista e atender CRÍTICO L1#6 da auditoria 10 lentes.

**Critérios de aceite:**
- **AC-SST-004-1**: GIVEN OS com atividade marcada `requer_altura=TRUE`, WHEN sistema invoca `nr_exigida_por_perfil(tenant_id, atividade_codigo)`, THEN retorna lista incluindo `NR-35`; WHEN técnico sem NR-35 válida, THEN bloqueio com mensagem clara ao despachante.
- **AC-SST-004-2**: GIVEN técnico com NR-35 vencida há ≥1 dia, WHEN abre painel de agenda, THEN aparece destacado como "INAPTO — treinamento vencido".
- **AC-SST-004-3 (matriz perfil — ADR-0067)**: GIVEN `tenant_perfil_e(["A", "C"])` retorna TRUE + atividade=`calibracao_bancada_industrial`, WHEN sistema invoca predicate, THEN exige NR-10 + NR-35 + NR-7 (PCMSO vigente); GIVEN `perfil = B`, exige NR-10 + NR-35 (NR-7 leve); GIVEN `perfil = D` + mesma atividade, exige só NR-1 + NR-6 (EPI básico).
- **AC-SST-004-4 (bypass paralelo ADR-0069)**: GIVEN técnico sem NR válida + tenta bypass, WHEN sistema valida, THEN aplica MESMAS 4 condições objetivas da ADR-0069 (supervisor presencial com NR válida + treinamento expirado ≤90d + justificativa enum + A3 gestor SST). Cota mensal por perfil (A=5%, B=10%, C=5%, D=20%) compartilhada com cota de competência ADR-0069.
- **AC-SST-004-5**: GIVEN `tenant_perfil_e(["A"])` + bypass NR > 2 meses consecutivos com cota cheia, WHEN job mensal roda, THEN dispara `Tenant.BypassRecorrente → NotificacaoMTE` síncrona (paralelo a NotificacaoCGCRE da ADR-0069 §2.4).

**Invariantes:** `INV-001`, `INV-003` espírito (operar dentro do escopo válido), `INV-COMP-BYPASS-001..004` (ADR-0069 reusado), `INV-PERFIL-001` (ADR-0067), `INV-NR-PERFIL-001` (nova — predicate canônico).

**Dependências:** depende de `treinamentos/` (US-TRE-007 — bypass paralelo).

---

### US-SST-005: Bloquear OS sem checklist de segurança preenchido

**Como** sistema, **quero** bloquear execução / fechamento de OS de risco sem checklist de segurança preenchido, **para** garantir que técnico avaliou risco antes de operar.

**Critérios de aceite:**
- **AC-SST-005-1**: GIVEN OS com flag "exige checklist segurança" + técnico tenta marcar OS como "em execução" sem preencher checklist, WHEN clica, THEN bloqueio com 412 `ChecklistSegurancaAusente`.
- **AC-SST-005-2**: GIVEN checklist preenchido + OS confirmada, WHEN persistido, THEN fica anexado à OS imutavelmente (`INV-001` + B2 WORM).

---

### US-SST-006: Emitir Permissão de Trabalho (PT) para serviço de risco

**Como** gerente SST, **quero** emitir PT por OS de risco (altura, espaço confinado, energizado), **para** atender NR-33/NR-35.

**Critérios de aceite:**
- **AC-SST-006-1**: GIVEN OS de risco + gerente SST autenticado, WHEN emite PT, THEN validade limitada (1 turno por padrão) + expira automaticamente em job horário.
- **AC-SST-006-2**: GIVEN PT em emissão, WHEN sistema valida, THEN exige assinatura do emitente E do executante (2 assinaturas) antes de status `EMITIDA`.

---

### US-SST-007: Anexar APR (Análise Preliminar de Risco) à OS

**Como** técnico, **quero** preencher APR antes de iniciar serviço de risco elevado, **para** documentar riscos e medidas de controle.

**Critérios de aceite:**
- **AC-SST-007-1**: GIVEN APR template configurável pelo tenant, WHEN técnico abre OS de risco, THEN sistema apresenta template + campos obrigatórios + texto livre passa por sanitização INV-AGENT-001.
- **AC-SST-007-2**: GIVEN APR anexada à OS + assinada, WHEN persistida, THEN imutável após assinatura (`INV-001` + B2 WORM).

**Invariantes:** `INV-001`, `INV-AGENT-001`, `INV-017`.

---

### US-SST-008: Registrar acidente / quase-acidente com evidências

**Como** gerente SST, **quero** registrar acidente ou quase-acidente com descrição, fotos, colaboradores envolvidos e ação corretiva, **para** análise e prevenção.

**Critérios de aceite:**
- **AC-SST-008-1**: GIVEN gerente SST autenticado, WHEN registra evento (tipo `acidente`/`quase-acidente`/`incidente ambiental` + data/hora + local + descrição + fotos + ação corretiva), THEN persistido + descrição passa por sanitização INV-AGENT-001.
- **AC-SST-008-2**: GIVEN registro confirmado, WHEN persistido, THEN imutável após confirmação (apenas adendos permitidos — `INV-001` + hash-chain HMAC ADR-0064).
- **AC-SST-008-3**: GIVEN acidente com afastamento, WHEN registrado, THEN colaborador marcado como "afastado por acidente" (sem cálculo, só flag) + bloqueia alocação em novas OS até retorno.
- **AC-SST-008-4 (perfil A — preparação MTE)**: GIVEN `tenant_perfil_e(["A"])` + acidente com afastamento >15 dias, WHEN registrado, THEN dispara alerta P1 + checklist "preparar CAT manual (eSocial S-2210 é Wave B)".

**Invariantes:** `INV-001`, `INV-AGENT-001`, `INV-HMAC-001..005`.

---

### US-SST-009: Relatório de segurança por período

**Como** gerente, **quero** relatório consolidado de SST por período (mês/trimestre/ano), **para** acompanhar indicadores e apresentar em reuniões.

**Critérios de aceite:**
- **AC-SST-009-1**: GIVEN período selecionado, WHEN sistema gera relatório, THEN inclui: nº acidentes, nº quase-acidentes, taxa de frequência, EPIs entregues, ASOs realizados, treinamentos válidos, % bypass NR mensal (perfil-aware).
- **AC-SST-009-2**: GIVEN relatório gerado, WHEN gerente clica export, THEN PDF + XLSX gerados; perfil A inclui matriz NR × perfil renderizada.

---

## 8. Métricas de sucesso

Ver `metricas.md`. Resumo:
- Taxa de OS executadas com checklist preenchido = 100%.
- Taxa de colaboradores com ASO válido (na cadência por perfil) = 100%.
- Tempo médio de resposta a quase-acidente = ≤7 dias.
- **% bypass NR mensal por perfil dentro da cota ADR-0069** (A ≤5%, B ≤10%, C ≤5%, D ≤20%) = 100%.
- **Zero meses com PCMSO vencido em perfil A**.

## 9. NFR

- **Performance:** painel de alertas SST carrega em ≤2s para tenant com 200 colaboradores; predicate `nr_exigida_por_perfil` ≤50ms p95 (cache 5min).
- **Segurança:** SEC-* aplicáveis; dado de ASO é dado pessoal sensível LGPD (saúde) — base legal "obrigação legal"; RLS via `tenant_id` (ADR-0002); evento acidente em hash-chain HMAC ADR-0064.
- **Acessibilidade:** WCAG 2.1 AA (`INV-016` + ADR-0057).
- **Imutabilidade:** registro de acidente é imutável (`INV-001` + B2 WORM).
- **Prompt injection:** texto livre em US-SST-001/007/008 passa por sanitização (`INV-AGENT-001`).

## 10. ADRs e INVs aplicáveis

- **ADRs:** 0007 (codegen), 0022 v2 (RT — gestor SST análogo), 0057 (a11y), 0064 (HMAC 25a), 0067 (perfil regulatório — matriz NR × perfil), 0068 (sucessão), 0069 (bypass — paralelo NR).
- **INVs:** INV-001, INV-003, INV-016, INV-017, INV-COMP-BYPASS-001..004, INV-NR-PERFIL-001, INV-PERFIL-001, INV-AGENT-001, INV-HMAC-001..005, INV-TENANT-001.

## 11. Glossário e referências

- **NR (Norma Regulamentadora)** — normas MTE de segurança e saúde do trabalho.
- **NR-7 (PCMSO)** — Programa de Controle Médico de Saúde Ocupacional; cadência por perfil declarada em §4.
- **NR-10** — Segurança em instalações e serviços com eletricidade.
- **NR-12** — Segurança no trabalho em máquinas e equipamentos.
- **NR-35** — Trabalho em altura (acima de 2m).
- **ASO (Atestado de Saúde Ocupacional)** — documento médico obrigatório; cadência por perfil ADR-0067.
- **PT (Permissão de Trabalho)** — autorização formal para serviço de risco; validade limitada (1 turno).
- **APR (Análise Preliminar de Risco)** — análise pré-execução de OS de risco elevado.
- **EPI / CA** — Equipamento de Proteção Individual / Certificado de Aprovação MTE.
- **Bypass NR (paralelo ADR-0069)** — operação fora da NR exigida, regulamentada pelas 4 condições objetivas + cota perfil + lock + notificação MTE.
- **Predicate `nr_exigida_por_perfil`** — função canônica lê `Tenant.perfil_regulatorio` + atividade e retorna lista de NRs exigidas; fail-closed.
- Ver `glossario.md` deste módulo.

## 12. Como este PRD evolui

- US nova → próximo ID `US-SST-NNN`.
- Mudança em AC já implementado → ADR + novo teste de regressão.
- Mudança na matriz NR × perfil → emenda no PRD + matriz feature-perfil + novo teste predicate.
