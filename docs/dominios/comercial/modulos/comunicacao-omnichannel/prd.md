---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/comercial/README.md
  - docs/comum/integracoes-externas/whatsapp.md
  - docs/conformidade/comum/lgpd-rat.md#RAT-12
  - docs/conformidade/comum/dpia-modulos-novos.md#DPIA-04
  - docs/conformidade/comum/retencao-matriz.md
---

# PRD — Módulo Comunicação Omnichannel

> Caixa de entrada unificada (WhatsApp + e-mail + SMS + chat do portal) com histórico por cliente / OS / orçamento, templates, automações e conformidade LGPD.

---

## 1. O que este módulo é

Camada única de conversa com o cliente. Centraliza canais (WhatsApp, e-mail, SMS, chat do portal), preserva histórico por entidade do CRM (cliente, OS, orçamento, chamado), e suporta automação (templates, respostas rápidas, mensagens disparadas por evento). Garante consentimento LGPD e opt-in/opt-out auditáveis.

## 2. Por que este módulo existe (problema a resolver)

Hoje a comunicação com cliente vive espalhada em celulares pessoais, e-mails individuais e grupos de WhatsApp. Resultados: contexto perdido quando atendente sai, falta de evidência LGPD de consentimento, retrabalho ("já te mandei isso?"), violação de prazo por mensagem ignorada e risco fiscal/regulatório quando um envio cobra ou afirma algo sem trilha.

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md` + `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Caixa de entrada unificada (WhatsApp, e-mail, SMS, chat portal).
- Histórico por cliente, por OS, por orçamento, por chamado.
- Templates de mensagem versionados.
- Respostas rápidas (atalhos de teclado/clique).
- Mensagens automáticas disparadas por evento (`SLA.AlertaPreventivo`, `OS.Encerrada`, `Orcamento.Aprovado`, etc.).
- Distribuição (round-robin / por carteira / por skill) para atendentes.
- Status de leitura/entrega por canal (quando suportado).
- Gravação de consentimento (LGPD): opt-in/opt-out, data, canal, base legal.
- Conversão conversa → chamado e conversa → lead.
- Relatórios de atendimento (volume, TMA, taxa de conversão).

## 5. Non-goals (o que NÃO está neste módulo)

- **NÃO** substitui telefonia / call center voz (apenas conversa por texto).
- **NÃO** processa pagamento em conversa (link de pagamento vem do Financeiro).
- **NÃO** assina certificado digital nas mensagens (cláusula informal; não tem valor jurídico de assinatura).
- **NÃO** cria contratos (envia comunicação sobre eles).
- **NÃO** decide automaticamente cobranças (apenas envia conforme regra configurada).
- **NÃO** implementa o conector WhatsApp/SMS/e-mail por dentro — usa adaptadores em `docs/comum/integracoes-externas/` (porta Anti-Corruption Layer).

## 6. User Stories

### US-COM-001: Atender mensagens em caixa unificada

**Como** atendente, **quero** ver todas as mensagens (WhatsApp + e-mail + SMS + chat) em uma única caixa, **para** responder sem alternar entre apps.

**Critérios de aceite:**
- **AC-COM-001-1**: GIVEN mensagens chegando em 4 canais, WHEN abro caixa, THEN vejo lista unificada com filtros por canal, status (não lida, em andamento, resolvida) e atribuição.
- **AC-COM-001-2**: GIVEN mensagem selecionada, WHEN clico, THEN vejo thread completa daquele cliente naquele canal + sidebar com histórico cross-canal do cliente.
- **AC-COM-001-3**: GIVEN cliente identificado pelo número/e-mail, WHEN clico no nome, THEN abre ficha do cliente do CRM.

**Invariantes:** `INV-TENANT-001`.

**Dependências:** bloqueado por `docs/comum/integracoes-externas/whatsapp.md`, conectores e-mail/SMS, módulo CRM/clientes.

---

### US-COM-002: Registrar consentimento LGPD ao primeiro contato

**Como** atendente, **quero** que o sistema registre o consentimento do cliente para receber comunicações comerciais, **para** atender LGPD sem retrabalho.

