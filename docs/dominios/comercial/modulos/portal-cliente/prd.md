---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/novas funcionalidades.txt
  - docs/dominios/comercial/README.md
---

# PRD — Módulo Portal do Cliente

> Fonte de funcionalidades: `docs/novas funcionalidades.txt` linhas 67-90 (Módulo 3).
> **Status no roadmap: Wave B.** Vai depois do MVP-1 dogfooding, quando há cliente externo querendo autoatendimento.

---

## 1. O que este módulo é

Área externa do Aferê para **o cliente final do tenant** (ex: cliente da Balanças Solution) acessar **seus próprios dados** sem precisar ligar/mandar e-mail. Login separado dos usuários internos, dashboard restrito, consulta de OS, orçamentos, faturas, certificados; aprovação/rejeição de proposta; canal de comunicação.

Não é portal público de catálogo nem CRM — é "minha conta" do cliente externo.

## 2. Por que este módulo existe (problema a resolver)

- Cliente final hoje liga/manda WhatsApp pra recepção pedindo status de OS, 2ª via de fatura, baixar certificado etc. → recepção fica saturada.
- Aprovação de orçamento via WhatsApp/e-mail perde rastreabilidade e demora.
- Cliente exigente (corporativo) pede portal próprio como diferencial — se não tiver, perde licitação.

Dor mapeada em `docs/discovery/dores-mapeadas.md` (referenciar ID quando criada): "recepção sobrecarregada com status" + "aprovação por e-mail/WhatsApp sem rastro".

## 3. Personas

Ver `personas.md` deste módulo + `../../personas.md` (domínio) + `docs/comum/personas.md`. Principais:
- **Cliente PF (pessoa física)** — pouca tech-fluência, mobile-first.
- **Cliente PJ — contato comercial** — aprova orçamento, vê fatura.
- **Cliente PJ — contato técnico** — vê OS, certificado, calibração.
- **Atendente do tenant** (P3 transversal) — interage no canal de mensagens.

## 4. Escopo (o que ESTÁ neste módulo)

Lista derivada **direto** das funcionalidades da seção 3 do `novas funcionalidades.txt`:

- Login separado para clientes.
- Dashboard do cliente.
- Consulta de ordens de serviço (do próprio cliente).
- Consulta de orçamentos (do próprio cliente).
- Aprovação ou rejeição de propostas.
- Consulta de faturas.
- Acompanhamento de serviços (status em tempo real da OS).
- Download de documentos, certificados e relatórios.
- Comunicação com a empresa (canal de mensagens / chamados).

Conexões com outros módulos (também da lista):
- Cadastro de clientes.
- Orçamentos.
- Ordens de serviço.
- Financeiro.
- Certificados.
- Notificações por e-mail ou WhatsApp.

## 5. Non-goals (o que NÃO está neste módulo)

- **Não é loja online** — sem checkout/pagamento integrado a TEF/cartão direto pelo portal nesta primeira versão (Wave B). Pagamento via 2ª via boleto/Pix é via Financeiro.
- **Não é CRM para o cliente** — cliente não vê outros clientes, oportunidades, leads.
- **Não emite NF-e nem altera dado fiscal** — leitura apenas dos documentos já emitidos.
- **Não substitui SAC humano** — canal de mensagens é assíncrono; chamados urgentes seguem fluxo do módulo Chamados.
- **Não permite editar dado cadastral sensível** sem aprovação interna (telefone/e-mail OK; CNPJ/IE não).
- **Não tem assinatura A3** para aprovação de orçamento (assinatura eletrônica simples + log + IP basta no escopo deste módulo).
- **MVP-1 não entrega** — Wave B.

## 6. User Stories

### US-POR-001: Login separado do cliente
**Como** cliente externo, **quero** fazer login com meu CPF/CNPJ + senha (ou link mágico), **para** acessar minha área sem precisar criar conta nova a cada interação.

**Critérios de aceite:**
- **AC-POR-001-1:** GIVEN cliente cadastrado pelo atendente do tenant, WHEN recebe e-mail de boas-vindas com link de definir senha, THEN consegue definir e logar.
- **AC-POR-001-2:** GIVEN cliente sem senha definida, WHEN tenta login, THEN opção "receber link mágico no e-mail/WhatsApp" disponível.
- **AC-POR-001-3:** GIVEN 5 tentativas de login erradas seguidas, WHEN tenta novamente, THEN bloqueia conta por 15 min + notifica atendente.

**Invariantes:** `INV-TENANT-001..004` (cliente só vê dados do tenant a que pertence), `SEC-*` (senha hash + rate limit), LGPD (consentimento na primeira entrada).

---

### US-POR-002: Dashboard do cliente
**Como** cliente externo, **quero** ver em 1 tela: OS em andamento, orçamentos aguardando minha aprovação, faturas em aberto, certificados a vencer, **para** entender o que demanda minha atenção.

