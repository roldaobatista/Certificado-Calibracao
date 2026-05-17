# Discovery — Domínio de negócio

> **Artefato Rodada 0** (agente faz sozinho, Roldão valida). Modelo conceitual de "como uma empresa de assistência técnica + calibração funciona" + glossário operacional do setor. **Base do glossário comum** (Família 2).
> **Atualizado:** 2026-05-17 (auditoria batch 3 noite — desambiguação "decisão fundadora" aplicada). Marcações `[Roldão validar]` apontam onde precisa de input direto antes de virar invariante de produto.

---

> ## Nomenclatura — desambiguação "decisão fundadora" (pós-auditoria 17/05/2026 noite, Aud-20)
>
> O projeto usa "decisão fundadora" em **DOIS sentidos distintos**. Não confundir:
>
> **Decisões fundadoras de PRODUTO (Roldão 17/05/2026)** — 4 blocos canônicos de escopo (etiquetados ⭐ neste doc):
> 1. **Frota + UMC + Caixa do Técnico** (seção "Controle de Técnico em Campo, Despesas, Frota e UMC")
> 2. **Comissões Configuráveis** (seção "Módulo de Comissões Configuráveis")
> 3. **Cliente 360° + CRM Contínuo + Automações** (seção "Cliente 360°, CRM Contínuo e Automações")
> 4. **Estoque Multi-local com lacre + selo INMETRO** (seção "Módulo de Estoque Completo para Assistência Técnica")
>
> A seção de **perfis de empresa A/B/C/D** também está marcada como decisão fundadora de produto — separa o que o tenant pode ou não emitir (ver INV-015 em `normas-e-regulacao.md`).
>
> **Decisões fundadoras de ENGENHARIA (D1–D6, tomadas 2026-05-16)** — princípios de processo, **não** de escopo de produto:
> - **D1** — Spec Kit (framework Microsoft de spec-driven development)
> - **D2** — spec-as-source (a especificação é a fonte da verdade; código é derivado)
> - **D3** — nomenclatura híbrida (PT-BR pra termos de negócio; EN pra termos técnicos)
> - **D4** — devcontainer obrigatório
> - **D5** — CODEOWNERS por pasta
> - **D6** — operação dual (Claude Code + Codex CLI sobre `AGENTS.md` canônico)
>
> Quando este doc fala "⭐ DECISÃO FUNDADORA DE PRODUTO (Roldão 17/05/2026)" trata-se sempre do **bloco de escopo**, nunca dos princípios D1–D6.

---

## Pra preencher quando Rodada 0 iniciar

### Visão geral do setor

Empresas brasileiras como a do Roldão operam **duas atividades complementares sob o mesmo CNPJ**:

1. **Assistência técnica** — manutenção (preventiva e corretiva) de equipamentos de medição e instrumentação em geral. Pode ser executada no laboratório (cliente leva o instrumento) ou em campo (técnico vai até o cliente). Atividade **não regulada por norma técnica obrigatória**, mas com forte expectativa contratual e de garantia.

2. **Laboratório de calibração ISO/IEC 17025** — emissão de **certificado de calibração** com rastreabilidade metrológica (cadeia até o SI) e incerteza declarada (GUM/EA-4/02). Atividade **fortemente regulada**: para emitir certificado com selo RBC, o laboratório precisa ser **acreditado pela Cgcre/INMETRO** (programa Rede Brasileira de Calibração) e cumprir 30+ documentos normativos (ISO/IEC 17025:2017 + NIT-DICLA-021/030 + DOQ-CGCRE-008 + ILAC G24, etc.).

**Por que essas duas atividades andam juntas no Brasil:** o mesmo cliente que compra calibração (indústria, hospital, lab clínico, construtora, distribuidora de combustíveis, refinaria, frigorífico) costuma também precisar de assistência (consertar o que quebrou, ajustar, fornecer peça). Separar as duas atividades em CNPJs diferentes complicaria atendimento e faturamento; manter sob mesmo CNPJ exige um sistema que entenda os DOIS fluxos sem misturar (um conserto não vira certificado RBC; um certificado RBC não pode ser feito sem padrão rastreado).

**Ecossistema:**

- **Clientes:** indústria farmacêutica, alimentícia, química, petroquímica, automotiva; postos de combustível (calibração de bombas — INMETRO PRM); hospitais e laboratórios clínicos (calibração de balanças, termômetros, autoclaves); concessionárias de veículos; construtoras (controle tecnológico de obras); distribuidoras de água/gás.
- **Fornecedores diretos:** fabricantes de instrumentos (Fluke, Beamex, Presys, Salvi Casagrande, Gehaka), fornecedores de padrões (laboratórios de calibração de nível mais alto na cadeia — RBC ou INM/Inmetro), distribuidores de peças, fornecedores de software (concorrentes mapeados em `concorrentes.md`).
- **Reguladores e órgãos técnicos:**
  - **Cgcre/INMETRO** — acredita lab RBC; **ciclo de acreditação de 4 anos com supervisões periódicas** (geralmente anuais ou a cada 18 meses, regido pela NIT-Dicla-031). Correção do doc anterior que dizia "a cada 2 anos".
  - **ABNT** — publica versão brasileira das normas ISO.
  - **CB-25 / ABNT** — Comitê Brasileiro de Qualidade e Avaliação da Conformidade (espelha ISO/CASCO). Atenção: o **CB-25 NÃO é "Comitê Brasileiro de Calibração"** como aparecia no doc anterior — esse era erro. Comitê técnico de calibração propriamente é responsabilidade do **CT-Dicla** dentro do Inmetro + BIPM/JCGM internacionalmente.
  - **IPEMs estaduais (RBMLQ-I)** — 26 órgãos delegados pelo Inmetro que fazem **verificação metrológica legal** (balanças comerciais, bombas de combustível, etilômetros, taxímetros). Fluxo distinto da calibração RBC voluntária. Empresa que calibra balança/bomba lida com IPEM constantemente.
  - **CONFAZ + SEFAZ estadual** — NF-e.
  - **Prefeitura municipal** — NFS-e + ISS.
  - **Receita Federal** — SPED, retenção fiscal 5 anos, RIR/2018.
  - **ANPD** — LGPD, prazo de incidente 3 dias úteis (Res. 15/2024).
  - **Bacen** — se integrar bancos (Open Finance, PIX, Res. 4.658/2018).
  - **ANS, Anvisa, Anatel** — dependendo do cliente atendido (calibração em saúde, farma, telecom regulados).
- **Ferramentas adjacentes que o setor usa hoje (status quo):** planilhas Excel pesadas, WhatsApp pra atendimento, Bling/Conta Azul pra emitir NFS-e, e-mail pra enviar certificado, pasta de rede ou Google Drive pra arquivar PDF de certificado, software dedicado de calibração só pra cálculo (Cali, Metroex) com export pra PDF que é depois anexado em e-mail. **Tudo em sistemas separados, integração via copia-cola humano.** Essa é a dor central do mercado.

**Por que importa pro produto:** entender que **o sistema único precisa atender 4 ciclos distintos sob um mesmo CNPJ**:
  - Ciclo comercial (CRM → orçamento → contrato),
  - Ciclo operacional (chamado/agenda → OS → execução em lab ou campo),
  - Ciclo metrológico regulado (entrada controlada → calibração → cálculo de incerteza → certificado assinado → arquivo WORM),
  - Ciclo financeiro/fiscal (NFS-e/NF-e → boleto/PIX → conciliação → DRE).

Errar a fronteira entre esses ciclos (ex: emitir certificado sem fechar OS, ou faturar sem cadeia de rastreabilidade) é o tipo de erro que **destrói confiança regulatória** e pode tirar acreditação RBC.

### Atores típicos

| Ator | Quem é | Relação com empresa |
|---|---|---|
| **Cliente PJ** | Empresa que precisa de manutenção ou calibração de instrumento | Origem de receita |
| **Cliente PF** | (raro mas possível — autônomo) | Idem |
| **Fornecedor de peça** | | |
| **Fornecedor de padrão** | Laboratório acreditado RBC que fornece padrão pra a empresa do Roldão | |
| **INMETRO / CGCRE** | Regulador de calibração | Auditoria, acreditação |
| **SEFAZ estadual / municipal** | | |
| **Receita Federal** | | |
| **Bancos** | | |
| **Operadora telecom** | | |
| **Cartórios / juntas comerciais** | | |

### Papéis dentro da empresa típica

| Papel | Responsabilidade | Frequência de uso de software |
|---|---|---|
| **Dono / sócio** | Estratégia, decisão grande | Semanal (relatório) |
| **Gerente operacional** | Triagem de chamado, agenda de técnico | Diário |
| **Atendente / SAC** | Abrir chamado, falar com cliente | Diário (intenso) |
| **Técnico de campo** | Executar OS no local do cliente | Diário (mobile) |
| **Metrologista (signatário)** | Emitir certificado de calibração | Semanal |
| **Financeiro** | Conta a pagar/receber, NF-e, conciliação | Diário |
| **Comercial / vendedor** | Captação, orçamento, fechamento | Diário |

