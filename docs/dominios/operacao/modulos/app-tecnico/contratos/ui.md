---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/adr/0003-mobile-tecnico-campo.md
---

# Contratos de UI — Módulo App do Técnico

> Telas do app mobile (Flutter — ADR-0003). Wireframe textual; visual final fica em design system pós Foundation.

---

## Telas

### Tela 1: Home / Agenda do dia
**Propósito:** ponto de entrada — mostra compromissos do dia.
**Persona principal:** Técnico de Campo.
**US relacionadas:** `US-APP-001`.
**Acessível por:** abertura do app pós-login.

**Elementos:**
- Saudação + data + badge offline (se aplicável).
- Lista vertical de compromissos: horário, cliente, endereço, tipo (OS/chamado/visita), botão "Iniciar".
- FAB "Buscar OS/Chamado" + ícone chat (com badge de não-lidas).
- Bottom nav: Agenda / OS / Chamados / Caixa / Mais.

**Estados:**
- Vazio: "Sem compromissos hoje. Aproveite ou peça uma OS pra base."
- Carregando: skeleton de 3 cards.
- Erro: "Não consegui carregar. Mostrando última versão de [data/hora]."
- Sucesso: lista renderizada.

**Acessibilidade:** AA, navegação por teclado físico (Bluetooth), screen reader (TalkBack/VoiceOver) com labels em PT.
**Mobile:** app nativo Flutter (Android/iOS) — não responsivo web.

---

### Tela 2: Detalhe OS (no app)
**Propósito:** todas ações relativas à OS em execução.
**US:** `US-APP-002`–`US-APP-007`.
**Acessível por:** toque em item da Home ou Lista de OS.

**Elementos:**
- Header com cliente, endereço, equipamento.
- Bloco status: deslocamento|em_servico|concluida.
- Botões de ciclo: "Iniciar deslocamento" → "Pausar/Retomar" → "Cheguei" → "Iniciar serviço" → "Concluir".
- Abas: Serviços | Peças | Fotos | Checklist | Anexos | Assinatura.
- Botão "Solicitar peça" (acessível mesmo offline).

**Estados:**
- Vazio (sem serviços marcados): "Marque o que executou."
- Conflito de sync detectado: banner amarelo "Esta OS foi alterada na base. Revise antes de fechar."

---

### Tela 3: Captura de foto
**Propósito:** anexar foto categorizada à OS.
**US:** `US-APP-006`.

**Elementos:**
- Câmera nativa com overlay de categoria (antes/durante/depois/avaria).
- Botão capturar grande (acessível com luva).
- Preview com opção "Refazer" ou "Anexar".

---

### Tela 4: Checklist
**Propósito:** marcar itens de checklist do serviço.
**US:** `US-APP-006`.

**Elementos:**
- Lista de itens com checkbox grande + campo observação opcional.
- Itens obrigatórios marcados com asterisco vermelho.
- Botão "Salvar e voltar".

**Estados:**
- Bloqueia conclusão da OS se item obrigatório não marcado (toast: "X itens obrigatórios faltam").

---

### Tela 5: Assinatura do cliente
**Propósito:** coletar assinatura tátil + identificação.
**US:** `US-APP-007`.

**Elementos:**
- Campo de assinatura tela cheia (touch).
- Campos: nome cliente, CPF, foto opcional (selfie/RG).
- Botão "Confirmar" → gera PDF de aceite offline.

---

### Tela 6: Lançar despesa
**Propósito:** registro rápido de gasto.
**US:** `US-APP-008`.

**Elementos:**
- Categoria (dropdown: combustível, alimentação, pedágio, hospedagem, outros).
- Valor (teclado numérico).
- Foto do comprovante (obrigatória ou bloqueio).
- Vincular a OS/viagem (opcional).

---

### Tela 7: Solicitar adiantamento
**Propósito:** pedir caixinha de viagem.
**US:** `US-APP-009`.

**Elementos:**
- Valor, justificativa, viagem associada.
- Botão "Enviar pedido".
- Status na tela: solicitado | aprovado | recusado.

---

### Tela 8: Prestação de contas
**Propósito:** fechar viagem.
**US:** `US-APP-009`.

**Elementos:**
- Resumo: total adiantamento, total despesas, saldo (receber/devolver).
- Lista de despesas com possibilidade de remover/editar pendentes.
- Botão "Enviar prestação".

---

### Tela 9: Chat interno
**Propósito:** mensagens com equipe.
**US:** `US-APP-010`.

**Elementos:**
- Lista de threads (1:1, grupos, por OS).
- Conversa estilo mensageria com indicador de leitura.
- Anexo de foto/arquivo curto.

---

### Tela 10: Sync e fila offline
**Propósito:** transparência sobre o que está pendente.
**US:** `US-APP-011`–`US-APP-013`.

**Elementos:**
- Contador: X operações pendentes.
- Botão "Forçar sync agora".
- Lista de operações em conflito com botão "Ver diff" → tela de resolução.

---

### Tela 11: Resolução de conflito
**Propósito:** decidir versão prevalecente.
**US:** `US-APP-013`.

**Elementos:**
- Diff lado a lado (campo a campo): versão local vs versão servidor.
- Por campo: "Manter local" | "Aceitar servidor".
- Botão "Resolver e enviar" (escalona ao coordenador se permissão técnica não bastar).

---

## Componentes reutilizáveis

- Componente "Cartão de OS" — usado em Home, Lista de OS, Resultados de busca.
- Componente "Botão de ciclo de status" — Iniciar/Pausar/Retomar/Concluir.
- Compartilhados com outros módulos: ver `../../../comum/contratos/ui.md`.

## Como esta lista evolui

- Tela nova → adicionar + ligar a US-NNN.
- Mudança em UX → bump CHANGELOG "Modificado".
- Tela descontinuada → `@deprecated` + janela de migração.
