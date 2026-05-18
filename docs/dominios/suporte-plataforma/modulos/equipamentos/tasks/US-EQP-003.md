---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
us: US-EQP-003
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-003.md
historico:
  - 2026-05-18 noite final — criado forward-looking. Decisão Roldão: Redis no docker-compose desde já (TL1).
---

# Tasks T-EQP-027..T-EQP-037 — US-EQP-003 (ficha 360° + scan QR dual-mode + PWA + Redis)

> Forward-looking. Pré-requisitos: US-EQP-001 + US-EQP-002 entregues; ADR-0018 (PWA) aceita; Redis ativo no docker-compose.

## Mapa task → arquivo/migration → AC → INV → endereça ressalva

| Task | Descrição | Arquivo/Migration | AC | INV | Endereça |
|---|---|---|---|---|---|
| T-EQP-027 | Hook `port-binding-validator.sh` — `poetry run python -c` resolve `PORT_BINDINGS` em runtime (NÃO regex); bloqueia release prod se algum binding aponta `Empty<...>Adapter` sem allowlist `# port-binding: empty-allowed -- <razão>`; +5 casos `_test-runner.sh`; registro em `.claude/settings.json` | `.claude/hooks/port-binding-validator.sh` | AC-3 | — | TL5 (ALTA — runtime via poetry) |
| T-EQP-028 | Migration 0010 — actions `equipamento.ler_via_qr` (atribuída a SYSTEM_USER + perfis autenticados) + `equipamento.imprimir_etiqueta` no seed authz | `0010_seed_authz_qr.py` | AC-1, AC-2 | SEC-LEAST-PRIV | — |
| T-EQP-029 | Use case `ResolverHashQrUseCase` — resolve `QrCode`, determina escopo (A/B/C), chama `AuthorizationProvider.can()`, retorna `RedirectToFicha` ou `PayloadMinimoB/C`. **Target time-constant ≥ p99 medido + jitter `secrets.randbelow(10) - 5 ms`** | `src/application/.../resolver_hash_qr.py` | AC-2 | INV-051, INV-AUTHZ-001 | TL2 (CRÍTICA — timing oracle) |
| T-EQP-030 | Middleware `RateLimitByIPLockout` (django-ratelimit com `cache='ratelimit'` apontando Redis DB 2) + lockout após 100 4xx em 1h por IP+UA hash | `src/infrastructure/equipamentos/middleware.py` | AC-2 | INV-AUTHZ-002 | TL1 (CRÍTICA — Redis ACEITO) |
| T-EQP-030a (NOVA) | Tabela `ip_lockout` em PG **apenas pra audit forense histórico** (não runtime); migration 0011 + RLS | `0011_ip_lockout_audit.py` | AC-2 | — | TL1 |
| T-EQP-031 | View `QrResolverView` — `_RESPONSE_404_BODY` ClassVar; `HttpResponse` direto (não `Http404`/DRF Response); hash inválido / revogado / cross-tenant entram no MESMO construtor; 6 headers anti-cache (`Cache-Control: private, no-store` + `Pragma` + `Expires: 0` + `Vary: Authorization, Cookie` + `Referrer-Policy: no-referrer` + `X-Robots-Tag: noindex, nofollow`) | `src/infrastructure/equipamentos/views.py` | AC-2 | — | TL3 (ALTA — 404 unificado) + R3 advogado (CONCERN headers) |
| T-EQP-032 | Ficha 360° `GET /v1/equipamentos/{id}` — agrega via portas (cadastro, versões, certs via `CertificadoQueryService`, OS via `OSQueryService`, eventos audit); camadas de visibilidade por papel conforme `ui.md` Tela 3 (RBC C8) | `src/application/.../ficha_360.py` + view | AC-1 | INV-AUTHZ-001 | RBC C8 |
| T-EQP-033 | Índice composto `(tenant_id, equipamento_id, created_at DESC)` em `audit_trail.eventos` e `equipamento_versao` (migration 0012); `pytest-benchmark` + fixture `equipamento_com_100_versoes_e_50_certs` + série temporal em `reports/bench.json`; meta p95 ≤ 1.5s | `0012_indices_performance.py` + `tests/equipamentos/test_ficha_360_p95.py` | AC-1 | — | TL4 (ALTA — benchmark p95) |
| T-EQP-034 | Log `equipamento.visualizado` síncrono ANTES de renderizar a ficha (espelho US-CLI-002 INV-013); granularidade `papel_visualizador + escopo_de_dados`; cobre admins do próprio tenant também | `src/application/.../ficha_360.py` | AC-3 | INV-013 análoga | R4 advogado (CONCERN síncrono) |
| T-EQP-035 | PWA scanner em `src/infrastructure/equipamentos/static/scanner/` — `index.html` + `manifest.json` + `service-worker.js` (network-only `/v1/qr/*` + `/v1/equipamentos/*`; cache-first static assets) + `scanner.js` (feature-detect `BarcodeDetector`; fallback jsQR) + tela explicativa pré-câmera + fallback `<input type="file" capture="environment">` + texto PT-BR; view Django `/equipamentos/scanner/` | `static/scanner/*` + `views.py` | AC-2 | — | TL6 (MÉDIA — service worker) + ADR-0018 |
| T-EQP-035a (NOVA) | `settings.AFERE_AUDIT_GLOBAL_SALT` (NÃO `tenant_id`) + helper `hash_pii_escopo_c()` em `src/infrastructure/equipamentos/audit_qr_scan.py` — atualiza `isolamento-multi-tenant.md` §8.1 + `qr-publico-allowlist.md` §3 | `config/settings/base.py` + `audit_qr_scan.py` | AC-2 | INV-AUTHZ-002 | R2 advogado (BLOQUEANTE — salt global Escopo C ACEITO) |
| T-EQP-036 | Suite 16 testes Python: escopo A/B/C, hash inexistente/revogado/cross-tenant todos 404 indistinguíveis, rate limit 429 (60/min), lockout 24h após 100 4xx, payload Escopo C sem PII (varredura 20 fixtures), payload Escopo B mostra próx. calibração sem PII, ficha metrologista vs atendente vs técnico campo (RBC C8), visualização grava audit, p95 ≤ 1.5s, scan grava audit com `ip_hash`/`ua_hash` salgados, **+ `test_timing_4xx_e_2xx_indistinguivel_estatistico` (TL2 — `abs(mean_404 - mean_200) > 10ms` falha)** **+ `test_payload_escopo_b_c_snapshot_byte_a_byte` (R1 advogado BLOQUEANTE)** **+ `test_visualizado_grava_audit_admin_proprio_tenant` (R4)** **+ `test_response_headers_incluem_vary_authorization` (R3)** | `tests/equipamentos/test_us_eqp_003_ficha_e_scan.py` | AC-1, AC-2, AC-3 | INV-051, INV-AUTHZ-001/002, INV-013 análoga | todas |
| T-EQP-037 | Testes manuais PWA — checklist matriz browser (Chrome Android, Safari iOS 17, Safari iOS 16, Firefox Android) em `docs/operacao/runbooks-pwa-scanner.md` (criar curto); smoke Playwright deferido pra Wave A late | `docs/operacao/runbooks-pwa-scanner.md` | AC-2 | — | TL6 |

## Pareceres aplicados

- `revisoes/US-EQP-003-tech-lead.md` — APROVADO COM RESSALVAS (**TL1 Redis ACEITO**, TL2 CRÍTICA timing oracle, TL3 ALTA 404 unificado, TL4 benchmark p95, TL5 hook runtime, TL6 service worker)
- `revisoes/US-EQP-003-advogado.md` — APROVADO COM RESSALVAS (R1 BLOQ snapshot JSON, **R2 BLOQ salt global ACEITO**, R3 6 headers anti-cache, R4 visualizado síncrono, R5 textos UX + fix `aferê_url`)
- `revisoes/US-EQP-003-corretora.md` — APROVADO (defesa em profundidade ADR-0019; reduz prêmio cyber)

## Total

13 tasks (11 originais + 2 novas) · 16 testes Python + smoke PWA · 3 migrations · 1 hook novo (`port-binding-validator.sh`).
