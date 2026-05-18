---
owner: tech-lead-saas-regulado
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-003
plano_revisado: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-003.md
veredito: APROVADO COM RESSALVAS
---

# Tech Lead Review — Plano US-EQP-003

## Resumo executivo

Plano cobre bem o recorte (ficha 360° + dual-mode QR + PWA + rate limit) e respeita ADR-0018, INV-051 e a allowlist. Cinco pontos exigem ajuste antes de `/implement` — três deles afetam diretamente postura de segurança (timing oracle, lockout em store volátil, e 404 indistinguível em código real). Nenhum reabre PRD ou ADR. Há também duas ressalvas operacionais sobre o hook novo (`port-binding-validator.sh`) e sobre a estratégia de medição da p95 (RBC C5 — "medir primeiro, cachear só se falhar").

## Veredito

**APROVADO COM RESSALVAS** (6 ressalvas — bloqueiam `/implement` até endereçadas no plano; nenhuma exige reabrir Story/ADR).

---

## Ressalvas (ordem por gravidade)

### 1. CRÍTICA — Lockout por IP em tabela PG é hit DB por request e perde corrida sob carga

**Problema:** o plano (`T-EQP-030`) propõe `RateLimitByIPLockout` + tabela `ip_lockout`. Hoje o projeto **não tem Redis** (`pyproject.toml` sem dependência; `config/settings/base.py:211` usa `LocMemCache` por processo). A consequência prática:

- **Cada request anônimo** ao `/v1/qr/{hash}` faz **SELECT em `ip_lockout` + INSERT/UPDATE em contador** dentro do request loop. Com 60 req/min/IP permitido + N IPs sob fuzzing (T-QR-PUB-05 manda exatamente esse cenário), a tabela vira hot-write — contenção de lock e amplificação do custo do ataque (o atacante derruba o banco, não a aplicação).
- **`django-ratelimit`** é dependência **nova** (não listada em `pyproject.toml`) e seu backend padrão é o cache Django. Com `LocMemCache`, cada processo gunicorn tem contador próprio — **lockout vira ficção** (atacante distribui em 4 workers e faz 4× o teto).
- **Race condition:** sem `SELECT ... FOR UPDATE` ou `INSERT ... ON CONFLICT DO UPDATE` correto, dois requests concorrentes do mesmo IP incrementam contador inconsistente.

**Correção exigida:**

1. **Decisão arquitetural (recomendo a opção B):**
   - **Opção A — manter PG, ser honesto sobre o custo:** documenta no plano que rate limit é PG-backed temporariamente; usa `INSERT ... ON CONFLICT (ip_hash) DO UPDATE SET counter = ip_lockout.counter + 1, window_start = CASE WHEN ip_lockout.window_start < now() - interval '1 minute' THEN now() ELSE ip_lockout.window_start END RETURNING counter` (atômico em uma rodada); aceita 1 SELECT+UPDATE por request com `pg_hint_plan` apontando pro índice `(ip_hash)`.
   - **Opção B — adicionar Redis agora (RECOMENDADO):** `redis-py` + `django-redis` no `pyproject.toml`, `CACHES.default = django_redis.cache.RedisCache` em prod, contadores atomicamente em Redis (`INCR ip:hash:{x}` + `EXPIRE`). Custa 1 container Redis no docker-compose e 4 linhas de config; resolve rate limit + sessão multi-worker + cache shared de uma vez. Redis SP/BR roda dentro do mesmo VPS Hostinger sem custo extra.
   - **Opção C — nginx-level** (rate limit antes da app): só funciona quando subirmos nginx; hoje dev é gunicorn direto. Não viável pra Marco 2.

2. **Decisão Roldão-friendly:** Wave A já está construindo módulo `equipamentos`. Adicionar Redis agora é **menos custoso** do que reescrever rate limit em Wave B. Redis também destrava cache compartilhado da ficha 360° (ressalva 4) e session backend multi-worker. **Minha recomendação concreta: Opção B.**

3. **Tabela `ip_lockout` permanece** — mas só pra **lockout de 24h** (gravação rara, ~1 evento por IP malicioso por dia), não pra contador hot. Contador volátil em Redis; transição para lockout persistente quando contador cruza 100 4xx/h.

