# Discovery — Jobs To Be Done (JTBD)

> **Artefato Rodada 0 — Batch 2** (agente faz sozinho; Roldão valida em entrevistas Onda 1+2).
> **Atualizado:** 2026-05-17 — primeira passagem do agente após `dominio-de-negocio.md`, `concorrentes.md`, `riscos.md` e `normas-e-regulacao.md`.
> **Status:** scaffolding **preenchido** com inferências do agente; toda linha marcada `[a confirmar via entrevista]` precisa virar evidência antes de virar requisito.
> **Saída desse doc alimenta:** `dores-mapeadas.md`, `personas-detalhadas.md`, `sintese-final.md`, `validacao-ativa.md` (perguntas das entrevistas).

---

## 1. Princípios do framework JTBD (Christensen + Ulwick)

> Resumo curto pro próprio agente lembrar enquanto preenche — e pro Roldão entender o que está vendo.

1. **Job ≠ feature.** Job é o "trabalho" que a pessoa contrata um produto pra fazer. Feature é como o produto faz. "Quero emitir certificado de calibração" é feature; **"Quero entregar o certificado pro meu cliente sem ele me cobrar 3 vezes pelo telefone"** é job.
2. **Forma Christensen:** "Quando eu **[situação trigger]**, eu quero **[motivação]**, pra que eu possa **[resultado esperado]**." Toda linha-de-job tem que caber nesse molde — se não cabe, é feature disfarçada.
3. **3 categorias (Ulwick):**
   - **Funcional** — trabalho concreto/operacional (emitir nota, calcular incerteza, agendar técnico).
   - **Emocional** — como a pessoa quer **se sentir** (segura, no controle, não-burra, não-culpada).
   - **Social** — como quer ser **vista pelos outros** (profissional pelo cliente, competente pelo chefe, "tô junto" pelo regulador).
4. **Métrica de sucesso (Outcome — Ulwick):** todo job tem que ter "como eu mediria se foi bem feito" — geralmente em forma de velocidade (mais rápido), confiabilidade (menos erro), custo (menos R$/hora), ou ansiedade (menos retrabalho mental).
5. **Concorrente do job ≠ concorrente do produto.** Concorrente do job é **o que a pessoa usa HOJE pra fazer esse trabalho** — pode ser planilha, WhatsApp, gritar com o colega, pasta de e-mail. Esse é o **status quo a derrotar**, não o software A ou B do mercado.
6. **Anti-job tem o mesmo peso de job.** Decidir explicitamente **o que NÃO resolvemos** é o que mantém o produto enxuto e impede scope creep.

---

## 2. Como ler cada job

Cada job tem 10 campos. Modelo:

```
JTBD-NNN | <título curto>
- Quem: <papel humano>
- Quando: <situação trigger>
- Quero: <motivação>
- Pra que possa: <resultado esperado>
- Categoria: funcional / emocional / social
- Métrica de sucesso: <como medir se foi bem feito>
- Solução hoje (status quo): <workaround atual: WhatsApp, planilha, Word, e-mail, copia-cola>
- Concorrente que mais resolve hoje: <produto/ferramenta — pode ser "nenhum">
- Prioridade MVP-1: alta / média / baixa
- Marcação: [a confirmar via entrevista] quando for inferência
```

---

## 3. Jobs por papel humano

> 7 papéis identificados em `dominio-de-negocio.md` §Papéis. Mínimo 5 jobs por papel.

### 3.1 Dono / sócio (Roldão é exemplo desse papel)

**Perfil:** decide estratégia, paga a folha, vive ansiedade de "o sistema vai cair no meio da auditoria?" e "vou ganhar dinheiro esse mês?".

```
JTBD-001 | Saber se o mês vai fechar no azul antes do mês fechar
- Quem: dono
- Quando: terça de manhã, tomando café antes de abrir a empresa
- Quero: olhar UM número que me diz como está o mês
- Pra que possa: decidir hoje se aperto cobrança ou se posso autorizar a compra do padrão novo
- Categoria: funcional + emocional (paz mental)
- Métrica de sucesso: tempo pra ter o número < 30s; número confiável (não preciso ligar pro contador pra confirmar)
- Solução hoje: liga pro financeiro, pede pra abrir planilha de "fluxo"; ou ele mesmo abre Conta Azul/Bling
- Concorrente que mais resolve hoje: Conta Azul, Omie (parcial — não casa com OS de calibração)
- Prioridade MVP-1: alta
- [a confirmar via entrevista] qual é o "1 número" que cada dono olha
```

```
JTBD-002 | Não tomar multa nem perder acreditação RBC por bobagem operacional
- Quem: dono (perfis A, B, C)
- Quando: chegando carta do INMETRO ou e-mail do cliente farma cobrando documentação
- Quero: ter certeza que o sistema BLOQUEIA o erro antes do erro virar NC
- Pra que possa: não acordar 3h da manhã pensando "será que emiti certificado com padrão vencido?"
- Categoria: emocional (segurança) + funcional (compliance automático)
- Métrica de sucesso: zero NC originada de erro que software poderia ter pegado
- Solução hoje: confia na cabeça do metrologista; planilha de validade de padrão revisada "quando lembra"
- Concorrente que mais resolve hoje: Cali, Metroex (parcial — alertam mas não bloqueiam emissão automaticamente)
- Prioridade MVP-1: alta
```

```
JTBD-003 | Provar pro cliente novo que minha empresa é séria mesmo sendo pequena
- Quem: dono (todos perfis, especialmente B/C/D)
- Quando: visita comercial em cliente grande (farma, automotivo)
- Quero: mostrar painel/portal com histórico de OS, certificados arquivados, indicadores de prazo
- Pra que possa: fechar contrato sem precisar levar pasta-de-papel ou imprimir Word
- Categoria: social (parecer profissional) + funcional (gerar credibilidade)
- Métrica de sucesso: tempo do "primeiro contato" até "contrato assinado" cai; cliente novo aceita perfil B/C como aceitaria A
- Solução hoje: PowerPoint feito à mão; site institucional desatualizado; mostra certificado de UM cliente como amostra
- Concorrente que mais resolve hoje: nenhum no perfil B/C/D; SaaS internacional (Qualer) faz pro perfil A grande
- Prioridade MVP-1: média
```

