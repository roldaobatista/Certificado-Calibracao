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

- **Pricing composicional flexível (ADR-0013):** plano monta-se com 7 tipos de componente
  - Base fixa (mensalidade)
  - Faixas de usuários (preço escalonado por seat)
  - Adicional por usuário (overage per-seat)
  - Bundle de módulos (quais módulos vêm inclusos)
  - Add-ons avulsos (módulos opcionais contratados separados)
  - Cobrança por uso variável (NFS-e, WhatsApp, OCR — metered billing)
  - Descontos automáticos (anual, volume, cupom, promoção)
- **Limites duros (hard caps):** bloqueia uso acima do limite (storage, API calls)
- **Catálogo de planos editável via UI** (operador comercial Aferê — US-BIL-009)
- **Versionamento automático de plano** (preço não retroage — assinaturas existentes mantêm snapshot)
- Cobrança recorrente (mensal/anual)
- Usuários por plano (quota por tenant + faixas + overage)
- Módulos liberados por plano (bundle + add-ons; sincronizado com `tenant_features` via ADR-0006)
- Período de teste (trial) com bloqueio automático ao expirar
- Upgrade de plano (proporcionalização imediata)
- Downgrade (efeito no próximo ciclo)
- Cancelamento (com retenção de dados conforme LGPD)
- Suspensão por inadimplência (bloqueio progressivo)
- Histórico de assinaturas (auditável)
- **Fatura da assinatura com breakdown completo** (PDF mensal com linhas detalhadas)
- **Medição de uso variável** (`MeterUsoEvent` consumido pelo cálculo)
- Cupons e descontos (campanhas, parceiros)
- Métricas de uso (consumo vs limite)
- Controle de trial (alertas D-7, D-3, D-0)
- Bloqueio progressivo (warning → read-only → bloqueio total)
- Alertas de proximidade de limite (80% e 100% — duros e cobrados)

## 5. Non-goals (o que NÃO está neste módulo)

- **Multi-moeda (Wave A non-goal explícito — G-BIL-1):** Wave A = **BRL único**. USD/EUR/multi-moeda fica V2 com ADR dedicada (FX rate frozen on invoice, gateway multi-moeda, conversão contábil).
- **Receita reconhecida vs recebida (Wave B non-goal — G-BIL-3):** Wave A só fatura `valor_recebido`. Reconhecimento contábil (accrual basis, deferred revenue) fica Wave B junto com `contabilidade-export` avançado.
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

### US-BIL-009: Operador comercial Aferê monta catálogo de planos com pricing composicional

**Como** operador comercial do Aferê (Roldão ou time comercial), **quero** criar e editar planos comerciais montando componentes de preço flexíveis (base fixa, faixas de usuários, adicional por usuário, bundle de módulos, add-ons opcionais, cobrança por uso, descontos), **para** ajustar a oferta comercial conforme estratégia da empresa sem depender de release de código.

**Contexto:** Roldão sinalizou (17/05/2026 madrugada) que precisa de "vários tipos de configurações" — preço por conjunto de módulos, preço por quantidade de usuários, adicional por usuário extra. ADR-0013 define o modelo composicional com 7 tipos de componente.

