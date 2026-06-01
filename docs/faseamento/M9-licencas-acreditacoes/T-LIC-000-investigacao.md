---
owner: agente-ia
revisado-em: 2026-06-01
proximo-review: 2026-09-01
status: draft
diataxis: explanation
audiencia: [agente, tech-lead, consultor-rbc]
marco: M9-licencas-acreditacoes
tipo: investigacao-regra-0-dossie
relacionados:
  - docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md
  - docs/faseamento/ordem-dependencia-bloco-metrologia.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0030-vigencia-temporal-canonica.md
  - docs/adr/0031-soft-delete-3-padroes.md
  - REGRAS-INEGOCIAVEIS.md
---

# T-LIC-000 — Investigação regra #0 + dossiê de planejamento — M9 `metrologia/licencas-acreditacoes`

> **P0 do ritual** (espelha T-CER-000 do M8 / T-ECMC-000 do M6). Módulo **#5 e último do
> bloco metrologia** (`ordem-dependencia-bloco-metrologia.md`). Dossiê produzido por
> workflow de 5 leitores (`decompositor-us` · `seam-codigo` · `dependencias-cross-modulo` ·
> `normas-iso-nit` · `anti-retrabalho-risco` — 2026-06-01, convergência forte).
> **Próximo passo do ritual:** spec (P1) → revisões `consultor-rbc` + `tech-lead` (P2) →
> plan (P3) → `/tasks` → implement. Esta ordem é cravada — não se pergunta a próxima etapa.

## 1. O que o módulo é (resumo do PRD)

Cadastro vivo dos documentos regulatórios da **empresa** (não do cliente): acreditação
RBC/CGCRE, licenças sanitárias/ambientais, alvarás, ART/RRT do RT, certidões. Para cada
documento: vigência + status calculado + alertas de vencimento + histórico versionado +
anexo probatório obrigatório + bloqueio de operação dependente quando vencido + trilha WORM.
13 US (US-LIC-001..013) no PRD `stable`.

## 2. Investigação regra #0 — SEAM (o que JÁ existe — NÃO reconstruir)

| Peça | Estado | Arquivo | Implicação |
|------|--------|---------|------------|
| Função `aplicar_evento_cgcre(tenant_id, direcao, perfil_novo, motivo, a3, ...)` SECURITY DEFINER | ✅ existe | `src/infrastructure/tenant/migrations/0008_aplicar_evento_cgcre_function.py` | ÚNICA forma de UPDATE em `tenants.perfil_regulatorio`/acreditacao (valida transições D→C→B→A + suspensão + advisory lock + `tenant_perfil_historico` append-only + bus_outbox). **AC-LIC-001-4 (promoção perfil A) CHAMA esta função** — não reconstrói. |
| Campos `Tenant.acreditacao_{cgcre_numero,vigencia_inicio,vigencia_fim,suspensa_em,suspensa_ate,ilac_mra}` | ✅ existem | `src/infrastructure/tenant/models.py:80-135` | O cadastro/renovação de acreditação CGCRE popula `acreditacao_vigencia_fim` → **fecha GATE-CER-CGCRE-VIG-DATA-POPULAR do M8**. |
| Job `verificar_vigencia_acreditacao_perfil_a(snapshots, agora, janela=60d)` | ✅ existe (puro) | `src/application/tenant/jobs/verificar_vigencia_acreditacao_perfil_a.py` | US-LIC-002-4 já parcialmente entregue (Sprint 3 SAN-PERFIL). Refinar p/ consultar a entidade `Licenca` como fonte. |
| Predicates `tenant_perfil_e(perfis)` + `acreditacao_cgcre_aplicavel_por_perfil` | ✅ existem (fail-closed 50ms) | `src/infrastructure/authz/perfil_tenant_helper.py:106-151` | AC-LIC-001-3/3b chamam `tenant_perfil_e(['A','B','C'])` (defesa L6 — perfil D rejeitado). **Chamar direto no use case/view**, não registry. |
| Como o M8 consome a vigência | ✅ `acreditacao_vigente_para_rbc` (fail-open lazy se `None`) | `src/domain/metrologia/certificados/transicoes.py:109-142` | O M8 lê `Tenant.acreditacao_vigencia_fim`. Este módulo POPULA o campo → bloqueio por vencimento vira efetivo. Sem retrofit no M8 em escopo do M9. |
| Entidade `Licenca`/`DocumentoRegulatorio` | ❌ NÃO existe | — | É o que o M9 cria (fonte rica). |
| Templates WORM/RLS/hash-chain/path aninhado (ADR-0072/0031/0064/0065) | ✅ M5-M8 | — | Reusar molde — **zero padrão novo**. |
| VOs `JanelaVigencia`/`Grandeza`/`FaixaMedicao`/`CNPJ` + `ReferenciaPIIAnonimizavel` | ✅ existem | `src/domain/shared/value_objects.py` + `metrologia/value_objects.py` | Reusar (vigência canônica ADR-0030). |

