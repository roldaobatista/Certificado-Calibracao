---
owner: roldao
revisado_em: 2026-05-27
proximo_review: 2026-08-27
status: aceito
aceito-em: 2026-05-27
diataxis: explanation
audiencia: agente
tipo: adr
---

# ADR-0066 — Predicates `cmc_cobre` + `procedimento_vigente_para` declarados mas fail-open lazy em Marco 4 calibração (módulos `escopo` + `procedimentos` Wave A)

## Contexto

Auditor produto (1ª passada P5 do M4 calibração, 2026-05-27) identificou que 6 AC binários do PRD `calibracao` v stable —

- **AC-CAL-001-2** (`recepcionar` → escopo NÃO cobre RBC → avisa + segue NÃO-RBC)
- **AC-CAL-002-2** (`configurar` → faixa fora CMC bloqueia RBC com 412 `EscopoNaoCobreFaixa`)
- **AC-CAL-015-1** (`gerenciarEscopoCMC` → CMC vigente filtra escopos)
- **AC-CAL-016-1** (`configurar` → procedimento vigente → predicate bloqueia se procedimento expirado)
- **AC-CAL-016-2** (idem AC-CAL-016-1 para revisão)
- **AC-CAL-016-3** (idem para 2ª conferência)

— não são cumpridos em runtime: os predicates `cmc_cobre` e `procedimento_vigente_para` existem em `src/infrastructure/calibracao/predicates_calibracao.py` como STUB Wave A retornando fail-open `(True, "")`, e **nenhum use case invoca eles**.

Investigação revelou bloqueio estrutural: os módulos consumidos pelos predicates ainda não existem.

- **`cmc_cobre`** precisa consultar o módulo `metrologia/escopos-cmc` (entidade `EscopoCMC` + `RTCompetenciaParaEscopo` + intervalos `[faixa_min, faixa_max]` + CMC=Capacidade de Medição e Calibração declarada pra CGCRE). Esse módulo é US-CAL-015 — entregue como query service puro em P4 Fase 6 mas SEM persistência Django (`EscopoCMCSnapshot` é dataclass local da query, não tem migration nem repositório).
- **`procedimento_vigente_para`** precisa consultar o módulo `metrologia/procedimentos-calibracao` (entidade `ProcedimentoCalibracao` + `vigencia_inicio/fim` + revisões). Esse módulo é US-CAL-016 — não entregue em P4 (apenas snapshot stub em `configurar_calibracao` aceita procedimento_id sem validação).

Adicionar predicates REAIS exige criar 2 módulos Django completos (entities + migrations + repositories + use cases + adapters). Pertence a Wave A pós-1º tenant RBC externo. Marco 4 atual é dogfooding-only.

Pattern é EXATAMENTE paralelo ao ADR-0063 do M3 OS (predicate `rt_competencia_cobre` declarado mas com fail-open lazy controlado quando `grandeza` ainda não persistida).

## Decisão

1. **Predicates `cmc_cobre` e `procedimento_vigente_para` continuam declarados como STUB Wave A em `predicates_calibracao.py`** retornando `(True, "")` fail-open controlado por design.
2. **Use cases NÃO invocam os predicates ainda** — invocação real entra em Wave A simultaneamente à criação dos módulos `escopos-cmc` + `procedimentos-calibracao`.
3. **AC-CAL-001-2 + AC-CAL-002-2 + AC-CAL-015-1 + AC-CAL-016-1/2/3 são MODIFICADOS** no PRD `calibracao` para refletir:
   - "Predicate `cmc_cobre` / `procedimento_vigente_para` declarado em Marco 4 P4 Fase 2; comportamento de bloqueio (412 `EscopoNaoCobreFaixa` / 412 `ProcedimentoExpirado`) entra em vigor quando módulos `metrologia/escopos-cmc` + `metrologia/procedimentos-calibracao` forem entregues — pertence a Wave A (`GATE-CAL-CMC-PREDICATE` + `GATE-CAL-PROC-VIGENTE-PREDICATE`)."
4. **Quando Wave A plugar os 2 módulos** + invocar os predicates nos use cases-alvo (`configurar_calibracao` para AC-CAL-002-2/016-1; `solicitar_revisao` para AC-CAL-016-2; `aprovar_2a_conferencia` para AC-CAL-016-3; `criar_calibracao` para AC-CAL-001-2), o bloqueio começa automaticamente.
5. **GATE-CAL-CMC-PREDICATE + GATE-CAL-PROC-VIGENTE-PREDICATE Wave A** já rastreados em `docs/faseamento/M4-calibracao/auditoria-familia5.md` §5 (NOVO — esta ADR formaliza o gate como decisão arquitetural, não TODO ad-hoc).

## Mitigação operacional (período de fail-open Marco 4 dogfooding)

- Marco 4 é **dogfooding-only** (Balanças Solution — projeto `project_sem_cliente_externo_agora`). Sem cliente externo RBC pago, risco de "calibração emitida fora do escopo CMC" é controlado por processo interno (RT da Balanças confere manualmente a faixa antes de configurar).
- **GATE-SEG-BPT-1** já bloqueia produtivo em Balanças até apólice BPT emitida — risco propagado limitado à apólice.
- **GATE-CAL-CMC-PREDICATE Wave A** (já rastreado em auditoria-familia5.md §5) é o lugar canônico onde a invocação real entra em vigor — esta ADR formaliza o status atual.
- **PRD `calibracao` recebe disclaimer** "ADR-0066: 6 ACs em fail-open lazy Wave A" idêntico ao retrofit do PRD `os` por ADR-0063 (commit `76614c8` M3 OS).

