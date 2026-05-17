---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo Precificação

> Telas + comportamento. Wireframe textual enquanto stack não está fechada.

---

## Telas

### Tela 1: Configurar regra de formação de preço (gestor)

**Propósito:** definir como o preço de cada item é calculado.
**Persona principal:** P-PRC-01 (gestor de pricing).
**US relacionadas:** US-PRC-001.
**Acessível por:** menu Pricing → Regras → escolher item.

**Elementos:**
- Item selecionado (com link para o catálogo).
- Custo direto atual (campo somente leitura — vindo de `custeio-real`).
- Modo (radio): cost-plus / margem-alvo / preço fixo.
- Campos condicionais conforme modo (markup %, margem-alvo %, preço fixo R$).
- Margem-piso % (chão absoluto).
- Preview: preço mínimo calculado + preço sugerido + margem resultante.
- Botões "salvar rascunho" e "publicar nova versão".

**Estados:**
- Sem custo cadastrado: mensagem "Cadastre o custo no módulo Custos Reais antes de definir regra".
- Custo desatualizado (> 90 dias): alerta "custo possivelmente desatualizado".
- Erro de fórmula (margem-alvo > 100%): bloqueia salvar.

**Acessibilidade:** WCAG AA; navegação teclado.

---

### Tela 2: Configurar tabela de preço

**Propósito:** criar/editar tabela por região, segmento ou contrato.
**US:** US-PRC-005.
**Persona:** P-PRC-01.

**Elementos:**
- Nome da tabela.
- Tipo (padrão / região / segmento / contrato).
- Critério de aplicação (form dinâmico: estados/cidades, segmentos, contratos).
- Validade (de/até).
- Grid de itens com preço sugerido + preço mínimo + desconto máx padrão.
- Botões "salvar rascunho" / "publicar nova versão".
- Aviso ao publicar: "esta ação cria nova versão imutável. Orçamentos já emitidos não serão afetados (INV-026)."

**Estados:**
- Conflito de aplicação (2 tabelas aplicáveis ao mesmo cliente): mostrar precedência aplicada.

---

### Tela 3: Configurar faixas de aprovação de desconto

**US:** US-PRC-004.
**Persona:** P-PRC-01.

**Elementos:**
- Lista de faixas (de % até %, aprovador, escopo).
- Botão "+ nova faixa".
- Validação: faixas não podem sobrepor no mesmo escopo.

---

### Tela 4: Painel de pricing no orçamento (vendedor)

**Propósito:** durante criação de orçamento, vendedor vê preços + impacto de desconto.
**US:** US-PRC-003, US-PRC-006.
**Persona:** P-PRC-02 (vendedor).
**Acessível por:** embarcado na tela de orçamento (módulo `orcamentos`).

**Elementos por item:**
- Preço sugerido (default preenchido).
- Preço mínimo (informativo).
- Campo "preço aplicado" (editável).
- Campo "desconto %" (editável).
- Margem resultante (calculada em tempo real, < 200ms).
- Comissão simulada.
- Imposto simulado.
- Alerta visual (amarelo) se desconto > faixa livre → exibe botão "solicitar aprovação".
- Alerta visual (vermelho) se preço < mínimo → bloqueia salvar.

**Elementos do total:**
- Subtotal + impostos + comissão + deslocamento + parcelamento simulado.
- Margem consolidada do orçamento.

**Estados:**
- Aguardando cálculo: skeleton (< 200ms).
- Erro de motor: fallback usa última versão cacheada + aviso.

**Mobile:** essencial (vendedor externo).

---

### Tela 5: Solicitação de aprovação (modal/popup do orçamento)

**US:** US-PRC-004.

**Elementos:**
- Resumo do pedido (cliente, item, desconto, margem resultante).
- Justificativa (textarea opcional).
- Aprovador sugerido (papel + nome).
- Botão "enviar para aprovação".

---

### Tela 6: Caixa de aprovações (aprovador)

**US:** US-PRC-004.
**Persona:** P-PRC-03.
**Acessível por:** menu + notificação push/e-mail.

**Elementos:**
- Lista de pedidos pendentes (mais urgentes primeiro).
- Por item: cliente, vendedor, valor, desconto solicitado, margem resultante.
- Botões "aprovar" / "negar" + justificativa.
- Filtros: vendedor, faixa, antiguidade.

**Mobile:** essencial (decide em movimento).

---

### Tela 7: Dashboard de margem

**Propósito:** monitorar saúde da política de preço.
**US:** US-PRC-007.
**Persona:** P-PRC-01.

**Elementos:**
- KPI: margem média realizada vs alvo.
- Ranking de itens deficitários.
- Ranking de vendedores por margem média.
- Top clientes por desconto concedido.
- Funil de aprovações (pendentes / aprovados / negados).

---

### Tela 8: Histórico de preço praticado

**US:** US-PRC-008.
**Persona:** P-PRC-01.

**Elementos:**
- Filtros: item, cliente, período.
- Timeline (gráfico) de preço médio + dispersão.
- Tabela detalhada (orçamento, data, preço, desconto, margem).
- Export CSV/XLSX.

**Estados:**
- Sem histórico: "ainda não há orçamentos fechados para este filtro."

---

## Componentes reutilizáveis

- Componente "Painel de Pricing" — embarcado em `orcamentos`, `marketplace` (área do cliente), `contratos`.
- Componentes compartilhados em `../../../comum/contratos/ui.md`.

## Como esta lista evolui

- Tela nova → adicionar + ligar a US.
- Mudança em UX → bump CHANGELOG.
- Tela descontinuada → `@deprecated`.
