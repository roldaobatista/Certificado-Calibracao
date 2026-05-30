---
owner: roldao
revisado-em: 2026-05-30
status: stable
fase: M6-escopos-cmc
dominio: metrologia
modulo: escopos-cmc
ritual: plan
versao: 2
depende-de: docs/faseamento/M6-escopos-cmc/spec.md
reviews-concluidas:
  - tech-lead-saas-regulado (APROVA COM CORREÇÕES — 2 CRÍTICO + 3 ALTO + 4 MÉDIO + 2 BAIXO)
  - consultor-rbc-iso17025 (APROVA COM CORREÇÕES — 1 CRÍTICO + 3 ALTO + 2 MÉDIO + 2 BAIXO)
consolidacao: docs/faseamento/M6-escopos-cmc/reviews-consolidado.md
adrs-emitidas-v2:
  - 0073 (validação metrológica no use case, não no permission layer DRF)
  - 0074 (cobertura RBC tridimensional: faixa ⊆ escopo + U ≥ CMC + menor-CMC-por-faixa)
  - 0075 (capacidade interna não-acreditada ≠ CMC acreditada — separação terminológica)
  - emenda ADR-0066 (transição fail-open→fail-closed + fail-open lazy vínculo RT)
---

# Plano técnico — M6 `metrologia/escopos-cmc`

> ✅ **v2 (2026-05-29) — `ready-for-tasks`.** As 19 não-conformidades (TL-C-01..11 +
> RBC-NC-01..08) das 2 revisões foram resolvidas: ver §15 (deltas) + ADR-0073/0074/0075
> + emenda ADR-0066. O corpo v1 (§1-§10) permanece como contexto; §15 SUPERSEDE onde
> diverge. Próximo passo: `/tasks`.

> **Ritual:** este é o `/plan`. Reusa padrões já cravados em M4/M5 (RLS pattern v2,
> triggers WORM, CAS optimistic lock, `tenant_perfil_e`, canonicalização ADR-0029,
> paginação F-C3) — **não reinventar**. **Sem código antes do `/tasks`.**

## 1. Arquitetura de camadas (ADR-0007 + ADR-0072 path aninhado)

```
src/domain/metrologia/escopos_cmc/        # PURO — sem Django
  entities.py     EscopoCMC + EscopoCMCSnapshot (migra de calibracao/queries/escopo.py)
                  + EscopoUsado (VO WORM congelado) + EscopoExtraido (staging)
  enums.py        EstadoEscopo (RASCUNHO_EXTRAIDO/CONFIRMADO/REVOGADO), OrigemEscopo
  cobertura.py    lógica pura de cobertura faixa/CMC (contenção total) — Decimal
  repository.py   Protocols (EscopoRepository)
  (VOs reusados de src/domain/metrologia/value_objects.py — NÃO recriar)

src/application/metrologia/escopos_cmc/   # use cases (orquestram Protocols)
  cadastrar_escopo.py / revisar_escopo.py / revogar_escopo.py /
  declarar_capacidade_interna.py / confirmar_escopo_extraido.py /
  queries/ (cobertura, escopos_vigentes, dossie)
  extracao/ (parse_pdf_cgcre.py — motor de extração; isolado p/ trocar engine)

src/infrastructure/metrologia/escopos_cmc/  # Django ORM + raw SQL
  models.py / migrations/ / repositories.py (escopo_repo singleton — drop-in) /
  query_service.py (cobre() fail-CLOSED) / serializers.py / views.py
  (EscopoCMCViewSet) / urls.py (plugada na raiz) / apps.py / management/commands/
```

**D-ECMC-1 (path):** seguir `src/infrastructure/metrologia/escopos_cmc/` (ADR-0072
manda; M4 achatado fica dívida conhecida, NÃO replicar). **Confirmar tech-lead.**

## 2. Decisões técnicas-chave (com justificativa — para os revisores baterem)

### D-ECMC-2 — Model com colunas TIPADAS (não JSONField)
`EscopoCMC` espelha 1:1 o `EscopoCMCSnapshot` cravado (`escopo.py:22-52`) com
colunas DecimalField/CharField — diferente do `PadraoMetrologico` (JSONField) —
porque o predicate `cobre()` precisa de índice PG eficiente em `grandeza` + range
`faixa_min/max`. Índice sugerido `(tenant_id, grandeza, vigencia_fim)` (espelha
RTCompetencia). O snapshot de query M4 migra para `entities.py` (docstring
`escopo.py:8-11` já anota essa migração).

