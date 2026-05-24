---
owner: roldao
revisado-em: 2026-05-23
proximo-review: 2026-08-23
status: proposta
diataxis: reference
audiencia: agente
fase: Foundation F-C1
tipo: especificacao-forward
substitui: spec.md status=draft (P1)
relacionados:
  - .specify/memory/constitution.md
  - docs/faseamento-foundation-waves.md
  - docs/faseamento/F-C1/plan.md
  - docs/faseamento/F-C1/matriz-reconciliacao.md
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
  - `SECURE_HSTS_INCLUDE_SUBDOMAINS=False` (ou ausência) — **R-1 / TL-01 / SEG-FC1-06**.
  - `SECURE_HSTS_PRELOAD=False` (ou ausência) — **R-1 / TL-01 / SEG-FC1-06**.
  - `SECURE_SSL_REDIRECT=False` (ou ausência).
  - `SECURE_PROXY_SSL_HEADER` ausente (Hostinger fica atrás de proxy/Cloudflare — sem isto, `is_secure()` retorna False e HSTS/SSL_REDIRECT entra em loop infinito) — **R-1 / TL-01**.
  - `CSRF_TRUSTED_ORIGINS` ausente ou contém `"*"` — **R-1 / TL-01**.
  - `DATA_UPLOAD_MAX_MEMORY_SIZE` ausente ou `> 10485760` (10 MB) — anti-DoS form bomb — **R-1 / TL-01**.
  - `DATA_UPLOAD_MAX_NUMBER_FIELDS` ausente ou `> 1000` — anti-DoS form bomb — **R-1 / TL-01**.
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
- **AC-FC1-002-3:** Cada `GET`/`POST` em `/admin/*` (sucesso ou não) grava entrada em tabela `audit_trail.admin_access` (append-only, RLS, trigger PG anti-mutation) com:
  - `usuario_id` (FK; vira `usuario_id_hash` HMAC após 90d — ver AC-FC1-002-7)
  - `ip_hash` (HMAC do IP com salt versionado — **R-10 / LGP-FC1-03**; NÃO armazena IP em claro)
  - `user_agent_hash` (HMAC do UA com salt versionado)
  - `path`
  - `status_code`
  - `timestamp`
  - **Finalidade declarada:** "detecção de acesso indevido a console administrativo do tenant" — **R-4 / LGP-FC1-01**
  - **Base legal LGPD:** art. 7º IX (legítimo interesse de segurança) + art. 37 (registro de operações de tratamento) — **R-4 / LGP-FC1-01**
  - **Retenção:** **24 meses rolling** (atende ISO 27001 ≥6mo + ANPD + apólice E&O ≥18mo) — **R-4 / CONV-FC1-B**
  - **Crypto-shred:** após 24 meses, job mensal soft-deleta (`tombstoned_em`) e elimina `user_agent_hash` + cifra-chave por tenant é destruída na anonimização do tenant — **R-4 / LGP-FC1-01**
  - **Cópia espelho B2 WORM:** preparação F-C2 (não bloqueia F-C1 — GATE-CYBER-AUDITRET) — **R-4 / SEG-FC1-04**
- **AC-FC1-002-4:** Hook `admin-hardening-check.sh` valida que `urls.py` raiz monta `/admin/` SOMENTE com `AdminHardeningMiddleware` aplicado.
- **AC-FC1-002-5:** Drill em ambiente dev: (a) login `/admin/` sem MFA → 403; (b) MFA OK mas IP fora do allowlist → 403; (c) 6 tentativas em 15min → bloqueio 1h; (d) acesso bem-sucedido → linha em `admin_access` com `ip_hash` (não IP em claro); (e) job de pseudonimização após 90d substituiu `usuario_id` por `usuario_id_hash`.
- **AC-FC1-002-6:** Hook registrado + ≥6 casos no `_test-runner.sh`.
- **AC-FC1-002-7** (novo — **R-4 / LGP-FC1-04**): Job `pseudonimizar_admin_access_antigo` (procrastinate, diário) substitui `usuario_id` por `usuario_id_hash` HMAC nas linhas com `timestamp > 90 dias`. Resolve conflito LGPD art. 18 (eliminação) × auditoria imutável: pessoa demitida pode requerer pseudonimização (não eliminação completa — base legal art. 16 II + art. 7º IX) preservando a trilha de auditoria sem expor identidade. Documentado em `docs/conformidade/comum/direitos-titular-cross-modulo.md` (entrada nova pra `admin_access`).
- **AC-FC1-002-8** (novo — **R-9 / TL-06**): Middleware grava `session['admin_ip_hash']` + `session['admin_ua_hash']` no login admin e valida em cada request. Mismatch → 403 + invalida sessão (anti session-hijacking pós-MFA).

