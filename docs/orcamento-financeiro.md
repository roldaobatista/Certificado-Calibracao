---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
relacionados:
  - docs/adr/0001-stack.md
  - docs/adr/0011-banco-analitico-bi.md
  - docs/orcamento-contexto.md
---

# Orçamento financeiro — projeção ano 1 / 3 / 5

> **Pra quê:** mostrar o custo real esperado de infra + LLM + ferramentas externas conforme o sistema cresce de 1 tenant (dogfooding Balanças Solution) → 5.000 tenants (TAM real BR de calibração + assistência técnica). A ADR-0001 estimou R$ 1.500/mês ano 1, mas isso foi calculado pra **19 módulos**. A auditoria de 10 agentes pós-48-módulos refez a conta e o custo real é diferente.
> **Status:** v1 — projeção revisada pós-auditoria 10 agentes (2026-05-17 madrugada). Substitui a estimativa otimista da ADR-0001 v2.
> **Não confunda com:** `docs/orcamento-contexto.md` (esse é sobre **janela de tokens** do LLM, não dinheiro).

---

## Resumo executivo

| Período | Custo mensal estimado | Custo anual | Driver principal |
|---|---|---|---|
| **Ano 1 (1-15 tenants, dogfooding + early customers)** | **R$ 700-2.500/mês** | **R$ 8k-30k** | LLM + observabilidade subindo conforme módulos entram |
| **Ano 2 (15-50 tenants)** | **R$ 2.000-4.500/mês** | **R$ 24k-54k** | Upgrade KVM 4 → KVM 8 + read-replica BI |
| **Ano 3 (50-200 tenants)** | **R$ 4.500-8.000/mês** | **R$ 54k-96k** | Migração cloud (AWS sa-east-1) + observabilidade escalada |
| **Ano 5 (200-2.000 tenants)** | **R$ 15.000-40.000/mês** | **R$ 180k-480k** | Multi-VPS sharded + Postgres gerenciado + KMS + LLM |

**Custo por tenant ano 5:** ~R$ 7-20/tenant/mês. Receita estimada por tenant (B segmento médio) ~R$ 800-1.200/mês. Margem bruta saudável.

**Discrepância pós-auditoria:** a estimativa original (ADR-0001 §Contexto) era R$ 1.500/mês ano 1. A realidade ano 1 vai de R$ 700 (mês 1-3, dogfooding) até R$ 2.500 (mês 10-12 com Wave B começando). O Auditor 8 da auditoria pós-48-módulos apontou que o **LLM é o vilão** — passou de R$ 800/mês estimado pra ~R$ 2.200/mês real com 48 módulos sendo construídos por agentes IA.

---

## Glossário rápido (pra Roldão)

| Termo | O que é, na prática |
|---|---|
| **VPS** | "Servidor virtual" — máquina alugada na nuvem. Hostinger KVM 4 = 4 CPUs, 16 GB RAM, 200 GB de disco. |
| **KMS** | "Key Management Service" — serviço que guarda chaves de criptografia em hardware especial (HSM). |
| **WORM** | "Write Once Read Many" — arquivo que depois de gravado não pode ser editado nem apagado. Exigência regulatória pra auditoria de 25 anos. |
| **Egress** | "Saída de dados" — quanto você paga por GB que cliente baixa do servidor. |
| **CDN** | "Content Delivery Network" — Cloudflare, R2 etc — cache global pra acelerar download. |
| **Observabilidade** | Logs + métricas + traces — sistema que mostra o que está acontecendo no servidor. |
| **Read-replica** | "Cópia somente-leitura" do banco principal. Relatório pesado roda na cópia sem travar o sistema operacional. |
| **DR** | "Disaster Recovery" — plano de recuperação se servidor primário pegar fogo. |
| **DPA** | "Data Processing Agreement" — contrato LGPD obrigatório com cada fornecedor terceiro. |

---

## Detalhamento por categoria

### 1. Hospedagem (servidor onde o sistema roda)

| Período | Configuração | Custo/mês |
|---|---|---|
| Mês 1-3 | Hostinger KVM 4 (4 vCPU / 16 GB / 200 GB NVMe — SP) | R$ 400 |
| Mês 4-12 | Hostinger KVM 8 (8 vCPU / 32 GB / 400 GB NVMe — SP) | R$ 850 |
| Ano 2 | KVM 8 + KVM 4 dedicada pra BI/read-replica (ADR-0011 Fase 1) | R$ 1.250 |
| Ano 3 | Migração AWS sa-east-1 (EC2 t3.xlarge + RDS PostgreSQL + S3) | R$ 2.500-4.000 |
| Ano 5 | Multi-region AWS sa-east-1 + us-east-1 (EC2 + RDS Multi-AZ + ALB) | R$ 8.000-15.000 |

