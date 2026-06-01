---
owner: agente-ia
revisado-em: 2026-06-01
proximo-review: 2026-09-01
status: draft
diataxis: reference
audiencia: [agente, auditor, tech-lead, consultor-rbc]
marco: M8-certificados
tipo: spec-faseamento
relacionados:
  - docs/dominios/metrologia/modulos/certificados/prd.md
  - docs/faseamento/ordem-dependencia-bloco-metrologia.md
  - docs/adr/0076-fonte-faixa-cobertura-declarada-config-vs-pontos-emissao.md
  - docs/adr/0074-cobertura-rbc-tridimensional-faixa-u-maior-cmc.md
  - docs/adr/0073-validacao-cobertura-metrologica-no-use-case.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/faseamento/M6-escopos-cmc/matriz-reconciliacao.md
  - docs/faseamento/M7-procedimentos-calibracao/matriz-reconciliacao.md
---

# Spec de faseamento — M8 `metrologia/certificados` (núcleo metrológico de emissão)

> **Não duplica AC** — a fonte é o PRD `docs/dominios/metrologia/modulos/certificados/prd.md`
> (stable, US-CER-001..020). Esta spec FASEIA o módulo: define o que entra AGORA
> (núcleo metrológico de emissão, que fecha os GATEs que o bloco metrologia vinha
> preparando) e o que é DIFERIDO (depende de infra externa não contratada ou de
> módulos ainda inexistentes). Ritual: spec → revisão `consultor-rbc` + `tech-lead`
> → plan → tasks → implement → P9.

## 1. Por que este faseamento (decisão de escopo)

O PRD tem 20 US (US-CER-001..020). A maioria depende de **infra externa diferida**
(`project_sem_contratacoes_externas_ate_producao`) ou de **módulos ainda não
construídos**:

- A3/Lacuna (assinatura), OCSP/CRL (ADR-0046), TSA-ITI (ADR-0047) — hardware +
  Autoridades de Carimbo + ICP-Brasil reais.
- Motor PDF/A-3 (ISO 19005-3), templates Jinja2 (US-CER-010/017) — engine própria + UX.
- Portal do cliente (US-CER-006), e-mail (ADR-0060 `EmailTemplateProvider`, US-CER-005).
- `metrologia/licencas-acreditacoes` (US-LIC-003/005) — bloqueio CGCRE/ART vencida.
- Export regulatório ANVISA (US-CER-016/017), recall/suspensão/errata (US-CER-018/019/020)
  — dependem de A3/TSA/CGCRE reais + comitê de imparcialidade.

O que NÃO depende de nada disso, e é o **coração metrológico que o bloco inteiro
(escopos-cmc M6 + procedimentos M7 + faixa declarada ADR-0076) vinha preparando**, é a
**emissão LÓGICA** do certificado: dado uma calibração APROVADA, reconciliar a
cobertura ponto-a-ponto, calcular a faixa efetiva do certificado, e materializar a
entidade `Certificado` com snapshots probatórios + numeração inviolável + perfil +
trilha WORM. **É isto que fecha `GATE-CAL-EMISSAO-RECONCILIA-FAIXA` + `GATE-ECMC-U-MAIOR-CMC`.**

**Escopo desta frente (M8 núcleo):** emissão lógica + reconciliação de cobertura +
numeração + snapshots + perfil + WORM. **PDF, assinatura, distribuição e pós-emissão
ficam para fatias seguintes (Wave A, quando a infra externa existir).**

## 2. Seam pronto (P0 — investigado 2026-05-31)

Tudo que a emissão metrológica consome JÁ existe (mapa em `T-CER-000-investigacao.md`):

