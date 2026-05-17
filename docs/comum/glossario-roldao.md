# Glossário pro Roldão

> **Pra que serve:** Roldão NÃO programa. Os documentos do projeto usam termos técnicos que ele não tem obrigação de conhecer. Este glossário traduz tudo em PT-BR humano.
>
> **Como usar:** quando ler um termo em qualquer doc e não entender, vir aqui. Ordem alfabética.
>
> **Atualizado:** 2026-05-17 (versão pós-auditoria 12 agentes). 236 termos (era 227 + 9 novos).

---

## Como consultar

Termos organizados em 4 grandes grupos (mas a listagem abaixo é em **ordem alfabética estrita** pra busca rápida — use Ctrl+F):

1. **Termos de produto / UX / negócio** (job, MVP, ICP, churn, etc.)
2. **Termos de programação / engenharia / segurança** (API, multi-tenant, hook, RBAC, etc.)
3. **Termos de metrologia / calibração** (RBC, GUM, EA-4/02, etc. — Roldão domina, ficam aqui só pra referência)
4. **Termos fiscais / regulatórios / compliance** (LGPD, NFS-e, PCI, etc.)

> **Marcação `(você sabe — só pra referência)`:** termo do dia a dia do setor de calibração que o Roldão conhece bem. Não precisa traduzir, fica aqui pra padronizar a grafia que aparece nos docs.
>
> **Marcação `[a confirmar pelo Roldão]`:** termo onde a fonte é secundária ou onde existe ambiguidade. Antes de virar invariante de produto, validar.

---

## Glossário alfabético

### A

- **ABNT** — Associação Brasileira de Normas Técnicas. É quem publica a versão brasileira oficial das normas ISO. Ex: ISO/IEC 17025 vira NBR ISO/IEC 17025.
- **ABRASF** — Associação Brasileira das Secretarias de Finanças das Capitais. Foi quem criou o padrão antigo de NFS-e que as prefeituras usavam. Está sendo encerrado em favor do Padrão Nacional.
- **Acreditação** — selo oficial do INMETRO que diz "este laboratório cumpre a norma ISO/IEC 17025 e pode emitir certificado com marca RBC". *(você sabe — só pra referência)*
- **ADN** — Ambiente de Dados Nacional (da NFS-e). Banco de dados nacional pra onde toda nota fiscal de serviço tem que ser espelhada a partir de 2026, mesmo as emitidas em sistemas próprios de prefeitura (SP, Goiânia etc.).
- **ADR** — Architecture Decision Record / Registro de Decisão de Arquitetura. Documento curto onde a gente registra por que escolheu uma solução técnica, pra não esquecer depois. Ex: ADR-0000 (uso de IA), ADR-0001 (stack).
- **Adiantamento** — dinheiro entregue ao técnico antes da viagem pra cobrir despesas em campo (combustível, alimentação, hospedagem). Depois ele "presta contas" anexando os comprovantes.
- **Ajuste** — operação que mexe no instrumento pra corrigir o erro de medição (diferente de calibração, que só mede o erro sem corrigir). *(você sabe — só pra referência)*
- **ANATEL** — Agência Nacional de Telecomunicações. Aparece se o cliente for empresa de telecom.
- **ANP** — Agência Nacional do Petróleo. Aparece em cliente de postos de combustível.
- **ANPD** — Autoridade Nacional de Proteção de Dados. Órgão federal que fiscaliza LGPD e aplica multa quando há vazamento de dados.
- **ANS** — Agência Nacional de Saúde Suplementar. Aparece em cliente de plano de saúde / hospital.
- **Anti-job** — algo que o produto **NÃO** vai fazer, deliberadamente. Listar serve pra evitar inchar o sistema com coisas que não são problema nosso (ex: o sistema não vai fazer folha de pagamento — é anti-job; usa integração externa).
- **ANTT** — Agência Nacional de Transportes Terrestres. Importante pra UMC (caminhão da calibração rodoviária) — pode exigir registro no RNTRC.
- **Anvisa** — Agência Nacional de Vigilância Sanitária. Aparece em cliente farma/saúde, que pede rastreabilidade pra RDC 658/2022 ou GMP.
- **API** — "Application Programming Interface". Em humano: o "encaixe" técnico que permite dois sistemas conversarem direto, sem humano copia-cola. Ex: o sistema da gente conversa com o BaaS fiscal por API pra emitir NFS-e.
- **Ariba** — portal de compras corporativas usado por grandes empresas pra contratar fornecedores. Se o lab quiser vender pra cliente grande, às vezes precisa estar cadastrado lá.
- **Atestado de capacidade técnica** — documento que cliente antigo emite dizendo "essa empresa me atendeu bem". Vira "currículo" da empresa em licitação pública.
- **ATPP** — Agente de Tratamento de Pequeno Porte. Categoria criada pela ANPD pra MEI/ME/EPP — tem prazos dobrados e algumas dispensas (ex: não precisa designar DPO formal).
- **Audit trail** (trilha de auditoria) — registro automático de "quem mexeu em que, quando, antes e depois". Obrigatório no produto pra ISO 17025 e LGPD.
- **AWS KMS** — serviço da Amazon pra guardar chaves de criptografia. A gente usa só pra chaves, não pra hospedar o sistema (que fica na Hostinger BR).

