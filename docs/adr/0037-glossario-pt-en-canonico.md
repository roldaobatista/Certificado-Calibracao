---
adr: 0037
titulo: Glossário PT-EN canônico — termos do produto + traduções para libs
owner: roldao
revisado-em: 2026-05-27
status: aceito
aceito-em: 2026-05-27
proposto-por: agente (auditoria projeto-inteiro 10 lentes — Onda 1 transversal, M-INT-02)
revisado-por: tech-lead-saas-regulado
bloqueia-fase: Wave A (canonicalização de nomes em código novo)
depende-de: D3 (nomenclatura híbrida PT + 7 arquivos EN), ADR-0029 (canonicalização texto)
---

# ADR-0037 — Glossário PT-EN canônico

## O QUE

Doc único `docs/comum/glossario.md` mapeia 1:1 termo PT (canônico do produto) ↔ termo EN (quando obrigado por lib/integração). Resolve drift "Cliente vs Customer", "Equipamento vs Asset/Device/Instrument", "Ordem de Serviço vs WorkOrder/ServiceOrder/Job".

## PORQUE

- D3 decidiu: produto em PT-BR. 7 arquivos EN só por ferramentas (CLAUDE.md, AGENTS.md, README.md, LICENSE, CHANGELOG.md, CONTRIBUTING.md, CODEOWNERS).
- Auditoria Onda 1 M-INT-02 detectou: "Cliente" vs "Customer" em diferentes módulos; "Equipamento" vs "Instrument"/"Asset" em diferentes contextos. Sem catálogo, cada agente IA inventa diferente.
- Termos técnicos metrológicos têm tradução obrigatória ISO/VIM (Vocabulário Internacional de Metrologia) — não inventar.

## COMO

Doc `docs/comum/glossario.md` é fonte única. Hook (a criar) valida que nome de classe Django nova em `src/domain/` bate com glossário (PT-BR canônico).

## ID

- **INV-DOC-GLOSS-001** — toda classe de domínio em `src/domain/**/models.py` ou `src/domain/**/value_objects.py` cujo nome **conceitual** esteja no glossário **deve** usar o nome PT-BR canônico (`Cliente`, não `Customer`). Adapter pode traduzir na borda EN.
- **INV-DOC-GLOSS-002** — termo metrológico ISO/VIM segue VIM 4ª edição quando aplicável (`Calibracao` não `Calibration`; `MedicaoControle` não `ControlMeasurement` — mantém PT canônico mesmo com correspondência ISO).

## NON-GOAL

- **Não** traduz strings de UI (i18n é outra ADR).
- **Não** força tradução de libs externas (Django, DRF, procrastinate continuam EN).
- **Não** mantém terceira linguagem (espanhol etc.) — V2 quando primeiro tenant internacional entrar.

## Consequências

**Boas:** próximo agente que criar `Customer` em `src/domain/comercial/` é bloqueado pelo hook + recebe sugestão `Cliente` do glossário. Modelo de domínio fica coerente PT-BR.

**Ruins:** algumas dependências têm que ser adapatadas nos boundaries (ex: webhook de gateway internacional fala "customer" — converte na borda).

## Referências cruzadas

- D3 (decisões fundadoras)
- `docs/comum/glossario.md` (catálogo)
- ADR-0029 (canonicalização de texto probatório)
