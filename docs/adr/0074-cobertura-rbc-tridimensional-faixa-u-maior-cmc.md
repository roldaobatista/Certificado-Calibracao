---
owner: roldao
revisado-em: 2026-05-29
proximo_review: 2026-08-29
status: aceito
aceito-em: 2026-05-29
diataxis: explanation
audiencia: agente
tipo: adr
---

# ADR-0074 — Cobertura RBC tridimensional: faixa ⊆ escopo + U ≥ CMC + menor-CMC-por-faixa

## Contexto

Revisão do `consultor-rbc-iso17025` ao `/plan` do M6 `metrologia/escopos-cmc`
(2026-05-29, NC-01 CRÍTICO + NC-03 ALTO) corrigiu um sub-dimensionamento
metrológico: o plan validava **apenas a contenção de faixa** (faixa solicitada ⊆
faixa do escopo) para autorizar emissão RBC. Falta a regra mais cobrada em
auditoria CGCRE.

**Regra normativa (ILAC-P14:09/2020 §5.5, texto literal):** *"accredited
calibration laboratories shall not report a smaller measurement uncertainty than
the uncertainty described by the CMC for which the laboratory is accredited."* —
o laboratório acreditado **não pode reportar incerteza menor que a CMC**. A CMC é o
**piso** da incerteza reportável; a incerteza do certificado é tipicamente **maior**
que a CMC (soma as contribuições do instrumento do cliente: resolução,
repetibilidade do UUT, deriva). Reportar `U < CMC` é não-conformidade direta — e é
a não-conformidade nº 1 em supervisão de certificado.

**Erro oposto também é NC (ILAC-P14):** preencher `U = CMC` cego (copiar a CMC como
se fosse a incerteza do serviço) — o U vem do orçamento de incerteza (US-CAL-005), a
CMC é só o piso.

**Múltiplos métodos por faixa (NIT-DICLA-012, verificar rev.):** quando o lab tem
mais de um método para a mesma grandeza+faixa, o escopo publica **uma** CMC: a do
método de **MENOR** incerteza. Não se publica CMC diferente por método.

**Sequenciamento:** `cmc_cobre` é avaliado na CONFIGURAÇÃO (US-CAL-002), **antes** de
existir o U calculado (US-CAL-005). Logo a regra `U ≥ CMC` não cabe no `cmc_cobre`
da configuração — exige um segundo ponto de avaliação, na EMISSÃO/aprovação.

## Decisão

O bloqueio de emissão RBC (perfil A) tem **três condições cumulativas**, não uma:

1. **Contenção total da faixa** (`solicitada_min ≥ escopo_min E solicitada_max ≤
   escopo_max`) — avaliada no use case `configurar_calibracao` via porta
   `escopos_cmc.query_service.cobre(...)` (ADR-0073) → 412 `EscopoNaoCobreFaixa`.
   A interseção (`_faixa_intersecta`, `escopo.py:55-71`) serve só para LISTAR
   escopos candidatos, **nunca** para bloquear.
2. **`U_reportada ≥ CMC`** — avaliada na EMISSÃO/aprovação (US-CAL-007/008/cert),
   quando o U expandido (k=2, ~95,45%) já existe, via **segunda porta**
   `escopos_cmc.query_service.cmc_para(grandeza, faixa, data) -> Decimal` →
   412 `IncertezaAbaixoDoCMC`. **Normalizar unidade e forma** (absoluta vs
   `a + b·X`) antes de comparar — comparação de `Decimal` cru sem normalizar produz
   falso-PASS/falso-bloqueio. → **INV-ECMC-009**.
3. **Menor CMC por faixa:** quando há N métodos vigentes para a mesma grandeza+faixa,
   `cmc_para()` retorna a **MENOR** CMC vigente (a publicada no escopo CGCRE) — não a
   "pior". O cadastro/extração valida consistência; o cálculo de cobertura usa a menor.

**Anti-cópia (NC-07):** `U` é sempre derivada do orçamento de incerteza (US-CAL-005);
o sistema NUNCA preenche `U = CMC` por default. Teste anti-cópia obrigatório.

## Onde cada condição é consumida

- Condição 1 (faixa): use case `configurar_calibracao` (M4) — entregue na **Fatia 3**
  do M6 (GATE-CAL-CMC-PREDICATE).
- Condição 2 (U ≥ CMC) e 3 (menor CMC): a porta `cmc_para()` é **entregue pelo M6**;
  o **consumo na emissão** depende de onde o U vira final + o certificado é emitido.
  Se for em M4 (aprovar_2a_conferencia, onde o U já está calculado), wire ali; se a
  emissão formal do certificado for no módulo `certificados` (Wave A, não construído),
  o consumo é **diferido** com **GATE-ECMC-U-MAIOR-CMC** rastreado — a porta existe e
  é testada isoladamente no M6; o ponto de consumo é investigado (regra #0) no
  `/tasks` do M6 e fechado onde o U for final.

## Non-goals desta ADR

- NÃO define o motor de cálculo de incerteza (US-CAL-005, já no M4).
- NÃO trata cobertura para perfis B/C/D (não emitem RBC; ver ADR-0075).
- NÃO crava o número/revisão exato das NIT (RBC-NC-08 — verificar com humano
  credenciado antes do dossiê CGCRE).

## Consequências

**Positivas:**
- Fecha a não-conformidade nº 1 de auditoria CGCRE (U < CMC) ANTES do 1º tenant RBC
  externo — o módulo cumpre a regra ILAC-P14 inteira, não metade.
- A porta dupla (`cobre()` na config + `cmc_para()` na emissão) respeita o
  sequenciamento real (faixa conhecida na config; U conhecido só na emissão).

**Negativas (aceitas):**
- Amplia o escopo do M6 para uma 2ª porta + um ponto de consumo na emissão
  (possivelmente diferido a `certificados`). Mitigação: GATE-ECMC-U-MAIOR-CMC
  rastreia o consumo; a porta + invariante + testes ficam prontos no M6.
- Exige normalização unidade/forma da CMC (`a + b·X`) — complexidade extra no
  cálculo de cobertura. Aceito: é a forma real como a CGCRE publica CMC.

## Dependências

- **Depende de:** ADR-0073 (validação no use case), ADR-0066 (fail-open lazy que
  destrava), ADR-0025 v2 (validação software cl. 7.11 do cálculo de cobertura),
  US-CAL-005 (motor de incerteza M4).
- **Habilita:** GATE-CAL-CMC-PREDICATE (condição 1) + GATE-ECMC-U-MAIOR-CMC
  (condições 2/3).

## Status

ACEITO em 2026-05-29 como conserto das NC-01 (CRÍTICO) + NC-03 (ALTO) da revisão RBC
do plan M6. Análogo a como a revisão RBC do M5 gerou ADR-0070/0071. Reconciliação em
`docs/faseamento/M6-escopos-cmc/reviews-consolidado.md`.

> **Limite:** parecer RBC consultivo (subagente sem credencial CGCRE); números de NIT
> marcados "verificar"; validação cl. 7.11 do cálculo de cobertura exige revisão de
> consultor humano credenciado pré-produção (diferido — `project_sem_contratacoes_externas_ate_producao`).
