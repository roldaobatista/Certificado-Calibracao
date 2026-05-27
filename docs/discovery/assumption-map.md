# Discovery — Assumption Mapping

> **Artefato Rodada 0 / Batch 2** (Auditor 6 v2 — NOVO). Framework David Bland (Testing Business Ideas). Separa premissas em 4 quadrantes × 2 níveis de confiança. Destaca **leap-of-faith** (premissas críticas + baixa confiança).
> **Atualizado:** 2026-05-17 — primeira versão DENSA pós-batch 2 do discovery (riscos R-001..R-057 consolidados, 14 personas, 12 Big Jobs, 109 JTBDs, 9 gaps defensáveis, 4 decisões fundadoras D1–D5, custo do status quo R$ 35–50k/mês mapeado).
> **Versão pré-entrevistas.** Nenhuma entrevista com cliente externo aconteceu ainda. Toda premissa marcada "Sabemos" se apoia em fonte secundária (relatório de mercado, regulação publicada, decisão fundadora documentada). LEAPs serão validados em `validacao-ativa.md` pelos experimentos propostos abaixo.
>
> **Versão pós-auditoria 12 agentes (17/05/2026 noite).** F-1 ganhou critérios de mortalidade explícitos + planos B/C/D. 3 LEAPs novos (V-15, F-17, F-18) + 1 LEAP de promoção (F-19, homologação CERTI). Van Westendorp N=30 cortado pra N=5-8 em entrevistas. **Total premissas: 61** (era 57; +V-15, +F-17, +F-18, +F-19). LEAPs priorizados: 15 (era 12).
>
> **Versão pós-validação externa documental (17/05/2026 noite tarde).** 4 buckets de pesquisa documental independentes validaram externamente 13 das 20 dores mapeadas. **V-8 (founder is customer)** sai de "Não sabemos LEAP" pra "Sabemos parcial" — evidência citada em `validacao-externa-documental.md`. **R-001 rebaixado de 20 → 12.** Dor nova #29 (janela ENIQ 2025-2026) adiciona pressão temporal de 12-18 meses. **Bandeiras amarelas** identificadas: V-2 (WTP perfil B) e D-13 (perfil B converte com BIG-03) continuam não validadas; dor #15 (comissões) e UMC específica em #16 continuam suspeitas de halo founder.

---

## Quadrantes

Cada premissa do projeto se encaixa em:

| Quadrante | Pergunta |
|---|---|
| **Desejabilidade** | As pessoas QUEREM isso? |
| **Viabilidade** | É bom NEGÓCIO? (sustenta receita?) |
| **Factibilidade** | É possível CONSTRUIR? (técnica) |
| **Ética** | É CERTO fazer isso? (legal, regulatório, social) |

× níveis de confiança:

| Confiança | Significa |
|---|---|
| **Sabemos** | Evidência sólida citada (dado externo, validação ativa, regulação publicada, decisão documentada) |
| **Não sabemos** | Especulação razoável; baixo custo de errar |
| **Não sabemos LEAP** | Especulação + crítica: se for falsa, mata o projeto ou um Big Job inteiro. PRECISA validar antes de comprometer recurso. |

---

## Matriz

### Desejabilidade — 16 premissas