### D-ECMC-3 — Cobertura por CONTENÇÃO TOTAL (§9 A — RBC decide)
Para o bloqueio RBC, faixa solicitada deve estar **totalmente contida** no escopo
(`faixa_min_solicitada ≥ escopo_min E faixa_max_solicitada ≤ escopo_max`). A query
de leitura M4 (`_faixa_intersecta`) usa interseção — correto para LISTAR, errado
para BLOQUEAR (interseção parcial deixaria emitir RBC fora do CMC = fraude
documental). `cobertura.py` implementa contenção total. **INV-ECMC-005.**
**REVISÃO CRÍTICA `consultor-rbc-iso17025`:** confirmar contenção total + se o
MVP deve também barrar `U_expandida_serviço < CMC_declarada` (lab não reporta
incerteza melhor que a capacidade declarada — §9 B).

### D-ECMC-4 — Perfil-aware (§9 O — decisão Roldão: todos declaram)
- Perfil **A**: declara **escopo RBC** (`rbc_acreditado=true`, lastro CGCRE +
  `numero_escopo_cgcre`). Sofre bloqueio duro 412 `EscopoNaoCobreFaixa`.
- Perfis **B/C/D**: declaram **capacidade interna** (`rbc_acreditado` **forçado
  false** server-side — anti-fraude INV-015/INV-ECMC-002; não-A nunca marca RBC).
  Sem bloqueio 412 (calibração não-A não carrega selo RBC); aviso suave opcional.
- Cadastro/leitura liberado a todos (matriz feature×perfil atualizada); o
  **bloqueio** continua RBC-only (preserva trava SAN-PERFIL/ADR-0067).
**REVISÃO `consultor-rbc-iso17025`:** validar que "capacidade interna" para B/C/D
é metrologicamente coerente (não confunde com escopo acreditado) + matriz perfil.

### D-ECMC-5 — Wire-in `cmc_cobre` (§9 C+D — tech-lead)
- **Shape resource:** aninhar `resource={'escopo': {'grandeza','faixa_min',
  'faixa_max','data'}}` — `escopo` já está na allowlist `_RESOURCE_KEYS_OK`,
  mudança mínima sem relaxar a validação anti-PII global. Adaptar `cmc_cobre` a
  ler de `resource['escopo']`.
- **Fonte server-side:** modelar a faixa solicitada como **campo de 1ª classe na
  Calibracao** (derivado na configuração do snapshot do equipamento/ponto), NÃO do
  payload (SEG-CAL-10). A view de `configurar`/`recepcionar` injeta grandeza+faixa+
  data no resource server-side.
- **Singleton:** `escopo_repo` exposto module-level em `repository.py` (o drop-in
  `predicates_calibracao.py:173` importa o símbolo — §9 Q).
- **GATE-CAL-CMC-PREDICATE:** wire-in + teste do caminho bloqueado + teste de
  transição fail-open→fail-closed (TST-005) sem quebrar a suíte M4 (629) + recepção
  (aviso degradante AC-CAL-001-2) e configuração (412 AC-CAL-002-2).

### D-ECMC-6 — WORM Padrão B + versionamento (§9 H)
Escopo CONFIRMADO sustenta certificado RBC → Padrão B WORM (ADR-0031): muta só via
revogação (`revogado_em`+`motivo_revogacao` ≥10 chars canon ADR-0029); DELETE
bloqueado por trigger PG (INV-SOFT-002). **Revisão** (AC-CAL-015-2) cria nova
`versao` preservando a anterior (auditoria retroativa — calibrações antigas
referenciam a versão vigente à época). Trigger BEFORE UPDATE bloqueia mutação de
campos probatórios de escopo CONFIRMADO (grandeza/faixa/cmc_valor/rbc_acreditado).

