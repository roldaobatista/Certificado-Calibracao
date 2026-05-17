---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/financeiro/README.md
  - docs/conformidade/comum/pci-dss.md
  - docs/conformidade/comum/lgpd-rat.md#RAT-16
  - docs/conformidade/comum/dpia-modulos-novos.md#DPIA-05
  - docs/conformidade/comum/retencao-matriz.md
  - docs/adr/0008-fiscal-pluggable.md
---

# PRD — Módulo Billing SaaS (Assinaturas e Planos)

> Gestão comercial do próprio software Aferê: planos, limites, cobrança recorrente, trial, suspensão por inadimplência.
>
> **Bloqueador do modelo de negócio SaaS** — sem este módulo, a gestão comercial do próprio software fica manual.

---

## 1. O que este módulo é

Módulo responsável pela monetização do Aferê como SaaS. Controla o ciclo comercial de cada tenant cliente: qual plano contratou, quanto paga, quando vence, quantos usuários pode ter, quais módulos estão liberados, se está em período de teste ou inadimplente.

Não confundir com `contas-receber` (que cobra os CLIENTES dos tenants) — este cobra o **próprio tenant** pelo uso do Aferê.

## 2. Por que este módulo existe

Sem este módulo, a gestão comercial do próprio software fica manual (linha 1508 de `docs/novas funcionalidades.txt`): controle de quem pagou, quem está em trial, quem deve ser bloqueado vira planilha + intervenção humana, e o Aferê não escala.

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Planos comerciais (Perfis A/B/C/D — definidos no PRD do produto)
- Limites por plano (usuários, módulos liberados, volume)
- Cobrança recorrente (mensal/anual)
- Usuários por plano (quota por tenant)
- Módulos liberados por plano (feature flags por tenant)
- Período de teste (trial) com bloqueio automático ao expirar
- Upgrade de plano (proporcionalização imediata)
- Downgrade (efeito no próximo ciclo)
- Cancelamento (com retenção de dados conforme LGPD)
- Suspensão por inadimplência (bloqueio progressivo)
- Histórico de assinaturas (auditável)
- Fatura da assinatura (PDF mensal)
- Cupons e descontos (campanhas, parceiros)
- Métricas de uso (consumo vs limite)
- Controle de trial (alertas D-7, D-3, D-0)
- Bloqueio progressivo (warning → read-only → bloqueio total)

## 5. Non-goals (o que NÃO está neste módulo)

- Cobrança dos CLIENTES dos tenants (isso é `contas-receber`).
- **Emissão técnica de NFS-e**: este módulo **dispara** a emissão da NFS-e da assinatura SaaS (US-BIL-008), mas a integração com prefeitura/Padrão Nacional fica no módulo `fiscal` via `FiscalProvider` (ADR-0008).
- Marketing/landing page de venda (fora do ERP).
- Suporte/onboarding pós-venda (fora deste módulo).
- Definição de qual plano o cliente "deveria" ter (não há recomendador inteligente nesta versão).
- **Processamento de dados de cartão** (PAN, CVV, banda): nunca tocam o backend Aferê — gateway tokeniza e devolve `gateway_token`. PCI-DSS por delegação (ver `docs/conformidade/comum/pci-dss.md`).

## 6. User Stories

### US-BIL-001: Contratar plano comercial inicial

**Como** novo tenant cliente, **quero** escolher um plano (A/B/C/D) ao criar minha conta, **para** ter acesso ao Aferê com limites compatíveis ao meu porte.

**Critérios de aceite:**
- **AC-BIL-001-1**: GIVEN catálogo de planos ativo, WHEN tenant escolhe Plano X, THEN sistema cria assinatura status=`ativa`, registra `plano_atual=X`, dispara evento `BillingSaas.AssinaturaCriada`.
- **AC-BIL-001-2**: GIVEN plano selecionado tem trial, WHEN assinatura é criada, THEN `status=trial`, `trial_termina_em=hoje+N dias`.
- **AC-BIL-001-3**: GIVEN tenant tenta criar assinatura sem método de pagamento e plano não tem trial, WHEN submete, THEN sistema rejeita com `409 método_pagamento_obrigatorio`.

