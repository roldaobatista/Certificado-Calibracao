---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Faseamento dos módulos em produção

> **Pra quê:** ordem em que os N módulos entram em produção. Saída do `discovery/sintese-final.md` (DRAFT v3) + `opportunity-solution-tree.md`. Sem isso, ADRs específicas de módulo (0008 fiscal, 0009 A3 calibração) ficam sem âncora de "quando vamos precisar disso de verdade".
>
> **Critério de ordenação:** dor regulatória com prazo > dor recorrente alta > diferencial competitivo > dependência técnica > débito conhecido.

---

## Visão geral

| Fase | Duração estimada | Conteúdo | Status |
|------|------------------|----------|--------|
| **Foundation** | 0-6 semanas (F-A) + paralelo | Multi-tenant + Auth + Cadastros + Mobile shell + Hooks + CI + Fechar ADR-0001 (sem spike descartável) | ⏳ não-iniciado |
| **Wave A — MVP-1** | 6-14 semanas | NFS-e + Certificado + Metrologia Legal + OS/App/Caixa + Financeiro mínimo | ⏳ depende Foundation |
| **Wave B — pós-MVP-1** | 14-22 semanas | Recalibração proativa + Comissões expandidas + Portal cliente + Cobrança + Painel dono | ⏳ depende Wave A em produção |
| **Wave C — escala** | 22+ semanas | Frota TCO completo + Trilha D→A + Manutenção preditiva + Multi-país | ⏳ depende Wave B validada |

**Total até 1º deploy MVP-1 viável:** 14 semanas estimadas; **margem realista 16-22 semanas** (4-5,5 meses) — alinhado com 3ª auditoria que apontou cronograma realista 5-7 meses.

---

## Foundation (semanas 0-6, pré-MVP)

Bloqueia Wave A inteira. Sem isso não há plataforma onde rodar módulo nenhum.

> **Sem spike descartável** (2026-05-17 — ver [[nao-construir-codigo-descartavel]]). Critérios de validação da ADR-0001 Portão 3 aplicados às primeiras 4-6 semanas de F-A real, não a experimento artificial. Se reprovar, dispara plano B (tech-lead consultivo); código fica.

| ID | Item | Origem | Bloqueia |
|----|------|--------|----------|
| **F-A** | Multi-tenant + RLS + audit trail (**+ critérios da ADR-0001 Portão 3 nas primeiras 4-6 semanas**) | ADR-0002 + ADR-0001 Portão 3 | tudo |
| **F-B** | Auth + RBAC + cadastros (usuário, papéis, permissões) | ADR-0001 | F-C, OS, NFS-e |
| **F-G** | Hooks + auditores Família 5 + CI completos | governança | qualquer commit em código sensível |
| **F-C** | Cliente master (BIG-07 — cadastro único) | discovery BIG-07 | OS, certificado, NFS-e, recalibração |
| **F-D** | Mobile shell offline-first (Flutter + drift) | ADR-0003 (stub) | OP3 app campo — pode rodar paralelo a F-E |
| **F-E** | WhatsApp BSP integrado | LEAP F-5 | recalibração proativa (Wave B) |
| **F-H** | ADR-0001 stack vira definitiva (Portões 2+3; Portão 1 diferido V2) | ADR-0001 | confirmação retroativa |

---

## Wave A — MVP-1 (semanas 6-14, núcleo regulatório)

**Tese:** capturar mercado em onda de pressão regulatória forçada (NFS-e cutover 01/09/2026 + janela ENIQ).

| ID | Item | Big Job | Dor priorizada | Bloqueia | Veta merge se |
|----|------|---------|----------------|----------|---------------|
| **OP7** | **Emissor NFS-e** via BaaS pluggable (PlugNotas 1ª impl) | BIG-04 | Dor #10 (cutover 09/2026) | nada (módulo independente) | Auditor de Produto: AC "emite NFS-e em SP+RS+MG+SC sem erro fatal" falhar |
| **OP2** | **Certificado de calibração completo** (ISO 17025 cláusula 7.8) | BIG-02 | Dor #04 (Excel/Word cálculo) | recalibração proativa | INV-002 violado (certificado sem cadeia rastreável) |
| **OP10** | **Metrologia Legal** (selo INMETRO rastreável) | BIG-06 | Dor #08 (técnico campo) | OP3 app campo | INV-002 / INV-009 (rastreabilidade) |
| **OP3.1** | **App de campo** (mobile shell + check-in/check-out OS) | BIG-05 | Dor #05 ("cadê OS?") | OP3.2 caixa | Mobile não funciona offline em rede 3G |
| **OP3.2** | **Caixa do técnico** (avulsos: combustível, refeição, peça menor) | BIG-08 (parcial) | Dor recorrente | Wave B frota TCO | Não fecha em conferência |
| **OP-FIN** | **Módulo Financeiro mínimo** (contas a receber + conciliação + boleto/PIX) | BIG-04 (parcial) | Dor #11 | OP11 cobrança Wave B | NFS-e não bate com contas a receber |