### US-FC1-003 — ADR-0054 OutboundWebhookProvider aceita e implementada

**Como** sistema que vai chamar webhooks externos (gateway pagamento Asaas, INMETRO, e-mail provider),
**quero** uma porta única `OutboundWebhookProvider` com HMAC, SSRF guard, allowlist de portas e timeout,
**para que** o agente IA não emita request servidor pra IP privado (vazamento de rede interna) ou sem assinatura (atacante intercepta).

**AC binários:**

- **AC-FC1-003-1:** ADR-0054 promovida de "proposta" para "aceito" no AGENTS §11.
- **AC-FC1-003-2:** Porta `OutboundWebhookProvider` em `src/domain/shared/ports/webhook_out.py` (Protocol).
- **AC-FC1-003-3:** Adapter padrão `RequestsWebhookOut` em `src/infrastructure/webhook_out/`:
  - HMAC-SHA256 sobre **canonical string** explícita = `f"{timestamp}.{method}.{path}.{sha256_hex(body)}"` — **R-2 / TL-02** (anti signature stripping/replay parcial).
  - Janela de aceitação do timestamp no consumer externo: **≤5min** (anti-replay) — **R-2 / TL-02**.
  - Chave HMAC por destino (lookup por `destino_id`) com `expires_at` declarado; rotação ≤90d documentada — **R-13 / SEG-FC1-03**.
  - `event_id` UUID v4 propagado no header `X-Aferê-Event-Id` + persistido em `consumer_idempotencia` (ADR-0033) — anti-replay no lado da Aferê quando webhook entrante volta — **R-2 / TL-02**.
  - Headers: `X-Aferê-Signature: sha256=<hex>` + `X-Aferê-Timestamp: <unix-int>` + `X-Aferê-Event-Id: <uuid>` + `X-Aferê-Algo: HMAC-SHA256-canonical-v1`.
  - SSRF guard: DNS resolve do destino → REJEITA se IP for:
    - RFC1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
    - loopback (`127.0.0.0/8`, `::1`)
    - link-local (`169.254.0.0/16`, `fe80::/10`)
    - multicast (`224.0.0.0/4`)
    - **IPv6 ULA `fc00::/7`** — **R-3 / CONV-FC1-A**
    - **CGNAT `100.64.0.0/10`** — **R-3 / CONV-FC1-A**
    - **`0.0.0.0/8`** (current network) — **R-3 / CONV-FC1-A**
    - Sufixos DNS de descoberta interna: `*.svc.cluster.local`, `*.consul`, `*.cluster.local`, `*.local` (mDNS) — **R-3 / TL-03**
  - DNS rebinding lock — **R-8 / TL-04**:
    - Resolve uma vez via `socket.getaddrinfo` ANTES da chamada.
    - Se múltiplos A/AAAA voltarem, validar **TODOS** contra a lista acima; rejeita se QUALQUER um cair em faixa proibida.
    - Connect pelo IP resolvido (não pelo hostname) via `HTTPAdapter` customizado.
    - Tratamento TTL=0: trata igual TTL>0 (sem revalidação durante o connect; lock no IP fixado).
  - Allowlist de portas: 443 (HTTPS default) e 80 (HTTP — só com flag `permite_http=True` explícita por destino).
  - Timeout obrigatório (conn=5s, read=15s).
  - Retry com backoff exponencial + jitter (PERF-002).
