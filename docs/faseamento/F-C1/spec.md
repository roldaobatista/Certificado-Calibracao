---
owner: roldao
revisado-em: 2026-05-23
proximo-review: 2026-08-23
status: draft
diataxis: reference
audiencia: agente
fase: Foundation F-C1
tipo: especificacao-forward
relacionados:
  - .specify/memory/constitution.md
  - docs/faseamento-foundation-waves.md
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0012-autorizacao-unificada.md
  - docs/adr/0054-webhook-out-provider.md
  - docs/adr/0062-devcontainer-canonico.md
  - REGRAS-INEGOCIAVEIS.md
---

# Foundation F-C1 — Hardening crítico (Especificação forward)

> **O que este documento é (Constituição §1, §2):** fonte da verdade do que a Foundation F-C1 deve fazer. Spec-as-source — código é derivado/validado contra esta spec.
>
> **Por que existe:** auditoria 10 lentes do plano-v1 (2026-05-23) detectou 27 gaps; auditoria do plano-v2 detectou que a Onda 1 com 9 GAPs violava "Conciso vence completo" (F-A=8, F-B=6, F-C estouraria). Convergência LLM+OBS+SEC: decompor em 3 sub-foundations sequenciais. Esta é a primeira.
>
> **Para Roldão (uma frase):** F-C1 fecha as travas críticas de configuração de produção (debug, headers de segurança, hardening do /admin, bloqueio de requisições servidoras pra IP interno) que faltavam antes de qualquer 1º deploy externo.

---

## 1. Escopo

F-C1 entrega **hardening crítico** em 4 frentes:

