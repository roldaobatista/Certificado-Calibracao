---
owner: roldao
revisado-em: 2026-05-29
status: stable
ordem-descoberta: 17/17
proximo: ADR-0001 (stack) — em aceitação
idioma: pt-BR
limite-linhas: 250
proposito: resumo de C1 Descoberta — destrava ADRs (C2).
---

<!--
template: sintese-final.md
destino: docs/descoberta/sintese-final.md
uso: 2-4 páginas resumindo problema, personas, jornadas, BMC, VPC, concorrentes, riscos, métricas, não-fazer.
status: stable aqui = "pode começar a decidir arquitetura (ADRs)".
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3
limite: ≤250 linhas.
-->

# Síntese final — Descoberta — Aferê Prumo

> **Status `stable` neste arquivo é o GATE para C2 ADRs.** Antes daqui, decisão arquitetural é prematura. Atualizado por humano + agente; gera coerência entre os 8-15 artefatos de C1.
>
> ✅ **DESCOBERTA ENCERRADA pelo Roldão em 2026-05-29.** O dono declarou explicitamente o fim de C1. Esta síntese está `stable`: o gate de arquitetura (C2 ADRs) está **liberado** e a fase-2 (operação/segurança) está **descongelada**. Próximo passo em §12.

## 1. Problema em 1 parágrafo

A Balanças Solution opera quatro frentes (venda, manutenção, calibração com selo e locação) de
forma majoritariamente manual — WhatsApp solto, orçamentos refeitos do zero, prazos de calibração
sem alarme e informação espalhada. Isso custa tempo de equipe, retrabalho e, principalmente,
**receita recorrente perdida quando prazos vencem sem aviso**. CRM/ERP genérico e chatbots prontos
não resolvem porque não entendem o domínio nem unem atendimento + automação interna. Detalhe em
[`problema.md`](./problema.md). Evidência: auto-entrevista do dono (`EE-AUTO-001`).

## 2. Quem usa (resumo)

| Persona ID | Nome | Papel | Comprador? |
|---|---|---|---|
| P-001 | Carla | Atendente/comercial (interno) | não |
| P-002 | Jorge | Técnico de calibração/manutenção (interno) | não |
| P-003 | Cliente | Cliente final (externo, via WhatsApp) | não |
| P-C-001 | Roldão | Dono/decisor (interno + comprador) | sim |

> Detalhes em [`personas.md`](./personas.md).

## 3. Jornada principal (a que justifica a Fase 1)

- **Jornada**: J-001 — Atendimento + orçamento pelo WhatsApp.
- **Canal real (evidência dos dados)**: **majoritariamente ÁUDIO** (WhatsApp PTT) — a IA tem de **transcrever** para entender e responder (D-PROD-013).
- **Persona**: P-001 (Carla) / P-003 (cliente).
- **Antes**: ~30-45 min por orçamento (est.), perguntas repetidas, informação espalhada.
- **Depois**: IA responde na hora e monta rascunho; equipe só revisa (2-3 min).
- **Economia**: tempo de atendimento repetitivo + fila; valor exato `(A VALIDAR)` — H-001.

> Segunda jornada de maior valor financeiro: J-002 (aviso de prazo de calibração). Detalhes em [`jornadas.md`](./jornadas.md).

## 4. Modelo (resumo) — PRODUTO SaaS vendido por assinatura (add-on do Aferê)

> **Virada de escopo (Roldão, 2026-05-28):** a infra de IA **será vendida por assinatura aos clientes
> que assinam o Aferê**. Não é só ferramenta interna — é **produto multi-tenant**. A **Balanças
> Solution é o 1º cliente (dogfooding)**, mas a infra precisa **comportar empresas de vários tipos e
> tamanhos, com nº de funcionários diferente e tudo configurável por empresa**.

- **Para quem (clientes pagantes)**: empresas de assistência técnica/calibração que assinam o Aferê — de portes variados (do lab de 1-2 pessoas a empresas com vários técnicos). A Balanças Solution é o primeiro.
- **Proposta**: IA central (cérebro + agentes por setor) que atende, orça, abre OS, confere certificado e avisa prazos — **configurável por empresa**.
- **Receita**: assinatura recorrente (add-on de IA do Aferê). Modelo/preço a definir (ver perguntas ao dono).
- **Custo unitário**: LLM + WhatsApp + hospedagem por tenant — tem de caber na margem da assinatura (G-005).
- **Dogfooding primeiro**: provar na Balanças Solution antes de abrir para os demais assinantes.

