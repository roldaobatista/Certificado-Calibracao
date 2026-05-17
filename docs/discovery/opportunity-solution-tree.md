# Discovery — Opportunity Solution Tree (OST)

> **Artefato Rodada 0 / Batch 2** (Auditor 6 v2 — NOVO). Framework Teresa Torres (Continuous Discovery Habits). Hierarquia outcome → opportunities → solutions → experiments.
>
> **Versão pós-auditoria 12 agentes (17/05/2026 noite).** Re-sequenciamento em Foundation + Wave A + Wave B; 4 OPs novas (OP9 BIG-03, OP10 BIG-06, OP11 cobrança, OP12 painel do dono); Confidence agora dual-axis (dono × mercado); reconciliação de pricing com mix realista; IDs de risco canônicos (R-049..R-057).
>
> **Atualizado:** 2026-05-17 — primeira versão DENSA pós-batch 2 do discovery. Cruza `jobs-to-be-done.md` (12 Big Jobs + ~109 JTBDs), `dores-mapeadas.md` (20 dores ranqueadas), `assumption-map.md` (57 premissas, 12 LEAPs), `personas-detalhadas.md` (14 personas), `dominio-de-negocio.md` (4 decisões fundadoras de PRODUTO Roldão 17/05/2026) e `concorrentes.md` (9 gaps defensáveis).
>
> **Versão pré-entrevistas.** Nenhuma entrevista com cliente externo aconteceu ainda. Toda Opportunity está ancorada em evidência interna (jornada, JTBD, decisão fundadora de PRODUTO) + marcação `[INFERÊNCIA — validar em onda 1]` quando os números (Reach/Impact/WTP) são palpite forte mas não confirmado. **Solutions serão re-priorizadas após onda 1 de entrevistas.**

---

## Estrutura

```
DESIRED OUTCOME (1 North Star)
  ├─ FOUNDATION (pré-MVP, semanas 0-6) — pré-requisitos técnicos/operacionais
  ├─ MVP-1 Wave A (semanas 6-14) — núcleo regulatório / sobrevivência
  ├─ MVP-1 Wave B (semanas 14-22) — camada de valor comercial
  ├─ Opportunity (dor + Big Job + decisão fundadora ancorados)
  │   ├─ Solution A (direção, não feature)
  │   │   └─ Experiment (smoke test / fake-door / WTP / spike técnico)
  │   ├─ Solution B
  │   └─ Solution C
  └─ Opportunity ...
```

> **Solution ≠ Feature.** Solution é a direção ("recalibração lembrada de forma proativa"); Feature é a implementação ("WhatsApp template aprovado + cron diário + portal cliente"). Cada Solution propõe 1 experiment pra validar a premissa LEAP antes de comprometer recurso de construção.

---

## Outcome principal (North Star)

**Outcome:** **Em 12 meses após o GA do MVP-1, atingir 50 tenants pagantes com receita recorrente média ponderada ≥ R$ 905/mês e churn mensal ≤ 3% — provando que o produto reduz o custo do status quo (R$ 35-50k/mês por empresa, conforme `jornada-atual-sem-produto.md` §8) em pelo menos 40% medido em piloto.**

**Mix-alvo de tenants e pricing por perfil:**

| Perfil | % do mix-alvo | Preço/mês | Justificativa |
|---|---|---|---|
| **A** (estruturado, ≥ 30 colaboradores, RBC ou em transição) | **10%** | **R$ 2.500** | Frota + UMC + comissões + farma add-on; alto WTP |
| **B** (PME organizada, 10-30 colab, ISO 17025 estável) | **55%** | **R$ 900** | Core do ICP — V-2 confirmada [INFERÊNCIA — validar onda 1] |
| **C** (em transição D→C, busca ISO 17025) | **25%** | **R$  600** | Trilha didática + wizard de upgrade |
| **D** (autônomo / informal / 1-3 pessoas) | **10%** | **R$ 400** | Tier essencial; sem frota/comissões avançadas |

**Média ponderada:** 0,10×2500 + 0,55×900 + 0,25×600 + 0,10×400 = **R$ 1.085** [com folga sobre meta de R$ 905]

**Como medir (3 indicadores acoplados):**

1. **MRR ≥ R$ 45k** (50 tenants × R$ 905 médio ponderado) — coerente com pricing por perfil e CAC/LTV viável (V-4).
2. **Churn mensal ≤ 3%** — proxy de "produto resolve dor real" vs "vendi mas cliente não usou" (mitiga R-001 — founder is customer).
3. **NPS-piloto ≥ 50 + economia auto-reportada ≥ R$ 14k/mês por tenant** — 40% de R$ 35-50k é o piso pra discurso de ROI sustentar preço acima de R$ 700/mês.

**Premissas comerciais novas (auditoria 17/05):**

- **V-15 (NOVA):** CAC blended ≤ R$ 4.500 nos primeiros 50 tenants. Acima disso, LTV/CAC fica abaixo de 3.
- **Setup pago substitui "1 mês grátis":** perfis A/B pagam **setup R$ 1.500-3.000 + 14 dias trial pós-setup** (ancoragem de valor + cobre custo de onboarding). Perfis C/D mantêm **trial puro de 14 dias** pra reduzir fricção de entrada.

**Por que esse outcome:**

- **É outcome de negócio, não de produto** (não é "lançar feature X" nem "ter Y telas") — Teresa Torres cláusula 1.
- **Acoplado a dor mapeada quantificada:** Jornada §8 calcula custo do status quo entre R$ 35k e R$ 50k/mês; Dor #02 sozinha vale R$ 8-12k/mês de receita perdida. 40% de redução = pitch de ROI inquestionável.
- **TAM compatível:** se V-1 (≥ 5.000 empresas no ICP A/B/C) for confirmado, 50 tenants = 1% — alvo conservador e factível em 12 meses, mas exigente o bastante pra forçar product-market-fit real.
- **Materializa V-2 (WTP perfil B R$ 700-1.500/mês)** e V-4 (CAC < LTV/3) sem assumir o cenário otimista.
- **Coerente com F-1 (modelo 100% agentes em ≤ 24 meses):** 12 meses pós-GA é metade do prazo total — primeiro semestre é construção, segundo é tração comercial.

**Anti-North-Star (o que NÃO é outcome principal):**

- ❌ "Número de features entregues" — vaidade.
- ❌ "Cobertura dos 12 Big Jobs" — todos têm que entregar valor, mas cobertura ≠ adoção.
- ❌ "Validar todas as 57 premissas" — premissas são meio; o fim é receita recorrente sustentável.

---

## Foundation (pré-MVP, semanas 0-6) — pré-requisitos NÃO-NEGOCIÁVEIS

> **Por que existe esta camada:** auditoria 12 agentes (17/05) identificou que vários itens estavam diluídos dentro de OPs do MVP-1, mas são pré-requisitos técnicos/operacionais que precisam estar prontos ANTES do MVP-1 começar de fato. Sem Foundation, MVP-1 Wave A trava no dia 1.

### F-A — Multi-tenant + Row-Level Security (RLS) + audit trail imutável

- **LEAP:** F-2 (stack aguenta multi-tenant com RLS).
- **Por quê:** sem isolamento de tenant bem feito desde o dia 1, vazamento de dado entre clientes destrói o produto. Audit trail imutável é base pra cláusula 7.5 ISO 17025 + LGPD.
- **Effort:** G (3 semanas, decisão de arquitetura + implementação core).

### F-B — Auth + RBAC + cadastros base (pessoas, equipamentos, veículos, padrões)

- **Por quê:** todo o resto depende. Auth + papéis (dono, RT, signatário, técnico, atendente, financeiro) + entidades base (cliente, equipamento do cliente, padrão de calibração, veículo da frota, colaborador).
- **Effort:** G (2-3 semanas).

### F-C — Cliente master único (era OP5 Solution 5.3, promovido pra Foundation)

- **Por quê:** modelo de dados com cliente como entidade única é foundation, não feature. Sem isso, OP1/OP2/OP4/OP7 não funcionam (todas dependem da mesma entidade cliente). Importador 1-clique de Cali/Bling/CSV.
- **Premissas:** F-16 (migração ≤ 8h por cliente), V-12 (trial → pagante ≥ 30%).
- **Effort:** M (importador + dedup + entidade única — 2 semanas).
- **Experiment:** spike de migração com 3 empresas reais (Roldão + 2 piloto). Métrica: 3/3 onboarding ≤ 8h + 0 perda de dado fiscal.

### F-D — App mobile shell PWA+Capacitor

- **LEAP:** F-10 (mobile sem time mobile dedicado).
- **Por quê:** OP3 (técnico em campo), OP6 (selo INMETRO), OP8 Solution 8.2 (link WhatsApp) e OP12 (painel do dono no celular) dependem de mobile. Shell pronto destrava 4 OPs.
- **Effort:** G (3 semanas paralelas a F-A/F-B).
- **Experiment:** spike — protótipo PWA+Capacitor com auth + 1 fluxo offline + sync. Métrica: 0 perda de dado em 100 OS criadas sem rede.

### F-E — Integração WhatsApp BSP (Meta Cloud / Z-API / 360dialog)

- **LEAP:** F-4 (WhatsApp BSP integra ≤ R$ 0,50/conversa).
- **Por quê:** **iniciar aprovação Meta no dia 1** — espera de aprovação de templates é 7-21 dias. Sem WhatsApp, OP1/OP5/OP8/OP11/OP12 não funcionam.
- **Effort:** M (integração técnica) + tempo de espera burocrática.

### F-F — Spike F-1 modelo 100% agentes em BIG-12 Estoque (SEM mobile)

