---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/dominios/comercial/modulos/portal-cliente/modelo-de-dominio.md
---

# Contratos de API — Módulo Portal do Cliente

> Endpoints expostos para o cliente externo + endpoints internos para gestão do portal pelo atendente.

---

## Convenções

- Versionamento via path (`/v1/`).
- **Subdomínio dedicado** sugerido (`portal.<tenant>.afere.app`) ou caminho prefixado (`/portal/`) — definir em ADR.
- Autenticação: header `Authorization: Bearer <token>` (token de sessão do portal) OU cookie HttpOnly + Secure (preferido para web).
- Tenant: implícito no token + obrigatório no contexto de RLS (`INV-TENANT-001..004`).
- Erros: RFC 7807.
- CORS: restrito a domínios do tenant.
- Rate limit: por IP + por usuário.

---

## Endpoints públicos (anônimos)

### `POST /v1/portal/auth/login`
**Propósito:** login com login + senha.
**Request:** `{ login, senha }`.
**Response:** `{ token, expira_em, usuario: { nome, papel } }`.
**Códigos:** 200, 400, 401, 423 (conta bloqueada), 429 (rate limit).
**Eventos:** dispara `Portal.LoginRealizado` (sucesso) ou `Portal.TentativaLoginFalhou`.
**Rate limit:** 5 tentativas/IP/min + bloqueio progressivo.
**US:** US-POR-001.

---

### `POST /v1/portal/auth/link-magico/solicitar`
**Propósito:** pedir envio de link mágico.
**Request:** `{ login }`.
**Response:** `{ mensagem: "se este e-mail está cadastrado, você vai receber um link" }` (sempre 200, sem vazar existência).
**Códigos:** 200, 429.
**Rate limit:** 3 req/IP/min.
**US:** US-POR-001 (AC-2).

---

### `POST /v1/portal/auth/link-magico/consumir`
**Propósito:** consumir link mágico → criar sessão.
**Request:** `{ token }`.
**Response:** `{ token_sessao, expira_em, usuario }`.
**Códigos:** 200, 401 (token inválido/expirado/usado), 423, 429.
**US:** US-POR-001.

---

### `POST /v1/portal/auth/recuperar-senha/solicitar`
**Propósito:** iniciar fluxo de recuperação.
**Request:** `{ login }`.
**Response:** mesma estratégia anti-enumeração.
**Códigos:** 200, 429.

---

### `POST /v1/portal/auth/recuperar-senha/confirmar`
**Propósito:** definir nova senha via token.
**Request:** `{ token, nova_senha }`.
**Códigos:** 200, 400 (senha fraca), 401 (token).

---

## Endpoints autenticados (cliente)

### `GET /v1/portal/me`
**Propósito:** dados do usuário logado + papéis.
**Response:** `{ id, nome, cliente: {id, razao_social ou nome}, papel_portal }`.
**Códigos:** 200, 401.

---

### `GET /v1/portal/dashboard`
**Propósito:** dados consolidados do dashboard do cliente.
**Response:** `{ os_abertas: N, orcamentos_pendentes: N, faturas_a_pagar: N, certificados_vencendo: N }`.
**Códigos:** 200, 401.
**Invariantes:** `INV-TENANT-001..004` (cliente_id derivado do token).
**US:** US-POR-002.

---

### `GET /v1/portal/os`
**Propósito:** lista de OS do cliente.
**Query:** `status`, `busca`, `paginacao`.
**Response:** lista paginada com filtro de visibilidade (somente OS com `visivel_cliente = true`).
**Códigos:** 200, 401.
**US:** US-POR-003.

---

### `GET /v1/portal/os/{id}`
**Propósito:** detalhe da OS + timeline + anexos visíveis.
**Códigos:** 200, 401, 403 (OS de outro cliente), 404.
**Invariantes:** cross-tenant/cross-cliente bloqueado pelo middleware + RLS.

---

### `GET /v1/portal/orcamentos` / `GET /v1/portal/orcamentos/{id}`
**Propósito:** lista e detalhe de orçamentos visíveis.
**Invariantes:** `INV-TENANT-001..004`; só status enviado/aguardando/aprovado/rejeitado/expirado (rascunho do tenant NÃO aparece).
**US:** US-POR-004.

---

### `POST /v1/portal/orcamentos/{id}/aprovar`
**Propósito:** cliente aprova orçamento.
**Request:** `{ aceite_termos: true }`.
**Response:** `{ aprovado_em, registro_id }`.
**Códigos:** 200, 400 (sem aceite), 401, 403, 409 (já aprovado/expirado).
**Eventos:** dispara `Comercial.OrcamentoAprovadoPeloCliente` (WORM) + cria OS via Operação.
**Invariantes:** `INV-001` (audit WORM), `INV-TENANT-*`.
**US:** US-POR-005.

---

### `POST /v1/portal/orcamentos/{id}/rejeitar`
**Propósito:** cliente rejeita.
**Request:** `{ motivo_codigo, motivo_livre? }`.
**Eventos:** `Comercial.OrcamentoRejeitadoPeloCliente`.
**US:** US-POR-005.

---

### `POST /v1/portal/orcamentos/{id}/pedir-revisao`
**Propósito:** cliente pede revisão.
**Request:** `{ observacao }`.
**Códigos:** 200.

