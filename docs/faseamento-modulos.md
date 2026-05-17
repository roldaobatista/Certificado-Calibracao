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

## Atualização v8 (2026-05-17 noite +12h): 48 módulos + cadeia bloqueadora resolvida

> Esta seção é **aditiva**. O conteúdo histórico abaixo (v6/v7 com 19 módulos) **permanece como está** pra rastreabilidade. Esta é a tabela em vigor.

### Por que mudou
1. **48 módulos** agora (era 19 na v7) — 25 novos mapeados pelo inventário paralelo de 10 agentes Explore confrontando `docs/novas funcionalidades.txt` × v7 (ver `documentos-do-projeto.md` v8, linhas ~482-571).
2. **Decisão Roldão (2026-05-17 noite):** subir 4 módulos antes catalogados como Wave B pra **Wave A**, resolvendo a cadeia bloqueadora regulatória do MVP-1.

### Decisão Roldão — cadeia bloqueadora resolvida

> **Texto cravado:** "Subir Licenças-Acreditações + Treinamentos + Segurança do Trabalho + Estoque pra Wave A (junto com OS, Certificados, App-Técnico, Calibração). Não dá pra emitir certificado sem RT acreditado (Licenças) + técnico treinado (ISO 17025 6.2 = Treinamentos), nem rodar OS em campo sem checklist segurança (SST) e sem peças (Estoque). MVP-1 sai completo, sem brecha regulatória. Cronograma realista: 8-12 semanas em vez de 4-6."

**O que destrava cada movimento:**

| Módulo movido pra Wave A | Cadeia que destrava | Sem isso, qual MVP-1 quebra? |
|---|---|---|
| `metrologia/licencas-acreditacoes` | RT (Responsável Técnico) acreditado no escopo é pré-requisito de **toda** emissão de certificado ISO 17025 | Certificado emitido fora do escopo acreditado = não-conformidade regulatória → MVP-1 inválido |
| `rh-frota-qualidade/treinamentos` | ISO 17025 cláusula 6.2 exige matriz de competência por colaborador que executa calibração | Auditor RBC reprova MVP-1 na 1ª visita |
| `rh-frota-qualidade/seguranca-trabalho` | OS em campo (NR-12 balança industrial, NR-10 elétrica, NR-35 altura) exige checklist SST | Acidente em campo sem registro de checklist = passivo trabalhista imediato |
| `suporte-plataforma/estoque` | OS de manutenção/calibração consome peças (pesos-padrão substitutos, fusíveis, células de carga) | Técnico em campo sem peça = OS reaberta = retrabalho = quebra promessa de "1 visita resolve" |

### Tabela consolidada de waves (48 módulos)

> **Legenda:** ✅ na wave; ⏩ promovido nesta v8; 🆕 módulo novo da v8 (era inexistente na v7).

#### Foundation (semanas 0-6) — pré-MVP, não é módulo de produto

`F-A` multi-tenant + RLS + audit · `F-B` auth + RBAC · `F-C` cliente master · `F-D` mobile shell · `F-E` WhatsApp BSP · `F-G` hooks + CI · `F-H` ADR-0001 final.

#### Wave A — MVP-1 (semanas 6-18, núcleo regulatório completo)

**18 módulos.** Critério: tudo necessário pra Balanças Solution operar legalmente em dogfooding profundo, sem brecha regulatória, sem fingir que treinamento/licença/SST/estoque "vem depois".

| Domínio | Módulo | Status | Justificativa de Wave A |
|---|---|---|---|
| `operacao/` | `os` | ✅ | Núcleo da operação técnica |
| `operacao/` | `chamados` | ✅ | Entrada de demanda do cliente |
| `operacao/` | `agenda` | ✅ | Roteirização do técnico |
| `operacao/` | `app-tecnico` 🆕 | ✅ | App de campo offline-first (OP3.1 da v7) |
| `operacao/` | `base-conhecimento` 🆕 | ✅ | Embutida em OS/Chamados desde MVP-1 (sem KB, técnico repete erro) |
| `metrologia/` | `calibracao` | ✅ | OP2 da v7 — núcleo do diferencial |
| `metrologia/` | `certificados` 🆕 | ✅ | Ciclo de vida do certificado separado de `calibracao/` |
| `metrologia/` | `licencas-acreditacoes` 🆕 ⏩ | ✅ | **Promovido (era Wave B):** RT acreditado é pré-requisito de toda emissão |
| `rh-frota-qualidade/` | `treinamentos` 🆕 ⏩ | ✅ | **Promovido (era Wave B):** ISO 17025 6.2 exige matriz de competência |
| `rh-frota-qualidade/` | `seguranca-trabalho` 🆕 ⏩ | ✅ | **Promovido (era Wave B):** OS em campo exige checklist SST |
| `suporte-plataforma/` | `estoque` ⏩ | ✅ | **Promovido (era Wave B implícita):** OS sem peça = retrabalho |
| `suporte-plataforma/` | `equipamentos` | ✅ | Cadastro do parque do cliente (pré-OS) |
| `suporte-plataforma/` | `acesso-seguranca` 🆕 | ✅ | RBAC avançado, MFA, audit log (pré-requisito de qualquer externo) |
| `comercial/` | `clientes` | ✅ | F-C da Foundation já cobre cadastro; módulo expande |
| `comercial/` | `orcamentos` | ✅ | Funil comercial mínimo |
| `financeiro/` | `fiscal` | ✅ | OP7 da v7 — NFS-e (cutover 09/2026) |
| `financeiro/` | `contas-receber` | ✅ | OP-FIN da v7 — mínimo viável |
| `financeiro/` | `caixa-tecnico` | ✅ | OP3.2 da v7 — avulsos do técnico |

