---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo Marketplace

> Telas + comportamento. Wireframe textual enquanto stack não está fechada.

---

## Telas

### Tela 1: Vitrine pública (home do marketplace)

**Propósito:** primeira impressão; mostra catálogo + destaques + busca + categorias.
**Persona principal:** P-MKT-01 (visitante anônimo).
**US relacionadas:** US-MKT-001, US-MKT-005.
**Acessível por:** URL pública do tenant (subdomínio ou domínio próprio).

**Elementos:**
- Header: logo do tenant, busca, login, contato.
- Banner de destaques (carrossel ou grid, conforme tema).
- Categorias (chips/abas).
- Grid de produtos/serviços (com preço, ou "consulte" se tabela privada).
- Footer: contato, redes sociais, LGPD, termos.

**Estados:**
- Vazio (sem itens publicados): mensagem "catálogo em montagem — entre em contato".
- Carregando: skeleton de cards.
- Erro: "não conseguimos carregar o catálogo. Tente novamente."

**Acessibilidade (WCAG):** AA; navegação por teclado obrigatória; alt em imagens; contraste mínimo 4.5:1.

**Mobile:** responsivo (60% do tráfego esperado).

---

### Tela 2: Ficha do item (produto ou serviço)

**Propósito:** detalhe completo + botão "adicionar ao carrinho".
**Persona principal:** P-MKT-01 / P-MKT-02.
**US relacionadas:** US-MKT-001, US-MKT-002.
**Acessível por:** clique no card da vitrine ou link direto.

**Elementos:**
- Galeria de imagens.
- Título + categoria + tempo médio (se serviço) + faixa de preço.
- Descrição (markdown).
- FAQ.
- Botões "adicionar ao carrinho" / "solicitar orçamento direto".
- Itens relacionados.

**Estados:**
- Item esgotado/indisponível: badge "consulte disponibilidade" + botão desabilitado.

---

### Tela 3: Carrinho de solicitação

**Propósito:** revisar itens antes de enviar.
**Persona principal:** P-MKT-01 / P-MKT-02.
**US relacionadas:** US-MKT-002.
**Acessível por:** ícone de carrinho no header.

**Elementos:**
- Lista de itens (nome, qtd editável, preço snapshot, remover).
- Subtotal estimado (com aviso "valor final pode variar conforme análise").
- Botão "solicitar orçamento" → vai para Tela 4.

**Estados:**
- Vazio: "seu carrinho está vazio. Volte à vitrine."

---

### Tela 4: Formulário de solicitação

**Propósito:** captar dados mínimos para gerar lead + orçamento rascunho.
**US:** US-MKT-002.

**Elementos:**
- Nome (obrigatório).
- Telefone com WhatsApp (obrigatório).
- E-mail (obrigatório).
- CNPJ/CPF (opcional).
- Observações (opcional, textarea).
- Canal preferido (radio: WhatsApp / e-mail).
- Termo LGPD (checkbox obrigatório, link para política).
- CAPTCHA (anti-spam).
- Botão "enviar solicitação".

**Estados:**
- Erro de validação: campo destacado + mensagem em PT.
- Enviando: botão desabilitado + spinner.
- Sucesso: redirect para Tela 5 + e-mail/WhatsApp de confirmação enviado.

---

### Tela 5: Confirmação da solicitação

**Propósito:** dar feedback claro + protocolo de acompanhamento.
**Elementos:** número do protocolo, próximos passos, link para área do cliente (se cadastrou).

---

### Tela 6: Login da área do cliente

**Persona:** P-MKT-02.
**US:** US-MKT-003.
**Elementos:** e-mail + senha, link "esqueci minha senha", botão "criar acesso" (envia link mágico para e-mail já cadastrado em OS anterior).

---

### Tela 7: Área do cliente — dashboard

**Propósito:** hub do cliente logado.
**US:** US-MKT-003.
**Acessível por:** após login.

**Elementos (abas):**
- Solicitações abertas.
- Orçamentos pendentes (com botão "aprovar" — reusa fluxo US-ORC-002).
- OS em andamento (com status + previsão).
- Contratos ativos (com renovação/cancelamento).
- Faturas (paga/pendente/atrasada, com botão "pagar" se gateway habilitado).
- Certificados emitidos (download).

**Estados:**
- Vazio em cada aba: mensagem específica + CTA para voltar à vitrine.

---

### Tela 8: Curadoria de vitrine (gestor)

**Persona:** P-MKT-03.
**US:** US-MKT-005.
**Acessível por:** área administrativa do tenant.

**Elementos:**
- Grid drag-and-drop de itens.
- Toggle destaque por item.
- Toggle ativo/inativo.
- Editor de descrição marketing + imagens.

---

### Tela 9: Funil de conversão

**Persona:** P-MKT-03.
**US:** US-MKT-007.

**Elementos:** funil visual (visita → carrinho → solicitação → orçamento → fechamento), com filtros por período e UTM.

---

## Componentes reutilizáveis

Componentes compartilhados ficam em `../../../comum/contratos/ui.md`.

## Como esta lista evolui

- Tela nova → adicionar + ligar a US.
- Mudança em UX → bump CHANGELOG.
- Tela descontinuada → marcar `@deprecated`.