> Detalhes em [`business-model-canvas.md`](./business-model-canvas.md) + [`value-proposition-canvas.md`](./value-proposition-canvas.md) + [`gtm-pricing.md`](./gtm-pricing.md).

## 4.1 Sequenciamento proposto (a resposta ao "quero tudo")

> A visão é ampla e legítima, mas se construída de uma vez só, trava (R-001). Proposta alinhada
> ao **plano do dono** (o piso): fatiar em ondas, cada uma resolvendo uma dor e servindo de base
> para a seguinte. Tudo começa em **modo assistido** (IA sugere, humano aprova) e só sobe de
> automação quando os dados provarem que pode.

| Onda | Foco | Por que nessa ordem |
|---|---|---|
| **−1 — Migração Auvo→Aferê** | Importar clientes/produtos/itens do legado Auvo para o Aferê | Dado estruturado base; já há baseline pronto (341 clientes, 389 produtos, 424 itens orçados — ver `dados-reais/_banco/`) |
| **0 — Cérebro** | Centralizar conhecimento + dados do Aferê + busca por significado | Tudo depende de ter informação organizada e consultável (acervo de 1.099 fontes já coletado) |
| **1 — Atendimento + OS** (1º piloto) | WhatsApp/e-mail → entender → consultar Aferê → sugerir resposta → abrir chamado/OS | Maior dor (destrava o dono); conecta atendimento, comercial e OS |
| **2 — Comercial** | Gerar proposta/orçamento (rascunho para revisão) | Vira atendimento em faturamento |
| **3 — Financeiro** | Comprovantes, cobrança, inadimplência (no **Aferê**) | Reduz trabalho manual e melhora controle |
| **4 — Metrologia** | Conferência de certificado (2 conferências), pesos padrão, prazos | Reduz erro técnico; protege receita recorrente de calibração |
| **5 — Gestão** | Painéis (margem, retrabalho, clientes parados) + agente de gestão | Transforma a operação em decisão; depende dos dados acumulados |

> Primeiro piloto recomendado (plano §18/25): **Agente de Atendimento + OS** integrado a
> WhatsApp/e-mail e ao **Aferê**. Demais frentes (estoque, jurídico, marketing, locação) entram
> como ondas seguintes — são o teto crescente, não a V1.

> **🟢 Recomendação do agente (vai além do plano — o "teto"):** como o dono **perde 100% dos
> prazos** hoje (H-002), o **lembrete de recalibração** (avisar o cliente antes do vencimento) é
> uma capacidade **simples** e de **valor financeiro altíssimo** — e é diferente do agente de
> Metrologia completo (que confere certificado, mais complexo, Q4). Proposta: **destacar o
> "lembrete de prazo" como uma mini-onda logo após a Onda 1**, sem esperar a Metrologia. Bate com
> o Aferê, que já lista "lembrete de recalibração via WhatsApp" como top-3 do MVP. A decidir com o dono.

## 4.2 Como especificar cada agente + o cérebro (lição da análise de concorrentes)

- **Ficha-contrato por agente** (não só "agente do setor X"): para cada um dos ~10 agentes, declarar
  **Tópicos** (tarefas que cobre) + **Ações permitidas** (consultar Aferê, abrir OS, rascunhar
  orçamento…) + **o que NUNCA faz** + **gatilho de escalonamento** + **teto de autonomia por ação**.
  Operacionaliza NF-005 (cada agente só no seu domínio) e evita virar "um chatbot que faz tudo".
  → **As 10 fichas-contrato completas + mapa de handoff estão em [`agentes.md`](./agentes.md)** (workflow
  2026-05-28). O revisor de consistência apontou lacunas a decidir: dono do **motor de prazos**, dono da
  **emissão de NF**, separar **cobrança amigável (Financeiro) × formal (Jurídico)**, **configuração = papel
  humano** (não-agente), e fronteira da **locação** (motorista/jurídico/financeiro).
- **Cérebro (Onda 0) = base VERSIONADA com citação de fonte obrigatória**: toda resposta ao cliente
  cita de onde veio (qual registro do Aferê / qual item do cérebro), com dono, versão e data. A
  citação é, ao mesmo tempo, controle anti-invenção (NF-004), item de auditoria (LGPD) e acelerador
  de confiança pro dono aprovar rápido na Inbox. O que a IA **não** soube responder vira **backlog de
  cadastro** (detecção de lacunas).