#### Bloqueador externo (entre Wave A e 1º cliente externo pago)

| Domínio | Módulo | Quando |
|---|---|---|
| `financeiro/` | `billing-saas` 🆕 | Antes do 1º cliente externo pagar. Sem isso, não cobra. Não bloqueia dogfooding Balanças. |

#### Wave B — pós-MVP-1 (semanas 18-32+, valor comercial e cobertura)

**21 módulos.** Só inicia quando Wave A estiver rodando ≥ 3 meses na Balanças sem SEV-0.

| Domínio | Módulo | Status |
|---|---|---|
| `operacao/` | `garantia` 🆕 | Pós-OS, controle de garantia |
| `operacao/` | `projetos` 🆕 | Instalação, retrofit, mudança de planta |
| `operacao/` | `capacity-planning-operacional` 🆕 | Planejamento carga técnicos/laboratório |
| `comercial/` | `crm` | Funil pós-orçamento |
| `comercial/` | `contratos` | Renovação, vigência |
| `comercial/` | `portal-cliente` 🆕 | Cliente externo acompanha — pré-requisito 1º cliente externo |
| `comercial/` | `precificacao` 🆕 | Régua de preços, tabelas, descontos |
| `comercial/` | `sla-contratual` 🆕 | SLA por contrato/cliente |
| `comercial/` | `comunicacao-omnichannel` 🆕 | WhatsApp/e-mail/SMS unificados |
| `financeiro/` | `contas-pagar` | Fornecedores, recorrências |
| `financeiro/` | `comissoes` | OP4 da v7 — 1 fórmula simplificada |
| `financeiro/` | `custeio-real` 🆕 | Custeio por OS/certificado/contrato |
| `financeiro/` | `despesas` 🆕 | Reembolso, adiantamento |
| `financeiro/` | `relatorios-financeiros` 🆕 | DRE gerencial, fluxo de caixa |
| `suporte-plataforma/` | `produtos-pecas-servicos` | Catálogo (estoque já no MVP-1) |
| `suporte-plataforma/` | `fornecedores` | Cadastro auxiliar |
| `suporte-plataforma/` | `onboarding` 🆕 | Self-service de novo tenant |
| `suporte-plataforma/` | `configuracoes-sistema` 🆕 | Temas, idioma, fuso |
| `suporte-plataforma/` | `automacoes-bpm` 🆕 | Motor BPM/workflow (ADR-0005) |
| `suporte-plataforma/` | `engenharia-tecnica` 🆕 | Procedimentos, padrões internos |
| `suporte-plataforma/` | `gestao-documental` 🆕 | DMS interno (versões, retenção, WORM) |
| `suporte-plataforma/` | `suporte-saas` 🆕 | Suporte interno do Aferê pros tenants |
| `suporte-plataforma/` | `release-management` 🆕 | Changelog visível pro cliente |
| `rh-frota-qualidade/` | `colaboradores` | Cadastro RH base (treinamentos já no MVP-1) |
| `rh-frota-qualidade/` | `qualidade` | SGQ, NC, ação corretiva |
| `rh-frota-qualidade/` | `auditoria-externa` 🆕 | Suporte a auditoria RBC/ISO/cliente |
| `dados/` | `bi` 🆕 | Cubos, painéis gerenciais, exports |

#### Wave C — escala (32+ semanas)

**Sem módulos novos** — Wave C é expansão de capacidades dentro de módulos existentes (não cria módulo novo): Frota TCO completo, Trilha D→A com auditoria interna, manutenção preditiva, MSA / Gage R&R, multi-país, cliente farma TOP (21 CFR Part 11).

#### V2/V3 — adiados conscientemente

| Domínio | Módulo | Por quê adiado |
|---|---|---|
| `comercial/` | `marketplace` 🆕 | Aplicativos/extensões/parceiros — só faz sentido com base de tenants instalada |
| `rh-frota-qualidade/` | `frota` (TCO completo) | Wave A leva só caixa do técnico; TCO completo entra em V2/V3 |

### Conta final de módulos por wave (v8)

