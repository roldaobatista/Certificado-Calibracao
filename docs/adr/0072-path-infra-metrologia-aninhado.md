---
owner: roldao
revisado_em: 2026-05-28
proximo_review: 2026-08-28
status: aceito
aceito-em: 2026-05-28
diataxis: explanation
audiencia: agente
tipo: adr
---

# ADR-0072 — Módulos do domínio metrologia em path aninhado `src/infrastructure/metrologia/<modulo>/`

## Contexto

Revisão `tech-lead-saas-regulado` do plan M5 (2026-05-28, P3) apontou assimetria
de path: o M4 `calibracao` (fechado) vive achatado em
`src/infrastructure/calibracao/`, enquanto o modelo-de-domínio de `padroes`
propõe `src/infrastructure/metrologia/padroes/`. O domínio puro já é aninhado
(`src/domain/metrologia/calibracao/`, `src/domain/metrologia/value_objects.py`).
Os próximos módulos Wave A (`escopos-cmc`, `procedimentos-calibracao`) amplificam
a escolha.

## Decisão

Daqui pra frente, **todo módulo do domínio metrologia usa path aninhado**:
`src/infrastructure/metrologia/<modulo>/` (espelha `src/domain/metrologia/<modulo>/`).
Aplica-se a `padroes`, `escopos-cmc`, `procedimentos-calibracao` e futuros.

O M4 `calibracao` permanece achatado (`src/infrastructure/calibracao/`) como
**dívida técnica conhecida e documentada**. NÃO renomear o módulo fechado agora:
risco gratuito (629 testes + imports em ~6 arquivos + migrations registradas) sem
ganho funcional. Renomeação eventual = ADR própria + PR isolado, se/quando valer.

## Consequências

- Coerência domínio↔infra para os novos módulos.
- Assimetria visível `calibracao` (achatado) vs `metrologia/*` (aninhado) —
  aceita e documentada (assimetria documentada é barata; renomear módulo fechado
  é caro/arriscado).
- Não replicar o achatamento de M4 nos novos (memória `auditar_antes_de_replicar_molde`).

## Alternativas rejeitadas

- **Achatar `padroes` pra `src/infrastructure/padroes/`** (consistência com M4):
  rejeitado — propaga um desvio; quebra coerência com `src/domain/metrologia/`.
- **Renomear `calibracao` agora:** rejeitado — risco em módulo fechado sem ganho.

## Relacionados

ADR-0040 (padrão entidade separada do domínio metrologia) ·
`docs/faseamento/M5-padroes/reviews-consolidado.md` (C-12).