### D-ECMC-7 — Granularidade escopo×método + RT (§9 F/G/M — RBC)
Proposta: **1 método por linha de escopo** (`procedimento_id` NOT NULL para RBC);
cada `(grandeza, faixa_min, faixa_max, procedimento_id)` é linha. **RTCompetencia
é a fonte de verdade do RT** — escopo referencia (não duplica); escopo sem RT
competente vivo cobrindo grandeza+método+faixa → `cobre()` bloqueia uso RBC (não
revoga automático). UNIQUE `(tenant_id, grandeza, faixa_min, faixa_max,
procedimento_id, versao)`. **REVISÃO `consultor-rbc-iso17025`:** confirmar 1:1
método×escopo + o vínculo com RTCompetencia (ADR-0022 v2 retrofit é Wave A —
model atual só tem grandeza; usar fail-open lazy paralelo a ADR-0063 até retrofit?).

### D-ECMC-8 — Extração PDF (§9 N/R — tech-lead)
Motor isolado em `application/.../extracao/parse_pdf_cgcre.py` (porta trocável).
**Proposta MVP: motor DETERMINÍSTICO** (leitor de tabela — pdfplumber/camelot ou
parser próprio das tabelas "Escopo da Acreditação" do inmetro.gov.br) + estado
`RASCUNHO_EXTRAIDO` editável → tela de conferência humana → `confirmar_extraido` →
`CONFIRMADO` (INV-ECMC-007 — nunca auto-persiste vigente). Staging = sub-entidade
`EscopoExtraido` (não polui o agregado vigente — §9 R). **GATE-ECMC-EXTRACT-ENGINE:**
**REVISÃO `tech-lead`:** determinístico é robusto o bastante para o layout CGCRE,
ou exige IA (LLM)? Se IA → **ativa ADR-0059 LLMProvider reservada** (INV-LLM-001..010
redaction/retenção/audit) + custo por chamada → **volta ao Roldão como decisão de
custo/privacidade** antes de construir. Validação cl. 7.11 (ADR-0025) do motor:
dado extraído que toca cmc_valor/faixa é metrology-affecting.

### D-ECMC-9 — Snapshot `EscopoUsado` congelado (§9 J — ADR-0014)
Na configuração da calibração RBC, congelar VO `EscopoUsado` (frozen, canon
ADR-0029) com o escopo vigente → alimenta `escopos_acreditados_vigentes_no_momento`
JSONB de `evento_de_calibracao` (coluna já criada SAN-PERFIL Sprint 4 — só falta
alimentar). Defesa retroativa CGCRE (INV-INT-003). INV-ECMC-008.

### D-ECMC-10 — Eventos (§9 S — tech-lead)
Proposta: CRUD de escopo usa o **audit trail padrão** (`registrar_auditoria` +
`perfil_no_evento`) — não exige cadeia hash-chain dedicada como calibração (escopo
é configuração regulatória, não medição). O congelamento probatório vive no
`EscopoUsado` dentro do `evento_de_calibracao` (que JÁ é hash-chain HMAC ADR-0064).
**REVISÃO `tech-lead`:** audit trail padrão basta, ou revogação/revisão de escopo
exige evento hash-chain dedicado (cl. 8.4 probatório)?

### D-ECMC-11 — Orquestração validação composta (§9 I — tech-lead)
Quando faixa-fora-de-escopo E sem-procedimento-vigente ocorrem juntos: **ordem
fixa escopo→procedimento, retorna a 1ª falha**. O núcleo Calibracao (M4) é dono da
orquestração (invoca os predicates em ordem); cada módulo dono só do seu predicate.
`escopos-cmc` e `procedimentos` saem do fail-open SEPARADAMENTE (este fecha
GATE-CAL-CMC-PREDICATE; o irmão fecha GATE-CAL-PROC-VIGENTE-PREDICATE).

## 3. Schema (Fatia 1) — tabelas + RLS v2 + WORM

- `escopo_cmc` (raiz) — colunas tipadas (D-ECMC-2), UNIQUE `(tenant_id, grandeza,
  faixa_min, faixa_max, procedimento_id, versao)`, `revision` (CAS), vigência
  ADR-0030, soft-delete B ADR-0031, `rbc_acreditado`, `numero_escopo_cgcre`,
  `documento_regulatorio_id` (FK NULLABLE→Licenças), `estado` (enum).
- `escopo_extraido` (staging — D-ECMC-8) — rascunho editável pré-confirmação.
- Migrations irmãs: 0001 initial (+UNIQUE+Index `# rls-policy: external 0002`) →
  0002 RLS v2 (ENABLE+FORCE + 4 policies) → 0003 triggers WORM (Padrão B: BEFORE
  DELETE RAISE + BEFORE UPDATE campos imutáveis de CONFIRMADO) → 0004 grants
  app_user → 0005 seed authz (ações `escopos_cmc.{cadastrar,revisar,revogar,
  declarar_capacidade,confirmar_extraido,ver}` × matriz perfil).