```
JTBD-004 | Não depender de UMA pessoa (signatário, gerente, técnico) pra empresa funcionar
- Quem: dono
- Quando: signatário tira férias, técnico pede demissão, gerente fica doente
- Quero: que o sistema saiba quem pode substituir quem e mostre quem está disponível hoje
- Pra que possa: dormir tranquilo nas férias do RT
- Categoria: emocional (continuidade) + funcional (matriz de competência)
- Métrica de sucesso: nenhum certificado/OS fica preso porque "fulano é o único que sabe"
- Solução hoje: cabeça do dono + WhatsApp; nas empresas maiores, planilha de férias
- Concorrente que mais resolve hoje: Metroex (parcial — gestão de pessoal); módulo Gestão de Competências do produto vai cobrir
- Prioridade MVP-1: alta (INV-003 depende disso)
```

```
JTBD-005 | Saber se vale a pena entrar no processo de acreditação RBC
- Quem: dono (perfil B/C)
- Quando: cliente novo pede "selo RBC" pra fechar contrato
- Quero: ver simulação de custo, tempo e gap entre minha empresa hoje e os requisitos Cgcre
- Pra que possa: tomar decisão informada de virar perfil A
- Categoria: funcional (gap analysis) + emocional (clareza pra decidir)
- Métrica de sucesso: dono toma decisão de "vou/não vou acreditar" em < 1 semana, com base em dados do próprio sistema
- Solução hoje: contrata consultor de qualidade (R$ 30-80k pelo diagnóstico)
- Concorrente que mais resolve hoje: nenhum (consultoria humana)
- Prioridade MVP-1: baixa (diferencial perfil C ⭐, mas pode entrar em MVP-2)
```

```
JTBD-006 | Ter histórico do negócio na minha mão se eu precisar vender a empresa, processar alguém ou me defender
- Quem: dono
- Quando: due diligence de venda, processo trabalhista, auditoria fiscal, briga com cliente
- Quero: extrair todo o histórico (OS, certificado, NF-e, e-mail, log) por cliente/período em formato auditável
- Pra que possa: provar minha versão dos fatos com dado, não com "eu lembro que..."
- Categoria: funcional + emocional (proteção)
- Métrica de sucesso: extração completa de qualquer cliente em < 1h, com hash de integridade
- Solução hoje: vasculha e-mail + pasta de rede + planilha; alguns dados perdidos
- Concorrente que mais resolve hoje: ERP fiscal tradicional (Omie, Bling) — parcial, só lado fiscal
- Prioridade MVP-1: média (a auditoria imutável INV-001 já entrega base; UI de extração pode ficar pra MVP-2)
```

```
JTBD-007 | Mudar perfil da empresa (D→C→B→A) sem ter que trocar de sistema
- Quem: dono (perfil C/D em crescimento)
- Quando: empresa amadurece e quer profissionalizar
- Quero: ligar/desligar regras 17025 conforme evoluo, sem migração de dados
- Pra que possa: usar o software como "trilha de evolução" e não como "decisão pra vida toda"
- Categoria: funcional (configurabilidade) + emocional (não-aprisionado)
- Métrica de sucesso: upgrade D→C→B em < 1 dia útil; A exige prova documental (INV-015) mas sem perda de histórico
- Solução hoje: troca de software com migração manual de dados (custo proibitivo)
- Concorrente que mais resolve hoje: nenhum — esse é o diferencial central do produto Aferê (ver `dominio-de-negocio.md` §Perfis)
- Prioridade MVP-1: alta (diferencial defensável)
```

---

### 3.2 Gerente operacional

**Perfil:** triagem de chamado, agenda do técnico, "bombeiro" do dia-a-dia, primeiro a saber quando dá problema.

```
JTBD-008 | Decidir em 30 segundos se chamado novo é manutenção ou calibração
- Quem: gerente
- Quando: chamado entra (WhatsApp, e-mail, telefone) e a fila tá cheia
- Quero: triagem com 3-5 perguntas + sugestão automática (com base no histórico do cliente e do instrumento)
- Pra que possa: passar pra técnico OU pra metrologista sem reabrir conversa com cliente
- Categoria: funcional + emocional (não-sobrecarregado)
- Métrica de sucesso: < 2 min do "chamado entra" até "atribuído"; < 5% de re-triagem (passei pro errado e voltou)
- Solução hoje: cabeça do gerente; WhatsApp do dono ("o que faço com esse aqui?")
- Concorrente que mais resolve hoje: nenhum dedicado; Pipedrive/Bitrix tentam mas sem semântica do setor
- Prioridade MVP-1: alta
```

```
JTBD-009 | Saber onde cada técnico está hoje e amanhã, sem ter que ligar
- Quem: gerente
- Quando: cliente liga querendo emergência pra hoje
- Quero: mapa/lista da agenda dos técnicos com folga visível e localização aproximada
- Pra que possa: dizer "tenho técnico aí 14h" sem mentir nem prometer impossível
- Categoria: funcional
- Métrica de sucesso: resposta ao cliente em < 1 min sem precisar ligar pra técnico
- Solução hoje: grupo de WhatsApp "campo"; planilha do Google Sheets compartilhada (desatualizada)
- Concorrente que mais resolve hoje: Bom Controle, ServiceDesk Plus (genéricos, sem cara de calibração)
- Prioridade MVP-1: alta
```

```
JTBD-010 | Reagendar OS sem virar bagunça quando técnico falta
- Quem: gerente
- Quando: técnico avisa que ficou doente, carro quebrou, atrasou
- Quero: arrastar a OS pra outro técnico ou outro dia e o sistema notificar o cliente automaticamente
- Pra que possa: não ter que escrever 5 mensagens iguais no WhatsApp
- Categoria: funcional + emocional (evitar conflito com cliente)
- Métrica de sucesso: reagendamento em < 2 min com notificação ao cliente automática
- Solução hoje: WhatsApp manual cliente a cliente
- Concorrente que mais resolve hoje: ServiceMax, Bom Controle (sem semântica de calibração)
- Prioridade MVP-1: alta
```

