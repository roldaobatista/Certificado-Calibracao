---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/comum/glossario-roldao.md
---

# Glossário do módulo BI

> Termos específicos. Termos transversais ficam em `docs/comum/glossario-roldao.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Dashboard | Painel visual com vários indicadores agrupados por tema | "painel BI", "tela de gráficos" | Tela que mostra cards/gráficos com números importantes | US-BI-001 |
| KPI (Indicador-chave) | Métrica de negócio com meta definida | "métrica solta", "número solto" | Número que tem uma meta a bater | US-BI-002 |
| Drill-down | Clicar num indicador para ver o detalhe que o compõe | "abrir detalhe", "expand" | Quando clica num card e vê a lista por trás dele | US-BI-001 |
| DRE gerencial | Demonstração de Resultado para uso interno, **não substitui contabilidade oficial** | "DRE contábil" | Visão de lucro/prejuízo do mês, mas pro dia-a-dia, não pro contador | US-BI-004 |
| Fluxo de caixa projetado | Saldo previsto do caixa nos próximos dias considerando entradas e saídas agendadas | "previsão de caixa" | Quanto vou ter no banco daqui a 30/60/90 dias | US-BI-003 |
| Inadimplência | Conjunto de parcelas vencidas e não pagas | "atraso", "calote" | Lista de clientes que estão devendo | US-BI-005 |
| Churn | Cliente que parou de comprar / renovar | "perda de cliente" | Cliente sumiu há X dias | US-BI-010 |
| Segmentação | Agrupar clientes por critério (porte / frequência / mix) | "filtro de cliente" | Cliente dividido em grupos pra ação dirigida | US-BI-011 |
| Manutenção preditiva (light) | Previsão de quando equipamento vai precisar de manutenção, baseada em histórico simples | "preditivo IA", "ML" | Alerta de "esse equipamento vai dar pau em breve" | US-BI-013 |
| Relatório customizado | Relatório montado pelo usuário escolhendo métricas + filtros + agrupamentos | "query ad-hoc", "SQL" | Relatório que o próprio Roldão monta sem chamar suporte | US-BI-014 |
| Envio agendado | Disparo automático de relatório em data/hora programada | "agendamento de e-mail" | E-mail que chega sozinho com o resumo na segunda 8h | US-BI-015 |
| Link público | URL externa que mostra dashboard restrito, opcionalmente com senha/expiração | "compartilhar dashboard" | Endereço que cliente externo abre pra ver SLA dele sem login | US-BI-016 |
| Data mart | Tabela/visão otimizada para leitura agregada (não confundir com banco operacional) | "BI database", "data warehouse" | Cópia dos dados arrumada pro BI ler rápido | ADR a criar |
| Defasagem | Quanto tempo o dado está atrasado em relação ao operacional | "lag", "atraso de atualização" | "Esse número é de 10 min atrás" | NFR PRD |
| SLA | Acordo de tempo de resposta/resolução para cliente | "prazo do contrato" | Prazo que prometemos cumprir | US-BI-009 |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar se conflita com glossário comum (hook valida).
- Termo descontinuado → marcar `@deprecated` + janela 3 meses.
- Mudança de definição → bump CHANGELOG.

## Convenções

- Termos PT-BR. Quando técnico-original (KPI, SLA, churn, drill-down) for inevitável, sempre traduzir na coluna "Se vir na tela/log".
- Definição em 1 linha. Se precisar mais, criar `docs/explicacoes/<termo>.md`.
