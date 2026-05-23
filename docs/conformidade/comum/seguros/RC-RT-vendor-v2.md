---
owner: roldao
revisado-em: 2026-05-23
status: minuta
aguarda-corretora-susep: true
selo: "PRÉ-COTAÇÃO — REQUER CORRETORA SUSEP CREDENCIADA"
finalidade: desenho de apólice RC profissional individual pra RT vendor próprio (V2 — quando Aferê fornecer RT credenciado próprio aos tenants)
gatilho: ADR-0022 V2 (RT vendor) — não se aplica em Wave A
---

# RC profissional individual — RT vendor Aferê (V2)

## 1. Contexto

ADR-0022 V1 (em vigor) modela apenas o **RT do tenant** (humano credenciado contratado pelo próprio tenant). Aferê não fornece RT.

ADR-0022 **V2 (futura)** prevê hipótese de Aferê fornecer RT credenciado próprio como serviço ao tenant (modelo BPO de responsabilidade técnica). Nesse cenário, Aferê passa a ter exposição direta de RC profissional individual sobre o profissional RT — D&O do Roldão não cobre porque RT é pessoa física distinta com registro CREA/CRQ próprio.

Este documento desenha a apólice **antes** de V2 entrar, pra que cotação esteja pronta quando o gatilho de contratação acontecer.

## 2. Modalidade

**RC Profissional Individual — Responsável Técnico CREA/CRQ acreditado RBC**

## 3. Capital mínimo

- **R$ 1.000.000/ano agregado** por RT
- **Sublimite por evento:** R$ 500.000
- **Múltiplos RTs:** apólice por RT ou apólice consolidada com sublimite individual nominal

## 4. Cláusulas obrigatórias

- **`Cobertura técnica CREA/CRQ`** — abrange exercício profissional regulamentado por conselho de classe
- **`Defesa em sindicância de conselho de classe`** — paga honorários advogado + perito em processo disciplinar CREA/CRQ
- **`Defesa em sindicância CGCRE`** — paga honorários em supervisão/auditoria que questione conduta técnica do RT
- **`Responsabilidade por assinatura A3`** — cobre disputa sobre assinatura ICP-Brasil em certificado/laudo
- **`Responsabilidade por declaração de competência por grandeza`** — cobre carta competência NIT-DICLA-021
- **`Cobertura retroativa`** — atos anteriores à apólice, claim posterior
- **`Right to defend`**
- **`Sublimite consequential damages tenant`** — perda de acreditação do tenant por conduta RT (R$ 250k)

## 5. Cláusulas a rejeitar

- Exclusão "atos dolosos do profissional" genérica — exigir definição estrita (somente fraude documentada com trânsito em julgado)
- Exclusão "decisões com auxílio de software" — RT decide com IA do Aferê assistindo (ADR-0025)
- Franquia > R$ 25k por evento (proibitivo pra defesa de sindicância)

## 6. Gatilho de contratação

| Evento gatilho | Ação |
|---|---|
| ADR-0022 V2 aceita pelo Roldão | Iniciar cotação |
| 1º RT vendor contratado por Aferê | Apólice ATIVA antes da 1ª calibração assinada por ele |
| Cada RT adicional | Endosso individual nominal |
| RT desligado | Cláusula `tail coverage` 2 anos (atos durante vigência reportados depois) |

## 7. Prêmio anual estimado

**R$ 3.000 a R$ 8.000/ano por RT** (porte PME, RT pleno CREA/CRQ ativo, sem histórico de sinistro). Sobe pra R$ 10-15k/ano se RT atua em farma/alimento.

## 8. Documentos exigidos pra cotação

Por RT a ser segurado:
- Cópia CREA/CRQ ativo
- Currículo (ênfase em experiência metrológica)
- Declaração de competências por grandeza (NIT-DICLA-021)
- Termo de contratação Aferê↔RT (modelo CLT ou PJ)
- Lista de tenants atendidos + escopo

## 9. Corretora

Mesma corretora SUSEP que emitir as 7 modalidades Wave A (consolidar relacionamento). Cotação separada por se tratar de modalidade com subscritor específico (alguns subscritores tech não fazem RC profissional individual).

## 10. GATE relacionado

**GATE-SEG-RT-RC-1** — em `gates-seg.md` (status 🟢 V2 — não bloqueia Wave A).

## 11. Status

Minuta — aguarda gatilho ADR-0022 V2 + cotação corretora SUSEP humana.

**Selo:** este desenho é pré-cotação. Apólice válida exige corretora SUSEP credenciada (Lei 4.594/64).
