# ADR 0049 — Dry-run de emissão consolida gates V1 em um pipeline executável

- Status: proposto para implementacao
- Data: 2026-04-22
- Relacionado: `specs/0046-v1-emission-dry-run.md`, `PRD.md` §13, `compliance/roadmap/v1-v5.yaml`

## Contexto

As regras centrais de V1 já existem como contratos separados, mas ainda não há uma peça executável que simule a emissão como operação única. Isso mantém `/emit-cert-dry` em modo apenas preparatório e deixa o back-office sem uma leitura operacional consolidada de prontidão para emissão.

## Decisão

1. `apps/api/src/domain/emission/dry-run.ts` passa a consolidar os checks necessários para dry-run de emissão.
2. O pipeline combina política regulatória, cadastro do equipamento, padrão, competência, numeração, declaração metrológica, hash-chain e QR público.
3. O resultado compartilhado passa a viver em `packages/contracts/src/emission-dry-run.ts`.
4. `tools/emit-cert-dry.ts` vira o CLI canônico do slash-command `/emit-cert-dry`.
5. `apps/web/src/emission` materializa um resumo operacional para o back-office com base no resultado compartilhado.

## Consequências

- O slash-command regulatório deixa de ser apenas preparatório e passa a ter execução útil para V1.
- O produto ganha uma peça de integração que conecta requisitos já validados sem exigir persistência real.
- O back-office passa a ter uma visão operacional de emissão antes do pipeline definitivo de PDF/A e assinatura.

## Limitações honestas

- O dry-run continua sem persistir certificado, eventos ou anexos.
- O pipeline ainda não gera PDF/A, assinatura real nem release-norm.
- O resultado depende de cenários/payloads de entrada canônicos, não de uma OS persistida ponta a ponta.
