---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Transferência internacional de dados

> **Pra quê:** Aferê usa **AWS KMS (USA/EUA)** + **Backblaze B2 EU Central (Alemanha)** + **Grafana Cloud (USA — V2)** + **Axiom (USA — V2)**. LGPD art. 33 trata de transferência internacional. Sem este doc, transferência fica em zona cinzenta.

---

## 1. Visão geral das transferências

| Destino | O que é transferido | Volume | Base legal |
|---------|---------------------|--------|------------|
| **AWS sa-east-1 (BR)** | Dados criptografados + chaves KMS | tudo | n/a (Brasil) |
| **AWS us-east-1 (USA)** | **Réplica de chaves KMS** (não dados) — Multi-Region Key | só chaves | Decisão de adequação ANPD em construção; cláusulas-padrão como mitigação |
| **Backblaze B2 EU Central (Alemanha)** | Backup + WORM de eventos + certificados (criptografados) | tudo cold storage | UE tem decisão de adequação ANPD vigente |
| **Grafana Cloud (USA)** ⏸️ V2 | Métricas + traces anonimizados | telemetria | Legítimo interesse + dados anonimizados |
| **Axiom (USA)** ⏸️ V2 | Logs aplicacionais anonimizados | logs | idem |
| **Anthropic API (USA)** | Prompts + responses LLM | uso do Claude | Sob revisão; ver §3 |
| **PlugNotas (BR)** | XML NFS-e | NFS-e emitida | Brasil — n/a |
| **WhatsApp Cloud (BR/USA — Meta)** ⏸️ V2 | Mensagens transacionais | lembretes | Brasil; processamento em datacenter regional |

---

## 2. Bases legais possíveis (LGPD art. 33)

| Base | Quando aplica |
|------|----------------|
| **I — Decisão de adequação** | País tem reconhecimento ANPD (UE em vigor; Reino Unido em construção) |
| **II — Cláusulas contratuais padrão** | DPA específico com cláusulas-padrão ANPD (UE GDPR cláusulas ok temporariamente) |
| **III — Consentimento específico** | Titular consentiu explicitamente após informado |
| **IV — Cumprimento obrigação legal** | Lei exige transferência |
| **V — Execução de contrato com titular** | Operação contratada exige transferência |
| **VI — Tutela de saúde** | n/a no Aferê |
| **VII — Garantia de prevenção a fraude** | n/a no Aferê |

---

## 3. Caso especial: AWS us-east-1 (KMS Multi-Region Key réplica)

**O que vai:** apenas a chave KMS criptográfica, replicada via MRK. **Não vai dado de cliente.**

**Por que precisa:** disaster recovery — se sa-east-1 inteira ficar indisponível por > 4h, us-east-1 mantém capacidade de descriptografar dados restaurados de backup B2.

**Base legal:** dados não-pessoais (chaves são material criptográfico, não PII). Quando algum dado pessoal eventualmente trafegar (cenário c DR ativado), aplicar cláusulas-padrão + decisão de adequação ANPD em construção pros EUA.

---

## 4. Caso especial: Backblaze B2 EU Central (Alemanha)

**O que vai:** backup completo + WORM de eventos + certificados emitidos. **Tudo criptografado** com chave KMS por tenant.

**Por que EU:** isolamento jurisdicional (jurisdição diferente do Brasil pra DR). Backblaze EU Central tem decisão de adequação ANPD em vigor (UE).

**Mitigações:**
- Dados criptografados em repouso + em trânsito
- Chave fica em AWS KMS (não em B2)
- Crypto-shredding ao deletar chave (B2 vira ilegível)

---

## 5. Caso especial: Anthropic API (Claude)

**O que vai:** prompts + contexto + outputs.

**Risco:** prompts podem conter PII inadvertidamente (e.g., agente ler audit log com `user_id_hash` mas com nome do tenant). Embora hash, é metadata sobre tenant.

**Mitigações:**
- Anthropic tem política de não-treinar com dados de cliente API
- LLM gateway (LiteLLM self-hosted) intercepta e sanitiza antes de mandar
- Não enviar PII bruta (CPF, nome completo) — usar hash/identificadores
- Audit log de toda invocação

**Base legal aplicável:** legítimo interesse (operação do produto) + V (execução de contrato) — operação de IA é parte da execução do contrato Aferê-tenant.

**Pendência V2:** revisar com DPO formal + parecer jurídico.

---

## 6. DPA com cada parceiro

Quando 1º cliente externo aparecer (V2), assinar DPA específico com cada parceiro acima. Lista:
- AWS Data Processing Addendum
- Backblaze Customer Data Processing Addendum
- Anthropic Data Processing Addendum
- Grafana Labs DPA (V2)
- Axiom DPA (V2)
- PlugNotas DPA (já é nacional, contrato comercial cobre)
- Meta WhatsApp Business Terms (V2)

---

## 7. Comunicação ao titular

DPA modelo Aferê → tenant deve listar transferências internacionais que afetam dado do cliente final do tenant. Tenant repassa em sua política de privacidade.

Aferê fornece template + lista atualizada de provedores subprocessadores.

---

## 8. Pendências

- [ ] DPO formal designado (V2)
- [ ] DPA com AWS assinado (faz parte do contrato AWS — verificar)
- [ ] DPA com Backblaze assinado (idem)
- [ ] Revisão jurídica Anthropic (subagent advogado + humano V2)
- [ ] Lista pública de subprocessadores em portal (V2)
- [ ] Atualização anual

---

## 9. Referências

- LGPD lei 13.709 art. 33-36
- ANPD Resoluções sobre transferência internacional
- GDPR art. 44-50 (referência — quando UE)
- `lgpd-rat.md` §7
- `seguranca-dados.md`
- `comum/integracoes-externas/` (futuro)