- **LEAP:** F-1 (modelo 100% agentes funciona).
- **Por quê:** validar o LEAP mais crítico do projeto em um Big Job pequeno e contido (Estoque) **antes** de comprometer MVP-1 inteiro. Mobile fica fora deste spike — mobile é F-D (paralelo).
- **Effort:** G (4 semanas de spike isolado).
- **Critério de sucesso:** ≥ 80% das operações de estoque executadas por agentes com supervisão humana ≤ 20% do tempo.

### F-G — Hooks bloqueantes Grupo 1 expandidos + CI básico

- **Por quê:** hooks já existem (block-destructive + secrets-scanner). Expandir Grupo 1 com: bloqueio de drop table, bloqueio de delete sem where, lint+types em pre-commit, CI mínimo no GitHub Actions.
- **Effort:** M (1 semana).

### F-H — ADR-0001 stack técnica decidida ANTES do spike F-F

- **Por quê:** decisão fundadora de ENGENHARIA D1-D6 (Spec Kit, spec-as-source, nomenclatura híbrida, devcontainer, CODEOWNERS, dual tooling) já existe, mas **stack** (linguagem, framework backend, ORM, DB, cloud) ainda não está em ADR. Sem ADR, spike F-F não tem chão.
- **Bloqueador:** ADR-0001 precisa ser assinado em ≤ 5 dias úteis.
- **Effort:** P (decisão + escrita do ADR).

---

## Re-sequenciamento MVP-1 em 2 Waves

> **Mudança crítica da auditoria 17/05:** MVP-1 não é mais "8 OPs lançadas juntas". Foi re-sequenciado em 2 Waves com critério explícito de dependência + risco regulatório.

### MVP-1 Wave A (semanas 6-14) — Núcleo regulatório / sobrevivência

> **Critério:** o que precisa estar pronto pra empresa não fechar / não perder acreditação / não levar multa fiscal.

1. **OP7 — NFS-e Padrão Nacional** — **PRIMEIRO** por deadline regulatório 01/09/2026 (Porto Alegre desliga local em 01/07/2026). Sem isso, receita = 0.
2. **OP2 — Certificado completo + cadeia rastreabilidade** — sobrevivência cláusula 7.11 ISO 17025 + base pra OP1.
3. **OP3 Solutions 3.1 + 3.2 — App técnico + caixa do técnico digital** (Solution 3.3 frota TCO move pra MVP-2).
4. **OP9 — Evoluir D→C→B→A sem trauma** (BIG-03, NOVA — wizard de setup por perfil).
5. **OP10 — Metrologia Legal + RBC no mesmo pacote** (BIG-06, NOVA — decisão fundadora 16/05).
6. **Módulo Financeiro mínimo** — contas a receber + status pago/pendente. Pré-requisito de OP7 (conciliação) e OP4 (comissão sobre recebimento).

### MVP-1 Wave B (semanas 14-22) — Camada de valor comercial

> **Critério:** o que destrava a venda recorrente após Wave A estar de pé. Construído sobre OP2 + F-C + F-E já prontos.

