---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: os
dominio: operacao
---

# Glossário do módulo OS (Ordens de Serviço)

> Termos específicos de OS. Transversais em `docs/comum/glossario.md`.

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| OS | Ordem de Serviço — registro do trabalho a executar em campo ou laboratório | "ticket de execução" (é Chamado) | trabalho com responsável, prazo e instrumento | OP3 |
| Tipo de OS | Classificação que define fluxo (calibração / manutenção / instalação / verificação INMETRO / vistoria) | "categoria" | dispara handlers diferentes (ex: calibração emite certificado) | OP3 + INV-027 |
| Estado da OS | Posição na máquina de estados (RASCUNHO, AGENDADA, EM_EXECUCAO, CONCLUIDA, FATURADA, PAGA, CANCELADA) | "status" (ambíguo) | transição validada por hook | INV-027 |
| Reabertura | Criação de **nova OS** referenciando uma OS concluída (NUNCA volta estado) | "reabrir OS" no sentido de mutar | OS antiga preservada; nova OS aponta `os_origem_id` | INV-027 |
| Checklist de execução | Lista de itens obrigatórios pra concluir a OS (foto, assinatura, peça, padrão usado) | "to-do" | bloqueia conclusão se algum item faltar | JTBD-014 |
| Não Conformidade (NC) | Marcação na OS de calibração que algo saiu fora dos limites | "erro de calibração" | bloqueia emissão de certificado | INV-012 |
| Padrão usado | Instrumento de referência (rastreado RBC) usado na execução | "padrão de medição" | obrigatório pra OS de calibração; alimenta rastreabilidade | ISO 17025 cl. 6.5 |
| Assinatura do cliente | Captura no app (touch ou foto de assinatura física) atestando recebimento | "OK do cliente" | item obrigatório do checklist em OS de campo | LGPD RAT-08 |
| OS de campo | OS executada fora da empresa (técnico vai ao cliente) | "OS externa" | exige geolocalização + sync mobile | RAT-07 |
| OS de bancada | OS executada no laboratório fixo | "OS interna" | dispensa geolocalização; instrumento entra via recepção | OP3 |
| Geolocalização da OS | Lat/long capturada no início e fim da execução | "GPS do técnico" | usado pra auditoria; LGPD exige justificativa | RAT-07 |
| os_origem_id | Atributo que liga OS-filha (reaberta) à OS-mãe | "OS pai" | aparece no histórico do equipamento | INV-027 |

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum (hook).
- Mudança de definição → CHANGELOG seção "Modificado".
