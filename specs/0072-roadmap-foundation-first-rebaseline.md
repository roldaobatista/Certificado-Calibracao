# 0072 - Rebaseline do roadmap para fundacao tecnica primeiro

## Contexto

O roadmap canônico V1-V5 foi introduzido para tirar o projeto do cronograma otimista original e impor gates de saída auditáveis. Na prática, porém, a execução recente priorizou leituras canônicas e módulos demonstrativos de várias áreas antes de fechar a fundação operacional real do software.

Isso gerou confusão de leitura: o repositório parece avançado em emissão, portal, sync e Qualidade, mas a base lógica esperada para um software utilizável ainda não está fechada como sequência operacional real de banco, autenticação, cadastros, OS e emissão.

O replanejamento precisa manter o formato V1-V5 exigido pelos gates, mas mudar o sentido da sequência para:

1. fundação técnica;
2. cadastros principais;
3. fluxo operacional central;
4. portal e extras;
5. Qualidade e camadas regulatórias avançadas.

## Escopo

- Reescrever `compliance/roadmap/v1-v5.yaml` para refletir a nova ordem lógica.
- Atualizar `harness/10-roadmap.md` como decisão arquitetural explicativa da nova sequência.
- Atualizar `compliance/roadmap/README.md` para deixar explícito que o roadmap agora é foundation-first.
- Atualizar `harness/STATUS.md` para registrar o rebaseline do P1-4 e esclarecer que adiantamentos canônicos fora de ordem não equivalem a fechamento de fatia.
- Preservar o formato V1-V5, os gates de saída por fatia e a cobertura rastreável de `REQ-PRD-*`.

## Fora de escopo

- Alterar implementação de backend, banco, portal, app web ou Android.
- Apagar módulos canônicos já criados.
- Mudar a política de gates transversais já existentes em `transversal-tracks.yaml`, salvo se fosse necessário para manter cobertura, o que não é o caso nesta fatia.

## Critérios de aceite

- `compliance/roadmap/v1-v5.yaml` passa a ordenar V1-V5 como:
  - fundação técnica;
  - cadastros principais;
  - fluxo operacional central;
  - portal e extras;
  - Qualidade e camadas regulatórias avançadas.
- `harness/10-roadmap.md` explica que uma fatia só conta como concluída quando banco, API, UI e testes reais do núcleo da fase estiverem fechados.
- `compliance/roadmap/README.md` deixa explícito que módulos canônicos adiantados fora de ordem continuam válidos como ativos preparatórios, mas não fecham a fatia correspondente.
- `harness/STATUS.md` registra o rebaseline do P1-4 e esclarece como interpretar os adiantamentos já feitos sob o planejamento anterior.
- `pnpm roadmap-check` continua verde com a nova organização.

## Evidência

- `pnpm roadmap-check`
- `pnpm harness-dashboard:write`
- `pnpm check:all`