1. **OP1 — Recalibração proativa** — agora factível porque OP2 (certificado completo), F-C (cliente master) e F-E (WhatsApp BSP) estão prontos.
2. **OP4 — Comissões** — **simplificada**: SÓ 1 fórmula no MVP-1 (% sobre bruto) + gatilho por recebimento. Demais 7 fórmulas movem pra MVP-2.
3. **OP5 Solution 5.1 — Timeline 360°** (Solution 5.2 motor de automações completo já estava MVP-2).
4. **OP8 Solution 8.2 — Link WhatsApp quick win** (Solution 8.1 portal completo confirma MVP-2).
5. **OP11 — Cobrança + inadimplência** (NOVA — dor universal #11 órfã).
6. **OP12 — Painel do Dono / 1 número do dia** (NOVA — dor universal #12 órfã; depende de OP7+OP3+OP11).

---

## Opportunities (12 total — 8 originais + 4 novas da auditoria 17/05)

> **Critério de inclusão:** cada Opportunity tem (a) ancoragem em ≥ 1 dor ranqueada com score ≥ 1.000, (b) cobertura de ≥ 1 Big Job dos 12, (c) ≥ 3 personas afetadas das 14, (d) custo do status quo R$ ou hr quantificável, (e) gap competitivo confirmado em `concorrentes.md` OU decisão fundadora de PRODUTO (Roldão 17/05/2026).
>
> **Confidence dual-axis:** desde a auditoria 17/05, Confidence tem 2 eixos: (a) Confidence-dono — quão certo o Roldão está; (b) Confidence-mercado — quantas entrevistas externas confirmam. **SOMENTE (b) entra no RICE até Onda 1.** (a) vira nota lateral.

---

### Opportunity 1 — Recalibração lembrada de forma proativa (não esquecida)

**Big Job:** BIG-02 (não-perder-acreditação) + BIG-10 (Cliente 360°) + BIG-11 (Automações)
**Gap defensável:** #5 (CRM contínuo — concorrentes nacionais matam o cliente no CRM após emitir certificado)
**Wave:** MVP-1 Wave B (depende de OP2 + F-C + F-E prontos)

**Origem em dores-mapeadas.md:** **Dor #02 — Esquecimento de lembrar cliente da próxima calibração** (score **28.500**, o maior do mapa).

**Evidência:**
- Jornada §1 + §8: "empresa-modelo perde 30-50% das recalibrações por esquecimento" → **R$ 8-12k/mês de receita perdida** [INFERÊNCIA — validar em onda 1]
- JTBD-084 (renovação automática), JTBD-044 (alerta 60-90 dias), JTBD-090 (alerta cliente inativo >180d), JTBD-096 (oportunidade auto pós-12m)
- `concorrentes.md` §3.1-3.10: Cali, Metroex, Calibre, Q-MAN, ConfLab — todos têm "agenda de validade" mas **nenhum tem CRM contínuo com automação WhatsApp aprovada + proposta automática de renovação**
- Decisão fundadora de PRODUTO 3 (Cliente 360° + CRM + Automações)

**Personas mais afetadas:** Roldão (perde receita), Rogério (perde comissão de renovação), Sandra (não fecha ciclo qualidade), João Eng. (cliente final sem certificado válido), João-Sênior (cliente low-tech que migra pra concorrente sem perceber)

**Custo do status quo:** **R$ 8.000-12.000/mês de receita perdida por empresa** (Jornada §8) + R$ 1-2k/mês em horas de Letícia/Rogério mandando lembrete manual quando lembram.

#### Solution 1.1 — Calendário de validade + régua de notificação WhatsApp aprovada

**Descrição:** O sistema calcula automaticamente a próxima janela de recalibração (60/30/15 dias antes do vencimento) por equipamento × cliente e dispara mensagem via template WhatsApp Business aprovado pela Meta — sem ação humana. Cliente final responde "quero agendar" → cria oportunidade pré-preenchida no funil de venda.

**Premissas a validar:** D-1 (compra unificada), D-3 (Letícia adota inbox unificada), D-16 (WhatsApp obrigatório — **SABEMOS**), F-4 (WhatsApp BSP integra ≤ R$ 0,50/conversa)

**Custo:** **M** (calendário + cron + template Meta + integração BSP — Z-API/360dialog/Meta Cloud)

**Experiment:** **Smoke test** — landing page com tráfego pago R$ 1.000 (Meta Ads + Google Ads SP/RS/MG). Métrica: ≥ 2% de conversão pra trial em donos perfil A/B/C identificados.

#### Solution 1.2 — Proposta de renovação automática pré-aprovada

**Descrição:** Sistema gera proposta automática com preço pré-aprovado (margem mínima travada pelo dono), envia link curto no WhatsApp; cliente clica, aceita, escolhe janela; vira OS agendada + assinatura digital simples + entrada no fluxo financeiro. JTBD-092 materializado.

**Premissas a validar:** D-1, D-10 (João-Sênior abre link no WhatsApp — **SABEMOS parcial**), V-2 (WTP), E-3, F-15 (assinatura digital ICP-Brasil A1 funciona)

**Custo:** **G** (geração de proposta + DSL de preço + link curto assinado + portal lite + OS automática)

**Experiment:** **Fake-door** — botão "Renovar com 1 clique" na landing + 5 entrevistas Onda 1 com clientes finais perfil João-Sênior. Métrica: 4/5 dizem "sim, eu clicaria".

#### Solution 1.3 — Painel de "cliente em risco" + alerta de inativo > 180 dias

**Descrição:** Pra Rogério (vendedor) — dashboard ranqueado por risco de churn (sem recalibração há X dias × LTV histórico × probabilidade migração). Comissão de retenção configurada pra essa ação no BIG-09.

**Premissas a validar:** D-7 (Rogério adota CRM pipeline), V-2, V-6 (pricing por perfil), F-8

**Custo:** **M** (algoritmo simples de risco — sem ML; lista ranqueada)

**Experiment:** **Protótipo clicável** — dashboard pra 5 vendedores reais. Métrica: 4/5 dizem "isso me faz vender mais" + auto-reportam ≥ R$ 500/mês de comissão recuperável.

---

### Opportunity 2 — Certificado emitido sem medo (cadeia completa + dossiê + assinatura digital ICP-Brasil)

**Big Job:** BIG-01 (ciclo completo) + BIG-02 (não perder acreditação)
**Gap defensável:** #1 (ciclo completo OS→certificado→NFS-e — **NENHUM concorrente nacional faz**, exceto FP2 regional Santa Maria/RS)
**Wave:** MVP-1 Wave A (#2 do top 3)

**Origem em dores-mapeadas.md:**
- **Dor #04 — Word/Excel/macros = NC permanente cláusula 7.11** (score **8.250**)
- **Dor #03 — Certificado sem campo NIT-DICLA-030** (score **2.400**, R-018 score 25 — o maior risco do projeto)
- **Dor #06 — Padrão usado com calibração vencida** (score **3.000**)
- **Dor #07 — Signatário-gargalo** (score **3.000**)

**Evidência:**
- Jornada §6.5 + §6.bis: "Planilha Excel + macros pra incerteza, SEM validação documentada = NC permanente da cláusula 7.11"
- JTBD-027, JTBD-028, JTBD-030, JTBD-051, JTBD-031
- INV-002 (cadeia rastreabilidade trava emissão), INV-004 (dossiê de validação), INV-011 (padrão vencido bloqueia)
- `concorrentes.md` §3.1-3.10: Cali tem cálculo de incerteza mas **sem dossiê de validação documentado**

**Personas mais afetadas:** Marcos (signatário), Sandra (RT), Roldão, Patrícia (cliente farma), Auditor Cgcre

**Custo do status quo:** **R$ 50.000-500.000 de indenização** + **perda de acreditação** = empresa fechada.

> **VALIDAR ANTES DE COMPROMETER** — esta OP entrou no MVP-1 por decisão fundadora de PRODUTO antes de entrevistas externas. Critério: >= 60% das 10 entrevistas Onda 1 confirmam dor + DAP >= R$ 200/mês. Se não atingir, mover pra MVP-2.

#### Solution 2.1 — Procedimentos PT-BR validados (massa, pressão, temperatura primeiro) + dossiê de validação cláusula 7.11

**Descrição:** O sistema entrega 3 grandezas com procedimento de cálculo de incerteza GUM/JCGM 100 pré-validado por metrologista externo + dossiê de validação gerado nativamente. Lab assina dossiê 1 vez por upgrade de versão e sai da NC permanente.

**Premissas a validar:** F-5 (LEAP #6), D-5 (LEAP #7), F-12

**Custo:** **G** (3 procedimentos × metrologista RBC externo R$ 6k + dossiê template + change log com hash)

**Experiment:** **Spike técnico** — comparar com Excel de 3 metrologistas RBC reais. Métrica: 3/3 concordam + 3/3 assinariam com CPF.

#### Solution 2.2 — Cadeia de rastreabilidade automática + bloqueio de emissão se padrão vencido / fora de escopo

**Descrição:** Hooks bloqueantes: emissão falha se padrão vencido OU signatário sem competência declarada OU campo NIT-DICLA-030 vazio. Mensagem PT-BR clara + link pra ação.

**Premissas a validar:** F-6 (hooks <= 5% falsos-positivos), F-1 (LEAP #1), E-2

**Custo:** **M** (motor de regras + matriz competência × signatário × grandeza × faixa)

**Experiment:** **Protótipo + entrevista validativa** — 5 RTs + 1 auditor Cgcre real. Métrica: 4/5 RTs + auditor confirma "atende cláusula 7.11".

#### Solution 2.3 — Assinatura digital ICP-Brasil A1/A3 + workflow "4 olhos" + fila do signatário priorizada por SLA do cliente

**Descrição:** Marcos assina digitalmente no celular/desktop com certificado A1/A3. Fila priorizada por SLA. Opcional "4 olhos".

**Premissas a validar:** F-15, D-5, F-7 (LEAP #10)

**Custo:** **M** (integração BaaS assinatura + fila com SLA)

**Experiment:** **Spike + WTP test** — Van Westendorp mediana >= R$ 300/mês.

---

### Opportunity 3 — Operação de campo controlada (frota, UMC, caixa do técnico, custo real por OS)

**Big Job:** BIG-08 (Frota + UMC + Caixa do técnico — decisão fundadora de PRODUTO 1)
**Gap defensável:** #6 (Frota + UMC + Caixa do técnico integrado a custo por OS — **inexistente em concorrentes**)
**Wave:** MVP-1 Wave A (Solutions 3.1 + 3.2; Solution 3.3 = MVP-2)

**Origem em dores-mapeadas.md:**
- **Dor #16 — Caixa do técnico + frota descontrolados** (score **6.300**)
- **Dor #19 — Registro em WhatsApp viola cláusula 7.5.1** (score **6.300**)
- **Dor #08 — Roteirização no escuro + 2ª visita** (score **1.000**)

**Evidência:**
- Decisão fundadora de PRODUTO Roldão 17/05/2026
- JTBD-060 a JTBD-070
- Jornada §5.4-5.5
- R-043 a R-047 (5 riscos novos)

**Personas mais afetadas:** Bruno (técnico), Bruna, Carlos (motorista UMC), Cláudia, Roldão

**Custo do status quo:** **R$ 3.000-6.000/mês de 2ª visita** + **R$ 1-2k/mês em comprovantes perdidos** + **R$ 500-2.000 em multas** + **risco patrimonial R$ 100-300k**.

> **VALIDAR ANTES DE COMPROMETER** — esta OP entrou no MVP-1 por decisão fundadora de PRODUTO antes de entrevistas externas. Critério: >= 60% das 10 entrevistas Onda 1 confirmam dor + DAP >= R$ 200/mês. Se não atingir, mover pra MVP-2.

#### Solution 3.1 — App mobile simples pra técnico/motorista

**Descrição:** App PWA + Capacitor com UI BIG, 3 telas: "minha OS de hoje", "registrar gasto", "fim do dia". Offline-first com IndexedDB.

**Premissas a validar:** D-4 (LEAP), D-8 (LEAP), F-10 (LEAP #12)

**Custo:** **G** (3 semanas spike + 2 meses produção)

**Experiment:** **Spike mobile** — UAT de 5 técnicos reais. Métrica: 70% completam OS digital sem ajuda em <= 5 min.

#### Solution 3.2 — Caixa do técnico digital (adiantamento -> prestação -> conciliação automática)

**Descrição:** Técnico solicita -> Cláudia aprova -> PIX cai -> técnico gasta + foto -> categoriza -> prestação automática. JTBD-068 materializado.

**Premissas a validar:** E-8, D-6, V-2

**Custo:** **G** (workflow + integração PIX BaaS + holerite hooks)

**Experiment:** **Protótipo + ride-along** — 2 técnicos × 3 dias. Métrica: 100% das despesas categorizadas com foto até dia D+1.

#### Solution 3.3 — Frota + UMC com TCO consolidado — **MOVIDO PRA MVP-2**

**Descrição:** Cadastro de veículos + odômetro + manutenção preventiva + integração SENATRAN/DETRAN + georreferenciamento UMC.

**Premissas a validar:** F-2 (LEAP #11), E-8, V-6

**Custo:** **G** (integração SENATRAN + telemetria + TCO)

**Experiment:** **Spike técnico** — API SENATRAN por 30 dias. Métrica: 1 multa recuperada em D+15.

---

### Opportunity 4 — Comissões pagas certas, no prazo, sem briga e sem planilha

**Big Job:** BIG-09 (Comissões configuráveis — decisão fundadora de PRODUTO 2)
**Gap defensável:** #7 (configuração de comissão sem programador, integrada a OS + financeiro + frota)
**Wave:** MVP-1 Wave B — **versão simplificada** (1 fórmula apenas)

**Origem em dores-mapeadas.md:**
- **Dor #15 — Comissões em planilha frágil, 3-5 dias do mês + brigas mensais** (score **1.312**)

**Evidência:**
- Decisão fundadora de PRODUTO Roldão 17/05/2026
- JTBD-071 a JTBD-082
- **R-055** (era "R-novo C1" — questão judicial sobre regra mudada sem aceite)
- **R-056** (era "R-novo C2")
- **R-057** (era "R-novo C3")
- `concorrentes.md`: nenhum concorrente nacional tem motor de comissões configurável

**Personas mais afetadas:** Cláudia, Roldão, Rogério, Bruno, Carlos

**Custo do status quo:** **R$ 600-1.000/mês em horas** + **R$ 500-2.000/mês de comissão paga errada** + **risco trabalhista R-055 score 12**.

> **VALIDAR ANTES DE COMPROMETER** — esta OP entrou no MVP-1 por decisão fundadora de PRODUTO antes de entrevistas externas. Critério: >= 60% das 10 entrevistas Onda 1 confirmam dor + DAP >= R$ 200/mês. Se não atingir, mover pra MVP-2.

> **Escopo MVP-1 reduzido:** **SÓ 1 fórmula (% sobre bruto) + gatilho por recebimento.** Demais 7 fórmulas (líquido, margem, ticket, escalonado, equipe, divisão multi-participante, retenção) movem pra MVP-2.

#### Solution 4.1 — DSL configurável pelo dono — **MVP-1 = 1 fórmula apenas**

**Descrição:** Tela "Configurar comissão" — dono escolhe % sobre bruto + gatilho por recebimento confirmado. Simulador "se rodasse hoje". Mudança de regra exige aceite digital (mitiga **R-055**).

**Premissas a validar:** V-8, D-1, E-8

**Custo:** **M** no MVP-1; **G** no MVP-2 (DSL completa)

**Experiment:** **Protótipo clicável + 5 entrevistas com donos perfil B**. Métrica: 4/5 configuram em <= 10 min sem ajuda.

#### Solution 4.2 — Bloqueio automático: não paga comissão sobre OS com prejuízo nem sobre inadimplência

**Descrição:** Hook cruza custo real da OS (BIG-08) e status de recebimento (BIG-04). Comissão sobre OS de margem negativa = bloqueada. Comissão sobre OS não-recebida = trava até recebimento (mitiga **R-057**).

**Premissas a validar:** F-2, E-1 (LEAP #8), V-7

**Custo:** **M** (depende de BIG-08 + BIG-04 integrados)

**Experiment:** **Spike de dados** — 3 meses do Roldão real. Métrica: identifica >= R$ 1.000 de comissão paga errada.

#### Solution 4.3 — Fechamento mensal em 1 hora com auditoria de cada ajuste

**Descrição:** Tela "Fechar comissão" com base auto + ajustes manuais (motivo obrigatório) + aceite digital. Cada ajuste vira evento auditado.

**Premissas a validar:** D-6, F-9, V-2

**Custo:** **M** (workflow + audit log)

**Experiment:** **Time-trial real** — Cláudia status quo × protótipo. Métrica: redução >= 70% de tempo + 0 ajustes não-auditados.

---

### Opportunity 5 — Cliente nunca "morre" no CRM (visão 360° + automações configuráveis sem código)

**Big Job:** BIG-10 (Cliente 360°) + BIG-11 (Automações configuráveis) — decisão fundadora de PRODUTO 3
**Gap defensável:** #8 (CRM 360° integrado a calibração)
**Wave:** MVP-1 Wave B (Solution 5.1 apenas; 5.2 confirma MVP-2; 5.3 promovido pra Foundation F-C)

**Origem em dores-mapeadas.md:**
- **Dor #20 — Cliente "morre" no CRM após calibração** (score **1.800**)
- **Dor #05 — Status de OS perguntado 10-30x/dia** (score **2.869**)
- **Dor #01 — Cadastro digitado 4-6 vezes** (score **8.100**)

**Evidência:**
- Decisão fundadora de PRODUTO Roldão 17/05/2026
- JTBD-083 a JTBD-097
- Jornada §1: "1 a 3 clientes finais perdidos por trimestre" × LTV médio = R$ 30-90k/ano
- **R-049** (era "R-novo CRM-1" — automação errada disparando 500 mensagens)
- **R-050** (era "R-novo CRM-2")
- **R-035 elevado** (era "R-novo CRM-3" — risco já existente promovido)

**Personas mais afetadas:** Roldão (perda silenciosa), Rogério, Letícia, Sandra

**Custo do status quo:** **R$ 2.500-7.500/mês de receita perdida silenciosamente** + **R$ 1-2k/mês em horas de Letícia**.

#### Solution 5.1 — Timeline 360° por cliente (MVP-1 Wave B)

**Descrição:** Tela única por cliente: cabeçalho com saúde (verde/amarelo/vermelho), timeline cronológica de eventos de 5 sistemas, ações rápidas. Mata Dor #01 + #05 + alimenta #20.

**Premissas a validar:** D-3 (LEAP), D-6, F-2 (LEAP #11)

**Custo:** **G** (modelo de dados consolidado + integração com 5 módulos)

**Experiment:** **Protótipo clicável + UAT** — 5 atendentes Letícia-equivalentes. Métrica: 4/5 dizem "quero hoje" + tempo de responder cai pra <= 30s.

#### Solution 5.2 — Motor de automações configurável sem código — **MVP-2**

**Descrição:** Dono configura regras "se cliente X então Y" sem programador. Sandbox obrigatório (mitiga **R-049**). Audit log de cada disparo.

**Premissas a validar:** V-8, F-6, E-3

**Custo:** **G** (DSL + sandbox + audit + UI sem código)

**Experiment:** **Fake-door** — landing "Crie regras sem programador" + 3 entrevistas pra mapear automações desejadas.

#### Solution 5.3 — Cliente único master — **PROMOVIDO PRA FOUNDATION F-C**

Ver Foundation F-C. Foi reclassificado como foundation porque é pré-requisito de OP1/OP2/OP4/OP7 — não é mais solution dentro de OP5.

---

### Opportunity 6 — Estoque + lacre/selo INMETRO rastreáveis individualmente

**Big Job:** BIG-12 (Estoque com lacre/selo — decisão fundadora de PRODUTO 4)
**Gap defensável:** #9 (rastreabilidade individual de lacre/selo INMETRO — **inexistente em concorrentes**)
**Wave:** MVP-1 Wave A (selecionada via spike F-F)

**Origem em dores-mapeadas.md:**
- **Dor #18 — Selo INMETRO/lacre sem rastreabilidade individual** (score **375**)
- **Dor #17 — Cliente confunde "selo INMETRO" com "certificado calibração"** (score **240**)

**Evidência:**
- Decisão fundadora de PRODUTO Roldão 17/05/2026
- JTBD-101 a JTBD-103, JTBD-108
- **R-051** (era "R-novo EST-1" — selo perdido sem controle)
- **R-052** (era "R-novo EST-2" — selo aplicado em equipamento errado = fraude metrológica)
- **R-053** (era "R-novo EST-3")
- **R-054** (era "R-novo EST-4")

**Personas mais afetadas:** Bruno (técnico aplicador), Sandra (responde fiscal IPEM), Roldão, Auditor IPEM, João-Sênior

**Custo do status quo:** **R$ 500-5.000/mês de multa IPEM** + **risco jurídico criminal** + **R$ 200-500/mês em selo perdido (R-051)**.

> **VALIDAR ANTES DE COMPROMETER** — esta OP entrou no MVP-1 por decisão fundadora de PRODUTO antes de entrevistas externas. Critério: >= 60% das 10 entrevistas Onda 1 confirmam dor + DAP >= R$ 200/mês. Se não atingir, mover pra MVP-2.

#### Solution 6.1 — Cada selo/lacre é entidade com número único + foto obrigatória + cliente vinculado

**Descrição:** Compra de lote -> cada selo entra no estoque como entidade individual. Técnico aplica -> app obriga foto do selo + foto do equipamento + georreferenciamento + assinatura do cliente final touch. Busca por número responde fiscal IPEM em 30s.

**Premissas a validar:** D-4 (LEAP), F-10 (LEAP #12), E-7

**Custo:** **M** (modelo de dados + workflow de aplicação)

**Experiment:** **Protótipo + 3 ride-alongs** — Bruno aplica selo em campo. Métrica: 100% dos selos com foto + cliente + número.

#### Solution 6.2 — Multi-local + transferência 2 etapas com aceite

**Descrição:** Estoque dividido em locais lógicos (sede, UMC#1, UMC#2, técnico Bruno, em-uso-cliente-X). Transferência exige envio + aceite. Sem aceite, item fica em "trânsito".

**Premissas a validar:** D-4, F-2, V-2

**Custo:** **M** (workflow de transferência + estado visual)

**Experiment:** **Protótipo + 1 semana piloto Roldão**. Métrica: 100% das transferências aceitas em <= 1 dia + 0 sumiço.

#### Solution 6.3 — Aviso obrigatório no certificado + calendário separado de verificação periódica INMETRO

**Descrição:** Mata Dor #17 — todo certificado de equipamento com obrigação de verificação periódica IPEM traz nota visível. Sistema mantém calendário separado e cobra lembrete (acoplado a OP1). **Referência cruzada com OP10 Solution 10.3.**

**Premissas a validar:** E-10 (INV-016), D-10

**Custo:** **P** (regra de geração + calendário extra)

**Experiment:** **Validação com 5 clientes finais João-Sênior**. Métrica: 4/5 entendem a diferença.

---

### Opportunity 7 — NFS-e municipal emitida sem dor (multi-município + cutover Padrão Nacional 01/09/2026)

**Big Job:** BIG-04 (NFS-e multi-município)
**Gap defensável:** #4 (NFS-e + calibração 17025 no mesmo produto)
**Wave:** MVP-1 Wave A — **PRIMEIRO** por deadline regulatório

**Origem em dores-mapeadas.md:**
- **Dor #10 — NFS-e cutover 01/09/2026 + 26 prefeituras** (score **8.750**)
- **Dor #09 — Conciliação manual 4h/semana** (score **3.187**)

**Evidência:**
- Jornada §7.1 (R-016): cutover Padrão Nacional CGSN 189/2026 obrigatório 01/09/2026; R-017 Porto Alegre desliga local 01/07/2026
- `concorrentes.md` §3-4: "GAP CONFIRMADO" — nenhum dos 14 concorrentes nacionais tem NFS-e nativa
- JTBD-034, JTBD-035

**Personas mais afetadas:** Cláudia, Roldão, Patrícia

**Custo do status quo:** **R$ 200-600/mês de Bling/Omie/Conta Azul** + **4h/semana de Cláudia em conciliação** + **risco fiscal cutover** = receita = 0 se não migrar até 01/09/2026.

#### Solution 7.1 — BaaS fiscal unificado (Focus/PlugNotas/TecnoSpeed) cobrindo 12+ municípios + Padrão Nacional

**Descrição:** Integração com 1 BaaS fiscal cobrindo 12-15 municípios prioritários + Padrão Nacional CGSN 189/2026 pronto pra 01/09/2026. Emissão a partir da OS finalizada — descrição técnica auto-gerada pelo certificado.

**Premissas a validar:** F-3 (LEAP), V-1, V-11

**Custo:** **M** (integração API + mapeamento por município)

**Experiment:** **Spike fiscal** — testar 3 BaaS em 15 municípios. Métrica: 1 BaaS cobre >= 12 + custo/NFS-e <= R$ 0,80.

#### Solution 7.2 — Conciliação automática extrato × NFS-e × OS

**Descrição:** Cláudia conecta conta bancária via Open Finance ou importa OFX. Sistema bate PIX por txid, boleto por nosso número, transferência por regex. Mata 80% das 4h/semana.

**Premissas a validar:** F-13 (**SABEMOS parcial**), E-1 (LEAP #8), V-13

**Custo:** **M** (integração + motor de match)

**Experiment:** **Spike de dados** — 1 mês de extrato real do Roldão. Métrica: >= 90% match automático.

#### Solution 7.3 — Detalhamento técnico do serviço auto-gerado a partir do certificado

**Descrição:** NFS-e descrição = auto-gera "Calibração de balança X, série Y, faixa Z, certificado nº W..." Patrícia (farma) aceita sem questionar.

**Premissas a validar:** D-9, V-13

**Custo:** **P** (regra de geração + mapeamento código serviço)

**Experiment:** **Validação com 3 gerentes farma**. Métrica: 3/3 dizem "essa eu aceito".

---

### Opportunity 8 — Cliente final acessa certificados sem ligar / sem perguntar status

**Big Job:** BIG-07 (Portal do cliente)
**Gap defensável:** #5 parcial (portal end-customer com escopo seguro)
**Wave:** MVP-1 Wave B (Solution 8.2 apenas; 8.1 e 8.3 confirmam MVP-2)

**Origem em dores-mapeadas.md:**
- **Dor #05 — Status de OS perguntado 10-30x/dia** (score **2.869**)
- **Dor #13 — Auditoria farma sem aviso** (score **400**)

**Evidência:**
- JTBD-017, JTBD-091, JTBD-058
- `concorrentes.md` §3.1: "Cali WEB existe mas portal feio que ninguém usa"
- D-10 (**SABEMOS parcial**), D-17

**Personas mais afetadas:** João Eng., Patrícia, João-Sênior, Letícia

**Custo do status quo:** **R$ 800-1.500/mês em horas de Letícia** + **risco operacional Sandra "virar a noite"** em auditoria farma.

#### Solution 8.1 — Portal end-customer simples — **MVP-2**

**Descrição:** Cliente final loga e vê certificados + status OS + próxima recalibração + botões de ação. Acoplado a OP5 (Cliente 360°) e OP7 (NFS-e).

**Premissas a validar:** D-17, E-7

**Custo:** **M** (UI + auth + scoped read-only)

**Experiment:** **Smoke test** — landing + 5 entrevistas farma. Métrica: 4/5 dizem "portal vira critério de habilitação".

#### Solution 8.2 — Link público assinado de WhatsApp — **MVP-1 Wave B quick win**

**Descrição:** Pra cliente final low-tech (D-10) — link curto assinado com expiração 30 dias + URL única por certificado; manda no WhatsApp; clica -> baixa PDF. Sem login.

**Premissas a validar:** D-10 (**SABEMOS parcial**), D-16 (**SABEMOS**), E-7

**Custo:** **P** (link curto + JWT scoped + expiração)

**Experiment:** **Validação com 5 João-Sênior reais**. Métrica: 5/5 clicam e baixam em <= 60s sem ajuda.

#### Solution 8.3 — Modo Auditoria 1 clique — **MVP-2**

**Descrição:** JTBD-058 materializado. Sandra clica "Modo Auditoria" -> tela única com todos os certificados + cadeia + competências + dossiê + NCs. Exportável em PDF.

**Premissas a validar:** D-9, E-2

**Custo:** **M** (consolidação read + export estruturado)

**Experiment:** **Validação com 3 gerentes farma + 2 RTs**. Métrica: 4/5 dizem "isso me tira da noite virada".

---

### Opportunity 9 — Evoluir D -> C -> B -> A sem trauma (NOVA — auditoria 17/05)

**Big Job:** BIG-03 (4 perfis configuráveis — gap defensável já existente em `concorrentes.md`)
**Gap defensável:** materializa BIG-03 — nenhum concorrente trata 4 perfis com regras configuráveis
**Wave:** MVP-1 Wave A

**Por que NOVA:** auditoria 12 agentes identificou que BIG-03 não tinha OP dedicada — estava diluído em outras. Materializa decisão fundadora 16/05 (4 perfis A/B/C/D + tipos configuráveis) e INV-015.

**Personas:** Persona 1 Roldão (perfil B atual) / Sandra RT (define quando upgrade) / Marcos metrologista (consultor de transição)

**Custo do status quo:** empresa perfil D paga ferramentas como se fosse B e não usa; empresa perfil C contrata consultoria 17025 R$ 30-80k sem necessidade de software ainda; perda de conversão por feature gating errado.

#### Solution 9.1 — Wizard de setup por perfil com regras configuráveis (INV-015)

**Descrição:** Onboarding com 3 perguntas (nº colaboradores, faturamento, tem ISO 17025?) -> sistema configura perfil A/B/C/D automaticamente. Features ativadas/desativadas conforme perfil. Tipos configuráveis (balança, manômetro, termômetro, etc.) seguem INV-015.

**Premissas a validar:** V-6 (pricing por perfil), D-1, F-8

**Custo:** **M** (matriz de perfil × features + UI wizard)

**Experiment:** **Protótipo + 10 entrevistas (2-3 por perfil)**. Métrica: 8/10 ficam no perfil sugerido após 30 dias de uso.

#### Solution 9.2 — Trilha didática perfil C (checklist 17025 + glossário PT-BR)

**Descrição:** Pra empresa em transição D->C buscando ISO 17025 — checklist progressivo de cláusulas + glossário PT-BR + templates de POPs. Reduz custo de consultoria externa de R$ 30-80k pra R$ 5-10k (consultoria pontual).

**Premissas a validar:** V-2, D-12, E-2

**Custo:** **G** (conteúdo curado por metrologista RBC + UI didática)

**Experiment:** **Smoke test** — landing "Saia de D pra C em 6 meses sem consultoria de R$ 50k" + entrevistas com 5 donos perfil C. Métrica: >= 30% conversão pra trial.

#### Solution 9.3 — Upgrade de perfil sem perda de histórico

**Descrição:** Empresa cresce D->C, depois C->B. Sistema preserva todo histórico (certificados, clientes, OS, financeiro) e ativa novas features sem migração de dados.

**Premissas a validar:** F-2, V-12, F-16

**Custo:** **P** (regras de feature flag por perfil + audit de upgrade)

**Experiment:** **Spike** — simular upgrade D->C->B no Roldão real. Métrica: 0 perda de dado + features ativadas em <= 5 min.

---

### Opportunity 10 — Metrologia Legal + RBC no mesmo pacote (NOVA — auditoria 17/05)

**Big Job:** BIG-06 (Metrologia Legal — gap defensável já existente)
**Gap defensável:** materializa BIG-06 — decisão fundadora 16/05 (Metrologia Legal obrigatória)
**Wave:** MVP-1 Wave A (dependência: OP2 pronto)

**Por que NOVA:** auditoria 17/05 identificou que Metrologia Legal estava só parcialmente coberta em OP6 (selo INMETRO). Faltava OP dedicada cobrindo o ciclo completo de verificação INMETRO + RBC no mesmo produto. Decisão fundadora de PRODUTO 16/05 tornou explícito.

**Personas:** Sandra (RT — define escopo), Marcos (signatário — assina verificação), Roldão, Auditor IPEM, cliente final João-Sênior (balança comercial)

**Custo do status quo:** lab que faz RBC e Metrologia Legal usa 2 ferramentas separadas; perde clientes que querem 1 fornecedor pra tudo; multa IPEM quando esquece verificação periódica.

> **VALIDAR ANTES DE COMPROMETER** — esta OP entrou no MVP-1 por decisão fundadora de PRODUTO antes de entrevistas externas. Critério: >= 60% das 10 entrevistas Onda 1 confirmam dor + DAP >= R$ 200/mês. Se não atingir, mover pra MVP-2.

#### Solution 10.1 — Cadastro tipo balança/instrumento com norma aplicável + verificação INMETRO periódica

**Descrição:** Catálogo de tipos (balança comercial, bomba combustível, taxímetro, esfigmomanômetro, etc.) com norma aplicável (Portaria INMETRO) + ciclo de verificação. Sistema sabe que balança comercial verifica anualmente; bomba combustível trimestral.

**Premissas a validar:** F-5, E-2, D-1

**Custo:** **M** (catálogo de tipos + ciclo de verificação por tipo)

**Experiment:** **Validação com 3 RTs + 1 fiscal IPEM**. Métrica: 4/4 confirmam que catálogo está conforme portarias INMETRO vigentes.

#### Solution 10.2 — Ciclo verificação IPEM com alertas

**Descrição:** Sistema gera alertas 60/30/15 dias antes da verificação INMETRO vencer. Cliente recebe WhatsApp via F-E. Mata risco de equipamento usado em comércio com selo vencido.

**Premissas a validar:** D-10, D-16, F-4

**Custo:** **P** (regra de calendário + integração F-E)

**Experiment:** **Spike** — gerar alertas pro Roldão real por 30 dias. Métrica: 100% dos alertas com data correta da próxima verificação INMETRO.

#### Solution 10.3 — Selo INMETRO com rastreabilidade (referência cruzada OP6 Solution 6.1)

**Descrição:** Já coberto em OP6 Solution 6.1. Referência cruzada — mesma solution materializa BIG-06 e BIG-12 simultaneamente.

---

### Opportunity 11 — Cobrança + inadimplência (NOVA — Dor #11 órfã)

**Big Job:** BIG-04 (financeiro) + BIG-11 (automações)
**Gap defensável:** parcial (concorrentes têm boleto mas não régua de cobrança configurável integrada a OP1)
**Wave:** MVP-1 Wave B

**Por que NOVA:** auditoria 17/05 identificou que Dor #11 (cobrança + inadimplência) estava órfã — score 2.000 em `dores-mapeadas.md` mas nenhuma OP a materializava. É dor universal (não founder), confirmada em jornada §7.

**Origem em dores-mapeadas.md:** Dor #11 (score **2.000**)

**Personas:** Cláudia (financeiro), Roldão, Rogério (cliente em risco -> vendedor)

**Custo do status quo:** inadimplência 8-15% nos labs PME (Jornada §7.3) [INFERÊNCIA — validar onda 1] -> R$ 4-7k/mês de fluxo travado por empresa.

#### Solution 11.1 — Régua de cobrança configurável

**Descrição:** Dono configura régua: D+5 lembrete WhatsApp amigável; D+10 boleto re-enviado; D+15 ligação automática; D+30 protesto/SPC opcional. Sem programador.

**Premissas a validar:** V-8, F-4, E-3

**Custo:** **M** (DSL + integração F-E + WhatsApp + email)

**Experiment:** **Spike com Roldão real** — rodar régua em 1 mês. Métrica: redução >= 30% no DSO (days sales outstanding).

#### Solution 11.2 — PIX recorrente + boleto fallback

**Descrição:** Cliente PME usa PIX recorrente (cobrança automática); cliente que rejeita recebe boleto. Integração com Iugu/Asaas/Cora.

**Premissas a validar:** F-13, V-13, E-1

**Custo:** **M** (integração BaaS bancário + workflow PIX recorrente)

**Experiment:** **Spike fiscal-bancário** — testar 3 BaaS. Métrica: 1 BaaS cobre PIX recorrente + boleto + custo <= R$ 1/transação.

#### Solution 11.3 — Dashboard inadimplência por idade

**Descrição:** Cláudia abre tela e vê: a vencer (verde), 0-15 dias (amarelo), 16-30 dias (laranja), > 30 dias (vermelho). Drill-down por cliente. Alimenta OP12 (Painel do Dono) e OP5 (cliente em risco).

**Premissas a validar:** D-6, V-2

**Custo:** **P** (consolidação read + UI)

**Experiment:** **Protótipo + UAT Cláudia**. Métrica: tempo de identificar inadimplente top 10 cai de 30 min pra <= 1 min.

---

### Opportunity 12 — Painel do Dono / 1 número do dia (NOVA — Dor #12 órfã)

**Big Job:** BIG-10 (Cliente 360°) + BIG-11 (Automações)
**Gap defensável:** parcial (concorrentes têm dashboards mas não "1 número do dia" pro celular do dono)
**Wave:** MVP-1 Wave B (depende de OP7 + OP3 + OP11 prontos)

**Por que NOVA:** auditoria 17/05 identificou que Dor #12 (dono não sabe número do dia) estava órfã — score 4.500 em `dores-mapeadas.md`, o segundo maior de dores universais. Roldão é a primeira persona afetada.

**Origem em dores-mapeadas.md:** Dor #12 (score **4.500**)

**Personas:** Roldão (primária), Cláudia (alimenta dados), Rogério (drill-down vendas)

**Custo do status quo:** Roldão abre 5 sistemas por dia pra montar "número do dia" mental — 30-60 min/dia + decisões tardias por falta de visibilidade.

#### Solution 12.1 — Home com 3 KPIs (faturamento mês + OS abertas + inadimplência)

**Descrição:** Tela inicial do dono (mobile + desktop) com 3 números grandes: (1) faturamento do mês × meta; (2) OS abertas vs ontem; (3) inadimplência > 30 dias. Atualização real-time.

**Premissas a validar:** D-1, V-2, F-2

**Custo:** **M** (consolidação read de 3 módulos + UI mobile)

**Experiment:** **Protótipo + UAT Roldão**. Métrica: tempo de ler "número do dia" cai de 30-60 min pra <= 30s.

#### Solution 12.2 — Alerta WhatsApp diário pro dono

**Descrição:** Todo dia 8h, dono recebe WhatsApp: "Bom dia! Faturamento mês: R$ X (Y% da meta). OS abertas: Z. Inadimplência > 30d: R$ W." 1 mensagem, 3 números.

**Premissas a validar:** D-16, F-4, E-3

**Custo:** **P** (cron + template WhatsApp + integração F-E)

**Experiment:** **Spike** — Roldão recebe alerta diário por 14 dias. Métrica: NPS-dono >= 70 + 0 dias sem abrir mensagem.

#### Solution 12.3 — Drill-down por módulo

**Descrição:** Dono clica em qualquer KPI -> abre tela detalhada do módulo (financeiro, OS, inadimplência). Mobile-first.

**Premissas a validar:** F-10 (LEAP #12), D-1

**Custo:** **M** (telas detalhadas mobile)

**Experiment:** **UAT Roldão + 3 donos perfil B**. Métrica: 4/4 fazem drill-down de KPI até decisão em <= 2 min.

---

## Opportunity 13 — Agenda gerencial completa (NOVA — 2026-05-17, mapeamento Módulo 10)

**Big Job:** BIG-05 (Técnico campo) + BIG-10 (Cliente 360°)
**Gap defensável:** alto (concorrentes têm agenda básica; Aferê integra com INV-020 jornada motorista + visão multi-técnico/equipe/unidade)
**Wave:** **MVP-1 Wave A** (destrava OP3, OP1, OP15, OP16 e OP10)

**Por que NOVA:** mapeamento Módulo 10 da lista funcional do Roldão (2026-05-17) identificou que agenda estava embutida em OP3.1 (app campo) e OP10 (metrologia legal) mas **sem módulo gerencial completo** (visão multi-técnico, conflito de horário, feriado, dependência entre atividades, integração externa).

**Origem em jobs-to-be-done.md:** JTBD-009 (onde técnico está) + JTBD-010 (reagendar sem virar bagunça) — antes órfãos no OST.

**Personas:** Cláudia (gerente operacional — atribui), Roldão (vê consolidado), Técnicos (preferência de notificação), Cliente final (acompanhamento)

**Custo do status quo:** Gerente usa planilha + WhatsApp + memória → 30-60 min/dia de retrabalho + conflitos invisíveis + risco INV-020 motorista.

#### Solution 13.1 — Agenda visual multi-técnico (dia/semana/mês) com drag-and-drop
**Descrição:** Tela kanban-like ou Gantt com OS + chamados + reuniões posicionados no tempo, por técnico/equipe/unidade. Drag-and-drop pra realocar. **Hook INV-020** valida jornada antes de aceitar drop. Subtarefas, comentários, dependência entre atividades, bloqueios de horário, feriados.
**Custo:** **M** (UI tabular complexa + integração com OS/chamado/agenda)
**Experiment:** UAT com Roldão + Cláudia. Métrica: gerente realoca 5 OS em < 5 min sem violar INV-020.

#### Solution 13.2 — Templates de agenda recorrente + automações
**Descrição:** Template "calibração mensal cliente X" que gera OS recorrente. Conecta com OP1 (recalibração proativa) e ADR-0005 (engine automações).
**Custo:** **P** (depende ADR-0005)
**Experiment:** Smoke test após ADR-0005 implementada.

#### Solution 13.3 — Integração Google Calendar / iCal bidirecional
**Descrição:** Sync 2-way com Google Calendar do técnico. Compromissos pessoais bloqueiam agenda Aferê; OS aparece no calendário pessoal.
**Custo:** **M** (OAuth + sync 2-way)
**Experiment:** Spike 2 semanas com 2 técnicos. Métrica: 0 double-booking; sync < 5 min.

---

## Opportunity 14 — Fornecedores + Compras (NOVA — 2026-05-17, mapeamento Módulo 6)

**Big Job:** BIG-12 (Estoque) + ampliação
**Gap defensável:** parcial (concorrentes têm cadastro básico; Aferê integra com estoque INMETRO + cotação + avaliação)
**Wave:** **Wave C** (escala — após Wave B em produção)

**Por que NOVA:** módulo totalmente ausente do discovery anterior. Mapeamento Módulo 6 destacou.

**Personas:** Comprador (V2), Almoxarife, Dono (aprovação)

**Custo do status quo:** WhatsApp com fornecedor + planilha + email — sem histórico, sem comparação, sem auditoria.

#### Solution 14.1 — Cadastro de fornecedor + histórico de compras
**Descrição:** PJ com dados fiscais, contatos, contratos de fornecimento, condições de pagamento. Histórico filtra "fornecedor que entregou peça X".
**Custo:** **P** (similar a clientes)

#### Solution 14.2 — Cotação multi-fornecedor + aprovação
**Descrição:** Pedido de cotação enviado pra N fornecedores em paralelo. Comparativo lado-a-lado. Aprovação do comprador/dono.
**Custo:** **M** (workflow + integração WhatsApp/email)

#### Solution 14.3 — Avaliação de desempenho do fornecedor
**Descrição:** A cada entrega: "no prazo? qualidade? preço?". Rating agregado vira filtro em próxima cotação.
**Custo:** **P** (cadastro + agregação)

---

## Opportunity 15 — Orçamentos formal (NOVA — 2026-05-17, mapeamento Módulo 7)

**Big Job:** BIG-07 (Cliente 360°) + BIG-10 (CRM 360°)
**Gap defensável:** alto (concorrentes têm orçamento básico; Aferê integra com OS + contrato + assinatura eletrônica + leitura tracking)
**Wave:** **MVP-1 Wave A** (criação básica + conversão em OS) → **Wave B** (versionamento + assinatura eletrônica + leitura tracking)

**Por que NOVA:** OP8 Solution 8.2 (link WhatsApp) cobria só envio; criação/edição/versionamento órfão. Mapeamento Módulo 7 destacou.

**Origem em jobs-to-be-done.md:** JTBD-041 (orçamento profissional rápido) + JTBD-020 (não copiar info 3x chamado→orçamento→OS) + JTBD-075 (impacto desconto em comissão prevista)

**Personas:** Rogério (vendedor), Cláudia (aprovação), Cliente final (aprovação digital)

**Custo do status quo:** Word + email + impressão + caneta → 30-60 min por orçamento + perda de versão + falta de tracking de aceitação.

#### Solution 15.1 — Criação de orçamento + itens + descontos + impostos + condições (Wave A)
**Descrição:** Tela tipo "carrinho" com itens do catálogo. Cálculo automático de imposto (tenant configura alíquota com contador). Templates pra orçamento padrão (calibração, manutenção, instalação).
**Custo:** **P** (CRUD + cálculo)

#### Solution 15.2 — Versionamento + revisão + comparação (Wave B)
**Descrição:** Toda edição cria nova versão; UI mostra diff (preço, item adicionado/removido). Auditoria preserva original.
**Custo:** **M** (versionamento + UI diff)

#### Solution 15.3 — Envio cliente + leitura tracking + aprovação digital (Wave B)
**Descrição:** Link público (token expirável). Cliente lê → vendedor notificado. Aprovação 1-clique gera assinatura eletrônica (não-A3 — A3 é só pra certificado de calibração).
**Custo:** **M** (link público + tracking + assinatura simples)

#### Solution 15.4 — Conversão em OS / chamado (Wave A)
**Descrição:** Orçamento aprovado vira OS rascunho (já com cliente, itens, preço travado pelo INV-026). Conversão preserva audit.
**Custo:** **P** (handler de evento `OrcamentoAprovado` → cria OS)

---

## Opportunity 16 — Chamados / Helpdesk dedicado (NOVA — 2026-05-17, mapeamento Módulo 8)

**Big Job:** BIG-05 (campo) + BIG-10 (Cliente 360°) + BIG-11 (Automações)
**Gap defensável:** alto (concorrentes têm helpdesk genérico; Aferê integra triagem auto + regras distribuição inteligentes + mapa)
**Wave:** **MVP-1 Wave B** (após OP3 + OP13 prontos)

**Por que NOVA:** chamados estavam embutidos em OP3 (operação) sem destaque. Mapeamento Módulo 8 destacou SLA, regras distribuição, detecção duplicados, mapa.

**Origem em jobs-to-be-done.md:** JTBD-008 (triagem 30s) + JTBD-016 (abrir 1 min) + JTBD-020 (não copiar 3x) + JTBD-086 (WhatsApp em 1 clique)

**Personas:** Atendente (abre), Cláudia (atribui), Técnico (executa), Cliente final (acompanha)

**Custo do status quo:** WhatsApp + planilha + perda de contexto → 30% chamados sem rastreio + SLA invisível.

#### Solution 16.1 — Abertura multi-origem + triagem com sugestão automática
**Descrição:** Chamado entra via portal/WhatsApp/email/telefone. Triagem com 3-5 perguntas + sugestão de tipo/prioridade/categoria (LLM via gateway).
**Custo:** **P** (interface + LLM gateway pré-existente)

#### Solution 16.2 — Atribuição automática por regras (proximidade/carga/habilidade/rodízio)
**Descrição:** Engine de regras (ADR-0005) decide técnico. Configurável por tenant (catálogo fechado de critérios). Mapa mostra distribuição.
**Custo:** **M** (engine + UI configuração)

#### Solution 16.3 — SLA + alertas escalonados
**Descrição:** SLA por cliente (perfil A = 4h; perfil B = 24h; perfil D = 5d). Alerta se 70% do SLA passou. Escalonamento automático ao gerente.
**Custo:** **M** (timer + escalonamento + integração ADR-0005)

#### Solution 16.4 — Detecção de chamados duplicados
**Descrição:** Ao abrir chamado novo, busca por cliente+equipamento+tipo nos últimos 30d. Se duplicata provável, sugere mesclar.
**Custo:** **P** (fuzzy matching)

---

## Opportunity 17 — Equipamentos master (cadastro do cliente) (NOVA — 2026-05-17, mapeamento Módulo 4)

**Big Job:** BIG-01 (Costura horizontal) + BIG-02 (Certificado)
**Gap defensável:** parcial (concorrentes têm cadastro básico; Aferê integra QR Code + histórico unificado + alertas + INV-025 imutabilidade)
**Wave:** **MVP-1 Wave A** (suporta OP2 certificado completo)

**Por que NOVA:** equipamentos estavam vinculados a F-B (cadastros base) sem detalhamento. Mapeamento Módulo 4 destacou QR Code, foto, manual, conformidade técnica.

**Origem em jobs-to-be-done.md:** JTBD-021 (saber tudo da OS antes de chegar) + JTBD-091 (Cliente 360° em UMA tela)

**Personas:** Metrologista, Técnico de campo, Atendente, Cliente final (vê seus equipamentos no portal)

**Custo do status quo:** Equipamento cadastrado 3 vezes em sistemas diferentes; foto perdida; manual em arquivo morto; sem alerta de validade.

#### Solution 17.1 — Cadastro de equipamento + QR Code rastreamento físico
**Descrição:** Marca/modelo/serial/categoria/capacidade + foto + docs técnicos + manual anexo + QR Code único.
**Custo:** **P** (CRUD + storage)

#### Solution 17.2 — Histórico unificado de serviços/calibrações/certificados
**Descrição:** Tela "histórico do equipamento" mostra timeline com OS + certificados + revisões + NCs. Acessível pelo cliente via portal (OP8 Solution 8.1).
**Custo:** **P** (agregação de eventos)

#### Solution 17.3 — INV-025 enforcement (imutabilidade pós-emissão)
**Descrição:** Após 1º certificado emitido referenciando o equipamento, campos críticos (serial, modelo, fabricante) viram imutáveis. Edição cria nova versão; certificados antigos referenciam versão original.
**Custo:** **P** (trigger banco + versionamento)

#### Solution 17.4 — Alertas de validade + status conformidade
**Descrição:** Calendário de vencimento (próxima calibração, próxima verificação INMETRO). Integra com OP1 (recalibração proativa) + OP10 (metrologia legal).
**Custo:** **P** (cron + integração WhatsApp)

---

## Priorização final — Opportunity Scoring (RICE-adapted, Confidence dual-axis)

> **Fórmula:** Score = (Reach × Impact × Confidence-mercado) ÷ Effort, escala 1-5 em cada dimensão.
>
> **Confidence dual-axis (mudança da auditoria 17/05):**
> - **Confidence-dono:** quão certo o Roldão está. NÃO entra no RICE até Onda 1. Vira nota lateral.
> - **Confidence-mercado:** quantas entrevistas externas confirmam. ESTE é o Confidence que entra no RICE.
> - **Pré-onda 1:** Confidence-mercado para OPs ancoradas SÓ em decisão fundadora de PRODUTO = 3 (inferência forte, não confirmada externamente). OPs ancoradas em gap competitivo confirmado em `concorrentes.md` + dor universal de mercado = 4.
>
> - **Reach** (1-5): % do ICP afetado (Reach 5 = >= 90%)
> - **Impact** (1-5): tamanho da dor mensurada em R$/mês ou NC ativa
> - **Confidence-mercado** (1-5): grau de evidência externa atual (5 = >= 5 entrevistas confirmam; 3 = inferência forte sem entrevista; 1 = palpite)
> - **Effort** (1-5): custo de construção (1 = POC dias; 5 = trabalho meses + dependência integração)

### Tabela de priorização (17 OPs — 12 originais + 5 novas em 2026-05-17)

| # | Opportunity | Reach | Impact | Conf-mercado | Effort | **Score** | **Wave/MVP** | **Dependências** | **Time-bomb regulatório** | **Conf-dono** |
|---|---|---|---|---|---|---|---|---|---|---|
| **OP7** | NFS-e Padrão Nacional (Dor #10 — score 8.750) | 5 | 5 | 5 | 3 | **41,7** | **MVP-1 Wave A #1** | F-A, F-B | **SIM 01/09/2026** | 5 |
| **OP1** | Recalibração proativa (Dor #02 — score 28.500) | 5 | 5 | 4 | 2 | **50,0** | **MVP-1 Wave B** | OP2, F-C, F-E | Não | 5 |
| **OP2** | Certificado completo (Dor #04+#03+#06+#07) | 4 | 5 | 3 | 4 | **15,0** | **MVP-1 Wave A #2** | F-A, F-B, F-C | INV-002 hard | 5 |
| **OP3** | Frota+UMC+Caixa (Dor #16+#19+#08) | 4 | 4 | 3 | 5 | **9,6** | **MVP-1 Wave A** (3.1+3.2 só) | F-D | Não | 5 |
| **OP4** | Comissões 1 fórmula (Dor #15) | 4 | 3 | 3 | 3 | **12,0** | **MVP-1 Wave B** simplificada | OP7, OP3, fin mínimo | Não | 5 |
| **OP5** | Cliente 360° Solution 5.1 (Dor #20+#05+#01) | 5 | 4 | 4 | 3 | **26,7** | **MVP-1 Wave B** | F-C, OP2 | Não | 4 |
| **OP6** | Selo INMETRO (Dor #18+#17) | 3 | 4 | 3 | 3 | **12,0** | **MVP-1 Wave A** | F-D, OP10 | Não | 5 |
| **OP7** | (já listada) | | | | | | | | | |
| **OP8** | Solution 8.2 link WhatsApp (Dor #05+#13) | 4 | 3 | 4 | 2 | **24,0** | **MVP-1 Wave B** | OP2, F-E | Não | 4 |
| **OP9** | Evoluir D->C->B->A (BIG-03) | 5 | 4 | 3 | 3 | **20,0** | **MVP-1 Wave A** | F-A, F-B | Não | 4 |
| **OP10** | Metrologia Legal + RBC (BIG-06) | 4 | 4 | 3 | 3 | **16,0** | **MVP-1 Wave A** | OP2 | Parcial (verif INMETRO) | 5 |
| **OP11** | Cobrança + inadimplência (Dor #11) | 5 | 4 | 4 | 3 | **26,7** | **MVP-1 Wave B** | F-E, fin mínimo | Não | 3 |
| **OP12** | Painel do Dono (Dor #12) | 5 | 3 | 4 | 2 | **30,0** | **MVP-1 Wave B** | OP7, OP3, OP11 | Não | 5 |
| **OP13** | Agenda gerencial completa (NOVA — Módulo 10) | 5 | 4 | 3 | 3 | **20,0** | **MVP-1 Wave A** | F-B, INV-020 | Não | 4 |
| **OP14** | Fornecedores + Compras (NOVA — Módulo 6) | 3 | 3 | 3 | 4 | **6,75** | **Wave C** | Estoque BIG-12 | Não | 3 |
| **OP15** | Orçamentos formal (NOVA — Módulo 7) | 5 | 4 | 4 | 3 | **26,7** | **Wave A** (s15.1, s15.4) + **Wave B** (s15.2, s15.3) | F-C, OP-FIN | Não | 4 |
| **OP16** | Chamados/Helpdesk dedicado (NOVA — Módulo 8) | 5 | 4 | 4 | 3 | **26,7** | **MVP-1 Wave B** | OP3, OP13 | Não | 4 |
| **OP17** | Equipamentos master (NOVA — Módulo 4) | 5 | 4 | 4 | 2 | **40,0** | **MVP-1 Wave A** | F-C | Não | 4 |

### Top 3 Opportunities pro MVP-1 (recomendação inicial pós-auditoria)

> **Mudança crítica:** Top 3 pré-auditoria era OP1 + OP7 + OP5. Pós-auditoria, o Top 3 é orientado por **deadline regulatório + dependências**, não por RICE score puro.

1. **OP7 — NFS-e Padrão Nacional** (Wave A #1) — **deadline regulatório 01/09/2026 + Porto Alegre 01/07/2026, não-negociável.** Sem isso, receita = 0.
2. **OP2 — Certificado completo** (Wave A #2) — INV-002 + base pra OP1 + sobrevivência cláusula 7.11 ISO 17025.
3. **OP10 — Metrologia Legal + RBC** (Wave A) — decisão fundadora de PRODUTO 16/05 + dependência OP2 + risco IPEM.

> **Observação:** OP1 (recalibração proativa) tem o maior RICE score (50,0) mas só faz sentido depois de OP2 + F-C + F-E. Por isso vai pra Wave B, não pro Top 3 de construção inicial.

### MVP-1 Wave A completo (semanas 6-14) — atualizado 2026-05-17

- **OP7** (NFS-e — deadline regulatório)
- **OP2** (certificado completo)
- **OP3 Solutions 3.1+3.2** (app técnico + caixa; 3.3 = MVP-2)
- **OP9** (evoluir D->C->B->A — wizard de setup)
- **OP10** (Metrologia Legal + RBC)
- **OP13** (Agenda gerencial — NOVA; destrava OP3/OP10/OP15/OP16)
- **OP15 Solutions 15.1 + 15.4** (Orçamentos básicos + conversão em OS — NOVA)
- **OP17** (Equipamentos master — NOVA; suporta OP2)
- **Módulo Financeiro mínimo** (contas a receber + status pago/pendente)
- **OP6** (selo INMETRO — sai do spike F-F)

### MVP-1 Wave B completo (semanas 14-22)

- **OP1** (recalibração proativa — agora factível)
- **OP4 simplificada** (1 fórmula apenas)
- **OP5 Solution 5.1** (Timeline 360°)
- **OP8 Solution 8.2** (link WhatsApp)
- **OP11** (cobrança + inadimplência)
- **OP12** (Painel do Dono / 1 número do dia)

### MVP-2 (6-12 meses pós-GA)

- OP3 Solution 3.3 (frota TCO + SENATRAN)
- OP4 fórmulas 2-8 (DSL completa)
- OP5 Solution 5.2 (motor de automação completo)
- OP8 Solutions 8.1 + 8.3 (portal completo + Modo Auditoria)
- OP2 Solution 2.3 (workflow "4 olhos" + SLA por cliente)
- Conciliação Open Finance bidirecional (OP7 Solution 7.2 avançada)

### MVP-3 (12-24 meses)

- Biblioteca de procedimentos PT-BR validados (todas as grandezas além de 3 iniciais — OP2 expandida)
- Integração hardware (Bluetooth/USB com Beamex/Fluke/Presys — ANTI-06 modulado)
- Add-on farma 21 CFR Part 11-eq + RDC 658/786 (V-13)

### Não entra (lazy / non-goal)

- Folha de pagamento completa (ANTI-01) — integração externa
- Gateway de pagamento próprio (ANTI-02) — PSP terceiro
- BI customizável / SQL pelo usuário (ANTI-05 + ANTI-09) — export pra Metabase/PowerBI
- Mensageria interna / chat (ANTI-08) — usar WhatsApp
- Hardware proprietário (ANTI-06) — integrar, não fabricar
- LIS análises clínicas humanas (ANTI-03) — escopo permanente fora

---

## Anti-padrão

- ❌ Pular direto pra "vamos fazer feature X" sem mapear opportunity primeiro.
- ❌ Listar 1 solution por opportunity (geralmente há 2-4 caminhos válidos).
- ❌ Solutions vagas ("melhorar UX", "usar IA pra resolver tudo") — precisam ser concretas o suficiente pra virar experiment.
- ❌ Confundir Solution com Feature. Solution = direção; Feature = implementação.
- ❌ Score sem evidência. RICE precisa de Reach/Impact baseados em dado de jornada/JTBD/dor mapeada, não palpite.
- ❌ Trair as 4 decisões fundadoras de PRODUTO (Frota+UMC+Caixa; Comissões Configuráveis; Cliente 360°+CRM+Automações; Estoque com lacre/selo) — qualquer Solution que contradiga é vetada.
- ❌ Esquecer das marcações `[INFERÊNCIA — validar em onda 1]` — pré-entrevistas, tudo é hipótese forte mas não confirmada.
- ❌ **Marcar Confidence 5/5 baseado em "decisão fundadora canônica" — Confidence em RICE é evidência de mercado, não certeza do dono.** (auditoria 17/05) Confidence-dono virou nota lateral; Confidence-mercado é o que entra no score.
- ❌ Confundir decisão fundadora de PRODUTO (4 decisões Roldão 17/05/2026: Frota+UMC+Caixa, Comissões, Cliente 360°+CRM, Estoque com selo) com decisão fundadora de ENGENHARIA (D1-D6: Spec Kit, spec-as-source, nomenclatura híbrida, devcontainer, CODEOWNERS, dual tooling).

---

## Como esta árvore evolui

- **Onda 1 de entrevistas** (5 donos perfil B + 5 RTs Sandra + 5 atendentes Letícia) -> substituir `[INFERÊNCIA]` por citação literal; re-rankear scores; **mover Confidence-mercado de 3 pra 4-5 nas OPs que >= 60% das entrevistas confirmarem**. OPs marcadas "VALIDAR ANTES DE COMPROMETER" que não atingirem 60% movem pra MVP-2.
- **Experiments executados** -> Solutions validadas sobem; Solutions refutadas saem ou pivotam.
- **LEAP refutado no `assumption-map.md`** -> Opportunity dependente entra em revisão (ex: se F-1 falhar no spike F-F, todo MVP-1 vira "produto sem agentes" e Effort × 3).
- **Novo gap em `concorrentes.md`** -> considerar Opportunity nova (alvo: <= 1 por trimestre, manter foco).
- **MVP-1 Wave A entregue** -> re-ler árvore + re-priorizar Wave B com base em adoção real (não previsão).

---

## Saída esperada

- **1 Outcome principal:** 50 tenants pagantes × R$ 905 médio ponderado × churn <= 3% × economia >= R$ 14k/mês auto-reportada × CAC blended <= R$ 4.500 (V-15).
- **Mix-alvo:** A=10% × R$ 2.500 / B=55% × R$ 900 / C=25% × R$ 600 / D=10% × R$ 400.
- **Foundation (pré-MVP):** 8 itens F-A..F-H não-negociáveis nas semanas 0-6.
- **12 Opportunities** cobrindo **12/12 Big Jobs** (8 OPs originais + OP9 materializa BIG-03 + OP10 materializa BIG-06 + OP11/OP12 materializam dores universais órfãs Dor #11 + #12).
- **36 Solutions** distribuídas entre as 12 OPs (com premissas D-N/V-N/F-N/E-N + custo P/M/G + experiment cada).
- **MVP-1 em 2 Waves:** Wave A regulatória/sobrevivência (semanas 6-14) + Wave B valor comercial (semanas 14-22).
- **Top 3 MVP-1 (lock obrigatório):** #1 OP7 NFS-e (deadline regulatório), #2 OP2 Certificado, #3 OP10 Metrologia Legal + RBC.
- **Priorização RICE-adapted com Confidence dual-axis:** Confidence-dono = nota lateral; Confidence-mercado entra no score. Pré-onda 1, Confidence-mercado >= 3 só pra OPs com gap em `concorrentes.md` confirmado + dor universal mapeada.
- **Cobertura:** 4 dimensões (Desejabilidade × Viabilidade × Factibilidade × Ética) com 12 LEAPs priorizados acoplados aos experiments.
- **IDs de risco canônicos:** R-049..R-057 substituem rótulos informais "R-novo CRM-N", "R-novo C-N", "R-novo EST-N" em `riscos-mapeados.md`.