**Invariantes relacionadas:** `INV-TENANT-001` (toda operação carrega `tenant_id`), `INV-030` (assinatura/plano define limite — flag tenant não pode burlar plano contratado).

**Dependências:**
- Bloqueia: US-BIL-002, US-BIL-003.
- Bloqueado por: ADR-0001 (stack), ADR-0002 (multi-tenancy).

---

### US-BIL-002: Cobrar fatura recorrente

**Como** sistema, **quero** gerar e cobrar fatura mensal/anual automaticamente, **para** receber dos tenants sem intervenção humana.

**Critérios de aceite:**
- **AC-BIL-002-1**: GIVEN assinatura ativa com `proximo_vencimento=hoje`, WHEN job de billing roda, THEN cria fatura, tenta cobrar via gateway (Stripe/PagSeguro), registra resultado.
- **AC-BIL-002-2**: GIVEN cobrança aprovada, WHEN gateway retorna sucesso, THEN `fatura.status=paga`, atualiza `proximo_vencimento`, dispara evento `BillingSaas.FaturaPaga`.
- **AC-BIL-002-3**: GIVEN cobrança recusada, WHEN gateway retorna falha, THEN `fatura.status=falhou`, agenda nova tentativa em D+1, D+3, D+7, dispara evento `BillingSaas.CobrancaFalhou`.

- **AC-BIL-002-4**: GIVEN operador comercial Aferê precisa configurar gateway (chaves de API, segredos de webhook, credenciais OAuth) WHEN acessa tela de configuração de gateway, THEN sistema **exige MFA ativo** (`SEC-MFA-001`) e registra a operação em trilha WORM (`INV-001`); chaves armazenadas cifradas via KMS (`INV-009`), nunca em texto plano nos logs.
- **AC-BIL-002-5 (LGPD)**: Tratamento atende base **Execução de contrato (art. 7º V) + Obrigação fiscal (art. 7º II)** (RAT-16 + DPIA-05). Aferê armazena somente: nome/CPF/CNPJ do contratante, token opaco do gateway, bandeira, últimos 4. **NUNCA** PAN completo, CVV, dados de track.
- **AC-BIL-002-6 (Retenção)**: Fatura conforme `retencao-matriz.md` linha "Cobrança recorrente Billing SaaS" (token: vigência + 30 dias; fatura: 5 anos fiscal); após prazo: token revogado no gateway + descartado; fatura anonimizada + crypto-shredding.
- **AC-BIL-002-7 (Webhook seguro)**: Webhook do gateway valida assinatura HMAC + IP allowlist do gateway + idempotência por `event_id` (DPIA-05 R1).
- **AC-BIL-002-8 (Log seguro)**: Filtro de log com regex PAN/CVV (PCI-DSS req 3.3); rejeição em CI (DPIA-05 R2, hook `log-pci-scanner.sh` a criar).
- **AC-BIL-002-9 (Cobrança cancelada)**: Após 3 falhas consecutivas sistema bloqueia novas tentativas e abre ticket para tenant regularizar (DPIA-05 R5, CDC art. 39).

**Non-goals:** este módulo NÃO processa cartões diretamente — dados de cartão (PAN, CVV, banda magnética) **nunca passam pelo backend Aferê**. Cliente do tenant insere o cartão diretamente no formulário hospedado/SDK do gateway (Stripe/PagSeguro/Asaas), que tokeniza e devolve `gateway_token` (token opaco). Aferê armazena apenas o token + últimos 4 dígitos + bandeira (já mascarados pelo próprio gateway). Conformidade PCI-DSS por delegação — ver `docs/conformidade/comum/pci-dss.md`.

**Invariantes relacionadas:** `SEC-PCI-001` (proibido armazenar PAN/CVV), `INV-TENANT-001`, `INV-001` (audit), `INV-009` (segredos via KMS), `SEC-MFA-001` (MFA obrigatório em configuração de gateway).

---

### US-BIL-003: Suspender por inadimplência (bloqueio progressivo)

