---
owner: roldao
revisado-em: 2026-05-28
status: stable
ordem-descoberta: 07/17
proximo: docs/descoberta/nao-fazer.md
idioma: pt-BR
limite-linhas: 200
proposito: análise de concorrentes diretos, indiretos e do "não-uso".
---

<!--
template: concorrentes.md
destino: docs/descoberta/concorrentes.md
uso: tabela comparativa + análise de mystery shopping (quando viável).
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3
limite: ≤200 linhas.
-->

# Concorrentes — Aferê Prumo

> **Contexto**: a IA é um **produto vendido por assinatura** (add-on do Aferê) a empresas de
> calibração. "Concorrente" = a alternativa que uma empresa-cliente poderia usar em vez de assinar a
> nossa IA. Para a 1ª cliente (Balanças Solution, dogfooding), o concorrente real ainda é o
> **status quo** (planilha + WhatsApp manual) — ver §2.

## 1. Concorrentes diretos (plataformas de "IA operacional" — comprar pronto vs construir)

> Pesquisa do dono (`ideia roldao/concorrentes.txt`). São as plataformas que poderíamos comprar
> em vez de construir. **Padrão comum**: todas são fortes em atendimento/CRM genérico e fracas
> (ou caras/complexas) para o domínio de **balanças, metrologia, certificados e campo técnico**.

| Concorrente | O que já entrega parecido | Onde fica fraco para o nosso caso |
|---|---|---|
| Salesforce + Agentforce + Service Cloud | CRM, atendimento, agentes de IA, automação, governança, dados centralizados | Caro, complexo, não vem pronto para metrologia/certificado/balanças |
| Microsoft Dynamics 365 + Copilot Studio | Forte no ecossistema Microsoft 365/Teams/Power BI; agentes e workflows | Precisa customizar muito para virar "ERP de calibração com IA" |
| ServiceNow + Now Assist | Excelente em workflow, field service, aprovações, auditoria | Voltado a grandes empresas; custo e implantação pesados |
| Zendesk AI Agents | Forte em atendimento omnichannel, tickets, base de conhecimento | Fraco em operação técnica, estoque, OS, certificado, ERP |
| Intercom + Fin AI | Bom atendimento omnichannel com IA e handoff humano | Mais suporte/SaaS do que ERP operacional |
| Freshdesk + Freddy AI | Atendimento, agentes no-code, auditoria, controle de acesso | Limitado para metrologia e campo técnico complexo |
| HubSpot + Breeze | CRM, vendas, marketing, atendimento | Mais comercial; não é infraestrutura operacional profunda |
| Zoho One + Zia | Ecossistema amplo (CRM, atendimento, financeiro, IA) | "Quase tudo", mas IA mais fraca que Salesforce/MS/ServiceNow |
| UiPath / Automation Anywhere | Fortes em automação/RPA com humano-na-aprovação | Camada de automação, não CRM/ERP pronto |

> **Dois grupos com limites diferentes** (vem pronto **vs.** segue sendo nosso = miolo metrológico-legal):
> - **Atendimento/CRM** (Salesforce, Zendesk, Intercom, Freshdesk, HubSpot, Zoho): vem pronta a
>   pergunta-resposta genérica; **não vem** equipamento como entidade, certificado, prazo por equipamento.
> - **Orquestração/RPA** (UiPath, Automation Anywhere): automatizam um processo e um sistema-de-registro
>   que **já existem** — não criam a organização do zero nem conhecem o domínio. O miolo (Aferê +
>   metrologia + regra legal de RT) segue sendo **nosso** em ambos os grupos.

## 2. Concorrentes indiretos

| Alternativa | Como resolve hoje | Por que pode bastar | Por que a IA vence |
|---|---|---|---|
| Planilha + WhatsApp (status quo) | Tudo manual | Custo zero, já conhecem | Não lembra prazo, não responde sozinho, informação espalhada |
| Contratar mais gente | Mais braços no atendimento | Resolve volume sem mudar processo | Custo recorrente alto; não resolve prazo/organização |
| Não fazer nada | Mantém como está | Inércia ("tá funcionando") | Continua perdendo tempo e prazo — gatilho: a dor já incomoda o dono |

## 3. Mystery shopping (quando viável)

> Para cada concorrente direto, registrar: trial feito, fluxo testado, screenshots, fricções observadas.

