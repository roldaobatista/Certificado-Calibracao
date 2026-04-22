# ADR 0050 - Rebaseline do roadmap para foundation-first

Status: Aprovado

Data: 2026-04-22

## Contexto

O roadmap V1-V5 já cumpria o papel de impor gates auditáveis, mas a interpretação prática do projeto ficou desalinhada da expectativa natural de construção de software. O repositório acumulou módulos canônicos de leitura em várias áreas antes de consolidar a fundação operacional real de banco, autenticação, cadastros e fluxo de emissão.

Isso não invalida os artefatos já criados, mas torna a leitura do plano confusa para quem espera a sequência lógica:

1. fundação técnica;
2. cadastros principais;
3. fluxo operacional central;
4. portal e extras;
5. Qualidade e camadas regulatórias avançadas.

## Decisão

Manter o formato canônico V1-V5 e o gate `pnpm roadmap-check`, mas reorientar semanticamente o roadmap para uma execução foundation-first:

- V1 = fundação técnica;
- V2 = cadastros principais;
- V3 = fluxo operacional central;
- V4 = portal e extras;
- V5 = Qualidade e camadas regulatórias avançadas.

Adiantamentos canônicos fora de ordem continuam válidos como ativos preparatórios, seeds de UX, contratos e cenários de referência, mas **não** contam como fechamento da fatia correspondente enquanto não houver:

- persistência real;
- fluxo transacional do núcleo da fase;
- integração banco/API/UI;
- verificação compatível com o escopo real da fatia.

O Android/offline permanece no roadmap, mas sai da posição de prioridade estrutural do núcleo e passa a entrar em V4 como extensão operacional/canal extra após o fechamento do fluxo central web.

## Consequências

- O roadmap passa a comunicar uma ordem de construção mais coerente para um software utilizável.
- O projeto preserva os gates, o formato V1-V5 e a rastreabilidade de requisitos já exigidos pelo harness.
- Módulos canônicos já implementados deixam de ser interpretados como prova de fase concluída e passam a ser tratados explicitamente como adiantamentos de design/contrato.
- O fechamento formal de V1-V5 continua dependendo de `release-norm`, dossiê de validação e pacote normativo vigente por fatia.