- **Carga inicial do cérebro (Onda 0)** via **extração de documento com conferência por confiança**:
  certificados antigos, OS em papel/foto, comprovantes, planilhas de preço → confiança baixa vira
  tarefa humana na Inbox antes de gravar; confiança alta segue, sempre auditável. Destrava o cadastro
  inicial sem travar a Onda 0 (H-012).
- **3 modos de uso por público** (níveis de automação diferentes por modo): (a) agente que fala com o
  **CLIENTE** → sempre Nível 1 (aprovação); (b) **copiloto** que assiste atendente/dono → pode ser
  mais solto; (c) **análise** para a gestão → não age, só informa. Não confundir "robô que responde
  cliente" com "assistente que sugere ao Roldão".

## 5. Concorrência — diferenciação

- **Concorrentes**: chatbot de WhatsApp pronto, CRM/ERP genérico, plataforma de agente genérica.
- **Concorrente real é "não fazer nada" (planilha+WhatsApp)?**: **sim**.
- **Diferencial 1**: conhece o domínio de balanças (calibração, selo, prazos).
- **Diferencial 2**: une atendimento ao cliente + automação interna no mesmo cérebro + aviso proativo de prazo.

> Detalhes em [`concorrentes.md`](./concorrentes.md).

## 6. Não-fazer (resumo)

- **NF-001**: a IA não emite certificado de calibração sozinha (norma + responsabilidade humana).
- **NF-002**: a IA não envia orçamento/oferta vinculante sem revisão humana.
- **Fora da V1**: revenda multi-empresa, NF-e, relatórios avançados, app mobile nativo.

> Detalhes em [`nao-fazer.md`](./nao-fazer.md).

## 7. Riscos top-3

| ID | Risco | Severidade | Mitigação principal |
|---|---|---|---|
| R-001 | Escopo "tudo de uma vez" trava o projeto | 🔴 | Faseamento (§4.1); Fase 1 enxuta |
| R-002 | Equipe não adota, volta pra planilha | 🟠 | Piloto, simplicidade, envolver equipe (H-004) |
| R-003 | IA dá orçamento errado ao cliente | 🟠 | Modo rascunho + revisão humana (NF-002, H-005) |

> **Riscos das capacidades novas (áudio + cérebro), adicionados 2026-05-29:** R-016 (erro de transcrição
> vira ação errada), R-017 (IA inventa diagnóstico técnico), R-018 (cérebro desatualiza/conflita), R-019
> (custo de transcrição consome margem), R-020 (vazamento de dado de terceiro no cérebro), R-021 (desconto
> IA ~3% × prática 26%), R-022 (vazamento de conhecimento técnico restrito a cliente externo). Detalhes em [`riscos.md`](./riscos.md).

## 8. Métricas que mediremos

- **North Star Metric**: nº de atendimentos/orçamentos resolvidos com apoio da IA por semana.
- **Guardrails**: zero orçamento errado enviado sem revisão; satisfação do cliente; prazos avisados a tempo; adoção da equipe ≥80%; custo de IA por atendimento.

> Detalhes em [`metricas-chave.md`](./metricas-chave.md).

## 9. Decisões de produto já tomadas (antes de C2)

