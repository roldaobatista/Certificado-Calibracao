---
owner: roldao
revisado-em: 2026-05-29
status: stable
ordem-descoberta: 03/17
proximo: docs/descoberta/business-model-canvas.md
idioma: pt-BR
limite-linhas: 250
proposito: fluxos ponta-a-ponta do usuário HOJE (sem produto) e DEPOIS (com produto).
---

<!--
template: jornadas.md
destino: docs/descoberta/jornadas.md
uso: 3-7 jornadas, 1 página por jornada. Marca momentos de DOR e DELIGHT.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3
limite: ≤250 linhas. Se passar, fatiar em docs/descoberta/jornadas/<slug>.md.
-->

# Jornadas — Aferê Prumo

> Cada jornada amarra uma persona (`P-NNN`) a um fluxo concreto. Tempos marcados
> `(est.)` são estimativa provisória do dono — números reais em `hipoteses-a-validar.md`.
>
> ⚠️ **Nota de status (auditoria 2026-05-29):** `status: stable` aqui = "fluxo definido e fundamentado", NÃO
> "custos de hoje medidos". O critério de promoção pede tempos/custos do "hoje" quantificados — vários ainda
> estão `(A VALIDAR)`. **Pendência: cronometrar 2 semanas reais de atendimento/orçamento no piloto** (H-001)
> para fechar os números. Jornadas J-004/J-007/J-008 são esboços a detalhar quando suas frentes forem priorizadas.

## J-001 — Atendimento + orçamento pelo WhatsApp — P-001 (Carla) / P-003 (cliente)

> **Canal real = majoritariamente ÁUDIO (D-PROD-013).** No "depois", todo áudio passa **primeiro pelo
> Agente de Transcrição** (voz→texto + score de confiança; ver `agentes.md`) antes do Roteador entender.
> Se a transcrição tiver baixa confiança, a IA confirma em texto com o cliente antes de agir (R-016).

### Hoje (sem o produto)

| Passo | O que a persona faz | Quanto tempo | Dor? |
|---|---|---|---|
| 1 | Cliente manda mensagem; entra na fila de várias conversas | — | 🔴 cliente espera resposta |
| 2 | Carla lê, entende o pedido, pergunta detalhes (modelo, capacidade, serviço) | 5-10 min (est.) | — |
| 3 | Busca preço/modelo em planilha ou pergunta pra outra pessoa | 10-20 min (est.) | 🔴 informação espalhada |
| 4 | Monta orçamento do zero e responde | 10-15 min (est.) | 🔴 retrabalho a cada pedido |

**Total hoje**: ~30-45 min por orçamento (est.); volume `(A VALIDAR)`.

**Momentos de dor**:
- 🔴 Mesmas perguntas repetidas o dia todo.
- 🔴 Orçamento refeito do zero, sem modelo nem histórico.

### Depois (com o produto)

| Passo | O que a persona faz | Quanto tempo | Delight? |
|---|---|---|---|
| 1 | IA recebe a mensagem, entende o pedido e responde dúvidas comuns sozinha | instantâneo | 🟢 cliente respondido na hora |
| 2 | IA já puxa modelo/preço e monta rascunho de orçamento | segundos | 🟢 sem caçar informação |
| 3 | Carla revisa e aprova (ou ajusta) o orçamento | 2-3 min (est.) | 🟢 só revisa, não cria do zero |

**Economia**: maior parte do tempo de atendimento repetitivo + redução de fila. Valor `(A VALIDAR)`.

**Momentos de delight**:
- 🟢 Cliente respondido em segundos, a qualquer hora.
- 🟢 Atendente vira revisor, não digitador.

### Risco da migração
- IA responder errado preço/escopo → precisa de revisão humana antes de fechar e base de preços confiável.
- Equipe confiar/adotar o canal novo.

---

## J-002 — Agendamento e aviso de prazo de calibração — P-002 (Jorge) / P-003 (cliente)

### Hoje (sem o produto)

| Passo | O que a persona faz | Quanto tempo | Dor? |
|---|---|---|---|
| 1 | Calibração é feita; próximo prazo fica na memória/planilha | — | 🔴 sem alarme |
| 2 | Ninguém acompanha o vencimento ativamente | — | 🔴 prazo passa despercebido |
| 3 | Cliente percebe tarde (ou um fiscal percebe) e cobra | dias/semanas | 🔴 perda de contrato / fora de norma |