**Como** sistema, **quero** bloquear progressivamente tenants inadimplentes, **para** proteger receita sem cortar acesso de forma abrupta.

**Critérios de aceite:**
- **AC-BIL-003-1**: GIVEN fatura vencida há 3 dias, WHEN job roda, THEN tenant recebe warning banner + email; operação normal.
- **AC-BIL-003-2**: GIVEN fatura vencida há 7 dias, WHEN job roda, THEN tenant entra modo `read-only` (não cria/edita; lê e exporta).
- **AC-BIL-003-3**: GIVEN fatura vencida há 15 dias, WHEN job roda, THEN tenant é bloqueado totalmente (`status=suspensa`), apenas área de regularização acessível.
- **AC-BIL-003-4**: GIVEN tenant suspenso paga fatura, WHEN pagamento confirma, THEN reativação automática em <5min.

**Invariantes:** dados do tenant suspenso NÃO são apagados durante a janela LGPD definida em `docs/conformidade/comum/retencao-matriz.md`.

---

### US-BIL-004: Upgrade/Downgrade de plano

**Como** tenant, **quero** mudar de plano, **para** acompanhar crescimento (upgrade) ou economizar (downgrade).

**Critérios de aceite:**
- **AC-BIL-004-1**: GIVEN tenant no Plano B, WHEN solicita upgrade pra Plano C, THEN sistema cobra diferença proporcional do ciclo atual, libera limites/módulos imediatamente.
- **AC-BIL-004-2**: GIVEN tenant no Plano C, WHEN solicita downgrade pra Plano B, THEN mudança agendada pro próximo ciclo; valida que uso atual cabe no Plano B (senão exige redução antes).

---

### US-BIL-005: Trial com bloqueio automático

**Como** sistema, **quero** controlar período de teste, **para** converter trial em pago sem deixar uso indefinido grátis.

**Critérios de aceite:**
- **AC-BIL-005-1**: GIVEN assinatura `status=trial`, WHEN faltam 7/3/1 dias pro fim, THEN envia email + banner.
- **AC-BIL-005-2**: GIVEN trial expira sem método de pagamento configurado, WHEN job roda, THEN bloqueia tenant (`status=trial_expirado`).
- **AC-BIL-005-3**: GIVEN trial expira COM método de pagamento configurado, WHEN job roda, THEN converte pra `status=ativa`, cobra primeira fatura.

---

### US-BIL-006: Aplicar cupom de desconto

**Como** tenant, **quero** aplicar cupom, **para** receber desconto promocional ou de parceiro.

**Critérios de aceite:**
- **AC-BIL-006-1**: GIVEN cupom válido e dentro da janela, WHEN tenant aplica, THEN desconto incide na próxima fatura conforme regra (% ou valor fixo, único ou recorrente N ciclos).
- **AC-BIL-006-2**: GIVEN cupom expirado/já usado/inválido, WHEN tenta aplicar, THEN sistema rejeita com mensagem clara.

---

### US-BIL-007: Consultar métricas de uso vs limites

**Como** tenant, **quero** ver meu consumo (usuários, módulos, volume) vs limite do plano, **para** decidir se preciso fazer upgrade.

**Critérios de aceite:**
- **AC-BIL-007-1**: GIVEN tenant logado, WHEN abre painel de uso, THEN mostra: usuários ativos / limite, módulos liberados, % consumo de cada limite mensurável.
- **AC-BIL-007-2**: GIVEN consumo passa 80% do limite, WHEN tela carrega, THEN exibe alerta sugerindo upgrade.

---

### US-BIL-008: Emitir NFS-e da fatura da assinatura SaaS

**Como** Aferê (empresa emissora do SaaS), **quero** emitir automaticamente NFS-e da assinatura paga pelo tenant cliente, **para** cumprir obrigação fiscal do próprio Aferê sem intervenção manual e sem depender de planilha.

