# ADR 0015 — Slash-commands regulatórios

Status: Aprovado

Data: 2026-04-20

## Contexto

P2-2 exigia slash-commands regulatórios, mas parte dos comandos existentes era apenas instrucional e dois comandos da lista canônica ainda não existiam. Sem gate, comandos críticos poderiam divergir dos gates reais ou prometer execução ainda não implementada.

## Decisão

Criar `tools/slash-commands-check.ts` para validar a lista canônica:

- `/spec-norm-diff`
- `/ac-evidence`
- `/claim-check`
- `/tenant-fuzz`
- `/emit-cert-dry`

Cada comando precisa declarar owner, risco, comandos executáveis e seções de objetivo, execução, evidência, escalonamento e referências. O gate entra em `pnpm check:all` e no pre-commit.

## Consequências

Os comandos passam a ser auditáveis e compatíveis com o harness. Execuções manuais de rotina regulatória ficam ligadas a comandos reais do workspace e a evidências esperadas.

## Limitação

`/emit-cert-dry` continua fail-closed enquanto a emissão dry-run real não for implementada nas fatias V1+. O comando atual prepara a cascata L4 e registra a indisponibilidade, sem simular certificado.