**Gate Mês 4 (KVM 4 → KVM 8):** RAM > 75% por 24h contínuo OU disco > 70% OU latência p99 subindo > 50% sem release nova.

**Gate Mês 10-12 (Hostinger → AWS):** 1º cliente externo pagante chegar OU Hostinger SLA não cobrir mais (sem multi-AZ).

### 2. Cota LLM (Claude + GPT pra agentes IA escreverem código)

Esta é a categoria que mais cresceu vs estimativa original. A ADR-0001 estimou R$ 800/mês. A auditoria pós-48-módulos refez a conta.

| Período | Atividade dominante | Custo/mês estimado |
|---|---|---|
| Mês 1-3 | Foundation F-A..F-H (multi-tenant, auth, hooks, CI) | R$ 500-800 |
| Mês 4-8 | Wave A construção (18 módulos × ~9 user stories cada) | R$ 1.500-2.500 |
| Mês 9-12 | Wave A polimento + dogfooding + correções | R$ 1.500-2.200 |
| Ano 2 | Wave B (27 módulos novos) + manutenção Wave A | R$ 2.500-4.000 |
| Ano 3 | Wave B fim + Wave C planejamento + manutenção | R$ 3.000-5.000 |
| Ano 5 | Manutenção + novos módulos V3 + multi-país | R$ 5.000-10.000 |

**Mitigações ativas (ADR-0001 v2 — Auditor 8):**
- Cota agregada hard cap R$ 2.500/mês ano 1 (configurada no LiteLLM)
- Gatilho Mês 6: se tokens > R$ 1.500/mês, migrar tarefas baixa complexidade pra Haiku/Sabiá (custo ~10x menor)
- Cache de prompts (Anthropic prompt caching) — reduz 50-70% custo em prompts repetidos
- IRRF 15% + IOF 3,5% sobre remessas exterior **já orçados** (Anthropic, OpenAI)

### 3. Storage WORM + KMS + backup

| Item | Mês 1-3 | Mês 4-12 | Ano 2 | Ano 5 |
|---|---|---|---|---|
| **Backblaze B2** (PDFs + audit + logs longos — WORM) | R$ 30 | R$ 50 | R$ 150 | R$ 600 |
| **AWS KMS Multi-Region** (sa-east-1 + us-east-1 MRK) | R$ 50 | R$ 60 | R$ 150 | R$ 500 |
| **Backup pgBackRest → B2** (PITR contínuo) | R$ 10 | R$ 30 | R$ 100 | R$ 400 |
| **Subtotal storage/cripto/backup** | **R$ 90** | **R$ 140** | **R$ 400** | **R$ 1.500** |

### 4. Observabilidade (logs, métricas, traces, alertas)

| Item | Mês 1-3 | Mês 4-12 | Ano 2 | Ano 5 |
|---|---|---|---|---|
| **Grafana Cloud** (free tier inicial → paid) | R$ 0 | R$ 100 | R$ 300 | R$ 800 |
| **Axiom logs** (free 500GB → paid) | R$ 0 | R$ 80 | R$ 250 | R$ 700 |
| **Sentry erros** (free 5k → Team) | R$ 0 | R$ 150 | R$ 200 | R$ 400 |
| **PagerDuty/Opsgenie** (oncall — só V2+) | R$ 0 | R$ 0 | R$ 150 | R$ 400 |
| **Subtotal observabilidade** | **R$ 0** | **R$ 330** | **R$ 900** | **R$ 2.300** |

### 5. Fiscal + ferramentas externas

