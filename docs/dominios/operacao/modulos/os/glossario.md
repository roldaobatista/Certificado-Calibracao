---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
modulo: os
dominio: operacao
---

# Glossário do módulo OS (Ordens de Serviço)

> Termos específicos de OS. Transversais em `docs/comum/glossario.md`.
> **Revisado em 2026-05-23 (ADR-0023):** glossário absorveu o modelo "OS com Atividades" — `tipo` saiu da OS e foi pra `AtividadeDaOS`; checklist saiu do agregado OS e foi pra atividade.

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| OS | Ordem de Serviço — container comercial/financeiro do atendimento (1 cliente, 1 instrumento, 1 fatura, 1 link no portal) | "ticket de execução" (é Chamado) | trabalho com responsável geral, prazo, valor, link de acompanhamento | OP3 + ADR-0023 |
| AtividadeDaOS | Trabalho técnico individual dentro de uma OS (cada atividade tem seu próprio tipo + checklist + ciclo de estado) | "subtipo de OS"; "etapa da OS" (ambíguo) | dispara handler do tipo correspondente (calibração emite cert; manutenção registra peças) | ADR-0023 |
| TipoAtividade | Enum fechado de 6 valores: `calibracao`, `manutencao_corretiva`, `manutencao_preventiva`, `instalacao`, `verificacao_inmetro`, `vistoria` (INV-OS-ATIV-003) | "tipo de OS" (não existe mais como enum) | controla qual módulo recebe o evento `AtividadeIniciada` | ADR-0023 + INV-OS-ATIV-003 |
| tipo_predominante | Cache estatístico na OS calculado a partir das atividades (opcional; usado em filtros de fila) | "tipo da OS" (sugere unicidade — não existe) | apenas hint de UX; fonte de verdade é a lista de atividades | ADR-0023 |
| sequencia | Ordem dentro da OS (`1, 2, ...`); manutenção corretiva sequência=1 + calibração sequência=2 é o caso típico | "ordem de execução" | gate opcional — atividade de sequência N só inicia se N-1 estiver em estado terminal | ADR-0023 US-OS-009 |
| EstadoOS | Posição na máquina de estados (RASCUNHO, AGENDADA, EM_EXECUCAO, CONCLUIDA, FATURADA, PAGA, CANCELADA) — **computado a partir das atividades** (INV-OS-ATIV-001) | "status da OS" (ambíguo) | derivado, não setado direto | INV-027 + ADR-0023 |
| EstadoAtividade | Ciclo próprio da atividade (PENDENTE, EM_EXECUCAO, CONCLUIDA, NAO_CONFORME, CANCELADA) | "status da atividade" | OS só fecha quando TODAS atividades em estado terminal | ADR-0023 |
| Reabertura | Criação de **nova OS** referenciando uma OS concluída (NUNCA volta estado); atividades novas começam em PENDENTE | "reabrir OS" no sentido de mutar | OS antiga preservada; nova aponta `os_origem_id` | INV-027 |
| ChecklistDaAtividade | Lista de itens obrigatórios por atividade (foto, assinatura, peça, padrão usado) — depende do `TipoAtividade` | "checklist de execução" (legado pré-ADR-0023) | bloqueia transição da atividade EM_EXECUCAO→CONCLUIDA se algum item faltar | ADR-0023 + JTBD-014 |
| Não Conformidade (NC) | Marcação **em atividade** (não na OS toda) que algo saiu fora dos limites | "erro de calibração" | bloqueia emissão de certificado SÓ da atividade calibração; outras atividades CONCLUIDA da mesma OS permanecem válidas | INV-012 + INV-OS-ATIV-001 |
| Padrão usado | Instrumento de referência (rastreado RBC) usado na execução da atividade tipo=calibração | "padrão de medição" | obrigatório pra atividade calibração; alimenta rastreabilidade | ISO 17025 cl. 6.5 |
| Assinatura do cliente | Captura no app (touch ou A1/A3) atestando recebimento da atividade (não da OS toda) | "OK do cliente" | item obrigatório do checklist; vinculada a `AceiteAtividade` (versão do termo + hash + IP) | Lei 14.063/2020 + LGPD RAT-08 |
| OS de campo | OS com ≥1 atividade executada fora da empresa (técnico vai ao cliente) | "OS externa" | exige geolocalização + sync mobile (ADR-0004 + RAT-07) | OP3 + RAT-07 |
| OS de bancada | OS com todas atividades executadas no laboratório fixo | "OS interna" | dispensa geolocalização; instrumento entra via recepção | OP3 |
| Geolocalização da Atividade | Lat/long capturada no início e fim da atividade (precisão limitada por INV-OS-GEO-001) | "GPS do técnico" | usado pra auditoria; LGPD exige opt-in + RIPD | INV-OS-GEO-001 + RAT-07 |
| os_origem_id | Atributo que liga OS-filha (reaberta) à OS-mãe | "OS pai" | aparece no histórico do equipamento | INV-027 |
| link_modulo_tecnico | FK tipada na atividade apontando pro registro técnico no módulo correspondente (ex: `Calibracao.id` para tipo=calibracao) | "ID externo da atividade" | resolve qual entidade técnica concretiza a atividade | ADR-0023 + INV-OS-ATIV-005 |
| AceiteAtividade | Entidade que registra a assinatura digital do cliente sobre uma atividade específica (versão do termo + hash texto + IP + timestamp + base legal Lei 14.063) | "termo de aceite" (genérico) | uma OS combinada pode ter N AceiteAtividade, um por atividade | TEMA-D.3 da auditoria 2026-05-23 |

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum (hook).
- Mudança de definição → CHANGELOG seção "Modificado".