| # | Premissa | Confiança | Evidência (se sabemos) / Experiment (se não) |
|---|---|---|---|
| D-1 | **Dono de PME de calibração perfil B (Roldão arquétipo) compra ERP que junta OS + calibração 17025 + NFS-e + financeiro num lugar só, em vez de manter Cali + Bling + planilha** | Não sabemos LEAP | Validar com 5 entrevistas Onda 1 (donos perfil B em SP/RS/MG) — perguntar "quais 3 sistemas você fechou hoje?" + mostrar mockup do orçamento → certificado → NFS-e em 1 fluxo |
| D-2 | **Sandra (RT da Qualidade, perfil A obrigatória) vê valor em sistema que junta gestão da qualidade 17025 + execução de calibração + portal de auditoria — concorrente NENHUM faz isso hoje** | Sabemos (parcial) | Gap confirmado em `concorrentes.md` §6 item 4 + 2 ondas de pesquisa (15+ players nacionais; nenhum cobre os 3). Falta validar se Sandra **pagaria** pela costura ou tolera 2 sistemas |
| D-3 | **Letícia (atendente) adota app que centraliza WhatsApp Business + abertura de chamado + agenda de técnico, em vez de pular entre 5 conversas paralelas** | Não sabemos LEAP | Smoke test: protótipo clicável de "inbox unificada com chamado" + 5 atendentes (rodada Onda 2). Métrica: 8/10 dizem "quero hoje" |
| D-4 | **Bruno/Bruna (técnico de campo) usa app mobile offline-first pra coletar leitura, foto e assinatura — em vez de papel + foto solta no WhatsApp pessoal** | Não sabemos | Validar em Onda 2 com 5 técnicos: instalar app de referência (Auvo, Field Control) e medir adoção 1 semana. Métrica: 70% completam OS digital sem ajuda |
| D-5 | **Eng. Marcos (metrologista signatário) confia em cálculo de incerteza GUM/JCGM 100 feito pelo sistema o suficiente pra assinar com CPF — em vez de recalcular em Excel** | Não sabemos LEAP | Spike: implementar cálculo de incerteza pra 3 grandezas (massa, pressão, temperatura) e fazer 3 metrologistas RBC compararem com Excel deles. Métrica: 100% concordam dentro da tolerância NIT-DICLA-021 |
| D-6 | **Cláudia (financeiro) troca planilha + Bling + extrato em 3 telas por painel único de conciliação + boleto/PIX + comissão calculada** | Não sabemos | Validar Onda 1 — mostrar mockup "fechei o mês em 1h" e perguntar quanto pagaria. Cláudia tem RAZÃO técnica forte de comprar (BIG-04 + BIG-09) |
| D-7 | **Rogério (vendedor) adota CRM de pipeline + comissão automática + bloqueio de desconto, em vez de planilha pessoal + caderno** | Não sabemos | Validar Onda 2. Risco: vendedor resiste à transparência de pipeline (medo de gerente ver) — entrevista precisa explorar |
| D-8 | **Carlos (motorista UMC) usa celular simples (R$ 600) com UI grande e poucos botões pra registrar viagem + nota de hospedagem + km — em vez de papel + WhatsApp** | Não sabemos LEAP | Teste de usabilidade com 3 motoristas reais (perfil A com UMC). Métrica: 80% completam "registrar gasto da viagem" sem treino prévio em < 2 min |
| D-9 | **Patrícia (gerente qualidade em cliente farma regulado) exige que o laboratório calibrador use sistema com trilha 21 CFR Part 11-equivalente + Anvisa RDC 658/2022** | Não sabemos | Entrevista 3 gerentes de qualidade farma BR. Métrica: 2/3 dizem "isso vira critério de habilitação de fornecedor" — vira diferencial pro tenant perfil A vender pra farma |
| D-10 | **João-Sênior (cliente final low-tech, açougueiro) ABRE PDF do certificado quando IPEM aparece pra fiscalizar — não usa portal, prefere WhatsApp com link direto** | Não sabemos | Validar Onda 2 com 5 clientes finais low-tech. Métrica: 0% logam em portal; 100% abrem link do WhatsApp |
| D-11 | **Roldão Sênior 65+ (dono PME veterano) compra software se UI tem letra grande, botão grande, voz "explica devagar" — não compra se UI parece "moderna demais"** | Não sabemos | Card sorting + 3 mockups de UI com 5 donos 60+. Métrica: identificar 3 padrões de UI que vendem e 3 que matam venda |
| D-12 | **Perfil A (acreditado RBC, 5–10% do ICP) paga 2–3× mais que perfil C porque calibração é risco regulatório de R$ 50k+ de multa** | Não sabemos LEAP | WTP test: landing page A vs C, tráfego pago R$ 1k, oferecer R$ 1.500/mês (A) e R$ 600/mês (C). Métrica: A converte ≥ 2× C |
| D-13 | **Perfil B (rastreável, 20–30% do ICP — Roldão é deste perfil) é o ICP de maior volume e converte com discurso "escada D→A sem trocar de sistema" (BIG-03)** | Não sabemos LEAP | Smoke test landing "trilha D→A automática" → métrica conversão ≥ 3% em tráfego pago R$ 1k |
| D-14 | **Perfil C (em preparação pra acreditar, ~30% do ICP) compra software que ENSINA o que falta pra acreditar — vê o produto como trilha didática** | Não sabemos | Entrevista 5 donos perfil C. Mostrar tela "você está em 60% dos requisitos 17025 — faltam X, Y, Z". Métrica: 3/5 dizem "isso me faz comprar" |
| D-15 | **Perfil D (calibração comercial pura, raro no ICP) NÃO é cliente nuclear — mas se aparecer, quer "OS simples + NFS-e" sem rituais 17025** | Sabemos (parcial) | `personas-detalhadas.md` Persona 1 §"Variações por perfil" + dado de mercado de assistência técnica BR. Mitigação: módulos opcionais (não obrigatório ativar 17025) |
| D-16 | **WhatsApp Business é canal OBRIGATÓRIO (não desejável) — cliente final BR comunica 90%+ por WhatsApp, sem integração o produto é DOA** | Sabemos | `personas-detalhadas.md` Persona 3 Letícia "tudo entra/sai pelo WhatsApp"; Persona 12 João-Sênior "manda por áudio fia"; `jornada-atual-sem-produto.md` §4 "WhatsApp é canal #1 de tudo". Validar técnica em factibilidade (F-4) |
| D-17 | **Portal do cliente final (BIG-07 novo) é desejado pelo end-customer perfil farma/automotivo — mas low-tech (açougue) ignora portal e prefere link direto via WhatsApp** | Sabemos (parcial) | Persona 8 João Eng. quer PDF rápido; Persona 12 João-Sênior não usa portal. Costura: portal pra farma + link público assinado pra low-tech. Validar conversão Onda 2 |

---

### Viabilidade — 15 premissas (era 14; +V-15)

