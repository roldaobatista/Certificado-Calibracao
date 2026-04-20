# Spec 0017 — Gate da estrutura canônica de compliance/

## Objetivo

Fechar a lacuna de P1-3 tornando a árvore canônica de `compliance/` verificável por ferramenta local, `check:all` e pre-commit.

## Escopo

- Adicionar `tools/compliance-structure-check.ts`.
- Validar presença e tipo de diretórios e arquivos canônicos em `compliance/`.
- Validar que `compliance/README.md` referencia os principais registros regulatórios.
- Adicionar script raiz `pnpm compliance-structure-check`.
- Incluir o gate em `pnpm check:all` e `.githooks/pre-commit`.
- Manter regressão em `tools/compliance-structure-check.test.ts`.

## Critérios de aceite

- O teste falha quando o checker, o script ou a ligação de pre-commit estão ausentes.
- O checker retorna `COMP-001` para artefatos obrigatórios ausentes ou com tipo incorreto.
- O checker retorna `COMP-002` quando o README deixa de citar entradas canônicas.
- `pnpm compliance-structure-check` passa na árvore real do repositório.
- `pnpm check:all` executa `pnpm compliance-structure-check`.

## Fora de escopo

- Não aprova conteúdo jurídico ou metrológico dos artefatos.
- Não substitui os gates especializados de dossiê, roadmap, runbooks, cloud agents ou auditoria.
- Não altera a regra de que mudanças regulatórias em `compliance/**` devem passar por PR + ADR.