### B

- **Backblaze B2** — serviço de armazenamento de arquivos na nuvem, mais barato que AWS S3. A gente usa pra guardar PDF de certificado em modo WORM (não pode ser apagado nem alterado).
- **Bacen** — Banco Central do Brasil. Quem regula PIX, Open Finance e o que bancos podem/não podem fazer.
- **BaaS fiscal** — "Banking-as-a-Service" mas fiscal. Empresa que faz a parte de emitir NFS-e/NF-e por todos os municípios e estados do Brasil pra gente (Focus NFe, PlugNotas, TecnoSpeed). A gente paga assinatura pra eles em vez de manter integração com cada município.
- **BCB** — sigla curta de Banco Central do Brasil (mesmo que Bacen).
- **Beamex / Presys / Fluke** — fabricantes de instrumentos de medição que os labs do nosso ICP geralmente usam.
- **Big Job** — um dos 8-10 grandes "trabalhos a serem feitos" centrais do produto, no framework JTBD. São os jobs que "vendem sozinhos" — se o sistema resolve um Big Job, o cliente compra.
- **Big Jobs cobertos** — quantos dos N Big Jobs principais cada concorrente atende. Métrica usada na análise comparativa.
- **Bling** — ERP horizontal popular de PME no Brasil. Não é concorrente direto (não tem ISO 17025), mas muitos clientes usam e a gente precisa entender como ele faz NFS-e.
- **BPF** — Boas Práticas de Fabricação (farma/alimentos). Anvisa RDC 658/2022 é uma BPF.
- **Branch** — em humano: uma "linha de trabalho" paralela no código. Permite trabalhar numa correção sem mexer no sistema que está funcionando. O equivalente pra Roldão: "cópia de rascunho do sistema, antes de salvar a versão oficial".
- **Build** — em humano: o processo automático que monta o programa final a partir do código. Tipo "compilar a planilha pra ela rodar".
- **Bus factor** — quantas pessoas precisam ser "atropeladas pelo ônibus" pra o projeto morrer. Bus factor = 1 é arriscado (= Roldão sozinho).

### C

- **Caixa do Técnico** — controle das despesas que o técnico faz em campo (adiantamento + prestação de contas). Módulo central do produto.
- **Calibração** — operação que estabelece a relação entre o que o instrumento mostra e o valor real (rastreado). Diferente de "ajuste" e "verificação". *(você sabe — só pra referência)*
- **CC-e** — Carta de Correção Eletrônica. Permite corrigir erros não-tributários numa NF-e já emitida (até 30 dias).
- **CDC** — Código de Defesa do Consumidor (Lei 8.078/90). Aplica quando o cliente final é PF.
- **CDE** — Cardholder Data Environment. O "ambiente" do sistema que toca dado de cartão de crédito. Se o produto tocar nisso, vira PCI-DSS.
- **Cgcre / CGCRE** — Coordenação Geral de Acreditação do INMETRO. É quem acredita os laboratórios RBC. *(você sabe — só pra referência)*
- **Certificado digital A1/A2/A3** — versões diferentes do certificado digital ICP-Brasil. A1 = arquivo, A3 = token/cartão. Necessário pra assinar NF-e e certificado de calibração com validade jurídica.
- **Certificado de calibração** — o documento final que o lab entrega ao cliente, com resultado, incerteza e rastreabilidade. *(você sabe — só pra referência)*
- **Churn** — taxa de cliente que cancela a assinatura. Churn alto = sistema ruim ou preço errado.
- **CI** ou **CI/CD** — Continuous Integration / Continuous Deployment. Em humano: "robô que testa o código toda vez que a gente salva, e que sobe pro servidor automaticamente quando passa". Pra Roldão: "controle de qualidade automático antes de o cliente ver".
- **CMC** — Calibration and Measurement Capability. A "melhor incerteza" que o lab consegue declarar pra cada grandeza/faixa no escopo de acreditação. *(você sabe — só pra referência)*
- **CMN** — Conselho Monetário Nacional. Aparece nas resoluções de Open Banking.
- **CNAB 240 / CNAB 400** — formatos antigos de arquivo bancário pra trocar dados de pagamento/cobrança com o banco. Hoje sendo substituído por PIX e API direta.
- **CNAE** — Código Nacional de Atividade Econômica. Define que tipo de empresa o cliente é (lab de calibração tem CNAE 7120-1/00).
- **Commit** — em humano: cada "save" individual do código no sistema de versões. A gente fala "fiz commit" como vocês diriam "salvei a alteração".
- **Compliance** — conformidade com regras (LGPD, ISO 17025, Bacen). Significa "cumprir o que a lei/norma manda".
- **ComprasNet** — portal de compras do governo federal. Pra vender pro setor público, é onde licitação acontece.
- **Conjoint analysis** — método de pesquisa de mercado que mede o quanto cada característica de um produto contribui pra disposição a pagar (WTP). Ex: "quanto vale, em R$/mês, ter portal de cliente vs ter app mobile vs ter NFS-e integrada?". Usado em V-2 (WTP test do `validacao-ativa.md`) numa versão simplificada via Typeform.
- **Coupa** — concorrente do Ariba (portal de compras corporativas).
- **CSAT** — Customer Satisfaction Score. Pesquisa rápida "deu 1 a 5 estrelas, gostou do atendimento?".
- **CSRT** — Código de Segurança do Responsável Técnico (NF-e). Obrigatório em algumas UFs (PR desde 04/2025).
- **CT-Dicla** — Comitê Técnico de Acreditação de Laboratórios do INMETRO. *(você sabe — só pra referência)*

