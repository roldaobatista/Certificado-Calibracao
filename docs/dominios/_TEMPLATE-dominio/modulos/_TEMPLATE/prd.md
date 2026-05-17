---
owner: roldao
revisado_em: 2026-05-16
proximo_review: 2026-08-16
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/[dominio]/README.md
---

# PRD — Módulo [NOME] (TEMPLATE)

> Product Requirements Document do módulo. Visão consolidada com user stories rastreáveis.
>
> **Não duplica** o `prd.md` raiz (que é visão do produto inteiro); este aprofunda o módulo.

---

## 1. O que este módulo é

[1–2 parágrafos. O que faz, pra quem, qual dor resolve. Cite jornada da persona.]

## 2. Por que este módulo existe (problema a resolver)

[Dor mapeada em `discovery/dores-mapeadas.md`. Cite ID da dor.]

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md` + `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- ...
- ...

## 5. Non-goals (o que NÃO está neste módulo)

> LLM não infere por omissão. Proibições positivas.

- ...
- ...

## 6. User Stories

### US-[MOD]-001: [Título curto da story]

**Como** [persona], **quero** [ação], **para** [valor de negócio].

**Critérios de aceite (Given-When-Then):**

- **AC-[MOD]-001-1**: GIVEN [contexto], WHEN [ação], THEN [resultado esperado].
- **AC-[MOD]-001-2**: ...

**Non-goals desta story:**
- ...

**Invariantes relacionadas:** `INV-NNN` (cite IDs de `REGRAS-INEGOCIAVEIS.md`)

**Dependências:**
- Bloqueia: US-...
- Bloqueado por: US-..., ADR-...

---

### US-[MOD]-002: ...

(mesmo formato)

---

## 7. Métricas de sucesso deste módulo

Ver `metricas.md`. Aqui só lista resumida:
- [Métrica primária] = [target]
- [Métrica secundária] = [target]

## 8. NFR (Requisitos Não-Funcionais)

- **Performance:** [target em ms / qps / etc.]
- **Disponibilidade:** [SLO específico do módulo — ver `../../../operacao/observabilidade.md`]
- **Segurança:** cita SEC-* aplicáveis
- **Acessibilidade:** [WCAG nível, se aplicável]

## 9. Glossário

Ver `glossario.md` deste módulo.

## 10. Como este PRD evolui

- US nova → adicionar com próximo ID livre (`US-[MOD]-NNN`).
- US deprecada → marcar `@deprecated` + ADR.
- Mudança em AC já implementado → ADR + novo teste.