- D-PROD-001 (**revisada 2026-05-28**): É **produto SaaS multi-tenant vendido por assinatura** aos clientes do Aferê. A Balanças Solution é o **1º cliente (dogfooding)**, não o único. A infra precisa ser **configurável por empresa** (tipos, tamanhos, nº de funcionários, agentes, parâmetros). *(Antes dizia "ferramenta interna, revenda futura" — invertido pela virada de escopo.)*
- D-PROD-002: Toda saída da IA ao cliente passa por **revisão humana** na Fase 1 (NF-002).
- D-PROD-003: Construir por **fases** (§4.1), não tudo de uma vez.
- D-PROD-004: Começar pela frente de **atendimento/orçamento** (Fase 1), após a Fundação de dados.
- **D-PROD-005 (princípio do dono):** as ideias e requisitos que o Roldão descreve são o **mínimo** que o sistema deve fazer — **piso, não teto**. Nunca tratar a lista do dono como escopo-limite; o sistema pode/deve ir além onde agregar valor, e o agente deve **propor melhorias** além do que foi pedido (sem violar os "não-fazer"). Reportada por Roldão em 2026-05-28.
- **D-PROD-006 (princípio-mãe):** "uma IA que opera **com você, não no lugar de você**" — 100% das ações visíveis ao cliente passam pela Inbox; decisão irreversível nunca sem humano; tudo começa no Nível 1 (assistido) e só sobe com dados.
- **D-PROD-007 (RT/legal):** a empresa não tem RT habilitado (CREA/CRQ) → usar "Responsável pela Emissão" (nunca "RT"); a IA nunca afirma acreditação RBC/ISO 17025; Disclaimer A em todo certificado; certificado exige 2 conferências. Ver `mercado-regulatorio.md`.
- **D-PROD-008 (ritmo de implantação):** **1 agente por trimestre** — Roteador+Atendimento (ativos) → OS/Campo → Comercial → Financeiro/Estoque → Metrologia/CEO → Jurídico/Marketing. Não todos de uma vez. *(Revisto pelo **D-PROD-018** para o piloto — lá todos os agentes ligam juntos, em Nível 1; o ritmo de 1/trimestre passa a valer para a evolução/maturação pós-piloto.)*
- **D-PROD-009 (sistema-núcleo):** o ERP operacional a integrar é o **Aferê** (`Certificado de calibracao`), não o Kalibrium. A IA consulta/age sobre ele; nunca inventa dado operacional.
- **D-PROD-010 (parâmetros decididos pelo dono em 2026-05-28):** (a) orçamento/serviço **acima de R$ 10.000** → escala pro dono *(**revisto pelo D-PROD-019**: a IA monta o rascunho e manda o dono revisar, em vez de "nem rascunha")*; (b) aviso de prazo de calibração em **dois toques: 30 e 7 dias antes**; (c) anti-spam: **máx. 1 mensagem do mesmo assunto por cliente/semana** (com opt-out); (d) **auto-envio: nada sai sem aprovação por ora** — o que pode soltar (ex.: FAQ pura) será decidido **caso a caso** pelo dono no futuro.
  > Nota: os valores de (a)/(b)/(c) são o **default**; como tudo é **configurável por empresa** (D-PROD-011), cada tenant pode ajustar.
- **D-PROD-011 (modelo comercial, decidido pelo dono em 2026-05-28):** (a) **cobrança por faixa de porte** (espelha os perfis **A/B/C/D do Aferê**) **com franquia de uso de IA inclusa** + excedente se estourar muito; (b) vendida como **add-on na mesma fatura do Aferê**; (c) **mesmos perfis de empresa do Aferê (A/B/C/D)** — sem segmentação nova; (d) **configurável por empresa**: quais agentes ligar, parâmetros (limites/avisos/níveis), papéis e permissões por setor, canais e identidade.
- **D-PROD-012 (separação Aferê×IA + regras comerciais, 2026-05-28):** os **valores/preços moram no Aferê** (a IA consulta, nunca inventa — NF-004); a **IA carrega as regras de comportamento** (configuráveis por empresa). Regras default decididas: desconto que a IA sugere sozinha **≤ 3%** (acima escala; teto subiu de 2% para 3% por decisão do dono em 2026-05-29); prazo padrão de calibração **≤ 3 dias úteis**; pagamento padrão **transferência/à vista**; **deslocamento** a IA calcula sozinha (distância × R$/km, do Aferê). **O Auvo é só sistema legado (origem de migração) — a IA integra no Aferê, não no Auvo.** Detalhe e fonte real em [`regras-negocio.md`](./regras-negocio.md).
- **D-PROD-013 (áudio é capacidade CENTRAL — decidido pelo dono em 2026-05-28):** o atendimento real da
  Balanças Solution acontece **majoritariamente por ÁUDIO** no WhatsApp. Evidência dura: nas **5 conversas
  reais** analisadas há **1.120 mensagens de voz** (`.opus`) contra poucas mensagens de texto — cliente e dono
  **negociam, explicam tecnicamente e fecham negócio falando**, não escrevendo. Consequências de produto:
  (a) a IA **precisa transcrever áudio (speech-to-text) como capacidade central**, não opcional — entender o
  áudio do cliente e agir; (b) o **tom de voz da IA** é aprendido das **falas reais** do dono (não do texto, que
  é telegráfico); (c) há **custo de IA por minuto de áudio** transcrito, que entra na conta da assinatura (ver
  `riscos.md`/`metricas-chave.md`); (d) toda mensagem de voz ganha uma **etapa de transcrição** no pipeline antes
  de o cérebro/agentes entenderem. **Fonte:** `dados-reais/` (5 conversas) → corpus transcrito em
  `dados-reais/_transcricao/transcricoes.md`, gerado localmente (sem serviço pago) pela skill
  `transcrever-audio-whatsapp`. *(O tom de voz foi **consolidado em 2026-05-29**: 5 conversas com clientes 100% transcritas → `regras-negocio.md §6/§6.1` com perfil, frequências reais e lista "sempre/nunca dizer".)*
