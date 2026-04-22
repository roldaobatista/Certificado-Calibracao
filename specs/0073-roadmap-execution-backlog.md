# 0073 - Backlog executável do roadmap foundation-first

## Contexto

O rebaseline da spec `0072` corrigiu a ordem macro do roadmap para:

1. fundação técnica;
2. cadastros principais;
3. fluxo operacional central;
4. portal e extras;
5. Qualidade e camadas regulatórias avançadas.

Isso resolveu a leitura estratégica, mas ainda deixou uma lacuna operacional: V1-V5 continua amplo demais para orientar a execução diária sem ambiguidade. Falta um artefato canônico dizendo qual é a sequência de trabalho dentro de cada fatia, qual item vem agora e como os blocos menores herdam a fase sem redefinir seus gates.

## Escopo

- Adicionar `compliance/roadmap/execution-backlog.yaml` como complemento operacional do roadmap V1-V5.
- Decompor V1-V5 em itens menores, com IDs `Vn.m`, dependência explícita e janela de planejamento.
- Criar `pnpm roadmap-backlog-check` para validar estrutura mínima, ordem, dependências e alinhamento dos itens com `compliance/roadmap/v1-v5.yaml`.
- Atualizar `compliance/roadmap/README.md`, `harness/10-roadmap.md`, `compliance/README.md` e `harness/STATUS.md` para explicar a relação entre fase e backlog executável.
- Tornar `execution-backlog.yaml` parte da estrutura canônica de `compliance/`.

## Fora de escopo

- Alterar os gates de saída de V1-V5.
- Redefinir os requisitos ligados a cada fatia em `compliance/roadmap/v1-v5.yaml`.
- Implementar backend, banco, auth, cadastros, OS, portal ou módulos de Qualidade nesta fatia.

## Critérios de aceite

- `compliance/roadmap/execution-backlog.yaml` existe como artefato canônico e descreve uma sequência explícita `V1.1 ... V5.x`.
- Cada item do backlog pertence a exatamente uma fatia V1-V5 e não pode fechar a fatia sozinho.
- O backlog deixa explícito que a janela `now/next/later` orienta prioridade de execução, mas não substitui os gates formais de slice.
- `pnpm roadmap-backlog-check` falha quando:
  - o arquivo estiver ausente ou inválido;
  - a ordem dos itens `Vn.m` quebrar a sequência;
  - um item apontar para fatia inexistente;
  - um item depender de item futuro ou desconhecido;
  - um requisito ligado ao item não pertencer à fatia correspondente em `v1-v5.yaml`.
- `pnpm roadmap-backlog-check` entra em `pnpm check:all`.

## Evidência

- `pnpm roadmap-backlog-check`
- `pnpm roadmap-check`
- `pnpm harness-dashboard:write`
- `pnpm check:all`
