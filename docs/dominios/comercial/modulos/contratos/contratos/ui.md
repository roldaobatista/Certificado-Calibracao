---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contratos
dominio: comercial
diataxis: reference
---

# Contratos UI — Módulo Contratos (recorrentes)

> Nota: "contratos/" como pasta de specs do módulo Contratos. Tela = experiência de contratos comerciais recorrentes.

## Telas

### 1. Lista de contratos — `/contratos`
**Propósito:** dono/vendedor ver portfólio vigente + alertas.
**Persona:** P-CTR-01 Dono, P-CTR-02 Vendedor.
**Elementos:** filtros (estado, cliente, responsável, vigência fim em N dias, valor), tabela com selo colorido (vigente/a vencer/suspenso/encerrado), KPI topo (MRR total, # a vencer 30d, # suspensos), ação rápida "renovar".
**Estados:** vazio ("nenhum contrato — começar primeiro contrato?"), com alertas em destaque.

### 2. Cadastro de contrato — `/contratos/novo`
**Propósito:** criar contrato novo (US-CTR-001).
**Elementos:**
- Cliente (autocomplete + validação não-bloqueado)
- Escopo: tabela de equipamentos (do módulo equipamentos) + serviços (catálogo) + valor unitário
- Vigência (início, fim ou duração em meses)
- Periodicidade (dropdown: mensal/trimestral/semestral/anual/custom)
- Reajuste (IGP-M/IPCA/% fixo/sem reajuste)
- Template (opcional)
- **Cláusula anti-fidelidade visível** + checkbox aceite cliente
- Botões: "salvar rascunho", "enviar para aprovação cliente"

### 3. Detalhes do contrato — `/contratos/{id}`
**Propósito:** ver vigente + histórico + próximos ciclos.
**Elementos:** cabeçalho (cliente + estado + selo vigência), abas (Escopo, Ciclos previstos/executados, Versões/Aditivos, OS geradas, PDF, Auditoria).

### 4. Bandeja de pré-OS — `/contratos/pre-os` (US-CTR-002)
**Propósito:** atendente revisa e confirma pré-OS geradas.
**Persona:** P-CTR-03 Atendente.
**Elementos:** lista agrupada por contrato/dia, badge "bloqueada — revisar" se cliente inadimplente, ação 1-clique "confirmar e abrir OS" + "ajustar data" + "skip ciclo".

### 5. Wizard de renovação — `/contratos/{id}/renovar` (US-CTR-004, Wave B)
**Persona:** P-CTR-02 Vendedor.
**Elementos:**
- Passo 1: revisar escopo (mantém/altera/adiciona/remove itens)
- Passo 2: ajustar valor (reajuste pré-aplicado, editável)
- Passo 3: nova vigência (default mesma duração)
- Passo 4: enviar pra aprovação do cliente (link público)

### 6. Tela pública de aprovação/encerramento — `/c/{token}` (sem login)
**Propósito:** P-CTR-04 Cliente final aprova contrato/aditivo/renovação OU encerra.
**Elementos:** PDF visual + botão "Aprovar" + botão "Pedir ajuste" + botão "Encerrar" (anti-fidelidade — US-CTR-005). Encerramento mostra explicitamente "sem multa abusiva — apenas X (prejuízo concreto) será cobrado se aplicável".
**Mobile-first.**

### 7. Aditivo — `/contratos/{id}/aditivar` (Wave B)
**Persona:** P-CTR-02 Vendedor.
**Elementos:** snapshot atual + edição + motivo obrigatório + data de aplicação.

### 8. Suspensão — modal em `/contratos/{id}` (Wave B)
**Elementos:** motivo, data início, retomada prevista.

### 9. Encerramento — modal em `/contratos/{id}` ou via tela pública
**Elementos:** motivo obrigatório (dropdown + texto livre), confirmação 2-step, exibe se há prejuízo concreto a cobrar.

### 10. Configuração de templates de contrato — `/configuracoes/contratos/templates`
**Persona:** P-CTR-01 Dono.

## Componentes reutilizáveis

- `<EscopoBuilder>` (tabela equipamentos+serviços+valor) — compartilhado com módulo Orçamentos.
- `<AlertaVigenciaBadge>` colorido por urgência.

## Acessibilidade

- WCAG AA.
- Tela pública de encerramento (`/c/{token}`): botão "encerrar" claramente visível — NÃO escondido em sub-menu (anti-padrão dark pattern).

## Mobile

- Tela pública mobile-first.
- Cadastro de contrato: prioridade desktop.
- Bandeja pré-OS responsiva.

## Como evolui

Tela nova → US-CTR-NNN.
