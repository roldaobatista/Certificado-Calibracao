---
owner: roldao
revisado-em: 2026-05-29
status: stable
ordem-descoberta: 01/17
proximo: docs/descoberta/personas.md
idioma: pt-BR
limite-linhas: 100
proposito: definir a dor real, quem sente, evidências e custo atual antes de qualquer decisão técnica
---

<!--
template: descoberta/problema.md
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C1
tamanho-alvo: 1-3 páginas
-->

# Problema — Aferê Prumo

## A dor

A Balanças Solution opera quatro frentes simultâneas — **venda**, **manutenção/assistência
técnica**, **calibração/aferição com selo (Inmetro/IPEM/RBC)** e **locação** de balanças.
Cada frente gera atendimento, orçamento, agendamento, execução e acompanhamento de prazo.
Hoje tudo isso é tocado de forma majoritariamente manual: atendimento por WhatsApp solto,
orçamentos refeitos do zero a cada pedido, controle de prazos de calibração/garantia/contrato
na memória ou em planilha, e informação de clientes/equipamentos espalhada. O efeito visível
é tempo perdido respondendo as mesmas coisas, retrabalho, e prazo de calibração que só é
lembrado quando já passou — o que custa contrato e credibilidade junto ao cliente.

A dor não é de um processo só: ela é **transversal** às quatro frentes e a dois públicos
(equipe interna e cliente final). Por isso a visão do dono é construir uma **infraestrutura
de IA** — um "cérebro" único + **agentes por setor** (atendimento, comercial, OS/campo,
metrologia, financeiro, estoque, jurídico, marketing, gestão) que consultam o sistema real da
empresa e agem com aprovação humana — e não um chatbot isolado.

**A dor central (a mais aguda):** hoje **a operação trava no dono**. A resposta ao cliente
depende do tempo do Roldão estar disponível; crescer significa contratar mais gente na mesma
proporção; e o conhecimento do negócio mora na cabeça das pessoas, não no sistema. A IA existe
para **destravar o dono** e permitir escalar atendimento e operação sem aumentar a equipe na
mesma proporção.

EE-AUTO-001/002 (auto-entrevista do dono + plano detalhado em `ideia roldao/`, registrados em
[`auto-entrevista.md`](./auto-entrevista.md)): sustentam as quatro frentes do negócio, a visão
ampla de IA (cérebro + agentes), o público duplo (interno + cliente) e as dores abaixo. O
sistema operacional é o **Aferê** (ERP de calibração em construção): a camada de IA é **100% integrada
a ele, por um módulo próprio de integração** (D-PROD-021), e **opera tudo que o usuário precisar** —
consultar **e** abrir orçamento, mexer na agenda, abrir OS, cadastro etc. (D-PROD-022), sempre com
aprovação humana no que vai ao cliente. O **como** técnico da integração é definido na etapa certa
(ADR-0001). Ver [`integracoes-externas.md`](./integracoes-externas.md).

> Evidência atual = auto-entrevista do dono (`EE-AUTO-001`). Faltam conversas registradas
> com clientes reais para confirmar a dor pelo lado de fora — listadas em
> [`hipoteses-a-validar.md`](./hipoteses-a-validar.md).

## Quem sente
- **Equipe de atendimento/comercial** (usuário interno): responde cliente e monta orçamento o dia todo. Sente a dor de tempo e repetição.
- **Técnico de calibração/manutenção** (usuário interno): executa serviço e precisa do histórico do equipamento; sofre com informação espalhada e prazo descontrolado.
- **Gestor / dono — Roldão** (usuário interno + comprador): é o **gargalo** — a operação depende dele estar online; não consegue enxergar o todo (demanda, prazos, contratos) nem garantir que nada vence sem aviso.
- **Cliente da Balanças Solution** (usuário externo): quer resposta rápida, orçamento na hora e ser avisado antes do prazo de calibração vencer — não depois.
- *Usuário ≠ comprador:* o **comprador é o Roldão** (dono); os usuários são a equipe e os clientes.

## Quanto custa hoje
- **Tempo:** ~50 atendimentos/semana, dos quais **~30 são orçamento** montado manualmente, absorvendo as 2 pessoas do escritório. Tempo médio por orçamento `(valida no piloto)`.
- **Dinheiro/risco (o mais grave):** o dono **não controla nenhum prazo de calibração → perde 100%**. Toda renovação depende de o cliente lembrar. A receita recorrente de recalibração está, na prática, deixada na mesa — e o cliente fica fora de norma sem aviso.
- **Risco operacional + dono-gargalo:** a operação trava no Roldão (resposta depende do tempo dele); informação de cliente/equipamento espalhada → erro, retrabalho e conhecimento na cabeça das pessoas, não no sistema.
- **Evidência nos dados reais (2026-05-28, exports do Auvo — ver [`regras-negocio.md`](./regras-negocio.md)):** dos **429 orçamentos** (acumulado histórico no Auvo), a maioria está em "Rascunho/Aberto" e **muitos venceram sem nenhum follow-up** (propostas vencidas há 34, 56, 240, até 350 dias). É a prova concreta de **orçamento parado / sem acompanhamento** — receita que morreu na gaveta. Base: 341 clientes, 389 produtos cadastrados.

## Por que solução existente não resolve
- **Planilha + WhatsApp (status quo):** não lembra prazo sozinho, não responde cliente, não cruza informação. Cada pessoa tem sua versão.
- **CRM/ERP genérico:** organiza cadastro, mas não atende cliente em linguagem natural nem entende o domínio de balanças (calibração, selo, RBC). Caro de configurar e ninguém preenche.
- **Chatbot de WhatsApp pronto (fluxo fixo):** responde FAQ, mas não monta orçamento real, não conhece o histórico do equipamento e não automatiza o interno.

## Validações pendentes
- Números de volume e tempo (atendimentos, orçamentos, calibrações, equipe, base de clientes) — todos `(A VALIDAR)`.
- Confirmar a dor pelo lado do cliente externo com ≥3 conversas reais.
- Todas movidas para [`hipoteses-a-validar.md`](./hipoteses-a-validar.md) com critério de validação.

## Critério para promover de `draft` para `stable`

- [ ] A dor tem ≥1 evidência concreta citada (EE-NNN ou EE-AUTO-NNN), não só suposição.
- [ ] "Quem sente" distingue usuário de comprador quando forem pessoas diferentes.
- [ ] Custo de hoje quantificado em R$, horas ou risco — número concreto, não "muito".
- [ ] Pelo menos 1 alternativa existente analisada com o motivo de não resolver.
- [ ] Toda suposição restante movida para `hipoteses-a-validar.md` com critério de validação.

---
> Termos técnicos: ver `GLOSSARIO-ROLDAO.md` na raiz.