### Processos típicos (fluxo)

#### Processo: Atender chamado e fazer OS
1. Cliente liga / WhatsApp / e-mail → **chamado** aberto
2. Triagem (gerente decide se é manutenção ou calibração)
3. **Orçamento** elaborado e enviado ao cliente
4. Aprovação do cliente
5. **OS** criada e atribuída a técnico
6. Técnico vai ao local OU cliente leva instrumento ao laboratório
7. Execução do serviço (manutenção / calibração)
8. Se calibração: emissão de **certificado** ISO 17025/RBC
9. Faturamento: emissão de **NF-e/NFS-e**
10. Cobrança, recebimento, conciliação bancária
11. Atualização do **CRM** com histórico do cliente

#### Processo: Calibração específica (regulado ISO 17025)
1. Recebimento do instrumento (entrada controlada)
2. Verificação inicial (medições preliminares)
3. Calibração propriamente dita (medição contra padrão rastreado)
4. Cálculo de incerteza
5. Verificação por segundo caminho (garantia de validade — cláusula 7.7)
6. Emissão do certificado (assinatura digital do metrologista)
7. Armazenamento do certificado em WORM (cláusula 8.4)
8. Devolução do instrumento + entrega do certificado ao cliente

### Documentos físicos que o setor maneja

| Documento | Quem emite | Quem recebe | Retenção |
|---|---|---|---|
| Orçamento | Empresa | Cliente | conforme contrato |
| OS | Empresa | Cliente | conforme contrato + 5 anos (fiscal se vinculado a NF-e) |
| Certificado de calibração | Empresa | Cliente | mínimo 5 anos / ciclo de vida do instrumento |
| NF-e / NFS-e | Empresa | Cliente + SEFAZ | 5 anos (Receita) |
| Recibo / boleto | Empresa | Cliente | conforme política |
| Relatório técnico | Empresa | Cliente | conforme contrato |

### Glossário operacional inicial (semente pro glossário comum)

| Termo | Definição (1 linha) | Origem |
|---|---|---|
| **Chamado** | Solicitação inicial de cliente, não necessariamente convertida em OS | Indústria |
| **Triagem** | Decisão sobre quem/quando vai atender o chamado | Indústria |
| **Orçamento** | Proposta comercial pré-aprovação | Indústria |
| **OS (Ordem de Serviço)** | Documento que autoriza execução de um serviço específico | Indústria |
| **Calibração** | Operação que estabelece relação entre valor indicado e valor de referência (VIM) | VIM 4ª ed |
| **Ajuste** | Operação que altera o instrumento pra reduzir erro (DIFERENTE de calibração) | VIM 4ª ed |
| **Verificação** | Comparação contra requisito (DIFERENTE de calibração) | VIM 4ª ed |
| **Padrão** | Realização da definição de uma grandeza (rastreado ao SI) | VIM 4ª ed |
| **Padrão de referência** | Padrão usado pra calibrar outros padrões no mesmo lab | VIM 4ª ed |
| **Padrão de trabalho** | Padrão usado rotineiramente em medições | VIM 4ª ed |
| **Rastreabilidade metrológica** | Cadeia ininterrupta de calibrações até o SI | VIM 4ª ed |
| **Incerteza de medição** | Parâmetro que caracteriza dispersão de valores atribuídos | VIM 4ª ed |
| **Deriva** | Variação contínua da indicação ao longo do tempo | VIM 4ª ed |
| **RBC** | Rede Brasileira de Calibração (acreditação INMETRO/CGCRE) | INMETRO |
| **ISO/IEC 17025** | Norma de requisitos pra laboratórios de ensaio e calibração | ISO |
| **Certificado de calibração** | Documento que apresenta resultado de calibração com incerteza e rastreabilidade | ISO 17025 |
| **Signatário técnico** | Pessoa física responsável legal pelo certificado emitido | RBC NIT-DICLA-021 |
| **Tenant** | Cliente que usa o ERP em modo SaaS (a empresa de assistência) | Engenharia |
| **Cliente** | Empresa/pessoa atendida pela empresa de assistência | Indústria |
| **SLA** | Service Level Agreement — compromisso de tempo de resposta/resolução | Indústria |
| **Funil de vendas** | Estágios sequenciais de qualificação de prospect até cliente | CRM padrão |
| **DRE** | Demonstrativo de Resultado do Exercício | Contábil |
| **NF-e** | Nota Fiscal Eletrônica (produto/mercadoria, estadual) | SEFAZ |
| **NFS-e** | Nota Fiscal de Serviços Eletrônica (municipal) | Município |

### Particularidades brasileiras

- **Imposto sobre serviço (ISS) varia por município** — afeta NFS-e
- **Diferentes regimes tributários** (Simples Nacional, Lucro Presumido, Lucro Real). LC 214/2025: ME/EPP do Simples migra pra NFS-e Padrão Nacional em **01/09/2026** (CGSN 189/2026).
- **Pagamento por boleto bancário** ainda dominante em B2B
- **Pix** crescendo rapidamente (recuperação de fundos obrigatória 02/02/2026, BCB 493/2025)
- **WhatsApp Business** é canal de atendimento informal mas dominante
- **Receita Federal exige SPED** dependendo do porte
- **Distância física grande** entre cliente e laboratório (BR continental) → logística de recebimento/devolução de instrumento conta como custo relevante (Correios, transportadora, motoboy)
- **Múltiplas certificações regulatórias coexistem por cliente** (ex: lab que atende cliente farma precisa ser RBC pra calibrar e o cliente exige rastreabilidade pra ANVISA RDC 658/2022 ou GMP/GAMP)

---

## Controle de Técnico em Campo, Despesas, Frota e UMC ⭐ DECISÃO FUNDADORA DE PRODUTO (Roldão 17/05/2026)

> **Registrado em 17/05/2026** (texto redigido pelo Roldão — fonte de verdade). Outra dimensão estrutural do produto — operação de campo não é "tema acessório", é módulo central com sub-domínios próprios.

O sistema deve contemplar o controle completo dos técnicos em campo, considerando que cada técnico poderá atender uma **Ordem de Serviço**, e essa Ordem de Serviço poderá conter **um ou vários equipamentos** vinculados ao mesmo atendimento.

Durante a execução dos serviços, o técnico poderá gerar diversos tipos de despesas operacionais, como:

- despesas de viagem;
- alimentação;
- hospedagem;
- combustível;
- pedágios;
- quilometragem rodada;
- manutenção emergencial;
- outras despesas relacionadas ao atendimento.

Para isso, o sistema deverá possuir um controle de **caixa do técnico**, permitindo registrar, acompanhar, aprovar e prestar contas de todos os valores utilizados durante a execução dos serviços.

O técnico poderá se deslocar de diferentes formas, conforme a necessidade da empresa:

1. **Veículo próprio do técnico** — o sistema deverá permitir o controle de pagamento por quilometragem rodada ou por aluguel mensal do veículo, conforme regra definida pela empresa.

2. **Veículo da empresa** — quando o técnico utilizar veículo da empresa, o sistema deverá controlar toda a gestão da frota, incluindo:
   - abastecimentos;
   - pneus;
   - troca de óleo;
   - revisões;
   - manutenções preventivas e corretivas;
   - documentos do veículo;
   - seguro;
   - multas;
   - custos gerais;
   - histórico de utilização por técnico e por Ordem de Serviço.

3. **Deslocamento em conjunto com outros veículos da empresa** — em alguns atendimentos, o técnico poderá ir em veículo pequeno separado ou acompanhar outro veículo operacional da empresa.

Nas calibrações de **balanças rodoviárias**, a empresa utiliza um caminhão específico chamado **UMC — Unidade Móvel de Calibração**. Esse caminhão transporta os **pesos padrão** utilizados na calibração de balanças rodoviárias.

A UMC deverá ser tratada no sistema como um veículo especial da frota, com controle completo de:

- motorista responsável;
- despesas do motorista;
- combustível;
- pneus;
- manutenção;
- troca de óleo;
- documentos;
- seguros;
- viagens realizadas;
- Ordens de Serviço atendidas;
- pesos padrão transportados;
- disponibilidade da UMC para agendamento;
- custos vinculados a cada serviço.

Quando houver atendimento com UMC, o sistema deverá permitir controlar separadamente:

- o técnico responsável pelo serviço;
- o motorista da UMC;
- o caminhão utilizado;
- o veículo de apoio, caso o técnico vá em carro pequeno separado;
- as despesas do técnico;
- as despesas do motorista;
- os custos da UMC;
- os custos gerais da viagem;
- a vinculação de todos esses custos à Ordem de Serviço.

Dessa forma, o sistema deverá permitir uma visão completa do **custo real de cada atendimento em campo**, incluindo mão de obra, deslocamento, despesas, veículos, motorista, técnico, UMC e demais recursos utilizados na execução do serviço.

