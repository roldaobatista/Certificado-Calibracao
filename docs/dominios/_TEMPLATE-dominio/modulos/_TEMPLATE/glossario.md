---
owner: roldao
revisado_em: 2026-05-16
proximo_review: 2026-08-16
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
---

# Glossário do módulo [NOME] (TEMPLATE)

> Termos **específicos** deste módulo. Termos transversais ficam em `docs/comum/glossario.md`.
>
> **Regra anti-duplicação:** hook valida que termo aqui NÃO duplica termo do glossário comum com sentido diferente.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem (norma/spec) |
|---|---|---|---|---|
| [termo-1] | [definição clara] | [outros nomes que NÃO usar] | [tradução pro Roldão] | [norma técnica / ADR / US] |
| [termo-2] | | | | |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar se conflita com glossário comum (hook valida).
- Termo descontinuado → marcar `@deprecated` + janela de migração 3 meses.
- Mudança de definição → bump no CHANGELOG seção "Modificado" + aviso.

## Convenções

- Termos em PT-BR. Quando termo técnico-original em inglês for inevitável (ex: "tenant", "ticket"), incluir tradução de campo na coluna "Se vir na tela/log...".
- Definição em 1 linha. Se precisar mais, criar entrada em `docs/explicacoes/<termo>.md`.
- Origem obrigatória pra termos regulados (ISO, NBR, RBC, LGPD, etc.).
