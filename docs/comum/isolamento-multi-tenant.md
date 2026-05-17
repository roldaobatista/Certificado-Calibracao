---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Isolamento multi-tenant

> **Pra quê:** estabelece o que significa "tenant não vê dado de outro tenant" no Aferê. Fonte explicativa dos IDs **INV-TENANT-001..004** + **SEC-TENANT-001** definidos em `REGRAS-INEGOCIAVEIS.md`. Outros docs referenciam os IDs, não duplicam texto — este aqui é a explicação de uma vez.
>
> **Decisão arquitetural:** ver `docs/adr/0002-multi-tenancy.md` (schema-shared + RLS + middleware).
> **Stack:** Django + PostgreSQL (ADR-0001 candidata).

---

## 1. O que é um tenant

Um **tenant** = um cliente do Aferê (uma assistência técnica, um laboratório de calibração, etc.). Cada tenant tem seus próprios dados (clientes finais, técnicos, OS, certificados, NFS-e emitidas, etc.) que **nenhum outro tenant pode ver** — nem por acidente, nem por bug, nem por hostilidade.

**Quantidade esperada de tenants no MVP-1:** 3-10 (com Balanças Solution como dogfooding + clientes piloto externos).
**Wave B/C:** dezenas a centenas.

---

## 2. Modelo escolhido: schema-shared + RLS

Decidido na **ADR-0002**:
- Todas as tabelas de dados de cliente moram no **mesmo schema PostgreSQL**.
- Toda tabela tem coluna `tenant_id` (NOT NULL).
- **Row-Level Security (RLS)** do PostgreSQL filtra por `tenant_id` em todas as queries — **mesmo se a aplicação esquecer**.
- Middleware Django injeta `tenant_id` na sessão de conexão a cada request.
- Role da aplicação criada com `NOBYPASSRLS` + `NOSUPERUSER`.

**Por que não schema-per-tenant:** custo de manutenção (cada tenant uma migration), escalabilidade limitada, complexidade operacional. Schema-shared + RLS é o padrão da indústria pra SaaS B2B com até dezenas de milhares de tenants.

**Critério de reversão:** se TAM > 5.000 tenants em 2028 → migrar pra schema-per-tenant (ver ADR-0001 critério de reversão).

---

## 3. Defesa em profundidade — 4 camadas

| Camada | Mecanismo | Falha aqui significa |
|--------|-----------|----------------------|
| **1. Aplicação** | Middleware Django + Manager customizado força `.filter(tenant_id=X)` em todo QuerySet | Bug óbvio, pego em revisão |
| **2. Banco — RLS** | PostgreSQL policy bloqueia query sem `current_setting('app.tenant_id')` | Aplicação esqueceu — RLS ainda barra |
| **3. Role** | Role `app_user` com `NOBYPASSRLS`; Docker NÃO roda como `postgres` superuser | RLS é absoluta — não é bypass-able |
| **4. Audit** | Toda query auditada com `tenant_id` no log (trilha imutável WORM em Backblaze B2) | Vazamento detectado retroativamente |

**Se camadas 1+2+3 falharem, vazamento é determinístico** — ANPD 72h + perda de cliente + incidente SEV-0.

---

## 4. Regras inegociáveis (fonte: `REGRAS-INEGOCIAVEIS.md`)

| ID | Regra |
|----|-------|
| **INV-TENANT-001** | Toda query SQL/ORM contém `tenant_id` no WHERE — validado por linter + teste de fuzzing |
| **INV-TENANT-002** | Toda tabela com dados de cliente tem coluna `tenant_id` NOT NULL — migration linter |
| **INV-TENANT-003** | RLS ativa em todas tabelas com `tenant_id` (PostgreSQL) — migration check + teste |
| **INV-TENANT-004** | Role da aplicação: `NOBYPASSRLS` + `NOSUPERUSER`. Migrations rodam com role `app_migrator` (também NOBYPASSRLS). Hook valida `current_setting('is_superuser') = off` e testa bypass policy |
| **SEC-TENANT-001** | RLS ativa em todas tabelas com dados de cliente (mesma coisa de INV-TENANT-003 vista do ângulo segurança) |