```
JTBD-011 | Não deixar OS "abandonada" no meio do fluxo
- Quem: gerente
- Quando: revisão semanal do trabalho em andamento
- Quero: ver lista de OS paradas há mais de N dias por estágio (orçamento aprovado mas não executou, executou mas não emitiu certificado, certificado emitido mas não faturou)
- Pra que possa: cobrar quem está segurando o trabalho
- Categoria: funcional + social (evita cliente reclamar primeiro)
- Métrica de sucesso: zero OS abandonada > 30 dias sem motivo registrado
- Solução hoje: planilha "controle geral" preenchida no fim do dia (quando dá tempo)
- Concorrente que mais resolve hoje: Trello, Asana (sem semântica do setor); Metroex parcial
- Prioridade MVP-1: alta
```

```
JTBD-012 | Saber a hora certa de cobrar verificação periódica INMETRO do cliente
- Quem: gerente
- Quando: cliente tem balança comercial cuja verificação anual IPEM está se aproximando
- Quero: alerta 90/60/30 dias antes + sugestão de cobrança automática
- Pra que possa: faturar a verificação SEM o cliente tomar multa do IPEM e me culpar
- Categoria: funcional + social (cliente fica grato)
- Métrica de sucesso: > 80% das verificações periódicas dos clientes são feitas no prazo; zero cliente multado por esquecimento
- Solução hoje: planilha de "controle de validade" que ninguém atualiza
- Concorrente que mais resolve hoje: nenhum nacional — R-040 confirma o gap
- Prioridade MVP-1: alta (Metrologia Legal MVP-1 obrigatório)
```

```
JTBD-013 | Ter visão consolidada da operação sem precisar abrir 5 telas
- Quem: gerente
- Quando: começo do dia
- Quero: dashboard único com: OS em aberto, certificados pra emitir hoje, padrões vencendo, financeiro do dia, NC abertas
- Pra que possa: priorizar o dia em 2 minutos
- Categoria: funcional + emocional (sensação de controle)
- Métrica de sucesso: < 2 min do "abrir o sistema" até "saber o que fazer hoje"
- Solução hoje: 4 abas no navegador + cabeça
- Concorrente que mais resolve hoje: Metroex, Calibre (parcial)
- Prioridade MVP-1: média (MVP pode entregar versão simples; refinar em MVP-2)
```

```
JTBD-014 | Provar pro dono que a equipe trabalhou (sem precisar provar de hora em hora)
- Quem: gerente
- Quando: reunião semanal com dono
- Quero: relatório automático "produtividade da semana" (OS fechadas, certificados emitidos, ticket médio, atrasos)
- Pra que possa: defender a equipe quando dono questionar custo de folha
- Categoria: social (proteger a equipe + a si mesmo) + funcional
- Métrica de sucesso: relatório sai sozinho toda 2ª de manhã; dono lê em < 5 min
- Solução hoje: gerente passa noite de domingo montando planilha
- Concorrente que mais resolve hoje: Metroex (relatórios)
- Prioridade MVP-1: média
```

---

### 3.3 Atendente / SAC

**Perfil:** primeira voz que o cliente ouve, vive sob pressão de tempo, precisa de informação ON-THE-FLY.

```
JTBD-015 | Identificar o cliente em 5 segundos quando ele liga
- Quem: atendente
- Quando: telefone toca / WhatsApp chega
- Quero: tela única com histórico de OS, certificados, pendências financeiras, último contato
- Pra que possa: cumprimentar pelo nome e dizer "vi que sua OS XPTO está com a Maria"
- Categoria: funcional + social (parecer organizado pro cliente)
- Métrica de sucesso: > 90% dos atendimentos identificam cliente sem ele precisar repetir CNPJ
- Solução hoje: planilha de contatos + busca no e-mail + chuta pelo telefone
- Concorrente que mais resolve hoje: CRM genérico (Pipedrive, HubSpot) — sem dado operacional
- Prioridade MVP-1: alta
```

```
JTBD-016 | Abrir chamado em 1 minuto sem perder informação importante
- Quem: atendente
- Quando: cliente está descrevendo problema no telefone
- Quero: formulário curto, com campos sugeridos por tipo de instrumento, foto/áudio anexável
- Pra que possa: registrar tudo sem pedir cliente pra repetir
- Categoria: funcional
- Métrica de sucesso: abertura de chamado em < 90s; > 80% das triagens posteriores não precisam re-perguntar
- Solução hoje: caderno + transcrever depois pra planilha (perde info)
- Concorrente que mais resolve hoje: Movidesk, Zendesk (sem semântica do setor)
- Prioridade MVP-1: alta
```

```
JTBD-017 | Responder "cadê meu certificado?" sem precisar levantar da cadeira
- Quem: atendente
- Quando: cliente liga querendo segunda via, status, ou cópia
- Quero: busca por cliente/instrumento/número e download imediato (com log)
- Pra que possa: resolver em 30s e não dizer "vou consultar e te retorno"
- Categoria: funcional + social
- Métrica de sucesso: 100% das solicitações de 2ª via resolvidas no mesmo telefonema
- Solução hoje: pede pro metrologista, que vai na pasta de rede achar PDF
- Concorrente que mais resolve hoje: Cali WEB (portal); Metroex
- Prioridade MVP-1: alta
```

```
JTBD-018 | Não cometer gafe de cobrar cliente que já pagou
- Quem: atendente
- Quando: cliente liga pra falar de OS, eu vejo financeiro junto
- Quero: status financeiro visível no mesmo card do cliente (sem precisar abrir financeiro)
- Pra que possa: não dizer "vc tá devendo" pra cliente em dia
- Categoria: social (evitar vexame) + funcional
- Métrica de sucesso: zero cobrança indevida feita por SAC
- Solução hoje: financeiro só abre no Bling/Omie; atendente "chuta"
- Concorrente que mais resolve hoje: nenhum integrado
- Prioridade MVP-1: alta
```