4. **Teste obrigatório:** `test_rate_limit_consistente_em_4_workers` — sobe `gunicorn --workers 4`, dispara 240 req com 4 conexões paralelas, confirma que o 61º request global retorna 429 (não 4× 60º). Esse teste sozinho diferencia A de B na implementação.

### 2. CRÍTICA — Timing oracle: "sleep até 100ms" não é time-constant; pode vazar diferença

**Problema:** plano (riscos §3) propõe "sleep constante até 100ms se resolução foi mais rápida". Isso é **timing padding**, e tem dois problemas:

1. **Padding fixo (sleep até X ms) vaza se o caminho 200 demorar > X ms.** Ataque conhecido: se o tempo total do caminho 200 (escopo C) é tipicamente 35ms e o caminho 404 com padding-pra-100ms é 100ms, atacante vê 100ms = 404, < 100ms = hit. Pra ser indistinguível, **todos os caminhos** (200/A, 200/B, 200/C, 404, 429) precisam terminar no **mesmo target** — e o target tem que ser ≥ p99 do caminho mais lento.
2. **`time.sleep()` em event loop síncrono Django bloqueia o worker** — 100ms × 60 req/min = 6s de worker bloqueado/minuto. Sob fuzzing, esgota workers (DoS amplification).

**Correção exigida — código sugerido (em `application/equipamentos/resolver_hash_qr.py`):**

```python
import secrets
import time
from dataclasses import dataclass

# Target medido empiricamente: p99 do caminho mais lento (Escopo A com redirect).
# Re-aferir trimestralmente; vive em settings.
TIMING_TARGET_MS = 120  # 20% acima de p99 medido

@dataclass
class ResolverHashQrUseCase:
    def execute(self, hash_qr: str, user, tenant_id_sessao) -> Resultado:
        start = time.monotonic()
        try:
            resultado = self._resolver_real(hash_qr, user, tenant_id_sessao)
        except (HashInvalido, HashRevogado, CrossTenant):
            resultado = Resultado404Indistinguivel()
        # Constant-time padding até TIMING_TARGET_MS.
        elapsed_ms = (time.monotonic() - start) * 1000
        if elapsed_ms < TIMING_TARGET_MS:
            time.sleep((TIMING_TARGET_MS - elapsed_ms) / 1000)
        # Jitter de ±5ms pra dificultar pico estatístico exato.
        time.sleep(secrets.randbelow(10) / 1000)
        return resultado
```

**Caveats no comentário do código** (precisam ficar no docstring):
- "Timing padding não é prova contra atacante medindo p99 de 10k requests. Defesa é defense-in-depth com rate limit + lockout."
- "Se `TIMING_TARGET_MS` ficar < p99 real, o oracle volta. Hook de monitoring (Marco 3) deve alertar se p99 > TIMING_TARGET_MS por > 5min."

**Teste obrigatório (adicionar a T-EQP-036):** `test_timing_404_e_200_estatisticamente_indistinguivel` — 1.000 req mistos (500 hash válido escopo C, 500 hash inválido); calcula `mean ± stddev` de cada grupo; falha se `|mean_404 - mean_200| > 10ms` OU se `stddev_404 < stddev_200 - 5ms`.

### 3. ALTA — 404 indistinguível: código precisa garantir mesma view, não dois ramos

**Problema:** plano (T-EQP-031) lista 404 separadamente, mas não cravou que **hash inválido, hash revogado e cross-tenant chegam ao mesmo construtor de response**. Erro clássico: dev cria `Http404("hash não existe")` num lugar e `PermissionDenied` em outro, ambos viram 404 via middleware mas com **headers diferentes** (`X-Frame-Options`, `Vary`, `Content-Length` do body).

**Correção exigida — código sugerido (em `infrastructure/equipamentos/views.py`):**

```python
class QrResolverView(APIView):
    permission_classes = [AllowAny]  # autorização é feita dentro pelo AuthorizationProvider

    # Body fixo, calculado uma vez no import time, garante Content-Length idêntico.
    _RESPONSE_404_BODY: ClassVar[bytes] = json.dumps(
        {"detail": "nao_encontrado"}, separators=(",", ":")
    ).encode("utf-8")

    def get(self, request, hash_qr: str):
        try:
            resultado = self.use_case.execute(
                hash_qr=hash_qr,
                user=request.user if request.user.is_authenticated else None,
                tenant_id_sessao=getattr(request, "active_tenant", None),
            )
        except (HashInvalido, HashRevogado, CrossTenantForjado, AuthorizationDenied):
            return self._response_404()

        if isinstance(resultado, RedirectFichaInterna):
            return HttpResponseRedirect(f"/equipamentos/{resultado.equipamento_id}")
        # Escopo B ou C: payload allowlist
        return JsonResponse(resultado.payload, status=200, headers={
            "Cache-Control": "private, no-store",
        })

    def _response_404(self) -> HttpResponse:
        # Body fixo, mesmo Content-Type, mesmos headers que o 200 success.
        return HttpResponse(
            self._RESPONSE_404_BODY,
            status=404,
            content_type="application/json",
            headers={"Cache-Control": "private, no-store"},
        )
```

