# Discovery — Personas detalhadas

> **Artefato Rodada 0 / Batch 2** (agente faz primeira versão; Roldão valida; entrevistas Onda 1+2 refinam).
> **Atualizado:** 2026-05-17 — primeira versão profunda das personas-base do produto Aferê (ERP brasileiro de assistência técnica + laboratório de calibração ISO 17025), com base em `dominio-de-negocio.md`, `concorrentes.md`, `riscos.md` e `normas-e-regulacao.md`.
> **Status de cada persona:** versão de referência inferida do material disponível + experiência reportada de mercado. Toda inferência **não confirmada** está marcada com `[a confirmar via entrevista]`.
> **Pra que serve este doc:** (a) script-base pra entrevistas qualitativas Onda 1 (Roldão) e Onda 2 (5–10 empresas externas); (b) insumo de decisão pra UI/feature do MVP; (c) priorização de jobs-to-be-done em `jobs-to-be-done.md`.

---

## 1. Resumo executivo

**14 personas (13 ativas + 1 quase-persona externa).** Nota: o bloco original era "8 personas (7 ativas + 1 quase-persona externa)"; a v2 (17/05/2026) adiciona 6 personas novas (9-14) cobrindo motorista da UMC, regulador, cliente regulado farma, cliente final low-tech, técnica de campo mulher e dono PME 65+.

| # | Nome / papel | Perfil de empresa dominante | Frase-chave |
|---|---|---|---|
| 1 | **Roldão — Dono / sócio fundador** | A / B / C (PME 5–50 pessoas) | "Eu não programo, mas sei exatamente onde minha empresa sangra dinheiro." |
| 2 | **Sandra — Gerente / RT da Qualidade** | A (obrigatório), B (frequente), C (em formação) | "Se a Cgcre aparece amanhã, eu preciso ter o procedimento, o registro e a evidência — agora, não depois do almoço." |
| 3 | **Letícia — Atendente / SAC** | Todos (A/B/C/D) | "Tudo entra pelo meu WhatsApp e some pelo meu WhatsApp." |
| 4 | **Bruno dos Santos — Técnico de campo** | B / C / D (forte) + A (quando lab faz calibração in loco) | "Eu tô numa balança rodoviária, debaixo de sol, sem internet, e preciso preencher 14 campos num celular." |
| 5 | **Eng. Marcos — Metrologista / signatário técnico** | A (regulado 17025 cl. 6.2), B (sombra do A) | "Meu CPF assina o certificado. Se tiver número errado, é minha cabeça que vai ser cobrada pelo Inmetro." |
| 6 | **Cláudia Nascimento — Financeiro** | Todos (com peso D/C maior) | "Eu fecho o mês olhando pra extrato bancário em uma tela, planilha em outra, Bling em uma terceira, e contando no dedo." |
| 7 | **Rogério — Vendedor / comercial** | B / C / D (forte) + A (orçamento) | "Cliente pergunta preço, eu prometo 'mando hoje à tarde', e mando daqui a 3 dias porque tô esperando o técnico me passar o tempo." |
| 8 | **Quase-persona: João Eng./qualidade — Cliente final do tenant** (responsável pela balança no cliente) | N/A (é o cliente do nosso cliente) | "Eu só quero o PDF do certificado pra mostrar pro auditor da ANVISA quando ele chegar." |
| 9 | **Carlos — Motorista da UMC** ⭐ NOVO 17/05/2026 | A / B (que operam UMC) | "Eu dirijo, o resto é problema do escritório." |
| 10 | **Auditor Cgcre/IPEM — Regulador em campo** | N/A (fiscaliza o tenant) | "Me mostre a evidência — não me conte a história." |
| 11 | **Patrícia — Gerente de Qualidade em cliente farma regulado** | N/A (cliente do tenant, exige IQ/OQ/PQ) | "Sem 21 CFR Part 11 e RDC 658/2022 atendidos, não passa pelo meu fornecedor homologado." |
| 12 | **João-Sênior — Cliente final low-tech (açougue)** | N/A (cliente do tenant) | "Manda no WhatsApp por áudio, fia. Esse negócio de portal eu não mexo." |
| 13 | **Bruna — Técnica de campo (mulher)** | B / C / D + A in loco | "Refinaria não tem vestiário feminino. Eu calibro com o EPI emprestado." |
| 14 | **Roldão Sênior 65+ — Dono PME veterano** | A / B / C (5–50 pessoas) | "Letra grande, botão grande, e me explica devagar. Eu compro." |

> **Nota de diversidade (Aud-2):** "dona Roldina existe" — empresa fundada por engenheira química que migrou de cliente final a empresária do setor é caso real (RS, MG, SP); persona Roldão é gender-neutral. Distribuição racial e regional: forte presença NE industrial (Suape/PE, Camaçari/BA, Mossoró/RN) e N (Manaus/ZFM, Belém) em personas operacionais.

---

## 2. Personas detalhadas

---

## Persona 1 — Roldão (Dono / sócio fundador de PME de calibração)

> **Contexto:** dono e sócio-fundador de empresa BR de assistência técnica + calibração, capital nacional, 5–50 funcionários, sob mesmo CNPJ executando manutenção + emissão de certificado ISO 17025 (ou rastreável). É o **founder is customer** do produto Aferê — referência central do Discovery, mas perigosa de generalizar (R-001).

### Identidade
- **Nome fictício:** Roldão Batista
- **Idade típica:** 45–55 anos
- **Formação típica:** técnica industrial (Senai/Cefet) ou superior incompleto em engenharia/administração; conhecimento de chão de fábrica somado a curso livre de gestão. **Não programa.**
- **Anos de experiência:** 15–30 anos no setor (geralmente começou como técnico, depois abriu empresa)
- **Remuneração típica BR:** pró-labore **R$ 5k–10k em PME 5–15 funcionários (perfil C/D)**; **R$ 12k–25k só em PME 30–50 (perfil A/B)** + distribuição de lucros variável. `[a confirmar via entrevista]`
- **Localização típica:** interior industrial (Caxias do Sul, Joinville, Campinas, Sorocaba, Sertãozinho, Volta Redonda, Recife, Curitiba) ou periferia metropolitana (ABC paulista, Grande BH, Grande POA). Capital pura é minoria.

### Contexto de trabalho
- **Onde trabalha fisicamente:** sala administrativa anexa ao laboratório/oficina. Vê a operação pela janela. Em empresa muito pequena, mesa fica dentro do próprio laboratório.
- **Horário típico:** comercial estendido (7h–19h). Plantão emocional 24/7 — atende WhatsApp de cliente no fim de semana.
- **Reporta a:** sócios (quando há) + esposa/família (na prática, conselho informal). Não tem chefe.
- **Equipe sob ele:** entre 5 e 50 pessoas — gerente operacional, atendente, 2–8 técnicos, metrologista, financeiro, comercial. Empresa pequena: papéis acumulados (a mesma pessoa é atendente + financeiro).
- **Perfil de empresa:** opera em **A**, **B** ou **C** (não em D — empresa D dificilmente é o ICP do Aferê porque cabe num ERP genérico de OS).

### O que ele quer
- **Faturar de forma previsível** — sair da montanha-russa de mês bom / mês ruim por falta de funil organizado.
- **Não perder acreditação RBC** (se perfil A) ou **conquistar acreditação** (se perfil C migrando para A).
- **Reduzir dependência operacional dele mesmo** — empresa rodar sem ele estar olhando o tempo todo (bus factor — R-029).
- **Conhecer custo real de cada OS** — hoje só sabe o faturado, não sabe a margem por instrumento/cliente.
- **Profissionalizar a imagem da empresa** com cliente — orçamento bonito, certificado padronizado, portal com cara de software sério, não Word de 2003.

### JTBDs principais
JTBD-001 (saber se mês vai fechar no azul), JTBD-004 (não depender de uma pessoa), JTBD-006 (histórico do negócio na mão), JTBD-013 (visão consolidada sem 5 telas), JTBD-039 (saber fluxo 30 dias).

### Dores principais
D-001 (cadastro digitado 4-6x), D-002 (recalibração esquecida), D-010 (dono sem visão estratégica).

### O que o deixa louco
- "Mando o orçamento por WhatsApp e o cliente esquece. Não sei quem viu, quem aprovou, quem ficou em dúvida."
- "Tenho 3 sistemas: Bling pra NFS-e, Cali pro certificado, planilha pra controle de OS. Cada um fala uma língua, e eu digito o mesmo número 4 vezes."
- "Tô em auditoria Cgcre e o auditor pede 'me mostre o histórico de calibração desse padrão' — vou na planilha, na pasta de PDFs, no e-mail e em 2 cadernos físicos. Ele me olha com cara de pena." (R-018 = risco 018: certificado sem cadeia de rastreabilidade rejeitado por Cgcre)
- "Técnico volta do campo com a OS no celular dele, em foto, e essa foto pode sumir."
- "Não consigo tirar férias de 7 dias. Algo trava sem mim."
- "Cliente cobra: 'cadê o certificado da calibração de janeiro?'. Eu não acho. Mando refazer? Cobro de novo? Quem comeu essa OS?"

### Dia típico
- **Manhã (7h–12h):** chega, olha o WhatsApp da empresa (40+ mensagens da madrugada), responde cliente irritado, decide com gerente operacional a agenda de técnico do dia, atende fornecedor que veio entregar peça, aprova pagamento de boleto que o financeiro mandou no WhatsApp pessoal dele.
- **Tarde (13h–18h):** entra no Cali pra ver se o metrologista terminou os certificados pendentes, abre o Bling pra emitir NFS-e da OS fechada na sexta, atende ligação de prospect que veio via indicação, vai até a oficina ver técnico que está com dúvida sobre instrumento novo, manda orçamento por WhatsApp.
- **Fim do dia (18h–20h):** "fecha" o caixa olhando extrato bancário no app do banco contra planilha que o financeiro mandou, anota no caderno físico o que precisa cobrar amanhã, responde mais 15 WhatsApps, vai embora.
- **Noite/fim de semana:** WhatsApp de cliente urgente; pensa em "como eu organizo essa bagunça".

### Ferramentas que usa HOJE
- **WhatsApp pessoal + Business** — canal #1 de tudo (cliente, fornecedor, técnico, sócio): **~3h/dia**
- **Bling ou Conta Azul** — NFS-e, contas a pagar/receber básico: **~1h/dia**
- **Cali LAB ou Calibre.Software ou planilha Excel** — gestão de calibração (se perfil A/B): **~30min/dia** (mais consumo do que produção — quem entra mesmo é o metrologista)
- **Planilha Excel** — controle de OS, controle de padrão, agenda de técnico, follow-up de proposta: **~1h/dia**
- **E-mail (Gmail)** — envio de certificado em PDF anexo, contato com cliente formal: **~30min/dia**
- **Google Drive ou pasta de rede** — arquivo de certificado, contrato, foto de OS: **acesso aleatório**
- **Caderno físico ou bloco** — anotações pessoais, "coisas pra fazer": **constante**
- **App do banco (Sicredi/Santander/Itaú PJ)** — checar saldo, aprovar PIX, baixar OFX: **~3x/dia**

### O que NÃO funciona hoje (gap específico)
- **Cali não fala com Bling** — copia-cola entre os dois (R-018 + risco operacional).

- **WhatsApp não tem histórico estruturado de chamado** — atendente abre nova conversa do zero a cada vez; histórico do cliente está espalhado em 5 conversas paralelas.
- **Bling não tem campo "OS de origem"** numa NFS-e — relação OS↔NFS-e fica no campo "descrição" e no cérebro do Roldão.
- **Planilha de padrão não alerta vencimento** — Roldão descobre que padrão venceu quando metrologista pergunta "posso usar o paquímetro X?".
- **Nenhuma das ferramentas mostra DRE simples por cliente / por tipo de OS** — só vê faturamento total no Bling.
- **Portal do cliente do Cali existe mas é feio e cliente não usa** — cliente prefere pedir o PDF por WhatsApp de qualquer jeito.

### O que daria sucesso visível pra essa persona
- "Quando eu abrir o sistema de manhã, eu vejo numa tela: quantos chamados entraram nas últimas 24h, quantas OS estão atrasadas, quanto eu tenho pra receber esse mês, e qual é o próximo padrão a vencer."
- "Eu tiro 5 dias de férias e a empresa funciona — porque o gerente operacional vê o mesmo painel e age sem me ligar."
- "Auditor Cgcre pede histórico, eu clico 2 vezes e mostro tudo encadeado: instrumento → padrão usado → certificado-pai → metrologista → data → assinatura."

### O que vai resistir a aceitar
- "Outro sistema pra aprender? Já cansei. Bling foi caro de implantar."
- "Vou perder os 8 anos de histórico que tem na planilha."
- "Meu metrologista vai resistir — ele AMA o Cali e não quer mexer."
- "E se der pau no meio do mês e eu não conseguir emitir nota?"
- "Quanto custa? Se for mais de R$ 500/mês eu já não topo." `[a confirmar — pode estar subestimado]`

### Frase-chave
> "Eu não programo, mas sei exatamente onde minha empresa sangra dinheiro. E é nas brechas entre os sistemas."

### Variações por perfil de empresa
- **Perfil A (acreditado RBC):** Roldão tem RT contratado separado dele; obsessão com auditoria Cgcre; investiu pesado em padrão RBC; ticket médio mais alto; vê o sistema como **risco regulatório** se quebrar.
- **Perfil B (rastreável):** Roldão acumula papel de "responsável pela qualidade"; quer migrar pra A em 1–3 anos; vê o sistema como **escada de profissionalização**.
- **Perfil C (em preparação):** Roldão mistura tudo; documentação ainda em planilha; depende de consultor externo; vê o sistema como **trilha didática** ("o software me ensina o que falta").
- **Perfil D (calibração comercial):** raríssimo no ICP; se aparecer, Roldão quer "ERP de OS simples", não 17025.

### Sinais pra entrevista qualitativa (Onda 1)
- "Me conta como foi sua última semana — só os incêndios."
- "Se você desaparecer 7 dias, o que para?"
- "Qual foi a última auditoria Cgcre? O que doeu mais?"
- "Quanto custa pra você emitir 1 certificado, em horas + dinheiro?"
- "Quanto você pagaria por mês por um sistema que resolvesse essas dores?" (validar willingness to pay — `validacao-ativa.md`)
- "Se eu te der 1 botão mágico pra resolver UMA coisa, qual é?"

---

## Persona 2 — Sandra (Gerente operacional / Responsável Técnica da Qualidade)

> **Contexto:** em perfil A é **exigida pela ISO/IEC 17025 cl. 6.2** (autorizada pra responder por escopo). Em perfil B/C, pode ser uma pessoa dedicada OU o próprio dono acumulando o papel. Em perfil D, geralmente não existe. Esta persona é descrita como **dedicada** (não acumulada).

