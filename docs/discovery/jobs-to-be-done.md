# Discovery — Jobs To Be Done (JTBD)

> **Artefato Rodada 0 — Batch 2** (agente faz sozinho; Roldão valida em entrevistas Onda 1+2).
> **Atualizado:** 2026-05-17 — 4ª passagem: decisão fundadora "Módulo de Comissões Configuráveis" (Roldão 17/05/2026) → BIG-09 novo + 12 JTBDs (JTBD-071 a JTBD-082) cobrindo configuração, fechamento, previsão por colaborador, bloqueio por margem, aprovação, auditoria e divisão por participantes/recebimento. Top 10 re-rankeado com BIG-09 entrando em #7.
> **Atualizado:** 2026-05-17 — 3ª passagem após 2ª rodada de auditoria do Roldão (15 correções aceitas): Big Job novo de Frota/UMC + Caixa do Técnico, 11 JTBDs novos de operação de campo, BIG-01 elevado a eixo primário junto com BIG-03, costura nominal com personas, tradução inline de códigos, padronização cliente final vs tenant.
> **Status:** scaffolding **preenchido** com inferências do agente; toda linha marcada `[a confirmar via entrevista]` precisa virar evidência antes de virar requisito.
> **Saída desse doc alimenta:** `dores-mapeadas.md`, `personas-detalhadas.md`, `sintese-final.md`, `validacao-ativa.md` (perguntas das entrevistas).

---

## 1. O que esse documento responde

Quais são os PROBLEMAS REAIS que cada pessoa da empresa precisa resolver no dia a dia. Não é "tela X" ou "botão Y" — é "preciso saber se vou pagar a folha no fim do mês" ou "preciso não levar multa do INMETRO".

Mapeamos **80+ problemas** no total. **9 são os GRANDES (Big Jobs)** que justificam comprar o sistema sozinhos. **11 são problemas que decidimos NÃO resolver (Anti-jobs)** pra manter o produto enxuto.

> Os princípios do framework JTBD (Christensen + Ulwick) que guiaram este doc estão no **Apêndice A** no fim do arquivo — quem nunca trabalhou com JTBD pode ler antes de continuar.

---

## 2. Como ler cada job

Cada job tem 10 campos. Modelo:

```
JTBD-NNN | <título curto>
- Quem: <papel> (persona: Roldão / Sandra / Letícia / Bruno / Marcos / Cláudia / Rogério / João)
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

### Glossário rápido pra ler este doc

- **tenant** = empresa que assina o SaaS Aferê (ex: o laboratório de calibração + assistência técnica do Roldão).
- **cliente final** = cliente do tenant (ex: indústria farmacêutica que recebe certificado emitido pelo lab acreditado). **Quando o doc diz só "cliente" dentro de um job do tenant, está se referindo ao cliente final** (cliente da empresa do Roldão) — não ao cliente do Aferê.
- **end-customer** = sinônimo de cliente final usado em alguns lugares (§4.6).
- **R-NNN** = risco mapeado em `riscos.md` (ex: R-018 = risco 018: certificado sem cadeia rejeitado por Cgcre).
- **D-NNN** = dor mapeada em `jornada-atual-sem-produto.md` §Dores (ex: D-001 = cadastro de cliente digitado 4-6 vezes em sistemas que não conversam).
- **INV-NNN** = regra fixa do produto (ex: INV-002 = emissão exige cadeia de rastreabilidade completa do padrão usado até o SI).
- **BaaS fiscal** = "Backend-as-a-Service" fiscal — empresa terceirizada que cuida só de emissão de nota fiscal (Focus NFe, PlugNotas).
- **Cgcre** = Coordenação Geral de Acreditação (parte do INMETRO) — quem acredita laboratórios RBC.
- **NC** = Não Conformidade (achado de auditoria que pode tirar a acreditação RBC se grave).
- **RBC** = Rede Brasileira de Calibração — selo Cgcre/INMETRO + reconhecimento ILAC MRA.
- **ICP-Brasil** = Infraestrutura de Chaves Públicas Brasileira (certificado digital com validade jurídica, ex: e-CPF).
- **OS** = Ordem de Serviço — documento que autoriza execução de um serviço.
- **UMC** = Unidade Móvel de Calibração — caminhão equipado com pesos-padrão calibrados pra calibrar balança rodoviária em campo.
- **TCO** = Total Cost of Ownership — custo total do veículo/mês (depreciação + IPVA + seguro + combustível + manutenção + multas).
- **IPEM / RBMLQ-I** = órgão estadual delegado pelo INMETRO pra verificação metrológica legal (balança comercial, bomba de combustível, etilômetro, taxímetro).
- **Cl. 7.10 / 7.11 / 6.2** = cláusulas da norma ABNT NBR ISO/IEC 17025:2017 (NC, validação de software, competência de pessoal).

---

## 3. Jobs por papel humano

> 7 papéis identificados em `dominio-de-negocio.md` §Papéis. Mínimo 5 jobs por papel.

### 3.1 Dono / sócio (Roldão é exemplo desse papel)

**Perfil:** decide estratégia, paga a folha, vive ansiedade de "o sistema vai cair no meio da auditoria?" e "vou ganhar dinheiro esse mês?".

**Jobs principais (resumo):** ver "1 número do dia" (JTBD-001 + JTBD-097), não perder acreditação (BIG-02), trilha de evolução D→A (BIG-03), ver custo real de campo (BIG-08), configurar e aprovar comissões sem depender de programador (BIG-09 — JTBD-071, JTBD-072, JTBD-076, JTBD-078, JTBD-080), **Cliente 360° + automações sem programador (BIG-10/BIG-11 — JTBD-084, 087, 090, 097)**.

```
JTBD-001 | Saber se o mês vai fechar no azul antes do mês fechar
- Quem: dono (persona: Roldão)
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
- Quem: dono (persona: Roldão; perfis A, B, C) — também ressoa em Sandra (RT)
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
- Quem: dono (persona: Roldão; todos perfis, especialmente B/C/D) + vendedor (Rogério)
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
- Quem: dono (persona: Roldão)
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
- Quem: dono (persona: Roldão; perfil B/C)
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
- Quem: dono (persona: Roldão)
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
- Quem: dono (persona: Roldão; perfil C/D em crescimento)
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

**Jobs principais (resumo):** triagem chamado em 30s (JTBD-008), agenda de técnico inteligente (JTBD-009 a 011), aprovar adiantamento/inventário (JTBD-063, JTBD-106), **disparar retenção em NPS negativo (JTBD-085)**, **alerta de cliente inativo + oportunidade de equipamento sem manutenção (JTBD-090, JTBD-096)**, **alerta automático de divergência de inventário (JTBD-106)**, **testar regra de automação em sandbox antes de ativar (JTBD-087)**.

```
JTBD-008 | Decidir em 30 segundos se chamado novo é manutenção ou calibração
- Quem: gerente (persona: Sandra)
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
- Quem: gerente (persona: Sandra)
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
- Quem: gerente (persona: Sandra)
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
- Quem: gerente (persona: Sandra)
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
- Quem: gerente (persona: Sandra)
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
- Quem: gerente (persona: Sandra)
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
- Quem: gerente (persona: Sandra)
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

**Jobs principais (resumo):** identificar cliente em 5s (JTBD-015), abrir chamado sem perder info (JTBD-016), responder "cadê meu certificado" sem levantar (JTBD-017), não cometer gafe de cobrança (JTBD-018), **abrir cadastro+chamado+oportunidade em 1 clique a partir do WhatsApp (JTBD-086)**, **Cliente 360° em uma tela só (JTBD-091)**.

```
JTBD-015 | Identificar o cliente em 5 segundos quando ele liga
- Quem: atendente (persona: Letícia)
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
- Quem: atendente (persona: Letícia)
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
- Quem: atendente (persona: Letícia)
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
- Quem: atendente (persona: Letícia)
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
- Quem: atendente / vendedor (personas: Letícia / Rogério)
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
- Quem: atendente (persona: Letícia)
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

**Jobs principais (resumo):** tudo da OS antes de chegar (JTBD-021), executar offline (JTBD-022), assinatura no celular (JTBD-024), não voltar à sede (JTBD-025), ver previsão da minha comissão no app (JTBD-073), **solicitar peça com aceite 2-etapas + baixar peça automaticamente na OS + registrar destino de peça retirada (JTBD-098 a 100)**, **aplicar/retirar lacre e selo INMETRO com foto obrigatória (JTBD-101 a 103)**, **registrar estoque offline e sincronizar (JTBD-109)**.

```
JTBD-021 | Saber TUDO da próxima OS antes de chegar no cliente
- Quem: técnico de campo (persona: Bruno)
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
- Quem: técnico de campo (persona: Bruno)
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
- Quem: técnico de campo (persona: Bruno)
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
- Quem: técnico de campo (persona: Bruno)
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
- Quem: técnico de campo (persona: Bruno)
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
- Quem: técnico de campo (persona: Bruno)
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
- Quem: metrologista (persona: Marcos)
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
- Quem: metrologista (persona: Marcos)
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
- Quem: metrologista (persona: Marcos)
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
- Quem: metrologista signatário (persona: Marcos)
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
- Quem: metrologista (persona: Marcos)
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
- Quem: metrologista (persona: Marcos)
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
- Quem: metrologista sênior (persona: Marcos) + RT Qualidade (Sandra)
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

**Jobs principais (resumo):** NFS-e municipal correta (BIG-04 / JTBD-034), conciliar pagamentos (JTBD-035), fluxo de caixa projetado (JTBD-039), fechar comissão do mês em poucos minutos com auditoria de cada ajuste (JTBD-074, JTBD-077, JTBD-082), **régua automática de cobrança com escalada (JTBD-088)**, **bloqueio de orçamento pra inadimplente (JTBD-095)**.

```
JTBD-034 | Emitir NFS-e do município certo sem aprender 26 prefeituras
- Quem: financeiro (persona: Cláudia)
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
- Quem: financeiro (persona: Cláudia)
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
- Quem: financeiro (persona: Cláudia)
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
- Quem: financeiro (persona: Cláudia) + dono (Roldão)
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
- Quem: financeiro (persona: Cláudia)
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
- Quem: financeiro (persona: Cláudia)
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

**Jobs principais (resumo):** orçamento profissional rápido (JTBD-041), histórico do cliente (JTBD-042), pipeline com prioridade (JTBD-040), renovação de contrato (JTBD-044), ver previsão de comissão por estágio do pipeline e impacto de desconto (JTBD-075, JTBD-081), **lista priorizada de clientes pra ligar hoje (JTBD-083)**, **proposta de renovação automática 60d antes do vencimento (JTBD-092)**, **flag automática de cliente fixo com condição comercial diferenciada (JTBD-094)**.