**Tese central (anti-retrabalho):** a **entidade `Licenca` é a FONTE RICA** (com anexo,
revisões, alertas, escopo) e `Tenant.acreditacao_vigencia_fim` é o **CACHE desnormalizado**
que o M8 já lê. O M9 mantém os dois em sincronia **via `aplicar_evento_cgcre`** (no
cadastro/renovação/promoção de acreditação CGCRE). Não duplica fonte de verdade.

## 3. Escopo do NÚCLEO Wave A (convergência das 5 lentes — espelha M5-M8)

Só a parte lógica/regulatória, testável sem infra externa:
- **Entidades** (path aninhado ADR-0072 `src/{domain,infrastructure}/metrologia/licencas_acreditacoes/`): `Licenca`/`DocumentoRegulatorio` (raiz) + `RevisaoDocumento` (WORM append-only) + `AlertaVencimento` + `BloqueioOperacional` + `EventoEmergencial`. Campos canônicos ADR-0030 (`vigencia_inicio/fim` + `revogado_em/motivo`) + ADR-0031 Padrão B (WORM) + `perfil_no_evento`.
- **Catálogo de tipos** (enum `TipoDocumentoRegulatorio`) + validador tipo × perfil (matriz §3.1).
- **US-LIC-001** cadastrar (perfil-aware `tenant_perfil_e(['A','B','C'])` defesa L6 + anexo sha256 obrigatório INV-046 + status calculado + promoção perfil A via `aplicar_evento_cgcre`).
- **US-LIC-002** vigência + alertas (job diário 90/60/30/15/7d + refinar job perfil A existente).
- **US-LIC-003** bloqueio por doc vencido (INV-032 fail-closed perfil A) + modo emergencial (INV-033 — registra justificativa ≥100ch + `a3_id` FK; A3 real diferida) + **query service `vigente_para_rbc(tenant, data)` fail-closed** (a porta que o M8 consome — fecha o ciclo).
- **US-LIC-004** histórico versionado (revisão imutável).
- **US-LIC-005** ART/RRT (tipo especial + vínculo opcional RT + bloqueio assinatura se vencida).
- **Sincronização** `Licenca.vigencia_fim` → `Tenant.acreditacao_vigencia_fim` (via `aplicar_evento_cgcre` no cadastro/renovação CGCRE) → **fecha GATE-CER-CGCRE-VIG-DATA-POPULAR**.
- **INVs**: reusa INV-032/033/046/INT-001/003/004; crava **família `INV-LIC-*`** (mín. INV-LIC-PERFIL-001 — CGCRE exige perfil A/B/C).
- WORM/RLS/grants/seed authz/drill `validar_licencas_acreditacoes` (molde M5-M8).
- URS `docs/dominios/metrologia/modulos/licencas-acreditacoes/urs.md` + OQ (testes AC binários perfil A/B/C/D, UNHAPPY perfil D → 403) — ADR-0025 v2.

## 4. Diferido Wave A/B (declarado — não bloqueia o núcleo; espelha M8)

