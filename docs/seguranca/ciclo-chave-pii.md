---
owner: roldao
revisado-em: 2026-05-22
proximo-review: 2026-08-22
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/faseamento/F-A/tasks-saneamento.md
  - docs/conformidade/comum/isolamento-multi-tenant.md
  - docs/conformidade/comum/retencao-matriz.md
  - docs/conformidade/comum/seguranca-dados.md
  - REGRAS-INEGOCIAVEIS.md
---

# Ciclo de vida da chave de hash de PII

> **Para o dono (resumo em 5 linhas):**
> - PII (CPF, CNPJ de pessoa física, e-mail, telefone) que entra em audit trail é guardada como **hash** (HMAC-SHA256) — não em texto claro. Mas o hash é só seguro enquanto a chave que gerou ele estiver protegida.
> - Toda chave de hash de PII tem **prazo de validade de 1 ano**. Em janeiro de cada ano a chave nova entra em uso; a antiga vai para `PII_HASH_KEYS_RETIRED` (aposentada).
> - A chave aposentada **não pode ser jogada fora imediatamente** — enquanto houver auditoria viva referenciando ela, ela fica guardada para a gente conseguir provar "isso aqui é mesmo o CPF do João".
> - Quando os audits cobertos pela chave antiga forem 100% destruídos (crypto-shredding), a chave aposentada é destruída também — só aí o ciclo dela fecha.
> - É gate `GATE-4` (vem antes do 1º cliente externo pago).

---

## 1. Problema

Auditoria do tipo "quem viu o CPF do João em 2027-03-15?" exige comparar `ip_hash` / `recurso` (hashes HMAC-SHA256) com um CPF candidato. Se o atacante tiver:

- (a) o **dump da tabela** de auditoria **e**
- (b) a **chave HMAC** usada no momento daquele hash

...ele pode confirmar presença por força bruta (CPF tem espaço enumerável: 11 dígitos = ~10¹¹ chaves; com chave HMAC ele itera em segundos).

Mitigação: **rotação anual** da chave de hash + **descarte controlado** da chave aposentada após crypto-shredding de 100% dos registros que ela cobriu.

A chave **não vive no banco do tenant** — vive em segredo gerenciado (AWS Secrets Manager ou env do app). Banco do tenant nunca lê a chave de hash diretamente; lê via função SQL `hash_pii(valor)` que internamente chama o segredo.

---

## 2. Calendário anual

| Janela | Ação | Quem executa |
|--------|------|--------------|
| Dezembro/N-1 | Provisionar chave nova `vN` no AWS Secrets Manager + KMS MRK | Roldão (cofre) |
| 01/janeiro/N 00:00 UTC | App passa a hashear **novos** registros com `vN` | deploy automático (release de janeiro) |
| 01/janeiro/N → 31/dezembro/N | `vN-1` (aposentada) fica em `PII_HASH_KEYS_RETIRED` — só lida para **verificar** hashes antigos (auditoria CGCRE/ANPD/Roldão); zero novos hashes. | banco PG |
| 01/janeiro/N+? | Quando 100% dos registros gerados sob `vN-1` foram **crypto-shredded** (chave de tenant revogada na KMS → dado cifrado vira lixo), aí `vN-1` é destruída no Secrets Manager + linha removida de `PII_HASH_KEYS_RETIRED`. | Roldão |

Prazo típico: chave aposentada vive ≥ 10 anos (alinhado a "audit trail paths sensíveis" da matriz de retenção).

---

## 3. Tabela `PII_HASH_KEYS_RETIRED`

Schema (a criar em migration na Wave A):

```sql
CREATE TABLE pii_hash_keys_retired (
    key_id text PRIMARY KEY,            -- 'v1', 'v2', ...
    aposentada_em timestamptz NOT NULL,
    motivo_aposentadoria text NOT NULL, -- 'rotacao_anual', 'comprometimento', 'auditoria_externa'
    registros_cobertos_estimados bigint, -- estimativa do volume; útil para planejamento de descarte
    descarte_previsto_em timestamptz,   -- data calculada com base na retenção dos registros cobertos
    descartada_em timestamptz NULL,     -- NULL = ainda guardada; preenche quando 100% crypto-shredded
    referencia_secrets_manager text     -- ARN ou path no cofre
);
```