### Identidade
- **Nome fictício:** Sandra Oliveira
- **Idade típica:** 35–50 anos
- **Formação típica:** caminho dominante é **engenharia química/mecânica/elétrica + pós-graduação em metrologia/qualidade**. Formação técnica BR concentrada em: **IFRJ Volta Redonda, INMETRO/IFF, colégio estadual do PI, EaD nacional IFRJ, cursos livres SBM/CECT**. Tecnólogo em metrologia puro é raro.
- **Anos de experiência:** 8–20 anos, sendo pelo menos 3–5 em laboratório acreditado
- **Remuneração típica BR:** R$ 7k–14k/mês CLT em PME; R$ 12k–20k em laboratório acreditado de porte médio. `[a confirmar]`
- **Localização típica:** mesmo eixo industrial do Roldão (interior SP/RS/SC/MG/PR)

### Contexto de trabalho
- **Onde trabalha fisicamente:** sala da Qualidade (dedicada em perfil A) ou compartilhada com a operação. Tem mesa, computador, segunda tela; muitas vezes uma pasta-arquivo física com procedimentos impressos pra auditoria.
- **Horário típico:** 8h–18h comercial estrito. Hora extra rara.
- **Reporta a:** dono / diretoria; em perfil A formal **e ao Cgcre como interlocutora técnica**.
- **Equipe:** geralmente 0 subordinados diretos (em PME) — ela é "exército de uma mulher só". Em lab acreditado maior, pode coordenar 2–3 metrologistas + auxiliares.
- **Perfil dominante:** **A (obrigatório)**. Aparece em B (preparação pra A) e C (formação). Em D, raramente.

### O que ela quer
- **Manter a acreditação RBC vigente** — nenhuma NC maior em auditoria Cgcre.
- **Garantir que TODO certificado emitido tenha cadeia de rastreabilidade completa** (INV-002 — regra fixa: emissão exige cadeia completa / NIT-DICLA-030 rev. 15 item 8.2.6).
- **Manter sistema de gestão da qualidade vivo** (cl. 8 da 17025): procedimentos atualizados, NC tratadas, auditorias internas feitas.
- **Treinar e autorizar pessoal por escopo** (cl. 6.2 + INV-003) com evidência documentada.
- **Implementar melhoria contínua** (cl. 8.6) — analisar feedback, indicador de tendência, ação corretiva eficaz.

### JTBDs principais
JTBD-002 (não tomar multa nem perder acreditação), JTBD-028 (rastreabilidade automática), JTBD-029 (NC pendente bloqueia emissão), JTBD-032 (gestão de padrões), JTBD-033 (treinar técnico júnior).

### Dores principais
D-003 (padrão vencido sem perceber), D-007 (certificado sem campo NIT-DICLA-030), D-016 (documentação 17025 só na véspera).

### O que a deixa louca
- "Eu tenho 47 procedimentos em Word, numa pasta de rede, com versão controlada no nome do arquivo (Proc_17_v3.2_FINAL_REVISADO.docx). É medieval."
- "Pra mostrar pro auditor a matriz competência × signatário × validade, eu monto uma planilha NA HORA, do zero, na frente dele. Em 2026."
- "Workflow de NC é WhatsApp + e-mail + planilha. Quando NC é fechada, eu apago a entrada. Aí o auditor pergunta 'me mostre evidência da ação corretiva' e eu suo frio."
- "Carta de controle de padrão eu faço no Excel, manualmente, copia-cola dos certificados de calibração-pai. Já errei duas vezes e quase emiti certificado com padrão deriva-fora."
- "Quando dono compra padrão novo, ele esquece de me avisar e o instrumento entra em OS sem eu ter cadastrado a rastreabilidade. Tenho que correr atrás."
- "Cali resolve a parte do certificado mas não me dá um dashboard 'estou pronta pra auditoria?'."

### Dia típico
- **Manhã (8h–12h):** revisa fila de certificados pendentes de assinatura técnica (delega ao metrologista se há mais de 1); confere se NC abertas têm prazo respeitado; responde dúvida de técnico sobre procedimento; abre planilha de validade de padrão pra ver se algo vence essa semana.
- **Tarde (13h–17h):** reunião com dono sobre indicadores; redige nova versão de procedimento (Word); cadastra novo signatário (preenche formulário, anexa diploma, treinamento, autoriza); aprova mudança de método; lê norma nova publicada pela Cgcre.
- **Fim do dia (17h–18h):** revisa as 3–5 últimas calibrações do dia (amostragem); fecha checklist de qualidade do dia.
- **Pico:** semana antes de auditoria Cgcre — fim de semana incluído.

### Ferramentas que usa HOJE
- **Word + Excel + pasta de rede** — gestão documental do sistema (procedimentos, formulários, registros): **~2h/dia**
- **Cali ou Metroex** (se lab dela usa) — só consome relatório, não gera diretamente: **~30min/dia**
- **E-mail corporativo** — comunicação formal com Cgcre, fornecedor de padrão, cliente regulado (farma): **~1h/dia**
- **Planilha Excel de carta de controle** — análise estatística de tendência de padrão: **~30min/dia**, picos semanais
- **WhatsApp** — comunicação informal interna: **~1h/dia**
- **Portal Sidoq Cgcre** — consulta de norma vigente: **~1x/semana**

### O que NÃO funciona hoje (gap específico)
- **Nenhum software no mercado BR junta gestão da qualidade 17025 + execução de calibração + portal de auditoria** num lugar só — Cali resolve calibração; Qualiex/Portal ISO resolvem qualidade; nada faz os dois sem integração manual.
- **Cali não tem matriz competência × signatário** estruturada (geralmente é planilha lateral).
- **Não há alerta automático "seu padrão vence em 30 dias"** — Sandra usa lembrete do Outlook ou planilha pintada de amarelo.
- **NC aberta no Cali não trava emissão de certificado do instrumento envolvido** — Sandra depende da disciplina humana (e às vezes falha — INV-012).
- **Nenhum produto oferece "modo auditoria"** (filtrar tudo por um período/auditor com 1 clique).

### O que daria sucesso visível pra essa persona
- "Quando o auditor Cgcre chegar, eu projeto na TV uma única tela: certificados emitidos no período, cadeia completa de cada um, validade dos padrões usados, NC abertas/fechadas no período, signatários autorizados na data."
- "Padrão vencendo dispara alerta + bloqueia automaticamente OS nova com aquele padrão (INV-011)."
- "Procedimento revisado dispara workflow de aprovação + treinamento + autorização — versão antiga vira read-only com selo 'OBSOLETO'."

### O que vai resistir a aceitar
- "Já sofri 2 implantações de software de qualidade. Levou 18 meses e ainda usamos planilha pra metade das coisas."
- "Cgcre auditou meu Cali em 2024 e aceitou. Se eu trocar, vai gerar NC na próxima auditoria?"
- "O sistema novo é validado conforme cláusula 7.11? Tem documento de validação que eu posso apresentar?"
- "Quem é o responsável técnico do software (vendor)? Tem RT registrado?" (preocupação de auditoria sobre o vendor — R-039)

### Frase-chave
> "Se a Cgcre aparece amanhã, eu preciso ter o procedimento, o registro e a evidência — agora, não depois do almoço."

### Variações por perfil de empresa
- **Perfil A:** existe como cargo dedicado; salário e autoridade altos; é figura **decisora** na compra do software (veto técnico).
- **Perfil B:** muitas vezes acumulada pelo dono ou por engenheiro júnior; menos autoridade; usa o software como apoio pra "fingir maturidade A" antes de ter.
- **Perfil C:** quase sempre dono ou consultor externo terceirizado; software vira **trilha de ensino** (cada feature explica o porquê normativo).
- **Perfil D:** **não existe.** Persona inativa.

### Sinais pra entrevista qualitativa
- "Me leva pelo seu processo de auditoria interna do ano passado — passo a passo."
- "Quantas NC você abriu nos últimos 12 meses? Quantas fechou no prazo?"
- "Última auditoria Cgcre — qual foi a observação mais incômoda?"
- "Você confia mais na Cali ou na sua planilha?"
- "Se eu falar que o software bloqueia emissão sem cadeia completa — você acha ótimo ou autoritário demais?" (testar receptividade aos invariantes)

---

## Persona 3 — Letícia (Atendente / SAC)

> **Contexto:** primeira ponta da operação. Recebe chamado por WhatsApp, telefone, e-mail; abre OS; agenda; faz follow-up. Em empresa pequena (perfil B/C/D) acumula com financeiro ou comercial; em perfil A pode ser dedicada. **Persona de uso mais frequente do sistema** — vai abrir o app 50+ vezes por dia.

### Identidade
- **Nome fictício:** Letícia Souza
- **Idade típica:** 22–35 anos
- **Formação típica:** ensino médio completo + curso técnico (administração, secretariado) ou superior em andamento (administração, comunicação). Eventualmente já trabalhou em call center.
- **Anos de experiência:** 2–8 anos
- **Remuneração típica BR:** **R$ 1.910–2.500/mês CLT (CCT regional); até R$ 2.800 com acúmulo SAC/admin em PME maior** (CBO 422105) + VR/VT. `[a confirmar]`
- **Localização típica:** sempre na sede da empresa, capital ou interior

### Contexto de trabalho
- **Onde trabalha fisicamente:** recepção / sala administrativa pequena. 1 monitor, 1 telefone fixo, 1 celular corporativo, fone de ouvido.
- **Horário típico:** comercial estrito (8h–17h ou 9h–18h); 1h de almoço.
- **Reporta a:** gerente operacional ou diretamente ao dono.
- **Equipe:** geralmente sozinha (PME pequena) ou em equipe de 2–3 (PME maior).
- **Perfil:** **todos os perfis (A/B/C/D)** — papel universal. Em D pode acumular com financeiro.

### O que ela quer
- **Atender rápido** — cliente não esperar mais de 2 minutos por resposta no WhatsApp.
- **Não esquecer follow-up** — chamado sem retorno = cliente perdido.
- **Abrir OS sem erro de digitação** — endereço errado, instrumento errado, técnico errado custam horas de retrabalho.
- **Saber onde está cada cliente no funil** (orçamento enviado? aprovado? OS aberta? técnico foi? certificado emitido? cobrança feita?) sem perguntar pra ninguém.
- **Encerrar o dia com inbox zero** (WhatsApp + e-mail respondidos).

### JTBDs principais
JTBD-015 (identificar cliente em 5s), JTBD-016 (abrir chamado em 1min), JTBD-017 (responder "cadê meu certificado"), JTBD-019 (enviar orçamento na hora), JTBD-020 (não copiar info 3 vezes).

### Dores principais
D-001 (cadastro digitado 4-6x), D-005 (cliente pergunta status), D-019 (foto de campo ilegível).

### O que a deixa louca
- "Recebo 200+ mensagens de WhatsApp por dia. Algumas são cliente, algumas são fornecedor, algumas são família. Cliente novo me manda foto da balança quebrada — eu tenho que copiar, colar em e-mail, anexar na planilha de chamado, abrir o número de OS no Excel."
- "Cliente liga e fala 'soltei a balança da minha açougue mês passado'. Eu pergunto 'qual sua empresa?' — abro 3 sistemas pra achar. Cliente reclama 'mas eu sou cliente há 5 anos'."
- "Técnico volta do campo, me manda foto da OS preenchida à mão. Tenho que digitar na planilha. Letra ruim, digito errado, gera retrabalho."
- "Bling pra abrir nota é separado do meu Excel de OS. Eu digito o mesmo cliente em 3 lugares."
- "Não sei se o cliente já recebeu o orçamento que mandei ontem. Não tem confirmação."
- "Cliente cobra status, eu não sei onde está a OS — pergunto pro técnico no WhatsApp, espero 2h."

### Dia típico
- **Manhã (8h–12h):** chega, abre WhatsApp Business (60 mensagens da noite), Outlook, planilha de OS, Bling. Triagem do WhatsApp: cliente novo → coleta info → abre chamado; cliente existente → procura histórico; cobrança → encaminha financeiro. Atende telefone (~10 chamadas).
- **Tarde (13h–17h):** segue WhatsApp + telefone + e-mail; envia orçamento que comercial preparou; agenda técnico junto com gerente operacional; preenche planilha de OS conforme técnico vai reportando; emite alguns boletos no Bling.
- **Fim do dia (17h–18h):** organiza pendências do dia, lista o que ficou pra amanhã (caderno físico), avisa gerente operacional do que travou.

### Ferramentas que usa HOJE
- **WhatsApp Business** — canal #1: **~4h/dia ativos**
- **Telefone fixo** — clientes mais velhos preferem: **~1h/dia**
- **Outlook / Gmail** — cliente formal, envio de PDF de certificado: **~1h/dia**
- **Planilha Excel de OS** — controle interno: **~2h/dia**
- **Bling ou ContaAzul** — abrir cliente novo, emitir 1–2 boletos: **~1h/dia**
- **Caderno físico** — pendências pessoais, "ligar pra fulano às 14h": **constante**

### O que NÃO funciona hoje (gap específico)
- **WhatsApp Business não integra com nenhum dos outros sistemas** — toda passagem é copia-cola manual (R-027 fica perigoso se integrar via webhook sem sanitização).
- **Bling não tem campo "data prevista de entrega de certificado"** — Letícia anota na planilha.
- **Planilha trava em cliente com 800+ linhas de histórico** — Letícia abre só "filtros do mês".
- **Cliente novo no WhatsApp precisa contar a história toda de novo** — não há identificação automática (Bling tem cadastro, WhatsApp não puxa).
- **Não há SLA visível** — Letícia descobre que orçamento envelheceu 7 dias quando cliente liga reclamando.

### O que daria sucesso visível pra essa persona
- "Cliente me manda WhatsApp; o sistema reconhece o número, abre o histórico dele, sugere 'parece chamado novo da balança X — confirmar?'."
- "Eu abro 1 tela e vejo: 'estes 12 clientes estão esperando resposta há mais de 24h'."
- "Cliente cobra status, eu vejo na hora: 'técnico Bruno saiu agora há 30 min, ETA 14h30'."
- "Boleto sai da OS aprovada com 2 cliques — não digito o cliente de novo."

### O que vai resistir a aceitar
- "Vou ter que largar meu WhatsApp Business? Cliente já me conhece nesse número."
- "Vai ser MAIS coisa pra preencher? Não tenho tempo."
- "E se travar no meio do atendimento — o que eu falo pro cliente?"
- "Tem que ser fácil. Eu não vou em treinamento de 8h."

### Frase-chave
> "Tudo entra pelo meu WhatsApp e some pelo meu WhatsApp. Eu sou o sistema."

### Variações por perfil de empresa
- **Perfil A:** mais clientes formais (farma, automotivo); mais e-mail e menos WhatsApp; usa SLA contratualmente; menos tolerância a erro.
- **Perfil B:** mistura de cliente formal e informal; WhatsApp dominante; SLA implícito.
- **Perfil C/D:** WhatsApp é 90%; SLA inexistente; alta rotatividade da persona (sai por R$ 200/mês a mais).

### Sinais pra entrevista qualitativa
- "Me mostra seu WhatsApp Business AGORA — quantas conversas abertas?"
- "Qual foi a última cagada (cliente errado, instrumento errado, técnico no endereço errado)? O que aconteceu depois?"
- "Quantos chamados você abre por dia em média? Quantos viram OS? Quantos morrem?"
- "Que ferramenta você AMA hoje? Que ferramenta você ODEIA?"
- "Se você pudesse só copiar/colar de uma janela pra outra, qual seria?"

---

## Persona 4 — Bruno dos Santos (Técnico de campo)

