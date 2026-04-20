# ADR 0001 — Framework do backend `apps/api`

- **Status:** aceito
- **Data:** 2026-04-19
- **Aprovado em:** 2026-04-19 pelo usuário (product owner)
- **Autor:** bootstrap (Claude Code)
- **Revisores:** `product-governance` + `senior-reviewer` (revisão formal pós-MVP, quando agentes estiverem operacionais)
- **Relacionado:** `harness/02-arquitetura.md`, P0-1 em `harness/STATUS.md`, `adr/0003-hosting-and-security-services.md`

## Contexto

`apps/api` é o dono único de auth, RBAC, emissão oficial, assinatura/QR, reemissão e sync server-side (regra de ownership em `harness/02-arquitetura.md`). Precisa rodar num VPS modesto (Hostinger KVM 4: 4 vCPU, 16GB RAM) ao lado de Postgres e Redis. Código tem que ser **auditável** e **explícito** para ISO/IEC 17025 (regra normativa em código de produção não pode esconder *magic*).

## Opções consideradas

| Opção | Prós | Contras |
|-------|------|---------|
| **Fastify + TypeScript** | Leve (baixa memória), plugin ecosystem maduro, suporte tRPC oficial, logs JSON nativos (Pino), schema validation nativa com JSON Schema/zod, hooks explícitos | DI manual (não é problema — ver contras de NestJS), menos opinionated |
| NestJS | DI estrutural, ecossistema rico, suporte enterprise | Pesado em memória (~2-3× Fastify), muita "magic" via decorators — ruim para auditoria normativa, overhead desnecessário no KVM 4 |
| Hono | Ainda mais leve que Fastify, edge-first | Ecossistema menor (Prisma + Fastify têm mais tutoriais/plugins), menos maduro em Node tradicional |
| Express | Mais popular historicamente | Performance inferior, não tem schema validation nativa, manutenção em declínio |

## Decisão

Adotar **Fastify + TypeScript** como framework do `apps/api`.

Stack concreta inicial:
- **Runtime**: Node.js 20 LTS.
- **HTTP**: Fastify 4.
- **RPC tipado**: tRPC 11 via `packages/contracts` (compartilhado com web/portal/android).
- **ORM**: Prisma 5 em `packages/db`.
- **Validação**: zod (reaproveitado em tRPC).
- **Logs**: Pino (default do Fastify) com output JSON para stdout → Axiom.
- **DI**: manual via factories em `src/infra/container.ts` (sem container mágico).
- **Hot-reload dev**: `tsx watch`.

## Consequências

**Positivas:**
- Código explícito favorece auditoria de `senior-reviewer` e `metrology-auditor`.
- Baixa footprint permite rodar api + Postgres + Redis num único KVM 4 no MVP.
- tRPC + zod dá type-safety end-to-end para web e Android (reduz bugs de contrato).

**Negativas / mitigadas:**
- DI manual exige disciplina — mitigar com lint + convenção em `src/infra/container.ts`.
- Sem magic de NestJS, precisa mais código "cola" — aceito em troca de auditabilidade.

**Consequências regulatórias:**
- Regra de emissão em `apps/api/src/domain/emission/**` fica inspecionável por função, sem decorators que escondam lógica — alinha com princípio §1 de `harness/01-principios.md`.

## Como validar

- P0-1 cria scaffold mínimo: `GET /healthz`, `tRPC /trpc` endpoint vazio, Pino logando em JSON, tsc/lint sem erros.
- `docker compose up -d` sobe api + postgres + redis num KVM 4 consumindo < 2GB RAM em idle.
- Sucesso = agentes conseguem rodar `pnpm dev` e bater em `/healthz` sem warnings.

## Revisão

- Revisar esta decisão no fim da fatia V1 (ver `harness/10-roadmap.md`). Se consumo de memória ou latência estourar budget, avaliar Hono.
- `product-governance` aprova ou veta com base no critério "auditabilidade regulatória".
