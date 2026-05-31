---
owner: agente-ia
revisado-em: 2026-05-31
status: stable
diataxis: reference
audiencia: [agente, tech-lead, consultor-rbc, roldao]
marco: M8-certificados
tipo: reviews-consolidado
---

# Revisões consolidadas — spec M8 `certificados` (núcleo de emissão)

> Síntese das revisões `consultor-rbc-iso17025` (metrológica) + `tech-lead-saas-regulado`
> (arquitetural) da `spec.md` (2026-05-31). **Ambas: APROVA COM CORREÇÕES.** Resolve a
> colisão de ADR (ambos propuseram "0077") e a tensão terminológica. Feed do `/plan`.

## Veredito

| Revisor | Veredito | Bloqueia /plan? |
|---------|----------|-----------------|
| consultor-rbc-iso17025 | APROVA COM CORREÇÕES | **SIM (NC-01 CRÍTICO)** |
| tech-lead-saas-regulado | APROVA COM CORREÇÕES | não (correções endereçáveis no /plan) |

## Achados metrológicos (consultor-rbc)

| ID | Sev | Resolução |
|----|-----|-----------|
| **NC-01** | **CRÍTICO** | U deve ser **por ponto**; M4 tem U único (1:1). Retrofit M4 → **ADR-0077** (orçamento por ponto; b1 preferido / b2 função U(X) declarada). Reconciliação = tabela ponto-a-ponto `{ponto, valor, U, k, nível_conf, ν_eff, cmc_ponto, atende}`. **Bloqueia Fatia 2.** |
| **NC-02** | ALTO | `faixa_certificado` = **pontos discretos válidos**; `[min,max]` só metadado rotulado "faixa calibrada" (não implica continuidade — CGCRE não extrapola). Reescrever INV-CER-RECONCILIA-003. |
| **NC-03** | ALTO | Ponto problemático NÃO bloqueia cert inteiro: partição `pontos_rbc`/`pontos_nao_rbc` + **decisão WORM do RT** para excluir ponto (padrão ADR-0070). Distinguir "fora da declarada" (furo de processo → RT decide) de "U<CMC dentro" (bug de orçamento ou exclusão legítima). Não auto-rebaixar silenciosamente. |
| **NC-04** | MÉDIO | Congelar snapshot da **regra de decisão** (cl. 7.8.6 / ADR-0024) quando aplicável. |
| **NC-05** | MÉDIO | Snapshot por ponto carrega `{U, k, nivel_confianca, ν_eff}`, não só U (NIT-DICLA-030 8.2.6). |
| **NC-06** | BAIXO | Flag anti-cópia `u_igual_cmc_suspeita` por ponto (P2, não bloqueia — RBC-NC-07). |
| **NC-07** | BAIXO | Confirmar vigência da calibração dos padrões usados no snapshot (cl. 6.5). |
| **NC-08** | BAIXO | (ver tensão resolvida abaixo) — evento desta frente = `CertificadoReconciliado`, não `CertificadoEmitido`. |
| **NC-09** | MÉDIO | Trava interina CGCRE: só reconcilia RBC quando `Tenant.acreditacao_vigencia_fim > today` (campo já existe — ADR-0067). Não diferir sem trava. |

## Achados arquiteturais (tech-lead)

| ID | Sev | Resolução |
|----|-----|-----------|
| **TL-01** | ALTO | Tabela `certificados` é contrato cross-app (trigger INV-025 lê `status='emitido'` literal). Tabela fica achatada; lógica aninhada. Migration aditiva. → **ADR-0078**. |
| **TL-03** | MÉDIO | Separar `numero_interno` (sequence M4-style, buracos OK) de `NumeroCertificado` visível (reserva TTL + confirmação transacional, sem buracos visíveis — US-CER-003). |
| **TL-02** | MÉDIO | Quebrar Fatia 1b em **1b-schema** (model+RLS+WORM) e **1b-numeração** (sequence+NumeroReservado+trigger virada). |
| **TL-04** | MÉDIO | Cravar **INV-CER-SNAPSHOT-CMC**: read-path do certificado emitido NUNCA reconsulta `cmc_para`/`tenant_perfil_e`; lê sempre os snapshots. (WORM furado por LEITURA, não escrita.) |
| **TL-05** | BAIXO | `tem_emitido` explícito (`.filter(status='emitido', revogado_em__isnull=True)`), não confiar no default manager. |
| **TL-06** | BAIXO | (ver tensão resolvida abaixo). |

