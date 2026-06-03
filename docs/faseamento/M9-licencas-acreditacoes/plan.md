---
owner: agente-ia
revisado-em: 2026-06-01
proximo-review: 2026-09-01
status: stable
diataxis: reference
audiencia: [agente, auditor, tech-lead, consultor-rbc]
marco: M9-licencas-acreditacoes
tipo: plan-faseamento
relacionados:
  - docs/faseamento/M9-licencas-acreditacoes/spec.md
  - docs/faseamento/M9-licencas-acreditacoes/T-LIC-000-investigacao.md
  - docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md
  - REGRAS-INEGOCIAVEIS.md
---

# Plan de implementação — M9 `metrologia/licencas-acreditacoes`

> **Status:** `ready-for-tasks`. Revisões P2 `consultor-rbc` (APROVA COM CORREÇÕES — 6) +
> `tech-lead` (APROVA COM CORREÇÕES — 7) **incorporadas** abaixo (D-LIC-1..10 + ADR-0079).
> Furo crítico TL-M9-01 confirmado pela regra #0: `aplicar_evento_cgcre` (migration tenant
> 0008) NÃO tem parâmetro de vigência — precisa ser estendida (migration 0012).

## 1. Decisões cravadas (D-LIC-*)

- **D-LIC-1 (ADR-0079 — TL-M9-01/04/06 + RBC-M9-05):** `Licenca` (tipo acreditação CGCRE) é a
  **FONTE de verdade rica** (vigência + escopo grandezas/faixas + número CGCRE + ILAC-MRA +
  anexo + revisões). `Tenant.acreditacao_{vigencia_inicio,fim,cgcre_numero,suspensa_*,ilac_mra}`
  é **CACHE desnormalizado** que o **M8 já lê** (`acreditacao_vigente_para_rbc`). O M8 **NÃO**
  consome a porta `vigente_para_rbc` — continua lendo o cache (SEM retrofit). O gate
  GATE-CER-CGCRE-VIG-DATA-POPULAR fecha **POPULANDO o cache**, não criando porta. Sincronização
  **unidirecional Licenca → cache** exclusivamente via `aplicar_evento_cgcre` (nunca UPDATE
  direto). ADR-0079 declara **invariante de não-drift verificável** (teste `cache == fonte` para
  tenant A — `tests/test_licencas_nao_drift.py`; GATE-LIC-DRIFT).
- **D-LIC-2 (TL-M9-01 — migration tenant 0012):** estender `aplicar_evento_cgcre` via
  `CREATE OR REPLACE FUNCTION` (aditivo, backward-compat, NÃO toca 0008) adicionando
  `p_acreditacao_vigencia_inicio DATE DEFAULT NULL` + `p_acreditacao_vigencia_fim DATE DEFAULT NULL`;
  `UPDATE tenants SET acreditacao_vigencia_inicio/fim = COALESCE(param, atual)` (CASE WHEN param
  NOT NULL). Migration vive em `src/infrastructure/tenant/migrations/0012_*` (módulo tenant — o
  M9 cria a migration mas ela pertence ao app tenant; documentar em ADR-0079).
- **D-LIC-3 (TL-M9-05 — nova direção):** adicionar direção `renovacao_vigencia_cgcre` à função
  (renova vigência SEM mudar perfil — caso mais comum; perfil permanece A). Validações: perfil
  atual = A; vigência_fim > vigência_inicio. `correcao_administrativa` como variante se necessário.
- **D-LIC-4 (TL-M9-03 — transacionalidade/TOCTOU):** cadastro CGCRE com `promove_para_A=True` em
  UMA `transaction.atomic`: (1) INSERT `Licenca` + `RevisaoDocumento` v1; (2) `aplicar_evento_cgcre`
  via raw cursor na MESMA transação. Idempotência da operação composta (Idempotency-Key); retentativa
  detecta Licenca+perfil → no-op. Advisory lock reusado (ADR-0065). Teste de crash entre (1) e (2) →
  rollback total.
- **D-LIC-5 (RBC-M9-01 — DUAS fronteiras de bloqueio por TIPO):** INV-LIC-BLOQUEIO-001 distingue:
  - **(a) `ACREDITACAO_CGCRE` vencida/suspensa** → **NÃO 409**; alimenta o cache que o M8 lê →
    rebaixamento RBC→não-RBC (perfil A) / no-op (B/C/D). Reescrever AC-LIC-003-1: trocar "409 hard"
    por "rebaixamento delegado ao M8 via cache". 409 só se o cliente exigiu explicitamente RBC e não
    aceita não-RBC (escopo de produto, não default).
  - **(b) `ART_RRT` / `e-CNPJ` do signatário vencido** → **409 hard legítimo** (cl. 6.2 /
    NIT-DICLA-021 — sem signatário habilitado não se assina certificado NENHUM). É a única operação
    que o M9 bloqueia hard nesta frente.
  - A porta `vigente_para_rbc` e o hard-block de emissão são API interna do M9; a integração com a
    emissão M8 fica **GATE-LIC-EMISSAO-HARDBLOCK (Wave B)** — o M8 não consome agora (TL-M9-07).
