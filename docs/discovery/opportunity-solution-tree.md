# Discovery — Opportunity Solution Tree (OST)

> **Artefato Rodada 0 / Batch 2** (Auditor 6 v2 — NOVO). Framework Teresa Torres (Continuous Discovery Habits). Hierarquia outcome → opportunities → solutions → experiments. Sem isso, dores viram lista plana sem prioridade clara.
>
> **Atualizado:** 2026-05-17 — primeira versão DENSA pós-batch 2 do discovery. Cruza `jobs-to-be-done.md` (12 Big Jobs + ~109 JTBDs), `dores-mapeadas.md` (20 dores ranqueadas), `assumption-map.md` (57 premissas, 12 LEAPs), `personas-detalhadas.md` (14 personas), `dominio-de-negocio.md` (4 decisões fundadoras canônicas) e `concorrentes.md` (9 gaps defensáveis).
>
> **Versão pré-entrevistas.** Nenhuma entrevista com cliente externo aconteceu ainda. Toda Opportunity está ancorada em evidência interna (jornada, JTBD, decisão fundadora) + marcação `[INFERÊNCIA — validar em onda 1]` quando os números (Reach/Impact/WTP) são palpite forte mas não confirmado. **Solutions serão re-priorizadas após onda 1 de entrevistas.**

---

## Estrutura

