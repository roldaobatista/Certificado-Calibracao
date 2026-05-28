---
owner: roldao
revisado-em: 2026-05-28
status: needs-v2
fase: M5-padroes
dominio: metrologia
modulo: padroes
ritual: plan
versao: 1
depende-de: docs/faseamento/M5-padroes/spec.md
reviews-concluidas:
  - consultor-rbc-iso17025 (AJUSTAR 5/5 — 3 ALTO)
  - tech-lead-saas-regulado (APROVA COM CORREÇÕES + drift C-6)
  - advogado-saas-regulado (AJUSTAR/OK)
  - corretora-seguros-saas (AJUSTAR — 2 furos bloqueantes)
consolidacao: docs/faseamento/M5-padroes/reviews-consolidado.md
---

# Plano técnico — M5 `metrologia/padroes`

> ⚠️ **v1 REVISADO 2026-05-28 — status `needs-v2`.** As 4 revisões dos subagentes
> exigem correções obrigatórias (C-1..C-16) antes de `/tasks` — ver
> `reviews-consolidado.md`. 3 ALTO metrológicos + 2 furos de risco bloqueantes +
> 1 drift-docs. Pendências antes de codar: **plan v2 + 2 ADRs novas** (Shewhart
> híbrido WORM; "2º caminho" = 2 implementações do mesmo mensurando) + 1 ADR curta
> (assimetria de path). **NADA de código até plan v2 + ADRs aprovados**
> (INV-RITUAL-001).

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

PRD §7 todos AC verdes · INV-PAD-001..009 em REGRAS + testes · drill estrutural
verde · GATE-PAD-PORTA-M4 (suíte M4 reverde) · 10 auditores PASS ZERO C/A/M
(INV-RITUAL-001) · ruff/mypy limpos · paginação herdada.

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

Revisão dos 4 subagentes desta `plan.md` → consolidar respostas (emendas
inline + ADRs se decisão estrutural mudar, ex: Shewhart congelado) → `/tasks`.
**Sem código antes do plan aprovado.**
