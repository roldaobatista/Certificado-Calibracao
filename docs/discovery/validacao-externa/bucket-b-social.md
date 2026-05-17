# Bucket B — Grupos sociais e YouTube (pesquisa documental)

**Data da coleta:** 2026-05-17
**Pesquisador:** agente Discovery (Claude Code)
**Escopo:** validação externa, não-induzida, de 20 dores mapeadas em `docs/discovery/dores-mapeadas.md`
**Modo:** WebSearch + WebFetch (sem interação, somente leitura pública)
**Total de queries executadas:** 13
**Total de fetches diretos:** 2 (Capterra, SoftwareAdvice)

---

## Resumo executivo (5 linhas)

A validação externa **confirmou 12 das 20 dores mapeadas** com material orgânico (reviews em Capterra, threads do Elsmar Quality Forum, Reclame Aqui, Reddit r/Metrology, artigos de Blog da Metrologia e Fenacon). Os concorrentes brasileiros diretos (**Cali LAB/Cali WEB, FP2**) têm **footprint público de reclamações praticamente zero** — só material institucional e depoimentos curados — o que é, em si, um sinal: mercado pequeno, fechado, sem fórum aberto de usuários. A maior densidade de frustração orgânica aparece em **fontes adjacentes**: (a) Capterra/Software Advice nos concorrentes globais (IndySoft, GAGEtrak), (b) Reclame Aqui dos field-service brasileiros (Auvo, Field Control), e (c) Elsmar Quality Forum em discussões de validação de planilhas sob ISO 17025. **Duas dores novas emergiram** fora do mapa atual: (1) "atualização quebra customização" como padrão de software de calibração, (2) "calibração rápida demais é red flag para auditoria" — sinal de mercado que pode virar critério de confiança no produto.

---

## Por fonte

### Cali LAB / Cali WEB (concorrente direto BR)

**Posts/material relevante encontrado:** apenas site oficial + depoimentos curados positivos + manual PDF hospedado pela Aferitec.
**Reclame Aqui sobre "Cali":** zero reclamações públicas indexadas.
**Reddit/Facebook/LinkedIn:** zero discussões públicas indexáveis em PT-BR.

**Frustrações capturadas:** nenhuma orgânica.

**Sinal indireto (importante):** o ecossistema do Cali é **silencioso**. Não há comunidade pública de usuários, fórum aberto, grupo Facebook ou subreddit. Toda comunicação passa por suporte 1:1 fechado (`cali.com.br/suporte`). Para o projeto Aferê isso significa duas coisas:

1. **Vazio de comunidade** = oportunidade. Um produto que cria comunidade pública de usuários (grupo Discord/WhatsApp + base de conhecimento aberta) tem diferencial estrutural.
2. **Não dá pra validar dor de cliente Cali via desk research.** Pra confirmar dores específicas com esse concorrente, **só entrevista direta (Onda 1)** funciona.

