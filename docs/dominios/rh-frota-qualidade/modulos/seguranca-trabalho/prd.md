---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
modulo: seguranca-trabalho
dominio: rh-frota-qualidade
relacionados:
  - docs/dominios/rh-frota-qualidade/modulos/colaboradores/prd.md
  - docs/dominios/rh-frota-qualidade/modulos/treinamentos/prd.md
  - docs/dominios/operacao/modulos/ordens-de-servico/prd.md
  - docs/conformidade/comum/lgpd-rat.md#RAT-14
  - docs/conformidade/comum/dpia-modulos-novos.md#DPIA-03
  - docs/conformidade/comum/retencao-matriz.md
---

# PRD — Módulo Segurança do Trabalho (SST)

> Origem: `docs/novas funcionalidades.txt` linhas 1339-1364 (Adicional 9 — Módulo de Segurança do Trabalho).

---

## 1. O que este módulo é

Módulo de Segurança e Saúde do Trabalho voltado a empresas com técnicos em campo. Centraliza EPIs (cadastro, entrega, validade, termo assinado), treinamentos obrigatórios de segurança (NR-10, NR-12, NR-35), ASO, permissão de trabalho, APR, checklist de segurança pré-OS e registro de acidentes / quase-acidentes com evidências fotográficas. Atua como **trava operacional**: bloqueia técnico sem treinamento de segurança válido e bloqueia execução de OS sem checklist preenchido.

## 2. Por que este módulo existe (problema a resolver)

Empresa de assistência técnica + calibração trabalha em campo (galpões, indústrias, altura, eletricidade) e responde por passivo trabalhista direto quando técnico se acidenta sem EPI/treinamento/ASO em dia. Sem trilha documental, multa MTE e ação trabalhista são quase certas. Operação do Roldão (Balanças Solution) já passou por situações de risco que motivam este módulo.

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Cadastro de EPIs (nome, CA, validade do CA, fornecedor, foto).
- Entrega de EPI a colaborador com termo assinado (eletronicamente) + data + assinatura.
- Validade individual do EPI entregue (alerta de troca).
- Treinamentos obrigatórios de segurança: NR-10 (eletricidade), NR-12 (máquinas), NR-35 (altura) e outros configuráveis pelo tenant.
- ASO (Atestado de Saúde Ocupacional): admissional, periódico, retorno, mudança de função, demissional, com validade.
- Permissão de Trabalho (PT) para serviços de risco (altura, espaço confinado, energizado).
- APR (Análise Preliminar de Risco) anexada à OS de risco elevado.
- Checklist de segurança pré-OS (configurável por tipo de serviço).
- Registro de acidente e quase-acidente com evidências fotográficas + descrição + ação corretiva.
- Bloqueio técnico sem treinamento de segurança válido (vínculo com módulo `treinamentos`).
- Bloqueio OS sem checklist de segurança preenchido (vínculo com OS).
- Relatório de segurança por período (acidentes, quase-acidentes, EPIs vencidos, ASOs vencidos).

## 5. Non-goals (o que NÃO está neste módulo)

> LLM não infere por omissão. Proibições positivas.

- **Folha de pagamento de adicional de periculosidade/insalubridade** — vive em `financeiro/` (não existe MVP-1).
- **PCMSO / PGR como documento técnico autoral** — módulo armazena PDF gerado externamente; não gera o documento técnico.
- **eSocial S-2210 (CAT eletrônica)** — V2; MVP só registra o acidente internamente.
- **Cálculo de afastamento INSS** — fora do escopo.
- **SIPAT / palestra anual** — fica em `treinamentos/` como evento; não tem fluxo próprio aqui.
- **Treinamento técnico de produto (calibração, regulagem balança)** — vive em `treinamentos/`. Aqui só treinamentos de **segurança**.
- **Brigada de incêndio / plano de emergência predial** — V2.
- **CIPA (eleição, ata, reuniões)** — V2.

## 6. User Stories

### US-SST-001: Cadastrar EPI com CA e validade
**Como** gerente operacional, **quero** cadastrar EPI com nº de CA e data de validade do CA, **para** garantir que estamos entregando EPI válido legalmente.

**Critérios de aceite:**
- **AC-SST-001-1**: GIVEN cadastro de EPI, WHEN nº de CA está vencido na data de hoje, THEN sistema marca EPI como "CA vencido" e bloqueia entrega futura.
- **AC-SST-001-2**: GIVEN cadastro de EPI, WHEN nº de CA é vazio, THEN entrega bloqueada (campo obrigatório).

**Invariantes:** `INV-001` (audit trail), `INV-TENANT-001` (toda query com tenant_id).

---

### US-SST-002: Entregar EPI com termo assinado eletronicamente
**Como** técnico de SST, **quero** registrar entrega de EPI ao colaborador com termo de recebimento assinado eletronicamente, **para** ter prova jurídica de entrega em ação trabalhista.

**Critérios de aceite:**
- **AC-SST-002-1**: GIVEN entrega de EPI, WHEN colaborador assina (touch / código de confirmação), THEN sistema grava PDF do termo + hash + timestamp em trilha imutável.
- **AC-SST-002-2**: GIVEN entrega sem assinatura, WHEN tenta salvar, THEN bloqueio.

**Invariantes:** `INV-001`, `INV-017` (assinatura digital quando aplicável).

---

### US-SST-003: Alertar EPI / ASO / treinamento de segurança vencido
**Como** gerente SST, **quero** painel com EPIs, ASOs e treinamentos vencidos ou a vencer em 30/60/90 dias, **para** evitar trabalhar com colaborador irregular.