```
JTBD-019 | Enviar orçamento pro cliente no momento que ele pediu
- Quem: atendente / vendedor
- Quando: cliente fecha conversa dizendo "manda o orçamento por e-mail/WhatsApp"
- Quero: gerar orçamento (PDF + link) e enviar com 2 cliques
- Pra que possa: não perder o "momento quente" do cliente (lead esfria em horas)
- Categoria: funcional + emocional (não-perder-venda)
- Métrica de sucesso: 100% dos orçamentos saem no mesmo turno do pedido
- Solução hoje: planilha modelo do Word, salva manualmente, anexa em e-mail
- Concorrente que mais resolve hoje: Bling, ContaAzul (sem semântica calibração); Pipedrive (sem PDF padronizado)
- Prioridade MVP-1: alta
```

```
JTBD-020 | Não ter que copiar a mesma info 3 vezes (chamado → orçamento → OS)
- Quem: atendente
- Quando: chamado vira orçamento, orçamento vira OS
- Quero: continuidade — info do chamado já preenche orçamento; orçamento aprovado vira OS sem retrabalho
- Pra que possa: parar de ser "digitador" e voltar a atender cliente
- Categoria: funcional + emocional (desumanização)
- Métrica de sucesso: tempo de geração de orçamento a partir de chamado < 1 min
- Solução hoje: copy-paste entre planilha do chamado, Word do orçamento, sistema de OS
- Concorrente que mais resolve hoje: ERP integrado (Bling) mas sem semântica calibração
- Prioridade MVP-1: alta
```

---

### 3.4 Técnico de campo

**Perfil:** vive no carro, no laboratório do cliente, em chão de fábrica. Conexão de internet ruim. Mãos sujas. Pressão de tempo.

```
JTBD-021 | Saber TUDO da próxima OS antes de chegar no cliente
- Quem: técnico de campo
- Quando: saindo de casa de manhã / saindo de um cliente pro próximo
- Quero: tela única com endereço, contato, histórico, instrumento, peças sugeridas, certificado anterior
- Pra que possa: chegar preparado e não voltar pra empresa por causa de peça faltando
- Categoria: funcional + emocional (não-burra)
- Métrica de sucesso: < 5% de retornos por falta de informação/peça
- Solução hoje: papel impresso na noite anterior + WhatsApp pra perguntar
- Concorrente que mais resolve hoje: Beamex bMobile, Metroex Coletor (parcial)
- Prioridade MVP-1: alta (ADR-0003 mobile obrigatório)
```

```
JTBD-022 | Executar a calibração sem internet quando o cliente é fora de cobertura
- Quem: técnico de campo
- Quando: cliente em zona rural, indústria pesada com sinal ruim, subsolo
- Quero: app offline com sincronização automática ao voltar pra área com sinal
- Pra que possa: não perder dado nem horário porque "caiu o sinal"
- Categoria: funcional
- Métrica de sucesso: 100% das OS executadas offline são sincronizadas sem perda de dado
- Solução hoje: anota em papel, transcreve depois
- Concorrente que mais resolve hoje: Beamex bMobile, Metroex Coletor — referências internacionais
- Prioridade MVP-1: alta
```

```
JTBD-023 | Coletar leitura do instrumento direto pelo telefone (foto, OCR, conexão)
- Quem: técnico de campo
- Quando: medição precisa ser transcrita
- Quero: tirar foto do display ou conectar com calibrador documentador (Bluetooth/USB)
- Pra que possa: não digitar errado e não perder tempo
- Categoria: funcional
- Métrica de sucesso: < 0,1% de erro de transcrição
- Solução hoje: digita à mão (e erra)
- Concorrente que mais resolve hoje: Beamex/Fluke/Presys (com hardware proprietário)
- Prioridade MVP-1: média (MVP pode aceitar foto; OCR/integração hardware pode esperar MVP-2)
```

```
JTBD-024 | Pegar assinatura do cliente direto no celular
- Quem: técnico de campo
- Quando: terminou execução da OS
- Quero: cliente assina na tela do celular + recebe via WhatsApp/e-mail automaticamente
- Pra que possa: fechar a OS sem voltar à empresa pra "registrar"
- Categoria: funcional + emocional (fim de dia mais cedo)
- Métrica de sucesso: 100% das OS fechadas no campo são concluídas no mesmo dia
- Solução hoje: papel assinado, levado pra empresa, scaneado depois
- Concorrente que mais resolve hoje: Bom Controle, Auvo
- Prioridade MVP-1: alta
```

```
JTBD-025 | Não ter que voltar pra empresa pra "encerrar" a OS
- Quem: técnico de campo
- Quando: última visita do dia
- Quero: tudo encerrado pelo celular, sem ir à sede
- Pra que possa: chegar em casa mais cedo (qualidade de vida)
- Categoria: emocional + funcional
- Métrica de sucesso: > 80% dos técnicos não voltam à sede em dias de campo
- Solução hoje: vai à sede entregar papel e bater ponto
- Concorrente que mais resolve hoje: Auvo, ServiceMax
- Prioridade MVP-1: alta
```

```
JTBD-026 | Reportar peça quebrada/faltando estoque no momento que percebo
- Quem: técnico de campo
- Quando: vai usar peça e percebe que acabou/quebrou
- Quero: registrar no app, gerar pedido automático pra compras, deixar OS suspensa com motivo
- Pra que possa: não esquecer e o problema voltar 3 dias depois
- Categoria: funcional + social (não-causador-de-problema-pros-colegas)
- Métrica de sucesso: < 24h entre detectar falta e gerar pedido de compra
- Solução hoje: anota em WhatsApp do grupo
- Concorrente que mais resolve hoje: nenhum integrado
- Prioridade MVP-1: média (depende do módulo Estoque entrar no MVP-1)
```

---

### 3.5 Metrologista / signatário técnico

**Perfil:** dono da responsabilidade legal/regulatória. Cabeça técnica. Vive entre planilha de cálculo de incerteza, certificado em Word, padrão guardado em armário. Maior risco da empresa porque ele assina.

```
JTBD-027 | Emitir certificado sem precisar montar cálculo de incerteza na mão a cada vez
- Quem: metrologista
- Quando: cada nova calibração
- Quero: rotina de cálculo pré-validada por grandeza/faixa, com fontes de incerteza configuradas
- Pra que possa: focar em interpretação, não em conta de calculadora
- Categoria: funcional + emocional (não-burra)
- Métrica de sucesso: tempo de emissão por certificado cai 60-80%; zero erro de fórmula
- Solução hoje: planilha Excel "do laboratório" copiada e adaptada caso a caso
- Concorrente que mais resolve hoje: Cali, Metroex, Beamex CMX, Fluke MET/CAL — todos resolvem para perfil A
- Prioridade MVP-1: alta (core do produto)
```