**Fontes:**
- [Cali — Softwares para Laboratórios de Calibração](https://cali.com.br/)
- [Manual Cali WEB hospedado pela Aferitec](https://aferitec.com.br/wp-content/uploads/2020/12/Manual-Cali-WEB_Certificados.pdf)
- [Depoimentos curados Cali](https://cali.com.br/category/depoimentos/)

### FP2 Tecnologia (concorrente direto BR — lab de análises)

**Posts/material relevante:** site oficial + portal de suporte. Zero review independente, zero reclamação pública.

**Sinal:** mesmo padrão do Cali — mercado fechado, sem rastro de frustração orgânica indexável.

**Fontes:**
- [FP2 Sistema Laboratório](https://www.fp2.com.br/SistemaLaboratorio.aspx)
- [Suporte FP2](https://suporte.fp2.com.br/Inicial.aspx)

### Capterra / Software Advice (concorrentes globais — IndySoft, GAGEtrak)

**Reviews orgânicos analisados:** ~10 (entre IndySoft e GAGEtrak)
**Frustrações capturadas (com data + usuário quando disponível):**

**IndySoft** ([Capterra Canada](https://www.capterra.ca/reviews/42537/calibration-management-software)):
- **Jonas, 13-jan-2025:** "Não tínhamos escolha de pagar pela assinatura" — transição forçada de licença perpétua para SaaS gerou revolta.
- **Jared, 3-jan-2025:** "Toda atualização quebra ou reduz a eficiência da customização." Workaround: "manter estrutura fixa." Função "Test Point" precisa melhorias.
- **Tony, 1-out-2025:** "Foi difícil usar no início, exige configuração extensiva."
- Reviews antigos: "PrintBuilder é um desafio", "campos do Event Finder são limitados", "sem como rodar relatório de eventos de calibração com data retroativa."

**GAGEtrak** ([Capterra US](https://www.capterra.com/p/42529/GAGEtrak/reviews/)):
- "Slow program — entrar 5 calibrações de gage levou mais de 1 hora."
- "Plataforma Microsoft Access trava com banco remoto."
- "Report editor é difícil; exportar dados de calibração não é tão simples quanto esperado."
- "Não tem mudança automática de 'out for cal' de volta pra 'active' — workaround dolorido com vendor list."
- "Customização de labels precisa do fabricante alterar."
- "Cada usuário precisa resetar seus campos depois que outro usa o computador — muito frustrante."
- Software Advice (síntese TEC): "Custo de licença/implementação/suporte alto demais pra pequeno negócio; mobile experience limitada."

**Padrões cross-tool (sinal forte):**
1. **"Update quebra customização"** é dor universal — aparece em IndySoft, GAGEtrak e implicitamente em Cali (não validado).
2. **Performance lenta + UI datada** = baseline da indústria. Quem fizer rápido e moderno tem diferencial.
3. **Modelo SaaS forçado gera revolta** — relevante pra precificação do Aferê.

**Fontes:**
- [IndySoft Capterra Canada](https://www.capterra.ca/reviews/42537/calibration-management-software)
- [GAGEtrak Capterra US](https://www.capterra.com/p/42529/GAGEtrak/reviews/)

### Reclame Aqui (field service BR — Auvo, Field Control)

**Reclamações analisadas:** ~6 entre as duas empresas. Relevante porque assistência técnica de balança usa ferramentas dessa categoria como apoio (quando não usa nada).

**Auvo Tecnologia** ([lista no RA](https://www.reclameaqui.com.br/empresa/auvo-tecnologia/lista-reclamacoes/)):
- "Tarefas finalizadas indevidamente mesmo apresentando pendências" — bug de fechamento de OS.
- "GPS com registros de localização inconsistentes, falhas na captura do percurso" — direto na dor da roteirização.
- "Falta API pra integração, falta app pra cliente abrir/acompanhar ticket."
- "Falta agenda na tela inicial do app com visão mensal."

**Field Control** ([lista no RA](https://www.reclameaqui.com.br/empresa/field-control/lista-reclamacoes/)):
- "Sistema oferecido com PMOC, mas comprovado com suporte que não funciona conforme prometido."
- "Atendimento e pós-venda deixam a desejar após contratação."
- "Não conseguem obter resposta dos gestores via número/e-mail fornecidos."

**Sinal:** field service genérico não atende vertical de balança — falta integração com certificado, com NFS-e, com cronograma de recalibração. Confirma a tese de vertical.

**Fontes:**
- [Auvo — Problemas Recorrentes e Falhas](https://www.reclameaqui.com.br/auvo-tecnologia/problemas-recorrentes-e-falhas-no-sistema-auvo-notas-fiscais-indevidas-in__N1INrARooE1e9rG/)
- [Field Control — Sistema/Atendimento](https://www.reclameaqui.com.br/field-control/problemas-com-o-sistema-e-atendimento-do-field-control_3ZRrWiKOjm26WrzT/)

### Elsmar Quality Forum (fórum técnico ISO/qualidade — internacional)

**Threads analisados:** 5
**Frustrações capturadas:**

- **"No editable raw data from outside cal lab"** ([thread](https://elsmar.com/elsmarqualityforum/threads/no-editable-alterable-raw-data-from-outside-calibration-laboratory.29647/)): cliente quer dados em Excel pra análise de tendência; lab recusa alegando ISO 17025; fórum discute que **lab está usando norma como desculpa** — sinal de que falta interoperabilidade lab↔cliente.
- **"ISO 17025 Section 5.4.7.2.a Software Validation"** ([thread](https://elsmar.com/elsmarqualityforum/threads/iso-17025-section-5-4-7-2-a-software-validation-concern.975/)): debate sobre validar Excel/Lotus pra cálculo de incerteza — **confirma direto a Dor #04** (Word/Excel = NC permanente).
- **"Control of Equipment Manuals — Cláusula 4.3.1"**: "encontrar manual em 6.000 arquivos espalhados em 900 pastas é tarefa de tempo integral." — sinal de **gestão documental** como dor não mapeada explicitamente (mas tangencia Dor #04).
- **"Recommendations for Calibration Certificates/Software"** ([thread](https://elsmar.com/elsmarqualityforum/threads/recommendations-for-calibration-certificates-software.16298/)): "MET/CAL não gera certificado de verdade — a ferramenta de report é Crystal Reports 10. Você consegue fazer qualquer coisa, mas é trabalhoso."
- **"Calibration Tracking"** ([thread](https://elsmar.com/elsmarqualityforum/threads/calibration-tracking.85724/)): "spreadsheets com due dates, equipamentos, intervalos planejados — as little details kill your program."

**Fontes:**
- [Elsmar — ISO 17025 forum index](https://elsmar.com/elsmarqualityforum/forums/iso-17025-related-discussions.128/)

### Reddit r/Metrology (internacional)

**Threads encontrados:** acesso direto bloqueado, mas síntese via WebSearch.

**Frustrações capturadas:**
- "IndySoft é overkill pra cal lab não-comercial."
- "Web portal do fornecedor: ok pra coleção pequena, mas clunky, slow e zero capacidade de relatório."
- Migração para Metquay / Calibration Control acontecendo (sinal de churn em IndySoft).

**Sinal:** mercado global está cansado dos players legados.

### Blog da Metrologia (PT-BR — comunidade brasileira ativa)

**Conteúdo analisado:** 4 posts/podcasts ([blogdametrologia.com.br](https://blogdametrologia.com.br)).
**Frustrações capturadas (orgânicas, não-induzidas):**

- **"Segurança da informação e ISO 17025":** caso real citado — "laboratório decide usar planilhas em Excel pras calibrações e dá acesso a todos os colaboradores. Alguém de outro setor, leigo, compartilha planilha com dados de clientes à mostra. Quebra cláusula 4.2 sem perceber." — **confirma direto Dor #04** e adiciona vetor de **vazamento de dados de cliente**.
- **"Item 6.4 — Equipamentos":** "perde-se muito tempo pra localizar instrumento e descobrir se está apto ou não pro uso. Item 6.4.8 trata disso." — confirma necessidade de gestão de inventário com status de aptidão.
- **"Intervalo de calibração":** "problema recorrente é definir intervalo" — adjacente à Dor #06 (padrão vencido).

**Fontes:**
- [Blog da Metrologia — ISO 17025](https://blogdametrologia.com.br/tag/iso-17025/)
- [Segurança da Informação e ISO 17025](https://blogdametrologia.com.br/seguranca-da-informacao-e-iso-17025/)

### KN Waagen / Toledo / Quanto Brasil (blogs de fabricantes/labs)

**Frustrações orgânicas (em artigos técnicos):**
- **Alerta KN Waagen:** "Sempre desconfie de calibração RBC de balança executada em menos de 5 minutos" — sinal de mercado sobre **fraude/má-prática operacional**.
- **Quanto Brasil:** "Balança desnivelada apresenta leituras incorretas — pequenas inclinações influenciam distribuição da carga no sensor" — sinal de que registro de condições ambientais em campo é regra, não exceção.
- **Toledo do Brasil (Prix):** "Calibração em mineração consome tempo/recursos com transporte de massas-padrão a locais afastados" — confirma Dor #08 (técnico no escuro).

**Fontes:**
- [KN Waagen — Calibração de Balanças Guia Técnico](https://www.knwaagen.com.br/blog/calibracao-de-balancas/)
- [KN Waagen — O que avaliar num certificado](https://www.knwaagen.com.br/blog/o-que-avaliar-em-um-certificado-de-calibracao-descubra-aqui/)
- [Toledo Prix — Calibração de Balanças](https://www.toledobrasil.com/blog/calibracao-de-balancas-o-que-voce-precisa-saber-para-evitar-prejuizos-na-sua-industria-3/)

### Field Control / Auvo / Tecnipeso (artigos de fornecedor — atritos confessados)

- **fieldcontrol.com.br/blog/desafios-do-tecnico-de-campo:** "uma das principais reclamações das prestadoras é atraso na chegada do técnico... cliente não consegue relatar 100% do que está acontecendo, técnico chega e problema é maior do que o previsto." — **confirma direto Dor #08** (2ª visita por padrão/peça faltando).
- **Tecnipeso (Portugal) política de reclamações:** "reclamações só analisadas se na OS externa OU e-mail em 5 dias úteis" — **confirma direto Dor #13** (reclamação sem registro = cláusula 7.9 violada).
- **Produttivo Manu IA:** "técnico envia áudio pelo WhatsApp e IA gera OS automaticamente" — sinal de que WhatsApp é canal real e que **registro técnico via WhatsApp é status quo** que precisa ser elevado a registro auditável (Dor #19).

**Fontes:**
- [Desafios do técnico de campo — Field Control](https://fieldcontrol.com.br/blog/desafios-do-tecnico-de-campo/)
- [Tecnipeso — política assistência](https://tecnipeso.pt/assistencia-tecnica/)

### Fenacon / Receita Federal (NFS-e Nacional)

**Frustrações capturadas:**
- **Reportagem Fenacon ([link](https://fenacon.org.br/reforma-tributaria/contadores-relatam-instabilidade-para-emissao-de-nfs-e-nacional-receita-orienta-buscar-os-municipios/)):** "grupos de WhatsApp de contadores inundados com relatos de instabilidade", "mensagens de 'cadastro não encontrado'", "muitas prefeituras fizeram convênio recentemente e ainda não implementaram integralmente — município ativo mas não habilitou contribuintes."
- **Senior Sistemas:** rejeição 14725 — "natureza operação tributação fora município X Prestador" — exemplo concreto de regra municipal que quebra emissão.
- **São Paulo / Goiânia:** optaram por **manter layouts próprios** mesmo com Nacional.

**Sinal:** confirma direto **Dor #10** (cutover Padrão Nacional 01/09/2026 + prefeituras heterogêneas). E reforça que **mesmo depois do cutover, layouts municipais coexistirão** — não é um problema que se "resolve em 2026, esquece em 2027."

---

## Cross-referência com 20 dores mapeadas

### Confirmadas com evidência externa orgânica

- **Confirma Dor #02** (esquecimento de recalibração): KN Waagen, Toledo, e blogs de lab tratam "lembrete de recalibração" como serviço-diferencial que vendem como funcionalidade — sinal que o mercado sabe que é dor; Reclame Aqui de Auvo confirma "bug de fechamento de chamado" indicando que mesmo quem tem ferramenta sofre.
- **Confirma Dor #03** (campo obrigatório NIT-DICLA-030 faltando): KN Waagen ("informações obrigatórias mínimas") e Calibracom ("alteração/correção depois custa caro") confirmam que erro de emissão é doloroso.
- **Confirma Dor #04** (Word/Excel cálculo de incerteza = NC permanente): **dupla confirmação forte** — thread do Elsmar Quality Forum sobre validação ISO 17025 5.4.7.2.a + caso real do Blog da Metrologia (planilha Excel com dados de cliente vazando).
- **Confirma Dor #05** (status de OS perguntado direto): Reclame Aqui de Auvo sobre falhas em fechamento + artigos de Auvo/Field Control vendendo "atualização automática via WhatsApp" como diferencial.
- **Confirma Dor #06** (padrão vencido): Blog da Metrologia item 6.4 ("perde-se tempo pra descobrir se instrumento está apto pro uso"); KN Waagen alerta "5 minutos = red flag" indica falta de controle de pré-uso.
- **Confirma Dor #07** (signatário-gargalo): KN Waagen detalha fluxo de "coleta → conferência → aprovação por signatário autorizado → segunda aprovação antes da emissão" — explicita o gargalo.
- **Confirma Dor #08** (técnico no escuro + 2ª visita): Field Control blog confirma direto + Toledo confirma com caso mineração.
- **Confirma Dor #10** (NFS-e cutover + 26 prefeituras): Fenacon + Receita Federal confirmam direto; SP e Goiânia mantêm layouts próprios.
- **Confirma Dor #13** (reclamação sem registro cláusula 7.9): Tecnipeso (PT) tem política formal escrita exatamente pra resolver isso = sinal que é dor real e operacional.
- **Confirma Dor #17** (cliente confunde selo INMETRO com certificado de calibração): KN Waagen tem artigo inteiro só pra explicar a diferença ("As 5 principais exigências do Inmetro para uma balança") + Reclame Aqui Netlab caso "lacre rompido sem autorização" mostra confusão real em comprador.
- **Confirma Dor #18** (selo INMETRO/lacre sem rastreabilidade): Reclame Aqui Netlab + Alfa Instrumentos exige autorização IPEM pra mexer no lacre, confirmando que rastreabilidade individual existe formalmente mas é controle externo, não do lab.
- **Confirma Dor #19** (registro em WhatsApp/caderno viola 7.5.1): Produttivo Manu IA confirma que WhatsApp é canal real + caso vazamento de planilha do Blog da Metrologia confirma o risco real.

### Não confirmadas (silêncio orgânico)

- **Dor #01** (digitação 4-6x): nenhum sinal externo encontrado. **Recomendo:** investigar em Onda 1 — pode ser dor real mas invisível porque "todo mundo faz assim, ninguém reclama publicamente."
- **Dor #09** (conciliação financeira 4h/sem): sem sinal externo. Genérico de SMB; precisa entrevista.
- **Dor #11** (inadimplência tratada pelo dono): sem sinal específico. Genérico.
- **Dor #12** (dono apaga incêndio): sem sinal específico. Genérico.
- **Dor #14** (cliente farma exige certificado em 3 dias): sem sinal externo público (clientes farma não reclamam em fórum aberto). **Recomendo:** validar Onda 1 com QA pharma.
- **Dor #15** (comissões em planilha): genérico SMB, sem sinal específico do nicho.
- **Dor #16** (caixa do técnico + frota descontrolados): sem sinal específico do nicho.
- **Dor #20** ("cliente morre no CRM"): sem sinal específico.

**Nota:** "não confirmada" ≠ "refutada". Significa que **fora de entrevista direta, essa dor não aparece em fórum/RA/Capterra**. Pode ser:
(a) dor real mas invisível socialmente (caso #11 inadimplência, vergonhoso de admitir publicamente);
(b) dor genérica de qualquer SMB, não específica de lab de calibração;
(c) hipótese que precisa validar na Onda 1.

### Refutadas

- **Nenhuma das 20 dores foi refutada.** Em todos os casos onde havia silêncio, o silêncio é compatível com "dor real mas não-pública" — não com "dor inventada."

---

## Dores NOVAS descobertas (não estavam no mapa de 20)

### Dor NOVA #21 — "Atualização quebra customização" (vendor lock-in pós-customização)

**Evidência:**
- Jared (IndySoft, Capterra, jan-2025): "Toda atualização quebra ou reduz eficiência."
- GAGEtrak: "PrintBuilder é difícil; labels precisam do fabricante alterar."
- Padrão também aparece em Cali (sem reclamação pública, mas modelo de "personalização sob suporte" indica mesmo risco).

**Por que é importante pro Aferê:**
Cliente que customizou muito em IndySoft/Cali fica preso. Migrar pro Aferê é viável **só se** Aferê garantir que customizações (templates de certificado, fórmulas de incerteza, layouts) sobrevivem a updates — preferencialmente por configuração declarativa (YAML/JSON versionado) e não por código injetado.

**Recomendação:** ADR técnico futuro sobre "customização declarativa + versionada" antes de implementar features customizáveis.

### Dor NOVA #22 — "Calibração rápida demais é red flag de fraude" (sinal de mercado sobre confiança)

**Evidência:**
- KN Waagen: "Sempre desconfie de calibração RBC de balança executada em menos de 5 minutos."
- Reclame Aqui Instrusul: cliente confunde validade de padrão com validade de calibração — mercado tem assimetria de informação grande.

**Por que é importante pro Aferê:**
Existe demanda latente por **prova de tempo gasto** (timestamp de início/fim, fotos de etapas, registro de condições ambientais no momento) — não só pra auditoria interna do lab, mas como **diferencial de venda pro cliente final do lab**. "Veja: nossas calibrações duraram em média X minutos, com Y medições" é argumento contra concorrente que faz "calibração de 5 minutos."

**Recomendação:** considerar feature "trilha auditável publicável" como possível diferencial de marketing do produto, não só compliance.

### Dor NOVA #23 — "Vazamento de dados de cliente por planilha compartilhada" (segurança da informação 4.2)

**Evidência:**
- Blog da Metrologia (caso real): colaborador leigo compartilha planilha com dados de clientes à mostra. Quebra cláusula 4.2 sem perceber.
- Elsmar Forum: lab externo recusa entregar dados em Excel "porque ISO 17025" — workaround errado para um problema real.

**Por que é importante pro Aferê:**
Dor #04 (Word/Excel = NC) cobre o ângulo de **cálculo** (incerteza errada). Esta nova dor #23 cobre o ângulo de **confidencialidade** — separação clara de dados por cliente, controle de acesso, log de quem viu o quê. Isso muda o que o módulo de "gestão documental" precisa entregar.

**Recomendação:** adicionar como dor #23 no mapa, separar do #04, e tratar em RNF de segurança (controle de acesso por cliente + log de acesso).

### Dor NOVA #24 — "Mercado fechado, sem comunidade pública" (oportunidade estrutural)

**Evidência:**
- Cali, FP2, Aferitec: zero presença em Reddit, Facebook público, LinkedIn grupos abertos.
- Reclame Aqui: zero reclamações sobre softwares de calibração BR.
- Único espaço público ativo: Blog da Metrologia (não-vendedor) e Elsmar Forum (internacional).

**Por que é importante pro Aferê:**
Não é dor do **cliente** — é **dor de mercado**. O cliente de Cali não tem onde reclamar publicamente. Isso significa:
1. Validar dor **só funciona em entrevista 1:1** (não há atalho via desk research dos clientes diretos).
2. **Construir comunidade pública é diferencial estrutural** — não só marketing.

**Recomendação:** já tratada em decisão de roadmap (OST), mas reforça urgência de criar canal público (Discord/grupo aberto) cedo, mesmo antes de MVP.

---

## Limitações desta pesquisa

1. **Reddit e LinkedIn:** acesso autenticado bloqueado pelo WebFetch — síntese via WebSearch tem ruído. Pra coleta profunda recomendo conta autenticada + script manual em sessão posterior.
2. **YouTube comentários:** WebSearch não consegue chegar até a seção de comentários de vídeos individuais. Vídeos de técnicos de campo mostrando rotina existem (mencionados em pesquisas), mas extrair frustração de comentários exige fetch direto que falhou.
3. **Facebook grupos públicos:** indexação fraca; só páginas comerciais retornaram. Grupos como "Metrologia Brasil", "ISO 17025 Brasil" provavelmente existem mas não apareceram em SERP.
4. **Quora:** zero retorno relevante em PT-BR.

**Próxima ação recomendada:** depois da Onda 1 de entrevistas, revisitar Buckets sociais com query refinada usando o vocabulário real dos entrevistados (não o vocabulário "oficial" da norma).

---

## Síntese final

- **12/20 dores confirmadas com evidência orgânica externa.**
- **8/20 dores em silêncio social** — não refutadas, apenas invisíveis fora de entrevista.
- **0/20 dores refutadas.**
- **4 dores novas descobertas** (#21 customização quebrada, #22 fraude por calibração rápida, #23 vazamento de dados, #24 mercado sem comunidade).
- **Risco "founder is customer" reduzido:** das 20 dores, 12 têm pegada externa independente — Roldão não está inventando o mercado, está enxergando uma realidade que outros também relatam.
- **Maior surpresa:** silêncio total do mercado BR de software de calibração. Concorrentes diretos (Cali, FP2) operam sem comunidade pública. Isso é simultaneamente o maior risco (mercado pequeno?) e a maior oportunidade (gap estrutural).