| # | Premissa | Confiança | Evidência (se sabemos) / Experiment (se não) |
|---|---|---|---|
| V-1 | **TAM de laboratórios RBC + assistência técnica BR — 5.000 estimado bruto. TAM ICP convertível (perfis A+B com WTP confirmado) pode ser 1.500-2.000.** Se TAM convertível < 1.000, MVP-1 inteiro precisa repensar pricing. | Não sabemos LEAP | Pesquisa secundária: lista CGCRE de RBC acreditados (~600), IPEM/INMETRO assistência técnica com selo (~2.000–10.000), CNAE 7120-1 (Testes e Análises Técnicas) IBGE + filtro geográfico SP/MG/RS/SC. Custo P, prazo 2 semanas. (refinado pós-auditoria Aud-18 batch 3) |
| V-2 | **WTP do perfil B (ICP nuclear) está entre R$ 700–1.500/mês — não R$ 300 nem R$ 3.000** | Não sabemos LEAP | **Van Westendorp em 4 perguntas DENTRO das entrevistas Onda 1 (custo marginal zero), N=5-8 donos perfil B.** Aceitar como sinal direcional, não estatístico. Se Roldão quiser N=30 com rigor estatístico, contratar Provokers/MindMiners B2B (R$ 15-25k). Custo P (era M), prazo 1 mês. (corrigido pós-auditoria: N=30 a R$ 2k era irreal — N=30 B2B custa R$ 15-25k) |
| V-3 | **Setor de calibração BR aceita modelo SaaS multi-tenant (não exige on-premise/desktop)** | Sabemos (parcial) | Cali ainda é desktop-first; Metroex/Calibre são SaaS; Qualer (internacional) é SaaS. Sandra (RT) tem objeção de soberania de dados (R-028). Sabemos que aceita; falta confirmar **prêmio de preço** que pagam por on-premise |
| V-4 | **CAC < LTV/3: cobranças R$ 600–1.500/mês × LTV 30 meses = R$ 18–45k → CAC viável até R$ 6–15k via inbound + indicação** | Não sabemos LEAP | Smoke test pago R$ 5k: landing + Google Ads + LinkedIn → métrica CAC de visitante MQL e SQL. Custo M, prazo 1 mês |
| V-5 | **Aquisição: dentro de 18 meses, Visma (que comprou Conta Azul em 08/2025, US$ 300M) compra Cali ou Metroex e clona vertical fiscal/NFS-e (R-035 score 20)** | Sabemos (parcial) | Visma fez 140+ aquisições, 50 só em 2024; Conta Azul + Cali = BIG-01+BIG-04 em 18 meses. Cenário plausível. Mitigação: chegar a 50+ clientes antes da aquisição |
| V-6 | **Pricing por perfil funciona: A paga R$ 1.500–3.000/mês, B paga R$ 700–1.500/mês, C paga R$ 500–800/mês, D paga R$ 300–500/mês — sem cliente migrar pra baixo** | Não sabemos | Pricing page com 3 tiers públicos + escolha guiada por perfil declarado. Métrica: ≤ 10% downgrade no primeiro ano |
| V-7 | **Receita recorrente SaaS domina serviço pontual: 80%+ ARR vem de mensalidade, < 20% de implementação/treinamento** | Não sabemos | Validar em primeiros 10 clientes pagantes. Risco: implementação cara mata o modelo (vira consultoria disfarçada) |
| V-8 ⭐ ATUALIZADA | **Roldão (founder is customer, R-001 score 12 — era 20) consegue NÃO transformar o produto em "ERP do Roldão"** | Sabemos parcial | **Validação documental concluída 17/05/2026** (`validacao-externa-documental.md`): 4 buckets independentes confirmam 13/20 dores externamente, 0 refutadas. R-001 rebaixado de 20 → 12. **Bandeiras amarelas restantes:** dor #15 (comissões — ZERO concorrentes endereçam) e UMC específica em #16 continuam suspeitas de halo founder. Validar com mystery shopping + cliente piloto sob NDA. Família 5 mantida ativa. |
| V-9 | **Operação pode pagar Hostinger VPS KVM 4 + Backblaze B2 + AWS KMS + tokens IA + ferramentas dev com ≤ R$ 3k/mês em custo direto até 50 clientes pagantes** | Sabemos (parcial) | Hostinger VPS KVM 4 SP: R$ 200/mês; B2 storage: R$ 50–200/mês; AWS KMS: R$ 50/mês; tokens IA (R-010 já tem hard cap R$ 50/dia × tenant). Falta dimensionar pra 50 tenants |
| V-10 | **Custo de token de IA não estoura: Hard cap R$ 50/dia × tenant + circuit breaker em ADR-0000 mantém margem bruta SaaS típica (≥ 70%)** | Sabemos (parcial) | R-010 já tem mitigação documentada. Falta executar circuit breaker. Sabemos parcial; não-LEAP |
| V-11 | **Concorrente nacional (Cali) NÃO lança fiscal NFS-e em < 18 meses** (R-019 score 12) | Não sabemos | Monitorar release notes Cali + mystery shopping trimestral. Custo P |
| V-12 | **Modelo "1 mês grátis + R$ 500–1.000 entrada" gera conversão ≥ 30% trial → pagante** | Não sabemos | Smoke test: landing + trial 30 dias × 20 prospects. Métrica: 6/20 = 30%. Custo M, prazo 2 meses |
| V-13 | **Mercado regulado farma (Patrícia, persona 11) paga ADD-ON 21 CFR Part 11-equivalente + RDC 658 + RDC 786 a R$ 1.000–3.000/mês extra** | Não sabemos | Entrevista 3 gerentes farma BR. Custo P |
| V-14 ⭐ ATUALIZADA 2026-05-27 | **Existem ao menos 200 prospects qualificados no ICP perfil A/B em MT+MS+GO+DF (Centro-Oeste onde Roldão opera, cruzando fronteira para estados vizinhos quando atende cliente) — não precisa mercado nacional pra primeiros 50 clientes. SP+RS+MG+SC fica como alvo secundário sem peso de prioridade.** | Não sabemos | Lista CGCRE + filtros geográficos Centro-Oeste. Custo P. **Correção 2026-05-27:** geografia anterior (SP+RS+MG+SC) era halo founder herdado errado — Roldão opera em MT, não Sudeste. |
| V-15 ⭐ NOVO | **CAC blended ≤ R$ 4.500 nos primeiros 50 tenants** — sub-itens por canal: inbound R$ 2k, indicação R$ 500, outbound R$ 8k (média ponderada). Se CAC > R$ 6k, LTV/CAC quebra abaixo de 3:1 e modelo SaaS sangra. | Não sabemos LEAP | Smoke test pago Meta Ads + Google Ads + LinkedIn por 4 semanas, R$ 5k total. Métrica: CAC blended ≤ R$ 4.500. Custo M, prazo 1 mês | (origem: Aud-21 batch 3 — 17/05/2026)