- **D-PROD-014 (arquitetura de conhecimento — levantada pelo dono em 2026-05-28):** o conhecimento NÃO pode ficar
  "jogado em pastas"; os agentes precisam de uma **base de conhecimento com BUSCA POR SIGNIFICADO** (busca
  semântica / RAG) — achar a informação certa pela **intenção**, não pela palavra exata. Requisitos do cérebro
  (reforça §4.2): (a) **busca semântica** sobre todo o acervo (manuais, transcrições, conhecimento do grupo);
  (b) **citação de fonte obrigatória** em toda resposta (anti-invenção, NF-004); (c) **isolamento multi-tenant**
  (a base de uma empresa não vaza pra outra); (d) **hierarquia de confiança das fontes** (manual oficial > Aferê >
  grupo > conversas); (e) **detecção de lacuna** (o que a IA não souber vira backlog de cadastro);
  (f) **classificação de acesso por audiência** (público-cliente × restrito-interno) — a resposta filtra pelo
  interlocutor: cliente externo só vê informação de uso; técnico/funcionário vê tudo (**D-PROD-016**, NF-009). **Separação de
  tipos de dado:** dado estruturado (preço, proposta, cliente) mora no **Aferê** e é consultado de forma exata
  (NF-004 / D-PROD-012); conhecimento não-estruturado (texto de manual/conversa) mora no **cérebro semântico**;
  os agentes usam os dois.
  > **Refinamento do dono (2026-05-29): o Aferê INTEIRO também é base de conhecimento da IA.** Todo o conteúdo do
  > Aferê (histórico de OS, certificados, orçamentos, conversas, configurações, documentação do ERP) entra no
  > cérebro **também como conhecimento indexado para busca por significado** — não só consulta pontual de registro.
  > O Aferê passa a ter **duplo papel**: fonte de **dado exato** (consulta pontual — preço, nº de série; NF-004) **e**
  > fonte de **conhecimento** (busca semântica sobre todo o histórico). Sempre respeitando **isolamento multi-tenant**
  > (uma empresa não vê o Aferê de outra) e **acesso por audiência** (D-PROD-016: cliente não acessa conhecimento interno).
  **Faseamento:** coletar + organizar a matéria-prima agora (transcrições, documentos,
  banco de preços) → a **escolha da tecnologia** do cérebro (qual índice/banco vetorial, embeddings, etc.) é
  **ADR na hora certa**, depois da descoberta fechar (não antecipar stack). O acervo que está sendo coletado
  (`dados-reais/`) é exatamente o insumo de carga inicial desse cérebro (Onda 0, H-012).
  > **Estado do acervo já coletado (2026-05-29):** **cérebro técnico com 1.099 fontes (~84 MB de texto)** —
  > 876 manuais (majoritariamente Toledo: IND780/IND560/WT3000/painel 9700/Prix), 143 procedimentos de
  > calibração, 7 tabelas de código de erro, **24 normas internacionais OIML** (R76 balanças, R111 pesos,
  > R60 células de carga, R134 pesagem rodoviária em movimento), **11 documentos Inmetro/IPEM** (VIM, GUM,
  > Portarias **157/2022** balanças e **289/2021** pesos) + guias Mettler Toledo. Índice em
  > `dados-reais/_banco/cerebro/INDICE-CEREBRO.md`. Métrica de saúde do cérebro: G-007. Riscos: R-017, R-018, R-020.
- **D-PROD-015 (banco de dados operacional pronto para migrar — 2026-05-29):** o legado **Auvo** foi
  exportado e estruturado em `dados-reais/_banco/`: **341 clientes, 389 produtos com preço, 80 serviços,
  429 orçamentos e 424 itens orçados reais** (pipeline de R$ 4,35 mi, ticket médio R$ 10.155, conversão de
  só 2,3% — o Auvo virou "cemitério de rascunho", o fechamento real é no WhatsApp, o que reforça a tese do
  produto). Esses dados são a base da **Onda −1** (migração Auvo→Aferê) e dão baseline para métricas e volume.
  Achados em `dados-reais/_banco/ACHADOS-AUVO.md`. **Confirma D-PROD-012**: a IA fica conservadora no desconto
  (≤3%) enquanto a prática humana real chega a 26% (decisão do dono: descontos grandes seguem com o Roldão).