| Item | Mês 1-3 | Mês 4-12 | Ano 2 | Ano 5 |
|---|---|---|---|---|
| **PlugNotas NFS-e** (~R$ 0,10 por nota) | R$ 0 | R$ 50 | R$ 300 | R$ 2.000 |
| **Resend email** (free 3k → Pro) | R$ 0 | R$ 50 | R$ 150 | R$ 500 |
| **Cloudflare CDN** (free → R2 quando egress crescer) | R$ 0 | R$ 0 | R$ 100 | R$ 400 |
| **Certificado A1 ICP-Brasil** (R$ 300/ano por cert) | R$ 25 | R$ 25 | R$ 50 | R$ 150 |
| **WhatsApp BSP** (Z-API ou Meta direto — por mensagem) | R$ 0 | R$ 100 | R$ 400 | R$ 1.500 |
| **Subtotal fiscal/ferramentas** | **R$ 25** | **R$ 225** | **R$ 1.000** | **R$ 4.550** |

### 6. Compliance + seguros + DPO (todos diferidos pra V2 — quando 1º cliente externo aparece)

| Item | Diferido até | Custo/mês quando ativar |
|---|---|---|
| **Apólice cyber + RC profissional** | 1º cliente externo pagante (V2) | R$ 800-1.500/mês |
| **DPO formal designado** | 1º cliente externo (V2) | R$ 1.500-3.000/mês (parcial) |
| **DPA-modelo + consultoria jurídica** | 1º cliente externo (V2) | R$ 500/mês recorrente |
| **Pentesting anual** | Wave B (pós-MVP-1 estável) | R$ 15-25k/ano (1x por ano) |
| **Auditoria externa Cgcre RBC** | Quando tenant pedir acreditação (V3+) | R$ 8-15k/ano por tenant |

**Decisão Roldão (2026-05-17):** todos esses itens **diferidos pra V2** quando 1º cliente externo pago aparecer (memória `sem-cliente-externo-na-janela-atual`). MVP-1 sai dogfooding-only, sem essas obrigações.

---

## Totais consolidados

### Ano 1 (1-15 tenants — dogfooding Balanças Solution)

| Mês | Hospedagem | LLM | Storage/KMS | Obs | Fiscal/ferr | **Total/mês** |
|---|---|---|---|---|---|---|
| Mês 1-3 (KVM 4) | R$ 400 | R$ 650 | R$ 90 | R$ 0 | R$ 25 | **~R$ 1.165** |
| Mês 4-8 (KVM 8 + Wave A) | R$ 850 | R$ 2.000 | R$ 140 | R$ 330 | R$ 225 | **~R$ 3.545** |
| Mês 9-12 (Wave A polimento) | R$ 850 | R$ 1.800 | R$ 140 | R$ 330 | R$ 225 | **~R$ 3.345** |

**Ano 1 total: ~R$ 33-36k** (média ~R$ 2.700-3.000/mês). Vs estimativa original R$ 18k/ano (R$ 1.500/mês) — **estourou em ~85%**.

**Onde está o estouro:** LLM (~R$ 22k vs R$ 9.6k estimado original) + observabilidade (~R$ 3k vs R$ 0 free tier original).

### Ano 3 (50-200 tenants — primeiros clientes externos pagos)

| Categoria | Custo/mês |
|---|---|
| Hospedagem (cloud AWS sa-east-1) | R$ 3.500 |
| LLM (codebase 100k+ LOC) | R$ 4.000 |
| Storage/KMS/backup | R$ 400 |
| Observabilidade | R$ 900 |
| Fiscal/ferramentas | R$ 1.000 |
| Compliance + seguros (V2 ativo) | R$ 2.500 |
| **Total ano 3** | **~R$ 12.300/mês = ~R$ 148k/ano** |

### Ano 5 (200-2.000 tenants — TAM crescendo)

| Categoria | Custo/mês |
|---|---|
| Hospedagem (multi-region AWS) | R$ 12.000 |
| LLM (manutenção + novos módulos V3) | R$ 8.000 |
| Storage/KMS/backup | R$ 1.500 |
| Observabilidade | R$ 2.300 |
| Fiscal/ferramentas | R$ 4.550 |
| Compliance + seguros + pentesting + DPO | R$ 4.500 |
| **Total ano 5** | **~R$ 32.850/mês = ~R$ 394k/ano** |

**Custo por tenant ano 5 (assumindo 1.000 tenants pagos):** R$ 33/tenant/mês de infra. Margem confortável vs ~R$ 800-1.200/mês de receita por tenant.

---

## Gatilhos de revisão deste orçamento