> **Contexto:** vai ao cliente executar OS (manutenção e/ou calibração in loco). Trabalha em **balança rodoviária em pátio de usina**, **balança comercial em açougue**, **manômetro em refinaria**, **balança industrial em frigorífico**. **Mobile-first obrigatório** (ADR-0003). Conexão de internet variável (4G ruim em mina, zona rural, dentro de galpão metálico).

### Identidade
- **Nome fictício:** Bruno dos Santos
- **Idade típica:** 25–45 anos
- **Formação típica:** técnico em eletrônica, mecânica, mecatrônica ou metrologia (Senai/Cefet). Muito raramente superior — quase sempre formação técnica + experiência prática.
- **Anos de experiência:** 3–15 anos
- **Remuneração típica BR:** R$ 2.500–5.500/mês CLT + diária de viagem (R$ 50–150/dia) + comissão por OS executada em alguns lugares. Técnico sênior em lab acreditado: R$ 5k–8k. `[a confirmar]`
- **Localização típica:** mesma região da empresa, mas roda o estado todo. Em empresa grande, técnico viaja pra fora do estado.

### Contexto de trabalho
- **Onde trabalha fisicamente:** **na rua / cliente / chão de fábrica / pátio de pesagem / refinaria / mina**. Raríssimo no laboratório (só pra calibrações de bancada feitas internamente).
- **Horário típico:** 7h–17h, mas viaja de madrugada se cliente é longe. Plantão (24/7) em contratos grandes (refinaria, frigorífico que para a linha).
- **Reporta a:** gerente operacional / supervisor de campo (em empresa maior).
- **Equipe:** dupla com auxiliar, ou solo.
- **Perfil dominante:** **B/C/D** (forte) + **A** quando o lab faz calibração in loco.

### O que ele quer
- **Fechar OS no mesmo dia da visita** — não voltar pra empresa com OS aberta.
- **Coletar evidência clara** (foto antes/depois, leitura, número de série) pra metrologista poder emitir certificado depois.
- **Não preencher papel** — odeia preencher OS em papel carbono.
- **Saber qual é a próxima OS sem ligar pro gerente** — pega celular, vê a agenda.
- **Receber sua diária / comissão sem disputa** — registro claro do que executou.

### JTBDs principais
JTBD-021 (saber tudo da próxima OS), JTBD-022 (executar sem internet), JTBD-023 (coletar leitura pelo celular), JTBD-024 (assinatura no celular), JTBD-025 (não voltar pra "encerrar OS").

### Dores principais
D-005 (status perguntado o tempo todo), D-006 (roteirização no escuro), D-019 (foto/anotação ilegível).

### O que o deixa louco
- "Tô numa balança rodoviária no pátio de uma usina, debaixo de sol, 39°C, óculos embaçado, sem 4G. O sistema da empresa abre só com internet."
- "OS chegou no meu WhatsApp como foto de Excel — não tenho onde marcar o que executei. Faço no caderno e digito depois (perdendo info)."
- "Cliente assina na minha prancheta com caneta — assinatura some no carbono. Aí auditor cobra evidência de aceite e a gente não tem."
- "Levei 14 fotos da balança — onde guardo? Mando no WhatsApp da Letícia? Ela perde."
- "Fim do dia, dirijo 2h pra voltar, chego morto, ainda tenho que 'fechar OS' no Excel. Faço bagunçado, gera retrabalho amanhã."
- "Gerente cobra: 'fez calibração com qual padrão?'. Eu não anotei. Tenho que voltar no cliente."
- "Minha diária do mês saiu R$ 200 a menos porque ninguém achou a OS de uma viagem que fiz."

### Dia típico
- **Madrugada/manhã cedo (5h–7h):** sai de casa, dirige até cliente (30 min a 4h).
- **Manhã (7h30–12h):** chega, se apresenta, vai ao instrumento, executa serviço (manutenção/calibração), fotografa, anota leitura, pede cliente assinar OS de aceite.
- **Almoço:** marmita ou restaurante de beira de estrada (45 min).
- **Tarde (13h–17h):** segunda OS do dia (se região permite); senão, dirige de volta.
- **Fim do dia (17h–20h):** chega na empresa, "fecha OS" no Excel (ou manda foto pra Letícia), entrega papelada física se houver, vai embora.

### Ferramentas que usa HOJE
- **Caderno físico + prancheta com OS impressa** — preenchimento em **70-80% das visitas** (instrumento principal de coleta): **constante**
- **Celular pessoal (Android, R$ 800–1.500)** — WhatsApp, foto, ligação (uso universal mas pra foto/comunicação, não pra coleta estruturada): **constante** (8h+ tela ligada)
- **Tablet corporativo** — **5-10% das visitas apenas** (não é padrão; só em lab maior ou contrato grande)
- **WhatsApp** — comunicação com Letícia, gerente, cliente: **~2h/dia**
- **Câmera do celular** — foto do antes/depois, número de série, plaqueta INMETRO: **constante**
- **Aplicativo do banco** — receber diária via PIX: **~1x/dia**
- **App de mapa (Waze/Google Maps)** — endereço do cliente: **~2x/dia**
- **Calibrador documentador** (em perfil A com cliente sofisticado — Beamex, Fluke, Presys) — registro automático de calibração: **~30min por OS** quando aplicável

### O que NÃO funciona hoje (gap específico)
- **Nenhum dos concorrentes BR (Cali, Metroex, Calibre) tem app mobile real de campo offline-first** — só portal web (Cali WEB é portal de cliente, não de técnico).
- **Cali WEB precisa de internet** — Bruno em mina/refinaria fica sem.
- **WhatsApp como canal de fechamento de OS é fonte de perda** (foto some, mensagem se mistura).
- **Cliente assinar em papel** = evidência fraca pra auditoria (Sandra reclama).
- **Bruno não vê quanto vai receber de diária no fim do mês** — só descobre no holerite.

### O que daria sucesso visível pra essa persona
- "Abro app no celular, vejo as 3 OS de hoje com endereço, instrumento, cliente, último histórico."
- "Executo OS offline, fotografo, cliente assina na tela, sincroniza quando tiver internet."
- "Fim do dia, OS fechada automática. Não preciso 'lançar no sistema' chegando em casa."
- "Vejo minha diária do mês acumulada em tempo real."

### O que vai resistir a aceitar
- "Meu celular é simples — vai funcionar?"
- "Cliente vai aceitar assinar em tela? Tem cliente velho que não confia."
- "Se travar no meio do cliente, o que faço?"
- "Vai ter geolocalização? Não quero meu chefe sabendo onde eu paro pra almoçar."

### Frase-chave
> "Eu tô numa balança rodoviária, debaixo de sol, sem internet, e preciso preencher 14 campos num celular. Faça funcionar OFFLINE ou esquece."

### Variações por perfil de empresa
- **Perfil A:** técnico mais qualificado; calibrador documentador conectado; pode ser também o signatário (raro) ou pré-aprovador; usa procedimento escrito por OS.
- **Perfil B:** técnico médio; combina manutenção + calibração na mesma OS; mais pressão de produtividade.
- **Perfil C/D:** técnico generalista; faz tudo (mecânica + elétrica + ajuste + "calibração comercial"); menos formação; alta rotatividade.

### Sinais pra entrevista qualitativa
- "Posso ver seu celular agora? Como você usa o WhatsApp pra trabalho?"
- "Última OS de campo: me conta minuto a minuto."
- "Quantas vezes por mês você fica sem 4G no cliente?"
- "Se eu te dou um celular novo da empresa, você usa pra trabalho?"
- "Cliente assinar com o dedo na tela: você acha que funciona?"

---

## Persona 5 — Eng. Marcos (Metrologista / signatário técnico)

> **Contexto:** assina o certificado de calibração; em perfil A é **regulado pela ISO/IEC 17025 cl. 6.2 + NIT-DICLA-016 + DOQ-CGCRE-019** (autorização documentada por escopo, vigência, evidência de competência — NIT-DICLA-021 trata de incerteza, não de signatário). Em perfil B/C pode ser informal mas tecnicamente competente. Persona com **maior peso técnico e ego profissional** — defendê-lo cuida do produto.

### Identidade
- **Nome fictício:** Eng. Marcos Cardoso
- **Idade típica:** 35–55 anos
- **Formação típica:** engenharia (mecânica, elétrica, química, controle e automação, materiais) ou física. Frequentemente com pós em metrologia (curso INMETRO ou Cefet-MG). Em lab pequeno pode ser técnico sênior com 20+ anos de chão.
- **Anos de experiência:** 10–30 anos, sendo **mínimo 3 em escopo específico** pra ser autorizado RBC.
- **Remuneração típica BR:** **R$ 6.500–12.000/mês CLT (PME); até R$ 15k+ em lab acreditado médio-grande** (fonte: CBO 2012-10 + CAGED 2026). Em consultoria, R$ 200–400/h. `[a confirmar]`
- **Localização típica:** mesmo eixo industrial. Pode trabalhar remoto parcialmente em PJ.

### Contexto de trabalho
- **Onde trabalha fisicamente:** **laboratório metrológico** com bancada, padrões, ambiente controlado (T/UR). Mesa com computador pra cálculo de incerteza e emissão de certificado.
- **Horário típico:** comercial 8h–17h; calibração tem ritmo próprio (não dá pra apressar — temperatura precisa estabilizar).
- **Reporta a:** RT da Qualidade (Sandra) / dono.
- **Equipe:** geralmente sozinho ou com 1 auxiliar de laboratório.
- **Perfil dominante:** **A (regulado)** e **B (sombra)**. Em C/D existe metrologista informal.

### O que ele quer
- **Emitir certificado tecnicamente impecável** — número certo, incerteza correta, cadeia rastreada.
- **Proteger sua autorização como signatário** — não assinar nada fora de escopo (risco profissional + regulatório).
- **Reduzir tempo de cálculo de incerteza** — hoje gasta 30–60 min por instrumento mais complexo na planilha GUM.
- **Garantir padrão sempre válido** — não usar padrão com calibração vencida (INV-011 — regra fixa: padrão vencido bloqueia emissão).
- **Documentar método com clareza** — evitar ambiguidade na próxima auditoria.

### JTBDs principais
JTBD-027 (cálculo incerteza embutido), JTBD-028 (rastreabilidade automática), JTBD-029 (NC pendente bloqueia), JTBD-030 (assinar digitalmente sem ritual), JTBD-031 (provar validação software).

### Dores principais
D-003 (padrão com calibração vencida), D-004 (signatário-gargalo), D-007 (cadeia incompleta no certificado).

### O que o deixa louco
- "Cali calcula incerteza, mas pra instrumento atípico eu tenho que sair pra planilha minha. Aí dou copia-cola do número, o que é fonte de erro."
- "Cliente quer 'certificado pra ontem'. Eu não posso correr — incerteza precisa ser revisada por segundo caminho (cl. 7.7)."
- "Auditor pediu evidência de validação do método de calibração de balança industrial — eu tinha em PDF de 2019, ele queria a versão de 2023. Tive que justificar."
- "Padrão venceu domingo passado e segunda eu emiti certificado sem saber. NC aberta semana passada — eu como assinante levei observação."
- "Software não me deixa marcar 'esta calibração é com regra de decisão diferente do padrão da casa' (ILAC G8) — tenho que escrever em campo livre, fragiliza."
- "Cliente farma pede 'declaração de validação do sistema computadorizado' — Cali não me dá."

### Dia típico
- **Manhã (8h–12h):** revisa fila de instrumentos pendentes; pega 1–3 pra calibrar (deixa estabilizar 1–2h na T/UR controlada); enquanto isso, abre cálculo de incerteza pendente, revisa números.
- **Tarde (13h–17h):** executa calibração propriamente dita (medições, registro), volta ao computador, calcula incerteza, gera draft de certificado, revisa por segundo caminho, assina digitalmente, encaminha pra metrologista pares revisar (se há) ou direto pra emissão.
- **Fim do dia (17h–18h):** registra padrão usado, observação técnica, lê norma se houver, programa amanhã.

### Ferramentas que usa HOJE
- **Cali LAB / Metroex / ProCalV5 / Beamex CMX** (alguma) — emissão de certificado: **~3h/dia**
- **Excel + planilhas próprias de cálculo de incerteza** (GUM) — herdadas, customizadas: **~1h/dia**
- **Word** — relatório técnico, procedimento, parecer: **~30min/dia**
- **E-mail** — comunicação técnica com cliente, fornecedor de padrão, par revisor: **~30min/dia**
- **Instrumento físico** — calibrador documentador (**Druck/GE, Additel, Wika** em pressão; **Crystal Engineering** em pressão de precisão; **Time Electronics, Beamex, Fluke, Presys** em elétrica/multifunção), padrão, multímetro, peso-padrão: **constante**

### O que NÃO funciona hoje (gap específico)
- **Cali não cobre TODOS os tipos de instrumento com cálculo embutido** — frequentemente Marcos cai em planilha lateral.
- **Nenhum software BR oferece validação de método metrológico** (cl. 7.2.2) com biblioteca de evidência.
- **Cali não tem fluxo claro de "revisor par"** (cl. 7.7 — segundo caminho) — fica na confiança do humano.
- **Não há trilha de auditoria visível pra ele** sobre quem viu / alterou / aprovou o certificado dele (INV-001 + INV-013).
- **Assinatura digital frequentemente é "imagem do nome" em PDF** — não certificado ICP-Brasil real.

### O que daria sucesso visível pra essa persona
- "Cálculo de incerteza GUM-compliant embutido pros 30 tipos mais comuns; pros atípicos, planilha customizada vinculada ao certificado com versão controlada."
- "Antes de eu clicar 'assinar', sistema mostra TODA a cadeia (instrumento → padrão → certificado-pai → validade → minha autorização vigente) — se tem qualquer pendência, não me deixa assinar."
- "Assinatura ICP-Brasil real (e-CPF A3) integrada — certificado tem hash + carimbo do tempo."
- "Histórico do instrumento mostra deriva ao longo das calibrações — ajuda recomendar intervalo de recalibração (ILAC G24)."

### O que vai resistir a aceitar
- "Vou ter que validar o software novo conforme cl. 7.11. Quem paga essa validação?"
- "Minha planilha GUM eu sei de cor — não confio em motor de cálculo de terceiro sem auditar."
- "Cali eu já briguei com a Cgcre e venci. Sistema novo vai gerar NC."
- "Documento de validação do software (IQ/OQ/PQ) — você tem? Sem isso eu não migro."
- "Quem é o vendor? Tem RT? Em qual escopo?"
- **Cali há 5-15 anos, conhece de cor; resistência REAL à mudança (não retórica)** — migração exige plano de mudança organizacional, não só UI melhor. Marcos cresceu junto com a ferramenta e tem orgulho técnico de dominá-la.

### Frase-chave
> "Meu CPF assina o certificado. Se tiver número errado, é minha cabeça que vai ser cobrada pelo Inmetro — não a do dono nem a do dev."

### Variações por perfil de empresa
- **Perfil A:** signatário formal autorizado RBC; figura de **poder técnico**; **decisor de veto** na compra do software; preocupado com validação (cl. 7.11).
- **Perfil B:** signatário informal mas tecnicamente sólido; menos burocracia; mais aberto à mudança se ferramenta entregar valor.
- **Perfil C:** geralmente sócio técnico do dono ou consultor PJ; em formação pra acreditação.
- **Perfil D:** não existe formalmente; quem "assina aferição" é o próprio dono ou técnico sênior.