- **D-PROD-016 (níveis de acesso ao conhecimento por audiência — decidido pelo dono em 2026-05-29):** o cérebro
  responde de forma **diferente conforme com quem fala** — controle de acesso ao conhecimento por interlocutor:
  - **Cliente final (externo, via WhatsApp)**: a IA **NÃO passa conhecimento técnico de acesso restrito**
    (procedimentos internos de calibração/manutenção, diagnóstico técnico profundo, códigos de erro internos,
    ajustes, parâmetros metrológicos, segredos de fabricante). Só fornece **informação de USO/operação da
    balança** (como o usuário opera o equipamento, dúvidas básicas) **+ os dados do próprio cliente** (suas OS,
    certificados, prazos, orçamentos). Pergunta técnica restrita de cliente → resposta de uso + oferta de serviço
    (ex.: "isso é manutenção, posso agendar um técnico?"), nunca o procedimento interno.
  - **Técnicos e funcionários (internos, autenticados)**: a IA orienta com **TODA a base de conhecimento**
    (cérebro completo: manuais, calibração, códigos de erro, procedimentos, normas) — é o **copiloto técnico** do time.
  - **Consequência para o cérebro (reforça D-PROD-014):** cada fonte/trecho do cérebro recebe uma **classificação
    de acesso** (público-cliente × restrito-interno); a resposta filtra pela audiência. A identidade do interlocutor
    (cliente externo × funcionário autenticado) define o nível. Operacionaliza NF-009.
- **D-PROD-017 (espelhar o Aferê no DADO, mas a IA faz MUITO MAIS — decidido/refinado pelo dono em 2026-05-29):**
  são dois lados que não se confundem:
  - **(espelho — para integrar)** No que é **dado e estrutura de negócio** (preços, R$/km, clientes, serviços
    comerciais como locação, parâmetros, faixas), a IA **espelha o que o Aferê tem disponível** e **não cria
    paralelo nem inventa dado operacional** (D-PROD-009/012). Ex.: R$/km **puxado do Aferê** quando configurado lá;
    locação (Onda V2) espelha o serviço como o Aferê o oferece. Fonte única da verdade, integração total.
  - **(muito mais — o valor da IA)** A **camada de IA NÃO se limita ao Aferê** — ela tem **muito mais coisa**:
    cérebro técnico (1.099 fontes), agentes por setor, transcrição de áudio, busca por significado, automação,
    diagnóstico técnico, aviso proativo de prazo, atendimento no WhatsApp e aprovação assistida. O Aferê **guarda
    e estrutura o dado**; a **IA entende, conversa, decide e age** sobre ele — e acrescenta capacidades que o Aferê
    não tem. Bate com D-PROD-005 (as ideias do dono são piso, não teto).
  > Regra prática: **dado/estrutura comercial → espelha o Aferê (não inventa); inteligência/automação/conhecimento
  > → camada de IA, livre para ir muito além.**
- **Nota comercial (resposta do dono 2026-05-29):** a **Balanças Solution usa a IA de graça durante o piloto/dogfooding**;
  só entra em faixa de cobrança (possivelmente especial) depois de validar. **Hospedagem (Brasil × fora):** decisão
  adiada para o **ADR de arquitetura** (sem preferência travada agora).
- **D-PROD-018 (piloto liga TODOS os agentes de uma vez — decidido pelo dono em 2026-05-29, ciente do risco):**
  o dono optou por **ativar todos os agentes simultaneamente no piloto** (dogfooding na Balanças Solution), em vez do
  ritmo "1 agente por trimestre" (revê o **D-PROD-008** para o contexto do piloto). O risco do "big-bang" (**R-001**,
  🔴: escopo "tudo de uma vez" trava o projeto; difícil isolar erros, configuração pesada, fila de aprovação) foi
  **explicado e aceito**. **Freios reforçados que
  tornam o risco aceitável:** (a) **TODOS entram em Nível 1** (100% do que vai ao cliente passa pela Inbox — ligar
  ≠ dar autonomia; nenhum agente é autônomo no dia 1); (b) **Inbox priorizada por motivo/urgência** para não afogar;
  (c) **cobaia é a própria empresa** (erro fica em casa, não em cliente pagante); (d) **métrica por agente desde o
  dia 1** para isolar quem precisa de ajuste; (e) **rollback de um agente** sem derrubar os outros. A **graduação de
  autonomia** (Nível 1 → mais autônomo) continua **gradual e por métrica de saúde**, agente a agente.