---

### Factibilidade — 19 premissas (era 16; +F-17, F-18, F-19)

| # | Premissa | Confiança | Evidência (se sabemos) / Experiment (se não) |
|---|---|---|---|
| F-1 | **Modelo 100% agentes funciona em ERP regulado** — PREMISSA MÃE (LEAP CRÍTICO #1). Ver detalhamento expandido com gates de sucesso, kill switches e planos B/C/D abaixo da matriz (seção "F-1 detalhado"). | Não sabemos LEAP CRÍTICO | Spike controlado em BIG-12 Estoque (RECORTADO — SEM mobile, mobile é F-10 separado), 4 semanas, custo G (R$ 5-10k tokens). Ver seção "F-1 detalhado" pra critérios mortalidade completos. |
| F-2 | **Stack escolhida aguenta multi-tenant em Hostinger VPS KVM 4 SP/BR (4 vCPU, 8GB RAM) com 50 tenants ativos sem degradação de performance** | Não sabemos LEAP | Spike `spikes-tecnicos/multi-tenant.md`: provisionar VPS + RLS PostgreSQL + carga sintética 50 tenants × 10 usuários simultâneos. Métrica: p95 < 500ms. Custo M, prazo 2 semanas |
| F-3 | **NF-e/NFS-e multi-município (15+ prefeituras + Padrão Nacional CGSN 189/2026) funciona via BaaS único (Focus/PlugNotas/TecnoSpeed) com ≥ 95% das prefeituras dos primeiros 50 clientes** | Não sabemos LEAP | Spike `spikes-tecnicos/nfe-municipio-proprio.md`: lista 15 municípios prioritários × 3 BaaS, demo de cada, custo por NFS-e. Métrica: 1 BaaS cobre ≥ 12/15. Custo M, prazo 1 mês |
| F-4 | **WhatsApp Business API (Meta Cloud API oficial OU 360dialog/Z-API) integra com inbox unificada do produto sem violar termos da Meta e sem custo proibitivo (≤ R$ 0,50/conversa)** | Não sabemos | Spike WhatsApp: aprovar template Meta + enviar 100 mensagens × 3 templates. Métrica: aprovação Meta ≤ 7 dias; custo médio ≤ R$ 0,30. Custo M, prazo 3 semanas |
| F-5 | **Cálculo de incerteza GUM/JCGM 100 + NIT-DICLA-016/019/021 + WELMEC 7.2 + OIML D 31 é validável por dossiê interno (cláusula 7.11 ISO 17025) + 1 metrologista externo + 3 procedimentos-modelo (massa, pressão, temperatura)** | Não sabemos LEAP | Spike metrologia: implementar 3 procedimentos × validar com Eng. Marcos persona-equivalente (pago R$ 300/h × 20h). Métrica: validação assinada + dossiê de validação aprovado. Custo G, prazo 6 semanas |
| F-6 | **Hooks bloqueantes INV-001 a INV-016 (cadeia rastreabilidade, NC trava emissão, lacre obrigatório, WCAG, signatário humano, etc.) funcionam sem matar produtividade do agente: < 5% das ações são bloqueadas indevidamente** | Não sabemos | Spike: rodar agente em 1 semana de tarefas reais com todos os hooks ativos. Métrica: ≤ 5% falsos-positivos; ≤ 10% tempo de espera adicional. Custo P, prazo 1 semana |
| F-7 | **Operação dual Claude Code + Codex CLI sobre AGENTS.md canônico (D6/dual-tooling) não descamba em divergência: 2 agentes produzem código consistente em mesma branch** | Não sabemos LEAP | Spike: 2 agentes em paralelo executam 5 tarefas equivalentes (1 cada) numa mesma branch. Métrica: 0 conflitos não-triviais; padrão de código consistente. Custo P, prazo 2 semanas |
| F-8 | **Devcontainer (D4) + CODEOWNERS (D5) + Spec Kit (D1) + spec-as-source (D2) são suficientes pra qualidade — não precisa adicionar code review humano nem CI complexo** | Não sabemos | Avaliar em 90 dias: bugs em produção / bugs prevenidos. Métrica: ≤ 2 bugs críticos/mês após primeiros 10 clientes |
| F-9 | **Bus factor 1 — Roldão único humano — é mitigável com runbook + procurador técnico em cartório + cofre digital + sucessor treinado (R-029 score 15)** | Não sabemos | Materializar runbook continuidade + nomear procurador + treinar 1 sucessor em `painel-do-dono.md`. Custo M, prazo 2 meses |
| F-10 | **App mobile Android+iOS pra técnico/motorista é factível com PWA + Capacitor (ou Flutter) + offline-first (IndexedDB/SQLite local) — sem time mobile dedicado** | Não sabemos LEAP | Spike mobile: protótipo OS offline + sync conflict resolution em 3 semanas. Métrica: 100 OS criadas offline + sync sem perda. Custo G, prazo 3 semanas |
| F-11 | **Spec Kit (D1) + spec-as-source (D2) aguentam N specs (12 Big Jobs × N JTBDs × N regras) sem virar caos: cada spec ≤ 200 linhas + índice navegável + versionado** | Não sabemos | Stress test: escrever 30 specs Big Job e medir. Métrica: tempo médio de "encontrar regra X" ≤ 2 min |
| F-12 | **Auditoria 17025 do próprio software (dossiê de validação cláusula 7.11) é viável internamente — não exige consultoria externa de R$ 50k+** | Não sabemos | Spike: rascunhar dossiê (template) + validar com 1 consultor RBC (R$ 5k). Métrica: consultor diz "passa numa auditoria Cgcre". Custo M, prazo 6 semanas |
| F-13 | **Integração bancária BR (boleto registrado + PIX QR + conciliação CNAB 240/400) é factível via BaaS (Iugu, Asaas, Cora, Stripe BR) — sem certificação Bacen direta** | Sabemos (parcial) | Iugu/Asaas/Cora atendem PME serviços; CNAB padronizado. Sabemos parcial; falta validar custo por transação |
| F-14 | **Spike de 4 semanas em 1 módulo (F-1) prova ou refuta o modelo agente sem queimar > R$ 10k em custos diretos (tokens + cloud + ferramentas)** | Sabemos (parcial) | Hard cap R$ 50/dia × 28 dias = R$ 1.400 tokens + R$ 1k cloud + R$ 2k ferramentas = ~R$ 5k. Sabemos viável |
| F-15 | **Assinatura digital ICP-Brasil (A1/A3) integra no PDF do certificado sem dor (via API LACUNA/BRy ou stack equivalente)** | Não sabemos | Spike: assinar 10 PDFs com certificado A1 do Roldão. Métrica: 10/10 válidos no Adobe Reader. Custo P, prazo 1 semana |
| F-16 | **Migração de dados de Cali/Bling/Planilha pra Aferê é factível em ≤ 8h de onboarding por cliente — não vira consultoria de R$ 20k+** | Não sabemos | Spike: importador genérico Cali (export XML/Access) + Bling (API) + planilha (CSV template). Métrica: 8/10 clientes onboarding ≤ 8h. Custo G, prazo 4 semanas |
| F-17 ⭐ NOVO | **Onboarding de tenant novo ≤ 8h até 1ª NFS-e real emitida** — sem isso, área que MORRE é receita unitária: onboarding > 40h vira consultoria escondida e mata margem SaaS. | Não sabemos LEAP | Ride-along com piloto interno (Roldão), cronômetro do "criou conta" até "emitiu NFS-e válida". Métrica: ≤ 8h total. Custo P, prazo 2 semanas | (origem: Aud-21 batch 3 — 17/05/2026)
| F-18 ⭐ NOVO | **CS L1 (suporte ao tenant) cabe em modelo 100% agentes — bot + Roldão como fallback humano** — sem isso, churn dispara mês 2 e modelo SaaS sangra. | Não sabemos LEAP | Bot mock (chatbot com FAQ + escalonamento) + 10 simulações de ticket reais com Roldão como árbitro. Métrica: bot resolve ≥ 70% sem intervenção humana. Custo M, prazo 3 semanas | (origem: Aud-21 batch 3 — 17/05/2026)
| F-19 ⭐ NOVO | **Homologação CERTI/INMETRO obtida em ≤ 36 meses** — sem isso, perdemos diferencial vs Cali (que tem) em concorrências de cliente regulado/grande. Processo leva 18-36 meses e exige iniciar no ano 1. | Não sabemos LEAP | Iniciar processo de homologação ainda no ano 1 (paralelo ao MVP-1). Custo G (R$ 30-80k em consultoria + testes), prazo 18-36 meses. **R-034 elevado de score 4 → 12 nos riscos.** | (origem: promoção de R-034 pós-auditoria 12 agentes batch 3)

---

### Ética — 10 premissas

| # | Premissa | Confiança | Evidência (se sabemos) / Experiment (se não) |
|---|---|---|---|
| E-1 | **LGPD permite IA processar PII financeiro de cliente (boletos, extrato bancário, conciliação) — desde que com base legal "execução de contrato" + DPO + DPIA documentada** | Não sabemos LEAP | Consulta jurídica especializada LGPD + Anthropic DPA. Custo M (R$ 3–5k), prazo 3 semanas. Mitigação parcial em R-028 (DPA + opt-out por tenant; roadmap modelo BR) |
| E-2 | **Certificado regulado emitido por sistema mantido por IA é juridicamente OK se: (a) signatário humano cl. 6.2 ISO 17025 assina com CPF; (b) NIT-DICLA-021 sobre RT está atendida; (c) dossiê de validação 7.11 do software existe** | Sabemos (parcial) | NIT-DICLA-021 + cl. 6.2 17025 são claros sobre signatário humano. Falta validar percepção de auditor Cgcre real: "vocês usam IA no backoffice — isso compromete acreditação?". Entrevista 2 auditores Cgcre + 1 consultor RBC. Custo P, prazo 3 semanas |
| E-3 | **Cliente (tenant) aceita texto contratual + DPA "este sistema é mantido por IA com supervisão humana de Roldão (responsável técnico)" — não vira deal-breaker em > 20% das vendas** | Não sabemos LEAP | A/B test em landing: "feito por humano" vs "feito por humano + IA com supervisão". Métrica: conversão A/B sem queda > 30%. Custo P, prazo 1 mês |
| E-4 | **Transferência de risco vendor↔tenant é tratável com pacote pré-MVP: contrato com limitação de responsabilidade + seguro RC profissional + seguro cibernético + DPA-modelo + dossiê de validação 17025 (R-042 score 20 CRÍTICO)** | Não sabemos LEAP | Pré-requisito MVP-1: advogado especializado em SaaS regulado (R$ 8–15k) + corretora seguros RC profissional + cyber (orçamento R$ 200–600/mês). Custo G, prazo 2 meses |
| E-5 | **Soberania de dados é resolvível: dados brasileiros ficam em Hostinger SP/BR; só prompts/tokens vão pra Anthropic EUA com DPA (R-028 score 16)** | Sabemos (parcial) | ADR-0000 já documenta DPA Anthropic + opt-out tenant + roadmap modelo BR (Maritaca/Sabiá). Falta executar opt-out por tenant. Premissa intermediária — não LEAP |
| E-6 | **Sigilo entre tenants é garantido via RLS PostgreSQL + INV-TENANT-001 + drill mensal (R-003 score 15)** | Sabemos (parcial) | Mitigação documentada. Falta executar drill + audit trail. Premissa intermediária |
| E-7 | **Sigilo do cliente final do tenant no portal (BIG-07) é defensável: cada cliente final vê SÓ seus próprios certificados; ataque cross-customer no portal é prevenido por escopo de token JWT por end-customer + auditoria de acesso** | Não sabemos | Spike segurança: pentest do portal por consultor terceiro (R$ 8–15k). Métrica: 0 falhas críticas. Custo M, prazo 1 mês |
| E-8 | **Vínculo trabalhista do técnico de campo (CLT vs PJ) é viável no modelo do tenant — sistema NÃO pode forçar relação trabalhista do tenant nem criar dependência que vire vínculo de subordinação reverso** | Não sabemos | Consulta trabalhista: revisar workflow técnico de campo (geo-tracking, agenda, comissão) à luz de Reforma Trabalhista 2017 + Lei 14.297/2022 (motorista app). Custo P, prazo 3 semanas |
| E-9 | **Fraude regulatória do tenant (R-039: tenant declara perfil A sem ter acreditação Cgcre real) é prevenível com upgrade-A bloqueado por prova documental + revisão automática portal Cgcre — sem Roldão (vendor) responder solidariamente** | Sabemos (parcial) | INV-015 documenta bloqueio. Falta validar com advogado se mitigação é juridicamente suficiente (revisar contrato/cláusula penal). Custo P, prazo 2 semanas |
| E-10 | **Acessibilidade WCAG 2.1 AA + PDF/UA é OBRIGATÓRIA — não negociável (Lei 13.146/2015 art. 63 + Lei 14.133/2021 licitação + R-048 score 12)** | Sabemos | INV-016 absoluta. axe-core em CI + revisão manual. Sem experiment — execução obrigatória |

---

## F-1 detalhado — critérios de mortalidade explícitos

> Pós-auditoria 12 agentes (17/05/2026 noite). F-1 (modelo 100% agentes) é a PREMISSA MÃE — se falsa, projeto inteiro precisa repensar. Auditoria exigiu critérios objetivos e antecipados de "quando matar a hipótese".

### Experiment
Spike controlado em **BIG-12 Estoque** (RECORTADO — SEM mobile; mobile vira spike próprio em F-10), 4 semanas, custo G (R$ 5-10k em tokens + cloud).

### Gates de sucesso (todos precisam bater pra F-1 ser CONFIRMADO)

**Funcionais:**
- 50 instrumentos cadastrados no módulo Estoque com cadeia de rastreabilidade
- 50 selos INMETRO emitidos com rastreio individual (número de série único)
- Hook bloqueante de "selo em equipamento errado" funciona 100% (zero falso-negativo em 20 testes adversariais)
- 30 transferências em 2 etapas (almoxarife → técnico → cliente) sem perda
- Drill multi-tenant com 3 tenants paralelos: 0 vazamento entre tenants

**Não-funcionais (qualidade do processo de agente):**
- Tempo de iteração mediana ≤ 45 min, p90 ≤ 2h. **Se p90 > 4h, vira LEAP-balança (precisa decidir).**
- Custo de tokens ≤ R$ 1.500 no spike total (hard cap R$ 50/dia × 28 dias = R$ 1.400 + 100 de folga)
- Roldão intervém em código manualmente ≤ 2 vezes por semana
- 0 `push --force`, 0 hook desligado, 0 `--no-verify`
- Cobertura de testes ≥ 60% no módulo
- 0 SEV-1 em homologação após 7 dias de uso real pelo Roldão

### Kill switches (sinais antecipados de fracasso)
Se QUALQUER um dos 10 abaixo acontecer, parar o spike e reavaliar F-1:

1. Roldão LÊ código pra desbloquear agente > 2× em 1 semana
2. Bug recorrente sem solução em 3 tentativas seguidas do agente
3. Drift de spec (spec virou "spec-as-suggestion") em > 10% dos commits
4. Custo de tokens > R$ 70/dia em 3 dias consecutivos
5. p90 > 4h por feature pequena
6. Conflito Claude × Codex no mesmo arquivo > 2× em 1 semana
7. Hook bloqueia > 15% das ações do agente (falso-positivo mata produtividade)
8. Roldão não consegue VERIFICAR sozinho se a feature está certa
9. Multi-tenant drill falha (qualquer vazamento)
10. **Gate dia 14:** "se eu parasse hoje, esse módulo entrega em ≤ 4 semanas extras?" — se resposta for "mais de 4 semanas", abortar

### Planos B/C/D (se F-1 falhar)

- **Plano B (preferido):** Tech-lead consultivo part-time 10h/semana, R$ 8-15k/mês. Preserva 70% da economia do modelo 100% agentes — agentes continuam fazendo o grosso, humano só revisa decisão técnica e desbloqueia.
- **Plano C (rejeitado):** Migrar pra low-code (Bubble, Retool, Adalo). **NÃO atende ISO 17025 cláusula 7.11** (dossiê de validação de software). Mantido só como referência.
- **Plano D:** Pivotar de ERP completo pra **gestor de qualidade 17025 puro** (só BIG-02). Escopo menor, menos LEAPs, viável com modelo mais conservador.

---

## Leap-of-Faith priorizado — 15 LEAPs (era 12; +V-15, F-17, F-18)

> Ranqueados por severidade (combinação: probabilidade-de-ser-falsa × impacto-se-falsa × proximidade-na-decisão). Validar TODOS antes de comprometer recurso significativo em MVP-1.

| Rank | LEAP | Área do produto que MORRE se falsa | Experiment | Custo | Prazo |
|---|---|---|---|---|---|
| **#1** | **F-1 — Modelo 100% agentes entrega ERP completo em ≤ 24 meses sem dev humano** | **PROJETO INTEIRO.** Sem isso, Roldão precisa contratar 3–5 devs e o modelo deixa de existir. | Spike 4 semanas em 1 módulo (BIG-12 Estoque) — entregar em produção com hooks + testes + dossiê. Métrica: módulo funcional, ≤ R$ 10k gastos, ≤ 24 dias úteis | **G** | 1 mês |
| **#2** | **D-1 — Donos perfil B compram ERP unificado em vez de manter 3–5 sistemas** | **Desejabilidade central.** Sem isso, BIG-01 (não perder informação) não vende — vira só "calibração 17025" e perde 80% do TAM. | 5 entrevistas Onda 1 + smoke test landing "1 sistema em vez de 3" + tráfego pago R$ 1k. Conversão ≥ 2% | M | 1 mês |
| **#3** | **V-1 — TAM ICP A/B/C ≥ 5.000 empresas BR com WTP ≥ R$ 600/mês** | **Viabilidade.** Se TAM real é < 1.000 empresas (R-004 score 15), ARR teto é R$ 7M e modelo SaaS não fecha. | Pesquisa secundária CGCRE + IBGE CNAE 7120 + mystery shopping Cali/Metroex pra estimar base instalada. Quantificar ≥ 5k em ICP geográfico SP+MG+RS+SC | P | 2 semanas |
| **#4** | **V-2 — WTP perfil B = R$ 700–1.500/mês (não R$ 300 nem R$ 3.000)** | **Pricing.** Se WTP < R$ 500, modelo SaaS sangra (CAC > LTV). Se > R$ 2k, mercado se restringe a perfil A enterprise (Cali domina). | Van Westendorp + WTP test pago em 10 donos perfil B. R$ 200 incentivo × 10 = R$ 2k | M | 1 mês |
| **#5** | **E-4 — Transferência risco vendor↔tenant tratável com contrato + seguro RC + dossiê 17025 + DPA (R-042 score 20)** | **Exposição jurídica do Roldão.** Sem isso, cada bug do sistema pode tirar acreditação do tenant E processar o Roldão solidariamente. Mata a empresa. | Advogado SaaS regulado (R$ 8–15k) + corretora seguros RC profissional + cyber. Pré-requisito MVP-1 | G | 2 meses |
| **#6** | **F-5 — Cálculo incerteza GUM + NIT-DICLA-016/019/021 + WELMEC 7.2 + OIML D 31 validável internamente** | **BIG-02 e BIG-06 (acreditação + Metrologia Legal).** Sem cálculo confiável, signatário não assina → produto vira gestor de papel sem o coração técnico. | Spike: 3 procedimentos (massa, pressão, temperatura) + validação com metrologista externo (R$ 6k) + dossiê | G | 6 semanas |
| **#7** | **D-5 — Metrologista signatário CONFIA no cálculo da máquina pra assinar com CPF** | **BIG-02 viabilidade humana.** Mesmo cálculo correto (F-5), se Marcos recalcula em Excel sempre, o produto não economiza o trabalho dele e BIG-02 não vende. | 3 metrologistas RBC comparam cálculo Aferê × Excel deles. Métrica: 3/3 concordam dentro tolerância NIT-DICLA-021 + dizem "eu assinaria" | M | 1 mês |
| **#8** | **E-1 — LGPD permite IA processar PII financeiro com base legal + DPO + DPIA** | **BIG-04 + BIG-09 (financeiro + comissões).** Sem isso, IA não toca em extrato bancário/boleto e produto perde 40% do valor de Cláudia (financeiro). | Consulta jurídica LGPD especializada + Anthropic DPA review (R$ 3–5k) | M | 3 semanas |
| ~~**#9**~~ ⭐ SAIU DO LEAP | ~~**V-8 — Roldão não transforma produto em "ERP do Roldão" (founder is customer, R-001 score 20)**~~ | **Generalização.** | **Validação documental 17/05/2026 confirmou 13/20 dores externamente (0 refutadas). V-8 saiu de LEAP pra "sabemos parcial"; R-001 rebaixado de 20 → 12. Bandeiras amarelas restantes (#15 comissões, UMC específica em #16) ficam pra mystery shopping + cliente piloto sob NDA.** Ver `validacao-externa-documental.md`. | — | **VALIDADO PARCIAL** |
| **#10** | **F-7 — Dual tooling Claude Code + Codex CLI sobre AGENTS.md canônico não diverge (D6)** | **Velocidade de entrega.** Se 2 agentes produzem código inconsistente, Roldão vira mediador 24/7 e velocidade colapsa. | 2 agentes em paralelo × 5 tarefas equivalentes × medir conflitos | P | 2 semanas |
| **#11** | **F-2 — Stack aguenta 50 tenants multi-tenant em Hostinger VPS KVM 4 SP** | **Hospedagem.** Se não aguenta, precisa migrar pra cloud premium (AWS/GCP) e custo explode 5×. | Spike multi-tenant: carga sintética 50 tenants × 10 users simultâneos. p95 < 500ms | M | 2 semanas |
| **#12** | **F-10 — App mobile offline-first viável sem time mobile dedicado (PWA + Capacitor ou Flutter)** | **BIG-05 + BIG-08.** Sem mobile offline, técnico/motorista não usa e dado de campo continua em papel/WhatsApp pessoal. | Spike mobile: protótipo OS offline + sync 3 semanas. 100 OS criadas offline + sync sem perda | G | 3 semanas |
| **#13** ⭐ NOVO | **V-15 — CAC blended ≤ R$ 4.500 nos primeiros 50 tenants** | **Aquisição inteira.** Se CAC > R$ 6k, LTV/CAC < 3:1, modelo SaaS sangra. | Smoke test pago Meta+Google+LinkedIn 4 semanas R$ 5k | M | 1 mês |
| **#14** ⭐ NOVO | **F-17 — Onboarding tenant novo ≤ 8h até 1ª NFS-e real emitida** | **Receita unitária.** Onboarding > 40h vira consultoria escondida e mata margem SaaS. | Ride-along com piloto interno (Roldão), cronômetro | P | 2 semanas |
| **#15** ⭐ NOVO | **F-18 — CS L1 cabe em modelo 100% agentes (bot + Roldão fallback)** | **Churn.** Sem CS L1, 1º cliente abre ticket sexta 22h, ninguém responde, churna mês 2. | Bot mock + 10 simulações de ticket com Roldão como árbitro | M | 3 semanas |

> **Top 5 pós-auditoria 12 agentes (17/05/2026 noite)** (a serem rodados em paralelo na semana 1 da Rodada 1):
> 1. **F-1 (modelo agentes)** — spike 4 semanas em BIG-12 estoque, **agora com critérios de mortalidade explícitos** (10 kill switches, 6 gates, planos B/C/D) — ver seção "F-1 detalhado"
> 2. **D-1 (compra unificada)** — 5 entrevistas + landing
> 3. **V-1 (TAM real)** — pesquisa CGCRE/IBGE, agora com **TAM convertível 1.500-2.000** (era estimado 5.000 bruto)
> 4. **V-2 (WTP)** — Van Westendorp **N=5-8 dentro das entrevistas Onda 1** (cortado de N=30 pago — N=30 B2B custa R$ 15-25k, não R$ 2k)
> 5. **E-4 (contrato + seguro)** — advogado + corretora
>
> **Top 8 pós-auditoria** (adiciona aos Top 5 acima):
> 6. **F-5 (cálculo incerteza)** — spike 3 procedimentos + metrologista externo
> 7. **F-17 (onboarding ≤ 8h)** — ride-along piloto interno (NOVO)
> 8. **V-15 (CAC blended)** — smoke test pago Meta/Google/LinkedIn (NOVO)

---

## Como esta lista evolui

- Premissa nova surge → adicionar com nível de confiança.
- Experiment dá resultado → mover premissa de "não sabemos" pra "sabemos" (com evidência citada) ou descartar.
- Premissa virada falsa → atualizar `riscos.md` (criar R-NNN novo se não existir) + ajustar `sintese-final.md` + revisar Big Job afetado.
- Premissa "sabemos parcial" → quando evidência adicional fechar a lacuna, virar "sabemos".
- LEAP validado → sai da seção LEAP, mas FICA na matriz com evidência.

---

## Saída esperada

- Matriz completa preenchida pós-onda 1 de entrevistas (5 donos perfil B + 5 RT Sandra)
- Top 12 leap-of-faith priorizados pra experimento (já listados acima)
- Validação de TODOS leap-of-faith antes da `sintese-final.md` travar MVP-1
- Pacote E-4 (contrato + seguro + dossiê) executado ANTES de qualquer cliente externo pagar
