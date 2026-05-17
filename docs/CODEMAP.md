---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# CODEMAP ⚪ (lazy — preencher quando código existir)

> **Pra quê:** mapa navegável do código-fonte. Substitui "abrir o IDE e procurar". Atualização automatizada quando módulo entra em produção.
>
> **Status:** ⚪ lazy — só faz sentido quando Foundation F-A existir. Gerado a partir de `docs/dominios/*/modulos/*/` + `apps/*/` (Django apps) + análise estática.

---

## Estrutura projetada (quando código existir)

```
afere/
├── apps/<modulo>/         ← cada módulo Django
│   ├── models.py          ← entities + tenant_id
│   ├── views.py / serializers.py
│   ├── usecases/          ← lógica de aplicação
│   ├── tasks.py           ← procrastinate jobs
│   └── tests/
├── domain/<bounded-context>/  ← regras puras
├── infrastructure/        ← anti-corrosion layer (9 portas)
└── interfaces/            ← api/web/admin/mobile
```

Detalhamento em `docs/arquitetura/overview.md`.

---

## Como manter (quando ativar)

1. Pre-commit hook gera `CODEMAP.md` automaticamente:
   - Lista pastas `apps/*/`
   - Lista models por módulo
   - Lista endpoints por módulo
   - Lista jobs procrastinate
2. Auditor Produto verifica que novo módulo tem entrada
3. Roldão lê pra ter mapa em 30s do que existe

---

Quando ativar este doc: Foundation F-A começar.