---

### Anexo técnico — desdobramentos pra arquitetura/produto

> Detalhes pra time técnico — derivados do texto canônico do Roldão acima.

**OS multi-equipamento (modelo de dados):**
- 1 OS → N equipamentos (1:N)
- Cada equipamento → 1 ou mais certificados (suportar "as found / as left")
- Status da OS pode ser parcial (N equipamentos prontos, M pendentes)
- Faturamento da OS pode ser único OU por equipamento

**Caixa do Técnico (fluxo operacional):**
1. Técnico recebe **adiantamento** antes de viajar (vinculado à OS ou genérico do mês)
2. Gasta em campo; tira foto de comprovantes (notas, recibos)
3. Volta e faz **prestação de contas** (anexa comprovantes; sistema reconcilia)
4. Saldo positivo: devolve à empresa. Saldo negativo: empresa repõe.
5. Conciliação com financeiro → custo real por OS / por cliente / por técnico no DRE

**UMC (Unidade Móvel de Calibração) — perfil técnico:**
- Veículo de carga (caminhão truck/toco, geralmente 6-12 ton de capacidade)
- Carrega pesos-padrão calibrados (conjunto de 500kg, 1ton, 2ton — total 10-30 ton de carga útil)
- Motorista: CNH C/D/E + curso MOPP (se carga sensível) + exames toxicológicos obrigatórios
- Registro no RNTRC/ANTT se >12 ton
- Documentação especial: TAC ANTT, seguro de carga, rastreamento veicular obrigatório

**Persona nova (Motorista da UMC)** — adicionar em `personas-detalhadas.md`:
- Nome típico: Carlos / Antônio / Sebastião
- Idade: 35-60; Formação: CNH D/E + MOPP; Salário: R$ 2.500-4.500 + diária
- Usa o sistema mínimo — só pra registrar abastecimento, KM, despesa, foto de comprovante (mobile simples)

**Controle Total de Frota (carros + UMC) — itens completos:**

| Categoria | Itens |
|---|---|
| Documentação/legal | IPVA anual, CRLV (licenciamento), seguro (apólice/cobertura/franquia), DPVAT, multas (com defesa + pontos CNH), TAC ANTT (UMC) |
| Manutenção | Óleo (por KM), filtros (ar/óleo/combustível/cabine), pneus (vida útil + alinhamento + balanceamento + calibragem), revisão preventiva, corretiva, velas, correia dentada, freio, suspensão, ar |
| Operacional | Hodômetro (KM por viagem), combustível (abastecimentos + KM/L + alerta), lavagem, histórico de uso (quem dirigiu, quando, pra qual OS) |
| Custo (TCO) | Custo total por veículo/mês = depreciação + IPVA + seguro + combustível + manutenção + multas. Vira indicador de gestão. |

**Mapa de domínios — adicionar:**

| Domínio | Módulos | Razão |
|---|---|---|
| **Frota e Operação de Campo** (NOVO) | Cadastro veículos (carros + UMC), Manutenção (preventiva + corretiva), Documentação (IPVA, licenciamento, seguro, multas), Combustível + KM, Pneus, Lavagem, TCO/veículo, Histórico por OS | Sem isso, lab com 3+ técnicos de campo perde controle de custo |
| **Despesas e Caixa de Campo** (sub-módulo Financeiro OU Frota) | Adiantamento, Prestação de contas, Anexo de comprovantes, Categorização, Aprovação gerente, Exportação contábil | Auvo cobre parcial; gap em integração com OS |
| **UMC — sub-módulo de Calibração** | Cadastro UMC, Pesos-padrão carregados (cadeia rastreabilidade), Agenda da UMC (gargalo crítico), Despesas específicas, Motorista vinculado, Vínculo com OS de balança rodoviária | Único nicho regulatório — nenhum concorrente nacional cobre |

**Riscos novos identificados:**
- **Caixa do técnico não prestada** (técnico sumiu com adiantamento) → R-novo
- **Manutenção atrasada** (carro quebra na viagem; cliente perde dia) → R-novo
- **Multa não paga vira protesto + CNH suspensa do condutor** → R-novo
- **UMC com peso-padrão roubado/batido** = perda R$ 100-300 mil em massas + parada operacional → R-novo (catastrófico)
- **Motorista UMC perde validade CNH/MOPP/toxicológico** → UMC parada → contratos perdidos → R-novo

**Conexão com concorrentes:**
- **Auvo** cobre parte (OS de campo + GPS) mas NÃO tem: (a) frota completa, (b) UMC, (c) caixa do técnico integrada com OS, (d) calibração ISO 17025. Continua "field service horizontal".
- **Bling/Conta Azul/Omie/Cali/Metroex/Calibre/FP2** — zero cobertura de frota e UMC.
- **GAP CONFIRMADO:** gestão completa de frota + UMC + caixa + integração com OS de calibração ISO 17025 = **vazio absoluto no mercado BR**. **6º gap defensável** (somar aos 5 já identificados).

---

## Módulo de Comissões Configuráveis ⭐ DECISÃO FUNDADORA DE PRODUTO (Roldão 17/05/2026)

> **Registrado em 17/05/2026** (texto redigido pelo Roldão — fonte de verdade). Módulo central do produto, **não pode ser opcional nem genérico**. Cobre comissões complexas que ERPs horizontais (Bling/Omie/Conta Azul) e softwares de calibração (Cali/Metroex) não cobrem.

O sistema deverá possuir um **módulo completo de gestão de comissões**, permitindo configurar, calcular, controlar, aprovar e pagar comissões para diferentes tipos de colaboradores envolvidos nos processos comerciais, operacionais e administrativos da empresa.

Esse módulo deverá ser totalmente configurável, permitindo ativar ou desativar comissões conforme a função, o usuário, o setor, o tipo de serviço ou a regra comercial definida pela empresa.

As comissões poderão ser aplicadas para diferentes perfis, como:

- técnico;
- auxiliar técnico;
- motorista;
- vendedor;
- supervisor;
- administrativo;
- gerente;
- parceiro externo;
- qualquer outro colaborador ou função configurada no sistema.

O objetivo é permitir uma gestão profissional das comissões, com regras flexíveis, rastreabilidade, fechamento por período e controle financeiro completo.

### Configuração das regras de comissão

O sistema deverá permitir criar múltiplas regras, de forma flexível e parametrizável. Cada colaborador poderá ter uma ou várias regras vinculadas, conforme tipo de serviço, cliente, produto, centro de custo, unidade, tipo de OS, tipo de venda etc.

**8 formas de cálculo suportadas:**

1. **Sobre valor bruto da OS** (mão de obra + peças + produtos + deslocamento). Ex: técnico 20% sobre bruto.
2. **Somente sobre mão de obra** (desconsidera peças/produtos/materiais/deslocamento). Ex: técnico 25% só mão de obra.
3. **Sobre peças e serviços com percentuais diferentes**. Ex: técnico 20% mão de obra + 5% peças.
4. **Sobre produtos vendidos** (vendedor ou técnico). Ex: vendedor 8% sobre célula de carga, indicador, caixa de junção, acessórios.
5. **Sobre valor líquido** (bruto da OS — despesas vinculadas: combustível, pedágio, alimentação, hospedagem, diária, KM, motorista, técnico, UMC, veículo, peças, terceiros, outras). Ex: OS R$ 10.000 — despesas R$ 2.500 = base R$ 7.500; comissão 20% sobre líquido = R$ 1.500.
6. **Por valor fixo** (por serviço, OS, equipamento, visita, atividade). Ex: técnico R$ 150 por calibração.
7. **Por tipo de serviço.** Ex: calibração 20%, manutenção corretiva 15%, instalação 18%, venda 5%, contrato mensal 10%.
8. **Por equipamento** (balança rodoviária, industrial, bancada, indicador de pesagem, sistema de automação, dosador, kit de pesagem). Como uma OS pode ter vários equipamentos, comissão pode ser por equipamento, por item ou pelo total consolidado.

### Múltiplas comissões na mesma OS

Mesma OS pode gerar comissão pra múltiplas pessoas simultaneamente:
- vendedor (pela venda);
- técnico (pela execução);
- auxiliar técnico (apoio);
- motorista (viagem);
- supervisor (desempenho da equipe);
- administrativo (gestão/fechamento, se regra ativa).

**Divisão de comissão entre participantes.** Ex: comissão total 20% da mão de obra → técnico principal recebe 70% da comissão, auxiliar recebe 30%.

### Período de fechamento e pagamento

Múltiplos ciclos suportados — cada colaborador/regra pode ter periodicidade própria:

- semanal, quinzenal, mensal, bimestral, trimestral, semestral, anual;
- por fechamento manual;
- por recebimento financeiro;
- por conclusão da OS;
- por emissão da nota fiscal;
- por compensação do pagamento do cliente.

Ex: técnico A mensal, vendedor B bimestral, gerente C trimestral, motorista D por fechamento manual de viagem.

