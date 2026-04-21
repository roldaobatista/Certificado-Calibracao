# ADR 0025 — `epic-review-flag` e reconciliação das verification issues

Status: Aprovado

Data: 2026-04-20

## Contexto

Depois da ADR 0024, a cascata já executava `spec-review-flag` em L1, mas ainda restavam duas lacunas práticas:

- o gatilho equivalente para L0/épico, já previsto em `harness/14-verification-cascade.md`;
- o fechamento das issues gerenciadas quando `main` deixa de reproduzir o finding.

Sem isso, a automação continuava parcial: issues podiam ser abertas automaticamente, mas o repositório ainda não convertia o reaparecimento ou a resolução do finding em mudança explícita de estado.

## Decisão

Adicionar um novo finding executável:

- `CASCADE-008` / `epic-review-flag`, emitido quando 3 correções consecutivas em ao menos 2 specs do mesmo épico alteram AC/REQ sem evidência de re-auditoria L0.

O épico é inferido a partir de tokens `L0/<EPIC-ID>` presentes em `propagated_up` ou `re_audits_completed`.

Também introduzir um reconciliador puro:

- `planVerificationIssueReconciliation(drafts, issues)` retorna quatro conjuntos: `create`, `reopen`, `keepOpen` e `close`.

O workflow `required-gates` passa a:

- gerar `verification-issue-drafts.json` em qualquer desfecho do job;
- buscar as issues gerenciadas atuais;
- montar um plano em `tsx` usando o reconciliador do repositório;
- criar, reabrir, atualizar ou fechar issues conforme esse plano;
- limitar fechamento automático ao `push` em `main`.

## Consequências

O ciclo de vida das verification issues deixa de ser apenas “abrir quando quebra” e passa a refletir o estado atual do repositório principal.

L0 e L1 ficam cobertos pelo mesmo contrato canônico de logs e drafts, sem criar um segundo diretório ou um segundo template.

## Limitação

A inferência de L0 continua dependente da qualidade dos registros em `compliance/verification-log/*.yaml`. Se o `L0/<EPIC-ID>` não for registrado, a automação não consegue agrupar as specs do mesmo épico.