- **AC-FC1-003-4:** Hook `outbound-webhook-ssrf-check.sh` detecta uso de `requests.get/post/put/delete`/`httpx.*`/`urllib.request.urlopen`/`urllib3` direto em `src/infrastructure/**` fora de `webhook_out/adapter.py` — bloqueia, força usar a porta.
- **AC-FC1-003-5:** Drill: tentar chamar provider com URL `http://169.254.169.254/latest/meta-data` (AWS metadata) → REJEITA antes do connect.
- **AC-FC1-003-6:** Drill: simular DNS que devolve IP válido na 1ª resolução e IP privado na 2ª (rebinding) → REJEITA na 2ª. Cobrir cenário com `getaddrinfo` retornando lista A/AAAA mista.
- **AC-FC1-003-7:** Hook registrado + ≥8 casos no `_test-runner.sh`.
- **AC-FC1-003-8** (novo — **R-5 / LGP-FC1-02**): tabela `webhook_destino` com colunas:
  - `destino_id` (UUID PK)
  - `tenant_id` (FK, RLS)
  - `nome` (ex: "Asaas", "INMETRO", "SendGrid")
  - `url_base` (ex: `https://api.asaas.com`)
  - `papel_lgpd` enum `{controlador, operador, terceiro_destinatario}`
  - `dpa_url` (link pro DPA assinado em S3/Drive)
  - `dpa_assinado_em` (date NOT NULL)
  - `dpa_vence_em` (date NOT NULL — null → infinito proibido)
  - `finalidade` (texto livre — ex: "cobrança recorrente cliente final")
  - `categorias_dados` (array enum `{nome, cpf, email, telefone, endereco, valor, ...}`)
  - `chave_hmac_id` (FK opaca → KMS — chave HMAC dedicada por destino)
  - `chave_expires_at` (date — rotação ≤90d)
  - `criado_em`, `criado_por`, `desativado_em`
  - Append-only para auditoria de quando o DPA foi cadastrado; `desativado_em` para soft-delete (ADR-0031 padrão configurações mutáveis).
- **AC-FC1-003-9** (novo — **R-5 / LGP-FC1-02**): Hook `outbound-webhook-ssrf-check.sh` estendido — **bloqueia chamada quando `webhook_destino.dpa_assinado_em IS NULL` ou `dpa_vence_em < CURRENT_DATE` ou `chave_expires_at < CURRENT_DATE`**. Allowlist via `# webhook-dpa: skip -- <razão ≥10 chars>` em código (não em runtime).

### US-FC1-004 — Rotação de credenciais dogfooding exercitada

**Como** dono do produto antes do 1º deploy externo,
**quero** ter executado pelo menos 1 vez o procedimento de rotação de `DJANGO_SECRET_KEY` e `PII_HASH_KEY` dogfooding,
**para que** quando rodar o procedimento produtivo (KMS MRK em F-C3) eu já saiba os passos.

**AC binários:**

- **AC-FC1-004-1:** Procedimento documentado em `docs/operacao/rotacao-credenciais-dogfooding.md` com checklist passo-a-passo + **mapeamento 1:1 procedimento manual → comando AWS KMS equivalente** (preparação F-C3 produtivo) — **R-15 / TL-08**.
- **AC-FC1-004-2:** Drill executado: nova chave gerada, `.env` atualizado, `docker compose restart`, sessões antigas inválidas (cookie assinado com chave antiga rejeitado).
- **AC-FC1-004-3:** Log do drill arquivado em `docs/operacao/drills/rotacao-dogfooding-2026-MM-DD.md` com **declaração de "eliminação efetiva" datada** — **R-15 / LGP-FC1-05**.
- **AC-FC1-004-4:** Procedimento referenciado no §10 do `runbook.md` (substituindo `# 9. Rotação` que hoje é só roteiro).
- **AC-FC1-004-5** (novo — **R-15 / LGP-FC1-05**): Procedimento exige eliminação efetiva da chave antiga:
  - `shred -u` no `.env` antigo antes de sobrescrever.
  - Checklist explícito: "buscar chave antiga em `~/.bash_history`, `~/.zsh_history`, backup local, OneDrive, Google Drive, cópias de `.env*` em outros diretórios → eliminar todas".
  - Declaração datada no log do drill: "Em <data>, declaro que a chave anterior foi eliminada de todos os locais conhecidos. Não há cópia ativa." (assinatura digital do Roldão via A3 quando A3 entrar; até lá, texto-livre datado).

### US-FC1-006 — Break-glass do `/admin/` (acesso emergencial)

**(Novo — R-14 / CONV-FC1-C — convergência tech-lead TL-07 + corretora SEG-FC1-01)**

**Como** dono do produto,
**quero** uma conta `admin-recovery` com U2F físico (YubiKey ou similar) + alerta crítico em qualquer login + procedimento documentado em runbook,
**para que** se a conta principal de admin perder o TOTP (celular roubado, MFA quebrado) eu ainda consiga entrar em incidente real, sem ter que desligar INV-ADMIN-001 em produção.

**AC binários:**