Tabela vive no plano-de-controle (não tem `tenant_id` — chave é global do app). Acesso só via role `app_admin_readonly` + audit obrigatório.

---

## 4. Procedimento operacional de rotação (4 passos)

1. **Gerar `vN`:** `aws secretsmanager create-secret --name afere/pii-hash-key/vN --secret-string "$(openssl rand -base64 32)"`. Atualizar config do app para passar a apontar para `vN` na próxima boot.
2. **Re-hash dos registros novos:** automático — toda escrita nova em audit usa `vN`. **Não re-hashea registros antigos** (eles continuam imutáveis sob `vN-1`).
3. **Aposentadoria:** inserir linha em `PII_HASH_KEYS_RETIRED` para `vN-1`. Tag no Secrets Manager `status=retired`. Aplicação para de aceitar `vN-1` em **escrita** (só leitura).
4. **Descarte (≥ 10 anos depois):** quando 100% dos registros cobertos por `vN-1` viraram lixo crypto-shredded (chave de tenant revogada na KMS), `aws secretsmanager delete-secret --secret-id afere/pii-hash-key/vN-1 --recovery-window-in-days 30`. Atualizar `PII_HASH_KEYS_RETIRED.descartada_em`.

---

## 5. Quando rotacionar antes do prazo

- **Comprometimento confirmado** da chave (incidente P0): rotação imediata + notificação ANPD em 3 dias úteis (INV-005).
- **Comprometimento suspeito** (P1): rotação em ≤24h.
- **Auditoria externa exigir** (CGCRE, ANPD, cliente farma TOP em due diligence): rotação na janela combinada.

Em qualquer rotação fora do calendário, motivo registrado em `PII_HASH_KEYS_RETIRED.motivo_aposentadoria` com valor explícito (não `rotacao_anual`).

---

## 6. Invariante + hook

- Adicionar `INV-PII-KEY-001` em `REGRAS-INEGOCIAVEIS.md`: "Chave de hash de PII tem prazo de validade ≤ 1 ano; aposentadoria entra em `PII_HASH_KEYS_RETIRED`; descarte só após crypto-shredding de 100% dos registros cobertos."
- Hook `pii-hash-key-validator.sh` (a criar Wave A): valida que `hash_pii()` no banco aponta para `vN` da config atual; bloqueia escrita se a chave atual estiver com `aposentada_em IS NOT NULL`.

---

## 7. Testes

Obrigatórios (Wave A):

1. **Rotação:** seed registros sob `v1`; girar para `v2`; novo registro tem `key_id=v2`; verificar que `v1` virou linha em `PII_HASH_KEYS_RETIRED`.
2. **Verificação histórica:** dado hash gerado sob `v1` + CPF candidato + chave `v1` no cofre → função `verificar_hash_pii(hash, cpf, key_id='v1')` retorna `True`.
3. **Tentativa de escrita com chave aposentada:** hook PG bloqueia + alerta P0.

---

## 8. Non-goals

- **Não** vamos rotacionar a chave KMS por-tenant aqui (essa é outra história — vive em `kms_chaves_tenant` + ciclo de tenant em ADR-0015).
- **Não** vamos hashear telemetria/analytics com essa chave (telemetria tem chave própria, retenção 13 meses).

---

## 9. Cronograma

- **Onda 2 (2026-05-22):** este PRD criado.
- **Wave A:** criar tabela `PII_HASH_KEYS_RETIRED` + função `hash_pii(valor)` + provisionar `v1` no Secrets Manager.
- **Janeiro do ano-calendário do 1º tenant pago:** 1ª rotação real (`v1 → v2`).
- **GATE-4 fechado:** quando tabela + função estiverem em produção + 1ª rotação ter rodado com evidência.

---

## 10. Referências

- `docs/conformidade/comum/retencao-matriz.md` — linha "Chave de hash de PII aposentada"
- `docs/conformidade/comum/isolamento-multi-tenant.md` §8 (audit trail)
- `docs/faseamento/F-A/tasks-saneamento.md` — T-FA-S-03
- LGPD Lei 13.709/2018 art. 37, art. 46-49
- Res. CD/ANPD 15/2024 — incidentes