### D

- **DANFE** — Documento Auxiliar da NF-e (a "espelhada" em PDF da nota fiscal eletrônica).
- **DANFSe** — versão DANFE pra NFS-e (nota fiscal de serviço).
- **DCTFWeb** — declaração federal de tributos. Aparece se a empresa tem folha de pagamento.
- **Decisão fundadora** — o projeto usa em **DOIS sentidos**. Cuidado pra não confundir:
  - **De PRODUTO** (Roldão 17/05/2026): os **4 blocos canônicos de escopo** — Frota+UMC+Caixa do técnico; Comissões configuráveis; Cliente 360°/CRM contínuo; Estoque multi-local com lacre + selo INMETRO. Esses 4 blocos não saem do escopo do MVP/produto sem ADR formal.
  - **De ENGENHARIA** (D1–D6, 16/05/2026): princípios de processo — D1 Spec Kit; D2 spec-as-source; D3 nomenclatura híbrida; D4 devcontainer; D5 CODEOWNERS; D6 operação dual (Claude Code + Codex CLI sobre AGENTS.md canônico).
- **Deploy** — em humano: subir uma nova versão do sistema pro servidor onde os clientes acessam. Pra Roldão: "fui ao ar com a correção / com a feature nova".
- **Deriva (drift)** — variação contínua da medição do instrumento ao longo do tempo. *(você sabe — só pra referência)*
- **Devcontainer** — ambiente de desenvolvimento padronizado dentro de uma "caixinha" (container). Garante que todo mundo trabalhe com mesmas versões. Decisão fundadora D4.
- **DF-e** — sigla genérica que cobre NF-e, NFC-e, CT-e, BP-e, etc. — todos os "documentos fiscais eletrônicos".
- **DNIT** — Departamento Nacional de Infraestrutura de Transportes. Fiscaliza balança rodoviária em rodovia federal.
- **Domínio** — área temática de software (ex: "domínio metrologia", "domínio financeiro"). Não é o `.com.br` — esse é "nome de domínio".
- **DOQ-CGCRE-008, -019, -053, -090** — documentos do INMETRO que dão orientações práticas pra cálculo de incerteza em diferentes tipos de calibração. *(você sabe — só pra referência)*
- **DPA** — Data Processing Agreement. Contrato entre quem trata os dados (Roldão como SaaS) e o cliente, explicando como os dados são tratados, onde, por quanto tempo.
- **DPO** — Data Protection Officer (em PT: Encarregado de dados). Pessoa designada pra responder pela LGPD na empresa. ATPP pode dispensar; demais agentes têm obrigação.
- **DRE** — Demonstrativo de Resultado do Exercício. Relatório contábil de "quanto entrou, quanto saiu, quanto sobrou".

### E

- **EA-4/02** — guia europeu de cálculo de incerteza em calibração. Base do NIT-DICLA-021. *(você sabe — só pra referência)*
- **e-MAG** — Modelo de Acessibilidade em Governo Eletrônico. Padrão brasileiro de acessibilidade web.
- **EMA / EMP** — Erro Máximo Admissível / Erro Máximo Permitido. Limite legal do erro que um instrumento pode ter pra ser aprovado em verificação metrológica. *(você sabe — só pra referência)*
- **End-customer / cliente final** — quando o doc fala "cliente do tenant" significa o cliente do laboratório que usa o nosso SaaS. NÃO é o nosso cliente direto. Ex: laboratório XYZ usa o sistema = nosso "tenant"; a fábrica que contrata o laboratório XYZ = "cliente final / end-customer".
- **Endpoint** — em humano: "endereço" específico de uma API onde o sistema fala. Pra Roldão: "porta de comunicação que o sistema usa pra falar com outro sistema".
- **EP** — Ensaio de Proficiência. Lab participa de comparação com outros labs pra provar competência. *(você sabe — só pra referência)*
- **EPEC** — Evento Prévio de Emissão em Contingência (NF-e). Quando o sistema da SEFAZ está fora, dá pra emitir NF-e mesmo assim em modo "vou retransmitir depois".
- **ERP** — Enterprise Resource Planning. "Sistema integrado de gestão" que cobre múltiplas áreas (financeiro, comercial, operação) no mesmo lugar. É o que a gente está construindo.
- **EURACHEM / CITAC** — entidade europeia que publica guias de cálculo de incerteza, especialmente pra química analítica. *(você sabe — só pra referência)*

### F