**Critérios de aceite:**
- **AC-POR-002-1:** GIVEN cliente logado, WHEN abre home, THEN vê 4 cards: OS abertas, orçamentos pendentes, faturas a pagar, certificados/calibrações próximos do vencimento.
- **AC-POR-002-2:** GIVEN card clicado, WHEN drill-down, THEN abre lista detalhada filtrada apenas para o cliente.

**Invariantes:** `INV-TENANT-001..004`.

---

### US-POR-003: Consulta de ordens de serviço
**Como** cliente, **quero** ver minhas OS (em andamento, concluídas, canceladas) com filtro e busca, **para** acompanhar serviços contratados.

**Critérios de aceite:**
- **AC-POR-003-1:** GIVEN cliente logado, WHEN abre "Minhas OS", THEN lista paginada com colunas: nº, descrição curta, status, data abertura, técnico responsável (nome simples).
- **AC-POR-003-2:** GIVEN OS clicada, WHEN abre detalhe, THEN vê histórico de status + anexos disponíveis para o cliente (filtrados — anexos internos NÃO aparecem).
- **AC-POR-003-3:** GIVEN OS com flag "visível ao cliente = false", WHEN cliente lista, THEN OS NÃO aparece.

**Invariantes:** `INV-TENANT-001..004`; filtro de visibilidade obrigatório.

---

### US-POR-004: Consulta de orçamentos
**Como** cliente, **quero** ver meus orçamentos com status (rascunho do tenant? enviado? aguardando minha aprovação? aprovado? rejeitado? expirado?), **para** decidir.

**Critérios de aceite:**
- **AC-POR-004-1:** GIVEN cliente logado, WHEN abre "Meus Orçamentos", THEN vê lista com nº, descrição, valor total, validade, status.
- **AC-POR-004-2:** GIVEN orçamento ainda em rascunho do tenant, WHEN cliente lista, THEN NÃO aparece (só aparece após status "enviado").
- **AC-POR-004-3:** GIVEN orçamento clicado, WHEN abre detalhe, THEN vê itens, valores, condições, anexos.

---

### US-POR-005: Aprovação ou rejeição de orçamento
**Como** cliente PJ (contato comercial) ou PF, **quero** aprovar ou rejeitar orçamento direto no portal com registro de IP + data + identidade, **para** dar agilidade e ter prova.

**Critérios de aceite:**
- **AC-POR-005-1:** GIVEN orçamento em status "aguardando aprovação", WHEN cliente clica "Aprovar", THEN sistema pede confirmação (texto + checkbox "li e concordo") + registra evento `Comercial.OrcamentoAprovadoPeloCliente` com `{ cliente_id, ip, user_agent, ts, geolocalizacao_aproximada? }`.
- **AC-POR-005-2:** GIVEN orçamento aprovado pelo cliente, WHEN evento dispara, THEN módulo Operação cria OS automaticamente (regra existente do módulo Orçamentos).
- **AC-POR-005-3:** GIVEN cliente rejeita, WHEN clica "Rejeitar", THEN pede motivo (lista predefinida + campo livre opcional) + grava evento.
- **AC-POR-005-4:** GIVEN orçamento expirado, WHEN cliente abre, THEN botões Aprovar/Rejeitar desabilitados + opção "solicitar revisão".

**Invariantes:** evento com IP + ts vai pra trilha WORM auditoria (`INV-001`), LGPD (consentimento explícito antes do registro de IP/geo).

**Non-goals desta story:** sem assinatura A3 (escopo separado).

---

### US-POR-006: Consulta de faturas
**Como** cliente, **quero** ver minhas faturas (em aberto, pagas, vencidas), com 2ª via de boleto/Pix, **para** quitar pendência.

**Critérios de aceite:**
- **AC-POR-006-1:** GIVEN cliente logado, WHEN abre "Faturas", THEN lista com nº, valor, vencimento, status (em aberto/paga/vencida).
- **AC-POR-006-2:** GIVEN fatura em aberto com boleto/Pix válidos, WHEN cliente clica "2ª via", THEN baixa PDF do boleto ou exibe QR Code Pix.
- **AC-POR-006-3:** GIVEN boleto vencido, WHEN cliente clica "2ª via", THEN gera novo (com juros/multa conforme regra do Financeiro).

**Invariantes:** `INV-TENANT-001..004`; emissão de 2ª via não cria duplicidade contábil.

---

### US-POR-007: Acompanhamento de serviços (status ao vivo)
**Como** cliente, **quero** ver status atualizado da OS (recebida → diagnóstico → orçamento → em execução → concluída → entregue) com timestamps, **para** saber sem ligar.

**Critérios de aceite:**
- **AC-POR-007-1:** GIVEN OS em andamento, WHEN cliente abre detalhe, THEN vê timeline de status com data/hora de cada transição.
- **AC-POR-007-2:** GIVEN mudança de status na OS, WHEN transição ocorre, THEN notifica cliente conforme preferência (e-mail / WhatsApp).
- **AC-POR-007-3:** GIVEN OS com checklist público habilitado, WHEN cliente abre, THEN vê itens do checklist marcados/pendentes.

---