**Critérios de aceite:**
- **AC-COM-002-1**: GIVEN cliente novo entrando em contato, WHEN inicio thread, THEN sistema dispara mensagem padrão de boas-vindas com termo de consentimento + opções (aceito / recuso / mais informações).
- **AC-COM-002-2**: GIVEN resposta do cliente, WHEN registra "aceito"/"recuso", THEN consentimento fica vinculado ao cliente com base legal, canal, timestamp e texto exato apresentado.
- **AC-COM-002-3**: GIVEN cliente sem consentimento ativo, WHEN tento enviar mensagem promocional/de marketing, THEN sistema bloqueia (mensagens transacionais essenciais ao serviço seguem permitidas com base legal de execução de contrato).

**Invariantes:** `INV-TENANT-001`, registro de consentimento WORM.

- **AC-COM-002-4 (LGPD):** Tratamento atende base **Consentimento explícito (art. 7º I)** para marketing/comercial; **Execução de contrato (art. 7º V)** para transacional essencial (RAT-12 + DPIA-04). Cada finalidade tem toggle individual e versão do termo registrada.
- **AC-COM-002-5 (Retenção):** Histórico de consentimento conforme `retencao-matriz.md` linha "Histórico de consentimento Comunicação Omnichannel" (opt-out + 6 meses); após prazo: anonimização (telefone/e-mail → hash) preservando registro de revogação para prova LGPD art. 8º.

**Dependências:** bloqueado por `docs/conformidade/comum/lgpd-rat.md`.

---

### US-COM-003: Opt-out a qualquer momento

**Como** cliente, **quero** poder pedir opt-out em qualquer canal a qualquer momento, **para** exercer direito LGPD.

**Critérios de aceite:**
- **AC-COM-003-1**: GIVEN mensagem do cliente com texto "SAIR", "PARAR", "STOP", "CANCELAR" (lista configurável), WHEN sistema recebe, THEN registra opt-out, envia confirmação e bloqueia futuras mensagens não-transacionais.
- **AC-COM-003-2**: GIVEN opt-out registrado, WHEN qualquer disparo automático for processado, THEN é bloqueado e marcado em log.
- **AC-COM-003-3**: GIVEN cliente em opt-out solicita reativação, WHEN registra novo opt-in explícito, THEN o ciclo recomeça.

**Invariantes:** opt-out é imediato; falha em bloquear comunicação é vazamento LGPD.

- **AC-COM-003-4 (LGPD):** Bloqueio implementado em camada de envio (não na UI) — DPIA-04 R1; qualquer chamada `enviar(cliente, canal, finalidade)` consulta tabela de consentimento, falha = exceção bloqueante + alerta crítico.

---

### US-COM-004: Templates de mensagem versionados

**Como** gerente comercial, **quero** cadastrar templates aprovados (especialmente WhatsApp Business — exige aprovação Meta), **para** garantir conformidade e padrão.

**Critérios de aceite:**
- **AC-COM-004-1**: GIVEN template novo, WHEN cadastro com variáveis (`{{cliente.nome}}`, `{{os.numero}}`), THEN sistema valida e marca status "pendente aprovação" (se canal exigir).
- **AC-COM-004-2**: GIVEN template aprovado pelo canal externo (ex: Meta), WHEN status atualiza, THEN fica disponível para uso.
- **AC-COM-004-3**: GIVEN template em uso, WHEN tento editar, THEN sistema exige nova versão (templates aprovados são imutáveis).

---

### US-COM-005: Respostas rápidas e atalhos

**Como** atendente, **quero** atalhos para respostas comuns ("/preco", "/horario", "/endereco"), **para** ganhar produtividade.

**Critérios de aceite:**
- **AC-COM-005-1**: GIVEN atendente digita "/preco" no chat, WHEN seleciono, THEN texto é expandido com variáveis preenchidas.
- **AC-COM-005-2**: GIVEN atalho mostrar lista, WHEN digito "/", THEN aparece dropdown filtrado.

---

### US-COM-006: Mensagem automática por evento de outro módulo

**Como** gerente, **quero** disparar mensagem automática quando um evento ocorre (OS encerrada, orçamento aprovado, SLA em risco), **para** manter cliente informado sem ação manual.