### Sinais pra entrevista qualitativa
- "Me leva pelo seu fluxo de emissão de certificado — do recebimento à entrega — passo a passo."
- "Última vez que você se recusou a assinar um certificado — por quê?"
- "Como você calcula incerteza pra instrumento atípico?"
- "Cali — o que ele faz bem? O que você odeia?"
- "Software novo precisa de IQ/OQ/PQ pra você aceitar? Quem documenta?"
- "Você assina digital (ICP-Brasil) ou imagem?"

---

## Persona 6 — Cláudia (Financeiro)

> **Contexto:** controla contas a pagar/receber, emite NFS-e, faz conciliação bancária, cobra cliente. Em PME pequena pode acumular com Letícia (atendente) ou com o próprio dono. Em perfil A maior, é cargo dedicado. **Tem foco fiscal forte** — vive cutover NFS-e Padrão Nacional 01/09/2026 (R-016).

### Identidade
- **Nome fictício:** Cláudia Nascimento
- **Idade típica:** 30–50 anos
- **Formação típica:** técnico em contabilidade, superior em ciências contábeis ou administração. Geralmente fez mais cursos livres (Sebrae, Senac) ao longo dos anos.
- **Anos de experiência:** 5–20 anos, frequentemente em mais de um setor antes (varejo, serviço).
- **Remuneração típica BR (2 cenários):** **(a) PME pequena/perfil D-C com Auxiliar Financeiro:** R$ 2.500–4.000 (CBO 413110). **(b) PME média/perfil B-A com Analista Financeiro:** R$ 5.000–8.000 (CBO 252210). `[a confirmar]`
- **Localização típica:** sede da empresa, capital ou interior.

### Contexto de trabalho
- **Onde trabalha fisicamente:** mesa administrativa, 2 monitores quase sempre (1 pro banco, 1 pro Bling/sistema).
- **Horário típico:** comercial estrito; hora extra no fechamento de mês (último dia + 5 dias úteis seguintes).
- **Reporta a:** dono / contador externo.
- **Equipe:** geralmente sozinha + contador externo (escritório terceirizado).
- **Perfil dominante:** **todos** — em D/C mais informal, em A/B mais estruturada.

### O que ela quer
- **Receber em dia** — DSO (dias de recebimento) baixo; baixar inadimplência.
- **Emitir NFS-e sem erro** — recusa de prefeitura = retrabalho + cliente irritado.
- **Conciliar 100% do extrato** — sem "valor não identificado" pendurado.
- **Fechar mês limpo** — DRE simples confiável pra contador.
- **Não levar multa de prefeitura** por NFS-e fora do padrão (Padrão Nacional 01/09/2026).

### JTBDs principais
JTBD-018 (não cobrar quem já pagou), JTBD-034 (NFS-e do município certo), JTBD-035 (conciliar PIX/boleto), JTBD-036 (cobrar atrasado), JTBD-039 (saber 30 dias adiante).

### Dores principais
D-008 (conciliação manual), D-009 (cobrança constrangedora), D-017 (cutover NFS-e 09/2026).

### O que a deixa louca
- "Bling emite NFS-e, mas pra cada município que tem padrão próprio eu preciso configurar diferente. **NFS-e SP tem padrão próprio TSS, e cada atualização da prefeitura quebra a integração — já fiquei 3 dias sem emitir.**"
- "OS fechada na operação não vira nota automaticamente — preciso pegar lista da Letícia, abrir cliente por cliente no Bling, digitar valor, prazo, descrição."
- "Cliente pediu boleto, eu emiti no Bling; cliente pagou no PIX direto na conta sem aviso. Eu não fecho o título com o pagamento — fica pendurado 15 dias."
- "Extrato bancário sai em OFX, mas o software de OS não importa — Excel manual."
- "Cobrança: ligo, mando WhatsApp, mando boleto novo. Não tem régua automática."
- "Mudança do Padrão Nacional NFS-e (set/2026) — meu contador me ligou em pânico, eu não sei se Bling vai atualizar a tempo (R-016)."
- "Pix tem que ter conciliação automática. Não tem."

### Dia típico
- **Manhã (8h–12h):** abre extrato bancário (Sicredi/Itaú/Santander/Bradesco PJ); identifica recebimentos do dia, baixa nos títulos no Bling; revisa contas a pagar do dia, agenda PIX/boleto; responde dúvida de cliente sobre nota emitida.
- **Tarde (13h–17h):** processa OS encerradas (lista que Letícia mandou), emite NFS-e uma a uma no Bling; envia 2ª via de boleto pra cliente atrasado; concilia conta corrente.
- **Fim do dia (17h–18h):** fecha movimento do dia, manda planilha pra dono ver, lista cobranças amanhã.
- **Fechamento de mês:** roda relatório de Bling, exporta pra Excel, ajusta, manda pro contador externo.

### Ferramentas que usa HOJE
- **Bling ou Conta Azul** — NFS-e, contas, fluxo de caixa básico: **~4h/dia**
- **Internet banking PJ** — extrato, PIX, boleto: **~2h/dia**
- **Excel** — fechamento mensal, controle paralelo, conciliação manual: **~2h/dia**
- **WhatsApp** — cobrança, comunicação com cliente sobre boleto: **~1h/dia**
- **E-mail** — envio de boleto formal, nota: **~30min/dia**
- **Sistema da prefeitura local** — quando Bling não cobre o município (ex: portal NFS-e SP): **~1x/semana**

### O que NÃO funciona hoje (gap específico)
- **Bling tem cobertura nacional mas qualidade variável** — alguns municípios têm bugs (recusa silenciosa, campo IBSCBS faltando).
- **Bling não tem integração com OS de calibração** — pra Cláudia, OS é "papel da operação".
- **Conciliação PIX é manual** — não há matching automático com título.
- **Régua de cobrança não existe** — Cláudia inventa a régua dela.
- **Nenhum competidor de calibração (Cali, Metroex, Calibre) emite NFS-e** — gap confirmado em `concorrentes.md` (única exceção parcial: FP2/Santa Maria-RS).

### O que daria sucesso visível pra essa persona
- "OS aprovada vira NFS-e com 1 clique. Município certo, padrão certo, IBSCBS 2026 preenchido."
- "PIX recebido com chave da empresa vira baixa de título automática (matching por valor + remetente)."
- "Régua de cobrança automática: D+0 lembrete; D+3 e-mail; D+7 WhatsApp; D+15 escalação."
- "1 tela: 'estes 8 clientes devem R$ 23k, atraso médio 12 dias'."

### O que vai resistir a aceitar
- "Bling eu já implantei. Não vou trocar de novo sem ver retorno claro."
- "Cutover NFS-e Padrão Nacional é em 09/2026 — não dá pra trocar de sistema agora (R-016)."
- "Meu contador externo só sabe Bling — ele vai resistir."
- "E se travar no dia 5 e eu não conseguir emitir NFS-e do mês todo?"

### Frase-chave
> "Eu fecho o mês olhando pra extrato bancário em uma tela, planilha em outra, Bling em uma terceira, e contando no dedo."

### Variações por perfil de empresa
- **Perfil A:** contas mais sofisticadas, cliente PJ farma/automotivo paga em D+60 ou D+90, fluxo de caixa apertado, NFS-e padrão SP/RJ frequente.
- **Perfil B:** mistura PJ + PME local, D+30 dominante.
- **Perfil C/D:** mais boleto pequeno, mais inadimplência, mais cobrança manual.

### Sinais pra entrevista qualitativa
- "Me mostra como você emite uma NFS-e — do começo ao fim."
- "Quanto tempo gasta conciliando o extrato bancário por dia?"
- "Última recusa de NFS-e pela prefeitura — qual o erro?"
- "Cutover NFS-e 09/2026 — você sabe? Tá preparada?"
- "Cobrança: como você decide cobrar cliente X hoje vs deixar pra amanhã?"
- "Se PIX recebido virasse baixa automática, isso te economizaria quanto?"

---

## Persona 7 — Rogério (Vendedor / comercial)

> **Contexto:** capta cliente novo via indicação / WhatsApp / visita; faz orçamento; segue até fechamento. Em empresa pequena (B/C/D) acumula com o próprio dono ("Roldão também vende"). Em empresa maior é dedicado. **CRM é dor crônica do setor** — quase ninguém usa.

### Identidade
- **Nome fictício:** Rogério Pinheiro
- **Idade típica:** 28–50 anos
- **Formação típica:** técnico ou superior em administração / engenharia comercial. Frequentemente ex-técnico que virou vendedor pela facilidade de explicar tecnicamente.
- **Anos de experiência:** 5–20 anos
- **Remuneração típica BR:** fixo R$ 3k–6k + comissão 1–5% sobre faturamento gerado. Em lab grande com cliente farma: fixo R$ 5k–8k + comissão. `[a confirmar]`
- **Localização típica:** sede da empresa + roda na região visitando cliente.

### Contexto de trabalho
- **Onde trabalha fisicamente:** mesa na empresa + carro + cliente. Frequentemente home office parcial pra fechar proposta.
- **Horário típico:** comercial elástico — visita cliente no horário do cliente.
- **Reporta a:** dono / gerente comercial (se houver).
- **Equipe:** sozinho, ou em equipe de 2–4 vendedores (lab maior).
- **Perfil dominante:** **B/C/D** (forte) + **A** (orçamento padrão).

### O que ele quer
- **Bater meta mensal de fechamento** (R$ ou número de propostas aprovadas).
- **Encurtar ciclo de vendas** — orçamento → aprovação em < 14 dias.
- **Não perder lead** — todo prospect responder em < 24h.
- **Conhecer histórico do cliente** antes de visitar (o que ele já comprou, último problema reportado).
- **Negociar com base em margem real** — saber até onde pode descontar.

### JTBDs principais
JTBD-019 (orçamento na hora pedido), JTBD-040 (qual prospect tem maior chance), JTBD-041 (orçamento profissional), JTBD-043 (calcular comissão sem brigar), JTBD-044 (renovação de contratos recorrentes).

### Dores principais
D-002 (recalibração esquecida = lead perdido), D-011 (versão de orçamento errada), D-018 (tabela de preço desatualizada).

### O que o deixa louco
- "Orçamento eu faço em Word, exporto PDF, mando por WhatsApp ou e-mail. Cliente não responde. Não sei se viu."
- "Pra fazer orçamento eu preciso perguntar pro técnico 'quanto tempo demora calibrar essa balança rodoviária' — espero 2h pela resposta. Cliente já esfriou."
- "Cliente novo me liga, pede preço de manutenção de balança industrial — eu não tenho tabela; pergunto pro Roldão; ele responde 'cobra X'; cobro X; cliente fecha; outro vendedor cobrou X+30% pro mesmo serviço outro dia. Perdi margem."
- "Tabela de preço fica numa planilha que ninguém atualiza. Última revisão 2024."
- "Não sei quantos orçamentos eu mandei esse mês. Não sei taxa de conversão."
- "Cliente fechou em janeiro e eu não recebi comissão até abril — não sei quem 'comeu' a venda."
- "Cliente que era meu há 3 anos foi atendido por OUTRO vendedor da empresa por engano — comissão dele, não minha."

### Dia típico
- **Manhã (8h–12h):** abre WhatsApp, responde leads novos; volta em 2–3 proposals da semana anterior pedindo retorno; abre planilha de pipeline pessoal; entra em ligação ou visita.
- **Tarde (13h–17h):** visita cliente (1–3 visitas), volta pra empresa, faz orçamento novo (Word + tabela imaginária), envia pra cliente.
- **Fim do dia (17h–18h):** atualiza planilha pessoal de pipeline; manda relatório (WhatsApp pro Roldão) do que rolou.

### Ferramentas que usa HOJE
- **WhatsApp** — canal #1 com prospect e cliente: **~3h/dia**
- **Word + PDF** — orçamento: **~1h/dia**
- **Excel** (planilha pessoal de pipeline) — controle do que está aberto: **~30min/dia**
- **Carro + visita presencial** — fechamento alto valor: **~2x/semana**
- **LinkedIn (raro)** — busca de prospect em farma/automotivo: **~30min/semana**
- **E-mail** — cliente formal, RFP de cliente grande: **~30min/dia**
- **Tabela de preço Excel** — desatualizada: **consulta esporádica**

### O que NÃO funciona hoje (gap específico)
- **Nenhum dos competidores BR de calibração (Cali, Metroex, Calibre) tem CRM próprio** — vendedor usa planilha ou Pipedrive/RD Station/HubSpot separado.
- **Tabela de preço não está no sistema** — está na cabeça do Roldão / planilha desatualizada.
- **Orçamento em Word é fonte de erro** — copia de proposta anterior, esquece de mudar nome do cliente.
- **Sem rastreio de "cliente abriu PDF"** — vendedor não sabe se proposta foi vista.
- **Comissão é calculada à mão pelo financeiro** — disputas frequentes.

### O que daria sucesso visível pra essa persona
- "Eu monto orçamento em 5 min: escolho cliente → escolho serviço da tabela → ajusto preço → manda. Sistema gera PDF profissional."
- "Sistema avisa: 'cliente abriu seu PDF há 1h' — eu ligo na hora certa."
- "Vejo MEU pipeline: 8 propostas abertas, R$ 47k, taxa esperada 30%."
- "Comissão calculada automaticamente: 'esse mês você vai receber R$ 3.200, baseado nestas 5 OS faturadas'."
- "Cliente novo entra, sistema marca 'esse cliente é seu' (proteção de carteira)."

### O que vai resistir a aceitar
- "Mais 1 sistema pra preencher? Eu mal abro CRM hoje."
- "Cliente vai receber proposta menos personalizada — vai parecer robô."
- "E se travar e eu não conseguir mandar proposta na hora?"
- "Comissão automática — e se o sistema errar pra menos?"

### Frase-chave
> "Cliente pergunta preço, eu prometo 'mando hoje à tarde', e mando daqui a 3 dias porque tô esperando o técnico me passar o tempo de execução."

### Variações por perfil de empresa
- **Perfil A:** cliente PJ regulado (farma, automotivo); ciclo longo (RFP, homologação de fornecedor); proposta técnica robusta; ticket médio alto; relacionamento de anos.
- **Perfil B:** mistura PJ + PME; ciclo médio; relacional.
- **Perfil C/D:** muito WhatsApp, ciclo curto, ticket baixo, alta rotatividade de cliente.

### Sinais pra entrevista qualitativa
- "Me mostra como você faz uma proposta — começo ao fim."
- "Qual sua taxa de conversão (proposta enviada → aprovada)?"
- "Última perda de venda — por quê?"
- "Você usa CRM hoje? Qual?"
- "Comissão: como é calculada? Tem disputa?"
- "Se eu te der relatório 'cliente abriu PDF' — você usaria?"

---

## Persona 8 — João Eng./qualidade (Cliente final do tenant — quase-persona)

