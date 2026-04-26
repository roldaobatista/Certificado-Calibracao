# Aferê — Certificado de Calibração

Monorepo do **Aferê**, plataforma metrológica de certificação de calibração com back-office web, portal do cliente, backend Fastify/Prisma/Postgres, engine metrológica e harness de compliance para ISO/IEC 17025, Inmetro/Cgcre e operação multitenant.

O objetivo é tratar o produto como **plataforma metrológica regulada** — não apenas como gerador de PDF — cobrindo ciclo completo: cadastro, execução guiada, cálculo com incerteza, revisão técnica, assinatura, emissão, reemissão controlada e verificação pública do certificado.

## Estrutura do repositório

| Pasta / Arquivo | Conteúdo |
|-----------------|----------|
| [`PRD.md`](./PRD.md) | Fonte principal de requisitos do Aferê |
| [`AGENTS.md`](./AGENTS.md) | Regras canônicas de operação por agentes e gates |
| [`apps/api/`](./apps/api) | Backend técnico Fastify + Prisma |
| [`apps/web/`](./apps/web) | Back-office Next.js |
| [`apps/portal/`](./apps/portal) | Portal do cliente e verificação pública |
| [`packages/`](./packages) | Contracts, DB, audit-log, normative-rules, copy-lint e engine de incerteza |
| [`specs/`](./specs) | Specs por feature, fonte de cada mudança |
| [`adr/`](./adr) | Decisões arquiteturais |
| [`compliance/`](./compliance) | Dossiê, roadmap, release-norm, runbooks e evidências |
| [`ideia.md`](./ideia.md) | Material inicial de concepção do app |
| [`iso 17025/`](./iso%2017025) | Material de apoio sobre a norma — visão geral, requisitos, checklists, templates, atualizações e referências |
| [`normas e portarias inmetro/`](./normas%20e%20portarias%20inmetro) | Índices oficiais de portarias, RTAC, RTM, DOQ-CGCRE, NIT-DICLA e resoluções Conmetro aplicáveis a laboratórios de calibração |

## Como navegar

1. Comece por [`AGENTS.md`](./AGENTS.md) para entender as regras duras do repositório.
2. Leia [`PRD.md`](./PRD.md) e o status em [`harness/STATUS.md`](./harness/STATUS.md).
3. Consulte [`specs/`](./specs) e [`adr/`](./adr) antes de alterar código.
4. Use [`iso 17025/`](./iso%2017025) e [`normas e portarias inmetro/`](./normas%20e%20portarias%20inmetro) como referência normativa.

## Verificação local

```bash
pnpm install
pnpm check:all
pnpm test:tenancy
```

Para subir dependências locais:

```bash
pnpm dev:deps
pnpm db:migrate
pnpm db:seed
```

## Base normativa

- **ABNT NBR ISO/IEC 17025:2017** — competência, imparcialidade e operação consistente de laboratórios.
- **Portaria Inmetro nº 157/2022** — Regulamento Técnico Metrológico para instrumentos de pesagem não automáticos (IPNA).
- **Cgcre/Inmetro** — rastreabilidade, relato de resultados, declaração de conformidade, CMC e consulta pública de escopo RBC.
- **ILAC P10 / P14** — rastreabilidade e incerteza de medição.
- **EURAMET cg-18** — boa prática para calibração de NAWI (referência, não obrigatória).

## Premissas do produto

- Resultado e incerteza **nunca** são omitidos em certificado com declaração de conformidade.
- Certificado de calibração **não tem validade automática** — a periodicidade é do proprietário.
- Padrão vencido, sem certificado ou fora da faixa **bloqueia** a emissão.
- Execução offline com sincronização posterior; "oficial" só após validação do backend.
- Arquitetura preparada para **DCC (Digital Calibration Certificate)**.

## Status

Projeto em implementação ativa. O `check:all` executa typecheck, testes de domínio, critérios de aceite, regulatory evals, copy-lint, tenancy, RLS policy check, prontidão de runtime RLS, sync simulator, WORM, governança, dossiê, snapshots, redundancy e drift de agentes. Ainda há limitações honestas registradas no harness: Android Kotlin real, `FORCE ROW LEVEL SECURITY` com role `afere_app` ainda pendente de contexto transacional, validação externa PDF/A, infraestrutura KMS real, drills de staging e piloto controlado de produção.

## Contribuição

Este repositório é spec-as-source. Mudanças devem nascer em `specs/NNNN-slug.md`, ser rastreadas por ADR quando houver decisão arquitetural e passar pelos gates antes de commit/push.
