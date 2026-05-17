---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/dominios/comercial/modulos/portal-cliente/prd.md
---

# Contratos de UI — Módulo Portal do Cliente

> Telas externas (consumidas por cliente final do tenant). Mobile-first.

---

## Princípios gerais de UI

- **Mobile-first** — design parte do mobile e expande para desktop.
- **PWA** — instalável "como app" em iOS/Android sem store nesta primeira fase.
- **Sem jargão técnico**. Linguagem para Persona 1 (PF baixa tech-fluência).
- **Branding do tenant** — logo + cores configuráveis por tenant.
- **WCAG AA** obrigatório.
- **Idioma** PT-BR no MVP.

---

## Telas

### Tela 1: Login

**Propósito:** autenticar cliente externo.
**Persona:** todas as 3 do módulo.
**US:** `US-POR-001`.
**Acessível por:** URL pública do portal (subdomínio do tenant ou caminho dedicado).

**Elementos:**
- Logo do tenant + nome.
- Campo "CPF/CNPJ ou e-mail".
- Campo "Senha" + link "Esqueci minha senha".
- Botão "Entrar".
- Link "Receber link de acesso por e-mail/WhatsApp" (link mágico).
- Rodapé: política de privacidade + termos.

**Estados:**
- Vazio: form padrão.
- Carregando: spinner no botão.
- Erro: "Não consegui encontrar essa conta" / "Senha errada — tentativa X de 5" / "Conta bloqueada — tente em 15 min".
- Sucesso: redireciona dashboard.

**Acessibilidade:** labels associados, contraste AA, navegação teclado.

---

### Tela 2: Dashboard do Cliente

**Propósito:** visão geral do que o cliente tem pendente/ativo.
**Persona:** todas.
**US:** `US-POR-002`.
**Acessível por:** home após login.

**Elementos:**
- 4 cards: OS abertas, orçamentos pendentes, faturas a pagar, certificados/calibrações próximas do vencimento.
- Cada card: número grande + label + ícone drill-down.
- Notificações in-app (sininho com badge).
- Menu lateral (mobile: hamburger): OS / Orçamentos / Faturas / Certificados / Mensagens / Perfil / Sair.

**Estados:** padrão.

---

### Tela 3: Minhas OS (Lista)

**Persona:** todas.
**US:** `US-POR-003`.

**Elementos:**
- Filtros: status (todas/em andamento/concluídas/canceladas), busca por nº ou descrição.
- Lista paginada (cards no mobile, tabela no desktop): nº, descrição curta, status (badge colorido), data, técnico (nome simples).
- Tap/clique → Detalhe da OS.

---

### Tela 4: Detalhe da OS (com Timeline)

**Persona:** todas.
**US:** `US-POR-003`, `US-POR-007`.

**Elementos:**
- Cabeçalho: nº, descrição, status atual, técnico responsável.
- **Timeline de status**: lista vertical com data/hora de cada transição (recebida → diagnóstico → orçamento → em execução → concluída → entregue).
- Checklist público (se habilitado): itens marcados ✓ / pendentes.
- Anexos liberados: lista com botão download.
- Botão "Enviar mensagem nesta OS" → abre thread.

---

### Tela 5: Meus Orçamentos (Lista)

**Persona:** PJ admin + PF.
**US:** `US-POR-004`.

**Elementos:**
- Filtros: status (aguardando aprovação / aprovado / rejeitado / expirado).
- Lista: nº, descrição, valor total, validade, status (badge).
- Badge especial "PRECISA SUA APROVAÇÃO" em destaque para aguardando.

---

### Tela 6: Detalhe do Orçamento (com Aprovação)

**Persona:** PJ admin + PF.
**US:** `US-POR-004`, `US-POR-005`.

**Elementos:**
- Cabeçalho: nº, validade (com contador "expira em X dias").
- Lista de itens (produto/serviço, qtde, valor unit, total).
- Total geral + condições de pagamento + condições gerais.
- Anexos (catálogo, foto técnica).
- **Bloco de aprovação** (somente se status = aguardando):
  - Checkbox "Li e concordo com os termos".
  - Botões grandes: "Aprovar" (verde) / "Rejeitar" (vermelho) / "Pedir revisão" (cinza).
