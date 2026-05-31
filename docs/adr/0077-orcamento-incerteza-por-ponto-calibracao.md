---
owner: roldao
revisado-em: 2026-05-31
proximo_review: 2026-08-31
status: proposta
diataxis: explanation
audiencia: agente
tipo: adr
---

# ADR-0077 — Orçamento de incerteza por ponto de calibração (retrofit M4)

## Contexto

A revisão `consultor-rbc-iso17025` da spec do M8 `certificados` (2026-05-31,
`docs/faseamento/M8-certificados/reviews-consolidado.md` NC-01 CRÍTICO) revelou um
descompasso estrutural entre o modelo de dados do M4 (marco FECHADO) e o que a
emissão de certificado RBC exige:

- A reconciliação de cobertura na emissão (ADR-0074 cond. 2 / INV-ECMC-009 /
  ILAC-P14 §5.5) compara **`U(ponto) ≥ CMC(ponto)`** — e a CMC varia por ponto
  (publicada como `a + b·X`; `EscopoCMCSnapshot.cmc_em(ponto)` já calcula por ponto).
- Mas o `OrcamentoIncertezaSnapshot` (M4) é **1:1 com a calibração** — UM único
  `U_expandida`. O `ComponenteIncertezaSnapshot` (1:N) **não carrega `ponto_calibracao`**.
- Logo, hoje não existe `U(ponto)`. Reconciliar com um U único aplicado a todos os
  pontos produz falso-PASS (onde a CMC sobe acima do U único) e falso-bloqueio
  (onde a CMC desce abaixo). É metrologicamente incorreto para RBC.

Fundamento normativo: o cálculo da incerteza (JCGM 100:2008 cl. 5 + G.4) avalia `u_c`
e `U = k·u_c` a partir dos componentes **no ponto de medição** (repetibilidade Tipo A
medida por ponto; resolução/deriva/contribuição do padrão avaliadas no valor).
NIT-DICLA-030 rev. 15 e a prática consolidada do certificado RBC reportam uma linha
por ponto (valor nominal, valor medido, correção, **U no ponto**, k). Um único U para
toda a faixa é NC de supervisão, exceto grandeza com incerteza comprovadamente constante.

## Perfil regulatório (ADR-0067 §4)

Esta decisão é dirigida pelo **perfil A (RBC acreditado)**, onde a reconciliação
`U(ponto) ≥ CMC(ponto)` é OBRIGATÓRIA (matriz `docs/conformidade/comum/matriz-feature-perfil.md`
linha "U≥CMC na emissão" — ✅ A / ⚪ N/A B/C/D, pois B/C/D não têm CMC acreditada). O
cálculo de incerteza por ponto vale também para B/C (capacidade interna declarada,
matriz "GUM clássico" ✅ A/B/C); em perfil D a incerteza é ⚪ opcional. Nenhuma
emenda à matriz-feature-perfil é necessária — a granularidade por ponto refina
features já existentes, não cria feature nova de tema sensível.

## Decisão

O orçamento de incerteza deixa de ser 1:1 com a calibração e passa a ser **por
ponto de calibração**. A forma canônica é a tabela do certificado: para cada
`ponto_calibracao` medido → `{valor_medido, correção, u_combinada, k, U_expandida,
grau_liberdade_efetivo (ν_eff), nivel_confianca}`.

Caminhos de implementação (decididos no `/plan` do retrofit, sob revisão `tech-lead`):
- **Preferido (b1):** adicionar `ponto_calibracao` ao `OrcamentoIncertezaSnapshot`
  e produzir N orçamentos (um por ponto). Modelo que a CGCRE espera ver.
- **Ponte aceitável (b2):** função de incerteza `U(X)` declarada e justificada pelo
  RT (espelha a forma `a + b·X` da CMC), avaliada por ponto na emissão. Só legítima
  com método de interpolação **validado e declarado** (cl. 7.11) — o software não
  inventa interpolação.
- **Rejeitado (a):** U único aplicado a todos os pontos como default silencioso.

Altera marco FECHADO M4 (entidades + migrations + motor de cálculo + drill) — por
isso exige esta ADR. A validação cl. 7.11 do cálculo de incerteza por ponto entra no
rol de revisão por consultor RBC humano credenciado pré-produção
(`project_sem_contratacoes_externas_ate_producao`).

## Consequências

- **Habilita** `GATE-CAL-EMISSAO-RECONCILIA-FAIXA` + `GATE-ECMC-U-MAIOR-CMC` (M8) —
  a reconciliação por ponto torna-se possível.
- **Retrofit M4:** `OrcamentoIncertezaSnapshot` ganha `ponto_calibracao` (ou
  estrutura por ponto) + migration aditiva + ajuste do motor de cálculo para produzir
  U por ponto + retrofit dos testes/drill M4. Frente própria (SAN-INCERTEZA-PONTO),
  ANTES da Fatia 2 do M8 (emitir_certificado).
- **Replay cl. 7.11:** o `replay_determinismo_hash` passa a cobrir o cálculo por
  ponto (fixtures versionadas por ponto).
- Non-goal: não muda a fórmula de cálculo em si, só a granularidade (por ponto).

## Status

🟡 **Proposta** (2026-05-31). Depende de: ADR-0074, ADR-0076, ADR-0025 v2.
Bloqueia: M8 Fatia 2 (`emitir_certificado`). Decisão de aceite + caminho (b1 vs b2) =
Roldão, após mini-plano do retrofit revisado pelo `tech-lead` (altera marco fechado).
