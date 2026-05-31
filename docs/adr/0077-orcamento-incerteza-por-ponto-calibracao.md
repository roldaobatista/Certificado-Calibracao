---
owner: roldao
revisado-em: 2026-05-31
proximo_review: 2026-08-31
status: aceito
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

**Caminho escolhido (decisão Roldão 2026-05-31): b1 + média derivada.**
- **b1 (escolhido):** adicionar `ponto_calibracao` ao `OrcamentoIncertezaSnapshot`
  e produzir N orçamentos (um por ponto). Modelo que a CGCRE espera ver. **Dado-fonte
  e valor reportado no certificado = por ponto.**
- **Média derivada (decisão Roldão):** além do por-ponto, expor um **agregado de
  conveniência** (ex.: `U_media`, e/ou faixa `[U_min, U_max]`) calculado a partir dos
  pontos — para quem quiser a "visão geral" rápida sem ler a tabela inteira. **É
  NÃO-NORMATIVO** (rótulo "visão geral"/resumo): o certificado RBC reporta por ponto;
  a média é só display/busca, nunca substitui o valor por ponto nem vira o U "do
  certificado". Derivada on-the-fly ou materializada como campo de leitura.
- **b2 (não escolhido, mas registrado):** função `U(X)` declarada+justificada pelo RT
  (cl. 7.11) — disponível como evolução futura se algum tenant medir muitos pontos e
  preferir declarar a função; não é o caminho desta frente.
- **Rejeitado (a):** U único aplicado a todos os pontos como default silencioso.

Altera marco FECHADO M4 (entidades + migrations + motor de cálculo + drill) — por
isso exige esta ADR. A validação cl. 7.11 do cálculo de incerteza por ponto entra no
rol de revisão por consultor RBC humano credenciado pré-produção
(`project_sem_contratacoes_externas_ate_producao`).

## Descoberta de-riscante (regra #0 — investigação 2026-05-31)

A premissa inicial da NC-01 ("M4 não tem estrutura por ponto") está **incompleta**: o
model **`OrcamentoPorPonto`** (1:N de `OrcamentoIncerteza`, com `ponto_calibracao`,
`u_combinada_no_ponto`, `U_expandida_no_ponto`, `k_no_ponto`) **JÁ EXISTE** no schema
M4 — tabela (migration 0006) + trigger WORM (0003) + grants (0014) + RLS testada. Foi
provisionado no M4 olhando pra frente, mas **nunca ligado**: o motor
`calcular_orcamento_incerteza` produz só o agregado (1 `U_expandida`) e não popula a
tabela por ponto; não há snapshot de domínio `OrcamentoPorPontoSnapshot` nem use case.

**Logo o retrofit é WIRING, não reconstrução:** não cria tabela/trigger/migration
destrutiva. Escopo real ≈ snapshot de domínio + use case popular por ponto +
repositório + média derivada + testes. Risco muito menor que o estimado pelo RBC.

## Consequências

- **Habilita** `GATE-CAL-EMISSAO-RECONCILIA-FAIXA` + `GATE-ECMC-U-MAIOR-CMC` (M8) —
  a reconciliação por ponto torna-se possível.
- **Retrofit M4 (frente SAN-INCERTEZA-PONTO, ANTES da Fatia 2 do M8):** liga o stub
  `OrcamentoPorPonto` existente — snapshot de domínio `OrcamentoPorPontoSnapshot` +
  use case produz N linhas por ponto + repositório popula + **média derivada**
  (agregado `OrcamentoIncerteza.U_expandida` vira a "visão geral" não-normativa) +
  retrofit testes/drill. Migration aditiva só se faltar coluna (ex.: `nivel_confianca_no_ponto`,
  `grau_liberdade_efetivo_no_ponto` — NC-05); a tabela base já existe. Decisão da forma
  do INPUT por ponto (componentes por ponto vs Tipo A por ponto) = mini-plano revisado
  pelo `tech-lead`.
- **Replay cl. 7.11:** o `replay_determinismo_hash` passa a cobrir o cálculo por
  ponto (fixtures versionadas por ponto).
- Non-goal: não muda a fórmula de cálculo em si, só a granularidade (por ponto).

## Status

🟡 **Proposta — caminho decidido (b1 + média derivada, Roldão 2026-05-31).** Depende
de: ADR-0074, ADR-0076, ADR-0025 v2. Bloqueia: M8 Fatia 2 (`emitir_certificado`).
Aceite formal após **mini-plano do retrofit (frente SAN-INCERTEZA-PONTO) revisado pelo
`tech-lead`** (altera marco fechado M4 — exigência da `ordem-dependencia-bloco-metrologia.md`).
A validação cl. 7.11 do cálculo por ponto = revisão consultor RBC humano credenciado
pré-produção.
