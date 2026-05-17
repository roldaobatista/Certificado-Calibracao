---
owner: roldao
revisado_em: 2026-05-16
proximo_review: 2026-08-16
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/modelo-de-dominio.md
  - docs/comum/governanca-modelo-comum.md
---

# Modelo de domínio — Módulo [NOME] (TEMPLATE)

> Entidades **específicas** deste módulo (DDD light). Entidades transversais ficam em `docs/comum/modelo-de-dominio.md`.
>
> **Regra de fronteira:** ver `docs/comum/governanca-modelo-comum.md`. Hook valida não-duplicação.

---

## Entidades

### [Entidade A]
- **Atributos obrigatórios:** ...
- **Atributos opcionais:** ...
- **Invariantes de agregado:** `INV-NNN` (cite IDs)
- **Relacionamento com entidades comuns:** [extension table / JSONB / referência simples]
- **Ciclo de vida:** [criada quando / mutável quando / imutável após X / arquivada quando]

### [Entidade B]
(mesmo formato)

---

## Agregados (DDD)

| Agregado raiz | Entidades incluídas | Invariantes |
|---|---|---|
| [Agregado A] | [Entidade A, Entidade B] | `INV-NNN`, `INV-MMM` |

---

## Value Objects

| VO | Definição | Imutável? |
|---|---|---|
| [VO-1] | ... | Sim |

---

## Eventos de domínio (publicados)

> Eventos que outros módulos podem consumir. Ver `docs/comum/integracoes-inter-modulos.md` pra contrato detalhado.

| Evento | Quando dispara | Payload | Quem consome (módulos) |
|---|---|---|---|
| `[ModuloA].[EventoX]` | [condição] | `{...}` | [módulo Y, módulo Z] |

---

## Comandos (entradas no módulo)

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| `[criarX]` | API / UI / outro módulo | ... | ... |

---

## Schema físico

Ver `../schema-banco.md` (deste módulo) se separado, OU `../../../comum/schema-banco.md` se entidade é comum.

## Diagramas

(opcional — Mermaid permitido)

```mermaid
%%{ exemplo Diagrama de classes }%%
classDiagram
    [ClasseA] <|-- [ClasseB]
```

## Como este modelo evolui

- Entidade nova → adicionar + verificar fronteira comum/módulo (`governanca-modelo-comum.md`).
- Atributo novo → migration + bump no CHANGELOG.
- Entidade descontinuada → ADR + janela de migração.
