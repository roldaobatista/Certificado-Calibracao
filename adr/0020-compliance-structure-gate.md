# ADR 0020 — Gate da estrutura canônica de compliance/

Status: Aprovado

Data: 2026-04-20

## Contexto

P1-3 define `compliance/` como registro canônico de governança, evidência e handoff. A árvore já existia desde o bootstrap, mas a permanência dessa estrutura dependia de revisão manual e de gates especializados para subáreas específicas.

Sem um gate estrutural, uma remoção acidental de diretórios, READMEs ou registros base poderia passar despercebida até quebrar outro fluxo.

## Decisão

Adicionar `tools/compliance-structure-check.ts` como gate estrutural de P1-3.

O gate valida:

- 44 artefatos canônicos de `compliance/`, entre diretórios e arquivos.
- 13 referências obrigatórias em `compliance/README.md`.
- Presença do novo script `pnpm compliance-structure-check` em `pnpm check:all`.
- Execução condicional no pre-commit quando o delta toca `compliance/`, o checker, a spec, a ADR, o status do harness ou o próprio hook.

## Consequências

`compliance/` passa a ter uma verificação estrutural de repositório inteiro, complementar aos gates especializados.

O checker é deliberadamente estrutural: ele garante que os registros existem e que a página índice não perca referências, mas não valida conteúdo normativo, jurídico ou metrológico. Essas validações continuam nos gates dedicados.

## Limitação

O gate não comprova que evidências ou pareceres estão semanticamente corretos. Ele apenas evita drift estrutural e remoção silenciosa de registros canônicos.
