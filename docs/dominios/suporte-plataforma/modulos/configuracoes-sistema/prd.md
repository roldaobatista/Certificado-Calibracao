---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/suporte-plataforma/README.md
  - docs/adr/ADR-0002-multi-tenancy.md
  - docs/adr/ADR-0006.md
  - docs/novas funcionalidades.txt
---

# PRD — Módulo Configurações do Sistema (Central de Configurações)

> Product Requirements Document do módulo. Baseado em `docs/novas funcionalidades.txt` linhas 1141-1169 (Adicional 2).

---

## 1. O que este módulo é

Central única e bem estruturada de parâmetros do Aferê por tenant. Cobre configuração da empresa, filiais, numeração de documentos, séries (OS, orçamento, fatura, certificado, NF), impostos, permissões, workflows, status personalizados, campos obrigatórios, modelos de PDF, assinatura, integrações, notificações, regras comerciais, SLA, estoque, financeiro, metrologia, backup e retenção de dados.

## 2. Por que este módulo existe (problema a resolver)

> "Em software grande, muita coisa precisa ser parametrizável. Sem uma central forte de configurações, o sistema fica engessado." — `novas funcionalidades.txt:1167-1168`.

Sem uma central única, configurações ficam dispersas em cada módulo, divergem entre filiais, viram código duro e impedem que o cliente ajuste o sistema sem chamar suporte.

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md` + `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Configuração dos dados da empresa (razão social, CNPJ, IE, endereço, logo).
- Cadastro e configuração de filiais.
- Numeração de documentos (formato, prefixo, próximo número).
- Séries de OS, orçamento, fatura, certificado e nota fiscal.
- Configuração de impostos (regime, alíquotas, CFOP, NCM padrão).
- Configuração de permissões (papéis/roles → recursos).
- Configuração de workflows (etapas, transições, automações por módulo).
- Status personalizados (por entidade configurável: OS, orçamento, chamado, etc.).
- Campos obrigatórios configuráveis por entidade.
- Modelos de PDF (templates de OS, orçamento, certificado, NF, contrato).
- Configuração de assinatura (cert A3, posição assinatura no PDF).
- Configuração de integrações (NF, banco, e-mail, WhatsApp, SEFAZ).
- Configuração de notificações (canais: e-mail, push, SMS, WhatsApp; eventos).
- Regras comerciais (descontos máximos, aprovações por alçada).
- Configuração de SLA (por tipo de chamado, contrato).
- Configuração de estoque (mínimo, máximo, multi-depósito on/off).
- Configuração de financeiro (centro de custo, plano de contas básico, formas pagamento).
- Configuração de metrologia (laboratórios, padrões usados, incerteza padrão).
- Configuração de backup (frequência, retenção, destino).
- Configuração de retenção de dados (por entidade, conforme `docs/conformidade/comum/retencao-matriz.md`).

## 5. Non-goals (o que NÃO está neste módulo)

- Não faz o trabalho de cada módulo (ex: aqui configura SLA; quem usa SLA é o módulo de chamados).
- Não substitui o módulo `onboarding` (este é uso contínuo; onboarding é o setup INICIAL).
- Não gerencia feature flags globais do produto (isso é interno Aferê — ver ADR-0006). Aqui só liga/desliga features liberadas pro tenant.
- Não controla limites de plano/billing (módulo financeiro de contrato).
- Não constrói o motor de workflow (módulo `workflow-bpm` quando criado); aqui só CONFIGURA workflows que aquele motor executa.

## 6. User Stories

### US-CFG-001: Dados da empresa e filiais

**Como** administrador do tenant, **quero** manter dados cadastrais da empresa e filiais, **para** alimentar documentos fiscais e operacionais com info correta.

**Critérios de aceite:**
- **AC-CFG-001-1**: GIVEN admin com permissão, WHEN edita razão social/CNPJ/IE, THEN persiste e dispara evento `Config.EmpresaAtualizada`.
- **AC-CFG-001-2**: GIVEN tenant multi-filial, WHEN cadastra nova filial, THEN exige CNPJ próprio, endereço, e marca uma como matriz.
- **AC-CFG-001-3**: GIVEN edição em massa, WHEN salva, THEN registra auditoria (quem, quando, valor antes/depois).

**Invariantes:** `INV-TENANT-001` (ADR-0002 — toda config isolada por tenant), `SEC-005` (auditoria de mudanças sensíveis).

---

### US-CFG-002: Numeração e séries de documentos

**Como** admin, **quero** configurar formato e numeração de OS, orçamento, fatura, certificado e NF, **para** seguir padrões fiscais e internos.