**Critérios de aceite:**
- **AC-COM-006-1**: GIVEN regra "ao `OS.Encerrada` enviar WhatsApp template `os-encerrada-v1`", WHEN evento ocorre, THEN sistema dispara para canal de preferência do cliente.
- **AC-COM-006-2**: GIVEN cliente sem opt-in, WHEN regra dispararia, THEN sistema bloqueia e registra motivo no log.
- **AC-COM-006-3**: GIVEN canal preferido indisponível (ex: WhatsApp falhou), WHEN regra de fallback configurada, THEN tenta canal seguinte (SMS, e-mail).

**Invariantes:** disparo automático respeita opt-out (`US-COM-003`).

---

### US-COM-007: Distribuição entre atendentes

**Como** gerente, **quero** distribuir conversas entre atendentes por carteira / round-robin / skill, **para** balancear carga.

**Critérios de aceite:**
- **AC-COM-007-1**: GIVEN conversa nova de cliente sem atendente fixo, WHEN regra "round-robin entre on-line", THEN atribui ao próximo.
- **AC-COM-007-2**: GIVEN cliente com gerente de carteira fixo, WHEN entra mensagem, THEN atribui ao gerente.
- **AC-COM-007-3**: GIVEN atendente off-line, WHEN tem conversa atribuída, THEN reassociado conforme regra.

---

### US-COM-008: Converter conversa em chamado

**Como** atendente, **quero** transformar uma conversa em chamado quando vira problema técnico, **para** mover para o fluxo correto.

**Critérios de aceite:**
- **AC-COM-008-1**: GIVEN thread aberta, WHEN clico "Converter em chamado", THEN abre formulário pré-preenchido com cliente, descrição (resumo da conversa), anexos.
- **AC-COM-008-2**: GIVEN chamado criado, WHEN salvo, THEN evento `Comunicacao.ConvertidoEmChamado` é publicado e a thread fica vinculada ao chamado.
- **AC-COM-008-3**: GIVEN conversa convertida, WHEN consulto histórico do chamado, THEN vejo link para thread original.

---

### US-COM-009: Converter conversa em lead

**Como** atendente, **quero** transformar uma conversa em lead/oportunidade quando demonstra interesse, **para** alimentar o CRM.

**Critérios de aceite:**
- **AC-COM-009-1**: GIVEN thread com cliente potencial, WHEN clico "Converter em lead", THEN abre formulário pré-preenchido.
- **AC-COM-009-2**: GIVEN lead criado, WHEN salvo, THEN evento `Comunicacao.ConvertidoEmLead` é publicado.

---

### US-COM-010: Status de leitura/entrega

**Como** atendente, **quero** ver se cliente recebeu/leu a mensagem (quando o canal suporta), **para** decidir se devo reenviar/escalar.

**Critérios de aceite:**
- **AC-COM-010-1**: GIVEN WhatsApp suporta entrega/leitura, WHEN status muda, THEN UI mostra (enviado, entregue, lido).
- **AC-COM-010-2**: GIVEN SMS/e-mail com suporte limitado, WHEN não há confirmação, THEN UI mostra "enviado — sem confirmação".

---

### US-COM-011: Relatório de atendimento

**Como** gerente, **quero** dashboard de volume, TMA (tempo médio de atendimento), taxa de conversão chamado/lead, **para** dimensionar equipe.

**Critérios de aceite:**
- **AC-COM-011-1**: GIVEN período, WHEN abro dashboard, THEN vejo gráficos por canal, atendente, hora do dia.

---

## 7. Métricas de sucesso deste módulo

Ver `metricas.md`. Resumo:
- TMA por canal ≤ 5 min em horário comercial.
- Taxa de opt-in registrada por contato novo ≥ 95%.
- Zero envio para clientes em opt-out (alerta crítico se ≠ 0).

## 8. NFR

- **Performance:** atualização de status em < 2s p95.
- **Disponibilidade:** SLO 99.5% (degradação degrada atendimento).
- **Segurança:** consentimento e opt-out em trilha imutável; integração com porta ACL.
- **Acessibilidade:** WCAG AA (caixa unificada).
- **Multi-tenant:** `INV-TENANT-001`.
- **LGPD:** ver `docs/conformidade/comum/lgpd-rat.md`.

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID livre `US-COM-NNN`.
- US deprecada → `@deprecated` + ADR.
- Mudança em AC implementado → ADR + novo teste.