1. **Settings de produção** validados por hook (DEBUG=False, ALLOWED_HOSTS, cookies SECURE, HSTS, CSP, X-Frame, Referrer Policy, X-Content-Type-Options).
2. **Hardening do /admin/** (MFA obrigatório, rate-limit, IP allowlist, audit de cada acesso).
3. **ADR-0054 Webhook out provider — aceita E implementada** (não split — auditor DRIFT alertou que aceitar sem implementar gera drift): porta `OutboundWebhookProvider` com HMAC, SSRF guard (bloqueio de IPs privados RFC1918 + loopback + link-local + DNS rebinding lock), allowlist de portas, timeout obrigatório.
4. **Rotação de credenciais dogfooding** como exercício de procedimento (não há credencial vazada — confirmado pelo gitleaks manual da Onda 0; rotação é treino antes do procedimento produtivo de F-C3).

Bloqueia: F-C2 (não pode rodar tracing antes do hardening do `/admin` que será observado).
Bloqueia: F-C3 (não pode pinar SHA no Docker antes de fechar o set de settings prod).
Bloqueia: Wave A (1º deploy externo).

### 1.bis Non-goals (Onda 2 plano-v2 — princípio §4 constituição)

- **NÃO** entrega observabilidade (`structlog` real / prometheus / OpenTelemetry / endpoints `/health` `/ready`) — entra em F-C2.
- **NÃO** entrega instrumentação ou métricas de negócio — F-C3.
- **NÃO** entrega circuit breaker, DLQ ativa no `outbox_worker`, paginação default, throttle — F-C3.
- **NÃO** entrega pin SHA em Docker / Actions / Dependabot — F-C3.
- **NÃO** entrega `/health/deep` checando B2/KMS — F-C2.
- **NÃO** implementa endpoint do canal do titular (`/privacidade/titular/*`) — ADR-0061 (Onda 3).
- **NÃO** materializa devcontainer com network allowlist — ADR-0062 INV-DEVCONT-003 entra em F-C2.

---

## 2. User stories

### US-FC1-001 — Settings de produção bloqueados a configuração insegura

**Como** dono do produto (Roldão),
**quero** que `config/settings/prod.py` REJEITE valores inseguros (DEBUG=True, ALLOWED_HOSTS vazio, cookies sem SECURE, sem HSTS, sem CSP),
**para que** um deploy acidental com configuração de dev não exponha o sistema.

**AC binários:**

- **AC-FC1-001-1:** Hook `prod-settings-check.sh` bloqueia commit em `config/settings/prod.py` quando:
  - `DEBUG=True` (qualquer atribuição direta).
  - `ALLOWED_HOSTS=[]` ou `ALLOWED_HOSTS=["*"]`.
  - `SESSION_COOKIE_SECURE=False` (ou ausência da declaração).
  - `CSRF_COOKIE_SECURE=False` (ou ausência).
  - `SECURE_HSTS_SECONDS<31536000` (ou ausência).
  - `SECURE_SSL_REDIRECT=False` (ou ausência).
  - `X_FRAME_OPTIONS!="DENY"` (ou ausência).
  - `SECURE_CONTENT_TYPE_NOSNIFF=False` (ou ausência).
  - `SECURE_REFERRER_POLICY!="same-origin"` e `!="strict-origin-when-cross-origin"` (ou ausência).
  - Cabeçalho CSP não declarado via `django-csp` ou middleware próprio.
- **AC-FC1-001-2:** Hook detecta uso de `os.environ.get(...)` SEM default seguro em variáveis sensíveis (ex: `SECRET_KEY` sem fallback explícito que falha em prod).
- **AC-FC1-001-3:** Allowlist explícita via `# prod-settings: skip -- <razão ≥10 chars>` por linha (não por arquivo — força justificativa por valor).
- **AC-FC1-001-4:** Drill em `prod.py` sintético: cada uma das ~10 violações dispara o hook isoladamente.
- **AC-FC1-001-5:** Hook registrado em `.claude/settings.json` + adicionado em `_test-runner.sh` com ≥10 casos verdes.

### US-FC1-002 — `/admin/` com MFA obrigatório + rate-limit + IP allowlist

**Como** dono do produto,
**quero** que `/admin/` exija MFA TOTP, tenha rate-limit anti-brute-force, aceite só IPs de uma allowlist configurável, e registre cada acesso em audit log imutável,
**para que** mesmo se a senha do superuser vazar, o atacante não consiga abrir o admin Django pelo IP qualquer.

**AC binários:**

- **AC-FC1-002-1:** INV-ADMIN-001 cravada em REGRAS-INEGOCIAVEIS.md: `/admin/*` exige (a) MFA TOTP verificado nas últimas 8h, (b) IP no `ADMIN_IP_ALLOWLIST` (env var), (c) rate-limit 5 tentativas/IP/15min em login.
- **AC-FC1-002-2:** Middleware Django `AdminHardeningMiddleware` implementa as 3 verificações; recusa com 403 sem revelar qual condição falhou (SEC-LOG-001 — sem oracle).
- **AC-FC1-002-3:** Cada `GET`/`POST` em `/admin/*` (sucesso ou não) grava entrada em tabela `audit_trail.admin_access` (append-only, RLS, trigger PG anti-mutation) com: `usuario_id`, `ip`, `user_agent_hash`, `path`, `status_code`, `timestamp`.
- **AC-FC1-002-4:** Hook `admin-hardening-check.sh` valida que `urls.py` raiz monta `/admin/` SOMENTE com `AdminHardeningMiddleware` aplicado.
- **AC-FC1-002-5:** Drill em ambiente dev: (a) login `/admin/` sem MFA → 403; (b) MFA OK mas IP fora do allowlist → 403; (c) 6 tentativas em 15min → bloqueio 1h; (d) acesso bem-sucedido → linha em `admin_access`.
- **AC-FC1-002-6:** Hook registrado + ≥6 casos no `_test-runner.sh`.

### US-FC1-003 — ADR-0054 OutboundWebhookProvider aceita e implementada

**Como** sistema que vai chamar webhooks externos (gateway pagamento Asaas, INMETRO, e-mail provider),
**quero** uma porta única `OutboundWebhookProvider` com HMAC, SSRF guard, allowlist de portas e timeout,
**para que** o agente IA não emita request servidor pra IP privado (vazamento de rede interna) ou sem assinatura (atacante intercepta).

**AC binários:**

- **AC-FC1-003-1:** ADR-0054 promovida de "proposta" para "aceito" no AGENTS §11.
- **AC-FC1-003-2:** Porta `OutboundWebhookProvider` em `src/domain/shared/ports/webhook_out.py` (Protocol).
- **AC-FC1-003-3:** Adapter padrão `RequestsWebhookOut` em `src/infrastructure/webhook_out/`:
  - HMAC-SHA256 do payload com chave por destino (lookup por `destino_id`).
  - Header `X-Aferê-Signature: sha256=<hex>` + `X-Aferê-Timestamp` + `X-Aferê-Event-Id` (idempotência consumer externo).
  - SSRF guard: DNS resolve do destino → REJEITA se IP for RFC1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) / loopback (`127.0.0.0/8`, `::1`) / link-local (`169.254.0.0/16`, `fe80::/10`) / multicast (`224.0.0.0/4`).
  - DNS rebinding lock: resolve uma vez antes da chamada, conecta pelo IP resolvido (não pelo hostname).
  - Allowlist de portas: 443 (HTTPS) e 80 (HTTP — só com flag explícita por destino).
  - Timeout obrigatório (conn=5s, read=15s).
  - Retry com backoff exponencial + jitter (PERF-002).
- **AC-FC1-003-4:** Hook `outbound-webhook-ssrf-check.sh` detecta uso de `requests.get/post/put/delete` direto em `src/infrastructure/**` fora de `webhook_out/adapter.py` — bloqueia, força usar a porta.
- **AC-FC1-003-5:** Drill: tentar chamar provider com URL `http://169.254.169.254/latest/meta-data` (AWS metadata) → REJEITA antes do connect.
- **AC-FC1-003-6:** Drill: simular DNS que devolve IP válido na 1ª resolução e IP privado na 2ª (rebinding) → REJEITA na 2ª.
- **AC-FC1-003-7:** Hook registrado + ≥8 casos no `_test-runner.sh`.

### US-FC1-004 — Rotação de credenciais dogfooding exercitada

**Como** dono do produto antes do 1º deploy externo,
**quero** ter executado pelo menos 1 vez o procedimento de rotação de `DJANGO_SECRET_KEY` e `PII_HASH_KEY` dogfooding,
**para que** quando rodar o procedimento produtivo (KMS MRK em F-C3) eu já saiba os passos.

**AC binários:**

- **AC-FC1-004-1:** Procedimento documentado em `docs/operacao/rotacao-credenciais-dogfooding.md` com checklist passo-a-passo.
- **AC-FC1-004-2:** Drill executado: nova chave gerada, `.env` atualizado, `docker compose restart`, sessões antigas inválidas (cookie assinado com chave antiga rejeitado).
- **AC-FC1-004-3:** Log do drill arquivado em `docs/operacao/drills/rotacao-dogfooding-2026-MM-DD.md`.
- **AC-FC1-004-4:** Procedimento referenciado no §10 do `runbook.md` (substituindo `# 9. Rotação` que hoje é só roteiro).

### US-FC1-005 — Drill end-to-end de F-C1

**Como** dono do produto,
**quero** um comando `python manage.py validar_f_c1` que rode todos os drills de F-C1 em sequência,
**para que** o critério de saída da fase seja verificável em 1 comando.

**AC binários:**

- **AC-FC1-005-1:** Comando `validar_f_c1` em `src/infrastructure/admin_ops/management/commands/validar_f_c1.py`.
- **AC-FC1-005-2:** Drills executados em ordem:
  1. Hook `prod-settings-check.sh` rejeita ~10 violações sintéticas.
  2. Middleware `AdminHardeningMiddleware` bloqueia: sem MFA / IP fora allowlist / 6ª tentativa.
  3. Audit log de `admin_access` registra acesso bem-sucedido.
  4. `OutboundWebhookProvider` rejeita 5 URLs com IP privado/loopback/metadata.
  5. `OutboundWebhookProvider` assina HMAC corretamente (verificação cross-check).
  6. Rotação dogfooding: chave antiga não decifra sessão nova.
- **AC-FC1-005-3:** Output do comando: 6/6 PASS ou parada na 1ª falha com mensagem clara.

---

## 3. Invariantes de F-C1 (REGRAS-INEGOCIAVEIS.md)

| ID | Regra | Hook que valida |
|---|---|---|
| INV-ADMIN-001 | `/admin/*` exige MFA TOTP + IP allowlist + rate-limit 5/15min | `admin-hardening-check.sh` |
| INV-PROD-SET-001 | Settings de produção tem `DEBUG=False`, `ALLOWED_HOSTS` lista fechada, cookies SECURE, HSTS≥1ano, X-Frame=DENY, Content-Type-NoSniff, Referrer Policy, CSP | `prod-settings-check.sh` |
| INV-WEBHOOK-OUT-001 | Toda chamada HTTP de saída (Lacuna, KMS, Asaas, INMETRO) passa por `OutboundWebhookProvider`. Uso direto de `requests`/`httpx`/`urllib` em `src/infrastructure/**` é proibido fora do adapter. | `outbound-webhook-ssrf-check.sh` |
| INV-WEBHOOK-OUT-002 | `OutboundWebhookProvider` valida SSRF antes do connect: bloqueia IP RFC1918, loopback, link-local, multicast | hook ASsinatura na chamada |
| INV-WEBHOOK-OUT-003 | `OutboundWebhookProvider` assina HMAC-SHA256 com chave dedicada por destino + timestamp + event_id | revisão `auditor-seguranca` |
| INV-WEBHOOK-OUT-004 | DNS resolve uma vez por chamada; conexão pelo IP resolvido (não pelo hostname) — anti-rebinding | revisão `auditor-seguranca` |

---

## 4. Critérios de entrada

- [x] Onda 0 plano-v2 fechada (ADRs reservadas, LICENSE BUSL-1.1, F-C decomposta no faseamento)
- [x] Onda 2 sub-A fechada (ADR-0057 a11y, ADR-0058 analytics, ADR-0062 devcontainer aceitas)
- [x] Onda 2 sub-B fechada (IDEMP-001a, matriz LGPD direitos titular, god-modules deferral)
- [ ] Roldão aprova arrancar F-C1 (gate manual)
- [ ] 4 humano-substitutos revisam `plan.md` desta F-C1 (ritual Spec Kit P2)

---

## 5. Critérios de saída (mortalidade)

- [ ] Comando `validar_f_c1` retorna 6/6 PASS.
- [ ] 10 auditores Família 5 PASS ZERO CRÍTICO/ALTO/MÉDIO.
- [ ] Suite total (≥250 hooks; pytest ≥621) verde.
- [ ] Hooks novos: `prod-settings-check.sh`, `admin-hardening-check.sh`, `outbound-webhook-ssrf-check.sh` — cada um com ≥6 casos verdes no `_test-runner.sh`.
- [ ] AGENTS §11: ADR-0054 promovida proposta → aceito.
- [ ] REGRAS-INEGOCIAVEIS.md: INV-ADMIN-001, INV-PROD-SET-001, INV-WEBHOOK-OUT-001..004 cravadas.
- [ ] `docs/operacao/rotacao-credenciais-dogfooding.md` criado + drill registrado.
- [ ] Auditor de Segurança não bloqueou merge nos últimos 7 dias da fase.

### Se reprovar (princípio "código não vira descartável")

- Hook `prod-settings-check.sh` muito conservador (false positive frequente em prod válida) → ajustar allowlist, NÃO desligar.
- SSRF guard rejeita destino legítimo (ex: KMS endpoint regional) → adicionar exceção explícita por destino no allowlist do adapter; documentar em ADR de extensão.
- MFA bloqueia acesso emergencial → procedimento `break-glass` documentado em runbook (ainda nesta fase OU em F-C2 — decisão em P2).
- Em nenhum caso código é jogado fora.

---

## 6. Entregáveis (P4)

1. **Hooks** (3 novos): `prod-settings-check.sh`, `admin-hardening-check.sh`, `outbound-webhook-ssrf-check.sh`.
2. **Settings**: `config/settings/prod.py` revisto com todos os 10 valores corretos.
3. **Middleware**: `src/infrastructure/auth/admin_hardening_middleware.py`.
4. **Modelo**: `src/infrastructure/audit/models.py` + migration `0017_admin_access` (append-only, RLS, trigger).
5. **ADR-0054 implementação**: `src/domain/shared/ports/webhook_out.py` (Protocol) + `src/infrastructure/webhook_out/{adapter,ssrf_guard,hmac_sign}.py`.
6. **Comando**: `validar_f_c1`.
7. **Doc**: `docs/operacao/rotacao-credenciais-dogfooding.md` + drill arquivado.
8. **REGRAS**: INV-ADMIN-001, INV-PROD-SET-001, INV-WEBHOOK-OUT-001..004 cravadas.
9. **AGENTS §11**: ADR-0054 aceita.

---

## 7. Dependências externas

- F-A (multi-tenant + RLS) — fechada.
- F-B (auth + MFA TOTP) — fechada. MFA TOTP do `/admin/` reusa o `django-otp` já instalado.
- ADR-0054 (Webhook out) — proposta. Aceitação acontece DENTRO desta F-C1 (não antes).
- ADR-0062 (Devcontainer) — aceita Onda 2 sub-A. Sessões de F-C1 que tocam `auth/`, `kms/`, `admin_ops/` rodam dentro do devcontainer (INV-DEVCONT-001).

---

## 8. Histórico

- 2026-05-23: criada por Onda 2 plano-v2 sub-B; status `draft`. Próximo passo: revisão por `tech-lead-saas-regulado` + `advogado-saas-regulado` + `corretora-seguros-saas` (não-aplicável CGCRE).
