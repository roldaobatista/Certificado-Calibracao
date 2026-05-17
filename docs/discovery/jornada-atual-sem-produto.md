# Discovery — Jornada atual (status quo, SEM o produto Aferê)

> **Artefato Rodada 0 / Batch 2** — mapeamento do "como uma empresa brasileira de assistência técnica + laboratório de calibração roda HOJE", sem nenhum produto integrado.
>
> **Status:** primeira passagem do agente (17/05/2026). Marcações `[a confirmar via entrevista]` apontam estimativas que precisam ser quantificadas nas Ondas 1 e 2 de entrevistas com clientes-alvo.
>
> **Objetivo:** servir de base para (a) demonstrar a dor real nas entrevistas, (b) quantificar custo do status quo (tempo perdido, retrabalho, erro humano, multa regulatória, cliente perdido), (c) priorizar onde o MVP-1 do Aferê entra primeiro com maior ROI percebido.
>
> **Princípio editorial:** este documento descreve **dor**, NÃO solução. Quando aparecer a tentação de escrever "o Aferê resolveria isso fazendo X", parar — esse conteúdo vai em `faseamento-modulos.md` e `painel-do-dono.md`.

---

## 1. Resumo executivo

A empresa brasileira típica de assistência técnica + calibração roda hoje em cima de uma **colcha de retalhos digital**: WhatsApp Business pra atender cliente, planilha Excel pra cadastrar instrumento e acompanhar OS, e-mail pra mandar orçamento e certificado, Word pra escrever o relatório técnico, **Cali ou Metroex** (quando existe acreditação RBC) só pra calcular incerteza e gerar o PDF do certificado, **Bling, Conta Azul ou Omie** pra emitir NFS-e e controlar financeiro, **Drive da Google ou pasta de rede** pra arquivar PDF, e **caderno do técnico** ou bloco de notas do celular pra anotar o que foi feito no campo. Nada disso conversa entre si — a "integração" é **copiar e colar feito por humano**, normalmente o atendente ou o dono. O mesmo dado de cliente (CNPJ, endereço, contato) é digitado de novo em 4 a 6 ferramentas diferentes ao longo de um único ciclo, multiplicando chance de erro de digitação, divergência de cadastro e atraso em cada handoff. **Estimativa preliminar (a quantificar):** uma empresa de 10 a 20 funcionários perde entre **80 e 150 horas/mês** com retrabalho administrativo evitável, e perde 1 a 3 clientes por trimestre por demora na resposta ou erro de certificado. O dono passa **2 a 4 horas por dia "apagando incêndio"** (cliente reclamando, técnico perdido na rua, certificado errado, boleto vencido sem cobrança) que poderiam ser evitados se houvesse fluxo único.

---

## 2. Empresa típica de referência (perfil B-rigoroso / A enxuto)

Como o Discovery decidiu mapear 4 perfis (A/B/C/D), o caso-base escolhido é o **lab calibrador médio brasileiro** — porque é o caso mais complexo (regulatório + comercial + fiscal) e os outros perfis são simplificações dele. As variações por perfil estão na seção 9.

### 2.1 Cartão de identidade da empresa-modelo

| Atributo | Valor de referência |
|---|---|
| Razão social | "Calibratec Soluções Metrológicas Ltda" (nome fictício) |
| Localização | Interior de SP, RS, PR, MG ou GO (cidade-polo industrial de 100 a 500 mil habitantes) |
| Tempo de mercado | 8 a 15 anos |
| Faturamento mensal estimado | R$ 80 mil a R$ 300 mil |
| Regime tributário | Lucro Presumido (já saiu do Simples) ou Simples Nacional faixa alta |
| Funcionários | 10 a 20 |
| Acreditação | Perfil B (rastreável ao RBC sem selo) OU Perfil A em escopo limitado (1 a 3 grandezas acreditadas, resto não) |
| Tipos de instrumento que atende | Balanças (comercial + industrial + analítica) + manômetros + termômetros + 1 ou 2 grandezas adicionais |
| Mix de receita | ~60% calibração (lab + campo) / ~30% assistência técnica + peças / ~10% venda de instrumento |
| Tickets de calibração/mês | 80 a 250 certificados emitidos |
| OS de manutenção/mês | 30 a 100 chamados ativos |
| Carteira de clientes ativos | 150 a 400 PJ |
| Distância média até cliente | 30 a 250 km (atende região metropolitana + interior próximo) |

### 2.2 Organograma operacional típico

```
Sócio-dono (1-2)
   |
   +-- Gerente operacional (1) -- triagem, agenda, "apaga incêndio"
   |       |
   |       +-- Atendente / SAC (1-2) -- WhatsApp + telefone + e-mail
   |       |
   |       +-- Técnico de campo (2-4) -- van/carro, sai cedo, volta tarde
   |       |
   |       +-- Técnico de bancada / lab (1-2) -- calibra instrumento que chega
   |
   +-- Signatário técnico / metrologista (1) -- assina certificado, responde RBC
   |
   +-- Financeiro / administrativo (1) -- NFS-e, boleto, conciliação, cobrança
   |
   +-- Comercial / vendedor (0-1, às vezes é o próprio dono)
```

**Observações estruturais críticas para o discovery:**

- **Signatário técnico é gargalo crônico.** Geralmente é uma pessoa só (às vezes o próprio dono), com escopo de assinatura limitado pelo NIT-DICLA-021. Quando ele tira férias, fica doente ou viaja, a emissão de certificados PARA. Isso é uma das **maiores dores ocultas** do setor (R-015 no inventário de riscos).
- **Atendente acumula função.** Não é só "tirar pedido": cadastra cliente em planilha, cria OS em outra planilha, copia dados pra orçamento em Word, fotografa instrumento no WhatsApp, encaminha pro técnico, atualiza status no grupo de WhatsApp interno, lembra o dono de cobrar. É a peça que mais sofre com a fragmentação.
- **Financeiro NÃO é o mesmo que comercial.** Mas em empresa pequena costuma ser a mesma pessoa, o que cria conflito de prioridade (cobrar cliente atrasado vs fechar venda nova).
- **Dono opera no nível operacional.** Não consegue planejar porque vive resolvendo problema do dia (técnico ligando perdido, cliente reclamando de certificado errado, financeiro pedindo boleto). É o perfil que o Aferê precisa libertar — exatamente o que motivou o `painel-do-dono.md`.

---

## 3. Mapa visual da jornada — 4 ciclos principais

A operação se organiza em 4 ciclos que **se sobrepõem temporalmente** mas que **as ferramentas atuais tratam como ilhas isoladas**. O custo do status quo está nas fronteiras entre ciclos — porque é nas fronteiras que o humano vira "cabo integrador".

```
                    +-------------------+      +-------------------+
                    |  CICLO COMERCIAL  | ---> |  CICLO OPERAC.    |
                    |  prospect ->      |      |  chamado -> OS    |
                    |  orçamento ->     |      |  -> execução      |
                    |  fechamento       |      |  (lab OU campo)   |
                    +-------------------+      +-------------------+
                            |                          |
                            |                          | (se calibração)
                            |                          v
                            |                  +-------------------+
                            |                  |  CICLO METROLÓG.  |
                            |                  |  entrada control. |
                            |                  |  -> calibração    |
                            |                  |  -> certificado   |
                            |                  +-------------------+
                            |                          |
                            v                          v
                    +---------------------------------------+
                    |        CICLO FINANCEIRO               |
                    |  NFS-e -> boleto/PIX -> conciliação   |
                    |  -> cobrança -> baixa                 |
                    +---------------------------------------+
```

**Onde estão as costuras humanas hoje (= onde o dado é COPIADO MANUALMENTE):**

