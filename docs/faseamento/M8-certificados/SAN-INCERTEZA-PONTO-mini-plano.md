---
owner: agente-ia
revisado-em: 2026-05-31
status: ready-for-tasks
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

## Decisões pós-revisão (tech-lead + RBC 2026-05-31 — AMBOS APROVA COM CORREÇÕES)

### Tech-lead (arquitetura)
- **Q-RETRO-1 = (b):** use case recebe componentes base + leituras; deriva Tipo A
  (s_x) por ponto das repetições; **motor GUM NÃO muda** (já é "por chamada" — N
  chamadas a `propagar()`). Único "caller" é teste → retrofit barato.
- **Q-RETRO-2 = manter agregado** `OrcamentoIncerteza` como **pior-caso (max U)**,
  NÃO-NORMATIVO; NÃO depreciar nem trocar por `U_media` (quebraria 3 consumers +
  teste M4 sem ganho). O help_text do model JÁ diz "pior caso".
- **Q-RETRO-3 = ambos hashes:** `replay_determinismo_hash_no_ponto` por ponto +
  hash agregado de fecho encadeando os por-ponto (tamper-evidence composicional).
- **Migration aditiva OBRIGATÓRIA (não condicional), 3 colunas + índice, ANTES do
  repositório:** `nivel_confianca_no_ponto`, `grau_liberdade_efetivo_no_ponto`,
  `replay_determinismo_hash_no_ponto` + `Index(tenant, orcamento_incerteza)`.
  Colunas NULL-áveis (tabela vazia; trigger WORM permite INSERT — zero risco).
- Protocol `OrcamentoIncertezaRepository.salvar_orcamento_com_componentes` ganha
  `pontos=()` (default) na MESMA transação atômica. Atualizar Fake + Django impl.
- **TL-A-03 (registrar, não codar):** `avaliar_conformidade` também é por ponto
  (zona ILAC G8 por ponto) — dependência conhecida do M8, não desta fatia.

### Consultor-RBC (física — base GUM/NIT-DICLA-030/EA-4/02/ILAC-P14)
- **Q-RBC-1 (Tipo B):** resolução (UUT+padrão) = CONSTANTE absoluto ✅; incerteza do
  padrão + deriva = `a+b·X` (NÃO opt-in puro). **1ª fatia segura:** Tipo B constante
  **+ portão fail-closed: padrão com `b≠0` no certificado/CMC NÃO emite RBC** (espera
  fatia 2 do escalonamento) — senão subestima U nos pontos altos = NC CGCRE. Campo
  `lei_escalonamento ∈ {CONSTANTE, PROPORCIONAL, LINEAR_AFIM}` + `coef_a`/`coef_b` por
  componente; defaults por origem pré-preenchidos, RT confirma.
- **Q-RBC-2 (n<6 por ponto):** híbrido perfil-aware — n≥6→Tipo A normal; 2≤n<6→tenta
  **s_pooled** do procedimento (continua Tipo A, GUM §4.2.4), senão **fail-closed
  perfil A** / ressalva registrada B/C/D; n<2→sem Tipo A, registrado. **Nunca
  silencioso** — gravar `metodo_tipo_a_ponto ∈ {SX_PROPRIO, S_POOLED, AUSENTE}` +
  `n_repeticoes_ponto`.
- **Q-RBC-3 (visão geral):** **pior caso (max U)** confirmado. Média aritmética =
  enganosa, NÃO exibir. Rótulo obrigatório "**U máxima na faixa**" (não "U da
  calibração"/"U média"); não usar pra conformidade de ponto; não substitui por-ponto.

### Campos novos do `OrcamentoPorPontoSnapshot` (consolidado)
`ponto_calibracao`, `u_combinada_no_ponto`, `U_expandida_no_ponto`, `k_no_ponto`
(já no model) + `nivel_confianca_no_ponto`, `grau_liberdade_efetivo_no_ponto`,
`replay_determinismo_hash_no_ponto`, `metodo_tipo_a_ponto`, `n_repeticoes_ponto`,
`lei_escalonamento_aplicada` (migration aditiva).

### Escalar a humano credenciado pré-produção (`project_sem_contratacoes_externas_ate_producao`)
1. Coeficientes `a,b` por componente/grandeza (Q-RBC-1). 2. Validação do `s_pooled`
(Q-RBC-2 — registro cl. 7.2.2). 3. Revalidação software cl. 7.11 do cálculo por ponto
(ADR-0025 — URS+OQ+replay por ponto). Minuta ~80% pronta. ~R$5-15k quando 1º tenant A real.

## Veredito

Mini-plano **`ready-for-tasks`** (tech-lead + RBC APROVA COM CORREÇÕES, incorporadas).
Próximo: `/tasks` SAN-INCERTEZA-PONTO (fatias: domínio snapshot → migration aditiva 3
colunas+índice → use case por ponto + portão b≠0 + n<6 perfil-aware → repositório →
testes/drill/replay por ponto → reverde M4) → implement → então M8 Fatia 2 (reconciliação).
**INV nova:** INV-CAL-INC-005 (incerteza por ponto + agregado pior-caso) a cravar nas tasks.