- **Decisões comerciais fechadas (dono, 2026-05-29):** ✅ **preço de venda aprovado** como ponto de partida
  (A R$1–1,4k · B R$550–750 · C R$300–450 · D R$180–280/mês — `estimativa-custo-viabilidade §4.1`); ✅ **custo fixo
  mensal ~R$ 5–15 mil** → **ponto de equilíbrio ~13–38 clientes** pagantes (provável 20–30). Refina no piloto.
- **D-PROD-019 (valor alto: a IA RASCUNHA, não "nem rascunha" — dono 2026-05-29):** revisa o D-PROD-010. Para
  orçamento/serviço **acima de R$ 10.000**, a IA agora **monta o rascunho completo** (preços do Aferê), marca
  **"valor alto — revisar com atenção"** e escala pro dono **revisar e aprovar** — em vez de não rascunhar. Motivo:
  adianta o trabalho (o dono não monta do zero) e o **freio continua sendo a revisão humana** (que já é universal,
  Nível 1). Em **cliente novo + valor alto**, confirmar dados antes de enviar. Atualiza as fichas em `agentes.md`.
- **D-PROD-020 (pedir humano / reclamar da IA → handoff IMEDIATO — dono 2026-05-29):** se o cliente disser qualquer
  coisa como **"quero falar com alguém / com humano / ser atendido por uma pessoa"**, ou **reclamar do atendimento
  da IA**, o agente **passa o atendimento imediatamente para um atendente humano** — sem insistir, sem tentar
  resolver sozinho, sem fila. Reforça o princípio-mãe (D-PROD-006) e o direito do CDC. Gatilho de prioridade alta
  na Inbox ("cliente pediu humano" / "reclamou da IA"). Aplicado nas fichas Roteador + Atendimento e no Exemplo 13.
- **D-PROD-021 (integração 100% ao Aferê via MÓDULO PRÓPRIO — dono 2026-05-29):** a camada de IA é **100%
  integrada ao Aferê** (fonte única da verdade, **sem base de dados paralela** — reforça D-PROD-009/017). A
  integração é **encapsulada num MÓDULO PRÓPRIO dedicado** (camada isolada / *anti-corrosion layer*): os agentes
  falam com esse módulo e **só ele** conversa com o Aferê — a integração **não fica espalhada** pelos agentes. **O
  DESENHO técnico** do módulo (contratos, API/DRF × banco × eventos, sincronização, auth) **é discutido na ETAPA
  CERTA do planejamento** — o **ADR-0001** (`docs/adr/ADR-0001-stack-e-integracao-afere.md`), hoje **congelado** até
  a descoberta fechar. Decisão de **princípio** agora (100% + módulo próprio); o **como** vem na hora certa, não antes.
- **D-PROD-022 (a IA OPERA o Aferê por completo, não só consulta — dono 2026-05-29):** pelo módulo de integração
  (D-PROD-021), a camada de IA pode **executar TODAS as operações** que o usuário precisar no Aferê — **abrir/editar
  orçamento, mexer na agenda, abrir/atualizar OS, cadastro, disparar fluxo de certificado, financeiro, etc.** É
  **read + write completo** (não é read-only). **Os freios de governança continuam intactos:** o que **vai ao cliente
  ou é irreversível passa pela aprovação humana** (Nível 1 — D-PROD-002/006); a IA grava **campo estruturado validado**
  (nunca texto livre de LLM em documento oficial/certificado); **cada agente só no seu domínio** (NF-005); certificado
  exige **2 conferências** (NF-001). Resumo: **capacidade ampla de operação no Aferê + governança humana preservada.**

- **D-PROD-023 (NOME DO PRODUTO = "Aferê Prumo" — escolhido pelo dono em 2026-05-29):** a camada de IA passa a se
  chamar **Aferê Prumo** (tagline: *"a IA que mantém sua operação no prumo"*). Escolhido por **auditoria de 5 agentes
  independentes** (4 de 5 votos) — "prumo" = precisão/equilíbrio do mundo da medição, marca própria e registrável,
  fácil de falar no interior. **Não confundir os três nomes:** **Aferê Prumo** = o **produto** (camada de IA, add-on);
  **Aferê** = o **ERP-núcleo** (Certificado de calibração); **Balanças Solution** = o **1º cliente** (empresa).
  Substitui o nome provisório "Balanças Solution IA" em toda a documentação. Marca pode exigir checagem de
  registro/domínio na hora certa (não bloqueia a descoberta).