| Insumo | Onde | Estado |
|--------|------|--------|
| Estado terminal `APROVADA` (2ª conferência ADR-0026) | `domain/.../calibracao/enums.py` + `aprovar_2a_conferencia.py` | ✅ |
| Pontos medidos `LeituraSnapshot` (`ponto_calibracao`, `valor_lido`, `unidade`) | `domain/.../calibracao/entities.py` + `repositories.obter_leituras_por_calibracao` | ✅ |
| Incerteza `OrcamentoIncertezaSnapshot` (`U_expandida`, `k`, `nivel_confianca`) | `domain/.../calibracao/entities.py` | ✅ (1 por orçamento — ver Q1) |
| Faixa declarada `grandeza_calibrada`+`faixa_calibrada_declarada` (ADR-0076) | `domain/.../calibracao/entities.py` | ✅ |
| Porta `cmc_para(tenant, grandeza, ponto, data) -> Decimal\|None` (U≥CMC) | `infrastructure/.../escopos_cmc/query_service.py` | ✅ |
| `cobertura.avaliar_u_cmc` + `menor_cmc_por_faixa` | `domain/.../escopos_cmc/cobertura.py` | ✅ |
| Snapshot probatório `EscopoUsado` (campos U na emissão) | `domain/.../escopos_cmc/entities.py` | ✅ |
| Snapshot probatório `ProcedimentoUsado` | `domain/.../procedimentos_calibracao/entities.py` | ✅ |
| VO `NumeroCertificado` (`<SLUG>-<YYYY>-<NNNNNN>`) | `domain/metrologia/value_objects.py` | ✅ |
| Stub `Certificado` (id/tenant/equipamento/status RASCUNHO/EMITIDO/REVOGADO) | `infrastructure/certificados/models.py` | ✅ (estender) |
| Evento bus `calibracao.aprovada` | `domain/.../calibracao/entities.py` (MAPA) | ✅ |
| Padrão WORM hash-chain (`append_evento_*`, advisory lock, `ACOES_CANONICAS`) | M4/M6/M7 | ✅ (replicar) |
| Perfil `tenant_perfil_e` + snapshot `perfil_no_evento` (ADR-0067) | `infrastructure/authz/predicates.py` + middleware | ✅ |

**FALTA (diferido):** sequence PG do certificado, motor PDF, A3/Lacuna, OCSP, TSA,
portal, e-mail, export ANVISA, recall/suspensão/errata.

## 3. Escopo desta frente — US cobertas (núcleo)

Deriva do PRD; só a parte LÓGICA/metrológica:

| US do PRD | O que entra AGORA | O que difere |
|-----------|-------------------|--------------|
| **US-CER-001** Gerar certificado | emissão lógica: consome APROVADA, reconcilia cobertura, crava snapshot imutável (cliente/instrumento/padrões/leituras/incerteza/EscopoUsado/ProcedimentoUsado), `perfil_emissor_no_momento` WORM, gating de campos por perfil (dados estruturados, NÃO render), evento `Certificados.CertificadoReconciliado` (emissão metrológica; `CertificadoEmitido` normativo cl. 7.8 dispara só na assinatura A3 — Wave A) | render PDF/A-3, template visual |
| **US-CER-003** Numeração sequencial inviolável | sequence PG `certificado_numero_seq` + `NumeroReservado` (TTL) + trigger virada anual + cancelamento preserva número | gap-detection job (diferível) |
| **US-CER-004** Reemissão versionada | nova versão `v(N+1)` linkada à `v(N)`, motivo ≥50 chars, `v(N)`→SUBSTITUIDA WORM | aviso no portal (UX) |
| **US-CER-013** Cert com equipamento baixado | `snapshot_equipamento_json` imutável na emissão (paridade calibração) | selo no PDF |

