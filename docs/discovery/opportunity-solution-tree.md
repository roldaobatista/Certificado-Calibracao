# Discovery — Opportunity Solution Tree (OST)

> **Artefato Rodada 0** (Auditor 6 v2 — NOVO). Framework Teresa Torres (Continuous Discovery Habits). Hierarquia outcome → opportunities → solutions → experiments. Sem isso, dores viram lista plana sem prioridade clara.

---

## Estrutura

```
DESIRED OUTCOME
  ├─ Opportunity A (dor / job mapeado)
  │   ├─ Solution A1 (ideia de feature)
  │   │   └─ Experiment A1a (teste pequeno pra validar)
  │   └─ Solution A2
  └─ Opportunity B
      └─ Solution B1
          └─ Experiment B1a
```

---

## Outcome (objetivo de negócio)

> 1 outcome principal. Métrica mensurável.

**Outcome:** [ex: "Reduzir em 50% o tempo de emissão de certificado de calibração nas assistências técnicas"]
**Como medir:** [tempo médio antes / depois]
**Por quê esse outcome:** [vem de `dores-mapeadas.md` + `jobs-to-be-done.md`]

---

## Opportunities (dores / jobs)

### Opportunity 1: [dor / job]
**Origem:** Dor #N de `dores-mapeadas.md` (score: XXX) + Job-N de `jobs-to-be-done.md`
**Evidência (entrevistas):** XX/12 entrevistados mencionaram
**Solutions exploradas:**

#### Solution 1.1: [ideia]
- **Descrição:** ...
- **Premissas (mover pra assumption-map.md):** ...
- **Custo estimado de implementação:** [P / M / G]
- **Experiment 1.1.a:** [smoke test / fake-door / protótipo de papel — definir em `validacao-ativa.md`]

#### Solution 1.2: [ideia alternativa]
- ...

### Opportunity 2: ...

---

## Anti-padrão

❌ Pular direto pra "vamos fazer feature X" sem mapear opportunity primeiro.
❌ Listar 1 solution por opportunity (geralmente há 2–4 caminhos).
❌ Solutions vagas ("melhorar UX") — precisam ser concretas o suficiente pra virar experiment.

---

## Saída esperada
- 1 outcome
- 3–5 opportunities mapeadas com evidência
- 2–4 solutions por opportunity
- 1 experiment por solution mais promissora
- Recomendação de qual opportunity atacar primeiro (entra na `sintese-final.md`)