## 10. Hipóteses críticas ainda não validadas

- H-001: a dor de atendimento justifica a Fase 1 — medir volume/tempo por 2 semanas.
- H-002: prazos perdidos custam receita recorrente — levantar prazos e perdas de 12 meses.
- H-004: a equipe adota e não volta pra planilha — piloto de 30 dias.

> Lista completa em [`hipoteses-a-validar.md`](./hipoteses-a-validar.md).

## 11. O que falta antes do GATE `stable`

> Checklist de pendências de C1. Todos os itens checked → status `stable`, C2 liberado.
>
> ✅ **Estado atual (2026-05-29): descoberta ENCERRADA.** O Roldão **declarou explicitamente o fim de C1**
> nesta data. Os 16 blocos abaixo estão preenchidos e fundamentados (auto-entrevista `EE-AUTO-001/002/003`
> + plano em `ideia roldao/` + 5 conversas reais transcritas + banco Auvo + cérebro de 1.099 fontes), e os
> números-chave foram confirmados (30 orçamentos/semana; 100% dos prazos perdidos). Esta síntese agora é
> `stable` e **libera a discussão de stack (C2 ADRs)**.
>
> ✅ **Nota de processo (resolvida 2026-05-29):** a fase-2 (`bootstrap-fase-2.sh`) e os ADRs
> (`docs/adr/ADR-0000/0001/0002`) tinham sido adiantados antes do fim da descoberta e ficaram **congelados**.
> Com o encerramento declarado pelo dono, estão **descongelados** — entram em discussão/aceitação normal.

- [x] `problema.md` em `stable`.
- [x] `personas.md` em `stable` — fundamentadas no dono (fonte). *Valida no piloto:* entrevistar cliente externo real (P-003).
- [x] `jornadas.md` em `stable` (J-001 principal + J-002 prazos + J-005 ciclo completo + J-006 rotina do dono).
- [x] `business-model-canvas.md` em `stable` (produto SaaS; receita por assinatura — D-PROD-011).
- [x] `value-proposition-canvas.md` em `stable`.
- [x] `concorrentes.md` em `stable` (diretos + indiretos + diferenciação).
- [x] `nao-fazer.md` em `stable` (10 NF + princípio-mãe).
- [x] `riscos.md` em `stable` (22 riscos com mitigação).
- [x] `metricas-chave.md` em `stable` (NSM + 7 guardrails + indicadores reais).
- [x] `gtm-pricing.md` em `stable` (pricing N/A na V1; é plano de implantação interna).
- [x] `restricoes.md` em `stable`. *Valida depois:* orçamento mensal em R$ (não bloqueia arquitetura).
- [x] `hipoteses-a-validar.md` em `stable` (H-001/H-002 confirmadas).
- [x] `glossario.md` em `stable` (24 termos do domínio).
- [x] `mercado-regulatorio.md` em `stable` (LGPD + RT/Responsável pela Emissão + Inmetro/RBC).
- [x] `dados-existentes.md` em `stable` (fontes: Aferê + planilhas + Drive).
- [x] `integracoes-externas.md` em `stable` (Aferê núcleo + 8 canais).

> **Valida no piloto (não bloqueia arquitetura):** tempo médio por orçamento; R$/ano de receita
> recorrente de calibração; satisfação do cliente; custo de IA por atendimento; adoção da equipe.

## 12. Próximo passo

✅ **Descoberta ENCERRADA pelo dono (2026-05-29) e síntese promovida a `stable`.** Fase C1 concluída.

Agora, fase **C2 — decisão de arquitetura (ADRs)**, já descongelada:
1. **ADR-0000 (uso de IA / LLM)** — confirmar provedor (Claude Haiku+Sonnet) + pseudonimização + DPA.
2. **ADR-0001 (stack + integração com o Aferê)** — decidir módulo dentro do Aferê × serviço vizinho em Python; **status `aceita` neste ADR libera o código** (phase-gate).
3. **ADR-0002 (multi-empresa + armazenamento do cérebro)** — isolamento por empresa (RLS) + onde guardar a busca por significado (pgvector × banco vetorial dedicado).
4. **Decisão de produto pendente do dono:** hospedagem dos dados (Brasil × fora) — implicação de LGPD, custo e confiança.

Em paralelo, ações formais do dono (não bloqueiam arquitetura): assinar AIPD, DPA com a Meta (WhatsApp),
ato de designação do Responsável pela Emissão.