**Critérios de aceite:**
- **AC-BIL-009-1**: GIVEN operador comercial autenticado com perfil `comercial_admin_afere`, WHEN acessa tela "Catálogo de Planos" e clica "Novo Plano", THEN sistema abre wizard de 7 passos (um por tipo de componente), permitindo adicionar/configurar/pular cada tipo.
- **AC-BIL-009-2**: GIVEN operador preencheu pelo menos 1 `ComponenteBase` OU 1 `ComponenteFaixaUsuarios`, WHEN clica "Simular fatura", THEN sistema mostra preview de fatura mensal com breakdown (linha por componente) pra cenários sintéticos (1 usuário, 5 usuários, 20 usuários, com/sem uso variável projetado).
- **AC-BIL-009-3**: GIVEN operador clica "Publicar plano novo", WHEN validação passa, THEN sistema cria plano com `versao=plano@v1`, status `ativo`, dispara `BillingSaas.PlanoCriado`, exibe no catálogo de checkout do tenant.
- **AC-BIL-009-4**: GIVEN operador edita plano existente (ex: ajusta `preco_mensal` do `ComponenteBase`), WHEN salva, THEN sistema **cria nova versão automaticamente** (`pro@v1` → `pro@v2`), dispara `BillingSaas.PlanoVersionado` + `BillingSaas.ComponentePrecoMudou`, **assinaturas existentes mantêm v1** (snapshot imutável — INV-026).
- **AC-BIL-009-5**: GIVEN plano tem assinaturas vinculadas E operador tenta excluí-lo, WHEN clica "Excluir", THEN sistema bloqueia com mensagem clara ("este plano tem N assinaturas ativas; depreque-o em vez de excluir") — INV-038.
- **AC-BIL-009-6**: GIVEN operador deprecia plano (clica "Despublicar"), WHEN salva, THEN plano marca `deprecado_em=agora`, some do catálogo público, mas **assinaturas existentes continuam vigentes**.
- **AC-BIL-009-7 (validação)**: GIVEN componentes inválidos (faixa com gap, módulo do bundle fora do catálogo, recurso de uso variável não cadastrado), WHEN operador tenta salvar, THEN sistema rejeita com mensagem explicando qual componente está mal configurado — hook valida.
- **AC-BIL-009-8 (auditoria)**: GIVEN qualquer mudança em plano, WHEN salva, THEN evento gravado em `audit_trail.bi_admin_queries` (ADR-0011 — auditoria do dono Aferê) com `quem`, `quando`, `antes`, `depois` — INV-001.
- **AC-BIL-009-9 (MFA)**: GIVEN operador comercial tenta editar plano que tem ≥10 assinaturas ativas, WHEN clica "Salvar", THEN sistema **exige MFA TOTP** (SEC-MFA-001) — proteção contra alteração massiva acidental.

**Non-goals desta US:**
- **Customização por tenant** — Aferê não cria plano "Pro especial pro cliente X" via UI; plano é único pro mercado (ANTI-11). Se cliente precisa preço diferente, cria-se plano novo no catálogo (com critério comercial).
- **Importar planos de planilha** — operador monta pela UI; bulk import via API só V2.
- **Migrar automaticamente todas as assinaturas pra nova versão** — migração é comando explícito (`migrarVersaoPlano`) por assinatura, não automático.

**Invariantes relacionadas:** `INV-026` (preço não retroage — snapshot imutável), `INV-038` (plano em uso não deletável), `INV-001` (audit trail), `INV-030` (feature flag não burla plano), `SEC-MFA-001` (MFA em operação sensível).

**Dependências:**
- Bloqueado por: ADR-0013 (modelo composicional), ADR-0006 (catálogo de feature flags), ADR-0011 (audit BI), ADR-0012 (autorização do operador comercial).
- Bloqueia: US-BIL-001 (tenant contrata plano — depende de catálogo existir), US-BIL-010 (cálculo de fatura — depende de componentes definidos).

---

### US-BIL-010: Sistema calcula fatura mensal por agregação composicional de componentes

**Como** sistema, **quero** calcular a fatura mensal do tenant agregando todos os componentes aplicáveis do plano contratado (base + faixas + adicional + bundle + addons + uso variável - descontos), **para** que o cliente pague exatamente o que contratou e usou, com breakdown transparente.

**Contexto:** ADR-0013 substitui o cálculo simples (`fatura.valor = plano.preco_mensal`) por agregação de N componentes. Cada componente vira uma `LinhaFatura` no breakdown.

