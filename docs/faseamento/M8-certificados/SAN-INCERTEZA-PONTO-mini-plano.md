---
owner: agente-ia
revisado-em: 2026-05-31
status: draft
diataxis: reference
audiencia: [agente, tech-lead, consultor-rbc, roldao]
marco: M8-certificados
tipo: mini-plano-retrofit
relacionados:
  - docs/adr/0077-orcamento-incerteza-por-ponto-calibracao.md
  - docs/faseamento/M8-certificados/reviews-consolidado.md
---

# Mini-plano — frente SAN-INCERTEZA-PONTO (retrofit M4: incerteza por ponto)

> Item #0 do M8. Reabre marco FECHADO M4 → exige revisão `tech-lead` (ordem-dependencia).
> Decisão Roldão (2026-05-31): **incerteza por ponto + média derivada** (ADR-0077 b1).

## Estado real (regra #0 — investigado)

- `OrcamentoIncerteza` (model + snapshot) = **1 por calibração**, `U_expandida` único,
  produzido por `calcular_orcamento_incerteza.executar(componentes...)` via GUM.
- `OrcamentoPorPonto` (model `infrastructure/calibracao/models.py:1092`) **JÁ EXISTE**:
  `ponto_calibracao`, `u_combinada_no_ponto`, `U_expandida_no_ponto`, `k_no_ponto`,
  FK→OrcamentoIncerteza, UNIQUE `(tenant, orcamento, ponto)`, trigger WORM (0003),
  grants (0014), RLS. **Nunca populado** — sem snapshot de domínio, sem use case, sem motor.
- `LeituraSnapshot` tem `ponto_calibracao` + `numero_repeticao` → repetições por ponto
  já permitem derivar s_x (Tipo A) por ponto.

## Escopo do retrofit (aditivo — não destrutivo)

1. **Domínio:** `OrcamentoPorPontoSnapshot` (frozen VO: `ponto_calibracao`,
   `u_combinada_no_ponto`, `U_expandida_no_ponto`, `k_no_ponto`, + NC-05:
   `nivel_confianca_no_ponto`, `grau_liberdade_efetivo_no_ponto`).
2. **Motor/use case:** `calcular_orcamento_incerteza` passa a produzir **N orçamentos
   por ponto** + o agregado-média. Forma do input por ponto = **Q-RETRO-1** (abaixo).
3. **Média derivada:** o `OrcamentoIncerteza.U_expandida` agregado vira a "visão geral"
   NÃO-NORMATIVA (ex.: `U_media` ou faixa `[U_min,U_max]` dos pontos) — rótulo resumo,
   nunca substitui o por-ponto (decisão Roldão).
4. **Repositório:** `salvar_orcamento_com_componentes` estende para persistir os
   `OrcamentoPorPonto` na mesma transação atômica.
5. **Migration:** SÓ se faltarem colunas (NC-05 `nivel_confianca_no_ponto` /
   `grau_liberdade_efetivo_no_ponto`) — aditiva (`ADD COLUMN`); a tabela base existe.
6. **Testes/drill:** retrofit `validar_m4_calibracao` (já lista `orcamento_por_ponto`
   estruturalmente — agora popular) + testes de cálculo por ponto + replay cl. 7.11 por ponto.
7. **Seam p/ M8:** porta de leitura `U(ponto)` que a reconciliação de certificados consome.

## Perguntas de revisão (rotear — NÃO inventar)

**Para `tech-lead` (forma do input + transação):**
- **Q-RETRO-1 (CRÍTICA):** forma do INPUT por ponto. Opções:
  (a) o caller passa `componentes` POR PONTO (tupla de tuplas — RT/import entra budget por ponto);
  (b) o use case recebe componentes "base" + as leituras, e deriva o Tipo A (s_x) por ponto
  das repetições, mantendo os Tipo B (resolução/deriva) compartilhados ou escalados;
  (c) híbrido: componentes marcados como `por_ponto: bool`.
  Qual minimiza retrofit de caller e mantém o motor puro?
- **Q-RETRO-2:** o agregado-média — manter o `OrcamentoIncerteza` atual como média
  derivada (compat com callers existentes) ou marcá-lo deprecado e expor `U_media` novo?
  Impacto nos consumers atuais de `OrcamentoIncertezaSnapshot.U_expandida` (avaliar_conformidade,
  visao_360, queries/orcamento).
- **Q-RETRO-3:** o replay determinístico (`replay_determinismo_hash` ADR-0025) — um hash
  por ponto, um hash agregado, ou ambos? (cl. 7.11 — reprodutibilidade por ponto).

**Para `consultor-rbc` (já consultado na spec — confirmar só se Q-RETRO-1 mudar a física):**
- A derivação de s_x (Tipo A) por ponto a partir das repetições da própria
  `LeituraSnapshot` é metrologicamente correta (n≥6 por ponto — INV-CAL-INC-003)?

## Veredito

Mini-plano `draft` para revisão `tech-lead`. Após APROVA COM CORREÇÕES → tasks
SAN-INCERTEZA-PONTO → implement (fatias) → reverde M4 → então M8 Fatia 2.