**Total hoje**: **0% dos prazos controlados → 100% perdidos** (confirmado pelo dono). Toda renovação depende do cliente lembrar.

**Momentos de dor**:
- 🔴 Não há controle de prazo nenhum — vence sem que ninguém saiba.
- 🔴 Receita recorrente de recalibração deixada na mesa; cliente fica fora de norma.

### Depois (com o produto)

| Passo | O que a persona faz | Quanto tempo | Delight? |
|---|---|---|---|
| 1 | Ao registrar a calibração, o sistema agenda o próximo prazo automaticamente | instantâneo | 🟢 nada fica na memória |
| 2 | IA avisa cliente e equipe **30 dias** e de novo **7 dias** antes do vencimento e propõe reagendar | automático | 🟢 aviso proativo (2 toques) |
| 3 | Cliente confirma; serviço entra na agenda do técnico | minutos | 🟢 renovação sem esforço |

**Economia**: prazos deixam de vencer sem aviso → receita recorrente preservada. Valor `(A VALIDAR)`.

**Momentos de delight**:
- 🟢 Cliente é avisado antes — vira diferencial de confiança.
- 🟢 Renovação de calibração vira fluxo automático.

### Risco da migração
- Precisa da data da última calibração e do prazo de cada equipamento (cadastro inicial).
- Não exagerar nos avisos (evitar spam ao cliente).

---

## J-003 — Ordem de serviço de manutenção com histórico — P-002 (Jorge)

### Hoje (sem o produto)

| Passo | O que a persona faz | Quanto tempo | Dor? |
|---|---|---|---|
| 1 | Recebe chamado de conserto sem o histórico do equipamento | — | 🔴 chega sem contexto |
| 2 | Faz o serviço e anota OS no papel | durante o serviço | 🔴 papel se perde |
| 3 | OS volta incompleta; peça/garantia sem registro confiável | depois | 🔴 informação perdida |

**Momentos de dor**:
- 🔴 Sem histórico → diagnóstico mais lento e erro.
- 🔴 OS em papel some ou volta incompleta.

### Depois (com o produto)

| Passo | O que a persona faz | Quanto tempo | Delight? |
|---|---|---|---|
| 1 | Abre o equipamento no celular e vê todo o histórico | segundos | 🟢 contexto na mão |
| 2 | Preenche a OS guiada no próprio celular | durante o serviço | 🟢 sem papel |
| 3 | Histórico, peça e garantia ficam registrados automaticamente | instantâneo | 🟢 nada se perde |

**Economia**: menos retrabalho e diagnóstico mais rápido. Valor `(A VALIDAR)`.

**Momentos de delight**:
- 🟢 Técnico chega sabendo a história do equipamento.

### Risco da migração
- Cadastrar a base inicial de equipamentos e histórico.
- App simples o suficiente para uso em campo (P-002 tem fluência média-baixa).

---

## J-004 — Locação de balança (ciclo de aluguel) — P-001 / P-003

> Esboço enxuto — **Onda V2** (decisão do dono 2026-05-29). A regra de locação **espelha o que o Aferê
> oferecer** (D-PROD-017): preço, duração, multa e devolução virão do que o Aferê tiver configurado, não de
> tabela própria da IA. Detalhar quando a frente for priorizada e o Aferê expuser a locação.

### Hoje
- Pedido de locação por WhatsApp; disponibilidade e prazo controlados manualmente; devolução e cobrança sem acompanhamento central. 🔴 risco de equipamento esquecido em cliente / cobrança perdida.

### Depois
- IA registra o pedido, checa disponibilidade, agenda entrega/retirada e acompanha prazo de devolução e cobrança. 🟢 ciclo de locação rastreado de ponta a ponta.

**Tempos e valores**: `(A VALIDAR)`.

## J-005 — Ciclo completo "do oi ao certificado" — P-003 / P-001 / P-002 / P-C-001

> Exemplo real do plano do dono (apresentação). Mostra o sistema maduro; cada passo crítico tem humano.