### US-POR-008: Download de documentos, certificados e relatórios
**Como** cliente, **quero** baixar certificados de calibração, relatórios técnicos, contratos, faturas em PDF, **para** arquivar e cumprir minhas próprias obrigações regulatórias.

**Critérios de aceite:**
- **AC-POR-008-1:** GIVEN documento marcado "visível ao cliente", WHEN cliente clica download, THEN baixa o PDF correto associado à entidade (OS/orçamento/fatura/certificado).
- **AC-POR-008-2:** GIVEN certificado de calibração emitido, WHEN cliente acessa, THEN vê PDF imutável (ISO 17025 cláusula 7.8) com link para validador externo (QR Code do INMETRO/RBC).
- **AC-POR-008-3:** GIVEN documento expirado/anulado, WHEN cliente acessa, THEN exibe estado claramente (selo "ANULADO") sem remover o histórico.

**Invariantes:** imutabilidade pós-emissão (`INV-NNN` certificado RBC), trilha de download em auditoria.

---

### US-POR-009: Comunicação com a empresa (canal de mensagens)
**Como** cliente, **quero** abrir uma conversa assíncrona com a empresa (mensagem, anexo) vinculada a uma OS/orçamento/fatura, **para** registrar formalmente em vez de WhatsApp pessoal.

**Critérios de aceite:**
- **AC-POR-009-1:** GIVEN cliente em uma OS, WHEN clica "Enviar mensagem", THEN abre thread vinculada à OS visível para o atendente do tenant.
- **AC-POR-009-2:** GIVEN nova mensagem do cliente, WHEN chega no sistema, THEN dispara notificação ao atendente atribuído + entra na fila do módulo Chamados (ou módulo equivalente).
- **AC-POR-009-3:** GIVEN cliente anexa arquivo, WHEN sobe, THEN valida tipo (whitelist) + tamanho (≤ 25MB) + scan antivirus básico (placeholder antes de provider).
- **AC-POR-009-4:** GIVEN mensagem urgente, WHEN cliente marca "urgente", THEN entra na trilha de chamados com SLA reduzido.

**Invariantes:** `INV-TENANT-001..004`, retenção de anexos conforme matriz LGPD.

---

### US-POR-010: Notificações por e-mail / WhatsApp
**Como** cliente, **quero** receber notificações em e-mail e/ou WhatsApp quando algo relevante acontece (orçamento enviado, OS muda de status, fatura vence em X dias, certificado vai vencer), **com** opção de configurar canais e frequência, **para** não perder o que importa sem ser inundado.

**Critérios de aceite:**
- **AC-POR-010-1:** GIVEN cliente logado, WHEN abre "Preferências de notificação", THEN escolhe por evento: e-mail / WhatsApp / nenhum.
- **AC-POR-010-2:** GIVEN evento configurado para WhatsApp, WHEN evento ocorre, THEN dispara via módulo Notificações (não duplicar lógica).
- **AC-POR-010-3:** GIVEN cliente sem consentimento explícito de WhatsApp, WHEN tenta ativar, THEN sistema pede opt-in formal (LGPD).

---

### US-POR-011: Edição de dado cadastral seguro
**Como** cliente, **quero** atualizar meu telefone/e-mail/endereço de entrega sem pedir ao atendente, **mas** dados sensíveis (CNPJ, IE, razão social) só mudam mediante validação interna.

**Critérios de aceite:**
- **AC-POR-011-1:** GIVEN cliente logado, WHEN edita telefone/e-mail/endereço, THEN salva direto + registra evento.
- **AC-POR-011-2:** GIVEN cliente tenta editar CNPJ/IE/razão social, WHEN clica salvar, THEN sistema abre solicitação para atendente aprovar (estado "pendente de validação").

**Invariantes:** LGPD (consentimento + auditoria).

---

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- **% de clientes ativos do tenant que acessam o portal/mês** = ≥ 40%.
- **Redução de chamadas/WhatsApp à recepção pedindo "status"** = ≥ 30% (medido por pesquisa qualitativa pós-3 meses de uso).
- **% de orçamentos aprovados/rejeitados via portal vs e-mail** = ≥ 60%.

## 8. NFR (Requisitos Não-Funcionais)

- **Performance:** dashboard p95 ≤ 2s; mobile p95 ≤ 3s em 3G.
- **Disponibilidade:** SLO 99,5% (não é crítico operacional do tenant, mas afeta percepção do cliente final).
- **Segurança:** SEC-* (senha + rate limit + 2FA opcional Wave B+), LGPD (consentimento + opt-in/opt-out claro), `INV-TENANT-*` rigoroso.
- **Acessibilidade:** WCAG AA (público externo aumenta exigência).
- **Mobile-first:** PWA obrigatório; app nativo opcional Wave C.
- **i18n:** PT-BR no MVP; preparar estrutura para EN em V2.

## 9. Glossário

Ver `glossario.md` deste módulo.

## 10. Como este PRD evolui

- US nova → próximo ID `US-POR-NNN`.
- US deprecada → `@deprecated` + ADR.
- Mudança em AC → ADR + novo teste.