**Critérios de aceite:**
- **AC-BIL-010-1**: GIVEN assinatura ativa com `plano_snapshot` carregando componentes, WHEN job `gerarFatura` roda no dia do vencimento, THEN sistema invoca `CalculadoraFatura.calcular(assinatura, ciclo, periodo)` que retorna `FaturaSaaS` com lista de `LinhaFatura` (uma por componente aplicável).
- **AC-BIL-010-2**: GIVEN plano tem `ComponenteBase` com `preco_mensal=350`, WHEN cálculo roda, THEN gera `LinhaFatura(descricao="Mensalidade base", quantidade=1, preco_unitario=350, subtotal=350)`.
- **AC-BIL-010-3**: GIVEN plano tem `ComponenteFaixaUsuarios` com `[{1-5: R$0}, {6-15: R$35}, {16+: R$25}]` E tenant tem 8 usuários ativos, WHEN cálculo roda, THEN gera `LinhaFatura(descricao="3 usuários (faixa 6-15)", quantidade=3, preco_unitario=35, subtotal=105)` (5 inclusos na faixa 1-5 + 3 cobrados na faixa 6-15).
- **AC-BIL-010-4**: GIVEN plano tem `ComponenteUsoVariavel(recurso=nfse_emitidas, unidade_inclusa=100, preco_por_unidade_extra=0.80)` E tenant emitiu 120 NFS-e no ciclo, WHEN cálculo agrega `MeterUsoEvent`, THEN gera `LinhaFatura(descricao="20 NFS-e além das 100 inclusas", quantidade=20, preco_unitario=0.80, subtotal=16.00)`.
- **AC-BIL-010-5**: GIVEN plano tem `ComponenteAddon(modulo=marketplace, preco_mensal=150)` E `Assinatura.addons_ativos=[marketplace]`, WHEN cálculo roda, THEN gera `LinhaFatura(descricao="Add-on: Marketplace", subtotal=150)`. GIVEN addon NÃO ativo, WHEN cálculo roda, THEN linha NÃO é gerada.
- **AC-BIL-010-6 (desconto)**: GIVEN plano tem `ComponenteDesconto(aplicavel_se=ciclo_anual, desconto_percentual=15)` E assinatura `ciclo=anual`, WHEN cálculo roda após agregar componentes 1-6, THEN gera `LinhaFatura(descricao="Desconto pagamento anual (-15%)", subtotal=-(0.15 × subtotal_parcial), eh_desconto=True)`.
- **AC-BIL-010-7 (consolidação)**: WHEN cálculo termina, THEN `Fatura.valor_bruto = sum(linhas where not eh_desconto)`; `Fatura.descontos_total = abs(sum(linhas where eh_desconto))`; `Fatura.valor_liquido = valor_bruto - descontos_total`; validação rejeita se `valor_liquido < 0`.
- **AC-BIL-010-8 (medição)**: GIVEN módulo `fiscal/` emite NFS-e, WHEN emissão confirma, THEN módulo publica `MeterUsoEvent(tenant_id, recurso=nfse_emitidas, quantidade=1, referencia_externa=nfse_id)` em outbox; consumido pelo `CalculadoraFatura` no fechamento de ciclo. Idempotência forte: evento duplicado (mesmo `referencia_externa`) NÃO cobra duas vezes.
- **AC-BIL-010-9 (snapshot)**: GIVEN plano original foi versionado entre contratação e hoje (`pro@v1` → `pro@v2`), WHEN cálculo roda pra assinatura que tem `plano_versao=pro@v1`, THEN sistema usa `plano_snapshot` (não consulta o plano atual no banco) — preço congelado na contratação (INV-026).
- **AC-BIL-010-10 (limite duro)**: GIVEN plano tem `LimiteDuro(recurso=storage_gb, valor_maximo=50, acao=bloquear_imediato)` E tenant chega em 80% do limite, WHEN publicação roda, THEN dispara `BillingSaas.LimiteDuroAtingido(percentual=80)` (alerta). GIVEN tenant chega em 100%, WHEN ação ocorre, THEN `AuthorizationProvider.can(action="documento.upload", ...)` retorna `denied, reason=limite_duro_estourado`.
- **AC-BIL-010-11 (performance)**: WHEN cálculo da fatura roda, THEN latência < 2s p95 mesmo com 7 componentes + 1000 `MeterUsoEvent` no ciclo (índice composto `(tenant_id, recurso, medido_em)` em `meter_uso_events`).
- **AC-BIL-010-12 (idempotência)**: GIVEN job `gerarFatura` é re-executado pro mesmo `(assinatura_id, periodo)`, WHEN job roda, THEN sistema detecta fatura já existente, NÃO cria duplicata, retorna fatura existente (idempotência por chave natural).

