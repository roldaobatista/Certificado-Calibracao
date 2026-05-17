---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: estoque
dominio: suporte-plataforma
---

# Contratos de UI — Estoque

## Telas

### Tela 1: Lista de saldos

**Propósito:** ver saldo por (item, local) em ≤ 30s.
**Persona:** almoxarife.
**US:** US-EST-001.

**Elementos:**
- Busca (item ou local)
- Filtros: local, categoria, "abaixo do mínimo", "lote vencendo em 30d"
- Tabela: item, local, saldo, reservado, em trânsito, lote, validade
- Ação por linha: ver kardex, nova transferência, consumir

**Estados:** vazio "sem estoque ainda — dar primeira entrada".

---

### Tela 2: Entrada de peça

**Propósito:** lançar entrada.
**US:** US-EST-002.

**Elementos:** item, local destino, quantidade, lote, validade, NS (se controla serie), origem (NF/manual), foto da NF (opcional).
**Erros:** "lote duplicado para mesmo item — verificar", "validade no passado".

---

### Tela 3: Transferência (emissão)

**Propósito:** emitir transferência.
**US:** US-EST-003.

**Elementos:** origem, destino, item, qtd, lote/NS, observação.
**Estados:**
- Sucesso: "transferência emitida, aguardando aceite de [destino]".
- Erro: "saldo insuficiente: disponível X, pedido Y".

---

### Tela 4 (mobile): Aceite de transferência

**Propósito:** etapa 2 com foto obrigatória.
**Persona:** técnico.
**US:** US-EST-003.

**Elementos:**
- Lista de transferências pendentes pro local do técnico
- Botão "aceitar" → câmera abre → captura foto do lacre → confirmação
- Botão "recusar" → motivo (categoria + texto livre)

**Estados:**
- Sem foto: botão "confirmar aceite" desabilitado; aviso "foto do lacre obrigatória" (BIG-12).
- Erro upload foto: "não foi possível enviar a foto, tentar novamente". (Não deixar passar sem foto.)

---

### Tela 5: Kardex do item

**Propósito:** linha do tempo de movimentos.
**Elementos:** filtros (período, local, tipo); tabela: timestamp, tipo, origem, destino, qtd, lote/NS, OS, usuário; total acumulado.

---

### Tela 6: Inventário

**Propósito:** rodar contagem.
**US:** US-EST-004.

**Elementos:**
- Iniciar inventário (local)
- Tela de contagem com lista de itens; campo "contagem física" por linha
- Coluna calculada "diferença"
- Botão "finalizar" → gera movimentos de ajuste com motivo obrigatório

---

### Tela 7: Configurar mínimo

**Propósito:** definir mínimo/crítico por item/local.
**US:** US-EST-006.

---

### Tela 8: Reserva pra OS

**Propósito:** reservar saldo.
**US:** US-EST-005. Geralmente acionada da tela de OS, não direto aqui.

---

## Acessibilidade

WCAG AA. Tela mobile (Tela 4) deve funcionar bem em 320px de largura.

## Mobile

App/PWA com câmera (BIG-12). Ver ADR-0003.

## Como evolui

- Tela nova → linkar US.
