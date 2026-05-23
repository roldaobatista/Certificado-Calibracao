---
owner: roldao
revisado-em: 2026-05-23
status: minuta
aguarda-corretora-susep: true
selo: "PRÉ-COTAÇÃO — REQUER CORRETORA SUSEP CREDENCIADA"
fonte: ADR-0028 (expandida Onda 8)
finalidade: tabela única pronta pra corretora SUSEP cotar — 7 modalidades Wave A
---

# Planilha de cotação Wave A — 7 modalidades

> Selo: este documento NÃO substitui apólice. Apólice exige corretora SUSEP credenciada (Lei 4.594/64).

## Perfil do segurado (corretora preenche/valida)

| Campo | Valor declarado | Espaço corretora |
|---|---|---|
| Razão social | Balanças Solution / Aferê (entidade pré-Wave A) | _____ |
| CNPJ | (a informar) | _____ |
| Receita anual estimada Wave A | Dogfooding: ~R$ 0; Pós-1º tenant externo: R$ 60-200k MRR (R$ 720k-2,4M ARR estimado) | _____ |
| Nº tenants alvo Wave A | 1 dogfooding + 5-10 externos em 12 meses | _____ |
| País operação | Brasil (todos os estados) | _____ |
| Tipo cliente final | PME assistência técnica + lab calibração ISO 17025 + pequena indústria | _____ |
| Exposição internacional | AWS KMS us-east-1 (réplica MRK); Backblaze B2 datacenters US; Anthropic API US | _____ |
| Setor tenants | Metrologia; potencial farma/alimento (com aceite escrito) | _____ |
| Dados sensíveis tratados | PII (CPF/CNPJ/contatos), fotos+EXIF+geo, certificados ICP-Brasil A3, dados fiscais NFS-e | _____ |
| Volume dados estimado 12m | 50-200 GB outbox + 100-500 GB B2 WORM | _____ |
| Funcionários | 1 (Roldão) + agentes IA (ver ADR-0019) | _____ |

## Tabela cotação — 7 modalidades

| # | Modalidade | Capital agregado anual sugerido | Sublimite por evento | Franquia | Cláusulas nomeadas obrigatórias | Exclusões aceitas | Justificativa de necessidade | Cenário-pior estimado |
|---|---|---|---|---|---|---|---|---|
| 1 | **E&O ampliado** | R$ 5M-10M | R$ 3M; recall farma R$ 3M | R$ 25k | consequential regulatory damages (SEFAZ/Receita/INMETRO/CGCRE/ANPD); software validation defect; wrongful billing; long-tail custody 25y; vicarious tenant on-site; right to defend | Atos dolosos pessoais comprovados (definição estrita); guerra; nuclear | Erro de cálculo IA (ADR-0019) em certificado farma → recall; bug fiscal → multa SEFAZ; vistoria errada → ação cliente final | Recall medicamento R$ 8M + defesa R$ 1M |
| 2 | **Cyber** | **R$ 5M** + `aggregate reinstatement` 1x/ano | R$ 2M | R$ 15k | third-party credential abuse; confidential business info clients; dependent BI tenant rework; time-source integrity defect; multi-claim aggregate E&O+Cyber ≥ R$ 10M | Atos dolosos do segurado (estrita); guerra cibernética estatal nomeada | Vazamento PII 50 tenants × LGPD multa até 2% faturamento tenant + notificação ANPD 72h + class action | Vazamento massivo: R$ 4M (multa) + R$ 1M (notificação/forense) |
| 3 | **D&O** | R$ 1M | R$ 500k | R$ 10k | personal liability technical decisions; investigation costs (CGCRE/ANPD) | Fraude pessoal comprovada | Roldão PF processado por decisão técnica (sem RT vendor até V2) | Sindicância CGCRE + civil R$ 800k |
| 4 | **BPT** (EMERGENCIAL) | R$ 500k-2M | R$ 1M | **R$ 10-15k FIXO** (não 2%) | named insured by date of loss; multi-activity single custody; cobertura mundial BR | Desgaste natural; uso impróprio documentado | CC art. 627 depositário — Balanças Solution recebe instrumentos hoje | Incêndio lab destrói 5 padrões premium R$ 1,5M |
| 5 | **Extensão veicular UMC** | R$ 50k-200k/veículo | — | R$ 5k | equipamento precisão em trânsito; compatível apólice veicular tenant | Direção sob efeito; veículo não autorizado | Padrão massa F1 + UMC instrumentação em campo | Colisão + perda padrão R$ 80k |
| 6 | **Dependent Service BI** (NOVA) | **R$ 1M agregado anual** | R$ 500k | janela espera 4h | CBI named vendors (AWS KMS, B2, PlugNotas, Lacuna, Hostinger, Anthropic, Grafana, Axiom); cyber-triggered CBI; reputational harm downstream | Outage planejado anunciado >72h; força maior nuclear/guerra | AWS KMS sa-east-1 cai 12h → 100% tenants param → SLA refund + churn | AWS down 24h: R$ 600k (refund SLA + churn 30%) |
| 7 | **Accreditation Loss Extension** (NOVA) | **R$ 2M agregado** | R$ 500k | R$ 25k | accreditation suspension direct loss + reaccreditation cost; customer churn following accreditation | Não-conformidade do tenant independente do Aferê | Aferê fora 48h durante janela CGCRE → tenant perde escopo RBC | Tenant RBC perde escopo: R$ 400k (consultoria) + R$ 200k (churn) |

## Cláusulas universais (todas modalidades)

- Cobertura retroativa (atos pré-apólice / claims pós)
- Right to defend ampliado
- Multi-claim aggregate anual (não por evento isolado)
- Cobertura mundial BR
- Inclusão explícita de multas regulatórias LGPD/INMETRO/CGCRE/ANPD
- **REJEITAR:** exclusão genérica "atos dolosos"; exclusão "depositário"; exclusão "código IA"; franquia > 5% capital/evento (exceto BPT fixo)

## Soma estimada de prêmio anual

**R$ 60k-120k/ano consolidado** — corretora ajusta após cotação real.

## Próximos passos

1. Corretora SUSEP recebe esta planilha + briefing (`briefing-corretora-susep.md`) + ADR-0028 + ADR-0019.
2. Corretora pede 3 propostas (Marsh / AON Tech / Howden).
3. Comparativo via tabela de mesmas colunas.
4. Decisão Roldão.
5. Emissão antes do 1º tenant externo pago (exceção BPT-1 IMEDIATO).