## Respostas às 6 perguntas (cravadas)

- **Q1 (RBC):** U **por ponto** (NC-01 / ADR-0077). Estrutura = tabela ponto-a-ponto.
- **Q2 (RBC):** pontos discretos enumerados; `[min,max]` só metadado (NC-02).
- **Q3 (RBC):** não bloqueia cert inteiro — partição rbc/não-rbc + decisão WORM do RT (NC-03).
- **Q4 (tech-lead):** híbrido — tabela achatada + lógica aninhada (ADR-0078).
- **Q5 (tech-lead):** sequence M4-style p/ `numero_interno` + `NumeroReservado` p/ número visível (TL-03).
- **Q6 (tech-lead):** **2 entidades** — `Certificado` (WORM) + `DocumentoCertificado` (mutável-até-assinar, Wave A).

## Tensão resolvida — `EMITIDO_LOGICO` vs `status='emitido'`

Os dois revisores divergiram:
- **RBC (NC-08):** sem A3 não é "emitido" no sentido normativo (cl. 7.8) — evento = `CertificadoReconciliado`.
- **tech-lead (TL-06):** o trigger INV-025 lê `status='emitido'` literal; equipamento deve travar na emissão LÓGICA (números definitivos).

**Síntese (decisão do agente — não é ambiguidade de produto, é reconciliação técnica):**
ambos estão certos no seu domínio e não se contradizem:
- A entidade `Certificado` usa **`status='emitido'`** desde a emissão lógica — satisfaz o
  contrato do trigger (TL-01/ADR-0078) E trava o equipamento (correto: equipamento com
  cert metrológico emitido não muda tag/NS independente do PDF ter saído).
- O `'emitido'` aqui significa **emissão metrológica** (números definitivos, snapshot
  congelado), NÃO "entregue ao cliente". A entrega normativa cl. 7.8 (RBC) só acontece
  quando o `DocumentoCertificado` é **assinado** (A3 — Wave A); até lá o certificado
  **não é distribuível**.
- **NÃO se inventa o estado `EMITIDO_LOGICO`** na entidade metrológica (evita reabrir
  WORM quando o PDF assinar). A pendência de documento vive no `DocumentoCertificado`
  (`AGUARDANDO_GERACAO → GERADO → ASSINADO → CARIMBADO`).
- **Evento desta frente: `Certificados.CertificadoReconciliado`** (NC-08 atendida) — o
  `CertificadoEmitido` normativo (cl. 7.8) dispara na assinatura (Wave A). A frente
  produz reconciliação metrológica + status `'emitido'` interno + evento `Reconciliado`.

## ADRs novas

| ADR | Tema | Origem | Status |
|-----|------|--------|--------|
| **0077** | Orçamento de incerteza por ponto (retrofit M4) | RBC NC-01 | proposta |
| **0078** | certificados: tabela achatada + lógica aninhada | tech-lead TL-01 | proposta |

## Drills recomendados (GATE-CER-DRILL-LOCAL)

- Imutabilidade cruzada: emitir cert REAL (`status='emitido'`) → UPDATE tag/NS/fabricante de equipamento → confirmar bloqueio trigger INV-025 (fecha loop Q4).
- Numeração sem buraco (TL-03): emitir → abortar antes do commit → emitir de novo → 2º pega número reservado (sem buraco visível). Threaded = TRACK Wave A.
- Anti-reconsulta (TL-04): emitir → revisar escopo-cmc (muda CMC vigente) → reler cert → `cmc_no_ponto` exibido é o do SNAPSHOT, não o novo vigente.

## Próximo passo

`/plan` resolve: caminho do retrofit M4 (ADR-0077 b1 vs b2), partição rbc/não-rbc
(NC-03), dual numbering (TL-03), 2 entidades (Q6), INV-CER-SNAPSHOT-CMC (TL-04),
trava CGCRE interina (NC-09), numeração final das INV-CER + tasks. **Pré-requisito de
fatia: o retrofit M4 (frente SAN-INCERTEZA-PONTO / ADR-0077) vem ANTES da Fatia 2
(emitir_certificado) — é o item #0 da ordem do M8.**
