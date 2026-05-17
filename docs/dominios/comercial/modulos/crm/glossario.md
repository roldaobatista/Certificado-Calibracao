---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: crm
dominio: comercial
diataxis: reference
---

# Glossário — Módulo CRM

> Termos específicos. Transversais em `docs/comum/glossario-roldao.md`.

| Termo | Definição | Sinônimos proibidos | Se vir na tela/log significa | Origem |
|---|---|---|---|---|
| Lead | Contato prospect ainda NÃO cadastrado como cliente master | "prospect", "interessado" | Aparece na "Caixa de entrada" do CRM antes de virar cliente | BIG-10 |
| Oportunidade | Lead/cliente com intenção concreta de compra (valor estimado, etapa do funil) | "deal", "negócio" | Card no kanban do funil | OP5 + JTBD-083 |
| Funil | Sequência de etapas pelo qual oportunidade caminha (ex: novo → contato → orçamento → fechamento) | "pipeline" sem qualificador | Tela kanban com colunas | OP5 |
| Etapa do funil | Coluna do kanban (configurável pelo tenant) | "stage", "fase" | Card movido entre colunas | OP5 |
| Lead scoring | Pontuação automática 0-100 baseada em sinais (calibração vencendo, NPS, valor histórico, sem contato há X dias) | "score" sem qualificador | Selo numérico no card + cor | JTBD-083 + BIG-10 |
| Tarefa de CRM | Atividade agendada (ligar, enviar e-mail, visitar) atribuída a vendedor com prazo | "to-do", "atividade" | Lista "minhas tarefas hoje" + alerta no prazo | OP5 |
| Sinal | Evento que pode disparar tarefa/automação (certificado vencendo, NPS detrator, parcela vencida, sem contato 90d, OS concluída) | "trigger" sem qualificador | "Por que esse cliente está no topo? → mostra sinais ativos" | JTBD-083 + BIG-10 |
| Automação | Regra gatilho→condição→ação configurada sem código | "workflow" | Listada em `/automacoes` | OP5.2 + BIG-11 |
| Sandbox de automação | Modo "se rodasse hoje, teria disparado em X clientes — eis a lista" antes de ativar | "simulação", "dry-run" | Tela de preview antes de "ativar" | JTBD-087 + R-novo CRM-1 |
| NPS | Pesquisa de 1 pergunta ("recomendaria de 0 a 10") disparada após OS concluída | — | Tela do cliente com 11 botões | JTBD-085 + BIG-10 |
| Detrator / Neutro / Promotor | Faixas de resposta NPS (0-6 / 7-8 / 9-10) | — | Selo no perfil + dispara automação | NPS metodologia padrão |
| Lista do dia | Ranking gerado todo dia de clientes que vendedor deve contatar, ordenado por sinais | "fila", "priorização" | Tela inicial do vendedor — JTBD-083 | JTBD-083 |
| Motivo de perda | Categoria escolhida ao mover oportunidade pra "perdido" (sem orçamento / preço / prazo / concorrente / cliente sumiu) | — | Dropdown obrigatório + texto livre opcional | OP5 |

## Convenções

- Lead **vira** cliente master ao converter — não vivem como entidades separadas após conversão.
- "Oportunidade" pode existir sobre lead OU sobre cliente master (recompra).
