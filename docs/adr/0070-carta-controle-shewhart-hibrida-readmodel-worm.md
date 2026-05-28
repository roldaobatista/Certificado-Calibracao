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

# ADR-0070 — Carta de controle Shewhart híbrida: read-model para visualização + registro WORM congelado da decisão

## Contexto

Revisão `consultor-rbc-iso17025` do plan M5 `metrologia/padroes` (2026-05-28,
NC-1 — ALTO) identificou não-conformidade ISO 17025 cl. 8.4 + cl. 7.5 na
proposta D-PAD-3 do plan v1.

O plan v1 propunha a carta de controle Shewhart (US-PAD-008, perfil A) como
**read-model puro calculado on-demand**: os pontos vêm de
`VerificacaoIntermediaria` + `RecalExternoPadrao` (já WORM), e linha central /
UCL / LCL / σ são recalculados sobre a série inteira a cada acesso. O argumento
(correto) era evitar duplicar pontos e drift.

O problema: os **limites de controle (LC/UCL/LCL/σ) mudam quando a série cresce**.
Quando uma regra Western Electric dispara e o RT analisa e aceita/recalibra, a
cl. 8.4 (registros técnicos por 25a) + cl. 7.5 exigem reconstruir a decisão
metrológica — incluindo **qual era o limite vigente no instante da decisão**.
Com read-model puro, recalcular meses depois muda LC/σ e a resposta ao auditor
CGCRE "qual era o UCL no dia em que você aceitou este ponto?" é impossível.
Decisão metrológica não-reconstruível = NC na 1ª supervisão.

A regra Western Electric também é **software metrológico** (cl. 7.11): mudar uma
regra muda decisões de aceite/recalibração — exige versionamento.

## Decisão

Carta de controle Shewhart **híbrida**:

1. **Visualização = read-model calculado** (mantém D-PAD-3): o gráfico do dia a
   dia (pontos + limites correntes) é calculado on-demand em
   `src/domain/metrologia/padroes/shewhart.py` (Decimal puro), sobre os dados-fonte
   WORM. NÃO se persiste entidade `PontoCartaControle` (evita drift).

2. **Decisão = registro WORM congelado** `AnaliseCartaControle` (entidade nova):
   gravada toda vez que (a) uma regra Western Electric dispara, OU (b) o RT
   registra análise/aceite/recalibração. Campos:
   - `padrao_id` (FK), `tenant_id`
   - `regra_violada` (enum WE — qual das regras; ver ADR-0071-companion / plan)
   - `pontos_referenciados` (FKs às VIs/recals que formaram a janela — NÃO cópia
     dos valores; os valores vivem WORM nas entidades-fonte)
   - `linha_central`, `ucl`, `lcl`, `sigma`, `n_pontos`, `janela_meses` —
     **snapshot congelado dos limites vigentes no instante**
   - `versao_motor_shewhart` (semver + commit — paralelo INV-CAL-VERSAO-001;
     cl. 7.11)
   - `decisao_rt` (enum: ACEITO_COM_JUSTIFICATIVA / RECALIBRAR / SUSPENDER_USO)
   - `justificativa_canonicalizada` + `justificativa_hash` (ADR-0029 + ADR-0064)
   - `assinatura_a3_rt_id` (NULL até A3 plugar — Wave A)
   - hash-chain HMAC ADR-0064 (cadeia global `audit_trail.eventos`)
   - WORM (trigger PG bloqueia UPDATE/DELETE — INV-CAL-WORM-001 estendido)

3. **Alerta/tendência (não só violação dura — corretora FURO-3 C-16):** estado de
   alerta (2-de-3, 4-de-5, tendência) também exige `AnaliseCartaControle`
   registrada (decisao_rt = ACEITO_COM_JUSTIFICATIVA no mínimo) antes de liberar
   uso continuado do padrão.

## Consequências

- **Positivas:** decisão metrológica 100% reconstruível para CGCRE (cl. 8.4);
  gráfico segue barato/sem drift; limites congelados são prova; versão do motor
  rastreável (cl. 7.11).
- **Custo:** 1 entidade WORM nova + trigger + a entidade entra no agregado
  `PadraoMetrologico`. Marginal frente ao risco de NC.
- **INV nova:** INV-PAD-010 — toda regra Western Electric disparada OU aceite de
  ponto em alerta exige `AnaliseCartaControle` WORM antes de liberar uso.

## Alternativas rejeitadas

- **Read-model puro (plan v1):** rejeitado — NC cl. 8.4 (decisão não-reconstruível).
- **Persistir todos os pontos (`PontoCartaControle`):** rejeitado — drift + os
  pontos já são WORM nas entidades-fonte; redundância sem ganho probatório
  (o que importa é o limite no instante da decisão, não re-guardar o ponto).

## Escopo / non-goals

- Perfil A obrigatório (US-PAD-008 + INV-PAD-008). Perfis B/C/D: feature oculta.
- Imagem PNG / CSV da carta no dossiê = Wave B+ (US-PAD-006 AC-2).
- O conjunto exato de regras Western Electric + parâmetros vira artefato de
  validação de software (cl. 7.11) — assinatura por pessoa credenciada quando
  houver tenant A real (diferido pré-produção).

## Relacionados

ADR-0025 v2 (validação software 7.11) · ADR-0029 (canonicalização) · ADR-0064
(HMAC 25a) · ADR-0067 (perfil) · ADR-0071 (2º caminho — companion) ·
INV-CAL-WORM-001 · `docs/faseamento/M5-padroes/reviews-consolidado.md` (C-1).
