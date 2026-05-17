---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/arquitetura/cross-cutting/auth-rbac.md
  - docs/conformidade/comum/seguranca-dados.md
  - docs/conformidade/comum/lgpd-rat.md
  - docs/comum/isolamento-multi-tenant.md
---

# Contratos de API — Módulo ACS

> Endpoints (REST candidato — formato final em ADR-0001). Padronização: HTTP/JSON, erros RFC 7807, autenticação Bearer.

---

## Convenções

- Versionamento via path (`/v1/`).
- Autenticação: `Authorization: Bearer <token>` (sessão OPACA — não JWT — pra suportar revogação imediata; ver `auth-rbac.md`).
- Tenant: derivado do token (não do header) para impedir spoofing (`INV-TENANT-001..004`, `SEC-TENANT-001`).
- Filial-contexto: header `X-Filial-Contexto: <id>` quando usuário tem acesso a múltiplas filiais. Default = filial padrão do usuário.
- Idempotência: endpoints de mutação aceitam `Idempotency-Key`.
- Rate-limit: documentado por endpoint sensível (`SEC-002`).
- Erros RFC 7807:
  ```json
  { "type": "https://afere.app/erros/credencial-invalida",
    "title": "Credencial inválida", "status": 401,
    "detail": "Email ou senha incorretos.",
    "instance": "/v1/acs/login",
    "correlation_id": "uuid" }
  ```
- Toda mutação grava evento de auditoria (`INV-001`).

---

## Endpoints — Autenticação

### `POST /v1/acs/login`

**Propósito:** iniciar sessão (passo 1 — senha).
**Auth:** público.
**Body:**
```json
{ "email": "user@example.com", "senha": "..." }
```
**Resposta 200 (sem MFA):**
```json
{ "sessao_id": "uuid", "token": "...", "expira_em": "ISO8601" }
```
**Resposta 200 (com MFA pendente):**
```json
{ "mfa_challenge_id": "uuid", "expira_em": "ISO8601" }
```
**Códigos:** 200, 400, 401 (genérico — `SEC-001`), 429 (rate-limit — `SEC-002`).
**Invariantes:** `INV-001`, `INV-002`, `SEC-001`, `SEC-002`.
**US:** `US-ACS-001`.
**Rate-limit:** 5 tentativas / 15min / IP / email (combinado).
**Eventos:** `acs.login.sucesso` ou `acs.login.falha` ou `acs.login.bloqueado`.

---

### `POST /v1/acs/login/mfa`

**Propósito:** validar TOTP (passo 2).
**Auth:** `mfa_challenge_id` no body.
**Body:**
```json
{ "mfa_challenge_id": "uuid", "codigo": "123456" }
```
**Resposta 200:**
```json
{ "sessao_id": "uuid", "token": "...", "expira_em": "ISO8601" }
```
**Códigos:** 200, 400, 401 (após 3 falhas — invalida challenge), 410 (challenge expirado).
**Invariantes:** `INV-003`, `SEC-001`, `SEC-002`.
**US:** `US-ACS-002`.

---

### `POST /v1/acs/logout`

**Propósito:** encerrar sessão atual.
**Auth:** Bearer.
**Resposta 204.**
**Eventos:** `acs.sessao.encerrada` (motivo=`logout`).

---

### `POST /v1/acs/senha/recuperacao/solicitar`

**Propósito:** pedir link de redefinição.
**Auth:** público.
**Body:** `{ "email": "..." }`.
**Resposta 202 (sempre — `SEC-001`):**
```json
{ "mensagem": "Se o email existir, enviaremos instruções." }
```
**Rate-limit:** 3 / hora / IP.
**US:** `US-ACS-003`.

---

### `POST /v1/acs/senha/recuperacao/confirmar`

**Propósito:** redefinir senha com token.
**Auth:** token no body (não Bearer).
**Body:**
```json
{ "token": "...", "nova_senha": "..." }
```
**Resposta 200** ou 400 (senha fraca) ou 410 (token inválido/expirado/usado).
**Pós-condição:** todas as sessões do usuário encerradas; token marcado como usado.

---

## Endpoints — Sessões

### `GET /v1/acs/me/sessoes`