- **Modal de confirmação**: "Você está aprovando o orçamento Nº X no valor de R$ Y. Isso vai gerar uma OS automaticamente. Confirma?"
- Se "Rejeitar": modal com motivo (lista predefinida + campo livre opcional).

**Estados especiais:**
- Expirado: botões desabilitados + opção "solicitar revisão".
- Já aprovado/rejeitado: somente leitura + selo + data/hora/quem aprovou.

**Invariantes:** evento WORM com ip + ts + aceite_termos (US-POR-005 AC-1).

---

### Tela 7: Minhas Faturas (Lista)

**Persona:** PJ admin + PF.
**US:** `US-POR-006`.

**Elementos:**
- Filtros: status (em aberto / pagas / vencidas).
- Lista: nº, valor, vencimento, status (badge).
- Total devido em destaque no topo.

---

### Tela 8: Detalhe da Fatura

**Persona:** PJ admin + PF.
**US:** `US-POR-006`.

**Elementos:**
- Cabeçalho: nº, valor, vencimento, status.
- Itens faturados.
- Botões: "Baixar boleto" (PDF) / "Pix QR Code" / "Baixar XML NF-e (se PJ)".
- Para vencidas: botão "Gerar 2ª via" com aviso "vai aplicar juros/multa conforme contrato".

---

### Tela 9: Meus Certificados / Equipamentos

**Persona:** PJ técnico + PF.
**US:** `US-POR-008`.

**Elementos:**
- Lista de equipamentos do cliente.
- Cada equipamento: nome, número série, próxima calibração (com alerta amarelo se < 30 dias / vermelho se vencida).
- Histórico de certificados por equipamento.
- Botão "Baixar certificado PDF" em cada certificado + QR Code do validador RBC/INMETRO.
- Selo "ANULADO" se aplicável.

---

### Tela 10: Mensagens (Lista de Threads)

**Persona:** todas.
**US:** `US-POR-009`.

**Elementos:**
- Lista de threads com badge "não-lidas" por thread.
- Filtros: abertas / encerradas / urgentes.
- Botão "+ Nova mensagem" (vincular OS/orçamento/fatura/outro).

---

### Tela 11: Detalhe da Thread (Chat)

**Persona:** todas.
**US:** `US-POR-009`.

**Elementos:**
- Cabeçalho: assunto + entidade vinculada (link pra OS/orçamento/fatura).
- Lista de mensagens (cliente à direita, atendente à esquerda) com timestamps.
- Campo de digitação + botão anexar (whitelist mime + 25MB max) + botão enviar.
- Toggle "Urgente" (1 uso por thread).

---

### Tela 12: Perfil e Preferências

**Persona:** todas.
**US:** `US-POR-010`, `US-POR-011`.

**Elementos:**
- Aba "Dados cadastrais":
  - Campos editáveis: telefone, e-mail, endereço de entrega.
  - Campos somente-leitura com botão "Solicitar alteração": CNPJ, IE, razão social.
- Aba "Preferências de notificação":
  - Tabela: evento × canal (e-mail / WhatsApp / nenhum).
  - Toggle WhatsApp exige aceite opt-in LGPD.
- Aba "Segurança":
  - Trocar senha.
  - 2FA opcional (Wave C).
  - Sessões ativas (com botão "encerrar todas").

---

### Tela 13: Esqueci minha senha / Link mágico

**Persona:** todas.
**US:** `US-POR-001`.

**Elementos:**
- Campo "CPF/CNPJ ou e-mail".
- Botão "Enviar link" → confirma envio (mesmo se usuário não existir, por segurança: "se este e-mail está cadastrado, você vai receber um link").

---

### Tela 14: Erro / Não autorizado / Sem permissão

**Persona:** todas.

**Elementos:**
- Mensagem PT-BR clara: "Você não tem permissão para ver isso" / "Esse link expirou".
- Botão "Voltar".
- Sem detalhes técnicos (não vazar stack trace).

---

## Componentes reutilizáveis

Compartilhados com outros módulos vão pra `../../../comum/contratos/ui.md`:
- Badge de status (verde/amarelo/vermelho/cinza)
- Card de KPI
- Lista paginada com filtros
- Modal de confirmação
- Componente de aceite LGPD
- Componente de upload com whitelist

## Como esta lista evolui

- Tela nova → linkar US-POR-NNN.
- Mudança UX → bump CHANGELOG.
- Tela deprecada → `@deprecated`.
