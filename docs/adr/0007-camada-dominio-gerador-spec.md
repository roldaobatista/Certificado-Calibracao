# ADR-0007 — Camada de domínio + gerador spec→código

> **Status:** rascunho (17/05/2026) — bloqueante do Portão 2 da ADR-0001
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Parecer 6 da 2ª auditoria de 10 agentes — Django ORM + DRF serializer + Pydantic + Dart = 4 representações do mesmo conceito que divergem em 2 sprints sem gerador. Spec-as-source (D2) precisa de pipeline real, não de promessa.
> **Depende de:** ADR-0001 v2 (stack Django + Flutter)

---

## Contexto

Decisão fundadora D2 diz "spec PT é a verdade; código segue a spec". Sem ferramenta concreta, agentes IA escrevem as 4 representações (model, serializer, Pydantic boundary, Dart class) manualmente — em 2 sprints divergem. Invariantes (INV-NNN) viram `if` espalhado em `save()` ao invés de método de agregado testável.

---

## Decisão (rascunho — a fechar)

### Pipeline spec → código

1. **Spec PT** em markdown com IDs estáveis (INV-NNN, agregado, campos, invariantes, transições de estado).
2. **YAML/JSON intermediário** extraído por `tools/spec-extract/` (parser markdown→YAML).
3. **Gerador `make spec-sync`** cascateia:
   - Migration Django draft
   - dataclass de domínio (sem dependência de ORM)
   - DRF serializer
   - drf-spectacular regenera OpenAPI
   - openapi-generator gera Dart client + drift schema mobile
   - factory-boy fixtures iniciais
4. **CI bloqueia merge** se spec mudou e gerados não regeneraram.

### Camada de domínio

- **`domain/`** separada de `models/` (Django) — dataclass + métodos de agregado.
- **Invariantes em 3 camadas obrigatórias:**
  - `CHECK`/`EXCLUSION`/RLS no banco pra dado-dependente (INV-011, INV-TENANT-003, INV-015)
  - Método `assert_invariant_*()` no agregado pra regra-comportamento (INV-007 imutabilidade)
  - Teste pytest que cita o ID (TST-004)
- **Pydantic** é só boundary de I/O (HTTP, LLM), não lar de invariante.

### Eventos de domínio

- **Message bus explícito** (`domain.events.emit("OSEncerrada", payload)`) consumido por Celery tasks.
- **Django signals proibidos por default** — override exige hook + decorator + revisão.

---

## Itens a fazer
- [ ] `tools/spec-extract/` parser markdown→YAML
- [ ] Templates Jinja pra gerar Django/Pydantic/Dart a partir do YAML
- [ ] `make spec-sync` + hook CI
- [ ] Domain layer scaffold + repository pattern
- [ ] Message bus + registry de eventos
- [ ] Documentação `docs/arquitetura/spec-as-source-pipeline.md`

---

## Aprovação
- [ ] Roldão — pendente
- [ ] Auditor de qualidade (Família 5) — pendente
