---
owner: roldao
revisado-em: 2026-05-29
status: v2-ready-for-tasks
fase: M5-padroes
dominio: metrologia
modulo: padroes
ritual: plan
versao: 2
depende-de: docs/faseamento/M5-padroes/spec.md
reviews-concluidas:
  - consultor-rbc-iso17025 (AJUSTAR 5/5 — 3 ALTO)
  - tech-lead-saas-regulado (APROVA COM CORREÇÕES + drift C-6)
  - advogado-saas-regulado (AJUSTAR/OK)
  - corretora-seguros-saas (AJUSTAR — 2 furos bloqueantes)
consolidacao: docs/faseamento/M5-padroes/reviews-consolidado.md
adrs-emitidas-v2:
  - 0070 (Shewhart híbrido read-model + WORM)
  - 0071 (2º caminho = 2 implementações mesmo mensurando)
  - 0072 (path metrologia/* aninhado)
---

# Plano técnico — M5 `metrologia/padroes`

> ✅ **v2 (2026-05-28) — `ready-for-tasks`.** As 16 correções (C-1..C-16) das 4
> revisões foram resolvidas: ver §14 (deltas) + ADR-0070/0071/0072 (estruturais)
> + emendas PRD §8 (C-13/C-14). O corpo v1 abaixo (§1-§13) permanece como
> contexto; §14 SUPERSEDE onde diverge. Próximo passo: `/tasks`.

> **Ritual:** este é o `/plan`. Antes de `/tasks` + `/implement`, os 4 subagentes
> revisam (seções §9 trazem as perguntas dirigidas a cada um). Reusa padrões já
> cravados em M4 `calibracao` (CAS optimistic lock, advisory lock hash-chain,
> HMAC versionado ADR-0064, RLS pattern v2, triggers WORM) — **não reinventar**.

## 1. Arquitetura de camadas (ADR-0007 spec-as-source)

```
src/domain/metrologia/padroes/          # PURO — sem Django
  entities.py        PadraoMetrologicoSnapshot + filhas + snapshots WORM
  enums.py           EstadoPadrao, VinculacaoCadeia, ClassePadrao, SubtipoPadrao,
                     StatusRecal, ResultadoVI, ResultadoPT
  repository.py      Protocols (PadraoRepository, RecalRepository, VIRepository, PTRepository)
  shewhart.py        regras Western Electric + cálculo UCL/LCL (puro Decimal)
  valor_convencional.py  2º caminho de cálculo (ADR-0025 v2) — puro
  (VOs reusados de src/domain/metrologia/value_objects.py — NÃO recriar)

src/application/metrologia/padroes/     # use cases (orquestram Protocols)
  cadastrar_padrao.py / registrar_recal_{envio,retorno}.py /
  registrar_verificacao_intermediaria.py / registrar_intercomparacao_{inicio,resultado}.py /
  baixar_padrao.py / calcular_valor_convencional.py / carta_shewhart.py (query) /
  queries/ (disponiveis_para_calibracao, dossie_cgcre, cartas)

src/infrastructure/metrologia/padroes/  # Django ORM + raw SQL
  models.py / migrations/ / repositories.py (adapters) /
  query_service.py (PadraoMetrologicoQueryService real — porta M4) /
  serializers.py / views.py (PadraoViewSet = T-CAL-130) / urls.py / jobs.py
```

Nota de path: M4 usou `src/infrastructure/calibracao/` (sem subpasta `metrologia`).
**Decisão a confirmar (tech-lead):** seguir `src/infrastructure/metrologia/padroes/`
(modelo-de-domínio §schema diz isso) OU achatar pra `src/infrastructure/padroes/`
por consistência com calibracao. Proposta: seguir o modelo (`metrologia/padroes`).

## 2. Decisões técnicas-chave (com justificativa)

### D-PAD-1 — Concorrência (reuso ADR-0065)
`PadraoMetrologico.revision` (int) + CAS optimistic (`atualizar_com_lock`
WHERE revision=esperada) idêntico a `Calibracao`. Transições de estado
(EM_USO↔EM_RECAL↔PT) via CAS. Sem advisory lock por padrão (não há hash-chain
por-padrão de alta contenção como em calibracao; eventos `padrao.*` vão pra
cadeia GLOBAL `audit_trail.eventos`, cujo advisory lock já existe em
`event_helpers`). **Confirmar com tech-lead.**

### D-PAD-2 — INV-PAD-006: incertezas só via recal (trigger PG)
Trigger BEFORE UPDATE em `padrao_metrologico`: se `incertezas_certificado` OU
`validade_certificado_rastreabilidade` mudou E a sessão não está dentro do
fluxo `registrar_recal_retorno` (sinalizado por GUC `app.padrao_recal_em_curso`
setado pelo use case, análogo ao padrão de `perfil_no_evento`), RAISE. Espelha
`audit-immutability` + os triggers de calibracao. **Confirmar com tech-lead** se
GUC-flag é o mecanismo certo vs coluna de controle.

### D-PAD-3 — Shewhart: READ-MODEL calculado (não persistir pontos)
Os pontos da carta derivam de `VerificacaoIntermediaria` + `RecalExternoPadrao`
(valor_convencional histórico). UCL/LCL/linha-central calculados on-demand em
`shewhart.py` (puro Decimal). NÃO criar entidade `PontoCartaControle`. Razão:
(a) evita duplicação/drift; (b) os dados-fonte já são WORM; (c) recalcular é
barato (≤24 meses de pontos). O alerta Western Electric (AC-PAD-008-2) é
disparado pelo use case `registrar_verificacao_intermediaria` ao detectar regra
violada na série atualizada → cria evento + bloqueia uso (estado lógico, não
muda `estado` do padrão; usa flag `bloqueado_por_carta_controle`). **REVISÃO
CRÍTICA `consultor-rbc-iso17025`:** read-model é aceitável para CGCRE ou a carta
precisa ser "congelada"/persistida como registro probatório imutável (cl. 8.4)?

### D-PAD-4 — 2º caminho de cálculo do valor convencional (ADR-0025 v2)
`valor_convencional.py` puro: Caminho A = média ponderada por incerteza dos
certs externos anteriores; Caminho B = GUM com modelo de variação temporal
(deriva linear). Compara desvio vs `k·u_combined` (k=2). Se >, retorna
`investigacao_requerida=True` → use case dispara alerta P1 + bloqueia.
**REVISÃO CRÍTICA `consultor-rbc-iso17025`:** o modelo de Caminho B (deriva
linear) é metrologicamente aceitável ou precisa de modelo mais rico? numpy
ainda bloqueado (DEP-001) — Caminho B em Decimal puro como o GUM de M4.

### D-PAD-5 — Porta M4 + snapshot ⚠️ REVISADO (C-6 drift + corretora 4 furos)
`PadraoUsadoSnapshot` (VO frozen) com TODOS os campos do padrão no momento da
seleção (INV-CAL-SNAP-001) **+ leitura ambiental dos auxiliares (C-8)**. M4 já
tem `PadraoUsado.snapshot_padrao_json`.
**Correção C-6:** `EmptyPadraoMetrologicoQueryService` NÃO existe — porta é NOVA
adição (funções de módulo estilo `certificados/query_service.py`, **fail-CLOSED**).
`padrao_bloqueado_para_uso` retorna `(True, motivo)` se: estado != EM_USO ·
recal vencido · **recal retornado pendente aprovação RT (C-4 FURO-1)** · VI
reprovada pendente · PT rejeitado · carta Shewhart violada **OU em alerta/trend
(C-16 FURO-3)** · auxiliar consumido vencido (INV-PAD-007) · **rastreabilidade
da origem revogada (C-5 FURO-4)** · [faixa/grandeza fora de uso — C-15 FURO-2:
decidir bloquear aqui vs delegar EXPLÍCITO a M4/escopos-cmc].
**GATE-PAD-PORTA-M4:** ADIÇÃO ao M4 (chamar `padrao_bloqueado_para_uso` antes de
gravar `PadraoUsado`) + testes NOVOS do caminho bloqueado + suíte 629 reverde.

### D-PAD-6 — HMAC hash-chain (reuso ADR-0064)
Eventos `padrao.*` vão pra cadeia global `audit_trail.eventos` via
`publicar_evento` (mesmo helper de M1-M4), com sanitização na escrita
(`localizacao_lab`/cert PDF/responsavel só hash) + `perfil_no_evento` no
envelope (INT-03). Não há cadeia por-padrão separada (decisão D-PAD-1).

### D-PAD-7 — Equipamentos auxiliares (US-PAD-007) no mesmo agregado
`subtipo` discrimina PRINCIPAL/AUXILIAR_*. Auxiliar: recal externo OPCIONAL
(pode ter calibração interna), VI obrigatória. `consome_auxiliar_ids: list`
no padrão principal → INV-PAD-007 bloqueia uso se auxiliar consumido vencido.
**Confirmar com `consultor-rbc-iso17025`** o vínculo principal↔auxiliar.

## 3. Schema (P2) — tabelas + RLS pattern v2 + WORM

- `padrao_metrologico` (raiz) — UNIQUE `(tenant_id, numero_serie)`, `revision`,
  vigência ADR-0030, soft-delete B ADR-0031, `subtipo`, `consome_auxiliar_ids`.
- `recal_externo_padrao` — imutável pós `retornado_em` (trigger).
- `verificacao_intermediaria` — WORM.
- `intercomparacao_pt` — WORM.
- Triggers: `padrao_incertezas_so_via_recal` (INV-PAD-006),
  `padrao_block_delete` (INV-SOFT-002), WORM em VI/PT/recal-retornado.
- Extensões pgcrypto/btree_gist já presentes (init scripts). RLS NOBYPASS.

## 4. Faseamento detalhado (vira `/tasks`)

P1 domínio puro (entidades+enums+shewhart+valor_convencional+invariantes) ·
P2 migrations+RLS+triggers · P3 use cases · P4 porta+query_service+GATE-PAD-PORTA-M4 ·
P5 PadraoViewSet (T-CAL-130)+serializers+urls (paginação F-C3 herdada) ·
P6 jobs (recal vencendo/VI pendente/recal>90d) · P7 INV-PAD-* em REGRAS+hooks ·
P8 reconciliação+drill `validar_m5_padroes` (estrutural + GATE-PAD-DRILL-LOCAL) ·
P9 10 auditores Família 5.

## 5. Riscos + mitigações

- **R1 Shewhart probatório** (D-PAD-3) — se RBC exigir carta congelada, vira
  entidade WORM `CartaControleSnapshot` no fechamento da VI. Mitiga: decisão no
  review ANTES de P1.
- **R2 numpy bloqueado** — Caminho B + Shewhart em Decimal puro (como GUM M4).
- **R3 porta M4 quebra suíte 629** — P4 roda suíte M4 chave antes de fechar.
- **R4 perfil-aware** — predicate `tenant_perfil_e` já existe (SAN-PERFIL Sprint 2);
  reusar, não recriar. Fail-closed.

## 6. Reuso explícito (não reinventar)

`publicar_evento` + hash-chain (M1-M4) · `tenant_perfil_e` (SAN-PERFIL) ·
HMAC `hash_versionado` + helpers crypto (M4) · RLS pattern v2 templates ·
CAS optimistic `atualizar_com_lock` (M4) · VOs metrológicos · paginação F-C3 ·
canonicalização texto probatório ADR-0029 (método VI / acao_corretiva).

## 7. Critérios de pronto (Definition of Done M5)

PRD §7 todos AC verdes · INV-PAD-001..010 em REGRAS + testes · drill estrutural
verde · GATE-PAD-PORTA-M4 (suíte M4 reverde) · auditores PASS ZERO C/A/M sob
roteamento INV-RITUAL-003 (essenciais sempre + roteados por área) · ruff/mypy
limpos · paginação herdada.

## 8. Non-goals do plano (confirmam spec §3)

PDF/A dossiê (Wave B+) · calibração interna de padrão · padrão emprestado ·
persistir pontos Shewhart (D-PAD-3, salvo veto RBC) · numpy/Monte Carlo.

## 9. Perguntas dirigidas aos revisores

### consultor-rbc-iso17025 (CRÍTICO — metrologia)
1. D-PAD-3: carta Shewhart como read-model calculado é aceitável p/ CGCRE, ou
   precisa ser registro congelado imutável (cl. 8.4)?
2. D-PAD-4: Caminho B (deriva linear em Decimal) é metrologicamente defensável
   p/ valor convencional, ou exige modelo mais rico?
3. Western Electric: as 4 regras do AC-PAD-008-2 estão corretas/completas p/
   padrão metrológico (vs as de processo industrial)?
4. US-PAD-007: vínculo principal↔auxiliar (cl. 6.4.5) — modelagem suficiente?
5. Intervalos VI por classe (E1/E2/F1/F2) — há valores canônicos OIML/NIT a cravar?

### tech-lead-saas-regulado (arquitetura)
1. D-PAD-1: CAS sem advisory lock por-padrão — correto (eventos vão p/ cadeia global)?
2. D-PAD-2: GUC-flag `app.padrao_recal_em_curso` p/ INV-PAD-006 vs coluna de controle?
3. Path `src/infrastructure/metrologia/padroes/` vs `src/infrastructure/padroes/`?
4. GATE-PAD-PORTA-M4: trocar adapter sem quebrar a suíte 629 — estratégia de migração?

### advogado-saas-regulado (LGPD/contratos)
1. PRD §8 afirma "padrão não contém PII direta" — `responsavel_envio`/`executor`
   (user_id) — confirmar hash-only nos eventos é suficiente (sem retenção extra)?
2. Cert externo PDF no storage — base legal art. 7º II ok? Retenção 25a cl. 8.4.

### corretora-seguros-saas (risco)
1. Padrão vencido usado em calibração = risco E&O — a barreira `padrao_bloqueado_para_uso`
   (D-PAD-5) cobre o vetor de sinistro? Falta algum estado de bloqueio?

## 10. Próximo passo

`/tasks` (M5-padroes/tasks.md) derivando das fases P1-P9 (§4) **com os deltas v2
da §14 aplicados**. Sem código antes de `/tasks`.

## 14. Plan v2 — deltas das revisões (SUPERSEDE §1-§13 onde diverge)

Resolução de C-1..C-16 (`reviews-consolidado.md`). Estruturais → ADR.

- **C-1 (Shewhart híbrido) → ADR-0070.** D-PAD-3 atualizada: read-model p/ gráfico
  + entidade WORM `AnaliseCartaControle` (snapshot congelado da decisão: LC/UCL/LCL/σ
  + `versao_motor_shewhart` + decisao_rt + justificativa canon + hash). **INV-PAD-010**
  nova. Entra no agregado + P2 (migration) + P3 (use case dispara no registro de VI).
- **C-2 + C-3 (2º caminho + Welch-Satterthwaite) → ADR-0071.** D-PAD-4 reescrita:
  2º caminho = 2 implementações do MESMO mensurando (anti-bug software cl. 7.11),
  NÃO 2 estimadores. Deriva linear → controle de tendência na carta (US-PAD-008).
  k via Welch-Satterthwaite/t-Student (reuso `gum_classico.py`) quando ν_eff<30.
  **US-PAD-009 reescrita** (emenda PRD pendente no /implement).
- **C-3 (Western Electric) → ADR-0070 + shewhart.py.** Regras 2 e 3 com "mesmo
  lado"; **adicionar regra de tendência** (7 pontos monotônicos — detecta deriva,
  Dor #04); motor versionado. **AC-PAD-008-2 emendar** no /implement.
- **C-4 (FURO-1) + C-5 (FURO-4) + C-16 (FURO-3):** `padrao_bloqueado_para_uso`
  (D-PAD-5 já atualizada) ganha: `recal_retornado_pendente_aprovacao_RT`,
  `rastreabilidade_origem_revogada` (flag por evento externo, paralelo ADR-0045),
  carta em alerta/trend. Estado novo intermediário: `RECAL_RETORNADO_PENDENTE_APROVACAO`.
- **C-6 (drift porta) → corrigido** em spec §7 + D-PAD-5: porta nova, funções de
  módulo estilo `certificados/query_service.py`, **fail-CLOSED**, entregue com
  ponto de consumo no M4 + testes novos. GATE-PAD-PORTA-M4 = adição (não troca).
- **C-7 → ADR-0071** (Welch-Satterthwaite — coberto acima).
- **C-8 (auxiliar):** `VinculoAuxiliar` entidade temporal N:N (ADR-0030) com
  grandeza de influência (temp/umidade/pressão) + leitura ambiental no
  `PadraoUsadoSnapshot`; intervalos próprios (corrigir AC-PAD-007-4 no /implement).
- **C-9 (intervalos):** NÃO cravar valores OIML R111 (R111 não define
  periodicidade). `intervalo_recal_meses`/`intervalo_vi_meses` configuráveis +
  `criterio_intervalo` justificado (cl. 6.4.7 + ILAC-G24). Enum `classe` mantém.
- **C-10 (GUC):** `app.padrao_recal_em_curso` no RESET do pool
  (`_resetar_app_settings_na_conexao`) + `SET LOCAL`. **Variante preferida
  (avaliar em P2):** derivar `incertezas_certificado` como READ-MODEL do último
  `RecalExternoPadrao` retornado vigente → trigger bloqueia QUALQUER UPDATE direto
  e o GUC some. Decisão final no /tasks com base em complexidade da migration.
- **C-11:** anotado — advisory-lock-por-tenant na cadeia global; hot path baixo.
- **C-12 (path) → ADR-0072.** `src/infrastructure/metrologia/padroes/`; M4 fica
  dívida; NÃO mexer no M4.
- **C-13 + C-14 (advogado) → emenda PRD §8** (feita neste lote) + linha matriz
  retenção (executor de evento de padrão; 5a quente / 25a evidência ISO; PDF cert
  externo cifrado por chave KMS tenant — PII de terceiro possível).
- **C-15 (FURO-2 faixa/grandeza):** **decisão:** a adequação faixa/grandeza↔ponto
  é validada no **Marco 4** (onde o ponto de calibração existe) via `cmc_cobre` +
  faixa do padrão; `padrao_bloqueado_para_uso` valida SAÚDE do padrão.
  `snapshot_para_uso` expõe `grandezas`+`faixas`+`incertezas` p/ M4 decidir.
  **Delegação EXPLÍCITA documentada** (não gap silencioso — R-042).

### INVs novas v2

- **INV-PAD-010** — toda regra Western Electric disparada / aceite de ponto em
  alerta exige `AnaliseCartaControle` WORM antes de liberar uso (ADR-0070).
- **INV-PAD-009** redefinida (ADR-0071) — divergência entre as 2 implementações
  do mesmo mensurando bloqueia release (bug de software), distinta de controle de deriva.

### Estados v2 (atualiza spec §4 / modelo)

`EM_USO` · `EM_RECAL_EXTERNO` · **`RECAL_RETORNADO_PENDENTE_APROVACAO`** (novo —
C-4) · `INTERCOMPARACAO_PT_EM_CURSO` · `BAIXADO` · `SUCATEADO`. Flag transversal
`rastreabilidade_origem_revogada` (C-5) bloqueia uso independente do estado.