- **D-LIC-6 (RBC-M9-02 — modo emergencial limitado):** modo emergencial sobre `ACREDITACAO_CGCRE`
  libera APENAS emissão NÃO-RBC (nunca contorna o rebaixamento do M8). Sobre `ART_RRT`/`e-CNPJ` não
  dispensa a EXISTÊNCIA do `a3_id` (a A3 é o instrumento legal). Pré-condição no `acionar_modo_emergencial`.
- **D-LIC-7 (RBC-M9-03 — A3 fail-open lazy + limiar):** modo emergencial registra `a3_id` (FK) +
  justificativa **≥100 chars** + WORM + expira ≤7d, SEM validação criptográfica (OCSP/LTV diferidos —
  **GATE-LIC-EMERGENCIAL-A3-CRIPTO** Wave B; fail-open lazy declarado). **Reconciliar INV-033 nas
  REGRAS:** texto diz ≥50 chars; alinhar para **≥100** (mais conservador; evita drift com hook/PRD).
- **D-LIC-8 (TL-M9-02 — hook):** estender `tenant-perfil-imutavel-check.sh` para bloquear `UPDATE
  tenants SET acreditacao_vigencia_fim|acreditacao_vigencia_inicio|acreditacao_cgcre_numero|
  acreditacao_suspensa_em|acreditacao_suspensa_ate|ilac_mra_aderido` fora dos auto-allow (só via
  função). + casos no `_test-runner.sh`. (Regra crítica vira hook — AGENTS §3.)
- **D-LIC-9 (RBC-M9-04 — retenção):** task espelho T-PAD-071 adiciona à `retencao-matriz.md`:
  `Acreditacao CGCRE + RevisaoDocumento` = 25a A/B/C / 5a D (ISO 17025 cl. 8.4 + NIT-DICLA-021 cl. 4.2,
  B2 WORM, PII de RT via `ReferenciaPIIAnonimizavel` — número/órgão/vigência preservados, CPF/nome
  hash); `ART/RRT` = enquanto vínculo ativo + 5a (D) / 25a se compôs cert RBC (A/B/C); `EventoEmergencial`
  = 25a (A/B/C) / 5a (D), B2 WORM, `justificativa_hash`. Número da ART NÃO é anonimizado (dado de
  conselho); CPF/nome do RT sim.
- **D-LIC-10 (RBC-M9-05/06 — escopo + perfil C):** cadastro/renovação CGCRE persiste o ESCOPO
  (grandezas/faixas/ilac_mra) na `Licenca` (fonte rica). Sincronização do escopo ao cache/evento:
  `GATE-LIC-ESCOPO-SYNC` — o /plan decide com base no que `aplicar_evento_cgcre` aceita; vigência via
  D-LIC-2; escopo fica na `Licenca` (M6/M8 leem escopo do evento WORM `escopos_acreditados_vigentes_no
  _momento` já existente — sem retrabalho). Perfil C: NÃO há RBC (não bloqueia/rebaixa emissão RBC);
  ART/RRT vencida bloqueia assinatura em A **e** C (ambos com RT habilitado, cl. 6.2).

## 2. ADR nova

- **ADR-0079 — `Licenca` fonte rica + `Tenant.acreditacao_*` cache sincronizado via
  `aplicar_evento_cgcre` (unidirecional, invariante de não-drift verificável).** Propõe a extensão
  da função (D-LIC-2/3), declara a direção de sincronização, o invariante `cache == fonte` com teste,
  e que o M8 lê o cache (sem retrofit). Revisão `tech-lead` (decisão de arquitetura, análoga a 0078).
  **Promover a aceito na Fatia 1b** (quando a migration 0012 concretizar o mecanismo).

## 3. Invariantes (família INV-LIC-* — numeração)

| INV | Regra | Enforcement | Hook |
|-----|-------|-------------|------|
| INV-LIC-PERFIL-001 | cadastro `ACREDITACAO_CGCRE` exige `tenant_perfil_e(['A','B','C'])`; D → 403 | use case guard server-side | **lic-perfil-cgcre-check** |
| INV-LIC-ANEXO-001 | documento exige anexo sha256 server-side → senão 422 | trigger PG + use case (formaliza INV-046) | **lic-anexo-obrigatorio-check** |
| INV-LIC-VIG-SYNC-001 | `Tenant.acreditacao_vigencia_fim` mantido SÓ via `aplicar_evento_cgcre` (nunca UPDATE direto); `Licenca`=fonte; cache==fonte (não-drift) | função estendida (0012) + teste não-drift | **tenant-perfil-imutavel-check** (estendido — D-LIC-8) |
| INV-LIC-WORM-001 | `RevisaoDocumento` + `EventoEmergencial` append-only (Padrão B) | trigger PG WORM | audit-immutability-check |
| INV-LIC-BLOQUEIO-001 | (a) ACREDITACAO_CGCRE vencida → rebaixa (não 409); (b) ART/RRT/e-CNPJ signatário vencido → 409 hard (cl. 6.2); modo emergencial INV-033 (a3_id + justif ≥100ch + ≤7d) | use case + query service `vigente_para_rbc` | **lic-emergencial-a3-check** |
| Reusadas | INV-032/033/046, INV-INT-001/003/004, INV-VIG-*, INV-SOFT-*, INV-TENANT-*, INV-TENANT-PERFIL-001/003/004/007, INV-ANON-*, INV-HMAC-* | | |

