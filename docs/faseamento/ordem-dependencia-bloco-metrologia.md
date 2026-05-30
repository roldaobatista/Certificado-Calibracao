---
owner: roldao
revisado-em: 2026-05-30
status: stable
diataxis: reference
audiencia: agente
relacionados:
  - docs/faseamento-foundation-waves.md
  - docs/faseamento-modulos.md
  - docs/faseamento/M6-escopos-cmc/tasks.md
  - docs/adr/0073-validacao-cobertura-metrologica-no-use-case.md
  - docs/adr/0074-cobertura-rbc-tridimensional-faixa-u-maior-cmc.md
---

# Ordem de implementação por dependência — bloco metrologia (Wave A)

> **Por que este doc existe (Roldão 2026-05-30):** a ordem das FASES está em
> `faseamento-foundation-waves.md` e a dos MÓDULOS em `faseamento-modulos.md`, mas
> faltava a ordem FINA do bloco metrologia que **evita retrabalho** — isto é, qual
> peça é compartilhada entre módulos e portanto deve ser feita UMA vez. Regra:
> ninguém pergunta "qual a próxima etapa"; segue-se esta ordem.

## Princípio (evitar retrabalho)

Os 4 módulos metrológicos de suporte/emissão (`escopos-cmc`,
`procedimentos-calibracao`, `certificados`, `licencas-acreditacoes`) validam regras
contra a calibração **na configuração** (faixa) e **na emissão** (ponto a ponto).
Há **uma peça de dados compartilhada** entre eles — se feita em duplicidade, vira
retrabalho. Identificá-la e fazê-la uma vez é o objetivo desta ordem.

## A peça compartilhada — `Calibracao.faixa_calibrada_declarada` (ADR-0076)

Decisões `consultor-rbc-iso17025` + `tech-lead-saas-regulado` (2026-05-30), cravadas
em **ADR-0076**:

- **Portão de CONFIGURAÇÃO (escopos-cmc + procedimentos):** fonte = **faixa
  calibrada declarada** pelo RT na transição RECEPCIONADA→CONFIGURADA. Campo de 1ª
  classe na `Calibracao` (`grandeza_calibrada: Grandeza` + `faixa_calibrada_declarada:
  FaixaMedicao`), WORM, reusando o vocabulário único de `value_objects.py`. Trava
  fail-CLOSED: `declarada ⊆ escopo acreditado` (NÃO contra capacidade M2 — essa é
  sanidade diferida GATE-CAL-FAIXA-M2-SANIDADE). Obrigatória em RBC.
- **Cobertura DEFINITIVA (EMISSÃO, módulo `certificados`):** medida contra os
  **pontos efetivamente medidos** (não a declarada — CGCRE não extrapola). Invariante
  `pontos ⊆ declarada ⊆ escopo` + `U(ponto) ≥ CMC(ponto)` + `faixa_certificado =
  [min,max] pontos válidos`. Novo INV-ECMC de reconciliação a cravar em `certificados`.
- **Vocabulário único** grandeza/unidade compartilhado pelos 3 módulos — maior risco
  de retrabalho silencioso ("kg" vs "kilograma").

Quem consome a mesma peça `faixa_calibrada_declarada`:
- `escopos-cmc` → `cobre(grandeza, faixa, data)` na configuração (GATE-CAL-CMC-PREDICATE).
- `procedimentos-calibracao` → `procedimento_vigente_para(grandeza, faixa, data)` na
  configuração (GATE-CAL-PROC-PREDICATE).
- `certificados` → `cmc_para(grandeza, ponto, data)` na emissão + reconciliação dos pontos.

## Ordem (sem retrabalho)

| # | Item | Estado | Por quê nessa posição |
|---|------|--------|----------------------|
| 0 | M6 escopos-cmc Fatias 1-2 + Fatia 3 Etapa 1 (porta wire-in fail-open lazy) | ✅ FEITO | seam ADR-0073 pronto; cobertura plugada mas permissiva |
| 0.5 | ADR-0076 (fonte da faixa: declarada=portão config / pontos=cobertura emissão) | ✅ FEITO | destrava o item 1 (tech-lead exigiu ADR antes de codar) |
| **1** | **Frente SAN-FAIXA-CALIBRADA (peça compartilhada).** Sub-passos: (1a) domínio — `grandeza_calibrada`+`faixa_calibrada_declarada` no snapshot (VO); (1b) schema — migration retrofit M4, 4 colunas decompostas, `# metrology-affecting:`; (1c) input/serializer config — RT declara; (1d) wire-in fail-CLOSED — `cobre(declarada)` obrigatório RBC, remove interim `_faixa_solicitada_server_side`; (1e) transição de testes fail-open→fail-closed (suíte M4 reverde) | **PRÓXIMO** | feita UMA vez; fecha GATE-CAL-CMC-PREDICATE (portão config) E pré-resolve `procedimentos`. Commit(s) próprio(s) ANTES de fechar o resto do M6 (tech-lead: não esconder mudança de bloqueio RBC dentro do fechamento). |
| 2 | M6 escopos-cmc resto: Fatia 4 (extração PDF CGCRE) → P7 (INVs+hooks) → P8 (docs+drill PG real) → P9 (auditores) | depois do #1 | independentes da peça; fecham o módulo pelo ritual |
| 3 | `procedimentos-calibracao` (espelha escopos-cmc; consome a peça #1; fecha GATE-CAL-PROC-PREDICATE) | depois do M6 | reusa #1 sem refazer; ADR-0073/0066 já resolvem o padrão |
| 4 | `certificados` (cobertura DEFINITIVA: U≥CMC ponto-a-ponto + reconciliação `pontos ⊆ declarada`; faixa do certificado = pontos; RT acreditado) | depois de procedimentos | é o ponto de emissão; consome escopos+procedimentos vigentes; GATE-CAL-EMISSAO-RECONCILIA-FAIXA |
| 5 | `licencas-acreditacoes` (RT acreditado no escopo vigente — pré-requisito de toda emissão) | junto/depois de certificados | INV-INT-001/003/004; bloqueia emissão fora de escopo |

## Diferido explicitamente (não bloqueia, não é retrabalho)

- Cobertura `cmc_para` + reconciliação por pontos na emissão → módulo `certificados`
  (#4), GATE-CAL-EMISSAO-RECONCILIA-FAIXA + GATE-ECMC-U-MAIOR-CMC. Não se implementa
  em escopos-cmc porque o ponto de emissão ainda não existe.
- Sanidade `declarada ⊆ capacidade M2` → GATE-CAL-FAIXA-M2-SANIDADE (espera M2
  estruturar grandeza+faixa; não bloqueia o portão por escopo).
- Dossiê de validação cl. 7.11 do gate de cobertura + parecer RBC credenciado →
  pré-produção (`project_sem_contratacoes_externas_ate_producao`).

## Como seguir

`/implement` segue esta tabela de cima pra baixo. Item #1 começa com mini-plano +
revisão `tech-lead-saas-regulado` (retrofit de marco fechado M4 é decisão de
arquitetura). Sem perguntar "próxima etapa" ao Roldão — a ordem é esta.
