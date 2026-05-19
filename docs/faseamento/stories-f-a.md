---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: deprecated
diataxis: reference
audiencia: agente
substituido_por: docs/faseamento/F-A/spec.md
relacionados:
  - docs/faseamento-foundation-waves.md
  - docs/governanca/debitos-ritual.md
  - docs/adr/0001-stack.md
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
---

# Stories retrospectivas Foundation F-A

> **Pra quê:** F-A foi entregue como 8 marcos técnicos sem ritual Spec Kit. Este arquivo mapeia retroativamente cada marco em uma Story `US-FA-NNN` com ACs binários, pra rastreabilidade auditorial (Constituição §6 — IDs rastreáveis).
>
> Os critérios de saída automáveis da F-A (`docs/faseamento-foundation-waves.md` §2) viraram os ACs. Drill `validar_f_a` valida em massa (5/5 verde em 2026-05-18).

---

## US-FA-001: Esqueleto Django + DRF + PostgreSQL 16 rodando local
**Como** orquestrador F-A, **quero** Django 5.0 LTS + DRF + PG16 + Poetry + Docker Compose subir com 1 comando, **para** ter ambiente reproduzível antes de inserir lógica.

- **AC-FA-001-1**: `docker compose up -d` levanta containers `afere-db` (PG16) + `afere-app` (Python 3.12 + Django 5.0) sem erro.
- **AC-FA-001-2**: `manage.py check` passa sem warnings de configuração.
- **AC-FA-001-3**: `/healthz/` responde 200 com payload JSON.

**Tasks executadas:** T-FA-001 (Dockerfile + compose), T-FA-002 (settings base/dev/prod), T-FA-003 (manage.py + urls), T-FA-004 (Poetry pyproject.toml).
**Commit referência:** `20e79c7`.

---

## US-FA-002: 4 tabelas-núcleo modeladas e migradas
**Como** orquestrador F-A, **quero** as entidades `Tenant`, `Usuario`, `Auditoria`, `FeatureFlag` criadas com migrations Django, **para** sustentar o resto do sistema multi-tenant.

- **AC-FA-002-1**: `Tenant` com (id UUID, slug unique, nome_fantasia, plano, status_lifecycle, criado_em).
- **AC-FA-002-2**: `Usuario` (AbstractBaseUser custom) com email como USERNAME_FIELD + flag `mfa_obrigatorio` + tabela M:N `UsuarioPerfilTenant` com `valido_de/ate`.
- **AC-FA-002-3**: `Auditoria` com hash chain (campos `hash_anterior`, `hash_atual`).
- **AC-FA-002-4**: `FeatureFlag` (tenant_id, modulo, feature_key, ativo, fonte enum).
- **AC-FA-002-5**: `manage.py migrate --database=migrator` aplica sem erro.

**Tasks executadas:** T-FA-005 a T-FA-008 (uma por modelo).
**Commit referência:** `60263ac`.

---

## US-FA-003: Multi-tenancy operacional (middleware + RLS + roles)
**Como** sistema, **quero** isolamento entre tenants forçado em duas camadas (middleware Django injeta `tenant_id` + PG RLS bloqueia query cruzada), **para** garantir que vazamento cross-tenant é impossível mesmo com bug de aplicação.

- **AC-FA-003-1**: `TenantMiddleware` extrai `tenant_id` do header `X-Afere-Active-Tenant` + valida que está na lista do `UsuarioPerfilTenant` do usuário.
- **AC-FA-003-2**: Role PG `app_user` é `NOBYPASSRLS NOSUPERUSER` (INV-TENANT-004). Role `app_migrator` separada também NOBYPASSRLS.
- **AC-FA-003-3**: Policy RLS em todas tabelas com `tenant_id` usando pattern `ANY(string_to_array(current_setting('app.tenant_ids'), ','))` (INV-AUTHZ-003 já no shape correto).
- **AC-FA-003-4**: Wrapper `run_in_tenant(tenant_id, fn)` disponível pra tasks Celery/Procrastinate fora de request HTTP.

**Tasks executadas:** T-FA-009 a T-FA-014.
**Commit referência:** `8b286cd`.

---

## US-FA-004: Audit trail síncrono com hash chain + trigger PG
**Como** sistema, **quero** trilha de auditoria INSERT-only com hash encadeado e trigger PG bloqueando UPDATE/DELETE, **para** atender INV-001 (rastreabilidade imutável) + ANPD/Cgcre.

