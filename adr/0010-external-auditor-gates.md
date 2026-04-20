# ADR 0010 — Gate dos auditores externos

Status: Aprovado

Data: 2026-04-20

## Contexto

O P0-12 define três agentes auditores externos como primeira linha de auditoria: `metrology-auditor`, `legal-counsel` e `senior-reviewer`. Sem gate executável, a separação entre executor e auditor dependeria de revisão manual.

## Decisão

Criar `tools/external-auditors-gate.ts` para validar:

- existência dos três agentes auditores;
- ausência de ferramentas de edição direta nos auditores;
- paths de escrita restritos aos pareceres permitidos;
- templates de parecer por domínio;
- briefing para os 5 casos-limite que exigem humano real;
- pareceres L5 por release via `pnpm external-auditors-gate release --release <versao>`.

`pnpm external-auditors-gate` passa a fazer parte de `pnpm check:all` e do pre-commit canônico quando arquivos P0-12 são alterados.

## Consequências

O repositório passa a falhar fechado quando a governança dos auditores estiver incompleta. Releases ainda precisam rodar explicitamente o subcomando de release com a versão alvo para validar os três pareceres concretos.

## Limitação

O gate valida estrutura e bloqueio, não a qualidade substantiva do parecer. Os 5 casos-limite continuam exigindo humano real e emissão permanece bloqueada até resolução formal.