- **FAPI 2.0** — padrão técnico de segurança usado em Open Finance (Financial-grade API).
- **Fake door** — em humano: "testar interesse antes de construir". Cria-se botão/link pra uma feature que ainda **não existe**; mede-se quantos cliques; se for alto, vale construir. É um tipo de smoke test. Risco ético: usuário clica esperando funcionar, frustra se receber "em breve" — então usa-se em landing pública, não em sistema de cliente pagante.
- **Fluxo de caixa** — relatório financeiro de "quando entra dinheiro e quando sai".
- **Folha (folha de pagamento)** — calcular salário, INSS, FGTS, IR de funcionários. Anti-job do nosso produto — vai por integração com Pontomais/Senior/Sankhya RH.
- **Founder is customer** — situação onde o fundador do produto é o cliente típico. É risco #1 do projeto (R-001): produto vira customização disfarçada da empresa do Roldão e não generaliza pra outras.
- **Frota** — controle dos veículos da empresa (carros + UMC): documento, manutenção, combustível, multas, custo total.
- **Funil** (de vendas) — etapas pelas quais um possível cliente passa até virar cliente pagante: prospect → lead → orçamento → contrato.

### G

- **Gap** — "buraco" no mercado: dor que ninguém atende. Ex: "gap confirmado — controle de UMC integrado com OS de calibração não existe no mercado BR".
- **GMP** — Good Manufacturing Practice. Padrão internacional de boas práticas de fabricação (farma).
- **GAMP** — Good Automated Manufacturing Practice. Versão de GMP focada em sistemas computadorizados de farma.
- **Grafana Cloud** — serviço que mostra gráficos de "como o sistema está rodando" (uso de CPU, erros etc.). A gente vai usar.
- **GUM** — Guide to the Expression of Uncertainty in Measurement (JCGM 100). Bíblia mundial do cálculo de incerteza. *(você sabe — só pra referência)*

### H

- **Hash** — "impressão digital" matemática de um arquivo ou registro. Se mudar 1 vírgula no registro, o hash muda totalmente. A gente usa pra blindar a trilha de auditoria.
- **Hook** — em humano: "gatilho automático" que dispara antes ou depois de uma ação. Ex: hook que **bloqueia** salvar o código se não passar nos testes; hook que **bloqueia** emissão de certificado se padrão estiver vencido.
- **Homologação** — ambiente "de teste" oficial onde a gente valida antes de ir pra produção. Ex: SEFAZ tem ambiente de homologação pra testar emissão de NF-e sem cair em multa.
- **Hostinger** — provedor de servidor onde a aplicação vai rodar (VPS KVM 4, São Paulo BR). Decisão fundadora.

### I

- **IBS / CBS** — novos impostos da Reforma Tributária (substituem ICMS/ISS/PIS/COFINS gradualmente até 2032).
- **ICP** — Ideal Customer Profile / perfil de cliente ideal. Quem é o cliente típico que a gente quer atender. Ex: PME 30-50 funcionários, perfil A/B, faturamento 5-25M.
- **ICP-Brasil** — Infraestrutura de Chaves Públicas Brasileira. O sistema oficial de certificado digital com validade jurídica no Brasil. NÃO confunda com ICP (Ideal Customer Profile).
- **ILAC MRA** — acordo internacional entre organismos de acreditação. Quando o certificado do lab brasileiro tem marca ILAC MRA, vale também no exterior. *(você sabe — só pra referência)*
- **ILAC G8 / G17 / G18 / G24** — guias ILAC sobre regras de decisão, incerteza, escopos e intervalos de recalibração. *(você sabe — só pra referência)*
- **Incerteza de medição** — parâmetro que diz "quanto a medição pode estar errada". *(você sabe — só pra referência)*
- **INDOP / cIndOp** — código de indicador de operação nas novas notas IBS/CBS.
- **INMETRO** — Instituto Nacional de Metrologia, Qualidade e Tecnologia. *(você sabe — só pra referência)*
- **INSS** — imposto sobre folha de pagamento.
- **IPEM** — Instituto de Pesos e Medidas (cada estado tem o seu, ligado ao INMETRO via RBMLQ-I). Faz a verificação metrológica legal de balança/bomba de combustível.
- **IPQ/OQ/PQ** — Installation Qualification / Operational Qualification / Performance Qualification. Etapas de validação de equipamento exigidas em farma (Anvisa, FDA).
- **IRRF** — Imposto de Renda Retido na Fonte. Aparece em fatura PJ.
- **ISO/IEC 17025:2017** — a norma central de laboratórios de ensaio e calibração. *(você sabe — só pra referência)*
- **ISS** — imposto municipal sobre serviços. Varia por município.
- **Invariante** — regra do produto que **nunca pode ser violada**. Ex: INV-002 ("emissão sem cadeia de rastreabilidade bloqueia"). Cada invariante vira um hook técnico.

### J

- **JCGM** — Joint Committee for Guides in Metrology. Comitê internacional que mantém o GUM e o VIM. *(você sabe — só pra referência)*
- **Job killer** — um job tão central que, se o produto não resolve, o cliente nem cogita comprar. Sinônimo de "deal breaker".
- **JTBD** — Jobs-To-Be-Done. Framework de produto que pergunta "qual o trabalho que o cliente está tentando concluir?", em vez de listar features.

### K

- **KPI** — Key Performance Indicator. Indicador chave que a empresa acompanha. Ex: "número de OS por técnico/mês".
- **KMS** — Key Management Service (ver AWS KMS).

