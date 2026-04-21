# ADR 0023 — Issue drafts automáticos da cascata de verificação

Status: Aprovado

Data: 2026-04-20

## Contexto

Depois da fatia de snapshot diff, `tools/verification-cascade.ts` passou a bloquear `CASCADE-003`, mas o passo seguinte ainda era manual: alguém precisava transformar o erro em issue de re-auditoria.

O harness já pede automação incremental de propagação em `harness/14-verification-cascade.md`, e o repositório já usa diretórios canônicos com `README.md` e `_template.md` para artefatos regulatórios.

## Decisão

Criar `compliance/verification-log/issues/` como raiz canônica para drafts de issue da cascata, com:

- `_template.md` como formato Markdown único;
- `drafts/` para os arquivos renderizados localmente ou no CI;
- `README.md` explicando o fluxo.

`tools/verification-cascade.ts` passa a:

- retornar findings estruturados para `CASCADE-003`;
- renderizar drafts determinísticos por snapshot afetado;
- gravar esses drafts em `compliance/verification-log/issues/drafts/`;
- expor o comando `verification-cascade issue-drafts`.

O workflow `required-gates` passa a:

- gerar o JSON dos drafts quando o job falha;
- tentar abrir issue real com `actions/github-script`;
- evitar duplicata quando já existir issue aberta com o mesmo título.

## Consequências

Snapshot diff deixa de depender de transcrição manual para virar issue de re-auditoria.

O fluxo local continua puro no `check`, sem escrever no working tree; a escrita fica restrita ao subcomando dedicado e ao CI.

## Limitação

A automação atual cobre apenas o bootstrap de `CASCADE-003` para snapshot diff. Outros gatilhos de propagação continuam pendentes, assim como a bateria final de 30 certificados canônicos em PDF/A.