**Critérios de aceite:**
- **AC-BIL-008-1**: GIVEN fatura SaaS com `status=paga` (evento `BillingSaas.FaturaPaga` emitido), WHEN trigger automático dispara, THEN módulo `fiscal/` é chamado via `FiscalProvider.emit_invoice()` (ADR-0008) passando `tenant_id` do cliente como `customer_taxid` e CNPJ do Aferê como `issuer_taxid`; resultado registra `nfse_id`, `authorization_code`, `pdf_url` na Fatura SaaS e dispara evento `BillingSaas.NFSeEmitida`.
- **AC-BIL-008-2**: GIVEN emissão de NFS-e rejeitada pela prefeitura/PlugNotas, WHEN `InvoiceResult.status=REJECTED`, THEN sistema registra `rejection_reason`, mantém fatura `paga` (cobrança não retroage), dispara evento `BillingSaas.NFSeFalhou`, alerta operador comercial Aferê (P1).
- **AC-BIL-008-3**: GIVEN provider primário (PlugNotas) indisponível, WHEN circuit breaker abre, THEN sistema usa fallback (Focus NFe) automaticamente — contingência SVC-AN homologada (`INV-007`).
- **AC-BIL-008-4**: GIVEN NFS-e já emitida com sucesso para uma fatura, WHEN reprocessamento for tentado (job retry, webhook duplicado), THEN sistema **NÃO retroage nem reemite** — operação idempotente (`INV-026`); XML armazenado em B2 WORM (`INV-001` audit).

**Non-goals desta US:**
- Cancelamento de NFS-e por desistência do tenant → fluxo separado (US futura no módulo `fiscal/`).
- Configuração de regime tributário (Simples Nacional vs Lucro Presumido) do próprio Aferê → fora deste módulo; vem do cadastro fiscal global.

**Invariantes relacionadas:** `INV-007` (contingência SVC-AN homologada), `INV-001` (trilha WORM da emissão), `INV-026` (operações fiscais não retroagem), `INV-TENANT-001` (todo evento carrega `tenant_id` do cliente).

**Dependências:**
- Bloqueado por: ADR-0008 (FiscalProvider pluggable), módulo `fiscal/` (implementação `PlugNotasProvider` + `FocusNFeProvider`), cadastro fiscal do Aferê (CNPJ, regime, código de serviço municipal).
- Bloqueia: encerramento contábil mensal automático.

---

## 7. Métricas de sucesso deste módulo

Ver `metricas.md`. Resumo:
- Taxa de conversão trial→pago ≥ 30%
- Churn mensal ≤ 3%
- MRR (Monthly Recurring Revenue) — crescimento mês a mês
- Taxa de inadimplência ≤ 5%

## 8. NFR

- **Performance:** painel de uso carrega <500ms p95; cálculo de cobrança recorrente p99 <2s.
- **Disponibilidade:** **SLO 99.95%** (alinhado com domínio Financeiro em `docs/operacao/observabilidade.md`) — billing-saas é a receita do próprio Aferê, indisponibilidade trava contratação de novos tenants e cobrança recorrente. Erro orçamento ≈ 21min/mês. Job de billing é idempotente; falha não duplica cobrança.
- **Segurança (PCI-DSS por delegação):** dados de cartão (PAN, CVV, banda) **nunca passam pelo backend Aferê** — gateway tokeniza no cliente e devolve `gateway_token` opaco (`SEC-PCI-001`). Aferê armazena apenas token + últimos 4 + bandeira. Webhooks de gateway assinados via HMAC e idempotentes por `gateway_event_id`. Configuração de chaves de gateway exige MFA (`SEC-MFA-001`) e fica cifrada via KMS (`INV-009`). Conformidade detalhada em `docs/conformidade/comum/pci-dss.md`.
- **Fiscal:** emissão de NFS-e da assinatura via `FiscalProvider` (ADR-0008) com fallback homologado; nunca retroage (`INV-026`); XML em B2 WORM (`INV-001`).
- **Auditoria:** toda mudança de plano/cobrança/suspensão/emissão fiscal registrada em trilha WORM imutável.

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID livre `US-BIL-NNN`.
- Mudança de plano comercial (criar Plano E, retirar Plano A) → ADR obrigatório.
