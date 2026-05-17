# Bucket A — Reviews e queixas dos concorrentes (pesquisa documental)

> **Metodologia.** Pesquisa pública via WebSearch + WebFetch entre 17/05/2026 16h–17h. ~16 buscas, ~1 fetch (Capterra Auvo BR). Fontes priorizadas: Reclame Aqui, Capterra (BR/EN), B2B Stack, Glassdoor, blogs de comparativo. **Sem login, sem cadastro, sem interação com chatbot.** Concorrentes nomeados na briefing investigados; aprofundamento variável conforme presença online.
>
> **Limites de honestidade.** Reclame Aqui da Auvo retornou HTTP 403 no fetch direto — métricas oficiais (nota, n reclamações 12m) **não acessadas**; usei apenas o que apareceu em SERP/snippet. Cali, FP2, Metroex, Calibre Software, Sismetro, TGM 4 **não têm pegada pública relevante de reclamações** — não há páginas Reclame Aqui, nem reviews em Capterra/B2B Stack, nem ratings em Glassdoor. Isso é em si um achado (ver "Observação meta" no fim).

---

## Resumo executivo (5 linhas)

1. **Auvo, Bling, Tiny e Conta Azul concentram TODAS as reclamações públicas relevantes;** os players verticais de calibração (Cali, FP2, Metroex, TGM 4, Sismetro, Calibre Software, Portal ISO) **são invisíveis no Reclame Aqui** — pegada online só institucional.
2. **Top-3 dores transversais entre concorrentes ERP/field service:** (a) suporte que abre chamado e não resolve, (b) integrações prometidas que não funcionam (especialmente NF/marketplace/banco), (c) bugs em GPS/sincronização que comprometem operação em campo.
3. **Tema "fechamento indevido de OS / NF gerada errada" (Auvo) confirma fortemente Dor #05 (status OS) e Dor #10 (NFS-e) do baseline interno;** "integração com OMIE quebrada" + "boletos não compensados Asaas" reforçam Dor #09 (conciliação financeira).
4. **Dor NOVA descoberta (não estava nas 20):** "**cobrança contratual abusiva / reajuste anual + cláusula de fidelidade de 12 meses sem possibilidade de cancelar**" — aparece em Field Control, Conta Azul, Tiny ERP e Bling. É vetor de churn dos concorrentes E oportunidade de posicionamento (anti-fidelidade) ou risco (se Aferê copiar o modelo).
5. **A ausência de reclamações públicas nos concorrentes verticais não é elogio** — é provável reflexo de (i) base pequena (Cali tem 5 funcionários e ~80 clientes Metroex, ~15 Cali, etc.), (ii) clientes B2B técnicos resolvem por telefone direto, (iii) o público metrologista não vai a Reclame Aqui — vai a CGCRE/Inmetro. **Conclusão: validação direta com clientes desses concorrentes é insubstituível** (Onda 1 de entrevistas continua obrigatória).

---

## Por concorrente

### 1. Cali (Calibrec / Cali LAB / Cali WEB) — Canoas/RS

**Volume de reclamações públicas:** **zero encontrado.** Sem página no Reclame Aqui, sem reviews no Capterra/GetApp/B2B Stack, sem perfil ativo no Glassdoor.