---

## 5. Hooks que enforce essas regras

| Hook | Status | Função |
|------|--------|--------|
| `tenant-id-validator` | ⏳ a criar | Pre-commit: lê diff de migrations e código Python; bloqueia se tabela nova sem `tenant_id` ou query sem filtro |
| `block-destructive` | ✅ existe | Bloqueia comandos perigosos no shell |
| Migration check em CI | ⏳ a criar | GitHub Action: roda RLS smoke test em cada PR — cria 2 tenants, tenta acesso cruzado, espera 0 rows |
| Fuzzing semanal | ⏳ Wave C | Robô tenta query maliciosa em ambiente staging, registra resultado |

---

## 6. Cenários proibidos (testes obrigatórios)

Cada cenário tem teste automatizado que **deve falhar** se proteção quebrar:

1. **Cross-tenant SELECT:** tenant A logado tenta `SELECT * FROM clientes WHERE id IN (lista de IDs do tenant B)` → 0 rows (RLS bloqueia)
2. **UPDATE em registro de outro tenant:** tenant A tenta `UPDATE certificados SET valor=X WHERE id=<id do tenant B>` → 0 affected rows
3. **Migration sem tenant_id:** PR adiciona tabela sem coluna `tenant_id` → CI falha
4. **Query sem filtro:** PR adiciona `.objects.all()` sem manager customizado → linter bloqueia
5. **Bypass via superuser:** docker compose roda como `postgres` → smoke test falha + alerta P0
6. **Connection pool fuga:** request do tenant A reusa conexão de tenant B sem trocar `app.tenant_id` → teste de carga detecta

---

## 7. LGPD / direito ao esquecimento

Quando tenant é deletado (cancela contrato + 15 dias de carência):
1. **Exclusão lógica primeiro** (flag `deleted_at`) — 15 dias pra reversão
2. **Crypto-shredding após 15 dias:** chave KMS do tenant em AWS KMS sa-east-1 é destruída → dados criptografados ficam ilegíveis
3. **Log da exclusão em WORM:** trilha imutável registra hash do request de exclusão + timestamp + signatário humano
4. **Backup com retenção:** backups têm a chave também — destruir chave = destruir leitura do backup

Detalhe em `docs/conformidade/comum/retencao-matriz.md` (a criar, ver `documentos-do-projeto.md` Família 6).

---

## 8. Observabilidade tenant-aware

- Todo log, trace, metric, alerta **tem `tenant_id` como label** — sem isso debug é cego em multi-tenant
- Painel Grafana filtra por tenant
- Drill trimestral (1 obrigatório no MVP-1, conforme ADR-0001 portão 3): "consigo isolar o que o tenant Y fez entre HH:MM-HH:MM em ≤ 5 min?"

---

## 9. Casos de exceção (a tratar caso surjam)

- **Operação de plataforma** (Roldão precisa ver dados de todos os tenants pra suporte): role `support_user` separada, com auditoria reforçada, sem `NOBYPASSRLS`. Acesso registrado em `governanca/trilha-auditoria-agentes.md`.
- **Backup/restore:** role `backup_user`, somente leitura, agendada.
- **Migration data fix entre tenants:** proibida sem ADR específica + aprovação do Roldão.

---

## 10. Referências

- ADR-0002 (multi-tenancy detalhada)
- `REGRAS-INEGOCIAVEIS.md` (IDs INV-TENANT-001..004 + SEC-TENANT-001)
- `docs/arquitetura/anti-corrosion-layer.md` (porta `MultiTenantDiscriminator`)
- `docs/operacao/multi-tenant-ops.md` (runbook — a criar)
- `docs/conformidade/comum/retencao-matriz.md` (LGPD — a criar)
