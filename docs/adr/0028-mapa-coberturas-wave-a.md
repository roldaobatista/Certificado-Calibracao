---
adr: 0028
titulo: Mapa de coberturas de seguro Wave A — 7 modalidades pré-1º tenant externo (expandida Onda 8)
status: proposta
data: 2026-05-23
revisado-em: 2026-05-23
proposto-por: agente (auditoria 10 lentes — TEMA-F.5 + TEMA-G; expansão Onda 8 — auditoria projeto-inteiro rodada 1)
revisado-por: corretora-seguros-saas + advogado-saas-regulado
aguarda-corretora-susep: true
selo: "PRÉ-COTAÇÃO — REQUER CORRETORA SUSEP CREDENCIADA (Lei 4.594/64 + Res. CNSP)"
bloqueia-fase: 1º tenant externo pago + Marco 3 dogfooding BPT
depende-de: ADR-0019, ADR-0022, ADR-0023, ADR-0025
observacao: "Expandida pós-auditoria projeto-inteiro Onda 8 (rodada 1) — aguarda parecer corretora SUSEP humana antes de emissão."
---

# ADR-0028 — Mapa de coberturas Wave A (7 modalidades)

## Contexto

ADR-0019 cravou pilares E&O + cyber genérico. Auditoria 10 lentes TEMA-F.5+G identificou 5 GAPs CRÍTICOS. **Auditoria projeto-inteiro rodada 1 (2026-05-23)** elevou pra 8 CRÍTICOS + 6 ALTOS + 5 MÉDIOS — destaques que motivam expansão pra 7 modalidades:

- Cap contratual responsabilidade ausente no DPA (resolvido em Onda 7 — DPA + cap 12x mensalidade ou R$ 500k, o maior).
- Cobertura BI consequente "perda de acreditação CGCRE do tenant" não negociada.
- Sub-operador crítico cai (AWS KMS, B2, PlugNotas, Lacuna, Hostinger) > 4h → tenant perde receita / janela auditoria.
- Cyber R$ 2M agregado abaixo do padrão LGPD pra 50+ tenants.
- Franquia BPT 2% (R$ 40k/evento) proibitiva.
- Recall farma/alimento sem sublimite específico.
- Cláusulas nomeadas faltantes: vicarious tenant on-site, time-source integrity defect, wrongful billing, long-tail custody 25 anos, software validation defect (ADR-0025), third-party credential abuse.

## Decisão

Adotar **7 modalidades complementares** ao ADR-0019, com capitais e cláusulas específicas, contratadas via corretora SUSEP humana antes do 1º tenant externo pago. **BPT permanece EMERGENCIAL** (Balanças Solution dogfooding já em custódia).

### Modalidade 1 — E&O (Errors & Omissions) AMPLIADO

- **Capital agregado anual:** **R$ 5M a R$ 10M** (faixa pra cotação)
- **Sublimite por evento:** R$ 3M
- **Sublimite nomeado `pharmaceutical/food recall extension`:** R$ 3M (excluir tenants farma/alimento sem aceite escrito + apólice complementar do tenant)
- **Franquia:** R$ 25k por evento
- **Cláusulas obrigatórias:**
  - `Pareceres técnicos assinados via plataforma` (`tipo=vistoria` ADR-0023)
  - `Consequential regulatory damages` nomeando **SEFAZ, Receita Federal, INMETRO, CGCRE, ANPD**
  - `Software validation defect causing accreditation suspension` (ADR-0025 cl. 7.11)
  - `Wrongful billing` (cobrança indevida billing-saas > R$ 50k)
  - `Long-tail data custody — 25 years` (custódia certificado/NFS-e B2 conforme matriz retenção ISO 17025 cl. 8.4)
  - `Vicarious liability — tenant operative on-site` (técnico tenant em campo causa dano)
  - `Right to defend` ampliado
  - **REJEITAR** exclusão "código gerado por IA sem revisão humana" (neutralizada por ADR-0019)

### Modalidade 2 — Cyber + responsabilidade de dado

- **Capital agregado anual:** **R$ 5M** (era R$ 2M — subido)
- **Sublimite por evento:** R$ 2M
- **Cláusula `aggregate reinstatement`:** 1 recomposição automática por ano após 1º sinistro
- **Franquia:** R$ 15k por evento
- **Cláusulas obrigatórias:**
  - `Third-party credential abuse / social engineering coverage` (A3 RT comprometido — phishing)
  - `Confidential business information of insured's clients` (foto/EXIF instrumento, layout fábrica)
  - `Dependent business interruption — tenant rework cost`
  - `Time-source integrity defect` (falha NTP/timestamp A3)
  - `Multi-claim aggregate` anual consolidado E&O+Cyber ≥ R$ 10M

### Modalidade 3 — D&O (Directors & Officers)

- **Capital agregado anual:** R$ 1M
- **Cláusulas obrigatórias:**
  - `Personal liability for technical decisions` (Roldão PF até RT vendor V2)
  - `Investigation costs coverage` (sindicância CGCRE/ANPD)

### Modalidade 4 — BPT (Bens em Poder de Terceiro) — EMERGENCIAL

- **Capital por sinistro:** R$ 500k a R$ 2M
- **Franquia:** **R$ 10.000-15.000/evento** (FIXO — substitui 2% capital)
- **Cláusulas obrigatórias:**
  - `Named insured by date of loss` (transferência mid-OS)
  - `Multi-activity coverage within single custody event` (manutenção + calibração na mesma OS)
  - Cobertura mundial BR
  - **GATE-SEG-BPT-1 IMEDIATO** — Balanças Solution dogfooding (CC art. 627 depositário)