- `metrology-affecting:` declarado nas migrations que tocam cmc_valor/faixa
  (INV-CAL-VAL-002 / hook `migration-metrology-classifier`).

## 4. Faseamento detalhado (vira `/tasks` — 4 fatias, INV-RITUAL-002)

- **Fatia 1 (P1-P4):** domínio puro (entities+enums+cobertura+repository) +
  migrations+RLS+triggers WORM + repositório `cobre()` + CAS + drill estrutural
  `validar_escopos_cmc`.
- **Fatia 2 (P5-P7):** use cases (cadastrar/revisar/revogar/declarar_capacidade) +
  EscopoCMCViewSet + serializers + idempotência + urls raiz + vínculo Licenças.
- **Fatia 3 (P8):** wire-in `cmc_cobre` real + shape resource + injeção server-side
  + snapshot EscopoUsado + GATE-CAL-CMC-PREDICATE (suíte M4 reverde) + INV-ECMC-* +
  TestINV_ECMC_NNN + validação cl. 7.11.
- **Fatia 4 (P9):** extração PDF + estado staging + conferência humana +
  GATE-ECMC-EXTRACT-ENGINE + validação cl. 7.11 do motor.

Cada fatia roda o ritual completo (auditores essenciais + roteados; MÉDIO+ bloqueia).

## 5. Riscos + mitigações

- **R1 extração frágil** (D-ECMC-8) — se determinístico falha no layout CGCRE,
  conferência humana cobre; escalar a IA só com decisão de custo do Roldão. Mitiga:
  decisão no review ANTES da Fatia 4.
- **R2 quebra suíte M4 (629)** no wire-in — Fatia 3 roda suíte M4 chave antes de fechar.
- **R3 RTCompetencia sem método+faixa** (ADR-0022 v2 Wave A) — fail-open lazy do
  vínculo RT (paralelo ADR-0063) até retrofit; documentar EXPLÍCITO, não gap silencioso.
- **R4 reabrir fraude L6** — `rbc_acreditado` forçado false p/ não-A + bloqueio 412
  perfil-A-gated; testar anti-fraude (TestINV_ECMC_002).
- **R5 ADR-0059 ativada por IA** — se extração exigir LLM, custo+privacidade voltam
  ao Roldão; INV-LLM-001..010 entram em escopo.

## 6. Reuso explícito (não reinventar)

`tenant_perfil_e` (SAN-PERFIL) · RLS pattern v2 templates (M4/M5) · triggers WORM
(M5 padroes) · CAS `atualizar_com_lock` (M4) · `registrar_auditoria`+`perfil_no_evento`
· canonicalização ADR-0029 · paginação F-C3 (teto 200) · `EscopoCMCSnapshot`+
`executar()` da query M4 (base da cobertura) · drill estrutural molde `validar_m5_padroes`.

## 7. Critérios de pronto (Definition of Done M6)

AC-CAL-001-2/002-2/015-1/2 verdes · INV-ECMC-001..008 em REGRAS + testes nomeados ·
drill estrutural verde + GATE-ECMC-DRILL-LOCAL · GATE-CAL-CMC-PREDICATE (suíte M4
reverde + caminho bloqueado testado) · auditores PASS ZERO C/A/M sob roteamento
INV-RITUAL-003 · ruff/mypy limpos · urls plugadas na raiz.

## 8. Non-goals do plano (confirmam spec §3)

Procedimento técnico vigente (irmão `procedimentos-calibracao`) · gerência da
acreditação CGCRE (Licenças) · RT/quem assina (responsavel_tecnico) · padrão físico
(padroes) · emissão de cert · PDF/A · extração por IA no MVP (salvo veto tech-lead+Roldão).

## 9. Perguntas dirigidas aos revisores

### consultor-rbc-iso17025 (CRÍTICO — metrologia)
1. **D-ECMC-3:** cobertura por contenção total é correta p/ bloqueio RBC? E o MVP
   deve barrar `U_expandida_serviço < CMC_declarada` (§9 B) já no dogfooding?
2. **D-ECMC-4:** "capacidade interna" para perfis B/C/D (`rbc_acreditado=false`) é
   metrologicamente coerente, ou confunde com escopo acreditado? Matriz perfil ok?
