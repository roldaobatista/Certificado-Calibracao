---
owner: roldao
revisado-em: 2026-05-22
status: stable
finalidade: inventário canônico das chaves AWS KMS usadas no Aferê — propósito, escopo (global × tenant × módulo), rotação, ciclo de vida e operações de crypto-shredding.
relacionados:
  - ADR-0001 (stack)
  - ADR-0021 (anonimização vs retenção)
  - ADR-0032 (FK cross-módulo + ReferenciaPIIAnonimizavel)
  - SEC-QR-001 (REGRAS-INEGOCIAVEIS — chave QR dedicada)
---

# Inventário de chaves KMS

> **Pra quê:** crypto-shredding por tenant (LGPD direito ao esquecimento Zona A) **exige** chaves enumeradas, com propósito e dono claros. Auditoria Onda 1 A-INT-04 detectou ausência deste inventário.

---

## Modelo de chaves

Aferê usa **AWS KMS Multi-Region Key (MRK)** (ADR-0001 — `sa-east-1` primária ↔ `us-east-1` réplica). Toda chave tem `key_id` versionado (`vN`) para rotação anual (GATE-1 F-A).

---

## Inventário

| key | Escopo | Propósito | Rotação | Dono | Crypto-shredding ao eliminar tenant? |
|---|---|---|---|---|---|
| `PII_HASH_KEY_REGISTRO` | **Global Aferê** | HMAC determinístico de PII em hash de registro (`cliente.cpf_hash`, `cliente.email_hash` etc.) usado para dedup multi-tenant. | Anual (GATE-1) | tech-lead | Não — global; rotação invalida hashes antigos progressivamente. |
| `PII_HASH_KEY_TENANT_<tenant_id>` | **Por tenant** | HMAC tenant-scoped para `ReferenciaPIIAnonimizavel.hash_original` (ADR-0032). | Anual + na suspensão do tenant. | tech-lead via job | **Sim** — eliminar a key efetua crypto-shredding de todos os hashes de referência daquele tenant. |
| `QR_HMAC_KEY_REGISTRO` | **Global Aferê (escopo etiqueta física)** | HMAC do QR de equipamento (SEC-QR-001). Dedicada — separada do PII. Etiqueta vive 25 anos por RBC. | **Versionada — nunca rotacionada hard** (etiqueta antiga não invalida). | tech-lead | Não — escopo etiqueta sobrevive a tenant. |
| `BIOMETRIA_KEY_<tenant_id>` | **Por tenant — dedicada biometria** | Criptografia AES-GCM da `AceiteAtividade.assinatura_base64` (INV-OS-ACEITE-BIO-001). Watermark embarcado antes de cifrar. | Anual + na suspensão. | tech-lead | **Sim** — eliminar a key = biometria do tenant some imediatamente. |
| `AUDIT_HASH_KEY` | **Global Aferê (escopo audit chain)** | Hash chain entre linhas da `auditoria` + `authz_decisions`. | **Nunca rotacionada** (quebra cadeia hash retroativamente). | tech-lead | Não — global imutável. |
| `KMS_TENANT_DATA_<tenant_id>` | **Por tenant — dados gerais** | Criptografia AES envelope de dados sensíveis do tenant (notas técnicas, anexos, metadados de cliente). | Anual + na suspensão. | tech-lead | **Sim** — crypto-shredding LGPD Zona A. |
| `KMS_BACKUP_<tenant_id>` | **Por tenant — backups WORM** | Criptografia dos backups Backblaze B2 do tenant. | Anual + na suspensão. | tech-lead | **Sim** — backups ficam inacessíveis ao apagar key. |

---

## Rotação anual (GATE-1 F-A — ciclo chave PII)

1. Job anual (1º de janeiro UTC) cria `vN+1` para todas as keys versionadas.
2. Aplicação **escreve novas referências em `vN+1`**; **lê referências antigas em `vN`** (janela 1 ano).
3. Após 1 ano: `vN` é deprecada; aplicação não escreve mais nela; leitura ainda permitida 1 ano (total 2 anos).
4. Após 2 anos: `vN` pode ser apagada com aprovação Roldão + audit + amostragem garantir que nenhuma referência ativa usa `vN`.

## Crypto-shredding ao eliminar tenant (Zona A inteira)

Operação manual com aprovação Roldão + audit imutável:

1. Tenant em `cancelado_definitivamente` há ≥retenção (5 anos Receita / 25 anos ISO 17025 cl. 8.4, o que vier primeiro aplicável).
2. Job lista `PII_HASH_KEY_TENANT_<tenant_id>`, `BIOMETRIA_KEY_<tenant_id>`, `KMS_TENANT_DATA_<tenant_id>`, `KMS_BACKUP_<tenant_id>`.
3. Cada key é deletada via AWS KMS (`ScheduleKeyDeletion` com pending window mínimo 7 dias — janela legal de reversão).
4. Após 7 dias sem reversão, keys são apagadas; dados ficam fisicamente inacessíveis.
5. Audit registra: `who, when, tenant_id, keys_deleted[], aprovacao_roldao_hash`.

## ID

- **INV-LGPD-KMS-001** — toda chave KMS criada para Aferê é registrada nesta tabela em PR. Hook (a criar Onda 4) bloqueia código que referencia `KMS_*` sem entrada correspondente.
- **INV-LGPD-KMS-002** — rotação anual de keys versionadas é responsabilidade do job `job_kms_rotacao` (tech-lead); falha dispara alerta P1.
- **INV-LGPD-KMS-003** — eliminação de tenant em Zona A executa crypto-shredding de todas as keys tenant-scoped listadas; audit imutável.

## NON-GOAL

- **Não** documenta key-pair de TLS (esses são gerenciados por Let's Encrypt + Hostinger).
- **Não** documenta key A3 (ICP-Brasil) — pertence ao usuário, não ao Aferê.
- **Não** lista keys de gateway de pagamento — gateway tokeniza no cliente (SEC-PCI-001).
