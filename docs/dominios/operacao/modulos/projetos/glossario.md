---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: projetos
dominio: operacao
relacionados:
  - docs/comum/glossario.md
---

# Glossário — Módulo Gestão de Projetos

> Específicos. Transversais em `docs/comum/glossario.md`.

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Projeto | Container de trabalho grande que reúne múltiplas OS, compras e marcos | "obra", "implantação" | entidade-raiz com escopo, cronograma e budget | módulo |
| Etapa | Bloco sequencial de trabalho dentro do projeto | "fase" | tem nome, ordem, prazo, responsável e % concluído | módulo |
| Marco | Ponto de controle relevante no projeto (entrega, faturamento, decisão) | "milestone" | data específica vinculada a etapa | PMI light |
| Tarefa | Unidade de trabalho menor dentro de uma etapa | "atividade" | atribuída a pessoa, tem prazo | módulo |
| Gantt | Visualização gráfica do cronograma (barras por etapa/tarefa no tempo) | "linha do tempo" | UI específica do módulo | PMI |
| Orçamento previsto | Soma de custos esperados (mão de obra, peça, serviço, etc.) | "budget" | informado na criação; evolui via aditivo | módulo |
| Custo realizado | Soma de custos efetivos agregados de OS, compras e estoque vinculados | "custo real" | atualizado em tempo quase-real | módulo |
| Receita prevista | Valor a faturar conforme contrato + aditivos | "receita planejada" | base do faturamento por etapa | módulo |
| Margem | Receita realizada/prevista − custo realizado/previsto | "lucro" | calculada no dashboard do projeto | módulo |
| Risco do projeto | Evento incerto que pode afetar escopo, prazo, custo ou qualidade | "ameaça" | tem probabilidade × impacto = nível de risco | PMI |
| Plano de mitigação | Ação para reduzir probabilidade ou impacto do risco | "contingência" | texto + responsável + prazo | PMI |
| Diário de execução | Entradas datadas com o que aconteceu no projeto | "log", "diário de obra" | imutável após gravação (`INV-001`) | construção civil + módulo |
| Entregável | Resultado tangível esperado em uma etapa | "deliverable" | linkado à etapa; tem aceite | PMI |
| Aceite de etapa | Confirmação formal de que entregável foi recebido pelo cliente | "homologação" | habilita faturamento da etapa | módulo |
| Aditivo | Alteração formal de escopo, prazo ou valor após início do projeto | "ajuste contratual" | nova versão do contrato (`INV-026` análogo) | construção civil + jurídico |
| Status do projeto | Estado atual: PLANEJADO / EM_EXECUCAO / PAUSADO / CONCLUIDO / CANCELADO | — | máquina de estados explícita | módulo |
| Reunião do projeto | Encontro registrado com ata, decisões e próximos passos | "meeting" | linka a participantes e gera ações | PMI |
| Documento do projeto | Arquivo anexado (contrato, planta, ata, relatório) | "anexo" | versionado, com controle de quem subiu | módulo |

---

## Como evolui

Termo novo → adicionar + verificar conflito (hook valida).