> **Contexto:** **NÃO é usuário do ERP Aferê.** É o **cliente do nosso cliente** (PME que pagou a calibração). Recebe certificado em PDF. Em alguns casos acessa portal do cliente pra baixar histórico. Relevante porque (a) é quem realmente "consome" o produto-fim (certificado), (b) decide se cobra portal do fornecedor, (c) influencia a próxima recompra. **Não desenvolver com a mesma profundidade das 7 anteriores** — é referência pra design do Portal do Cliente (módulo "Atendimento ao cliente" no mapa).

### Identidade
- **Nome fictício:** João Ferreira (responsável pela qualidade / metrologia no cliente — pode ser engenheiro, técnico, ou supervisor de produção dependendo do porte do cliente final)
- **Idade típica:** 30–55 anos
- **Formação típica:** técnico ou superior (engenharia, farmácia, química, gestão da qualidade)
- **Anos de experiência:** 5–25 anos no setor do cliente final
- **Remuneração típica BR:** R$ 4k–15k/mês CLT, faixa larga porque depende do setor (farma > açougue)
- **Localização típica:** indústria/lab/hospital cliente — qualquer região do BR

### Contexto de trabalho
- **Onde trabalha fisicamente:** instalação do cliente (indústria, hospital, posto, mina, frigorífico).
- **Horário típico:** comercial da indústria do cliente.
- **Reporta a:** gerente de qualidade / produção do cliente final.
- **Perfil:** cliente do tenant — todos os perfis (mas perfil A do tenant tende a atender cliente final mais regulado, ex: farma).

### O que ele quer (do ponto de vista DELE, cliente final)
- **Ter o certificado em mãos quando o auditor (ANVISA, Cgcre, ISO 9001) chegar** — sem caçar em e-mail antigo.
- **Saber quando próximo instrumento vence** — não levar multa IPEM (R-040) nem rejeição de auditoria.
- **Receber lembrete de recalibração** com antecedência razoável (60–90 dias) — pra negociar agenda interna.
- **Pagar o que combinou** — sem surpresa fora do orçamento aprovado.

### JTBDs principais
JTBD-017 (achar certificado quando precisa), JTBD-012 (lembrete de recalibração / verificação IPEM).

### Dores principais
D-002 (recalibração esquecida pelo lado dele), D-015 (confusão calibração vs verificação INMETRO).

### O que o deixa louco
- "O certificado da balança do meu açougue veio por e-mail em 2024. Acabei de mudar de notebook. Cadê?"
- "Eu pago R$ 800 pra calibrar uma balança. Auditor pediu evidência, eu mandei foto da plaqueta. Auditor pediu certificado. Eu fui procurar e demorei 2 dias."
- "Fornecedor (Roldão) me cobrou 30% a mais do que combinado. Eu não tinha o orçamento aprovado em mãos."
- "Auditor ANVISA pediu cadeia de rastreabilidade da balança da minha sala de pesagem — eu fui até o Roldão, ele mandou um PDF que tinha o nome dele e o número do padrão, mas faltava o certificado-pai do padrão. ANVISA rejeitou."
- "Esqueci de chamar pra recalibrar minha balança rodoviária — DNIT autuou meu caminhão por excesso de peso (carga real vs balança fora). Custou caro."

### O que daria sucesso visível pra essa persona
- "Recebo e-mail/WhatsApp 90 dias antes de cada instrumento vencer."
- "Entro num portal com meu CNPJ, vejo histórico completo de tudo que o Roldão calibrou pra mim, baixo PDF a qualquer momento."
- "Vejo cadeia de rastreabilidade clicando 1x — instrumento → padrão → certificado-pai do padrão."

### O que vai resistir a aceitar
- "Mais 1 portal pra logar? Eu tenho 14 portais de fornecedor já."
- "Não vou ensinar nada novo pro auditor. Continua mandando o PDF."

### Frase-chave
> "Eu só quero o PDF do certificado pra mostrar pro auditor da ANVISA quando ele chegar. O resto é responsabilidade do Roldão."

### Por que essa quase-persona importa pro produto
- **Decisão de UI do portal do cliente:** se João não usar, portal vira ornamento (over-design — `riscos.md`). Validar via WTP test.
- **Risco regulatório (R-040):** se João levar multa IPEM por esquecer verificação periódica, ele **culpa o software do Roldão**. Sistema precisa ter alerta + nota legal explícita no certificado.
- **Diferencial competitivo:** portal do cliente bom = retenção do Roldão pelo João (cliente final fica feliz com o Roldão → Roldão renova SaaS).

---

---

## Persona 9 — Carlos (Motorista da UMC) ⭐ NOVO POR DECISÃO ROLDÃO 17/05/2026

> **Contexto:** dirige a **UMC — Unidade Móvel de Calibração** (caminhão truck/toco 6-12 ton que transporta pesos-padrão pra calibração de balança rodoviária). Persona introduzida a partir da decisão fundadora **Frota + UMC + Caixa do Técnico** (ver `dominio-de-negocio.md` §"Controle de Técnico em Campo, Despesas, Frota e UMC"). Atua exclusivamente em **perfis A e B** (que operam UMC); perfil C/D raramente tem UMC. `[a confirmar via entrevista]`

### Identidade
- **Nome fictício:** Carlos / Antônio / Sebastião Souza
- **Idade típica:** 35–60 anos
- **Formação típica:** ensino fundamental ou médio + **CNH D ou E** + **curso MOPP** (se carga sensível) + experiência prévia em transporte de carga ou ônibus. Exames toxicológicos obrigatórios em dia.
- **Anos de experiência:** 10–30 anos no volante (raramente menos)
- **Remuneração típica BR:** **R$ 2.500–4.500/mês CLT + diária de viagem (R$ 80–200/dia) + ajuda de custo de hospedagem/refeição** (CBO 7825). `[a confirmar]`
- **Localização típica:** mora perto da garagem da UMC (geralmente cidade-sede do lab); **viaja por todo o Brasil** (a UMC atende contratos a 1.500-2.500 km da base; comum atravessar regiões NE/N pra usina, frigorífico, mina, porto).

### Contexto de trabalho
- **Onde trabalha fisicamente:** **dentro do caminhão UMC** (cabine + boléia) e na operação de descarga/recarga dos pesos-padrão no cliente (com guincho, empilhadeira, ou ajudante).
- **Horário típico:** sai 4–6h da garagem; dirige 6–10h; espera a calibração 4–12h; volta dirigindo. Pernoite em hotel barato de beira de estrada. Viagem típica: 2–5 dias fora de casa.
- **Reporta a:** gerente operacional / supervisor de frota / dono.
- **Equipe:** geralmente solo no caminhão; encontra técnico no cliente (que pode ter ido em carro pequeno separado).
- **Perfil dominante:** **A e B** (perfis com UMC operante).

### O que ele quer
- **Dirigir seguro** — chegar inteiro, voltar inteiro.
- **Não estragar peso-padrão** (R$ 100-300 mil em massas calibradas — perda catastrófica se cair, batida, roubo — risco-novo registrado em `dominio-de-negocio.md`).
- **Chegar no horário combinado** com o cliente (atraso = técnico parado, cliente irritado).
- **Prestação de contas rápida** (diária + comprovante de combustível/pedágio/hotel processados sem burocracia).
- **Documentação em dia** (TAC ANTT, RNTRC, CNH, MOPP, toxicológico — vencimento de qualquer um desses = UMC parada).

### JTBDs principais
JTBD-022 (executar sem internet — caminhão em estrada perde 4G), JTBD-025 (não voltar pra "encerrar" — prestação de contas no celular), **JTBD-frota-NOVO** (registrar abastecimento + KM + despesa em 1 clique), **JTBD-frota-NOVO-2** (foto de comprovante anexada à viagem). `[IDs definitivos serão criados quando jobs-to-be-done.md for refatorado pra incluir Frota+UMC]`

### Dores principais
D-005 (status perguntado o tempo todo — gerente liga "cadê o caminhão?"), D-006 (roteirização no escuro — Carlos descobre desvio de obra na BR-364 só quando chega), D-019 (foto/comprovante perdido). **D-NOVO-frota** (caixa do motorista não prestada/não conciliada).

### O que o deixa louco
- "Estrada ruim — BR-101 NE cheia de buraco; BR-364 N alagada em janeiro; BR-116 quase intransitável em alguns trechos."
- "Posto de combustível com preço abusivo no meio do nada — sou obrigado a abastecer ou paro o caminhão."
- "Refeição ruim na rodovia — comi marmita estragada na BR-040, perdi 1 dia de viagem doente."
- "Fiscal PRF/IPEM parando sem motivo claro — perco 2-3h por blitz; tenho que mostrar TAC, RNTRC, CNH, MOPP, toxicológico, nota da carga (pesos-padrão), DUT do caminhão. Se faltar UM papel é multa + UMC apreendida."
- "Técnico atrasado pra carregar o caminhão — saio 2h depois do previsto, perco janela de cliente."
- "Esqueci documento na garagem — RNTRC venceu e eu não vi; quase fui autuado."
- "Caixa do motorista — gerente cobra 'cadê comprovante do hotel?' e eu mando foto pelo WhatsApp; foto some; eu pago do meu bolso."

### Dia típico
- **Madrugada (4h–6h):** sai da garagem com caminhão carregado (pesos-padrão + ajudante eventual); confere documentação; abastece se necessário.
- **Manhã (6h–12h):** dirige 6h direto (com paradas obrigatórias de descanso conforme Lei do Motorista 13.103/2015 — 30 min a cada 5h30 de direção).
- **Almoço:** restaurante de beira de estrada (1h); foto da nota.
- **Tarde (13h–17h):** chega no cliente (usina/mina/frigorífico/porto); ajuda técnico a descarregar pesos com guincho/empilhadeira (1-2h); aguarda calibração (4-12h, frequentemente noite adentro).
- **Pernoite:** hotel barato perto do cliente; foto da nota; jantar simples.
- **Dia seguinte:** carrega de volta; volta dirigindo (mesma rota, ou desvio se contrato múltiplo); chega na garagem 1-2 dias depois.

### Ferramentas que usa HOJE
- **Caminhão UMC** — instrumento principal (cabine, hodômetro, painel): **constante**
- **Waze + Google Maps** — rota e desvios: **constante**
- **WhatsApp** — pro gerente avisar onde tá ("passei Feira de Santana", "cheguei em Mossoró", "saindo agora"): **~1h/dia**
- **Câmera do celular** — foto do hodômetro, nota de posto, nota de hotel, nota de pedágio: **~5x/dia**
- **Papel mesmo** — prestação de contas com envelope de notas físicas entregues à empresa na volta: **constante**
- **Aplicativo do banco** — receber diária via PIX: **~1x/dia**
- **Rastreador veicular** — instalado no caminhão (obrigatório por seguro de carga); ele NÃO opera, só é monitorado: **passivo**

### O que NÃO funciona hoje (gap específico)
- **Caixa do motorista é planilha + envelope** — comprovante físico se perde, valor diverge entre o que Carlos lembra e o que o financeiro registra.
- **Nenhum dos concorrentes BR (Cali, Metroex, Calibre) tem gestão de frota nem UMC** — gap absoluto confirmado em `concorrentes.md`.
- **Auvo cobre OS de campo + GPS** mas NÃO tem caixa do motorista, manutenção de frota, vínculo com OS de calibração ISO 17025.
- **Foto de comprovante pelo WhatsApp** — qualidade ruim, não-OCR, gerente não consegue reembolsar sem digitar tudo.
- **KM rodado** — Carlos anota no caderno; financeiro retransfere pra planilha; erros frequentes (R$ por KM diverge).

### O que daria sucesso visível pra essa persona
- "Abro app no celular, vejo 'sua viagem de hoje: garagem → Mossoró/RN, cliente Frigorífico X, 1.450 km, descarregar 12 ton de pesos'."
- "Abasteço, tiro foto do bico/nota — sistema reconhece valor, KM, posto, lança no caixa da viagem."
- "Pago hotel R$ 90, foto da nota, sistema lança como hospedagem da viagem XYZ."
- "Chego na garagem — prestação de contas pronta; financeiro só confere e libera saldo (positivo me devolvem, negativo eu devolvo)."
- "Documentação vence em 30 dias? Sistema me avisa + avisa gerente."

### O que vai resistir a aceitar
- "Outro app na minha vida? Já tenho 15 no celular e mal sei usar."
- "Mais coisa pra preencher — eu dirijo, não sou escritório."
- "Login com senha complicada — esqueço; MFA com SMS não chega na estrada (sem sinal)."
- "Se travar no posto e eu não conseguir abastecer porque não registrou — paro a viagem?"
- "Geolocalização me incomoda — não quero patrão sabendo onde paro pra dormir."
- "Tela pequena — meu celular é simples (R$ 600)."

### Frase-chave
> "Eu dirijo, o resto é problema do escritório."

### Variações por perfil de empresa
- **Perfil A:** UMC dedicada, motorista CLT formal, processo de prestação rigoroso; rastreador veicular obrigatório por contrato (cliente farma/petroquímico exige); auditoria interna de viagens.
- **Perfil B:** UMC compartilhada com outra função (transporte de instrumento entre lab e cliente); motorista pode acumular com técnico se tiver CNH D.
- **Perfil C/D:** **raramente tem UMC** — calibração de balança rodoviária é nicho que exige investimento alto (R$ 500k+ em pesos-padrão + caminhão); persona inativa.

### Sinais pra entrevista qualitativa (Onda 2 — fora da empresa Roldão)
- "Quantas viagens por mês? Quantos km na média?"
- "Caixa do motorista — como funciona hoje? Quanto te devem agora?"
- "Última documentação vencida — o que aconteceu?"
- "Você usa que app no dia a dia? Qual te ajuda mais?"
- "Geolocalização te incomoda?"
- "Se eu te der app que faz a prestação de contas no celular — você usa?"

---

## Persona 10 — Auditor Cgcre/IPEM (Reguladores em campo)

> **Contexto:** persona composta — combina **Auditor Cgcre** (avaliação RBC de laboratório acreditado, conforme ABNT NBR ISO/IEC 17011 + NIT-DICLA-031) com **RT IPEM (RBMLQ-I)** (verificação metrológica legal de balança comercial, bomba de combustível, taxímetro, etilômetro). Fluxos distintos mas comportamento e psicologia de fiscalização similares. **NÃO é usuário do ERP Aferê** — é quem o tenant precisa **convencer com evidência**. `[a confirmar via entrevista — possível parceria com associação de signatários ou ex-auditores Cgcre]`

### Identidade
- **Nome fictício:** Eng. Roberto Mendes (Cgcre) / Eng. Patrícia Lopes (IPEM-SP)
- **Idade típica:** 40–60 anos
- **Formação típica:** engenharia (mecânica, elétrica, química) + pós em metrologia/qualidade + treinamento Cgcre/Inmetro. Frequentemente ex-técnico de lab acreditado que virou auditor.
- **Anos de experiência:** 15–30 anos no setor (mín. 5 como auditor Cgcre); RT IPEM costuma ter 10+ anos no órgão.
- **Remuneração típica BR:** auditor Cgcre PJ contratado R$ 300-600/h + diária; RT IPEM concursado R$ 8-15k CLT. `[a confirmar]`
- **Localização típica:** Cgcre tem sede em Xerém/RJ + auditores PJ espalhados pelo BR (avaliam onde o lab está); IPEM é estadual (26 órgãos delegados).

