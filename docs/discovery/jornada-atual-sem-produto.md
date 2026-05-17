# Discovery — Jornada atual (status quo, SEM o produto Aferê)

> **Artefato Rodada 0 / Batch 2** — mapeamento do "como uma empresa brasileira de assistência técnica + laboratório de calibração roda HOJE", sem nenhum produto integrado.
>
> **Status:** segunda passagem do agente (17/05/2026), incorporando 13 correções aceitas pelo dono após auditoria cruzada (Aud-6 recalibração de empresa-modelo + custo do status quo; Aud-7 violações regulatórias silenciosas; Aud-8 padronização de nomenclatura e costura nominal de personas). Marcações `[a confirmar via entrevista]` apontam estimativas que precisam ser quantificadas nas Ondas 1 e 2 de entrevistas com clientes-alvo.
>
> **Objetivo:** servir de base para (a) demonstrar a dor real nas entrevistas, (b) quantificar custo do status quo (tempo perdido, retrabalho, erro humano, multa regulatória, cliente perdido), (c) priorizar onde o MVP-1 do Aferê entra primeiro com maior ROI percebido.
>
> **Princípio editorial:** este documento descreve **dor**, NÃO solução. Quando aparecer a tentação de escrever "o Aferê resolveria isso fazendo X", parar — esse conteúdo vai em `faseamento-modulos.md` e `painel-do-dono.md`.
>
> **Convenção terminológica (Aud-8):** "tenant" = empresa que usa o Aferê (lab calibrador / assistência técnica). "Cliente final" = quem contrata o tenant (indústria, hospital, varejo, lab clínico). "Cliente" sozinho NÃO é usado neste documento — sempre qualificado.

---

## 1. Resumo executivo

**Como é hoje.** A empresa-modelo brasileira de assistência técnica + calibração roda em cima de uma colcha de retalhos digital: WhatsApp, Excel, Word, Cali/Metroex, Bling/Conta Azul, Drive da Google, caderno do técnico. **Nada disso conversa entre si.** A "integração" é copia-cola feito por humano — o mesmo dado de cliente final é digitado em 4 a 6 ferramentas ao longo de um único ciclo.

**Os números-chave da dor (estimativas a confirmar Onda 1+2):**

- **80 a 150 horas/mês perdidas** com retrabalho administrativo evitável (empresa-modelo de 5-10 pessoas).
- **1 a 3 clientes finais perdidos por trimestre** por demora na resposta ou erro de certificado.
- **2 a 4 horas/dia do dono "apagando incêndio"** — técnico perdido, certificado errado, boleto vencido, cliente final reclamando.
- **30-50% das recalibrações são perdidas** por esquecimento de lembrar o cliente final (fonte: estimativa setorial, validar Onda 1+2).
- **Word + Excel pra certificado/cálculo de incerteza em perfil B sem validação documentada = NC permanente da cláusula 7.11.** Não é "macro quebra com Office novo" — é não conformidade ativa enquanto o lab usa.

**O que isso custa por mês.** Soma de retrabalho + 2ª visita + conciliação manual + custo de oportunidade do dono + receita perdida por esquecimento + risco regulatório provisionado: **R$ 35.000 a R$ 50.000/mês** (detalhamento em §8).

---

## 2. Empresa-modelo de referência (perfil B com algumas regras 17025 ativas)

A empresa-modelo é a **fatia modal real do mercado BR (~50-60% dos labs):** **5-10 funcionários, perfil B com algumas regras 17025 ativadas, atende balança comercial + industrial + manômetro.** O caso anterior (10-20 funcionários, perfil B-rigoroso ou A enxuto) vira variação em §9.1.

### 2.1 Cartão de identidade da empresa-modelo

| Atributo | Valor de referência |
|---|---|
| Razão social | "Calibratec Soluções Metrológicas Ltda" (nome fictício) |
| Localização | Interior de SP, RS, PR, MG ou GO (cidade-polo industrial de 100 a 500 mil habitantes) |
| Tempo de mercado | 5 a 12 anos |
| Faturamento mensal estimado | **R$ 50 mil a R$ 150 mil** (corrigido — antes inflado em R$ 80-300k) |
| Regime tributário | Simples Nacional faixa média/alta ou Lucro Presumido (transição) |
| Funcionários | **5 a 10** |
| Acreditação | **Perfil B** (rastreável ao RBC sem selo) com algumas regras 17025 ativadas (registro de padrões, autorização de signatário, cadeia de rastreabilidade — outras configuráveis) |
| Tipos de instrumento que atende | **Balança comercial + balança industrial + manômetro** (mix dominante BR) |
| Mix de receita | ~55% calibração (lab + campo) / ~35% assistência técnica + peças / ~10% venda de instrumento |
| Tickets de calibração/mês | 60 a 180 certificados emitidos |
| OS de manutenção/mês | 25 a 80 chamados ativos |
| Carteira de clientes finais ativos | 100 a 250 PJ |
| Distância média até cliente final | 30 a 250 km |

### 2.2 Organograma operacional típico (5-10 pessoas)

```
1 Dono (Roldão) — acumula comercial + gestão + às vezes RT
    |
    +-- 1 RT/Qualidade — Sandra OU o próprio dono (acumulado)
    |
    +-- 1-2 Técnicos de campo — Bruno (vai pra rua de van/carro)
    |
    +-- 1 Atendente — Letícia (WhatsApp + telefone + cadastro)
    |
    +-- 1 Financeiro/auxiliar — Cláudia auxiliar (NFS-e, boleto, conciliação)
    |
    +-- 1 Metrologista signatário — Marcos (às vezes é o próprio Roldão se engenheiro)
```

**Observações estruturais críticas para o discovery:**

- **Acúmulo de papel é a regra, não a exceção** em empresa-modelo de 5-10 pessoas. O dono frequentemente é também RT, comercial e signatário. Atendente Letícia também cadastra cliente final, abre OS, fotografa instrumento.
- **Signatário (persona: Marcos OU Roldão) é gargalo crônico.** Geralmente uma pessoa só, escopo de assinatura limitado pelo NIT-DICLA-021. Quando falta, emissão PARA (R-015).
- **Atendente (persona: Letícia) é a peça que mais sofre com a fragmentação.** Não é só "tirar pedido": cadastra cliente final em planilha, cria OS em outra planilha, copia dados pra orçamento em Word, fotografa instrumento no WhatsApp, encaminha pro técnico, atualiza status no grupo interno, lembra o dono de cobrar.
- **Financeiro (persona: Cláudia auxiliar) NÃO é o mesmo que comercial.** Em empresa pequena costuma ser a mesma pessoa, criando conflito de prioridade (cobrar cliente final atrasado vs fechar venda nova).
- **Dono (persona: Roldão) opera no nível operacional.** Vive resolvendo problema do dia em vez de planejar — perfil que motivou o `painel-do-dono.md`.

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

1. Entre Comercial e Operacional: orçamento aprovado precisa virar OS — copia-cola de dados do cliente final, do instrumento e do escopo do serviço.
2. Entre Operacional e Metrológico: OS de calibração precisa virar entrada controlada no Cali/Metroex — copia-cola de dados do instrumento, faixa, ponto, padrão.
3. Entre Metrológico e Operacional: certificado emitido precisa voltar pra OS pra fechar e encaminhar pro financeiro — copia-cola de número do certificado, data, signatário.
4. Entre Operacional e Financeiro: OS fechada precisa virar NFS-e no Bling/Conta Azul — copia-cola de dados do cliente final, descrição do serviço, valor.
5. Entre Financeiro e Comercial: cliente final inadimplente precisa ser bloqueado pra novos serviços — comunicação por WhatsApp interno, planilha de inadimplência, nada automatizado.

**Cada copia-cola = 30 segundos a 5 minutos + risco de erro de digitação.** Multiplicando por 60-180 certificados/mês + 25-80 OS/mês, a conta de horas perdidas é o que justifica o produto.

---

## 4. Detalhamento do Ciclo Comercial

> **Da primeira conversa ao "pode iniciar o serviço".**

### Etapa 4.1 — Captação do prospect

| Item | Detalhe |
|---|---|
| Papel: vendedor (persona: Rogério OU o próprio dono Roldão) | |
| Onde acontece | WhatsApp Business (~70%), telefone fixo/celular (~20%), e-mail (~10%), feira/visita esporádica |
| Ferramenta hoje | WhatsApp Business + caderno do vendedor + planilha "prospects.xlsx" no Drive |
| Tempo médio | 5 a 15 min por contato inicial |
| Onde dói | Não existe funil estruturado — prospect "esquecido" na conversa do WhatsApp é receita perdida. Vendedor não tem visão de quantos contatos abertos tem na semana. Dono não sabe quantos prospects entraram esse mês |
| Vezes que o dado é copiado | 1 a 2 |
| Risco regulatório | Baixo. LGPD: pessoa de contato do cliente final é dado pessoal — base "execução de contrato" cobre, mas precisa ser registrada |