```
DESIRED OUTCOME (1 North Star)
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

**Outcome:** **Em 12 meses após o GA do MVP-1, atingir 50 tenants pagantes com receita recorrente média ≥ R$ 900/mês e churn mensal ≤ 3% — provando que o produto reduz o custo do status quo (R$ 35-50k/mês por empresa, conforme `jornada-atual-sem-produto.md` §8) em pelo menos 40% medido em piloto.**

**Como medir (3 indicadores acoplados):**

1. **MRR ≥ R$ 45k** (50 tenants × R$ 900 médio) — coerente com WTP perfil B inferido R$ 700–1.500/mês (V-2) e CAC/LTV viável (V-4).
2. **Churn mensal ≤ 3%** — proxy de "produto resolve dor real" vs "vendi mas cliente não usou" (mitiga R-001 — founder is customer).
3. **NPS-piloto ≥ 50 + economia auto-reportada ≥ R$ 14k/mês por tenant** — 40% de R$ 35-50k é o piso pra discurso de ROI sustentar preço acima de R$ 700/mês.

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

## Opportunities (8 — cobertura obrigatória dos 4 eixos + 4 decisões fundadoras)

> **Critério de inclusão:** cada Opportunity tem (a) ancoragem em ≥ 1 dor ranqueada com score ≥ 1.000, (b) cobertura de ≥ 1 Big Job dos 12, (c) ≥ 3 personas afetadas das 14, (d) custo do status quo R$ ou hr quantificável, (e) gap competitivo confirmado em `concorrentes.md` OU decisão fundadora canônica.

---

### Opportunity 1 — Recalibração lembrada de forma proativa (não esquecida)

**Big Job:** BIG-02 (não-perder-acreditação) + BIG-10 (Cliente 360°) + BIG-11 (Automações)
**Gap defensável:** #5 (CRM contínuo — concorrentes nacionais matam o cliente no CRM após emitir certificado)

**Origem em dores-mapeadas.md:** **Dor #02 — Esquecimento de lembrar cliente da próxima calibração** (score **28.500**, o maior do mapa).

**Evidência:**
- Jornada §1 + §8: "empresa-modelo perde 30-50% das recalibrações por esquecimento" → **R$ 8-12k/mês de receita perdida** [INFERÊNCIA — validar em onda 1]
- JTBD-084 (renovação automática), JTBD-044 (alerta 60-90 dias), JTBD-090 (alerta cliente inativo >180d), JTBD-096 (oportunidade auto pós-12m)
- `concorrentes.md` §3.1-3.10: Cali, Metroex, Calibre, Q-MAN, ConfLab — todos têm "agenda de validade" mas **nenhum tem CRM contínuo com automação WhatsApp aprovada + proposta automática de renovação**
- Decisão fundadora 3 (Cliente 360° + CRM + Automações)

**Personas mais afetadas:** Roldão (perde receita), Rogério (perde comissão de renovação), Sandra (não fecha ciclo qualidade), João Eng. (cliente final sem certificado válido), João-Sênior (cliente low-tech que migra pra concorrente sem perceber)

**Custo do status quo:** **R$ 8.000-12.000/mês de receita perdida por empresa** (Jornada §8) + R$ 1-2k/mês em horas de Letícia/Rogério mandando lembrete manual quando lembram.

#### Solution 1.1 — Calendário de validade + régua de notificação WhatsApp aprovada (proativa, baseada em data de emissão + ciclo do instrumento)

**Descrição:** O sistema calcula automaticamente a próxima janela de recalibração (60/30/15 dias antes do vencimento) por equipamento × cliente e dispara mensagem via template WhatsApp Business aprovado pela Meta — sem ação humana. Cliente final responde "quero agendar" → cria oportunidade pré-preenchida no funil de venda. Atendente só vê os que pediram retorno.

**Premissas a validar:** D-1 (compra unificada), D-3 (Letícia adota inbox unificada), D-16 (WhatsApp é canal obrigatório — **SABEMOS**), F-4 (WhatsApp BSP integra ≤ R$ 0,50/conversa)

**Custo:** **M** (calendário + cron + template Meta + integração BSP — Z-API/360dialog/Meta Cloud)

**Experiment:** **Smoke test** — landing page "Aferê manda lembrete de recalibração pelo WhatsApp 60 dias antes — você nunca mais perde renovação" com tráfego pago R$ 1.000 (Meta Ads + Google Ads SP/RS/MG). Métrica: ≥ 2% de conversão pra trial em donos perfil A/B/C identificados.

#### Solution 1.2 — Proposta de renovação automática pré-aprovada (cliente clica "aceito" no WhatsApp e vira OS agendada)

**Descrição:** Vai além do lembrete: o sistema gera proposta automática com preço pré-aprovado (margem mínima travada pelo dono), envia link curto no WhatsApp; cliente clica, aceita, escolhe janela; vira OS agendada + assinatura digital simples + entrada no fluxo financeiro. Reduz fricção de "preciso mandar e-mail explicando que está na hora" pra zero. JTBD-092 (proposta de renovação automática) materializado.

**Premissas a validar:** D-1, D-10 (João-Sênior abre link no WhatsApp — **SABEMOS parcial**), V-2 (WTP), E-3 (cliente aceita texto "feito com IA + supervisão"), F-15 (assinatura digital ICP-Brasil A1 funciona)

**Custo:** **G** (geração de proposta + DSL de preço + link curto assinado + portal lite + OS automática)

**Experiment:** **Fake-door** — adicionar botão "Renovar com 1 clique" na landing → quantos clicam? + 5 entrevistas Onda 1 com clientes finais perfil João-Sênior pra validar "se chegasse esse link no WhatsApp você clicaria?". Métrica: 4/5 dizem "sim".

#### Solution 1.3 — Painel de "cliente em risco" + alerta de inativo > 180 dias pro vendedor

**Descrição:** Pra Rogério (vendedor) — em vez de o cliente "morrer" silenciosamente, o sistema mostra dashboard ranqueado por risco de churn (sem recalibração há X dias × LTV histórico × probabilidade migração com base em concorrentes ativos na região). Vendedor abre o dia já com lista priorizada de quem ligar/visitar; comissão de retenção é configurada pra essa ação no BIG-09.

**Premissas a validar:** D-7 (Rogério adota CRM pipeline), V-2, V-6 (pricing por perfil), F-8 (CODEOWNERS + Spec Kit aguenta complexidade)

**Custo:** **M** (algoritmo simples de risco — sem ML; lista ranqueada + sinaliza ação)

**Experiment:** **Protótipo clicável** — mostrar dashboard de "10 clientes que vão sair" pra 5 vendedores reais (Rogério-equivalentes em PME calibração). Métrica: 4/5 dizem "isso me faz vender mais" + auto-reportam ≥ R$ 500/mês de comissão recuperável.

---

### Opportunity 2 — Certificado emitido sem medo (cadeia completa + dossiê + assinatura digital ICP-Brasil)

**Big Job:** BIG-01 (ciclo completo) + BIG-02 (não perder acreditação)
**Gap defensável:** #1 (ciclo completo OS→certificado→NFS-e — **NENHUM concorrente nacional faz**, exceto FP2 regional Santa Maria/RS)

**Origem em dores-mapeadas.md:**
- **Dor #04 — Word/Excel/macros = NC permanente cláusula 7.11** (score **8.250**, "pitch real do Aferê" per Jornada §6.5)
- **Dor #03 — Certificado sem campo NIT-DICLA-030** (score **2.400**, R-018 score 25 — o maior risco do projeto)
- **Dor #06 — Padrão usado com calibração vencida** (score **3.000**)
- **Dor #07 — Signatário-gargalo** (score **3.000**)

**Evidência:**
- Jornada §6.5 + §6.bis: "Planilha Excel + macros pra incerteza, SEM validação documentada = NC permanente da cláusula 7.11. Não é 'macro vai quebrar' — é não conformidade ATIVA enquanto o lab usa"
- JTBD-027 (rotina pré-validada por grandeza/faixa), JTBD-028 (cadeia rastreabilidade), JTBD-030 (assinar sem ritual), JTBD-051 (assinar 20 com checklist verde), JTBD-031 (provar validação)
- INV-002 (cadeia rastreabilidade trava emissão), INV-004 (dossiê de validação), INV-011 (padrão vencido bloqueia)
- `concorrentes.md` §3.1-3.10: Cali tem cálculo de incerteza mas **sem dossiê de validação documentado**; CalibraFácil declara ISO 17025 mas validação interna opaca

**Personas mais afetadas:** Marcos (signatário — responsabilidade legal CRQ), Sandra (RT — defende NC), Roldão (negócio em risco), Patrícia (cliente farma — audita fornecedor), Auditor Cgcre

**Custo do status quo:** **R$ 50.000-500.000 de indenização** quando cliente farma audita e descobre cálculo não-validado (Jornada §6.5) + **perda de acreditação** = empresa fechada. Mensal recorrente: R$ 0 visível, **R$ infinito quando materializa**.

#### Solution 2.1 — Procedimentos PT-BR validados (massa, pressão, temperatura primeiro) + dossiê de validação cláusula 7.11 nativo

**Descrição:** O sistema entrega 3 grandezas com procedimento de cálculo de incerteza GUM/JCGM 100 pré-validado por metrologista externo + dossiê de validação (especificação + teste de aceitação + aprovação RT) gerado nativamente. Lab assina dossiê 1 vez por upgrade de versão e sai da NC permanente. Cada certificado emitido cita versão do procedimento + hash do dossiê.

**Premissas a validar:** F-5 (cálculo validável internamente — **LEAP #6**), D-5 (Marcos confia na máquina pra assinar — **LEAP #7**), F-12 (auditoria interna 17025 viável sem consultoria R$ 50k+)

**Custo:** **G** (3 procedimentos × metrologista RBC externo R$ 6k validação + dossiê template + change log com hash)

**Experiment:** **Spike técnico** — implementar massa + pressão + temperatura + comparar com Excel de 3 metrologistas RBC reais (pagos R$ 300/h × 20h). Métrica: 3/3 concordam dentro da tolerância NIT-DICLA-021 + 3/3 assinam "eu assinaria com meu CPF".

#### Solution 2.2 — Cadeia de rastreabilidade automática + bloqueio de emissão se padrão vencido / fora de escopo (INV-002 + INV-011)

**Descrição:** Hooks bloqueantes: emissão de certificado falha se (a) padrão usado não tem calibração-pai válida na data de uso, (b) signatário não tem competência declarada pra grandeza × faixa, (c) campo obrigatório NIT-DICLA-030 está vazio. Mensagem ao operador é PT-BR clara ("padrão X vencido em 15/04 — recalibre antes de emitir") + link pra ação. Resolve Dor #03 + #06 simultaneamente.

**Premissas a validar:** F-6 (hooks ≤ 5% falsos-positivos), F-1 (modelo agentes entrega — **LEAP #1**), E-2 (auditor Cgcre aceita "IA no backoffice + signatário humano")

**Custo:** **M** (motor de regras + matriz competência × signatário × grandeza × faixa)

**Experiment:** **Protótipo + entrevista validativa** — mostrar fluxo "tentei emitir certificado com padrão vencido → sistema bloqueou com mensagem X" pra 5 RTs (Sandra-equivalentes). Métrica: 4/5 dizem "isso me tira sono de cima" + 1 auditor Cgcre real confirma "isso atende cláusula 7.11".

#### Solution 2.3 — Assinatura digital ICP-Brasil A1/A3 + workflow "4 olhos" + fila do signatário priorizada por SLA do cliente

**Descrição:** Marcos assina digitalmente no celular ou desktop em PDF com certificado A1/A3 (LACUNA/BRy/ValidCertificadora) — válido juridicamente. Antes de assinar, sistema mostra fila priorizada por SLA do cliente (Dor #14 — cliente farma 3 dias úteis primeiro). Opcional "4 olhos": certificado precisa de revisão de outro signatário antes (mitiga "assina em massa sem reler" — Dor #07). Substitui PDF Word + carimbo + scan.

**Premissas a validar:** F-15 (assinatura ICP-Brasil integra sem dor), D-5, F-7 (dual tooling consistente — **LEAP #10**)

**Custo:** **M** (integração BaaS assinatura + fila com SLA por contrato)

**Experiment:** **Spike + WTP test** — assinar 10 PDFs com certificado A1 do Roldão validados no Adobe Reader. Métrica: 10/10 válidos. + Van Westendorp: "quanto pagaria por mês pra Marcos assinar 30 certificados em 15 minutos com 100% conformidade?" → mediana ≥ R$ 300/mês = sustenta tier B.

---

### Opportunity 3 — Operação de campo controlada (frota, UMC, caixa do técnico, custo real por OS)

**Big Job:** BIG-08 (Frota + UMC + Caixa do técnico — decisão fundadora 1 canônica)
**Gap defensável:** #6 (Frota + UMC + Caixa do técnico integrado a custo por OS — **inexistente em concorrentes**)

**Origem em dores-mapeadas.md:**
- **Dor #16 — Caixa do técnico + frota descontrolados** (score **6.300**)
- **Dor #19 — Registro em WhatsApp viola cláusula 7.5.1** (score **6.300**)
- **Dor #08 — Roteirização no escuro + 2ª visita** (score **1.000**)

**Evidência:**
- Decisão fundadora Roldão 17/05/2026 (`dominio-de-negocio.md` §"Controle de Técnico em Campo, Despesas, Frota e UMC")
- JTBD-060 a JTBD-070 (11 jobs novos da decisão)
- Jornada §5.4-5.5: "30% dos comprovantes somem"; combustível dobrado por roteirização ruim; "2ª visita custa R$ 3-6k/mês"
- R-043 a R-047 (5 riscos novos): multa não paga vira protesto + CNH suspensa; UMC com pesos-padrão R$ 100-300k sem rastreamento

**Personas mais afetadas:** Bruno (técnico — não-mendigar-adiantamento), Bruna (técnica), Carlos (motorista UMC — baixo letramento digital), Cláudia (planilha lateral interminável), Roldão (custo invisível + risco patrimonial)

**Custo do status quo:** **R$ 3.000-6.000/mês de 2ª visita** (Jornada §8) + **R$ 1-2k/mês em comprovantes perdidos** + **R$ 500-2.000 em multas/manutenção tardia** + **risco patrimonial R$ 100-300k** (UMC com pesos-padrão sem rastreio).

#### Solution 3.1 — App mobile simples pra técnico/motorista (1 botão pra cada ação: pedir adiantamento, registrar gasto com foto, sincronizar OS offline)

**Descrição:** App PWA + Capacitor (ou Flutter) com UI BIG (letra grande, botão grande, voz "explica devagar" — D-11), 3 telas principais: (1) "minha OS de hoje" com checklist pré-saída (padrão certo, peça certa, endereço certo); (2) "registrar gasto" com foto + categoria + 1 clique aprova solicita reembolso; (3) "fim do dia" com KM rodado + viagens + recibos sincronizados. Offline-first com IndexedDB; sync inteligente sem perder dado.

**Premissas a validar:** D-4 (técnico usa app offline-first — **LEAP**), D-8 (Carlos motorista usa celular simples — **LEAP**), F-10 (mobile sem time mobile dedicado — **LEAP #12**)

**Custo:** **G** (3 semanas spike + 2 meses de produção)

**Experiment:** **Spike mobile** — protótipo OS offline + sync de 100 OS criadas sem rede → 0 perda + UAT de 5 técnicos reais. Métrica: 70% completam OS digital sem ajuda em ≤ 5 min na primeira tentativa.

#### Solution 3.2 — Caixa do técnico digital (adiantamento → prestação → conciliação automática)

**Descrição:** Fluxo: técnico solicita R$ 500 no app → Cláudia aprova no celular → PIX cai na conta do técnico → técnico gasta + tira foto de cada nota → categoriza (combustível, hospedagem, alimentação, peça) → no fim da viagem, prestação automática → caixa fecha; ausência de nota = débito automático no holerite (com aceite do técnico antes do mês fechar — JTBD-068). Mata 100% da planilha lateral.

**Premissas a validar:** E-8 (vínculo trabalhista CLT/PJ não distorcido), D-6 (Cláudia troca planilha), V-2

**Custo:** **G** (workflow completo + integração PIX BaaS + holerite hooks)

**Experiment:** **Protótipo + ride-along** — acompanhar 2 técnicos por 3 dias com app de fluxo simulado em papel → mapear fricção real. Métrica: 100% das despesas categorizadas com foto até dia D+1.

#### Solution 3.3 — Frota + UMC com TCO consolidado (KM por veículo, manutenção alertada, multa não vira protesto)

**Descrição:** Cadastro de veículos da empresa (carro técnico + UMC com pesos-padrão R$ 100-300k) com odômetro mensal + manutenção preventiva agendada (KM ou data) + integração SENATRAN/DETRAN pra puxar multa em D+15 (antes de virar protesto) + georreferenciamento da UMC quando ela está rodando (rastreamento patrimonial). Custo real por OS = combustível + diária + km × R$/km da frota — alimenta Painel do Dono (JTBD-080 — rentabilidade por OS) e BIG-09 (comissão sobre líquido).

**Premissas a validar:** F-2 (stack aguenta — **LEAP #11**), E-8 (rastreamento veicular vs CLT), V-6 (pricing por perfil A premium)

**Custo:** **G** (integração SENATRAN + telemetria + cálculo TCO)

**Experiment:** **Spike técnico** — testar integração SENATRAN API (consulta de multas) com CNH/placa do Roldão por 30 dias. Métrica: 1 multa real recuperada em D+15 antes do prazo de protesto.

---

### Opportunity 4 — Comissões pagas certas, no prazo, sem briga e sem planilha

**Big Job:** BIG-09 (Comissões configuráveis — decisão fundadora 2 canônica)
**Gap defensável:** #7 (configuração de comissão sem programador, integrada a OS + financeiro + frota)

**Origem em dores-mapeadas.md:**
- **Dor #15 — Comissões em planilha frágil, 3-5 dias do mês + brigas mensais** (score **1.312**)

**Evidência:**
- Decisão fundadora Roldão 17/05/2026 (`dominio-de-negocio.md` §"Módulo de Comissões Configuráveis")
- JTBD-071 a JTBD-082 (12 jobs novos da decisão): DSL configurável, 8 formas de cálculo, simulador "se rodasse hoje", auditoria de ajuste, bloqueio por margem mínima
- R-055/R-056/R-057 (3 riscos novos da decisão)
- `concorrentes.md`: nenhum concorrente nacional tem motor de comissões configurável; Cali Web tem cálculo fixo

**Personas mais afetadas:** Cláudia (esgotamento mensal), Roldão (paga comissão errada — pode estar pagando sobre OS com prejuízo), Rogério (briga por número), Bruno (não confia no holerite), Carlos (motorista UMC sem visibilidade)

**Custo do status quo:** **3-5 dias úteis do financeiro/mês × R$ 200/dia = R$ 600-1.000/mês em horas** + **R$ 500-2.000/mês de comissão paga errada** (sobre OS com prejuízo invisível) + **risco trabalhista R-055 score 12** (questão judicial sobre regra mudada sem aceite).

#### Solution 4.1 — DSL configurável pelo dono (8 formas de cálculo + gatilho por recebimento + simulador "se rodasse hoje")

**Descrição:** Tela "Configurar comissão" — sem programador. Dono escolhe: (a) base de cálculo (bruto, líquido, margem, ticket); (b) gatilho (emissão da NFS-e, recebimento confirmado, fim do mês); (c) percentual ou valor fixo; (d) regras por colaborador/equipe/papel; (e) divisão entre participantes (vendedor + técnico + comissionado especial). Simulador mostra "se rodasse hoje, X colaborador receberia R$ Y" antes de ativar. Mudança de regra exige aceite digital do colaborador (mitiga R-055 trabalhista).

**Premissas a validar:** V-8 (Roldão não vira "comissão do Roldão"), D-1, E-8 (vínculo trabalhista)

**Custo:** **G** (DSL + motor de cálculo + simulador)

**Experiment:** **Protótipo clicável + 5 entrevistas com donos perfil B** — mostrar tela de configuração; pedir que descrevam suas 3 regras mais usadas; medir tempo de configurar. Métrica: 4/5 configuram regra real em ≤ 10 min sem ajuda.

#### Solution 4.2 — Bloqueio automático: não paga comissão sobre OS com prejuízo nem sobre inadimplência

**Descrição:** Hook bloqueante: ao fechar comissão do mês, sistema cruza com (a) custo real da OS (BIG-08 — frota + caixa do técnico + peças BIG-12) e (b) status de recebimento (BIG-04 NFS-e + financeiro). Comissão sobre OS de margem negativa = bloqueada com mensagem PT-BR ("essa OS deu R$ -200 — comissão zerada por margem mínima"). Comissão sobre OS não-recebida = trava até recebimento confirmado (mitiga R-novo C3).

**Premissas a validar:** F-2, E-1 (LGPD IA toca PII financeiro — **LEAP #8**), V-7 (recorrência domina serviço)

**Custo:** **M** (depende de BIG-08 + BIG-04 estarem integrados)

**Experiment:** **Spike de dados** — pegar 3 meses do Roldão real (planilha de comissão atual × extrato × OS reais) e rodar motor. Métrica: identifica ≥ R$ 1.000 de comissão paga errada no histórico.

#### Solution 4.3 — Fechamento mensal em 1 hora com auditoria de cada ajuste

**Descrição:** Tela "Fechar comissão do mês" — vê lista por colaborador com (a) base calculada automaticamente, (b) ajustes manuais (com motivo obrigatório), (c) aceite digital do colaborador. Cada ajuste vira evento auditado (quem, quando, por quê). Exportação direta pra folha de pagamento (integração Pontomais/Sankhya RH MVP-3). Cláudia fecha em 1h em vez de 3-5 dias.

**Premissas a validar:** D-6, F-9 (bus factor mitigável), V-2

**Custo:** **M** (workflow + audit log)

**Experiment:** **Time-trial real** — cronometrar Cláudia (ou financeiro-equivalente) fechando comissão num mês: status quo (planilha) × protótipo (Aferê mock). Métrica: redução ≥ 70% de tempo + 0 ajustes não-auditados.

---

### Opportunity 5 — Cliente nunca "morre" no CRM (visão 360° + automações configuráveis sem código)

**Big Job:** BIG-10 (Cliente 360°) + BIG-11 (Automações configuráveis) — decisão fundadora 3 canônica
**Gap defensável:** #8 (CRM 360° integrado a calibração — concorrentes têm "cadastro de cliente", não CRM contínuo)

**Origem em dores-mapeadas.md:**
- **Dor #20 — Cliente "morre" no CRM após calibração** (score **1.800**)
- **Dor #05 — Status de OS perguntado 10-30x/dia** (score **2.869**)
- **Dor #01 — Cadastro digitado 4-6 vezes** (score **8.100**)

**Evidência:**
- Decisão fundadora Roldão 17/05/2026 (`dominio-de-negocio.md` §"Cliente 360°, CRM Contínuo e Automações")
- JTBD-083 a JTBD-097 (15 jobs novos), JTBD-091 (Cliente 360° em 1 tela), JTBD-090 (alerta inativo), JTBD-096 (oportunidade auto pós-12m)
- Jornada §1: "1 a 3 clientes finais perdidos por trimestre" × LTV médio = R$ 30-90k/ano de receita perdida silenciosamente
- `concorrentes.md`: Cali tem portal mas sem timeline 360°; Metroex tem cadastro robusto mas sem automação

**Personas mais afetadas:** Roldão (perda silenciosa), Rogério (vendedor sem alerta), Letícia (atende sem contexto), Sandra (não monitora ciclo), todas as personas internas

**Custo do status quo:** **R$ 2.500-7.500/mês de receita perdida silenciosamente** (1-3 clientes × LTV trimestral) + **horas de Letícia respondendo "cadê meu certificado"** (Dor #05 — 200-600 perguntas/mês × 5-10min) = R$ 1-2k/mês.

#### Solution 5.1 — Timeline 360° por cliente (todas as OS, certificados, NFS-e, mensagens, oportunidades, recebimentos em 1 tela)

**Descrição:** Tela única por cliente: cabeçalho com saúde do cliente (verde/amarelo/vermelho — última calibração, próximo vencimento, inadimplência, NPS); timeline cronológica fundindo eventos de 5 sistemas hoje separados; ações rápidas (ligar, mandar WhatsApp template, criar OS, gerar proposta de renovação). Letícia abre 1 tela e responde "cadê meu certificado?" sem abrir 5 sistemas. Mata Dor #01 + #05 + alimenta #20.

**Premissas a validar:** D-3 (Letícia adota inbox unificada — **LEAP**), D-6, F-2 (stack aguenta — **LEAP #11**)

**Custo:** **G** (modelo de dados consolidado + integração com 5 módulos)

**Experiment:** **Protótipo clicável + UAT** — mostrar timeline 360° pra 5 atendentes Letícia-equivalentes. Métrica: 4/5 dizem "quero hoje" + tempo de responder "cadê meu certificado" cai de 5-10min pra ≤ 30s.

#### Solution 5.2 — Motor de automações configurável sem código (gatilho → condição → ação) com sandbox

**Descrição:** Dono configura regras "se cliente não calibrou há 180 dias E é perfil farma → criar tarefa de retenção pro Rogério + enviar WhatsApp template Z" — sem programador. Sandbox obrigatório: testa em modo seco antes de ativar (mitiga R-novo CRM-1 — automação errada disparando 500 mensagens). Audit log de cada disparo. Materializa JTBD-085, JTBD-088, JTBD-093, JTBD-094, JTBD-095.

**Premissas a validar:** V-8, F-6 (hooks bloqueantes ≤ 5% falsos-positivos), E-3 (cliente aceita "feito com IA")

**Custo:** **G** (DSL + sandbox + audit + UI sem código)

**Experiment:** **Fake-door** — landing "Crie regras de WhatsApp sem programador" com botão "ver demo" → quantos clicam + 3 entrevistas pra mapear as 5 automações que mais querem.

#### Solution 5.3 — Cliente único master (zera cadastro 4-6x; integra NFS-e, OS, financeiro, CRM com a mesma entidade)

**Descrição:** Modelo de dados com cliente como entidade única — uma vez cadastrado, vai pra todos os módulos automaticamente (NFS-e via Focus/PlugNotas, OS, financeiro, CRM, portal). Importador 1-clique de Cali/Bling/planilha CSV (matching por CNPJ + dedup automático). Mata Dor #01 e destrava 5 outras dores.

**Premissas a validar:** F-16 (migração ≤ 8h por cliente), V-12 (trial → pagante ≥ 30%), V-1 (TAM)

**Custo:** **M** (importador + dedup + entidade única)

**Experiment:** **Spike de migração** — exportar dados Cali + Bling de 3 empresas reais (Roldão + 2 piloto) → importar Aferê → tempo + perda. Métrica: 3/3 empresas onboarding ≤ 8h + 0 perda de dado fiscal.

---

### Opportunity 6 — Estoque + lacre/selo INMETRO rastreáveis individualmente (multi-local, transferência com aceite, foto obrigatória)

**Big Job:** BIG-12 (Estoque com lacre/selo — decisão fundadora 4 canônica)
**Gap defensável:** #9 (rastreabilidade individual de lacre/selo INMETRO — **inexistente em concorrentes**)

**Origem em dores-mapeadas.md:**
- **Dor #18 — Selo INMETRO/lacre sem rastreabilidade individual** (score **375**, alta-consequência apesar de Reach 50%)
- **Dor #17 — Cliente confunde "selo INMETRO" com "certificado calibração"** (score **240**)

**Evidência:**
- Decisão fundadora Roldão 17/05/2026 (`dominio-de-negocio.md` §"Módulo de Estoque Completo para Assistência Técnica")
- JTBD-101 a JTBD-103, JTBD-108 (responder fiscal IPEM em 30s — diferencial único BR)
- R-051/R-052: selo aplicado em equipamento errado = fraude metrológica (crime); multa IPEM
- `concorrentes.md`: nenhum tem rastreabilidade individual de selo INMETRO por número de série + foto

**Personas mais afetadas:** Bruno (técnico aplicador), Sandra (RT responde fiscal IPEM), Roldão (responsabilidade legal), Auditor IPEM, João-Sênior (cliente final low-tech multado)

**Custo do status quo:** **R$ 500-5.000/mês de multa IPEM** quando fiscalização cobra rastreabilidade + **risco jurídico criminal** (fraude metrológica) + **R$ 200-500/mês em selo perdido sem controle** (R-novo EST-1).

#### Solution 6.1 — Cada selo/lacre é entidade com número único + foto obrigatória na aplicação + cliente vinculado

**Descrição:** Compra de lote de selo INMETRO → cada selo entra no estoque como entidade individual (número de série único). Técnico aplica → app obriga foto do selo aplicado + foto do equipamento + georreferenciamento + assinatura do cliente final touch. Não é possível "esquecer de registrar". Busca por número responde fiscal IPEM em 30s.

**Premissas a validar:** D-4 (técnico usa app — **LEAP**), F-10 (mobile — **LEAP #12**), E-7 (sigilo end-customer)

**Custo:** **M** (modelo de dados + workflow de aplicação)

**Experiment:** **Protótipo + 3 ride-alongs** — Bruno aplica selo em campo com protótipo. Métrica: 100% dos selos aplicados têm foto + cliente + número associado.

#### Solution 6.2 — Multi-local + transferência 2 etapas com aceite (estoque sede × UMC × técnico × cliente)

**Descrição:** Estoque dividido em locais lógicos: sede, UMC#1, UMC#2, técnico Bruno, técnico Bruna, em-uso-cliente-X. Transferência exige envio (origem) + aceite (destino). Sem aceite, item fica em "trânsito" — bloqueia uso. Bruno não pode "esquecer" que pegou. Sandra vê em 1 tela onde está cada peso-padrão de R$ 100k.

**Premissas a validar:** D-4, F-2, V-2

**Custo:** **M** (workflow de transferência + estado visual)

**Experiment:** **Protótipo + 1 semana piloto Roldão** — simular movimentação real de 1 semana. Métrica: 100% das transferências aceitas em ≤ 1 dia + 0 "sumiço".

#### Solution 6.3 — Aviso obrigatório no certificado "esta calibração NÃO substitui verificação INMETRO" + calendário separado de verificação periódica

**Descrição:** Mata Dor #17 — todo certificado emitido pra equipamento com obrigação de verificação periódica IPEM (balança comercial, bomba combustível, taxímetro) traz nota visível: "Esta calibração voluntária NÃO substitui a verificação periódica INMETRO obrigatória — próxima verificação: DD/MM/AAAA". Sistema mantém calendário separado e cobra lembrete (acoplado a OP1).

**Premissas a validar:** E-10 (acessibilidade — INV-016 absoluta), D-10 (João-Sênior abre PDF do WhatsApp)

**Custo:** **P** (regra de geração + calendário extra)

**Experiment:** **Validação com 5 clientes finais João-Sênior** — mostrar PDF com vs sem aviso → entender se entendem a diferença. Métrica: 4/5 dizem "agora entendi, vou chamar pra verificação no prazo".

---

### Opportunity 7 — NFS-e municipal emitida sem dor (multi-município + cutover Padrão Nacional 01/09/2026)

**Big Job:** BIG-04 (NFS-e multi-município)
**Gap defensável:** #4 (NFS-e + calibração 17025 no mesmo produto — **só FP2 regional cobre, gap absoluto BR**)

**Origem em dores-mapeadas.md:**
- **Dor #10 — NFS-e cutover 01/09/2026 + 26 prefeituras** (score **8.750**)
- **Dor #09 — Conciliação manual 4h/semana** (score **3.187** — depende de #10)

**Evidência:**
- Jornada §7.1 (R-016): cutover Padrão Nacional CGSN 189/2026 obrigatório 01/09/2026; R-017 Porto Alegre desliga local 01/07/2026
- `concorrentes.md` §3-4: "GAP CONFIRMADO" — nenhum dos 14 concorrentes nacionais (Cali, Metroex, Calibre, Q-MAN, ConfLab, etc.) tem NFS-e nativa; FP2 cobre só Santa Maria/RS
- JTBD-034 (NFS-e municipal correta), JTBD-035 (conciliar PIX/boleto)

**Personas mais afetadas:** Cláudia (toda emissão), Roldão (preocupação com fisco), Patrícia (cliente farma exige NFS-e com detalhamento técnico)

**Custo do status quo:** **R$ 200-600/mês de Bling/Omie/Conta Azul** (que o lab paga só pra NFS-e) + **4h/semana de Cláudia em conciliação** = R$ 800-1.200/mês + **risco fiscal cutover** = receita = 0 se não migrar até 01/09/2026.

#### Solution 7.1 — BaaS fiscal unificado (Focus/PlugNotas/TecnoSpeed) cobrindo 12+ municípios prioritários + Padrão Nacional

**Descrição:** Integração com 1 BaaS fiscal que cobre 12-15 municípios prioritários (eixo SP/MG/RS/SC do ICP geográfico) + Padrão Nacional CGSN 189/2026 pronto pra 01/09/2026. Emissão a partir da OS finalizada — cliente único master (OP5) preenche dados; descrição técnica auto-gerada pelo certificado (vincula NFS-e ao certificado emitido — JTBD-034 detalha "instrumento + nº série + faixa").

**Premissas a validar:** F-3 (BaaS único cobre ≥ 12/15 — **LEAP**), V-1, V-11 (Cali não lança fiscal em 18 meses)

**Custo:** **M** (integração API + mapeamento por município)

**Experiment:** **Spike fiscal** — testar 3 BaaS (Focus, PlugNotas, TecnoSpeed) em 15 municípios prioritários. Métrica: 1 BaaS cobre ≥ 12 + custo/NFS-e ≤ R$ 0,80.

#### Solution 7.2 — Conciliação automática extrato × NFS-e × OS (PIX por txid, boleto por nosso número, OFX por valor + data)

**Descrição:** Cláudia conecta conta bancária via Open Finance (Iugu/Asaas/Cora) ou importa OFX. Sistema bate PIX recebido com NFS-e (txid no QR), boleto com nosso número, transferência com regex de descrição. Saldo manual = exceção, não regra. Mata 80% das 4h/semana.

**Premissas a validar:** F-13 (BaaS bancário — **SABEMOS parcial**), E-1 (LGPD PII financeiro — **LEAP #8**), V-13 (farma paga add-on)

**Custo:** **M** (integração + motor de match)

**Experiment:** **Spike de dados** — pegar 1 mês de extrato + NFS-e + OS do Roldão real e rodar motor. Métrica: ≥ 90% match automático.

#### Solution 7.3 — Detalhamento técnico do serviço auto-gerado a partir do certificado (cliente farma aceita)

**Descrição:** NFS-e descrição = não mais "calibração" genérica; auto-gera "Calibração de balança de precisão MARCA modelo X, nº série Y, faixa 0-500g, resolução 0,01g, certificado nº Z emitido em DD/MM/AAAA por signatário CPF — conforme NIT-DICLA-016". Patrícia (farma) aceita sem questionar; ISS classificado certo; código de serviço municipal padronizado.

**Premissas a validar:** D-9 (farma exige rastreabilidade fiscal), V-13

**Custo:** **P** (regra de geração + mapeamento código serviço por município)

**Experiment:** **Validação com 3 gerentes farma** — mostrar PDF de NFS-e gerada pelo Aferê vs pelo Bling atual. Métrica: 3/3 dizem "essa eu aceito sem mandar de volta".

---

### Opportunity 8 — Cliente final acessa certificados sem ligar / sem perguntar status

**Big Job:** BIG-07 (Portal do cliente — gap único)
**Gap defensável:** #5 parcial (portal end-customer com escopo seguro — Cali tem portal "feio que ninguém usa")

**Origem em dores-mapeadas.md:**
- **Dor #05 — Status de OS perguntado 10-30x/dia** (score **2.869**)
- **Dor #13 — Auditoria farma sem aviso** (score **400** — alta-consequência subset)

**Evidência:**
- JTBD-017 (responder "cadê meu certificado" sem levantar), JTBD-091 (Cliente 360°), JTBD-058 (modo auditoria 1 clique)
- `concorrentes.md` §3.1: "Cali WEB existe mas portal feio que ninguém usa"
- D-10 (João-Sênior abre link WhatsApp — **SABEMOS parcial**) + D-17 (portal farma + link público low-tech)

**Personas mais afetadas:** João Eng. (cliente final tecnófilo), Patrícia (farma audita fornecedor), João-Sênior (low-tech açougue — prefere link WhatsApp), Letícia (interrompida 10-30x/dia)

**Custo do status quo:** **R$ 800-1.500/mês em horas de Letícia** (200-600 consultas × 5-10min) + **risco operacional Sandra "virar a noite"** em auditoria farma + **percepção cliente "não dão satisfação"** (NPS).

#### Solution 8.1 — Portal end-customer simples (login por CPF/CNPJ + senha curta) com lista de certificados + download + status OS

**Descrição:** Cliente final loga e vê: (1) certificados emitidos em PDF assinado ICP-Brasil pra download; (2) status da OS em andamento ("estamos a caminho", "calibrando", "emitindo", "pronto"); (3) próxima recalibração agendada; (4) botão "preciso de cópia" / "agendar". Acoplado a OP5 (Cliente 360°) e OP7 (NFS-e — cliente vê NFS-e também).

**Premissas a validar:** D-17 (farma quer portal, low-tech não), E-7 (sigilo end-customer + pentest)

**Custo:** **M** (UI + auth + scoped read-only)

**Experiment:** **Smoke test** — landing "Seu cliente final acessa certificado 24/7 sem ligar pra você" + 5 entrevistas farma. Métrica: 4/5 farma dizem "portal vira critério de habilitação de fornecedor".

#### Solution 8.2 — Link público assinado de WhatsApp (cliente low-tech João-Sênior clica e baixa, sem login)

**Descrição:** Pra cliente final low-tech (D-10) — sistema gera link curto assinado com expiração (ex: 30 dias) + URL única por certificado; manda no WhatsApp template aprovado pelo cliente; ele clica → baixa PDF. Sem login. Sem senha. Sem portal. Mata fricção cliente-final-low-tech (D-11 Roldão Sênior 65+).

**Premissas a validar:** D-10 (**SABEMOS parcial**), D-16 (WhatsApp obrigatório — **SABEMOS**), E-7 (sigilo via token URL com escopo)

**Custo:** **P** (link curto + JWT scoped + expiração)

**Experiment:** **Validação com 5 João-Sênior reais** — mandar link no WhatsApp pra eles. Métrica: 5/5 clicam e baixam em ≤ 60s sem ajuda.

#### Solution 8.3 — Modo Auditoria 1 clique (Patrícia farma chega sem aviso — Sandra clica 1 botão e exibe certificados + cadeia + competências)

**Descrição:** JTBD-058 materializado: Sandra clica "Modo Auditoria" → tela única com (a) lista de certificados emitidos pro cliente farma X no período Y, (b) cadeia de rastreabilidade de cada um (padrão usado, validade, lab-pai), (c) competência declarada do signatário, (d) versão do dossiê de validação do cálculo, (e) últimas NCs e ações corretivas. Tudo exportável em PDF estruturado. Sandra deixa de virar a noite.

**Premissas a validar:** D-9 (farma exige 21 CFR Part 11-eq), E-2 (Cgcre aceita IA backoffice)

**Custo:** **M** (consolidação read + export estruturado)

**Experiment:** **Validação com 3 gerentes farma + 2 RTs** — simular auditoria com Modo Auditoria. Métrica: 4/5 dizem "isso me tira da noite virada".

---

## Priorização final — Opportunity Scoring (RICE-adapted)

> **Fórmula:** Score = (Reach × Impact × Confidence) ÷ Effort, escala 1-5 em cada dimensão.
>
> - **Reach** (1-5): % do ICP afetado (Reach 5 = ≥ 90%)
> - **Impact** (1-5): tamanho da dor mensurada em R$/mês ou NC ativa
> - **Confidence** (1-5): grau de evidência atual (5 = decisão fundadora canônica + gap competitivo confirmado; 3 = inferência forte sem entrevista; 1 = palpite)
> - **Effort** (1-5): custo de construção (1 = POC dias; 5 = trabalho meses + dependência integração)

| # | Opportunity | Reach | Impact | Confidence | Effort | **Score** | **MVP** |
|---|---|---|---|---|---|---|---|
| **OP1** | **Recalibração proativa (Dor #02 — score 28.500)** | 5 | 5 | 4 | 2 | **50,0** | **MVP-1** (eixo primário) |
| **OP7** | **NFS-e multi-município (Dor #10 — score 8.750, cutover 01/09/2026)** | 5 | 5 | 5 | 3 | **41,7** | **MVP-1** (deadline duro) |
| **OP5** | **Cliente 360° + Automações (Dor #20+#05+#01 — score acumulado 12.769)** | 5 | 4 | 4 | 3 | **26,7** | **MVP-1** (decisão fundadora 3) |
| **OP2** | **Certificado sem medo (Dor #04+#03+#06+#07 — score 16.650)** | 4 | 5 | 4 | 4 | **20,0** | **MVP-1** parcial (núcleo metrológico — Solution 2.2 prioritária) |
| **OP3** | **Frota+UMC+Caixa do técnico (Dor #16+#19+#08 — score 13.600)** | 4 | 4 | 5 | 5 | **16,0** | **MVP-1** parcial (decisão fundadora 1 — Solution 3.2 prioritária; 3.3 = MVP-2) |
| **OP4** | **Comissões configuráveis (Dor #15 — score 1.312)** | 4 | 3 | 5 | 4 | **15,0** | **MVP-1** (decisão fundadora 2 — não dá pra adiar; já decidido) |
| **OP6** | **Estoque + lacre/selo (Dor #18+#17 — score 615)** | 3 | 4 | 5 | 3 | **20,0** | **MVP-1** (decisão fundadora 4 — gap único + alta consequência) |
| **OP8** | **Portal cliente final (Dor #05+#13 — score 3.269)** | 4 | 3 | 3 | 2 | **18,0** | **MVP-2** (Solution 8.2 link WhatsApp = MVP-1 quick win; portal completo = MVP-2) |

### Top 3 Opportunities pro MVP-1 (lock obrigatório)

1. **OP1 — Recalibração proativa** (score **50,0**) — maior dor mapeada × universal × baixo Effort. **Eixo de venda #1.**
2. **OP7 — NFS-e multi-município** (score **41,7**) — gap único nacional confirmado + deadline regulatório 01/09/2026 obrigatório. **Eixo de venda #2.**
3. **OP5 — Cliente 360° + Automações** (score **26,7**) — destrava OP1 + OP8; decisão fundadora canônica; resolve Dor #01 que é foundation.

### MVP-1 completo (8 OPs com escopo gerenciado)

- **OP1, OP7, OP5, OP6** (decisões fundadoras canônicas — não-negociáveis)
- **OP2 Solution 2.2** (cadeia rastreabilidade + bloqueios INV-002/INV-011 — sobrevivência regulatória)
- **OP3 Solutions 3.1+3.2** (app mobile + caixa do técnico; 3.3 frota TCO completo = MVP-2)
- **OP4** (comissões — sem isso a equipe interna do Roldão não usa e produto perde o piloto)
- **OP8 Solution 8.2** (link WhatsApp = quick win; portal completo Solution 8.1 = MVP-2)

### MVP-2 (6-12 meses pós-GA)

- OP3 Solution 3.3 (frota TCO + SENATRAN)
- OP8 Solutions 8.1 + 8.3 (portal completo + Modo Auditoria)
- OP2 Solution 2.3 (workflow "4 olhos" + SLA por cliente)
- OP5 Solution 5.2 (motor de automação completo)
- Conciliação Open Finance bidirecional (OP7 Solution 7.2 avançada)

### MVP-3 (12-24 meses)

- Biblioteca de procedimentos PT-BR validados (todas as grandezas além de 3 iniciais — OP2 expandida)
- Integração hardware (Bluetooth/USB com Beamex/Fluke/Presys — Anti-job ANTI-06 modulado)
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
- ❌ Listar 1 solution por opportunity (geralmente há 2–4 caminhos válidos — explorar é parte do trabalho).
- ❌ Solutions vagas ("melhorar UX", "usar IA pra resolver tudo") — precisam ser concretas o suficiente pra virar experiment.
- ❌ Confundir Solution com Feature. Solution = direção; Feature = implementação. Várias features podem materializar uma Solution.
- ❌ Score sem evidência. RICE precisa de Reach/Impact baseados em dado de jornada/JTBD/dor mapeada, não palpite.
- ❌ Trair as 4 decisões fundadoras canônicas (Frota+UMC+Caixa; Comissões Configuráveis; Cliente 360°+CRM+Automações; Estoque com lacre/selo) — qualquer Solution que contradiga é vetada.
- ❌ Esquecer das marcações `[INFERÊNCIA — validar em onda 1]` — pré-entrevistas, tudo é hipótese forte mas não confirmada.

---

## Como esta árvore evolui

- **Onda 1 de entrevistas** (5 donos perfil B + 5 RTs Sandra + 5 atendentes Letícia) → substituir `[INFERÊNCIA]` por citação literal; re-rankear scores.
- **Experiments executados** → Solutions validadas sobem; Solutions refutadas saem ou pivotam.
- **LEAP refutado no `assumption-map.md`** → Opportunity dependente entra em revisão (ex: se F-1 falhar, todo MVP-1 vira "produto sem agentes" e Effort × 3).
- **Novo gap em `concorrentes.md`** → considerar Opportunity nova (alvo: ≤ 1 por trimestre, manter foco).
- **MVP-1 entregue** → re-ler árvore + re-priorizar pro MVP-2 com base em adoção real (não previsão).

---

## Saída esperada

- **1 Outcome principal:** 50 tenants pagantes × R$ 900 médio × churn ≤ 3% × economia ≥ R$ 14k/mês auto-reportada.
- **8 Opportunities** cobrindo 12 Big Jobs + 4 decisões fundadoras + 9 gaps defensáveis + 20 dores mapeadas.
- **24 Solutions** (3 por Opportunity) com premissas explícitas (D-N/V-N/F-N/E-N), custo P/M/G e 1 experiment cada.
- **24 Experiments** propostos (smoke test / fake-door / protótipo / spike técnico / WTP / ride-along / time-trial / UAT).
- **Priorização RICE-adapted:** Top 3 MVP-1 = OP1, OP7, OP5; MVP-1 completo = 8 OPs com escopo gerenciado; MVP-2 = expansões; MVP-3 = farma/hardware.
- **Cobertura:** 4 dimensões (Desejabilidade × Viabilidade × Factibilidade × Ética) com 12 LEAPs priorizados acoplados aos experiments.
