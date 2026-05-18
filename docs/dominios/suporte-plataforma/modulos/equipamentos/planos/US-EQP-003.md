---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-003
---

# Plano US-EQP-003 — Ficha 360° + scan QR dual-mode + PWA

> Story em `prd.md` §6 (US-EQP-003).
>
> **Pré-requisitos:** US-EQP-001 (módulo + QR) + US-EQP-002 (EquipamentoVersao); ADR-0018 aceita.
>
> **Revisão (2026-05-18 noite):** APROVADO COM RESSALVAS — 6 tech-lead + 5 advogado. Pareceres em `revisoes/US-EQP-003-{tech-lead,advogado}.md`. **Decisão Roldão: adotar Redis no docker-compose agora** (TL1).

## Resumo

Implementar (a) endpoint `GET /v1/equipamentos/{id}` retornando ficha 360° completa com escopo por papel (RBC C8), (b) endpoint `GET /v1/qr/{hash}` dual-mode (INV-051 — Escopo A/B/C com allowlist), (c) hook `port-binding-validator.sh` (tech-lead B5), (d) PWA scanner em HTML+JS vanilla com BarcodeDetector + fallback jsQR (ADR-0018), (e) rate limit por IP + lockout (advogado B3 + corretora B1).

## Sequência de tasks

- **T-EQP-027**: hook `port-binding-validator.sh` — bloqueia release prod se algum binding em `settings.production.PORT_BINDINGS` aponta para classe começando com `Empty`. Atualizar `_test-runner.sh` com 4 casos. Atualizar `.claude/settings.json` registrando o hook em PostToolUse/PreToolUse conforme convenção.
- **T-EQP-028**: action novas no seed authz (migration 0010): `equipamento.ler_via_qr`, `equipamento.imprimir_etiqueta`. Atribuir `equipamento.ler_via_qr` aos perfis SYSTEM (anônimo via SYSTEM_USER) + todos perfis autenticados.
- **T-EQP-029**: use case `ResolverHashQr` em `src/application/.../resolver_hash_qr.py`:
  - Recebe `hash, user, tenant_id_da_sessao`.
  - Resolve `QrCode` pela tabela (consulta indexada) — se não existe ou `revogado_em != NULL` → 404 indistinguível.
  - Determina escopo: A (sessão + tenant igual), B (sessão + tenant diferente), C (sem sessão).
  - Chama `AuthorizationProvider.can(user, "equipamento.ler" | "equipamento.ler_via_qr", {...}, purpose=...)`.
  - Retorna `RedirectToFicha` (Escopo A) ou `PayloadMinimoB/C` (DTOs).
- **T-EQP-030**: middleware `RateLimitByIPLockout` em `src/infrastructure/equipamentos/middleware.py` — django-ratelimit + tabela `ip_lockout` (migration 0011) que rastreia 4xx por IP/hora. Hook `audit_trail.eventos` action=`equipamento.qr_scanned` em todos scans (com `ip_hash` + `user_agent_hash` salgados por tenant — INV-AUTHZ-002).
- **T-EQP-031**: view `QrResolverView` mapeando para 3 responses:
  - 302 redirect para `/equipamentos/{id}` (Escopo A).
  - 200 JSON Escopo B (allowlist).
  - 200 JSON Escopo C (mensagem genérica + logo Aferê institucional).
  - 404 (hash inválido / revogado / cross-tenant — todos indistinguíveis).
  - 429 (rate limit por IP).
  - Cache `Cache-Control: private, no-store`.
- **T-EQP-032**: ficha 360° completa `GET /v1/equipamentos/{id}` — agrega via portas:
  - Dados cadastrais (modelo)
  - Versões (`EquipamentoVersao`)
  - Histórico de certificados (porta `CertificadoQueryService.buscar_por_equipamento`)
  - OS abertas (porta `OSQueryService.buscar_abertas_por_equipamento`)
  - Eventos (`audit_trail.eventos` filtrados por equipamento_id)
  - Camadas de visibilidade por papel (RBC C8 — tabela da Tela 3 em `ui.md`).
- **T-EQP-033**: índice composto `(tenant_id, equipamento_id, created_at DESC)` em `audit_trail.eventos` + `equipamento_versao` (migration 0012) — performance ficha 360° p95 ≤ 1.5s.
- **T-EQP-034**: log de visualização (INV-013 análoga) — todo acesso à ficha 360° de outro perfil grava `equipamento.visualizado` com `papel_visualizador + escopo_de_dados`.
- **T-EQP-035**: PWA scanner em `src/infrastructure/equipamentos/static/scanner/`:
  - `index.html` + `manifest.json` + `service-worker.js`
  - `scanner.js` — feature-detect `window.BarcodeDetector`; carrega `jsQR.js` se não disponível
  - Tela explicativa antes de pedir câmera
  - Fallback `<input type="file" capture="environment">` se permissão negada
  - Texto UX em PT-BR
  - View Django `/equipamentos/scanner/` serve a página estática