**Critérios de aceite:**
- **AC-CFG-002-1**: GIVEN nova série, WHEN configurada, THEN define prefixo, próximo número, padding e formato (ex: `OS-{ano}-{seq:6}`).
- **AC-CFG-002-2**: GIVEN série em uso, WHEN tenta diminuir o "próximo número", THEN bloqueia (números gerados são imutáveis).
- **AC-CFG-002-3**: GIVEN documento emitido, WHEN gera, THEN incrementa contador de forma atômica (sem gap nem duplicata).

**Invariantes:** `INV-CFG-001` (numeração estritamente crescente), `INV-006` (idempotência na emissão).

---

### US-CFG-003: Impostos

**Como** admin (ou contador), **quero** configurar regime tributário, alíquotas, CFOP e NCM padrão, **para** que módulos fiscais calculem corretamente.

**Critérios de aceite:**
- **AC-CFG-003-1**: GIVEN regime tributário selecionado (Simples / Lucro Presumido / Lucro Real), WHEN salva, THEN expõe campos relevantes ao regime.
- **AC-CFG-003-2**: GIVEN alíquota mudada, WHEN salva, THEN só vale pra documentos futuros (passados são imutáveis).

**Invariantes:** ADR-0008 (fiscal pluggable), `INV-CFG-002` (config fiscal imutável após emissão de documento).

---

### US-CFG-004: Permissões (RBAC)

**Como** admin, **quero** definir papéis e mapear recursos/ações permitidas, **para** controlar quem faz o quê.

**Critérios de aceite:**
- **AC-CFG-004-1**: GIVEN admin, WHEN cria papel, THEN escolhe módulos e ações (criar/ler/editar/aprovar/excluir).
- **AC-CFG-004-2**: GIVEN papel atribuído a usuário, WHEN usuário tenta ação não permitida, THEN sistema nega com mensagem clara em PT-BR.
- **AC-CFG-004-3**: GIVEN tentativa de remover último admin, WHEN solicitado, THEN bloqueia.

**Invariantes:** `SEC-002` (princípio do menor privilégio), `INV-CFG-003` (sempre ≥1 admin ativo).

---

### US-CFG-005: Workflows e status personalizados

**Como** admin, **quero** configurar etapas, transições e status customizados por entidade (OS, chamado, orçamento), **para** refletir o processo real da empresa.

**Critérios de aceite:**
- **AC-CFG-005-1**: GIVEN entidade configurável, WHEN cria status, THEN define nome, cor, posição no fluxo, transições permitidas.
- **AC-CFG-005-2**: GIVEN status em uso por registros, WHEN tenta excluir, THEN bloqueia (oferece marcar como deprecado + migração de registros).
- **AC-CFG-005-3**: GIVEN transição configurada com aprovação, WHEN executada, THEN exige aprovador da alçada.

---

### US-CFG-006: Campos obrigatórios configuráveis

**Como** admin, **quero** marcar campos como obrigatórios por entidade, **para** garantir qualidade dos dados conforme processo interno.

**Critérios de aceite:**
- **AC-CFG-006-1**: GIVEN entidade, WHEN admin marca campo como obrigatório, THEN validação aplica em criações futuras.
- **AC-CFG-006-2**: GIVEN registros antigos sem o campo, WHEN consultados, THEN não bloqueia (validação só em mutação).

---

### US-CFG-007: Modelos de PDF

**Como** admin, **quero** escolher e customizar template de PDF por tipo de documento (OS, orçamento, certificado, NF, contrato), **para** refletir identidade visual.

**Critérios de aceite:**
- **AC-CFG-007-1**: GIVEN modelos disponíveis, WHEN seleciona um por tipo, THEN aplica em emissões futuras.
- **AC-CFG-007-2**: GIVEN logo enviado, WHEN salva, THEN aparece no header dos PDFs.
- **AC-CFG-007-3**: GIVEN template editado, WHEN salva, THEN versão antiga preservada (auditoria); documentos antigos seguem template usado na emissão.

**Invariantes:** `INV-CFG-004` (template usado na emissão é imutável depois — não regerar PDF emitido com template novo).

---

### US-CFG-008: Configuração de assinatura

**Como** admin, **quero** definir certificado A3 padrão e posição da assinatura no PDF, **para** documentos saírem assinados conforme regra do tenant.

**Critérios de aceite:**
- **AC-CFG-008-1**: GIVEN cert A3 vinculado a usuário, WHEN configurado como padrão da entidade emissora, THEN PDF é assinado client-side (ADR-0009).
- **AC-CFG-008-2**: GIVEN posição definida (coordenadas + página), WHEN PDF gerado, THEN bloco visual aparece no lugar configurado.

**Invariantes:** ADR-0009 (A3 client-side via Lacuna), `SEC-A3-001` (chave privada nunca trafega).

