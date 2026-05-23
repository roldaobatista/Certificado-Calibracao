---
owner: roldao
revisado-em: 2026-05-22
status: stable
finalidade: mapa topológico dos GATEs Wave A — dependências entre GATEs cravadas em `gates-wave-a-consolidado.md` (atende M-INT-06 Onda 1).
relacionados:
  - docs/governanca/gates-wave-a-consolidado.md
  - docs/comum/sagas-cross-modulo.md
---

# Topologia dos GATEs Wave A

> **Pra quê:** auditoria Onda 1 M-INT-06 detectou que o catálogo `gates-wave-a-consolidado.md` lista os GATEs mas não diz qual precede qual. Sem topologia, advogado/auditor decide ordem por intuição. Esta doc dá o DAG.

---

## DAG (texto)

```
[Foundation cravada]
  |
  +--> GATE-1 (B2 WORM bucket criado)
  |       └--> GATE-2 (verificação periódica B2)
  |       └--> KMS PII_HASH_KEY_TENANT_* habilitada (chaves-kms-inventario §"PII tenant")
  |
  +--> GATE-3 (NTP cravado SP)
  |       └--> Bloqueia timestamps em produção (ADR-0030 §"tz_lab")
  |
  +--> GATE-4 (ciclo chave PII anual)
  |       └--> Pré-req: GATE-1 + KMS_TENANT_DATA_* habilitada
  |
  +--> GATE-5 (hash AcessoDadosCliente em audit chain)
  |       └--> Pré-req: AUDIT_HASH_KEY habilitada
  |
  +--> GATE-6 (ADR-0020 + CODEOWNERS expandida)
  +--> GATE-7 (higiene `::uuid` em policies RLS)
  |
  +--> GATE-FB-1 (perfil tenant-specific — INV-AUTHZ-004)
  |       └--> Pré-req: GATE-FB-2 (retenção authz_decisions + ip_hash)
  |
  +--> GATE-FB-3 (redator escopo PII)
  +--> GATE-FB-4 (texto INV-AUTHZ-002 via ADR)
  |
  +--> GATE-CLI-1 (retenção stable + B2 WORM)
  |       └--> Pré-req: GATE-1
  |
  +--> GATE-CLI-2 (EventoTimeline consumers)
  |       └--> Pré-req: ADR-0033 (idempotência) entregue
  |
  +--> GATE-CLI-3 (p95 visão-360)
  |       └--> Pré-req: GATE-CLI-2 + OBS-003 (métricas em hot path)
  |
  +--> GATE-CLI-4 (dashboard regularização)
  +--> GATE-CLI-5 (régua D+30/60/89)
  |       └--> Pré-req: GATE-CLI-2 + INV-INT-010
  |
  +--> GATE-CLI-6 (reativação ContasReceber.Pago)
  |       └--> Pré-req: GATE-CLI-5 + ADR-0035 (matriz suspenso/reativado)
  |
  +--> GATE-CLI-7 (consumer agenda)
  +--> GATE-CLI-8 (consumer certificados)
  |
  +--> GATE-EQP-1 (A3 Lacuna integrada)
  +--> GATE-EQP-RT (carta competência)
  +--> GATE-EQP-RT-NOTIF (consumer ANPD/CGCRE)
  |
  +--> GATE-EQP-DEP-WEASYPRINT-UPGRADE (CVE-2025-68616)
  +--> GATE-SEG-BPT-1 (apólice BPT Balanças Solution — ADR-0028)
  |       (independente do produto — antes do 1º dogfooding real em campo)
```

---

## Tabela resumida (precedência)

| GATE | Pré-requisitos | Bloqueia |
|---|---|---|
| GATE-1 (B2 WORM) | Foundation F-A fechada | GATE-2, GATE-4, GATE-CLI-1 |
| GATE-2 (verificação B2) | GATE-1 | 1º tenant externo |
| GATE-3 (NTP) | Foundation F-A | timestamps prod |
| GATE-4 (rotação chave PII) | GATE-1 | retenção LGPD operacional |
| GATE-5 (hash audit chain) | AUDIT_HASH_KEY | LGPD ANPD inquérito |
| GATE-CLI-2 (consumers EventoTimeline) | ADR-0033 | GATE-CLI-3, GATE-CLI-5 |
| GATE-CLI-5 (régua D+30/60/89) | GATE-CLI-2, INV-INT-010 | GATE-CLI-6 |
| GATE-CLI-6 (reativação) | GATE-CLI-5, ADR-0035 | 1º cancelamento real |
| GATE-EQP-RT-NOTIF (ANPD/CGCRE) | LGPD-NOTIF-001 | troca de RT em prod |
| GATE-SEG-BPT-1 (apólice BPT) | ADR-0028 | 1º dogfooding BPT em campo |

---

## Como navegar

- "Posso começar GATE-CLI-3?" → consultar pré-req: GATE-CLI-2 + OBS-003. Se algum aberto, GATE-CLI-3 fica pendente.
- "GATE-1 atrasou — o que mais cai?" → tudo que depende dele (GATE-2, GATE-4, GATE-CLI-1).
- "Auditor Família 5 pode marcar Wave A como pronta?" → todos os GATEs deste DAG fechados.

## Consequências

- Auditor pode discutir ordem com base na topologia, não em intuição.
- Roldão pode priorizar caminho crítico (`GATE-1 → GATE-CLI-2 → GATE-CLI-5 → GATE-CLI-6` é o blocking path para 1º cliente externo pago real).

## Manutenção

- Adição/remoção de GATE em `gates-wave-a-consolidado.md` exige atualização nesta topologia (CODEOWNERS força).
- Hook (Onda 4) valida que todo GATE-NOME mencionado em PR corresponde a entrada aqui.