| Quando | O que acontece | Quem decide |
|---|---|---|
| Seg 09:14 | Cliente manda WhatsApp ("balança da fazenda oscilando") | — |
| Seg 09:14 | IA classifica (suporte técnico) e busca no Aferê: cliente + OS #892 (mesma falha mar/2024) | IA |
| Seg 09:14 | IA prepara resposta + chamado pré-preenchido | IA |
| Seg 09:16 | Roldão abre a Inbox, lê e **aprova** (2 min após o cliente) → vira OS #1104 | 🟠 humano |
| Seg 09:17 | OS cai no app do técnico (Jorge, P-002): cliente, local, histórico, checklist, peças prováveis | IA |
| Ter 08:30 | Jorge executa **offline**: checklist, 3 fotos, marca peça, cliente assina na tela | técnico |
| Ter 11:45 | App sincroniza; Estoque baixa a peça; Metrologia começa a conferir | IA |
| Ter 11:46 | Metrologia **bloqueia**: peso padrão 500kg vencido | IA (bloqueio) |
| Ter 14:20 | Peso atualizado; Roldão revisa certificado (30 campos), preenche incerteza, assina (5 min) | 🟠 humano |
| Qua 09:00 | OS faturada → **Aferê** gera NFS-e + boleto (a IA opera); cliente recebe boleto + certificado | IA |
| +2 semanas | Painel de gestão: margem do cliente +8%, retrabalho zerou, virou indicação | IA (análise) |

**O que esse ciclo elimina**: 3 ligações atendente↔técnico, 1 ligação de cobrança do cliente, risco de certificado com peso vencido, despesa esquecida do técnico, boleto que demoraria 3 dias.

> **J-005 como PROCESSO (máquina de estados), não tabela linear:** cada passo tem um tipo —
> *decisão-de-IA* (probabilística, sempre sugere) · *passo determinístico conferível* · *aprovação
> humana EDITORIAL* (revisar o texto ao cliente) · *bloqueio técnico/irreversível*. O processo
> **trava sozinho** na etapa obrigatória: a OS **não fatura** e o certificado **não emite** enquanto
> as 2 conferências + peso padrão válido não forem cumpridos. Na **exceção** (timeout, rejeição, dado
> não achado no Aferê) → volta pro humano. São **dois checkpoints humanos**: editorial (texto) +
> bloqueio (irreversível) — orquestradores genéricos só têm o bloqueio.
> **Regra de gravação:** nenhum dado vai ao Aferê/certificado como texto livre de LLM — vai como
> **campo estruturado validado, com a fonte registrada** (reforça NF-004 com mecanismo, não só princípio).

## J-006 — Rotina do dono (15–30 min/dia) — P-C-001 (Roldão)

- **07:30** — recebe **Resumo Matinal** no WhatsApp: nº de mensagens, atendimentos resolvidos, quantos aguardam, custo de IA do mês, pontos de atenção (ex.: "cliente X 3ª vez na semana"). Não dispara se a noite teve 0 atividade.
- **Manhã** — abre a **Inbox de Aprovação**, navega por teclado (J/K), aprova o que está claro, edita o duvidoso. Zera a fila em 15–20 min (tempo médio por item ~42s).
  - **Recursos da Inbox** (lição dos concorrentes): **resumo do caso** ao abrir o item (o que o cliente pediu, o que a IA achou no Aferê, por que sugeriu) — não a conversa inteira; **indicador de confiança** por item para **ordenar a fila** (baixa confiança / assunto sensível sobe); aprovar/editar/rejeitar **em lote**; **reatribuir/delegar** para as 2 pessoas do escritório (respeitando permissão por setor) quando o Roldão está em campo.
- **Quando edita** — a IA aprende: corrigiu a mesma coisa 3× em 14 dias → ela propõe virar regra (modo teste → "gradua" com ≥80% de aceite). Tela "Minhas Regras" mostra ativas/aprendendo e deixa desativar em 30s. **Caminho proativo** (além do reativo): o dono escreve uma política em português comum ("nunca prometa prazo < 3 dias", "sempre ofereça calibração junto da manutenção") e a IA passa a obedecer, com teste antes de ativar.
- **Cockpit de Governança de IA** (uma tela só): todos os agentes ativos, o que cada um pode/não pode, nível de automação atual de cada um, custo acumulado no mês e **botão de desligar (kill-switch)**.
- 🟢 **Delight**: o dono deixa de ser gargalo — a operação anda mesmo quando ele está em campo/reunião.

## J-007 — Entrada de uma empresa-cliente que assina o SaaS (onboarding B2B) — P-CL-001/002/003

> Lacuna apontada pela auditoria: as personas das empresas pagantes (perfis A/B/C/D) existiam sem jornada. Esboço — detalhar com o dono.