**Propósito:** listar minhas sessões ativas.
**Auth:** Bearer.
**Resposta 200:**
```json
{ "sessoes": [
  { "id": "uuid", "dispositivo": "Chrome/Windows", "ip": "x.x.x.x",
    "localizacao": "São Paulo, BR", "iniciada_em": "ISO", "ultima_em": "ISO", "atual": true }
] }
```

### `DELETE /v1/acs/me/sessoes/{id}`

**Propósito:** encerrar uma sessão minha.
**Auth:** Bearer (deve ser dona da sessão).
**Resposta 204.**

### `POST /v1/acs/me/sessoes/{id}/repudiar`

**Propósito:** marcar "esse não fui eu".
**Resposta 204** + alerta P1 + invalidação global de sessões.
**Eventos:** `acs.sessao.repudiada`.

### `GET /v1/acs/me/logins-recentes?desde=ISO`

**Propósito:** histórico de tentativas (sucesso e falha) próprias.
**Resposta:** lista paginada cursor-based.

---

## Endpoints — MFA

### `POST /v1/acs/me/mfa/setup/iniciar`

**Propósito:** gerar segredo TOTP novo.
**Resposta 200:** `{ "segredo": "...", "qr_code_uri": "otpauth://...", "backup_codes": [...] }`
**Importante:** segredo só é persistido após `/confirmar`.

### `POST /v1/acs/me/mfa/setup/confirmar`

**Body:** `{ "codigo": "123456" }`.
**Resposta 200** ou 400 (código inválido).

### `DELETE /v1/acs/me/mfa`

**Propósito:** desativar MFA (só permitido se perfil não exige).
**Resposta 204** ou 403 (perfil exige MFA — `INV-003`).

---

## Endpoints — Gestão de Usuários (admin tenant)

### `GET /v1/acs/usuarios?status=&perfil=&filial=&busca=`
Lista paginada. Permissão: `usuario.ler`.

### `POST /v1/acs/usuarios`
**Body:**
```json
{ "nome": "...", "email": "...", "cpf": "...", "perfis": ["..."],
  "filiais": ["..."], "filial_padrao": "...", "mfa_obrigatorio": true }
```
**Resposta 201.** Dispara email de boas-vindas com token de definição de senha.
**Permissão:** `usuario.criar`. **Eventos:** `acs.usuario.criado`.

### `GET /v1/acs/usuarios/{id}` | `PATCH /v1/acs/usuarios/{id}` | `POST /v1/acs/usuarios/{id}/desativar`

Desativação NÃO exclui (`INV-001`). Eventos correspondentes.

### `POST /v1/acs/usuarios/{id}/forcar-logout`
Encerra todas as sessões do usuário. Permissão: `usuario.gerir_sessao`.

---

## Endpoints — Perfis e Permissões

### `GET /v1/acs/perfis` | `POST /v1/acs/perfis` | `PATCH /v1/acs/perfis/{id}`

`PATCH` com mudança em `permissoes` invalida caches + dispara `acs.permissao.alterada`.

### `GET /v1/acs/permissoes/catalogo`
Catálogo de permissões disponíveis (somente leitura — definidas em código).

### `GET /v1/acs/me/permissoes`
Permissões efetivas do usuário autenticado (combinação dos perfis).
**Cache:** 5min OU invalidação por evento. Frontend usa para habilitar/desabilitar UI.

---

## Endpoints — Auditoria

### `GET /v1/acs/auditoria?desde=&ate=&usuario=&tipo=&entidade=&ip=&busca=&cursor=`

Paginação cursor-based. Permissão: `auditoria.ler`.
Filtro `tipo` aceita prefixo (`acs.login.*`).

### `GET /v1/acs/auditoria/{evento_id}`
Detalhe com `valores_antes`, `valores_depois`.

### Sem `DELETE`, sem `PATCH` — `INV-001` WORM.

---

## Endpoints — Histórico de Registros

### `GET /v1/acs/historico/{entidade_tipo}/{entidade_id}`
Lista de versões.

### `GET /v1/acs/historico/{entidade_tipo}/{entidade_id}/versoes/{n}`
Snapshot de uma versão.

### `POST /v1/acs/historico/{entidade_tipo}/{entidade_id}/restaurar`
**Body:** `{ "versao_num": N, "motivo": "..." }`.
Permissão dedicada `<entidade>.restaurar_versao`. Eventos.

---

## Endpoints — LGPD (Portal do Titular)