### Comissão por recebimento do cliente (CRÍTICO pra fluxo de caixa)

Configurável: comissão pode ser gerada **no momento da venda / aprovação do orçamento / abertura da OS / conclusão da OS / emissão da NF / faturamento / recebimento financeiro / somente após compensação bancária**.

**Opção "somente sobre valores efetivamente recebidos"** — evita pagar comissão sobre dinheiro que ainda não entrou.

Ex: OS R$ 12.000 parcelada em 3x R$ 4.000. Comissão 10% = R$ 400 a cada parcela recebida.

### Controle de descontos, custos e margem

Regras configuráveis incluem:

- comissão sobre valor cheio OU com desconto;
- comissão somente se houver margem mínima;
- comissão reduzida quando desconto acima do permitido;
- comissão bloqueada se OS dá prejuízo;
- comissão calculada após dedução de despesas / impostos / custo de peças / custo operacional.

Ex: vendedor dá desconto acima de 10% → comissão cai de 8% pra 5%.

### Aprovação, conferência e auditoria

Fluxo obrigatório antes do pagamento:

- calcular comissão automaticamente;
- revisar valores;
- bloquear comissão com divergência;
- aprovar / reprovar;
- ajustar manualmente **com justificativa obrigatória**;
- registrar histórico de alteração (trilha de auditoria);
- anexar comprovantes;
- gerar relatório de fechamento;
- enviar demonstrativo para o colaborador.

**Todo ajuste manual exige justificativa e fica registrado em auditoria.**

### Status das comissões

Cada comissão tem status pra controle: **prevista | calculada | aguardando recebimento | liberada para fechamento | em conferência | aprovada | bloqueada | cancelada | paga | estornada**.

### Integração com outros módulos

Comissões precisa estar integrado com: Orçamento, OS, Chamado Técnico, Contratos, Financeiro, Contas a Receber, Contas a Pagar, Estoque, Produtos e Serviços, **Frota, Caixa do Técnico, Despesas de Viagem**, Nota Fiscal, Usuários e Permissões, Relatórios Gerenciais.

### Relatórios e demonstrativos

Análises mínimas: comissão por técnico / vendedor / motorista / OS / cliente / período / tipo de serviço / produto / paga / pendente / bloqueada / estornada / por valor recebido / por margem; ranking; comparativo faturamento × custo × lucro × comissão.

**Demonstrativo individual por colaborador:** período do fechamento, OS vinculadas, clientes atendidos, valores faturados, valores recebidos, base de cálculo, percentual aplicado, despesas descontadas, comissão bruta, descontos, ajustes, comissão líquida a pagar, status do pagamento.

### Controle de fechamento

Rotina dedicada de fechamento:
- selecionar colaborador / equipe / período / tipo de comissão;
- buscar OS concluídas + valores recebidos;
- calcular comissão aplicando regras configuradas;
- demonstrar valores → conferência → aprovação;
- integrar com contas a pagar ou folha;
- registrar data de pagamento + anexar comprovante.

**Após aprovado, fechamento fica bloqueado pra alteração** — mudanças exigem reabertura autorizada com registro de auditoria.

### Gestão profissional sem mexer no código

Empresa deve configurar comissões simples ou complexas **sem depender de alteração no código do sistema**. O módulo deve cobrir desde comissão básica (% sobre serviço) até regras avançadas envolvendo: múltiplos participantes, percentuais diferentes por item, pagamento por recebimento, dedução de despesas, cálculo sobre líquido, metas, faixas de comissão, bonificações, bloqueios por inadimplência, margem mínima, estornos, fechamento periódico, aprovação por gestor, integração com financeiro.

---

### Anexo técnico — desdobramentos pra arquitetura

> Implicações pra mapa de domínios, modelo de dados e concorrentes.

**Domínios afetados:** Comissões pode ser:
- (a) Domínio próprio "Comissões e Remuneração Variável" (recomendação forte — escopo é grande)
- (b) Sub-módulo do Financeiro com integração com Operação e Frota

**Modelo de dados conceitual:**
- 1 OS → N comissões (1:N)
- 1 comissão → N participantes com % de divisão
- 1 colaborador → N regras de comissão
- 1 regra → critérios (tipo de serviço, cliente, produto, equipamento, etc.) + cálculo (sobre bruto/líquido/MO/fixo/etc.) + período + gatilho de pagamento
- Hash de auditoria em cada cálculo + ajuste manual

**Conexão com Frota/UMC/Caixa do Técnico:** comissão líquida depende de despesas da OS. Sem integração funcional com Caixa do Técnico e despesas da UMC, cálculo de líquido é impossível. **Comissões e Frota/Despesas são módulos acoplados.**

**Conexão com concorrentes:**
- **Bling/Omie/Conta Azul** — têm comissão básica de vendedor (% sobre venda), NÃO suportam comissão sobre OS de serviço, NÃO suportam múltiplos participantes, NÃO suportam comissão sobre líquido pós-despesas.
- **Cali/Metroex/Calibre** — zero módulo de comissão.
- **Auvo** — tem comissão básica por OS, mas sem regras complexas (sem cálculo sobre líquido, sem múltiplos participantes, sem fechamento bloqueado com auditoria).
- **TOTVS Protheus** — tem módulo de comissão robusto, mas exige licença enterprise (>R$ 50k implementação) e é genérico (não entende OS de calibração).
- **GAP CONFIRMADO**: módulo de comissão configurável com regras de calibração + integração nativa com Frota/UMC/Caixa do Técnico + cálculo sobre líquido = **vazio absoluto no mercado BR PME**. **7º gap defensável** (somar aos 6 já identificados).

**Riscos novos:**
- **R-novo C1:** Erro de configuração de regra de comissão (% errado, regra duplicada) → cálculo errado em escala → reclamação trabalhista. Mitigação: simulador "se rodasse hoje" antes de ativar; auditoria de toda mudança de regra; revisão por gerente antes de fechamento.
- **R-novo C2:** Vendedor descobre brecha (descontos pra própria empresa pra elevar margem aparente e ganhar mais comissão) → fraude interna. Mitigação: bloqueio de desconto acima de N% sem aprovação; alerta de padrão suspeito.
- **R-novo C3:** Comissão paga sobre fatura que cliente depois não pagou (inadimplência) → comissão paga indevidamente. Mitigação: regra "comissão só sobre recebido" + estorno automático em caso de cancelamento.

**Jobs-to-be-done implicados (a adicionar em `jobs-to-be-done.md`):**
- Roldão/gerente: configurar regra de comissão flexível sem depender de programador
- Roldão/gerente: ver demonstrativo de comissão por colaborador antes de aprovar pagamento
- Bruno/técnico: ver previsão de comissão do mês em tempo real
- Cláudia/financeiro: fechar comissão do mês em N horas (não dias)
- Vendedor: ver pipeline com previsão de comissão
- Roldão: bloquear comissão se OS deu prejuízo (sem ele precisar olhar 1 a 1)
- Sandra/Cláudia: aprovar/reprovar comissão com 1 clique
- Auditor: reconstruir cálculo histórico de comissão (rastreabilidade)

---

## Cliente 360°, CRM Contínuo e Automações ⭐ DECISÃO FUNDADORA DE PRODUTO (Roldão 17/05/2026)

> **Registrado em 17/05/2026** (texto redigido pelo Roldão — fonte de verdade). Define a **filosofia integrada** do sistema. Todo módulo conversa com todos.

### Conceito de Sistema Integrado

O sistema deve funcionar como um **organismo único**, onde todos os módulos estejam integrados entre si e compartilhem informações de forma automática, sem retrabalho e sem dados isolados.

A ideia principal é que o cliente nunca seja tratado apenas como um cadastro estático. Todo cliente cadastrado no sistema deve ser considerado também um **lead permanente**, com histórico, relacionamento contínuo, oportunidades futuras, contatos programados e acompanhamento comercial recorrente.

Mesmo após a venda, atendimento, manutenção ou calibração, esse cliente continua sendo uma oportunidade ativa, pois futuramente poderá precisar de: nova calibração, manutenção preventiva, manutenção corretiva, substituição de peças, atualização de sistema, venda de equipamentos, contrato de manutenção, renovação de certificado, nova visita técnica, novos serviços relacionados aos equipamentos cadastrados.

Portanto, o cliente nunca deve "morrer" dentro do CRM. Ele deve permanecer em acompanhamento contínuo, sempre com uma próxima ação, próxima oportunidade, próximo contato ou próximo vencimento a ser monitorado.

### Cliente como Lead Permanente

Todo cliente cadastrado deverá entrar automaticamente em uma lógica de relacionamento contínuo. Estados possíveis: prospecção, pós-venda, renovação de calibração, manutenção preventiva, contrato em negociação, oportunidade futura, cliente inativo a reativar, cliente com certificado próximo do vencimento, cliente com equipamento sem manutenção recente, cliente com proposta pendente, cliente com chamado aberto, cliente com OS em andamento, cliente com pendência financeira, cliente com oportunidade de venda de peças ou serviços.