### Contexto de trabalho
- **Onde trabalha fisicamente:** no laboratório do tenant durante auditoria (1-3 dias presenciais por ciclo).
- **Horário típico:** comercial — auditoria começa 8h, termina 17h com reunião de fechamento.
- **Reporta a:** Cgcre/Inmetro central / direção do IPEM estadual.
- **Equipe:** geralmente sozinho ou em dupla (auditor líder + auditor técnico do escopo).

### O que ele quer
- **Verificar conformidade com a norma** sem perder tempo procurando evidência.
- **Coletar evidência objetiva** — não aceitar "a gente faz assim, é confiável" — quer ver registro datado e assinado.
- **Fechar auditoria com NC bem documentadas** (NC maior, menor, observação) pra justificar parecer.
- **Não ser enganado** — sistemas que "maquiam" pra auditoria geram NC séria.
- **Cumprir cronograma** (auditoria de 2 dias não pode virar 4).

### JTBDs principais (do ponto de vista de quem opera o tenant — Sandra/Marcos)
JTBD-002 (não perder acreditação), JTBD-028 (rastreabilidade automática), JTBD-029 (NC pendente bloqueia emissão), **JTBD-aud-NOVO** (modo auditoria do sistema — 1 clique mostra tudo do período).

### Dores principais (do tenant ao receber este auditor)
D-007 (cadeia incompleta no certificado), D-016 (documentação 17025 só na véspera). **D-NOVO-aud** (auditor pede evidência que sistema não consegue mostrar de imediato).

### O que ele rejeita (do ponto de vista do auditor)
- **Evidência não-datada ou retroativa** — "imprimir tudo na véspera" é red flag.
- **Sistema que permite editar registro sem trilha** — auditor procura `INV-001` (trilha imutável) sem nem saber o nome técnico; se ele duvida, abre NC.
- **PDF com assinatura-imagem** — não vale como assinatura técnica; precisa ser ICP-Brasil A3 ou equivalente.
- **Procedimento sem versão controlada** ("Proc_v3_FINAL_REVISADO.docx") — NC menor automática.
- **Falar mais que mostrar** — auditor desconfia de tenant que apresenta narrativa em vez de evidência.

### Como aceita evidência digital vs física
- **Aceita digital se:** sistema tem versionamento, timestamp confiável, trilha de auditoria visível, assinatura ICP-Brasil ou hash, possibilidade de exportar relatório auditável.
- **Aceita físico se:** procedimento impresso com assinatura física datada, organizado em pasta-arquivo com índice.
- **Híbrido (mais comum em PME):** auditor aceita digital pra registro de calibração + físico pra ata de reunião e procedimento assinado pelo RT.

### Como interage com "modo auditoria" do sistema (feature crítica do Aferê)
- **Quer:** filtro por período + tipo de instrumento + signatário; export de tudo em 1 PDF; possibilidade de clicar em certificado → ver cadeia até o SI sem trocar de tela.
- **Não tolera:** sistema que precisa de "exportar relatório customizado" demorado; precisa de "modo somente leitura" pra ele navegar sozinho enquanto Sandra atende outra demanda.

### Frase-chave
> "Me mostre a evidência — não me conte a história."

### Variações Cgcre vs IPEM
- **Cgcre (RBC):** foco em sistema de gestão da qualidade + cadeia de rastreabilidade + competência do signatário + cálculo de incerteza. Auditoria de 1-3 dias, ciclo de 4 anos com supervisões.
- **IPEM (RBMLQ-I):** foco em conformidade legal metrológica (selo INMETRO presente, dentro de prazo, balança/bomba em tolerância). Visita rápida (1-3h), sem agendamento prévio em alguns casos. Multa imediata se irregular.

### Por que essa persona importa pro produto
- **"Modo auditoria" é feature de venda Tier-1** — sem ela, Sandra (decisora técnica) rejeita o sistema.
- **R-039 (tenant declarar perfil A sem ser acreditado e emitir falso RBC):** auditor é quem descobre + autua + denuncia ao MP. Sistema precisa impedir tecnicamente antes de chegar nele.
- **Diferencial competitivo:** se o produto entrega "abre, audita, fecha em 1 dia" vs concorrentes que entregam "auditor leva 3 dias procurando", venda fica fácil.

### Sinais pra entrevista qualitativa (Onda 2 — buscar 2-3 ex-auditores Cgcre ou ex-RT IPEM)
- "Auditoria que você fez no último ano — o que mais te incomodou no sistema do tenant?"
- "Software de calibração que você já avaliou — qual é melhor pra auditar? Por quê?"
- "Que evidência você sempre pede e quase nunca recebe pronta?"
- "Se o tenant te entregasse 1 PDF com tudo do período — você confia ou desconfia?"

---

## Persona 11 — Patrícia (Gerente de Qualidade em cliente farma regulado)

> **Contexto:** **NÃO é usuária do ERP Aferê.** É **cliente DO TENANT** (compra calibração do lab que usa o Aferê). Trabalha em indústria farma/biotech regulada (ANVISA RDC 658/2022 + GMP + FDA 21 CFR Part 11 se exporta pros EUA). **Decisora de compra do tenant** — manda RFP com 80 perguntas técnicas; pode auditar fornecedor (o lab) presencialmente. **Influenciadora de feature do Aferê** — porque o que ela exige do lab, o lab exige do software. `[a confirmar via entrevista — 1-2 gerentes de qualidade farma]`

### Identidade
- **Nome fictício:** Patrícia Almeida
- **Idade típica:** 35–55 anos
- **Formação típica:** farmácia, química, engenharia química/bioquímica + pós em qualidade/regulamentação farmacêutica + certificações (RAC, RAPS, GMP).
- **Anos de experiência:** 10–25 anos em farma regulada (laboratório, validação, qualidade).
- **Remuneração típica BR:** R$ 15-30k/mês CLT em multinacional farma; R$ 10-18k em farma nacional. `[a confirmar]`
- **Localização típica:** polo farma (Anápolis/GO, Hortolândia/SP, Jaguariúna/SP, Manaus/AM ZFM, Suape/PE, Rio de Janeiro).

### Contexto de trabalho
- **Onde trabalha fisicamente:** indústria farma (sala de qualidade + sala limpa + bancada de QC).
- **Horário típico:** comercial estrito; pico em pré-inspeção ANVISA/FDA.
- **Reporta a:** diretor de qualidade / regulatório / planta.
- **Equipe:** coordena 3-10 analistas de qualidade + auditores internos.

### O que ela quer (impactando o tenant)
- **Fornecedor (lab de calibração) homologado** — qualificação inicial + reavaliação anual + auditoria presencial periódica.
- **Certificado de calibração com IQ/OQ/PQ documentado** quando o instrumento é GxP-crítico.
- **Cadeia de rastreabilidade rastreável ao SI** — sem isso, instrumento "perde GMP".
- **21 CFR Part 11 compliance** se o instrumento exporta dado pra sistema validado FDA (electronic records + electronic signatures + audit trail).
- **RDC 658/2022 atendida** (registros gravados, assinatura eletrônica equivalente, validade legal).
- **Evidência de competência do signatário** — ela exige o currículo do Marcos antes de aceitar certificado.

### O que ela rejeita (e bloqueia compra)
- **Lab perfil B/C/D** — não compra de quem não é acreditado RBC.
- **Certificado em PDF com assinatura-imagem** — rejeita; exige ICP-Brasil A3 ou equivalente.
- **Software do lab sem documento de validação (cl. 7.11)** — RFP elimina automaticamente.
- **Vendor do software sem RT registrado / sem ART** — pergunta direta da RFP.
- **Lab que não aceita auditoria presencial** — elimina.
- **Falta de cadeia até INMETRO/SI documentada** — elimina.

### JTBDs principais (impacto no Aferê via Sandra/Marcos)
JTBD-002 (não perder acreditação RBC), JTBD-028 (rastreabilidade automática), JTBD-031 (provar validação do software). **JTBD-NOVO-pharma** (atender RFP de cliente farma com 1 export documentado).

### Dores principais (do tenant em atender Patrícia)
D-007 (cadeia incompleta no certificado), D-016 (documentação 17025 só na véspera), **D-NOVO-pharma** (RFP de cliente farma exige documento que o lab não tem pronto).

### O que a deixa louca (vendo do lado do cliente farma)
- "Recebi certificado do meu fornecedor sem o número de série do padrão-pai. Tive que devolver e exigir reemissão. Atrasou validação."
- "Lab terceirizado mandou PDF com 'assinatura digital' que era imagem do nome do RT. ANVISA rejeitou na pré-inspeção."
- "Fornecedor de calibração mudou de software no meio do contrato — sem me avisar — e o novo não tinha documento de validação. Tive que requalificar o fornecedor."
- "Auditei lab presencialmente, pedi 'me mostre o procedimento de validação do método de calibração da minha balança analítica em uso há 2 anos' — RT abriu 3 sistemas e não achou. Abri NC e troquei de fornecedor."

### Como Patrícia interage com o tenant
1. **Qualificação inicial** (1ª compra): manda RFP com 60-80 perguntas; pede ART, RT registrado, acreditação Cgcre vigente, política de qualidade, último relatório de auditoria interna do lab, certificados-modelo, política de validação de software, evidência de IQ/OQ/PQ do sistema computadorizado.
2. **Auditoria presencial** (1ª compra + anual): 1 dia no lab; "modo auditoria" do sistema é testado.
3. **Renovação anual** (questionário curto + amostragem).
4. **Cada certificado novo:** confere assinatura ICP-Brasil + cadeia + incerteza + signatário autorizado.

### Como ela aceita evidência do software
- **Documento de validação do software (IQ/OQ/PQ)** assinado pelo vendor com data e versão.
- **Trilha de auditoria exportável** mostrando quem fez o quê quando.
- **Assinatura ICP-Brasil A3** no certificado (não imagem; não ICP-Brasil A1).
- **Cadeia de rastreabilidade clicável** — ela quer ver no portal: instrumento → padrão → certificado-pai → ... → SI.

### Frase-chave
> "Sem 21 CFR Part 11 e RDC 658/2022 atendidos, não passa pelo meu fornecedor homologado."

### Por que essa persona importa pro produto
- **Define teto de qualidade** que o Aferê precisa entregar pra Sandra/Marcos atenderem o cliente farma.
- **Influencia roadmap:** features como "documento de validação do software exportável", "21 CFR Part 11 compliance kit", "ICP-Brasil A3 integrado" nascem dela.
- **Risco competitivo:** Cali tem cliente farma; se Aferê não atende esse nível, perde mercado A premium.

### Sinais pra entrevista qualitativa (Onda 2 — 1-2 gerentes farma)
- "Última qualificação de fornecedor de calibração que você fez — o que mais demorou?"
- "RFP que você manda — quantas perguntas? Qual a mais difícil pro fornecedor responder?"
- "Lab que você desqualificou — por quê?"
- "Sistema computadorizado do lab — como você valida?"

---

## Persona 12 — João-Sênior (Cliente final low-tech — açougue)

> **Contexto:** **NÃO é usuário do ERP Aferê.** É variação da quase-persona "João Eng./qualidade" (Persona 8) — mas no extremo oposto do espectro: **cliente final de baixa alfabetização digital**, idoso, dono de pequeno comércio (açougue, padaria, mercadinho de bairro). **Decisor da recompra de calibração** mas **NÃO vai usar Portal do Cliente** — exige fluxo zero-login alternativo (WhatsApp, SMS, e-mail simples). Renomeação implícita: a Persona 8 "João Eng./qualidade" cobre o cliente final corporativo/regulado; **João-Sênior cobre o cliente final pequeno comerciante**. `[a confirmar via entrevista — falar com 3-5 açougueiros/padeiros sobre calibração]`

### Identidade
- **Nome fictício:** João Pereira (dono do "Açougue do João" no bairro)
- **Idade típica:** 60–75 anos
- **Formação típica:** ensino fundamental incompleto ou completo; aprendeu o ofício na prática.
- **Anos de experiência:** 30-50 anos no comércio.
- **Remuneração típica BR:** retira do caixa do açougue R$ 4-8k/mês (rendimento variável); patrimônio em imóvel.
- **Localização típica:** bairro periférico ou cidade do interior; capital também (açougue de bairro).

### Contexto de trabalho
- **Onde trabalha fisicamente:** balcão do açougue; câmara fria; pequena salinha de fundo onde fica o computador (raramente usado).
- **Horário típico:** abre 7h, fecha 19h, segunda a sábado.
- **Reporta a:** ele mesmo (dono).
- **Equipe:** 1-3 funcionários (esposa/filho/funcionário fixo).

### O que ele quer
- **Não levar multa do IPEM** — verificação metrológica anual da balança comercial (INMETRO Portaria 157/2022) precisa estar em dia. Multa pode ser R$ 800-3.000.
- **Pagar pouco pela calibração/verificação** — sensível a preço; troca de fornecedor por R$ 50 de diferença.
- **Resolver no WhatsApp** — não baixa app, não acessa portal, não cria senha.
- **Receber lembrete antes do vencimento** — esquece datas; já levou multa por isso.
- **Confiar no fornecedor** — relação de anos, "fia, vai lá e faz".

### O que ele rejeita
- **Portal do cliente com login + senha + MFA** — desiste antes de tentar.
- **E-mail formal** — abre 1x por semana, perde.
- **App pra baixar** — celular dele é simples (R$ 600, Android 6 ou Whatsapp-only); memória cheia.
- **PDF complicado** — não consegue baixar; pede pro filho ou pro técnico do fornecedor.

### JTBDs principais (impacto no Aferê pelo lado do tenant)
JTBD-012 (lembrete de recalibração / verificação IPEM), JTBD-017 (achar certificado quando precisa). **JTBD-NOVO-low-tech** (receber certificado por WhatsApp sem precisar de app/portal).

### Dores principais (do tenant em atender João-Sênior)
D-002 (recalibração esquecida), D-015 (confusão calibração vs verificação INMETRO), **D-NOVO-low-tech** (cliente final não usa portal — comunicação só por WhatsApp/SMS, o que sobrecarrega a Letícia).

### O que o deixa louco
- "Esqueci da verificação da balança. IPEM veio, multou R$ 1.200. Pago em 3x e tô puto."
- "Mandaram PDF do certificado no meu e-mail. Não sei abrir, não sei imprimir. Fui no Casas Bahia pedir pra imprimir."
- "Filho me mostrou portal — pediram pra eu fazer senha. Eu desisti. Liguei pro fornecedor."
- "Fornecedor mudou e o novo não me lembrou da próxima verificação. Levei multa de novo."

### Como ele interage com o tenant
- **Canal único:** WhatsApp do fornecedor (PJ ou pessoal do Roldão / Letícia).
- **Lembrete:** áudio de WhatsApp ("seu Roldão, dia 15 venço a balança, marca?") ou ligação.
- **Recebe certificado:** WhatsApp como imagem JPG (não PDF — JPG ele vê na hora) ou impresso entregue na mão pelo técnico.
- **Paga:** PIX (aprendeu na pandemia) ou dinheiro pro técnico no ato.

### Frase-chave
> "Manda no WhatsApp por áudio, fia. Esse negócio de portal eu não mexo."