### Etapa 4.2 — Qualificação (entendimento da necessidade)

| Item | Detalhe |
|---|---|
| Papel: vendedor (persona: Rogério) + técnico (persona: Bruno) quando demanda é complexa | |
| Onde acontece | WhatsApp + telefone + visita |
| Ferramenta hoje | Nenhuma estruturada. Conversa, anotação em caderno, foto do instrumento no WhatsApp |
| Tempo médio | 15 a 60 min por prospect |
| Onde dói | Vendedor frequentemente não tem competência técnica pra entender "que padrão precisa? que faixa? que incerteza o cliente final exige?" → erro no orçamento. Técnico interrompido constantemente pra "consulta" |
| Vezes que o dado é copiado | 0 a 1 |

### Etapa 4.3 — Levantamento técnico (visita ou pedido de fotos/specs)

| Item | Detalhe |
|---|---|
| Papel: técnico de campo (persona: Bruno) OU cliente final envia foto + nota fiscal | |
| Onde acontece | No cliente final (visita) ou WhatsApp (foto/spec) |
| Ferramenta hoje | Câmera do celular, WhatsApp, caderno do técnico, planilha "instrumentos clientes.xlsx" |
| Tempo médio | 30 min a 4 horas |
| Onde dói | Visita custa caro (combustível + hora do técnico) e frequentemente não vira venda. Foto mandada por WhatsApp some na conversa em 2 semanas. Spec técnica é digitada 3 vezes: planilha de prospect, orçamento, OS |
| Vezes que o dado é copiado | 2 a 4 |

### Etapa 4.4 — Elaboração do orçamento

| Item | Detalhe |
|---|---|
| Papel: vendedor (persona: Rogério) OU atendente (persona: Letícia), com revisão do dono em casos complexos | |
| Onde acontece | Computador do escritório |
| Ferramenta hoje | Word ou Excel com template "Orçamento padrão.docx" no Drive. Cálculo de preço em planilha separada "tabela de preços.xlsx" — frequentemente desatualizada |
| Tempo médio | 20 a 90 min |
| Onde dói | Tabela de preço desatualizada → margem errada. Esquecimento de incluir deslocamento, hora-técnica, peças, ART. Cliente final pede "desconto" e vendedor não sabe até onde pode ir. Versionamento manual ("Orçamento João v3 FINAL FINAL2.docx") gera confusão |
| Vezes que o dado é copiado | 3 a 5 |
| Risco regulatório | Baixo, mas ART de calibração quando exigida tem retenção 5 anos |

### Etapa 4.5 — Envio do orçamento ao cliente final

| Item | Detalhe |
|---|---|
| Papel: vendedor / atendente (Rogério / Letícia) | |
| Onde acontece | E-mail OU WhatsApp (PDF anexo) |
| Ferramenta hoje | Outlook/Gmail OU WhatsApp Business |
| Tempo médio | 5 a 15 min |
| Onde dói | Vendedor não sabe se cliente final abriu o e-mail. Cliente final pede "manda de novo". Versão errada enviada. PDF mandado por WhatsApp some em 1-2 semanas |
| Vezes que o dado é copiado | 0 a 1 |

### Etapa 4.6 — Follow-up / negociação

| Item | Detalhe |
|---|---|
| Papel: vendedor / dono (Rogério / Roldão) | |
| Onde acontece | WhatsApp + telefone |
| Ferramenta hoje | Caderno do vendedor + planilha (raramente atualizada) |
| Tempo médio | 5 a 30 min/interação, com 1 a 5 interações ao longo de 1 a 6 semanas |
| Onde dói | **Esquecimento de follow-up é causa #1 de perda de venda** [a confirmar via entrevista]. Vendedor "promete ligar amanhã" e não liga. Dono pergunta "o que aconteceu com o orçamento da Empresa X?" e ninguém sabe |
| Vezes que o dado é copiado | 0 |

### Etapa 4.7 — Aprovação formal do cliente final

| Item | Detalhe |
|---|---|
| Papel: cliente final confirma via e-mail, WhatsApp ou ordem de compra (PO) | |
| Onde acontece | Mesmo canal do orçamento |
| Ferramenta hoje | E-mail ou print de WhatsApp salvo em pasta "Pedidos confirmados/2026/" |
| Tempo médio | Variável — 1 dia a 3 semanas |
| Onde dói | Cliente final "aprova verbalmente" no WhatsApp e depois nega. Sem prova documental, lab faz o serviço e fica sem receber. Cliente final esquece que aprovou e reclama da nota fiscal |
| Vezes que o dado é copiado | 1 |
| Risco regulatório | **CDC (Lei 8.078/90)**: aprovação verbal sem prova escrita gera vulnerabilidade em disputa — especialmente B2C ou PME PF |

### Etapa 4.8 — Cadastro de cliente final novo no sistema

| Item | Detalhe |
|---|---|
| Papel: atendente (persona: Letícia) ou financeiro (persona: Cláudia auxiliar) | |
| Onde acontece | Múltiplos sistemas em sequência |
| Ferramenta hoje | (1) Planilha "Clientes.xlsx" / (2) Bling ou Conta Azul / (3) Cali ou Metroex / (4) Planilha de OS / (5) Grupo de WhatsApp interno |
| Tempo médio | 20 a 45 min por cliente final novo |
| Onde dói | **MESMO DADO digitado de 4 a 6 vezes.** Erro de digitação em CNPJ trava NFS-e depois. Endereço diferente entre sistemas → técnico vai pra endereço errado. E-mail divergente → certificado vai pro lugar errado |
| Vezes que o dado é copiado | **4 a 6** — pior ponto de duplicação da jornada |
| Risco regulatório | LGPD: cadastro de pessoa de contato sem base legal explícita; divergência entre sistemas dificulta resposta a direito do titular (art. 18) |

### Etapa 4.9 — Emissão do contrato / proposta formal (B2B grande)

| Item | Detalhe |
|---|---|
| Papel: dono (persona: Roldão) com apoio do contador externo | |
| Onde acontece | Word + e-mail + assinatura física ou digital |
| Ferramenta hoje | Template Word + assinatura via DocuSign / GovBR / impressão + escâner |
| Tempo médio | 1 a 4 horas (contrato simples); 1 a 5 dias úteis (contrato com revisão jurídica) |
| Onde dói | Cliente final grande devolve com cláusula alterada — vai/vem por dias. Versionamento manual de contrato. Dono assina sem reler porque é volume |
| Vezes que o dado é copiado | 2 a 3 |

### Etapa 4.10 — Licitação pública / pregão eletrônico (NOVO — Aud-6)

| Item | Detalhe |
|---|---|
| Papel: dono (persona: Roldão) + financeiro (persona: Cláudia auxiliar) + signatário (persona: Marcos) para atestados | |
| Onde acontece | Portais BR: **ComprasNet, ME Bradesco, SAP Ariba, Coupa**, portais municipais/estaduais |
| Ferramenta hoje | Word/PDF + e-CPF/e-CNPJ A3 (token) + planilha de habilitação + e-mail com contador |
| Etapas | Edital → análise técnica → habilitação documental (CND, CRF, balanço patrimonial, atestados de capacidade técnica) → proposta lacrada → disputa de lances → diligência → ata de adjudicação |
| Tempo médio | 8 a 40 horas por licitação (depende de complexidade) |
| Onde dói | Habilitação documental dispersa (CND vence, balanço com contador, atestado com signatário). Edital cai na sexta com prazo na segunda. Token A3 trava na hora do pregão. Atestado de capacidade técnica não encontrado em pasta de PDFs — gargalo no signatário |
| Vezes que o dado é copiado | 4 a 8 |
| Risco regulatório | Lei 14.133/2021 (Nova Lei de Licitações). Erro em proposta = desclassificação |

### Etapa 4.11 — Contrato anual de calibração (cliente farma/automotivo — NOVO — Aud-6)

| Item | Detalhe |
|---|---|
| Papel: dono (persona: Roldão) + signatário (persona: Marcos) | |
| Onde acontece | Contrato anual firmado com cronograma de calibração trimestral/semestral pré-acordado. **NÃO é orçamento avulso** |
| Ferramenta hoje | Contrato Word + planilha "cronograma 2026.xlsx" + WhatsApp pra confirmar visita |
| Tempo médio | Setup inicial 4-8 horas; gestão mensal 1-2 horas |
| Onde dói | Cliente final farma exige cronograma fixo, mas planilha não emite lembrete automático → lab esquece visita programada → cliente farma sai com cara de raiva. Cobrança recorrente sem régua de faturamento. Atraso em uma visita do cronograma quebra a recorrência |
| Vezes que o dado é copiado | 2 a 4 por execução de cronograma |
| Risco regulatório | Anvisa RDC 658/2022 (BPF) — cliente farma precisa de calibração no prazo |

### Etapa 4.12 — Emissão de atestado de capacidade técnica (NOVO — Aud-6)

