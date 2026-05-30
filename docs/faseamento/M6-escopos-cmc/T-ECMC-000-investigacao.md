---
owner: roldao
revisado-em: 2026-05-30
status: stable
fase: M6-escopos-cmc
ritual: investigacao-regra-0
tarefa: T-ECMC-000
exige-pg-real: true
---

# T-ECMC-000 — Investigação Regra #0 antes do wire-in (Fatia 3)

> Pré-condição da Fatia 3 (TL-C-03). Resposta à pergunta do plan §283: "a view
> passa grandeza/faixa hoje? algum teste M4 de `configurar` perfil A passa, e por
> quê?". Verificado com **PG real** (Docker up, `--no-cov --reuse-db`).

## Achados (estado real — não suposição)

1. **`configurar_calibracao` é use case PURO** (`src/application/metrologia/calibracao/configurar_calibracao.py`).
   Importa só domínio + `CalibracaoRepository` (Protocol). Hoje valida apenas
   `escopo_id NOT NULL` quando `tipo_acreditacao == RBC` (linhas 156-160). **NÃO
   chama `cobre()`** — nenhuma validação de cobertura de faixa existe ainda.

2. **A porta `escopos_cmc.query_service.cobre/cmc_para` já existe** (Fatia 1b),
   fail-CLOSED, infra Django. Assinatura de `cobre`:
   `cobre(*, tenant_id, grandeza, faixa_min, faixa_max, unidade, data) -> (bool, reason)`.
   É **função de módulo sem estado** (ADR-0073 ponto 4 / TL-C-04), não singleton.

3. **A view `configurar` NÃO monta resource com grandeza/faixa, NEM chama `can()`
   com o predicate** (`views.py:419-609`). O predicate STUB `cmc_cobre` está
   registrado em `apps.py` mas o resource real nunca recebe grandeza/faixa
   estruturados → o STUB nunca bloqueia de fato. **Confirma a tese da ADR-0073**:
   não há dado metrológico server-side no momento da avaliação no permission layer.

4. **NÃO existe fonte server-side estruturada de grandeza/faixa hoje:**
   - `CalibracaoSnapshot` (`entities.py:65`) **não tem** `grandeza`/`faixa` de 1ª classe.
   - `snapshot_equipamento_json` é dict **livre** — nos testes/fixtures aparece como
     `{}`, `{"modelo": "X"}`, `{"nome": "Balanca"}`. Sem chaves grandeza/faixa.
   - M2 `Equipamento.faixa` (`equipamentos/models.py:105`) é **CharField texto livre**
     (ex.: "0 a 200 kg"), sem `grandeza` estruturada nem `faixa_min/max` parseável.

5. **Baseline verde (PG real):** `pytest tests/test_m4_uc_configurar_calibracao.py
   tests/test_m4_predicates_calibracao.py --no-cov --reuse-db` → **43 passed**.

## Conclusão — tamanho real do wire-in

O wire-in **não é drop-in**. O fail-closed efetivo depende de uma **cadeia de dados
server-side** (M2 Equipamento → Calibracao → `cobre()`) que **não existe estruturada
em lugar nenhum** hoje. A estratégia de **2 etapas** (T-ECMC-046) é obrigatória:

- **Etapa 1 (esta fatia — executável agora):** plugar a porta real `cobre()` DENTRO
  do use case `configurar_calibracao` via injeção de `CoberturaEscopoPort` (Protocol),
  derivando grandeza/faixa **do snapshot PERSISTIDO** (`snapshot_equipamento_json` —
  server-side, não do payload da request → SEG-CAL-10). Enquanto a fonte estruturada
  não existir, o use case opera **fail-open lazy** (paralelo a ADR-0063: só valida
  quando há `grandeza` derivável; ausência = libera + log + GATE). Fecha o seam
  arquitetural da ADR-0073 sem regressão no M4. Adapter real injetado pela view.

- **Etapa 2 (futura — GATE-CAL-CMC-PREDICATE):** promover grandeza/faixa a campo de
  1ª classe na Calibracao (capturado na recepção a partir do M2) OU estruturar
  `grandeza`+faixa no M2 Equipamento. Quando o dado fluir, a validação fail-CLOSED
  ativa automaticamente — sem mudar o use case. Inclui testes de transição
  fail-open→fail-closed (T-ECMC-045) e suíte M4 reverde.

## Decisão de produto/metrológica que fica ABERTA para Etapa 2 (Roldão/RBC)

**De onde vem a "faixa solicitada" para a cobertura CMC?** Dois caminhos válidos:
- (a) **faixa de capacidade do equipamento** (instrumento 0-200 kg → cobertura cobre
  0-200?), capturada na recepção; ou
- (b) **faixa dos pontos de calibração** definidos no procedimento/orçamento (range
  efetivamente calibrado), conhecida só após configuração.

Decisão NÃO bloqueia a Etapa 1 (o seam é genérico). Será pinada antes da Etapa 2,
junto do retrofit M2/recepção. Rastreada em **GATE-CAL-CMC-PREDICATE**.