### Hoje
- Não existe — o produto ainda não foi aberto comercialmente (dogfooding na Balanças Solution).

### Depois (empresa-cliente assinante)
| Passo | O que acontece | Quem |
|---|---|---|
| 1 | Empresa assina o **add-on de IA** na fatura do Aferê (D-PROD-011) | cliente |
| 2 | **Migração** dos dados do legado para o Aferê (Onda −1), se houver | IA + suporte |
| 3 | **Configuração por empresa**: liga agentes, define perfil A/B/C/D, parâmetros (limiares, avisos), papéis/permissões, identidade/tom | humano (papel de configuração — não é agente) |
| 4 | **Carga do cérebro** (Onda 0) com o acervo da empresa (manuais, histórico) | IA + conferência |
| 5 | Piloto assistido 30 dias; mede TTFV, adoção, margem por tenant | dono da empresa |

**Riscos**: complexidade de onboarding (R-014); margem por tenant (R-012). **Validar**: H-014, H-015. **Tempos/valores**: `(A VALIDAR)`.

## J-008 — Motorista: entrega/retirada (locação e equipamentos) — P-004 (motorista)

> Lacuna: P-004 (motorista) não tinha jornada nem agente dono da agenda/rota. Esboço.

### Hoje
- Rota e entregas/retiradas combinadas de forma solta (WhatsApp/telefone); sem coordenação central; 🔴 risco de equipamento esquecido em cliente e rota ineficiente.

### Depois
- Um agente de **Logística/Agenda** (ou extensão do OS/Campo) sugere **rota e ordem de entregas/retiradas** (entrega de locação, coleta de devolução, transporte de peso padrão); o coordenador aprova; motorista recebe a lista no celular; baixa/confirma cada parada. 🟢 rota coordenada, nada esquecido.

**Decisão pendente do dono**: o dono da agenda do motorista é o OS/Campo estendido ou um agente novo de Logística? **Tempos/valores**: `(A VALIDAR)`.

## J-009 — Emissão de certificado de calibração (2 conferências) — P-002 / Responsável pela Emissão

> Lacuna: o fluxo de emissão (passo crítico regulado) não tinha jornada própria, só aparecia dentro de J-005.

| Passo | O que acontece | Quem | Trava |
|---|---|---|---|
| 1 | Calibração executada; dados de medição registrados | técnico (P-002) | — |
| 2 | IA monta o rascunho do certificado (30+ campos) consultando o Aferê + cérebro; **cita fonte** | IA | não emite sozinha (NF-001) |
| 3 | **1ª conferência (Metrologia)**: confere medições, peso padrão válido, incerteza | IA bloqueia se peso padrão vencido | bloqueio técnico |
| 4 | **2ª conferência + assinatura**: Responsável pela Emissão revisa, preenche incerteza, assina | 🟠 humano | Disclaimer A obrigatório (NF-003) |
| 5 | Certificado liberado ao cliente + registro auditável | IA | — |

**Regra**: nunca afirmar acreditação RBC/ISO 17025 nem usar "RT" (D-PROD-007, NF-003); 2 conferências são **obrigação legal**, não boa prática. **Pendência**: penalidades do Inmetro/IPEM e responsável legal → `mercado-regulatorio.md`.

## Padrões transversais (reaproveitáveis em várias jornadas)

- **Motor "prazo + alarme + escalonamento"** — **DECISÃO (2026-05-29): é um COMPONENTE de infraestrutura**
  (não um agente), genérico e reutilizável: prazo de calibração (J-002), devolução de locação (J-004), tempo de
  1ª resposta ao cliente, item mais antigo na Inbox. **Dono da notificação**: o componente dispara o alerta e o
  **agente Comercial recebe** o aviso de vencimento de calibração (30 e 7 dias — D-PROD-010) para propor
  reagendamento; o **OS/Campo** recebe o de devolução de locação. Resolve a lacuna "motor de prazo sem dono".
  Não reconstruir três vezes.
