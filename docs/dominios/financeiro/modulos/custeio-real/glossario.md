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

# Glossário do módulo Custeio Real

> Termos específicos. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Custo previsto | Estimativa de custo feita no orçamento da OS antes de executar | "orçamento" (orçamento é doc, não custo) | "o que esperávamos gastar" | linha 1579 `novas funcionalidades.txt` |
| Custo real | Custo apurado pós-execução com base em insumos efetivamente consumidos | "custo final", "actual cost" | "o que de fato gastamos" | linha 1580 |
| Custo de mão de obra | Horas-técnico aplicadas × hora-base configurada | "mão" | "tempo humano que essa OS consumiu, em R$" | linha 1581 |
| Hora-base | Valor unitário por hora do técnico (configurado por tenant/por técnico) | "salário-hora" (cuidado: salário é outro conceito) | "quanto vale uma hora desse técnico" | parâmetro de custeio |
| Custo de deslocamento | km rodados × valor/km + combustível direto | "viagem" | "deslocamento até cliente entrou na conta" | linha 1582 |
| Custo de retrabalho | Esforço adicional em OS reaberta sem nova cobrança | "rework" | "fizemos de novo de graça" | linha 1587 |
| Custo de garantia | Esforço/peça aplicada em atendimento em garantia (gratuito ao cliente) | "warranty" | "atendimento sob garantia entrou como custo" | linha 1588 |
| Margem real | Receita da OS menos custo real total | "lucro bruto" (lucro tem mais nuances contábeis) | "quanto sobrou de fato dessa OS" | linha 1590 |
| Margem % | Margem real ÷ receita × 100 | "rentabilidade" | "margem percentual" | derivado |
| OS deficitária | OS cuja margem real é negativa ou abaixo do threshold | "OS no prejuízo" | "essa OS deu prejuízo, ver porquê" | linha 1596 |
| Threshold de alerta | Valor de margem % abaixo do qual sistema alerta (configurável por tenant) | "limite" | "abaixo disso o sistema vai chiar" | parâmetro |
| Apuração | Processo de consolidar todos os custos de uma OS | "fechamento" (fechamento é mais amplo) | "rodou a conta da OS" | PRD |
| Comparação previsto × real | Tabela lado a lado por categoria de custo | "variance analysis" | "estouramos onde?" | linha 1595 |
| Categoria de custo | Cada uma das colunas: mão de obra, deslocamento, peças, retrabalho, garantia, comissão, etc. | "tipo de gasto" | "rubrica de onde veio o gasto" | PRD |
| Reapuração | Recalcular custo real após correção em insumo (OS reaberta) | "recalc" | "refizemos a conta porque algo mudou" | US-CUS-001 |

---

## Como esta lista evolui

- Categoria nova de custo → adicionar aqui + atualizar modelo + ADR.
- Termo conflitante com glossário comum → hook valida.

## Convenções

- PT-BR sempre. Inglês só em "Sinônimos proibidos" pra explicitar o que NÃO usar.