### Por que essa persona importa pro produto
- **Define o piso de UX do canal externo** — se sistema só oferece portal, perde toda essa fatia (estimada em 30-50% dos clientes finais de balança comercial em bairro).
- **Implica feature obrigatória:** **WhatsApp Business API** integrada ao sistema do tenant, com fluxo "envio de certificado como imagem + áudio de lembrete + confirmação por reply 'OK'".
- **Mitigação de R-040** (cliente final esquece verificação periódica e culpa o software do tenant): lembrete proativo via canal que ele usa.
- **Diferencial vs Cali/Metroex** (que só têm portal web tradicional): tenant que serve João-Sênior fica preso ao Aferê.

### Sinais pra entrevista qualitativa (Onda 2 — 3-5 donos de comércio pequeno)
- "Última vez que precisou de calibração — como soube?"
- "Você acessa portal de fornecedor?"
- "Certificado em PDF — você baixa e guarda? Como?"
- "Lembrete da próxima verificação IPEM — chega como?"

---

## Persona 13 — Bruna (Técnica de campo mulher)

> **Contexto:** variação da Persona 4 (Bruno dos Santos). **Mesma faixa salarial, mesmas atribuições, mesmas ferramentas**, mas com pautas adicionais de gênero e segurança que o sistema deve contemplar. Reflete crescimento real (~5-15% em RS/SP/MG segundo CAGED 2025 setor metrologia/calibração; números mais altos em farma e alimentos). `[a confirmar via entrevista — 2-3 técnicas mulheres em lab de calibração]`

### Identidade
- **Nome fictício:** Bruna Soares
- **Idade típica:** 25–45 anos
- **Formação típica:** mesma do Bruno — técnico em eletrônica, mecânica, mecatrônica ou metrologia (Senai/Cefet/IFs). Alguns casos de superior em engenharia (mais comum em farma e alimentos).
- **Anos de experiência:** 3–15 anos.
- **Remuneração típica BR:** **mesma do Bruno** — R$ 2.500–5.500/mês CLT + diária + comissão; sênior R$ 5-8k. **Gap salarial observado em campo:** 5-12% a menos pra mulher em mesma função (CAGED 2025; mitigação via política interna do tenant). `[a confirmar]`
- **Localização típica:** mesmo eixo industrial; **concentração em RS/SP/MG/farma de Anápolis-GO**.

### Contexto de trabalho — pautas extras vs Bruno
- **Mesmo trabalho de campo** (balança rodoviária, manômetro em refinaria, balança em frigorífico) com **considerações adicionais**:
  - **Vestiário feminino** raramente disponível em refinaria, mina, frigorífico antigo, usina sucroenergética — Bruna troca roupa no carro, banheiro improvisado, ou usa o masculino com "guarda" de colega.
  - **EPI feminino** (botina, capacete, óculos, luva, macacão) ainda não é padrão em todo cliente — Bruna recebe EPI masculino que não veste bem, atrapalha agilidade e segurança.
  - **Segurança em campo:** evitar entrar sozinha em obra/cliente com ambiente machista; dupla sempre que possível; check-in com gerente a cada chegada.
  - **Gestante temporária:** restrição de calibração em ambiente de risco químico (refinaria, farma com solvente, frigorífico com amônia); precisa de **alocação alternativa por 9 meses + puerpério** — sistema deve permitir flag de restrição temporária no perfil do técnico.

### O que ela quer (além do que Bruno quer)
- **Vestiário e EPI adequados** declarados pelo cliente ANTES de ela aceitar a OS.
- **Dupla técnica** em cliente novo/inseguro (sistema sugere par automaticamente).
- **Possibilidade de recusar OS** em cliente com histórico de assédio (sistema permite flag confidencial).
- **Status "gestante" no perfil** (oculto pra cliente, visível pra gerente) que recalibra automaticamente roteiros pra ambientes seguros.
- **Equilíbrio jornada/maternidade** — folga sexta com filho doente, sem disputa.

### JTBDs principais
Mesmos do Bruno: JTBD-021 (saber tudo da próxima OS), JTBD-022 (executar offline), JTBD-023 (coletar leitura pelo celular), JTBD-024 (assinatura no celular), JTBD-025 (não voltar pra "encerrar OS"). **JTBD-NOVO-bruna** (perfil do técnico declara restrições temporárias — gestante, lesão, EPI especial).

### Dores principais
D-005, D-006, D-019 (compartilhadas com Bruno). **D-NOVO-bruna** (sistema não modela restrições temporárias / segurança de gênero em campo).

### O que a deixa louca (além das dores do Bruno)
- "Refinaria não tem vestiário feminino. Eu calibro com o EPI emprestado de um cara que tem o pé 4 números maior."
- "Frigorífico antigo só tem 1 banheiro misto na entrada — fila de 30 funcionários homens. Eu seguro 8h."
- "Cliente novo no interior — fui sozinha, o gerente flertou o tempo todo, ambiente péssimo. Avisei o Roldão; ele falou 'aguenta, contrato é grande'."
- "Engravidei e tive que sair da operação de campo por 9 meses — sistema não tem como marcar 'restrição temporária', minhas OS continuaram caindo pra mim, gerente esquecia."
- "Volto da licença, sou alocada em OS de bancada interna por 3 meses — sem aviso, sem combinado."

### Como o sistema deve responder (features específicas)
- **Perfil do técnico com campos:** restrições temporárias (gestante, lesão, retorno gradual), EPI especial necessário, preferência por dupla.
- **Cadastro do cliente final:** marcar "vestiário feminino disponível?", "EPI feminino disponível?", "histórico de incidente de segurança?" — sistema bloqueia atribuição de OS pra Bruna em cliente sem condições mínimas, ou alerta o gerente.
- **Modo "dupla obrigatória"** — checkbox por OS / por cliente.
- **Flag confidencial "não enviar"** — Bruna pode marcar cliente como "recusado" sem ter que justificar pra gerente homem.

### Frase-chave
> "Refinaria não tem vestiário feminino. Eu calibro com o EPI emprestado."

### Variações por perfil de empresa
- **Perfil A em farma/alimentos:** ambiente mais favorável (cliente já tem EPI feminino, vestiário, política DEI); Bruna mais presente.
- **Perfil B/C/D:** ambiente inconsistente; Bruna mais rara mas crescendo.
- **Refinaria/petroquímica/mina:** ainda muito masculino; Bruna minoritária; pautas de segurança críticas.

### Sinais pra entrevista qualitativa (Onda 2 — 2-3 técnicas)
- "Última vez que você não teve vestiário no cliente — o que fez?"
- "Cliente onde você se sentiu insegura — como sinalizou pro gerente?"
- "EPI feminino — quem fornece, lab ou cliente?"
- "Sistema do seu lab atual modela alguma restrição temporária?"
- "Se eu te der app que sinaliza 'esse cliente tem vestiário' — você usa?"

---

## Persona 14 — Roldão Sênior 65+ (Dono PME veterano)

> **Contexto:** variação da Persona 1 (Roldão principal). **Dono que abriu a empresa nos anos 80-90 e nunca passou pra filho**, mantém-se no comando aos 65+. **Decisor de compra** mas com necessidades de acessibilidade marcantes — óculos bifocal, dificuldade com formulário longo, baixa familiaridade com SaaS moderno. **Crítico pra UX:** se o sistema não funcionar pra ele, ele não compra (e bloqueia compra de qualquer concorrente também). `[a confirmar via entrevista — 2-3 donos PME 65+ do setor]`

### Identidade
- **Nome fictício:** Roldão Mendes Sênior (Sr. Roldão pros funcionários)
- **Idade típica:** 65–78 anos
- **Formação típica:** técnico em eletrônica ou mecânica (Senai dos anos 70-80) + cursos livres ao longo de 40 anos de operação. Frequentemente não tem ensino superior; conhecimento técnico profundo construído na prática.
- **Anos de experiência:** **35–55 anos** no setor (abriu empresa nos anos 80-90; era técnico antes).
- **Remuneração típica BR:** pró-labore + distribuição de lucros — varia muito; em PME consolidada R$ 15-30k/mês equivalente; patrimônio em imóvel + maquinário.
- **Localização típica:** mesmo eixo industrial do Roldão principal — interior consolidado (Caxias do Sul, Joinville, Sorocaba, Volta Redonda).