- **T-EQP-036**: testes Python:
  - `test_qr_resolver_escopo_a_redirect_302` (mesma sessão tenant)
  - `test_qr_resolver_escopo_b_payload_minimo` (outro tenant)
  - `test_qr_resolver_escopo_c_anonimo` (sem sessão)
  - `test_qr_resolver_hash_inexistente_404` (indistinguível)
  - `test_qr_resolver_revogado_404` (indistinguível)
  - `test_qr_resolver_cross_tenant_forjado_404` (HMAC inválido)
  - `test_rate_limit_ip_60_por_min_retorna_429` (corretora B1)
  - `test_lockout_ip_100_4xx_em_1h_bloqueia_24h` (corretora B1)
  - `test_payload_escopo_c_nao_contem_pii` (varredura regex em 20 fixtures plantadas — qr-publico-allowlist.md T-QR-PUB-08)
  - `test_payload_escopo_b_mostra_proxima_calibracao_mas_nao_pii` (qr-publico-allowlist.md)
  - `test_ficha_360_metrologista_ve_eventos_e_recebimentos` (RBC C8)
  - `test_ficha_360_atendente_nao_ve_aba_eventos` (RBC C8)
  - `test_ficha_360_tecnico_campo_so_ve_os_atribuidas` (advogado C3)
  - `test_visualizacao_ficha_grava_audit_log` (INV-013 análoga)
  - `test_ficha_360_p95_menor_1500ms` (benchmark com 100 versões + 50 certs simulados via stub)
  - `test_qr_scan_grava_audit_com_ip_hash_e_ua_hash_salgados` (INV-AUTHZ-002)
- **T-EQP-037**: testes JS do PWA (manual + automatizado simples):
  - Manual: matriz browser (Chrome Android, Safari iOS 17, Safari iOS 16, Firefox Android) — checklist em `docs/operacao/runbooks-pwa-scanner.md` (a criar curto).
  - Automatizado: smoke test Playwright (futuro — Wave A late).

## Modelos/tabelas envolvidos

- **Novo:** `ip_lockout` (rate limit defensivo)
- **Novo (índice):** `audit_trail_eventos.idx_tenant_equipamento_created`
- **Já existe:** `equipamento`, `equipamento_versao`, `qrcode`, `audit_trail.eventos`

## Endpoints envolvidos

- `GET /v1/equipamentos/{id}` (ficha 360° completa com escopo por papel)
- `GET /v1/qr/{hash}` (dual-mode INV-051)
- `GET /equipamentos/scanner/` (PWA estática)

## Hooks ativados

- Todos US-EQP-001/002 + novo `port-binding-validator.sh` (T-EQP-027).

## Testes obrigatórios

Ver T-EQP-036 (16 testes Python) + smoke test PWA. Cobertura ≥85%.

## Riscos / pontos sensíveis

1. **PWA performance:** câmera ativa + jsQR fallback em CPU fraca pode dar latência > 3s. Mitigação: reduzir frame rate dinamicamente; toast "aponte e mantenha estável" após 3s sem detecção.
2. **Rate limit cross-IP / proxy:** corp clients atrás de NAT podem ser bloqueados em massa. Mitigação: lockout só após 100 4xx (não 200), e por IP+UA hash conjunto (não só IP).
3. **Resposta 404 indistinguível:** precisa garantir tempo de resposta também indistinguível (timing oracle). Implementar timing constante (sleep até 100ms se resolução foi mais rápida).
4. **Performance p95 ≤ 1.5s:** com porta stub retornando `[]` rapidamente, easy. Quando módulo certificados nascer e retornar 50+ certs, pode estourar. Mitigação: medir agora + adicionar cache invalidado por evento `equipamento.versao_criada` só se medido falhar (RBC C5).
5. **PWA install vs HTTPS:** PWA exige HTTPS em produção. Dev usa http://localhost (permitido). Documentar em runbook deploy.

## Subagentes a consultar

- `tech-lead-saas-regulado`: validar arquitetura do `ResolverHashQr` + middleware rate limit + cache layer (se aplicável) + PWA service worker.
- `advogado-saas-regulado`: validar exatos JSON Escopo B/C contra `qr-publico-allowlist.md` (nada vaza).
- `corretora-seguros-saas`: confirmar que defesa em profundidade atende ADR-0019 + reduz prêmio cyber.
- `consultor-rbc-iso17025`: confirmar que log de visualização cobre cl. 4.2 (confidencialidade).

## Non-goals deste plano

- NÃO implementar UI HTMX da ficha 360° além do mínimo de serializer DRF (UI HTMX entra em iteração posterior).
- NÃO implementar app Flutter (ADR-0003 — Wave B).
- NÃO implementar adapter real `LacunaWebPkiAssinaturaA3Service` (US-EQP-002 já deixa stub).
- NÃO implementar VIEW real `OSQueryService` (porta stub `EmptyOSQueryService` até módulo OS nascer).

---

## Endereçamento da revisão (11 ressalvas)

### Tech-lead