**Notas críticas:**
- **Use `HttpResponse` direto, não `Http404`** — `Http404` vai pelo handler global do Django que adiciona `X-Frame-Options` e o template debug em dev (vaza estado).
- **NÃO use `Response()` do DRF nos 404** — ele renderiza com `BrowsableAPIRenderer` em browser, vazando UI.
- **`AuthorizationProvider` precisa lançar `AuthorizationDenied` (não retornar False)** — dois caminhos de retorno (`raise` vs `return`) já viraram timing oracle em outros projetos; mantém uma única árvore de exceção.

### 4. ALTA — Medição de p95 ficha 360° precisa benchmark em CI, não wishful thinking

**Problema:** RBC C5 disse "medir primeiro, cachear só se falhar" — instrução correta. Plano (T-EQP-036) lista `test_ficha_360_p95_menor_1500ms` com "100 versões + 50 certs simulados via stub". Há 3 buracos:

1. **Stub retornando `[]` rapidamente passa o teste sempre** — qualquer impl. passa, o teste é vácuo até `CertificadoQueryService` real chegar.
2. **p95 em test runner local (Windows Roldão / GitHub Actions) ≠ p95 em produção Hostinger** — sem load + sem dados realistas, número não representa nada.
3. **Cobertura ≥85% não é benchmark** — pytest-cov não mede latência.

**Correção exigida:**

- **Adicionar `pytest-benchmark`** (em `pyproject.toml` `[tool.poetry.group.dev]`) — 0 custo, 1 linha.
- **Substituir `test_ficha_360_p95_menor_1500ms` por:**

```python
@pytest.mark.benchmark(group="ficha-360")
def test_benchmark_ficha_360_carga_realista(benchmark, equipamento_com_100_versoes_e_50_certs):
    """
    Benchmark com dados realistas em fixture.
    Hard fail se p95 > 1500ms (RBC C5).
    Stub Empty* substituído por fake-que-retorna-50-objetos (não lista vazia).
    """
    resultado = benchmark.pedantic(
        target=lambda: client.get(f"/v1/equipamentos/{equipamento_com_100_versoes_e_50_certs.id}"),
        iterations=20,
        rounds=5,
    )
    # benchmark.stats expõe percentis
    assert benchmark.stats["max"] < 1.5, f"p100 = {benchmark.stats['max']:.3f}s — RBC C5 violado"
    # p95 aproximado (20 iter × 5 rounds = 100 amostras): índice 95
    p95 = sorted(benchmark.stats["data"])[int(0.95 * 100)]
    assert p95 < 1.5, f"p95 = {p95:.3f}s > 1500ms"
```

- **Fixture `equipamento_com_100_versoes_e_50_certs`** — `FakeCertificadoQueryService` injetado em `PORT_BINDINGS` retornando lista populada de objetos sintéticos com tamanho realista de JSON (não dicts vazios).
- **CI grava série temporal** — `pytest-benchmark --benchmark-json=reports/bench.json`; commit do arquivo gera histórico. Quando p95 começar a degradar > 2 commits seguidos, abrir issue de cache (não cachear preventivamente — RBC C5 é regra de ouro aqui).
- **Stub real `EmptyCertificadoQueryService`** permanece em prod até módulo certificados nascer; mas teste roda contra fake populado.

### 5. ALTA — Hook `port-binding-validator.sh` tem 3 falsos negativos e 2 falsos positivos prováveis

**Problema:** plano (T-EQP-027) descreve o hook em uma linha. Olhei os hooks vizinhos (`migration-rls-check.sh`, `authz-check.sh`) e antecipo:

**Falsos positivos:**
1. **Path Windows normalização:** `authz-check.sh` precisou de fix recente (CLAUDE.md §3) pra `backslash→forward`. O novo hook lê `settings.production.PORT_BINDINGS` — se o regex assumir `/` em path do módulo Python (`src.infrastructure.equipamentos.adapters.EmptyOSQueryService`), funciona; mas se ler import de string em `.py` literal e fizer match em path de arquivo, vai falhar em Windows.
2. **Comentário `# port-binding: empty-allowed -- <razão>` precisa existir** — caso real: dev/staging querem `Empty*` mesmo. Sem allowlist, hook bloqueia comum de teste.

**Falsos negativos:**
1. **Detecta `EmptyOSQueryService` mas não `OSQueryServiceStub` / `NullOSQueryService` / `FakeOSQueryService`** — regex `^Empty` é frágil. Convenção precisa ser estrita: **toda classe que não seja implementação real começa com `Empty`** (cravar em `CONTRIBUTING.md` ou no docstring do hook).
2. **Settings dinâmico:** se `PORT_BINDINGS` for montado via `os.environ.get("...", "Empty...")` ou via `if DEBUG: ...`, o parser estático não vê. Hook precisa rodar `python -c "from config.settings import production; print(production.PORT_BINDINGS)"` em subprocess e parsear o output, não regex no source.
3. **Hook só bloqueia em "release prod"** — plano não define o gatilho. PreToolUse de quê? Sugestão: gatilho é PreToolUse de `git tag` matching `v*` OU PreToolUse de mudança em `config/settings/prod.py`. Documentar no plano.

**Correção exigida — esqueleto sugerido (a refinar):**

```bash
#!/usr/bin/env bash
# port-binding-validator.sh — bloqueia release prod com binding stub.
# Convenção: classes Empty* / Null* / *Stub são stubs; produção exige binding real.
set -euo pipefail

# 1. Normalizar paths Windows
PROJECT_DIR_NORM="${CLAUDE_PROJECT_DIR//\\//}"

# 2. Resolver PORT_BINDINGS em runtime, não por regex no source
BINDINGS_JSON=$(
  cd "${PROJECT_DIR_NORM}" && \
  poetry run python -c "
from config.settings import prod
import json
print(json.dumps(prod.PORT_BINDINGS))
" 2>/dev/null
) || {
  echo "ERRO: não consegui resolver PORT_BINDINGS em prod" >&2
  exit 2  # warning não-bloqueante
}

# 3. Match contra padrões de stub
STUB_REGEX='(^Empty|^Null|Stub$|Fake$)'
VIOLATIONS=$(echo "$BINDINGS_JSON" | perl -MJSON::PP -ne '
  my $j = decode_json($_);
  while (my ($port, $impl) = each %$j) {
    my $cls = (split /\./, $impl)[-1];
    print "$port -> $impl\n" if $cls =~ /'"$STUB_REGEX"'/;
  }
')

# 4. Allow via comentário em prod.py
if [[ -n "$VIOLATIONS" ]]; then
  ALLOW=$(grep -E "^#\s*port-binding:\s*empty-allowed\s*--\s*.{10,}" \
    "${PROJECT_DIR_NORM}/config/settings/prod.py" || true)
  if [[ -z "$ALLOW" ]]; then
    echo "BLOQUEIO: PORT_BINDINGS em prod com stub:" >&2
    echo "$VIOLATIONS" >&2
    exit 1
  fi
fi
exit 0
```

**Casos do `_test-runner.sh` (mínimo 5, não 4):**
1. prod.py com `OSQueryService -> EmptyOSQueryService` SEM comentário → bloqueia (exit 1).
2. prod.py com `OSQueryService -> EmptyOSQueryService` COM `# port-binding: empty-allowed -- módulo os entra Wave A late` → passa.
3. prod.py com `OSQueryService -> PostgresOSQueryService` → passa.
4. prod.py com `OSQueryService -> OSQueryServiceStub` → bloqueia (regex `Stub$`).
5. settings com import error / sintaxe quebrada → exit 2 (warning, não bloqueia commit pra não criar deadlock — escalation pra dev).

### 6. MÉDIA — Service worker do PWA: cache estratégia precisa ser explícita