**Lógica do sistema:** todo cliente tem histórico, presente e futuro. O sistema deve registrar o que já aconteceu, controlar o que está acontecendo e gerar ações para o que precisa acontecer depois.

### Visão 360° do Cliente

Tela única consolidada com: dados cadastrais, contatos, unidades/filiais, equipamentos cadastrados, histórico de calibrações, certificados emitidos, histórico de manutenções, chamados técnicos, OS, orçamentos, propostas, contratos, peças aplicadas, financeiro, NF, pagamentos, inadimplência, mensagens/e-mails/WhatsApp enviados, tarefas comerciais, oportunidades em aberto, próxima ação comercial, próxima calibração, próximo contato, documentos anexados, fotos, assinaturas, reclamações, NPS, histórico de relacionamento.

**Objetivo:** qualquer pessoa autorizada abre o cadastro e entende toda a relação do cliente com a empresa sem consultar vários módulos.

### Integração Chamado → OS → Calibração → CRM

Fluxo integrado: cliente contata → chamado técnico registrado → analisado/classificado/agendado → na data do atendimento gera OS → atribuída ao técnico → técnico executa → registra serviços → se calibração, lança dados → sistema gera certificado → equipamento atualizado com data → calcula próxima calibração → CRM atualizado → cria ações futuras pro vendedor → cliente recebe mensagens automáticas → vendedor recebe alertas → relacionamento ativo.

### Atualização Automática do CRM após Calibração

Quando calibração é registrada, o sistema atualiza automaticamente:
- data da calibração realizada, técnico responsável, equipamento, certificado gerado, resultado, validade
- **data da próxima calibração** (baseada na periodicidade configurada)
- status do equipamento, histórico do cliente
- **próxima oportunidade comercial, tarefa de contato, campanha automática**

Ex: Cliente calibrou balança em 17/05/2026 → periodicidade 12 meses → próxima 17/05/2027 → alertas automáticos 90/60/30/15/7 dias antes.

### Funil Comercial Contínuo

CRM como **funil contínuo de relacionamento, recorrência e reativação** (não só funil de venda inicial). Etapas: lead novo, prospecção, orçamento enviado, negociação, venda realizada, atendimento agendado, OS em execução, serviço concluído, pós-venda, certificado emitido, próxima calibração programada, vencimento próximo, contato comercial agendado, renovação em negociação, cliente recorrente, cliente inativo, cliente a reativar.

**Múltiplos funis configuráveis:** venda, calibração, manutenção, contratos, pós-venda, renovação, clientes inativos, recuperação de orçamento perdido.

### Módulo de Automações

Módulo dedicado, **configurável sem alterar código**, lógica **gatilho → condição → ação**.

Ex: Gatilho "certificado emitido" → Condição "periodicidade 12 meses" → Ação "criar tarefa pro vendedor 60 dias antes do vencimento + enviar WhatsApp automático 30 dias antes".

**Gatilhos suportados:** cliente cadastrado, lead criado, orçamento enviado/aprovado/recusado, chamado aberto/agendado, OS aberta/iniciada/concluída, calibração lançada, certificado gerado, certificado próximo do vencimento, equipamento sem calibração recente, manutenção concluída, peça substituída, contrato próximo do vencimento, parcela vencida, pagamento recebido, cliente sem contato há X período, cliente inativo, reclamação registrada, NPS recebido.

**Condições suportadas:** tipo de cliente, cidade, estado, segmento, vendedor responsável, técnico responsável, tipo de equipamento, tipo de serviço, status do cliente, status financeiro, data da última calibração, data da próxima calibração, valor do orçamento, valor da OS, inadimplência, periodicidade, contrato ativo/inativo, quantidade de equipamentos, prioridade, cliente estratégico, cliente sem contato há X dias.

**Ações suportadas:** criar tarefa (vendedor/técnico/admin), enviar WhatsApp, enviar e-mail, notificação interna, alterar etapa do funil, criar oportunidade, criar chamado técnico, gerar orçamento recorrente, agendar contato, atualizar status cliente, marcar ativo/inativo/recorrente, anexar certificado ao portal, enviar certificado ao cliente, avisar gestor, criar alerta financeiro, gerar pendência, atualizar dashboard.

### Reaproveitamento de Dados entre Módulos

Tudo lançado em um módulo alimenta os demais — sem duplicidade.

- **Cliente:** alimenta CRM, orçamentos, chamados, OS, contratos, financeiro, fiscal, portal, equipamentos, automações, relatórios.
- **Equipamento:** alimenta OS, calibração, certificado, histórico técnico, manutenção, peças aplicadas, cronograma, automações, oportunidades.
- **OS concluída:** alimenta histórico do cliente, histórico do equipamento, financeiro, comissão, estoque, certificado, CRM, pós-venda, automações, relatórios.
- **Certificado emitido:** alimenta histórico de calibração, validade do equipamento, próxima calibração, CRM, funil de renovação, portal do cliente, automações de aviso, tarefas comerciais.

### Filosofia geral do sistema

> **Toda ação operacional deve gerar inteligência comercial.**
> **Toda informação técnica deve alimentar o histórico do cliente.**
> **Toda calibração deve gerar oportunidade futura.**
> **Todo serviço concluído deve alimentar CRM, financeiro, estoque, comissões e relatórios.**
> **Todo cliente deve permanecer em relacionamento contínuo com a empresa.**

**Objetivo:** reduzir retrabalho, evitar perda de informações, impedir esquecimento de clientes, melhorar pós-venda, aumentar recorrência de calibrações, criar oportunidades automaticamente, acompanhar vencimentos, automatizar contatos, gerar tarefas pra vendedores, manter histórico técnico completo, melhorar gestão comercial/operacional, aumentar faturamento recorrente, dar visão completa do cliente pra equipe inteira.

---

### Anexo técnico — desdobramentos pra arquitetura

**Implicações pra modelo de dados:**
- Cliente é entidade raiz com FKs pra Equipamentos, OS, Certificados, Financeiro, Mensagens, Tarefas, Funil etc.
- Cada calibração emitida dispara `event` que alimenta CRM, Equipamento, Funil, Automações
- Próxima calibração = campo calculado (data_ultima + periodicidade) por equipamento, recalculado a cada certificado
- View Cliente 360° = query agregada cara — exige cache + materialização periódica

**Engine de Automações:**
- Trigger storage com retry idempotente
- DSL configurável (gatilho/condição/ação) sem código
- Aprovação humana antes de executar ação irreversível (envio em massa de WhatsApp)
- Sandbox de teste antes de ativar regra em produção
- Auditoria de toda execução (quem disparou, quando, resultado)

**Conexão com Big Jobs:**
- BIG-01 (ciclo completo) → este é o coração de BIG-01
- BIG-07 (portal cliente) → certificado integra portal automaticamente
- JTBD-044 (alerta renovação) → caso de uso central de Automações
- D-002 (recalibração esquecida — R$ 3-8k/mês perdido) → resolvida diretamente

**Gap competitivo confirmado:**
- Bling/Omie/Conta Azul têm CRM operacional, mas não cruzam com calibração/equipamento.
- Cali/Metroex/Calibre têm calibração, mas não têm CRM contínuo nem automação.
- HubSpot/RD Station têm automação, mas não entendem semântica de calibração.
- **GAP CONFIRMADO**: CRM 360° + Automações nativas em ciclo de calibração + integração total = **vazio no mercado BR**. **8º gap defensável.**

**Riscos novos:**
- **R-novo CRM-1:** Automação dispara mensagem indevida em massa pra cliente errado → reclamação no Reclame Aqui. Mitigação: sandbox + aprovação humana + opt-out granular.
- **R-novo CRM-2:** Cliente reclama de spam (LGPD art. 18 — oposição). Mitigação: opt-in granular por tipo de mensagem + canal de unsubscribe.
- **R-novo CRM-3:** Cliente Visma compra Conta Azul e adiciona engine de CRM/automação no produto deles + integra Cali = mata diferencial. Já citado em R-035.

---

## Módulo de Estoque Completo para Assistência Técnica ⭐ DECISÃO FUNDADORA DE PRODUTO (Roldão 17/05/2026)

> **Registrado em 17/05/2026** (texto redigido pelo Roldão — fonte de verdade). Estoque NÃO é "feature acessória" — é módulo central com rastreabilidade rigorosa de peças, lacres e selos INMETRO.

O sistema deverá possuir um **módulo de estoque robusto e totalmente integrado com a assistência técnica**, permitindo controlar peças, produtos, materiais, lacres, selos, ferramentas e demais itens utilizados nos atendimentos em campo.

Atende a realidade operacional: **estoque central + estoques móveis em veículos + estoque individual dos técnicos + estoque específico em caminhões operacionais (UMC)**. Rastreabilidade total da entrada até a utilização final em OS.

### Tipos de Estoque