### L

- **LBI** — Lei Brasileira de Inclusão (Lei 13.146/2015). Obriga sites/apps a serem acessíveis.
- **Lead** — possível cliente que demonstrou interesse mas ainda não comprou.
- **Leap-of-faith (LEAP)** — premissa crítica de **baixa confiança**. Se for falsa, a empresa morre. Marcar uma hipótese como LEAP força priorizar a validação dela **antes** de comprometer recursos. Ex no Aferê: F-1 (modelo 100% agentes substitui consultor humano) é um LEAP central — se falhar, todo o plano de defesas anti-erro precisa ser refeito.
- **LIMS / ELN / LES** — softwares de laboratório (Laboratory Information Management System / Electronic Lab Notebook / Laboratory Execution System). Concorrentes/adjacentes ao nosso produto.
- **Lint** — verificação automática de "estilo" do código. Garante padronização. Pra Roldão: "corretor ortográfico do código".
- **LGPD** — Lei Geral de Proteção de Dados (Lei 13.709/2018). Equivalente brasileiro do GDPR europeu.

### M

- **MAPA** — Ministério da Agricultura. Aparece em cliente de frigorífico.
- **Marco Civil da Internet** — Lei 12.965/2014. Obriga provedor de aplicação (= nosso SaaS) a guardar logs de acesso por 6 meses.
- **MED** — Mecanismo Especial de Devolução. Recurso do PIX pra devolução em caso de fraude.
- **MES** — Manufacturing Execution System. Software de execução de produção industrial.
- **Metrologia legal** — área da metrologia regulada pela lei (balança comercial, bomba de combustível, etilômetro, taxímetro). Diferente da calibração RBC, que é voluntária. *(você sabe — só pra referência)*
- **MFA** — Multi-Factor Authentication. Login com senha + código no celular. Obrigatório pra usuários com acesso a CDE (PCI-DSS).
- **Migration** — em humano: mudança na estrutura dos dados salvos (adicionar uma coluna nova no banco, mudar formato). Pra Roldão: "mudança na estrutura dos dados salvos — pode mexer no que o cliente já tem cadastrado".
- **Mock / fixture** — em humano: "dados falsos pros testes". Pra Roldão: "cliente falso, OS falsa, certificado falso, só pra testar o sistema sem mexer em dado real".
- **MODBUS / OPC-UA** — protocolos industriais pra ler dado direto do instrumento. Pode ser usado pra coletar leitura automática em vez de digitar.
- **MOC** — Manual de Orientação ao Contribuinte (NF-e). Documento técnico da SEFAZ que diz como emitir nota fiscal.
- **Moat** — "fosso defensivo". O que protege o produto da concorrência (no caso da gente: profundidade técnica RBC + UX moderna + módulos integrados).
- **MOPP** — Movimentação Operacional de Produtos Perigosos. Curso obrigatório pra motorista que transporta carga sensível (algumas configurações da UMC podem exigir).
- **MR / MRC** — Material de Referência / Material de Referência Certificado. Padrão químico/físico rastreado, usado pra calibrar. *(você sabe — só pra referência)*
- **MTLS** — mutual TLS. Modo de autenticação reforçada usado em Open Finance.
- **Multi-tenant** — em humano: "um mesmo sistema serve vários clientes ao mesmo tempo, com dados separados". Pra Roldão: "uma única instalação do sistema atende a Empresa A, a Empresa B, a Empresa C — sem elas verem dados uma da outra". É o nosso modelo.
- **Mystery shopping** — pesquisa onde a gente liga pro concorrente fingindo ser cliente, pra entender preço/atendimento.

### N

- **NBR** — Norma Brasileira (ABNT). Ex: NBR ISO/IEC 17025 = versão brasileira oficial da ISO/IEC 17025.
- **NBS** — Nomenclatura Brasileira de Serviços. Código de 9 dígitos obrigatório nas notas IBS/CBS a partir de 2026.
- **NC** — Não Conformidade. Quando algo sai do padrão ISO 17025 (ex: padrão vencido foi usado). Tem que abrir ação corretiva (AC).
- **NF-e** — Nota Fiscal Eletrônica (mercadoria, estadual). Modelo 55.
- **NFS-e** — Nota Fiscal de Serviços Eletrônica (municipal). Em transição pro Padrão Nacional desde 01/01/2026.
- **NFC-e** — Nota Fiscal de Consumidor Eletrônica (varejo final).
- **NIT-DICLA-016 / -021 / -028 / -030 / -031** — documentos do INMETRO sobre auditoria interna, expressão de incerteza, avaliação, rastreabilidade, ciclo de acreditação. *(você sabe — só pra referência)*
- **NPS** — Net Promoter Score. Pesquisa "você recomendaria a um amigo?". Vai de -100 a +100.
- **North Star Metric** — a métrica única que indica se o produto está crescendo de forma saudável. Ex: "número de certificados emitidos via produto por mês".

### O

