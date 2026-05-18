---
owner: tech-lead-saas-regulado
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: stable
diataxis: reference
audiencia: agente
relacionados:
  - docs/adr/0001-stack.md
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - REGRAS-INEGOCIAVEIS.md
---

# Convenções Django — como escrever código neste projeto

> **Pra quê:** agentes IA diferentes a cada sessão tendem a reinventar estilo. Sem trilho, o código apodrece em 2 sprints (Parecer 6 da auditoria). Este doc é o trilho mínimo.
>
> **Status:** stable em F-A. Wave A pode adicionar mais regras conforme padrões emergem.

---

## Princípios

1. **Spec PT é a verdade.** Modelo Django segue a spec, não o contrário. Marcou conflito → spec vence; reabra a spec se ela estiver errada.
2. **Domain code não conhece Django.** `src/domain/` importa só `dataclasses`, `typing`, `uuid`, std lib. Zero `from django.*`.
3. **Use cases em `src/application/`** recebem `Repository` (Protocol) + `EventBus` (Protocol) via injeção de dependência. Nunca importam de `infrastructure/`.
4. **Adapters em `src/infrastructure/`** implementam os Protocols. É onde Django vive (ORM, signals — quando justificado, middleware, serializer DRF, admin).

---

## Idioma

- **Tudo em PT-BR:** nomes de variável, classe, método, app_label, db_table, comentário, docstring, migration name. Ex: `class Auditoria`, não `class Audit`.
- **Exceções (7 arquivos lidos por ferramenta):** `README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODEOWNERS`, `.env.example`. Conteúdo deles também em PT, mas nome é EN porque ferramentas (GitHub, Dependabot) procuram por nome.
- **Nomes técnicos consagrados** (`Tenant`, `RLS`, `JWT`, `OAuth`, `UUID`) ficam em EN — não traduza. Use no contexto correto.

---

## Estrutura de pastas

```
src/
├── domain/                     # PURO (sem Django)
│   ├── <bounded-context>/
│   │   ├── agregado.py         # Entidade(s) + metodos
│   │   ├── invariantes.py      # assert_inv_NNN()
│   │   ├── eventos.py          # DomainEvent subclasses
│   │   └── repository.py       # Protocol — sem implementacao
│   └── shared/                 # events, value_objects, invariantes base
│
├── infrastructure/             # Adapters Django/Postgres/Celery
│   ├── <bounded-context>/
│   │   ├── apps.py             # AppConfig com label = nome curto
│   │   ├── models.py           # Django Model + Manager + Meta.db_table
│   │   ├── admin.py            # ModelAdmin (readonly em audit + sensiveis)
│   │   ├── serializers.py      # DRF (gerados em Wave A via codegen ADR-0007)
│   │   ├── views.py            # DRF ViewSet (com AuthorizationProvider.can())
│   │   ├── repositories.py     # implementacao Django do Protocol
│   │   ├── tasks.py            # Procrastinate tasks
│   │   └── migrations/
│   ├── multitenant/            # middleware, RLS, router, context vars
│   ├── audit/                  # canonicalizar, hash_chain, services, tasks
│   └── eventbus/               # adapter Procrastinate do EventBus
│
└── application/                # Use cases
    └── <bounded-context>/
        └── <verbo>_<recurso>.py  # ex: emitir_certificado.py
```

---

## Models

### Nomes
- Classe singular: `Tenant`, `Usuario`, `Auditoria` (substantivo).
- `app_label` curto: `tenant`, `usuario`, `audit`, `feature_flag`.
- `db_table` plural em snake: `tenants`, `usuarios`, `auditoria`, `feature_flags`.
- FK explícito + `related_name` em PT: `related_name="auditoria"`.