**Critérios de aceite:**
- **AC-SST-003-1**: Painel lista vencidos hoje + vence em ≤30 dias + ≤60 dias + ≤90 dias.
- **AC-SST-003-2**: Notificação automática 30 dias antes do vencimento para o gerente SST.
- **AC-SST-003-3 (LGPD — dado sensível saúde)**: Tratamento do ASO atende base **Art. 11 II "a" — cumprimento de obrigação legal** (NR-7/PCMSO + CLT art. 168 + NR-35); SEM consentimento aplicável (vínculo trabalhista, RAT-14 + DPIA-03). Aferê armazena apenas resultado (apto/inapto/restrição) + validade + PDF — sem CID-10/diagnóstico.
- **AC-SST-003-4 (Retenção)**: ASO conforme `retencao-matriz.md` linha "ASO (Atestado de Saúde Ocupacional)" — **20 anos pós-vínculo (NR-7 item 7.4.5.1)**; obrigação legal vence direito de esquecimento LGPD; após prazo: anonimização (CPF → hash; nome → "Colaborador anonimizado #N") preservando aptidão+validade+médico para auditoria MTE histórica.
- **AC-SST-003-5 (RBAC)**: Acesso ao laudo restrito a perfis "gerente SST" + "RH" + "médico do trabalho" + auditor read-only (DPIA-03 R1); demais perfis veem só "apto/inapto/validade" sem laudo.

---

### US-SST-004: Bloquear técnico sem treinamento de segurança válido
**Como** sistema, **quero** bloquear alocação de técnico em OS que exija NR-10/NR-12/NR-35 se o treinamento estiver vencido, **para** evitar passivo trabalhista.

**Critérios de aceite:**
- **AC-SST-004-1**: GIVEN OS marcada como "exige NR-35 (altura)", WHEN tenta alocar técnico sem NR-35 válida, THEN bloqueio com mensagem clara ao despachante.
- **AC-SST-004-2**: GIVEN técnico tem NR-35 vencida há ≥1 dia, WHEN abre painel de agenda, THEN aparece destacado como "INAPTO — treinamento vencido".

**Invariantes:** `INV-001`, `INV-003` espírito (operar dentro do escopo válido).

**Dependências:** depende de `treinamentos/` (US-TRE-*).

---

### US-SST-005: Bloquear OS sem checklist de segurança preenchido
**Como** sistema, **quero** bloquear execução / fechamento de OS de risco sem checklist de segurança preenchido, **para** garantir que técnico avaliou risco antes de operar.

**Critérios de aceite:**
- **AC-SST-005-1**: GIVEN OS com flag "exige checklist segurança", WHEN técnico tenta marcar OS como "em execução" sem preencher checklist, THEN bloqueio.
- **AC-SST-005-2**: Checklist preenchido fica anexado à OS imutavelmente (`INV-001`).

---

### US-SST-006: Emitir Permissão de Trabalho (PT) para serviço de risco
**Como** gerente SST, **quero** emitir PT por OS de risco (altura, espaço confinado, energizado), **para** atender NR-33/NR-35.

**Critérios de aceite:**
- **AC-SST-006-1**: PT tem validade limitada (1 turno por padrão); expira automaticamente.
- **AC-SST-006-2**: PT exige assinatura do emitente e do executante.

---

### US-SST-007: Anexar APR (Análise Preliminar de Risco) à OS
**Como** técnico, **quero** preencher APR antes de iniciar serviço de risco elevado, **para** documentar riscos e medidas de controle.

**Critérios de aceite:**
- **AC-SST-007-1**: APR é template configurável pelo tenant.
- **AC-SST-007-2**: APR anexada à OS é imutável após assinatura (`INV-001`).

---

### US-SST-008: Registrar acidente / quase-acidente com evidências
**Como** gerente SST, **quero** registrar acidente ou quase-acidente com descrição, fotos, colaboradores envolvidos e ação corretiva, **para** análise e prevenção.

**Critérios de aceite:**
- **AC-SST-008-1**: Registro inclui tipo (acidente / quase-acidente / incidente ambiental), data/hora, local, descrição, fotos, ação corretiva.
- **AC-SST-008-2**: Registro é imutável após confirmação (apenas adendos permitidos — `INV-001`).
- **AC-SST-008-3**: Acidente com afastamento marca colaborador como "afastado por acidente" (sem cálculo, só flag).

---

### US-SST-009: Relatório de segurança por período
**Como** gerente, **quero** relatório consolidado de SST por período (mês/trimestre/ano), **para** acompanhar indicadores e apresentar em reuniões.

**Critérios de aceite:**
- **AC-SST-009-1**: Inclui: nº acidentes, nº quase-acidentes, taxa de frequência, EPIs entregues, ASOs realizados, treinamentos válidos.
- **AC-SST-009-2**: Exportável em PDF e XLSX.

---

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- Taxa de OS executadas com checklist preenchido = 100%.
- Taxa de colaboradores com ASO válido = 100%.
- Tempo médio de resposta a quase-acidente = ≤7 dias.

## 8. NFR

- **Performance:** painel de alertas SST carrega em ≤2s para tenant com 200 colaboradores.
- **Segurança:** SEC-* aplicáveis; dado de ASO é dado pessoal sensível LGPD (saúde) — base legal "obrigação legal".
- **Acessibilidade:** WCAG 2.1 AA (`INV-016`).
- **Imutabilidade:** registro de acidente é imutável (`INV-001`).

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID `US-SST-NNN`.
- Mudança em AC já implementado → ADR + novo teste.