- **PDF consolidado real** (US-LIC-007/013) — motor PDF/A (GATE-LIC-PDF). Núcleo entrega export estruturado.
- **E-mail real** (US-LIC-002 — ADR-0060 `EmailTemplateProvider`) — núcleo dispara evento/dashboard; envio real Wave B.
- **A3/PAdES** (US-LIC-003 modo emergencial + US-LIC-011 resposta NC com carimbo LTV ADR-0047) — núcleo registra `a3_id` + justificativa; assinatura real diferida.
- **Fluxos CGCRE complexos** (US-LIC-010 ampliação / US-LIC-011 NC / US-LIC-012 revisão quinquenal) — ADR-0014 fluxos 7/8/9, Wave B.
- **US-LIC-013 dossiê pré-auditoria** — composição horizontal (depende de escopos/procedimentos/treinamento) — Wave B.
- **US-LIC-006/008/009 cadastro físico A3** — já delegados a `seguranca/certificados-digitais` (ADR-0048); M9 mantém referência cruzada (FK) + alerta de vencimento.
- **Integração API CGCRE / auto-renovação portal** — V2 (sem API pública estável).
- **Validação cl. 7.11 com parecer RBC credenciado** — pré-produção (`project_sem_contratacoes_externas_ate_producao`).

## 5. Fatias propostas (ordem por dependência — refinar no /plan)

| Fatia | Conteúdo | Fecha |
|-------|----------|-------|
| 0 (se houver peça compartilhada) | catálogo `TipoDocumentoRegulatorio` + validador tipo×perfil (se reusado por outro módulo) | — |
| 1a | domínio puro (entidades + enums + transições WORM + validações INV-046/032/033) | — |
| 1b | schema (migrations RLS v2 + WORM Padrão B + grants + seed authz + drill `validar_licencas_acreditacoes`) + mappers/repositories aninhados | — |
| 2 | use cases (cadastrar perfil-aware + renovar + promover perfil A via `aplicar_evento_cgcre` + acionar modo emergencial) + REST + idempotência + eventos WORM | — |
| 3 | **sincronização vigência → `Tenant.acreditacao_vigencia_fim`** + query service `vigente_para_rbc` (porta M8) + job alertas | **GATE-CER-CGCRE-VIG-DATA-POPULAR** |
| 4 | histórico versionado + ART/RRT + P7 (INV-LIC-* em REGRAS + hooks) | — |
| P8/P9 | matriz-reconciliacao + emenda PRD + URS + auditores roteados | módulo |

## 6. ADR nova necessária (P2/P3)

- **ADR-00XX (provável 0079) — `Licenca` fonte rica + `Tenant.acreditacao_*` cache desnormalizado:** decide que a entidade `Licenca` (tipo acreditação CGCRE) é a fonte de verdade da vigência/escopo, e `Tenant.acreditacao_vigencia_fim` é projeção mantida **exclusivamente** via `aplicar_evento_cgcre`. Define quem sincroniza e a direção (evita dupla fonte de verdade — risco de drift). **Revisão `tech-lead` obrigatória** (decisão de arquitetura, análoga a ADR-0078). Possível 2ª ADR sobre catálogo de tipos × perfil se virar regra perfil-aware nova.

## 7. Riscos / pontos de atenção (lente anti-retrabalho)

- **Drift Licenca ↔ Tenant.acreditacao_***: a sincronização DEVE ser unidirecional via `aplicar_evento_cgcre` (não UPDATE direto — bloqueado pelo hook `tenant-perfil-imutavel-check`). Teste de regressão de não-drift.
- **Bloqueio de emissão fail-CLOSED perfil A** (INV-032): perfil A com acreditação vencida bloqueia; B/C/D configurável. Reusa a fronteira já decidida no M8 (INV-CER-CGCRE-VIG-001 — rebaixa, não 409 hard, no ponto de emissão; o bloqueio "hard" do US-LIC-003 é no documento bloqueante — reconciliar a semântica no /plan com `consultor-rbc`).
- **Anexo PII / retenção perfil-aware** (matriz-feature-perfil): 25a A/B/C, 5a D — usar `ReferenciaPIIAnonimizavel` onde houver PII de RT/titular.
- **Zero padrão novo** — tudo template M4/M5/M8 (WORM/RLS/hash-chain/outbox/predicates/path aninhado).

## 8. Veredito P0

Seam mapeado (regra #0): o "cache" que o M8 lê (`Tenant.acreditacao_vigencia_fim`) e a
máquina de promoção (`aplicar_evento_cgcre`) + job de vigência **já existem**; falta a
**entidade `Licenca` (fonte rica)** que os alimenta e o **bloqueio operacional** que o M8
consome. Escopo do núcleo convergente entre as 5 lentes. **Pronto para P1 (spec).**