```
JTBD-028 | Garantir rastreabilidade completa SEM ter que abrir pasta-de-padrão atrás do certificado-pai
- Quem: metrologista
- Quando: emitindo certificado
- Quero: sistema puxar automaticamente certificado-pai do padrão usado, validade, incerteza, e bloquear se vencido
- Pra que possa: cumprir INV-002 sem esforço extra
- Categoria: funcional + emocional (não-pode-falhar)
- Métrica de sucesso: 100% dos certificados emitidos têm cadeia rastreada; zero rejeição em auditoria por falta de cadeia
- Solução hoje: pasta de rede com PDF dos certificados-pai; copy-paste manual
- Concorrente que mais resolve hoje: Cali (parcial), Metroex (parcial); MasterControl Asset Excellence (forte)
- Prioridade MVP-1: alta (R-018 score 25, INV-002)
```

```
JTBD-029 | Saber se há NÃO conformidade pendente que afete a emissão
- Quem: metrologista
- Quando: vai assinar certificado
- Quero: alerta se houver NC aberta naquele instrumento, padrão usado, ou método
- Pra que possa: não emitir certificado contaminado
- Categoria: funcional + emocional (não-quero-ser-pego)
- Métrica de sucesso: zero certificado emitido com NC pendente relacionada
- Solução hoje: cabeça do metrologista + reunião semanal de qualidade
- Concorrente que mais resolve hoje: Qualer/MasterControl (forte); Cali (parcial)
- Prioridade MVP-1: alta (INV-012)
```

```
JTBD-030 | Assinar certificado digitalmente sem ritual chato
- Quem: metrologista (signatário)
- Quando: lote de certificados pra assinar no fim do dia
- Quero: assinatura digital ICP-Brasil (e-CPF) integrada, com confirmação biométrica/MFA
- Pra que possa: assinar 20 certificados em 5 min, sem virar Word
- Categoria: funcional
- Métrica de sucesso: < 15s por assinatura; assinatura legalmente válida
- Solução hoje: imprime, assina à mão, escaneia (e gasta R$ 800 em toner/ano)
- Concorrente que mais resolve hoje: FP2 (declara ICP-Brasil); MasterControl
- Prioridade MVP-1: alta
```

```
JTBD-031 | Provar que software/cálculo está validado quando auditor pedir
- Quem: metrologista
- Quando: auditoria Cgcre / cliente farma audita / GMP/GAMP
- Quero: relatório de validação do software, change log, hash dos cálculos, versão de cada certificado
- Pra que possa: passar auditoria sem precisar virar a noite anterior
- Categoria: funcional + emocional (sobrevivência)
- Métrica de sucesso: auditor sai com NC zero ou ≤1 por software
- Solução hoje: improvisa documentação na semana da auditoria
- Concorrente que mais resolve hoje: Beamex CMX, MasterControl, ProCalV5 (21 CFR Part 11)
- Prioridade MVP-1: alta (INV-004a/b/c + cl. 7.11)
```

```
JTBD-032 | Manter padrões em ordem (validade, localização, uso)
- Quem: metrologista
- Quando: planejamento mensal
- Quero: dashboard de padrões com validade, localização, último uso, custo de recalibração esperado
- Pra que possa: planejar recalibração com tempo (evitar parar o lab)
- Categoria: funcional
- Métrica de sucesso: zero padrão vence sem aviso prévio de ≥60 dias
- Solução hoje: planilha mestre + memória
- Concorrente que mais resolve hoje: Cali, Metroex, Qualer
- Prioridade MVP-1: alta (sub-domínio "Padrões e Rastreabilidade")
```

```
JTBD-033 | Treinar técnico júnior sem virar babá
- Quem: metrologista (sênior)
- Quando: novo técnico chega
- Quero: trilha de procedimento embutida no app (passo a passo, evidência de execução)
- Pra que possa: delegar com segurança
- Categoria: social (parecer bom líder) + funcional
- Métrica de sucesso: técnico júnior produtivo em < 30 dias
- Solução hoje: paira ao lado por 3 meses (custo alto)
- Concorrente que mais resolve hoje: nenhum BR forte; MasterControl (procedimentos prontos) parcial
- Prioridade MVP-1: baixa (MVP-2)
```

---

### 3.6 Financeiro

**Perfil:** lida com NF-e, NFS-e, boleto, conciliação. Pressão da Receita + cliente + dono.

```
JTBD-034 | Emitir NFS-e do município certo sem aprender 26 prefeituras
- Quem: financeiro
- Quando: OS executada, cliente em município X
- Quero: emissão automática conforme padrão do município (próprio SP, ADN nacional RJ, etc.)
- Pra que possa: não estudar layout de prefeitura
- Categoria: funcional + emocional (não-pode-errar-fisco)
- Métrica de sucesso: 100% das NFS-e emitidas aceitas pela prefeitura na 1ª tentativa
- Solução hoje: emissor da prefeitura + cópia manual; ou Bling/Conta Azul (sem integração com OS)
- Concorrente que mais resolve hoje: FP2 (só Santa Maria); BaaS fiscal (Focus, PlugNotas) sem integrar com calibração
- Prioridade MVP-1: alta (R-016 cutover 01/09/2026)
```

```
JTBD-035 | Conciliar pagamento PIX/boleto sem virar Excel
- Quem: financeiro
- Quando: extrato do banco chega
- Quero: conciliação automática (PIX por txid; boleto por nosso número)
- Pra que possa: não passar 4h por semana batendo extrato
- Categoria: funcional + emocional (esgotamento)
- Métrica de sucesso: > 90% de auto-conciliação; tempo manual < 1h/semana
- Solução hoje: planilha + extrato em PDF
- Concorrente que mais resolve hoje: Conta Azul, Omie (forte); Bling
- Prioridade MVP-1: alta (financeiro de alto nível está no MVP-1 confirmado)
```

