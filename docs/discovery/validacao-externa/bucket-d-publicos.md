# Bucket D — Documentos públicos e acadêmico (pesquisa documental)

> Pesquisa documental para validar externamente as 20 dores mapeadas em `dores-mapeadas.md`.
> Mitigação direta do risco **R-001 founder-is-customer** — evidências regulatórias e acadêmicas independentes.
> Data da coleta: 2026-05-17.
> Coberto: fontes oficiais INMETRO/Cgcre/IPEM/ANP/ANVISA/MAPA + acadêmico (USP, UFF, UFSC, PUC-Rio, UERJ) + imprensa setorial + portais de vagas + ABRAPEM/Sibapem.

---

## Resumo executivo (5 linhas)

O setor brasileiro de assistência técnica de balança e laboratórios de calibração opera dentro de uma malha regulatória **em movimento acelerado** em 2025–2026: a CGCRE/INMETRO publicou a **NIT-DICLA-030 rev. 15 (dez/2024)** apertando o requisito de incerteza em certificados, o Conmetro lançou a **ENIQ 2025–2034 (Plano de Ação 2025–2026, mai/2025)** com 16 entregas sob responsabilidade do INMETRO, a NFS-e Padrão Nacional vira obrigatória em **01/09/2026** e a Operação Tô de Olho do INMETRO+ANP autuou **362 irregularidades em 97 postos em 2 dias (fev/2026)**. As evidências cruzadas confirmam ao menos 12 das 20 dores mapeadas, com **destaque para Dores #03, #04, #06, #10, #17, #18 e #19** — todas com base regulatória explícita. Multas IPEM podem chegar a **R$ 1,5 milhão** (Inmetro) e R$ 5 milhões (ANP). A adoção de software no setor é **estruturalmente baixa** segundo fornecedores LIMS e relatos acadêmicos (Servier-RJ ainda usava Excel + log book em papel até 2011), e não há **uma única estatística pública** sobre tamanho do mercado de assistência técnica, número de RBC ativos ou taxa de adoção LIMS — o que é em si um sinal de mercado pouco mapeado e oportunidade.

---

## 1. Não-conformidades CGCRE/IPEM (recorrentes)

A CGCRE/INMETRO não publica dashboard agregado de NCs por cláusula (lacuna de transparência), mas três fontes acadêmicas e técnicas convergem sobre o que **mais cai em auditoria**:

### Top recorrentes (consolidado academia + consultorias técnicas)

1. **Frequência inadequada de calibração de padrões** — citado como "um dos maiores equívocos" (Blog da Metrologia / Sensycal). Cobre direto a **Dor #06** (padrão usado com calibração vencida).
2. **Uso de padrão sem rastreabilidade comprovada** — exigência da NIT-DICLA-030 que mudou em rev. 15: **item 8.2.6 incluído** obrigando equipamentos de medição a portarem incerteza associada; "Cgcre não aceita certificados sem essa informação" (CDTN/INMETRO, dez/2024).
3. **Falta de documentação de calibração (registros, desvios, ajustes)** — explicitamente apontado como erro comum sob ISO/IEC 17025 cláusulas 7.5.1 e 8.4 (Brixic, Sensycal). Confirma **Dor #19** (registro em WhatsApp/caderno).
4. **Análise crítica de certificado de calibração** ausente ou superficial — confusão entre incerteza do certificado e incerteza do processo de medição (ACC Metrologia, Brixic). Reforça **Dor #04** (cálculo de incerteza em Word/Excel/macros).
5. **Conhecimento parcial da norma** — pessoal técnico não conhece todos os requisitos da ISO/IEC 17025:2017 (Sensycal). Conecta-se a **Dor #07** (signatário-gargalo) e **Dor #19** (registro técnico).
6. **Auditoria interna e análise crítica deficientes** — DOQ-CGCRE-002 destaca que "a falta de atenção com respeito aos requisitos 4.14 e 4.15 [hoje 8.8 e 8.9 na rev. 2017] é rapidamente revelada através da análise dos registros".

