---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
  - docs/comum/integracoes-externas/whatsapp.md
---

# Glossário do módulo Comunicação Omnichannel

> Termos específicos. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Caixa de entrada unificada | Tela única que agrega mensagens de todos os canais (WhatsApp, e-mail, SMS, chat portal) | "inbox" cru, "caixa de e-mail" | painel central do atendente | Definição interna |
| Canal | Meio pelo qual a mensagem trafega (WhatsApp, e-mail, SMS, chat portal) | "fila", "queue" | propriedade da mensagem | Definição interna |
| Thread | Sequência de mensagens entre um cliente e a empresa em um canal | "conversa" sozinho (ambíguo) | unidade que o atendente atua | Definição interna |
| Conversa | Conjunto de threads do mesmo cliente cruzando canais | "thread" cru | agregação por cliente | Definição interna |
| Template (de mensagem) | Texto pré-aprovado e versionado, com variáveis | "modelo" sozinho | só pode disparar template aprovado em canais regulados (WhatsApp) | Meta WhatsApp Business Policy |
| HSM (WhatsApp) | Highly Structured Message — template aprovado pela Meta | siglas sem traduzir | template WhatsApp pronto para envio iniciado pela empresa | Meta WhatsApp Business |
| Sessão (WhatsApp) | Janela de 24h após cliente responder em que se pode enviar mensagem livre | "janela aberta" sozinho | sem template necessário enquanto válida | Meta WhatsApp Business |
| Resposta rápida | Texto curto disparado por atalho ("/preco") | "macro", "shortcut" cru | snippet de produtividade | Definição interna |
| Mensagem automática | Mensagem disparada por regra/evento sem atendente | "auto-reply" | regra orientada a evento | Definição interna |
| Distribuição | Algoritmo de atribuição de conversa a atendente | "roteamento" sozinho | round-robin / carteira / skill | Definição interna |
| Carteira | Conjunto de clientes atribuídos a um gerente fixo | "portfolio" cru | atribuição preferencial | Definição interna |
| Skill | Etiqueta de competência (idioma, segmento, calibração) usada na distribuição | "tag" sozinho | competência do atendente | Definição interna |
| Opt-in | Consentimento explícito do cliente para receber comunicações | "aceitou" sozinho | base legal LGPD | LGPD art. 8º |
| Opt-out | Pedido do cliente para parar de receber comunicações | "descadastro" | bloqueio imediato | LGPD art. 18 |
| Base legal | Hipótese LGPD que autoriza tratamento (consentimento, contrato, legítimo interesse, etc.) | "permissão" sozinho | justifica o tratamento | LGPD art. 7º |
| Status de leitura | Confirmação de leitura pelo cliente (quando canal suporta) | "ack" cru | controle de entrega | Padrão por canal |
| Conversão | Transformar conversa em chamado ou em lead | "convert" | evento de fluxo cross-módulo | Definição interna |
| Trilha de consentimento | Log imutável de cada opt-in/opt-out | "logs" sozinho | evidência LGPD | LGPD art. 37º |
| TMA | Tempo Médio de Atendimento | "AHT" cru | KPI de operação | Padrão call center |
| TMR | Tempo Médio de primeira Resposta | "TPR" cru | KPI de operação | Padrão call center |
| Conector | Adaptador entre o módulo e o serviço externo (Meta, provedor SMS, SMTP/IMAP) | "integração" sozinho | implementação na porta ACL | `docs/arquitetura/anti-corrosion-layer.md` |

---

## Como esta lista evolui

- Termo novo → verificar conflito (hook).
- Termo descontinuado → `@deprecated` + janela.
- Mudança de definição → bump CHANGELOG.

## Convenções

- PT-BR.
- Definição em 1 linha.
- Origem obrigatória para termos regulados (LGPD, Meta).