| Wave | Módulos | Contagem |
|---|---|---|
| **Wave A (MVP-1)** | 18 | 18 |
| **Bloqueador antes 1º cliente externo** | `billing-saas` | 1 |
| **Wave B (pós-MVP-1)** | 27 | 27 |
| **Wave C (escala)** | 0 módulos novos (só expansão) | 0 |
| **V2/V3** | `marketplace`, `frota` TCO | 2 |
| **TOTAL** | | **48** |

### Estimativa de esforço Wave A (realista)

**Premissa:** ~170 user stories agregadas nos 18 módulos da Wave A (média 9-10 US por módulo, sendo `os`, `calibracao` e `certificados` os mais densos com ~20 cada).

| Cenário | Velocidade | Duração estimada |
|---|---|---|
| **Fantasia (v7)** | 4-6 semanas | Sub-dimensionado — ignora 13 dos 18 módulos hoje na Wave A |
| **Realista (v8)** | 3-4 devs × 3-5 dias por US × ~170 US ÷ paralelismo razoável | **8-12 semanas** corridas |
| **Conservador (Roldão + 1 dev sênior + 2 agentes IA densos)** | considerando código gerado por agente IA, revisão humana, retrabalho | **12-16 semanas** |

**Adoção oficial:** **8-12 semanas pra Wave A** (substitui 6-14 da v7). Total até MVP-1 em dogfooding profundo Balanças = **Foundation 6 semanas + Wave A 8-12 semanas = 14-18 semanas** (3,5-4,5 meses). Ainda dentro da janela 5-7 meses da 3ª auditoria; folga é margem pra retrabalho regulatório (LGPD-RAT, ISO 17025).

### Dependências cruzadas re-validadas (após movimentação v8)

**Novas dependências detectadas que NÃO existiam na v7:**

1. **`calibracao` → `licencas-acreditacoes`:** emissão de certificado precisa validar online se o RT atual está dentro do escopo acreditado vigente (não vencido). Antes era assumido como "controle manual fora do sistema". Agora é hook de bloqueio.
2. **`calibracao` → `treinamentos`:** assinatura do técnico no certificado só vale se matriz de competência atual marca ele apto pro tipo de calibração executada. Hook de bloqueio.
3. **`os` → `seguranca-trabalho`:** abertura de OS de campo precisa retornar checklist SST aplicável (NR-10, NR-12, NR-35) conforme tipo de equipamento + ambiente. Sem checklist preenchido, OS não fecha.
4. **`os` → `estoque`:** OS reserva peças do estoque no check-in; baixa no check-out; devolve no cancelamento. Sem isso, OS fecha "no escuro" e técnico em campo descobre que não tem a peça.
5. **`acesso-seguranca` → todos:** RBAC/MFA já é Foundation parcial (F-B), mas o módulo `acesso-seguranca` expande pra MFA + audit log de acesso. Bloqueia qualquer feature que dependa de log de acesso (LGPD).

**Dependências antigas que continuam válidas** (v7 segue valendo): `F-C cliente master` → `OS/Certificado/NFS-e`, `F-D mobile shell` → `app-tecnico`, `F-E WhatsApp BSP` → `recalibração proativa` (Wave B).

**Dependências quebradas/inválidas:** nenhuma. Todos os movimentos pra Wave A foram **promoções** (módulo vira pré-requisito), nenhum foi rebaixamento.

### Critério atualizado de "MVP-1 entregue" (substitui v7)

- ✅ Os **18 módulos** da Wave A rodando em produção real na Balanças Solution (dogfooding profundo)
- ✅ NFS-e emitida sem erro fatal em ≥ 95% das tentativas
- ✅ Certificado emitido **com RT acreditado no escopo vigente** em 100% dos casos (hook bloqueia o resto)
- ✅ Técnico em campo NÃO fecha OS sem checklist SST aplicável preenchido
- ✅ ≥ 3 meses contínuos de operação real
- ✅ Zero SEV-0; ≤ 2 SEV-1 no período
- ✅ Auditor de Segurança não bloqueou nenhum merge nos últimos 30 dias
- ✅ Auditor de Qualidade simulou visita RBC e não encontrou não-conformidade maior

---

## Conteúdo histórico (v6/v7 — preservado pra rastreabilidade)

> Tudo abaixo é o faseamento original com 19 módulos. **Não está mais em vigor sozinho** — leia em conjunto com a seção v8 acima. Conservado porque IDs de OPs (`OP1`-`OP12`, `F-A`-`F-H`) ainda são referenciados em ADRs e PRDs.

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
| 2026-05-17 (noite +12h) | **v8 + decisão cadeia bloqueadora.** 48 módulos (era 19). Promoção pra Wave A: `licencas-acreditacoes`, `treinamentos`, `seguranca-trabalho`, `estoque`. Wave A passa a ter 18 módulos. Cronograma realista revisado pra 8-12 semanas (era 4-6 fantasia). Conteúdo histórico v6/v7 preservado abaixo da seção v8 pra rastreabilidade dos IDs OP1-OP12. |