- **AC-FC1-006-1:** Conta `admin-recovery` criada via `manage.py` (não via /admin/) com flag `is_break_glass=True` em `Usuario`.
- **AC-FC1-006-2:** Conta `admin-recovery` exige U2F (WebAuthn) — NÃO aceita TOTP (defesa contra mesmo vetor de comprometimento que tirou o TOTP da conta principal).
- **AC-FC1-006-3:** Login da conta `admin-recovery` dispara alerta CRÍTICO síncrono: (a) linha em `audit_trail.admin_access` com flag `eh_break_glass=True`, (b) evento `Admin.BreakGlass.Usado` no bus (consumer envia notificação ao Roldão quando bus produtivo entrar — F-C2 estendido).
- **AC-FC1-006-4:** Procedimento documentado em `docs/operacao/runbook.md §11.bis` (novo) com: (a) quando usar (após esgotar reset normal), (b) registrar motivo + horário em texto livre, (c) ação obrigatória pós-uso (restaurar MFA da conta principal + revisar audit).
- **AC-FC1-006-5:** Drill mensal de `admin-recovery` rastreado em `docs/operacao/drills/break-glass-YYYY-MM-DD.md` (1ª execução em F-C1; recorrência mensal vira GATE-CYBER-BREAKGLASS-DRILL Wave A).

### US-FC1-005 — Drill end-to-end de F-C1

**Como** dono do produto,
**quero** um comando `python manage.py validar_f_c1` que rode todos os drills de F-C1 em sequência,
**para que** o critério de saída da fase seja verificável em 1 comando.

**AC binários:**

- **AC-FC1-005-1:** Comando `validar_f_c1` em `src/infrastructure/admin_ops/management/commands/validar_f_c1.py`.
- **AC-FC1-005-2:** Drills executados em ordem:
  1. Hook `prod-settings-check.sh` rejeita as ~14 violações sintéticas (settings expandido R-1).
  2. Middleware `AdminHardeningMiddleware` bloqueia: sem MFA / IP fora allowlist / 6ª tentativa / session-rebind mismatch (AC-FC1-002-8).
  3. Audit log de `admin_access` registra acesso bem-sucedido com `ip_hash` (não IP em claro) — AC-FC1-002-3.
  4. Job de pseudonimização: linha com `timestamp > 90d` tem `usuario_id_hash` (não `usuario_id`) — AC-FC1-002-7.
  5. `OutboundWebhookProvider` rejeita URLs com IP nas 8 faixas proibidas (incluindo IPv6 ULA, CGN, 0.0.0.0/8, sufixos descoberta interna) — AC-FC1-003-3 expandido.
  6. `OutboundWebhookProvider` assina HMAC com canonical string `{timestamp}.{method}.{path}.{sha256(body)}` (verificação cross-check) — AC-FC1-003-3.
  7. `OutboundWebhookProvider` rejeita chamada quando `webhook_destino.dpa_assinado_em IS NULL` — AC-FC1-003-9.
  8. DNS rebinding: simular múltiplos A/AAAA → rejeita se qualquer um cair em faixa proibida — AC-FC1-003-6.
  9. Rotação dogfooding: chave antiga não decifra sessão nova; declaração de eliminação efetiva no log do drill — AC-FC1-004-5.
  10. Break-glass: login com U2F na conta `admin-recovery` dispara evento `Admin.BreakGlass.Usado` + entrada em `admin_access` com `eh_break_glass=True` — US-FC1-006.
- **AC-FC1-005-3:** Output do comando: 10/10 PASS ou parada na 1ª falha com mensagem clara.

---

## 3. Invariantes de F-C1 (REGRAS-INEGOCIAVEIS.md)

