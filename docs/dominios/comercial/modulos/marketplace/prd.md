---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
modulo: marketplace
dominio: comercial
diataxis: explanation
relacionados:
  - docs/conformidade/comum/lgpd-rat.md#RAT-12
  - docs/conformidade/comum/dpia-modulos-novos.md#DPIA-04
  - docs/conformidade/comum/retencao-matriz.md
---

# PRD — Módulo Marketplace (Catálogo Comercial Online)

> **Fronteira com `portal-cliente` (cravada em 2026-05-17):** Marketplace = **vitrine pública + carrinho + landing de captação de leads**. Portal do Cliente = **área restrita autenticada** (tudo pós-login: OS, orçamentos, faturas, certificados, mensagens, 360° relacional). Após login bem-sucedido no marketplace, o usuário é redirecionado para `portal-cliente` — a autenticação é **única** (mesmo sistema de login, gerido pelo módulo `portal-cliente`). O marketplace mantém apenas a visão restrita do **estado dos pedidos originados dele**, sem duplicar as demais funções do portal.

## 1. O que este módulo é

Vitrine pública (ou privada por tenant) que expõe o catálogo de produtos e serviços do tenant na web, permite ao visitante/cliente montar um carrinho de solicitação e pedir orçamento. É **canal de captação e auto-serviço de entrada**, não área genérica do cliente. A "minha conta" completa (relacionamento, OS, faturas, certificados, chat) é responsabilidade do módulo `portal-cliente`.

## 2. Por que este módulo existe

Hoje a captação depende 100% de entrada manual (telefone, WhatsApp, e-mail) digitada por atendente. Marketplace abre canal de auto-serviço, qualifica lead com produto/serviço já escolhido pelo cliente e elimina retrabalho de digitação. Também responde à dor "cliente não sabe quais serviços a empresa oferece" — comum em assistência técnica e calibração.

## 3. Personas