## Non-goals desta ADR

- NÃO entrega os módulos `metrologia/escopos-cmc` ou `metrologia/procedimentos-calibracao` agora (escopo Wave A).
- NÃO altera contrato dos predicates (assinatura `(resource: dict) -> (bool, str)` continua a mesma).
- NÃO retrofita testes existentes — a 2ª passada do auditor produto deve aceitar fail-open documentado como CONCERN BAIXO (paralelo a M3 OS).

## Consequências

**Positivas:**
- 2 ALTO (PROD-CAL-01 + PROD-CAL-02) da 1ª passada P5 são consertados por causa-raiz: o pattern fail-open lazy fica explicitamente documentado em ADR ao invés de implícito em docstring de predicate STUB.
- Drop-in pattern: quando módulo Wave A entrar, predicate JÁ está conectado nos use cases (zero retrofit code) — só implementação real do `cmc_cobre`/`procedimento_vigente_para` muda.
- Aderência ao princípio do M3 OS (ADR-0063): fail-open controlado por design é melhor que TODO escondido em docstring.

**Negativas (aceitas):**
- 6 ACs do PRD ficam com nota "Wave A" — produto entrega menor que prometido na spec original. Mitigação: dogfooding-only + GATE-SEG-BPT-1 ativo.
- Auditor produto na 2ª passada precisa **aceitar fail-open documentado** como CONCERN BAIXO (não FAIL ALTO) — exatamente paralelo a PROD-M3-02 que aceitou ADR-0063 e fechou.

## Dependências

- **Bloqueada por:** nenhuma — esta ADR só formaliza estado atual.
- **Habilita Wave A:**
  - GATE-CAL-CMC-PREDICATE: criar módulo `src/{domain,application,infrastructure}/metrologia/escopos_cmc/` + invocar `cmc_cobre` em `configurar_calibracao` + `criar_calibracao`.
  - GATE-CAL-PROC-VIGENTE-PREDICATE: criar módulo `procedimentos_calibracao/` + invocar em 3 use cases (configurar, solicitar_revisao, aprovar_2a_conferencia).

## Comparação com ADR-0063 (M3 OS)

| Aspecto | ADR-0063 (M3 OS) | ADR-0066 (M4 cal) |
|---|---|---|
| Predicate STUB | `rt_competencia_cobre` | `cmc_cobre` + `procedimento_vigente_para` |
| Causa estrutural | `AtividadeDaOS.grandeza` não persistido | módulos `escopos_cmc` + `procedimentos_calibracao` não entregues |
| ACs modificados no PRD | 4 (OS-002-3/002b-4/003-6/012-2) | 6 (CAL-001-2/002-2/015-1/016-1/016-2/016-3) |
| Invocação dos predicates | invocados nos use cases | NÃO invocados (predicates retornam True hoje; invocação entra com Wave A) |
| GATE de fechamento | GATE-OS-GRANDEZA-EM-ATIVIDADE | GATE-CAL-CMC-PREDICATE + GATE-CAL-PROC-VIGENTE-PREDICATE |
| Risco residual dogfooding | RT atribui técnico sem competência (controle de processo Balanças) | RT emite calibração fora do escopo CMC (controle de processo Balanças + GATE-SEG-BPT-1) |

## Status

ACEITO em 2026-05-27 como conserto Batch S5 da 1ª passada P5 Família 5 do Marco 4 calibração. Espelha decisão Roldão (memória `feedback_negocio_sobre_agente`): "negócio vence conveniência do agente — fail-open documentado é melhor que ACs prometidos sem entrega".

## Emenda 2026-05-29 (revisões M6 `escopos-cmc` — formalização da transição)

A revisão do plan M6 (tech-lead TL-C-01/TL-C-05 + RBC NC-04) detalhou **como** o
fail-open lazy fecha, formalizando o que aqui era genérico:

1. **`cmc_cobre` fecha pelo use case, não pelo predicate-na-permissão.** A ADR-0073
   move a validação de cobertura metrológica para dentro do use case
   (`configurar_calibracao`) por chamada explícita à porta `escopos_cmc.query_service.
   cobre(...)`. O predicate STUB `cmc_cobre` em `predicates_calibracao.py` fica
   DEPRECADO (no-op) na transição. Bloqueio real (412 `EscopoNaoCobreFaixa`) entra
   na **Fatia 3** do M6 (GATE-CAL-CMC-PREDICATE).
2. **Cobertura RBC é tridimensional (ADR-0074):** faixa ⊆ escopo (na config) +
   `U ≥ CMC` (na emissão, 2ª porta) + menor-CMC-por-faixa. O fechamento da condição
   `U ≥ CMC` é rastreado por **GATE-ECMC-U-MAIOR-CMC** (consumo possivelmente diferido
   ao módulo `certificados`).
3. **Vínculo RT↔escopo permanece fail-open lazy** (paralelo ao `rt_competencia_cobre`
   da ADR-0063) até o retrofit ADR-0022 v2 (RTCompetencia por método+faixa) chegar.
   No MVP dogfooding NÃO bloqueia por RT; bloqueio real (escopo sem RT competente
   vivo → DENY uso RBC) é rastreado por **GATE-ECMC-RT-VINCULO**, obrigatório antes
   do 1º tenant RBC externo. Fail-open documentado explícito no código + teste nomeado
   (nunca gap silencioso).
4. **`procedimento_vigente_para` segue o mesmo padrão** (ADR-0073) quando o módulo
   `procedimentos-calibracao` for construído — fecha via use case, não via predicate.
