---
owner: roldao
revisado-em: 2026-05-23
status: minuta
aguarda-corretora-susep: true
selo: "PRÉ-COTAÇÃO — REQUER CORRETORA SUSEP CREDENCIADA"
finalidade: consolidar todos os GATEs de seguro Wave A (catálogo único)
---

# GATEs de seguro — consolidado Wave A

> Todos os GATEs aqui exigem corretora SUSEP humana pra emissão de apólice real.
> Severidade segue INV-RITUAL-001: GATE aberto bloqueia fase quando marcado bloqueante.

| GATE | Status | Modalidade | Gatilho de fechamento | Bloqueia | Prazo / Urgência |
|---|---|---|---|---|---|
| **GATE-SEG-BPT-1** | 🔴 EMERGENCIAL | BPT (Modalidade 4) | Apólice BPT emitida antes da próxima recepção de instrumento físico em Balanças Solution | Dogfooding em curso | **IMEDIATO** — Balanças Solution já recebe instrumentos (CC art. 627) |
| **GATE-SEG-CAP-1** | 🟡 em andamento | (contratual — não apólice) | Cap responsabilidade Aferê no DPA = 12x mensalidade ou R$ 500k, o maior | 1º tenant externo pago | Onda 7 (jurídico) — quase fechado |
| **GATE-SEG-CYBER-1** | 🔴 aberto | Cyber (Modalidade 2) | Cyber R$ 5M agregado + `aggregate reinstatement` emitido | 1º tenant externo pago | Pré-Wave A externo |
| **GATE-SEG-EO-1** | 🔴 aberto | E&O ampliado (Modalidade 1) | E&O R$ 5-10M com sublimite `pharmaceutical/food recall extension` R$ 3M | Aceite de tenant farma/alimento | Pré-1º tenant farma — exige apólice complementar do próprio tenant |
| **GATE-SEG-DBI-1** | 🔴 aberto | Dependent Service BI (Modalidade 6) | CBI R$ 1M agregado com 8 sub-operadores nomeados (AWS KMS, B2, PlugNotas, Lacuna, Hostinger, Anthropic, Grafana, Axiom) | 1º tenant externo pago | Pré-Wave A externo |
| **GATE-SEG-ACR-1** | 🔴 aberto | Accreditation Loss Extension (Modalidade 7) | Apólice ACR R$ 2M agregado emitida | 1º tenant RBC acreditado | Pré-1º tenant RBC |
| **GATE-SEG-VIST-1** | 🟡 aberto | E&O `pareceres técnicos` | Cláusula `pareceres técnicos assinados via plataforma` ativa em apólice E&O | Habilitar `tipo=vistoria` (ADR-0023) em tenant externo | Junto com GATE-SEG-EO-1 |
| **GATE-SEG-META-1** | 🟡 aberto | E&O `consequential regulatory damages` | Cláusula nomeando SEFAZ + Receita + INMETRO + CGCRE + ANPD ativa | 1º tenant farma/RBC | Junto com GATE-SEG-EO-1 |
| **GATE-SEG-A3-1** | 🟡 aberto | Cyber `third-party credential abuse` | Cláusula ativa em apólice cyber | 1º tenant externo | Junto com GATE-SEG-CYBER-1 |
| **GATE-SEG-BPT-2** | 🟡 aberto | BPT `named insured by date of loss` + DPA tenant↔Aferê | Cláusula + DPA emitidos | 1º tenant externo com Marco 2 (transferência) | Junto com GATE-SEG-CAP-1 |
| **GATE-SEG-VEIC-1** | 🟡 aberto | Extensão veicular UMC (Modalidade 5) | Apólice veicular UMC emitida | Habilitar OS de campo com padrão metrológico em trânsito | Pré-OS campo |
| **GATE-SEG-RT-RC-1** | 🟢 V2 | RC profissional RT vendor (`RC-RT-vendor-v2.md`) | Apólice RC R$ 1M/ano emitida pra RT vendor próprio | Aferê fornecer RT credenciado próprio (V2 — quando ADR-0022 V2 entrar) | V2 |
| **GATE-SEG-DRILL-1** | 🔴 aberto | Operacional (não apólice) | Drill anual incidente cyber+ANPD executado + relatório arquivado | Aderência ANPD 72h notificação | Anual — começar antes 1º tenant externo |

## Legenda

- 🔴 = aberto bloqueante imediato/Wave A
- 🟡 = aberto, fecha junto com modalidade-mãe
- 🟢 = V2 (não bloqueia Wave A)

## Notas

- **GATE-SEG-BPT-1 é o único IMEDIATO** — Balanças Solution dogfooding em curso configura CC art. 627 depositário hoje.
- **GATE-SEG-CAP-1** é contratual (DPA), não apólice — fechamento em Onda 7 jurídica.
- **GATE-SEG-RT-RC-1** detalhado em `RC-RT-vendor-v2.md`.
- **GATE-SEG-DRILL-1** vincula seguros à conformidade LGPD operacional (drill anual = controle compensatório que reduz prêmio cyber).

## Rastreabilidade

Todos os GATEs referenciados em:
- ADR-0028 (mapa de coberturas)
- AGENTS.md §12 (pendências reais — corretora SUSEP humana)
- CURRENT.md (prioridade #1: GATE-SEG-BPT-1)
- `briefing-corretora-susep.md` §10