### Campos
- **PK UUID** em toda tabela (defesa anti enumeração + facilita migration entre bancos):
  ```python
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  ```
- **`tenant_id` obrigatório** em toda tabela com dados de cliente (INV-TENANT-002). Tabelas SHARED (`tenants`, `usuarios`) marcam-se como tal no docstring do modelo.
- **`criado_em` + `atualizado_em`** sempre que faz sentido (com `auto_now_add` / `auto_now`).
- **`status_*` choices via `TextChoices`** (não strings soltas).

### Proibido
- **Lógica de negócio em `Model.save()`** — vai pra `application/` use case.
- **Django signals para regra de negócio** — usa `EventBus` (Protocol). Override exige decorator `@signal_allowed` + revisão Auditor 2.
- **`null=True` em `CharField`/`TextField`** — usar `default=""` (evita 3 estados).

### Obrigatório
- **`Meta.db_table` explícito** — não confiar na convenção `<app>_<modelo>`.
- **`Meta.indexes`** quando query padrão pesar > 50ms estimado.
- **`Meta.constraints`** (UniqueConstraint, CheckConstraint) — banco força integridade.

---

## Queries

### Obrigatório
- **`select_related`** pra FK lidos no template/serializer (evita N+1).
- **`prefetch_related`** pra M:N e reverse FK.
- **Sempre via Manager customizado** (Wave A vai introduzir `TenantManager` que injeta filtro tenant_id; F-A usa `.objects` normal sob middleware).

### Proibido
- **`Model.objects.all()`** em código de aplicação (hook `tenant-id-validator` bloqueia).
- **`.raw()` / `connection.cursor()`** fora de `src/infrastructure/multitenant/` ou `src/infrastructure/audit/services.py` (hook bloqueia futuramente).
- **`get()` sem `try/except Model.DoesNotExist`** ou `select_for_update` — use `.first()` + `if`.

---

## Multi-tenancy

### Em **todo** use case que toca tabela com `tenant_id`:
```python
with run_in_tenant_context(tenant_id=request.user.active_tenant_id, usuario_id=request.user.id):
    # queries aqui dentro tem RLS aplicada
    ...
```

### Em **toda** task Procrastinate/Celery:
```python
@procrastinate_app.task
def minha_task(tenant_id: str, usuario_id: str, ...):
    with run_in_tenant_context(UUID(tenant_id), UUID(usuario_id)):
        ...
```

### **Nunca** salvar `tenant_id` vindo do cliente direto:
- INSERT em tabela com RLS força `tenant_id = current_setting('app.active_tenant_id')` via policy WITH CHECK.
- Cliente passa `tenant_id` no header `X-Afere-Active-Tenant` apenas pra middleware validar que está na LISTA permitida — depois disso o sistema usa o que setou no PG.

---

## Audit trail

### Obrigatório em ações sensíveis:
```python
from src.infrastructure.audit.services import registrar_auditoria

registrar_auditoria(
    tenant_id=tenant.id,
    usuario_id=usuario.id,
    action="certificado.emitido",
    resource_summary=f"Certificado #{cert.numero}",
    payload={"certificado_id": str(cert.id), "valor": Decimal("123.45")},
)
```

### **Quais ações exigem audit:**
- Mudança em dados regulados (certificados, NFS-e, calibrações).
- Mudança em permissões (UsuarioPerfilTenant criada/expirada/revogada).
- Acesso a dado sensível LGPD (CPF, conta bancária).
- Provisioning de tenant / mudança de plano.
- Cancelamento / suspensão de tenant.

### **Proibido:**
- Editar/deletar linha existente — modelo bloqueia em Python (Marco 2) + trigger PG bloqueia (Marco 4) + hook pre-commit bloqueia DROP TRIGGER (Marco 5).
- `payload` com `datetime` naive (sem timezone) — `ValueError` fail-loud.
- Adicionar campos sensíveis (senha, token) direto no `payload`.

---

## Testes

