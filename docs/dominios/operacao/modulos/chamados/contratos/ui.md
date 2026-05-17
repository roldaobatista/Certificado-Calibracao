---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: chamados
dominio: operacao
---

# Contratos de UI — Módulo Chamados

> Telas principais. UI desenhada pra triagem em ≤ 30s (US-CH-001).

---

## Tela 1: Triagem rápida (atendente)

**Propósito:** atendente classifica chamado em ≤ 30s.
**Persona:** P-OP-03.
**US:** US-CH-001, US-CH-002.
**Acessível:** botão grande "Novo chamado" no topo do menu Operação.

**Elementos:**
- Campo de busca cliente (autocomplete por nome/telefone/CNPJ) — Enter aceita primeiro resultado.
- Caixa de texto "Cole o WhatsApp ou descreva" — sistema tenta extrair (nome do cliente, equipamento) e pré-preenche.
- Sugestão de equipamento (último do cliente) com 1 tap.
- **Alerta de duplicado** (banner amarelo): "Possível duplicado de #1234 — aberto há 3 dias. Mesclar?" com botões "Sim, é o mesmo" / "Não, é novo".
- Tipo (dropdown com top 5 mais usados primeiro).
- Urgência (default: média; segmented control: baixa/média/alta/crítica).
- Texto livre (opcional).
- Botão grande "Salvar e converter em OS" / "Salvar como chamado" / "Fechar com orientação".

**Atalhos de teclado:** Tab navega; Ctrl+Enter salva como chamado; Ctrl+Shift+Enter converte em OS.

**Estados:**
- Sem cliente identificado → bloqueia salvar; sugere criar cliente novo (link pro módulo Comercial).
- Salvando → spinner pequeno no botão.

**Acessibilidade:** WCAG AA. Labels claros, foco visível, leitor de tela anuncia "duplicado detectado".

---

## Tela 2: Fila de chamados (atendente/gerente)

**Propósito:** ver chamados ativos ordenados por SLA.
**Persona:** P-OP-03 + P-OP-04.
**US:** US-CH-007.

**Elementos:**
- Filtros: estado, canal, atribuído, tipo, urgência.
- Lista com cor de fundo por SLA consumido (verde < 50%, amarelo 50-75%, laranja 75-100%, vermelho > 100% escalado).
- Cada linha: cliente, equip, tipo, urgência, % SLA, tempo restante, atribuído.
- Coluna "ação rápida": Triar / Responder / Converter / Fechar.
- Modo "mapa de calor" (gerente): visão agrupada por atendente mostrando carga + chamados estourando.

**Estados:**
- Vazio: "Nenhum chamado ativo." + botão grande "Novo chamado".

**Mobile:** lista vertical compacta (gerente consulta no celular).

---

## Tela 3: Detalhe do chamado (todos)

**Propósito:** ver histórico de mensagens + ações + auditoria.
**US:** US-CH-003, US-CH-004, US-CH-005, US-CH-006.

**Elementos:**
- Header: número, estado, SLA com barra de progresso, atribuído.
- Aba "Conversa": mensagens cliente ↔ atendente em ordem cronológica, anexos.
- Aba "Triagem": tipo, urgência, equipamento, alertas de duplicado.
- Aba "Histórico": EventoDoChamado timeline.
- Botões de ação variam por estado: "Atribuir", "Converter em OS" (abre wizard), "Fechar com orientação" (exige razão), "Cancelar" (exige razão).

---

## Tela 4: Portal cliente — Acompanhamento

**Propósito:** cliente vê status sem login complexo (link curto WhatsApp).
**Persona:** P-OP-05.
**US:** US-CH-008.

**Elementos:** estado atual + linha do tempo simples + botão "Falar com a gente" (volta pro WhatsApp).

---

## Componentes reutilizáveis

Barra de SLA, badge de urgência, autocomplete de cliente → `../../../comum/contratos/ui.md`.

## Como evolui

Tela nova → ligar a US-CH-NNN.