```
JTBD-036 | Cobrar atrasado sem ficar mal com cliente
- Quem: financeiro
- Quando: vencimento passou
- Quero: régua de cobrança automática (e-mail/WhatsApp/SMS) com escala
- Pra que possa: não ser eu o "chato" da história
- Categoria: emocional + funcional
- Métrica de sucesso: redução de inadimplência > 20%; horas/mês em cobrança caem 50%
- Solução hoje: lembrete no calendário + ligação pessoal
- Concorrente que mais resolve hoje: Asaas, Cobre Fácil; ERPs (Omie/Conta Azul)
- Prioridade MVP-1: média (MVP-2)
```

```
JTBD-037 | Saber margem de cada cliente/serviço sem pedir pro contador
- Quem: financeiro (e dono)
- Quando: avaliação trimestral
- Quero: relatório margem por cliente / por tipo de serviço / por técnico
- Pra que possa: identificar quem dá prejuízo
- Categoria: funcional
- Métrica de sucesso: relatório em < 5 min com dados do mês fechado
- Solução hoje: contador faz semestral (e cobra)
- Concorrente que mais resolve hoje: Omie, Sankhya (parcial)
- Prioridade MVP-1: baixa (MVP-2)
```

```
JTBD-038 | Não tomar surpresa de imposto no fim do trimestre
- Quem: financeiro
- Quando: virada de mês
- Quero: provisão de imposto calculada em tempo real (ISS, PIS, COFINS, IRPJ, CSLL)
- Pra que possa: separar dinheiro antes
- Categoria: funcional + emocional
- Métrica de sucesso: variação real vs provisionado < 5%
- Solução hoje: estimativa "do olhômetro"
- Concorrente que mais resolve hoje: Omie, Conta Azul (forte)
- Prioridade MVP-1: baixa
```

```
JTBD-039 | Saber quanto vou receber e quanto vou pagar nos próximos 30 dias
- Quem: financeiro
- Quando: planejamento semanal
- Quero: fluxo de caixa projetado com OS em aberto, NF emitidas, boletos a vencer, contas a pagar
- Pra que possa: avisar dono se vai dar problema
- Categoria: funcional + emocional
- Métrica de sucesso: projeção dos próximos 30 dias com erro < 10%
- Solução hoje: planilha estática
- Concorrente que mais resolve hoje: ERPs financeiros
- Prioridade MVP-1: alta
```

---

### 3.7 Comercial / vendedor

**Perfil:** caça lead, fecha contrato, segue cliente. Comissionado, urgência por fechamento.

```
JTBD-040 | Saber qual prospect tem maior chance de fechar essa semana
- Quem: vendedor
- Quando: começo da semana
- Quero: pipeline ordenado por score (tempo no funil, interações, sinais de compra)
- Pra que possa: priorizar ligações
- Categoria: funcional
- Métrica de sucesso: taxa de fechamento sobe 15-20%
- Solução hoje: cabeça + planilha
- Concorrente que mais resolve hoje: Pipedrive, RD Station, HubSpot
- Prioridade MVP-1: baixa (CRM básico no MVP-1; score em MVP-2)
```

```
JTBD-041 | Mostrar pro cliente um orçamento que parece profissional (não Word amarelo)
- Quem: vendedor
- Quando: envio de proposta
- Quero: template visual customizado por cliente, com logo, escopo, prazo, condições
- Pra que possa: aumentar percepção de valor (e ticket)
- Categoria: social + funcional
- Métrica de sucesso: ticket médio sobe; tempo de fechamento cai
- Solução hoje: Word de 2015 com logo deformada
- Concorrente que mais resolve hoje: PandaDoc, Proposify, Bling (parcial)
- Prioridade MVP-1: alta (orçamento confirmado MVP-1)
```

```
JTBD-042 | Saber histórico do cliente antes da reunião
- Quem: vendedor
- Quando: indo pra reunião
- Quero: ficha do cliente com últimas OS, certificados, pendências, ticket médio, "quem da empresa atende"
- Pra que possa: chegar com contexto e não fazer pergunta básica
- Categoria: social + funcional
- Métrica de sucesso: zero pergunta básica sobre "vocês usam X mesmo?"
- Solução hoje: pergunta pro atendente
- Concorrente que mais resolve hoje: CRM genérico
- Prioridade MVP-1: alta
```

```
JTBD-043 | Calcular comissão sem brigar com financeiro
- Quem: vendedor
- Quando: virada de mês
- Quero: relatório de comissões automático por regra (cliente novo, recorrente, tipo de serviço)
- Pra que possa: confiar no número
- Categoria: emocional + funcional
- Métrica de sucesso: zero discordância recorrente
- Solução hoje: planilha do gerente, contestada pelo vendedor
- Concorrente que mais resolve hoje: Omie (parcial)
- Prioridade MVP-1: baixa (MVP-2)
```

```
JTBD-044 | Acompanhar contratos recorrentes (calibração anual programada) pra não perder renovação
- Quem: vendedor
- Quando: 60-90 dias antes do vencimento do contrato/calibração anual
- Quero: alerta automático + sugestão de proposta de renovação
- Pra que possa: garantir receita recorrente
- Categoria: funcional + emocional (não-deixar-cair)
- Métrica de sucesso: > 85% de taxa de renovação
- Solução hoje: cabeça + planilha
- Concorrente que mais resolve hoje: nenhum dedicado
- Prioridade MVP-1: alta (calibração é negócio recorrente; isso é vital)
```

```
JTBD-045 | Visitar cliente novo sem precisar montar apresentação corporativa
- Quem: vendedor
- Quando: primeira visita
- Quero: portal/print pronto com cases, normas atendidas, escopo de calibração
- Pra que possa: focar em ouvir, não em vender com slide
- Categoria: social
- Métrica de sucesso: tempo de preparação < 15 min por visita
- Solução hoje: monta no PowerPoint na véspera
- Concorrente que mais resolve hoje: nenhum
- Prioridade MVP-1: baixa
```

---

## 4. Big Jobs — os 5-7 jobs centrais que VENDEM o produto

> Transversais aos papéis. São o "porquê" alguém compra o produto. Se o Aferê resolver bem só esses 5-7, ganha o mercado. Se entregar perfeito todo o resto e falhar nesses, perde.