- **AC-FA-004-1**: Cada linha de `auditoria` tem `hash_atual = sha256(hash_anterior || canonicalizar(payload))`.
- **AC-FA-004-2**: Trigger PG `auditoria_anti_update` + `auditoria_anti_delete` rejeitam mutação com `RAISE EXCEPTION` (errcode 23514).
- **AC-FA-004-3**: Drill executa fuzzing 50×100 e detecta zero quebra de chain.
- **AC-FA-004-4**: Job Celery agendado pra export hourly stub (destino B2 entra em Wave A).

**Tasks executadas:** T-FA-015 a T-FA-018.
**Commit referência:** `97ef55b`.

---

## US-FA-005: Hooks `migration-rls-check` + `audit-immutability-check`
**Como** orquestrador F-A, **quero** hook pre-commit que bloqueie qualquer migration que crie tabela com `tenant_id` sem CREATE POLICY na mesma migration, e outro que detecte DROP TRIGGER em auditoria, **para** previnir bug regulatório em pre-commit (princípio da Regra mestre 1).

- **AC-FA-005-1**: `migration-rls-check.sh` rejeita migration sem `ENABLE ROW LEVEL SECURITY` quando detecta `tenant_id` na CreateModel/AddField.
- **AC-FA-005-2**: `audit-immutability-check.sh` rejeita DROP TRIGGER `auditoria_anti_*`, DROP FUNCTION `auditoria_bloqueia_mutation`, ALTER TABLE auditoria DISABLE RLS, TRUNCATE/DELETE/UPDATE em auditoria.
- **AC-FA-005-3**: Allowlist `# rls-policy: external NNNN` permite policy em migration separada com justificativa.
- **AC-FA-005-4**: `_test-runner.sh` cobre os 2 hooks com cenários happy + unhappy.

**Tasks executadas:** T-FA-019, T-FA-020.
**Commit referência:** `d2f5edc`.

---

## US-FA-006: Suite de testes pytest + fuzzing 50×100
**Como** orquestrador F-A, **quero** suite pytest com factories + fuzzing concurrent 50 threads × 100 queries cruzando tenants, **para** provar empíricamente que RLS não vaza.

- **AC-FA-006-1**: pytest-django + factory-boy configurados; `tests/conftest.py` + `tests/factories.py` rodam.
- **AC-FA-006-2**: Suite passa com 58 tests + 1 skipped.
- **AC-FA-006-3**: Fuzzing 50 threads × 100 queries injeta queries cross-tenant; zero vazamento detectado.
- **AC-FA-006-4**: pytest-cov instalado; cobertura HTML em `reports/coverage/index.html`.

**Tasks executadas:** T-FA-021 a T-FA-025.
**Commit referência:** `b22afae`.

---

## US-FA-007: Convenções django (`docs/arquitetura/django-convencoes.md`)
**Como** orquestrador do projeto, **quero** doc canônico com regras de naming + estrutura de pastas + uso de signals + select_related + serializers, **para** que agentes futuros não reinventem estilo a cada sessão.

- **AC-FA-007-1**: Doc lista naming PT-BR, app_label curto, db_table plural, related_name PT, signals proibidos por default.
- **AC-FA-007-2**: Doc define estrutura `src/domain/` (puro) + `src/infrastructure/<bounded-context>/` (Django) + `src/application/` (use cases).
- **AC-FA-007-3**: Doc fica em `docs/arquitetura/django-convencoes.md` com frontmatter `status: stable`.

**Tasks executadas:** T-FA-026, T-FA-027.
**Commit referência:** `f323379`.

---

## US-FA-008: Drill F-A automático (`validar_f_a` management command)
**Como** orquestrador, **quero** comando Django que rode os 5 critérios automáveis da F-A e produza tabela visual de PASS/FAIL, **para** validar fase em 1 comando.

- **AC-FA-008-1**: `manage.py validar_f_a` roda hooks `_test-runner.sh`, verifica NOBYPASSRLS, trigger anti-mutation, hash chain íntegra, p99 < 200ms.
- **AC-FA-008-2**: Output em tabela: 5/5 [OK] ao final.
- **AC-FA-008-3**: Exit 0 se tudo verde; exit 1 se algum falhar.
- **AC-FA-008-4**: Drill restore PG executado: dump + restore em 2,52s (limite 30min).

**Tasks executadas:** T-FA-028 a T-FA-031.
**Commit referência:** `4be9f3a`, `9fba126`, `83bf48b`.

---

## Auditoria retroativa

Auditores Família 5 (Qualidade + Segurança + Produto) rodados em 2026-05-18 sobre o código F-A entregue. Output em `docs/governanca/trilha-auditoria-agentes.md`.

**Drill `validar_f_a` em 2026-05-18 (canônico):** 5/5 critérios automáveis verde. Suite 58 passed + 1 skipped. Hooks 103/103.
