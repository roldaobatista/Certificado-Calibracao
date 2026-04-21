# ADR 0003 — Topologia de hosting e serviços de segurança

- **Status:** aceito
- **Data:** 2026-04-19
- **Aprovado em:** 2026-04-19 pelo usuário (product owner)
- **Autor:** bootstrap (Claude Code)
- **Revisores:** `product-governance` + `lgpd-security` + `legal-counsel` (revisão formal pós-MVP, quando agentes estiverem operacionais)
- **Nota:** pendências operacionais (registro de domínio, conta AWS, conta Backblaze, parecer LGPD formal) continuam válidas — não bloqueiam scaffold, mas são pré-requisito de deploy.
- **Relacionado:** `harness/05-guardrails.md` (Gates 3, 4), `harness/09-cloud-agents-policy.md`, `compliance/cloud-agents-policy.md`

## Contexto

Usuário decidiu hospedar Aferê em **Hostinger** (VPS KVM 4, São Paulo, BR). Hostinger não oferece nativamente WORM storage nem KMS gerenciado — requisitos duros dos Gates 3 (audit hash-chain) e 4 (WORM) em `harness/05-guardrails.md`.

Precisamos decidir onde rodam: aplicação, banco, filas, chaves de assinatura, checkpoints imutáveis de audit log, PDFs emitidos e observabilidade.

## Opções consideradas

| Opção | Prós | Contras |
|-------|------|---------|
| **Híbrido: Hostinger VPS + Backblaze B2 + AWS KMS** | Custo baixo (<$15/mês MVP), dados em BR, KMS isolado em conta separada, WORM via Object Lock (S3-compatível) | 3 contas a gerenciar, Backblaze fora do Brasil (us-west por padrão; EU também disponível) |
| Full-cloud AWS (EC2 + RDS + KMS + S3 Object Lock + CloudWatch) | Stack única, soberania BR em sa-east-1 | Custo 3-5× maior no MVP (~R$500-800/mês só de infra); usuário já escolheu Hostinger |
| Full self-host (VPS + Postgres + MinIO + Vault) | Total soberania | Complexidade alta, risco de gestão de KMS/WORM artesanal, não é auditável facilmente em 17025 |
| Hostinger Cloud Hosting (shared) | Mais barato | Sem Docker, sem Redis, sem extensões Postgres custom — inviável para Aferê |

## Decisão

Adotar topologia **híbrida** com **Hostinger VPS como núcleo + serviços externos especializados**.

### Topologia

```
┌────────────────────────── Hostinger VPS KVM 4 (São Paulo, BR) ──────────────────────────┐
│                                                                                         │
│   Docker Compose:                                                                       │
│   ├─ apps/api (Fastify)          :3000                                                  │
│   ├─ apps/web (Next.js SSR)      :3001                                                  │
│   ├─ apps/portal (Next.js)       :3002                                                  │
│   ├─ postgres:16                 :5432   (com pgcrypto, uuid-ossp, pg_partman)          │
│   ├─ redis:7                     :6379   (cache + BullMQ)                               │
│   ├─ nginx (reverse proxy + TLS via Let's Encrypt)  :80, :443                           │
│   └─ watchtower (auto-pull de imagens estáveis)                                         │
│                                                                                         │
│   Volumes persistentes em /var/lib/afere/{postgres,redis,uploads-hot}.              │
│                                                                                         │
└──────┬──────────────────────────────┬──────────────────────────────┬────────────────────┘
       │                              │                              │
       │ assinatura/chaves            │ WORM (imutável)              │ logs + métricas
       ▼                              ▼                              ▼
┌───────────────┐          ┌────────────────────┐          ┌──────────────────────┐
│  AWS KMS      │          │  Backblaze B2      │          │ Grafana Cloud (free) │
│  sa-east-1    │          │  Object Lock       │          │ + Axiom (logs)       │
│               │          │  bucket: afere │          │                      │
│ - chave       │          │  -certificates     │          │ OpenTelemetry        │
│   assinatura  │          │  + afere-audit │          │ export via OTLP      │
│ - chave       │          │  -checkpoints      │          │                      │
│   hash-chain  │          │                    │          │                      │
└───────────────┘          └────────────────────┘          └──────────────────────┘
```

### Responsabilidades

