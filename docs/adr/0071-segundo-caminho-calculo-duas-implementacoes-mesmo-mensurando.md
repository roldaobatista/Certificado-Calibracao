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

# ADR-0071 — "2º caminho de cálculo" (ISO 17025 cl. 7.11) = 2 implementações independentes do MESMO mensurando, não 2 estimadores de naturezas diferentes

## Contexto

Revisão `consultor-rbc-iso17025` do plan M5 `metrologia/padroes` (2026-05-28,
NC-2 — ALTO) corrigiu erro conceitual na proposta D-PAD-4 do plan v1 + US-PAD-009
do PRD.

O plan v1 definia o "2º caminho de cálculo do valor convencional" (ADR-0025 v2
cl. 7.11) como: **Caminho A** = média ponderada por incerteza dos certificados
externos anteriores; **Caminho B** = "GUM completo com modelo de variação
temporal" (deriva linear). Comparava `desvio > k·u_combined` e disparava
investigação se excedido.

**Erro:** o propósito do 2º caminho na cl. 7.11 é **verificação independente do
software de cálculo** — duas implementações que estimam o **mesmo mensurando** e
devem convergir, provando que o software não tem bug. Mas média-ponderada e
regressão-de-deriva **medem coisas diferentes** (valor atual ignorando tempo vs
valor projetado considerando tendência). Compará-las dispara **falso-positivo de
investigação sempre que houver deriva real** — exatamente quando o padrão está
se comportando como esperado. Isso é ruído metrológico, não verificação de
software. Adicionalmente (NC-3 — MÉDIO): `k=2` fixo com ν_eff baixo (≥2 recals)
subestima a incerteza expandida.

ADR-0025 v2 (validação software estendida ao módulo padrões) referencia "2º
caminho de cálculo" sem fixar a interpretação — esta ADR a crava.

## Decisão

1. **2º caminho de cálculo (cl. 7.11 — verificação de software):** o **mesmo
   mensurando** (valor convencional) calculado por **duas implementações
   independentes** do mesmo modelo metrológico — ex: fórmula fechada (Decimal
   direto) vs cálculo iterativo/decomposto. Convergência dentro de tolerância de
   ponto-flutuante-decimal prova ausência de bug de implementação. Divergência →
   bug de software (bloqueia release / alerta de engenharia), NÃO investigação
   metrológica.

2. **Deriva linear (regressão temporal) NÃO é o 2º caminho** — é **controle de
   estabilidade/tendência**, e pertence à carta de controle Shewhart (regra de
   tendência — ADR-0070 + C-3) ou a análise de estabilidade. Detectar deriva é
   controle metrológico (abre VI/recal/NC), não verificação de software.

3. **Incerteza expandida:** quando ν_eff (graus de liberdade efetivos) < 30,
   calcular k via **Welch-Satterthwaite + t-Student** (tabela GUM Anexo G — a
   mesma já usada no motor GUM de M4 `gum_classico.py`), não k=2 fixo. Reuso do
   motor existente; Decimal puro (sem numpy — DEP-001).

4. **US-PAD-009 reescrita:** AC-PAD-009-1/2/3 passam a refletir "2 implementações
   do mesmo modelo convergem" + "k via Welch-Satterthwaite quando ν_eff baixo".
   A detecção de deriva migra para US-PAD-008 (Shewhart, regra de tendência).

## Consequências

- **Positivas:** elimina falso-positivo de investigação em deriva normal;
  cumpre o real intento da cl. 7.11 (anti-bug de software); incerteza correta em
  ν baixo (defensável em supervisão CGCRE).
- **Custo:** 2 implementações do mesmo modelo + harness de comparação (replay
  determinístico — paralelo ADR-0025). Reusa Welch-Satterthwaite do M4.
- **INV nova:** INV-PAD-009 redefinida — divergência entre as 2 implementações
  do mesmo mensurando bloqueia release (bug); NÃO confundir com controle de deriva.

## Alternativas rejeitadas

- **Plan v1 (2 estimadores diferentes):** rejeitado — falso-positivo + não cumpre
  cl. 7.11 (não prova ausência de bug, compara coisas diferentes).
- **Monte Carlo como 2º caminho:** diferido — numpy bloqueado (DEP-001); para
  padrão de massa/dimensional o modelo é linear, RSS Decimal basta (paralelo M4).

## Relacionados

ADR-0025 v2 (refines) · ADR-0070 (Shewhart — deriva vai pra lá) · motor
`src/domain/metrologia/calibracao/motor_calculo/gum_classico.py` (Welch-Satterthwaite
reuso) · `docs/faseamento/M5-padroes/reviews-consolidado.md` (C-2 + C-3).