Ver `personas.md` (P-MKT-01 Visitante anônimo, P-MKT-02 Cliente cadastrado autoatendimento, P-MKT-03 Gestor de catálogo do tenant) + transversais em `../../personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Catálogo online de produtos (vitrine + ficha).
- Catálogo online de serviços (com tempo médio, requisitos, faixa de preço).
- Solicitação de orçamento direto pelo site (formulário + carrinho).
- Carrinho de solicitação (não é checkout — é "monte sua proposta").
- Tabela de preço pública OU privada (com login do cliente).
- Produtos/serviços em destaque (curadoria pelo gestor do tenant).
- Serviços recorrentes (assinatura/contrato; integra com módulo `contratos`).
- **Visão restrita de "Meus pedidos do marketplace"** (apenas status processual das solicitações originadas aqui: enviada / em atendimento / convertida em orçamento / descartada). Demais visões (OS, faturas, certificados, contratos, mensagens) ficam no `portal-cliente` — link/redirecionamento exibido na visão restrita.
- Rastreamento de conversão (visita → carrinho → orçamento → fechamento).
- Integração com CRM (lead criado), Estoque (disponibilidade), Pagamento (quando habilitado), Orçamentos (carrinho vira orçamento), **Portal do Cliente (handoff pós-login + entrega de solicitação)**.

## 4.1 Escopo V2/V3 — Marketplace de extensões (esqueleto)

**NÃO Wave A.** ADR-0055 define curadoria + sandbox + revenue share para abertura do marketplace a parceiros externos (extensões/plugins instaláveis por N tenants). Resumo:

- **Curadoria (G-MKT-1):** parceiro submete via portal dev → Aferê valida (testes + security review + DPA) → publica.
- **Sandbox (G-MKT-2, `INV-MKT-SANDBOX-001`):** extensão Python executa em `RestrictedPython` + subprocess `firejail/nsjail` + cgroups (CPU 500ms, RAM 128MB, rede default-deny — só APIs Aferê via allowlist).
- **Revenue share (G-MKT-3):** ADR-0013 ganha tipo 8 `ComponenteExtensaoMarketplace(extension_id, percentual_afere=30, percentual_desenvolvedor=70)`. Cobrança via billing-saas; payout PIX D+30.

Toda execução de hook recebe `UntrustedInput[dict]` (porta #17 ACL `MarketplaceExtensionProvider`).

## 5. Non-goals (o que NÃO está neste módulo)

- **Marketplace de extensões em Wave A** — só V2/V3 (ADR-0055).
- **Não é área genérica do cliente** — relacionamento 360° (OS, orçamentos completos, faturas, certificados, contratos, mensagens, preferências de notificação, edição cadastral) é responsabilidade do módulo `portal-cliente`. Marketplace só mostra "estado do meu pedido vindo do marketplace" e redireciona pro portal para qualquer outra função.
- **Não tem sistema de autenticação próprio** — login/sessão/senha/link mágico/2FA são do `portal-cliente` (entidade `UsuarioPortal`). Marketplace consome a sessão estabelecida; após login, redireciona pro portal.
- **Checkout B2C com cobrança imediata** — V2; MVP é "solicitação de orçamento", não venda direta.
- **Marketplace multi-vendedor (estilo Mercado Livre)** — fora do escopo; cada tenant tem só a própria vitrine.
- **Editor visual de site/landing page** — fora; layout é tema configurável, não construtor livre.
- **SEO técnico avançado (sitemaps dinâmicos por região, AMP, schema.org rico)** — V2.
- **Integração com marketplaces externos (Mercado Livre, Amazon)** — fora.
- **Programa de afiliados/cashback** — fora.
- **Geração de NF-e na solicitação** — só após orçamento aprovado e OS concluída (módulo `financeiro`).
- **Catálogo: fonte de verdade dos produtos/serviços** — pertence a `suporte-plataforma/catalogo`; este módulo só EXIBE.

## 6. User Stories

### US-MKT-001: Visitante navega catálogo público
**Como** visitante anônimo, **quero** ver lista de produtos/serviços do tenant, **para** entender o que a empresa oferece sem ligar.

- **AC-MKT-001-1**: GIVEN tenant com catálogo público habilitado, WHEN acesso URL pública, THEN vejo grid de produtos/serviços ativos com preço (se tabela pública) ou "consulte" (se privada).
- **AC-MKT-001-2**: GIVEN item em destaque, WHEN renderizo a home, THEN destaque aparece em posição prioritária.
- **AC-MKT-001-3**: GIVEN visitante anônimo, WHEN clica em item, THEN ficha técnica abre sem login.

**Non-goals desta story:** comparação lado a lado de itens.

**Invariantes relacionadas:** INV-TENANT-001 (todo dado filtrado por tenant da URL/subdomínio), INV-026 (preço exibido respeita versão atual do catálogo; preço de orçamento já gerado não retroage).

**Dependências:** Bloqueado por: módulo `suporte-plataforma/catalogo`.

### US-MKT-002: Visitante monta carrinho e solicita orçamento
**Como** visitante anônimo, **quero** adicionar itens ao carrinho e enviar pedido de orçamento, **para** receber proposta sem precisar ligar.

- **AC-MKT-002-1**: GIVEN carrinho com ≥1 item, WHEN clico "solicitar orçamento", THEN sistema pede dados mínimos (nome, contato, CNPJ/CPF opcional) + termo LGPD.
- **AC-MKT-002-2**: GIVEN solicitação enviada, WHEN backend processa, THEN cria lead no módulo `crm` + rascunho de orçamento no módulo `orcamentos`.
- **AC-MKT-002-3**: GIVEN solicitação criada, WHEN concluída, THEN visitante recebe e-mail/WhatsApp de confirmação com link de acompanhamento.
- **AC-MKT-002-4 (LGPD):** Tratamento atende base **Consentimento explícito (art. 7º I)** para contato comercial + **Execução de contrato (art. 7º V)** para o orçamento solicitado (RAT-12); consentimento registrado em `POST /marketplace/lgpd/consentimento` com texto exato + canal + timestamp + IP.
- **AC-MKT-002-5 (Retenção):** Lead com opt-in conforme `retencao-matriz.md` linha "Histórico de consentimento Comunicação Omnichannel" (até opt-out + 6 meses); visita anônima conforme linha "Telemetria + analytics" (13 meses); após prazo: anonimização irreversível.

**Invariantes relacionadas:** INV-TENANT-001.

**Dependências:** Bloqueia: US-CRM-* (criação automática de lead); Bloqueado por: US-ORC-001.

### US-MKT-003: Cliente acompanha status das solicitações originadas no marketplace
**Como** cliente cadastrado, **quero** ver o status processual das solicitações que enviei pela vitrine do marketplace (enviada → em atendimento → convertida em orçamento → descartada), **para** acompanhar especificamente o que pedi por aqui sem precisar navegar até o portal completo.

> **Escopo restrito (fronteira com `portal-cliente`):** esta visão cobre **apenas pedidos originados no marketplace** (entidade `SolicitacaoOrcamento` deste módulo). Qualquer outra função do cliente — visão consolidada de OS, faturas, certificados, contratos, mensagens, edição cadastral, preferências de notificação, aprovação de orçamento — é responsabilidade do `portal-cliente` (ver US-POR-002 a US-POR-011). Esta US **não duplica** essas funções; oferece link/CTA "ver tudo no Portal" que redireciona com sessão preservada.

- **AC-MKT-003-1**: GIVEN cliente logado no marketplace, WHEN abre "Meus pedidos do marketplace", THEN vejo lista das minhas `SolicitacaoOrcamento` com status (enviada / em atendimento / convertida / descartada), data de envio e itens do carrinho original.
- **AC-MKT-003-2**: GIVEN solicitação já convertida em orçamento, WHEN clico no item, THEN o marketplace redireciona para a tela de detalhe/aprovação do orçamento no `portal-cliente` (US-POR-004/US-POR-005), preservando sessão — não duplica a tela de aprovação aqui.
- **AC-MKT-003-3**: GIVEN cliente logado no marketplace, WHEN procuro OS, faturas, certificados, contratos ativos ou mensagens, THEN a UI exibe CTA "Acessar área do cliente completa no Portal" + link direto pro `portal-cliente` — essas funções **não são renderizadas no marketplace**.
- **AC-MKT-003-4**: GIVEN cliente, WHEN acessa, THEN só vejo solicitações cujo `cliente_id` bate com o meu (escopo de visão restrito — INV-TENANT-001).

**Invariantes relacionadas:** INV-TENANT-001 (isolamento por tenant + cliente_id), SEC-AREA-CLIENTE (a definir — escopo de visão por cliente_id), **separação de responsabilidades com `portal-cliente`** (esta US **não** entrega "área genérica do cliente").

**Dependências:** Bloqueado por: `portal-cliente` (autenticação única + visão consolidada — sem o portal, o redirecionamento não tem destino).

### US-MKT-004: Tabela de preço pública vs privada por cliente
**Como** gestor de catálogo, **quero** configurar quais clientes/segmentos veem qual tabela, **para** preservar preço diferenciado de cliente VIP.

- **AC-MKT-004-1**: GIVEN cliente logado com tabela X atribuída, WHEN navega no marketplace, THEN vê preços da tabela X.
- **AC-MKT-004-2**: GIVEN visitante anônimo, WHEN navega, THEN vê tabela padrão pública (se habilitada) ou "consulte" se sem tabela pública.
- **AC-MKT-004-3**: AC-MKT-004-3: alteração de tabela NÃO retroage a orçamentos/contratos já emitidos.

**Invariantes relacionadas:** INV-026, INV-TENANT-001.

**Dependências:** Bloqueado por: módulo `precificacao` (tabela por segmento/contrato).

### US-MKT-005: Gestor curadoria itens em destaque
**Como** gestor de catálogo do tenant, **quero** marcar produtos/serviços como "destaque" e ordenar a vitrine, **para** empurrar o que tem margem maior ou estoque parado.

- **AC-MKT-005-1**: GIVEN gestor, WHEN abre tela de curadoria, THEN posso arrastar itens para reordenar.
- **AC-MKT-005-2**: GIVEN item marcado destaque, WHEN renderizo home, THEN aparece em posição prioritária.

### US-MKT-006: Serviços recorrentes assináveis
**Como** cliente, **quero** assinar serviço recorrente (ex: calibração anual de balança) pela vitrine, **para** garantir continuidade sem precisar pedir orçamento a cada ciclo.

- **AC-MKT-006-1**: GIVEN serviço marcado como recorrente, WHEN cliente assina, THEN cria contrato no módulo `contratos` + agenda OS recorrente.
- **AC-MKT-006-2**: Cliente pode cancelar/pausar pela área do cliente (com janela mínima configurável pelo tenant).

**Dependências:** Bloqueado por: módulo `contratos`.

### US-MKT-007: Rastreamento de conversão
**Como** gestor comercial, **quero** ver funil visita → carrinho → solicitação → orçamento → fechamento, **para** identificar onde perco cliente.

- **AC-MKT-007-1**: GIVEN visitante, WHEN navega, THEN evento de visualização registrado (sem PII, respeita LGPD).
- **AC-MKT-007-2**: GIVEN funil, WHEN abro dashboard, THEN vejo taxa de conversão por etapa e por canal de origem (UTM).

**Invariantes relacionadas:** RAT-09 (telemetria/analytics) e RAT-12 (lead) — ver `docs/conformidade/comum/lgpd-rat.md`. Evento de visualização sem PII; conversão com PII só após consentimento US-MKT-002.

### US-MKT-008: Integração com pagamento (quando habilitado)
**Como** cliente, **quero** pagar orçamento aprovado direto na área do cliente, **para** acelerar o início do serviço.

- **AC-MKT-008-1**: GIVEN orçamento aprovado, WHEN clico "pagar", THEN redireciono para gateway configurado pelo tenant (PIX, cartão, boleto).
- **AC-MKT-008-2**: Pagamento confirmado dispara evento `Marketplace.PagamentoConfirmado` → módulo `financeiro` registra recebimento.

**Dependências:** Bloqueado por: porta `payment` (a definir em ADR específica) + módulo `financeiro`.

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- Taxa visita → solicitação de orçamento > 2%.
- Taxa solicitação → orçamento fechado > 30%.
- Tempo médio da visita ao envio da solicitação < 4 min.

## 8. NFR

- **Performance:** TTFB página de catálogo < 800ms (p95); paginação de catálogo ≥ 100 itens com lazy load.
- **Disponibilidade:** 99.5% (impacto reputacional alto — vitrine pública).
- **Segurança:** isolamento estrito por tenant na URL/subdomínio; rate limit no formulário de solicitação (anti-spam); CAPTCHA opcional para visitantes anônimos.
- **Acessibilidade:** WCAG AA (vitrine pública).
- **SEO básico:** títulos, descrições, imagens com alt.

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID livre `US-MKT-NNN`.
- US deprecada → marcar `@deprecated` + ADR.
- Mudança em AC já implementado → ADR + novo teste.
