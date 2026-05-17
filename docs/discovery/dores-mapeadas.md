# Discovery — Dores mapeadas

> **Artefato Rodada 0** (agente sintetiza, a partir das entrevistas). Dores ranqueadas por **6 dimensões** (Auditor 6 v2):

---

## Métrica de priorização

Cada dor é avaliada em 6 dimensões:

| Dimensão | Pergunta | Escala |
|---|---|---|
| **Agudez** | Quão grave quando acontece? | 1 (incomoda) – 5 (paralisa empresa) |
| **Frequência** | Quantas vezes por mês? | <1 / 1–4 / 5–20 / >20 |
| **Disposição a pagar** | Cliente pagaria pra resolver? Quanto? | R$/mês auto-reportado (deflacionar 50%) |
| **Solvability** | Quão caro pra a gente resolver? | 1 (POC em 1 dia) – 5 (rewrite de meses) |
| **Reach** | Quantos clientes do TAM têm essa dor? | % estimado da amostra |
| **Evitabilidade** | Existe workaround manual aceitável hoje? | sim (baixa urgência) / não (alta urgência) |

**Score sugerido:** (Agudez × Frequência × Reach × DAP) ÷ (Solvability × Evitabilidade)

Ranking não é cego ao score — sempre justificar com citação literal da entrevista.

---

## Dores ranqueadas (a preencher)

### Dor #1: [título curto]
- **Agudez:** /5
- **Frequência:** /mês
- **DAP:** R$ /mês (auto-reportado: R$ — deflacionado)
- **Solvability:** /5
- **Reach:** % da amostra
- **Evitabilidade:** sim/não
- **Score:** XXX
- **Citações literais:**
  - "[entrevistado #1]: ..."
  - "[entrevistado #4]: ..."
- **Origem na jornada (`dominio-de-negocio.md`):** processo X, passo Y
- **Implicação pra MVP:** se score > N → forte candidato a MVP-1
- **Módulo onde resolveria:** [a definir]

### Dor #2 ...

---

## Por persona

| Persona | Top 3 dores | Score médio |
|---|---|---|
| Dono | ... | |
| Atendente | ... | |
| Técnico de campo | ... | |
| Financeiro | ... | |
| Metrologista | ... | |

## Por módulo provável

| Módulo | Dores relacionadas | Score acumulado |
|---|---|---|
| (a preencher quando módulos forem confirmados na sintese-final) | | |

---

## Saída esperada
- Top 5 dores prioritárias com score
- Recomendação de MVP-1 baseada em score (entra na `sintese-final.md`)
- Lista de dores fora de escopo (entra em `non-goals` do PRD futuro)
