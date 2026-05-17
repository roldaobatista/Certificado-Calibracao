# Discovery — Domínio de negócio

> **Artefato Rodada 0** (agente faz sozinho, Roldão valida). Modelo conceitual de "como uma empresa de assistência técnica + calibração funciona" + glossário operacional do setor. **Base do glossário comum** (Família 2).
> **Atualizado:** 2026-05-16 — primeira passagem do agente, base pra Roldão complementar com vivência da empresa dele. Marcações `[Roldão validar]` apontam onde precisa de input direto antes de virar invariante de produto.

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
