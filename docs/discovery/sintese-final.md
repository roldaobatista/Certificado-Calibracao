# Discovery — Síntese final ⭐

> **Artefato Rodada 0** (agente + Roldão). **DESTRAVA TODAS AS OUTRAS RODADAS.** Conclusões da discovery em formato de DECISÃO.
>
> **Status:** 🟡 DRAFT v2 (17/05/2026, noite tarde) — preenchida com base na **validação documental** (4 buckets em `validacao-externa-documental.md`) + **mystery shopping documental** (`mystery-shopping-documental.md`) + **estudo monográfico Calibre.Software** (`estudo-calibre-software.md`). **NÃO ESTÁ FECHADA** — falta cliente piloto sob NDA + 3 cartas de intenção pra cravar definitiva. Cada seção marca nível de confiança e o que falta validar.

---

## Por que esta síntese existe (e por que está em DRAFT)

O Auditor 10 da 2ª auditoria de 10 agentes (17/05/2026) levantou que aceitar stack antes de fechar discovery é "founder is customer" virando real. Esta v1 corrige o sintoma — não pode estar VAZIA enquanto se discute MVP-1.

Roldão optou por **não fazer Onda 1 declarada** (proteção competitiva). A discovery foi mitigada via:
- 4 buckets de pesquisa documental independente (✅ concluído) — 13/20 dores confirmadas externamente
- Mystery shopping documental (✅ concluído) — Cali, Metroex, Calibre, FP2 aprofundados
- Estudo monográfico Calibre.Software (✅ concluído) — empresa-mãe identificada
- Cliente piloto sob NDA (⏳ quando aparecer oportunidade)

Esta síntese só fecha como definitiva quando os 3 últimos forem concluídos.

---

## 1. CLIENTE IDEAL (ICP)

**Status:** 🟡 SABEMOS PARCIAL — 4 perfis hipotetizados, perfil B (núcleo) validado documentalmente, perfis A/C/D pendentes de validação direta.

### Perfis (decisão fundadora 16/05/2026)

| Perfil | Descrição | Tamanho ICP | DAP estimada | Validação atual |
|---|---|---|---|---|
| **A** | Laboratório acreditado RBC (CGCRE) com escopo formal | 5-10% do ICP | R$ 1.500-3.000/mês | Validação parcial (Bucket D regulatório); falta DAP real |
| **B** ⭐ | Lab rastreável (não-acreditado), com clientes regulados ocasionais — **Roldão é deste perfil** | 20-30% do ICP | R$ 700-1.500/mês | LEAP V-2 ainda aberto; Bucket C confirma demanda |
| **C** | Lab em preparação pra acreditar (escada D→A) | ~30% do ICP | R$ 500-800/mês | Não validado (Bucket B silêncio) |
| **D** | Calibração comercial pura (sem rituais 17025) | Raro no ICP | R$ 300-500/mês | Não-cliente nuclear — módulos opcionais |

### Sinais de "ESTE é o ICP" (validados documentalmente)

- ✅ Mantém 3+ sistemas paralelos (Bling + Cali + Excel + WhatsApp) — Dor #01 confirmada
- ✅ Perde 30-50% das renovações por esquecimento — Dor #02 confirmada
- ✅ Sofre com NFS-e municipal (cutover 09/2026) — Dor #10 confirmada
- ✅ Atende cliente farma ocasionalmente (BPF RDC 658/972) — Dor #13 confirmada
- ✅ Tem ≥1 técnico de campo com UMC ou veículo dedicado — Dor #08 confirmada
- ✅ Conhece pressão regulatória ENIQ 2025-2026 — Dor #29 (nova) válida

### Sinais de "este NÃO é o ICP"

- Lab que não atende a clientes externos (calibração interna corporativa pura) — TOTVS/SIGAMNT atende melhor
- Empresa que cobra calibração avulsa sem rastreabilidade — produto vira overkill
- Lab de bancada-only sem campo nem UMC — anti-perfil de Roldão; testa halo founder

### Geografia (validação documental Bucket D)

- **Núcleo MVP-1:** SP + RS + MG + SC (eixo industrial onde Roldão opera)
- **TAM ICP convertível estimado:** 1.500-2.000 (não os 5.000 brutos)
- **Validar via LAI INMETRO/CGCRE:** número de RBC ativos por estado (lacuna estatística confirmada)