**Non-goals desta US:**
- **Pro-rata em mudança de plano mid-cycle** — US separada (US-BIL-004 cobre upgrade/downgrade); algoritmo de pro-rata fica em `calculadora-fatura.md`.
- **Cobrança preditiva** ("você vai pagar X no próximo ciclo se mantiver o uso") — Wave B/V2; MVP-1 só fatura o ocorrido.
- **Estorno parcial de linha específica** — só estorno total via comando `reembolsar`; granularidade por linha fica V3.

**Invariantes relacionadas:** `INV-026` (snapshot imutável; preço não retroage), `INV-028` (numeração sequencial de fatura por tenant), `INV-001` (audit trail), `INV-TENANT-001` (tenant_id em toda query do cálculo), `SEC-PCI-001` (cobrança via gateway tokenizado).

**Dependências:**
- Bloqueado por: ADR-0013 (modelo composicional), US-BIL-009 (catálogo de planos existir), `MeterUsoEvent` instrumentado nos módulos consumidores (fiscal, omnichannel, gestão-documental), `RuleEngineProvider` (porta #14 ACL), `AuthorizationProvider` (porta #12 ACL — pra limite duro).
- Bloqueia: US-BIL-002 (cobrança recorrente — usa esta calculadora), US-BIL-007 (painel de uso — usa mesmo MeterUsoEvent), US-BIL-008 (NFS-e da assinatura — valor vem desta fatura).

---

### US-BIL-011: Provisioning atômico de novo tenant (state machine 7 etapas)

**Como** sistema (após receber `BillingSaas.AssinaturaCriada`), **quero** executar provisioning em 7 etapas com checkpoints atômicos, **para** garantir que tenant que pagou tenha 100% do acesso pronto antes de ser cobrado pela primeira vez.

**Contexto:** ADR-0015 fluxo 1. Auditor G apontou que hoje cada consumer de `AssinaturaCriada` reage independentemente — sem checkpoint = falha silenciosa.

**Critérios de aceite:**
- **AC-BIL-011-1**: GIVEN `BillingSaas.AssinaturaCriada` publicado, WHEN onboarding inicia, THEN state machine entra em `TENANT_DB_CRIADO` (cria registro em tenants, RLS app.tenant_id provisionado).
- **AC-BIL-011-2**: Cada transição publica evento dedicado (`Onboarding.EtapaConcluida` com `etapa` atual) e grava em audit trail síncrono.
- **AC-BIL-011-3**: GIVEN qualquer etapa falha, WHEN sistema detecta, THEN state machine pausa, publica `Onboarding.ProvisioningFalhou` com `etapa, motivo`, alerta P1 dispara pro dono Aferê. Tenant **NÃO** recebe e-mail de boas-vindas até completar.
- **AC-BIL-011-4**: GIVEN tenant tenta logar antes de estado `PRONTO`, WHEN `AuthorizationProvider.can("login", {tenant_id})` é invocado, THEN retorna `denied, reason="provisioning_em_andamento"`.
- **AC-BIL-011-5**: GIVEN estado atinge `PRONTO`, WHEN sistema confirma, THEN publica `Onboarding.ProvisioningCompletado` + alias `BillingSaas.AssinaturaPronta`. Cobrança recorrente começa a contar a partir desse momento.
- **AC-BIL-011-6**: GIVEN etapa idempotente é re-executada (retry Celery), WHEN sistema processa, THEN não duplica efeito (cria usuário admin → não cria duplicata; e-mail já enviado → não reenvia).
- **AC-BIL-011-7**: GIVEN provisioning leva >5 min, WHEN SLO viola, THEN alerta SEV-2 dispara pra investigação.

**Invariantes:** `INV-INT-007` (provisioning atômico), `INV-001` (audit imutável), `INV-TENANT-001..004`.

**Dependências:** ADR-0015, ADR-0007 (outbox), ADR-0002 (RLS).
**Bloqueia:** uso do tenant em produção; cobrança recorrente.

---

### US-BIL-013: PIX recorrente BCB 1.071/2024 + tipos de MetodoPagamento

**Como** tenant, **quero** pagar a assinatura SaaS via PIX recorrente (mandato bancário), **para** evitar MDR do cartão (3,5% → 0,4%) e chargeback.

**Contexto:** ADR-0052 (G-BIL-2). `MetodoPagamento.tipo` vira enum fechado: `cartao_recorrente | pix_recorrente | boleto | pix_unico`.

**Critérios de aceite:**
- **AC-BIL-013-1**: GIVEN tenant escolhe PIX recorrente no checkout, WHEN gateway redireciona ao Internet Banking, THEN cliente autoriza mandato (valor_teto, periodicidade), banco devolve `mandato_id` opaco; Aferê grava `MetodoPagamento(tipo=pix_recorrente, mandato_id=...)` + emite `BillingSaas.MandatoPixCriado`.
- **AC-BIL-013-2** (`INV-BIL-PIX-001`): GIVEN tentativa de cobrança PIX recorrente, WHEN `mandato_id` ausente OU revogado OU expirado OU `fatura.valor > mandato.valor_teto`, THEN sistema rejeita **antes** de chamar gateway; alerta tenant a renovar mandato.
- **AC-BIL-013-3**: GIVEN cliente revoga mandato no banco, WHEN webhook `MandatoPixRevogado` chega, THEN Aferê pausa cobrança recorrente + alerta tenant a configurar novo método; consumer trata como falha D+0 (dunning).

**Invariantes:** `INV-BIL-PIX-001`, `INV-001`, `SEC-PCI-001` (PIX não é PCI, mas auditoria igual).

**Dependências:** ADR-0052, `PaymentGatewayProvider` (porta #11 ACL).

---

### US-BIL-014: Motivo de churn declarado (voluntário vs involuntário)

**Como** sistema, **quero** registrar `motivo_churn` enum em cancelamento de assinatura, **para** que BI separe churn por causa (G-BIL-4).

**Critérios de aceite:**
- **AC-BIL-014-1**: cancelamento exige escolher `motivo_churn ∈ {voluntario_preco, voluntario_funcionalidade, voluntario_concorrente, voluntario_fechou_empresa, involuntario_inadimplencia, involuntario_falha_pagamento}`.
- **AC-BIL-014-2**: BI dashboard MRR separa churn voluntário × involuntário (ver US-BI-019).

---

### US-BIL-015: Reembolso total cancela NFS-e + estorna gateway + audit

**Como** operador comercial Aferê, **quero** reembolsar total de fatura, **para** desfazer cobrança com rastreabilidade fiscal.

**Critérios de aceite:**
- **AC-BIL-015-1** (G-BIL-6): GIVEN fatura paga, WHEN operador clica "Reembolsar total", THEN sistema **simultaneamente**: (a) chama `PaymentGatewayProvider.reembolsar(valor=None)`; (b) cancela NFS-e via `FiscalProvider.cancel_invoice(motivo)`; (c) audit_trail `fatura.reembolsada` com `quem/quando/motivo`.
- **AC-BIL-015-2**: GIVEN reembolso parcial, WHEN operador tenta, THEN sistema rejeita ("estorno parcial só V3 — US-BIL-010 non-goal"); operador deve cancelar fatura inteira.

---

### US-BIL-016: Plano × feature flag sincronizado em ≤5min

**Como** sistema, **quero** que mudança de plano atualize `tenant_features` em ≤5min (G-BIL-7), **para** features acompanharem contratação sem janela de drift.

**Critérios de aceite:**
- **AC-BIL-016-1**: GIVEN `BillingSaas.PlanoMudouModulos` publicado, WHEN consumer `acesso-seguranca` processa, THEN `tenant_features` sincroniza em ≤5min p95 (SLO).
- **AC-BIL-016-2**: dunning retry usa back-off exponencial (G-BIL-5): D+1, D+3, D+7, D+15 (vs job fixo).

---

### US-BIL-012: Suspensão por inadimplência com modo explícito (read_only / bloqueado_total)

**Como** sistema, **quero** suspender tenant inadimplente em modos distintos (read_only D+7 e bloqueado_total D+15), **para** que módulos consumidores reajam corretamente e features sejam desabilitadas atomicamente.

**Contexto:** ADR-0015 fluxo 3. Auditor G apontou que `TenantSuspenso` hoje não detalha modo → consumers interpretam diferente.

**Critérios de aceite:**
- **AC-BIL-012-1**: GIVEN fatura vencida há 7 dias E ainda não paga, WHEN job diário de suspensão roda, THEN publica `BillingSaas.TenantSuspenso(modo=read_only)`.
- **AC-BIL-012-2**: GIVEN fatura vencida há 15 dias E ainda não paga, WHEN job roda, THEN publica `BillingSaas.TenantSuspenso(modo=bloqueado_total)`.
- **AC-BIL-012-3**: Consumer `acesso-seguranca` modo=read_only: invalida cache Redis `auth:tenant:{id}:*`, força re-auth, AuthorizationProvider passa a negar actions `create/update/delete` mas permite `read`.
- **AC-BIL-012-4**: Consumer `acesso-seguranca` modo=bloqueado_total: encerra TODAS as sessões ativas + bloqueia login até `BillingSaas.TenantReativado`.
- **AC-BIL-012-5**: Consumer billing-saas (callback) modo=bloqueado_total: publica `BillingSaas.PlanoMudouModulos(modulos_removidos=tudo, efetivo_em=imediato)` → features desligam em cascata.
- **AC-BIL-012-6**: Consumer `comunicacao-omnichannel`: envia WhatsApp + e-mail explicando suspensão + link de regularização.
- **AC-BIL-012-7**: GIVEN pagamento confirmado, WHEN `ContasReceber.Pago` chega, THEN publica `BillingSaas.TenantReativado` em ≤5min; consumers re-permitem acesso + re-ativam features.

**Invariantes:** `INV-INT-009` (suspensão desliga features), `INV-001` (audit), `SEC-MFA-001`.

**Dependências:** ADR-0015, ADR-0012 (autorização), ADR-0006 (feature flags).

---

## 7. Métricas de sucesso deste módulo

Ver `metricas.md`. Resumo:
- Taxa de conversão trial→pago ≥ 30%
- Churn mensal ≤ 3%
- MRR (Monthly Recurring Revenue) — crescimento mês a mês
- Taxa de inadimplência ≤ 5%

## 8. NFR

- **Performance:** painel de uso carrega <500ms p95; **cálculo composicional de fatura p95 < 2s mesmo com 7 componentes + 1000 `MeterUsoEvent` no ciclo** (índice composto `(tenant_id, recurso, medido_em)` em `meter_uso_events`); wizard de criação de plano renderiza simulação em <500ms.
- **Disponibilidade:** **SLO 99.95%** (alinhado com domínio Financeiro em `docs/operacao/observabilidade.md`) — billing-saas é a receita do próprio Aferê, indisponibilidade trava contratação de novos tenants e cobrança recorrente. Erro orçamento ≈ 21min/mês. Job de billing é idempotente; falha não duplica cobrança.
- **Segurança (PCI-DSS por delegação):** dados de cartão (PAN, CVV, banda) **nunca passam pelo backend Aferê** — gateway tokeniza no cliente e devolve `gateway_token` opaco (`SEC-PCI-001`). Aferê armazena apenas token + últimos 4 + bandeira. Webhooks de gateway assinados via HMAC e idempotentes por `gateway_event_id`. Configuração de chaves de gateway exige MFA (`SEC-MFA-001`) e fica cifrada via KMS (`INV-009`). Conformidade detalhada em `docs/conformidade/comum/pci-dss.md`.
- **Fiscal:** emissão de NFS-e da assinatura via `FiscalProvider` (ADR-0008) com fallback homologado; nunca retroage (`INV-026`); XML em B2 WORM (`INV-001`).
- **Auditoria:** toda mudança de plano/cobrança/suspensão/emissão fiscal registrada em trilha WORM imutável.

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID livre `US-BIL-NNN`.
- **Adicionar tipo de componente de preço novo (8º tipo além dos 7 da ADR-0013)** → reabrir ADR-0013.
- **Recurso mensurável novo** (ex: `ocr_processados`) → adicionar em `recursos-mensuraveis.md` + hook valida.
- Mudança de plano comercial (criar Plano "Enterprise Plus", retirar Plano "Starter") → versionamento automático cuida; sem ADR.
