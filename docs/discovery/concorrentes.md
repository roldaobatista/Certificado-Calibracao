# Discovery — Concorrentes

> **Artefato Rodada 0** (agente faz sozinho). Pesquisa secundária sobre concorrência no mercado de ERP de assistência técnica BR e sistemas de calibração ISO 17025.
>
> **Última atualização:** 2026-05-16 — dossiê de concorrentes do módulo de calibração ISO/IEC 17025 preenchido (internacionais + nacionais). Seções de ERP BR genérico (Bling/Tiny/Omie) permanecem em scaffolding e serão preenchidas em rodada própria.

---

## 1. Resumo executivo (TL;DR para o Roldão)

O mercado mundial de software de gestão de calibração ISO/IEC 17025 tem duas camadas:

- **Camada internacional (madura, 20–40 anos de mercado):** Beamex CMX, Fluke MET/CAL+MET/TEAM, IndySoft, ProCalV5, GAGEtrak, Qualer (agora **MasterControl Asset Excellence**), LabWare LIMS, STARLIMS. Todas têm ISO 17025 + 21 CFR Part 11 + cálculo de incerteza explícito; quase nenhuma publica preço; foco pesado em farma, óleo & gás, aeroespacial, dispositivos médicos. Mobile e SaaS já são padrão nos líderes; integração com SAP/ERP via conector dedicado (Beamex Business Bridge, MET/TEAM API).
- **Camada brasileira (pequena, fragmentada):** Cali LAB/WEB (homologado pela CERTI), Metroex/MyLogical (ForLogic), Calibre.Software, Q-MAN (Série-Q), Portal ISO, Qualiex, 8Quali, ISOPLAN (Presys), MK 3.3 (LCDS), FP2 Tecnologia. Aderentes à ABNT NBR ISO/IEC 17025 e RBC, mas — com **uma única exceção parcial (FP2)** — nenhum entrega ciclo completo orçamento → OS → execução de calibração → certificado → **NFS-e municipal** dentro do mesmo produto.

**Achado-chave do bônus (Roldão pediu explícito):** **Não existe, no Brasil, um ERP de calibração que entregue, de forma plena, o trio "OS de calibração + emissão de certificado ISO 17025 + NFS-e municipal multi-prefeitura"**. O caso mais próximo (FP2) integra NFS-e mas só explicita o município de Santa Maria/RS. Os líderes nacionais (Cali, Metroex, Calibre) **terminam o ciclo no certificado de calibração** e empurram o faturamento para um ERP fiscal de terceiros. **Isso é um gap de mercado real e defensável** para o produto que Roldão está desenhando.

---

## 2. Concorrentes internacionais (calibração / metrologia)

### 2.1 Beamex CMX (Finlândia)

| Item | Resposta |
|---|---|
| URL | https://www.beamex.com/calibration-software/cmx/ |
| Origem | Finlândia (Beamex Oy) |
| Foco | Calibração industrial pesada (pressão, temperatura, elétrica, vazão) com calibradores documentadores Beamex no centro |
| ISO 17025? | **Sim, explícito** — auditoria, assinatura eletrônica, cálculo de incerteza expandida combinada por ponto, change management 21 CFR Part 11 |
| Outras normas | cGMP, GMP/GAMP, FDA 21 CFR Part 11, ISO 9001, padrões EURAMET/OIML/NIST para pesagem |
| Integra com ERP? | **Sim** — SAP, IBM Maximo, SAP PM, Infor EAM via "Beamex Business Bridge" |
| Mobile | **Sim** — bMobile Calibration Application + Mobile Security Plus (offline assinado) + calibradores documentadores próprios |
| Preço | **Sob consulta**. Edições Professional e Enterprise; on-premise estação única ou servidor flutuante; SSA (Software Service Agreement) obrigatório. Companion SaaS chamado **LOGiCAL** |
| Deploy | On-premise (CMX) + SaaS separado (LOGiCAL) |
| Mercado-alvo | Farma, óleo & gás, geração de energia, química — laboratórios e indústrias regulados grandes |
| Reviews | Listado em Capterra/GetApp/SoftwareAdvice; pricing sempre redirecionado pra cotação |

**Por que importa pra nós:** referência técnica do setor. Quem compra Beamex já tem calibrador documentador Beamex (hardware caro). Não é concorrente direto para laboratório calibrador brasileiro pequeno/médio.

---

### 2.2 Fluke MET/CAL + MET/TEAM + MET/TRACK (EUA)

| Item | Resposta |
|---|---|
| URL | https://www.fluke.com/en-us/product/fluke-software/fluke-calibration-software |
| Origem | EUA (Fluke Calibration, divisão da Fortive) |
| Foco | **Automação** de calibração elétrica/RF/microondas + asset management |
| ISO 17025? | **Sim** — desde v6.0 (1999) com cálculo de incerteza GUM-compliant. Também ISO 9000, ANSI Z540.3, NRC 10 CFR |
| Integra com ERP? | API do MET/TEAM permite integração (não há conector pronto pra SAP como Beamex); export Excel/Word |
| Mobile | **Sim, módulo Mobile** — checkout de dados do cliente, calibração on-site, sincronização ao retornar |
| Portal cliente | **Sim** — read-only, cliente vê status de OS, baixa certificados |
| Preço | **Sob consulta**. Edições MET/CAL Lite, MET/CAL, MET/CAL Plus + MET/SUPPORT Gold |
| Deploy | On-premise (Windows, BD próprio gerido pelo MET/TRACK) |
| Mercado-alvo | Laboratórios calibradores comerciais e cativos com workload pesado de instrumento elétrico/RF |
| Reviews | Reportes de usuários: "4 a 8x mais rápido que calibração manual"; curva de aprendizado dura |

**Por que importa pra nós:** padrão de mercado pra laboratório que automatiza com instrumento Fluke. Mesma lógica do Beamex — captura o cliente via hardware.

---

### 2.3 IndySoft (EUA)

| Item | Resposta |
|---|---|
| URL | https://www.indysoft.com/ |
| Origem | EUA (IndySoft Corporation) |
| Foco | Calibração + gage management + asset tracking |
| ISO 17025? | **Sim** — também FDA 21 CFR Part 11, ISO 9000/9100, QS, MilSpec legados |
| Integra com ERP? | Não documentado conector pronto; customização via scripts |
| Mobile | App IndySoft Scales + IndySoft RFID |
| Preço | **Sob consulta**. Capterra reporta "alto pra equipes pequenas" |
| Deploy | Cloud + on-premise |
| Mercado-alvo | Manufatura, aeroespacial, automotivo, saúde, **laboratórios comerciais ISO 17025** |
| Reviews | Capterra: usuário ISO 17025 elogia customização ("moldar processo ao negócio"); reclamações sobre curva de aprendizado, suporte lento, preço alto pra pequeno |
| Observação | **Não foi encontrado um produto "Sapphire"**. A linha atual é IndySoft (core) + Scales + RFID. Nome "Sapphire" pode ser confusão com outro produto ou edição descontinuada — [a confirmar com o fornecedor] |

---

### 2.4 ProCalV5 / Prime Technologies (EUA)

| Item | Resposta |
|---|---|
| URL | https://www.primetechpa.com/procalv5-software/procalv5/ |
| Origem | EUA (Prime Technologies, Inc.) |
| Foco | Calibração + manutenção planejada de instrumentação de processo |
| ISO 17025? | **Sim** + FDA (foi o **primeiro CMS comercial 21 CFR Part 11 compliant**) |
| Integra com ERP? | Não documentado conector pronto; foco em integração com calibradores documentadores via Mobile Workstation |
| Mobile | **Sim** — "21 CFR Part 11 compliant Mobile Workstation" offline com sincronização |
| Preço | **Sob consulta**. Capterra/GetApp não publicam |
| Deploy | On-premise (ProCalV5) + cloud SaaS (**ProCal Direct**) |
| Mercado-alvo | Life sciences (farma, dispositivos médicos), química, processos regulados |
| Reviews | Reputação sólida em farma; comentários frequentes sobre custo de formulários customizados |

---

### 2.5 GAGEtrak / CyberMetrics (EUA)

| Item | Resposta |
|---|---|
| URL | https://gagetrak.com/ |
| Origem | EUA (CyberMetrics Corporation, Arizona — 35+ anos) |
| Foco | Gage management + calibração + MSA/Gage R&R |
| ISO 17025? | Suporte declarado a "padrões internacionais (FDA e ISO)"; **menos explícito que Beamex/Fluke quanto à cláusula 6.4/7.6**. Tem produto separado "FDA Compliance Manager" como add-on |
| Integra com ERP? | MQTT Publisher/Broker + Web API Server; SharePoint via embed |
| Mobile | **Sim, mas com reclamações** — usuários reportam glitches e funcionalidade reduzida vs desktop |
| Preço | **Sob consulta**. Licenciamento perpétuo ou subscription; concurrent ou node-locked |
| Deploy | On-premise + RDS/Citrix; cloud limitado |
| Mercado-alvo | Manufatura, automotivo, aeroespacial, dispositivos médicos — porte pequeno a médio |
| Reviews | SelectHub: #3 do segmento. Pontos fortes: facilidade de uso, relatórios. Fracos: mobile, suporte |
| Edições | **GAGEtrak Pro** (full) + **GAGEtrak Lite** (touchscreen, mais barato) |