---

### US-CFG-009: Integrações

**Como** admin, **quero** configurar credenciais e endpoints de integrações (NF, banco, e-mail, WhatsApp, SEFAZ), **para** módulos consumirem.

**Critérios de aceite:**
- **AC-CFG-009-1**: GIVEN credencial inserida, WHEN salva, THEN criptografada no KMS por tenant (`SEC-KMS-001`).
- **AC-CFG-009-2**: GIVEN integração ativa, WHEN salva, THEN sistema tenta teste de conectividade e mostra resultado.
- **AC-CFG-009-3**: GIVEN credencial trocada, WHEN salva, THEN registro de auditoria sem expor valor antigo.

**Invariantes:** `SEC-KMS-001`, `SEC-005`, ADR-0008.

---

### US-CFG-010: Notificações

**Como** admin, **quero** configurar quais eventos disparam notificações em quais canais (e-mail, push, SMS, WhatsApp), **para** equipes ficarem cientes do que importa.

**Critérios de aceite:**
- **AC-CFG-010-1**: GIVEN catálogo de eventos, WHEN admin liga "OS atrasada" → "WhatsApp do técnico", THEN evento dispara mensagem no canal.
- **AC-CFG-010-2**: GIVEN canal sem credencial, WHEN admin tenta ativar, THEN bloqueia até configurar integração (US-CFG-009).

---

### US-CFG-011: Regras comerciais e SLA

**Como** admin, **quero** configurar descontos máximos por papel, alçadas de aprovação e SLAs por tipo de chamado/contrato, **para** governança comercial e atendimento.

**Critérios de aceite:**
- **AC-CFG-011-1**: GIVEN desconto além do permitido, WHEN usuário aplica, THEN sistema exige aprovação da alçada superior.
- **AC-CFG-011-2**: GIVEN SLA configurado, WHEN chamado criado, THEN prazo calculado automaticamente.

---

### US-CFG-012: Configurações operacionais (estoque, financeiro, metrologia)

**Como** admin, **quero** parametrizar estoque (multi-depósito, mínimo/máximo), financeiro (centro de custo, plano de contas básico, formas pagamento) e metrologia (laboratórios, padrões, incerteza padrão), **para** módulos operarem com base correta.

**Critérios de aceite:**
- **AC-CFG-012-1**: GIVEN multi-depósito desligado, WHEN módulo estoque é usado, THEN trabalha como depósito único (transparente).
- **AC-CFG-012-2**: GIVEN forma de pagamento removida, WHEN há registros usando, THEN bloqueia (oferece desativar em vez de remover).

---

### US-CFG-013: Backup e retenção de dados

**Como** admin, **quero** configurar frequência de backup, retenção e destino, alinhado à retenção legal por entidade, **para** atender LGPD + ISO 17025 + fiscal.

**Critérios de aceite:**
- **AC-CFG-013-1**: GIVEN config padrão, WHEN tenant é criado, THEN herda matriz `retencao-matriz.md` (admin pode endurecer, não relaxar abaixo do mínimo legal).
- **AC-CFG-013-2**: GIVEN tentativa de baixar retenção abaixo do mínimo legal, WHEN salva, THEN bloqueia com referência à norma.

**Invariantes:** retenção conforme `docs/conformidade/comum/retencao-matriz.md`, `SEC-006` (backup imutável).

---

### US-CFG-014: Ativação de features liberadas (feature flags do tenant)

**Como** admin, **quero** ligar/desligar features liberadas pro meu plano, **para** controlar o que minha equipe enxerga.

**Critérios de aceite:**
- **AC-CFG-014-1**: GIVEN feature liberada pro plano, WHEN admin liga, THEN passa a aparecer pros usuários do tenant.
- **AC-CFG-014-2**: GIVEN feature NÃO liberada pro plano, WHEN admin tenta ligar, THEN bloqueia com mensagem "fale com comercial".

**Invariantes:** ADR-0006 (feature flags), `INV-CFG-005` (flag de tenant não pode burlar limite do plano).

---

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- % de configurações default mantidas vs customizadas (indica quanto o produto serve "fora da caixa").
- Tempo médio entre cliente pedir mudança e config aplicada (idealmente: self-service, 0 atendimento).

## 8. NFR

- **Performance:** leitura de config p95 < 50ms (alto cache, invalidação por evento).
- **Segurança:** SEC-002 (RBAC), SEC-KMS-001 (credenciais criptografadas), SEC-005 (auditoria de mudanças), `INV-TENANT-001`.
- **Disponibilidade:** módulo crítico — SLO 99.95%.

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID livre `US-CFG-NNN`.
- Mudança em AC implementado → ADR + novo teste.
