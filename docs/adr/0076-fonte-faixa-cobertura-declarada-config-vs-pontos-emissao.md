---
owner: roldao
revisado-em: 2026-05-30
proximo_review: 2026-08-30
status: aceito
aceito-em: 2026-05-30
diataxis: explanation
audiencia: agente
tipo: adr
---

# ADR-0076 — Fonte da faixa de cobertura RBC: faixa calibrada declarada na configuração (portão) vs faixa efetiva por pontos na emissão

## Contexto

A investigação Regra #0 da Fatia 3 do M6 `escopos-cmc`
(`docs/faseamento/M6-escopos-cmc/T-ECMC-000-investigacao.md`) deixou EXPLICITAMENTE
aberta a fonte da "faixa solicitada" usada na verificação de cobertura CMC:
(a) capacidade do instrumento (M2) ou (b) pontos calibrados. O wire-in da Etapa 1
(ADR-0073) plugou a porta `cobre()` no use case `configurar_calibracao` lendo a
faixa de `snapshot_equipamento_json` (dict livre — fail-open lazy interim).

Duas revisões de substitutos humanos (2026-05-30) fecharam a questão:

- **`consultor-rbc-iso17025`:** a fonte canônica NÃO é a capacidade do instrumento
  (erro de cobertura — uso indevido de acreditação cl. 8.1.3) NEM os pontos no
  momento da configuração (ainda não fechados). É a **faixa calibrada declarada**
  pelo RT na transição RECEPCIONADA→CONFIGURADA. PORÉM, a cobertura RBC
  **definitiva** e a faixa reportada no certificado se medem contra os **pontos
  efetivamente medidos**, na EMISSÃO — a CGCRE não reconhece extrapolação (cl.
  7.8.4.1 + 7.6 + NIT-DICLA-021/012/013 + ILAC-P14 §5.5). A faixa declarada é
  necessária (portão de planejamento) mas NÃO suficiente como fonte única.
- **`tech-lead-saas-regulado`:** exigiu ADR antes de codar (altera marco FECHADO
  M4); apontou que validar a declaração contra a capacidade M2 não satisfaz
  SEG-CAL-10 enquanto o M2 for texto livre. **Reconciliação:** o teto regulatório
  real é o **escopo acreditado** (server-side, via `cobre()`), não a capacidade
  física do instrumento — logo o portão fail-closed NÃO depende do retrofit M2.

## Decisão

1. **`Calibracao.faixa_calibrada_declarada` (VO `FaixaMedicao`) + `grandeza_calibrada`
   (VO `Grandeza`)** cravados na CONFIGURAÇÃO pelo RT (operador interno autenticado).
   Campos de 1ª classe no snapshot (None/None em RECEPCIONADA, preenchidos
   atomicamente em CONFIGURADA), WORM probatório (cl. 8.4 + ADR-0029/0064). No
   schema, decompostos em 4 colunas tipadas (TL-C-02 — não JSONField). Reusam o
   vocabulário único `Grandeza`/`FaixaMedicao` (`src/domain/metrologia/value_objects.py`)
   compartilhado por `escopos-cmc`, `procedimentos-calibracao`, `certificados`.

2. **Portão de configuração (RBC, fail-CLOSED):** `faixa_calibrada_declarada ⊆
   escopo acreditado vigente` via porta `escopos_cmc.cobre()` → erro de domínio
   `EscopoNaoCobreFaixa` (412). Em RBC, declarar grandeza+faixa é **obrigatório**
   para sair de CONFIGURADA (não fail-open permanente — o fail-open lazy da Etapa 1
   era ponte). Em NAO_RBC (perfis B/C/D — ADR-0075): no máximo aviso suave, nunca
   bloqueio.

3. **Teto regulatório do portão = escopo acreditado, NÃO capacidade do instrumento.**
   `faixa_declarada ⊆ escopo` é a trava server-side (o RT não ganha nada declarando
   faixa fora do escopo — é bloqueado). A sanidade física `declarada ⊆ capacidade
   do instrumento` é **diferida** até o M2 estruturar grandeza+faixa
   (GATE-CAL-FAIXA-M2-SANIDADE) — refinamento, não bloqueante do portão.

4. **Cobertura DEFINITIVA + faixa do certificado = reconciliada contra os PONTOS na
   EMISSÃO** (módulo `certificados`, Wave A, ainda não construído):
   - invariante `pontos ⊆ faixa_declarada ⊆ escopo` (bloqueia emissão se ponto fora);
   - `U(ponto) ≥ CMC(ponto)` ponto a ponto (ADR-0074 cond. 2, porta `cmc_para`);
   - `faixa_do_certificado = [min(pontos_validos), max(pontos_validos)]` — NUNCA a
     declarada (reportar só o medido; calibração parcial é válida e explícita);
   - INV-ECMC novo de reconciliação (a cravar no módulo `certificados`).

5. **SEG-CAL-10:** a faixa declarada vem do input do RT (interno autenticado —
   distinto de cliente externo), validada server-side ⊆ escopo. Não é controlável
   de forma útil pelo declarante (declarar fora do escopo = bloqueio).

## Non-goals

- NÃO valida `U ≥ CMC` na configuração (é ponto a ponto, na emissão — `certificados`).
- NÃO exige retrofit M2 para o portão de configuração (só para a sanidade física,
  diferida).
- NÃO força `faixa_certificado == faixa_declarada` (mentira documental — calibração
  parcial é o caso normal).

## Consequências

**Positivas:**
- Fecha `GATE-CAL-CMC-PREDICATE` (portão de configuração) pela raiz, sem depender de
  marco fechado M2.
- Peça `faixa_calibrada_declarada` feita UMA vez serve `escopos-cmc` (cobertura
  faixa) E `procedimentos-calibracao` (procedimento vigente para grandeza+faixa) —
  evita retrabalho (ordem em `docs/faseamento/ordem-dependencia-bloco-metrologia.md`).
- Separa claramente portão (config) de cobertura definitiva (emissão), coerente com
  ADR-0073/0074.

**Negativas (aceitas):**
- Sanidade `declarada ⊆ capacidade M2` fica diferida (GATE-CAL-FAIXA-M2-SANIDADE) —
  no interim, RT pode declarar faixa fisicamente impossível para o instrumento, mas
  nunca fora do escopo acreditado (que é a trava regulatória).
- Cria dependência forte do módulo `certificados` para a cobertura RBC definitiva
  (GATE-CAL-EMISSAO-RECONCILIA-FAIXA).

## Dependências

- **Refina:** ADR-0074 (cobertura tridimensional — agora explicita config vs emissão),
  ADR-0073 (validação no use case).
- **Depende de:** ADR-0040 (calibracao), ADR-0067 (perfil), ADR-0075 (capacidade ≠ CMC).
- **Habilita:** GATE-CAL-CMC-PREDICATE (config, M6) + GATE-CAL-PROC-PREDICATE
  (procedimentos) + GATE-CAL-EMISSAO-RECONCILIA-FAIXA (certificados).

## Status

ACEITO em 2026-05-30 com base nas revisões `consultor-rbc-iso17025` (fonte +
normativa cobertura por pontos) e `tech-lead-saas-regulado` (APROVA COM CORREÇÕES —
NC-01/NC-02 endereçadas). Parecer RBC credenciado humano + dossiê cl. 7.11 do gate
ficam para pré-produção (`project_sem_contratacoes_externas_ate_producao`).
