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

# Glossário do módulo SLA Contratual

> Termos específicos. Transversais em `docs/comum/glossario.md`. Hook valida não-duplicação.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| SLA Contratual | Acordo comercial de nível de serviço pactuado em contrato com cliente | "SLA" sozinho (ambíguo) | promessa comercial mensurável com penalidade/bonificação | Contrato cliente |
| SLO | Service Level Objective — meta interna técnica (latência, uptime do app) | confundir com SLA | meta de operação técnica, não comercial | SRE / `docs/operacao/observabilidade.md` |
| SLA Operacional (chamado) | SLA interno de atendimento de chamados de TI/suporte ao uso do sistema | confundir com SLA Contratual | acordo operacional sem cláusula contratual com cliente externo | `dominios/operacao/modulos/chamados/` |
| TR | Tempo de Resposta — do registro do incidente até primeiro retorno qualificado | "primeiro atendimento" | quantos minutos/horas até reconhecer | Contrato |
| TS | Tempo de Solução — do registro até resolução definitiva | "tempo total" | quantos minutos/horas até resolver | Contrato |
| Criticidade | Severidade do incidente (P0/P1/P2/P3) que define qual SLA aplicar | "prioridade" sozinho | qual perfil de SLA será aplicado | Contrato |
| Calendário de atendimento | Janela horária do SLA (8x5, 24/7, plantão) com feriados | "horário comercial" sozinho | quando o cronômetro corre | Contrato |
| Perfil de SLA | Modelo reutilizável (Ouro, Prata, Bronze) vinculado a contratos | "template SLA" | conjunto de regras agrupado | Definição interna |
| Pausa de SLA | Suspensão temporária do cronômetro com motivo justificado | "stop" | tempo não conta no SLA | Contrato |
| Estouro de SLA | Descumprimento — tempo decorrido > limite contratual | "violação" sozinho | gera penalidade | Contrato |
| Penalidade | Valor cobrado da empresa contratada por descumprimento | "multa" | desconto/débito ao próximo ciclo | Contrato |
| Bonificação | Valor adicional pelo bom desempenho | "bônus" sozinho | crédito ao próximo ciclo | Contrato |
| Escalonamento | Notificação automática de níveis hierárquicos quando SLA em risco | "escalation" cru | aviso hierárquico programado | Definição interna |
| Evidência de cumprimento | Anexo (foto, log, assinatura) que comprova execução | "comprovante" sozinho | prova juntada para defesa em questionamento | ISO 17025 cláusula 7.5 (analogia) |
| Relatório SLA | PDF mensal ao cliente com TR/TS/% cumprimento + evidências | "relatório de atendimento" | evidência contratual periódica | Contrato |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum (hook).
- Termo descontinuado → `@deprecated` + janela de migração 3 meses.
- Mudança de definição → bump CHANGELOG seção "Modificado".

## Convenções

- PT-BR.
- Definição em 1 linha; mais que isso vai pra `docs/explicacoes/<termo>.md`.
- Origem obrigatória para termos regulados ou contratuais.