**Problema:** plano (T-EQP-035) menciona service worker mas não a estratégia. O risco real: cachear `/v1/qr/{hash}` por engano = atacante força um payload, navega offline, mostra dado obsoleto de outro equipamento. **Resolução de hash NUNCA pode ser cacheada** — nem com `Cache-Control: private` (service worker ignora HTTP cache directives se a estratégia for `cache-first`).

**Correção exigida — `service-worker.js`:**

```javascript
// Strategy: cache-first APENAS para assets estáticos do scanner;
// network-only para API.
const STATIC_CACHE = 'afere-scanner-v1';
const STATIC_ASSETS = [
  '/equipamentos/scanner/',
  '/equipamentos/scanner/scanner.js',
  '/equipamentos/scanner/jsQR.min.js',
  '/equipamentos/scanner/manifest.json',
  // NÃO incluir /v1/qr/* aqui.
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(STATIC_CACHE).then(c => c.addAll(STATIC_ASSETS)));
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // Resolução de hash: SEMPRE network. Nunca cachear.
  if (url.pathname.startsWith('/v1/qr/') || url.pathname.startsWith('/v1/equipamentos/')) {
    e.respondWith(fetch(e.request));  // sem fallback offline — falha aberta.
    return;
  }
  // Static: cache-first.
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
```

**Adicionar a T-EQP-036:**
- `test_service_worker_nao_cacheia_endpoint_qr` — robô (Playwright headless ou puppeteer simples) instala o SW, dispara `fetch('/v1/qr/abc')`, inspeciona `caches.keys()` e confirma que nenhum cache tem entrada com prefix `/v1/qr/`.

**`manifest.json` mínimo:**

```json
{
  "name": "Aferê Scanner",
  "short_name": "Aferê",
  "start_url": "/equipamentos/scanner/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#0066cc",
  "icons": [
    {"src": "/static/scanner/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/static/scanner/icon-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}
```

**Nota Lighthouse PWA ≥90 (ADR-0018):** requer `start_url` acessível offline (cacheado), HTTPS, manifest válido, theme_color, e ícones 192+512. Documentar em `docs/operacao/runbooks-pwa-scanner.md` (já listado pra criar em T-EQP-037).

---

## Pontos fortes do plano

- Sequência `T-EQP-027..037` bem fatiada; cada task ≤ 1 commit.
- Reconhece tensão "p95 vs cache" e segue corretamente RBC C5 (medir antes).
- Aproveita audit_trail com hash salgado por tenant (INV-AUTHZ-002 cumprida) em vez de IP em claro.
- Não tenta antecipar Flutter; PWA é entrega permanente, não descartável (memória `feedback_sem_codigo_descartavel` honrada).
- Non-goals claros (sem Flutter, sem A3 real, sem OS real).

---

## Recomendação operacional

1. Aplicar as 6 ressalvas no plano antes de `/tasks`. As três críticas (1, 2, 3) **bloqueiam `/implement`**; as três altas/médias (4, 5, 6) podem entrar como sub-tasks dentro de T-EQP-035/036/030 sem reabrir o plano.
2. **Decisão Roldão necessária na ressalva 1**: adoção de Redis agora (recomendação minha) vs PG-backed pro Marco 2. Custo de adiar: reescrever rate limit + sessão + cache em Wave B = ~3 dias-agente. Custo de adotar agora: 1 container docker-compose + 4 linhas settings = ~2h-agente.
3. Após `/implement`, invocar auditor de Segurança (foco em timing oracle + indistinguibilidade 404 + service worker não-cacheando QR) + auditor de Qualidade (benchmark p95 ativo, não vácuo).

---

## Limites de honestidade

- **Confiante (li código real):** ressalvas 1 (sem Redis em `pyproject.toml`, `LocMemCache` em `base.py:211`), 3 (padrão Django de `Http404`), 5 (fix recente em `authz-check.sh` por backslash).
- **Suspeita não-provada empiricamente:** ressalva 2 — timing oracle real depende de medir distribuição em prod sob load; meu cálculo do `TIMING_TARGET_MS` é heurístico. Pentest externo (R-065 — recomendação Auditor 5) é quem fecha esse risco de verdade. Recomendo cravar isso como aceite condicional: "ASVS Level 2 verde por pentest humano antes do 1º tenant pago" — já está implícito mas não está no plano.
- **Fora do meu alcance:** validação UX da tela explicativa do PWA (texto, ícones, acessibilidade WCAG) — escalar `advogado-saas-regulado` pra aceite LGPD + Roldão pra texto final.
