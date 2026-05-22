---
adr: 0028
titulo: Mapa de coberturas de seguro Wave A — 5 modalidades pré-1º tenant externo
status: proposta
data: 2026-05-23
proposto-por: agente (auditoria 10 lentes — TEMA-F.5 + TEMA-G)
revisado-por: corretora-seguros-saas + advogado-saas-regulado
bloqueia-fase: 1º tenant externo pago + Marco 3 dogfooding BPT
depende-de: ADR-0019 (responsabilidade civil código IA), ADR-0023 (OS com Atividades — atividade vistoria gera passivo)
---

# ADR-0028 — Mapa de coberturas Wave A

## Contexto

ADR-0019 (responsabilidade civil código IA) cravou pilares E&O + cyber genérico. Auditoria 10 lentes (corretora-seguros-saas — TEMA-G) identificou **5 GAPs CRÍTICOS** de cobertura não endereçados:

1. **BPT (Bens em Poder de Terceiro)** — custódia física do instrumento no laboratório por dias/semanas. Aferê é depositário civil (CC art. 627). Ausente em ADR-0019. **GATE imediato — Balanças Solution dogfooding já recebe instrumentos de cliente.**
2. **Atividade `vistoria` (ADR-0023)** — laudo civil sem cobertura E&O dimensionada pra parecer técnico humano.
3. **Garantia metrológica do certificado** — cliente farma usa cert pra liberar lote → recall. Cláusula `consequential regulatory damages` obrigatória.
4. **Cyber A3 do RT** — comprometimento de chave A3 do RT do tenant (phishing). Cláusula `third-party credential abuse` obrigatória.
5. **Transferência de equipamento mid-OS (Marco 2)** — segurado BPT indefinido. Cláusula `named insured by date of loss`.

Esta ADR consolida o mapa de coberturas Wave A — base do briefing pra corretora SUSEP humana.

## Decisão

**Adotar 5 modalidades complementares ao ADR-0019**, com capitais e cláusulas específicas, contratadas via corretora SUSEP humana antes do 1º tenant externo pago.

### Modalidade 1 — E&O (Errors & Omissions) ampliado

- **Capital agregado anual:** R$ 3M
- **Franquia:** R$ 25k por evento
- **Cláusulas obrigatórias:**
  - `Pareceres técnicos assinados via plataforma` (cobre `tipo=vistoria` da ADR-0023)
  - `Consequential regulatory damages` (Receita/INMETRO/CGCRE invalidando medição)
  - `Right to defend` ampliado (inclui disputa de cobrança US-OS-005)
  - **REJEITAR exclusão genérica de "código gerado por IA sem revisão humana"** — neutralizada pelos 3 pilares ADR-0019 + `controles-compensatorios-codigo-ia.md`

### Modalidade 2 — Cyber + responsabilidade de dado

- **Capital agregado anual:** R$ 2M
- **Franquia:** R$ 15k por evento
- **Cláusulas obrigatórias:**
  - `Third-party credential abuse / social engineering coverage` (A3 do RT comprometido — phishing)
  - `Confidential business information of insured's clients` (foto/EXIF de instrumento, NS, layout fábrica)
  - `Dependent business interruption — tenant rework cost` (perda de dado pré-WORM gera retrabalho remunerado)
  - `Multi-claim aggregate` anual ≥ R$ 5M consolidado E&O+Cyber

### Modalidade 3 — D&O (Directors & Officers)

- **Capital agregado anual:** R$ 1M
- **Cláusulas obrigatórias:**
  - `Personal liability for technical decisions` (cobre Roldão como pessoa física até RT vendor V2)

### Modalidade 4 — BPT (Bens em Poder de Terceiro)

- **Capital por sinistro:** R$ 500k a R$ 2M (baseado em estoque médio de piso × 3 instrumentos premium)
- **Franquia:** 2% do capital por evento
- **Cláusulas obrigatórias:**
  - `Named insured by date of loss` (resolve transferência mid-OS — GAP-SEG-05)
  - `Multi-activity coverage within single custody event` (manutenção + calibração — GAP-SEG-11)
  - Cobertura mundial (clientes em qualquer estado BR)
  - **GATE IMEDIATO** — Balanças Solution dogfooding já recebe instrumentos hoje (CC art. 627 depositário)

### Modalidade 5 — Extensão veicular UMC

- **Capital por veículo:** R$ 50k a R$ 200k (padrão F1 R$ 15-80k + UMC instrumentação)
- **Cláusulas obrigatórias:**
  - `Equipamento de precisão em trânsito` (cobre padrão metrológico em deslocamento)
  - Compatibilidade com apólice veicular existente do tenant