- **ODR / Onboarding** — em produto: o processo de "primeira experiência" do cliente no sistema, do cadastro até o primeiro uso real.
- **OFX** — formato antigo de arquivo de extrato bancário. Hoje quase substituído por Open Finance.
- **OIML D 31** — recomendação internacional sobre software pra instrumentos legalmente regulados. Referência pra validação de software metrológico. *(você sabe — só pra referência)*
- **OKR** — Objectives and Key Results. Sistema de metas trimestrais (objetivo + 3-5 indicadores).
- **Onda 1 / Onda 2** — fases do Discovery em que vamos entrevistar empresas reais. Onda 1 = 5 empresas; Onda 2 = mais 5.
- **Open Banking / Open Finance** — sistema regulado pelo Bacen onde bancos compartilham dados (com autorização do cliente) via API.
- **OS** — Ordem de Serviço. *(você sabe — só pra referência)*
- **OS multi-equipamento** — uma mesma OS pode ter vários instrumentos ligados a ela. Decisão fundadora do produto.
- **OST** — Opportunity Solution Tree. Árvore que mapeia: meta → oportunidades (dores) → soluções (features) → experimentos.

### P

- **Padrão (de referência / de trabalho / primário)** — instrumento rastreado usado pra calibrar outro. *(você sabe — só pra referência)*
- **Padrão Nacional NFS-e** — substitui o antigo ABRASF. Obrigatório pra prefeituras desde 01/01/2026, pra ME/EPP do Simples desde 01/09/2026.
- **PCI-DSS 4.0.1** — Payment Card Industry Data Security Standard. Padrão de segurança obrigatório pra quem toca em dado de cartão. Versão 4.0.1 vigente desde 01/2025.
- **Persona** — descrição detalhada de um tipo de usuário do sistema (Roldão, Sandra, Letícia, Bruno, etc.).
- **PIX** — sistema de pagamento instantâneo do Bacen.
- **Pipeline** — sequência de etapas (vendas, deploy etc.). "Pipeline de vendas" = funil. "Pipeline de CI" = sequência de testes/build automatizados.
- **PMC** — Pequena, Média Capital — informal pra PME (Pequena e Média Empresa).
- **PO (Purchase Order)** — Ordem de Compra. Documento que empresa-cliente emite autorizando a contratação. Comum em B2B grande.
- **Pregão eletrônico** — modalidade de licitação pública online.
- **Prompt injection** — ataque onde um usuário mal-intencionado escreve um texto que "engana" a IA pra fazer algo que ela não devia. Risco R-027 (cliente final mexer com IA do tenant).
- **PSP** — Payment Service Provider (Stripe, Pagar.me, Asaas, PagSeguro). A gente usa pra não tocar em cartão direto (reduz escopo PCI).
- **Pull Request (PR)** — em humano: "pedido pra integrar uma alteração no sistema oficial". Pra Roldão: "carta dizendo 'olha minhas mudanças, deixa eu juntar com o sistema principal?'". A gente trabalha direto na main, então PR é raro.

### Q

- **Quality gates** — checagens automáticas que travam o código antes de subir (lint, testes, types). Em humano: "controle de qualidade automático".
- **Quick win** — vitória rápida e fácil. Funcionalidade que dá resultado rápido pro cliente.

### R

- **RBAC** — Role-Based Access Control. Sistema de permissão por papel ("admin vê tudo; técnico só vê OS dele; financeiro só vê módulo financeiro"). É como a gente vai controlar acesso no produto.
- **RBC** — Rede Brasileira de Calibração. *(você sabe — só pra referência)*
- **RBMLQ-I** — Rede Brasileira de Metrologia Legal e Qualidade do INMETRO. Liga os 26 IPEMs estaduais.
- **RDC 658/2022 / RDC 786/2023** — resoluções da Anvisa sobre BPF/sistemas computadorizados. Importantes pra cliente farma.
- **Refactor** — em humano: reorganizar o código sem mudar o que aparece pro usuário. Pra Roldão: "reorganizar essa parte por dentro — cliente não vê diferença".
- **REGRAS-INEGOCIAVEIS.md** — arquivo onde a gente lista todas as invariantes do produto. Roldão lê esse no painel-do-dono.
- **REST** — estilo de API. A grande maioria das APIs modernas é REST.
- **RICE** — método de **priorização** que combina 4 fatores: **R**each (quantas pessoas afeta) × **I**mpact (quão forte é o efeito) × **C**onfidence (quão certa é a estimativa) **÷ E**ffort (quanto custa fazer). Resultado = score em "pontos por mês de esforço". Usado no `opportunity-solution-tree.md` pra ranquear as 12 Opportunities por ordem de ataque.
- **Ride-along** — pesquisador acompanha funcionário em **trabalho real** (técnico em campo, atendente em ligação, motorista em viagem). Revela dores que entrevista nunca pega ("aí o sinal cai e eu refaço a OS toda no papel"). Em setor de calibração é socialmente difícil de fazer com concorrente direto — limitado a empresa amiga ou própria.
- **RIPD** — Relatório de Impacto à Proteção de Dados Pessoais. Documento exigido pela LGPD pra tratamentos de risco.
- **RLS** — Row-Level Security. Técnica no banco de dados que garante "cada linha da tabela só é visível pra quem tem permissão". Defesa principal contra vazamento entre tenants.
- **RNTRC** — Registro Nacional de Transportadores Rodoviários de Cargas (ANTT). UMC acima de 12 ton pode exigir.
- **Rollback / revert** — em humano: voltar pra versão anterior. Pra Roldão: "voltar pra versão anterior — desfazer a mudança que deu problema".
- **ROI** — Return on Investment. "Quanto a empresa ganha pra cada R$ 1 investido no produto".

