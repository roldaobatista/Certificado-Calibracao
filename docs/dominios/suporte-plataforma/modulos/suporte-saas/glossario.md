---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
---

# Glossário — Módulo Suporte SaaS

> Termos específicos. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Ticket de suporte | Solicitação aberta por usuário do tenant à equipe SaaS | "chamado" (esse é cliente final do tenant) | demanda interna do produto | Interno |
| Suporte SaaS | Suporte oferecido PELO Aferê PRA usuários dos tenants | "suporte interno" (ambíguo) | distinto de `operacao/chamados/` | Interno |
| Chamado do cliente final | Demanda do cliente final do tenant — fica em `operacao/chamados/` | NÃO confundir com ticket de suporte | módulo diferente | Interno |
| Categoria | Bug / Dúvida / Sugestão / Acesso / Financeiro do SaaS | "tipo" (ambíguo) | roteamento + métrica | Interno |
| SLA de suporte | Tempo máximo de resposta/resolução por plano | "prazo" (ambíguo) | obrigação contratual | Plano comercial |
| Plano | Free / Pro / Enterprise — define SLA + features | "tier" | nível de assinatura | Comercial |
| Base de conhecimento | Coleção curada de artigos resolutivos | "BC", "wiki" (impreciso) | autoatendimento | Interno |
| Deflexão | Resolução sem abrir ticket (autoatendimento via BC) | — | KPI de saúde | Padrão helpdesk |
| Acesso remoto | Atendente entra no tenant com consentimento + log | "impersonation" (técnico interno apenas) | sessão temporária auditada | Interno |
| Roadmap público | Lista visível a todos os tenants | "backlog" (interno) | comunicação externa | Interno |
| Sugestão | Pedido de melhoria — pode virar item de roadmap | "feature request" | input do usuário | Interno |
| Votação | Mecanismo de priorização por usuários | — | sinal de demanda | Interno |
| Página de status | Painel público com saúde do sistema | "status page" | comunicação de manutenção | Padrão SaaS |
| Manutenção planejada | Janela agendada de indisponibilidade ou degradação | — | aviso antecipado obrigatório | Interno |
| Banner de aviso | Notificação visual dentro do produto | "alerta" (ambíguo) | comunicação push | Interno |
| Handoff IA→humano | Transferência de conversa do agente IA para humano | "escalonamento" (também serve P1/P2) | continuidade de chat | Interno |

---

## Como esta lista evolui

Termo novo → adicionar + verificar conflito com glossário comum. Mudança → bump CHANGELOG.