| Item | Detalhe |
|---|---|
| Papel: signatário (persona: Marcos) | |
| Onde acontece | Word + assinatura signatário + envio por e-mail |
| Ferramenta hoje | Template Word "Atestado padrão.docx" + assinatura física ou digital e-CPF |
| Tempo médio | 30 min a 2 horas por atestado |
| Onde dói | **Recorrente** — cliente final pede atestado pra usar em licitação dele próprio. Signatário é gargalo (já é gargalo do certificado, ainda atende pedido de atestado). Sem histórico estruturado, signatário tem que reconstituir "quantas calibrações vocês fizeram pra Empresa X em 2025" olhando pasta de PDFs |
| Vezes que o dado é copiado | 2 a 3 |
| Risco regulatório | Atestado falso é crime (CP art. 299). Signatário responde |

---

## 5. Detalhamento do Ciclo Operacional

> **Do "pode iniciar" à execução do serviço — em laboratório OU em campo.**

### Etapa 5.1 — Abertura do chamado / OS

| Item | Detalhe |
|---|---|
| Papel: atendente (persona: Letícia) | |
| Onde acontece | Após confirmação comercial OU contato direto do cliente final |
| Ferramenta hoje | Planilha "Controle OS 2026.xlsx" — numeração manual frequentemente furada/duplicada |
| Tempo médio | 10 a 25 min |
| Onde dói | Numeração de OS duplicada quando 2 atendentes abrem ao mesmo tempo. Planilha trava com 5 mil linhas. Sem visão de "carga por técnico" — atribuição no escuro. Dono não sabe quantas OS abertas tem |
| Vezes que o dado é copiado | 2 |
| Risco regulatório | **17025 cláusula 7.1 — Análise crítica de pedidos:** lab precisa registrar análise crítica ANTES de iniciar. Planilha não obriga → NC em auditoria Cgcre. **Cláusula 7.1.3 — Regra de decisão:** se cliente final vai exigir declaração de conformidade, regra de decisão precisa ser acordada ANTES, registrada. Status quo: nunca é |

### Etapa 5.2 — Triagem (manutenção vs calibração vs venda de peça)

| Item | Detalhe |
|---|---|
| Papel: dono / técnico sênior (Roldão / Marcos) | |
| Onde acontece | Planilha + WhatsApp interno |
| Ferramenta hoje | Reunião curta, mensagem no grupo |
| Tempo médio | 5 a 15 min por OS |
| Onde dói | Triagem errada — calibração vira manutenção (perde receita regulatória) OU manutenção vira calibração (técnico sem padrão vai calibrar). Cliente final cobrado errado. Retrabalho |
| Risco regulatório | Médio — triagem errada pode levar a emissão indevida de certificado (perfil A: NC grave) |

### Etapa 5.3 — Atribuição de técnico + agendamento

| Item | Detalhe |
|---|---|
| Papel: dono (persona: Roldão) ou gerente operacional | |
| Onde acontece | Planilha "Agenda Técnicos.xlsx" + Google Calendar individual |
| Ferramenta hoje | Planilha + WhatsApp ("João, amanhã 8h, Cliente Y, Rua Z") |
| Tempo médio | 5 a 15 min por OS agendada |
| Onde dói | **Roteirização péssima:** técnico A vai pra zona norte de manhã e zona sul à tarde, técnico B faz o oposto — 2x combustível e 2x tempo. Cancelamento em cima da hora deixa técnico ocioso. Técnico esquece compromisso porque foi avisado só por WhatsApp |
| Vezes que o dado é copiado | 2 a 3 |

### Etapa 5.4 — Preparação do técnico (pra ir a campo)

| Item | Detalhe |
|---|---|
| Papel: técnico de campo (persona: Bruno) | |
| Onde acontece | Laboratório, antes de sair |
| Ferramenta hoje | Imprime OS, pega ficha técnica, separa padrões do armário, anota número de série dos padrões no caderno, abastece carro |
| Tempo médio | 30 a 90 min |
| Onde dói | Padrão errado levado (não cobre faixa) → técnico chega e não consegue calibrar → 2ª visita = prejuízo. Padrão VENCIDO levado → certificado emitido é NULO em auditoria Cgcre |
| Risco regulatório | **17025 cláusula 6.5 + INV-011:** padrão vencido invalida calibração. **Risco crítico** [a confirmar frequência via entrevista] |

### Etapa 5.5 — Execução em campo (calibração in loco ou manutenção)

| Item | Detalhe |
|---|---|
| Papel: técnico de campo (persona: Bruno) | |
| Onde acontece | Cliente final |
| Ferramenta hoje | Caderno de campo + planilha em papel + foto + WhatsApp pro signatário ("achei isso, posso seguir?") |
| Tempo médio | 1 a 6 horas |
| Onde dói | Anotação a lápis ilegível. Foto do display borrada. Técnico esquece de medir 1 ponto → 2ª visita. Sem sinal de celular = sem consulta ao signatário = decisão errada de NC. Cliente final assina "termo de recebimento" rabiscado num papel que se perde |
| Risco regulatório | **17025 cláusula 7.5 — Registros técnicos:** dados brutos legíveis exigidos. Caderno ilegível = NC. **Cláusula 7.5.1 — Identificação inequívoca + ininterrupção:** registro em WhatsApp NÃO cumpre — mensagem pode ser apagada, conta encerrada, conversa exportada com perda. **Violação silenciosa permanente.** |

### Etapa 5.6 — Execução em laboratório (cliente final deixou o instrumento)

| Item | Detalhe |
|---|---|
| Papel: metrologista / signatário (persona: Marcos) ou técnico (persona: Bruno) | |
| Onde acontece | Laboratório |
| Ferramenta hoje | Cali ou Metroex (se acreditado, ~50-55% dos labs B/C) **OU Planilha Excel + macros próprias + GUM Workbench (~25-30% dos labs)** OU Word puro (perfil D) |
| Tempo médio | 1 a 8 horas por instrumento |
| Onde dói | Cali desktop só roda em 1 PC — se quebra, calibração para. Backup do banco do Cali esquecido. Versão do Cali desatualizada → erro de cálculo descoberto em auditoria. **Planilha Excel + macros pra cálculo de incerteza SEM validação documentada = NC permanente da cláusula 7.11**, não "vai dar problema quando Office atualizar" — é não conformidade ATIVA enquanto o lab usa |
| Vezes que o dado é copiado | 2 a 3 |
| Risco regulatório | **17025 cláusula 7.11 — Software validado:** versão do software DEVE estar gravada no certificado (INV-004c). Excel + macros sem dossiê de validação (especificação + teste + aprovação documentada) é NC permanente. **Esse é o pitch real do Aferê: tirar o lab da NC, não "facilitar o cálculo"** |

### Etapa 5.7 — Volta pro laboratório / fechamento da OS

| Item | Detalhe |
|---|---|
| Papel: técnico (persona: Bruno) + atendente (persona: Letícia) | |
| Onde acontece | Lab, fim do dia |
| Ferramenta hoje | Técnico entrega papel/caderno → atendente digita na planilha → marca OS como "pronta pra emitir certificado" |
| Tempo médio | 15 a 45 min por OS |
| Onde dói | Atendente digita errado o que técnico anotou. Técnico "esquece" de entregar OS porque saiu correndo pra próxima visita → OS aparece 3 dias depois → cliente final já cobrou |

### Etapa 5.8 — Atualização do cliente final sobre status

| Item | Detalhe |
|---|---|
| Papel: atendente (persona: Letícia) | |
| Onde acontece | WhatsApp / e-mail / telefone |
| Ferramenta hoje | Mensagem manual quando o cliente final pergunta |
| Tempo médio | 5 a 10 min por consulta |
| Onde dói | **Atendente recebe 10-30 perguntas/dia** sobre status, todas respondíveis se tivesse portal. Tempo perdido enorme. Cliente final fica com sensação de "não dão satisfação" |

### Etapa 5.9 — Logística de devolução do instrumento

| Item | Detalhe |
|---|---|
| Papel: atendente (persona: Letícia) + motoboy/transportadora/Correios OU cliente final vem buscar | |
| Onde acontece | Lab → cliente final |
| Ferramenta hoje | Etiqueta impressa + nota de remessa em Word + WhatsApp pra motoboy |
| Tempo médio | 30 a 60 min por instrumento |
| Onde dói | Instrumento entregue ao cliente final errado (duas balanças similares, etiqueta caiu). Motoboy não confirma entrega → ninguém sabe se chegou. Extravio = prejuízo + cliente final furioso |
| Risco regulatório | **17025 cláusula 7.4 — Manuseio de itens:** rastreabilidade desde recebimento até devolução exigida. Sem sistema = sem prova → NC se cliente final reclamar |

### Etapa 5.10 — Pós-venda / pesquisa de satisfação