### S

- **SaaS** — Software as a Service. O produto não é vendido, é alugado por mensalidade.
- **Sandbox** — em humano: "caixa de areia" — ambiente isolado onde nada do que rodar afeta o sistema real. Usado pra testar.
- **SAQ A** — Self-Assessment Questionnaire A (PCI). É o nível mais leve de obrigação PCI; alcançável quando todo o cartão passa por PSP terceirizado.
- **SCADA** — Supervisory Control and Data Acquisition. Sistema industrial de supervisão. Adjacente ao nosso produto.
- **Scope creep** — quando o escopo do projeto vai inchando sem controle e nunca termina. Risco grande pro nosso ERP "de N módulos".
- **SEFAZ** — Secretaria da Fazenda estadual. Quem autoriza NF-e.
- **Signatário (técnico autorizado)** — pessoa que assina o certificado de calibração. Tem que ser autorizada por escopo (cl. 6.2 da 17025). *(você sabe — só pra referência)*
- **Sidoq** — Sistema de Documentos do INMETRO. Portal onde a gente baixa NIT, DOQ etc.
- **SLA** — Service Level Agreement. Acordo de "em X horas a gente responde / em Y dias a gente conclui".
- **Smoke test** — teste rápido com **landing page + tráfego pago** pra medir interesse de mercado **antes** de construir o produto. Em B2B nicho (lab calibrador), costuma dar **sinal fraco** porque o ICP é pequeno demais pra anúncio em massa funcionar — ride-along + entrevista qualitativa rendem mais. Mas serve pra validar mensagem/posicionamento.
- **SPED** — Sistema Público de Escrituração Digital. Obrigação fiscal federal.
- **Spike (técnico)** — investigação rápida pra descobrir se uma solução técnica é viável (ou se uma hipótese de negócio se sustenta). "Vou fazer um spike de 2 dias pra testar X". É a forma natural de derrubar um LEAP antes de comprometer recursos. O **spike F-1 do Aferê** (modelo 100% agentes substitui consultor humano) é um dos LEAPs centrais do projeto — precisa de spike formal antes do MVP-1.
- **Spec Kit** — framework de "spec-as-source" da Microsoft que vamos usar. Decisão fundadora D1.
- **Story** — descrição curta de uma feature do ponto de vista do usuário ("Como atendente, quero abrir chamado em 1 min...").
- **SVC-AN / SVC-RS** — SEFAZ Virtual de Contingência (Ambiente Nacional / Rio Grande do Sul). Plano B quando SEFAZ do estado cai.

### T

- **TAC ANTT** — Termo de Autorização e Cadastro da ANTT. Pode ser exigido pra UMC.
- **TAM** — Total Addressable Market. Tamanho total do mercado que o produto pode atender em teoria.
- **TCO** — Total Cost of Ownership. Custo total de algo ao longo da vida útil (frota: combustível + manutenção + depreciação + seguro + multas).
- **TecnoSpeed / PlugNotas / Focus NFe** — provedores BaaS fiscais mais maduros do mercado BR.
- **Tenant** — em humano: cada cliente que usa o nosso SaaS. Ex: laboratório Calix é um tenant; laboratório XYZ é outro tenant. Não confundir com "cliente final" — esse é o cliente do tenant.
- **Tipo de cargo (signatário)** — só pessoas autorizadas pelo escopo da acreditação podem assinar certificados. INV-003 garante isso.
- **Time-trial** — comparação **cronometrada**: o mesmo usuário faz a mesma tarefa no **sistema atual** (Cali/Excel) e no **novo sistema** (Aferê). Mede ganho real de tempo (ex: "emitir certificado caiu de 18 min pra 4 min"). Exige protótipo funcional + usuário-cobaia disposto a topar. É uma das técnicas mais convincentes de venda pra perfil A/B.
- **Trail / Audit trail** — ver "Audit trail".

### U

- **UMC** — Unidade Móvel de Calibração. Caminhão que leva pesos-padrão pra calibrar balança rodoviária em campo. Decisão fundadora do produto. *(você sabe — só pra referência)*
- **UX** — User Experience. Experiência de uso. "Boa UX" = sistema fácil; "má UX" = cliente xinga.

### V

- **Validação de software** — exigência da cláusula 7.11 da 17025: o software de cálculo de incerteza tem que ser validado antes de uso. Referências: WELMEC 7.2, OIML D 31.
- **Van Westendorp** — método de pesquisa de disposição a pagar (WTP) com **4 perguntas**: (1) "qual preço você considera **caro demais** que não compraria?"; (2) "qual preço é **barato demais** ao ponto de sugerir má qualidade?"; (3) "qual preço você considera **caro mas ainda compraria**?"; (4) "qual preço você considera **uma barganha**?". O cruzamento das 4 curvas dá uma **faixa de preço aceitável** (Point of Marginal Cheapness até Point of Marginal Expensiveness). Usado em V-2 (`validacao-ativa.md`).
- **Verificação** — comparação de medição contra um requisito específico, com decisão "passa / não passa". Diferente de "calibração". *(você sabe — só pra referência)*
- **Verificação metrológica legal** — verificação obrigatória feita pelo IPEM (balança comercial anual, bomba de combustível, etc.). Diferente da calibração RBC voluntária.
- **VIM** — Vocabulário Internacional de Metrologia (JCGM 200). Vigente em 05/2026: JCGM 200:2012 (3ª ed). 4ª ed ainda em rascunho. *(você sabe — só pra referência)*
- **VPS** — Virtual Private Server. Servidor virtual onde a aplicação roda. A gente usa Hostinger VPS KVM 4 (São Paulo).