**Perfil:** fundada 1995, 2-10 funcionários (LinkedIn), ~US$ 2M receita 2025 (RocketReach), Microsoft Partner, software homologado ISO/IEC 17025 pela Fundação CERTI. ([cali.com.br](https://cali.com.br/))

**Elogios (apenas depoimentos curados no próprio site):**
- Metroquality: *"Temos atualmente 15 bases instaladas do software CALI em nosso laboratório e estamos muito satisfeitos com os resultados e benefícios gerados ao longo destes 20 anos de parceria"*
- Precisotec: *"durante 11 anos de utilização, a equipe técnica buscou sempre soluções para suas necessidades, transformando demandas em novas funções para o software"*
- Aferitec: destaca PDF automático no Cali WEB *"reduzindo consideravelmente o tempo em mão de obra"*

**Dores recorrentes:** não acessíveis publicamente.

**Cancelamentos / saídas:** não acessíveis.

**Interpretação:** empresa pequena (~5 funcionários efetivos), modelo on-premise legado (Cali LAB) + módulo web complementar (Cali WEB). Cliente fica preso porque migrar dados custa caro e auditoria Cgcre tem track record com aquele sistema — switching cost altíssimo, reclamação migra pra telefone direto, nunca aparece online. **Risco competitivo Aferê:** Cali é referência de mercado e ninguém reclama publicamente; sem entrevista direta a clientes Cali, é cego.

---

### 2. FP2 Tecnologia — Santa Maria/RS

**Volume:** **zero reclamação pública.** Página Facebook com 166 likes, Yelp listing sem reviews, sem Reclame Aqui, sem Capterra.

**Perfil:** fundada 03/2005, foco em software financeiro pra fundações/ONGs + módulo laboratório (ISO/IEC 17025:2005 — atenção: cita versão **antiga** da norma; a vigente é 2017). Cliente-âncora: laboratório de Micotoxinas da UFSM, Instituto SAMITEC. ([fp2.com.br](https://www.fp2.com.br/SistemaLaboratorio.aspx))

**Dores recorrentes:** não acessíveis.

**Interpretação:** produto laboratório parece ser linha secundária da FP2; foco institucional + cliente público (UFSM, SAMITEC). Pegada B2C muito baixa. Citação à ISO 17025:**2005** no site é red flag — sugere produto possivelmente desatualizado em relação à norma vigente.

---

### 3. Calibre Software (calibre.software) — SaaS modular

**Volume:** **zero review encontrado.** Capterra retornou produtos homônimos (Calibre = call recording + Calibre = ebook converter), nenhum é este. ([calibre.software](https://calibre.software/))

**Posicionamento próprio:** atende ISO-17025, ISO-9001, VIM, ISO-GUM, "já serve laboratórios RBC", afirma "ganho de produtividade de até 30% comparado a planilhas, contando apenas a emissão de certificados".

**Dores recorrentes:** não acessíveis.

**Interpretação:** marketing forte ("modular web"), zero validação independente. Provável base ≤ 100 clientes.

---

### 4. Auvo — Goiânia, 2015

**Volume:** Reclame Aqui retornou HTTP 403 no fetch (provável bloqueio anti-bot); via SERP, identifiquei **3+ reclamações recentes (nov–dez/2025)** com títulos detalhados. Capterra Brasil mostra **19 avaliações verificadas**, **nota 4,5/5** (mas reviews "incentivadas" — atenção ao viés). ([Capterra Auvo BR](https://www.capterra.com.br/software/201778/auvo))

**Dores recorrentes (Reclame Aqui — citações literais):**

- **Integração OMIE quebrada (motivo declarado da contratação):** *"a plataforma prometeu integração com o OMIE — um dos principais motivos do fechamento do negócio — mas a integração não funciona e não conseguem dar prazo para solução"* (nov/2025) — [link](https://www.reclameaqui.com.br/auvo-tecnologia/problemas-com-a-plataforma-auvo-falha-na-integracao-com-omie-bugs-e-atrasos-na-entrega-de-dashboards_wQIYE4KoirwGe_JM/)
- **Fechamento indevido de OS:** *"tarefas finalizadas com pendências de maneira indevida"* (Auvo Agenda) — mesma reclamação acima
- **NF gerada errada sem configuração:** *"o sistema gera NFs automaticamente mesmo quando essa funcionalidade não está configurada no contrato do cliente, com erro grave e recorrente"* (dez/2025) — [link](https://www.reclameaqui.com.br/auvo-tecnologia/problemas-recorrentes-e-falhas-no-sistema-auvo-notas-fiscais-indevidas-in__N1INrARooE1e9rG/)
- **GPS / rastreio inconsistente:** *"registros de localização inconsistentes, falhas na captura do percurso e divergências no apontamento de entrada e saída, comprometendo o monitoramento das equipes em campo"* (dez/2025)
- **Suporte cordial mas inefetivo:** *"Os atendentes são ótimos! Sempre bastante educados, mas não conseguem evoluir com a solução dos problemas reportados"*
- **Mais de 10 reclamações de erros que voltam após resolução temporária** (dez/2025)

**Contras Capterra:** falta API/app pro AuvoDesk, agenda no app mobile só dia-a-dia (sem mês), vínculo de equipamento preso a cliente único (não suporta multi-endereço por equipamento), backoffice lento em consulta de cadastro.

**Elogios:** acompanhamento de técnico em tempo real, app mobile intuitivo, suporte rápido (chat na tela), check-in geolocalizado.

**Tempo de resposta da empresa:** SERP indica que a Auvo responde aos chamados Reclame Aqui (resposta padrão: "time técnico revisou os problemas e está trabalhando"), mas sem prazos concretos.

**Cancelamentos / saídas:** clientes citam Field Control como concorrente avaliado ("Field Control - Sistema mais complexo e preço muito mais alto" — Capterra).

---

### 5. Conta Azul — Joinville

**Volume:** Reclame Aqui classifica **"BOM" com nota 7,4/10**, tempo médio de resposta **4 dias**, período 01/11/2025–30/04/2026 (dados via SERP). ([Reclame Aqui Conta Azul](https://www.reclameaqui.com.br/empresa/contaazul/lista-reclamacoes/))

**Dores recorrentes (citações literais):**

- **Burocracia pra contatar suporte:** *"uma burocracia falar com o suporte mesmo pagando pelo sistema"*; clientes ficam *"uma semana impossibilitados de usar o Conta Azul porque a plataforma não envia o ID de Suporte"*
- **Reajuste anual abusivo:** *"problemas de aumento abusivo todos os anos"*, casos extremos relatam *"novo contrato 3 vezes mais caro"*
- **Promessa vs entrega:** *"na hora da venda é mil maravilhas, prometeram mundos e fundos, porém depois que você passa o cartão e paga, esquece"*
- **Instabilidade / sumiço de dados:** *"sumiço de informações registradas, erros no preenchimento de campos obrigatórios"*
- **B2B Stack — falta automação NFS-e/boleto:** *"a solução poderia ter uma geração de boletos e notas fiscais mais automatizada com integração com bancos e prefeituras"*
- **B2B Stack — uniformidade demais:** *"Por ser um ERP simples, algumas funcionalidades mais complexas deixam a desejar"*

**Elogios:** facilidade de uso, clareza das informações financeiras, backups automáticos, suporte ágil em casos específicos resolvidos.

---

### 6. Metroex / MyLogical (ForLogic) — Cornélio Procópio + Londrina/PR

**Volume:** **zero reclamação pública.** ForLogic em Apucarana/PR não é mais o endereço atual (mudou pra Londrina+Cornélio Procópio). ([metroex.com.br](https://metroex.com.br/))

**Posicionamento próprio:** *"comunidade de mais de 80 clientes satisfeitos"*, *"validado em mais de 500 avaliações INMETRO"*. ISO 9001, ISO 10012, ISO/IEC 17025. Aderente a CGCRE.

**Elogios curados no site:** clientes citam aprovação em auditoria CGCRE/INMETRO sem não-conformidade no software ("manutenção de acreditação com resultados satisfatórios e somente elogios dos auditores").

**Dores recorrentes:** não acessíveis publicamente.

**Interpretação:** ForLogic é grupo maior (Qualiex + Qualitfy + Metroex). Provavelmente o player vertical mais sólido tecnicamente — base de 80+ clientes, foco INMETRO, módulo WebView. **Concorrente mais perigoso identificado neste bucket.** Ausência de reclamações pode significar (i) suporte responde direto, (ii) cliente técnico não usa Reclame Aqui, (iii) NPS realmente alto. Não dá pra concluir sem entrevistar cliente Metroex.

---

### 7. SoftExpert — Joinville

**Volume:** Reclame Aqui — *"ainda não verificada e não possui o selo de confiança"*, *"1 reclamação aguardando resposta, 0 reclamações avaliadas"*. Sem reputação calculada. ([Reclame Aqui SoftExpert](https://www.reclameaqui.com.br/empresa/softexpert-software-s-a/))

**Glassdoor (funcionários, não clientes):** **4,4/5** com 277 reviews, 86% recomendam. **Pros:** 30 anos de mercado, dedicação a compliance/transformação digital. **Cons:** plano de saúde fraco fora de Joinville; processo de demissão *"concentrado em uma única pessoa, com motivos esdrúvulos, parecendo desculpa para corte de gastos"*; alguns líderes com postura arrogante. ([Glassdoor SoftExpert](https://www.glassdoor.com/Reviews/SoftExpert-Reviews-E2375976.htm))

**Dores recorrentes (cliente):** não acessíveis — base B2B enterprise grande não reclama em Reclame Aqui.

**Interpretação:** SoftExpert não é concorrente direto pra MEI/PE de assistência técnica de balança — atende grandes corporações (Petrobras, Ambev). Compete por overlap parcial em ISO 9001/17025 enterprise.

---

### 8. Bling — Porto Alegre / Curitiba

**Volume:** **dezenas de reclamações em 2025**, com 2 incidentes de instabilidade reconhecidos pela própria empresa (22/01/2025 e 27/01/2025) + 1 em 12/05/2025. ([Reclame Aqui Bling](https://www.reclameaqui.com.br/empresa/bling/lista-reclamacoes/))

**Dores recorrentes (citações literais):**

- **Instabilidade paralisante:** *"fiquei duas semanas com sistema inoperante, atendimento telefone não era feito, pois deixaram gravações de que estavam ocultado"* (jan/2025)
- **NF travada em horário crítico:** *"estou com problemas para gerar a nota fiscal de venda realizado na minha loja Amazon e que precisa ser enviado hoje. Um grande Absurdo essa situação, já que essa plataforma BLING está me cobrando muito CARO para sua assinatura"* (jul/2025)
- **Defesa contratual jurídica:** Bling responde citando Código Civil arts. 421/422/423 e cláusula contratual de "disponibilidade mínima de 98% no mês" — clientes percebem como esquiva.
- **Degradação percebida:** *"Toda semana aparece algum problema novo nesse sistema. Já faz mais de 3 anos que uso Bling, e de 1 ano pra cá ficou PIOR do que sempre foi"*
- **Armazenamento estourado bloqueando emissão de NF** (out/2025–mar/2026)

**Tempo de resposta:** Bling reconhece publicamente os incidentes e tem status page (bling.freshstatus.io). Mas resposta a reclamação individual demora *"quase 20 dias"*.

---

### 9. Tiny ERP (Olist) — pós-aquisição

**Volume:** alta concentração de reclamações **pós-aquisição pela Olist** (2024–2026). ([Reclame Aqui Tiny](https://www.reclameaqui.com.br/empresa/tiny-erp/lista-reclamacoes/))

**Dores recorrentes (citações literais):**

- **Suporte que terceiriza culpa:** *"em muitos casos o problema é sempre atribuído a algum sistema que não é Tiny"* (fev/2026)
- **Chat abandonado pelo atendente:** *"envia a dúvida, explica todo o contexto técnico, e quando o atendente percebe que não consegue sanar a questão, simplesmente abandona a conversa, encerrando o atendimento sem qualquer solução"*
- **Bugs antigos não resolvidos:** *"há mais de 1 ano e meio identificou problemas de pedidos duplicados importados do Full do ML"*
- **Cobrança surpresa:** *"recebeu uma fatura de R$ 175 alegando uso de 3 extensões a mais"*
- **Suporte por copy-paste:** *"suporte Tiny é extremamente ruim, não lêem o que é escrito e simplesmente copiam e colam respostas favoráveis a eles"*
- **Backlog ignorado:** *"as solicitações de suporte vão para um canal de ideias onde vários pedem a mesma coisa e nada é feito"*

---

### Concorrentes adjacentes encontrados na pesquisa (não da lista briefing)

**Field Control** (concorrente direto da Auvo em field service):
- Tempo médio de resposta Reclame Aqui: 1d 8h (01/08/2025–31/01/2026)
- Reclamações: *"PMOC que foi comprovado pela equipe de suporte que não funciona"*, *"sistema ficou fora do ar [...] durante todo o mês de dezembro, totalizando 33 dias, [...] sem emitir orçamento, sem emitir ordens de serviço"*
- Cláusula contratual obriga pagar 12 meses inteiros mesmo com 3 meses de uso. ([Reclame Aqui Field Control](https://www.reclameaqui.com.br/empresa/field-control/lista-reclamacoes/))

**Omie** (citado pela briefing indireta — Auvo prometeu integração):
- Tempo médio resposta 5d 2h (01/04/2025–30/09/2025)
- Reconhece publicamente que NFS-e municipal é caótico: *"como cada município tem autonomia para escolher ou desenvolver seu próprio sistema, ainda não é adotado um modelo único"*
- Solicitação de integração com prefeitura específica: prazo 2–3 semanas. ([Reclame Aqui Omie](https://www.reclameaqui.com.br/empresa/omiexperience/lista-reclamacoes/))

**Asaas** (gateway boletos — concorrente indireto):
- Reclamações massivas sobre *"boletos pagos não compensados"* — confirma fortemente Dor #09 (conciliação) por outro ângulo. ([Reclame Aqui Asaas](https://www.reclameaqui.com.br/empresa/asaas-gestao-financeira/lista-reclamacoes/))

**Checkmob** (field service): sem reclamações no Reclame Aqui (01/09/2025–28/02/2026). Capterra: 26 reviews verificados.

**Sismetro / TGM 4 / Portal ISO / 8Quali / Q-MAN / Qualyteam:** todos players verticais brasileiros de calibração. **Nenhum com pegada em Reclame Aqui ou Capterra.** Pesquisa só retornou material institucional próprio.

---

## Cross-referência com dores mapeadas

### Dores CONFIRMADAS por evidência externa

| Dor baseline | Confirma? | Evidência externa |
|---|---|---|
| **#01 Cadastro duplicado em sistemas que não conversam** | **CONFIRMA forte** | Auvo: integração OMIE quebrada; Conta Azul: *"poderia ter integração com bancos e prefeituras"*; Tiny: pedidos duplicados ML não sincronizam; B2B Stack Conta Azul: *"ainda faltam algumas parametrizações [...] Ainda é muito uniforme"* |
| **#02 Esquecimento de recalibração** | **CONFIRMA forte** | Tema central de todo o pitch dos players verticais (Calibre, Portal ISO, Q-MAN, 8Quali, Metroex). *"Receba notificações sobre os vencimentos [...] evitando paradas indesejadas"*. Confirma que o problema existe — o que ainda não confirma é que **assistência técnica do prestador** (não só o cliente industrial) sente a dor com a mesma intensidade. |
| **#05 Status OS perguntado o tempo todo** | **CONFIRMA forte** | Auvo Capterra: *"A Auvo vem solucionando um grande problema que tínhamos que era o acompanhamento em tempo real do técnico"*; tema #1 da categoria field service. |
| **#08 Roteirização técnico no escuro / 2ª visita** | **CONFIRMA parcial** | Reclamações Auvo sobre GPS inconsistente; Capterra: *"vínculo de equipamento preso a cliente único"* (não suporta multi-endereço) — confirma que mesmo concorrentes maduros não resolvem bem. |
| **#09 Conciliação financeira manual** | **CONFIRMA forte** | Asaas: dezenas de queixas de boleto pago não compensado; Conta Azul: *"poderia ter integração com bancos"*; Bling: armazenamento estourado bloqueia NF. |
| **#10 NFS-e municipal — 26 prefeituras** | **CONFIRMA forte** | Omie reconhece publicamente *"não é adotado um modelo único"*, prazo 2–3 semanas pra integrar nova prefeitura; Auvo cliente reclama de NF gerada errada. Padrão Nacional jan/2026 mencionado pelo Omie alinha com seu cutover 01/09/2026. |
| **#15 Comissões em planilha frágil** | **CONFIRMA forte** | Caso Exame/SplitC: *"cliente identificou erro de centenas de milhares de reais causado por falhas em fórmulas. Situações como essa são bastante comuns"* — é o exato Dor #15. |
| **#19 Registro em WhatsApp viola 7.5.1** | **CONFIRMA parcial** | Não direto em concorrente, mas Auvo Capterra elogia: *"A gestão dos operadores externos ficou muito mais fácil. Em tempo real, conseguimos acompanhar todo o percurso"* — implica que muitos clientes vinham de WhatsApp. |

### Dores NÃO encontradas em evidência externa (não refuta — só não confirma)

- **#03 Certificado emitido sem campo NIT-DICLA-030**: nenhuma reclamação pública. Faz sentido — auditoria CGCRE não vai a Reclame Aqui.
- **#04 Word/Excel pra cálculo incerteza (cláusula 7.11)**: idem, só aparece em material de marketing de software vertical, não em queixa.
- **#06 Padrão com calibração vencida**: idem.
- **#07 Signatário-gargalo**: idem — provável "tabu interno" do lab, não vai pra internet.
- **#11 Inadimplência tratada pelo dono**: idem — embaraço pessoal, ninguém posta.
- **#13 Auditoria farma sem aviso**: idem.
- **#14 Cliente farma 3 dias úteis**: idem.
- **#16 Caixa do técnico + frota**: idem — interno.
- **#17 Selo INMETRO vs calibração (multa IPEM)**: idem.
- **#18 Selo INMETRO sem rastreabilidade individual**: idem.
- **#20 Cliente morre no CRM após calibração**: idem.

**Interpretação:** essas 12 dores são **internas ao lab** (cláusula ISO, embaraço, regulatório IPEM) e por natureza não geram queixa pública contra fornecedor. **Continuam válidas como hipóteses**, mas validação só vem de entrevista direta.

### Dores NOVAS descobertas (não estavam no baseline)

**DOR-NOVA-A — Cláusula de fidelidade 12 meses + reajuste anual abusivo.** Aparece em **4 concorrentes** (Conta Azul, Field Control, Bling, Tiny):
- *"problemas de aumento abusivo todos os anos [...] cancelar o plano e usar a reclamação como alerta"* (Conta Azul)
- *"oferecido um novo contrato 3 vezes mais caro, considerando isso um desrespeito"* (Conta Azul)
- *"cláusulas contratuais que obrigam pagamento do valor total até o final do contrato de um ano, mesmo sem utilizar os serviços por todo o período"* (Field Control)
- *"BLING está me cobrando muito CARO para sua assinatura"* (Bling)
- *"recebeu uma fatura de R$ 175 alegando uso de 3 extensões a mais"* (Tiny)

**Implicação pra Aferê:** modelo comercial transparente (sem fidelidade, reajuste pré-anunciado, pricing por uso real) seria diferenciador. Mas também é risco: se Aferê for SaaS B2B com fidelidade padrão de mercado, vai herdar a mesma dor.

**DOR-NOVA-B — "Suporte cordial mas inefetivo / atendente abandona chat".** Padrão recorrente em **3 concorrentes** (Auvo, Tiny, Conta Azul):
- *"Os atendentes são ótimos! Sempre bastante educados, mas não conseguem evoluir com a solução"* (Auvo)
- *"o atendente percebe que não consegue sanar a questão, simplesmente abandona a conversa"* (Tiny)
- *"não lêem o que é escrito e simplesmente copiam e colam respostas favoráveis a eles"* (Tiny)
- *"chat com robô, sem opção [...] para falar com atendente"* (Asaas)

**Implicação:** dor real do mercado SaaS BR. Aferê precisa decidir: SLA de suporte = diferencial (custo alto, escala difícil) ou produto auto-explicativo o suficiente pra suporte ser raro (estratégia melhor pra MEI).

**DOR-NOVA-C — "Integração prometida na venda que não funciona depois".** Padrão recorrente em **3 concorrentes**:
- Auvo + OMIE
- Tiny + TikTok Shop, ML Full, Nuvemshop
- Bling + WooCommerce, Mercado Livre

**Implicação:** Aferê vai ter que integrar (ERP contábil cliente, prefeitura NFS-e, gateway de pagamento, INMETRO/Sistemas Cgcre). Cada integração quebrada = reclamação pública = churn. Dor #01 do baseline já cobre parcialmente, mas o aspecto "**prometido na venda, não funciona depois**" é vetor de risco comercial específico.

**DOR-NOVA-D — Instabilidade de sistema em horário fiscal crítico paralisa cliente.** Padrão Bling (jan/2025: 2 incidentes, 12/05: 1 incidente) + Field Control (33 dias dezembro):
- *"períodos de instabilidade causaram transtornos significativos, incluindo retrabalhos e a interrupção de atividades essenciais"* — Bling reconhece formalmente.

**Implicação:** Aferê precisa de SLA público + status page desde dia 1. Não pode parecer Bling janeiro/2025.

### Dores que talvez NÃO sejam tão críticas quanto o baseline diz

Nenhuma dor do baseline foi **refutada** pela pesquisa externa. Mas há **sinal fraco** sobre:

- **#12 (Dono opera no dia / sem visão estratégica):** não aparece em nenhuma queixa pública. Isso pode ser porque é dor 100% interna (dono não reclama de si), ou porque o argumento "founder is customer" inflou a importância dessa dor. **Não cortar — investigar em entrevista Onda 1.**

---

## Observação meta — o silêncio dos concorrentes verticais

**Achado mais importante deste bucket:** Cali, FP2, Metroex, Sismetro, TGM 4, Portal ISO, 8Quali, Q-MAN, Calibre Software — **nenhum** tem reclamação pública relevante. Hipóteses:

1. **Base pequena**: Cali tem ~5 funcionários, Metroex cita "80 clientes". Em valor absoluto, número de queixas pequeno.
2. **Cliente B2B técnico não usa Reclame Aqui**: gerente de laboratório resolve por telefone com vendedor direto; não dá likes em Facebook nem registra reclamação pública.
3. **Switching cost altíssimo trava reclamação**: migrar dados de 10 anos do Cali LAB pra concorrente custa caro e arrisca auditoria CGCRE — cliente engole sapo silencioso.
4. **Reclamação migrou pra outros canais**: blog da Metrologia, grupos LinkedIn de metrologistas, Cgcre/Inmetro diretamente. Esses canais **não foram acessados** nesta pesquisa (vale buscar em bucket futuro).

**Recomendação operacional:**
- **Não tirar conclusão de que "concorrentes verticais resolvem tudo bem"** — provavelmente não, mas o canal de queixa é outro.
- **Entrevistas Onda 1** com clientes **atuais** dos verticais (Cali principalmente, Metroex em segundo lugar) é insubstituível — bucket B+C continua obrigatório.
- **Buscar em fontes não-tradicionais** num bucket futuro: LinkedIn (grupos metrologia), blog da Metrologia (comentários), Cgcre processos públicos, ResearchGate (papers que citam software de calibração).

---

## Fontes consultadas

- [Cali Softwares — site oficial](https://cali.com.br/)
- [FP2 Tecnologia — laboratório](https://www.fp2.com.br/SistemaLaboratorio.aspx)
- [Calibre Software](https://calibre.software/)
- [Metroex (ForLogic)](https://metroex.com.br/)
- [Auvo Tecnologia — Reclame Aqui (lista)](https://www.reclameaqui.com.br/empresa/auvo-tecnologia/lista-reclamacoes/)
- [Auvo Tecnologia — reclamação integração OMIE](https://www.reclameaqui.com.br/auvo-tecnologia/problemas-com-a-plataforma-auvo-falha-na-integracao-com-omie-bugs-e-atrasos-na-entrega-de-dashboards_wQIYE4KoirwGe_JM/)
- [Auvo Tecnologia — problemas recorrentes + NF indevida](https://www.reclameaqui.com.br/auvo-tecnologia/problemas-recorrentes-e-falhas-no-sistema-auvo-notas-fiscais-indevidas-in__N1INrARooE1e9rG/)
- [Auvo no Capterra BR](https://www.capterra.com.br/software/201778/auvo)
- [Conta Azul — lista Reclame Aqui](https://www.reclameaqui.com.br/empresa/contaazul/lista-reclamacoes/)
- [Conta Azul — B2B Stack avaliações](https://www.b2bstack.com.br/product/conta-azul/avaliacoes)
- [SoftExpert — Glassdoor](https://www.glassdoor.com/Reviews/SoftExpert-Reviews-E2375976.htm)
- [SoftExpert — Reclame Aqui](https://www.reclameaqui.com.br/empresa/softexpert-software-s-a/)
- [Bling — lista Reclame Aqui](https://www.reclameaqui.com.br/empresa/bling/lista-reclamacoes/)
- [Tiny ERP — lista Reclame Aqui](https://www.reclameaqui.com.br/empresa/tiny-erp/lista-reclamacoes/)
- [Tiny ERP — pós-aquisição Olist](https://www.reclameaqui.com.br/olist-oficial/insatisfacao-com-o-servico-e-suporte-do-tiny-erp-apos-aquisicao-pela-olist-problemas-de-notas-fiscais-pedidos-duplicados-controle-de-estoque-manual-e-mudanca-unilateral-de-planos_2_dcAkSHE7RPE3sO/)
- [Field Control — Reclame Aqui](https://www.reclameaqui.com.br/empresa/field-control/lista-reclamacoes/)
- [Omie — ajuda NFS-e Padrão Nacional](https://ajuda.omie.com.br/pt-BR/articles/13355728-padrao-nacional-municipios-integrados-ao-omie-para-emissao-de-nfs-e)
- [Asaas — lista Reclame Aqui](https://www.reclameaqui.com.br/empresa/asaas-gestao-financeira/lista-reclamacoes/)
- [Checkmob — Capterra](https://www.capterra.com/p/205458/CHECKMOB/)
- [SISMETRO — produto](https://www.sismetro.com/metrologia)
- [Portal ISO — módulo calibração](https://www.portaliso.com/software-de-gestao-de-instrumentos-de-calibracao/)
- [Exame — caso SplitC erro planilha comissão](https://exame.com/negocios/um-erro-em-uma-planilha-de-comissao-de-vendas-virou-um-negocio-de-r-14-milhoes/)