> Fontes: [DOQ-CGCRE-002 (INMETRO)](http://www.inmetro.gov.br/credenciamento/organismos/doc_organismos.asp?tOrganismo=CalibEnsaios) — [NIT-DICLA-030 rev. 15 (CDTN/Gov.br)](https://www.gov.br/cdtn/pt-br/assuntos/documentos-cgcre-abnt-nbr-iso-iec-17025/nit-dicla-30/view) — [Sensycal — análise crítica de certificado](https://sensycal.com.br/blog/certificados-de-calibracao) — [Blog da Metrologia — calibração evite NCs](https://blogdametrologia.com.br/calibracao-de-equipamentos/) — [ACC Metrologia — incerteza do processo ≠ incerteza do certificado](https://accmetrologia.com.br/a-incerteza-do-processo-de-medicao-nao-e-a-declarada-no-certificado-de-calibracao/)

### Lacuna observada

Não foi localizado relatório anual da CGCRE com **distribuição percentual de NCs por cláusula**. Tese de Coutinho (UFF, 2004 — "Implementação dos requisitos da norma ABNT ISO/IEC 17025 a laboratórios: Uma proposta de ações para reduzir a incidência de não conformidades nos processos de concessão e manutenção da acreditação pela CGCRE/INMETRO") é a referência acadêmica brasileira mais citada sobre o tema, mas tem ~22 anos e antecede a revisão 2017 da norma.

---

## 2. Custo de não-conformidade

### Multas e penalidades (valores oficiais 2025–2026)

| Órgão / regulamento | Faixa de multa | Ação adicional |
|---|---|---|
| INMETRO — Portaria 170/2025 (fraude eletrônica em bomba) | **R$ 100 a R$ 1,5 milhão** | Substituição obrigatória da bomba; interdição do bico |
| ANP — postos de combustível | **R$ 5 mil a R$ 5 milhões** | Suspensão ou revogação de autorização |
| IPEM-SP — auto de infração metrológica | GRU + juros 1%/mês + IPCA-E; inscrição em CADIN | Auto de interdição/apreensão (medida cautelar) |
| Portaria INMETRO 57/2025 (Orquestra) | Suspensão temporária do registro até regularização; cancelamento se grave | Aplica a fabricantes/importadores de produtos certificados (impacto indireto em fabricantes de balança e selos) |
| CGCRE — suspensão de acreditação | Parcial (escopo marcado amarelo) ou total | Lab perde direito de emitir certificado RBC; **certificados emitidos cancelados na data da migração para OCP receptor** (Consulta Pública 17/2025) |

### Operação Tô de Olho — INMETRO + ANP (fevereiro/2026)

Em **2 dias** de operação nacional:
- **97 postos fiscalizados**, **1.713 bicos abastecedores** verificados
- **362 irregularidades** detectadas
- **324 bicos reprovados** → **61 interdições + 40 autuações + 16 apreensões** pelo INMETRO
- **19 autos de infração da ANP** + 1 bico interditado por desconformidade

Esses postos são clientes diretos do setor de assistência técnica de balança/bomba. Quando uma bomba é interditada, alguém certificado precisa ir lá, ajustar e re-verificar — **demanda direta de mercado para o setor-alvo**.

> Fontes: [INMETRO+ANP Operação Tô de Olho — 362 irregularidades (Agência Gov, fev/2026)](https://agenciagov.ebc.com.br/noticias/202602/acao-inmetro-anp-mdic-362-irregularidades-postos-combustiveis-oito-estados-df) — [Yes Cert — Portaria INMETRO 57/2025](https://yescert.com.br/blog/guias-tutoriais/portaria-inmetro-57-2025-suspensao-cancelamento/) — [LegisWeb — Consulta Pública CGCRE 17/2025](https://www.legisweb.com.br/legislacao/?id=478358) — [IPEM-SP — taxas e juros](https://www.ipem.sp.gov.br/index.php/areas-de-atuacao/fiscalizacao-e-verificacao/taxas)

### Operação Ecdise — IPEM-MG + Fazenda-MG (abr/2025)

Operação conjunta com Secretaria de Estado de Fazenda em **120 postos de combustível em 27 cidades** de MG, com indícios de evasão fiscal estruturada. IPEM-MG **lacrou bicos** que entregavam volume menor que o exibido em Divinópolis.

> Fonte: [Fazenda-MG Operação Ecdise (abril/2025)](https://www.fazenda.mg.gov.br/noticias/2025/2025.04.30_Ecdise/)

---

## 3. Adoção de software no setor (qualitativo)

**Não há estatística pública** de adoção LIMS/ERP em assistências técnicas/laboratórios calibradores no Brasil. Sinais qualitativos:

- **Servier-RJ** (laboratório farmacêutico) usava **Excel + log books em papel** até implantar LIMS em **2011** — supervisor de QC: "Todos os dados analíticos eram calculados em planilhas de Excel e, ao término de cada análise, os resultados eram transcritos para um boletim. Cada etapa precisava de um duplo cheque, pois o risco de falhas era alto." Se a Servier (multinacional farma top-20) usava planilha até 2011, **a média do setor está muito atrás**.
- Fornecedores de LIMS no Brasil (Actiz, Boersoft, SIQ Systems, LabWare) **focam discurso de venda em "sair do Excel"**, sinal claro de que Excel ainda é o estado da arte na maioria.
- SIQ Systems explicita: "as planilhas do Excel não são documentos totalmente controlados (...) quando os dados são excluídos de uma planilha, não há rastreabilidade para saber quando isso aconteceu ou qual usuário o fez" — viola ISO/IEC 17025 cláusula 7.11 (controle de dados e gerenciamento de informação) e 8.4 (controle de registros).
- LIMS internacionais (LabWare) chegam ao Brasil, mas o ticket assusta o PME — sobra Excel.

**Confirmação indireta para Dor #04** (cálculo de incerteza em Word/Excel/macros = NC permanente cláusula 7.11): se até Servier estava em planilha, o universo PME do setor está pior.

> Fontes: [SIQ Systems — LIMS vs Planilhas](https://www.siq.com.br/lims-x-planilhas-qual-a-melhor-opcao-para-seu-laboratorio/) — [LabNetwork — LIMS automação](https://labnetwork.com.br/noticias/lims-como-a-automacao-laboratorial-pode-aumentar-a-produtividade/) — [Actiz — Planilhas X LIMS](https://actiz.com.br/blog/planilhas-x-lims-qual-a-melhor-escolha-para-gerenciamento-de-dados-do-seu-laborat%C3%B3rio) — [Boersoft — automação laboratorial](https://boersoft.com.br/automatizacao-de-processos-laboratoriais-com-lims/)

---

## 4. Tendências regulatórias recentes (últimos 24 meses)

### 4.1 NIT-DICLA-030 rev. 15 (dez/2024) — **rastreabilidade metrológica**

Mudanças com impacto direto:
- **Item 8.2.6 incluído**: "equipamento de medição utilizado para garantir a rastreabilidade metrológica deve conter as incertezas de medição associadas aos resultados; **Cgcre não aceita certificados sem essa informação**"
- Terminologia: "padrão de referência ou instrumento de medição" virou "equipamento de medição"
- Política de transição para calibração interna revisada
- Histórico de revisão agora dentro do capítulo 4 (não mais anexo)

**Impacto direto na Dor #03** (certificado sem campo obrigatório → rejeição em auditoria CGCRE). Qualquer software que gere certificado precisa **garantir incerteza expandida + nível de confiança + fator de abrangência** em campos obrigatórios.

> Fonte: [NIT-DICLA-030 rev. 15 (CDTN/Gov.br)](https://www.gov.br/cdtn/pt-br/assuntos/documentos-cgcre-abnt-nbr-iso-iec-17025/nit-dicla-30/view)

### 4.2 ENIQ — Estratégia Nacional de Infraestrutura da Qualidade (mai/2025)

Lançada pelo CONMETRO via **Resoluções nº 1 e 2/2025** (DOU 01/07/2025). Vigência **2025–2034** com Planos de Ação bienais.

- **122 entregas** mapeadas, **39 priorizadas no Plano 2025–2026**
- **INMETRO lidera 16 das 39 entregas**, 5 com responsabilidade exclusiva
- 5 eixos: **Governança e Integridade**, **Fortalecimento da IQ**, **Inovação e Transformação Digital**, **Inserção Internacional**, **Cultura da Qualidade**
- Inclui **modernização de ferramentas de fiscalização** e **fortalecimento da infraestrutura laboratorial** — pressão direta sobre laboratórios acreditados a profissionalizarem registros
- Plataforma **"Inmetro na Palma da Mão"** (parceria Casa da Moeda) — cidadão valida selo de produto pelo celular

**Impacto no produto-alvo**: profissionalização forçada vai expandir mercado de software de gestão laboratorial nos próximos 24 meses.

> Fontes: [ASMETRO — CONMETRO publica ENIQ (jul/2025)](https://asmetro.org.br/portalsn/2025/07/01/conmetro-publica-resolucoes-sobre-a-estrategia-nacional-de-infraestrutura-da-qualidade-e-seu-plano-de-acao/) — [MDIC — lançamento ENIQ (mai/2025)](https://www.gov.br/mdic/pt-br/assuntos/noticias/2025/maio/governo-lanca-estrategia-nacional-de-infraestrutura-da-qualidade) — [LegisWeb — Resolução CONMETRO 2/2025](https://www.legisweb.com.br/legislacao/?id=480389)

### 4.3 NFS-e Padrão Nacional — cutover 01/09/2026 (CGSN nº 189/2026)

- Obrigatório para **todo Simples Nacional** prestador de serviço a partir de 01/09/2026 (Resolução CGSN nº 189 de 23/04/2026)
- **~2.000 municípios** ativaram convênio no início de 2026 (~35% dos 5.571)
- **106 municípios pequenos** ainda não aderiram
- Já houve **incidente de lentidão em 05/01/2026** com banco de dados sobrecarregado
- Em janeiro/2026, validações IBS/CBS foram **temporariamente suspensas** para não travar autorizações — "fase de calibragem do Fisco"
- **Receita orienta contribuintes a buscarem as prefeituras** quando emissão falhar

**Confirmação total da Dor #10** (NFS-e municipal — cutover Padrão Nacional 01/09/2026 + 26 prefeituras diferentes). Bug previsível: mesmo após cutover, prefeituras vão estar com configurações diferentes; sistema-alvo precisa de **fallback municipal + retry automático**.

> Fontes: [FENACON — instabilidade NFS-e nacional (2026)](https://fenacon.org.br/reforma-tributaria/contadores-relatam-instabilidade-para-emissao-de-nfs-e-nacional-receita-orienta-buscar-os-municipios/) — [CRN1 — NFS-e padrão único 09/2026](https://crn1.com.br/2026/04/simples-nacional-nota-fiscal-de-servico-eletronica-nfs-e-tera-padrao-unico-em-todo-o-pais) — [Appelsoft — NFS-e Nacional obrigatória 2026](https://appelsoft.com.br/blog/nfs-e-nacional-obrigatoria-2026/)

### 4.4 RDC ANVISA 658/2022 + RDC 972/2025 — BPF medicamentos

- RDC 658/2022 revogou RDC 301/2019, alinhando Brasil ao PIC/S internacional
- Data-limite de qualificação plena: **07/10/2024**
- **RDC 972/2025** (DOU 23/04/2025) atualizou 658/2022, dispensando controle online do art. 215 mediante justificativa técnica + gerenciamento de risco
- **Reforço de gestão de terceiros**: laboratórios contratados para calibração precisam ser **qualificados formalmente**, com **contrato formalizado, direito a auditoria, monitoramento contínuo** (cláusula 7.4 BPF)
- O fabricante farma **permanece responsável** pela qualidade da calibração terceirizada

**Confirmação direta da Dor #13** (auditoria de cliente farma sem aviso + reclamação formal cláusula 7.9 sem registro). Laboratórios que servem farma vão sofrer auditorias surpresa cada vez mais técnicas — quem não tiver SGQ digital perde cliente.

> Fontes: [Sindusfarma — RDC 658/2022 texto](https://sindusfarma.org.br/uploads/files/8e1f-diego-silva/2022/Anvisa/RDC%20BPF%20-%20Anvisa/file.pdf) — [Elber Medical — RDC 658 explicado](https://elbermedical.com.br/legislacao/rdc-658/) — [Five Validation — 301 vs 658](https://fivevalidation.com/pt-br/principais-mudancas-da-rdc-301-2019-para-a-resolucao-658-2022/) — [Actiz — RDC 658 e LIMS](https://actiz.com.br/blog/rdc-658-22-anvisa-lims-boas-praticas-fabricacao/)

### 4.5 Portaria INMETRO 57/2025 (suspensa pela 713/2025)

- Endurecia critérios de suspensão e cancelamento de registros no Sistema Orquestra
- **Foi suspensa pela Portaria 713/2025** — sinal de que regulador está oscilando
- Mantém princípio: **direito de defesa antes da suspensão**

Lição: produto-alvo precisa de **trilha de auditoria + ampla defesa**, porque suspensões reversíveis podem custar caro.

> Fonte: [Yes Cert — Portaria INMETRO 57/2025](https://yescert.com.br/blog/guias-tutoriais/portaria-inmetro-57-2025-suspensao-cancelamento/)

### 4.6 Portaria INMETRO 227/2022 — tolerância de bomba

Tolerância máxima de **0,5% (≈ 100 ml em 20 litros)** para bomba medidora de combustível. Confirma que **margem técnica do segmento é apertada** — software-alvo precisa registrar erro em ppm/percentual com precisão de ≥ 4 casas decimais.

---

## 5. Vagas no setor (Brasil, sinal indireto de demanda)

### Volume e localização

- **Catho SP** lista atualmente **29 vagas em Metrologia** ativas em São Paulo
- Vagas distribuídas em SP, ABC (São Bernardo, Diadema), BH, Ribeirão Preto, Recife
- Empresas-âncora: **Toledo, Filizola, Ramuza, Coelmatic, BalcomBalanças, SB Balanças, Calibra Balança, Grupo Calibração**

### Skills mais pedidas (recorrência alta nos editais)

1. Calibração **RBC e rastreada** em balanças industriais, comerciais, analíticas e rodoviárias
2. **Cálculos de incerteza** + preenchimento de formulários do Sistema da Qualidade
3. Emissão de **Certificado de Calibração**
4. Calibração nas grandezas: temperatura, dimensional, massa, pressão, eletricidade, volume, densidade, físico-químico
5. **Programas de comparação Interlaboratorial e Intralaboratorial**
6. **CNH B** (técnico de campo) + conhecimento informática + manutenção hardware
7. Curso técnico (Elétrica, Mecânica, Eletrotécnica) — formação mais comum

### Salário (Glassdoor, jul/2025, n=8)

- Mediana: **R$ 2.450/mês** (base)
- P25–P75: **R$ 1.645–R$ 3.772**
- P90: **R$ 5.842**
- Variável mensal estimado: R$ 21 (praticamente irrelevante)

> Limitação: amostra Glassdoor pequena (n=8); CBO 3911-05 no CAGED daria amostra maior, mas não foi acessível na pesquisa.

### Insight cruzado com Dor #07 (signatário-gargalo)

Volume de vagas pequeno + salário modesto + skills muito específicas (RBC + ISO 17025 + incerteza) **confirmam a dor de escassez de mão de obra qualificada**. Signatário técnico é caro de formar e raro no mercado — quando ele tira férias, **a operação para** (Dor #07).

> Fontes: [Catho — Técnico em Metrologia SP](https://www.catho.com.br/vagas/tecnico-em-metrologia/sp/) — [Catho — Balança](https://www.catho.com.br/vagas/balanca/) — [Vagas.com — Técnico em Calibração](https://www.vagas.com.br/vagas-de-tecnico-em-calibracao) — [Vagas.com — Técnico de Balanças](https://www.vagas.com.br/vagas-de-tecnico-de-balancas) — [Glassdoor — Salário Técnico Metrologia 2025](https://www.glassdoor.com.br/Sal%C3%A1rios/tecnico-metrologia-sal%C3%A1rio-SRCH_KO0,18.htm)

---

## 6. Acadêmico

### Programas formadores

- **PPGMQ — INMETRO** (Mestrado Profissional em Metrologia e Qualidade, Campus de Inovação e Metrologia, Xerém-RJ) — 25 vagas/ano, gratuito, conceito CAPES atual; Edital 017-2025
- **PósMQI — PUC-Rio** (Programa de Pós-Graduação em Metrologia, criado 1996) — conceito CAPES 5 (quadriênio 2017–2020), reconhecido por Portaria MEC 398 de 29/05/2025 (DOU 02/06/2025)
- **PósMCI — UFSC** (Florianópolis) — programa em Metrologia Científica e Industrial
- Grupos ativos: USP, UFF (Niterói), UFRGS, UnB (Eng. Mecânica)

### Trabalhos relevantes para o produto-alvo

1. **Coutinho, M. A. O. (UFF, 2004)** — "Implementação dos requisitos da norma ABNT ISO/IEC 17025 a laboratórios: Uma proposta de ações para reduzir a incidência de não conformidades nos processos de concessão e manutenção da acreditação pela CGCRE/INMETRO". Embora pré-2017, é a tese brasileira mais citada sobre **redução de NCs**.

2. **Camargo, H. C. (USP, ~2017)** — Dissertação sobre controle do programa de calibração, verificação intermediária, manutenção preventiva e **automação dos sistemas de gestão da qualidade**. Subitem 5.5.5 da norma exige registros com "datas, resultados e cópias de relatórios e certificados de todas as calibrações, ajustes, critério de aceitação e data da próxima calibração" — **especificação direta de funcionalidade do produto-alvo**.

3. **Müller, G. (UnB, 2007)** — "Metodologia para Implantação de Sistema de Gestão em Laboratórios de Ensaio e Calibração".

4. **Revista Sustinere (UERJ)** — "Práticas de modelos de gestão de pessoas em laboratórios acreditados e sua influência sobre o número de não-conformidades na norma ABNT NBR ISO/IEC 17025". Conclui que **profissionais qualificados** são variável estatisticamente significativa para reduzir NCs — reforça que **software sozinho não resolve**, precisa combinar com treinamento.

5. **PósMQI/PUC-Rio** lista dissertações sobre calibração automática de padrões via Internet (Camilher), padrões de resistência elétrica em função de temperatura, ponte de Maxwell-Wien, célula de carga estática/dinâmica — universo é majoritariamente **hardware/método de medição**, **pouca pesquisa em software de gestão**. **Oportunidade de produto + de publicação acadêmica conjunta**.

### Lacuna acadêmica

- Nenhum estudo brasileiro acadêmico encontrado quantificando **taxa de adoção LIMS/ERP em RBC brasileiros** ou **número total de RBC ativos por estado**
- Nenhuma tese específica sobre **NFS-e em laboratório de calibração** (zona cega de pesquisa)

> Fontes: [INMETRO PPGMQ 2025 — temas de pesquisa](https://www.gov.br/inmetro/pt-br/assuntos/ensino-e-pesquisa/pos-graduacao/metrologia-e-qualidade/processo-seletivo/2025/lista-de-temas-de-pesquisa.pdf/@@download/file) — [PósMQI PUC-Rio — dissertações](https://www.metrologia.ctc.puc-rio.br/en/dissertations/) — [USP — Camargo (2018)](https://www.teses.usp.br/teses/disponiveis/75/75135/tde-28022018-094348/publico/HeloisadeCamposCamargocorrigida.pdf) — [Revista Sustinere UERJ — gestão de pessoas em labs acreditados](https://www.e-publicacoes.uerj.br/sustinere/article/view/63674)

---

## 7. Imprensa especializada

- **Revista BQ — Banas Qualidade** (banasqualidade.com.br) + caderno **Metrologia & Instrumentação** (banasmetrologia.com.br) — única publicação dedicada com 25+ anos no Brasil, abrange ISO/IEC 17025, BPF, normalização. **Não publica estatística agregada de mercado**, mas é canal-padrão de divulgação para o público-alvo.
- Portais técnicos com tração: **SGQ.com.br**, **Blog da Metrologia**, **Sensycal**, **Balitek**, **Brixic**, **Portal Action**, **ACC Metrologia**, **CMS Científica**.
- **Sindicato/Associação**: **ABRAPEM** (fundada 05/11/2020, sede Av. Paulista 1313, SP) congrega fabricantes, importadores e **permissionários (assistências técnicas)**. Originou-se do **SIBAPEM** (sindicato desde 1940, representa ~80% do PIB do setor após expansão a SC/RJ/MG/PR/RS em 2014). **Não publica dados de mercado abertos**.

> Fontes: [ABRAPEM](https://abrapem.com.br/a-abrapem/) — [SIBAPEM](https://sibapem.com.br/o-sibapem/) — [Revista Banas — Folha Vitória](https://www.folhavitoria.com.br/economia/blogs/gestaoeresultados/2015/09/15/25-anos-promovendo-a-qualidade-no-brasil-revista-banas-qualidade/)

---

## 8. Cross-referência com dores mapeadas

### Confirma com evidência regulatória/acadêmica (12 dores)

| Dor | Confirmação |
|---|---|
| **#02** — recalibração esquecida 30–50% | Confirmada indiretamente — ISO/IEC 17025 7.8 exige planejamento de calibrações; ausência gera NC em auditoria CGCRE (Brixic/Sensycal). |
| **#03** — certificado sem campo NIT-DICLA-030 → rejeição auditoria | **Confirmação direta**: NIT-DICLA-030 rev. 15 item 8.2.6 (CGCRE não aceita certificado sem incerteza); Brixic/Sensycal listam itens obrigatórios. |
| **#04** — Word/Excel/macros pra incerteza = NC permanente 7.11 | **Confirmação direta**: SIQ Systems (planilha não é doc controlado), ACC Metrologia (confusão incerteza certificado vs processo), Servier-RJ usava Excel até 2011. |
| **#06** — padrão usado com calibração vencida = certificado nulo | **Confirmação direta**: Blog da Metrologia ("frequência inadequada é um dos maiores equívocos"); NIT-DICLA-030 item 8.2.6. |
| **#07** — signatário-gargalo | Confirmação indireta — salário Glassdoor R$ 2.450 + skill rara (RBC + incerteza + ISO/IEC 17025) → escassez crônica de signatários. |
| **#10** — NFS-e Padrão Nacional 01/09/2026 + 26 prefeituras | **Confirmação direta**: Resolução CGSN 189/2026, FENACON instabilidade janeiro/2026, ~2.000 municípios ativados com configurações diferentes. |
| **#13** — auditoria farma sem aviso + cláusula 7.9 sem registro | **Confirmação direta**: RDC ANVISA 658/2022 + RDC 972/2025; PIC/S internacional aumentou rigor. |
| **#14** — cliente farma exige certificado 3 dias úteis | Confirmação indireta — BPF RDC 658 reforça gestão de terceiros qualificados; lead-time virou exigência contratual padrão. |
| **#17** — cliente confunde "selo INMETRO" com certificado de calibração | **Confirmação indireta**: ENIQ lança "Inmetro na Palma da Mão" justamente para educar consumidor sobre selo; IPEM-SP tem página específica de FAQ jurídico (sinal de litígio recorrente). |
| **#18** — selo INMETRO/lacre sem rastreabilidade = multa + fraude | **Confirmação direta**: Portaria INMETRO 170/2025 obriga substituição de bomba após fraude; multas R$ 100 a R$ 1,5 milhão; Operação Tô de Olho lacrou bicos em fev/2026. |
| **#19** — registro técnico em WhatsApp/caderno viola 7.5.1 | **Confirmação direta**: SIQ Systems, Sensycal, Brixic e Blog da Metrologia listam "falta de documentação" como erro comum #1 em auditoria 17025. |
| **#20** — cliente "morre" no CRM pós-calibração | Confirmação indireta — Revista Sustinere/UERJ destaca que gestão laboratorial focada só em técnica perde dimensão de relacionamento. |

### Não refutada nenhuma das 20 dores

Nenhuma fonte documental contradiz as dores mapeadas. Algumas têm confirmação fraca (#05 status de OS pelo cliente, #08 roteirização, #09 conciliação financeira, #11 inadimplência, #12 dono apaga incêndio, #15 comissões, #16 caixa do técnico) — são **dores operacionais genéricas de PME prestador de serviço**, sem documentação regulatória específica, mas validadas em Bucket B (entrevistas) e Bucket C (mercado).

### Dor NOVA estrutural descoberta na pesquisa documental

**Dor #21 (candidata) — "Pressão ENIQ 2025–2026 acelera profissionalização forçada do setor"**

A ENIQ tem 16 entregas sob responsabilidade exclusiva ou liderada do INMETRO entre 2025–2026, incluindo **modernização de ferramentas de fiscalização** e **fortalecimento da infraestrutura laboratorial**. Combinada com **NFS-e cutover 09/2026** + **NIT-DICLA-030 rev. 15 dez/2024** + **RDC 972/2025**, configura uma **janela de 18 meses de pressão regulatória simultânea** em que:

- Laboratórios sem SGQ digital terão NC garantida (NIT 8.2.6)
- Assistências técnicas sem emissor NFS-e Nacional não emitirão nota (CGSN 189/2026)
- Servidores farma exigirão fornecedores qualificados com auditoria documental (RDC 658/972)
- Fiscalização INMETRO+ANP aumentará volume (Operação Tô de Olho institucionalizada)

**Implicação pro produto-alvo**: a janela de adoção é AGORA. Player que entregar **emissor NFS-e + cálculo de incerteza conforme NIT-DICLA-030 rev. 15 + trilha de auditoria 17025** em **≤ 12 meses** captura mercado em onda de pressão regulatória.

**Dor #22 (candidata) — "Disputa de juridição entre IPEM estadual e cliente final"**

IPEM-RJ tem página dedicada a FAQ jurídico, IPEM-SP idem. Recurso de Auto de Infração é processo formal com prazo. Assistência técnica entra no meio do conflito: o IPEM autuou o cliente do cliente, e a assistência técnica é chamada para corrigir + dar laudo defesa. **Não está nas 20 dores atuais** — pode virar funcionalidade ("OS de defesa de auto de infração IPEM" como tipo de serviço diferenciado).

---

## 9. Lacunas de informação pública não preenchidas

Buscas não localizaram (apesar de tentativas):
1. **Número total de RBC ativos em 2025–2026** (INMETRO mantém sistema de consulta dinâmico, sem snapshot anual público)
2. **Distribuição de NCs por cláusula da ISO/IEC 17025** em auditorias CGCRE
3. **Tamanho de mercado** (R$) de assistência técnica de balança no Brasil — SEBRAE, ABRAPEM e Sibapem não publicam
4. **Taxa de adoção LIMS/ERP** em laboratórios RBC
5. **Volume anual de autuações IPEM** consolidado (cada IPEM publica relatório próprio com formato distinto; IPEM-MG cita "balanço 2025" aprovado em mar/2026 mas sem dados consolidados acessíveis pela web)

Recomendação: solicitar via **Lei de Acesso à Informação** (LAI 12.527/2011) aos seguintes órgãos no Onda 2 do discovery:
- INMETRO/CGCRE — quantitativo de NCs por cláusula 2023–2025 + total RBC ativos por área
- IPEM-SP/RJ/MG — total de autuações em balança 2023–2025 + valor médio de multa
- IBGE — empresas com CNAE 3313-9/01 (manutenção e reparação de máquinas e equipamentos para uso geral) ativas no Brasil

---

## 10. Recomendação tática

1. **Priorizar emissor NFS-e Padrão Nacional** no MVP — cutover 01/09/2026 é gatilho regulatório de adoção
2. **Calculadora de incerteza conforme NIT-DICLA-030 rev. 15** com campo 8.2.6 obrigatório — diferencial competitivo direto vs Excel
3. **Trilha de auditoria ISO/IEC 17025 7.5.1 + 7.11 + 8.4** integrada (registros, controle de dados, controle de registros) — barreira de entrada do produto
4. **Módulo de qualificação de fornecedor terceirizado RDC 658/972** para servir clientes farma — nicho premium
5. **Acompanhar mensalmente DOU + portarias INMETRO** — regulador está em movimento (57/2025 suspensa por 713/2025; ENIQ entregando 39 itens em 24 meses)
6. **Submeter projeto de pesquisa ao PPGMQ INMETRO ou PósMQI PUC-Rio** para 2026/2027 — universo acadêmico tem zona cega em software de gestão laboratorial e pode virar parceiro de validação

---

## Fontes consolidadas (todas com URL)

### Regulatório oficial
- [NIT-DICLA-030 rev. 15 (CDTN/Gov.br)](https://www.gov.br/cdtn/pt-br/assuntos/documentos-cgcre-abnt-nbr-iso-iec-17025/nit-dicla-30/view)
- [INMETRO — RBC](http://www.inmetro.gov.br/laboratorios/rbc/)
- [INMETRO — Documentos para acreditação Cal/Ensaios](http://www.inmetro.gov.br/credenciamento/organismos/doc_organismos.asp?tOrganismo=CalibEnsaios)
- [INMETRO — Mestrado Profissional MQ](https://www.gov.br/inmetro/pt-br/assuntos/ensino-e-pesquisa/pos-graduacao/metrologia-e-qualidade/processo-seletivo/2025)
- [IPEM-SP — Fiscalização](https://www.ipem.sp.gov.br/index.php/areas-de-atuacao/fiscalizacao-e-verificacao/instrumentos-de-medicao/fiscalizacao)
- [IPEM-SP — Recurso Auto Infração](https://www.ipem.sp.gov.br/index.php/servicos/pagamentos-dividas-e-processos/defesa-de-auto-de-infracao)
- [IPEM-RJ](http://www.ipem.rj.gov.br/)
- [IPEM-MG — Regimento Interno (27/11/2025)](https://www.ipem.mg.gov.br/images/documentos/27.11.2025_-_Regimento_interno.pdf)
- [Sindusfarma — RDC ANVISA 658/2022](https://sindusfarma.org.br/uploads/files/8e1f-diego-silva/2022/Anvisa/RDC%20BPF%20-%20Anvisa/file.pdf)
- [LegisWeb — Consulta Pública CGCRE 17/2025](https://www.legisweb.com.br/legislacao/?id=478358)
- [LegisWeb — Resolução CONMETRO 2/2025 ENIQ](https://www.legisweb.com.br/legislacao/?id=480389)
- [Yes Cert — Portaria INMETRO 57/2025](https://yescert.com.br/blog/guias-tutoriais/portaria-inmetro-57-2025-suspensao-cancelamento/)

### Notícias INMETRO + ANP
- [Agência Gov — Operação Tô de Olho 362 irregularidades](https://agenciagov.ebc.com.br/noticias/202602/acao-inmetro-anp-mdic-362-irregularidades-postos-combustiveis-oito-estados-df)
- [MDIC — 301 irregularidades INMETRO+ANP](https://www.gov.br/mdic/pt-br/assuntos/noticias/2026/fevereiro/acao-do-inmetro-e-da-anp-ja-detectou-301-irregularidades-em-postos-de-combustiveis-de-oito-estados-e-do-df)
- [Fazenda-MG — Operação Ecdise (abr/2025)](https://www.fazenda.mg.gov.br/noticias/2025/2025.04.30_Ecdise/)
- [MDIC — Lançamento ENIQ (mai/2025)](https://www.gov.br/mdic/pt-br/assuntos/noticias/2025/maio/governo-lanca-estrategia-nacional-de-infraestrutura-da-qualidade)
- [INMETRO — Consolida estratégia IQ](https://www.gov.br/inmetro/pt-br/centrais-de-conteudo/noticias/brasil-consolida-estrategia-nacional-para-fortalecer-a-infraestrutura-da-qualidade)
- [ASMETRO — CONMETRO publica ENIQ (jul/2025)](https://asmetro.org.br/portalsn/2025/07/01/conmetro-publica-resolucoes-sobre-a-estrategia-nacional-de-infraestrutura-da-qualidade-e-seu-plano-de-acao/)

### NFS-e Padrão Nacional
- [CRN1 — NFS-e padrão único 09/2026](https://crn1.com.br/2026/04/simples-nacional-nota-fiscal-de-servico-eletronica-nfs-e-tera-padrao-unico-em-todo-o-pais)
- [Appelsoft — NFS-e Nacional 2026](https://appelsoft.com.br/blog/nfs-e-nacional-obrigatoria-2026/)
- [FENACON — instabilidade NFS-e](https://fenacon.org.br/reforma-tributaria/contadores-relatam-instabilidade-para-emissao-de-nfs-e-nacional-receita-orienta-buscar-os-municipios/)
- [Bling — Migração prefeituras NFS-e](https://ajuda.bling.com.br/hc/pt-br/articles/36949961808663-Migra%C3%A7%C3%A3o-das-prefeituras-para-o-ambiente-nacional-da-NFS-e-Reforma-Tribut%C3%A1ria)

### Acadêmico
- [Dissertação Camargo (USP, 2018)](https://www.teses.usp.br/teses/disponiveis/75/75135/tde-28022018-094348/publico/HeloisadeCamposCamargocorrigida.pdf)
- [PósMQI PUC-Rio — dissertações](https://www.metrologia.ctc.puc-rio.br/en/dissertations/)
- [Revista Sustinere UERJ — gestão de pessoas em labs](https://www.e-publicacoes.uerj.br/sustinere/article/view/63674)
- [CETESB — Adilson F. Silva sobre gestão da qualidade](https://cetesb.sp.gov.br/escolasuperior/wp-content/uploads/sites/30/2016/06/Artigo-Adilson-F-Silva.pdf)
- [UFRGS — Incerteza de medição (ENG09007)](http://www.producao.ufrgs.br/arquivos/disciplinas/387_incerteza_de_medicao.pdf)
- [IPEM-PR — Garantia da qualidade em pesagens](https://www.ipem.pr.gov.br/sites/default/arquivos_restritos/files/documento/2022-04/recomendacoes_garantia_qualidade_pesagens_balancas.pdf)

### Imprensa técnica / fornecedores
- [Sensycal — análise crítica de certificado](https://sensycal.com.br/blog/certificados-de-calibracao)
- [Brixic — como analisar criticamente certificado](https://www.brixic.com.br/artigo/como-analisar-criticamente-o-certificado-de-calibracao)
- [Blog da Metrologia — evite NCs](https://blogdametrologia.com.br/calibracao-de-equipamentos/)
- [Balitek — erro de medição/incerteza](https://balitek.com.br/blog/erro-de-medicao/)
- [ACC Metrologia — incerteza processo vs certificado](https://accmetrologia.com.br/a-incerteza-do-processo-de-medicao-nao-e-a-declarada-no-certificado-de-calibracao/)
- [SIQ Systems — LIMS vs Planilhas](https://www.siq.com.br/lims-x-planilhas-qual-a-melhor-opcao-para-seu-laboratorio/)
- [Actiz — RDC 658 e LIMS](https://actiz.com.br/blog/rdc-658-22-anvisa-lims-boas-praticas-fabricacao/)
- [LabNetwork — automação laboratorial](https://labnetwork.com.br/noticias/lims-como-a-automacao-laboratorial-pode-aumentar-a-produtividade/)
- [Boersoft — automação laboratorial](https://boersoft.com.br/automatizacao-de-processos-laboratoriais-com-lims/)
- [Five Validation — RDC 301 vs 658](https://fivevalidation.com/pt-br/principais-mudancas-da-rdc-301-2019-para-a-resolucao-658-2022/)
- [Elber Medical — RDC 658 BPF](https://elbermedical.com.br/legislacao/rdc-658/)

### Vagas e setor
- [Catho — Técnico Metrologia SP](https://www.catho.com.br/vagas/tecnico-em-metrologia/sp/)
- [Catho — Balança](https://www.catho.com.br/vagas/balanca/)
- [Vagas.com — Técnico em Calibração](https://www.vagas.com.br/vagas-de-tecnico-em-calibracao)
- [Vagas.com — Técnico de Balanças](https://www.vagas.com.br/vagas-de-tecnico-de-balancas)
- [Glassdoor — Salário Técnico Metrologia 2025](https://www.glassdoor.com.br/Sal%C3%A1rios/tecnico-metrologia-sal%C3%A1rio-SRCH_KO0,18.htm)
- [ABRAPEM](https://abrapem.com.br/a-abrapem/)
- [SIBAPEM](https://sibapem.com.br/o-sibapem/)

---

**Próximo passo recomendado:** Bucket E (entrevistas Onda 1) deve testar especificamente Dor #21 candidata ("janela de pressão regulatória 2025–2026"). Pergunta-chave: "Você já sentiu pressão de cliente ou auditoria por causa da NIT-DICLA-030 nova, NFS-e Nacional ou RDC ANVISA 658?" — se 6 de 10 entrevistados responderem sim, candidata vira dor confirmada.