### W

- **WCAG 2.1 AA** — Web Content Accessibility Guidelines. Padrão internacional de acessibilidade. AA é o nível usual exigido (vs. A mais leve, AAA mais rigoroso).
- **WebSocket / Webhook** — formas de comunicação entre sistemas. **Webhook** = "quando acontecer X aí, você me avisa nesse endereço". Útil pra notificações em tempo real.
- **WELMEC 7.2** — guia europeu sobre validação de software em instrumentos regulados. Referência pra cláusula 7.11 da 17025. *(você sabe — só pra referência)*
- **WhatsApp Business API** — versão oficial da API do WhatsApp pra empresas. Diferente do WhatsApp Business app comum.
- **WORM** — Write Once, Read Many. Modo de armazenamento onde o arquivo só pode ser escrito uma vez, depois é só leitura — nem o admin pode apagar. Obrigatório pro arquivo de certificados (cl. 8.4 da 17025).
- **WTP** — Willingness to Pay. "Disposição a pagar". Teste em entrevista: "quanto você pagaria por mês por isso?".

### X / Y / Z

- **XML** — formato de arquivo usado pra trocar dados estruturados. NF-e é um XML autenticado pela SEFAZ.

---

## Termos compostos / decisões fundadoras

**Decisões fundadoras de ENGENHARIA (D1–D6, 16/05/2026):**

- **D1 — Spec Kit** — framework de "spec-as-source" da Microsoft. Decidimos em 2026-05-16.
- **D2 — Spec-as-source** — princípio: a especificação **é** a fonte da verdade; código é derivado dela.
- **D3 — Nomenclatura híbrida** — padrão de nomes de arquivo/pasta. PT-BR pra conteúdo de negócio, EN pra termos técnicos consagrados.
- **D4 — Devcontainer obrigatório** — todo dev mexe num ambiente padronizado.
- **D5 — CODEOWNERS** — arquivo que define "quem aprova mudança em cada parte do código".
- **D6 — Operação dual** — Claude Code + Codex CLI sobre `AGENTS.md` canônico (roteamento por tipo de tarefa).

**Decisões fundadoras de PRODUTO (Roldão 17/05/2026):** ver verbete "Decisão fundadora" na seção D do glossário alfabético + `dominios/dominio-de-negocio.md`.

- **MVP-1 / MVP-2 / MVP-3** — Minimum Viable Product. Versão mínima viável, em fases. MVP-1 = conjunto mínimo pra lançar pro 1º cliente externo.

---

## Termos do dia a dia do projeto Claude Code

- **Agente** (no contexto do projeto) — assistente de IA configurada com objetivo específico (auditor de conformidade, auditor de segurança, etc.). Não confundir com "agente de tratamento de dados" (LGPD).
- **Codex CLI** — alternativa ao Claude Code da OpenAI. A gente usa em paralelo (operação dual).
- **Discovery** — fase inicial do produto onde a gente investiga mercado, dores, concorrentes — antes de codar. Família 0 do projeto.
- **Família 0 a 6** — divisões da Discovery do projeto (cada uma com seus artefatos). Família 0 = visão geral; Família 5 = auditoria viva.
- **Hooks** (no contexto do projeto) — scripts bash de segurança que rodam antes/depois do Claude executar uma ação. Bloqueiam comando perigoso.
- **MCP** — Model Context Protocol. Padrão pra a IA conversar com sistemas externos (GitHub, Playwright etc.).
- **Painel do Dono** — `docs/painel-do-dono.md`. O documento que o Roldão lê toda manhã pra saber o que aconteceu, o que decidir, o que está pendente.

---

## Lacunas / pendências de termo

- **Enunciado CD/ANPD nº 4** — texto não encontrado em consulta inicial. `[a confirmar]`
- **CSRT por UF** — quais UFs já exigem além de PR. `[a confirmar]`
- **MOC CT-e** — versão vigente. `[a confirmar]`
- **VIM 4ª edição** — publicação efetiva. `[a confirmar]`

---

## Como manter este glossário

- Termo novo aparece em algum doc → adicionar aqui na mesma PR/commit.
- Termo do setor que Roldão já conhece bem → marcar com `(você sabe — só pra referência)` e não traduzir muito.
- Termo com fonte secundária ou dúvida → marcar `[a confirmar pelo Roldão]`.
- Manter ordem alfabética rigorosa por seção (A, B, C…).
- Evitar definição enciclopédica — Roldão precisa de **1-2 frases humanas**, não verbete de Wikipedia.
