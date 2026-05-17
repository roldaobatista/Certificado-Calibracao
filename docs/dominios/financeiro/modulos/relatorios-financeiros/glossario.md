---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
  - docs/dominios/financeiro/glossario.md
---

# Glossário do módulo Relatórios Financeiros

> Termos específicos. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| DRE gerencial | Demonstração de Resultado do Exercício para gestão (não para fisco) | "resultado" sozinho | tabela receitas → custos → despesas → lucro | US-RFN-001 |
| DRE contábil oficial | DRE que vai para SPED / contador (não fica neste módulo) | — | sai em `fiscal/`, não aqui | non-goal |
| Fluxo de caixa realizado | Entradas e saídas efetivamente liquidadas no período | "caixa realizado" | dinheiro que já entrou/saiu | US-RFN-002 |
| Fluxo de caixa projetado | Soma de recebíveis + pagáveis + recorrências futuras em janela definida | "previsão", "forecast" | estimativa baseada em títulos existentes | US-RFN-003 |
| Aging | Agrupamento de títulos em aberto por faixa de atraso (0-30, 31-60, 61-90, 90+ dias) | "carteira" | quanto está vencido e há quanto tempo | US-RFN-004 |
| Centro de custo | Unidade contábil que “possui” a despesa/custo (filial, equipe, projeto) | "departamento" | rótulo financeiro pra rateio | US-RFN-005 |
| Conciliação bancária | Comparar extrato do banco com lançamentos do sistema e marcar matches | — | OFX vs. sistema | US-RFN-006 |
| Drill-down | Clicar num número agregado e ver os lançamentos que somam aquele valor | "detalhamento" | usuário "abre" um total | INV-RFN-001 |
| Resultado por dimensão | Margem (receita − custo direto) calculada por cliente, técnico, vendedor ou serviço | "lucro por X" | tabela de lucratividade segmentada | US-RFN-008 |
| Custo direto | Custo atribuível à OS / contrato / serviço (vem de `custeio-real/`) | "custo de venda" | base do lucro bruto | `custeio-real/` |
| Margem bruta | Receita − custo direto | — | linha do DRE | US-RFN-001 |
| Materialized view | Tabela pré-calculada para performance de relatório (detalhe técnico, não aparece pro usuário) | — | objeto interno de banco | NFR |
| Saldo acumulado | Saldo de caixa somado dia a dia / linha a linha | — | última coluna do fluxo | US-RFN-002 |
| Janela de projeção | Quantos dias à frente o fluxo projetado considera (30/60/90 padrão) | — | seletor no topo do relatório | US-RFN-003 |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Mudança de definição → bump no CHANGELOG.
- Termo descontinuado → `@deprecated` + janela 3 meses.
