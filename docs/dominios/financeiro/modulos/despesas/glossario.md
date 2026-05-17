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

# Glossário do módulo Despesas

> Termos específicos. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Despesa corporativa | Gasto feito por colaborador em nome da empresa, registrado para aprovação | "gasto", "saída", "nota" | gasto a ser aprovado e (talvez) reembolsado | US-DSP-001 |
| Comprovante | Arquivo (foto, PDF, XML) que prova a despesa | "anexo", "documento" | imagem ou PDF da nota fiscal/recibo | US-DSP-001 |
| Alçada | Valor máximo que um papel pode aprovar sem escalonar | "limite", "teto" | limite individual de aprovação | US-DSP-002 |
| Reembolso | Pagamento ao colaborador da despesa aprovada não coberta por adiantamento | "ressarcimento" | conta a pagar gerada em nome do colaborador | US-DSP-003 |
| Compensação com adiantamento | Despesa aprovada que abate o saldo de um adiantamento existente no caixa do técnico | — | despesa não vira reembolso, abate saldo | US-DSP-003 |
| Vínculo com OS | Liga despesa a ordem de serviço, gerando custo real no atendimento | "associação", "OS-link" | OS aparece na linha da despesa | US-DSP-004 |
| Categoria de despesa | Classificação (combustível, alimentação, hospedagem, peça, terceiros, outros) | "tipo" | rótulo usado pra agrupar em relatórios | modelo-de-dominio.md |
| Centro de custo | Unidade contábil que “possui” o gasto (filial, equipe, projeto) | "departamento" | rótulo financeiro para rateio | `custeio-real/` |
| Status `pendente_aprovacao` | Despesa lançada aguardando primeiro aprovador | — | aparece para o gestor | US-DSP-001 |
| Status `aprovada` | Despesa autorizada e elegível para reembolso ou compensação | — | habilita ação do financeiro | US-DSP-002 |
| Status `rejeitada` | Despesa recusada com motivo registrado | — | colaborador deve refazer ou desistir | US-DSP-002 |
| Status `reembolsada` | Despesa que virou pagamento já liquidado em `contas-pagar/` | — | encerrada pelo financeiro | US-DSP-003 |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Mudança de definição → bump no CHANGELOG seção "Modificado".
- Termo descontinuado → `@deprecated` + janela 3 meses.