- estoque central da empresa
- estoque por filial
- estoque por técnico
- estoque em veículo da empresa
- estoque em veículo particular utilizado pelo técnico
- estoque em caminhão operacional
- **estoque da UMC** (Unidade Móvel de Calibração)
- estoque sob responsabilidade do motorista
- estoque de peças usadas/retiradas do cliente
- estoque de sucata/descarte
- estoque de itens aguardando devolução
- estoque de itens em garantia ou RMA

Cada local tem responsável definido, histórico de movimentações e saldo em tempo real.

### Estoque Central

Local principal. Itens típicos: placas eletrônicas, células de carga, indicadores de pesagem, cabos, caixas de junção, fontes, conectores, módulos de comunicação, sensores, **lacres, selos de reparo do INMETRO**, ferramentas, materiais de instalação, peças de reposição.

Responsável controla: entradas, saídas, transferências, saldos, inventários, ajustes, perdas, devoluções, movimentações internas.

### Estoque do Técnico

Cada técnico pode ter estoque próprio (geralmente no veículo de atendimento). Veículo pode ser próprio do técnico, alugado pela empresa, da empresa ou outro operacional autorizado.

Sempre que técnico usar peça em OS, sistema baixa automaticamente do estoque dele + vincula à OS + cliente + equipamento.

### Estoque em Caminhão / UMC / Veículo Operacional

UMC ou caminhão tem estoque próprio sob responsabilidade do **motorista**. Contém: peças de reposição, cabos, conectores, lacres, selos, ferramentas, materiais de apoio, pesos-padrão, equipamentos auxiliares, itens usados em campo.

Motorista registra transferências pros técnicos quando entrega item durante atendimento.

### Transferência de Estoque em DUAS Etapas (CRÍTICO)

Toda transferência funciona com controle em duas etapas:
1. **Envio da transferência pelo responsável de origem**
2. **Aceite obrigatório pelo responsável de destino**

Evita divergências do tipo "peça transferida no sistema mas destino alega que não recebeu".

**Fluxo:** central separa peça → responsável lança transferência → status "**aguardando aceite**" → técnico notificado no app → técnico confere fisicamente → aceita ou recusa → após aceite, peça entra no estoque do técnico.

**Em caso de recusa, motivos:** item não recebido, item diferente, quantidade divergente, item danificado, número de série incorreto, outra justificativa.

Mesmo controle vale pra transferência motorista ↔ técnico em campo.

### Aplicativo Mobile (Android + iOS)

Técnico e motorista usam app pra: visualizar OS, registrar serviços, lançar peças, consultar estoque, aceitar transferências, solicitar peças (estoque central / motorista / UMC), registrar devolução, lançar fotos, coletar assinatura cliente, **registrar lacres retirados/instalados, selos INMETRO**, trabalhar offline quando internet for instável.

### Utilização de Peças na OS

Ao usar peça em OS, sistema registra: item, quantidade, número de série (se houver), lote (se houver), origem, técnico responsável, cliente, equipamento, data/hora, foto (quando necessário), observação técnica, peça retirada do equipamento antigo (quando houver). Baixa saldo do estoque do técnico automaticamente.

### Controle de Peças Retiradas do Cliente

Destinos possíveis: peça retornou pra empresa, ficou com o cliente, foi descartada, enviada pra garantia, será analisada tecnicamente, será reaproveitada, foi substituída em definitivo. Técnico tira foto da peça retirada + registra observações.

### Controle de Lacres

Sob responsabilidade do estoque central / técnico / motorista / veículo / UMC. **Controle individual** por número, status, histórico.

Estados: disponíveis, transferidos, em posse do técnico, aplicados, retirados, inutilizados, perdidos, devolvidos, vinculados a OS/equipamento/cliente.

**Lacres retirados da balança:** registrar inclusive lacres de concorrentes. Pra cada lacre retirado: número, tipo, quem instalou anteriormente (se identificado), se era da empresa ou concorrente, local instalado, motivo da retirada, foto antes/depois, observação técnica.

**Lacres instalados:** número, tipo, local instalação, equipamento, OS, técnico responsável, data/hora, foto, observação. Após lançar, sai automaticamente do estoque do técnico e fica vinculado ao equipamento.

### Controle de Selos de Reparo do INMETRO

Rastreabilidade ainda mais rigorosa. Cada selo tem controle individual: numeração, série, lote, status, responsável atual, data de recebimento, transferência, aplicação, inutilização, perda, devolução, OS, equipamento, cliente, técnico, foto, histórico completo.

Status: disponível, transferido, em posse do técnico, aplicado, cancelado, inutilizado, perdido, devolvido, aguardando conferência.

**Na OS, técnico informa:**
- **Selo retirado:** número, foto antes, motivo, localização no equipamento, observação, origem (próprio/concorrente/órgão metrológico).
- **Selo colocado:** número novo, foto instalado, localização, técnico, data/hora, OS, cliente, equipamento.

Sistema mantém histórico completo pra auditoria, fiscalização e rastreabilidade metrológica.

### Inventário e Conferência

Periodicidades: diárias, semanais, quinzenais, mensais, por fechamento de viagem, por troca de responsável, por encerramento de OS, por auditoria, por inventário geral.

Permite: contagem física, comparação com saldo, identificação de divergências, **justificativa obrigatória pra diferenças**, anexar fotos, aprovação por gestor, ajustes controlados, histórico de auditoria.

### Rastreabilidade Completa

Cada item tem histórico completo: onde entrou, quem recebeu, pra quem foi transferido, quando, quem aceitou, em qual veículo/técnico ficou, em qual OS foi usado, em qual cliente aplicado, em qual equipamento instalado, devolução, perda, descarte, conferência pendente.

### Controle de Responsabilidade

Sistema deixa claro quem é o responsável por cada item em cada momento:
- estoque central → almoxarifado;
- transferido pro técnico → técnico (após aceite);
- transferido pro caminhão → motorista (após aceite);
- aplicado na OS → vai pro histórico do cliente/equipamento;
- retirado do cliente → responsável definido conforme destino.

**Nenhuma movimentação crítica acontece sem identificação de usuário, data, hora e justificativa quando necessário.**

### Integração com OS

Na OS, técnico lança: peças usadas, materiais consumidos, lacres retirados/instalados, selos retirados/aplicados, peças substituídas, peças devolvidas, peças que ficaram com o cliente, fotos, observações, assinatura do cliente.

Ao finalizar OS, sistema atualiza automaticamente: estoque do técnico, do veículo, do caminhão, histórico do cliente, histórico do equipamento, financeiro, comissão, relatório técnico, certificado (se aplicável), rastreabilidade de lacres e selos.

### Integração com Compras e Reposição

Alertas automáticos: estoque mínimo atingido, peça crítica em falta, técnico com baixo estoque, veículo sem item obrigatório, UMC sem item essencial, lacres abaixo do mínimo, selos abaixo do mínimo, itens pendentes de aceite, divergência em inventário. Gera solicitações de compra automaticamente.

### Regras de Segurança e Auditoria

- Toda transferência tem origem, destino, responsável + aceite do destino.
- Toda recusa exige justificativa.
- Todo ajuste de estoque exige motivo.
- Itens críticos exigem aprovação de gestor.
- Lacres e selos têm controle individual.
- Baixa de peça na OS fica vinculada ao serviço.
- Fotos obrigatórias pra lacres e selos.
- Divergências de inventário geram alerta.
- Cancelamentos ficam em auditoria.
- **Usuários NÃO podem apagar movimentações** — apenas estornar com justificativa.

---

### Anexo técnico — desdobramentos

**Modelo de dados (entidades principais):**
- `LocalEstoque` (central / técnico / veículo / UMC / motorista / sucata / RMA / etc.)
- `Item` (peça, material, lacre, selo INMETRO) com flag `controle_individual` (sim/não)
- `Movimentacao` (entrada / saída / transferência / aplicação em OS / retirada de cliente / descarte)
- `Transferencia` (com status: aguardando aceite / aceito / recusado + motivo)
- `Lacre` (entidade própria com número, status, histórico)
- `SeloINMETRO` (entidade própria com série, lote, status, histórico)
- `Inventario` (snapshot periódico + divergências + ajustes)

**Mapa de domínios — adicionar:**

| Domínio | Módulos | Razão |
|---|---|---|
| **Estoque e Suprimentos** (já promovido a domínio próprio) — agora detalhado | Itens, Locais, Movimentações, Transferências 2-etapas, **Lacres (rastreabilidade individual)**, **Selos INMETRO (rastreabilidade individual + foto obrigatória)**, Inventário, Compras/Reposição, Mobile do técnico/motorista, Auditoria de divergências | Sem isso, peças caras somem; lacres/selos sem rastreabilidade = NC fiscal grave |