**Critério de "MVP-1 entregue"** (atualizado 2026-05-17 — sem cliente externo na janela atual):
- ✅ Os 6 itens acima rodando em produção real na **Balanças Solution** (dogfooding profundo, não simulação)
- ✅ NFS-e emitida sem erro fatal em ≥ 95% das tentativas
- ✅ Certificado de calibração sem retrabalho em ≥ 90% dos casos
- ✅ ≥ 3 meses contínuos de operação real com NFS-e, OS, certificado emitidos
- ✅ Zero SEV-0; ≤ 2 SEV-1 no período
- ✅ Auditor de Segurança não bloqueou nenhum merge nos últimos 30 dias

**Diferido pra V2:** "3 tenants externos pagantes" — entra como gate da Wave C ou quando 1º cliente externo aparecer. Ver memória [[sem-cliente-externo-na-janela-atual]].

**Frota TCO completo move pra MVP-2** — Wave A leva só caixa do técnico.

---

## Wave B — pós-MVP-1 (semanas 14-22, valor comercial)

Só inicia depois que MVP-1 está em produção com ≥ 3 tenants pagantes.

| ID | Item | Big Job | Depende de |
|----|------|---------|------------|
| **OP1** | **Recalibração proativa** (lembrete via WhatsApp + dashboard) | BIG-10 + BIG-11 | OP2 + F-C + F-E |
| **OP4** | **Comissões SIMPLIFICADA** (1 fórmula no MVP-1; 7 outras espalhadas em MVP-2/MVP-3) | BIG-09 | OP-FIN |
| **OP5.1** | **Timeline 360° do cliente** (histórico unificado) | BIG-07 | OP2 + OP3 |
| **OP8.2** | **Link curto WhatsApp** ("ver minha OS") | BIG-07 | OP3 + OP5.1 |
| **OP9** | **Trilha D→A** (módulo de preparação pra acreditação RBC) | BIG-03 | OP2 |
| **OP11** | **Cobrança e inadimplência** | BIG-04 | OP-FIN + OP1 |
| **OP12** | **Painel do Dono** (Roldão + outros donos vendo seu próprio tenant) | suporte | tudo Wave A |

---

## Wave C — escala (semanas 22+, expansão)

Lista provisória — depende fortemente de feedback dos primeiros tenants.

- **Frota TCO completo** (BIG-08 expandido)
- **Trilha D→A com módulos de auditoria** interna (BIG-03 expandido)
- **Manutenção preditiva** (Dor #31 nova — pode virar BIG-13)
- **MSA / Gage R&R** (Dor #32 nova — add-on enterprise)
- **Multi-país** (mercados ICP em LatAm)
- **Cliente farma TOP** (depende de contratar RT vendor + DPO + 21 CFR Part 11)

Reavaliar síntese após 1º deploy do MVP-1.

---

## Dependências entre módulos (resumo gráfico)

```
F-A multi-tenant ──┬─→ F-B auth ──→ F-C cliente master ──┬─→ OP2 certificado ──┐
                   │                                     │                    │
                   │                                     ├─→ OP3 app/caixa    │
                   │                                     │                    ├─→ Wave A entregue
                   │                                     ├─→ OP7 NFS-e        │
                   │                                     │                    │
                   │                                     └─→ OP10 metrologia──┘
                   │
F-D mobile shell ──┴─→ OP3.1 app de campo
F-E WhatsApp BSP ────→ OP1 recalibração proativa (Wave B)
F-G hooks + CI ──────→ qualquer commit em código
F-H ADR-0001 final ──→ confirma stack após Foundation rodar
```

---

## Critérios de "pode começar Wave seguinte"

| Wave | Critério (atualizado 2026-05-17 sem cliente externo) |
|------|---------|
| **Foundation** | ADR-0001 sai de "candidata" → "definitiva" via Portões 2+3 (Portão 1 diferido pra V2) |
| **Wave A (MVP-1)** | Foundation completa + critérios da ADR-0001 Portão 3 aprovados em F-A + Balanças Solution pronta pra dogfooding |
| **Wave B (pós-MVP)** | Wave A rodando em Balanças Solution por ≥ 3 meses sem SEV-0 |
| **Wave C (escala)** | Wave B validada + decisão consciente de Roldão "agora quero buscar cliente externo" → ativar Portão 1 + apólice + DPO + DPA |

---

## Critérios de mortalidade (kill switches)

A qualquer momento, se um dos abaixo disparar, o módulo/wave para e abre revisão:

- **F-A (Foundation primeira peça) falha nos critérios:** > 2 intervenções de código/semana do Roldão, > 3 bugs SEV-1, ou estouro de token cap R$ 1.500 nas primeiras 4-6 semanas → dispara plano B (tech-lead consultivo R$ 8-15k/mês). **NÃO reverte stack pra TS. NÃO joga código fora.** F-A continua, só muda quem programa.
- **OP7 NFS-e não emite em 09/2026:** abre crise + replan; provavelmente atrasa Wave A 4-6 semanas
- **Tenant vaza dado de outro tenant:** drop Wave atual, abre RACI-incidente-ai, postmortem obrigatório
- **Auditor de Segurança bloqueia mais de 30% dos commits:** revisar regras (falsos positivos) ou refactor (regras corretas)
- **Churn 90 dias > 30%:** abre LEAP F-18 (CS L1) como prioridade emergencial

---

## Histórico

| Data | Mudança |
|------|---------|
| 2026-05-17 | Criação consolidando síntese-final discovery v3 + opportunity-solution-tree + ADRs já cravadas. Wave A explicitada como MVP-1. Frota TCO completo movido pra Wave C. |