### <Concorrente 1>
- Data do teste: 2026-05-28
- Quem testou: <nome>
- Plano testado: <free/trial/pago — R$/mês>
- Fluxo testado: <ex.: cadastro → import CSV → primeiro relatório>
- Fricções observadas: <bullets>
- Pontos positivos: <bullets>
- Screenshots: `docs/descoberta/mystery-shopping/<concorrente1>/` (se aplicável)

### <Concorrente 2>
[mesmo formato]

## 4. Diferenciação clara do Aferê Prumo

> Análise dos 10 concorrentes (workflow 2026-05-28) mostrou que o diferencial NÃO é "conhece balanças"
> genérico — são **quatro eixos duros** que nenhum genérico cruza:

- **Eixo 1 — FILOSOFIA (aprovação humana como propósito):** todos os 10 otimizam **deflexão autônoma** (a IA resolve sozinha; vendem "X% resolvido sem humano" como troféu). Num domínio regulado (certificado, CDC, responsabilidade legal) o troféu é o oposto: **nada vinculante sai sem gente**. Nosso "tudo passa pela Inbox" (D-PROD-006) é argumento de **confiança e conformidade**, não limitação.
- **Eixo 2 — DADO (equipamento vivo, não FAQ/contato):** todo CRM/atendimento gira em torno de contato/negócio/ticket ou artigo de FAQ. Nós respondemos sobre **ESTE equipamento** (nº de série, última OS #892, próximo prazo) consultando o **Aferê em tempo real**. Fronteira que nenhum genérico atravessa.
- **Eixo 3 — DOMÍNIO metrológico-legal embutido:** certificado com 30+ campos, 2 conferências, peso padrão com validade, Disclaimer A, proibição de afirmar RBC/ISO 17025, "Responsável pela Emissão". Os 10 têm **zero** disso nativo — viraria customização cara.
- **Eixo 4 — AVISO PROATIVO por equipamento+norma:** o mercado avisa "renovação de **contrato** por data" e opera reativo-por-ticket; nós avisamos **vencimento de calibração por equipamento, antes de qualquer contato**, com o risco de o cliente ficar fora de norma. Como o dono perde 100% dos prazos (H-002), é o diferencial de maior valor financeiro.
- *Bônus:* operável por **não-programador numa PME de 9 pessoas** (vs. implantação enterprise com time de TI) e **integração nativa com o Aferê** (não RPA frágil por cima de sistema fechado).

## 5. Riscos competitivos

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| **Buy-vs-build do atendimento** (R-009): helpdesk/CRM pronto resolve a pergunta-resposta "bom o suficiente", barato e rápido | A | M | Ancorar valor nos ~20% insubstituíveis (Aferê, certificado, prazo por equipamento, campo offline, RT); os ~80% genéricos são comoditizáveis |
| **Zoho One** (barato/usuário + governança + campo offline) e **Microsoft** (inércia "já tenho M365, é só ligar o Copilot") | M | M | Diferencial de domínio + custo proporcional; medir adoção real |
| **Comoditização rápida** da camada "agente + aprovação + auditoria" (12-18 meses) | A | M | Fosso = domínio metrológico + fonte de verdade própria (Aferê) + conformidade BR — nunca "temos agentes" |
| **Inveja de funcionalidade** (ver concorrente resolver sozinho pressiona a acelerar além do Nível 1) | M | A | Graduar só por métrica de saúde do agente, nunca por comparação |
| **Fragmentação da verdade** (CRM/suite externa vira 2º dono do dado, esvazia o Aferê) | M | A | Fonte da verdade é ÚNICA = Aferê; nunca dividir com plataforma externa |
| Provedor de IA muda preço/regra | M | M | Camada de adaptação (R-006) |

> **Risco inverso (a favor):** para 9 pessoas sem TI, o custo/complexidade das suites enterprise é tão alto que o concorrente real continua sendo o **não-uso (planilha + WhatsApp)**. Não desviar o foco do piloto enxuto da Onda 1 comparando com Salesforce/ServiceNow.

## Critério para promover de `draft` para `stable`

- [ ] ≥3 concorrentes diretos listados (ou justificativa em `nao-aplica.md` se mercado vazio).
- [ ] ≥2 concorrentes indiretos listados (incluindo "não fazer nada").
- [ ] ≥1 mystery shopping concluído OU motivo de não fazer documentado.
- [ ] Diferenciação tem ≥2 bullets concretos (não "mais fácil de usar" sem qualificar).
