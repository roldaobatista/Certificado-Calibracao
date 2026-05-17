---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Arquitetura — overview

> **Pra quê:** code map de alto nível pra agente novo (Claude/Codex) entender em ≤ 5 min o que tem onde. Atualizar conforme código existir.

---

## 1. Stack (ADR-0001 candidata)

| Camada | Tecnologia |
|--------|------------|
| Backend | Django 5.x LTS + DRF |
| Banco | PostgreSQL 16+ com RLS |
| Filas | procrastinate (Python sobre PG) + Celery secundário |
| Cache | Redis 7 |
| Frontend web | Django templates + HTMX + Alpine.js + Tailwind |
| Mobile | Flutter 3.x + drift + Riverpod |
| KMS | AWS KMS Multi-Region (sa-east-1 ↔ us-east-1) |
| Storage | Backblaze B2 EU Central (WORM) |
| Hospedagem | Hostinger VPS KVM 4 SP/BR (deploy ⏸️ dormente) |
| LLM gateway | LiteLLM self-hosted |
| Observabilidade | OpenTelemetry → Grafana Cloud + Axiom |

---

## 2. Layout de pastas (quando código existir)

```
afere/                          # repo
├── apps/                       # módulos de domínio (Django apps)
│   ├── tenant/                 # multi-tenant + RLS middleware (F-A)
│   ├── auth_app/               # auth + RBAC (F-B)
│   ├── cliente/                # cliente master (F-C, BIG-07)
│   ├── os/                     # Ordens de Serviço (Wave A)
│   ├── calibracao/             # certificado, cálculo incerteza (Wave A)
│   ├── fiscal/                 # NFS-e via PlugNotas (Wave A)
│   ├── financeiro/             # contas a receber + conciliação (Wave A)
│   └── ...
├── domain/                     # camada de domínio pura (sem Django ORM)
│   ├── certificado/
│   ├── incerteza/
│   └── ...
├── infrastructure/             # adapters (anti-corrosion layer — 9 portas)
│   ├── fiscal/                 # FiscalProvider (PlugNotas, Focus)
│   ├── signature/              # SignatureProvider (Lacuna, pyhanko)
│   ├── llm/                    # LLMGateway (LiteLLM)
│   ├── storage/                # StorageProvider (B2, S3)
│   ├── hosting/                # HostingProvider (Hostinger, Magalu)
│   ├── auth/                   # AuthProvider (allauth, OTP)
│   ├── queue/                  # QueueProvider (procrastinate, Celery)
│   ├── sync/                   # SyncProvider (offline mobile)
│   └── multitenant/            # TenantDiscriminator
├── interfaces/                 # entrada
│   ├── api/                    # DRF (mobile + integrações)
│   ├── web/                    # Django views + HTMX
│   ├── admin/                  # Django admin customizado
│   └── mobile/                 # Flutter (repo separado quando F-D começar)
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── migrations/                 # Django migrations
├── docker-compose.yml          # ambiente local
├── pyproject.toml              # Poetry deps
└── manage.py
```

Detalhes em [anti-corrosion-layer.md](anti-corrosion-layer.md).

---

## 3. Entry points (quando código existir)

| Entry | Acesso |
|-------|--------|
| `manage.py runserver` | Django dev local |
| `manage.py shell_plus` | REPL com models carregados |
| `manage.py migrate` | aplicar migrations |
| `procrastinate worker` | worker de fila |
| `docker compose up` | stack completa local |
| `pytest` | suite de testes |

---

## 4. Camadas e dependências

```
┌────────────────────────────────────┐
│  interfaces/ (api, web, admin)     │  ← entrada
└─────────┬──────────────────────────┘
          │ chama
          ▼
┌────────────────────────────────────┐
│  apps/<modulo>/ (Django apps)      │  ← orquestração / use cases
└─────────┬──────────────────────────┘
          │ usa
          ▼
┌────────────────────────────────────┐
│  domain/ (regras puras)            │  ← núcleo (sem Django)
└─────────┬──────────────────────────┘
          │ depende de
          ▼
┌────────────────────────────────────┐
│  infrastructure/ (anti-corrosion)  │  ← saída pro mundo externo
└────────────────────────────────────┘
```

**Regra:** `domain/` NÃO importa `apps/` nem `infrastructure/`. `infrastructure/` NÃO importa `apps/`. Linter custom (semgrep) enforce.

---

## 5. Multi-tenant em todas as camadas

- **interfaces:** middleware Django injeta `tenant_id` na sessão a cada request
- **apps:** managers customizados filtram por `tenant_id` automaticamente
- **domain:** entidades carregam `tenant_id` como atributo
- **infrastructure:** porta `MultiTenantDiscriminator` aplica RLS no banco

Detalhes em `docs/comum/isolamento-multi-tenant.md`.

---

## 6. Cross-cutting (8 docs separados)

Cada um detalha política transversal:
- [erro.md](cross-cutting/erro.md) — categorias, handling, retries
- [log.md](cross-cutting/log.md) — formato estruturado + tenant_id
- [retry.md](cross-cutting/retry.md) — backoff, jitter, deadletter
- [timeout.md](cross-cutting/timeout.md) — propagação + cancelamento
- [idempotencia.md](cross-cutting/idempotencia.md) — chave + replay seguro
- [transacao.md](cross-cutting/transacao.md) — boundary, isolation level
- [auth-rbac.md](cross-cutting/auth-rbac.md) — papéis, permissões, MFA
- [validacao.md](cross-cutting/validacao.md) — Pydantic + DRF serializer

---

## 7. Integrações externas

- [comum/integracoes-externas/](../comum/integracoes-externas/) — 1 doc por parceiro (a criar)
- [seguranca/mcp-policy.md](../seguranca/mcp-policy.md) — MCP servers

---

## 8. Boundaries — onde uma mudança "vaza" pra outro módulo

| De → Para | Como |
|-----------|------|
| `os/` → `calibracao/` | OS gera certificado: evento `OSConcluida` → handler em `calibracao/` cria certificado rascunho |
| `calibracao/` → `fiscal/` | Após emitir certificado, evento opcional `CertificadoEmitido` dispara NFS-e |
| `fiscal/` → `financeiro/` | NFS-e emitida vira lançamento em contas a receber |
| `cliente/` → todos | Cliente é referenciado em quase tudo; mudança em modelo de cliente é breaking change |

Eventos em [comum/integracoes-inter-modulos.md](../comum/integracoes-inter-modulos.md).

---

## 9. Pré-código (estado atual)

Pasta `apps/`, `domain/`, `infrastructure/`, `interfaces/` ainda não existem. Foundation F-A criará a estrutura básica.

Layout aqui é **proposta** — refinar conforme código existe. Atualizar este doc a cada release minor.