### Cláusulas universais (todas as 5 modalidades)

- Cobertura retroativa (cobre ato pré-apólice, claim pós).
- Right to defend ampliado.
- **REJEITAR:** franquia > 5% do capital por evento; exclusão "depositário" (incompatível com modelo dogfooding); exclusão de multas regulatórias (LGPD + INMETRO + CGCRE devem ser INCLUÍDAS).

### Prêmio anual estimado consolidado

**R$ 25k a R$ 50k/ano** (5 modalidades juntas, porte PME inicial — estimativa corretora pré-cotação).

## Briefing pra corretora SUSEP humana

> O Aferê é SaaS multi-tenant para empresas de assistência técnica metrológica (ISO 17025). Modelo 100% agentes IA com 3 pilares de controles compensatórios (ADR-0019). Operação envolve: (a) custódia física de instrumentos do cliente no laboratório por dias/semanas (modelo "OS com Atividades" — ADR-0023 — admite 6 tipos: calibração, manutenção corretiva, manutenção preventiva, instalação, verificação INMETRO, vistoria); (b) emissão de certificado metrológico com validade técnica regulatória (ISO 17025 cl. 8.4); (c) assinatura A3 ICP-Brasil pelo RT humano do tenant; (d) técnico em campo com padrão de massa classe F1; (e) armazenamento de fotos do instrumento (EXIF + geo) por LGPD. Cenário de risco: erro de medição em certificado afeta liberação de lote farma/Receita; comprometimento de A3 do RT do tenant; dano físico ao instrumento durante custódia. Solicito cotação para 5 modalidades: E&O (R$ 3M agregado), Cyber (R$ 2M agregado), D&O (R$ 1M), BPT (R$ 1-2M por sinistro), Extensão veicular para padrão metrológico (R$ 100k por veículo). Cláusulas críticas: ver lista anexa de 12 itens. Janela: emissão antes do 1º tenant externo pago (data a definir).

## Corretoras candidatas

- **Marsh Brasil** (já citada em ADR-0019)
- **AON Tech**
- **Howden Brasil**

Pedir 3 propostas + comparar. Decisão Roldão.

## Caminhos alternativos considerados

| Alternativa | Por que NÃO |
|---|---|
| Apólice única consolidada (1 corretora) | Risco de concentração + dificulta substituição |
| BPT diferida pós-1º tenant | **INACEITÁVEL** — Balanças Solution dogfooding já em custódia hoje (R-073 ativado) |
| Auto-seguro (provisão financeira) | Provisão R$ 2M+ é inviável pra Aferê pré-Wave A |

## Consequências

### Positivas

- 5 GAPs CRÍTICOS de cobertura endereçados.
- BPT no curto prazo protege dogfooding atual (R-073).
- Apólice E&O ampliada cobre `vistoria` (ADR-0023) + cyber A3 (TEMA-G.4).
- Briefing pronto pra corretora.

### Negativas (mitigáveis)

- Custo anual R$ 25-50k.
- Tempo de cotação: 4-6 semanas estimado.

## Non-goals

- NÃO substitui apólice civil dos veículos do tenant (cada tenant decide).
- NÃO substitui apólice cyber do tenant (tenant tem cobertura própria — Aferê é fornecedor).

## GATEs Wave A criados

- **GATE-SEG-BPT-1** (IMEDIATO) — apólice BPT antes da próxima recepção de instrumento em Balanças Solution.
- **GATE-SEG-VIST-1** — apólice E&O ampliada antes de habilitar `tipo=vistoria` em tenant externo.
- **GATE-SEG-META-1** — apólice E&O com `consequential regulatory damages` antes do 1º tenant farma/RBC.
- **GATE-SEG-A3-1** — apólice cyber com `third-party credential abuse` pré-tenant externo.
- **GATE-SEG-BPT-2** — DPA padrão tenant↔Aferê + BPT `named insured by date of loss` antes do 1º tenant externo com Marco 2 (transferência).
- **GATE-SEG-VEIC-1** — extensão veicular antes de habilitar OS de campo com UMC.

## Implicações pro faseamento

- **Wave imediata (dogfooding):** GATE-SEG-BPT-1 sai antes da próxima OS de manutenção/calibração que receba instrumento de cliente em Balanças Solution.
- **Pré-1º tenant externo:** GATE-SEG-VIST-1 + META-1 + A3-1 + BPT-2 + VEIC-1.
- **Briefing corretora** entregue antes de Marco 3 começar P4.

## Status

Proposta — aguarda aceite Roldão. Briefing pra corretora SUSEP humana redigido e pronto. BPT é EMERGENCIAL pelo modelo dogfooding atual.