```
JTBD-040 | Saber qual prospect tem maior chance de fechar essa semana
- Quem: vendedor (persona: Rogério)
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
- Quem: vendedor (persona: Rogério)
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
- Quem: vendedor (persona: Rogério)
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
- Quem: vendedor (persona: Rogério)
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
- Quem: vendedor (persona: Rogério)
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
- Quem: vendedor (persona: Rogério)
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

---

### 3.8 Jobs emocionais e sociais de primeira classe

> Auditoria 17/05/2026 apontou que jobs emocionais/sociais estavam sub-representados. Adicionados 8 jobs onde a dor é principalmente "como me sinto / como sou visto" — não "que tarefa preciso fazer". Esses jobs vendem o produto tanto quanto os funcionais.

```
JTBD-046 | Não me sentir o pequeno da sala em reunião com cliente farma grande
- Quem: dono (persona: Roldão)
- Quando: primeira reunião com cliente farma de porte (Sanofi, EMS, Aché)
- Quero: ter dashboard/portal de credenciais que me dê presença executiva
- Pra que possa: negociar preço sem dar desconto por insegurança
- Categoria: social
- Métrica de sucesso: ticket médio em cliente grande sobe; desconto médio cai
- Solução hoje: PowerPoint feito na véspera; sentir-se "intruso"
- Concorrente que mais resolve hoje: nenhum no perfil B/C; SaaS internacional (Qualer) no perfil A
- Prioridade MVP-1: média (UI tem que transmitir profissionalismo)
- [a confirmar via entrevista]
```

```
JTBD-047 | Parar de perder fim-de-semana revisando documentação atrasada
- Quem: RT Qualidade (persona: Sandra)
- Quando: Cgcre marca data de auditoria de supervisão
- Quero: sistema que me diga "está pronto" sem eu precisar passar 3 sábados revisando 47 procedimentos Word
- Pra que possa: dormir tranquila e ter vida pessoal
- Categoria: emocional
- Métrica de sucesso: zero fim-de-semana sacrificado por preparação de auditoria
- Solução hoje: planilha pintada de amarelo + memória + adrenalina
- Concorrente que mais resolve hoje: nenhum integra qualidade + execução
- Prioridade MVP-1: alta (atinge persona Sandra que é decisora técnica)
```

```
JTBD-048 | Não passar vergonha quando recomendo o sistema pra outro dono de lab amigo
- Quem: dono (persona: Roldão)
- Quando: conversa de bastidor em feira (Metrologia BR), grupo de WhatsApp do setor
- Quero: ter certeza de que o produto recomendado não vai me envergonhar
- Pra que possa: virar evangelista do produto (driver de aquisição orgânica)
- Categoria: social
- Métrica de sucesso: NPS > 50; > 30% de leads novos vêm de indicação
- Solução hoje: cuidado em recomendar qualquer coisa
- Concorrente que mais resolve hoje: produto que entrega o que promete
- Prioridade MVP-1: indireta — é métrica de saúde, não feature
- [a confirmar via entrevista]
```

```
JTBD-049 | Não me sentir derrotado quando perdemos cliente pra concorrente acreditado
- Quem: dono (persona: Roldão)
- Quando: cliente migra pra lab acreditado RBC por exigência regulatória
- Quero: ter narrativa interna ("estou no caminho, BIG-03 me leva lá") em vez de "decidi errado"
- Pra que possa: manter motivação pra investir na trilha de acreditação
- Categoria: emocional
- Métrica de sucesso: dono não desiste do plano de migrar pra A
- Solução hoje: aceitar a perda; reclamar com sócio
- Concorrente que mais resolve hoje: consultor de qualidade (caro)
- Prioridade MVP-1: indireta — atendida via BIG-03
- [a confirmar via entrevista]
```

```
JTBD-050 | Não sentir que estou pagando salário pra babá quando técnico júnior pergunta o básico
- Quem: RT Qualidade (persona: Sandra) + metrologista sênior (Marcos)
- Quando: técnico júnior pergunta a mesma coisa de procedimento pela 3ª vez
- Quero: trilha de procedimento embutida que o júnior consulta sozinho
- Pra que possa: focar em trabalho de alto valor, não em supervisão de checklist
- Categoria: emocional
- Métrica de sucesso: redução > 50% de perguntas básicas; técnico júnior produtivo em < 30 dias
- Solução hoje: paira ao lado 3 meses; reescreve procedimento Word
- Concorrente que mais resolve hoje: MasterControl (procedimentos prontos — caro)
- Prioridade MVP-1: baixa (MVP-2; mas marcar como driver de retenção da persona Sandra)
```

```
JTBD-051 | Ter certeza de que não estou colocando minha CRQ em risco quando assino em massa
- Quem: signatário (persona: Marcos)
- Quando: pilha de 20+ certificados pra assinar no fim do dia
- Quero: cada certificado mostrar checklist verde de invariantes (padrão válido, cadeia OK, sem NC pendente)
- Pra que possa: assinar com confiança, sem revisar manualmente cada um
- Categoria: emocional (sobrevivência profissional)
- Métrica de sucesso: zero certificado assinado que cause NC retrospectiva
- Solução hoje: confiar em planilhas + cabeça; revisar amostra
- Concorrente que mais resolve hoje: MasterControl (forte); Beamex CMX
- Prioridade MVP-1: alta (atende INV-002 + INV-011 + INV-012 do produto, e tira ansiedade do Marcos)
```

```
JTBD-052 | Ter argumento técnico claro pra explicar preço pro cliente final
- Quem: dono (persona: Roldão) + vendedor (Rogério)
- Quando: cliente questiona "por que tão caro?"
- Quero: relatório/folder que mostre custo de padrão + horas de signatário + acreditação Cgcre
- Pra que possa: não negociar preço por desespero
- Categoria: social
- Métrica de sucesso: desconto médio cai; tempo de fechamento sobe (mas margem sobe mais)
- Solução hoje: explicar de cabeça; perder a venda; aceitar desconto
- Concorrente que mais resolve hoje: nenhum
- Prioridade MVP-1: baixa (MVP-2 — gerador de relatório)
- [a confirmar via entrevista]
```

```
JTBD-053 | Não me sentir indelicada/o quando cobro cliente atrasado
- Quem: financeiro (persona: Cláudia) + atendente (Letícia, quando acumula)
- Quando: cliente atrasou pagamento e tem OS ativa
- Quero: régua automática de cobrança polida (e-mail + WhatsApp via template)
- Pra que possa: não ser a pessoa "chata" da relação, manter cliente engajado
- Categoria: emocional + social
- Métrica de sucesso: inadimplência cai > 20%; zero cliente "perdido" por cobrança constrangedora
- Solução hoje: lembrete pessoal + ligação direta (constrangedora)
- Concorrente que mais resolve hoje: Asaas, Cobre Fácil (genéricos)
- Prioridade MVP-1: média (MVP-2 — mas registrar como prioridade da Cláudia)
```

---

### 3.9 JTBDs funcionais adicionados na auditoria 17/05/2026

```
JTBD-054 | Cadastrar cliente UMA vez e ter ele em todos os fluxos (D-001 — cadastro 4-6x)
- Quem: atendente (Letícia) + financeiro (Cláudia) + dono (Roldão)
- Quando: cliente novo entra; cliente existente muda dado
- Quero: cadastro único propagado pra OS, certificado, NFS-e, cobrança
- Pra que possa: não re-digitar o mesmo CPF/CNPJ em 4-6 sistemas
- Categoria: funcional + emocional
- Métrica de sucesso: dor D-001 zerada; tempo de cadastro novo < 2 min
- Solução hoje: digitação manual em Bling + Cali + planilha + e-mail
- Concorrente que mais resolve hoje: ERP horizontal (Bling, Conta Azul) mas sem ligar com Cali/Metroex
- Prioridade MVP-1: ALTA (promovido a BIG-07 — Top 10 #9)
```

```
JTBD-055 | Calibrar instrumento desconhecido sem escrever procedimento do zero (gap G8)
- Quem: metrologista (Marcos)
- Quando: cliente solicita calibração de instrumento que o lab nunca atendeu
- Quero: biblioteca de procedimentos técnicos pré-aprovados em PT-BR por grandeza/faixa
- Pra que possa: não escrever procedimento do zero a cada vez
- Categoria: funcional + emocional
- Métrica de sucesso: tempo de "novo instrumento" até "calibração executável" cai 70%
- Solução hoje: copia procedimento de cliente parecido; adapta; valida com RT
- Concorrente que mais resolve hoje: MasterControl (forte mas internacional); nenhum BR
- Prioridade MVP-1: baixa (MVP-3 — exige curadoria técnica especializada)
- [a confirmar via entrevista]
```

---

### 3.10 JTBDs específicos da RT Qualidade (Sandra) — gap identificado na auditoria

> Auditoria 17/05/2026 apontou que a Sandra estava sub-representada — só JTBD-031 era explicitamente dela. Adicionados 4 jobs core da função de RT.
>
> **Jobs adicionais da RT cobertos por outras seções (decisões fundadoras 17/05/2026):** Cliente 360° em uma tela (JTBD-091, §3.13), workflow automático pra reclamação ISO 7.9 (JTBD-093, §3.13), responder fiscalização IPEM sobre selo aplicado (JTBD-108, §3.14), divergência de inventário com alerta + aprovação (JTBD-106, §3.14).

```
JTBD-056 | Manter matriz competência × signatário × grandeza sem planilha lateral
- Quem: RT Qualidade (Sandra)
- Quando: auditoria Cgcre pede comprovação; novo signatário entra; signatário muda escopo
- Quero: matriz estruturada que mostra quem está autorizado a assinar qual grandeza/faixa/método em qual data
- Pra que possa: cumprir ISO/IEC 17025 cl. 6.2 + INV-003 (autorização por escopo) sem montar Excel na hora
- Categoria: funcional + emocional
- Métrica de sucesso: matriz exportável em < 30s; zero certificado emitido por signatário não-autorizado
- Solução hoje: planilha "matriz_competencia_v17.xlsx" feita na semana da auditoria
- Concorrente que mais resolve hoje: nenhum BR forte; MasterControl parcial
- Prioridade MVP-1: alta (INV-003 depende disso)
```

```
JTBD-057 | Gerir NC (cláusula 7.10) com workflow estruturado em vez de e-mail + WhatsApp
- Quem: RT Qualidade (Sandra)
- Quando: NC detectada (auditoria interna, reclamação cliente, erro de processo)
- Quero: workflow guiado: abrir NC → causa raiz → ação corretiva → evidência → fechamento auditável
- Pra que possa: passar auditoria Cgcre com evidência rastreável
- Categoria: funcional + emocional (sobrevivência regulatória)
- Métrica de sucesso: 100% das NC com workflow completo arquivado; tempo médio de fechamento cai
- Solução hoje: planilha de controle de NC + e-mail + WhatsApp; quando fecha, apaga a entrada
- Concorrente que mais resolve hoje: Qualiex, Portal ISO (sem ligar com execução)
- Prioridade MVP-1: alta (BIG-02 depende disso)
```

```
JTBD-058 | Ativar "modo auditoria Cgcre" com 1 clique
- Quem: RT Qualidade (Sandra)
- Quando: auditor Cgcre chega; cliente farma quer auditar
- Quero: filtro/visão que mostra TODOS os registros do período: certificados emitidos, cadeia, NC, signatários autorizados, padrões usados, procedimentos vigentes
- Pra que possa: projetar na TV pro auditor sem virar a noite
- Categoria: funcional + emocional
- Métrica de sucesso: < 5 min do "auditor chegou" até "tela pronta"
- Solução hoje: improvisação de última hora; pasta de rede + planilhas
- Concorrente que mais resolve hoje: nenhum
- Prioridade MVP-1: alta (diferencial Sandra — vende o produto pra perfil A)
```

```
JTBD-059 | Gerir procedimentos com workflow de aprovação versionado
- Quem: RT Qualidade (Sandra)
- Quando: procedimento precisa ser revisado (norma nova, mudança de método, NC)
- Quero: workflow revisão → aprovação → treinamento → autorização; versão antiga vira read-only com selo "OBSOLETO"
- Pra que possa: parar de gerir Proc_17_v3.2_FINAL_REVISADO.docx em pasta de rede
- Categoria: funcional
- Métrica de sucesso: zero versão obsoleta em uso; rastro completo de aprovação
- Solução hoje: Word + pasta de rede + nome de arquivo como versionamento
- Concorrente que mais resolve hoje: MasterControl (forte); Qualiex (parcial)
- Prioridade MVP-1: média (MVP-2; mas registrar como driver Sandra perfil A)
```

---

### 3.11 JTBDs de Frota, UMC e Caixa do Técnico (decisão fundadora Roldão 17/05/2026)

> 11 jobs novos derivados da decisão fundadora "operação de campo + frota + UMC + caixa do técnico = módulo central". Detalhes técnicos do domínio em `dominio-de-negocio.md` §"Controle de Técnico em Campo, Despesas, Frota e UMC". Persona nova **Carlos** (motorista UMC) entra em `personas-detalhadas.md`.
>
> **Jobs adicionais do Carlos cobertos em outras seções (decisão fundadora Estoque 17/05/2026):** transferência de peça pro técnico em campo com 2-etapas/aceite (JTBD-104, §3.14).

```
JTBD-060 | Receber adiantamento por OS ou genérico sem pedir pelo WhatsApp
- Quem: técnico de campo (persona: Bruno)
- Quando: saindo em viagem de campo (1 dia ou mais)
- Quero: solicitar adiantamento pelo app (vinculado a OS específica OU genérico do mês) com aprovação digital
- Pra que possa: não depender de WhatsApp pra Cláudia "esquentar" a transferência
- Categoria: funcional + emocional (não-mendigar)
- Métrica de sucesso: > 95% das viagens com adiantamento aprovado antes da saída; zero pedido por WhatsApp
- Solução hoje: WhatsApp pra financeiro; PIX manual; planilha lateral do que cada técnico recebeu
- Concorrente que mais resolve hoje: nenhum no setor; ERPs corporativos (Sankhya, TOTVS) têm — caro e horizontal
- Prioridade MVP-1: alta (BIG-08)
```

```
JTBD-061 | Tirar foto da nota/recibo e categorizar no mobile sem perder comprovante
- Quem: técnico de campo (persona: Bruno) + motorista UMC (persona: Carlos)
- Quando: gasta em campo (combustível, pedágio, refeição, hospedagem, peça emergencial)
- Quero: tirar foto do comprovante, categorizar (combustível/refeição/hospedagem/pedágio/peça/outro), vincular a OS
- Pra que possa: não voltar com bolso cheio de papel amassado e perder 30% dos comprovantes
- Categoria: funcional
- Métrica de sucesso: > 95% das despesas com comprovante anexado; zero comprovante perdido
- Solução hoje: papel no bolso; foto solta no WhatsApp; muito comprovante perdido = empresa absorve custo
- Concorrente que mais resolve hoje: Expensify (genérico, sem ligar com OS); nenhum BR forte no nicho
- Prioridade MVP-1: alta (BIG-08)
```

```
JTBD-062 | Fazer prestação de contas em 5 min, sem planilha
- Quem: técnico (Bruno) + motorista UMC (Carlos)
- Quando: volta da viagem
- Quero: prestação guiada (despesas já categorizadas + foto anexada + KM rodado + saldo) com botão "enviar pra aprovação"
- Pra que possa: chegar em casa e descansar; não passar sábado mexendo em planilha
- Categoria: funcional + emocional (qualidade de vida)
- Métrica de sucesso: < 5 min por prestação; zero prestação atrasada > 7 dias
- Solução hoje: planilha Excel feita pelo financeiro; técnico digita à mão; demora 30-60 min
- Concorrente que mais resolve hoje: Expensify (genérico)
- Prioridade MVP-1: alta (BIG-08)
```

```
JTBD-063 | Aprovar/reprovar adiantamento com 1 clique baseado em política
- Quem: gerente (Sandra) ou financeiro (Cláudia)
- Quando: técnico solicitou adiantamento
- Quero: ver pedido com contexto (OS vinculada, histórico do técnico, política da empresa: máx R$ X por OS / R$ Y por dia) + botão aprovar/reprovar
- Pra que possa: liberar dinheiro rápido sem ficar revisando cada caso
- Categoria: funcional
- Métrica de sucesso: tempo médio aprovação < 30 min em horário comercial
- Solução hoje: WhatsApp + confiança; reuniões de "fechamento de caixa" mensais
- Concorrente que mais resolve hoje: nenhum integrado com OS
- Prioridade MVP-1: alta (BIG-08)
```

```
JTBD-064 | Registrar KM rodado por OS pra receber reembolso (carro próprio)
- Quem: técnico de campo com carro próprio (Bruno em alguns casos)
- Quando: usa o próprio veículo numa OS
- Quero: app abre/fecha o registro de KM (manual ou via GPS); vincula a OS; calcula valor por regra da empresa (R$/km)
- Pra que possa: ver no fim do mês quanto vou receber de reembolso e ter prova
- Categoria: funcional + emocional (não-ser-prejudicado)
- Métrica de sucesso: 100% dos KM rodados de OS registrados; reembolso fecha com diferença < 5%
- Solução hoje: anota em papel/agenda; manda planilha pro RH; muita discussão de KM "não-bate"
- Concorrente que mais resolve hoje: Auvo (GPS); nenhum com regra de reembolso configurável BR
- Prioridade MVP-1: alta (BIG-08)
```

```
JTBD-065 | Saber qual veículo está disponível antes de agendar OS de campo
- Quem: gerente de frota / gerente operacional (Sandra ou papel novo)
- Quando: vai agendar OS de campo (carro normal ou UMC pra balança rodoviária)
- Quero: ver agenda de cada veículo com bloqueios automáticos (documento vencido, manutenção pendente, já alocado em outra OS)
- Pra que possa: não mandar técnico com carro que vai ser parado em blitz / não agendar UMC parada na oficina
- Categoria: funcional + emocional (evitar fiasco)
- Métrica de sucesso: zero OS executada com veículo em situação irregular; zero conflito de alocação
- Solução hoje: planilha + memória + telefonema pro mecânico ("tá pronto?")
- Concorrente que mais resolve hoje: nenhum integrado com agenda de OS
- Prioridade MVP-1: alta (BIG-08)
```

```
JTBD-066 | Receber alerta automático de manutenção antes de quebrar na estrada
- Quem: gerente de frota / dono (Roldão)
- Quando: manutenção tá chegando (por KM ou por data — óleo, pneus, revisão)
- Quero: alerta 30/60 dias antes ou X% do KM-alvo + sugestão de agendamento
- Pra que possa: agendar com calma na concessionária/oficina certa, não em emergência na BR
- Categoria: funcional + emocional (evitar caos)
- Métrica de sucesso: > 90% das manutenções preventivas feitas dentro do prazo; zero quebra de motor por óleo vencido
- Solução hoje: hodômetro + memória + planilha "controle frota" desatualizada
- Concorrente que mais resolve hoje: Frota.io (genérico); softwares de gestão de transportadora — caros e fora do nicho
- Prioridade MVP-1: alta (BIG-08)
```

```
JTBD-067 | Ver multa com contexto (qual veículo, qual condutor, qual data, qual valor) pra decidir defender ou pagar
- Quem: gerente de frota / dono (Roldão)
- Quando: multa chega (Detran/PRF/PRE/MAERP)
- Quero: cadastrar a multa, vincular ao veículo + condutor da data + custo (multa + indicação + pontos CNH) + botão "defender (gera doc)" ou "pagar"
- Pra que possa: tomar decisão informada (multa cara/injusta = defender; multa barata = pagar) e cobrar do condutor se for o caso
- Categoria: funcional + social (cobrar técnico sem brigar)
- Métrica de sucesso: zero multa esquecida vira protesto; > 70% das multas defensáveis defendidas; CNH suspensa do condutor evitada
- Solução hoje: pasta de papel + WhatsApp ("foi você?"); muita multa esquecida vira protesto
- Concorrente que mais resolve hoje: Tag de pedágio (parcial); nenhum nacional integrado
- Prioridade MVP-1: alta (BIG-08; ver risco novo R-novo "multa não paga vira protesto + CNH suspensa")
```

```
JTBD-068 | Registrar abastecimento + KM + despesa no celular sem login complicado (motorista UMC)
- Quem: motorista UMC (persona: Carlos — usa o sistema mínimo possível)
- Quando: abastece, paga pedágio, faz qualquer despesa em viagem com UMC
- Quero: app simples (login fácil ou QR-code) com 4-5 botões grandes: "Abastecer", "Pedágio", "Refeição", "Hospedagem", "Outro"
- Pra que possa: registrar em 30s sem saber mexer com tela complicada
- Categoria: funcional (acessibilidade mobile pra perfil pouco técnico)
- Métrica de sucesso: motorista UMC consegue registrar despesa sem suporte do gerente
- Solução hoje: papel + envia foto pro grupo WhatsApp; muita despesa não-categorizada
- Concorrente que mais resolve hoje: nenhum desenhado pra perfil baixo-letramento-digital
- Prioridade MVP-1: alta (BIG-08; ADR-0003 mobile abrangente)
```

```
JTBD-069 | Saber custo real da UMC pra precificar OS de balança rodoviária
- Quem: dono (Roldão) ou gerente (Sandra) na precificação
- Quando: cliente pede orçamento de calibração de balança rodoviária
- Quero: simulador de custo da UMC pra atender essa OS (combustível diesel + pedágio na rota + diária motorista + manutenção rateada por km + custo de oportunidade dos pesos-padrão)
- Pra que possa: precificar com margem real, não no "olhômetro" — UMC tem custo altíssimo (caminhão truck, motorista CNH D/E+MOPP, pesos-padrão calibrados R$ 100-300k de massa transportada)
- Categoria: funcional + emocional (não-trabalhar-no-prejuízo)
- Métrica de sucesso: margem real por OS de balança rodoviária > 25% (hoje muitas dão prejuízo invisível)
- Solução hoje: chuta valor por km e por dia; faz manualmente em planilha
- Concorrente que mais resolve hoje: nenhum (nicho ultra-específico)
- Prioridade MVP-1: alta (BIG-08; diferencial único no mercado BR)
```

```
JTBD-070 | Decidir se vale manter veículo na frota ou vender/alugar (TCO por veículo)
- Quem: dono (Roldão)
- Quando: revisão trimestral/anual de frota
- Quero: TCO por veículo/mês = depreciação + IPVA + seguro + combustível + manutenção + multas, comparado com KM rodado e receita gerada
- Pra que possa: decidir vender o que dá prejuízo, alugar quando for sazonal, comprar veículo novo quando faz sentido
- Categoria: funcional
- Métrica de sucesso: decisão de frota baseada em dado, não em "feeling"; redução de custo de frota > 10% no primeiro ano
- Solução hoje: cabeça do dono + planilha do contador
- Concorrente que mais resolve hoje: Frota.io (parcial)
- Prioridade MVP-1: média (TCO consolidado pode entrar em MVP-2; dados brutos no MVP-1)
```

---

### 3.12 JTBDs de Comissões Configuráveis (decisão fundadora Roldão 17/05/2026)

> 12 jobs novos derivados da decisão fundadora "Módulo de Comissões Configuráveis = módulo central, não opcional nem genérico". Detalhes técnicos do domínio em `dominio-de-negocio.md` §"Módulo de Comissões Configuráveis" (8 formas de cálculo, múltiplos participantes, gatilho por recebimento, bloqueio por margem, auditoria de cada ajuste). Cobre o GAP do 7º "vazio absoluto" — nenhum concorrente nacional PME entrega comissão configurável que cruze OS multi-equipamento + líquido pós-despesas + múltiplos participantes + gatilho por recebimento.

```
JTBD-071 | Configurar regra de comissão e simular efeito antes de aplicar
- Quem: dono (Roldão) ou gerente (Sandra)
- Quando: muda política comercial (subir % do vendedor, criar bônus por meta, mudar regra de desconto)
- Quero: configurar a regra no setup + ver simulação "se rodasse esse mês com a regra nova, dava quanto?" antes de ativar
- Pra que possa: não quebrar fechamento do mês nem dar surpresa pra equipe
- Categoria: funcional + emocional (segurança de mudança)
- Métrica de sucesso: 100% das mudanças de regra simuladas antes de ativar; zero fechamento "explodido" por regra mal-configurada
- Solução hoje: planilha do gerente; mudanças aplicadas direto sem simulação; surpresa só aparece no fechamento
- Concorrente que mais resolve hoje: TOTVS Protheus (caro, enterprise R$ 50k+); nenhum PME
- Prioridade MVP-1: alta (BIG-09)
- [a confirmar via entrevista] que % e quais variáveis de regra a empresa do Roldão usa hoje
```

```
JTBD-072 | Ver demonstrativo claro por colaborador antes de aprovar pagamento
- Quem: dono (Roldão) ou gerente (Sandra)
- Quando: vou aprovar fechamento mensal de comissão
- Quero: demonstrativo por colaborador (OS atendidas, base de cálculo, % aplicado, ajustes manuais com justificativa, líquido a pagar) com 1 clique
- Pra que possa: aprovar com confiança e mandar pra contas a pagar sem ter que checar OS a OS
- Categoria: funcional + emocional (confiança no número)
- Métrica de sucesso: tempo de aprovação de fechamento < 30 min pra equipe inteira; zero pagamento revisado depois por divergência
- Solução hoje: planilha do gerente; reunião 1:1 com cada colaborador pra explicar conta
- Concorrente que mais resolve hoje: TOTVS (enterprise); Omie (só vendedor básico, sem OS)
- Prioridade MVP-1: alta (BIG-09)
```

```
JTBD-073 | Ver previsão da minha comissão no app sem esperar fim do mês
- Quem: técnico de campo (Bruno) — também ressoa em vendedor (Rogério) e motorista UMC (Carlos)
- Quando: termino uma OS no campo; abro o app no fim do dia/semana
- Quero: ver previsão acumulada do mês ("você já fez X OS, comissão prevista R$ Y, status: aguardando recebimento / liberada / aprovada")
- Pra que possa: não ficar no escuro até o fechamento; planejar minha vida financeira; sentir motivação no esforço diário
- Categoria: emocional (motivação + previsibilidade) + funcional
- Métrica de sucesso: > 80% dos técnicos consultam previsão pelo menos 1x por semana; zero técnico surpreendido negativamente no fechamento
- Solução hoje: pergunta pro gerente; chuta de cabeça; só descobre o valor real no holerite
- Concorrente que mais resolve hoje: Auvo (comissão básica por OS); nenhum integrado com regras complexas
- Prioridade MVP-1: alta (BIG-09; driver de retenção/motivação da equipe)
```

```
JTBD-074 | Fechar comissão de todos os colaboradores em minutos, não dias
- Quem: financeiro (Cláudia) — também ressoa em gerente (Sandra)
- Quando: fechamento de mês (ou semana / quinzena conforme regra do colaborador)
- Quero: rotina dedicada que busca OS concluídas + valores recebidos no período, aplica as regras configuradas, gera demonstrativo individual, e me leva pra aprovação com auditoria de cada ajuste
- Pra que possa: não passar 3-5 dias do mês mexendo em planilha gigante
- Categoria: funcional + emocional (esgotamento mensal)
- Métrica de sucesso: tempo de fechamento da equipe inteira < 1 dia útil (hoje: 3-5 dias); 100% dos ajustes manuais com justificativa registrada
- Solução hoje: planilha mestre do financeiro com fórmulas frágeis; cada colaborador questiona o número; refaz 2-3x
- Concorrente que mais resolve hoje: TOTVS (enterprise); Omie (parcial e só pra vendedor)
- Prioridade MVP-1: alta (BIG-09)
```

```
JTBD-075 | Ver previsão de comissão por estágio do pipeline pra priorizar leads
- Quem: vendedor (Rogério)
- Quando: começo da semana, abrindo pipeline
- Quero: cada oportunidade do pipeline mostrar comissão prevista (com base na regra atual + estágio + chance de fechamento)
- Pra que possa: priorizar leads com retorno maior — não trabalhar igual em lead que paga R$ 200 e lead que paga R$ 2.000
- Categoria: funcional + emocional (esforço bem alocado)
- Métrica de sucesso: vendedor consegue ordenar pipeline por retorno esperado; ticket médio sobe (vendedor foca em lead grande)
- Solução hoje: vendedor calcula de cabeça; muitas vezes prioriza o "lead barulhento" em vez do "lead grande"
- Concorrente que mais resolve hoje: Pipedrive/RD Station (genérico, sem regra de comissão real); nenhum integrado
- Prioridade MVP-1: média (MVP-2; mas registrar como driver Rogério)
- [a confirmar via entrevista] se vendedores do nosso ICP realmente usariam essa visão
```

```
JTBD-076 | Bloquear comissão automaticamente quando OS dá prejuízo
- Quem: dono (Roldão) — também ressoa em gerente (Sandra)
- Quando: OS fechada onde despesas (combustível, pedágio, hospedagem, peças, terceiros, motorista, UMC) ultrapassaram a receita
- Quero: sistema bloquear comissão automaticamente nessas OS (status "bloqueada — OS deu prejuízo") sem eu ter que olhar 1 a 1
- Pra que possa: não pagar comissão de R$ 500 sobre uma OS que deu R$ 1.200 de prejuízo
- Categoria: funcional + emocional (não-pagar-pra-trabalhar)
- Métrica de sucesso: zero comissão paga indevidamente em OS deficitária; alerta visível pro Roldão quando isso acontece (input pra repensar precificação)
- Solução hoje: confiança no técnico/vendedor; descoberta tardia ao fechar DRE do mês (e aí a comissão já foi paga)
- Concorrente que mais resolve hoje: nenhum PME; TOTVS enterprise tem
- Prioridade MVP-1: alta (BIG-09; depende de integração com Caixa do Técnico/Frota — BIG-08)
- [a confirmar via entrevista] qual % de OS hoje dá prejuízo invisível
```

```
JTBD-077 | Aprovar ou bloquear comissão com 1 clique, com motivo automático em divergência
- Quem: gerente (Sandra) ou financeiro (Cláudia)
- Quando: recebo lote de comissões pra aprovar antes do pagamento
- Quero: cada item com botão "aprovar / bloquear"; se houver divergência (margem mínima não atingida, desconto acima do permitido, OS sem recebimento), sistema sugere motivo do bloqueio automaticamente
- Pra que possa: liberar fechamento rápido sem ter que escrever justificativa pra cada bloqueio
- Categoria: funcional
- Métrica de sucesso: > 90% dos itens aprovados/bloqueados em < 10s cada; 100% dos bloqueios com motivo registrado em auditoria
- Solução hoje: planilha + reunião com gerente; motivo de bloqueio escrito à mão em e-mail
- Concorrente que mais resolve hoje: nenhum no setor
- Prioridade MVP-1: alta (BIG-09)
```

```
JTBD-078 | Reconstruir cálculo histórico de comissão pra responder questionamento
- Quem: auditor interno / dono (Roldão) — também atende a Marcos quando questionado
- Quando: técnico questiona valor recebido 3 meses atrás; auditor pede prova; processo trabalhista
- Quero: rastrear cada R$ da comissão paga até a origem (qual OS, qual regra vigente naquela data, qual base de cálculo, qual ajuste manual, quem aprovou, quando, com qual justificativa)
- Pra que possa: responder qualquer questionamento com dado, não com "deve ter sido assim"
- Categoria: funcional + emocional (proteção legal)
- Métrica de sucesso: reconstrução completa de qualquer comissão paga em < 5 min; hash de auditoria em cada cálculo
- Solução hoje: planilha sumiu / fórmula mudou / regra de hoje ≠ regra de 3 meses atrás; impossível reconstruir com certeza
- Concorrente que mais resolve hoje: TOTVS (enterprise, com auditoria forte); nenhum PME
- Prioridade MVP-1: alta (BIG-09; mitiga R-novo C1 de configuração errada e R-novo C2 de fraude interna)
```

```
JTBD-079 | Saber se vou ter comissão/bônus pela viagem com UMC sem perguntar pro escritório
- Quem: motorista UMC (Carlos)
- Quando: termino viagem com UMC (calibração de balança rodoviária em outra cidade/estado)
- Quero: app simples mostrar "viagem X: km Y, dias fora Z, peso transportado W ton → comissão/bônus previsto: R$ N"
- Pra que possa: não ficar inseguro sobre receber; não depender de ligar pro escritório toda vez
- Categoria: emocional (segurança/motivação) + funcional
- Métrica de sucesso: 100% dos motoristas UMC sabem o valor previsto antes de chegar em casa; zero "achei que ia receber mais"
- Solução hoje: pergunta no WhatsApp; aceita o que vier no holerite
- Concorrente que mais resolve hoje: nenhum (nicho ultra-específico — motorista UMC)
- Prioridade MVP-1: alta (BIG-09 + BIG-08; persona Carlos com baixo letramento digital — UI simples)
- [a confirmar via entrevista] qual regra de comissão a empresa do Roldão usa hoje pro motorista UMC
```

```
JTBD-080 | Ver rentabilidade real por OS (faturamento − despesas − comissões = lucro líquido)
- Quem: dono (Roldão)
- Quando: análise mensal/trimestral; decisão de aceitar mais OS daquele tipo
- Quero: demonstrativo por OS mostrando faturamento − despesas (Frota/UMC/Caixa) − comissões (todos participantes) = lucro líquido; agrupado por tipo de serviço, tipo de equipamento, cliente, região
- Pra que possa: decidir com dado se "OS de balança rodoviária no interior dá lucro" ou se "calibração de manômetro no laboratório dá mais margem"; precificar contratos novos com base real
- Categoria: funcional
- Métrica de sucesso: Roldão consegue identificar top 5 tipos de OS mais rentáveis e bottom 5 prejuízos invisíveis em < 5 min/mês
- Solução hoje: contador faz semestral; muito tipo de OS dá prejuízo invisível
- Concorrente que mais resolve hoje: Omie/Sankhya (parcial, sem cruzar comissão + despesa de campo); nenhum integrado
- Prioridade MVP-1: alta (BIG-09 + BIG-08; depende dos dois Big Jobs estarem integrados)
```

```
JTBD-081 | Ver impacto no meu bolso quando dou desconto pro cliente
- Quem: vendedor (Rogério) — também ressoa em técnico de campo quando negocia escopo (Bruno)
- Quando: cliente pede desconto na negociação
- Quero: simulador no momento — "desconto de 10% → sua comissão cai de R$ 800 pra R$ 600" (se a regra penaliza desconto acima de N%)
- Pra que possa: negociar com consciência; não dar desconto sem saber que tô tirando do meu próprio bolso
- Categoria: funcional + emocional (não-ser-prejudicado)
- Métrica de sucesso: desconto médio cai (vendedor pensa 2x antes de dar); margem da empresa sobe
- Solução hoje: vendedor não sabe; dá desconto pra fechar; descobre na hora do fechamento
- Concorrente que mais resolve hoje: nenhum no setor
- Prioridade MVP-1: média (MVP-2; mas registrar como driver de comportamento da equipe comercial)
- [a confirmar via entrevista] se a regra de "comissão reduzida por desconto acima de X%" é usada hoje
```

```
JTBD-082 | Liberar comissão proporcionalmente quando cliente paga parcela
- Quem: financeiro (Cláudia)
- Quando: cliente paga 1ª de 3 parcelas de uma OS de R$ 12.000 parcelada
- Quero: sistema liberar automaticamente comissão proporcional ao valor recebido (R$ 4.000 → liberou comissão sobre R$ 4.000)
- Pra que possa: não calcular na mão a cada parcela; não pagar comissão sobre o valor total que ainda não entrou
- Categoria: funcional
- Métrica de sucesso: 100% das comissões com gatilho "por recebimento" liberadas automaticamente conforme parcela compensa; zero comissão paga sobre fatura inadimplente
- Solução hoje: planilha mestre; cálculo manual a cada parcela; muito atraso e erro
- Concorrente que mais resolve hoje: nenhum no setor; TOTVS enterprise tem
- Prioridade MVP-1: alta (BIG-09; mitiga R-novo C3 de pagar comissão sobre inadimplência)
```

---

### 3.13 JTBDs de Cliente 360°, CRM Contínuo e Automações (decisão fundadora Roldão 17/05/2026)

> 15 jobs novos derivados das decisões fundadoras "Cliente nunca morre no CRM" + "Engine de Automações configurável sem código". Detalhes do domínio em `dominio-de-negocio.md` §"Cliente 360°, CRM Contínuo e Automações" — fonte canônica. Esses jobs alimentam BIG-10 (Cliente 360°/CRM contínuo) e BIG-11 (Automações configuráveis).

```
JTBD-083 | Ver lista priorizada de clientes pra ligar hoje
- Quem: vendedor (persona: Rogério)
- Quando: começo do expediente / segunda de manhã
- Quero: lista do dia ordenada por sinal (calibração vencendo, OS recém-fechada, NPS negativo, sem contato há 90d, parcela vencida)
- Pra que possa: não decidir "do que faço primeiro" no improviso e nunca esquecer cliente quente
- Categoria: funcional + emocional (não-pulverizar-foco)
- Métrica de sucesso: > 80% das ligações do dia saem da lista; tempo de decisão "quem ligar" < 1 min
- Solução hoje: cabeça + planilha + bilhete na mesa; muito cliente esquece
- Concorrente que mais resolve hoje: HubSpot/RD Station (CRM puro, sem dado de calibração); nenhum integra ciclo de calibração
- Prioridade MVP-1: alta (BIG-10; eixo Cliente 360°)
```

```
JTBD-084 | Disparar tarefa de renovação + lembrete WhatsApp ao emitir certificado
- Quem: dono (Roldão) configura; vendedor (Rogério) recebe; cliente final recebe lembrete
- Quando: certificado emitido com periodicidade definida
- Quero: sistema automaticamente cria tarefa de renovação 30d antes da próxima calibração + agenda mensagem WhatsApp ao cliente 7d antes
- Pra que possa: nunca perder janela de renovação (D-002: R$ 3-8k/mês de receita perdida por esquecimento)
- Categoria: funcional + emocional (não-deixar-cair-receita)
- Métrica de sucesso: > 90% das renovações disparadas automaticamente; taxa de renovação sobe pra > 85%
- Solução hoje: planilha de vencimento + alarme no celular do dono
- Concorrente que mais resolve hoje: nenhum integra calibração + automação; Cali/Metroex apenas alertam
- Prioridade MVP-1: alta (BIG-10 + BIG-11; mitiga R-novo CRM-1 com sandbox)
```

```
JTBD-085 | Gerar tarefa imediata de retenção quando NPS negativo cai
- Quem: gerente/RT (Sandra) define regra; vendedor (Rogério) responsável é acionado
- Quando: cliente responde NPS com nota detratora (0-6)
- Quero: tarefa automática criada pro vendedor responsável em < 5 min + alerta pro gerente
- Pra que possa: salvar relacionamento antes do cliente postar reclamação ou cancelar
- Categoria: funcional + emocional (proteção de receita recorrente)
- Métrica de sucesso: 100% dos NPS detratores com tarefa de retenção em < 1h; taxa de retenção pós-NPS-ruim > 60%
- Solução hoje: NPS vira planilha; ninguém olha; cliente vai embora silenciosamente
- Concorrente que mais resolve hoje: Track.co (NPS puro, sem ligar com vendedor); RD Station (parcial)
- Prioridade MVP-1: alta (BIG-11)
```

```
JTBD-086 | Abrir cadastro + chamado + oportunidade em 1 clique a partir de WhatsApp novo
- Quem: atendente (persona: Letícia)
- Quando: cliente novo manda mensagem WhatsApp pedindo orçamento ou abrindo chamado
- Quero: botão único que cria cliente + chamado + nota de oportunidade no CRM puxando os dados já capturados na conversa
- Pra que possa: não digitar mesma info em 3 telas e não perder lead enquanto cadastra
- Categoria: funcional + emocional (não-ser-só-digitador)
- Métrica de sucesso: tempo "primeira mensagem → tudo cadastrado" < 90s; zero lead novo "esquecido na conversa"
- Solução hoje: anota CNPJ no caderno, cadastra depois em 3 sistemas (perde uns 20% dos leads)
- Concorrente que mais resolve hoje: Z-API, Take Blip (chatbot puro); nenhum integra cadastro+chamado+CRM
- Prioridade MVP-1: alta (BIG-10; zera dor D-001 também)
```

```
JTBD-087 | Testar regra de automação em sandbox antes de ativar em produção
- Quem: dono (Roldão) ou gerente (Sandra) configurando engine de automação
- Quando: nova regra gatilho→condição→ação criada (ex.: "se NPS<7 disparar mensagem")
- Quero: simulador que mostra "se essa regra rodasse hoje, ela teria disparado em X clientes — eis a lista" antes de eu ativar
- Pra que possa: evitar disparo em massa errado (R-novo CRM-1 — mensagem indevida pra cliente errado vira reclamação no Reclame Aqui)
- Categoria: funcional + emocional (controle antes de ativar algo irreversível)
- Métrica de sucesso: zero automação ativa que disparou pro público errado; 100% das automações novas passam por sandbox antes de "ligar"
- Solução hoje: não existe — Bling/Cali/Metroex não têm engine; HubSpot tem (referência)
- Concorrente que mais resolve hoje: HubSpot, ActiveCampaign (engine + sandbox); nenhum BR no setor
- Prioridade MVP-1: alta (BIG-11; mitigação obrigatória R-novo CRM-1)
```

```
JTBD-088 | Régua automática de cobrança com escalada pro vendedor
- Quem: financeiro (persona: Cláudia) configura; sistema executa
- Quando: parcela ou fatura vence
- Quero: régua configurável (lembrete D-3 amistoso → cobrança D+1 → 2ª cobrança D+7 → escalar pro vendedor D+15 → bloqueio D+30) com mensagens em WhatsApp/e-mail
- Pra que possa: parar de ser a "chata" pessoalmente e ainda assim reduzir inadimplência
- Categoria: funcional + emocional (não-ser-cobrador)
- Métrica de sucesso: inadimplência cai > 20%; horas/mês em cobrança caem 50%; zero esquecimento de cobrar
- Solução hoje: lembrete no celular + ligação pessoal; alguns vencimentos esquecidos
- Concorrente que mais resolve hoje: Asaas, Cobre Fácil (régua pura); ERPs (Omie/Conta Azul) têm parcial; nenhum integra com vendedor responsável
- Prioridade MVP-1: alta (BIG-11; extensão automatizada do JTBD-036)
```

```
JTBD-089 | Receber certificado por WhatsApp com link pra próxima calibração já agendável
- Quem: cliente final (persona João — end-customer do tenant)
- Quando: certificado emitido pelo laboratório
- Quero: receber WhatsApp/e-mail com PDF do certificado + link "agendar próxima calibração" que já abre formulário pré-preenchido
- Pra que possa: deixar o lab fazer pra mim — não precisar lembrar de ligar daqui a 12 meses
- Categoria: funcional + emocional (cliente final percebe lab como "que cuida")
- Métrica de sucesso: > 50% dos clientes agendam próxima calibração pelo link; satisfação > 4,5/5
- Solução hoje: cliente recebe PDF por e-mail; precisa lembrar de ligar; muitos esquecem (D-002)
- Concorrente que mais resolve hoje: nenhum BR; Beamex CMX tem portal mas não envia ativo
- Prioridade MVP-1: alta (BIG-10; mantém cliente "vivo" no CRM)
```

```
JTBD-090 | Receber alerta automático no dashboard quando cliente fica inativo
- Quem: dono (Roldão) e gerente (Sandra)
- Quando: cliente passa de 180d sem nova OS ou contato
- Quero: alerta no dashboard + sugestão de campanha de reativação (cupom, contato pessoal, oferta de pacote)
- Pra que possa: parar de descobrir "ah, ele foi pro concorrente há 1 ano" tarde demais
- Categoria: funcional + emocional (não-perder-cliente-em-silêncio)
- Métrica de sucesso: 100% dos clientes inativos > 180d com tarefa de reativação; taxa de reativação > 25%
- Solução hoje: cabeça do dono; só descobre quando vai puxar lista do ano e nota "ué, cadê esse?"
- Concorrente que mais resolve hoje: HubSpot/RD Station (genérico); nenhum BR no setor
- Prioridade MVP-1: alta (BIG-10 + BIG-11)
```

```
JTBD-091 | Ver Cliente 360° em UMA tela sem abrir 7 módulos
- Quem: gerente (Sandra), atendente (Letícia), vendedor (Rogério), dono (Roldão)
- Quando: cliente liga / vai a reunião / vai responder e-mail / fechar contrato
- Quero: tela única consolidada (cadastro + contatos + filiais + equipamentos + calibrações + certificados + OS + orçamentos + contratos + financeiro + mensagens + tarefas + oportunidades + NPS + próxima ação)
- Pra que possa: entender em < 30s tudo da relação cliente x empresa sem abrir Bling + Cali + WhatsApp + planilha + e-mail
- Categoria: funcional + emocional (parecer-organizado-pro-cliente)
- Métrica de sucesso: > 90% das interações cliente x atendente/vendedor consultam só essa tela; tempo médio de consulta < 30s
- Solução hoje: 5-7 telas abertas em paralelo; muita info ainda fica em conversa WhatsApp
- Concorrente que mais resolve hoje: Bling (parcial — só fiscal); HubSpot (parcial — sem calibração); ninguém junta tudo
- Prioridade MVP-1: alta (BIG-10 — coração do Cliente 360°)
```

```
JTBD-092 | Gerar proposta de renovação automática 60d antes do contrato anual vencer
- Quem: vendedor (persona: Rogério)
- Quando: contrato anual de manutenção/calibração chega a 60d do vencimento
- Quero: sistema gera proposta de renovação automaticamente (puxando histórico, índice de reajuste, escopo atual) + cria tarefa pro vendedor revisar e enviar
- Pra que possa: não perder renovação por esquecimento e não montar proposta do zero a cada vez
- Categoria: funcional + emocional (segurança da receita anual)
- Métrica de sucesso: > 90% das renovações com proposta gerada em < 5 min de revisão; taxa de renovação anual > 85%
- Solução hoje: planilha de contratos com cor de "atenção"; muita renovação esquecida; ou proposta sai 2 semanas atrasada
- Concorrente que mais resolve hoje: nenhum BR; Salesforce CPQ (caro e horizontal)
- Prioridade MVP-1: alta (BIG-10 + BIG-11; complementa JTBD-044)
```

```
JTBD-093 | Workflow automático pra reclamação formal (ISO 17025 cl. 7.9) com escala se atrasar
- Quem: RT Qualidade (persona: Sandra)
- Quando: cliente registra reclamação formal (e-mail, portal, telefone, NPS detrator com texto)
- Quero: workflow automático que atribui RT como responsável + define prazo de resposta (ex.: 5 dias úteis) + escala pro gerente se prazo for ultrapassado + registra todas as ações pra evidência
- Pra que possa: cumprir ISO 17025 cl. 7.9 + INV (ainda a definir) com rastreabilidade e não tomar NC por reclamação "perdida no e-mail"
- Categoria: funcional + emocional (compliance automático)
- Métrica de sucesso: 100% das reclamações com workflow completo arquivado; tempo médio de resposta dentro do prazo definido pela empresa; zero NC por reclamação esquecida
- Solução hoje: e-mail + WhatsApp + planilha "controle de reclamações"; muita perda
- Concorrente que mais resolve hoje: Qualiex, MasterControl (parcial); nenhum integra com automação
- Prioridade MVP-1: alta (BIG-02 + BIG-11; complementa JTBD-057)
```

```
JTBD-094 | Flag automática de "cliente fixo" + condição comercial diferenciada após N contratos
- Quem: dono (Roldão) define regra; vendedor (Rogério) e financeiro (Cláudia) executam
- Quando: cliente fecha 3º contrato/OS-recorrente
- Quero: sistema marca cliente como "fixo" automaticamente + ativa condição comercial específica (desconto pré-aprovado, prazo de pagamento estendido, prioridade de agenda)
- Pra que possa: fidelizar clientes recorrentes sem depender da memória de quem atende (e não ofertar condição premium pra cliente novo eventual)
- Categoria: funcional + social (cliente percebe ser "tratado diferente")
- Métrica de sucesso: 100% dos clientes elegíveis com flag ativa; condição comercial aplicada automaticamente em propostas/orçamentos
- Solução hoje: depende do vendedor lembrar; nem todo cliente fixo recebe condição
- Concorrente que mais resolve hoje: Salesforce (regra de pricing); nenhum BR no setor
- Prioridade MVP-1: média (BIG-10 + BIG-11; entra completo em MVP-2; flag manual no MVP-1)
```

```
JTBD-095 | Bloquear emissão de novo orçamento quando cliente está inadimplente
- Quem: financeiro (persona: Cláudia) e vendedor (Rogério)
- Quando: vendedor tenta abrir novo orçamento pra cliente com fatura vencida > X dias
- Quero: sistema bloqueia emissão + exibe motivo + envia alerta pro vendedor responsável + libera após pagamento ou aprovação manual do gerente
- Pra que possa: parar de empilhar dívida + forçar a conversa de cobrança antes da venda nova
- Categoria: funcional + emocional (não-acumular-prejuízo)
- Métrica de sucesso: zero orçamento aberto pra inadimplente sem aprovação; redução de exposição em > 30%
- Solução hoje: vendedor não sabe; cobrança descobre depois; cliente acumula débito
- Concorrente que mais resolve hoje: Bling/Omie (parcial — alerta visual mas não bloqueia); nenhum no setor
- Prioridade MVP-1: alta (BIG-11)
```

```
JTBD-096 | Gerar oportunidade automática quando equipamento está sem manutenção há > 12 meses
- Quem: gerente (Sandra) e vendedor (Rogério)
- Quando: equipamento cadastrado do cliente passa de 12 meses sem manutenção registrada
- Quero: sistema cria oportunidade no funil de pós-venda + atribui ao vendedor + sugere pacote de manutenção
- Pra que possa: monetizar pós-venda passiva (calibração ≠ manutenção) e não deixar dinheiro na mesa
- Categoria: funcional + emocional (não-dormir-no-volante)
- Métrica de sucesso: > 20% das oportunidades automáticas viram OS; receita de manutenção sobe > 15% em 6 meses
- Solução hoje: ninguém olha; manutenção só acontece quando equipamento quebra
- Concorrente que mais resolve hoje: nenhum BR; ServiceMax (parcial, internacional)
- Prioridade MVP-1: média (BIG-10 + BIG-11)
```

```
JTBD-097 | Ver "1 número que importa hoje" + lista de ações pendentes (não 50 KPIs)
- Quem: dono (persona: Roldão)
- Quando: abre o sistema de manhã
- Quero: 1 número-foco do dia (escolhido por mim ou sugerido pelo sistema) + lista curta de ações pendentes/decisões a tomar (ex.: aprovar adiantamento, NPS detrator, contrato vencendo)
- Pra que possa: não me afogar em 50 KPIs e tomar 3-5 decisões certeiras por dia
- Categoria: emocional (paz mental) + funcional (priorização)
- Métrica de sucesso: dono toma decisão sobre "o que olhar hoje" em < 30s; > 80% das ações pendentes da lista são resolvidas no mesmo dia
- Solução hoje: dashboard com 30 gráficos que ninguém olha; ou pergunta pra financeiro
- Concorrente que mais resolve hoje: Conta Azul (parcial — "saldo do dia"); nenhum dedicado
- Prioridade MVP-1: alta (BIG-10; complementa JTBD-001)
```

---

### 3.14 JTBDs de Estoque Multi-local com Lacre/Selo INMETRO (decisão fundadora Roldão 17/05/2026)

> 12 jobs novos derivados da decisão fundadora "Estoque multi-local + rastreabilidade individual de lacre/selo INMETRO + transferência 2 etapas com aceite + foto obrigatória = módulo central". Detalhes do domínio em `dominio-de-negocio.md` §"Módulo de Estoque Completo para Assistência Técnica" — fonte canônica. Alimentam BIG-12 (9º gap defensável do projeto).

```
JTBD-098 | Solicitar peça pelo app e receber via transferência 2 etapas com aceite
- Quem: técnico (persona: Bruno)
- Quando: em campo, precisa de peça que não está no estoque dele
- Quero: solicitar pelo app (pra central / motorista UMC / colega) + receber notificação quando peça é despachada + aceitar fisicamente quando recebo
- Pra que possa: não depender de WhatsApp + não ser cobrado por peça que nunca chegou
- Categoria: funcional + emocional (não-mendigar + não-ser-injustiçado)
- Métrica de sucesso: > 95% das solicitações de peça com aceite registrado; zero divergência "saiu da central mas não chegou"
- Solução hoje: WhatsApp + foto + confiança; muita peça "perdida no meio"
- Concorrente que mais resolve hoje: nenhum no setor com 2-etapas; ERPs (Bling/Omie) não suportam multi-local + aceite
- Prioridade MVP-1: alta (BIG-12)
```

```
JTBD-099 | Baixar peça do meu estoque automaticamente ao lançar na OS
- Quem: técnico (persona: Bruno)
- Quando: usa peça em OS em execução
- Quero: ao lançar peça na OS pelo app, sistema baixa do meu estoque automaticamente + vincula à OS + cliente + equipamento
- Pra que possa: não digitar 2x (no app de OS + na planilha de estoque) e não esquecer baixa
- Categoria: funcional
- Métrica de sucesso: 100% das peças usadas em OS baixadas automaticamente; zero divergência inventário x OS
- Solução hoje: técnico anota; alguém digita depois em planilha; muita divergência
- Concorrente que mais resolve hoje: Auvo (parcial — peça em OS sem multi-local); nenhum BR completo
- Prioridade MVP-1: alta (BIG-12)
```

```
JTBD-100 | Registrar destino da peça retirada do cliente (com foto e observação)
- Quem: técnico (persona: Bruno)
- Quando: retira peça defeituosa do equipamento do cliente
- Quero: registrar no app o destino (empresa / cliente / descarte / garantia / análise técnica) + foto obrigatória + observação
- Pra que possa: comprovar destino (legal e operacionalmente) + não acumular peça "limbo" no carro
- Categoria: funcional + emocional (não-ser-acusado)
- Métrica de sucesso: 100% das peças retiradas com destino + foto registrados; zero "peça sumida"
- Solução hoje: foto solta no WhatsApp; muita peça vai pro carro e nunca sai
- Concorrente que mais resolve hoje: nenhum no setor
- Prioridade MVP-1: alta (BIG-12)
```

```
JTBD-101 | Aplicar lacre na balança com número + foto obrigatória vinculados ao equipamento
- Quem: técnico (persona: Bruno)
- Quando: finaliza serviço que exige aplicação de lacre (próprio da empresa)
- Quero: registrar no app número do lacre + tipo + localização + foto obrigatória + vincular OS/cliente/equipamento; lacre sai automaticamente do meu estoque
- Pra que possa: ter rastreabilidade individual de cada lacre (quem aplicou, onde, quando, com foto) — exigência fiscal/metrológica + defesa contra fraude
- Categoria: funcional + emocional (compliance + proteção)
- Métrica de sucesso: 100% dos lacres aplicados com foto + vinculação completa; zero lacre "perdido" do estoque do técnico
- Solução hoje: anota número em papel; sem foto; controle de estoque de lacre só na cabeça
- Concorrente que mais resolve hoje: nenhum BR (Bling/Omie não têm conceito de lacre; Cali/Metroex não têm estoque)
- Prioridade MVP-1: alta (BIG-12)
```

```
JTBD-102 | Registrar lacre retirado (próprio OU de concorrente) com foto + origem + motivo
- Quem: técnico (persona: Bruno)
- Quando: retira lacre antigo do equipamento antes de fazer manutenção
- Quero: registrar no app número (se identificado) + tipo + origem (empresa/concorrente) + motivo + foto antes/depois + observação
- Pra que possa: ter evidência da condição encontrada (defesa em caso de questionamento de cliente ou fiscalização) + dar inteligência comercial (qual concorrente atende cliente x)
- Categoria: funcional + emocional + social (inteligência comercial passiva)
- Métrica de sucesso: 100% dos lacres retirados com foto + origem registrados; relatório "lacres de concorrentes encontrados por mês" vira ferramenta comercial
- Solução hoje: não registra; ou foto solta sem catalogar
- Concorrente que mais resolve hoje: nenhum
- Prioridade MVP-1: alta (BIG-12; gera dado comercial bônus)
```

```
JTBD-103 | Aplicar selo INMETRO de reparo com registro rigoroso (número, série, lote, foto, rastreabilidade fiscal)
- Quem: técnico (persona: Bruno) com autorização legal pra aplicar selo INMETRO
- Quando: finaliza reparo de balança/instrumento metrológico legal que exige selo INMETRO
- Quero: registrar no app número + série + lote + foto obrigatória + OS + cliente + equipamento + técnico + data/hora; selo sai do estoque com rastreabilidade individual
- Pra que possa: cumprir exigência metrológica legal (fiscalização IPEM pode pedir "cadê esse selo?") + defender em caso de auditoria
- Categoria: funcional + emocional (sobrevivência regulatória)
- Métrica de sucesso: 100% dos selos com rastreabilidade individual completa; zero selo "perdido" ou aplicado sem registro; auditoria IPEM respondida em < 30s por selo
- Solução hoje: registra em planilha lateral; muita confusão; risco real de multa por selo sem rastreio
- Concorrente que mais resolve hoje: nenhum BR (Cali/Metroex não têm; Bling/Omie não entendem o conceito)
- Prioridade MVP-1: alta (BIG-12; mitigação obrigatória R-novo EST-1 — selo perdido = multa IPEM)
```

```
JTBD-104 | Transferir peça do motorista pro técnico em campo com 2 etapas (envio + aceite)
- Quem: motorista UMC (persona: Carlos) e técnico (Bruno)
- Quando: motorista entrega peça pro técnico em campo
- Quero: motorista lança envio no app; técnico recebe notificação; técnico confere fisicamente; aceita ou recusa com motivo
- Pra que possa: não ser cobrado pelo que entreguei ao colega + comprovar entrega (foto opcional)
- Categoria: funcional + emocional (não-ser-acusado)
- Métrica de sucesso: 100% das transferências com aceite; zero divergência motorista x técnico
- Solução hoje: foto no WhatsApp + confiança; brigas mensais no fechamento de inventário
- Concorrente que mais resolve hoje: nenhum no setor BR
- Prioridade MVP-1: alta (BIG-12; complementa JTBD-068 e JTBD-098)
```

```
JTBD-105 | Conferir + dar entrada com foto na devolução de peça não-usada pelo técnico
- Quem: almoxarife / responsável estoque central (papel novo, geralmente Sandra ou auxiliar)
- Quando: técnico devolve peça não-utilizada após visita
- Quero: conferir fisicamente + foto + dar entrada com status (íntegra/danificada/aberta) + assinar no app
- Pra que possa: não aceitar peça aberta como "íntegra" + ter rastro de quem devolveu em que estado
- Categoria: funcional + social (proteção da almoxarifa contra cobrança injusta)
- Métrica de sucesso: 100% das devoluções com foto + status; redução de divergência > 50%
- Solução hoje: técnico larga peça na mesa; ninguém confere; some no inventário
- Concorrente que mais resolve hoje: nenhum no setor
- Prioridade MVP-1: alta (BIG-12)
```

```
JTBD-106 | Receber alerta automático + justificativa obrigatória + aprovação em divergência de inventário
- Quem: gerente (Sandra) e dono (Roldão)
- Quando: inventário do técnico/motorista fecha com divergência (peça faltando, sobrando, número de série errado)
- Quero: alerta automático no dashboard + bloqueio até justificativa preenchida pelo responsável + aprovação manual do gerente + relatório por responsável (sinal de fraude se recorrente)
- Pra que possa: detectar fraude/displicência cedo (R-novo EST-4 — divergência sistemática em técnico X) + não confiar no "tava aqui ontem"
- Categoria: funcional + emocional (proteção patrimônio + detecção fraude)
- Métrica de sucesso: 100% das divergências com justificativa + aprovação; redução de divergência em > 40% após 3 meses
- Solução hoje: inventário em planilha; muito "tava aqui ontem"; pouco controle
- Concorrente que mais resolve hoje: ERPs (Bling/Omie) parcial; nenhum BR com multi-local + relatório por responsável
- Prioridade MVP-1: alta (BIG-12; mitigação R-novo EST-4)
```

```
JTBD-107 | Alerta automático + sugestão de pedido de compra quando peça crítica está abaixo do mínimo
- Quem: dono (Roldão), gerente (Sandra), almoxarife
- Quando: saldo de peça crítica (definida no cadastro) cai abaixo do estoque mínimo configurado
- Quero: alerta no dashboard + sugestão pronta de pedido de compra (puxando fornecedor preferencial, último preço, prazo de entrega)
- Pra que possa: não parar OS por falta de peça + comprar com calma (não em emergência caríssima)
- Categoria: funcional + emocional (não-trabalhar-em-emergência)
- Métrica de sucesso: zero OS parada por falta de peça crítica; > 80% das compras de reposição feitas com antecedência > 5d do esgotamento
- Solução hoje: descobre quando técnico pede peça e não tem; corre pra comprar caro
- Concorrente que mais resolve hoje: ERPs (Bling/Omie/Conta Azul) — parcial, sem entender peça crítica de calibração
- Prioridade MVP-1: alta (BIG-12)
```

```
JTBD-108 | Responder fiscalização IPEM "cadê o selo X aplicado em maio" em 30 segundos
- Quem: RT Qualidade (persona: Sandra) e dono (Roldão)
- Quando: auditor IPEM aparece com número de selo específico questionando aplicação
- Quero: buscar pelo número do selo + ver imediatamente OS + equipamento + cliente + foto + técnico responsável + data/hora
- Pra que possa: responder em < 30s sem virar pasta de papel ou planilha (sob pressão de fiscal na sala)
- Categoria: funcional + emocional (sobrevivência regulatória sob pressão)
- Métrica de sucesso: < 30s do "auditor pergunta" até "tela respondida"; zero "deixa eu te ligar de volta"
- Solução hoje: vasculha planilha + pasta de papel; sob pressão; risco real de multa
- Concorrente que mais resolve hoje: nenhum
- Prioridade MVP-1: alta (BIG-12 + BIG-02; complementa JTBD-058)
```

```
JTBD-109 | Registrar peças/lacres/selos offline (campo sem internet) e sincronizar ao voltar
- Quem: técnico (persona: Bruno) em zona rural / chão de fábrica / subsolo
- Quando: cliente em local sem cobertura
- Quero: app offline registra peça/lacre/selo aplicado + foto + assinatura; sincroniza tudo quando volta pra área com sinal sem perda de dado
- Pra que possa: não voltar de viagem com "anotações soltas" pra digitar depois (perde dado e foto se troca o celular)
- Categoria: funcional + emocional (qualidade de vida + segurança do dado)
- Métrica de sucesso: 100% dos registros offline sincronizados sem perda; zero técnico passa sábado "passando a limpo"
- Solução hoje: papel + WhatsApp + planilha depois; muito dado perdido
- Concorrente que mais resolve hoje: Beamex bMobile, Metroex Coletor (offline real, com hardware proprietário)
- Prioridade MVP-1: média (registro online no MVP-1; offline-first robusto = MVP-2, junto com JTBD-022/BIG-05)
```

---

## 4. Big Jobs — os 12 jobs centrais que VENDEM o produto

> Transversais aos papéis. São o "porquê" alguém compra o produto. Se o Aferê resolver bem só esses 12, ganha o mercado. Se entregar perfeito todo o resto e falhar nesses, perde.
>
> **Auditoria 17/05/2026:** 5 dos 7 Big Jobs originais (BIG-01, 03, 05, 06, 07) estavam contaminados por solução — "ciclo completo em UM sistema" é descrição de produto, não de trabalho do cliente. Reescritos no formato Christensen puro abaixo. BIG-02 e BIG-04 sobreviveram ao teste.
>
> **2ª rodada 17/05/2026 (decisão fundadora Roldão):** BIG-08 antigo (cadeia de rastreabilidade) foi rebaixado a JTBD-028 alta-prioridade (continua no Top 10 #8 mas perdeu status de Big Job autônomo — é habilitador técnico do BIG-02, não venda por si só). **Slot liberado vira BIG-08 NOVO** = Frota + UMC + Caixa do técnico + custo real por atendimento. **BIG-01 também foi elevado** a eixo primário + moat estrutural junto com BIG-03 (eram eixo só BIG-03 antes).
>
> **3ª rodada 17/05/2026 (decisão fundadora Roldão):** **BIG-09 NOVO** = Comissões configuráveis sem mexer no código (módulo central, não opcional). 7º gap defensável (somar aos 6 já identificados); acoplado a BIG-08 (cálculo sobre líquido depende de Caixa do Técnico/Frota).
>
> **4ª rodada 17/05/2026 (decisões fundadoras Roldão):** **BIG-10 NOVO** = Cliente 360° + CRM Contínuo (cliente nunca "morre" no CRM; eixo primário de venda junto com BIG-01/03). **BIG-11 NOVO** = Engine de Automações configurável sem código (gatilho→condição→ação, com sandbox). **BIG-12 NOVO** = Estoque multi-local com lacre/selo INMETRO rastreáveis individualmente + transferência 2 etapas com aceite + foto obrigatória. **3 novos gaps defensáveis** (8º, 9º, 10º — somar aos 7 já mapeados). Detalhes em `dominio-de-negocio.md` §"Cliente 360°, CRM Contínuo e Automações" + §"Módulo de Estoque Completo para Assistência Técnica" — fontes canônicas.

---

### BIG-01 — Não perder informação entre etapas do atendimento

> **Quando** atendo cliente do primeiro contato até cobrança, **quero** não perder informação entre etapas, **pra que possa** não pedir desculpa por incompetência.

- **Categoria:** funcional + social (parecer organizado pro cliente)
- **Quem mais sente:** dono (Roldão), atendente (Letícia), gerente (Sandra)
- **Concorrente que mais resolve hoje:** nenhum no BR — cada empresa improvisa com 3-5 ferramentas costuradas com copy-paste
- **Métrica de sucesso:** zero "deixa eu te ligar de volta porque preciso consultar"; zero re-digitação do mesmo dado em 2+ telas
- **EIXO PRIMÁRIO DE VENDA + MOAT ESTRUTURAL** (junto com BIG-03)
- **Nota sobre moat:** BIG-01 + BIG-03 são os dois eixos estruturais que diferenciam Aferê dos concorrentes nacionais. BIG-01 = costura horizontal (todos os ciclos sob 1 fluxo); BIG-03 = costura vertical (todos os perfis de maturidade sob 1 produto). Concorrentes resolvem 1 dos dois — nenhum cobre os dois.

---

### BIG-02 — Não perder acreditação RBC nem tomar NC por erro evitável

> **Quando** chega carta do INMETRO ou cliente farma cobrando, **quero** ter certeza que o sistema bloqueia o erro antes dele virar NC, **pra que possa** não acordar 3h da manhã pensando "será que emiti certificado com padrão vencido?".

- **Categoria:** emocional (segurança) + funcional (compliance automático)
- **Quem mais sente:** dono (Roldão), RT Qualidade (Sandra), signatário (Marcos)
- **Concorrente que mais resolve hoje:** Cali, Metroex (parcial — alertam mas não bloqueiam); Beamex CMX (forte mas internacional)
- **Métrica de sucesso:** zero NC originada de erro que software poderia ter pego

---

### BIG-03 — Evoluir D→C→B→A sem trauma de troca de sistema

> **Quando** minha empresa amadurece de calibração comum pra acreditação RBC, **quero** evoluir sem trauma de troca de sistema, **pra que possa** decidir crescimento sem o peso da migração.

- **Categoria:** funcional (configurabilidade) + emocional (não-aprisionado)
- **Quem mais sente:** dono (Roldão), RT Qualidade (Sandra) — perfis C/B em ambição de subir
- **Concorrente que mais resolve hoje:** **nenhum** — diferencial único do Aferê
- **Métrica de sucesso:** upgrade D→C→B em < 1 dia útil sem perda de histórico; A exige prova documental (INV-015)
- **EIXO PRIMÁRIO DE VENDA + MOAT ESTRUTURAL** (junto com BIG-01)
- **Nota sobre moat:** é o único Big Job que constitui moat estrutural difícil de copiar — concorrentes nacionais (Cali, Metroex, FP2) foram construídos pra UM perfil cada e re-arquitetar sai caro. Vida útil do moat estimada em 3-5 anos antes de aparecer cópia crível.
- **Escopo MVP-1:** **entrega apenas perfil B com flag pra desligar regras = D**. Perfis A e C entram MVP-2 (A exige prova documental; C exige biblioteca de gap analysis).

---

### BIG-04 — NFS-e municipal correta em qualquer prefeitura

> **Quando** OS executada e cliente em município X, **quero** emissão automática conforme padrão do município (Padrão Nacional + variantes próprias SP/Goiânia/Brasília), **pra que possa** não estudar layout de 26 prefeituras.

- **Categoria:** funcional + emocional (não-pode-errar-fisco)
- **Quem mais sente:** financeiro (Cláudia), dono (Roldão)
- **Concorrente que mais resolve hoje:** FP2 (só Santa Maria); BaaS fiscal — empresa terceirizada que cuida só de nota fiscal — (Focus, PlugNotas) sem integrar com OS de calibração
- **Métrica de sucesso:** 100% das NFS-e aceitas pela prefeitura na 1ª tentativa
- **Deadline duro:** cutover Padrão Nacional 01/09/2026 (R-016)

---

### BIG-05 — Não voltar à sede pra registrar visita de campo

> **Quando** termino visita no campo, **quero** não voltar à sede pra registrar, **pra que possa** chegar em casa antes do escuro.

- **Categoria:** funcional + emocional (qualidade de vida)
- **Quem mais sente:** técnico (Bruno), gerente (Sandra)
- **Concorrente que mais resolve hoje:** Beamex bMobile, Metroex Coletor (com hardware proprietário); Auvo (sem semântica calibração)
- **Métrica de sucesso:** > 80% dos técnicos não voltam à sede em dias de campo; OS fechada no mesmo dia em > 90% dos casos
- **Escopo MVP-1:** **entrega web responsivo + foto + assinatura touch**. Offline-first verdadeiro (sincronização robusta com conflito de dado) = MVP-2.

---

### BIG-06 — Atender Metrologia Legal + Voluntária no mesmo pacote

> **Quando** atendo cliente que precisa dos dois tipos (RBC voluntária + verificação INMETRO obrigatória), **quero** não administrar dois processos paralelos, **pra que possa** cobrar uma vez e entregar um pacote.

- **Categoria:** funcional + social (cliente percebe como único fornecedor)
- **Quem mais sente:** gerente (Sandra), dono (Roldão)
- **Concorrente que mais resolve hoje:** nenhum (R-040: risco 040 — gap confirmado de mercado)
- **Métrica de sucesso:** 1 fatura, 1 OS-pai com 2 sub-OS (RBC + IPEM), 1 visita técnica quando possível
- **Decisão fundadora:** MVP-1 obrigatório (16/05/2026)

---

### BIG-07 — Cadastrar cliente UMA vez e ter ele em todos os fluxos

> **Quando** recebo cliente novo, **quero** cadastrar uma vez e ter ele em todos os fluxos (OS, certificado, NFS-e, cobrança), **pra que possa** não re-digitar o mesmo CPF/CNPJ em 4-6 sistemas.

- **Categoria:** funcional + emocional (não-burro)
- **Quem mais sente:** atendente (Letícia), financeiro (Cláudia), dono (Roldão)
- **Concorrente que mais resolve hoje:** ERP horizontal (Bling, Conta Azul) tem cadastro único mas não fala com Cali/Metroex
- **Métrica de sucesso:** zero re-digitação; dor D-001 zerada
- **Promovido a Big Job na auditoria 17/05/2026** (era JTBD-054; eleito #2 no novo Top 10)
- **Nota:** BIG-07 antigo ("portal pro cliente final") foi movido pra nova §4.6 — job-holder diferente.

---

### BIG-08 — Saber o custo real de cada atendimento em campo (Frota + UMC + Caixa do técnico)

> **Quando** opero técnicos em campo + UMC (Unidade Móvel de Calibração — caminhão com pesos-padrão pra balança rodoviária), **quero** ter visão completa do custo real de cada atendimento (mão de obra + deslocamento + despesas + veículo + motorista + UMC), **pra que possa** precificar certo e não trabalhar no prejuízo.

- **Categoria:** funcional + emocional (não-trabalhar-no-prejuízo)
- **Quem mais sente:** dono (Roldão), gerente (Sandra), técnico (Bruno), motorista UMC (Carlos)
- **Concorrente que mais resolve hoje:** **nenhum** — Auvo cobre só OS+GPS de campo (sem UMC, sem caixa do técnico, sem frota completa); Bling/Conta Azul/Omie/Cali/Metroex/Calibre/FP2 = zero cobertura. **6º gap defensável do projeto** (ver `dominio-de-negocio.md` §"Controle de Técnico em Campo").
- **Métrica de sucesso:** TCO por veículo/mês visível; custo real por OS visível; zero técnico volta da viagem sem prestação de contas em > 7 dias; zero veículo com documento vencido durante atendimento agendado.
- **Decisão fundadora 17/05/2026** (Roldão): operação de campo + frota + UMC + caixa do técnico é módulo central, não acessório. Detalhes técnicos em `dominio-de-negocio.md` §"Controle de Técnico em Campo".
- **Nota sobre o slot BIG-08:** o antigo BIG-08 (cadeia de rastreabilidade automática) foi rebaixado de Big Job a JTBD-028 alta prioridade — continua no Top 10 #8, mas perdeu o status de "Big Job autônomo" porque na prática é habilitador técnico do BIG-02 (não-perder-acreditação), não um job de venda por si só.

---

### BIG-09 — Comissões configuráveis sem mexer no código

> **Quando** vou precificar comissão de N tipos de colaborador (vendedor, técnico, auxiliar, motorista, supervisor) com regras diferentes por tipo de serviço, equipamento, perfil, **quero** configurar tudo no setup (sem ter que pedir pra programador), **pra que possa** mudar política comercial em horas, não em semanas.

- **Categoria:** funcional + emocional (autonomia sobre política comercial) + social (equipe sente que é "casa séria")
- **Quem mais sente:** dono (Roldão), gerente (Sandra), financeiro (Cláudia), técnico (Bruno), motorista UMC (Carlos), vendedor (Rogério)
- **Concorrente que mais resolve hoje:** **nenhum no PME nacional.** Bling/Omie/Conta Azul têm comissão básica de vendedor (% sobre venda); TOTVS Protheus tem módulo robusto mas é enterprise (>R$ 50k de implementação) e genérico (não entende OS de calibração); Auvo tem comissão simples por OS; Cali/Metroex/Calibre/FP2 = zero módulo de comissão.
- **Métrica de sucesso:** mudança de política comercial aplicada em < 1 dia (hoje: semanas com programador externo); zero comissão paga em OS deficitária; zero comissão paga sobre fatura inadimplente; tempo de fechamento da equipe inteira < 1 dia útil (hoje: 3-5 dias).
- **Decisão fundadora 17/05/2026** (Roldão): módulo central do produto, não opcional nem genérico. Detalhes técnicos em `dominio-de-negocio.md` §"Módulo de Comissões Configuráveis" (8 formas de cálculo: bruto / só mão de obra / peças+serviços separados / produtos / líquido pós-despesas / valor fixo / por tipo de serviço / por equipamento; múltiplos participantes por OS; gatilho por venda/orçamento/OS/NF/recebimento/compensação; bloqueio por margem/desconto/prejuízo; aprovação com auditoria de cada ajuste).
- **Gap competitivo:** Aferê é o **único PME entregando isso**. 7º gap defensável do projeto (acoplado a BIG-08 — cálculo sobre líquido depende de Frota/UMC/Caixa do Técnico).
- **JTBDs cobertos:** JTBD-071 a JTBD-082 (12 jobs novos em §3.12).
- **Riscos a mitigar:** R-novo C1 (regra mal-configurada → cálculo errado em escala) via simulador "se rodasse hoje" antes de ativar; R-novo C2 (vendedor abusa de desconto pra elevar margem aparente) via bloqueio de desconto acima de N% sem aprovação; R-novo C3 (comissão paga sobre fatura inadimplente) via gatilho "só sobre recebido" + estorno automático em cancelamento.

---

### BIG-10 — Cliente 360°, CRM contínuo e nunca esquecer cliente

> **Quando** atendo um cliente, **quero** que toda informação dele fique conectada num só lugar (calibrações, certificados, OS, financeiro, equipamentos, próxima ação comercial), **pra que possa** nunca esquecer cliente e transformar todo serviço em oportunidade futura.

- **Categoria:** funcional + social (parecer organizado pro cliente) + emocional (não-dormir-no-volante)
- **Quem mais sente:** dono (Roldão), vendedor (Rogério), atendente (Letícia), gerente (Sandra)
- **Concorrente que mais resolve hoje:** **nenhum integra.** Bling/Omie/Conta Azul têm CRM operacional sem cruzar com calibração/equipamento. Cali/Metroex/Calibre têm calibração sem CRM contínuo. HubSpot/RD Station têm automação sem semântica de calibração. **Gap competitivo confirmado — 8º gap defensável do projeto** (ver `dominio-de-negocio.md` §"Cliente 360°…").
- **Métrica de sucesso:** zero cliente inativo > 180d sem alerta; > 90% das interações cliente x equipe consultam só a tela Cliente 360°; tempo médio "abrir cliente → entender contexto" < 30s; taxa de renovação anual > 85%.
- **EIXO PRIMÁRIO DE VENDA** (junto com BIG-01/BIG-03). Coração da filosofia "cliente nunca morre" — toda ação operacional gera inteligência comercial.
- **Decisão fundadora 17/05/2026** (Roldão).
- **JTBDs cobertos:** JTBD-083 a JTBD-097 (15 jobs novos em §3.13).
- **Riscos a mitigar:** R-novo CRM-1 (automação dispara mensagem indevida em massa → Reclame Aqui) via sandbox obrigatório de BIG-11; R-novo CRM-2 (LGPD art. 18 — direito de oposição) via opt-in granular por canal/tipo de mensagem; R-novo CRM-3 (Visma/Conta Azul + Cali clonam diferencial) já citado em R-035 — mitigação via velocidade de mercado.

---

### BIG-11 — Engine de Automações configurável sem programador

> **Quando** configuro fluxos repetitivos (avisar cliente antes da recalibração, lembrar técnico de carregar peça, criar tarefa pro vendedor pós-OS, escalar cobrança), **quero** montar regras gatilho→condição→ação sem programador, **pra que possa** mudar política em horas, não em sprints.

- **Categoria:** funcional + emocional (autonomia operacional sem dependência de TI)
- **Quem mais sente:** dono (Roldão), gerente (Sandra), financeiro (Cláudia), RT Qualidade
- **Concorrente que mais resolve hoje:** HubSpot/RD Station/ActiveCampaign têm engine forte mas **sem semântica de calibração**; Bling/Omie/Conta Azul não têm engine; Cali/Metroex/Calibre nem perto. **Gap competitivo confirmado — acoplado a BIG-10; é o motor que faz Cliente 360° "respirar".**
- **Métrica de sucesso:** mudança de política operacional aplicada em < 1 dia (hoje: semanas); 100% das regras novas passam por sandbox antes de ativar; zero disparo em massa errado em produção; > 80% das tarefas comerciais/operacionais geradas por automação.
- **Decisão fundadora 17/05/2026** (Roldão): módulo central, não opcional. Detalhes técnicos em `dominio-de-negocio.md` §"Cliente 360°…" anexo técnico (engine com retry idempotente, DSL gatilho/condição/ação, aprovação humana antes de ação irreversível, sandbox de teste, auditoria de toda execução).
- **JTBDs cobertos:** JTBD-084, 085, 087, 088, 090, 092, 093, 094, 095, 096 (10 jobs novos em §3.13).
- **Riscos a mitigar:** R-novo CRM-1 (disparo errado em massa) via sandbox obrigatório + aprovação humana antes de ação irreversível; risco "regra mal-configurada cria loop" via limite de disparos/minuto + alerta de anomalia.

---

### BIG-12 — Estoque multi-local com lacre/selo INMETRO rastreáveis individualmente

> **Quando** opero estoque distribuído (central + N técnicos + N veículos + UMC + motorista), **quero** rastrear cada peça/lacre/selo individualmente com transferência em 2 etapas (envio + aceite) e foto obrigatória, **pra que possa** nunca perder peça cara nem tomar NC fiscal por selo sem rastreio.

- **Categoria:** funcional + emocional (proteção patrimônio + sobrevivência regulatória)
- **Quem mais sente:** técnico (Bruno), motorista UMC (Carlos), almoxarife/gerente (Sandra), dono (Roldão), RT Qualidade
- **Concorrente que mais resolve hoje:** **nenhum no mercado BR.** Bling/Omie/Conta Azul têm estoque básico sem multi-local (técnico/motorista/UMC) nem lacre/selo individual nem transferência 2-etapas. Cali/Metroex/Calibre = zero estoque. Auvo tem peça simples em OS sem multi-local nem lacre/selo INMETRO. **Gap competitivo confirmado — 9º gap defensável do projeto** (ver `dominio-de-negocio.md` §"Módulo de Estoque…").
- **Métrica de sucesso:** zero peça "sumida" no inventário trimestral; 100% dos selos INMETRO com rastreabilidade individual completa + foto; resposta de auditoria IPEM ("cadê o selo X aplicado em maio?") em < 30s; zero NC fiscal por selo sem rastreio; redução de divergência de inventário > 40% em 3 meses.
- **Decisão fundadora 17/05/2026** (Roldão): módulo central, não acessório. Detalhes técnicos em `dominio-de-negocio.md` §"Módulo de Estoque Completo…" (12 tipos de local, transferência 2-etapas com aceite + motivo de recusa, lacre/selo INMETRO com controle individual + foto obrigatória, inventário com justificativa obrigatória pra divergência, integração total com OS).
- **JTBDs cobertos:** JTBD-098 a JTBD-109 (12 jobs novos em §3.14).
- **Riscos a mitigar:** R-novo EST-1 (selo INMETRO perdido → multa IPEM) via rastreabilidade individual + foto + workflow de perda com aprovação gestor; R-novo EST-2 (lacre/selo aplicado em equipamento errado = fraude metrológica) via confirmação dupla (técnico + foto + assinatura cliente); R-novo EST-3 (técnico recusa peça alegando que não veio) via 2-etapas + foto da peça na origem; R-novo EST-4 (divergência sistemática em técnico X = sinal de fraude) via relatório de divergência por responsável.

---

### 4.5 Mapa do trabalho (Ulwick) por Big Job

> Cada Big Job não é um evento — é um **processo de 8 fases**. Mapear as fases mostra onde o trabalho dói mais hoje e onde aparecem jobs sub-cobertos (especialmente Confirm/Modify/Conclude — geralmente esquecidos pelos concorrentes).
>
> **As 8 fases (Ulwick):**
> 1. **Definir** — usuário decide que precisa fazer isso
> 2. **Localizar** — onde achar a info/recurso necessário
> 3. **Preparar** — montar tudo antes
> 4. **Confirmar** — checar se tá pronto
> 5. **Executar** — fazer
> 6. **Monitorar** — acompanhar enquanto rola
> 7. **Modificar** — ajustar quando muda
> 8. **Concluir** — encerrar/arquivar
>
> **🔥 = fase que mais dói hoje.**

#### BIG-01 — Não perder informação entre etapas

| Fase | O que acontece | Onde dói |
|---|---|---|
| Definir | Cliente entra em contato; atendente decide se é manutenção ou calibração | — |
| Localizar | Atendente busca histórico do cliente em 5 conversas WhatsApp + planilha + e-mail | 🔥 |
| Preparar | Cria chamado, transcreve descrição, anexa foto recebida | — |
| Confirmar | Re-pergunta ao cliente "vocês usam X mesmo?" | 🔥 |
| Executar | Triagem → orçamento → OS → calibração → certificado → NFS-e (6 sistemas) | 🔥 |
| Monitorar | Cliente liga "cadê?", ninguém sabe responder | 🔥 |
| Modificar | Cliente pede mudança de escopo a meio caminho — re-digitação em todos | — |
| **Concluir** | OS fechada mas faturamento esquece de subir; arquivo nunca consolidado | **🔥 sub-coberto** |

**Job sub-coberto identificado:** JTBD-056 abaixo (gestão documental — arquivamento auditável da OS completa).

#### BIG-02 — Não perder acreditação por erro evitável

| Fase | O que acontece | Onde dói |
|---|---|---|
| Definir | Sandra decide rodar verificação de readiness | — |
| Localizar | Busca evidências espalhadas | 🔥 |
| Preparar | Monta planilha de matriz competência na hora | 🔥 |
| Confirmar | "Tá tudo certo?" — não tem como saber sem checklist | 🔥 |
| Executar | Auditoria Cgcre acontece | — |
| Monitorar | NC abertas — quem fecha? quando? | 🔥 |
| **Modificar** | NC corrigida → atualizar procedimento → re-treinar pessoal → re-autorizar | **🔥 sub-coberto** |
| **Concluir** | Evidência da ação corretiva arquivada de forma rastreável | **🔥 sub-coberto** |

**Job sub-coberto identificado:** JTBD-057 abaixo (gestão de NC com workflow estruturado).

#### BIG-03 — Evoluir D→C→B→A sem trauma

| Fase | O que acontece | Onde dói |
|---|---|---|
| Definir | Dono decide subir de perfil (cliente novo exige RBC) | — |
| Localizar | Procurar consultor / sondar Cgcre / ler norma | 🔥 |
| **Preparar** | Gap analysis: o que falta? quanto custa? quanto tempo? | **🔥 sub-coberto — JTBD-005** |
| Confirmar | "Estou pronto pra pedir?" | 🔥 |
| Executar | Petição Cgcre + auditoria de habilitação | — |
| Monitorar | Acompanhar processo (~12-18 meses) | — |
| Modificar | Ajustar conforme Cgcre pede correções | — |
| Concluir | Migração de dados entre perfis sem perder histórico | 🔥 |

**Job sub-coberto identificado:** JTBD-005 já existe mas é baixa prioridade — promover pra MVP-2 alta com base nesse mapeamento.

#### BIG-04 — NFS-e municipal correta

| Fase | O que acontece | Onde dói |
|---|---|---|
| Definir | OS executada — financeiro decide emitir nota | — |
| Localizar | Qual o município? qual padrão? | — |
| Preparar | Configurar prefeitura uma vez por município | 🔥 |
| Confirmar | Dados estão batendo? | — |
| Executar | Emissão | 🔥 |
| Monitorar | Recebeu confirmação da prefeitura? rejeitou? | 🔥 |
| **Modificar** | Cancelar + reemitir quando erra | **🔥 sub-coberto** |
| Concluir | Arquivar XML pra 5 anos (obrigação fiscal) | — |

**Job sub-coberto identificado:** workflow de cancelamento/reemissão amigável (sem precisar ligar pra contador).

#### BIG-05 — Não voltar à sede pra registrar visita

| Fase | O que acontece | Onde dói |
|---|---|---|
| Definir | Técnico chega no cliente | — |
| Localizar | Histórico do instrumento, peças sugeridas, certificado anterior | 🔥 |
| Preparar | Conferir maleta de padrões e ferramentas | — |
| Confirmar | Cliente confirma escopo da OS | — |
| Executar | Calibração propriamente dita | — |
| Monitorar | — | — |
| Modificar | Cliente pede mais um instrumento de última hora | 🔥 |
| Concluir | Assinatura + envio do certificado + fechamento da OS pelo celular | 🔥 |

#### BIG-06 — Metrologia Legal + Voluntária juntos

| Fase | O que acontece | Onde dói |
|---|---|---|
| Definir | Cliente atende balança comercial (precisa IPEM) + lab interno (precisa RBC) | — |
| Localizar | Calendário IPEM por instrumento + calendário RBC | 🔥 |
| Preparar | Agendar 2 visitas separadas (hoje) ou 1 unificada (com Aferê) | 🔥 |
| Confirmar | Confirmar com cliente data + escopo dos dois processos | — |
| Executar | Calibrar (RBC) + acompanhar verificação IPEM | — |
| Monitorar | Status da verificação IPEM (sai do escopo do lab) | 🔥 |
| **Modificar** | IPEM reprovou — reagendar | **🔥 sub-coberto** |
| Concluir | 1 fatura agregada + 1 dossiê pro cliente | 🔥 |

#### BIG-07 — Cadastro de cliente único

| Fase | O que acontece | Onde dói |
|---|---|---|
| Definir | Cliente novo entra em contato | — |
| Localizar | Já existe cadastro? em qual sistema? | 🔥 |
| Preparar | Coletar CNPJ, IE, contato, endereço, dados de cobrança | — |
| Confirmar | Validar dados via Receita/SintegraWS | — |
| Executar | Cadastrar UMA vez, propagar pra OS/certificado/NFS-e/cobrança | 🔥 |
| Monitorar | Cliente mudou de endereço? IE foi cancelada? | 🔥 |
| Modificar | Atualizar em UM lugar, propagar pra todos | 🔥 |
| Concluir | Cliente inativo — arquivar mas manter histórico | — |

#### BIG-08 — Custo real do atendimento em campo (Frota + UMC + Caixa)

| Fase | O que acontece | Onde dói |
|---|---|---|
| Definir | Gerente decide agendar OS de campo / Roldão precifica novo contrato | — |
| Localizar | Qual veículo está disponível? sem documento vencido? sem manutenção pendente? Qual técnico? Qual UMC se for balança rodoviária? | 🔥 |
| **Preparar** | Adiantamento pro técnico (genérico ou por OS); reservar UMC; checar combustível; planejar rota | **🔥 sub-coberto — JTBDs 060, 063, 065** |
| Confirmar | Confirmar com cliente data + escopo; confirmar com motorista UMC disponibilidade | — |
| Executar | Técnico/motorista em campo; abastece, paga pedágio, hospeda, alimenta, gasta peça emergencial | 🔥 |
| Monitorar | Onde está o veículo agora? quanto gastou até agora? KM rodado bate com o esperado? | 🔥 |
| **Modificar** | Imprevisto (veículo quebra, técnico fica doente, cliente pede equipamento extra) — re-alocar recursos | **🔥 sub-coberto — JTBD-066** |
| **Concluir** | Prestação de contas em 5 min via mobile (não planilha); reembolso KM se carro próprio; reconciliação custo real vs orçado por OS; TCO atualizado por veículo | **🔥 sub-coberto — JTBDs 062, 064, 069, 070** |

**Resumo dos gaps identificados pelo Job Map:** as fases **Confirm, Modify e Conclude** são sistematicamente sub-cobertas pelos concorrentes nacionais. Aferê tem oportunidade de diferenciação ao tratar essas fases como cidadãs de primeira classe — não como afterthought.

---

### 4.6 Jobs do end-customer do tenant (cliente do nosso cliente — persona João)

> O cliente final do tenant não opera o ERP; ele consome o resultado (certificado). Os jobs dele importam porque a percepção dele afeta a retenção do tenant.

**BIG-END-01 — Baixar certificado sozinho sem ligar pro lab**

> **Quando** preciso do certificado pra mostrar pro auditor/cliente, **quero** baixar sozinho sem ligar pro lab, **pra que possa** não depender de horário comercial.

- **Categoria:** funcional + emocional (autonomia)
- **Quem:** cliente final do tenant (persona: João)
- **Concorrente que mais resolve hoje:** Cali WEB (portal feio que ninguém usa); MasterControl (perfil A grande)
- **Métrica de sucesso:** > 50% dos downloads de certificado via portal, sem passar pelo SAC do tenant
- **Era BIG-07** na versão anterior; movido pra cá porque o job-holder é diferente (não é o usuário do ERP)

---

## 5. Anti-jobs — o que o produto NÃO deve resolver

> Decididos AGORA pra evitar scope creep durante MVP-1. Cada anti-job tem motivo explícito.
>
> **Dois princípios que regem a lista de anti-jobs (acordados na auditoria 17/05/2026):**
>
> 1. **Vertical thin, não horizontal raso.** Aferê é fundo em assistência técnica + calibração; jamais raso em N domínios adjacentes. Quando o anti-job vira tentação ("mas dá pra fazer rapidinho"), revisar este princípio.
> 2. **Produto, não plataforma.** Aferê é produto opinativo: regras embutidas, fluxos definidos, customização limitada à configuração. Não é plataforma onde cada cliente molda o seu. Tentação de "customização pra fechar venda grande" é violação desse princípio.

### Anti-jobs antigos (mantidos)

| Anti-job | Por que NÃO | Onde resolver |
|---|---|---|
| **ANTI-01** Folha de pagamento, ponto, holerite, férias | Domínio RH completo é mercado próprio (Senior, ADP, Sankhya RH); ROI baixo pro nosso ICP; complexidade trabalhista alta | Integração externa (Pontomais, Sankhya RH) — domínio `RH/Pessoas` marcado como lazy em `dominio-de-negocio.md` |
| **ANTI-02** Pagamento online com cartão direto (gateway próprio) | Vira PCI-DSS 4.0.1 escopo full (R-025); custo de auditoria anual desproporcional ao ticket | Usar PSP terceiro (Asaas, Pagar.me, Stripe) — escopo SAQ A |
| **ANTI-03** Gestão clínica/análises clínicas humanas (LIS) | Domínio próprio (CFM 1821/2007, SBIS-CFM); ABNT NBR ISO 15189 ≠ 17025 | Fora de escopo; se cliente farma exigir, MVP-3+ |
| **ANTI-04** ERP horizontal genérico (restaurante, oficina mecânica) | "Founder is customer" + R-001 (customização disfarçada — risco 001: produto perde foco no nicho defensável) | Foco em ICP "assistência técnica + lab calibração" |
| **ANTI-05** BI/Analytics sofisticado (dashboards customizáveis, query SQL pelo usuário) | Custo de UX e suporte alto; gigantes resolvem melhor (Metabase, PowerBI, Looker) | Dashboards essenciais nativos; export pra BI externo via API |
| **ANTI-06** Hardware proprietário (calibrador, sensor, dispositivo de coleta) | Não somos fabricante; Beamex/Fluke/Presys já fazem | Integrar via Bluetooth/USB com hardware existente — MVP-2/3 |

### Anti-jobs adicionados na auditoria 17/05/2026

| Anti-job | Por que NÃO | Onde resolver |
|---|---|---|
| **ANTI-07** WhatsApp Business bidirecional livre | Meta restringe API Business; só template outbound aprovado; conversação livre só após cliente iniciar; risco de banimento de número | Templates aprovados (notificação de OS, certificado pronto); resposta inbound vira chamado |
| **ANTI-08** Mensageria interna entre técnicos (Slack-mini, chat interno) | Mercado saturado (WhatsApp já usado pessoalmente); custo de UX alto; baixo valor diferencial | Equipes usam WhatsApp pessoal/grupo; produto só notifica eventos relevantes |
| **ANTI-09** BI customizado com SQL ou no-code builder | Mesma razão do ANTI-05 — reforço explícito | Dashboards fixos por papel + export CSV/Parquet pra Metabase/PowerBI externo |
| **ANTI-10** Calendário/agenda como produto | Google Calendar e Outlook resolvem; reinventar não agrega | Integração bidirecional Google Calendar (técnico vê agenda no calendário pessoal) |
| **ANTI-11** **Zero customização por cliente** ⚠️ CRÍTICO | Customização por tenant mata produto opinativo, dispara dívida técnica exponencial e vira o R-001 ("founder is customer" virando "cada cliente é customer"); é a tentação mais perigosa do negócio | Única forma de mexer é **configuração estruturada** (switches, perfis, checklists). Cliente que quer mais paga **setup** que vira config **nativa pra todos** — não código exclusivo. Quem insistir em customização individual: educar ou não fechar a venda |

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
| BIG-01 (não perder info entre etapas) | Quer ERP de OS + fiscal simples |
| BIG-04 (NFS-e) | É a coluna vertebral do negócio dele |
| BIG-05 (não voltar à sede) | Assistência técnica vive no campo |
| **BIG-08 (Frota + UMC + caixa do técnico)** | Operação de campo intensa = custo descontrolado sem isso |
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

## 8. Síntese — Top 10 Jobs prioritários pro MVP-1 (re-rankeado 17/05/2026 — 4ª rodada)

> Critério: combinação de (a) Big Job ou job de alta prioridade, (b) gap real (sem concorrente forte), (c) bloqueio de venda se não tiver, (d) ancorado em invariante regulatória, (e) ROI quantificado pro tenant.
>
> **4ª rodada 17/05/2026:** com a entrada de BIG-10 (Cliente 360°), BIG-11 (Engine de Automações) e BIG-12 (Estoque multi-local com lacre/selo INMETRO), o Top 10 foi re-rankeado. **BIG-12 entra como #5** (gap absoluto + crítico pro Bruno + mitiga risco metrológico real). **BIG-10 entra como #6** (eixo primário de venda junto com BIG-01/03). **BIG-11 entra como #7** (motor que faz BIG-10 funcionar). Itens antes em #6-#9 desceram 1-3 posições; JTBD-030 sai do Top 10 estrito (vai pra alta-prioridade abaixo do Top 10).

**#1 — BIG-02 (JTBD-002) — Não perder acreditação RBC**
- Vital pro perfil A; medo central do dono. Sem isso, perfil A não compra.
- Mitiga R-018 (score 25 — maior risco do projeto)

**#2 — JTBD-044 — Acompanhar contrato recorrente pra não perder renovação** ⬆️ promovido
- ROI quantificado mais alto: R$ 3-8k/mês por cliente perdido por esquecimento de renovação
- Calibração é negócio inerentemente recorrente; perda de renovação é o vazamento de receita mais sangrento
- Complementado por JTBD-084 (disparo automático ao emitir certificado) e JTBD-092 (proposta renovação 60d antes)

**#3 — BIG-03 reescrito — Evoluir D→C→B→A sem migração** 🛡️ eixo + moat
- Diferencial defensável único; **vida útil do moat 3-5 anos** antes de cópia crível
- Junto com BIG-01 e BIG-10 é eixo primário de venda

**#4 — BIG-04 — NFS-e multi-prefeitura BR**
- R-016: cutover Padrão Nacional 01/09/2026 — deadline duro, externo ao projeto
- Quem não estiver pronto até a data perde capacidade de faturar

**#5 — BIG-12 NOVO — Estoque multi-local com lacre/selo INMETRO rastreáveis** ⬆️ novo (17/05/2026)
- Decisão fundadora 17/05/2026 (Roldão): módulo central, não acessório
- 9º gap defensável (vazio absoluto no mercado BR — Bling/Omie/Cali/Metroex/Auvo não cobrem)
- Crítico pro Bruno (técnico) + Carlos (motorista) + Sandra (RT na fiscalização IPEM)
- Mitiga R-novo EST-1 (selo perdido → multa IPEM)
- 12 JTBDs novos (JTBD-098 a JTBD-109)

**#6 — BIG-10 NOVO — Cliente 360° + CRM contínuo** ⬆️ novo (17/05/2026) 🛡️ eixo primário
- Decisão fundadora 17/05/2026 (Roldão): "cliente nunca morre" — filosofia central do produto
- 8º gap defensável (ninguém integra calibração + CRM + automação no BR)
- EIXO PRIMÁRIO DE VENDA junto com BIG-01/BIG-03
- 15 JTBDs novos (JTBD-083 a JTBD-097)

**#7 — BIG-11 NOVO — Engine de Automações configurável sem código** ⬆️ novo (17/05/2026)
- Decisão fundadora 17/05/2026 (Roldão): motor de BIG-10; gatilho→condição→ação com sandbox
- Acoplado a BIG-10 (sem engine, Cliente 360° vira tela bonita sem ação)
- Mitiga obrigatoriamente R-novo CRM-1 (disparo errado em massa) via sandbox antes de ativar
- 10 JTBDs novos (JTBD-084, 085, 087, 088, 090, 092, 093, 094, 095, 096)

**#8 — BIG-06 reescrito — Metrologia Legal + RBC juntos**
- Sem concorrente nacional (R-040 — gap confirmado)
- Decisão fundadora 16/05/2026: MVP-1 obrigatório

**#9 — BIG-08 NOVO — Frota + UMC + custo real por atendimento**
- Decisão fundadora 17/05/2026 (Roldão): operação de campo + frota + UMC + caixa do técnico é módulo central
- 6º gap defensável (sem concorrente nacional integrado)
- 11 JTBDs (JTBD-060 a JTBD-070); persona Carlos motorista UMC

**#10 — BIG-09 NOVO — Comissões configuráveis sem mexer no código**
- Decisão fundadora 17/05/2026 (Roldão): módulo central, não opcional nem genérico
- 7º gap defensável (acoplado a BIG-08)
- 12 JTBDs (JTBD-071 a JTBD-082); cobre 6 papéis
- Único PME no mercado BR entregando isso

**Saíram do Top 10 estrito nessa rodada (mantidos como alta prioridade pro MVP-1):**
- **JTBD-027** — Cálculo de incerteza embutido (3 grandezas no MVP-1) — segue core técnico obrigatório, fora do Top 10 porque é entrega "implícita" de qualquer software de calibração
- **JTBD-028** — Cadeia de rastreabilidade automática — segue alta prioridade (INV-002), habilitador de BIG-02
- **JTBD-030** — Assinatura digital ICP-Brasil — alta prioridade (INV-001), saiu do Top 10 estrito
- **JTBD-054 / BIG-07** — Cadastro único — Big Job mantido, sai do Top 10 estrito; entrega "wow" óbvio em demo
- **BIG-01 reescrito** (eixo de venda guarda-chuva — toda dor de "não perder info entre etapas" cai dentro dele)
- **BIG-05 reescrito** (alta prioridade, escopo MVP-1 reduzido a web responsivo + foto + assinatura touch; offline-first robusto em MVP-2)
- **JTBD-001 + JTBD-013 + JTBD-097** (dashboard "1 número do dia") — alta prioridade pro MVP-1 como "wow" em demo
- **JTBD-021 + JTBD-024** (habilitadores do BIG-05)
- **JTBD-039** (fluxo de caixa projetado)
- **JTBD-091** (Cliente 360° tela única) — entra dentro de BIG-10 como entrega principal
- **JTBD-101 a JTBD-103** (lacre/selo INMETRO) — entram dentro de BIG-12 como entregas principais

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
- **Big Job** = os 12 trabalhos centrais que, se a gente fizer bem, justifica a venda sozinhos.
- **Métrica de sucesso** = como medir se o trabalho foi bem feito (geralmente: mais rápido, menos erro, menos vergonha, menos R$).
- **Moat estrutural** = vantagem competitiva difícil de copiar. Aferê tem **dois**: **BIG-01** (costura horizontal — todos os ciclos sob 1 fluxo, do chamado à NFS-e à cobrança) e **BIG-03** (costura vertical — todos os perfis de maturidade D→C→B→A sob 1 produto sem migração). Concorrentes nacionais resolvem 1 dos dois, nenhum cobre os dois. Vida útil estimada do moat: 3-5 anos.

---

## 11. Apêndice A — Princípios do framework JTBD (Christensen + Ulwick)

> Mantido como apêndice porque é jargão técnico de produto, não conteúdo de negócio. Quem é novo no framework lê isso antes de voltar pra §3.

1. **Job ≠ feature.** Job é o "trabalho" que a pessoa contrata um produto pra fazer. Feature é como o produto faz. "Quero emitir certificado de calibração" é feature; **"Quero entregar o certificado pro meu cliente sem ele me cobrar 3 vezes pelo telefone"** é job.
2. **Forma Christensen:** "Quando eu **[situação trigger]**, eu quero **[motivação]**, pra que eu possa **[resultado esperado]**." Toda linha-de-job tem que caber nesse molde — se não cabe, é feature disfarçada.
3. **3 categorias (Ulwick):**
   - **Funcional** — trabalho concreto/operacional (emitir nota, calcular incerteza, agendar técnico).
   - **Emocional** — como a pessoa quer **se sentir** (segura, no controle, não-burra, não-culpada).
   - **Social** — como quer ser **vista pelos outros** (profissional pelo cliente, competente pelo chefe, "tô junto" pelo regulador).
4. **Métrica de sucesso (Outcome — Ulwick):** todo job tem que ter "como eu mediria se foi bem feito" — geralmente em forma de velocidade (mais rápido), confiabilidade (menos erro), custo (menos R$/hora), ou ansiedade (menos retrabalho mental).
5. **Concorrente do job ≠ concorrente do produto.** Concorrente do job é **o que a pessoa usa HOJE pra fazer esse trabalho** — pode ser planilha, WhatsApp, gritar com o colega, pasta de e-mail. Esse é o **status quo a derrotar**, não o software A ou B do mercado.
6. **Anti-job tem o mesmo peso de job.** Decidir explicitamente **o que NÃO resolvemos** é o que mantém o produto enxuto e impede scope creep.
7. **Job Map de 8 fases (Ulwick — Outcome-Driven Innovation):** todo job grande pode ser quebrado em 8 fases (Definir → Localizar → Preparar → Confirmar → Executar → Monitorar → Modificar → Concluir). Concorrentes geralmente cobrem bem Execute; as fases Confirm/Modify/Conclude são sub-cobertas e oferecem oportunidade de diferenciação. Ver §4.5.
8. **Forma de Big Job vs. Job comum:** Big Job é transversal a papéis e justifica compra; job comum é específico de papel/situação. Top 10 do MVP-1 mistura Big Jobs com jobs comuns que entregam "wow" imediato (ex: cadastro único, dashboard "1 número").
