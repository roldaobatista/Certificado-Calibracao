# ADR 0021 — Traces determinísticos por seed de property testing

Status: Aprovado

Data: 2026-04-20

## Contexto

P0-11 exige redundância, seeds canônicos e evidência auditável. `evals/property-config.yaml` já declarava `N`, `canonical_seeds`, teste, comando e caminho de relatório, mas os seeds não tinham um artefato de trace versionado que pudesse ser refeito e comparado pelo gate.

Isso deixava a evidência de property testing menos rastreável do que o restante do dossiê.

## Decisão

Adicionar `trace_path` em cada propriedade e gerar JSONL determinístico por seed com:

- requisito associado;
- seed canônico;
- teste;
- comando;
- caminho de relatório;
- gerador (`tools/redundancy-check.ts trace`).

`pnpm redundancy-check:trace` gera os arquivos, e `pnpm redundancy-check` bloqueia:

- propriedade sem `trace_path`;
- trace fora de `compliance/validation-dossier/evidence/property-traces/`;
- trace ausente;
- trace desatualizado em relação à configuração.

## Consequências

Os seeds canônicos deixam de ser apenas configuração e passam a ter evidência versionada e reprodutível no dossiê.

O gate de redundância continua sendo estrutural e determinístico, sem depender de banco, rede ou credenciais.

## Limitação

O trace registra a matriz de execução esperada por seed. Ele não substitui os relatórios reais dos testes nem classifica flakes automaticamente.