3. **D-ECMC-7:** 1 método por linha de escopo + RTCompetencia como fonte de verdade
   do RT — modelagem suficiente? Escopo sem RT competente vivo deve bloquear uso RBC?
4. CMC: há regra canônica NIT-DICLA-031/ILAC sobre como o CMC se compara à incerteza
   do serviço que devamos cravar como invariante?
5. Versionamento de escopo (revisão CGCRE): a versão antiga deve continuar válida
   para calibrações já configuradas com ela (sim, AC-CAL-015-2) — confirmar regra.

### tech-lead-saas-regulado (arquitetura)
1. **D-ECMC-1:** path `src/infrastructure/metrologia/escopos_cmc/` (ADR-0072) ok?
2. **D-ECMC-5:** shape resource aninhado sob `escopo` + faixa como campo de 1ª classe
   na Calibracao (server-side) — estratégia correta p/ não relaxar anti-PII e não ler payload?
3. **D-ECMC-8 (CRÍTICO):** motor de extração determinístico no MVP basta, ou o layout
   CGCRE exige IA (ativa ADR-0059)? Staging `EscopoExtraido` separado vs flag no agregado?
4. **D-ECMC-10:** audit trail padrão p/ CRUD basta, ou revogação/revisão exige evento
   hash-chain dedicado (cl. 8.4)?
5. **GATE-CAL-CMC-PREDICATE:** estratégia de wire-in sem quebrar a suíte M4 (629) +
   transição fail-open→fail-closed sem quebrar calibrações legadas?
6. **D-ECMC-7 (RT lazy):** usar fail-open lazy no vínculo RTCompetencia (paralelo
   ADR-0063) até o retrofit ADR-0022 v2 chegar em Wave A — aceitável?

## 10. Próximo passo

Revisão dos 2 subagentes → `reviews-consolidado.md` (NCs → ADR se estruturais) →
plan v2 `ready-for-tasks` → `/tasks`. Se a extração exigir IA, decisão de
custo/privacidade volta ao Roldão antes da Fatia 4. **Sem código antes do plan v2.**

## 15. Plan v2 — deltas das revisões (SUPERSEDE §1-§10 onde diverge)

Resolução de TL-C-01..11 + RBC-NC-01..08 (`reviews-consolidado.md`). Estruturais → ADR.

### Estruturais → ADR

- **TL-C-01 (CRÍTICO) → ADR-0073.** D-ECMC-5 reescrita: a validação de cobertura
  (`cmc_cobre`/`procedimento_vigente_para`) NÃO é predicate-na-permissão — é **chamada
  explícita à porta DENTRO do use case** `configurar_calibracao`, 412 do domínio. O
  permission layer DRF fica para RBAC/perfil/segregação. Predicates STUB ficam
  DEPRECADOS (no-op) na transição. Resolve TL-C-02 (shape resource) de uma vez — a
  checagem nem usa o resource DRF.
- **RBC-NC-01 (CRÍTICO) + RBC-NC-03 → ADR-0074.** Cobertura RBC **tridimensional**:
  (1) contenção total de faixa (config, porta `cobre()`); (2) `U ≥ CMC` (emissão,
  **2ª porta `cmc_para()`** → 412 `IncertezaAbaixoDoCMC`, ILAC-P14 §5.5) — **INV-ECMC-009
  nova**; (3) múltiplos métodos por faixa → menor CMC vigente (NIT-DICLA-012).
  Normalizar unidade/forma (abs vs `a+b·X`). `U` sempre do orçamento, nunca `U=CMC`
  cego (RBC-NC-07). Consumo da condição (2) rastreado por **GATE-ECMC-U-MAIOR-CMC**.
- **RBC-NC-02 (ALTO) → ADR-0075.** Separação terminológica: A = "CMC (menor incerteza
  declarada)" + "Escopo CGCRE nº"; B/C/D = "Capacidade interna declarada (sem
  acreditação RBC)" + badge "NÃO ACREDITADO". Dado compartilhado (`cmc_valor`), rótulo
  distinto. Bloqueio 412 RBC-only. **Reportado ao Roldão (veto aberto).**