**NOVA INV de reconciliação (ADR-0076 / ordem-dependencia #4):** a cobertura
DEFINITIVA do certificado é medida contra os **pontos efetivamente medidos** (CGCRE
não extrapola): `pontos ⊆ declarada ⊆ escopo` + `U(ponto) ≥ CMC(ponto)` +
`faixa_certificado = [min,max] dos pontos válidos`.

## 4. Non-goals desta frente (diferidos — declarados)

US-CER-002 (A3/OCSP/TSA) · US-CER-005 (e-mail) · US-CER-006 (portal) · US-CER-007
(foto) · US-CER-008 (NC) · US-CER-009 (QR público) · US-CER-010 (templates visuais) ·
US-CER-016/017 (export ANVISA + PDF/A-3) · US-CER-018/019/020 (recall/suspensão/errata) ·
geração de PDF de qualquer tipo. **Todos rastreados como GATE-CER-* Wave A.** A
emissão desta frente produz o certificado em estado lógico (`EMITIDO_LOGICO` /
pré-PDF) com todos os dados estruturados congelados — o PDF/assinatura plugam depois
sobre o snapshot já imutável.

## 5. Invariantes (a cravar em REGRAS — INV-CER-*)

Núcleo (esta frente). Numeração definitiva dos IDs no `/plan`:
- **INV-CER-EMISSAO-001** — só calibração `APROVADA` emite (2ª conferência perfil A); estado anterior → 422 `CALIBRACAO_NAO_APROVADA`.
- **INV-CER-RECONCILIA-001** — cobertura por pontos medidos: `∀ ponto ∈ leituras: ponto ∈ faixa_calibrada_declarada` (CGCRE não extrapola); ponto fora → bloqueio na emissão RBC.
- **INV-CER-RECONCILIA-002** — `U(ponto) ≥ CMC(ponto)` via porta `cmc_para` (ADR-0074 cond. 2 / INV-ECMC-009); `U < CMC` em ponto → bloqueio RBC (fecha GATE-ECMC-U-MAIOR-CMC). [Q1: granularidade de U]
- **INV-CER-RECONCILIA-003** — `faixa_certificado = [min,max]` dos pontos VÁLIDOS, não a declarada nem o escopo (cravado no snapshot, imutável).
- **INV-CER-NUM-001/002** — numeração inviolável (PRD §6.2): tenant+tipo+ano, reserva TTL 5min, virada anual, cancelamento preserva número; reuso → erro PG.
- **INV-CER-PERFIL-001** — campos do certificado MATCH `Tenant.perfil_regulatorio` vigente (PRD §6.1); RBC em perfil≠A → 403 (defesa L6).
- **INV-CER-SNAPSHOT-PERFIL-001** — `perfil_emissor_no_momento CHAR(1) NOT NULL` cravado no INSERT, imutável (ADR-0067 §3).
- **INV-CER-WORM-001** — certificado emitido é imutável; correção só via reemissão versionada (US-CER-004); DELETE bloqueado por trigger.
- **Reusadas:** INV-CAL-WORM-001, INV-ECMC-008/009, INV-VIG-*, INV-SOFT-*, INV-TENANT-*, INV-TENANT-PERFIL-001/003/004, INV-DOC-CANON-001, INV-HMAC-001..005.

## 6. Fatias propostas (refinar no /plan)

- **Fatia 0** — peça compartilhada de reconciliação: extrair/centralizar a geometria
  `pontos ⊆ declarada` reusando `faixa_cobertura` (M7 Fatia 0) + `avaliar_u_cmc` (M6).
- **Fatia 1a** — domínio puro: entidades `CertificadoSnapshot` + `CertificadoUsado`/snapshots,
  enums de estado, transições, reconciliação de cobertura (pura), repository Protocol.
- **Fatia 1b** — schema+infra: estender model `Certificado` (colunas tipadas) + migrations
  RLS v2/WORM Padrão B/grants/seed + sequence PG `certificado_numero_seq` + `NumeroReservado`
  + trigger virada anual + mappers/repositories + drill.
- **Fatia 2** — use cases: `emitir_certificado` (consome APROVADA, reconcilia, crava snapshot,
  numera, perfil) + `reemitir_certificado` (versão) + CertificadoViewSet REST + idempotência +
  eventos WORM.
- **Fatia 3** — fechamento: INV-CER-* em REGRAS + TestINV_CER + hooks + matriz-reconciliacao + P9.

## 7. Perguntas de revisão (rotear — NÃO inventar)

**Para `consultor-rbc-iso17025`:**
- **Q1 (granularidade de U):** o `OrcamentoIncertezaSnapshot` tem **um** `U_expandida` por
  orçamento (1:1 com calibração). A reconciliação `U(ponto) ≥ CMC(ponto)` precisa de U por
  ponto. Opções: (a) U único do orçamento aplicado a todos os pontos; (b) orçamento por
  ponto/faixa; (c) U por ponto derivado. Qual é metrologicamente correto p/ RBC (a CMC
  varia por ponto)? Isto define a estrutura da reconciliação.
- **Q2:** `faixa_certificado` = envelope `[min,max]` dos pontos válidos é suficiente, ou
  CGCRE exige enumerar os pontos discretos (sem implicar continuidade entre eles)?
- **Q3:** quando um ponto medido falha `U≥CMC` ou está fora da declarada: bloqueia a emissão
  inteira (perfil A) ou emite excluindo o ponto + marca não-RBC naquele ponto? (ILAC-P14)

**Para `tech-lead-saas-regulado`:**
- **Q4:** estender o stub `Certificado` (Marco 2, `infrastructure/certificados/`) ou criar
  `infrastructure/metrologia/certificados/` aninhado (ADR-0072)? O stub tem trigger de
  imutabilidade de equipamento que não pode quebrar.
- **Q5:** sequence PG do certificado — replicar o padrão M4 (`calibracao_numero_seq_global` +
  trigger) ou o padrão OS (ADR-0056 sequence global + unique composto)?
- **Q6:** estado lógico pré-PDF — nome do estado (`EMITIDO_LOGICO`? `PENDENTE_DOCUMENTO`?) e
  como o snapshot imutável convive com a anexação posterior de PDF/assinatura sem violar WORM.

## 8. Veredito

Spec revisada por `consultor-rbc` + `tech-lead` (2026-05-31) — **ambas APROVA COM
CORREÇÕES**. Consolidado + resolução das 6 perguntas + tensão terminológica em
`reviews-consolidado.md`.

## 9. Decisões pós-revisão (cravadas — feed do /plan)

- **Q1/NC-01 (CRÍTICO):** incerteza **por ponto** → **ADR-0077** (retrofit M4
  `OrcamentoIncertezaSnapshot`). É o **item #0** do M8 (frente SAN-INCERTEZA-PONTO,
  ANTES da Fatia 2 `emitir_certificado`). Reconciliação = tabela ponto-a-ponto.