### Modalidade 5 — Extensão veicular UMC

- **Capital por veículo:** R$ 50k a R$ 200k
- **Cláusulas:** `equipamento de precisão em trânsito`; compatível apólice veicular tenant

### Modalidade 6 — Dependent Service BI (Contingent Business Interruption) — NOVA

- **Capital agregado anual:** R$ 1M (agregado anual único)
- **Franquia temporal:** janela de espera 4h
- **Sub-operadores nomeados:** AWS KMS (sa-east-1 + us-east-1), Backblaze B2, PlugNotas, Lacuna Web PKI, Hostinger VPS, Anthropic API, Grafana Cloud, Axiom
- **Cláusulas obrigatórias:**
  - `Contingent business interruption — named third-party vendors`
  - `Cyber event triggered CBI`
  - `Reputational harm following downstream outage`
  - Cobertura SLA tenant degradado (refund/multa contratual ao tenant)

### Modalidade 7 — Accreditation Loss Extension — NOVA

- **Capital por evento:** R$ 500k
- **Agregado anual:** R$ 2M
- **Gatilho:** tenant perde escopo CGCRE/RBC ou tem auditoria de supervisão suspensa por indisponibilidade Aferê ou por defeito software (ADR-0025)
- **Cláusulas obrigatórias:**
  - `Accreditation suspension — direct loss + reaccreditation cost`
  - `Customer churn following accreditation event`
  - Cobertura honorários consultoria reacreditação

### Cláusulas universais (7 modalidades)

- Cobertura retroativa
- Right to defend ampliado
- **REJEITAR:** franquia > 5% capital/evento (exceto BPT fixo); exclusão "depositário"; exclusão multas LGPD+INMETRO+CGCRE+ANPD; exclusão "ato doloso" genérica; exclusão "código IA sem revisão humana".

### Prêmio anual estimado consolidado expandido

**R$ 60k a R$ 120k/ano** (7 modalidades, porte PME Wave A). Estimativa pré-cotação.

## Briefing pra corretora

Ver `docs/conformidade/comum/seguros/briefing-corretora-susep.md`.

## Corretoras candidatas

Marsh Brasil, AON Tech, Howden Brasil — pedir 3 propostas.

## GATEs Wave A (consolidados em `gates-seg.md`)

GATE-SEG-BPT-1 (IMEDIATO) · GATE-SEG-CAP-1 · GATE-SEG-CYBER-1 · GATE-SEG-EO-1 · GATE-SEG-DBI-1 · GATE-SEG-ACR-1 · GATE-SEG-VIST-1 · GATE-SEG-A3-1 · GATE-SEG-BPT-2 · GATE-SEG-VEIC-1 · GATE-SEG-RT-RC-1 (V2) · GATE-SEG-DRILL-1 · GATE-SEG-INMETRO-PRAZO-1 (NOVO P-OS-S6).

## Cláusulas adicionais — rev 2 (pós P3 Marco 3 — 2026-05-23)

**Origem:** parecer corretora M3 P-OS-S2/S3/S4/S5. REQUER CORRETORA SUSEP HUMANA pra confirmar viabilidade de cada cláusula no mercado segurador brasileiro hoje.

### Modalidade 1 (E&O ampliado) — cláusulas novas

- **`Wrongful billing` revisado:** remover gatilho R$ 50k; usar franquia fixa R$ 5k por evento, cobrindo de R$ 5k até sublimite por evento R$ 3M. Cobre R-OS-5 (cancelamento parcial × CR) e R-OS-9 (race valor_total). (GATE-SEG-EO-1)
- **`Tax penalty exposure — incorrect cancellation / late tax document`:** dentro do `consequential regulatory damages`, nomeando Receita Federal + SEFAZ específicos. Cobre R-OS-5 fiscal residual.
- **`Software validation defect causing accreditation suspension`** estendido: cláusula explicita que cobre **vetores upstream do módulo Calibração** (não só erro no cálculo de incerteza — também erro no controle de OS que precede a medição). Cobre R-OS-6 (concorrência cascateia recall farma — vetor M3→M4).
- **`Vicarious liability` expandido:** `Vicarious liability — tenant operative on-site OR tenant administrative decision via platform`. Cobre US-OS-013 dispensa de aceite gerencial (R-OS-13).

### Modalidade 2 (Cyber) — cláusulas novas

- **`Sensitive personal data — LGPD art. 11 (biometric, racial, health, religion) — affirmative coverage, no sub-aggregate restriction`:** cobre R-OS-3 (biometria cross-tenant). Sem sublimite separado para categoria especial. (GATE-SEG-CYBER-1)
- **`Image rights — incidental third-party capture in field service photo`:** cobre R-OS-12 (foto no-show captura terceiros — CC art. 20 + LGPD).

### Cláusula universal — rev 2

- **`Continuity of coverage clause` (P-OS-S6):** retroatividade contínua via renovação anual sem gap — cobre R-OS-7 (hash quebrado 25a depois, sinistro reportado em ano X+1 sobre fato do ano X-5). REQUER corretora SUSEP confirmar mercado.

## Status

Proposta rev 2 (7 modalidades + 6 cláusulas novas pós Marco 3 P3) — aguarda corretora SUSEP humana. BPT EMERGENCIAL.