- **TL-C-05 + RBC-NC-04 → emenda ADR-0066.** Vínculo RT↔escopo fail-open lazy no MVP
  (paralelo ADR-0063) até retrofit ADR-0022 v2; **GATE-ECMC-RT-VINCULO** rastreia o
  fechamento (escopo sem RT competente vivo → DENY uso RBC antes do 1º tenant externo).
  Fail-open documentado + teste nomeado — nunca gap silencioso.

### Ajustes (entram no `/tasks`)

- **TL-C-03 (investigação regra #0):** ANTES do `/tasks`, investigar estado real da
  suíte M4 sob perfil A no `configurar` (a view passa grandeza/faixa hoje? algum teste
  perfil A passa?). Determina o tamanho do wire-in. Transição em 2 etapas (canal de
  dados com STUB True → troca real). **Nunca relaxar assert M4** (anti-mascaramento).
- **TL-C-04 → porta = função de módulo** `cobre()`+`cmc_para()` em `query_service.py`
  (molde M5), NÃO singleton `escopo_repo` stateful. (§9 Q resolvida: função de módulo.)
- **TL-C-06:** revogação/revisão emitem `registrar_auditoria` com
  `action="escopos_cmc.revogado"/"...revisado"` na cadeia hash central `auditoria`
  (molde M5 `padrao.*`). Audit trail padrão JÁ é hash-chain — sem tabela nova.
- **TL-C-07:** "revisar" = INSERT nova `versao` (não UPDATE in-place); trigger BEFORE
  UPDATE bloqueia campos metrológicos de linha CONFIRMADA exceto one-shot `revogado_em`
  (molde `recal_externo_padrao_worm_check`). Sem GUC.
- **TL-C-08:** NÃO reusar `_faixa_intersecta` (escopo.py:55-71) para BLOQUEAR;
  `cobertura.py` implementa contenção total isolada. Interseção só para LISTAR.
- **TL-C-09 → 5 fatias** (split Fatia 1): **1a** domínio puro + cobertura.py; **1b**
  schema + migrations + RLS + WORM + repo + drill; **2** use cases + API + versionamento;
  **3** wire-in `cmc_cobre`/`cmc_para` + GATE-CAL-CMC-PREDICATE; **4** extração PDF +
  conferência humana.
- **TL-C-10:** `apps.py` `label="escopos_cmc"`. **TL-C-11:** índice parcial
  `WHERE estado='CONFIRMADO' AND revogado_em IS NULL`.
- **RBC-NC-05:** redução de escopo CGCRE → `vigencia_fim` na versão antiga + bloqueio
  PROSPECTIVO; certificados pretéritos permanecem válidos (snapshot congelado sustenta).
- **RBC-NC-06:** VO `EscopoUsado` enriquecido: `versao` + CMC-da-época com forma +
  comparação U×CMC + RT da época + `perfil_no_evento`. (INV-ECMC-008 v2.)
- **RBC-NC-08:** validar números/revisões das NIT (021/031/012/016) com humano
  credenciado antes do dossiê CGCRE — não bloqueia código; bloqueia dossiê.

### Decisão de extração (D-ECMC-8) — confirmada, sem ADR agora

Motor **determinístico** no MVP + staging em sub-entidade `EscopoExtraido` separada +
conferência humana obrigatória (INV-ECMC-007). NÃO ativar ADR-0059 (LLMProvider) —
a conferência humana torna a robustez do parser problema de UX, não de correção; e
validação cl. 7.11 sobre código determinístico é muito mais barata que sobre LLM
não-determinístico. IA só se o parser provar inviável na Fatia 4 (R1) → volta ao
Roldão como decisão de custo/privacidade. **GATE-ECMC-EXTRACT-ENGINE** rastreia.

### Estados v2 (atualiza spec §4)

`RASCUNHO_EXTRAIDO` (staging, sub-entidade `EscopoExtraido`, mutável) → `CONFIRMADO`
(linha nova em `escopo_cmc`, WORM Padrão B) → `REVOGADO` (one-shot). Revisão = INSERT
`versao+1`. Só `CONFIRMADO` vigente entra em `cobre()`/`cmc_para()`.

## 16. Próximo passo (v2)

`/tasks` (M6-escopos-cmc/tasks.md) derivando das 5 fatias (§15 TL-C-09) com TL-C-01..11
+ RBC-NC-01..08 aplicados. **TL-C-03 (investigar suíte M4 sob perfil A) precede o
wire-in da Fatia 3.** Sem código antes do `/tasks`.