---

## 2. N MÓDULOS TOTAL

**Status:** 🟡 SABEMOS PARCIAL — 12 Big Jobs confirmados via discovery; lista total fluida.

### Big Jobs confirmados (de `jobs-to-be-done.md`)

1. **BIG-01** — Não perder informação entre sistemas
2. **BIG-02** — Emitir certificado RBC sem ansiedade
3. **BIG-03** — Trilha D→A (escada de acreditação)
4. **BIG-04** — Faturar sem dor (NFS-e municipal)
5. **BIG-05** — Técnico de campo trabalhar offline
6. **BIG-06** — Metrologia legal (selo INMETRO rastreável)
7. **BIG-07** — Cliente 360° (cadastro único, histórico, portal)
8. **BIG-08** — Frota + UMC + caixa do técnico
9. **BIG-09** — Comissões configuráveis
10. **BIG-10** — CRM (acompanhamento de cliente)
11. **BIG-11** — Automações (lembretes, fluxos)
12. **BIG-12** — Estoque com lacre/selo

### Domínios

- **Comercial:** BIG-07 (cliente 360°), BIG-10 (CRM), BIG-11 (automações)
- **Operação:** BIG-01 (não perder info), BIG-05 (mobile técnico), BIG-08 (frota+UMC)
- **Financeiro:** BIG-04 (NFS-e), BIG-09 (comissões), cobrança/inadimplência
- **Metrologia:** BIG-02 (certificado), BIG-03 (D→A), BIG-06 (metrologia legal)
- **Suporte/Plataforma:** RBAC, multi-tenant, audit trail, observabilidade

### Lacunas (vão sair com cliente piloto)