### `POST /v1/acs/lgpd/portal/autenticar/iniciar`
**Body:** `{ "tenant_slug": "...", "cpf": "...", "email": "..." }`.
**Resposta 202** (mensagem genérica). Envia token 6 dígitos por email/SMS.
**Rate-limit:** 3 / hora / IP.

### `POST /v1/acs/lgpd/portal/autenticar/confirmar`
**Body:** `{ "tenant_slug": "...", "cpf": "...", "codigo": "..." }`.
**Resposta 200:** `{ "token": "...", "expira_em": "60min" }`.

### `GET /v1/acs/lgpd/portal/me/dados-resumo`
Auth: token do portal. Resumo dos dados que o tenant tem do titular.

### `GET /v1/acs/lgpd/portal/me/consentimentos`
Lista consentimentos ativos e histórico.

### `POST /v1/acs/lgpd/portal/me/consentimentos/{id}/revogar`
**Body:** `{ "motivo": "..." }`. Eventos.

### `POST /v1/acs/lgpd/portal/me/solicitacoes`
**Body:** `{ "tipo": "exportacao|anonimizacao|exclusao", "motivo": "..." }`.
**Resposta 201:** `{ "protocolo": "...", "prazo_legal": "ISO8601" }`.
**Eventos:** `acs.lgpd.solicitacao_aberta`.

### `GET /v1/acs/lgpd/portal/me/solicitacoes`
Status das solicitações.

### `GET /v1/acs/lgpd/portal/me/solicitacoes/{id}/download`
Disponível só quando `status=concluida` e `tipo=exportacao`. Pré-signed URL Backblaze válida 24h.

---

## Endpoints — LGPD (interno admin tenant)

### `GET /v1/acs/lgpd/solicitacoes?status=&tipo=&vencendo_em=`
Fila operacional.

### `POST /v1/acs/lgpd/solicitacoes/{id}/processar`
Disparo manual (workflow normal é automático). Permissão: `lgpd.operar`.

### `POST /v1/acs/lgpd/solicitacoes/{id}/negar`
**Body:** `{ "motivo": "..." }`. Apenas com base legal (ex: retenção fiscal vigente). Auditável.

---

## Endpoints — Consentimentos (interno — chamados por outros módulos)

### `POST /v1/acs/consentimentos`
Outros módulos chamam ao coletar consentimento.
**Body:** `{ "titular_id": "...", "finalidade": "...", "base_legal": "...", "versao_termo": "...", "ip": "..." }`.

### `GET /v1/acs/consentimentos/verificar?titular_id=&finalidade=`
Resposta: `{ "permitido": true|false, "base_legal": "..." }`. Usado por módulos antes de processar dado pessoal.

---

## Endpoints — Health & Debug (internos plataforma)

### `GET /v1/acs/health`
Liveness simples.

### `GET /v1/acs/admin/tenants/{id}/status-seguranca`
Auth: admin global Aferê. Retorna métricas seguras (sem dados de negócio — `INV-TENANT-004`).

---

## Eventos consumidos de outros módulos

| Evento | Origem | Ação |
|---|---|---|
| `<modulo>.registro.alterado` | Qualquer | Cria `VersaoRegistro` se tipo for crítico |
| `cliente.criado` | comercial/clientes | Sugere coleta de consentimentos |
| `pagamento.confirmado` | financeiro | Reativa tenant suspenso |

Ver `docs/comum/integracoes-inter-modulos.md` para contrato detalhado.

---

## Rate limits (resumo)

| Endpoint | Limite |
|---|---|
| `POST /login` | 5 / 15min / IP+email |
| `POST /login/mfa` | 3 / challenge |
| `POST /senha/recuperacao/solicitar` | 3 / hora / IP |
| `POST /lgpd/portal/autenticar/*` | 3 / hora / IP |
| Mutations admin | 60 / min / usuário |
| Reads | 600 / min / usuário |

---

## Versionamento

- v1 e v2 coexistem 6 meses.
- Quebra de contrato exige ADR + bump CHANGELOG.
- Endpoint deprecado → header `Sunset` (RFC 8594).

## Como esta lista evolui

- Endpoint novo → linkar US + adicionar permissão no catálogo.
- Quebra → ADR + janela de migração.
- Deprecação → header Sunset + comunicação aos integradores.