## 4. Fatias (ordem por dependência — evita retrabalho)

| Fatia | Conteúdo | Fecha |
|-------|----------|-------|
| **1a** domínio puro | enums (`TipoDocumentoRegulatorio`/`MotivoRevisao`/estados) + entidades (`Licenca`,`RevisaoDocumento`,`AlertaVencimento`,`BloqueioOperacional`,`EventoEmergencial`) + transições WORM + validações (status calculado, tipo×perfil, INV-046/032/033, duas fronteiras de bloqueio D-LIC-5) + repository Protocols. Zero Django. | — |
| **1b** schema + ADR-0079 | migrations RLS v2 + WORM Padrão B (triggers) + grants + seed authz + UNIQUE idempotência alertas + drill `validar_licencas_acreditacoes` + mappers/repositories aninhados (ADR-0072). **Promove ADR-0079.** | — |
| **1c** extensão função tenant (D-LIC-2/3) | migration `tenant/0012` `CREATE OR REPLACE aplicar_evento_cgcre` (+ params vigência + direção `renovacao_vigencia_cgcre`) + estende hook `tenant-perfil-imutavel-check` (D-LIC-8) + testes da função (vigência setada; UPDATE direto bloqueado) | mecanismo de sync (TL-M9-01) |
| **2** use cases + REST | `cadastrar_documento_regulatorio` (perfil-aware + anexo) + `renovar_documento` + `promover_perfil_a` (transação atômica D-LIC-4 invocando função) + `acionar_modo_emergencial` (D-LIC-6/7) + ViewSet + idempotência + eventos WORM | — |
| **3** sync + porta + job | sincronização `Licenca`(CGCRE)→cache via função (cadastro/renovação) + query service `vigente_para_rbc` (API interna) + job alertas (D-90..7) + refino job perfil A + **teste não-drift** | **GATE-CER-CGCRE-VIG-DATA-POPULAR** + GATE-LIC-DRIFT |
| **4** histórico + ART/RRT + P7 | US-LIC-004 (revisão imutável) + US-LIC-005 (ART/RRT + bloqueio 409 D-LIC-5b) + INV-LIC-* em REGRAS + reconciliar INV-033 ≥100ch (D-LIC-7) + `TestINV_LIC_*` + 3 hooks + retenção-matriz (D-LIC-9) | — |
| **P8/P9** | matriz-reconciliacao (molde M7) + emenda PRD (AC-LIC-003-1 fronteiras D-LIC-5) + URS (ADR-0025 v2) + auditores roteados INV-RITUAL-003 | módulo |

## 5. GATEs

**Fecha:** GATE-CER-CGCRE-VIG-DATA-POPULAR (Fatia 3 popula o cache) · GATE-LIC-DRIFT (teste não-drift).
**Rastreados/diferidos:** GATE-LIC-EMISSAO-HARDBLOCK (integração 409↔emissão M8 — Wave B) ·
GATE-LIC-EMERGENCIAL-A3-CRIPTO (OCSP/LTV — Wave B) · GATE-LIC-ESCOPO-SYNC (decidir no impl se escopo
vai ao cache ou só evento) · GATE-LIC-PDF (relatório/dossiê real — Wave B) · GATE-LIC-PQ (smoke
produção) · validação cl. 7.11 com parecer RBC credenciado (pré-produção).

## 6. Verificação por fatia (proporcional — espelha M5-M8)

1a: pytest domínio puro + ruff/mypy (zero Django). 1b: makemigrations --check + migrate + drill +
RLS/WORM PG-real + migration-rls-check/metrology-classifier. 1c: teste função (vigência setada +
UPDATE direto bloqueado pelo hook) + `_test-runner` (hook estendido). 2: use cases + API + idempotência
+ crash-rollback (D-LIC-4). 3: não-drift cache==fonte + job + reverde M8 (cert RBC com vigência
populada agora bloqueia/rebaixa real). 4: `TestINV_LIC_*` + hooks + `_test-runner` SEM FILTRO. P9:
6 auditores roteados + verificação adversarial.

## 7. Veredito

Plan `ready-for-tasks`. 13 correções P2 incorporadas (1 CRÍTICA TL-M9-01 confirmada pela regra #0 +
4 ALTAS + 5 MÉDIAS + 3 BAIXAS). ADR-0079 cravada. Fatia 1c nova (extensão da função tenant) inserida
ANTES da Fatia 2/3 por dependência. **Próximo:** `/tasks` (gerar T-LIC-NNN) → implement Fatia 1a.