- Pode haver Big Jobs específicos a verticais (farma, automotivo) ainda não mapeados
- Manutenção preditiva (Dor #31 nova) pode virar BIG-13 condicional
- MSA/Gage R&R (Dor #32) pode virar add-on enterprise

---

## 3. PLANO DE FASEAMENTO

**Status:** ✅ SABEMOS — estruturado pós-auditoria 12 agentes em `opportunity-solution-tree.md`.

### Foundation (semanas 0-6, pré-MVP)
- F-A: multi-tenant + RLS + audit
- F-B: auth + RBAC + cadastros
- F-C: cliente master (BIG-07)
- F-D: mobile shell
- F-E: WhatsApp BSP
- F-F: spike F-1 (modelo 100% agentes)
- F-G: hooks + CI
- F-H: ADR-0001 stack ✅ candidata

### Wave A (semanas 6-14, núcleo regulatório)
- **OP7** NFS-e (deadline 01/09/2026 — não-negociável)
- **OP2** Certificado completo (INV-002)
- **OP10** Metrologia Legal + RBC (BIG-06)
- **OP3** Solutions 3.1+3.2 (app + caixa; frota TCO move pra MVP-2)
- Módulo Financeiro mínimo

### Wave B (semanas 14-22, valor comercial)
- OP1 Recalibração proativa (depende de OP2 + F-C + F-E)
- OP4 Comissões SIMPLIFICADA (1 fórmula no MVP-1; 7 outras MVP-2)
- OP5 Solution 5.1 Timeline 360°
- OP8 Solution 8.2 link WhatsApp
- OP9 Trilha D→A (BIG-03)
- OP11 Cobrança/inadimplência
- OP12 Painel do Dono

> Detalhe operacional em `opportunity-solution-tree.md`.

---

## 4. MVP-1 (PRIMEIRO MÓDULO EM PRODUÇÃO)

**Status:** ✅ SABEMOS PARCIAL — escopo estruturado, falta confirmar com cliente piloto.

### Tese central do MVP-1 (decisão fundadora)

> **Em 12 meses, antes do cutover NFS-e 01/09/2026 + janela ENIQ fechar (Dor #29 nova), entregar emissor NFS-e + cálculo de incerteza NIT-DICLA-030 rev. 15 + trilha de auditoria 17025 + recalibração proativa, capturando mercado em onda de pressão regulatória forçada.**

### Top 5 dores no MVP-1 (pós-validação documental)

1. **Dor #10 — NFS-e municipal cutover 09/2026** (validação 4 buckets) — Top 1
2. **Dor #02 — Esquecimento recalibração** — eixo primário de venda
3. **Dor #04 — Word/Excel cálculo incerteza** — pitch metrológico defensável
4. **Dor #01 — Cadastro duplicado 4-6x** — foundation
5. **Dor #05 — Status OS perguntado 10-30x/dia** — quick win

### Escopo mínimo (top 3 features)

1. **Cadastro único cliente + emissão de OS + certificado de calibração** (BIG-07 + BIG-02)
2. **Emissão NFS-e via BaaS pluggable (PlugNotas como 1ª impl)** (BIG-04 + ADR-0008)
3. **Lembrete de recalibração via WhatsApp BSP** (BIG-10 + BIG-11)

### Non-goals do MVP-1 (alinhado com ANTI-01..ANTI-11)

- Folha de pagamento / RH completo
- Pagamento direto com cartão (PCI-DSS escopo)
- BI sofisticado / dashboards customizáveis
- Mensageria interna entre técnicos
- Customização individual por tenant (CRÍTICO — ANTI-11)
- Hardware proprietário (somos software, não fabricante)
- 7 das 8 fórmulas de comissão (deixar 1, expandir MVP-2)
- Frota TCO completo (deixar caixa do técnico, frota move MVP-2)

### Estimativa de tempo até 1º deploy

- Foundation: 6 semanas
- Wave A: 8 semanas
- **Total até MVP-1 viável: 14 semanas (~3,5 meses)**
- Margem realista pós-LEAPs validados: 16-22 semanas (4-5,5 meses)

### Cliente piloto

- ✅ Roldão (founder is customer — já confirmado)
- ⏳ 1-2 clientes piloto sob NDA — pendente, oportunidade quando aparecer

---

## 5. MODELO DE NEGÓCIO

**Status:** 🟡 SABEMOS PARCIAL — modelo decidido, faixas de preço como hipótese.

### Modelo

- **SaaS multi-tenant** em Hostinger SP + Backblaze B2 EU + AWS KMS sa-east-1
- **Por que não on-premise:** mercado aceita SaaS (V-3 validada parcial); on-premise seria nicho premium futuro

### Pricing hipotético (LEAP V-2)

| Perfil | Faixa mensal | Setup |
|---|---|---|
| A | R$ 1.500-3.000 | R$ 0 (anti-padrão #25) |
| B | R$ 700-1.500 | R$ 0 |
| C | R$ 500-800 | R$ 0 |
| D | R$ 300-500 | R$ 0 |

**Princípios comerciais validados pelo Bucket A:**
- ❌ Sem cláusula de fidelidade abusiva (Dor #25 — concorrentes prendem 12 meses)
- ❌ Sem reajuste anual acima do IPCA (Dor #25)
- ✅ Pricing público transparente (vs setor opaco; só Conta Azul publica hoje — Bucket C)
- ✅ Trial gratuito de 30 dias (LEAP V-12 a validar)
- ✅ Transparência radical sobre integrações prontas vs roadmap (Dor #27 — anti-padrão concorrentes)

### Mercado

- **TAM bruto BR:** 5.000 (lab + assistência técnica)
- **TAM ICP convertível (A+B+C):** 1.500-2.000 (estimativa pós-auditoria)
- **SAM (núcleo SP+MG+RS+SC):** 600-1.000
- **SOM 12 meses (50 clientes pagantes):** meta operacional

### Canal de aquisição (validação parcial)

- **Primário:** indicação de cliente piloto + LinkedIn outbound pra RT/dono
- **Secundário:** inbound via SEO ("software calibração ISO 17025" + "NFS-e calibração 2026")
- **Terciário:** parceria com BaaS fiscal (PlugNotas tem rede de leads)

### CAC × LTV (LEAP V-15)

- **CAC blended target:** ≤ R$ 4.500
- **LTV target:** R$ 18-45k (mensalidade R$ 600-1.500 × 30 meses)
- **LTV/CAC:** ≥ 4:1 sustentável (3:1 mínimo)
- **Smoke test pago Meta+Google+LinkedIn pendente** (R$ 5k, 4 semanas)

---

## 6. STACK CANDIDATE

**Status:** 🟡 CANDIDATA — Django + Flutter + PostgreSQL, sujeita a 3 portões (ADR-0001 v2).

| Camada | Escolha |
|---|---|
| Linguagem principal | Python (backend) + Dart (mobile) |
| Framework backend | Django 5.x LTS + DRF |
| Framework frontend | Django Admin + Jazzmin + HTMX + Alpine.js + Tailwind |
| Mobile | Flutter 3.x + drift (SQLite ORM) + Riverpod |
| Banco principal | PostgreSQL 16+ com RLS |
| Cache/Filas | Redis 7 + Celery |
| Auth | django-allauth + django-otp (MFA) + SimpleJWT (mobile) |
| Modelo tenancy | Schema compartilhado + middleware tenant_id + RLS — **ADR-0002 rascunho** |
| LLM gateway | LiteLLM self-hosted (rede Docker isolada) |
| CI/CD | GitHub Actions → SSH → docker compose up |
| Provedor fiscal | PlugNotas (SDK Python) — pluggable via **ADR-0008** |
| Assinatura PDF | pyhanko (PAdES-LTV nativo, ICP-Brasil) |
| A3 (token físico) | Sempre cliente-side via Web PKI Lacuna — **ADR-0009** |
| Provedor bancário | A definir (Pluggy/Belvo/Asaas) |
| Observabilidade | OpenTelemetry → Grafana Cloud + Axiom + B2 (logs longos) |
| WORM | Backblaze B2 EU Central (Object Lock) |
| Crypto crítica | AWS KMS sa-east-1 + replica us-east-1 |
| IaC | Docker Compose + Ansible playbook |

### Critério de reversão pra abrir ADR-0001 reaberta

- LEAP F-1 falhar (agentes não dão conta de NestJS em escala) → disparar plano B (tech-lead consultivo R$ 8-15k/mês), NÃO reverter pra TS
- TAM > 5.000 tenants em 2028 → migrar schema-shared pra schema-per-tenant
- Offline Flutter inviável no F-D → revisar (não voltar pra RN)

---

## 7. EQUIPE OPERACIONAL

**Status:** 🟡 SABEMOS PARCIAL — gaps críticos identificados na auditoria.

### Roles confirmados

- **Roldão:** dono não-técnico, 1º cliente, decisor de produto. Founder is customer — R-001 score 12 pós-validação documental.
- **Claude Code + Codex CLI (agentes IA):** principais executores do código. LEAP F-1.

### Roles obrigatórios pendentes (gap pré-MVP-1)

- **RT do vendor com CREA + competência metrológica** (R-065 score 20 — gap crítico). Sem ele, cliente farma reprova due diligence técnica.
- **DPO (LGPD em larga escala)** — pode ser advogado especializado ou contratação fracionada
- **Advogado SaaS regulado** (R$ 8-15k pacote, R-042 score 20) — contrato vendor↔tenant + cláusula penal + DPA-modelo
- **Corretora de seguros** — RC profissional + cibernético (~R$ 200-600/mês)
- **Consultor RBC** (R$ 5-8k) — validar dossiê 17025 do software (F-12)
- **Contador especializado em SaaS** — ajustes fiscais ano 1
- **Signatário técnico de calibração (RBC NIT-DICLA-021)** — Roldão se habilitado OU contratar

### CS L1 (suporte ao tenant) — gap crítico

R-062 score 20 — sem suporte L1, churn 90 dias > 40%. LEAP F-18 a validar: bot + Roldão como fallback humano.

---

## 8. RISCOS RESIDUAIS APÓS DISCOVERY

**Status:** ✅ SABEMOS — 65 riscos catalogados em `riscos.md`.

### Mitigados na discovery (sai ou cai)

- **R-001 (founder is customer)** — score 20 → 12 pós-validação documental (4 buckets, 13/20 dores confirmadas externamente)
- **R-004 (TAM ridículo)** — TAM convertível 1.500-2.000 confirmado (Bucket D + V-1)
- **R-026 (confusão 3 AutoLab)** — padronizado em concorrentes.md

### Score 25 (críticos remanescentes — bloqueantes MVP-1)

- **R-027** — Prompt injection cliente final (ADR-0000 + hooks pendentes)
- **R-018** — Certificado sem cadeia rejeitado por CGCRE (INV-002 hook pendente)

### Score 20 (graves remanescentes)

- R-002 (Família 5 vaporware), R-005 (1 pessoa = anos), R-007 (retenção tríplice), R-016 (cutover NFS-e), R-035 (Visma compra Cali), R-042 (transferência risco vendor↔tenant), R-062 (CS L1 inexistente), R-065 (vendor sem RT)

### Lacunas conhecidas (Onda 1 / cliente piloto resolve)

- DAP real perfil A/B/C/D (LEAP V-2)
- Reach real Dor #15 comissões (suspeita halo founder)
- UMC específica em Dor #16 (suspeita halo founder)
- Aceitação "feito por IA com supervisão humana" (LEAP E-3)

---

## 9. CONCORRENTES — leitura pós-mystery shopping (17/05/2026)

**Status:** ✅ SABEMOS — 4 concorrentes diretos aprofundados em pesquisa documental sem expor projeto.

### Reordenação da ameaça competitiva (mudou após mystery shopping)

| Ranking | Concorrente | Por que é ameaça (ou não é tanto) |
|---|---|---|
| **#1 Metroex/ForLogic** | Mais maduro: Glassdoor 3,7/5 (56 reviews), ~100+ funcionários, 22 anos, cross-sell Qualiex+Qualitfy+Metroex, **API pública documentada** (único), **MSA + SPC + IATF 16949** (único — automotivo), +500 INMETRO, cases enterprise (Netzsch/Maersk/Dräger). Posicionamento: indústria + lab interno. |
| **#2 Cali** | 28 anos (maior tempo de casa), **homologação CERTI declarada** (único — diferencial técnico defensável), **Cali LAB Mobile com QR code offline** (descoberto no mystery shopping — bucket-c não tinha pego), base instalada longa (Metroquality 20 anos). Marketing fraco (posts comemorativos). Posicionamento: lab prestador RBC. |
| **#3 Calibre.Software** | **Player menor que esperado:** é uma das 5 frentes da Zara Falcão Processamento de Dados (Goiânia/GO, software house generalista, bootstrapped, 2-10 pessoas em 18 anos). Tráfego ~1.500 visitas/mês, base estimada 15-40 labs. Calculadora ROI quebrada (404). Docs técnicos só cobrem 2 de 6 módulos prometidos. **Conflito de marca** com Calibre e-book reader. **Reduzido de "principal ameaça conceitual" pra "player nicho".** |
| **#4 FP2 Tecnologia** | **Reclassificado: ADJACENTE, não concorrente direto** — atende lab de análises (UFSM, Samitec), não RBC puro. Tem NFS-e + ICP-Brasil A1/A3 + CNAB 240/400 + audit trail + multi-filial. **Vale como prova de viabilidade técnica** da stack que Aferê planeja. |

### 4 logos verídicos confirmados em RBC (alvos potenciais de mystery shopping futuro)

- **Suporty** — Goiânia (vizinha do fornecedor Calibre.Software)
- **ST Metrologia** — São José dos Campos/SP (hospitalar)
- **Metrominas** — Ipatinga/MG (detectores de gases)
- **ERJos** — não localizada em buscas públicas (pode estar inativa ou ter mudado nome)

### Achados que mudam estratégia

1. **Pricing público = ZERO em todos os 4.** Setor 100% venda consultiva. **Transparência de pricing pelo Aferê** vira diferencial defensável real, não cosmético.

2. **Self-service trial = ZERO em todos.** Todos exigem demo agendada com vendedor. Aferê com **trial self-service de 30 dias** seria pioneiro estrutural.

3. **App mobile iOS Metroex publicado mar/2024, sem ratings, EN-only (não localizado PT-BR).** **Janela competitiva real** pra Aferê entrar com mobile sólido em PT-BR antes de Metroex consolidar mobile.

4. **Reviews independentes em Capterra/B2B Stack/Reclame Aqui = ZERO** pros 4 concorrentes BR de calibração. Setor invisível em agregadores genéricos. **Aferê com prova social verificável** (NPS, métricas reais, comunidade pública) seria primeiro.

5. **Blog da Metrologia é propriedade ForLogic** (confirmado no footer) — não é blog neutro. Bucket B já havia identificado; mystery shopping confirma.

6. **NFS-e exclusividade FP2 (regional Santa Maria/RS)** — segunda passagem independente confirma o gap absoluto. **Dor #10 + Janela ENIQ (Dor #29) = vetor competitivo mais defensável do Aferê.**

7. **Cali tem homologação CERTI declarada** — único do levantamento. **Aferê precisa pensar contra-narrativa:** ou busca homologação CERTI (R-034 promovido de 4 → 12 já reflete isso, processo 18-36 meses), ou positioning "transparência radical + audit trail publicável" (Dor #22 nova) como prova alternativa.

8. **Concorrente mais perigoso REORDENADO:** era "Calibre conceitualmente mais alinhado" (proposta v1) → agora é **Metroex/ForLogic empresa estruturada**. Calibre.Software vira "anti-padrão a evitar" (marketing/calculadora abandonados, docs incompletas, time pequeno = produto em manutenção mais que evolução ativa).

---

## Recomendações pra Rodadas 1+

### Bloqueio imediato (Portão 1 ADR-0001 não fecha sem isso)

1. ⏳ Mystery shopping documental concluir (em andamento)
2. ⏳ Estudo Calibre.Software concluir (em andamento)
3. ⏳ Pacote E-4 (advogado + corretora + dossiê 17025) — R-042 score 20 obrigatório
4. ⏳ Contratar RT do vendor — R-065 score 20 obrigatório
5. ⏳ Cliente piloto sob NDA — quando aparecer oportunidade

### Pode rodar em paralelo (não bloqueia)

- Fechar 4 ADRs filhas (0002 multi-tenancy, 0007 domain layer, 0008 fiscal pluggable, 0009 A3) — Portão 2
- Atualizar `REGRAS-INEGOCIAVEIS.md` com INV-TENANT-004 + INV-AGENT-001
- Expandir anti-corrosion-layer com 9 portas
- Spike F-5 (cálculo incerteza + metrologista externo)

### Próximo módulo (Fase 2 pós-MVP-1)

- Wave B (recalibração proativa + comissões expandidas + portal cliente + cobrança + painel dono)
- Reavaliar síntese após 1º deploy do MVP-1

---

## Aprovação

- [ ] Auditor de Produto leu e aprovou — pendente
- [ ] Auditor de Segurança identificou riscos não cobertos — pendente
- [ ] Roldão leu e aprovou (decisão dele) — DRAFT em revisão
- [ ] Atualizou `painel-do-dono.md` com status "discovery parcialmente validada"
- [ ] Atualizou `documentos-do-projeto.md` com plano de faseamento real

---

## Critério pra fechar definitiva (sair de DRAFT)

A síntese só fecha como definitiva quando:

1. ✅ Validação documental concluída — 4 buckets
2. ✅ Mystery shopping documental concluído
3. ✅ Estudo monográfico Calibre.Software concluído
4. ⏳ 1-2 clientes piloto sob NDA confirmaram dores #15 (comissões) e UMC em #16
5. ⏳ R-001 cai pra ≤9 com evidência
6. ⏳ LEAPs críticos do `assumption-map.md` validados ou descartados (F-1, V-2, D-1, V-15, E-4)

---

## Histórico de revisões

| Data | Mudança | Quem |
|---|---|---|
| 2026-05-16 | Criação do template | Agente |
| 2026-05-17 (noite tarde) | DRAFT v1 preenchida com validação documental 4 buckets; R-001 rebaixado 20→12; 12 dores novas mapeadas; bloqueios pra fechamento explicitados | Claude Code + Roldão |
| 2026-05-17 (noite tarde +2h) | DRAFT v2 incorpora mystery shopping documental + estudo monográfico Calibre.Software. Nova seção 9 "CONCORRENTES — leitura pós-mystery shopping" com reordenação da ameaça: Metroex/ForLogic é #1, Calibre.Software é nicho (não startup), FP2 reclassificado como adjacente. | Claude Code + Roldão |
