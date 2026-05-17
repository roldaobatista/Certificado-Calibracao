---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: chamados
dominio: operacao
---

# Glossário do módulo Chamados (Helpdesk)

> Termos específicos. Transversais em `docs/comum/glossario.md`.

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Chamado | Registro de solicitação/problema do cliente antes de virar OS | "ticket" sem tradução | algo que o cliente quer e ainda precisa triagem | OP16 |
| Canal de origem | Por onde o chamado entrou (WhatsApp, telefone, portal, email, presencial) | "fonte" | influencia regra de distribuição | JTBD-086 |
| Triagem | Classificação inicial (tipo, urgência, equipamento) feita pela atendente em ≤ 30s | "screening" | chamado em fila aguardando análise | JTBD-008 |
| SLA | Acordo de tempo máximo de resposta/resolução por tipo+urgência | "prazo combinado" (ambíguo) | timer rodando; alerta se aproximar do limite | OP16 |
| Escalonamento de SLA | Subir a prioridade ou notificar nível superior quando SLA está perto de estourar | "escalar" sozinho | timer disparou; atribuição muda automaticamente | OP16 |
| Duplicado | Chamado com mesmo cliente + mesmo equipamento + janela ≤ 7 dias | "repetido" | sistema sugere mesclar; nunca mescla sozinho | JTBD-020 |
| Conversão em OS | Promoção do chamado para OS (estado RASCUNHO) preservando histórico | "abrir OS" (ambíguo com criar OS do zero) | chamado FECHADO com `os_id` referenciada | OP16 |
| Urgência | Nível (baixa, média, alta, crítica) atribuído na triagem; afeta SLA | "prioridade" (palavra usada também pra ordenação visual) | timer SLA diferente; cor da linha muda | OP16 |
| Atendente de plantão | Pessoa responsável pela triagem do chamado em horário comercial | "operadora" | aparece como `atribuido_a` no chamado | P-OP-03 |
| Regra de distribuição | Lógica que sugere atendente/técnico baseada em carga atual + competência | "auto-assign" | sistema sugere; humano aceita ou redireciona | OP16 |
| Fechamento sem OS | Chamado resolvido por orientação (não vira OS) | "encerrado" (ambíguo) | estado FECHADO + `os_id=null` + `razao_fechamento` | OP16 |

## Como evolui

Termo novo → verificar conflito com glossário comum.