| ID | Big Job | Categoria | Quem mais sente | Concorrente que mais resolve |
|---|---|---|---|---|
| **BIG-01** | **Fechar o ciclo CHAMADO → ORÇAMENTO → OS → CALIBRAÇÃO → CERTIFICADO → NFS-e dentro de UM sistema, sem cópia manual entre 4 ferramentas** | Funcional + emocional | Todos os papéis | Nenhum no BR (FP2 parcial só Santa Maria) — **gap central, eixo da venda** |
| **BIG-02** | **Não perder acreditação RBC nem tomar NC por erro que software poderia evitar** | Emocional + funcional | Dono, metrologista | Cali, Metroex, Beamex (parcial) |
| **BIG-03** | **Servir 4 perfis de empresa (A/B/C/D) no mesmo sistema, com regras configuráveis** — trilha de evolução até acreditação | Funcional + emocional | Dono, gerente | **Nenhum** — diferencial defensável único do Aferê |
| **BIG-04** | **Emitir NFS-e municipal correta em qualquer prefeitura do Brasil (Padrão Nacional + variantes próprias SP/Goiânia/Brasília)** | Funcional | Financeiro, dono | FP2 (1 município); BaaS fiscal externo sem ligar com OS |
| **BIG-05** | **Operar 100% mobile no campo, offline-first, sem o técnico voltar à sede pra "registrar"** | Funcional + emocional | Técnico, gerente | Beamex bMobile, Metroex Coletor, Auvo (sem semântica calibração) |
| **BIG-06** | **Atender Metrologia Legal (balança comercial/rodoviária) junto com Metrologia Voluntária (RBC) na mesma ferramenta** — calendário IPEM + selo + auditoria | Funcional + social | Gerente, dono | Nenhum (R-040 confirma o gap) |
| **BIG-07** | **Dar pro cliente final do nosso cliente um portal/visão (download certificado, abrir chamado, ver status) que parece corporativo** — sem que o tenant precise pagar UX próprio | Social + funcional | Dono, atendente | Cali WEB, MasterControl (perfil A grande) |

---

## 5. Anti-jobs — o que o produto NÃO deve resolver

> Decididos AGORA pra evitar scope creep durante MVP-1. Cada anti-job tem motivo explícito.

| Anti-job | Por que NÃO | Onde resolver |
|---|---|---|
| **ANTI-01** | **Folha de pagamento, ponto eletrônico, holerite, férias** | Domínio RH completo é mercado próprio (Senior, ADP, Sankhya RH); ROI baixo pro nosso ICP; complexidade trabalhista alta | Integração externa (Pontomais, Sankhya RH) — domínio `RH/Pessoas` marcado como lazy em `dominio-de-negocio.md` |
| **ANTI-02** | **Pagamento online com cartão direto** (gateway próprio) | Vira PCI-DSS 4.0.1 escopo full (R-025); custo de auditoria anual + risco operacional desproporcional ao ticket | Usar PSP terceiro (Asaas, Pagar.me, Stripe) — escopo SAQ A |
| **ANTI-03** | **Gestão clínica/laboratório de análises clínicas humanas** (LIS) | Domínio próprio (CFM 1821/2007, SBIS-CFM); regulamentação distinta; ABNT NBR ISO 15189 ≠ 17025 | Fora de escopo; se cliente farma exigir, consultar caso a caso em MVP-3+ |
| **ANTI-04** | **ERP horizontal genérico** (vender pra restaurante, oficina mecânica genérica) | "Founder is customer" + R-001 (customização disfarçada); produto perderia foco no nicho defensável | Foco em ICP "empresa de assistência técnica + lab calibração" — verticais adjacentes (oficina mecânica) só com decisão estratégica |
| **ANTI-05** | **BI/Analytics sofisticado** (dashboards customizados pelo cliente, query SQL pelo usuário) | Custo de UX e suporte alto; gigantes resolvem melhor (Metabase, PowerBI, Looker) | Dashboards essenciais nativos (10-15 KPIs fixos por papel); export pra BI externo via API |
| **ANTI-06** | **Hardware proprietário** (calibrador documentador, sensor, dispositivo de coleta) | Não somos fabricante; Beamex/Fluke/Presys já fazem; integração via Bluetooth/USB é viável | Integrar com hardware existente via API/protocolo padrão (MODBUS, OPC-UA) — MVP-2/3 |

---

## 6. Jobs por perfil de empresa (A/B/C/D)

> Cada job tem peso diferente conforme perfil. Aqui o que MUDA por perfil (não repete o que é comum a todos).

### Perfil A — Acreditado RBC/ISO 17025

| Job mais crítico | Por quê |
|---|---|
| BIG-02 (não perder acreditação) | Cgcre audita a cada 4 anos com supervisões anuais; **perder acreditação = perder cliente farma/automotivo** |
| JTBD-031 (provar validação de software) | Cl. 7.11 + auditoria trimestral de cliente farma |
| JTBD-028 (cadeia rastreabilidade automática) | INV-002 absoluta no perfil A; R-018 score 25 |
| JTBD-032 (gestão padrões) | Padrão vencido bloqueia emissão (INV-011) |
| JTBD-005 (acreditação inicial) | N/A — já é acreditado |

### Perfil B — Não-acreditado, padrões RBC rastreáveis

| Job mais crítico | Por quê |
|---|---|
| JTBD-003 (provar seriedade pra cliente novo) | Não tem selo RBC — precisa convencer com outras credenciais |
| BIG-03 (regras configuráveis) | Quer ligar regras "à la carte" — pode estar preparando-se pra acreditar |
| JTBD-007 (trilha B→A) | Pode querer migrar pra A |
| INV-015 (não emitir selo RBC) | Sistema deve bloquear emissão indevida |

### Perfil C — Em preparação pra acreditação

| Job mais crítico | Por quê |
|---|---|
| JTBD-005 (gap analysis pra RBC) | **Diferencial único** — software como trilha de evolução |
| JTBD-007 (migração C→A sem perder dado) | Evento estratégico que justifica a venda |
| JTBD-031 (validação software) | Já precisa documentar antecipadamente |