---

### 2.6 Qualer → **MasterControl Asset Excellence** (EUA)

| Item | Resposta |
|---|---|
| URL | https://qualer.com/ (redireciona pra MasterControl) |
| Origem | EUA — **adquirida/rebrandeada pela MasterControl em 03/03/2025**, rebatizada como **MasterControl Asset Excellence**. MasterControl tem ARR de ~US$ 200M e ~1,25M de usuários (contexto de porte). Fonte: [mastercontrol.com/news](https://www.mastercontrol.com/news/mastercontrol-acquires-qualer/) |
| Foco | Calibração + asset management SaaS-first para laboratórios |
| ISO 17025? | **Sim, forte** — engine de incerteza, validação **live de CMC**, multi-channel acceptance, biblioteca de **+10.000 procedimentos** prontos |
| Integra com ERP? | API; mais voltado pra integração com fornecedores de calibração externa (vendor certificate workflow) |
| Mobile | **Sim** — app de campo com captura em tempo real |
| Preço | **Sob consulta**. 3 planos: Asset Control Basic / Plus / **Service Assurance** (este para laboratórios calibradores comerciais). Estimativas de mercado (ITQlick): US$ 50–150/usuário/mês; implementação one-time variável. Sem free trial; **paid test drive** de 30 dias creditável |
| Deploy | **SaaS puro** (cloud pública, sem private cloud); SLA 99,95% |
| Mercado-alvo | Biotech, dispositivos médicos, pesquisa clínica, saúde, laboratórios comerciais — **mid-size** |
| Reviews | Bem ranqueado (#3 ZipDo, #6 Gitnux). Reclamações de opacidade de preço e custo pra labs pequenos |

**Por que importa pra nós:** é a referência SaaS mais próxima do que Roldão quer desenhar (cloud-first, ISO 17025, lab calibrador). Diferença-chave: **Qualer é US-centric, sem fiscal BR e sem NFS-e municipal**.

---

### 2.7 LabWare LIMS (EUA)

| Item | Resposta |
|---|---|
| URL | https://www.labware.com/ |
| Origem | EUA |
| Foco | **LIMS amplo** (sample tracking, ELN, LES) — calibração é um módulo entre dezenas |
| ISO 17025? | **Sim** — Instrument Manager (cláusula 6.4: calibração, PM, audit trail), COA Manager (cláusula 5.10/7.8 reporting), 21 CFR Part 11 e-signatures |
| Integra com ERP? | Plataforma altamente integrável (SAP, Oracle, etc.) — projeto de integração não-trivial |
| Mobile | Via ELN/LES web; mobile não é o ponto forte |
| Preço | **Sob consulta**. Projeto enterprise — implantação tipicamente meses a anos via integradores certificados |
| Deploy | On-premise + cloud privado |
| Mercado-alvo | **Lab grande regulado** (farma, ambiental, alimentos, petroquímica) com escopo amplo de ensaios — não lab calibrador puro |
| Reviews | Plataforma reconhecida; ressalva universal sobre complexidade e custo de implantação |

**Por que importa pra nós:** **não é concorrente direto** de lab calibrador pequeno/médio. Vira concorrente se o cliente fizer **ensaio + calibração** sob 17025.

---

### 2.8 STARLIMS (EUA / Abbott Informatics)

| Item | Resposta |
|---|---|
| URL | https://www.starlims.com/ ([a confirmar página específica do módulo calibração]) |
| Origem | EUA (Abbott Informatics) |
| Foco | LIMS amplo, mesma família funcional do LabWare |
| ISO 17025? | **Sim** — módulo calibração endereça cláusula 6.4 (equipamento), 7.5 (registros técnicos), 7.7 (validade de resultados). Detalhe específico do produto **[a confirmar via vendor docs]** — busca pública não retornou página dedicada do módulo |
| Integra com ERP? | Sim, plataforma integrável (similar LabWare) |
| Mobile | Web-based |
| Preço | **Sob consulta** |
| Deploy | On-premise + cloud |
| Mercado-alvo | Laboratórios regulados grandes — farma, alimentos, ambiental, forense |
| Observação | Mesmo perfil de competidor que LabWare: **lab calibrador puro pequeno/médio não é o ICP** |

---

### 2.9 Hexagon — esclarecimento sobre "Cornerstone"

A busca **não encontrou produto chamado "Cornerstone" na Hexagon**. O termo aparece como descrição de marketing ("um dos cornerstones do portfolio é o PC-DMIS"). Produtos Hexagon relevantes pra calibração:

- **PC-DMIS** — software de CMM (coordinate measuring machine), inspeção dimensional.
- **HxGN EAM (Calibration Management)** — calibração dentro de EAM corporativo (asset-driven, não lab-driven).
- **Metrology Asset Manager** (lançado em 2025 dentro do **Autonomous Metrology Suite** sobre plataforma Nexus) — monitora calibração, operação, ambiente (T/UR/vibração) de equipamentos de medição.
- URL: https://hexagon.com/products/product-groups/measurement-inspection-software/metrology-software

**Tem outro produto chamado "Cornerstone Software" (ASTEC, Fort Lauderdale, EUA)** — independente da Hexagon — focado em **calibração de instrumentos de processo HART**, com bibliotecas pra Beta, Druck, Fluke, Transmation. URL: https://cornerstone-software.com/. Suporta ISO 9000; ISO 17025 não é destacado.

Há ainda **LECO Cornerstone** (software só pra instrumentos LECO) — irrelevante.

---

## 3. Concorrentes nacionais (Brasil)

### 3.1 Cali (Cali LAB + Cali WEB) — Canoas/RS

| Item | Resposta |
|---|---|
| URL | https://cali.com.br/ • https://www.softwaredecalibracao.com/ |
| Origem | Brasil (Cali, Canoas/RS — desde 2000, com origem em projeto CAMELO de 1998) |
| Foco | **Lab calibrador puro** + indústria com gestão metrológica interna |
| ISO 17025? | **Sim, homologado pela Fundação CERTI** — referência nacional. Cobre dimensional, elétrica, pressão, temperatura, massa, volume, força, tempo |
| Integra com ERP? | **Não documentado.** Foco em OS + certificado + portal cliente |
| NFS-e? | **Não documentado** publicamente. Termina o ciclo no certificado |
| Mobile | Cali WEB (portal cliente web) — não é app mobile nativo de campo |
| Preço | **Sob consulta** |
| Deploy | Desktop (Cali LAB) + WEB (Cali WEB) — modelo híbrido |
| Mercado-alvo | "Grande número de laboratórios credenciados ao INMETRO" (declarado pela própria Cali) |
| Reviews | Não há aggregator pt-BR com volume relevante de review; reputação ancorada na homologação CERTI e tempo de mercado |

**Posicionamento provável vs nós:** **principal concorrente nacional direto** no segmento "lab calibrador acreditado RBC". Forte tecnicamente, mas é **desktop-first** (legado) e **não cobre fiscal/NFS-e**.

---

### 3.2 Metroex / MyLogical — ForLogic (Apucarana/PR)

| Item | Resposta |
|---|---|
| URL | https://metroex.com.br/ |
| Origem | Brasil (ForLogic, Apucarana/PR — ~20 anos no setor) |
| Foco | Plataforma de calibração/metrologia/ensaios + ERP de gestão laboratorial (MyLogical ERP) |
| ISO 17025? | **Sim** — ISO 9001, ISO 10012 e ISO/IEC 17025. Atende laboratórios e indústrias |
| Integra com ERP? | **Sim — com o Qualiex** (também ForLogic, sistema de gestão da qualidade). API documentada (portal-api.forlogic.net). Integração com ERP de terceiros não é destacada |
| NFS-e? | **Não confirmado** publicamente. Termina em proposta comercial, OS, certificado, portal cliente |
| Mobile | **Sim, app offline** ("Coletor"), QR Code |
| Preço | **Sob consulta**. Licença por empresa sem limite de máquina/usuário. Implantação 3–12 meses dependendo do escopo |
| Deploy | **SaaS (cloud)** + **on-premise** |
| Mercado-alvo | Laboratórios calibradores + indústrias com gestão metrológica interna |
| Reviews | Cases internos relatam até 23,5% de ganho de produtividade e 80% de redução de lead time de relatório |
| Produtos | Metroex Gestão, Metroex Operação, Webview, Coletor, QR Code, API |

**Posicionamento provável vs nós:** **segundo concorrente nacional mais forte**, mais moderno que Cali (cloud-first, mobile offline, API). Mesmo gap fiscal/NFS-e.

---

### 3.3 Calibre.Software

| Item | Resposta |
|---|---|
| URL | https://calibre.software/ |
| Origem | Brasil |
| Foco | Calibração + metrologia + gestão laboratorial 100% web modular |
| ISO 17025? | **Sim** — ISO/IEC 17025, ISO GUM, ISO 9001, VIM. **Atende RBC declarado** |
| Integra com ERP? | Não documentado conector pronto. **Tem módulo Financeiro próprio** (fluxo de caixa, contas, despesas/receitas) — embrião de ERP |
| NFS-e? | **Não documentado** explicitamente |
| Mobile | Web responsivo (sem app nativo declarado) |
| Preço | **Sob consulta** |
| Deploy | **SaaS puro** (sem instalação) |
| Mercado-alvo | Lab calibrador acreditado RBC + indústria que faz NR-13 (inspeção de vasos/tubulações) |
| Diferencial | Modularidade real (cliente expande/reduz módulos): Metrologia, Documentos Controlados, Usuários, Contatos, OS, Financeiro, Pendências/Ações. Promete +30% de produtividade vs planilhas |

**Posicionamento provável vs nós:** mais próximo conceitualmente do que Roldão quer (web modular). Não publicou NFS-e — confirmar via demo.

---

### 3.4 Q-MAN NEXT II — Série-Q Informática

| Item | Resposta |
|---|---|
| URL | https://serieq.com.br/index.php/q-man/ |
| Origem | Brasil (Série-Q Informática — desde 1985) |
| Foco | Gestão de calibração de instrumentos **na indústria** (cliente interno) |
| ISO 17025? | Sim + ISO 9001 |
| Integra com ERP? | Não documentado conector pronto |
| NFS-e? | **N/A** — produto não é orientado a lab prestador de serviço |
| Mobile | [a confirmar] |
| Preço | **Sob consulta** (somente WhatsApp) |
| Deploy | [a confirmar] |
| Mercado-alvo | **Indústria com calibração interna**, não lab calibrador comercial |
| Complementares | Q-MSA (Measurement System Analysis), Q-CEP (controle estatístico de processo) |

---

### 3.5 Portal ISO (Módulo Calibração)

| Item | Resposta |
|---|---|
| URL | https://www.portaliso.com/ |
| Origem | Brasil (parceria com UFV) |
| Foco | Gestão da Qualidade ampla (documentos, NC, auditorias, calibração) |
| ISO 17025? | **Sim, módulo dedicado** com critérios de aceitação automáticos + critérios de checagem entre calibrações |
| Integra com ERP? | Não destacado |
| NFS-e? | Não |
| Mobile | [a confirmar] |
| Preço | Tem "teste grátis" (modelo freemium/trial) — único do grupo a expor isso |
| Deploy | SaaS |
| Mercado-alvo | Indústria que precisa de **gestão da qualidade + calibração de instrumentos internos** |

---

### 3.6 Qualiex (ForLogic) — gestão de instrumentos de medição

| Item | Resposta |
|---|---|
| URL | https://qualiex.com/ |
| Origem | Brasil (ForLogic — mesma casa do Metroex) |
| Foco | Gestão da qualidade + módulo de gestão de instrumentos |
| ISO 17025? | Sim + ISO 9001 |
| Integra com ERP? | Integra nativamente com Metroex (sister product) |
| NFS-e? | Não |
| Deploy | SaaS |
| Mercado-alvo | Indústria — calibração interna, não lab calibrador |

---

### 3.7 8Quali

| Item | Resposta |
|---|---|
| URL | https://8quali.com.br/gestao-de-calibracao/ |
| Origem | Brasil |
| Foco | Gestão da qualidade com módulo de calibração |
| ISO 17025? | Sim (declarado) |
| Foco mais raso que os anteriores — controle de prazos, certificados, notificações de vencimento |
| Mercado-alvo | Indústria |

---

### 3.8 ISOPLAN — Presys

| Item | Resposta |
|---|---|
| URL | https://presys.com.br/software-de-calibracao/ |
| Origem | Brasil (Presys — fabricante BR de calibradores documentadores) |
| Foco | Igual Beamex/Fluke: **software amarrado ao hardware Presys** |
| ISO 17025? | Sim |
| Mercado-alvo | Cliente Presys |

---

### 3.9 MK 3.3 — LCDS

| Item | Resposta |
|---|---|
| URL | https://lcds.com.br/mk.asp |
| Origem | Brasil |
| Foco | Calibração + metrologia + certificados |
| ISO 17025? | [a confirmar — produto pouco documentado publicamente] |
| Status | Menor visibilidade que Cali/Metroex/Calibre |

---

### 3.10 FP2 Tecnologia — **único com NFS-e nativa documentada**

| Item | Resposta |
|---|---|
| URL | https://www.fp2.com.br/SistemaLaboratorio.aspx |
| Origem | Brasil (Santa Maria/RS) |
| Foco | Sistema para laboratórios de análises/calibração |
| ISO 17025? | **Sim** — declarado conforme ABNT NBR ISO/IEC 17025 |
| NFS-e? | **SIM — único do levantamento que explicita** integração nativa com Sistema de ISS On-line via WebService + certificado digital ICP-Brasil (e-CPF A1/A3). **Porém: declarado apenas pra Prefeitura de Santa Maria/RS.** Cobertura multi-município **[a confirmar]** |
| Extras fiscais | Boletos bancários, CNAB 240/400 (remessa e retorno) |
| Mercado-alvo | Laboratórios — **regional/Santa Maria/RS confirmado**: os 4 principais clientes públicos listados pela própria FP2 (UFSM, SAMITEC, FATEC, FISMA) são TODOS de Santa Maria/RS. Evidência adicional de que a empresa nunca expandiu cobertura municipal. |
| Reviews | Visibilidade nacional limitada |

**Por que importa pra nós:** é a evidência de que **existe demanda real** pelo combo lab+ISO17025+NFS-e — mas a oferta está restrita a um player regional, sem capilaridade nacional. **Confirma o gap.**

---

### 3.11 Conferi / Calibcert / QMSoft / MetraLabs BR / Mastersaf Calibração

**Não encontrados.** As buscas direcionadas com esses nomes específicos retornaram: (a) nenhum resultado para "Conferi", "Calibcert", "QMSoft" como software de calibração BR; (b) "Mastersaf" existe mas é plataforma de **tax/fiscal** (Thomson Reuters), **sem produto de calibração**; (c) "MetraLabs" é uma empresa alemã de robótica, não BR. Marcar como **não confirmados / possivelmente inexistentes**.

---

### 3.12 CalibraFácil

| Item | Resposta |
|---|---|
| URL | https://calibrafacil.com/ |
| Origem | Brasil — cidade/ano [a confirmar] |
| Foco | Lab calibrador puro — software pra laboratórios ISO/IEC 17025 |
| ISO 17025? | **Sim, claim principal** ("Software para Laboratórios de Calibração ISO/IEC 17025") |
| Cálculo incerteza | **Sim, GUM** |
| Emite certificado? | **Sim** ("emissão automática de certificados") |
| OS / orçamento? | Tem gestão de OS; fluxo orçamento [a confirmar] |
| NFS-e / fiscal? | **Não mencionado publicamente** — provável gap (confirmar via demo) |
| Deploy / Mobile | [a confirmar] |
| Preço | Sob consulta |
| Mercado-alvo | Laboratórios em busca de acreditação ou já acreditados, pequeno/médio porte |

**Posicionamento provável vs nós:** concorrente direto, mas posicionamento "fácil" sugere PME. Sem fiscal evidente — mesmo gap. Adicionar à lista de demos-mystery shopping.

---

### 3.13 Sistema de Calibração ABC71

| Item | Resposta |
|---|---|
| URL | https://sistemadecalibracao.com.br/ • https://abc71.com.br/ |
| Origem | Brasil — ABC71 fundada em **1971**, pioneira em ERP no país |
| Foco | **Módulo dentro de ERP industrial** — controle metrológico interno (fábrica), não lab calibrador prestador |
| ISO 17025? | **Parcial/indireto** — cita ISO 9001/14001/IATF 16949 + "calibrações rastreáveis à RBC", mas não posiciona como software pra lab acreditado emissor |
| Cálculo incerteza | **Não menciona GUM** — usa método Schumacher pra periodicidade |
| Emite certificado? | **Sim pra calibrações internas**; pra terceirizadas faz validação/análise crítica do certificado externo (anexa PDF + aprova/reprova por tolerância) |
| OS / orçamento? | **Não** — controle interno, não fluxo comercial |
| NFS-e / fiscal? | **Não no módulo calibração**; ABC71 tem outros módulos ERP fiscais, mas não nesse |
| Deploy | 100% cloud declarado + opção on-premise via ERP Omega [a confirmar] |
| Mercado-alvo | **Indústria média/grande** (Dormer/Sandvik, MSA Safety, Black & Decker) — não lab acreditado |
| Diferencial | Integração com ERP industrial, código de barras pra movimentação de instrumento, método Schumacher |

**Posicionamento provável vs nós:** **adjacente, não concorrente direto.** Compete pelo metrologista interno da fábrica do cliente, não pelo lab calibrador prestador. Útil pra mapear: se um cliente nosso de calibração também atende esses clientes industriais, há sinergia (eles podem indicar nosso software pro lab que os atende).

---

### 3.14 SoftExpert Suite (módulo Calibration)

| Item | Resposta |
|---|---|
| URL | https://www.softexpert.com/en/module/calibration/ |
| Origem | **Joinville/SC, Brasil** — fundada em **1995** por Ricardo Lepper. Multinacional com escritórios em 12+ países (~3.000 clientes, ~3M usuários, faturamento ~R$ 200M/2024) |
| Foco | **GRC corporativo** (QMS, BPM, ERM, ESG, EAM, PLM, SLM). Calibração é **um módulo entre dezenas** — não é produto dedicado a lab calibrador |
| ISO 17025? | **Sim** — página específica de compliance ISO/IEC 17025 |
| Cálculo incerteza | **Não confirmado** na página do módulo [a confirmar] — claim é "planejamento, execução e controle" |
| Emite certificado? | **Não explícito** — fala em controle de planos, sem claim de emissão formal RBC [a confirmar] |
| OS / orçamento? | **Não** — gestão interna de programa, não fluxo comercial |
| NFS-e / fiscal? | **Não** — plataforma de GRC, sem módulo fiscal BR |
| Deploy | SaaS + on-premise (tradição Suite) [a confirmar pro módulo específico] |
| Mobile | App da Suite existe; cobertura do módulo Calibration [a confirmar] |
| Preço | Sob consulta — ticket enterprise alto |
| Mercado-alvo | **Empresa média/grande com GRC integrado** (farma, alimentos, manufatura regulada) — calibração de ativos próprios |

**Posicionamento provável vs nós:** **adjacente.** Vence quando o cliente já tem outro módulo SoftExpert e quer adicionar calibração ali; perde quando é lab pequeno/médio que vende calibração. Concorrente importante pra empresas brasileiras grandes que querem "tudo num só lugar" — mas nosso ICP é diferente.

---

### 3.15 Confience myLIMS

| Item | Resposta |
|---|---|
| URL | https://www.confience.io/mylims |
| Origem | EUA — investida pela STG Partners (private equity); separada e concorrente da PerkinElmer/Revvity Signals e LabWare. Hipótese inicial de vínculo PerkinElmer estava errada (busca pública). Origem provável: Computer Aided Solutions / linhagem LIMS legado [a confirmar] |
| Foco | **LIMS amplo** — ciclo de vida de amostra, integração com instrumentos, ELN, workflows configuráveis. Calibração é submódulo de "instrument/equipment management" |
| ISO 17025? | **Sim** (material institucional); plataforma também ISO 27001 |
| Cálculo incerteza | **Não mencionado** — foco é agendamento de calibração, log de manutenção, SPC (regras Western Electric); não emite certificado com incerteza |
| Emite certificado? | **Não no sentido formal RBC** — gerencia "calibration certificate records" de terceiros; não é máquina de emitir certificado pra clientes externos |
| OS / orçamento? | **Não no sentido brasileiro** — tem worklist management pra amostras de teste |
| NFS-e / fiscal? | **Não** — produto americano, sem fiscal BR |
| Deploy | **Cloud SaaS web-based** (declarado) |
| Mobile | Web responsivo provável; app nativo [a confirmar] |
| Preço | Sob consulta (enterprise) |
| Mercado-alvo | Labs complexos: água, manufatura, industrial, comercial testing, materiais — perfil regulado (cliente PetroReconcavo citado no BR) |

**Posicionamento provável vs nós:** **não é concorrente direto** — é LIMS que **inclui** calibração, não software de calibração que inclui LIMS. Compete em lab de **ensaio** que faz calibração como atividade secundária. Pra nosso ICP (lab calibrador puro RBC), é dimensionamento errado.

---

### 3.16 AutoLab — **três produtos distintos com mesmo nome**

A busca trouxe **3 empresas brasileiras** usando "AutoLab" — atenção pra não confundir:

**3.16a — Sistema Autolab (Arkade Soluções, Goiânia/GO)**
- URL: https://sistema-autolab.com.br/
- Foco: **controle tecnológico de obras civis** (concreto, ensaios de construção) — NÃO é lab de calibração tradicional. Equipamentos monitorados quanto à validade da calibração; calibração vem de terceiros
- ISO 17025: não mencionado | NFS-e: não mencionado
- Deploy: Cloud SaaS + **app mobile nativo** pra campo (único da lista declarando app nativo robusto, junto com Metroex)
- Mercado-alvo: construtoras e laboratórios de obras (mercado adjacente)
- **Diferencial:** integridade imutável dos ensaios pós-aprovação

**3.16b — AUTOLAB (Automa Consultoria & Informática)**
- Foco: **gestão e automação de laboratórios de calibração e ensaios ISO/IEC 17025** — esse SIM é concorrente direto
- Caso real: IPEN-CNEN/SP (Laboratório de Calibração de Instrumentos LCI) usa pra calibração gama
- Demais campos: [a confirmar] — pouca informação pública indexada

**3.16c — AUTOLAB (MRI Tecnologia Eletrônica / Autolab Automação, São Carlos/SP)**
- Foco: **automação laboratorial industrial** com coleta Wi-Fi direta de instrumentos analíticos ("Lab 4.0") + gestão de equipamentos
- MRI: 30 anos de mercado
- Mercado-alvo: indústria com lab analítico interno (não lab calibrador RBC)

**Posicionamento provável vs nós:** o **AutoLab da Automa** é concorrente direto a investigar (IPEN como cliente é referência forte). Os outros dois são adjacentes/diferentes mercados.

---

### 3.17 ConfLab

| Item | Resposta |
|---|---|
| URL | https://www.conflab.com.br/ (manual em https://conflab.com.br/app/Manual) |
| Origem | **São Carlos/SP — Instituto de Química da USP (IQSC)**; criadores: Dr. Igor Renato Bertoni Olivares (auditor externo Cgcre/Inmetro desde 2009) e Dr. Vitor Hugo Polisél Pacces (auditor externo desde 2012) |
| Foco | **Validação de métodos analíticos + cálculo de incerteza + controle de qualidade** (conceito Analytical Quality Assurance Cycle — AQAC). É **ferramenta complementar** de lab de ensaio, não software completo de lab calibrador |
| ISO 17025? | **Sim, claim direto** ("atender 100% dos requisitos de validação, incerteza e controle de qualidade da ISO/IEC 17025:2017") |
| Cálculo incerteza | **Sim — é o ponto forte** — baseado em Eurachem e Nordtest, +10 tipos de fontes de incerteza combináveis, inclui incerteza de amostragem, sem precisar inserir fórmulas |
| Emite certificado? | **Não mencionado** — foco é validação/incerteza/QC |
| OS / orçamento? | Não mencionado |
| NFS-e / fiscal? | Não |
| Deploy | **Web** — qualquer dispositivo, projetos na nuvem |
| Mobile | Web responsivo; app nativo [a confirmar] |
| Preço | Sob consulta |
| Mercado-alvo | **Labs de ensaio analítico** (químico/farma/alimentos/ambiental) que precisam validar método e estimar incerteza pra acreditação ANVISA/INMETRO. Universidades também |
| Diferencial | **Pedigree acadêmico** (USP + 2 auditores Cgcre ativos) + ciclo AQAC integrando validação + incerteza + QC em base única |

**Posicionamento provável vs nós:** **complementar, não concorrente direto.** Disputa o nicho "validação rigorosa de método". Pode ser parceiro estratégico (integração via API pra labs que usam ConfLab pra validação e o nosso pra OS+certificado+fiscal).

---

### 3.18 Síntese da rodada 2 de pesquisa (6 adicionais)

**Achado-chave:** **NENHUM dos 6 novos confirmou módulo fiscal NFS-e brasileiro.** Reforça o gap absoluto identificado no levantamento original. Lista total nacional sem NFS-e nativa: Cali, Metroex, Calibre.Software, Q-MAN, Portal ISO, Qualiex, 8Quali, ISOPLAN, MK 3.3, CalibraFácil, ABC71, SoftExpert, myLIMS, AutoLab (3 variantes), ConfLab. Único com NFS-e declarada = **FP2 (regional, Santa Maria/RS)**. **Gap confirmado em 2 ondas independentes de pesquisa.**

**Segmentação atualizada dos 16 nacionais identificados:**

| Categoria | Players |
|---|---|
| **Concorrentes diretos (lab calibrador prestador puro)** | Cali, Metroex, Calibre.Software, CalibraFácil, AUTOLAB/Automa, FP2 |
| **Adjacentes (controle metrológico interno de indústria)** | ABC71, Q-MAN, Qualiex, 8Quali, ISOPLAN (Presys), MK 3.3, AutoLab/Arkade (obras), AutoLab/MRI (analítico industrial) |
| **Complementares (QMS / LIMS amplo / validação)** | SoftExpert (GRC corporativo), Portal ISO (QMS), Confience myLIMS (LIMS), ConfLab (validação acadêmica) |

---

## 4. Bônus crítico — gap "OS + calibração ISO 17025 + NFS-e municipal"

**Pergunta do Roldão:** existe ERP brasileiro que já entrega o trio?

**Resposta investigada (16/05/2026):**

| Vendor | OS de calibração | Certificado ISO 17025 | NFS-e municipal | Multi-município | Status |
|---|---|---|---|---|---|
| Cali LAB/WEB | ✅ | ✅ (CERTI homologado) | ❌ | — | Forte em metrologia; fiscal não |
| Metroex (ForLogic) | ✅ | ✅ | ❌ (não documentado) | — | Mais moderno; fiscal não |
| Calibre.Software | ✅ | ✅ | ❌ (não documentado) | — | Modular web; sem fiscal |
| Q-MAN | ⚠️ (foco interno) | ✅ | ❌ | — | Não atende lab prestador |
| Portal ISO | ⚠️ | ✅ | ❌ | — | QMS amplo |
| **FP2 Tecnologia** | ✅ | ✅ | ✅ | ⚠️ **só Santa Maria/RS documentado** | **Único que combina, mas regional** |
| ISOPLAN (Presys) | ✅ | ✅ | ❌ | — | Amarrado ao hardware |
| Internacionais (Beamex, Fluke, Qualer, IndySoft, ProCalV5, GAGEtrak, LabWare, STARLIMS) | ✅ | ✅ | ❌ (sem fiscal BR) | ❌ | Nenhum tem fiscal brasileiro |

**Conclusão:**

1. **Nenhum** dos 8 grandes internacionais tem fiscal brasileiro (esperado — não é mercado-alvo deles).
2. **Nenhum** dos top 5 nacionais de calibração (Cali, Metroex, Calibre, Q-MAN, Portal ISO) entrega NFS-e nativa do ciclo.
3. **Apenas o FP2 Tecnologia** entrega o trio, e mesmo assim documentado para um único município (Santa Maria/RS). Cobertura multi-município é **[a confirmar]** mas, por porte da empresa e ausência de visibilidade nacional, é improvável que cubra padrão nacional NFS-e ou centenas de prefeituras com layout próprio.
4. **GAP CONFIRMADO.** O produto que Roldão está desenhando ataca um vão real: **"primeiro ERP brasileiro nativo cloud para laboratório de calibração acreditado RBC com NFS-e multi-município integrada"**.

**Cuidado a registrar em `riscos.md`:**

- **R1** — FP2 pode estar mais avançado que o site público mostra. Antes de cravar "gap absoluto", agendar demo do FP2 e validar cobertura real de municípios.
- **R2** — Cali (líder de mercado nacional) pode lançar fiscal via parceria com Bling/Omie a qualquer momento. Janela competitiva é estreita.
- **R3** — A complexidade de NFS-e multi-município no Brasil é **enorme** (3.500+ prefeituras, padrões ABRASF/Padrão Nacional/legados). Subestimar esse esforço derruba o produto. Solução real: integrar com **emissor especializado** (Focus NFe, Plug NotasNimbus, etc.) em vez de implementar municipal-a-municipal.

---

## 5. Matriz comparativa síntese (calibração ISO 17025)

| Vendor | Origem | Cloud | Mobile | ISO 17025 | 21 CFR Part 11 | Multi-grandeza | NFS-e BR | Integração ERP | Mercado-alvo |
|---|---|---|---|---|---|---|---|---|---|
| Beamex CMX | FI | + LOGiCAL | bMobile | ✅ | ✅ | ✅ | ❌ | SAP/Maximo | Farma, O&G, energia |
| Fluke MET/CAL+TEAM | EUA | ❌ (on-prem) | módulo | ✅ | ✅ | Elétrica/RF/uW | ❌ | API | Lab calibrador elétrico |
| IndySoft | EUA | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | Customização | Manufatura, aero |
| ProCalV5 | EUA | ✅ (Direct) | ✅ offline | ✅ | ✅ (primeiro) | Processo | ❌ | — | Farma, life sciences |
| GAGEtrak | EUA | parcial | ⚠️ | ⚠️ | add-on | Dimensional | ❌ | MQTT/API | PME manufatura |
| Qualer / MasterControl | EUA | ✅ puro | ✅ | ✅ (forte) | ✅ | ✅ +10k procedimentos | ❌ | API | Biotech, medical devices |
| LabWare LIMS | EUA | priv. cloud | web | ✅ | ✅ | LIMS amplo | ❌ | SAP/Oracle | Lab enterprise |
| STARLIMS | EUA | ✅ | web | ✅ | ✅ | LIMS amplo | ❌ | sim | Lab enterprise |
| **Cali LAB/WEB** | **BR** | híbrido | portal web | ✅ CERTI | ⚠️ | ✅ | ❌ | ❌ | **Lab RBC** |
| **Metroex** | **BR** | ✅+on-prem | ✅ offline | ✅ | ⚠️ | ✅ | ❌ | Qualiex | Lab + indústria |
| **Calibre.Software** | **BR** | ✅ puro | web | ✅ | ⚠️ | ✅ + NR-13 | ❌ | ❌ | Lab RBC + NR-13 |
| Q-MAN | BR | [confirmar] | [confirmar] | ✅ | ⚠️ | ✅ | N/A | ❌ | Indústria interna |
| Portal ISO | BR | ✅ | [confirmar] | ✅ módulo | ⚠️ | sim | ❌ | ❌ | QMS + calibração |
| **FP2 Tecnologia** | **BR** | [confirmar] | [confirmar] | ✅ | ⚠️ | sim | **✅ (Santa Maria/RS)** | parcial | Regional RS |
| ISOPLAN (Presys) | BR | [confirmar] | hardware-bound | ✅ | ⚠️ | sim | ❌ | ❌ | Cliente Presys |

Legenda: ⚠️ = não destacado / não documentado publicamente.

---

## 6. Gaps de mercado que o nosso produto pode explorar

1. **NFS-e multi-município nativa** — gap absoluto entre vendors nacionais com penetração nacional (FP2 cobre mas é regional). **Esta é a tese central.**
2. **Cloud-first SaaS pt-BR** — Cali ainda é desktop-first; Metroex/Calibre estão mais modernos mas Cali domina a base instalada de RBC.
3. **Mobile offline nativo pt-BR** — só Metroex tem app offline robusto. Calibre, Cali WEB e Portal ISO são web responsivo.
4. **Onboarding rápido (LGPD + RBC + fiscal pronto)** — gigantes internacionais exigem implementação de meses; nacionais ainda têm setup pesado. SaaS multitenant com onboarding self-service é raro.
5. **Integração nativa com bancos BR** (boleto, PIX, conciliação) — só FP2 cita CNAB 240/400. Nenhum cita PIX como cobrança nativa.
6. **Preço transparente** — **nenhum** dos 15+ players acima publica preço. Tabela pública (mesmo que por porte) seria diferenciação clara de marketing.
7. **21 CFR Part 11 brasileiro adaptado (Anvisa RDC)** — internacionais cobrem FDA, nacionais cobrem 17025 mas não anunciam Anvisa RDC 658/2022 ou RDC 786/2023 (boas práticas em sistemas computadorizados). Gap pra clientes farma BR.
8. **Cálculo de incerteza explícito por método** — Qualer tem +10k procedimentos prontos. Nenhum nacional anuncia volume comparável. Biblioteca aberta de procedimentos pt-BR seria moat.

---

## 7. Riscos competitivos (input pra `riscos.md`)

| ID | Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|---|
| RC-01 | Cali lança fiscal/NFS-e via parceria | Média | Alto (perdemos diferencial #1) | Ir a mercado rápido; lockar com integração bancária mais profunda |
| RC-02 | FP2 expande pra multi-município nacional | Baixa-Média | Alto | Monitorar; vantagem competitiva por capilaridade SaaS + UX moderna |
| RC-03 | Qualer/MasterControl lança versão pt-BR + fiscal | Baixa | Médio | Foco em PME; gigantes vão entrar pelo enterprise primeiro |
| RC-04 | ERP horizontal BR (Omie/Bling) lança vertical calibração | Média-Alta | Alto | Profundidade técnica ISO 17025 (incerteza, rastreabilidade) que generalistas não dominam |
| RC-05 | Fundação CERTI dá homologação só pra Cali e cria barreira política | Baixa | Alto | Buscar homologação CERTI cedo; preparar caso de uso comparativo técnico |
| **RC-06** | **Visma (dona da Conta Azul desde 08/2025) compra vertical de calibração BR (Cali, Metroex)** e pluga no stack Conta Azul (que já tem NFS-e em 400+ municípios). Resolveria sozinho o gap que Aferê ataca. Visma tem 140+ aquisições históricas — apetite confirmado. | Média | Alto | Monitorar M&A Visma na BR; ir a mercado rápido; lockar com integração bancária mais profunda |
| **RC-07** | **TOTVS lança vertical de calibração** via SIGAMNT (já tem módulo embrionário de calibração interna) ou parceria estratégica. Captura base instalada industrial. | Baixa-Média | Alto | Profundidade técnica RBC + UX moderna SaaS que TOTVS Protheus não consegue replicar |
| **RC-08** | **CGCRE muda paradigma pra acreditação baseada em riscos** (tendência 2025-2026) e exige software adaptado pra "risk-based audit trail". Quem chegar primeiro vira referência. | Média | Médio | Acompanhar discussões CGCRE; modelar audit trail extensível ao novo modelo desde o dia 0 |
| **RC-09** | **INMETRO/CGCRE oferece plataforma estatal grátis** pra labs acreditados (precedente BIPM/UKAS). Mataria mercado nacional. | Baixíssima | Catastrófico | Sem ação ativa; gatilho seria comunicado oficial |

---

## 8. Posicionamento sugerido (1 frase por concorrente)

- **vs Beamex/Fluke/IndySoft/ProCalV5/Qualer/LabWare/STARLIMS:** "feito no Brasil, com fiscal brasileiro embutido — sem você precisar contratar consultoria de US$ 50k pra adaptar um produto americano".
- **vs Cali LAB:** "moderno, cloud e mobile-first, com fiscal NFS-e integrado — você emite OS, faz calibração, gera certificado e fatura no mesmo lugar, sem segundo sistema".
- **vs Metroex/ForLogic:** "mesma cobertura técnica, mas com NFS-e nativa multi-município e onboarding em dias, não meses".
- **vs Calibre.Software:** "mesmo conceito modular e SaaS, mas com fiscal completo, integração bancária PIX/boleto e foco em laboratório acreditado RBC".
- **vs Q-MAN/Portal ISO/Qualiex/8Quali:** "produto desenhado pra **laboratório calibrador prestador de serviço**, não pra indústria com calibração interna — ciclo comercial completo (orçamento → OS → certificado → NFS-e → recebimento)".
- **vs FP2:** "cobertura nacional NFS-e (Padrão Nacional + ABRASF + integradores), não regional — e UX moderna SaaS, não desktop tradicional".

---

## 9. Pricing observado (calibração ISO 17025)

**Padrão de mercado: opacidade total.** Nenhum dos 15+ players acima publica preço. Estimativas indiretas:

- **Mid-market internacional (Qualer/IndySoft/ProCalV5):** US$ 50–150/usuário/mês (estimativa ITQlick); implementação one-time alguns milhares de USD; 5–20 usuários típico para lab calibrador médio.
- **Enterprise (Beamex CMX, Fluke MET/CAL+TEAM, LabWare, STARLIMS):** US$ 20k–200k+ projeto inicial, mais SSA/SaaS anual.
- **Nacionais (Cali, Metroex, Calibre):** indícios indiretos sugerem R$ 500–5.000/mês por laboratório dependendo do número de instrumentos/usuários/módulos. **Confirmar via mystery shopping (pedir orçamento como cliente).**

**Janela pra nosso produto:**
- Entrada (lab pequeno, até 200 instrumentos, 1–3 usuários): **R$ 300–800/mês** com NFS-e + portal cliente já incluso.
- Crescimento (lab médio, até 2.000 instrumentos, 4–10 usuários): **R$ 1.000–2.500/mês**.
- Pro (lab acreditado RBC com escopo amplo, 10+ usuários, multi-site): **R$ 2.500–6.000/mês**.

Preço **transparente** em tabela pública é diferencial defensável.

---

## 10. Fontes consultadas

### Internacionais
- Beamex CMX — https://www.beamex.com/calibration-software/cmx/ • https://resources.beamex.com/intro-to-cmx-calibration-software
- Beamex CMX brochure — https://www.beamex.com/app/uploads/2019/10/Beamex-CMX-brochure-ENG.pdf
- Fluke MET/CAL — https://www.fluke.com/en-us/product/fluke-software/fluke-calibration-software
- Fluke MET/TEAM — https://www.fluke.com/en-us/product/fluke-software/fluke-calibration-software/met-team-asset-management-software
- Fluke ISO 17025 — https://www.fluke.com/en-us/learn/blog/calibration-software/iso-17025-compliance
- IndySoft — https://www.indysoft.com/ • Capterra: https://www.capterra.com/p/42537/Calibration-Management-Software/
- ProCalV5 — https://www.primetechpa.com/procalv5-software/procalv5/ • helpcenter.primetechpa.com
- GAGEtrak — https://gagetrak.com/ • https://cybermetrics.com/
- Qualer / MasterControl Asset Excellence — https://qualer.com/pricing/ • https://qualer.com/iso-17025-calibration-meeting-your-needs/ • ITQlick: https://www.itqlick.com/qualer/pricing
- LabWare LIMS — https://www.labware.com/blog/implementing-lab-management-software-failed-audit
- STARLIMS (contexto ISO 17025) — https://www.scispot.com/blog/iso-17025-compliance-guide-requirements-software-best-practices
- Hexagon Metrology — https://hexagon.com/products/product-groups/measurement-inspection-software/metrology-software • https://docs.hexagonppm.com/r/en-US/EAM-System-Overview/12.1/1271474
- ASTEC Cornerstone — https://cornerstone-software.com/

### Brasileiros
- Cali LAB/WEB — https://cali.com.br/ • https://cali.com.br/produtos/calilab/ • https://cali.com.br/produtos/caliweb/ • https://www.softwaredecalibracao.com/
- Metroex / ForLogic — https://metroex.com.br/ • https://metroex.com.br/laboratorios-de-calibracao/ • https://portal-api.forlogic.net/
- Calibre.Software — https://calibre.software/ • https://calibre.software/modulos-e-servicos.html
- Q-MAN / Série-Q — https://serieq.com.br/index.php/q-man/ • https://serieq.com.br/index.php/gerenciamento-da-calibracao-metrologia/
- Portal ISO — https://www.portaliso.com/ • http://www.presys.com.br/blog/normas-tecnicas-para-laboratorios-de-calibracao/
- Qualiex (ForLogic) — https://qualiex.com/en/gestao-de-instrumentos-de-medicao/
- 8Quali — https://8quali.com.br/gestao-de-calibracao/
- ISOPLAN (Presys) — https://presys.com.br/software-de-calibracao/
- MK 3.3 (LCDS) — https://lcds.com.br/mk.asp
- FP2 Tecnologia — https://www.fp2.com.br/SistemaLaboratorio.aspx
- Tecnocalibração (laboratório, não software) — https://www.tecnocalibracao.com.br/
- Qualyteam — https://qualyteam.com/pb/software-gestao-calibracoes-calib/

### Regulação BR
- INMETRO RBC — http://www.inmetro.gov.br/laboratorios/rbc/ • https://www.gov.br/inmetro/pt-br/centrais-de-conteudo/sistemas/rbc
- Lista de laboratórios acreditados — http://www.inmetro.gov.br/laboratorios/labrbc.asp
- Blog da Metrologia (cláusulas 6.4, 6) — https://blogdametrologia.com.br/iso-170252017-6-4-equipamentos/ • https://blogdametrologia.com.br/iso-170252017-6-requisitos-de-recursos/
- I9 Consultoria — https://www.i9ce.com.br/iso-17025/
- Docnix — https://docnix.com.br/normas/iso-iec-17025/

### NFS-e / fiscal (referência cruzada)
- Senior ERP NFS-e Nacional — https://documentacao.senior.com.br/gestaoempresarialerp/5.10.4/integracoes/nfs-e/emissao-nfse-nacional.htm
- Notas Fiscais para laboratórios de metrologia — https://softwaredecalibracao.com.br/blog/notas-fiscais-o-que-os-laboratorios-de-metrologia-precisam-saber-sobre-esse-assunto/

---

## 11. Itens pendentes / a confirmar (próxima iteração)

- [ ] **FP2 Tecnologia** — agendar demo e validar cobertura multi-município de NFS-e (não só Santa Maria/RS).
- [ ] **Cali** — pedir orçamento como cliente (mystery shopping) pra confirmar range de preço e roadmap fiscal.
- [ ] **Metroex** — confirmar via comercial se há previsão de NFS-e nativa no roadmap.
- [ ] **Calibre.Software** — confirmar se o módulo Financeiro emite NFS-e ou só controle interno.
- [ ] **STARLIMS** — buscar página oficial do módulo de calibração via vendor docs (Abbott Informatics).
- [ ] **IndySoft "Sapphire"** — confirmar com fornecedor se o nome existe (não apareceu em pesquisa pública).
- [ ] **Hexagon HxGN EAM Calibration Management** — fechar capítulo (página exige JS, não foi possível ler conteúdo público).
- [ ] **Q-MAN / ISOPLAN / MK 3.3** — confirmar deploy (cloud/on-premise) e mobile via fornecedor.
- [ ] **Pesquisar emissores de NFS-e BR** (Focus NFe, PlugNotas, Nimbus, Migrate) pra desenhar integração — vira spike técnico em `spikes-tecnicos/`.

---

## 12. ERPs horizontais BR (PME serviços) — outra trilha de concorrência

> Esta camada não compete em **calibração ISO 17025** (nenhum tem), mas compete pelo **financeiro+NFS-e+OS** do cliente. Se o lab calibrador for pequeno e usar Bling/Conta Azul "no remendo" pra emitir nota, **somos nós contra a inércia desse stack**, não contra o vendor.

### 12.1 Bling (LWSA / Locaweb)

| Item | Resposta |
|---|---|
| URL | https://www.bling.com.br |
| Preço | R$ 55/mês (Cobalto, entrada) → Titânio (faixas por volume: 500/2.000/5.000 pedidos) → Diamante → Elite (sob proposta). Reestruturação abr/2026. Faixa típica: R$ 55–R$ 405/mês |
| Fundação | 2009 (Bento Gonçalves/RS); adquirido pela LWSA em 2022 |
| Módulos | vendas, estoque, financeiro, fiscal (NF-e/NFC-e/NFS-e), PDV, loja virtual, **OS**, propostas, marketplaces, conta digital |
| NF-e/NFS-e | Sim ambas; NFS-e via padrão municipal + Padrão Nacional pra MEI. Cobertura municipal específica [a confirmar] |
| Mobile | App nativo Android (publisher "Organisys Software") + iOS, funcionalidades reduzidas |
| API | Pública REST OAuth 2.0 (v3); webhooks (retentativa 3 dias); doc em developer.bling.com.br; rate limit por plano |
| Multi-tenant | SaaS multi-tenant; multi-empresa até 3 CNPJs por conta; sem white-label |
| OS/chamados | **Sim** — módulo nativo (cadastro de serviço, geração de NFS-e da OS, envio e-mail/WhatsApp). **Não é assistência técnica especializada** (sem laudo, sem garantia, sem rastreio de peças) |
| Calibração ISO 17025 | **Não** |
| Forte em | Integração marketplaces (ML/Shopee/Amazon), preço de entrada baixo, base instalada >300 mil, API madura |
| Fraco em | Instabilidade recorrente em 2025, suporte demorado, downgrade quase impossível, foco e-commerce deixa serviços em 2º plano |
| Reclamações | "Sistema lento e cai toda hora" • "Suporte horrível e instabilidade" • "Impossibilidade de downgrade e cobrança indevida" — Reclame Aqui |

### 12.2 Tiny ERP (Olist)

| Item | Resposta |
|---|---|
| URL | https://tiny.com.br |
| Preço | A partir de ~R$ 99/mês (Começar) → Crescer → Evoluir → Potencializar. Olist não publica tabela fixa. Faixa típica R$ 99–R$ 500+/mês. Conta Digital Olist grátis se faturamento ≥ R$ 10k/mês, senão R$ 350 |
| Fundação | ~2012 (Bento Gonçalves/RS); adquirido pela Olist em 2022 |
| Módulos | vendas multicanal, estoque, financeiro, fiscal (NF-e/NFC-e/NFS-e), pedidos, picking & packing, multi-empresa (Crescer+), hub de marketplaces, conta digital |
| NF-e/NFS-e | Sim ambas; cobertura municipal [a confirmar] |
| Mobile | App Android + iOS; funcionalidades reduzidas |
| API | REST/JSON, v2.0 legada e v3 atual com OAuth 2.0; **webhooks só nos planos Evoluir/Potencializar**; limite 5 apps por conta |
| Multi-tenant | SaaS; multi-empresa interno; sem white-label |
| OS/chamados | **Parcial** — endpoint de Ordem de Produção (industrial) + Nota de Serviço, mas sem módulo dedicado de OS/chamados/assistência técnica com SLA/técnico/peças |
| Calibração ISO 17025 | **Não** |
| Forte em | Integração marketplaces (historicamente o melhor), conta digital integrada, hub Olist (frete + canais) |
| Fraco em | Queda de qualidade percebida pós-aquisição Olist, mudanças unilaterais de plano/preço, suporte que abandona chat, cancelamento difícil, sem exportação em massa de NFS-e |
| Reclamações | "Notas duplicadas, estoque manual, mudança unilateral de planos" • "Quero cancelar e não consigo" • "Atendimento finalizado sem solução" |

### 12.3 Omie

| Item | Resposta |
|---|---|
| URL | https://www.omie.com.br |
| Preço | A partir de R$ 99/mês (ERP básico) → Multivarejo a partir de R$ 209/mês → enterprise sob proposta. Omie Fit grátis pra MEI/micro. Reajuste anual IGP-M |
| Fundação | 2013 (São Paulo/SP) [a confirmar no site institucional] |
| Módulos | CRM, vendas, finanças (CP/CR, fluxo, conciliação), estoque, compras, produção industrial, **serviços e NFS-e (com Kanban de OS)**, fiscal (NF-e/NFC-e/NFS-e ilimitadas todos planos), PDV (Omie PDV), loja virtual, BPO contábil, marketplace Omie.Store |
| NF-e/NFS-e | Sim, **ilimitadas em todos planos**; cobertura municipal [a confirmar] |
| Mobile | App Android + iOS (consulta/aprovações) |
| API | REST + SOAP legado; doc developer.omie.com.br; inclusa em todos planos com rate limit; webhooks via Omie.Store |
| Multi-tenant | SaaS; programa de parceiros + BPO contábil estruturado; sem white-label nativo público |
| OS/chamados | **Sim** — módulo dentro de "Serviços e NFS-e", **Kanban customizável** (3-6 etapas), API completa (IncluirOS, ListarOS, faturamento em lote), integração direta com NFS-e e CR. Não é assistência técnica especializada |
| Calibração ISO 17025 | **Não** |
| Forte em | Módulo fiscal robusto (melhor do segmento PME pra regime complexo), ecossistema de apps (Omie.Store), integração nativa com escritórios contábeis (BPO), Kanban de OS pra serviços |
| Fraco em | Lentidão geral ("nuvem que pensa muito"), suporte por chat genérico, reajustes agressivos (~100% pra clientes antigos), roadmap lento, faltam filtros analíticos básicos |
| Reclamações | "Falhas graves: atualização manual de preços e impostos" • "Quedas constantes inviabilizam o uso" • "Omie PDV — produto e suporte que não funcionam" |

### 12.4 Conta Azul

| Item | Resposta |
|---|---|
| URL | https://contaazul.com |
| Preço | Essencial (MEI) ~R$ 119,90/mês anual com 20% off → Controle → Avançado ~R$ 290/mês (R$ 869,70 trimestral) → Performance (top com API). Cupons recorrentes ~21% off |
| Fundação | 2011 (Joinville/SC); **adquirida pela Visma (Noruega) em agosto/2025 por US$ 300 milhões (~R$ 1,7 bi)** — fundadores permanecem. Visma fez 140+ aquisições históricas (50 só em 2024). |
| Módulos | Financeiro (CP/CR, conciliação bancária automática — **diferencial**), vendas (orçamento → pedido → OS → NFS-e em 1 clique), fiscal (NF-e/NFC-e/NFS-e), estoque básico, propostas, integração contador forte, banco/cobrança (boleto/Pix), relatórios |
| NF-e/NFS-e | Sim; NFS-e depende de homologação municipal (lista pública aceita pedido de inclusão); MEI via Padrão Nacional. Número de municípios [a confirmar] |
| Mobile | App Android + iOS (consulta de saldo, vendas, NF, lembretes) |
| API | REST, **só a partir do plano Performance**; doc developers.contaazul.com [a confirmar detalhes públicos] |
| Multi-tenant | SaaS; programa Exclusivo pra Parceiros (contadores/BPO); sem white-label |
| OS/chamados | **Sim** — "Sistema de Ordem de Serviço" nativo, fluxo orçamento→OS→NFS-e em 1 clique. Mais voltado a prestadores simples; sem SLA, sem chamados/tickets |
| Calibração ISO 17025 | **Não** |
| Forte em | **Conciliação bancária automática** (referência de mercado), UX amigável pra não-técnicos, integração nativa com contadores (BPO maduro), fluxo orçamento→OS→NFS-e |
| Fraco em | Cancelamento/reembolso difícil (só 7 dias de janela), suporte robotizado e lento, frustração com "nova versão" (migração desde 2022 ainda gera dores), aumentos abusivos, estoque pobre, sem multi-empresa em todos planos |
| Reclamações | "Aumento abusivo e insatisfação" • "Suporte" • "Nova versão (frustração com migração)" |

### 12.5 Granatum

| Item | Resposta |
|---|---|
| URL | https://www.granatum.com.br |
| Preço | **Plano único** — R$ 269/mês site oficial (R$ 396 em sites comparadores, desatualizado). Trial 7 dias |
| Fundação | 2008 (versão gratuita, Webgoal) / 2010 (versão paga comercial) |
| Módulos | Financeiro completo (CP/CR, conciliação, fluxo, DRE), planejamento orçamentário (cenários), centros de custo e tags, cobranças automatizadas (cartão/boleto/Pix), NFS-e, recibos, relatórios, API |
| NF-e/NFS-e | NFS-e sim, integrado a **mais de 700 cidades**. NF-e (produtos) [provavelmente não] |
| Mobile | Sem app nativo de destaque público — produto web-first responsivo [a confirmar] |
| API | Pública, integra externos (citada nas funcionalidades), via Pluga e nativa; modelo de cobrança [a confirmar] |
| Multi-tenant | SaaS; sem white-label |
| OS/chamados | **Não** — sem módulo de OS operacional. Só emite NFS-e a partir de lançamentos financeiros. **Inadequado pra assistência técnica** |
| Calibração ISO 17025 | **Não** |
| Forte em | Financeiro denso e maduro (planejamento orçamentário, DRE, cenários — superior à média), cobrança automatizada bem resolvida, NFS-e em 700+ cidades, plano único simples |
| Fraco em | **Escopo estreito** (é financeiro+NFS-e, não ERP completo — sem estoque, CRM, OS, PDV), suporte horário comercial dependente de vídeo do bug, sem app mobile dedicado claro, base menor (menos integrações marketplace) |
| Reclamações | "Pior suporte que eu já vi" • "Grave falta de recursos de segurança" • "Cobrança 3x maior pra cliente antigo ao contratar plano novo" |

---

### 12.6 Auvo (Goiânia/GO + Florianópolis/SC)

> Adicionado por indicação do Roldão (16/05/2026) — concorrente horizontal de **field service** que ficou de fora da pesquisa inicial.

| Item | Resposta |
|---|---|
| URL | https://www.auvo.com • https://www.auvo.com.br |
| Fundação | **2015** (Goiânia/GO) por Gabriel Rodrigues, Valmir Caixeta e Danilo Silva. 2º escritório em Florianópolis/SC (2020). Aporte recente da Cloud9 Capital |
| Foco | **Gestão de equipes externas / field service** — OS digital, agenda, roteirização, checklist, captura de assinatura, rastreio GPS em tempo real. Verticais fortes: climatização/refrigeração, segurança eletrônica, energia solar, manutenção industrial |
| Módulos | Gestão (OS + agenda + GPS), Financeiro (NF), Auvo Bank (PIX/boletos), AuvoDesk (chamados — desacoplado), PMOC (HVAC), Cobranças, Despesas, Relatórios |
| ISO 17025 / calibração | **Não** — nenhuma menção a metrologia/17025 |
| NF-e / NFS-e | **Sim** (módulo Financeiro emite NF + Auvo Bank). ⚠️ reclamação ativa no Reclame Aqui (dez/2025) sobre emissão indevida de NF |
| OS / chamados | **Sim, é o core.** OS digital com checklist, fotos antes/depois, assinatura mobile, geração a partir de orçamento. AuvoDesk pra chamados/tickets (queixa: roda em plataforma separada, sem API pública) |
| Mobile | App nativo Android/iOS/iPad. **Offline [a confirmar]** — site descreve "totalmente online", mas reviews relatam dificuldade de sincronização |
| Deploy | SaaS na nuvem (web + mobile); sem on-premise |
| API | **Sim**, REST com APP KEY + TOKEN (token temporário 30 min). Integrações nativas com Conta Azul Pro, NectarCRM e ERPs |
| Multi-tenant | SaaS multi-tenant |
| Preço | **Sob consulta** / modular por nº de usuários + módulos. Sem tabela pública |
| Mercado-alvo | PME a média/enterprise com equipe de campo — **~8 mil clientes, 80 mil usuários ativos, 16 países LATAM**. Clientes: WEG, Daikin, Gree, Sem Parar. **Recusa explícita operações com <4 funcionários** |
| Forte em | OS digital madura, ecossistema modular amplo (PMOC, Bank, Cobranças), internacionalização LATAM, atendimento responsivo (~7h resposta média no RA), aporte recente |
| Fraco em | Bugs recorrentes (GPS, sincronização, emissão indevida de NF), AuvoDesk desacoplado e sem API, cobrança pós-cancelamento problemática (caso Serasa), **zero suporte a metrologia/17025**, preço opaco |
| Reclamações | "Problemas com app — sincronização e GPS" • "Notas fiscais indevidas" • "Preconceituosos e utópicos (recusa operação <4 func)" — Reclame Aqui |

**Posicionamento provável vs Aferê:** **concorrente horizontal de field service** — forte em OS/campo genérico, mas zero cobertura de calibração 17025/incerteza/rastreabilidade. Em assistência técnica de manutenção corretiva, **Auvo é provavelmente o concorrente mais perigoso do lado de OS de campo** (mais maduro que módulos de OS de Bling/Omie/Conta Azul). Se Roldão atender muito cliente com técnico de campo, Auvo é referência.

**Fontes:** https://www.auvo.com • https://scinova.com.br/com-escritorio-em-sc-auvo-tecnologia-recebe-investimento-da-cloud9-capital/ • https://empreenderemgoias.com.br/2024/04/02/empresa-goiana-para-gestao-de-equipes-se-consolida-na-america/ • https://www.reclameaqui.com.br/empresa/auvo-tecnologia/ • https://www.capterra.pt/software/201778/auvo

---

### 12.7 Síntese ERPs horizontais BR

**Confirmado nos 5:** **ninguém tem calibração ISO 17025.** Gap absoluto também nessa camada.

**OS / Assistência técnica:**
- **Bling, Omie, Conta Azul:** têm "OS" funcional, mas é sempre "orçamento → serviço → NFS-e" simples, nunca assistência técnica de verdade (sem laudo, sem rastreio de peças, sem garantia, sem fluxo de devolução de equipamento, sem agenda de técnico, sem SLA por contrato).
- **Tiny:** parcial (OS de produção industrial + nota de serviço).
- **Granatum:** zero.

**Dores recorrentes nos 5 (oportunidades competitivas extras):**

1. **Suporte ruim/lento em todos** → diferencial: SLA real, suporte humano em pt-BR via WhatsApp.
2. **Instabilidade (especialmente Bling, Omie)** → diferencial: uptime publicado em status page + SLA financeiro.
3. **Reajustes abusivos e cancelamento difícil** → diferencial: política transparente, cancelamento self-service, preço previsível.
4. **Migração de versão traumática (Conta Azul)** → diferencial: versionamento com convivência.
5. **Sem foco em empresa de serviço técnico** → todos vêm de e-commerce (Bling/Tiny), contabilidade (Conta Azul/Granatum) ou ERP industrial (Omie). Nenhum nasceu pra OS de assistência técnica nem pra calibração.

**Faixa de preço do segmento horizontal:** entrada R$ 55–120/mês, top R$ 300–500/mês (sem Elite/Enterprise sob proposta). Granatum é o mais caro no plano único (R$ 269).

**Posicionamento vs ERPs horizontais:** "Aferê faz tudo o que Bling/Omie/Conta Azul fazem pro seu financeiro/NFS-e — **e ainda faz o ciclo completo de calibração ISO 17025 que nenhum deles toca**. Sem precisar de 2 sistemas conversando por planilha."

---

## 13. Fontes adicionais consultadas (rodada 2)

- CalibraFácil — https://calibrafacil.com/
- ABC71 Sistema de Calibração — https://sistemadecalibracao.com.br/ • https://abc71.com.br/
- SoftExpert Calibration — https://www.softexpert.com/en/module/calibration/ • https://pt.wikipedia.org/wiki/SoftExpert
- Confience myLIMS — https://www.confience.io/mylims
- Sistema Autolab (Arkade) — https://sistema-autolab.com.br/ • https://br.linkedin.com/company/autolab-automacao
- ConfLab — https://www.conflab.com.br/ • https://saocarlos.usp.br/pesquisadores-do-iqsc-desenvolveram-software-para-validacao-de-metodos-e-calculo-de-incertezas/
- Bling — https://www.bling.com.br/planos-e-precos • https://developer.bling.com.br/bling-api • https://www.bling.com.br/funcionalidades/ordem-servico • https://www.reclameaqui.com.br/empresa/bling/
- Tiny ERP — https://tiny.com.br/planos • https://tiny.com.br/api-docs/api • https://www.ecommercebrasil.com.br/noticias/tiny-erp-olist-reformula-planos • https://www.reclameaqui.com.br/empresa/olist-oficial/
- Omie — https://www.omie.com.br/precos/ • https://developer.omie.com.br/ • https://ajuda.omie.com.br/pt-BR/articles/498949-cadastrando-uma-nova-ordem-de-servico • https://www.reclameaqui.com.br/empresa/omiexperience/
- Conta Azul — https://contaazul.com/planos/ • https://contaazul.com/funcionalidades/sistema-ordem-de-servico/ • https://contaazul.com/funcionalidades/nfs-e/ • https://braziljournal.com/visma-compra-a-contaazul-por-quase-r-2-bilhoes/ • https://www.reclameaqui.com.br/empresa/contaazul/
- Granatum — https://www.granatum.com.br/financeiro/precos-planos • https://www.granatum.com.br/financeiro/funcionalidades • https://controlefinanceiro.granatum.com.br/sobre-nos/ • https://www.reclameaqui.com.br/empresa/granatum-controle-financeiro/
