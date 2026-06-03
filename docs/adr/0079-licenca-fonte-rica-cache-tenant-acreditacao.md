---
owner: roldao
revisado-em: 2026-06-02
proximo_review: 2026-09-02
status: aceito
diataxis: explanation
audiencia: agente
tipo: adr
---

# ADR-0079 — `Licenca` (acreditação CGCRE) é fonte de verdade rica; `Tenant.acreditacao_*` é cache sincronizado unidirecionalmente via `aplicar_evento_cgcre`

## Contexto

O M8 `certificados` (FECHADO) lê a vigência da acreditação a partir do CACHE
desnormalizado `Tenant.acreditacao_vigencia_fim` (predicate
`acreditacao_vigente_para_rbc` — `domain/metrologia/certificados/transicoes.py`).
Enquanto esse campo é `None`, o M8 opera em **fail-open lazy**
(GATE-CER-CGCRE-VIG-DATA-POPULAR): não rebaixa RBC→não-RBC porque não tem o dado.

O M9 `metrologia/licencas-acreditacoes` introduz a entidade `DocumentoRegulatorio`
(`tipo=ACREDITACAO_CGCRE`) como **registro vivo e rico** da acreditação: vigência,
escopo (grandezas/faixas), número CGCRE, aderência ILAC-MRA, anexo probatório e
histórico versionado WORM (`RevisaoDocumento`). Surge uma pergunta de arquitetura:
quem é a fonte de verdade da vigência — a `Licenca` ou o cache do `Tenant`? Duas
fontes de verdade divergentes = bug de conformidade (o M8 poderia emitir RBC com
acreditação vencida na `Licenca` mas cache desatualizado).

A revisão `tech-lead-saas-regulado` da spec/plan do M9
(`docs/faseamento/M9-licencas-acreditacoes/`, P2 — TL-M9-01/04/06) confirmou pela
regra #0 que `aplicar_evento_cgcre` (migration tenant/0008) **não tinha parâmetro de
vigência** — por isso o gate ficava aberto: não havia mecanismo de população do cache.

## Perfil regulatório (ADR-0067 §4)

Decisão de arquitetura de dados (fonte de verdade / sincronização). O comportamento
perfil-aware da acreditação (só A acredita RBC; B/C/D rebaixam/no-op) vive no PRD +
matriz-feature-perfil + nos predicates `tenant_perfil_e`/`acreditacao_vigente_para_rbc`.
Esta ADR não cria regra perfil-aware nova — só decide ONDE o dado canônico mora e como
o cache é mantido coerente.

## Decisão

1. **`DocumentoRegulatorio(tipo=ACREDITACAO_CGCRE)` é a FONTE de verdade RICA** —
   vigência + escopo + número CGCRE + ILAC-MRA + anexo + revisões WORM. Modela o
   documento real emitido pela CGCRE.

2. **`Tenant.acreditacao_{vigencia_fim,cgcre_numero,suspensa_em,suspensa_ate,ilac_mra}`
   é CACHE desnormalizado** — leitura barata para o caminho quente da emissão (M8). NÃO
   é fonte de verdade; é uma projeção.

3. **Sincronização UNIDIRECIONAL `Licenca → cache`, EXCLUSIVAMENTE via
   `aplicar_evento_cgcre`** (função SECURITY DEFINER — INV-LIC-VIG-SYNC-001). NUNCA por
   `UPDATE` direto (SQL ou ORM) nas colunas `acreditacao_*` — o hook
   `tenant-perfil-imutavel-check.sh` (estendido na Fatia 1c — D-LIC-8) bloqueia isso.
   A migration tenant/0012 (Fatia 1c) **estende a função** com
   `p_acreditacao_vigencia_fim` + a direção `renovacao_vigencia_cgcre` (renova sem mudar
   perfil) — aditivo, backward-compat (DROP-13 + CREATE-14, sem overload).

4. **O M8 continua lendo o cache — SEM retrofit.** O M9 NÃO cria porta consumida pelo
   M8 agora; fecha GATE-CER-CGCRE-VIG-DATA-POPULAR **populando o cache**. A porta
   `query_service.vigente_para_rbc` é API interna do M9 (hard-block de emissão futuro —
   GATE-LIC-EMISSAO-HARDBLOCK, Wave B) e base do teste de não-drift.

5. **Invariante de não-drift VERIFICÁVEL (INV-LIC-VIG-SYNC-001):** para todo tenant
   perfil A, `Tenant.acreditacao_vigencia_fim == max(vigencia_fim das Licencas CGCRE
   não-revogadas)`. Cravado pelo teste `tests/test_licencas_nao_drift.py` (Fatia 3 —
   GATE-LIC-DRIFT).

Análoga à ADR-0078: assimetria deliberada (dado canônico num lugar, projeção em outro)
documentada para que um agente futuro NÃO "conserte" introduzindo `UPDATE` direto no
cache (que romperia a coerência e a trilha auditável da função).

## Consequências

- **Positivas:** uma fonte de verdade; cache coerente por construção (único caminho de
  mutação auditável + advisory lock por tenant); GATE-CER-CGCRE-VIG-DATA-POPULAR fecha
  sem retrabalho no M8; drift detectável por teste.
- **Negativas / trade-offs:** toda mutação de vigência da acreditação passa por uma
  função PL/pgSQL (não há atalho ORM) — intencional. O cache pode ficar *stale* se
  alguém burlar a função — mitigado pelo hook + teste de não-drift.

## Alternativas descartadas

- **Cache como fonte de verdade (sem `Licenca` rica):** perde escopo/número/histórico/
  anexo — o M9 existe justamente para isso.
- **M8 passa a ler a `Licenca` direto (retrofit do predicate):** acopla o caminho quente
  da emissão a um JOIN extra + reabre módulo FECHADO sem ganho (o cache já serve a
  leitura). Diferido a Wave B se algum dia o hard-block exigir.
- **Sincronização bidirecional:** dupla escrita = risco de divergência; rejeitada.

## Referências

- `docs/faseamento/M9-licencas-acreditacoes/{spec,plan}.md` (D-LIC-1/2/3/8)
- `src/infrastructure/tenant/migrations/0012_*` (função estendida — Fatia 1c)
- ADR-0067 (perfil regulatório), ADR-0030 (vigência canônica), ADR-0031 (soft-delete),
  ADR-0078 (assimetria deliberada análoga)
- INV-LIC-VIG-SYNC-001 (REGRAS-INEGOCIAVEIS — Fatia 4)