| ID | Regra | Hook que valida |
|---|---|---|
| INV-ADMIN-001 | `/admin/*` exige MFA TOTP + IP allowlist + rate-limit 5/15min + session-rebind a `ip_hash`+`ua_hash` (P3 retrofit AC-FC1-002-8) | `admin-hardening-check.sh` |
| INV-ADMIN-002 (novo P3) | `admin_access` é append-only com RLS + trigger anti-mutation; retenção 24m rolling; pseudonimização `usuario_id` → `usuario_id_hash` após 90d (resolve LGPD art. 18 × auditoria) | `audit-immutability-check.sh` estendido |
| INV-ADMIN-003 (novo P3) | Conta `admin-recovery` exige U2F (WebAuthn); login dispara evento `Admin.BreakGlass.Usado` + linha em `admin_access` com flag `eh_break_glass=True` | revisão `auditor-seguranca` |
| INV-PROD-SET-001 | Settings de produção tem `DEBUG=False`, `ALLOWED_HOSTS` lista fechada, cookies SECURE, HSTS≥1ano com `includeSubDomains; preload`, X-Frame=DENY, Content-Type-NoSniff, Referrer Policy, CSP, **`SECURE_PROXY_SSL_HEADER`** + **`CSRF_TRUSTED_ORIGINS`** + **`DATA_UPLOAD_MAX_MEMORY_SIZE≤10MB`** + **`DATA_UPLOAD_MAX_NUMBER_FIELDS≤1000`** (P3 retrofit R-1) | `prod-settings-check.sh` |
| INV-WEBHOOK-OUT-001 | Toda chamada HTTP de saída (Lacuna, KMS, Asaas, INMETRO, SendGrid, qualquer destino externo) passa por `OutboundWebhookProvider`. Uso direto de `requests`/`httpx`/`urllib3`/`urllib.request` em `src/infrastructure/**` é proibido fora do adapter. | `outbound-webhook-ssrf-check.sh` |
| INV-WEBHOOK-OUT-002 | `OutboundWebhookProvider` valida SSRF antes do connect: bloqueia 8 faixas (RFC1918 + loopback + link-local + multicast + **IPv6 ULA fc00::/7** + **CGN 100.64/10** + **0.0.0.0/8** + sufixos DNS internos) — P3 retrofit R-3 | hook + revisão `auditor-seguranca` |
| INV-WEBHOOK-OUT-003 | `OutboundWebhookProvider` assina HMAC-SHA256 com **canonical string `{timestamp}.{method}.{path}.{sha256(body)}`** + janela ≤5min + event_id em `consumer_idempotencia` — P3 retrofit R-2 | revisão `auditor-seguranca` |
| INV-WEBHOOK-OUT-004 | DNS resolve uma vez via `getaddrinfo` → valida TODOS os A/AAAA → connect pelo IP fixado (não pelo hostname). TTL=0 tratado igual TTL>0 — anti-rebinding P3 retrofit R-8 | revisão `auditor-seguranca` |
| INV-WEBHOOK-OUT-005 (novo P3) | Toda chamada `OutboundWebhookProvider.post(destino_id, ...)` REJEITA quando `webhook_destino.dpa_assinado_em IS NULL` ou `dpa_vence_em < CURRENT_DATE` ou `chave_expires_at < CURRENT_DATE` (LGPD art. 39 + rotação ≤90d) | `outbound-webhook-ssrf-check.sh` estendido |

---

## 4. Critérios de entrada

- [x] Onda 0 plano-v2 fechada (ADRs reservadas, LICENSE BUSL-1.1, F-C decomposta no faseamento)
- [x] Onda 2 sub-A fechada (ADR-0057 a11y, ADR-0058 analytics, ADR-0062 devcontainer aceitas)
- [x] Onda 2 sub-B fechada (IDEMP-001a, matriz LGPD direitos titular, god-modules deferral)
- [ ] Roldão aprova arrancar F-C1 (gate manual)
- [ ] 4 humano-substitutos revisam `plan.md` desta F-C1 (ritual Spec Kit P2)

---

## 5. Critérios de saída (mortalidade)

- [ ] Comando `validar_f_c1` retorna **10/10 PASS** (drill expandido após P3).
- [ ] 10 auditores Família 5 PASS ZERO CRÍTICO/ALTO/MÉDIO.
- [ ] Suite total (≥250 hooks; pytest ≥621) verde.
- [ ] Hooks novos: `prod-settings-check.sh`, `admin-hardening-check.sh`, `outbound-webhook-ssrf-check.sh` — cada um com ≥8 casos verdes no `_test-runner.sh` (8 em vez de 6 — escopo expandido P3).
- [ ] AGENTS §11: ADR-0054 promovida proposta → aceito.
- [ ] REGRAS-INEGOCIAVEIS.md: **INV-ADMIN-001..003 + INV-PROD-SET-001 + INV-WEBHOOK-OUT-001..005** cravadas (9 invariantes; era 6 — escopo expandido P3 absorveu break-glass, audit retention, DPA enforcement).
- [ ] `docs/operacao/rotacao-credenciais-dogfooding.md` criado com mapeamento manual→KMS + drill registrado com declaração de eliminação efetiva.
- [ ] `docs/conformidade/dpia/admin-access.md` criado (DPIA template ANPD; **não bloqueia F-C1**, bloqueia 1º tenant externo — GATE-LGPD-DPIA-ADMIN).
- [ ] Conta `admin-recovery` U2F criada + drill break-glass executado e arquivado.
- [ ] Auditor de Segurança não bloqueou merge nos últimos 7 dias da fase.