**Riscos novos:**
- **R-novo EST-1:** Selo INMETRO perdido → fiscalização IPEM exige justificativa formal + pode multar lab. Mitigação: rastreabilidade individual + foto obrigatória + workflow de perda com aprovação gestor.
- **R-novo EST-2:** Lacre/selo aplicado em equipamento errado → fraude metrológica. Mitigação: confirmação dupla (técnico + cliente assina foto).
- **R-novo EST-3:** Técnico recusa peça que recebeu (alega que não veio) → sumiço de peça. Mitigação: transferência 2 etapas + foto da peça na origem.
- **R-novo EST-4:** Inventário com divergência sistemática em técnico X → sinal de fraude. Mitigação: relatório de divergência por técnico ao gestor.

**Conexão com concorrentes:**
- **Bling/Omie/Conta Azul** têm estoque básico, mas não suportam multi-local (técnico, motorista, UMC), nem rastreabilidade individual de lacre/selo, nem transferência 2 etapas, nem foto obrigatória.
- **Cali/Metroex/Calibre** zero estoque.
- **Auvo** tem controle simples de peça em OS, sem multi-local nem lacre/selo INMETRO.
- **GAP CONFIRMADO**: estoque multi-local + lacres/selos INMETRO + transferência 2 etapas com aceite = **vazio absoluto no mercado BR**. **9º gap defensável.**

---

## Perfis de empresa (setup do tenant) ⭐ DECISÃO FUNDADORA DE PRODUTO (Roldão 17/05/2026)

> **Registrado em 16/05/2026** (decisão Roldão). Esta é decisão estrutural do produto, NÃO opcional. O setup do tenant DEVE pedir o perfil; o sistema ativa/desativa regras (invariantes) com base nele. Implica também que **algumas invariantes deixam de ser absolutas** e viram **condicionais ao perfil**.

### Os 4 perfis de empresa

| ID | Perfil | Selo do certificado | Padrões usados | Regras 17025 | Mercado típico |
|---|---|---|---|---|---|
| **A** | **Acreditada ISO/IEC 17025 + RBC** | Marca combinada Cgcre + ILAC MRA (RBC) | Padrões calibrados RBC ou rastreáveis ao SI | **Todas as invariantes ATIVAS e não-editáveis** — auditoria Cgcre exige | Lab acreditado pra emitir certificado válido pra cliente farma/automotivo/aeroespacial regulado |
| **B** | **Não-acreditada, com padrões RBC** | Sem selo RBC; **"Certificado de calibração rastreável ao RBC"** com declaração explícita de rastreabilidade | Padrões calibrados RBC (com certificado-pai válido) | **Todas as regras 17025 são CONFIGURÁVEIS pelo dono do tenant** — empresa B pode escolher rodar com regras 17025 totalmente ativas (preparando-se pra futura acreditação) OU com regras leves. Única trava absoluta: INV-015 (não pode emitir com selo RBC sem ser acreditada) | Empresa que quer credibilidade técnica sem ter passado por acreditação completa (ou que está só em preparação inicial) |
| **C** | **Quer trabalhar no padrão ISO pra futura homologação** | Configurável: pode emitir "Certificado rastreável ao RBC" ou "Certificado de calibração interno" | Padrões rastreados (RBC ou outros) | **Todas as invariantes ATIVAS por padrão, MAS editáveis** — funciona como trilha de evolução: empresa começa em C com algumas regras relaxadas e vai endurecendo conforme amadurece. **Ao migrar pra A, todas viram ativas e não-editáveis automaticamente** | Lab em preparação pra acreditação Cgcre (período típico: 12-24 meses) |
| **D** | **Calibração comercial básica** (nem ISO 17025 nem padrões RBC) | "Certificado de aferição" (NUNCA "calibração rastreável ao RBC" — proibido pelo INMETRO se não houver rastreabilidade) | Padrões próprios ou de origem variada | **Invariantes desativadas ou editáveis** (exceto integridade de dados e auditoria); sistema imita ERP "leve" de OS de manutenção | Assistência técnica que faz "calibração de balança" sem pretensão metrológica formal |

### Por que esses 4 perfis

- **A maioria dos concorrentes (Cali, Metroex, Calibre) atende só perfil A.** Eles assumem que o cliente é lab acreditado. Quem não é fica usando planilha + Word.
- **Perfis B, C e D são o GAP REAL não atendido.** É grande parte das empresas BR de assistência técnica que ainda quer profissionalizar mas não consegue (ou não quer) entrar na 17025.
- **Perfil C é diferencial competitivo único:** software como **trilha de evolução** pra acreditação. Cliente entra simples, vai apertando regras conforme prepara documentação. Migração final pra perfil A é só virar um flag.
- **Sem distinguir perfis, o sistema vira "OU rigoroso demais pra D OU frouxo demais pra A".** Os dois extremos perdem.

### Regras e travas configuráveis por perfil (corrigido 16/05/2026)

> **Princípio (correção Roldão):** apenas o **perfil A** tem regras totalmente travadas (porque Cgcre audita; afrouxar = perde acreditação). **Perfis B, C e D escolhem** quais regras 17025 querem aplicar — pode ser nenhuma, algumas ou todas. Setup do tenant pergunta isso como checklist editável.

- **Sempre absolutas (não-editáveis em NENHUM perfil — universais de produto):**
  - INV-001 (trilha de auditoria imutável)
  - INV-004c (versão do software gravada em cada certificado)
  - INV-005 (incidente LGPD em ≤3 dias úteis)
  - INV-006 (DPO publicado)
  - INV-007 (NF-e arquitetura SVC)
  - INV-008 (logs de acesso ≥6 meses)
  - INV-009 (MFA quando PCI aplica)
  - INV-013 (confidencialidade cláusula 4.2 com log de visualização)
  - **INV-015 — Tenant não emite certificado de tipo superior ao perfil declarado** (perfil B/C/D não pode emitir com selo RBC; perfil D não pode declarar rastreabilidade que não tem). **Esse é o único invariante que SEPARA os perfis — quebrá-lo é fraude regulatória.**
- **Absolutas em perfil A (não-editáveis); CONFIGURÁVEIS pelo dono do tenant em B, C, D:**
  - INV-002 (cadeia de rastreabilidade na emissão)
  - INV-003 (signatário por escopo)
  - INV-004a (deploy só com aprovação RT)
  - INV-004b (revalidação de cálculo de incerteza)
  - INV-010 (retenção 17025)
  - INV-011 (padrão vencido bloqueia emissão)
  - INV-012 (workflow NC bloqueia emissão)
  - INV-014 (certificado externo sem incerteza bloqueia)
- **Sempre configuráveis (todos os perfis podem ligar/desligar):**
  - Pesquisa de satisfação automática, alerta de validade, formato de PDF, idioma do certificado, templates personalizados

**Implicação prática:** o setup do tenant B/C/D tem checklist "quais regras 17025 você quer aplicar?" — empresa escolhe à la carte. Empresa B com ambição de acreditação ativa tudo (vira `B-rigoroso`, equivalente a A sem o selo). Empresa D pode desativar tudo (vira ERP de OS comum). Mudanças são auditadas (log de quem mudou + quando).

### Implicações pra arquitetura

- Setup do tenant tem step obrigatório "qual o perfil da sua empresa?" com explicação de cada um.
- Perfil é **mutável** (cliente pode migrar C→A quando se acreditar) mas **com auditoria** (todas as mudanças ficam no log).
- **Modelo do certificado depende do perfil:** templates A e B têm campos obrigatórios diferentes (B obrigatoriamente exibe declaração "RASTREÁVEL AO RBC, mas SEM acreditação Cgcre"); template D não menciona RBC.
- **Risco regulatório novo (R-039):** tenant declarar perfil A sem ter acreditação real e emitir certificado com selo RBC falso = fraude. Sistema precisa pedir prova documental no upgrade pra perfil A.

---

## Tipos de instrumento atendidos (configurável no setup) ⭐

> **Confirmado pelo Roldão (16/05/2026):** o produto cobre **TODOS os tipos de balança + instrumentos correlatos**. Mas o **tenant escolhe no setup quais tipos atende** — pode ser 1, 2, 3 ou todos, e a configuração é **editável a qualquer momento** (empresa começa atendendo balança comercial, depois expande pra rodoviária, depois adiciona manômetro, etc.).
>
> **Implicação:**
> - Setup do tenant tem checklist "tipos atendidos" (marcar 1 ou mais).
> - Empresa só vê dashboards/filtros/relatórios dos tipos que marcou (UI limpa).
> - Adicionar tipo novo depois é self-service (sem entrar em contato com suporte).
> - Pricing pode estar atrelado (mais tipos = mais módulos = tier maior — a confirmar no `precificacao-mercado.md`).
> - Sistema sugere/recomenda regras 17025 específicas por tipo (ex: balança rodoviária ativa INV-014 obrigatoriamente; manômetro ativa diferente).
>
> **Resolve D-aud-7:** Metrologia Legal ENTRA no MVP (balança comercial + rodoviária são reguladas).