- **TL1 (CRÍTICA — Redis):** **ACEITO POR ROLDÃO.** Redis adicionado ao docker-compose (container `afere-redis`); `config/settings/base.py` configura `default` cache + `ratelimit` cache (DB 1/2 isolados); `test.py` override pra LocMem. Tabela `ip_lockout` em PG mantida APENAS pra audit forense (não pra rate-limit em runtime).
- **TL2 (CRÍTICA — timing oracle):** `ResolverHashQrUseCase` usa target time-constant ≥ p99 medido + jitter `secrets.randbelow(10) - 5 ms`. Teste estatístico exigido: `abs(mean_404 - mean_200) > 10ms` falha. Pentest externo continua sendo dívida pra Wave A+ (R-065).
- **TL3 (ALTA — 404 unificado):** `_RESPONSE_404_BODY` ClassVar em `QrResolverView` + `HttpResponse` direto (não `Http404`/DRF Response — esses vazam headers). Hash inválido / revogado / cross-tenant entram no MESMO construtor.
- **TL4 (ALTA — benchmark p95):** `pytest-benchmark` + fixture `equipamento_com_100_versoes_e_50_certs` + série temporal commitada em `reports/bench.json`. RBC C5 já estabeleceu "medir primeiro, cachear só se falhar".
- **TL5 (ALTA — `port-binding-validator.sh`):** esqueleto bash usando `poetry run python -c` (resolve PORT_BINDINGS em runtime, NÃO regex). Allowlist via comentário `# port-binding: empty-allowed -- <razão>` (Marco 2 `FinanceiroQueryService` Empty allowed). +5 casos em `_test-runner.sh`.
- **TL6 (MÉDIA — service worker):** `network-only` para `/v1/qr/*` e `/v1/equipamentos/*`; `cache-first` para static assets; teste Playwright (futuro — smoke manual no Marco 2).

### Advogado

- **R1 (BLOQUEANTE — snapshot test JSON):** `test_payload_escopo_{b,c}_bate_exatamente_contrato_json` byte-a-byte contra fixtures congeladas. Sem isso, agente Wave A pode introduzir campo sem detecção.
- **R2 (BLOQUEANTE — salt institucional global):** **ACEITO.** Escopo C usa `settings.AFERE_AUDIT_GLOBAL_SALT`, não `tenant_id`. Atualizado `isolamento-multi-tenant.md` §8.1 + `qr-publico-allowlist.md` §3.
- **R3 (CONCERN — headers extras):** `Cache-Control: private, no-store` + `Pragma: no-cache` + `Expires: 0` + `Vary: Authorization, Cookie` + `Referrer-Policy: no-referrer` + `X-Robots-Tag: noindex, nofollow`.
- **R4 (CONCERN — `equipamento.visualizado`):** TODA abertura (inclusive admins do próprio tenant) síncrono ANTES de renderizar (espelho US-CLI-002 INV-013). Granularidade por `papel_visualizador + escopo_de_dados`.
- **R5 (CONCERN — textos UX divergentes):** 3 textos prontos no parecer (UX1 outro tenant, UX2 anônimo, UX3 404). Replicar em `ui.md` Tela 7 (já alinhado v3) + remover bug `aferê_url_institucional` → `afere_url_institucional` (aplicado em `qr-publico-allowlist.md` + `api.md`).

## Sequência revisada de tasks (Marco 2 + Redis aceito)

- **T-EQP-027**: hook `port-binding-validator.sh` (TL5 — runtime via poetry python)
- **T-EQP-028**: actions seed authz (`ler_via_qr`, `imprimir_etiqueta`)
- **T-EQP-029**: use case `ResolverHashQr` com target time-constant (TL2 jitter ±5ms)
- **T-EQP-030**: middleware Redis rate-limit (django-ratelimit com `cache='ratelimit'` — TL1)
- **T-EQP-030a (NOVA)**: tabela `ip_lockout` em PG apenas pra audit forense histórico (não runtime — TL1)
- **T-EQP-031**: view `QrResolverView` com `_RESPONSE_404_BODY` ClassVar (TL3) + 6 headers anti-cache (R3)
- **T-EQP-032**: ficha 360° via portas + camadas papel (RBC C8 ui.md v3)
- **T-EQP-033**: índices `(tenant_id, equipamento_id, created_at DESC)` + `pytest-benchmark` (TL4)
- **T-EQP-034**: log de visualização `equipamento.visualizado` SÍNCRONO toda abertura (R4)
- **T-EQP-035**: PWA scanner (HTML+JS vanilla + service worker `network-only` /qr/* — TL6)
- **T-EQP-035a (NOVA)**: `AFERE_AUDIT_GLOBAL_SALT` em settings (R2) + helper `hash_pii_escopo_c()` em `audit_qr_scan.py`
- **T-EQP-036**: testes (acrescenta `test_timing_4xx_e_2xx_indistinguivel_estatistico` TL2 + `test_payload_escopo_b_c_snapshot_byte_a_byte` R1 + `test_visualizado_grava_audit_admin_proprio_tenant` R4 + `test_response_headers_incluem_vary_authorization` R3)
- **T-EQP-037**: testes PWA matriz browser (manual) + Playwright smoke (futuro)
