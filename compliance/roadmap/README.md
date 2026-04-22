# Roadmap

Fonte canônica executável do roadmap por fatias verticais V1-V5.

`harness/10-roadmap.md` explica a decisão arquitetural. A leitura recomendada é:

- `v1-v5.yaml` para entender fatias, escopo e gates formais;
- `execution-backlog.yaml` para entender a sequência operacional `V1.1 ... V5.x`;
- `transversal-tracks.yaml` para entender o que fica fora do V1-V5 por já estar coberto por gates transversais.

O roadmap vigente é **foundation-first**:

- V1 — fundação técnica;
- V2 — cadastros principais;
- V3 — fluxo operacional central;
- V4 — portal e extras;
- V5 — Qualidade e camadas regulatórias avançadas.

Artefatos canônicos implementados fora dessa ordem continuam válidos como ativos preparatórios de contrato, UX e cenários, mas **não fecham** a fatia correspondente enquanto não houver banco, API, UI e fluxo real do núcleo da fase.

`execution-backlog.yaml` não redefine os gates de V1-V5. Ele apenas quebra cada fatia em passos menores, com dependência explícita e janela de planejamento:

- `now`: frente imediata de execução;
- `next`: próximo lote depois do fechamento da frente atual;
- `later`: itens dependentes das fases anteriores.

`transversal-tracks.yaml` materializa a parte do PRD que fica fora das fatias V1-V5 por ser coberta por gates transversais já ativos.

## Gate

```bash
pnpm roadmap-check
pnpm roadmap-backlog-check
```

O gate exige ordem estrita V1-V5, dependência sequencial, release-norm, dossiê de validação, pacote normativo e gates de saída por fatia.

O backlog executável complementa o roadmap com uma cadeia `Vn.m` e valida:

- ordem estrita dos itens do backlog;
- coerência entre `id`, `slice` e a fase canônica;
- dependências entre itens;
- janelas `now -> next -> later` sem regressão;
- alinhamento de `linked_requirements` do item com a fatia correspondente em `v1-v5.yaml`.

Cada fatia também declara:

- `epic_id`: identificador canônico do épico L0 usado pela cascata de verificação;
- `linked_requirements`: lista de REQs cuja re-auditoria pode ser agregada por esse épico.

`linked_requirements` é validado contra `compliance/validation-dossier/requirements.yaml`: cada ID precisa existir e não pode ser compartilhado por mais de uma fatia.

O bloco `coverage` torna a cobertura do roadmap explícita:

- `tracked_requirement_prefixes` define quais famílias de requisito o V1-V5 deve cobrir;
- `excluded_requirements` lista os requisitos rastreados que ficam fora das fatias por pertencerem a gates transversais.

Cada `REQ-ID` listado em `coverage.excluded_requirements` deve aparecer em exatamente uma trilha de `transversal-tracks.yaml`, com:

- `owner`: agente responsável pela capacidade transversal;
- `harness_refs`: decisões do harness que fundamentam o gate;
- `gate_commands`: comandos canônicos que validam a trilha;
- `linked_requirements`: requisitos excluídos do V1-V5 e cobertos por aquela trilha.
