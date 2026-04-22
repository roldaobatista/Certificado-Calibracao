# ADR 0051 - Backlog executável do roadmap foundation-first

Status: Aprovado

Data: 2026-04-22

## Contexto

Após o rebaseline foundation-first, o roadmap V1-V5 passou a comunicar a ordem correta das fases, mas ainda não dizia como quebrar cada fatia em passos menores e sequenciais. Para um projeto regulado com múltiplos agentes e histórico recente de adiantamentos canônicos fora de ordem, isso mantém uma pergunta operacional aberta: "qual é exatamente o próximo passo?".

Sem um backlog canônico, a resposta ficaria dependente de contexto oral, memória efêmera de sessão ou interpretação livre dos agentes.

## Decisão

Adicionar `compliance/roadmap/execution-backlog.yaml` como artefato canônico complementar ao roadmap V1-V5.

Esse backlog:

- decompõe cada fatia em itens menores com IDs `Vn.m`;
- mantém a execução foundation-first em cadeia explícita;
- registra dependências entre itens;
- distingue janela de planejamento (`now`, `next`, `later`) de gate formal de slice;
- herda os limites do roadmap V1-V5, sem criar critérios paralelos de fechamento de fase.

Adicionar também o gate `pnpm roadmap-backlog-check` para validar:

- existência e schema básico do artefato;
- ordem estrita dos itens;
- integridade das dependências;
- coerência entre `slice`, `id` e a fatia canônica;
- alinhamento dos `linked_requirements` do item com os requisitos já atribuídos à respectiva fatia em `compliance/roadmap/v1-v5.yaml`.

## Consequências

- O projeto passa a ter uma resposta canônica e auditável para o "próximo passo" sem reabrir a discussão da ordem macro.
- O backlog operacional deixa de ser implícito e passa a ser versionado junto com o roadmap e o harness.
- Continuam existindo dois níveis de planejamento:
  - `v1-v5.yaml` define fases, escopo e gates;
  - `execution-backlog.yaml` organiza a sequência prática dentro dessas fases.
- Fechar um item do backlog não fecha a fatia correspondente por si só; os gates V1-V5 continuam soberanos.