1. Entre Comercial e Operacional: orçamento aprovado precisa virar OS — copia-cola de dados do cliente, do instrumento e do escopo do serviço.
2. Entre Operacional e Metrológico: OS de calibração precisa virar entrada controlada no Cali/Metroex — copia-cola de dados do instrumento, faixa, ponto, padrão.
3. Entre Metrológico e Operacional: certificado emitido precisa voltar pra OS pra fechar e encaminhar pro financeiro — copia-cola de número do certificado, data, signatário.
4. Entre Operacional e Financeiro: OS fechada precisa virar NFS-e no Bling/Conta Azul — copia-cola de dados do cliente, descrição do serviço, valor.
5. Entre Financeiro e Comercial: cliente inadimplente precisa ser bloqueado pra novos serviços — comunicação por WhatsApp interno, planilha de inadimplência, nada automatizado.

**Cada copia-cola = 30 segundos a 5 minutos + risco de erro de digitação.** Multiplicando por 80-250 certificados/mês + 30-100 OS/mês, a conta de horas perdidas é o que justifica o produto.

---

## 4. Detalhamento do Ciclo Comercial

> **Da primeira conversa ao "pode iniciar o serviço".**

### Etapa 4.1 — Captação do prospect

| Item | Detalhe |
|---|---|
| Quem faz | Vendedor (ou dono) |
| Onde acontece | WhatsApp Business (canal #1, ~70% dos contatos), telefone fixo/celular (~20%), e-mail (~10%), feira/visita de campo (esporádico) |
| Ferramenta hoje | WhatsApp Business + caderno do vendedor + planilha "prospects.xlsx" no Drive |
| Tempo médio | 5 a 15 min por contato inicial |
| Onde dói | Não existe funil estruturado — prospect "esquecido" na conversa do WhatsApp é receita perdida. Vendedor não tem visão de quantos contatos abertos tem na semana. Dono não sabe quantos prospects entraram esse mês |
| Vezes que o dado é copiado | 1 a 2 (WhatsApp → planilha, às vezes WhatsApp → caderno → planilha) |
| Risco regulatório | Baixo. LGPD: cliente PJ é dado de cadastro empresarial (geralmente público), mas se entrar dado de pessoa de contato é dado pessoal — base legal "execução de contrato" cobre, mas precisa ser registrada |

### Etapa 4.2 — Qualificação (entendimento da necessidade)

| Item | Detalhe |
|---|---|
| Quem faz | Vendedor + às vezes técnico (quando demanda é técnica complexa) |
| Onde acontece | WhatsApp + telefone + visita |
| Ferramenta hoje | Nenhuma estruturada. Conversa, anotação em caderno, foto do instrumento no WhatsApp |
| Tempo médio | 15 a 60 min por prospect (dependendo da complexidade) |
| Onde dói | Vendedor frequentemente não tem competência técnica pra entender "que padrão precisa? que faixa? que incerteza o cliente exige?" → erro no orçamento. Técnico interrompido constantemente pra "consulta" |
| Vezes que o dado é copiado | 0 a 1 (informação fica na cabeça/caderno) |
| Risco regulatório | Baixo |

### Etapa 4.3 — Levantamento técnico (visita ou pedido de fotos/specs)

| Item | Detalhe |
|---|---|
| Quem faz | Técnico de campo (visita ao cliente) OU cliente envia foto + nota fiscal do instrumento |
| Onde acontece | No cliente (visita) ou WhatsApp (foto/spec) |
| Ferramenta hoje | Câmera do celular, WhatsApp, caderno do técnico, planilha "instrumentos clientes.xlsx" |
| Tempo médio | 30 min a 4 horas (depende da quantidade de instrumentos) |
| Onde dói | Visita custa caro (combustível + hora do técnico) e frequentemente não vira venda. Foto de instrumento mandada por WhatsApp some na conversa depois de 2 semanas. Spec técnica do instrumento (faixa, classe de exatidão, número de série, fabricante) é digitada 3 vezes: planilha de prospect, orçamento, OS |
| Vezes que o dado é copiado | 2 a 4 |
| Risco regulatório | Baixo |

### Etapa 4.4 — Elaboração do orçamento

| Item | Detalhe |
|---|---|
| Quem faz | Vendedor ou atendente (com revisão técnica do dono/signatário em casos complexos) |
| Onde acontece | Computador do escritório |
| Ferramenta hoje | Word ou Excel com template "Orçamento padrão.docx" salvo no Drive. Cálculo do preço em planilha separada "tabela de preços.xlsx" — frequentemente desatualizada |
| Tempo médio | 20 a 90 min por orçamento (dependendo do número de instrumentos) |
| Onde dói | Tabela de preço desatualizada → margem errada. Esquecimento de incluir deslocamento, hora-técnica, peças, ART (Anotação de Responsabilidade Técnica). Cliente pede "desconto pra fechar" e vendedor não sabe até onde pode ir. Versionamento manual ("Orçamento João v3 FINAL FINAL2.docx") gera confusão. Cliente recebe orçamento errado e isso queima credibilidade |
| Vezes que o dado é copiado | 3 a 5 (cadastro cliente + lista de instrumentos + tabela de preço + template Word) |
| Risco regulatório | Baixo, mas ART de calibração quando exigida tem retenção 5 anos |

### Etapa 4.5 — Envio do orçamento ao cliente

| Item | Detalhe |
|---|---|
| Quem faz | Vendedor / atendente |
| Onde acontece | E-mail OU WhatsApp (PDF anexo) |
| Ferramenta hoje | Outlook/Gmail OU WhatsApp Business |
| Tempo médio | 5 a 15 min |
| Onde dói | Vendedor não sabe se cliente abriu o e-mail. Cliente pede "pode mandar de novo?" porque perdeu. Versão errada enviada (Orçamento v2 em vez de v3). PDF mandado por WhatsApp some na conversa em 1-2 semanas |
| Vezes que o dado é copiado | 0 a 1 |

### Etapa 4.6 — Follow-up / negociação

| Item | Detalhe |
|---|---|
| Quem faz | Vendedor / dono |
| Onde acontece | WhatsApp + telefone |
| Ferramenta hoje | Caderno do vendedor + planilha (raramente atualizada) |
| Tempo médio | 5 a 30 min por interação, com 1 a 5 interações por prospect ao longo de 1 a 6 semanas |
| Onde dói | **Esquecimento de follow-up é causa #1 de perda de venda** [a confirmar via entrevista]. Vendedor "promete ligar amanhã" e não liga. Dono pergunta "o que aconteceu com o orçamento da Empresa X?" e ninguém sabe |
| Vezes que o dado é copiado | 0 |
| Risco regulatório | Baixo |

### Etapa 4.7 — Aprovação formal do cliente

| Item | Detalhe |
|---|---|
| Quem faz | Cliente confirma via e-mail, WhatsApp ou ordem de compra (PO) |
| Onde acontece | Mesmo canal do orçamento |
| Ferramenta hoje | E-mail ou print de WhatsApp salvo em pasta "Pedidos confirmados/2026/" |
| Tempo médio | Variável — confirmação formal pode levar de 1 dia a 3 semanas |
| Onde dói | Cliente "aprova verbalmente" no WhatsApp e depois nega — "eu não disse que aprovava, falei que ia ver". Sem prova documental, lab faz o serviço e fica sem receber. Cliente esquece que aprovou e reclama da nota fiscal |
| Vezes que o dado é copiado | 1 (do canal pro arquivo) |
| Risco regulatório | **CDC (Lei 8.078/90)**: aprovação verbal sem prova escrita gera vulnerabilidade em caso de disputa — especialmente B2C ou PME PF |

### Etapa 4.8 — Cadastro de cliente novo no sistema

| Item | Detalhe |
|---|---|
| Quem faz | Atendente ou financeiro |
| Onde acontece | Múltiplos sistemas em sequência |
| Ferramenta hoje | (1) Planilha "Clientes.xlsx" / (2) Bling ou Conta Azul (pra emitir NFS-e) / (3) Cali ou Metroex (se for calibração) / (4) Planilha de OS / (5) Grupo de WhatsApp interno avisando "novo cliente" |
| Tempo médio | 20 a 45 min por cliente novo (digitar CNPJ, IE, IM, endereço, contato, e-mail, condição de pagamento, regime tributário em 4-5 sistemas) |
| Onde dói | **MESMO DADO digitado de 4 a 6 vezes.** Erro de digitação em CNPJ trava NFS-e depois. Endereço diferente entre sistemas → técnico vai pra endereço errado. E-mail divergente → certificado vai pro lugar errado. Cliente "renomeado" num sistema e não no outro → relatório financeiro não bate com operacional |
| Vezes que o dado é copiado | **4 a 6** — é o pior ponto de duplicação da jornada |
| Risco regulatório | LGPD: cadastro de pessoa de contato sem base legal explícita; risco de divergência entre sistemas dificulta resposta a direito do titular (acesso, retificação) |

---

## 5. Detalhamento do Ciclo Operacional

> **Do "pode iniciar" à execução do serviço — em laboratório OU em campo.**

### Etapa 5.1 — Abertura do chamado / OS

| Item | Detalhe |
|---|---|
| Quem faz | Atendente |
| Onde acontece | Após confirmação comercial OU após contato direto do cliente "vim deixar a balança" |
| Ferramenta hoje | Planilha "Controle OS 2026.xlsx" com colunas (Nº OS, Cliente, Instrumento, Serviço, Status, Técnico, Data prevista, Data real, Valor). Numeração de OS manual e frequentemente furada/duplicada |
| Tempo médio | 10 a 25 min |
| Onde dói | Numeração de OS duplicada quando 2 atendentes abrem ao mesmo tempo. Planilha trava com 5 mil linhas. Sem visão de "carga de trabalho por técnico" — atendente atribui no escuro. Dono não sabe quantas OS abertas tem |
| Vezes que o dado é copiado | 2 (do orçamento → planilha OS; depois planilha OS → caderno do técnico) |
| Risco regulatório | **17025 cláusula 7.1 — Análise crítica de pedidos:** lab precisa registrar análise crítica de cada solicitação ANTES de iniciar. Planilha não obriga isso → NC em auditoria Cgcre |

### Etapa 5.2 — Triagem (manutenção vs calibração vs venda de peça)

| Item | Detalhe |
|---|---|
| Quem faz | Gerente operacional ou técnico sênior |
| Onde acontece | Olhando a planilha + conversando com atendente |
| Ferramenta hoje | Reunião curta, mensagem no grupo de WhatsApp interno |
| Tempo médio | 5 a 15 min por OS |
| Onde dói | Triagem errada — calibração vira manutenção (perde receita regulatória) OU manutenção vira calibração (técnico sem padrão vai calibrar). Cliente cobrado errado. Retrabalho |
| Vezes que o dado é copiado | 0-1 (atualização do "tipo" na planilha) |
| Risco regulatório | Médio — triagem errada pode levar a emissão indevida de certificado (perfil A: NC grave) |

### Etapa 5.3 — Atribuição de técnico + agendamento

| Item | Detalhe |
|---|---|
| Quem faz | Gerente operacional |
| Onde acontece | Planilha "Agenda Técnicos.xlsx" com aba por técnico + Google Calendar individual de cada técnico (quando usa) |
| Ferramenta hoje | Planilha + WhatsApp avisando o técnico ("João, amanhã 8h, Cliente Y, Rua Z") |
| Tempo médio | 5 a 15 min por OS agendada |
| Onde dói | **Roteirização péssima:** técnico A vai pra zona norte de manhã e zona sul à tarde, técnico B faz o oposto, gastando 2x o combustível e 2x o tempo. Cancelamento de cliente em cima da hora deixa técnico ocioso. Técnico esquece compromisso porque foi avisado só por WhatsApp |
| Vezes que o dado é copiado | 2 a 3 (planilha OS → planilha agenda → WhatsApp técnico → Google Calendar) |
| Risco regulatório | Baixo |

### Etapa 5.4 — Preparação do técnico (pra ir a campo)

| Item | Detalhe |
|---|---|
| Quem faz | Técnico de campo |
| Onde acontece | Laboratório, antes de sair |
| Ferramenta hoje | Imprime OS da planilha em papel, pega ficha técnica do instrumento (quando existe), separa padrões do armário, anota número de série dos padrões num caderno, pega ferramentas, abastece carro |
| Tempo médio | 30 a 90 min |
| Onde dói | Padrão errado levado (não cobre faixa do instrumento do cliente) → técnico chega e não consegue calibrar → cliente irritado → 2ª visita = prejuízo. Padrão VENCIDO levado (calibração do padrão expirou e ninguém percebeu) → certificado emitido é NULO em auditoria Cgcre |
| Vezes que o dado é copiado | 2 (planilha → papel → caderno) |
| Risco regulatório | **17025 cláusula 6.5 + INV-011:** padrão vencido invalida calibração. **Risco crítico, materializou várias vezes no setor** [a confirmar frequência via entrevista] |

### Etapa 5.5 — Execução em campo (calibração in loco ou manutenção)

| Item | Detalhe |
|---|---|
| Quem faz | Técnico de campo |
| Onde acontece | Cliente |
| Ferramenta hoje | Caderno de campo + planilha em papel + foto do instrumento + WhatsApp pro signatário ("achei isso, posso seguir?") |
| Tempo médio | 1 a 6 horas no cliente, dependendo do escopo |
| Onde dói | Anotação a lápis frequentemente ilegível. Foto do display do instrumento borrada. Técnico esquece de medir 1 ponto (das 5 a 10 medidas exigidas pela faixa) e descobre só ao voltar pro lab → 2ª visita. Sem sinal de celular = sem consulta ao signatário = decisão errada de NC. Cliente assina "termo de recebimento" rabiscado num papel que se perde |
| Vezes que o dado é copiado | 1 a 2 |
| Risco regulatório | **17025 cláusula 7.5 — Registros técnicos:** todos os dados brutos devem ser registráveis e legíveis. Caderno ilegível = NC. **Risco também de cláusula 7.10 (NC)** se técnico decide na hora "desencanar" de uma medida fora |

### Etapa 5.6 — Execução em laboratório (cliente deixou o instrumento)

| Item | Detalhe |
|---|---|
| Quem faz | Técnico de bancada |
| Onde acontece | Laboratório |
| Ferramenta hoje | Cali ou Metroex (se acreditado) OU planilha + Word (se não). Padrões organizados em armário com etiqueta de identificação |
| Tempo médio | 1 a 8 horas por instrumento |
| Onde dói | Cali/Metroex desktop só rodam em um PC específico — se aquela máquina está em manutenção, calibração para. Backup do banco do Cali frequentemente esquecido — perda de dados ao formatar máquina. Versão do Cali desatualizada → erro de cálculo de incerteza descoberto só na auditoria Cgcre |
| Vezes que o dado é copiado | 2 a 3 (planilha de OS → Cali → certificado → de volta pra planilha) |
| Risco regulatório | **17025 cláusula 7.11 — Software validado:** versão do software DEVE estar gravada no certificado (INV-004c). Empresa que atualiza Cali sem revalidar tem NC |

### Etapa 5.7 — Volta pro laboratório / fechamento da OS

| Item | Detalhe |
|---|---|
| Quem faz | Técnico + atendente |
| Onde acontece | Lab, fim do dia |
| Ferramenta hoje | Técnico entrega papel/caderno → atendente digita dados na planilha → marca OS como "pronta pra emitir certificado" → avisa signatário |
| Tempo médio | 15 a 45 min por OS |
| Onde dói | Atendente digita errado o que técnico anotou (ilegibilidade + interpretação). Técnico "esquece" de entregar OS de hoje porque saiu correndo pra próxima visita → OS aparece 3 dias depois → cliente já cobrou |
| Vezes que o dado é copiado | 2 |
| Risco regulatório | Médio — atraso pode quebrar prazo contratual (SLA) |

### Etapa 5.8 — Atualização do cliente sobre status

| Item | Detalhe |
|---|---|
| Quem faz | Atendente |
| Onde acontece | WhatsApp / e-mail / telefone |
| Ferramenta hoje | Mensagem manual quando o cliente pergunta ("oi, e a calibração da nossa balança? já tá pronta?") |
| Tempo médio | 5 a 10 min por consulta |
| Onde dói | **Atendente recebe 10-30 perguntas/dia** sobre status, todas respondíveis se tivesse portal cliente. Tempo perdido enorme. Cliente fica com sensação de "não dão satisfação" |
| Vezes que o dado é copiado | 0 |
| Risco regulatório | Baixo |

### Etapa 5.9 — Logística de devolução do instrumento

| Item | Detalhe |
|---|---|
| Quem faz | Atendente + motoboy/transportadora/Correios OU cliente vem buscar |
| Onde acontece | Lab → cliente |
| Ferramenta hoje | Etiqueta impressa + nota de remessa em Word + WhatsApp pra motoboy |
| Tempo médio | 30 a 60 min por instrumento |
| Onde dói | Instrumento entregue ao cliente errado (duas balanças similares, etiqueta caiu). Motoboy não confirma entrega → ninguém sabe se chegou. Instrumento extraviado em transportadora = prejuízo + cliente furioso |
| Vezes que o dado é copiado | 2 |
| Risco regulatório | **17025 cláusula 7.4 — Manuseio de itens:** rastreabilidade do item desde recebimento até devolução exigida. Sem sistema = sem prova → NC se cliente reclamar |

### Etapa 5.10 — Pós-venda / pesquisa de satisfação

| Item | Detalhe |
|---|---|
| Quem faz | Atendente (quando faz) |
| Onde acontece | WhatsApp ou e-mail, semanas depois |
| Ferramenta hoje | Mensagem manual genérica |
| Tempo médio | 5 min por cliente (quando faz) |
| Onde dói | **Não é feito sistematicamente.** Empresa não tem NPS, não tem CSAT, não sabe quem está satisfeito ou insatisfeito até receber reclamação ou perder o cliente |
| Vezes que o dado é copiado | 0 |
| Risco regulatório | **17025 cláusula 8.6 — Melhoria:** feedback de cliente é entrada obrigatória pro sistema de gestão. Sem registro estruturado = lacuna em auditoria |

---

## 6. Detalhamento do Ciclo Metrológico (regulado ISO 17025)

> **Da entrada controlada do instrumento até o certificado assinado e arquivado. O ciclo mais crítico do ponto de vista regulatório — onde uma falha pode tirar a acreditação.**

### Etapa 6.1 — Recebimento e entrada controlada

| Item | Detalhe |
|---|---|
| Quem faz | Atendente + técnico de bancada |
| Onde acontece | Recepção do laboratório |
| Ferramenta hoje | Etiqueta numerada + planilha "Entradas 2026.xlsx" + ficha de recepção em papel |
| Tempo médio | 15 a 30 min por instrumento |
| Onde dói | Etiqueta cai. Ficha de papel se perde. Número de série do instrumento digitado errado → confusão com outro instrumento similar. Cliente nega que entregou ("a minha balança era a outra") |
| Vezes que o dado é copiado | 3 (ficha papel → planilha → Cali) |
| Risco regulatório | **17025 cláusula 7.4 + 7.8:** identificação inequívoca do item é obrigatória durante todo o ciclo. Perder rastreabilidade = certificado nulo |

### Etapa 6.2 — Inspeção inicial / verificação preliminar

| Item | Detalhe |
|---|---|
| Quem faz | Técnico de bancada |
| Onde acontece | Bancada de calibração |
| Ferramenta hoje | Caderno técnico + foto + planilha de "estado inicial" |
| Tempo médio | 20 a 60 min |
| Onde dói | Anotação subjetiva ("estado regular", "danos pequenos") sem padrão → cliente reclama depois ("vocês danificaram"). Foto de baixa qualidade |
| Vezes que o dado é copiado | 1 a 2 |
| Risco regulatório | Médio — registro de estado inicial protege lab contra acusação de dano causado |

### Etapa 6.3 — Verificação de validade do padrão a ser usado

| Item | Detalhe |
|---|---|
| Quem faz | Técnico |
| Onde acontece | Armário de padrões |
| Ferramenta hoje | **Olhar a etiqueta colada no padrão** + planilha "Padrões — validade.xlsx" + pasta no Drive com certificados-pai dos padrões |
| Tempo médio | 5 a 10 min |
| Onde dói | **Esquecimento de verificar a validade é falha comum** [a confirmar frequência]. Padrão com calibração vencida usado em calibração = certificado nulo + risco de perder acreditação. Planilha "Padrões — validade.xlsx" desatualizada → técnico confia na planilha errada |
| Vezes que o dado é copiado | 0 |
| Risco regulatório | **CRÍTICO — INV-011 + 17025 cláusula 6.5.** Materializa o risco R-018 (NIT-DICLA-030 rev. 15) |

### Etapa 6.4 — Execução da calibração (medições contra padrão)

| Item | Detalhe |
|---|---|
| Quem faz | Técnico de bancada / metrologista |
| Onde acontece | Bancada |
| Ferramenta hoje | Cali / Metroex (entrada manual das leituras) OU planilha + cálculo no Excel |
| Tempo médio | 30 min a 4 horas (depende da grandeza e faixa) |
| Onde dói | Digitação manual de 10 a 50 leituras → erro de digitação. Cali não tem captura automática do instrumento (geralmente) → técnico lê display, anota, digita. Interrupção (telefone toca, cliente chega) → técnico perde linha, repete tudo. Ambiente sem controle de T/UR registrado → NC em auditoria |
| Vezes que o dado é copiado | 2 a 3 |
| Risco regulatório | **17025 cláusula 7.5:** registros técnicos completos exigidos, incluindo condições ambientais |

### Etapa 6.5 — Cálculo de incerteza

| Item | Detalhe |
|---|---|
| Quem faz | Cali / Metroex (automático) OU planilha de incerteza específica por grandeza |
| Onde acontece | Software |
| Ferramenta hoje | Cali / Metroex / planilha Excel com macros |
| Tempo médio | 5 a 30 min (automático no Cali; manual na planilha é o problema) |
| Onde dói | Planilha de incerteza personalizada por técnico/empresa = cada um faz de um jeito → resultados divergentes. Macros Excel quebram com nova versão do Office. Cálculo errado descoberto só em auditoria de cliente farma (cliente reprova lote inteiro por causa do erro do lab) |
| Vezes que o dado é copiado | 0 a 1 |
| Risco regulatório | **17025 cláusula 7.6 + NIT-DICLA-021:** cálculo de incerteza segundo EA-4/02 obrigatório. **INV-004b:** alteração na rotina exige revalidação registrada |

### Etapa 6.6 — Análise crítica do resultado

| Item | Detalhe |
|---|---|
| Quem faz | Signatário técnico ou metrologista responsável |
| Onde acontece | Antes de assinar o certificado |
| Ferramenta hoje | Olhar resultado no Cali ou Word + comparar com histórico do instrumento (quando tem) |
| Tempo médio | 10 a 30 min |
| Onde dói | Sem histórico estruturado, signatário não percebe deriva anormal. Análise feita "no olho" sem critério documentado. Pressa pra emitir → análise superficial → erro passa |
| Vezes que o dado é copiado | 0 |
| Risco regulatório | **17025 cláusula 7.7 — Garantia da validade:** análise sistemática obrigatória |

### Etapa 6.7 — Decisão sobre regra de decisão / declaração de conformidade

| Item | Detalhe |
|---|---|
| Quem faz | Signatário técnico |
| Onde acontece | Antes da emissão |
| Ferramenta hoje | Documento de procedimento interno (Word) + cabeça do signatário |
| Tempo médio | 5 a 15 min |
| Onde dói | Regra de decisão aplicada inconsistentemente entre signatários. Cliente que pediu "conformidade simples" recebe "conformidade com risco compartilhado" → confusão jurídica. ILAC G8 não aplicado |
| Vezes que o dado é copiado | 0 |
| Risco regulatório | **17025 cláusula 7.8.6 + ILAC G8:** regra de decisão obrigatória quando declaração de conformidade |

### Etapa 6.8 — Emissão do certificado (PDF)

| Item | Detalhe |
|---|---|
| Quem faz | Técnico de bancada ou signatário |
| Onde acontece | Cali / Metroex / Word |
| Ferramenta hoje | Template do Cali ou template Word "Certificado padrão.docx" |
| Tempo médio | 10 a 30 min |
| Onde dói | Template Word frequentemente desalinhado com requisitos do NIT-DICLA-021 (faltam campos: rastreabilidade explícita, incerteza expandida com fator k=2, condições ambientais, versão do software). PDF não tem assinatura digital ICP-Brasil → cliente farma rejeita |
| Vezes que o dado é copiado | 1 a 2 |
| Risco regulatório | **17025 cláusulas 7.8 + 7.8.6 + NIT-DICLA-021 + INV-002 + INV-004c:** todos os campos obrigatórios devem estar presentes. **R-018 é o maior risco do produto** |

### Etapa 6.9 — Assinatura do certificado

| Item | Detalhe |
|---|---|
| Quem faz | Signatário técnico autorizado |
| Onde acontece | Signatário abre PDF, imprime, assina, escaneia OU assina digitalmente com certificado e-CPF |
| Ferramenta hoje | Adobe Reader + scanner OU ferramenta de assinatura digital (Adobe Sign, GovBR) |
| Tempo médio | 5 a 15 min por certificado |
| Onde dói | **Signatário é gargalo.** Empilha 20 certificados pra assinar e demora 2-3 dias. Assina sem reler porque é volume grande. Escopo de assinatura não controlado pelo sistema → signatário assina fora do escopo dele = NC grave |
| Vezes que o dado é copiado | 0 |
| Risco regulatório | **17025 cláusula 6.2 + INV-003:** signatário só assina dentro do escopo autorizado. **R-015** materializa quando ele falta |

### Etapa 6.10 — Arquivamento do certificado

| Item | Detalhe |
|---|---|
| Quem faz | Atendente ou financeiro |
| Onde acontece | Drive da Google, OneDrive ou pasta de rede |
| Ferramenta hoje | Nomeação manual: "Certificado-12345-ClienteX-Balanca-2026.pdf" salvo em pasta por cliente |
| Tempo médio | 5 min por certificado |
| Onde dói | Convenção de nome inconsistente entre atendentes → busca difícil. Pasta de rede sem backup → perda de histórico. Drive público compartilhado com cliente errado por engano → quebra de cláusula 4.2 (confidencialidade). Sem WORM → certificado pode ser editado depois (fraude possível) |
| Vezes que o dado é copiado | 1 |
| Risco regulatório | **17025 cláusula 8.4 + INV-001 + INV-013 + INV-010:** retenção mínima 5 anos, WORM, log de acesso. **Compartilhamento errado = quebra de cláusula 4.2** |

### Etapa 6.11 — Envio do certificado ao cliente

| Item | Detalhe |
|---|---|
| Quem faz | Atendente |
| Onde acontece | E-mail (anexo PDF) ou WhatsApp |
| Ferramenta hoje | Gmail / Outlook / WhatsApp Business |
| Tempo médio | 5 a 10 min |
| Onde dói | Certificado mandado pro contato errado do cliente (e-mail desatualizado). Cliente perde o e-mail e pede de novo 3 meses depois ("manda lá, ó!"). Sem log de envio → "vocês nunca me mandaram!" |
| Vezes que o dado é copiado | 1 |
| Risco regulatório | LGPD: dado de cliente vazado se enviado pro endereço errado |

### Etapa 6.12 — Gestão da validade da calibração (lembrar cliente da próxima)

| Item | Detalhe |
|---|---|
| Quem faz | Vendedor ou atendente (quando lembra) |
| Onde acontece | Planilha "Validades.xlsx" + Google Calendar |
| Ferramenta hoje | Planilha + lembretes manuais |
| Tempo médio | 30 min/mês pra revisar a planilha |
| Onde dói | **NÃO é sistemático.** Empresa perde **30-50% das recalibrações** por esquecimento [a confirmar via entrevista — é uma das maiores oportunidades de receita perdida do setor]. Cliente recebe lembrete da concorrência antes |
| Vezes que o dado é copiado | 0 a 1 |
| Risco regulatório | Risco do CLIENTE (instrumento descalibrado em uso) mais que do lab. Mas oportunidade comercial enorme |

---

## 7. Detalhamento do Ciclo Financeiro

> **Do "OS fechada" ao "valor entrou na conta + conciliado".**

### Etapa 7.1 — Emissão da NFS-e

| Item | Detalhe |
|---|---|
| Quem faz | Financeiro |
| Onde acontece | Bling, Conta Azul, Omie, ou portal da prefeitura (quando empresa não usa ERP fiscal) |
| Ferramenta hoje | Bling/Omie/Conta Azul (~70% das empresas pequenas) OU portal municipal direto (~30%) |
| Tempo médio | 10 a 20 min por NFS-e |
| Onde dói | Dados do cliente DIGITADOS DE NOVO no Bling/Omie (já estão na planilha + no Cali — terceira digitação). Descrição do serviço genérica ("calibração") sem detalhar instrumento, faixa, certificado → cliente questiona. Código de serviço municipal errado → ISS errado → retrabalho fiscal. **Cutover NFS-e Padrão Nacional 01/09/2026** (R-016) muda layout — empresas que dependem só do portal municipal vão sofrer transição |
| Vezes que o dado é copiado | 3 a 5 (cliente + descrição + valor + data + número certificado) |
| Risco regulatório | **LC 214/2025 + Resolução CGSN 189/2026:** ME/EPP migra obrigatoriamente em 01/09/2026. **R-016 score 20** |

### Etapa 7.2 — Geração de boleto / cobrança PIX

| Item | Detalhe |
|---|---|
| Quem faz | Financeiro |
| Onde acontece | Internet banking + Bling/Conta Azul |
| Ferramenta hoje | Conta bancária PJ (Itaú, BB, Bradesco, Santander, Sicredi, etc.) + Bling/Omie pra controle |
| Tempo médio | 5 a 10 min por boleto |
| Onde dói | Geração manual de boleto trava se sistema bancário cai. PIX manual sem identificação no extrato → conciliação difícil depois. Boleto enviado pro contato errado |
| Vezes que o dado é copiado | 2 a 3 |
| Risco regulatório | **PIX Recuperação de fundos obrigatória desde 02/02/2026** (BCB 493/2025) — lab pode ter PIX recebido revertido sem aviso |

### Etapa 7.3 — Envio de boleto/cobrança ao cliente

| Item | Detalhe |
|---|---|
| Quem faz | Financeiro |
| Onde acontece | E-mail + WhatsApp |
| Ferramenta hoje | Gmail/Outlook + WhatsApp |
| Tempo médio | 5 min por cliente |
| Onde dói | Cliente alega "não recebi" e financeiro reenvia. Sem log estruturado, financeiro perde tempo provando que enviou. Cliente "esquece" boleto |
| Vezes que o dado é copiado | 1 |

### Etapa 7.4 — Recebimento e conciliação bancária

| Item | Detalhe |
|---|---|
| Quem faz | Financeiro |
| Onde acontece | Internet banking + Bling/Omie |
| Ferramenta hoje | Download de extrato OFX/CNAB + importação no Bling/Omie + conciliação manual quando não bate |
| Tempo médio | 30 min a 3 horas por semana |
| Onde dói | PIX recebido com identificador errado ("João Silva" em vez de "Empresa ABC") → não bate com NFS-e → conciliação manual. Boleto pago com valor parcial → financeiro precisa cobrar diferença. Boleto pago em duplicidade → financeiro precisa devolver. **Sem integração bancária = trabalho manual enorme** |
| Vezes que o dado é copiado | 2 |
| Risco regulatório | **Bacen Res. 4.658/2018 + Open Finance:** integração com banco exige requisitos de segurança quando feita direto |

### Etapa 7.5 — Gestão de inadimplência

| Item | Detalhe |
|---|---|
| Quem faz | Financeiro + dono |
| Onde acontece | Planilha "Inadimplentes.xlsx" + WhatsApp/telefone |
| Ferramenta hoje | Planilha manual atualizada semanalmente + cobrança manual |
| Tempo médio | 2 a 4 horas/semana só pra acompanhar |
| Onde dói | **Cobrança vira problema pessoal do dono.** Cliente inadimplente é também cliente operacional ativo (já tá com nova OS aberta!) → conflito interno: cobrar e perder cliente OU atender e nunca receber. Régua de cobrança não automatizada = cliente "esquece" de pagar |
| Vezes que o dado é copiado | 1 |

### Etapa 7.6 — Bloqueio de cliente inadimplente

| Item | Detalhe |
|---|---|
| Quem faz | Dono (decisão difícil) |
| Onde acontece | Reunião dono + financeiro + atendente |
| Ferramenta hoje | "Aviso" pelo WhatsApp do grupo interno "não atender cliente X até pagar" |
| Tempo médio | Variável — discussão prolongada |
| Onde dói | Atendente não-avisado abre OS pra cliente bloqueado. Cliente reclama publicamente do bloqueio. Decisão emocional do dono ("é cliente antigo, atende mesmo") gera mais inadimplência |
| Vezes que o dado é copiado | 0 |

### Etapa 7.7 — Fechamento contábil mensal

| Item | Detalhe |
|---|---|
| Quem faz | Financeiro + contador externo |
| Onde acontece | Bling/Omie → envio de relatório pro contador via e-mail |
| Ferramenta hoje | Bling/Omie/Conta Azul + Excel + e-mail pro contador |
| Tempo médio | 4 a 12 horas/mês + tempo do contador |
| Onde dói | Conciliação operacional ↔ financeiro inexistente (não dá pra cruzar OS executada ↔ NFS-e emitida ↔ pagamento recebido sem trabalho manual). Contador devolve perguntas que financeiro não sabe responder → vai/volta de e-mail |
| Vezes que o dado é copiado | 2 a 4 |
| Risco regulatório | **Receita Federal:** SPED, retenção fiscal 5 anos. **CTN art. 173/174** |

### Etapa 7.8 — DRE / visão do dono

| Item | Detalhe |
|---|---|
| Quem faz | Contador (envia relatório) + dono lê |
| Onde acontece | E-mail / reunião mensal |
| Ferramenta hoje | PDF do contador + planilha "Resumo do mês.xlsx" |
| Tempo médio | 1 hora pro dono entender + reunião com contador |
| Onde dói | Dono vê DRE com 30-45 dias de atraso → decide com base em info defasada. Sem visão de margem por serviço/cliente/grandeza → não sabe o que é rentável |
| Vezes que o dado é copiado | 0 |

---

## 8. Visão integrada da dor — custo do status quo (estimativa)

> **Todas as estimativas abaixo são preliminares e devem ser quantificadas nas entrevistas Onda 1 + 2.** Marcadas como `[a confirmar via entrevista]`.

Para a empresa-modelo (10-20 funcionários, ~150 certificados/mês + ~50 OS de manutenção/mês):

| Categoria de perda | Horas/mês perdidas (estimativa) | Custo aproximado (a R$ 50/h média) |
|---|---|---|
| Digitação duplicada de cadastro de cliente em 4-6 sistemas | 20 a 35 h | R$ 1.000 a R$ 1.750 |
| Atendimento manual de perguntas "qual o status?" via WhatsApp | 25 a 40 h | R$ 1.250 a R$ 2.000 |
| Retrabalho por erro de digitação ou versão errada (orçamento, OS, certificado) | 15 a 25 h | R$ 750 a R$ 1.250 |
| Roteirização ruim de técnicos (combustível + tempo) | 10 a 20 h + R$ 800 a R$ 1.500 em combustível | R$ 1.300 a R$ 2.500 |
| 2ª visita por padrão errado, padrão vencido ou erro de execução | 8 a 20 h | R$ 400 a R$ 1.000 |
| Conciliação financeira manual (extrato bancário vs NFS-e vs OS) | 15 a 25 h | R$ 750 a R$ 1.250 |
| Cobrança manual de inadimplência | 8 a 16 h | R$ 400 a R$ 800 |
| Recalibração perdida por esquecimento de lembrar o cliente | (oportunidade perdida) | **R$ 3.000 a R$ 8.000/mês em receita não realizada** |
| Tempo do dono "apagando incêndio" diariamente | 40 a 80 h | R$ 2.000 a R$ 4.000 (custo de oportunidade) |
| **TOTAL conservador** | **~140 h/mês de retrabalho operacional** | **~R$ 10.000 a R$ 22.500/mês** |

**Mais difícil de quantificar mas igualmente real:**

- **Perda de clientes** por demora de resposta, certificado errado ou cobrança constrangedora. Estimativa: 1 a 3 clientes/trimestre [a confirmar].
- **Risco regulatório acumulado** — uma NC grave em auditoria Cgcre custa de R$ 5 mil (reauditoria + custo do consultor) até **perda da acreditação** (que destrói o negócio).
- **Burnout do dono** — empresa cresceu organicamente até o limite de operação manual; dono trabalha 60-70h/semana, ansiedade, qualidade de vida zero.
- **Bloqueio de crescimento** — empresa não consegue dobrar de tamanho porque a operação manual já está no limite. Contratar mais gente piora porque não tem fluxo padronizado pra integrar.

---

## 9. Variações por perfil (A / B / C / D)

### 9.1 Perfil A (acreditado RBC)

**Diferenças vs caso-base:**

- Ciclo metrológico é **MAIS rigoroso** — todos os invariantes 17025 ativos. Mais campos obrigatórios no certificado, mais documentação de NC, supervisão Cgcre a cada 12-18 meses.
- Signatário ainda mais crítico — escopo de assinatura é validado em auditoria.
- Cliente final (farma, automotivo, aeroespacial) exige rastreabilidade completa → empresa não tem espaço pra erro.
- **Dor adicional:** preparação pra auditoria Cgcre custa 80-200 horas a cada ciclo, com signatário e dono parando o trabalho normal pra revisar pastas, certificados, padrões, planilhas, registros de treinamento.
- **Cali ou MET/CAL** são quase obrigatórios — empresa em perfil A puro raramente sobrevive só com Word + Excel.

### 9.2 Perfil B (rastreável ao RBC, sem acreditação)

**Diferenças vs caso-base (que já é B-rigoroso):**

- Menos rigor formal — alguns invariantes desativados pelo dono.
- Certificado leva declaração "rastreável ao RBC sem acreditação Cgcre".
- Cliente final aceita pra usos não-críticos (manutenção interna, controle de processo não-regulado).
- **Dor adicional:** confusão de cliente final ("seu certificado vale ou não vale?") → vendedor passa 15 min explicando em cada venda.

### 9.3 Perfil C (preparando-se pra acreditação)

**Diferenças vs caso-base:**

- Operação como B + esforço de "endurecer" processos para passar em auditoria de admissão Cgcre.
- Consultor externo de qualidade contratado (R$ 5-15 mil/mês durante 12-24 meses).
- **Dor adicional:** ter que retroativamente padronizar registros que foram feitos sem estrutura → projeto longo e doloroso. Muitas empresas DESISTEM a meio caminho.
- **Maior oportunidade do Aferê:** software que cresce com a empresa = caminho mais curto até a acreditação.

### 9.4 Perfil D (calibração comercial básica, sem 17025)

**Diferenças vs caso-base:**

- Operação MUITO mais simples. Ciclo metrológico = "técnico mede, anota e dá um papel com a leitura". Sem incerteza formal, sem rastreabilidade declarada, sem signatário formal.
- **Cali ou Metroex frequentemente NÃO usados** — Word + Excel bastam.
- Cliente final é varejo (açougue, padaria, supermercado), feira, oficina mecânica, lab interno sem regulação.
- **Dor adicional:** confusão regulatória — empresa D pode estar **violando R-040** (cliente final acha que tem verificação INMETRO válida porque "calibrou", quando na verdade falta a verificação periódica obrigatória do IPEM).
- **Mais fácil de capturar com Aferê** mas ticket menor.

---

## 10. Variações por tipo de instrumento

### 10.1 Balança comercial (regulada IPEM/INMETRO)

- **Diferença-chave:** verificação metrológica legal obrigatória anual pelo IPEM/RBMLQ-I (Portaria 157/2022). Calibração feita pelo lab NÃO substitui essa verificação.
- **Ciclo extra:** lab calibrador frequentemente é também o "intermediário" que avisa cliente sobre verificação IPEM, prepara instrumento, acompanha técnico do IPEM.
- **Dor adicional:** confusão cliente final entre "selo INMETRO" (verificação) e "certificado de calibração" (rastreabilidade) — R-040 score 12.
- **Logística simples** (instrumento portátil, vai ao lab).

### 10.2 Balança industrial / dosadora

- **Calibração frequentemente em campo** (instrumento fixo na linha de produção).
- **Padrões pesados** — massas-padrão M1/F1 de 5kg a 50kg, levados em maleta.
- **Dor adicional:** parar linha de produção do cliente é caro → janela curta (madrugada, fim de semana) → técnico trabalha em horário não comercial.
- **Cliente costuma ser indústria de médio/grande porte** → exigência regulatória maior.

### 10.3 Balança analítica / semi-analítica (lab químico, farma)

- **Calibração em lab** preferencial (transporte cuidadoso).
- **Faixa pequena** (mg-g), exatidão alta, incerteza expandida exigida com fator k=2.
- **Cliente farma exige:** rastreabilidade + IQ/OQ/PQ + validação de software + Anvisa RDC 658/2022.
- **Dor adicional:** documentação 3x mais densa por cliente → atendente passa horas só preparando "pacote de documentos pra auditoria do cliente".

### 10.4 Balança rodoviária

- **Calibração 100% em campo** (instrumento não-móvel).
- **Cargas-padrão de 100kg a 30 toneladas** — caminhão com bloco de teste, custa caro o deslocamento.
- **Implicação tributária** (peso = ICMS, pedágio, royalty mineração) → erro vira disputa fiscal.
- **Dor adicional:** logística complexa, técnico vai com caminhão de carga-padrão por 200-500 km.

### 10.5 Manômetro / termômetro / paquímetro / micrômetro

- **Volume alto** (lab faz dezenas por dia).
- **Calibração em lab** (instrumento portátil).
- **Dor adicional:** instrumentos parecidos visualmente → risco de troca/confusão (etiqueta cai = caos).

---

## 11. Pontos de inflexão — eventos que fazem o dono dizer "preciso resolver isso JÁ"

> Os "triggers de dor crítica" — eventos que normalmente disparam a busca por uma solução estruturada (= momento de venda mais quente pro Aferê).

1. **Não conformidade em auditoria Cgcre** — supervisão chega, audita pastas, encontra rastreabilidade quebrada, padrão usado com calibração vencida, certificado sem incerteza. Custo: 80-200 h pra resolver + risco de perder acreditação (= empresa quebra).
2. **Cliente farma rejeita certificado** — lote inteiro do cliente reprovado porque certificado de calibração tinha erro de cálculo de incerteza. Cliente cobra prejuízo do lab (R$ 50k a R$ 500k) e cancela contrato.
3. **Multa IPEM** — balança comercial do cliente não foi verificada no prazo. Cliente recebe multa, descobre que lab "deveria ter avisado" (não há obrigação legal, mas há expectativa), processa lab no Procon ou na Justiça.
4. **Retrabalho de certificado em massa** — descoberto erro em rotina de cálculo de incerteza usada por 6 meses. Lab precisa reemitir 300-800 certificados, comunicar cada cliente, fazer NC formal, justificar à Cgcre.
5. **Técnico perdido na rua / acidente** — técnico não atende telefone, atendente não sabe onde está, cliente liga reclamando que técnico não chegou. Sem rastreio, sem comprovação de visita.
6. **Boleto duplicado / cliente cobrando errado** — financeiro reemite NFS-e por engano, cliente paga 2x, descobre, exige devolução, fica chateado.
7. **Signatário sai da empresa** — única pessoa autorizada pra escopo X de calibração pede demissão. Lab fica meses sem poder emitir certificado nesse escopo. Receita despenca.
8. **Concorrente ganhou cliente importante** — descoberto que cliente foi pra concorrente "porque eles têm portal pra eu baixar meus certificados". Lab perde 5-10% do faturamento.
9. **Dono adoeceu / esgotamento** — dono que trabalha 70h/semana entra em burnout, atendimento médico, afastamento. Empresa fica paralisada porque "só ele sabe como funciona".
10. **Visma compra um concorrente** (R-035) — Cali ou Metroex viram parte do Conta Azul/Sankhya. Cliente atual desses sistemas começa a receber pressão de upgrade integrado → janela rara de "quem está procurando alternativa agora".

---

## 12. Síntese: top 10 pontos de dor mais graves (input pra `dores-mapeadas.md`)

> Ordenados por (frequência × gravidade × custo da dor). Cada um deve virar um item em `dores-mapeadas.md` com link pra entrevista que confirma.

| # | Ponto de dor | Frequência | Gravidade | Onde no ciclo | Quem sente mais |
|---|---|---|---|---|---|
| **D-001** | **Cadastro de cliente digitado 4-6 vezes em sistemas que não conversam** | Diária | Alta (erro + tempo) | Comercial → Operacional → Metrológico → Financeiro | Atendente + financeiro |
| **D-002** | **Esquecimento de lembrar cliente da próxima calibração** (recalibração perdida) | Mensal recorrente | Altíssima (receita perdida 20-40%) | Pós-metrológico | Dono (receita) + vendedor |
| **D-003** | **Padrão usado com calibração vencida** (lab não percebe) | Esporádica mas catastrófica | Crítica (NC Cgcre, certificado nulo) | Metrológico — etapa 6.3 | Signatário + dono |
| **D-004** | **Signatário-gargalo** (pilha de certificados pra assinar; sai de férias e tudo para) | Semanal | Alta (atraso) → Crítica (quando ele falta de vez) | Metrológico — etapa 6.9 | Signatário + dono |
| **D-005** | **Status de OS perguntado o tempo todo pelo cliente** (sem portal) | Diária (10-30x/dia) | Média mas drenante | Operacional — etapa 5.8 | Atendente |
| **D-006** | **Roteirização de técnico no escuro** (planilha + WhatsApp) | Diária | Alta (combustível + tempo + 2ª visita) | Operacional — etapa 5.3 | Gerente + técnico + dono |
| **D-007** | **Certificado emitido sem campo obrigatório do NIT-DICLA-030** (rastreabilidade incompleta, incerteza ausente) | Variável | **CRÍTICA** (R-018 score 25, perde acreditação) | Metrológico — etapas 6.8-6.10 | Signatário + dono |
| **D-008** | **Conciliação financeira manual** (extrato banco vs NFS-e vs OS) | Semanal | Alta (horas) | Financeiro — etapa 7.4 | Financeiro |
| **D-009** | **Cobrança de inadimplência pessoal e constrangedora** (sem régua automatizada; cliente operacional ativo é também inadimplente) | Mensal | Alta (caixa + relacionamento) | Financeiro — etapa 7.5-7.6 | Dono + financeiro |
| **D-010** | **Dono opera no nível diário sem visão estratégica** (sem DRE em tempo real, sem margem por cliente/serviço, vive "apagando incêndio") | Diária | Altíssima (burnout, bloqueio de crescimento) | Transversal | Dono |

**Dores adjacentes que merecem entrar em `dores-mapeadas.md` em segunda leva:**

- D-011: Versão de orçamento errada enviada (Word "v3 FINAL FINAL2").
- D-012: Cliente recebe certificado errado por e-mail (vazamento de confidencialidade cláusula 4.2).
- D-013: Backup do banco do Cali/Metroex esquecido → perda de histórico ao formatar PC.
- D-014: Instrumento extraviado em transportadora sem rastreio (cláusula 7.4).
- D-015: Confusão cliente final entre "calibração" e "verificação INMETRO" (R-040).
- D-016: Documentação 17025 (registros de treinamento, autorização signatário) só lembrada em véspera de auditoria.
- D-017: Cutover NFS-e Padrão Nacional 01/09/2026 (R-016) — empresas que dependem do portal municipal vão sofrer.
- D-018: Tabela de preço desatualizada → vendedor erra margem.
- D-019: Foto/anotação de campo ilegível → atendente erra digitação.
- D-020: Sem NPS/satisfação estruturado → empresa só descobre que cliente está insatisfeito quando perde.

---

## 13. Ferramentas BR críticas mapeadas no status quo (a confirmar nas entrevistas)

| Ferramenta | Onde aparece | Frequência de uso no setor (estimada) |
|---|---|---|
| **WhatsApp Business** | Atendimento, agendamento, envio de certificado, cobrança, comunicação interna técnico ↔ lab | **~100%** das empresas BR de assistência/calibração |
| **Excel / Google Sheets** | Controle de OS, agenda de técnico, validade de padrão, inadimplência, prospects, cadastro de cliente | **~95%** — substituto universal de "sistema" |
| **Word / Google Docs** | Template de orçamento, relatório técnico, certificado em perfil B/C/D | **~80%** |
| **Bling** | NFS-e + financeiro de pequena empresa | **~30-40%** das pequenas |
| **Conta Azul** | NFS-e + financeiro + integração contador | **~25-35%** — concorre com Bling |
| **Omie** | NFS-e + financeiro + ERP mais robusto | **~10-20%** — empresa que cresceu |
| **Cali (Cali LAB ou Cali WEB)** | Cálculo de incerteza + certificado de calibração | **~50-70%** dos labs acreditados RBC |
| **Metroex (ForLogic)** | Idem Cali (concorrente) | **~15-30%** |
| **Drive da Google / OneDrive / Dropbox** | Arquivamento de certificados, fotos, orçamentos | **~90%** |
| **Pasta de rede local** | Empresas mais antigas/sem migração à nuvem | **~30-40%** |
| **Internet banking PJ** (Itaú, BB, Bradesco, Santander, Sicredi) | Boleto, PIX, extrato | **~100%** |
| **GovBR / e-CPF / e-CNPJ** | Assinatura digital de certificado, login portal prefeitura/INMETRO/Receita | **~70%** |
| **Portal da prefeitura (NFS-e municipal)** | Empresas que não usam Bling/Omie/Conta Azul | **~30%** — mais comum em interior |
| **Google Calendar** | Agenda individual de técnico (quando usado) | **~40-60%** |
| **Caderno / bloco de papel** | Campo, anotação de medição, recados | **~80%** ainda usado em paralelo ao digital |
| **Câmera do celular** | Foto de instrumento, display, lacre, defeito | **~100%** |

---

## 14. Próximos passos (saída deste documento)

1. **Validar tudo na Onda 1 de entrevistas** (3-5 empresas, foco em quantificar tempo perdido) — ver `entrevistas-onda-1.md` quando existir.
2. **Quantificar D-001 a D-010** com perguntas específicas nas entrevistas (ver §15).
3. **Alimentar `personas-detalhadas.md`** com os papéis identificados (atendente, técnico de campo, signatário, financeiro, dono) e seus pontos de fricção no dia a dia.
4. **Confirmar `concorrentes.md` §3** observando quais clientes usam Cali vs Metroex vs nenhum.
5. **Subsidiar priorização do MVP-1 em `faseamento-modulos.md`** — qual ciclo doer mais entra primeiro? Sinalização preliminar: Operacional + Metrológico + cadastro único de cliente (porque atravessa todos os ciclos).
6. **Alimentar `validacao-ativa.md`** — usar dores D-001, D-002, D-005, D-010 como hipóteses pra teste de WTP (Willingness To Pay).

---

## 15. Perguntas-chave pra validar nas entrevistas Onda 1+2

> Cada pergunta tenta quantificar uma dor específica. Idealmente o entrevistador anota o número em minutos/reais/percentual.

1. **"Quantas vezes por mês acontece de um cliente reclamar de demora na resposta ou pedir status de uma OS?"** (mede D-005)
2. **"Em quantos sistemas diferentes o cadastro do mesmo cliente vive hoje? Quanto tempo leva pra cadastrar um cliente novo do zero?"** (mede D-001)
3. **"Quantas recalibrações vocês perdem por trimestre porque o cliente esqueceu de pedir a próxima ou o concorrente chegou antes?"** (mede D-002 — a receita escondida)
4. **"Quando o signatário tira férias ou fica doente, quantos dias a emissão de certificados para? Qual o impacto financeiro disso?"** (mede D-004)
5. **"Quanto tempo o dono passa por dia 'apagando incêndio' — coisas que se tivesse fluxo padronizado não chegariam até ele?"** (mede D-010)

**Bônus (se houver tempo):**

6. "Qual foi a última NC que vocês tiveram em auditoria Cgcre? O que custou pra resolver?"
7. "Quanto tempo demora pra fechar o mês contábil hoje (entre OS executada → NFS-e emitida → boleto recebido → conciliação)?"
8. "Quantas vezes um padrão foi usado com calibração vencida nos últimos 12 meses?"

---

## 16. Como este documento foi escrito

- Agente leu `dominio-de-negocio.md`, `concorrentes.md`, `riscos.md`, `normas-e-regulacao.md` e cruzou observações.
- Mapa de ferramentas BR ancorado em pesquisa de mercado já consolidada no `concorrentes.md` (Cali, Metroex, FP2, Bling, Omie, Conta Azul).
- Estimativas quantitativas marcadas com `[a confirmar via entrevista]` — devem virar números reais na Onda 1.
- Princípio editorial: descrever DOR, não solução. Onde a tentação foi grande de escrever "o Aferê resolveria fazendo X", o texto foi reescrito pra ficar no problema.
- Próxima atualização: após Onda 1 de entrevistas (Roldão + 3-5 outras empresas), refinar números e adicionar quotes diretos.