---

### `GET /v1/portal/faturas` / `GET /v1/portal/faturas/{id}`
**Propósito:** lista e detalhe de faturas.
**Códigos:** 200, 401, 403.
**US:** US-POR-006.

---

### `GET /v1/portal/faturas/{id}/segunda-via`
**Propósito:** baixa PDF/QR Code da 2ª via.
**Response:** `{ tipo: "boleto" | "pix", url_pdf?, qrcode_base64?, expira_em }`.
**Códigos:** 200, 401, 403, 409 (fatura paga).
**Eventos:** `Portal.SegundaViaGerada`.
**US:** US-POR-006.

---

### `GET /v1/portal/certificados` / `GET /v1/portal/certificados/{id}`
**Propósito:** lista e detalhe de certificados visíveis.
**US:** US-POR-008.

---

### `GET /v1/portal/certificados/{id}/pdf`
**Propósito:** baixar PDF imutável + link validador externo.
**Response:** URL assinada temporária + metadados.
**Eventos:** `Portal.CertificadoBaixado` (auditoria ISO 17025).
**US:** US-POR-008.

---

### `GET /v1/portal/equipamentos`
**Propósito:** lista equipamentos do cliente + próximas calibrações.
**US:** US-POR-008.

---

### `GET /v1/portal/mensagens` / `POST /v1/portal/mensagens`
**Propósito:** listar threads, criar nova thread.
**Request POST:** `{ entidade_tipo, entidade_id, assunto, corpo_inicial, urgente? }`.
**Eventos:** `Portal.MensagemCriada`.
**US:** US-POR-009.

---

### `GET /v1/portal/mensagens/{threadId}` / `POST /v1/portal/mensagens/{threadId}/responder`
**Propósito:** ver thread, responder.
**Request POST:** `{ corpo, anexos: [arquivo_id, ...] }`.
**US:** US-POR-009.

---

### `POST /v1/portal/anexos`
**Propósito:** upload de arquivo (multipart).
**Limites:** ≤ 25MB; whitelist mime (PDF, JPG, PNG, XLSX, DOCX).
**Response:** `{ id, url_temporaria_preview }`.
**Códigos:** 201, 400, 413 (muito grande), 415 (mime não permitido).
**US:** US-POR-009.

---

### `GET /v1/portal/preferencias-notificacao` / `PUT /v1/portal/preferencias-notificacao`
**Propósito:** consultar/atualizar preferências.
**Request PUT:** `{ evento, canal, opt_in_lgpd }`.
**Invariantes:** WhatsApp exige opt_in_lgpd = true.
**US:** US-POR-010.

---

### `PUT /v1/portal/me/dados-cadastrais`
**Propósito:** atualizar dado não-sensível (telefone/e-mail/endereço entrega).
**Códigos:** 200, 400, 401.
**Eventos:** `Auditoria.DadoCadastralAlterado`.
**US:** US-POR-011.

---

### `POST /v1/portal/me/solicitacoes-cadastrais`
**Propósito:** abrir solicitação de alteração sensível (CNPJ/IE/razão social).
**Request:** `{ campo, valor_solicitado, motivo }`.
**Eventos:** `Portal.SolicitacaoCadastralCriada`.
**US:** US-POR-011.

---

## Endpoints internos (atendente — não públicos)

Vivem em `/v1/admin-portal/...` e seguem RBAC interno (atendente/admin do tenant), **não** RBAC cliente_portal.

### `POST /v1/admin-portal/usuarios`
Criar UsuarioPortal para um cliente (dispara e-mail boas-vindas).

### `POST /v1/admin-portal/usuarios/{id}/desbloquear`
Desbloquear conta após N tentativas.

### `GET /v1/admin-portal/solicitacoes-cadastrais` / `POST .../{id}/aprovar` / `POST .../{id}/rejeitar`
Fila de pendências cadastrais.

### `GET /v1/admin-portal/aprovacoes-orcamento`
Trilha WORM consultável (auditoria).

---

## Eventos consumidos

Ver `../../../comum/integracoes-inter-modulos.md`. Resumo:
- `Comercial.OrcamentoEnviado` → torna visível no portal.
- `Operacao.OSStatusMudou` → atualiza timeline.
- `Financeiro.FaturaEmitida` → exibe.
- `Metrologia.CertificadoEmitido` → exibe.
- `Metrologia.CalibracaoVencendo` → notifica.

## Rate limits

| Endpoint | Limite |
|---|---|
| `POST /v1/portal/auth/login` | 5/min/IP + bloqueio progressivo |
| `POST /v1/portal/auth/link-magico/solicitar` | 3/min/IP |
| `POST /v1/portal/anexos` | 10/min/usuário |
| `GET /v1/portal/*` (leitura) | 60/min/usuário |
| Default mutação | 30/min/usuário |

## Versionamento

- v1, v2 coexistem por 6 meses.
- Quebra de contrato exposto a clientes externos exige aviso prévio + janela maior (90 dias).

## Como esta lista evolui

- Endpoint novo → linkar US-POR-NNN.
- Quebra → ADR + janela + Sunset header.
- Deprecação → `@deprecated`.