- **Operação da Inbox (fila de aprovação) — defaults (2026-05-29, configuráveis por empresa):**
  - **Prazo de 1ª resposta por tipo**: dúvida rápida/FAQ ≤ 15 min · orçamento ≤ 1 h · emergência (balança parada/fiscal) ≤ 5 min · assunto regulado ≤ 1 h. Ao estourar → realça e realarma.
  - **Fila cheia**: acima de **N itens** (default 30) ou item parado além de **X h** (default 2 h) → alerta o dono e **reprioriza** (confiança baixa / sensível / antigo sobem).
  - **Cobertura na ausência do dono**: as **2 pessoas do escritório** assumem a Inbox por **delegação/reatribuição** (respeitando permissão por setor); o que só o dono aprova (desconto grande, valor > R$ 10k) **espera** ou vai para um aprovador designado.
  - **Limiar fila × despacho direto**: tudo que vai ao cliente passa pela Inbox por ora (D-PROD-010); o que pode despachar direto (FAQ pura) só com decisão caso a caso do dono e métrica de saúde alta (H-006).
- **Ordem de prioridade da Inbox (2026-05-29) — pra 2 pessoas não se afogarem.** O dono é (com razão) cauteloso e a IA escala bastante coisa pra confirmação humana; sem ordem, a fila vira gargalo (liga a H-016/R-002). A IA **entrega a fila pré-priorizada** assim (do topo pra baixo):

  | Ordem | Tipo de item | Por quê | Alvo |
  |---|---|---|---|
  | 1 🚨 | **Emergência** (balança parada, fiscal no local) | prejuízo imediato do cliente | ≤ 5 min, notifica celular |
  | 2 🔴 | **Cliente irritado / ameaça** (Procon, cancelar) | risco de perder cliente/reputação | minutos |
  | 3 🔴 | **Cliente pediu humano / reclamou da IA** (D-PROD-020) | direito do cliente + CDC | minutos |
  | 4 🟠 | **Decisão de margem** (desconto > teto, valor > R$ 10k) | só o dono decide | mesmo dia |
  | 5 🟠 | **Prazo estourando** (SLA 1ª resposta, calibração vence hoje) | não deixar cliente no vácuo (vai pro concorrente) | dentro do SLA |
  | 6 🟡 | **Rascunhos de rotina** (orçamento, resposta, follow-up, agendamento, cobrança) | fluxo normal, aprovar em sequência | dentro do SLA do tipo |
  | 7 ⚪ | **Informativos / baixo risco** (status, FAQ, pós-serviço) | candidatos a aprovar em lote / soltar quando amadurecer | quando der |

  - **Como a IA alivia a fila (não só prioriza):** (a) **pré-prioriza** e mostra o **motivo + contexto pronto** (a pessoa não investiga, só decide); (b) **agrupa itens iguais** (ex.: 5 follow-ups) pra **aprovar em lote**; (c) **resume cada item em 1 linha** (decisão em ~42s); (d) **SLA visível** — o mais urgente/antigo realça, nada "esquecido"; (e) **cobertura**: dono em campo → as 2 do escritório assumem; emergência/irritado tocam o **celular**; (f) **graduação**: categorias de **baixo risco e alta aprovação-sem-edição** (status, FAQ) podem, por decisão do dono, **soltar sozinhas** (com amostragem) — aliviando a fila sem perder controle.
  - **Métrica de saúde da fila (piloto):** itens/dia por pessoa, tempo médio de aprovação, % aprovado-sem-edição, idade do item mais antigo. Se a fila crescer além do que 2 pessoas vencem no SLA → sinal para **soltar mais categorias de baixo risco** ou **reforçar equipe** (decisão do dono).
- **Guardrail de frequência de aviso ao cliente (anti-spam)**: nº máximo de mensagens proativas por
  cliente/período, com opt-out e supressão (ver `metricas-chave.md`). Aviso sem governança de
  frequência queima a confiança — o oposto do nosso diferencial.

## Jornadas fora do escopo (V1)

- Revenda da plataforma de IA para outras empresas de balança (multi-empresa) — visão futura, não V1.
- Integração contábil/fiscal (NF-e) — avaliar depois da fundação; depende de ADR e regulação.
- Previsão de demanda / relatórios analíticos avançados — Fase posterior (depende de dados acumulados).

## Critério para promover de `draft` para `stable`

- [ ] Cada jornada tem coluna "tempo" preenchida com número concreto.
- [ ] Pelo menos 1 dor por jornada (sem dor, não é jornada relevante).
- [ ] Pelo menos 1 delight no fluxo "depois" — produto sem delight é commodity.
- [ ] Custos do "hoje" quantificados em R$ ou horas.
