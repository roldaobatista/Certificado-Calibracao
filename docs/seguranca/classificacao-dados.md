---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Classificação de dados

> **Pra quê:** definir as 5 classes de dados do Aferê + controles obrigatórios por classe. Sem isso, time trata cadastro de tenant igual senha de KMS — ou pior, o contrário.
>
> **Fonte primária:** `conformidade/comum/seguranca-dados.md` §1. Este doc detalha aplicação prática.

---

## 5 classes

| Classe | Definição | Exemplo no Aferê |
|--------|-----------|-------------------|
| **Público** | Pode ser exposto sem prejuízo | Doc público de marketing, blog, status page |
| **Interno** | Limitado à equipe Aferê | Métricas internas, código-fonte, audit log governance |
| **Confidencial** | Dados de tenants (negócio do cliente) | Cadastros de clientes, OS, certificados, NFS-e |
| **Regulado** | Dados pessoais sob LGPD + fiscais + ISO 17025 | PII (CPF, nome, telefone), dados fiscais, dados de certificado |
| **Regulado-untrusted** | Input externo não-confiável | PR comment, issue body, e-mail, anexo de cliente, prompt LLM |

---

## Controles por classe

| Controle | Público | Interno | Confidencial | Regulado | Regulado-untrusted |
|----------|---------|---------|---------------|----------|----------------------|
| Auth + RBAC | ❌ | ✅ | ✅ | ✅ + MFA | ✅ + sanitização |
| Encryption-at-rest | ❌ | opcional | ✅ | ✅ + KMS por tenant | ✅ |
| Encryption-in-transit (TLS 1.3) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Audit log | ❌ | parcial | ✅ | ✅ + WORM | ✅ + sanitização logada |
| Multi-tenant isolation (RLS) | n/a | n/a | ✅ | ✅ | n/a |
| Retenção formal | ❌ | 1 ano | conforme tenant | conforme `retencao-matriz.md` | 30 dias |
| Crypto-shredding | ❌ | ❌ | opcional | ✅ por tenant | ❌ (descartado) |
| Pode disparar ação automática? | ✅ | ✅ | ✅ | ✅ com auditoria | ❌ **NUNCA em paths sensíveis sem aprovação humana** |

---

## Tagging em código

Marcar models e endpoints:

```python
# CLASS: confidencial
class Cliente(models.Model):
    # ...

# CLASS: regulado
class Certificado(models.Model):
    # PII + ISO 17025
    # ...

@classified("regulado")
class CertificateEmissionView(APIView):
    permission_classes = [IsAuthenticated, IsSignatario, MFAVerified]
    # ...
```

Auditor Segurança verifica em pre-commit:
- Model novo sem tag → CONCERN
- Endpoint público (`AllowAny`) acessando model `regulado` → FAIL
- Model `regulado` sem `tenant_id` → FAIL (INV-TENANT)

---

## Mapeamento por módulo

| Módulo | Classe dominante |
|--------|------------------|
| `tenant/` | Regulado (PII contratante) |
| `auth_app/` | Regulado (PII + credencial) |
| `cliente/` | Regulado (PII cliente final) |
| `os/` | Confidencial |
| `calibracao/` | Regulado (PII signatário + dado ISO 17025) |
| `fiscal/` | Regulado (PII + fiscal) |
| `financeiro/` | Regulado (PII + fiscal) |
| `mobile/` | Regulado (GPS + foto + identificação) |
| `painel-do-dono/` | Interno |

---

## Logs e classificação

Conteúdo de log também é classificado:
- Log de ação em `regulado` → log também é `regulado` (anonimizar PII antes de escapar pra Axiom)
- Log de telemetria anônima → `interno`
- Audit WORM → `regulado` (retenção formal)

Hook `log-redaction` (a criar) sanitiza antes de mandar pra observability.

---

## Fluxo de "dado regulado-untrusted vira ação"

```
Input externo (PR comment / e-mail / anexo)
   ↓
Tagged como `regulado-untrusted`
   ↓
LLM gateway sanitiza + classifica
   ↓
Output passa por adapter (anti-corrosion)
   ↓
Decisão: ação em path sensível? → REQUER `APROVADO POR ROLDAO`
                                  → SE NÃO: ação proibida (SEC-003)
   ↓
Audit log obrigatório
```

Ver `seguranca/agente-input-nao-confiavel.md` detalhado.

---

## Referências

- `seguranca-dados.md` (política geral)
- `lgpd-rat.md` (RAT por operação)
- `retencao-matriz.md`
- `agente-input-nao-confiavel.md`
- `REGRAS-INEGOCIAVEIS.md` SEC-003