### Perfil D — Calibração comercial básica / só assistência técnica

| Job mais crítico | Por quê |
|---|---|
| BIG-01 (ciclo completo) | Quer ERP de OS + fiscal simples |
| BIG-04 (NFS-e) | É a coluna vertebral do negócio dele |
| BIG-05 (mobile campo) | Assistência técnica vive no campo |
| JTBD-012 (verificação periódica IPEM) | Se atende balança comercial — vital |
| **JTBD-027 / JTBD-031 (cálculo incerteza, validação software)** | **Desligados ou simplificados** — perfil D não precisa |

---

## 7. Jobs por tipo de instrumento

> Mesmo papel, instrumento diferente = job diferente. Aqui o que muda.

### Balança comercial (varejo)

| Job adicional | Categoria | Por quê |
|---|---|---|
| JTBD-012 (calendário verificação IPEM) | Funcional | Portaria 157/2022 — obrigação anual |
| **Marcar selo INMETRO de cada visita** | Funcional | Comprovação física pro cliente |
| Aviso de "esta calibração NÃO substitui verificação IPEM" no certificado | Social | R-040: evita cliente culpar nosso tenant por multa |

### Balança rodoviária

| Job adicional | Categoria | Por quê |
|---|---|---|
| Planejamento logístico de cargas-padrão grandes (100 kg-30 t) | Funcional | Custo logístico relevante; precisa programar com semanas |
| Certificado com implicação tributária (ICMS por peso) | Funcional | Impacto fiscal direto pro cliente |
| Verificação de capacidade técnica do tenant pra atender esse tipo | Funcional | R-041 — sistema alerta se tenant marcou "rodoviária" sem padrão |

### Balança analítica / semi-analítica (lab farma)

| Job adicional | Categoria | Por quê |
|---|---|---|
| Calibração em múltiplos pontos com incerteza expandida | Funcional | EURACHEM/CITAC + DOQ-CGCRE-008 |
| Conformidade FDA 21 CFR Part 11 (se cliente exporta) | Funcional | Cliente farma exige |
| Documentação IQ/OQ/PQ | Funcional | RDC 658/2022 Anvisa |

### Balança industrial / dosadora

| Job adicional | Categoria | Por quê |
|---|---|---|
| Calibração em condições de processo (não em laboratório) | Funcional | Linha de produção parada custa caro |
| Integração com SCADA/MES do cliente (export OPC-UA, MODBUS) | Funcional | MVP-2+ |

### Manômetro / termômetro / outros instrumentos

| Job adicional | Categoria | Por quê |
|---|---|---|
| Modelo de instrumento "genérico" (não só balança) | Funcional | Dominio-de-negocio.md confirma escopo amplo |
| Calibração de grandezas diferentes (pressão, temperatura, dimensional, elétrica) | Funcional | Cada uma com fórmula de incerteza diferente |

---

## 8. Síntese — Top 10 Jobs prioritários pro MVP-1

> Critério: combinação de (a) Big Job ou job de alta prioridade, (b) gap real (sem concorrente forte), (c) bloqueio de venda se não tiver, (d) ancorado em invariante regulatória.

| # | ID | Job | Por que entra no MVP-1 | Mitiga risco |
|---|---|---|---|---|
| **1** | BIG-01 | Ciclo completo chamado→OS→certificado→NFS-e em UM sistema | Eixo de venda; gap único no Brasil | R-001, R-013, R-019 |
| **2** | BIG-02 | Não perder acreditação por erro evitável | Vital pro perfil A; medo central do dono | R-018 (score 25) |
| **3** | BIG-03 | Configuração por perfil A/B/C/D | Diferencial defensável único; nenhum concorrente | R-001 |
| **4** | BIG-04 | NFS-e multi-prefeitura BR | R-016 (cutover 01/09/2026) é deadline duro | R-016, R-006 |
| **5** | BIG-05 | Mobile offline campo | Bloqueio de UX pro técnico; ADR-0003 mobile obrigatório | — |
| **6** | BIG-06 | Metrologia Legal (verificação IPEM) | MVP-1 obrigatório decidido em 16/05/2026; sem concorrente | R-040 |
| **7** | JTBD-027 | Cálculo incerteza embutido | Core técnico; sem isso não é software de calibração | — |
| **8** | JTBD-028 | Rastreabilidade automática (cadeia padrões) | INV-002; R-018 score 25 | R-018 |
| **9** | JTBD-021 + JTBD-024 | OS preparada/assinada no celular | Habilita BIG-05 | — |
| **10** | JTBD-001 + JTBD-013 + JTBD-039 | "1 número do dia/mês" pra dono e gerente | Vende valor imediato; entrega "wow" em demo | R-005 |

---

## 9. Como esse doc evolui

- **Onda 1 de entrevistas (5-8 empresas):** validar/desafiar cada job marcado `[a confirmar via entrevista]`. Perguntas-chave estão em `validacao-ativa.md`.
- **Onda 2 (10-15 empresas):** descobrir jobs **que o agente não previu** (provavelmente os mais valiosos). Esperar 5-15 jobs novos vindos do campo.
- **Após cada onda:** re-priorizar Top 10; mover jobs entre prioridade alta/média/baixa; promover/rebaixar Big Jobs com base em frequência.
- **Anti-jobs:** revisitar a cada release pra não deixar scope creep entrar pela porta dos fundos.
- **Versão fechada de Top 10** vira input direto de `dores-mapeadas.md` (cada job → dor mensurável) e `sintese-final.md` (top-10 dores + top-10 jobs = base do MVP-1).

---

## 10. Glossário rápido pro Roldão (linguagem de negócio)

- **Job** = trabalho real que a pessoa quer ver feito (não confundir com tela ou botão do sistema).
- **Status quo** = o jeito porco que ela faz hoje (planilha + WhatsApp + Word).
- **Anti-job** = trabalho que a gente decide NÃO fazer (e não vai ter culpa por isso).
- **Big Job** = os 5-7 trabalhos centrais que, se a gente fizer bem, justifica a venda sozinhos.
- **Métrica de sucesso** = como medir se o trabalho foi bem feito (geralmente: mais rápido, menos erro, menos vergonha, menos R$).