- **Q2/NC-02:** `faixa_certificado` = pontos discretos válidos; `[min,max]` só metadado.
- **Q3/NC-03:** partição `pontos_rbc`/`pontos_nao_rbc` + decisão WORM do RT (não bloqueia
  cert inteiro; distingue "fora da declarada" de "U<CMC dentro").
- **Q4/TL-01:** tabela `certificados` achatada (contrato trigger INV-025) + lógica
  aninhada → **ADR-0078**. Migration aditiva.
- **Q5/TL-03:** `numero_interno` (sequence M4) + `NumeroCertificado` visível (reserva TTL).
- **Q6:** 2 entidades — `Certificado` (WORM, `status='emitido'` na emissão lógica) +
  `DocumentoCertificado` (PDF/A3 mutável-até-assinar, Wave A). Evento desta frente =
  `Certificados.CertificadoReconciliado` (não `Emitido` — este é normativo cl. 7.8, na
  assinatura). NÃO inventar estado `EMITIDO_LOGICO`.
- **TL-04:** cravar `INV-CER-SNAPSHOT-CMC` (read-path nunca reconsulta `cmc_para`/`tenant_perfil_e`).
- **NC-09:** trava interina CGCRE (`Tenant.acreditacao_vigencia_fim > today`) antes de reconciliar RBC.
- **NC-04/05/06/07, TL-02/05:** ver `reviews-consolidado.md` (regra de decisão snapshot;
  k+nível+ν_eff por ponto; flag U==CMC; vigência padrões; quebrar Fatia 1b; `tem_emitido` explícito).

**Próximo:** `/plan` (resolve caminho b1/b2 do ADR-0077, numera INV-CER + tasks, crava
ADRs 0077/0078). **Bloqueio de ordem:** retrofit M4 (ADR-0077) antes da Fatia 2.