### Contexto de trabalho
- **Onde trabalha fisicamente:** sala dele com computador desktop (não usa notebook), monitor grande (24"), teclado/mouse físicos.
- **Horário típico:** comercial mais curto (8h–17h); às vezes só meio período; nunca mais "plantão emocional 24/7" como o Roldão principal — delega WhatsApp ao filho ou ao gerente.
- **Reporta a:** ele mesmo + esposa/sócia.
- **Equipe:** 10-50 funcionários; estrutura mais formalizada que o Roldão principal.

### O que ele quer (igual ao Roldão principal + extras de acessibilidade)
- **Igual ao Roldão principal:** faturar previsível, não perder acreditação, reduzir dependência operacional, conhecer custo real, profissionalizar imagem.
- **Extras desta persona:**
  - **Fonte grande** — sistema com texto < 12pt ele não consegue ler com o óculos bifocal.
  - **Botões grandes e bem espaçados** — toque preciso é difícil; clique acidental frequente.
  - **Fluxo curto e linear** — formulário com 30 campos em 5 abas ele abandona; prefere wizard de 3 telas.
  - **Suporte por telefone humano** — não suporta "abra ticket no portal"; quer voz.
  - **Sistema que "lembra" dele** — esqueceu senha 4x essa semana; quer login simples ou biométrico no desktop.

### O que ele rejeita
- **Tela carregada de informação** (dashboard com 20 KPIs).
- **Ícones sem rótulo** (texto sob ícone é regra).
- **Modal/popup que aparece sem aviso**.
- **Cor como único indicador** (daltonismo masculino comum + visão deteriorada).
- **Treinamento online de 4h** — abandona em 30 min; prefere visita presencial.
- **Preço acima de R$ 800/mês** — sensível; valor de SaaS ainda é desconfiável.

### JTBDs principais
Mesmos do Roldão principal: JTBD-001 (saber se mês vai fechar no azul), JTBD-004 (não depender de uma pessoa), JTBD-006 (histórico do negócio na mão), JTBD-013 (visão consolidada), JTBD-039 (saber fluxo 30 dias). **JTBD-NOVO-sênior** (fluxo zero-fricção pra dono que não vai virar power user).

### Dores principais
D-001, D-002, D-010 (compartilhadas com Roldão principal). **D-NOVO-sênior** (sistema moderno desenhado pra geração Z é hostil pra dono 65+).

### O que o deixa louco
- "Esse sistema novo tá em letra miúda — preciso aumentar o navegador. Quando aumento, layout quebra."
- "Tem 7 botões em cima e eu não sei qual usar. Antes tinha 1 botão grande 'Calibrar'."
- "Esqueci senha de novo. Pedi nova; chegou no e-mail; demoro 10 min pra abrir Gmail; perdi o link."
- "Filho me mostrou — 'arrasta pra cima, clica nos 3 pontinhos'. Eu não enxergo os 3 pontinhos."
- "Suporte por chat — eu prefiro telefone. Voz humana resolve."

### Como o sistema deve responder (features específicas — INV-016 WCAG)
- **Fonte escalonável até 200%** sem quebra de layout (responsive type).
- **Contraste forte** (mínimo WCAG 2.1 AA — relação 4.5:1 pra texto normal).
- **Modo de alto contraste** + tema claro tradicional (Roldão Sênior não gosta de dark mode).
- **Botões mín. 44x44px** (recomendado 60x60 pra essa persona).
- **Wizards lineares** com "voltar/avançar" claro (não SPA com 30 abas).
- **Login biométrico** desktop (Windows Hello) ou cookie persistente.
- **Suporte por telefone** humano em horário comercial (não só chat).

### Frase-chave
> "Letra grande, botão grande, e me explica devagar. Eu compro."

### Por que essa persona importa pro produto
- **Define o piso de acessibilidade** que o Aferê deve garantir (INV-016 WCAG 2.1 AA + Lei 13.146/2015 LBI).
- **Mercado real:** ~20-30% dos donos PME do setor calibração no BR têm 60+ anos (estimativa CAGED dono de CNAE 7120-1/00); fatia não-trivial.
- **Risco competitivo:** Cali e concorrentes têm UI dos anos 2010 — pesada, ícones sem rótulo, fluxos longos. Aferê pode liderar em "ERP-pra-dono-veterano" se priorizar acessibilidade.

### Sinais pra entrevista qualitativa (Onda 2 — 2-3 donos PME 60+)
- "Sistema que você usa hoje — o que mais te incomoda na tela?"
- "Já desistiu de algum software por causa de letra/botão pequeno?"
- "Suporte: telefone, chat, ticket — qual você prefere?"
- "Se filho/neto te ajudar com SaaS — o quê ele faz mais?"
- "Treinamento online ou presencial — qual funciona pra você?"

---

## 2.5 Acessibilidade por persona (WCAG 2.1 AA + Lei 13.146/2015 + INV-016)

> **Adição Aud-2 (17/05/2026):** acessibilidade não é "feature extra" — é requisito legal (Lei Brasileira de Inclusão 13.146/2015) + invariante de produto (**INV-016** — sistema deve atender WCAG 2.1 nível AA, ver `normas-e-regulacao.md`). Cada persona tem necessidade específica que o design DEVE contemplar; ignorar = excluir parte do mercado + exposição a ação judicial LGPD/MP-Consumidor.

| Persona | Necessidade prioritária de acessibilidade | Feature obrigatória do produto |
|---|---|---|
| **Bruno (técnico campo)** | Tela legível sob sol forte (outdoor 5.000+ lux); precisão de toque com luva/dedo molhado/sujo; uso em rotação retrato/paisagem | **Contraste forte** (relação ≥ 7:1 modo outdoor), **target size ≥ 48x48px**, **rotação automática**, modo "alto brilho" toggleável |
| **Cláudia (financeiro)** | Trabalho prolongado de tela (8h/dia); fadiga ocular; atalhos pra ganhar produtividade | **Modo escuro/claro/auto**, **atalhos de teclado** pra ações repetitivas (Tab navigation completa), redimensionamento de fonte |
| **Marcos (metrologista)** | Daltonismo masculino comum (~8% pop. masculina BR — deuteranopia/protanopia) | **Cor NUNCA como indicador único** (ex: status de calibração não pode ser só "verde/amarelo/vermelho" — precisa ícone + texto), paleta dalton-safe |
| **Letícia (atendente)** | Multitarefa pesada com áudio (telefone + WhatsApp áudio); ruído ambiente | **Controle de áudio** em notificações, **transcrição automática** de áudio do WhatsApp (integração); legendas em vídeo |
| **Bruno + Bruna (técnicos)** | Trabalho com EPI (luva/capacete/óculos de proteção); destreza fina reduzida | Target size ≥ 60x60px no app mobile; **comando de voz** pra "OK", "próximo", "anexar foto" |
| **João-Sênior (cliente final low-tech)** | Baixa alfabetização digital + idade; aversão a portal/senha | **Fluxo zero-login alternativo** (WhatsApp Business API + SMS + e-mail simples); certificado entregue como imagem JPG, não só PDF |
| **Roldão Sênior 65+ (dono veterano)** | Visão presbiopia + dificuldade motora fina + baixa familiaridade SaaS | **Fonte escalonável até 200%** sem quebra de layout; **contraste forte AA mín / AAA recomendado**; **botões ≥ 44x44px** (60x60 ideal); wizards lineares (não SPA); login biométrico desktop |
| **Carlos (motorista UMC)** | Mobile simplíssimo na cabine do caminhão (1 mão livre); offline na estrada; tela suja de combustível/poeira | **Mobile simplíssimo**, target size 60x60px, **comando de voz** pra confirmar "OK / abasteci R$ X / cheguei", funciona offline 100%, sincroniza ao ter sinal |
| **Sandra (RT qualidade)** | Trabalho com leitor de tela eventual (acessibilidade pra auditor que pode ter deficiência); modo auditoria | **Compatibilidade leitor de tela** (NVDA/JAWS) em todas as telas; navegação por teclado completa; semântica HTML correta |
| **Patrícia (cliente farma)** | Acessibilidade de portal do cliente em ambiente regulado (21 CFR Part 11 + RDC 658/2022 também exigem usabilidade) | Portal cliente WCAG 2.1 AA; exportações PDF/A acessíveis (estrutura semântica preservada) |
| **Auditor Cgcre/IPEM** | Pode ter qualquer condição (presbita, daltônica, etc.); precisa navegar sistema do tenant que não é dele | "Modo auditoria" simplificado + acessível por padrão |
| **Rogério (vendedor)** | Uso em carro (não dirigindo) entre visitas; multitarefa | App mobile responsive; modo offline pra ver pipeline sem internet |
| **Roldão principal (dono)** | Uso em desktop + mobile alternado; pouca paciência com fricção | Atalhos + dashboard configurável + onboarding incremental (não bombardear no dia 1) |
| **Bruna (técnica mulher)** | Compartilha necessidades do Bruno + perfil com flag confidencial visível só pra gerente | Privacidade UI (campo "restrição temporária" oculto pra cliente) |

**Referências normativas:**
- **Lei 13.146/2015** (Lei Brasileira de Inclusão — LBI): art. 63 — acessibilidade de sítios eletrônicos é obrigação legal pra empresas com sede ou representação no BR.
- **WCAG 2.1 nível AA** (W3C, recomendação 2018) — padrão técnico universalmente aceito.
- **WCAG 2.2** (W3C, recomendação 2023) — incrementos opcionais (Aferê pode mirar AA da 2.2 como meta v2).
- **INV-016 (novo)** — invariante de produto: sistema atende WCAG 2.1 AA em **todas as telas críticas** (auth, dashboard, OS, certificado, portal cliente, mobile do técnico). Ver `normas-e-regulacao.md` (pendente: aplicar INV-016 lá).
- **eMAG 3.1** (Modelo de Acessibilidade em Governo Eletrônico) — referência adicional pro mercado público (se Aferê quiser atender lab acreditado de universidade federal / órgão público).

**Conexão com R-NOVO-acessibilidade:** Aferê processado por MP-Consumidor ou ação coletiva por violação de Lei 13.146/2015 — risco real, especialmente se cliente farma/hospital depende do produto e funcionário com deficiência visual não consegue operar.

---

## 3. Síntese cruzada

### 3.1 Quem usa quais módulos do mapa de domínios

> **Nota:** tabela atualizada 17/05/2026 com personas 9-14. Personas externas (não usuárias diretas do ERP, mas que **interagem com o sistema via canal externo OU exigem features específicas**) também aparecem na matriz pra clareza de design.

| Módulo (do `dominio-de-negocio.md`) | Roldão | Sandra | Letícia | Bruno | Marcos | Cláudia | Rogério | Carlos (motorista) | Auditor Cgcre/IPEM | Patrícia (farma) | João-Sênior | Bruna | Roldão Sênior |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CRM | ◐ relatório | — | ◐ ficha | — | — | — | ● principal | — | — | ◐ recebe RFP | — | — | ◐ relatório |
| Orçamentos | ◐ aprova preço | — | ◐ envia | — | — | — | ● principal | — | — | ◐ recebe | — | — | ◐ aprova |
| Chamados/OS | ◐ dashboard | — | ● principal | ● executa | — | — | ◐ inicia | ◐ consome viagem | — | — | — | ● executa | ◐ dashboard |
| Agenda do técnico | ◐ aprova | — | ● cria | ● consome | — | — | — | ◐ consome | — | — | — | ● consome | ◐ aprova |
| Mobile do técnico | — | — | — | ● principal | — | — | — | — | — | — | — | ● principal | — |
| **Frota + UMC** (NOVO) | ◐ aprova compras | — | — | ◐ usa carro | — | ◐ custo | — | ● principal UMC | — | — | — | ◐ usa carro | ◐ aprova |
| **Caixa do técnico/motorista** (NOVO) | ◐ aprova | — | — | ● principal | — | ● concilia | — | ● principal | — | — | — | ● principal | ◐ aprova |
| Estoque/peças | ◐ aprova compra | — | — | ◐ consome | — | ◐ controla | — | — | — | — | — | ◐ consome | ◐ aprova |
| Calibração (execução) | — | ◐ supervisiona | — | ◐ campo | ● lab | — | — | — | ◐ audita | ◐ recebe certif. | ◐ recebe certif. | ◐ campo | — |
| Padrões/rastreabilidade | — | ● principal | — | — | ● consome | — | — | ◐ transporta | ● audita | ● exige | — | — | — |
| Garantia validade (cartas) | — | ● principal | — | — | ● gera dado | — | — | — | ● audita | ◐ exige | — | — | — |
| Metrologia Legal (IPEM) | ◐ alerta cliente | ◐ proced. | ● alerta venc. | ◐ executa | — | — | ◐ vende renov. | — | ● audita (IPEM) | — | ● recebe verif. | ◐ executa | ◐ alerta |
| NFS-e / NF-e | ◐ aprova fat. | — | — | — | — | ● principal | — | — | — | ◐ recebe | ◐ recebe img | — | ◐ aprova |
| Contas a pagar/receber | ◐ aprova pgto | — | — | — | — | ● principal | — | — | — | — | — | — | ◐ aprova |
| Conciliação bancária | — | — | — | — | — | ● principal | — | — | — | — | — | — | — |
| Cobrança | ◐ escalonamento | — | ◐ cliente conhec. | — | — | ● principal | ◐ informal | — | — | — | ◐ alvo WhatsApp | — | ◐ escalonam. |
| RBAC / config tenant | ● principal | ◐ aprova regra | — | — | — | — | — | — | — | — | — | — | ● principal |
| Gestão competências/autorização | — | ● principal | — | — | ● objeto autoriz. | — | — | ◐ doc motorista | ● audita | ◐ exige | — | ● objeto autoriz. | — |
| Conformidade/NC | — | ● principal | — | ◐ reporta campo | ◐ reporta técn. | — | — | ◐ reporta viagem | ● audita | ◐ exige report | — | ◐ reporta campo | — |
| Portal do cliente final | — | — | ◐ orienta uso | — | — | — | ◐ vende diferenc. | — | — | ● usuário principal | **NÃO usa** (canal WhatsApp/SMS) | — | — |
| **Acessibilidade (transversal — INV-016)** | ● beneficiário | ● beneficiária | ● beneficiária | ● contraste outdoor | ● cor não-única | ● escuro/atalhos | ● mobile carro | ● simplíssimo+voz | ● leitor tela | ● portal AA | ● zero-login | ● privacidade UI | ● fonte 200%+botão grande |

**Legenda:** ● = usuário/beneficiário principal; ◐ = usuário/beneficiário secundário; — = não usa / não se aplica.

### 3.2 Quem é signatário em cada perfil

| Perfil | Signatário formal | Sob quais regras 17025 (INV-003) |
|---|---|---|
| **A** | **Marcos** (autorizado RBC, escopo declarado, validade documentada) | Absoluta — bloqueia se autorização vencida ou fora de escopo |
| **B** | Marcos (informal mas tecnicamente qualificado) OU Sandra OU Roldão | Configurável — empresa pode optar por replicar regra A |
| **C** | Sócio técnico / consultor PJ | Configurável — sistema sugere replicar regra A como trilha de aprendizado |
| **D** | Roldão ou técnico sênior (não regulado formalmente) | Desligado por padrão |

### 3.3 Quem se importa com NFS-e / cutover Padrão Nacional 09/2026 (R-016)

- **Cláudia (financeiro):** dor direta — emite todo dia, vai sentir cutover de cara.
- **Roldão (dono):** dor indireta — paga multa, leva bronca de contador.
- **Letícia (atendente):** dor secundária — cliente liga reclamando de nota errada.
- **Sandra, Marcos, Bruno, Rogério:** não tocam diretamente.

### 3.4 Decisores vs influenciadores na compra do software (B2B típico)

| Persona | Papel na compra |
|---|---|
| **Roldão** (ou **Roldão Sênior 65+**) | **Decisor final** (assina contrato, paga). Roldão Sênior tem **veto adicional de acessibilidade** — se UI não funciona pra ele, ele recusa por experiência própria |
| **Sandra** | **Veto técnico** (perfil A) — se diz "não valida cl. 7.11", Roldão não compra |
| **Marcos** | **Veto técnico** (perfil A) — se diz "não confio no cálculo de incerteza", Roldão não compra |
| **Patrícia (cliente farma)** | **Veto externo** — se ela rejeita o lab que usa Aferê em RFP, Roldão perde contrato; influencia roadmap (21 CFR Part 11, IQ/OQ/PQ) |
| **Cláudia** | **Influenciadora forte** — se diz "vai parar minha NFS-e no dia 5", Roldão adia |
| **Letícia** | **Usuária diária crítica** — adoção dela faz ou desfaz |
| **Bruno + Bruna** | **Usuários diários críticos em campo** — se app travar, todos param |
| **Carlos (motorista UMC)** | **Usuário operacional** (em tenant A/B com UMC) — se prestação de contas frustrar, motorista sabota uso, frota fica sem controle |
| **Auditor Cgcre/IPEM** | **Veto externo regulatório** — auditoria que dá NC maior por causa do sistema = Roldão troca de sistema imediatamente |
| **João Eng. / João-Sênior** (cliente final) | **Influenciador retentivo** — bom portal/canal externo = cliente final feliz = Roldão renova SaaS; canal ruim = Roldão troca |
| **Rogério** | **Influenciador moderado** — se ajuda comissão, ele vira advogado interno |

**Implicação:** demo de venda precisa endereçar **Roldão (visão dono) + Sandra/Marcos (técnico) + Cláudia (fiscal) + Patrícia (cliente farma quando aplicável)** em paralelo. Vender só pro Roldão e cair no veto técnico do Marcos é fracasso recorrente do mercado (Cali entendeu isso e tem demo "técnica" separada). Vender pra perfil A sem responder Patrícia (cliente farma) = perda de mercado premium.

### 3.5 Quem é mais relevante por perfil de empresa

| Perfil | Personas mais ativas | Personas inativas / acumuladas |
|---|---|---|
| **A (acreditado RBC)** | Roldão (ou Roldão Sênior) + Sandra + Marcos + Cláudia + Rogério + Letícia + Bruno + Bruna + **Carlos (se opera UMC)**; **Auditor Cgcre** entra periodicamente; **Patrícia** (cliente farma) influencia compra | — |
| **B (rastreável)** | Roldão (acumula Sandra), Marcos (informal), Letícia, Bruno+Bruna, Cláudia, Rogério, **Carlos (raro — só se opera UMC)**; **Auditor IPEM** entra se atende balança comercial; **João-Sênior** comum no mix de clientes finais | Sandra inexiste como cargo formal |
| **C (em preparação)** | Roldão (acumula Sandra + Marcos + Cláudia), Letícia, Bruno+Bruna, Rogério; **João-Sênior** dominante em clientes finais | Sandra e Marcos formais inexistem; Carlos/UMC quase nunca |
| **D (comercial)** | Roldão (acumula quase tudo), Letícia, Bruno+Bruna; **João-Sênior** dominante em clientes finais | Sandra, Marcos, Carlos não existem; Patrícia (farma) não compra deste perfil |

---

## 4. Próximos passos

### 4.1 Validação via entrevistas qualitativas

- **Onda 1 (Roldão como sujeito):** validar persona 1 (Roldão) com profundidade. Usar `treinamento-entrevista-roldao.md` como guia.
- **Onda 2 (5–10 empresas externas):** entrevistar 1–2 representantes por persona (especialmente Sandra, Marcos, Letícia, Bruno+Bruna, **Carlos motorista UMC**, **Auditor Cgcre/IPEM ex-funcionário**, **Patrícia farma**, **João-Sênior açougueiro**, **Roldão Sênior 65+**) em outras empresas — mitigação obrigatória de **R-001 (founder is customer)** e **R-004 (TAM ridículo)**.
- **Mínimo aceitável antes de "personas v1.0":** 2 entrevistas por persona em empresas que NÃO são a do Roldão. Para as 6 personas novas (9-14), mínimo aceitável é **1 entrevista cada** na primeira passada (orçamento de discovery limitado), com meta de chegar a 2 antes de virar input pra UI/feature.

### 4.2 Refinamento iterativo

- Cada entrevista atualiza o respectivo bloco (frustrations, ferramentas, goals).
- Variações por perfil A/B/C/D precisam ser confirmadas — hoje são inferência educada.
- Salário, idade, formação são inferências de mercado; revalidar com 3+ amostras antes de virar invariante.

### 4.3 Saídas pra outros artefatos do Discovery

- `jobs-to-be-done.md` — extrair 1 JTBD principal por persona + 2–3 JTBDs secundários.
- `dores-mapeadas.md` — cada frustração vira candidata a dor; cruzar com soluções do produto.
- `opportunity-solution-tree.md` — Goals + Frustrations alimentam topo da árvore.
- `jornada-atual-sem-produto.md` — narrar 1 jornada de "Letícia recebe chamado até Cláudia recebe pagamento" + 1 jornada de "Marcos emite certificado" usando estas personas como atores.
- `docs/comum/personas.md` (futuro) — versão filtrada/condensada de 1 página por persona, pra ser referência interna do produto.

### 4.4 Lacunas explicitamente `[a confirmar]` a fechar

- Salários BR específicos por persona (faixa atualizada 2026).
- Tamanho médio típico da equipe por papel em PME calibração (5–50 é faixa larga demais).
- Variação real entre perfis A/B/C/D no dia a dia operacional (hoje é inferência).
- Adoção real de calibrador documentador (Beamex/Fluke/Presys) no perfil-alvo brasileiro.
- Adoção real de e-CPF ICP-Brasil A3 pra assinatura de certificado vs "imagem em PDF".
- Receptividade de João (cliente final) ao portal — testar com WTP em `validacao-ativa.md`.
- Disposição de pagar (willingness to pay) do Roldão por perfil — entrada pra `precificacao-mercado.md`.

---

> **Lembrete (regra global Discovery — `feedback_discovery_completo.md`):** essas personas são mitigação direta do risco "founder is customer". **Não reduzir profundidade** sob argumento de "lean / MVP rápido". Refinar com entrevistas até estabilizar antes de virar input pra UI/feature.