### Markers obrigatórios:
- `@pytest.mark.django_db` em qualquer teste que usa modelo.
- `@pytest.mark.django_db(transaction=True)` quando exercita advisory lock / RLS (precisa commits reais).
- `@pytest.mark.tenant_isolation` em testes que exigem PG vivo + RLS aplicada (não rodam no harness IA).
- `@pytest.mark.slow` em fuzzing / drill / testes > 5s.

### Convenções:
- **Nomes descrevem CENÁRIO + RESULTADO**: `def test_usuario_sem_perfil_em_tenant_recebe_403`.
- **Arrange/Act/Assert** explícito (linhas em branco separando).
- **Factories** em `tests/factories.py` (factory-boy) — nunca instancie modelo direto em teste.
- **Cobertura mínima 80%** (configurada em `pyproject.toml` `[tool.pytest.ini_options]`).

### Proibido (TST-001/002/003):
- `assert True` / `assert 1 == 1` / `assertTrue(true)` — mascaramento, hook bloqueia.
- `pytest.skip()` sem comentário no formato `# skip YYYY-MM-DD (Nome) — motivo`.
- `# noqa` / `# type: ignore` sem justificativa de >=10 caracteres na mesma linha.

---

## Imports

Ordem (ruff configura via `[tool.ruff.lint]`):
1. Std lib (`from __future__ import annotations` primeiro)
2. 3rd party (`django`, `rest_framework`)
3. Local (`src.domain.*`, `src.infrastructure.*`, `src.application.*`)
4. Tests fixtures

```python
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from django.db import models
from rest_framework import serializers

from src.domain.shared.events import DomainEvent
from src.infrastructure.tenant.models import Tenant
```

---

## Migrations

- **Geradas via `makemigrations`** (não escrever à mão exceto pra RunSQL específicas tipo RLS).
- **Nome descritivo:** `0042_add_assinatura_certificado.py`, não `0042_auto_20260517_1430.py`.
- **Toda tabela com `tenant_id` exige `CREATE POLICY` na mesma migration OU em migration referenciada** via comentário `# rls-policy: external NNNN_setup`. Hook `migration-rls-check` força.
- **Migration destrutiva** (DROP COLUMN, DROP TABLE) exige aprovação Roldão (Caso-limite 1 — `docs/governanca/limites-autonomia.md`).

---

## DRF views (Wave A em diante)

### Obrigatório em todo endpoint:
```python
from rest_framework.viewsets import ModelViewSet

class CertificadoViewSet(ModelViewSet):
    serializer_class = CertificadoSerializer

    def get_queryset(self):
        # RLS aplica automaticamente via middleware
        return Certificado.objects.select_related("instrumento")

    def perform_create(self, serializer):
        # Marco F-B: AuthorizationProvider.can() obrigatorio aqui
        decision = authz.can(
            user_id=self.request.user.id,
            action="certificado.emitir",
            resource="certificado",
            tenant_id=active_tenant_context.get(),
            purpose="emissao_normal",
        )
        if not decision.allowed:
            raise PermissionDenied(decision.reason)
        serializer.save(tenant_id=active_tenant_context.get())
```

### Hook `authz-check` bloqueia:
- ViewSet sem `AuthorizationProvider.can()` em métodos write.
- Endpoint público sem `permission_classes=[AllowAny]` explícito.
- Override raro com `# authz-check: skip` + justificativa.

---

## Comandos curtos

| Operação | Comando |
|---|---|
| Format + lint | `poetry run ruff check . && poetry run ruff format .` |
| Type-check | `poetry run mypy src config` |
| Testes rápidos | `poetry run pytest -m "not tenant_isolation"` |
| Testes E2E | `poetry run pytest -m tenant_isolation` |
| Nova migration | `poetry run python manage.py makemigrations <app>` |
| Aplicar migration | `poetry run python manage.py migrate --database=migrator` |
| Shell + auto-import | `poetry run python manage.py shell_plus` |
| Validar hooks | `bash .claude/hooks/_test-runner.sh` |