| Item | Detalhe |
|---|---|
| Papel: atendente (persona: Letícia) quando faz | |
| Onde acontece | WhatsApp ou e-mail, semanas depois |
| Ferramenta hoje | Mensagem manual genérica |
| Tempo médio | 5 min por cliente final |
| Onde dói | **Não é sistemático.** Sem NPS, sem CSAT, empresa não sabe quem está satisfeito até receber reclamação ou perder o cliente final |
| Risco regulatório | **17025 cláusula 8.6 — Melhoria:** feedback é entrada obrigatória pro sistema de gestão. Sem registro = lacuna em auditoria |

---

## 6. Detalhamento do Ciclo Metrológico (regulado ISO 17025)

> **Da entrada controlada do instrumento até o certificado assinado e arquivado. O ciclo mais crítico do ponto de vista regulatório — onde uma falha pode tirar a acreditação.**

### Etapa 6.1 — Recebimento e entrada controlada

| Item | Detalhe |
|---|---|
| Papel: atendente (persona: Letícia) + técnico (persona: Bruno) | |
| Onde acontece | Recepção do laboratório |
| Ferramenta hoje | Etiqueta numerada + planilha "Entradas 2026.xlsx" + ficha de recepção em papel |
| Tempo médio | 15 a 30 min por instrumento |
| Onde dói | Etiqueta cai. Ficha de papel se perde. Número de série digitado errado → confusão. Cliente final nega que entregou ("a minha balança era a outra") |
| Risco regulatório | **17025 cláusula 7.4 + 7.8:** identificação inequívoca obrigatória |

### Etapa 6.1.5 — Avaliação de aceitabilidade do item (NOVA sub-etapa — Aud-6)

| Item | Detalhe |
|---|---|
| Papel: técnico (persona: Bruno) ou signatário (persona: Marcos) | |
| O que é | **Critério de rejeição documentado.** Decisão registrada: "instrumento entra na fila de calibração" OU "instrumento rejeitado por dano/contaminação/falta de pré-requisito" |
| Ferramenta hoje | Não existe formalmente. Decisão verbal "esse aí tá ruim, manda voltar" — sem registro |
| Onde dói | Cliente final reclama que rejeição não foi comunicada. Critério de rejeição varia de técnico pra técnico. Auditor Cgcre pede evidência de avaliação documentada — não tem |
| Risco regulatório | **17025 cláusula 7.4.3:** avaliação de aceitabilidade obrigatória. Sem registro = NC |

### Etapa 6.2 — Inspeção inicial / verificação preliminar

| Item | Detalhe |
|---|---|
| Papel: técnico de bancada (persona: Bruno) | |
| Onde acontece | Bancada de calibração |
| Ferramenta hoje | Caderno técnico + foto + planilha de "estado inicial" |
| Tempo médio | 20 a 60 min |
| Onde dói | Anotação subjetiva ("estado regular") sem padrão → cliente final reclama depois ("vocês danificaram"). Foto de baixa qualidade |

### Etapa 6.3 — Verificação de validade do padrão a ser usado

| Item | Detalhe |
|---|---|
| Papel: técnico (persona: Bruno) ou signatário (persona: Marcos) | |
| Onde acontece | Armário de padrões |
| Ferramenta hoje | Olhar etiqueta colada no padrão + planilha "Padrões — validade.xlsx" + pasta no Drive com certificados-pai |
| Tempo médio | 5 a 10 min |
| Onde dói | **Esquecimento de verificar validade é falha comum** [a confirmar]. Padrão com calibração vencida usado = certificado nulo + risco de perder acreditação |
| Risco regulatório | **CRÍTICO — INV-011 + 17025 cláusula 6.5.** Materializa R-018 (NIT-DICLA-030 rev. 15) |

### Etapa 6.3.5 — Estabilização térmica (NOVA sub-etapa — Aud-6)

| Item | Detalhe |
|---|---|
| Papel: técnico (persona: Bruno) | |
| O que é | Instrumento e padrão estabilizados em 20±2°C por 4-24 horas antes da calibração (depende da grandeza). Etapa esquecida em ambiente sem controle |
| Ferramenta hoje | Memória do técnico — "deixei desde ontem", sem registro de hora |
| Onde dói | Calibração feita sem estabilização adequada gera erro sistemático nas medições. Auditor Cgcre pede registro de tempo de estabilização — não tem |
| Risco regulatório | **17025 cláusula 6.3:** instalações e condições ambientais devem ser monitoradas e registradas |

### Etapa 6.4 — Execução da calibração (medições contra padrão)

| Item | Detalhe |
|---|---|
| Papel: técnico de bancada / metrologista (Bruno / Marcos) | |
| Onde acontece | Bancada |
| Ferramenta hoje | Cali / Metroex (entrada manual) OU planilha + cálculo no Excel |
| Tempo médio | 30 min a 4 horas |
| Onde dói | Digitação manual de 10 a 50 leituras → erro. Cali não tem captura automática do instrumento → técnico lê display, anota, digita. Interrupção (telefone, cliente final chega) → técnico perde linha, repete tudo |

### Etapa 6.4.5 — Registro de condições ambientais (NOVA sub-etapa — Aud-6)

| Item | Detalhe |
|---|---|
| Papel: técnico (persona: Bruno) | |
| O que é | Registro de T (temperatura), UR (umidade relativa), P (pressão) durante a calibração — com sensor calibrado, não termômetro de cozinha |
| Ferramenta hoje | Anotação manual no caderno OU sensor sem certificado de calibração próprio (caso comum) |
| Onde dói | Sem sensor calibrado = registro inválido. Sem registro contínuo (só leitura única no início) → não cobre variação durante a calibração de 4 horas |
| Risco regulatório | **17025 cláusula 6.3 + 7.5:** condições ambientais que afetam resultado devem ser registradas e o instrumento de monitoramento deve ser calibrado |

### Etapa 6.5 — Cálculo de incerteza

| Item | Detalhe |
|---|---|
| Papel: signatário (persona: Marcos) ou metrologista | |
| Onde acontece | Software |
| Ferramenta hoje | Cali / Metroex / **GUM Workbench (Metrodata)** / planilha Excel com macros |
| Tempo médio | 5 a 30 min |
| Onde dói | **Planilha Excel personalizada com macros pra incerteza, SEM validação documentada (especificação + teste + aprovação) = NC permanente da cláusula 7.11.** Não é "macro vai quebrar" — é não conformidade ATIVA enquanto o lab usa. Cálculo errado descoberto só em auditoria de cliente farma (cliente reprova lote inteiro). GUM Workbench é alternativa mais defensável que Excel puro |
| Risco regulatório | **17025 cláusula 7.6 + 7.11 + NIT-DICLA-021:** cálculo de incerteza segundo EA-4/02 obrigatório. **Software validado obrigatório — Excel puro sem dossiê é NC permanente** |

### Etapa 6.6 — Análise crítica do resultado

| Item | Detalhe |
|---|---|
| Papel: signatário (persona: Marcos) ou metrologista responsável | |
| Onde acontece | Antes de assinar o certificado |
| Ferramenta hoje | Olhar resultado no Cali ou Word + comparar com histórico (quando tem) |
| Tempo médio | 10 a 30 min |
| Onde dói | Sem histórico estruturado, signatário não percebe deriva anormal. Análise feita "no olho". Pressa pra emitir → análise superficial → erro passa |

### Etapa 6.6.5 — Verificação por segundo caminho (NOVA sub-etapa — Aud-6)

| Item | Detalhe |
|---|---|
| Papel: signatário (persona: Marcos) + RT (persona: Sandra) | |
| O que é | Carta de controle, ensaio de proficiência (EP), intercomparação — segundo caminho independente que confirma o resultado |
| Ferramenta hoje | Excel manual com pontos de controle desatualizados; EP só quando provider externo cobra |
| Onde dói | Sem carta de controle viva, deriva do padrão não é detectada. EP feito 1x/ano só pra cumprir tabela — não usado pra ajuste de procedimento |
| Risco regulatório | **17025 cláusula 7.7 — Garantia da validade dos resultados:** monitoramento sistemático obrigatório. Sem evidência = NC |

### Etapa 6.7 — Decisão sobre regra de decisão / declaração de conformidade

| Item | Detalhe |
|---|---|
| Papel: signatário (persona: Marcos) | |
| Onde acontece | Antes da emissão |
| Ferramenta hoje | Documento de procedimento interno (Word) + cabeça do signatário |
| Tempo médio | 5 a 15 min |
| Onde dói | Regra aplicada inconsistentemente. Cliente final que pediu "conformidade simples" recebe "conformidade com risco compartilhado" → confusão jurídica. ILAC G8 não aplicado |
| Risco regulatório | **17025 cláusula 7.8.6 + 7.1.3 + ILAC G8:** regra de decisão deve ser **acordada PREVIAMENTE com o cliente final** + obrigatória quando declaração de conformidade. Status quo viola — regra é "escolhida" pelo signatário na hora |

### Etapa 6.8 — Emissão do certificado (PDF)