| Função | Onde | Por quê |
|--------|------|---------|
| App (api + web + portal) | Hostinger VPS | Baixa latência interna + controle total |
| Postgres | Hostinger VPS | Proximidade com app, backup diário para B2 |
| Redis / filas (BullMQ) | Hostinger VPS | Volátil, sem requisito de soberania |
| Fila de sync (pg-boss) | Postgres | Parte da trilha auditável |
| **Chaves de assinatura digital** | **AWS KMS sa-east-1** | Isolamento físico do VPS (comprometimento do VPS não expõe chave), compliance forte |
| **Checkpoint de hash-chain assinado** | **AWS KMS sa-east-1** | Gate 3 exige chave segregada |
| **WORM — PDFs emitidos** | **Backblaze B2 Object Lock** | Imutabilidade verificável; Gate 4 |
| **WORM — checkpoints de audit log** | **Backblaze B2 Object Lock** | Gate 3 + 4 |
| Métricas (Prometheus scrape) | **Grafana Cloud free tier** | Sem self-host |
| Logs (Pino JSON stdout) | **Axiom free tier** | Query rápida, retenção 30d suficiente para MVP |
| Backups diários de Postgres | Backblaze B2 (bucket separado, não Object Lock) | Restore precisa de mutabilidade |

### Ambientes

- `dev` — Docker Compose local na máquina do usuário.
- `staging` — mesmo VPS (namespace docker compose `staging`) até V3; depois segundo VPS.
- `prod` — Docker Compose no VPS, portas `443/80` via nginx.

### Deploy

- **GitHub Actions** build das imagens Docker → push para **GHCR** (GitHub Container Registry, grátis).
- Action de deploy: SSH no VPS, `docker compose pull && docker compose up -d` (rolling via nginx health check).
- Migrations Prisma executadas como step isolado antes do `docker compose up` (fail-closed se falhar).

### Segurança do VPS

- SSH por chave apenas, porta não padrão, **Fail2ban** ativo.
- **UFW** bloqueia tudo exceto 22 (ssh custom), 80, 443.
- Atualizações de segurança automáticas (`unattended-upgrades`).
- Logs de acesso também exportados para Axiom.
- **Sem** credenciais AWS/B2 no VPS: api carrega via variáveis de ambiente injetadas do GitHub Secrets → systemd env → Docker.

## Consequências

**Positivas:**
- Custo operacional estimado MVP: **< R$150/mês** (VPS ~R$70 + B2 ~$2 + KMS ~$2 + registros de domínio).
- Dados em território nacional (Hostinger SP). WORM em Backblaze EU/US com Object Lock mantém integridade regulatória ainda que não esteja no Brasil — será documentado em matriz de tratamento `compliance/legal-opinions/`.
- KMS em conta AWS **segregada** (único serviço) reduz surface de ataque.
- Dá para demonstrar auditoria CGCRE com artefatos assinados + cadeia reproduzível.

**Negativas / mitigadas:**
- SPOF no VPS — aceito no MVP; V4+ plano de migração para 2 VPS ou Coolify/Dokku multi-node.
- B2 não está no Brasil — `lgpd-security` + `legal-counsel` precisam atestar em `compliance/legal-opinions/` que WORM externo não viola LGPD para os dados em questão (PDFs de certificado não contêm dados pessoais além do mínimo já público).
- Três contas para gerenciar — documentar em runbook de onboarding.

**Consequências regulatórias:**
- Matriz LGPD em `compliance/legal-opinions/lgpd-matrix.md` precisa listar:
  - Hostinger (operador principal, SP/BR).
  - Backblaze B2 (sub-operador, região declarada).
  - AWS KMS (sub-operador, sa-east-1).
  - Grafana Cloud + Axiom (sub-operadores de telemetria).
- Parecer jurídico do `legal-counsel` obrigatório antes do GA (ver P0-12 em `harness/STATUS.md`).
- Gate 4 em `harness/05-guardrails.md` validado via smoke test pós-deploy contra Backblaze B2.

## Como validar

- Terraform/IaC mínimo em `infra/` provisiona:
  - Conta B2 com bucket Object Lock configurado (retenção ≥ 5 anos, conforme LGPD + 17025).
  - Conta AWS KMS com 2 chaves (assinatura + checkpoint hash-chain), rotação anual.
- Smoke test:
  - `apps/api` grava blob no B2 → tenta sobrescrever → recebe `AccessDenied` (Gate 4 ✓).
  - `apps/api` pede assinatura ao KMS → assina blob → verifica assinatura localmente com pubkey cacheada (hash-chain ✓).
- Dashboard Grafana mostra p95 latência API < 300ms em carga MVP.

## Pendências antes de `[x] Aprovado`

1. Usuário registrar domínio (sugestão: via Hostinger para simplificar DNS).
2. Usuário criar conta AWS (ou delegar para mim via IaC depois que ele aceitar) com credencial para `sa-east-1`.
3. Usuário criar conta Backblaze com application key de escrita.
4. Fechado em `2026-04-21`: `legal-counsel` emitiu parecer sobre sub-operadores em `compliance/legal-opinions/lgpd-matrix.md`.

## Revisão

- Re-revisar topologia no fim de V3 (Tipo A acreditado). Se múltiplos clientes e latência virarem gargalo, migrar para 2 VPS Hostinger com Coolify + PgBouncer + read replica.