| Tipo | Onde se usa | Regulamentação dominante | Implicação pro produto |
|---|---|---|---|
| **Balança comercial** | Açougue, padaria, supermercado, feira, varejo em geral | **INMETRO Portaria 157/2022** (substitui Portaria 236/1994 — verificação metrológica legal via IPEM/RBMLQ-I) | Sistema precisa de calendário de **obrigação de verificação periódica** (anual via IPEM). **Atenção:** a marca/selo INMETRO colocado na balança **NÃO tem vencimento estampado** — o que existe é a obrigação legal de submeter à verificação periódica anual. Marca/selo é prova de que verificação foi feita, não tem prazo próprio |
| **Balança industrial** | Linha de produção, dosadora, pesagem em lote | Geralmente **rastreabilidade ao SI** via padrões RBC; opcional acreditação ISO 17025 | Calibração + cálculo de incerteza em múltiplos pontos da faixa; pode emitir certificado RBC se cliente quiser |
| **Balança rodoviária** | Pesagem de caminhão (postos fiscais, pedágio, mina, usina, frigorífico) | **INMETRO Portaria 102/2017** (rodoviária) + DNIT (fiscalização) + INMETRO Portaria 157/2022 | Calibração com cargas-padrão grandes (100kg a 30 ton); logística pesada; certificado pode ter implicação tributária (peso de carga = ICMS) |
| **Balança de processo / dosadora** | Química, farma, alimentos, cosmética | **Anvisa RDC 658/2022** (BPF) + ISO 17025 + IQ/OQ/PQ pra farma | Calibração + validação do sistema computadorizado da balança (FDA 21 CFR Part 11 quando exporta pra cliente farma EUA) |
| **Balança analítica / semi-analítica** | Laboratório (química, farma, P&D) | **Resolução RDC ANVISA** + ISO 17025 + EURACHEM/CITAC (incerteza) | Faixa de pesagem pequena (mg-g); incerteza expandida exigida; calibração em vários pontos |
| **Balança de bancada** | Geral (oficina, loja, lab interno) | Variável conforme uso | Mais simples; perfil D ou C costuma servir |
| **Balança contadora de peças** | Logística, almoxarifado | Variável; geralmente sem regulação específica | Calibração de pesagem + verificação da função de contagem |
| **Balança de gancho / suspensa** | Movimentação de carga, frigorífico | Pode ter regulamentação setorial (ex: MAPA pra frigorífico) | Calibração com células de carga; cuidado com segurança operacional |
| **Balança plataforma** | Indústria, logística | Similar à industrial | Faixa média (até 1-3 ton) |
| **Outros instrumentos correlatos** (frequentes em assistência técnica) | Manômetros, termômetros, termo-higrômetros, paquímetros, micrômetros, multímetros, células de carga | Variável por grandeza | O produto deve modelar instrumento genérico, não só balança |

### Implicação pro mapa de domínios

- **Domínio "Metrologia Legal"** foi adicionado no v5 anterior — **agora confirmado como MVP-1 obrigatório**, com base no escopo "balança comercial + rodoviária".
- **Sub-domínio "Verificação periódica"** dentro de Metrologia Legal: agenda de verificação INMETRO/IPEM por estado, geração de aviso ao cliente com 60-90 dias de antecedência, integração com layout de comunicação IPEM se houver.
- **Domínio "Estoque e Suprimentos"** (já adicionado) atende peças de reposição (célula de carga, mostrador, fonte, cabo, indicador).

---

## Mapa preliminar de domínios → módulos prováveis (entrada pra `faseamento-modulos.md` e `sintese-final.md`)

> **Bordas a confirmar nas entrevistas** (Onda 1+2). Este mapa não fixa N nem ordem — só lista os candidatos identificáveis pela observação do setor.

| Domínio | Módulos candidatos | Já confirmados como prioritários? |
|---|---|---|
| **Comercial** | CRM, Orçamentos, Pedidos/Contratos, Comissões, Pipeline de oportunidades, Portal do prospect | CRM + Orçamentos confirmados (estão entre os 6 do banner do v5) |
| **Operação** | Chamados/Tickets, OS, Agenda do técnico, Logística (recebimento/devolução de instrumento), Mobile do técnico de campo | Chamados + OS confirmados; mobile do técnico fica em ADR-0003 obrigatório |
| **Estoque e Suprimentos** ⭐ | Cadastro de peças (NCM, CFOP, lote, validade), entrada/saída, movimentação, inventário, fornecedores, compras, recebimento, peças aplicadas em OS, **venda de peça avulsa pra cliente** | **PROMOVIDO a domínio próprio** (16/05/2026, decisão Roldão). Razão: empresa fornece peças usadas no reparo das balanças → estoque é receita + custo, não acessório de OS. Auditor 3 já tinha sugerido. |
| **Metrologia** ⭐ subdividido | **3 sub-domínios** (decisão Roldão pós-auditoria, 16/05/2026): (a) **Execução de calibração** — OS de calibração, cálculo de incerteza, emissão de certificado; (b) **Padrões e rastreabilidade** — gestão de padrões da empresa, validade, cadeia rastreada, certificados-pai; (c) **Garantia da validade** — ensaios de proficiência (EP), cartas de controle, validação de método, intercomparações. Materializar a estrutura quando módulo entrar no faseamento. | Calibração é o **diferencial central** — confirmado |
| **Metrologia Legal** (NOVO) | Verificação metrológica legal (balança comercial Portaria INMETRO 157/2022; bomba combustível Portaria 227/2022; etilômetro Portaria 006/2002; taxímetro), integração com IPEM estadual (RBMLQ-I), calendário de verificação periódica, selo de verificação | **NOVO domínio** (decisão Roldão pós-auditoria, 16/05/2026). Confirmar se está no escopo do MVP: depende de Roldão atender cliente de balança/bomba. Pode entrar como sub-domínio de Metrologia ou como flag/perfil dentro de Calibração |
| **Financeiro** | NFS-e, NF-e, Contas a pagar/receber, Conciliação bancária, Fluxo de caixa, DRE, Boleto/PIX, Cobrança automatizada | "Financeiro de alto nível" confirmado |
| **Suporte/Plataforma** | RBAC/permissões, Multi-tenant ops, Notificações/Webhooks, Auditoria/Logs, Configurações por tenant, Onboarding, Integrações externas | Implícito (sem isso o produto não funciona como SaaS) |
| **Conformidade e Qualidade** (a confirmar) | LGPD (consentimento, direitos do titular, RIPD), Gestão documental ISO 9001/17025, NC e ação corretiva, Auditoria interna, Treinamento | Surgiu na auditoria (Família 6); **possivelmente vira domínio próprio** dependendo do peso pra clientes RBC |
| **Atendimento ao cliente** (a confirmar) | Portal do cliente (download de certificado, histórico, abertura de chamado), Pesquisa de satisfação, FAQ/conteúdo | Forte sinal de demanda pelo levantamento de concorrentes (Cali WEB e similares têm portal) |
| **BI/Analytics** (a confirmar — pode ser lazy) | Dashboards, relatórios programados, exports, KPIs por papel | Necessário, mas pode ser entregue como visão simples no MVP |
| **Gestão de Competências e Autorizações** ⭐ | Matriz competência × grandeza, validade de qualificação, registro de treinamento, autorização de signatário por escopo, evidências para auditoria | **OBRIGATÓRIO NO MVP-1** (decisão Roldão pós-auditoria, 16/05/2026). Razão: 17025 cláusula 6.2 exige autorização documentada do signatário — sem isso o sistema NÃO PODE emitir certificado válido. Escopo magro (NÃO é RH completo): só matriz + validade + autorização. Folha/ponto/holerite ficam fora ou via integração externa |
| **RH/Pessoas** (lazy) | Folha de pagamento, ponto, holerite, férias, demais processos de RH | Fora do MVP-1; resolver via integração com Pontomais/Senior/Sankhya RH quando necessário |

**Riscos do mapa:**

- **Inflar contagem de módulos** sem dor confirmada por entrevista é gatilho de "ERP que nunca termina". Auditor 6 alertou: critério de promoção módulo precisa ser dor real + diferencial defensável (não "tem em ERP A e B, vamos ter também").
- **Domínios podem se fundir após entrevistas.** Ex: se "Conformidade" for sempre operada pelos mesmos papéis de "Metrologia", pode ficar tudo embaixo de Metrologia. Decidir depois de mapear papéis reais.
- **Portal do cliente é tentação de over-design.** Validar via WTP test (`validacao-ativa.md`) se cliente final (cliente do nosso cliente) realmente vai usar — ou se é "feature pra marketing".

---

## Como preencher

- Agente lê normas + literatura técnica + observa Roldão na empresa dele.
- Roldão valida porque vive o domínio.
- Validar com entrevistas (Onda 1 onda 2) — ajustar a partir do que outros dizem.

## Saída esperada

- Modelo conceitual sólido do setor
- Glossário inicial (vai pra `docs/comum/glossario.md` após filtragem)
- Lista de papéis (vai pra `personas-detalhadas.md`)
- Lista de processos (vai pra `dores-mapeadas.md` quando entrevistas mapearem dor em cada)