| Item | Detalhe |
|---|---|
| Papel: técnico (persona: Bruno) ou signatário (persona: Marcos) | |
| Onde acontece | Cali / Metroex / Word |
| Ferramenta hoje | Template do Cali ou template Word "Certificado padrão.docx" |
| Tempo médio | 10 a 30 min |
| Onde dói | Template Word frequentemente desalinhado com NIT-DICLA-021 (faltam campos: rastreabilidade explícita, incerteza k=2, condições ambientais, versão do software). PDF sem assinatura digital ICP-Brasil → cliente farma rejeita |
| Risco regulatório | **17025 cláusulas 7.8 + 7.8.6 + NIT-DICLA-021 + INV-002 + INV-004c:** todos campos obrigatórios. **R-018 é o maior risco do produto** |

### Etapa 6.8.5 — Revisão técnica por 2º signatário "4 olhos" (NOVA sub-etapa — Aud-6)

| Item | Detalhe |
|---|---|
| Papel: 2º signatário (persona: Marcos #2) ou RT (persona: Sandra) | |
| O que é | Boa prática em lab A maduro — segundo signatário revisa certificado antes da emissão. Reduz erro grosseiro |
| Ferramenta hoje | Não existe na empresa-modelo de 5-10 pessoas (só tem 1 signatário) |
| Onde dói | Empresa A em transição quer implementar 4-olhos mas não tem ferramenta — vira "imprime e passa pra colega olhar" — não escala, não registra |

### Etapa 6.9 — Assinatura do certificado

| Item | Detalhe |
|---|---|
| Papel: signatário (persona: Marcos) | |
| Onde acontece | Signatário abre PDF, imprime, assina, escaneia OU assina digitalmente com e-CPF |
| Ferramenta hoje | Adobe Reader + scanner OU ferramenta de assinatura digital (Adobe Sign, GovBR, e-CPF A3) |
| Tempo médio | 5 a 15 min por certificado |
| Onde dói | **Signatário é gargalo.** Empilha 20 certificados e demora 2-3 dias. **Assina em massa sem reler** porque é volume grande — descumpre supervisão da cláusula 6.2. Escopo de assinatura não controlado pelo sistema → signatário assina fora do escopo = NC grave |
| Risco regulatório | **17025 cláusula 6.2 + INV-003:** signatário só assina dentro do escopo + obrigação de supervisão real (não assinatura cega). Assinar em massa sem reler = NC. **R-015** materializa quando ele falta |

### Etapa 6.9.5 — Aplicação de selo/etiqueta no instrumento (NOVA sub-etapa — Aud-6)

| Item | Detalhe |
|---|---|
| Papel: técnico (persona: Bruno) | |
| O que é | Etiqueta física aplicada no instrumento com: nº do certificado, data, próxima calibração, signatário, lab. Etapa frequentemente esquecida |
| Ferramenta hoje | Impressora térmica de etiqueta OU etiqueta manual escrita à caneta |
| Onde dói | Etiqueta cai/borra → cliente final liga "qual era o número desse certificado?" → atendente garimpa pasta de PDFs |

### Etapa 6.10 — Arquivamento do certificado

| Item | Detalhe |
|---|---|
| Papel: atendente (persona: Letícia) ou financeiro (persona: Cláudia auxiliar) | |
| Onde acontece | Drive da Google, OneDrive ou pasta de rede |
| Ferramenta hoje | Nomeação manual: "Certificado-12345-ClienteX-Balanca-2026.pdf" |
| Tempo médio | 5 min por certificado |
| Onde dói | Convenção de nome inconsistente. Pasta de rede sem backup. Drive público compartilhado errado por engano. Sem WORM → certificado pode ser editado depois (fraude possível) |
| Risco regulatório | **17025 cláusula 8.4 + INV-001 + INV-013 + INV-010:** retenção mínima 5 anos, WORM, log de acesso. **Drive sem WORM = sem garantia de integridade = NC cláusula 8.4** |

### Etapa 6.10.5 — Ajuste pós-calibração + recalibração as found/as left (NOVA sub-etapa — Aud-6)

| Item | Detalhe |
|---|---|
| Papel: técnico (persona: Bruno) + signatário (persona: Marcos) | |
| O que é | Fluxo "as found / as left" — quando cliente final pede ajuste após calibração: emitir **2 certificados** (as found = como veio + as left = após ajuste). Comum em cliente farma |
| Ferramenta hoje | Refazer tudo no Cali do zero. Sem link entre os 2 certificados |
| Onde dói | Cliente farma espera 2 certificados encadeados (rastreabilidade do antes/depois). Lab entrega 2 certificados soltos sem referência cruzada. Auditor do cliente final reclama. **Receita perdida** — muito lab cobra 1 calibração quando podia cobrar 2 |

### Etapa 6.11 — Envio do certificado ao cliente final

| Item | Detalhe |
|---|---|
| Papel: atendente (persona: Letícia) | |
| Onde acontece | E-mail (anexo PDF) ou WhatsApp |
| Ferramenta hoje | Gmail / Outlook / WhatsApp Business |
| Tempo médio | 5 a 10 min |
| Onde dói | Certificado mandado pro contato errado do cliente final (e-mail desatualizado). Cliente final perde o e-mail e pede de novo 3 meses depois. Sem log de envio → "vocês nunca me mandaram!" |
| Risco regulatório | LGPD: dado de cliente final vazado se enviado pro endereço errado |

### Etapa 6.12 — Gestão da validade da calibração (lembrar cliente final da próxima)

| Item | Detalhe |
|---|---|
| Papel: vendedor (persona: Rogério) ou atendente (persona: Letícia) quando lembra | |
| Onde acontece | Planilha "Validades.xlsx" + Google Calendar |
| Ferramenta hoje | Planilha + lembretes manuais |
| Tempo médio | 30 min/mês pra revisar a planilha |
| Onde dói | **NÃO é sistemático.** Empresa-modelo perde **30-50% das recalibrações** por esquecimento (fonte: estimativa setorial, validar Onda 1+2). Cliente final recebe lembrete da concorrência antes |

---

## 6.bis — Violações regulatórias silenciosas (NOVA seção — Aud-7)

> **A jornada atual viola silenciosamente várias cláusulas 17025 + LGPD enquanto o lab opera, sem ninguém perceber.** Lista compacta — cada item materializa NC permanente ATIVA.

| Cláusula / artigo | Como o status quo viola |
|---|---|
| **17025 cláusula 7.11** (software validado) | Word/Excel/macros pra certificado e cálculo de incerteza SEM dossiê de validação documentado (especificação + teste + aprovação). NC ativa enquanto usar |
| **17025 cláusula 7.5.1** (registros técnicos com identificação inequívoca + ininterrupção) | Registro em WhatsApp não cumpre — mensagem pode ser apagada, conta encerrada, conversa exportada com perda de metadado. Caderno físico também viola (não tem timestamp confiável nem assinatura inequívoca) |
| **17025 cláusula 8.4** (controle de registros, integridade) | Drive da Google / OneDrive / pasta de rede SEM WORM = certificado pode ser editado depois → sem garantia de integridade = NC |
| **17025 cláusula 4.2** (confidencialidade) | Dado de cliente final passa por Bling/Conta Azul/Drive sem DPA (Data Processing Agreement) assinado |
| **17025 cláusula 6.2** (supervisão de signatário) | Signatário assina 20 certificados em massa sem reler — descumpre obrigação de supervisão real |
| **17025 cláusula 7.1.3** (regra de decisão acordada previamente) | Regra de decisão escolhida pelo signatário na hora da emissão, sem acordo prévio escrito com o cliente final |
| **LGPD art. 33** (transferência internacional / operador) | Sem DPA com Bling, Conta Azul, Drive da Google, WhatsApp. Dado de cliente final do tenant trafega/é armazenado por terceiros sem contrato de tratamento |
| **LGPD art. 18** (direitos do titular) | Sem canal estruturado pra responder pedido de titular (acesso, retificação, exclusão). Se cliente final pedir, tenant não consegue cumprir prazo |
| **LGPD art. 48** (notificação de incidente à ANPD) | Sem mecanismo pra notificar ANPD em **3 dias úteis** (Res. CD/ANPD 15/2024) — vazamento de e-mail com certificado fica sem comunicação |

**Implicação pro pitch:** Aferê não é "mais conveniente" — é **a única forma de tirar a empresa-modelo do estado de violação silenciosa permanente**.

---

## 7. Detalhamento do Ciclo Financeiro

> **Do "OS fechada" ao "valor entrou na conta + conciliado".**

### Etapa 7.1 — Emissão da NFS-e

| Item | Detalhe |
|---|---|
| Papel: financeiro (persona: Cláudia auxiliar) | |
| Onde acontece | Bling, Conta Azul, Omie, ou portal da prefeitura |
| Ferramenta hoje | Bling/Omie/Conta Azul (~70% das pequenas) OU portal municipal direto (~30%) |
| Tempo médio | 10 a 20 min por NFS-e |
| Onde dói | Dados do cliente final DIGITADOS DE NOVO no Bling/Omie. Descrição genérica ("calibração") sem detalhar instrumento, faixa, certificado → cliente final questiona. Código de serviço municipal errado → ISS errado. **Cutover NFS-e Padrão Nacional 01/09/2026** (R-016) muda layout |
| Risco regulatório | **LC 214/2025 + Resolução CGSN 189/2026:** ME/EPP migra obrigatoriamente em 01/09/2026. **R-016 score 20** |

### Etapa 7.2 — Geração de boleto / cobrança PIX

| Item | Detalhe |
|---|---|
| Papel: financeiro (persona: Cláudia auxiliar) | |
| Onde acontece | Internet banking + Bling/Conta Azul |
| Ferramenta hoje | Banco PJ (Itaú, BB, Bradesco, Santander, Sicredi, **Banco Inter PJ, BTG Empresas, Nubank PJ, C6 Bank PJ**) OU plataforma de cobrança (**Asaas, Cobre Fácil, Vindi, Iugu, Pagar.me**) |
| Tempo médio | 5 a 10 min por boleto |
| Onde dói | Geração manual de boleto trava se sistema bancário cai. PIX manual sem identificação no extrato → conciliação difícil. Boleto enviado pro contato errado |
| Risco regulatório | **PIX Recuperação de fundos obrigatória desde 02/02/2026** (BCB 493/2025) |

### Etapa 7.3 — Envio de boleto/cobrança ao cliente final

| Item | Detalhe |
|---|---|
| Papel: financeiro (persona: Cláudia auxiliar) | |
| Onde acontece | E-mail + WhatsApp |
| Ferramenta hoje | Gmail/Outlook + WhatsApp |
| Tempo médio | 5 min por cliente final |
| Onde dói | Cliente final alega "não recebi" e financeiro reenvia. Sem log estruturado |

### Etapa 7.4 — Recebimento e conciliação bancária

| Item | Detalhe |
|---|---|
| Papel: financeiro (persona: Cláudia auxiliar) | |
| Onde acontece | Internet banking + Bling/Omie |
| Ferramenta hoje | Download de extrato OFX/CNAB + importação no Bling/Omie + conciliação manual |
| Tempo médio | **30 min a 3 horas por semana** |
| Onde dói | PIX recebido com identificador errado → não bate com NFS-e → conciliação manual. Boleto pago com valor parcial → cobrar diferença. Boleto pago em duplicidade → devolver. **Sem integração bancária = trabalho manual enorme** |
| Risco regulatório | **Bacen Res. 4.658/2018 + Open Finance:** integração com banco exige requisitos de segurança quando feita direto |

### Etapa 7.5 — Gestão de inadimplência

| Item | Detalhe |
|---|---|
| Papel: financeiro (persona: Cláudia auxiliar) + dono (persona: Roldão) | |
| Onde acontece | Planilha "Inadimplentes.xlsx" + WhatsApp/telefone |
| Ferramenta hoje | Planilha manual + cobrança manual |
| Tempo médio | 2 a 4 horas/semana |
| Onde dói | **Cobrança vira problema pessoal do dono.** Cliente final inadimplente é também cliente operacional ativo → conflito interno: cobrar e perder cliente OU atender e nunca receber |

### Etapa 7.6 — Bloqueio de cliente final inadimplente

| Item | Detalhe |
|---|---|
| Papel: dono (persona: Roldão) — decisão difícil | |
| Onde acontece | Reunião dono + financeiro + atendente |
| Ferramenta hoje | "Aviso" pelo WhatsApp do grupo interno |
| Tempo médio | Variável |
| Onde dói | Atendente não-avisada abre OS pra cliente final bloqueado. Decisão emocional do dono gera mais inadimplência |

### Etapa 7.7 — Fechamento contábil mensal

| Item | Detalhe |
|---|---|
| Papel: financeiro (persona: Cláudia auxiliar) + contador externo | |
| Onde acontece | Bling/Omie → e-mail pro contador |
| Ferramenta hoje | Bling/Omie/Conta Azul + Excel + e-mail. **Empresas maiores: Sankhya, TOTVS PME, Tiny, Egestor, Granatum, Nibo** |
| Tempo médio | 4 a 12 horas/mês + tempo do contador |
| Onde dói | Conciliação operacional ↔ financeiro inexistente. Contador devolve perguntas que financeiro não sabe responder |
| Risco regulatório | **Receita Federal:** SPED, retenção fiscal 5 anos. **CTN art. 173/174** |

### Etapa 7.8 — DRE / visão do dono

| Item | Detalhe |
|---|---|
| Papel: contador (envia relatório) + dono (persona: Roldão) lê | |
| Onde acontece | E-mail / reunião mensal |
| Ferramenta hoje | PDF do contador + planilha "Resumo do mês.xlsx" |
| Tempo médio | 1 hora pro dono entender + reunião com contador |
| Onde dói | Dono vê DRE com 30-45 dias de atraso → decide com info defasada. Sem visão de margem por serviço/cliente final/grandeza → não sabe o que é rentável |

---

## 8. Custo do status quo — visão consolidada (recalibrado Aud-6)

> **Empresa-modelo: 5-10 funcionários, perfil B com algumas regras 17025 ativadas, atendendo balança comercial + industrial + manômetro, faturamento R$ 50-150k/mês, ~120 certificados/mês + ~50 OS de manutenção/mês.**
>
> **Esse número é o que vende o produto.** Detalhamento abaixo — todos `[a confirmar via entrevista Onda 1+2]`.

| Categoria de perda | Custo mensal |
|---|---|
| Retrabalho operacional puro (digitação duplicada, versão errada, erro de cadastro, atendimento manual de status) | **R$ 8.000 a R$ 15.000** |
| Combustível + 2ª visita (roteirização ruim, padrão errado, padrão vencido, esquecimento de medida em campo) | **R$ 3.000 a R$ 6.000** |
| Conciliação financeira manual (extrato vs NFS-e vs OS) + cobrança manual de inadimplência | **R$ 1.500 a R$ 3.000** |
| Custo de oportunidade do dono "apagando incêndio" (40-80h/mês em problemas evitáveis a R$ 150-300/h efetiva) | **R$ 9.000** |
| **Receita perdida em recalibração (30-50% de esquecimento × ticket médio × volume)** | **R$ 8.000 a R$ 12.000** |
| Risco regulatório provisionado (NC, multa potencial, custo de reauditoria, perda parcial de cliente farma) — provisão mensal | **R$ 3.300** |
| Cliente final perdido (1-3 por trimestre × LTV médio) — distribuído mensalmente | **R$ 2.500** |
| **TOTAL** | **R$ 35.000 a R$ 50.000/mês** |

**Comparação:** o custo do status quo equivale a **23% a 100% do faturamento mensal** da empresa-modelo. **Não é "ineficiência tolerável" — é hemorragia.**

**Mais difícil de quantificar mas igualmente real:**

- **Burnout do dono** — dono trabalha 60-70h/semana, qualidade de vida zero.
- **Bloqueio de crescimento** — empresa não consegue dobrar de tamanho porque operação manual já está no limite.
- **Risco catastrófico** — NC grave em auditoria Cgcre custa de R$ 5 mil (reauditoria + consultor) até **perda da acreditação** (destrói o negócio).

---

## 9. Variações por perfil (A / B / C / D)

### 9.1 Variação — empresa maior (10-20 funcionários, perfil B-rigoroso ou A enxuto)

**Diferenças vs caso-base (5-10 pessoas, perfil B com algumas regras):**

- 2-4 técnicos de campo (vs 1-2).
- RT/Qualidade dedicada (Sandra) — não acumulada com o dono.
- Signatário dedicado (Marcos) — não é o dono.
- Faturamento R$ 150-400k/mês.
- 150-300 certificados/mês.
- Pode estar em transição pra acreditação A ou já acreditado em escopo limitado.
- **Custo de status quo maior em termos absolutos** (R$ 50-90k/mês) **mas proporcionalmente menor** (15-30% do faturamento — empresa absorve melhor).

### 9.2 Perfil A puro (acreditado RBC)

- Ciclo metrológico é **MAIS rigoroso** — todos os invariantes 17025 ativos. Auditoria Cgcre a cada 12-18 meses (não 2 anos).
- Signatário ainda mais crítico — escopo de assinatura validado em auditoria.
- Cliente final (farma, automotivo, aeroespacial) exige rastreabilidade completa.
- **Dor adicional:** preparação pra auditoria Cgcre custa 80-200 horas a cada ciclo.
- **Cali ou Metroex** são quase obrigatórios — Word + Excel insustentável.

### 9.3 Perfil C (preparando-se pra acreditação)

- Operação como B + esforço de "endurecer" processos pra passar em auditoria de admissão.
- Consultor externo de qualidade contratado (R$ 5-15k/mês durante 12-24 meses).
- **Dor adicional:** ter que retroativamente padronizar registros que foram feitos sem estrutura → projeto longo e doloroso. Muitas empresas DESISTEM.
- **Maior oportunidade do Aferê:** software que cresce com a empresa.

### 9.4 Perfil D (calibração comercial básica, sem 17025)

- Operação MUITO mais simples. Ciclo metrológico = "técnico mede, anota, dá um papel".
- **Cali ou Metroex frequentemente NÃO usados** — Word + Excel bastam.
- Cliente final é varejo (açougue, padaria, supermercado), oficina mecânica, lab interno sem regulação.
- **Dor adicional:** confusão regulatória — empresa D pode estar **violando R-040** (cliente final acha que tem verificação INMETRO válida porque "calibrou", quando falta verificação periódica do IPEM).

---

## 10. Variações por tipo de instrumento

### 10.1 Balança comercial (regulada IPEM/INMETRO)

- **Verificação metrológica legal obrigatória anual pelo IPEM/RBMLQ-I** (Portaria 157/2022). Calibração feita pelo lab NÃO substitui essa verificação.
- **Ciclo extra:** lab calibrador frequentemente é o "intermediário" que avisa cliente final sobre verificação IPEM.
- **Dor adicional:** confusão cliente final entre "selo INMETRO" e "certificado de calibração" — R-040 score 12.

### 10.2 Balança industrial / dosadora

- **Calibração frequentemente em campo** (instrumento fixo na linha de produção).
- **Padrões pesados** — massas-padrão M1/F1 de 5kg a 50kg.
- **Dor adicional:** parar linha de produção do cliente final é caro → janela curta (madrugada, fim de semana).

### 10.3 Balança analítica / semi-analítica (lab químico, farma)

- **Calibração em lab** preferencial.
- **Faixa pequena** (mg-g), exatidão alta, incerteza expandida com k=2.
- **Cliente farma exige:** rastreabilidade + IQ/OQ/PQ + validação de software + Anvisa RDC 658/2022.

### 10.4 Balança rodoviária

- **Calibração 100% em campo**.
- **Cargas-padrão de 100kg a 30 toneladas** — caminhão com bloco de teste.
- **Implicação tributária** (peso = ICMS, pedágio, royalty mineração) → erro vira disputa fiscal.

### 10.5 Manômetro / termômetro / paquímetro / micrômetro

- **Volume alto** (lab faz dezenas por dia).
- **Calibração em lab**.
- **Dor adicional:** instrumentos parecidos visualmente → risco de troca/confusão.

---

## 11. Pontos de inflexão — eventos que fazem o dono dizer "preciso resolver isso JÁ"

> Os "triggers de dor crítica" — eventos que normalmente disparam a busca por uma solução estruturada.

1. **Não conformidade em auditoria Cgcre** — supervisão chega, audita pastas, encontra rastreabilidade quebrada, padrão usado com calibração vencida. Custo: 80-200h pra resolver + risco de perder acreditação.
2. **Cliente farma rejeita certificado** — lote inteiro reprovado por erro de cálculo de incerteza. Cliente cobra prejuízo do lab (R$ 50k a R$ 500k) e cancela contrato.
3. **Multa IPEM** — balança comercial do cliente final não verificada no prazo.
4. **Retrabalho de certificado em massa** — descoberto erro em rotina usada por 6 meses. Lab precisa reemitir 300-800 certificados.
5. **Técnico perdido na rua / acidente** — técnico não atende telefone, sem rastreio.
6. **Boleto duplicado / cliente final cobrando errado** — financeiro reemite NFS-e por engano.
7. **Signatário sai da empresa** — única pessoa autorizada pra escopo X pede demissão. Receita despenca.
8. **Concorrente ganhou cliente final importante** — descoberto que cliente final foi pra concorrente "porque eles têm portal pra eu baixar meus certificados".
9. **Dono adoeceu / esgotamento** — dono que trabalha 70h/semana entra em burnout.
10. **Visma compra um concorrente** (R-035) — Cali ou Metroex viram parte do Conta Azul/Sankhya. Janela rara de "quem está procurando alternativa agora".
11. **Cliente farma exige certificado + relatório técnico em 3 dias úteis** (NOVO — Aud-6) — lab descobre que prazo apertado quebra fluxo manual; signatário gargalo materializa.
12. **Auditor externo (cliente final farma/automotivo) chega sem aviso pra auditoria de fornecedor** (NOVO — Aud-6) — lab precisa apresentar evidência de rastreabilidade, validação de software, autorização de signatário NA HORA. Status quo trava.
13. **Padrão da casa quebra/vence em ciclo apertado** (NOVO — Aud-6) — padrão referência precisa ir pra calibração externa; lab fica sem capacidade durante 30-60 dias.
14. **Reclamação formal cláusula 7.9 com prazo de resposta** (NOVO — Aud-6) — cliente final formaliza reclamação; lab tem prazo regulatório pra responder e registrar; status quo não tem workflow.
15. **Mudança regulatória entra em vigor com prazo curto** (NOVO — Aud-6) — NIT-DICLA-030 rev. 16, NFS-e cutover 01/09/2026, BCB 493/2025 etc. Lab descobre no dia que a regra mudou.

---

## 12. Síntese: top 10 pontos de dor mais graves (input pra `dores-mapeadas.md`)

> Ordenados por (frequência × gravidade × custo). Cada um vira item em `dores-mapeadas.md`.

| # | Ponto de dor | Frequência | Gravidade | Onde no ciclo | Quem sente |
|---|---|---|---|---|---|
| **D-001** | **Cadastro de cliente final digitado 4-6 vezes em sistemas que não conversam** | Diária | Alta | Comercial → Operacional → Metrológico → Financeiro | Atendente (Letícia) + Financeiro (Cláudia auxiliar) |
| **D-002** | **Esquecimento de lembrar cliente final da próxima calibração** (recalibração perdida 30-50%) | Mensal recorrente | Altíssima (receita perdida) | Pós-metrológico | Dono (Roldão) + Vendedor (Rogério) |
| **D-003** | **Padrão usado com calibração vencida** | Esporádica mas catastrófica | Crítica (NC Cgcre, certificado nulo) | Metrológico — etapa 6.3 | Signatário (Marcos) + Dono (Roldão) |
| **D-004** | **Signatário-gargalo** (pilha de certificados; sai de férias e tudo para) | Semanal | Alta → Crítica | Metrológico — etapa 6.9 | Signatário (Marcos) + Dono (Roldão) |
| **D-005** | **Status de OS perguntado o tempo todo pelo cliente final** (10-30x/dia) | Diária | Média mas drenante | Operacional — etapa 5.8 | Atendente (Letícia) |
| **D-006** | **Roteirização de técnico no escuro** | Diária | Alta | Operacional — etapa 5.3 | Dono (Roldão) + Técnico (Bruno) |
| **D-007** | **Certificado emitido sem campo obrigatório do NIT-DICLA-030** | Variável | **CRÍTICA** (R-018 score 25) | Metrológico — etapas 6.8-6.10 | Signatário (Marcos) + Dono (Roldão) |
| **D-008** | **Conciliação financeira manual** | Semanal | Alta (horas) | Financeiro — etapa 7.4 | Financeiro (Cláudia auxiliar) |
| **D-009** | **Cobrança de inadimplência pessoal e constrangedora** | Mensal | Alta | Financeiro — etapa 7.5-7.6 | Dono (Roldão) + Financeiro (Cláudia auxiliar) |
| **D-010** | **Dono opera no nível diário sem visão estratégica** | Diária | Altíssima (burnout, bloqueio crescimento) | Transversal | Dono (Roldão) |
| **D-011** | **Word/Excel pra certificado e incerteza = NC permanente cláusula 7.11** (NOVO — Aud-7) | Diária (enquanto usar) | **CRÍTICA** (NC ativa) | Metrológico — etapas 6.5 e 6.8 | RT (Sandra) + Signatário (Marcos) |
| **D-012** | **Reclamação formal cláusula 7.9 sem registro estruturado** (NOVO — Aud-6 D-novo A) | Esporádica mas obrigatória | Alta (prazo regulatório) | Transversal — pós-entrega | RT (Sandra) + Dono (Roldão) |
| **D-013** | **Auditoria de cliente farma sem aviso** (NOVO — Aud-6 D-novo B) | 1-3x/ano por cliente farma | Alta (perde cliente se falhar) | Transversal | Dono (Roldão) + RT (Sandra) |
| **D-014** | **Cliente final exige certificado em 3 dias úteis** (NOVO — Aud-6 D-novo C) | Recorrente com cliente farma | Alta (multa contratual + perda cliente) | Metrológico — etapas 6.4 a 6.11 | Signatário (Marcos) + Dono (Roldão) |

**Dores adjacentes que merecem entrar em `dores-mapeadas.md` em segunda leva:**

- D-015: Versão de orçamento errada enviada (Word "v3 FINAL FINAL2").
- D-016: Certificado vazado pra cliente final errado por e-mail (quebra cláusula 4.2).
- D-017: Backup do banco do Cali/Metroex esquecido → perda de histórico.
- D-018: Instrumento extraviado em transportadora sem rastreio (cláusula 7.4).
- D-019: Confusão cliente final entre "calibração" e "verificação INMETRO" (R-040).
- D-020: Documentação 17025 só lembrada em véspera de auditoria.
- D-021: Cutover NFS-e Padrão Nacional 01/09/2026 (R-016).
- D-022: Tabela de preço desatualizada → vendedor erra margem.
- D-023: Foto/anotação de campo ilegível → atendente erra digitação.
- D-024: Sem NPS/satisfação estruturado → empresa só descobre insatisfação quando perde cliente final.

---

## 13. Ferramentas BR críticas mapeadas no status quo (corrigido Aud-6)

| Ferramenta | Onde aparece | Frequência de uso (estimada) |
|---|---|---|
| **WhatsApp Business** | Atendimento, agendamento, envio de certificado, cobrança, comunicação interna | **~100%** das empresas BR |
| **Excel / Google Sheets** | Controle de OS, agenda de técnico, validade de padrão, inadimplência, prospects, cadastro | **~95%** — substituto universal de "sistema" |
| **Word / Google Docs** | Template de orçamento, relatório técnico, certificado em perfil B/C/D | **~80%** |
| **Bling** | NFS-e + financeiro de pequena empresa | **~30-40%** das pequenas |
| **Conta Azul** | NFS-e + financeiro + integração contador | **~25-35%** |
| **Omie** | NFS-e + financeiro + ERP mais robusto | **~10-20%** |
| **Sankhya, TOTVS PME, Tiny, Egestor, Granatum, Nibo** (NOVO) | ERP fiscal pra empresa que cresceu | **~5-10%** empresas maiores |
| **Cali (Cali LAB ou Cali WEB)** | Cálculo de incerteza + certificado | **~50-55%** dos labs (corrigido — antes "50-70%") |
| **Metroex (ForLogic)** | Idem Cali (concorrente) | **~10-15%** (corrigido — antes "15-30%") |
| **Planilha Excel + macros próprias** (NOVO — adicionado como linha própria) | Cálculo de incerteza + certificado em lab B/C que não comprou Cali | **~25-30%** dos labs B/C |
| **GUM Workbench (Metrodata)** (NOVO) | Cálculo de incerteza segundo GUM — alternativa mais defensável que Excel puro | **~5-10%** |
| **SoftExpert Calibration** (NOVO) | Lab grande / corporativo | **~3-5%** |
| **Drive da Google / OneDrive / Dropbox** | Arquivamento de certificados, fotos, orçamentos | **~90%** |
| **Pasta de rede local** | Empresas mais antigas | **~30-40%** |
| **Internet banking PJ — Itaú, BB, Bradesco, Santander, Sicredi** | Boleto, PIX, extrato | **~80%** |
| **Banco Inter PJ, BTG Empresas, Nubank PJ, C6 Bank PJ** (NOVO) | Bancos digitais crescentes em PME | **~20-30%** crescendo |
| **Asaas, Cobre Fácil, Vindi, Iugu, Pagar.me** (NOVO) | Cobrança automatizada / régua de cobrança | **~15-25%** |
| **e-CPF A3 (token Serasa/Certisign/Soluti/Valid/Digital Sign)** (NOVO) | Assinatura digital padrão BR — ICP-Brasil | **~70%** dos labs B-A |
| **GovBR Avançado/Qualificado** (NOVO) | Assinatura digital crescente em MEI/micro | **~30-40%** crescendo |
| **Portal da prefeitura (NFS-e municipal)** | Empresas que não usam Bling/Omie/Conta Azul | **~30%** mais comum em interior |
| **Portais B2B — SAP Ariba, ME Bradesco, Coupa, ComprasNet** (NOVO) | Obrigatório em cliente grande / licitação pública | **~15-25%** (sobe pra ~60% em quem atende cliente grande) |
| **Google Calendar** | Agenda individual de técnico | **~40-60%** |
| **Outlook + Microsoft 365** (NOVO) | Calendário/email integrado em empresa que padroniza | **~30-40%** |
| **Caderno / bloco de papel** | Campo, anotação de medição, recados | **~80%** ainda em paralelo |
| **Câmera do celular** | Foto de instrumento, display, lacre, defeito | **~100%** |

---

## 14. Próximos passos (saída deste documento)

1. **Validar tudo na Onda 1 de entrevistas** (3-5 empresas, foco em quantificar tempo perdido) — ver `entrevistas-onda-1.md` quando existir.
2. **Quantificar D-001 a D-014** com perguntas específicas nas entrevistas (ver §15).
3. **Alimentar `personas-detalhadas.md`** com os papéis identificados — costura já feita (Roldão, Sandra, Letícia, Bruno, Marcos, Cláudia auxiliar, Rogério).
4. **Confirmar `concorrentes.md` §3** observando quais clientes usam Cali vs Metroex vs Planilha+GUM Workbench vs SoftExpert vs nenhum.
5. **Subsidiar priorização do MVP-1 em `faseamento-modulos.md`** — qual ciclo doer mais entra primeiro? Sinalização preliminar: Operacional + Metrológico + cadastro único de cliente final.
6. **Alimentar `validacao-ativa.md`** — usar dores D-001, D-002, D-005, D-010, D-011 como hipóteses pra teste de WTP.

---

## 15. Perguntas-chave pra validar nas entrevistas Onda 1+2

> Cada pergunta tenta quantificar uma dor específica.

1. **"Quantas vezes por mês acontece de um cliente final reclamar de demora na resposta ou pedir status de uma OS?"** (mede D-005)
2. **"Em quantos sistemas diferentes o cadastro do mesmo cliente final vive hoje? Quanto tempo leva pra cadastrar um cliente final novo do zero?"** (mede D-001)
3. **"Quantas recalibrações vocês perdem por trimestre porque o cliente final esqueceu de pedir a próxima ou o concorrente chegou antes?"** (mede D-002)
4. **"Quando o signatário tira férias ou fica doente, quantos dias a emissão de certificados para? Qual o impacto financeiro?"** (mede D-004)
5. **"Quanto tempo o dono passa por dia 'apagando incêndio'?"** (mede D-010)
6. **"Vocês usam Word/Excel/planilha pra certificado ou cálculo de incerteza? Têm dossiê de validação dessa planilha? (especificação + teste + aprovação documentada)"** (mede D-011 — NC cláusula 7.11)
7. **"Quantas reclamações formais (cláusula 7.9) vocês receberam nos últimos 12 meses? Como vocês registram e respondem?"** (mede D-012)
8. **"Quantas vezes nos últimos 12 meses um cliente farma chegou pra auditoria de fornecedor sem aviso prévio? O que doeu mais?"** (mede D-013)
9. **"Cliente farma já pediu certificado em 3 dias úteis? Conseguiram entregar? O que travou?"** (mede D-014)

**Bônus (se houver tempo):**

10. "Qual foi a última NC em auditoria Cgcre? O que custou pra resolver?"
11. "Quanto tempo demora pra fechar o mês contábil hoje?"
12. "Quantas vezes um padrão foi usado com calibração vencida nos últimos 12 meses?"
13. "Vocês emitem atestado de capacidade técnica pros clientes finais usarem em licitação? Quantos por mês? Quanto tempo leva cada um?"
14. "Vocês fecham contrato anual com cliente farma/automotivo? Como gerenciam o cronograma de calibração?"
15. "Vocês participam de licitação pública / pregão eletrônico? Qual portal mais usam?"

---

## 16. Como este documento foi escrito

- Agente leu `dominio-de-negocio.md`, `concorrentes.md`, `riscos.md`, `normas-e-regulacao.md`, `personas-detalhadas.md` e cruzou observações.
- Mapa de ferramentas BR ancorado em pesquisa de mercado já consolidada no `concorrentes.md` + recalibração Aud-6 (Cali 50-55%, Metroex 10-15%, Planilha+GUM Workbench 25-30%, SoftExpert 3-5%).
- Estimativas quantitativas marcadas com `[a confirmar via entrevista]` — devem virar números reais na Onda 1.
- Princípio editorial: descrever DOR, não solução.
- **2ª passagem (17/05/2026):** 13 correções aceitas pelo dono após auditoria cruzada — recalibração da empresa-modelo (5-10 pessoas, R$ 50-150k/mês), custo do status quo recalibrado pra R$ 35-50k/mês, Word/Excel reclassificado como NC permanente cláusula 7.11, 3 fluxos comerciais adicionados (licitação, contrato anual, atestado), 6 sub-etapas metrológicas adicionadas (aceitabilidade, estabilização, ambiente, 2º caminho, 4-olhos, selo, as found/as left), ferramentas faltantes adicionadas (GUM Workbench, SoftExpert, planilha Excel, bancos digitais, plataformas de cobrança, e-CPF A3, GovBR, portais B2B, Outlook), 5 pontos de inflexão adicionados, 3 dores novas no top 10, padronização "cliente final" vs "tenant", costura nominal com personas em cada etapa, nova seção §6.bis de violações regulatórias silenciosas.
- Próxima atualização: após Onda 1 de entrevistas (Roldão + 3-5 outras empresas), refinar números e adicionar quotes diretos.
