---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contratos
dominio: comercial
diataxis: reference
---

# Glossário — Módulo Contratos

> Termos específicos. Transversais em `docs/comum/glossario-roldao.md`.
>
> **Atenção homonímia:** "contratos/" também é o nome da PASTA que guarda UI/API/Export specs em todos os módulos. Aqui o sentido é **contrato comercial recorrente** (relação cliente↔tenant).

| Termo | Definição | Sinônimos proibidos | Se vir na tela/log significa | Origem |
|---|---|---|---|---|
| Contrato | Acordo comercial entre tenant e cliente com escopo + valor + vigência + recorrência de execução (calibração mensal, manutenção trimestral) | "acordo", "convênio" | Documento que gera OS automaticamente em ciclos | OP1 |
| Vigência | Período entre data início e data fim do contrato | "validade" (não usar — confunde com orçamento) | Selo "vigente / a vencer / vencido / encerrado" | OP1 |
| Periodicidade | Frequência de geração automática de OS (mensal, trimestral, semestral, anual, custom) | "frequência" | Configuração que dispara cron job | OP1 |
| Geração automática | Ato do sistema criar OS rascunho na data prevista do ciclo | "auto-criação" | Notificação aparece pra atendente revisar/confirmar | OP1 |
| Recorrência | Padrão de repetição (a cada N dias/meses) com regras (próximo útil, mesmo dia do mês) | — | Próxima execução visível no contrato | OP1 |
| Renovação | Ato de estender vigência expirada/a expirar com novo período + revisão de preço | "prorrogação" | Wizard de renovação 60d antes do vencimento | OP1 + INV-026 |
| Alerta de vigência | Notificação configurável X dias antes do fim (default 30d / 60d / 90d) | "lembrete" sem qualificador | Notificação ao dono + vendedor responsável | OP1 |
| Anti-fidelidade abusiva | Princípio fundador: cliente pode encerrar contrato a qualquer momento sem multa abusiva. Multa permitida só pro prejuízo concreto comprovável | "sem-letra-miúda" | Cláusula padrão obrigatória no PDF do contrato | Princípio fundador `prd.md §6` |
| Reajuste | Aumento periódico de preço (IGP-M, IPCA, % fixo) configurável | "correção monetária" | Botão "aplicar reajuste" no aniversário | INFERÊNCIA |
| Aditivo | Mudança formal em contrato vigente (escopo, preço, vigência) sem encerrar — gera nova versão | "amendment" | Histórico do contrato mostra V1, V2 com motivo | INFERÊNCIA |
| Suspensão | Estado temporário onde contrato existe mas NÃO gera OS automática | "pausa" | Selo amarelo + motivo + data prevista retomada | INFERÊNCIA |
| Encerramento | Estado terminal por iniciativa de cliente, tenant ou prazo (vigência fim) | "cancelamento" | Estado=encerrado + motivo + data + última OS | OP1 |
| Pré-OS gerada | OS rascunho criada pelo job automático que aguarda confirmação humana ANTES de virar OS formal | "OS pendente" | Bandeja "pendentes do contrato X" para atendente | OP1 + R-novo CRM-1 |

## Convenções

- "Contrato" sem qualificador = contrato recorrente comercial.
- Quando se referir à pasta `contratos/` do módulo (UI/API/Export specs), usar "pasta de contratos técnicos" ou "specs do módulo".
- Cliente bloqueado/inadimplente: contrato ativo NÃO gera nova OS automática (validação na geração).