### Se reprovar (princípio "código não vira descartável")

- Hook `prod-settings-check.sh` muito conservador (false positive frequente em prod válida) → ajustar allowlist, NÃO desligar.
- SSRF guard rejeita destino legítimo (ex: KMS endpoint regional) → adicionar exceção explícita por destino no allowlist do adapter; documentar em ADR de extensão.
- MFA bloqueia acesso emergencial → procedimento `break-glass` documentado em runbook (ainda nesta fase OU em F-C2 — decisão em P2).
- Em nenhum caso código é jogado fora.

---

## 6. Entregáveis (P4) — 14 T-FC1 estimadas (R-7 / TL-10)

1. **Hooks** (3 novos): `prod-settings-check.sh`, `admin-hardening-check.sh`, `outbound-webhook-ssrf-check.sh`.
2. **Settings**: `config/settings/prod.py` revisto com todos os ~14 valores corretos (P3 expandido).
3. **Middleware**: `src/infrastructure/auth/admin_hardening_middleware.py` + middleware session-rebind.
4. **Modelo**: `src/infrastructure/audit/models.py` + migration `0017_admin_access` (append-only, RLS, trigger, `ip_hash`, retenção 24m); job procrastinate `pseudonimizar_admin_access_antigo`.
5. **Modelo**: `src/infrastructure/webhook_out/models.py` + migration `0018_webhook_destino` (cadastro DPA + chave HMAC + `expires_at`).
6. **Conta break-glass**: `manage.py criar_admin_recovery` + integração WebAuthn + evento `Admin.BreakGlass.Usado`.
7. **Comando**: `validar_f_c1` (10 drills).
8. **Doc**: `docs/operacao/rotacao-credenciais-dogfooding.md` + drill arquivado com declaração eliminação efetiva.
9. **Doc**: `docs/conformidade/dpia/admin-access.md` (template ANPD — não bloqueia F-C1).
10. **REGRAS**: INV-ADMIN-001..003 + INV-PROD-SET-001 + INV-WEBHOOK-OUT-001..005 cravadas (9 invariantes).
11. **ADR-0054 aceitação + implementação** (R-6 / TL-09 — entregável principal desta F-C1, não dependência externa): `src/domain/shared/ports/webhook_out.py` (Protocol) + `src/infrastructure/webhook_out/{adapter,ssrf_guard,hmac_sign,destino_dpa_check}.py`. Promoção em AGENTS §11.
12. **Direitos titular** (R-11 / LGP-FC1-04): atualizar `docs/conformidade/comum/direitos-titular-cross-modulo.md` com entrada nova `admin_access` (matriz pseudonimização vs eliminação).
13. **Runbook**: atualizar §10 `runbook.md` substituindo `# 9. Rotação` por procedimento canônico + §11.bis novo (break-glass).
14. **Drill `break-glass`** mensal arquivado em `docs/operacao/drills/break-glass-2026-MM-DD.md`.

---

## 7. Dependências externas

- F-A (multi-tenant + RLS) — fechada.
- F-B (auth + MFA TOTP) — fechada. MFA TOTP do `/admin/` reusa o `django-otp` já instalado.
- ADR-0062 (Devcontainer) — aceita Onda 2 sub-A. Sessões de F-C1 que tocam `auth/`, `kms/`, `admin_ops/`, `webhook_out/` rodam dentro do devcontainer (INV-DEVCONT-001).

> **R-6 / TL-09:** ADR-0054 NÃO é dependência externa — é **entregável** desta F-C1 (item 11 do §6). Aceitação + implementação acontecem juntas na P4 (auditor DRIFT alertou que aceitar sem implementar gera drift).

---

## 8. Histórico

- 2026-05-23 P1: criada por Onda 2 plano-v2 sub-B; status `draft`.
- 2026-05-23 P2: 3 reviews paralelos (tech-lead, advogado, corretora; RBC N/A). 4 BLOQ + 4 convergências + 7 MED dirigidos absorvidos. Detalhe em `matriz-reconciliacao.md` + `plan.md`.
- 2026-05-23 P3: retrofit aplicado neste spec.md absorvendo R-1..R-15. Status `draft` → `proposta`. Próximo passo: Roldão aprovar P3 antes de P4 (implementação 14 T-FC1).
- Próximas fases: P4 (implementação) + P5 (10 auditores Família 5 — critério ZERO C/A/M).