| Sinal | Ação |
|---|---|
| LLM > R$ 1.500/mês em mês isolado | Investigar overrun; ativar migração pra Haiku/Sabiá em tarefas baixa complexidade |
| LLM > R$ 2.500/mês em mês isolado | Hard cap dispara (LiteLLM bloqueia); revisar prompt caching + revisões manuais |
| Hostinger RAM > 75% por 48h | Migrar pra KVM 8 (ou KVM 16 se mês > 8) |
| Hostinger SLA quebrar > 4h | Acelerar migração pra cloud (DR provedor B pré-configurado) |
| 1º cliente externo pagante chega | Ativar todos os itens compliance V2 (apólice, DPO, DPA) |
| Custo total > R$ 5k/mês ano 1 | Revisar este doc + ADR-0001 critério de reversão |

---

## Comparativo com estimativa original (ADR-0001 v2)

| Item | ADR-0001 v2 estimou | Realidade pós-auditoria | Diferença |
|---|---|---|---|
| Infra (hospedagem) | R$ 400/mês | R$ 600-850/mês ano 1 | +50-110% |
| LLM | R$ 800/mês | R$ 1.500-2.500/mês ano 1 | +90-215% |
| Storage + KMS + backup | R$ 90/mês | R$ 90-140/mês | OK |
| Observabilidade | R$ 75/mês (free + paid) | R$ 0-330/mês | OK no início |
| **Total ano 1** | **R$ 1.500/mês** | **R$ 1.165-3.545/mês** | Estouro de até 130% no pico |

**Conclusão:** estimativa original era otimista. Realidade ano 1 é R$ 25-40k/ano, não R$ 18k. **Roldão aceitou conscientemente** (auditoria às cegas confirmou que stack está certa — o que mudou é o tamanho do escopo, de 19 pra 48 módulos).

---

## Comparativo — quanto NÃO vamos pagar (decisões da auditoria)

| Ferramenta avaliada e REJEITADA | Custo evitado | Por que rejeitada |
|---|---|---|
| **Snowflake / BigQuery** (data warehouse) | R$ 800-1.500/mês fixo | ADR-0011: PG único Fase 0 + DuckDB Fase 2 cobre |
| **Auth0 / Clerk / WorkOS** (auth como serviço) | R$ 0,99-2,99/usuário/mês × 5k = ~R$ 5-15k/mês | ADR-0012: Django built-in + RLS é suficiente |
| **Casbin / OPA daemon** (policy engine externo) | ~R$ 200-500/mês operação | ADR-0012: Django + RLS cobre, decisão na porta `AuthorizationProvider` |
| **Keycloak self-hosted** (SSO enterprise) | R$ 300-500/mês operação | django-allauth + django-otp cobre Wave A |
| **Temporal Cloud** (workflow engine) | R$ 1-5k/mês | ADR-0005: procrastinate + DSL caseira pro MVP-1 |
| **Metabase Cloud** (BI) | R$ 400/mês por instância | ADR-0011: Superset open source embedded |
| **Datadog** (observabilidade tudo-em-um) | R$ 2-5k/mês | Grafana Cloud + Axiom + Sentry separados, cada um em free/cheap tier |
| **CircleCI / GitLab pago** (CI/CD) | R$ 200-500/mês | GitHub Actions free tier + SSH deploy |
| **TypeScript fullstack** (1ª versão da ADR-0001) | 6-12 meses de admin construído | Django Admin grátis |

**Economia total estimada ano 1 vs "se tivesse seguido o caminho convencional":** ~R$ 100-200k.

---

## Itens a fazer

- [ ] Adicionar este doc no `INDEX.yaml` como `carrega_quando: sob-demanda`
- [ ] Citar este doc em `painel-do-dono.md` (Roldão consulta mensal)
- [ ] Hook `auditor-financeiro` mensal — compara custo real (faturas Hostinger/B2/AWS/Anthropic) vs projeção; alerta se desviar >20%
- [ ] Atualizar este doc trimestralmente com custo real consolidado
- [ ] Atualizar `painel-do-dono.md` com gráfico de "custo mensal real × projeção"

---

## Referências

- ADR-0001 v2 — Stack (estimativa original)
- ADR-0011 — BI 3 fases (impacto em hospedagem ano 1-3)
- Auditoria 10 agentes pós-48-módulos 17/05/2026 — Auditor 9 (custo VPS) + Auditor 8 (cota LLM)
- Auditoria às cegas 17/05/2026 — Auditor G (DevOps/SRE/infra) confirmou números
- `docs/orcamento-contexto.md` (sobre tokens de contexto LLM — **diferente** deste arquivo)
