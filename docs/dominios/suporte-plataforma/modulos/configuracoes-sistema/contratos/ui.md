---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo Configurações do Sistema

> Telas da central de configurações. Organizada como hub com seções navegáveis.

---

## Telas

### Tela 1: Hub de configurações

**Propósito:** ponto único de entrada com todas as seções de configuração agrupadas.
**Persona principal:** Admin do tenant.
**US relacionadas:** todas as US-CFG-*.
**Acessível por:** menu lateral "Configurações" (visível só pra papéis com permissão).

**Elementos:**
- Cards/sessões: Empresa & filiais, Documentos & séries, Impostos, Permissões & papéis, Workflows & status, Campos obrigatórios, PDFs & assinatura, Integrações, Notificações, Regras comerciais & SLA, Estoque, Financeiro, Metrologia, Backup & retenção, Features.
- Busca rápida (digite "alíquota ICMS" → leva à tela de impostos).
- Indicador de mudança recente (avatar do último editor + timestamp por sessão).

**Estados:**
- Carregando: skeleton de cards.
- Erro: mensagem em PT + retry.

**Acessibilidade:** WCAG AA, navegação por teclado.

---

### Tela 2: Empresa e filiais

**Propósito:** editar dados cadastrais.
**US relacionadas:** `US-CFG-001`.

**Elementos:** formulário razão social, CNPJ, IE, endereço, regime tributário, logo (upload). Lista de filiais com CRUD.

---

### Tela 3: Numeração e séries

**Propósito:** configurar séries por tipo de documento.
**US relacionadas:** `US-CFG-002`.

**Elementos:** lista de séries (tipo, prefixo, próximo número), botão "Nova série", edição com aviso bloqueante ao tentar diminuir o contador.

---

### Tela 4: Impostos

**Propósito:** alíquotas, CFOP, NCM, regime.
**US relacionadas:** `US-CFG-003`.

**Elementos:** lista de impostos por tipo com vigência, formulário de novo imposto, aviso de imutabilidade pós-emissão.

---

### Tela 5: Permissões e papéis

**Propósito:** gestão RBAC.
**US relacionadas:** `US-CFG-004`.

**Elementos:**
- Lista de papéis com nº de usuários.
- Editor de papel: matriz (módulo × ação), checkboxes.
- Aviso bloqueante ao remover último admin.

---

### Tela 6: Workflows e status personalizados

**Propósito:** editor visual (drag-and-drop) ou tabular.
**US relacionadas:** `US-CFG-005`.

**Elementos:**
- Seletor de entidade (OS, chamado, orçamento, etc.).
- Lista de versões do workflow (ativa + histórico).
- Editor: etapas em ordem, transições permitidas, aprovação por alçada, status visuais (cor + nome).
- Avisos ao tentar excluir status em uso.

---

### Tela 7: Campos obrigatórios

**Propósito:** marcar campos como required por entidade.
**US relacionadas:** `US-CFG-006`.

**Elementos:** árvore entidade → campos → toggle obrigatório.

---

### Tela 8: Modelos de PDF

**Propósito:** escolher template por tipo de documento.
**US relacionadas:** `US-CFG-007`.

**Elementos:**
- Lista de tipos (OS, orçamento, certificado, NF, contrato) → modelo ativo.
- Galeria de modelos disponíveis com pré-visualização.
- Upload de logo, customização de cores.
- Aviso: documentos antigos NÃO são regerados com template novo.

---

### Tela 9: Configuração de assinatura

**Propósito:** definir cert A3 padrão e posição no PDF.
**US relacionadas:** `US-CFG-008`.

**Elementos:**
- Seletor de cert A3 (lista dos vinculados aos usuários).
- Editor visual de posição (clica no PDF de pré-visualização).
- Aviso: chave privada nunca trafega (ADR-0009).

---

### Tela 10: Integrações

**Propósito:** conectar sistemas externos.
**US relacionadas:** `US-CFG-009`.

**Elementos:**
- Lista por tipo (NF, banco, e-mail, WhatsApp, SEFAZ).
- Formulário de credenciais (campos sensíveis mascarados, salvo no KMS).
- Botão "Testar conexão" obrigatório antes de ativar.
- Status do último teste (data + resultado).

---

### Tela 11: Notificações

**Propósito:** mapear evento → canal.
**US relacionadas:** `US-CFG-010`.

**Elementos:**
- Catálogo de eventos do sistema (por módulo).
- Por evento: canais ativos + destinatários (papel / usuário / contato).
- Bloqueio se canal sem integração configurada.

---

### Tela 12: Regras comerciais e SLA

**Propósito:** desconto máximo, alçadas, SLAs.
**US relacionadas:** `US-CFG-011`.

**Elementos:**
- Tabela de regras com tipo, parâmetros, vigência.
- Tabela de SLAs por tipo de chamado / contrato / cliente.
- Editor de horário comercial e feriados.

---

### Tela 13: Configurações operacionais (Estoque / Financeiro / Metrologia)

**Propósito:** parâmetros específicos.
**US relacionadas:** `US-CFG-012`.

**Elementos:** abas Estoque (multi-depósito on/off, mínimo, máximo), Financeiro (centro de custo, plano de contas, formas de pagamento), Metrologia (laboratórios, padrões, incerteza padrão).

---

### Tela 14: Backup e retenção

**Propósito:** frequência, retenção, destino.
**US relacionadas:** `US-CFG-013`.

**Elementos:**
- Frequência (diária / semanal / horária).
- Retenção por entidade com mínimo legal mostrado (não editável abaixo).
- Destino (Backblaze B2 — info exibida).
- Botão "Forçar backup agora".

---

### Tela 15: Features (flags do tenant)

**Propósito:** ligar/desligar features liberadas pelo plano.
**US relacionadas:** `US-CFG-014`.

**Elementos:**
- Lista de features liberadas no plano com toggle.
- Features NÃO liberadas aparecem cinzas com "fale com comercial".

---

## Componentes reutilizáveis

- Editor de matriz (módulo × ação) reutilizável em RBAC.
- Editor visual de workflow reutilizável.

## Como esta lista evolui

- Tela nova → ligar US.
- Mudança UX em config sensível → ADR.
